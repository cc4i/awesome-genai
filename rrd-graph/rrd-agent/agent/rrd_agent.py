# Base
from typing_extensions import TypedDict
from typing import Annotated, Literal, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
from dotenv import load_dotenv

# Customized utiles
from agent.tools.rrd_backend import query_thread_by_id
from agent.tools.rrd_backend import create_rrd_thread
from agent.tools.rrd_backend import query_jobs_by_thread_id
from agent.tools.rrd_backend import attche_jobs_to_rrd_thread
from agent.tools.rrd_backend import list_threads
from agent.tools.rrd_sentiment import last_sentiment_summary
from agent.tools.rrd_backend import keywords4tweets_by_context
from agent.tools.rrd_backend import update_job_with_keywords
from agent.tools.rrd_backend import posts_distribution
from agent.tools.rrd_backend import total_posts_count
from agent.tools.rrd import running_model
from agent.tools.rrd import how_to_sentiment
from agent.tools.rrd_backend import generate_sql_run
from agent.tools.rrd_playbook import latest_playbook

from agent.tools.utilities import create_tool_node_with_fallback
from agent.tools.utilities import _print_event
from agent.shared.llm import init_model


# GenAI
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage


# State for Graph
def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    print(f"update_dialog_stack > {right}")
    return left + [right]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    # thread_id: str
    dialog_state: Annotated[
        list[
            Literal[
                "rrd_assistant",
                "rrd_backend",
                "rrd_sentiment",
                "rrd_playbook",
            ]
        ],
        update_dialog_stack,
    ]

# Initial LLM
# llm = init_model(project_id="multi-gke-ops", location="us-east5", model_id="claude-3-5-sonnet-v2@20241022")
llm = init_model(project_id="multi-gke-ops", location="us-east5", model_id="claude-3-7-sonnet@20250219")
# ?400 Function calling is not enabled for models/gemini-2.0-flash-thinking-exp-01-21
llm = init_model(project_id="multi-gke-ops", location="us-central1", model_id="gemini-2.0-flash-001")
# llm = init_model(project_id="multi-gke-ops", location="us-central1", model_id="gemini-2.0-flash")
# llm = init_model(project_id="multi-gke-ops", location="us-central1", model_id="gemini-exp-1220")
# llm = init_model(project_id="multi-gke-ops", location="us-central1", model_id="grok-2-latest")
#gemini-2.0-flash-thinking-exp-1219
#gemini-exp-1220

# CompleteOrEscalate
class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the rrd assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str


# rrd backend
rrd_backend_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant to handle all backend oprational tasks for Realtime Reputation Defender (RRD)."
            "The rrd assistant delegates work to you whenever the user needs help around data query, thread creation, job creation, backend matainnace etc. "
            "When creating or provisioning resources, you always double check all required information has been provided before proceeding."
            "Use the provided tools to accomplish tasks, be persistent, and fulfill user's request. "
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then"
            ' "CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.',
        ),
        ("placeholder", "{messages}"),
    ]
)
rrd_backend_tools=[
    query_thread_by_id,
    create_rrd_thread,
    attche_jobs_to_rrd_thread,
    query_jobs_by_thread_id,
    keywords4tweets_by_context,
    update_job_with_keywords,
    list_threads,
    posts_distribution,
    total_posts_count,
    generate_sql_run,
]
rrd_backend_runnable = rrd_backend_prompt | llm.bind_tools(rrd_backend_tools + [CompleteOrEscalate])

# rrd sentiment
rrd_sentiment_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling Sentiment Analysis."
            "The rrd assistant delegates work to you whenever the user needs help with Sentiment Analysis related tasks. "
            "Use the provided tools to search and retrieve for all possible information, be persistent. Expand your work bounds if the first try returns no results. "
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then"
            ' "CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.',
            
        ),
        ("placeholder", "{messages}"),
    ]
)
rrd_sentiment_tools=[
    last_sentiment_summary

]
rrd_sentiment_runnable = rrd_sentiment_prompt | llm.bind_tools(rrd_sentiment_tools+[CompleteOrEscalate])

# rrd playbook 
rrd_playbook_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant to provide a playbook based on sentiment analysis results to guide through mitigation process."
            "The rrd assistant delegates work to you whenever the user needs help with playbook, guide, mitigation, etc related tasks. "
            "Use the provided tools to search and retrieve for all possible information and complish the tasks, be persistent. Expand your work bounds if the first try returns no results. "
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then"
            ' "CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.',
            
        ),
        ("placeholder", "{messages}"),
    ]
)
rrd_playbook_tools=[latest_playbook]
rrd_playbook_runnable = rrd_playbook_prompt | llm.bind_tools(rrd_playbook_tools+[CompleteOrEscalate])



# Entry to sub-agents

class ToRrdBackend(BaseModel):
    """Transfers work to a specialized assistant to handle all backend oprational tasks for Realtime Reputation Defender (RRD)."""
    
    request: str = Field(
        description="Any necessary follow up questions RRD Backend Assistant should clarify before proceeding."
    )

class ToRrdSentiment(BaseModel):
    """Transfers work to a specialized assistant to handle Sentiment Analysis."""

    thread_id: str = Field(
        description="The thread_id is PK and what the Thread refers to."
    )
    request: str = Field(
        description="Any necessary follow up questions RRD Sentiment Assistant should clarify before proceeding."
    )

