# Base
from typing_extensions import TypedDict
from typing import Annotated, Literal, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
from dotenv import load_dotenv

# GenAI
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage

# 
from agent.shared.llm import init_model
from agent.tools.utilities import create_tool_node_with_fallback


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# Initial LLM
llm = init_model(project_id="multi-gke-ops", location="us-east5", model_id="claude-3-5-sonnet-v2@20241022")

perception_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are the perception for AI moderation agent.

            Your primary role is to monitor chat message, record origin messages, enrich messages with context and relevant information,
            so that pass messages to downstream for better result.
            """,
        ),
        ("placeholder", "{messages}"),
    ]
)

perception_tools=[]
perception_runnable = perception_prompt | llm.bind_tools(perception_tools)


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


# Edge routing for tools
def route_tools(state: State):
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # print(f"ai_message > {ai_message}")
    # print(f"ai_message.tool_calls > {ai_message.tool_calls}")
    # print(f"CompleteOrEscalate > {CompleteOrEscalate.__name__}")
    # print(f"ai_message.response_metadata > {ai_message.response_metadata}")

    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    print(f"first_tool_call > {first_tool_call}")
    if first_tool_call["name"] in {t.name for t in zip(perception_tools)}:
        return "perception_tools"


# Define the Graph State
builder = StateGraph(State)

# Define nodes: these do the work
# perception
builder.add_node("perception", Assistant(perception_runnable))
builder.add_node("perception_tools", create_tool_node_with_fallback(perception_tools))
builder.add_conditional_edges(
    "perception", route_tools, ["perception_tools", END]
)
builder.add_edge("perception_tools", "perception")

# reasoning
builder.add_edge("perception", "reasoning")
builder.add_node("reasoning", Assistant(perception_runnable))
builder.add_node("reasoning_tools", create_tool_node_with_fallback(perception_tools))
builder.add_conditional_edges(
    "reasoning", route_tools, ["reasoning_tools", END]
)
builder.add_edge("reasoning_tools", "reasoning")

# actions
builder.add_edge("reasoning", "actions")
builder.add_node("actions", Assistant(perception_runnable))
builder.add_node("actions_tools", create_tool_node_with_fallback(perception_tools))
builder.add_conditional_edges(
    "actions", route_tools, ["actions_tools", END]
)
builder.add_edge("actions_tools", "actions")

# human
builder.add_node("human", Assistant(perception_runnable))
builder.add_node("human_tools", create_tool_node_with_fallback(perception_tools))
builder.add_conditional_edges(
    "human", route_tools, ["human_tools", END]
)
builder.add_edge("human_tools", "human")
builder.add_edge("actions", "human")


builder.add_edge(START, "perception")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)