class ToRrdPlaybook(BaseModel):
    """Transfers work to a specialized assistant to handle playbook, guide, mitigation, etc related tasks."""

    thread_id: str = Field(
        description="The thread_id is PK and what the Thread refers to."
    )
    request: str = Field(
        description="Any necessary follow up questions RRD Sentiment Assistant should clarify before proceeding."
    )


# rrd assistant
rrd_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful rrd assistant for Realtime Reputation Defender (RRD). "
            "Your primary role is to general guidance to use RRD, provide public relationship and risk stratagies to answer user's queries. "
            "If a user requests to backend manatainace, data query, or sentiment analysis (must have thread before doing any analysis)"
            "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. You are not able to make these types of tasks yourself."
            "Only the specialized assistants are given permission to do this for the user."
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the user, and always double-check before concluding that information is unavailable. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())
rrd_assistant_tools=[
    running_model,
    how_to_sentiment
]
rrd_assistant_runnable = rrd_assistant_prompt | llm.bind_tools(
    rrd_assistant_tools
    + [
        ToRrdBackend,
        ToRrdSentiment,
        ToRrdPlaybook,
    ]
    )


# Entry node for all specialized assistant
def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the rrd assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node

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

    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in ai_message.tool_calls)
    if did_cancel:
        return "leave_skill"

    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    print(f"first_tool_call > {first_tool_call}")
    print(rrd_sentiment_tools)
    if first_tool_call["name"] in {t.name for t in rrd_sentiment_tools}:
        return "rrd_sentiment_tools"
    elif first_tool_call["name"] in {t.name for t in rrd_playbook_tools}:
        return "rrd_playbook_tools"
    else:
        return "rrd_backend_tools"


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


# Define the Graph State
builder = StateGraph(State)


# Define nodes: these do the work
builder.add_node("rrd_assistant", Assistant(rrd_assistant_runnable))
builder.add_node("rrd_assistant_tools", create_tool_node_with_fallback(rrd_assistant_tools))

# Backend nodes
builder.add_node(
    "enter_rrd_backend",
    create_entry_node("Backend Assistant", "rrd_backend"),
)
builder.add_node("rrd_backend", Assistant(rrd_backend_runnable))
builder.add_edge("enter_rrd_backend", "rrd_backend")
builder.add_node("rrd_backend_tools", create_tool_node_with_fallback(rrd_backend_tools))

# Sentiment nodes
builder.add_node(
    "enter_rrd_sentiment",
    create_entry_node("Sentiment Assistant", "rrd_sentiment"),
)
builder.add_node("rrd_sentiment", Assistant(rrd_sentiment_runnable))
builder.add_edge("enter_rrd_sentiment", "rrd_sentiment")
builder.add_node("rrd_sentiment_tools", create_tool_node_with_fallback(rrd_sentiment_tools))

# Playbook nodes
builder.add_node(
    "enter_rrd_playbook",
    create_entry_node("Playbook Assistant", "rrd_playbook"),
)
builder.add_node("rrd_playbook", Assistant(rrd_playbook_runnable))
builder.add_edge("enter_rrd_playbook", "rrd_playbook")
builder.add_node("rrd_playbook_tools", create_tool_node_with_fallback(rrd_playbook_tools))




# Define edges: these determine how the control flow moves
builder.add_conditional_edges(
    "rrd_backend", route_tools, ["rrd_backend_tools", "leave_skill", END]
)
builder.add_edge("rrd_backend_tools", "rrd_backend")

builder.add_conditional_edges(
    "rrd_sentiment", route_tools, ["rrd_sentiment_tools", "leave_skill", END]
)
builder.add_edge("rrd_sentiment_tools", "rrd_sentiment")

builder.add_conditional_edges(
    "rrd_playbook", route_tools, ["rrd_playbook_tools", "leave_skill", END]
)
builder.add_edge("rrd_playbook_tools", "rrd_playbook")



def route_rrd_primary_assistant(state: State):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToRrdBackend.__name__:
            return "enter_rrd_backend"
        elif tool_calls[0]["name"] == ToRrdSentiment.__name__:
            return "enter_rrd_sentiment"
        elif tool_calls[0]["name"] == ToRrdPlaybook.__name__:
            return "enter_rrd_playbook"
        return "rrd_assistant_tools"
    raise ValueError("Invalid route")

builder.add_conditional_edges(
    "rrd_assistant",
    route_rrd_primary_assistant,
    [
        "enter_rrd_backend",
        "enter_rrd_sentiment",
        "enter_rrd_playbook",
        "rrd_assistant_tools",
        END,
    ],
)
builder.add_edge("rrd_assistant_tools", "rrd_assistant")



# This node will be shared for exiting all specialized assistants
def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }


builder.add_node("leave_skill", pop_dialog_state)
builder.add_edge("leave_skill", "rrd_assistant")

builder.add_edge(START, "rrd_assistant")



# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)



# Local run without LangGraph Studio
# import uuid
# thread_id = str(uuid.uuid4())

# config = {
#     "configurable": {
#         # Checkpoints are accessed by thread_id
#         "thread_id": thread_id,
#     }
# }
# _printed = set()
# while True:
#     user_input = input("User: ")
#     if not user_input:
#         user_input = "query thread by id=1"
#     if user_input.lower() in ["quit", "exit", "q"]:
#         print("Goodbye!")
#         break
#     events = graph.stream(
#             {"messages": ("user", user_input)}, config, stream_mode="values"
#         )
#     for event in events:
#         _print_event(event, _printed)

