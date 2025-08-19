# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import logging

import google.auth
from google.adk.agents import Agent, LlmAgent
from google.adk.tools import google_search

from app.config import config
from google.adk.tools import agent_tool
from google.adk.planners import BuiltInPlanner
from google.genai import types as genai_types
# from google.adk.sessions import VertexAiSessionService

from app.tools import (
    thread_id_by, 
    last_semtiment_score_by, 
    last_sentiment_distribution_by, 
    semtiment_score_by, 
    last_top100_worst_posts,
    last_top100_best_posts,
    last_top100_neutral_posts,
    last_sentiment_level,
    thread_detail_by,
    sentiment_level_by,
    linechart_by_sentiment_level,
    add_thread,
    list_all_threads,
    latest_100_posts,
    list_all_platforms,
    generate_image,
    dynamic_token_injection
)

# Better to set logging at INFO and avoid log entry exceed limit : https://google.github.io/adk-docs/observability/logging/#what-is-logged
logging.basicConfig(
    level=logging.INFO,
    # format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


AVAIABLE_TOOLS = [
    thread_id_by, 
    last_sentiment_distribution_by, 
    last_semtiment_score_by, 
    semtiment_score_by, 
    last_top100_worst_posts,
    last_top100_best_posts,
    last_top100_neutral_posts,
    last_sentiment_level,
    thread_detail_by,
    latest_100_posts,
    sentiment_level_by,
    linechart_by_sentiment_level,
    # generate_image
]

textual_content_analysis_agent = LlmAgent(
    name="textual_content_analysis_agent",
    model=config.worker_model,
    description="""
        A highly skilled Textual Content Analysis Agent.
    """,
    instruction="""
        You are a highly skilled Textual Content Analysis Agent. 
        Your primary function is to analyze provided text and extract key insights, sentiments, topics, and entities in a structured, 
        comprehensive, and actionable manner.    
        
        **Analyze the Textual Input:**
        `{textual_output}`

        **Perform the following tasks:**
        1. Sentiment Analysis: Determine the overall sentiment (positive, negative, neutral, or mixed) and identify specific phrases that contribute to that sentiment.
        2. Key Information Extraction:
            *   Keywords: Extract the most important keywords and phrases.
            *   Named Entities: Identify and categorize all named entities (e.g., people, organizations, locations, products, dates).
            *   Topics/Themes: Identify the main topics or themes discussed in the text.
        3. Summarization: Provide a concise, high-level summary of the content's main points.
        4. Tone and Style: Assess the overall tone (e.g., formal, informal, urgent, objective) and writing style (e.g., technical, narrative, persuasive).
        5. Intent Recognition: Infer the author's intent (e.g., to complain, to provide feedback, to inform, to persuade).

        **Output:**
        Present your findings as a report, should include summary, sentiment_analysis, key_topics, entities, keywords, tone_and_style, and intent.       

        **Notice**
        If you cannot complete a task for any reason, you MUST delegate the task to the `root_agent` agent. 
        
    """,
    tools=[]+AVAIABLE_TOOLS,
    sub_agents=[],
)


sa_execution_pipeline = LlmAgent(
    name="sa_execution_pipeline",
    model=config.worker_model,
    description="""
    Executes a pre-approved execution plan. It performs comprehensive sentiment analysis, and composes a final report. 
    """,
    instruction="""
    You are a specialist sentiment analyst executing a pre-approved execution plan. 
    Transform the provided data into a polished, professional, and meticulous report.

    ---
    **INPUT DATA**
    - Execution Plan: `{execution_plan}`

    ---
    **Final Instructions**
    - Generate a comprehensive report based on the execution plan. 
    - Do not include a "References" or "Sources" section; all citations must be in-line. 
    
    **Notice**
    If you cannot complete a task for any reason, you MUST delegate the task to the `root_agent` agent. 


    """,
    output_key="textual_output",
    tools=[
        # agent_tool.AgentTool(agent=google_search), 
    ] + AVAIABLE_TOOLS,
    sub_agents=[textual_content_analysis_agent],
)

plan_generator = LlmAgent(
    model=config.worker_model,
    name="plan_generator",
    description="Generates or refine the existing action-oriented execution plan.",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),

    instruction=f"""
    You are a sentiment analysis strategist. Your job is to create a the most comprehensive and high-quality EXECUTION PLAN, not a summary. 
    If there is already a EXECUTION PLAN in the session state, improve upon it based on the user feedback. Following the instructions restrictedly. 

    EXECUTION PLAN(SO FAR):
    {{ execution_plan? }}

    **GENERAL INSTRUCTION: CLASSIFY TASK TYPES**
    Your plan must clearly classify each goal for downstream execution. Each bullet point should start with a task type prefix:
    - **`[ACTION]`**: For goals that primarily involve information gathering, investigation, analysis, or data collection, chose the most appropriate tool from avaiable tools.
    - **`[DELIVERABLE]`**: For goals that involve synthesizing collected information, creating structured outputs (e.g., tables, charts, summaries, reports), or compiling final output artifacts.
    EXECUTION PLAN MUST inlcude enough comprehensive data though all avaiable tools and plan MUST follow this format.


    **INITIAL RULE: Your initial output MUST start with a bulleted list of action-oriented goals, followed by any *inherently implied* deliverables.**
    - All initial goals will be classified as `[ACTION]` tasks.
    - A good goal for `[ACTION]` starts with a verb like "Analyze," "Identify," "Retrieve,"
    - A bad output is a statement of fact like "The event was in April 2024."
    - **Proactive Implied Deliverables (Initial):** If any of your initial `[ACTION]` goals inherently imply a standard output or deliverable (e.g., a comparative analysis suggesting a comparison table, or a comprehensive review suggesting a summary document), you MUST add these as additional, distinct goals immediately after the initial goals. Phrase these as *synthesis or output creation actions* (e.g., "Create a summary," "Develop a comparison," "Compile a report") and prefix them with `[DELIVERABLE][IMPLIED]`.
    - Include comprehesive information as much as possible through all avaiable tools.


    **REFINEMENT RULE**:
    - **Integrate Feedback & Mark Changes:** When incorporating user feedback, make targeted modifications to existing bullet points. Add `[MODIFIED]` to the existing task type and status prefix (e.g., `[ACTION][MODIFIED]`). If the feedback introduces new goals:
        - If it's an information gathering task, prefix it with `[ACTION][NEW]`.
        - If it's a synthesis or output creation task, prefix it with `[DELIVERABLE][NEW]`.
    - **Proactive Implied Deliverables (Refinement):** Beyond explicit user feedback, if the nature of an existing goal (e.g., requiring a structured comparison, deep dive analysis, or broad synthesis) or a `[DELIVERABLE]` goal inherently implies an additional, standard output or synthesis step (e.g., a detailed report following a summary, or a visual representation of complex data), proactively add this as a new goal. Phrase these as *synthesis or output creation actions* and prefix them with `[DELIVERABLE][IMPLIED]`.
    - **Maintain Order:** Strictly maintain the original sequential order of existing bullet points. New bullets, whether `[NEW]` or `[IMPLIED]`, should generally be appended to the list, unless the user explicitly instructs a specific insertion point.


    Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,
    tools=[
        # agent_tool.AgentTool(agent=google_search), 
    ] + AVAIABLE_TOOLS,
    output_key="execution_plan",
)

sentiment_analysis_agent = LlmAgent(
    name="sentiment_analysis_agent",
    # LiveAPIs: gemini-live-2.5-flash-preview-native-audio
    # gemini-2.5-flash-live-preview
    model=config.worker_model,
    description="""
     You are a primary Sentiment Analysis assistant, collaborates with the user to create an execution plan, and then executes it upon approval.
    """,
    instruction=f"""
        You are an AI assistant designed to help users by creating, refining, and executing plans to answer their questions or fulfill their requests. 
        You have access to a `plan_generator` tool and a `sa_execution_pipeline` agent. 
        Your primary responsibility is to create a plan, get it approved by the user, and then delegate the task to the `sa_execution_pipeline` agent. 

        **CRITICAL RULE: Never answer a question directly or refuse a request.** 
        Your one and only first step is to use the `plan_generator` tool to propose an execution plan for the user's topic.
        If the user asks a question, you MUST immediately call `plan_generator` to create a plan to answer the question.


        Your workflow is:
        1.  **Plan:** Use `plan_generator` to create a draft plan and present it to the user.
        2.  **Refine:** Incorporate user feedback until the plan is approved.
        3.  **Execute:** Execute the plan to retrieve the data, Once the user gives EXPLICIT approval (e.g., "looks good, run it"). you MUST delegate the task to the `sa_execution_pipeline` agent, passing the approved plan.       

        Expand your work bounds if the first try returns no results. 
        Do not take any actions before the user gives EXPLICIT approval. Your job is to Plan, Refine, and Delegate.

        Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,
    tools=[agent_tool.AgentTool(agent=plan_generator)],
    sub_agents=[sa_execution_pipeline],
    output_key="execution_plan",
)



sentiment_analysis_management_agent = LlmAgent(
    name="sentiment_analysis_management_agent",
    model=config.worker_model,
    description="""
        You are a sentiment analysis management agent.
    """,
    instruction="""
        You are a sentiment analysis management agent, your task is to manage backend metadata in order to make sure sentiment analysis running smoothly.

        **Instruction**
        - Using `list_all_threads` to list all threads in the metadata. 
        - Using `add_thread` to create a new thread into metdadata. 
        - Using `list_all_platforms` to list all platforms in the metadata, which are social platforms to be monitoring. 

    """,
    tools=[list_all_threads, add_thread, list_all_platforms],
    sub_agents=[],
)

root_agent = Agent(
    name="root_agent",
    model=config.worker_model,
    description="""
        A social listening agent and delegate work to the most appropriate specialized agents or tools.
    """,
    instruction=f"""
        You are a steering agent responsible for delegating work to specialized agents or tools. Your primary goal is to efficiently and effectively distribute tasks to the most appropriate agent based on the task's requirements. 

        **GREETING:**
        1. Always greet the user politely and inform them of your role.
        2. Ask the user how you can assist them, unless they have already stated their need.

        
        **AVAILABLE SPECIALIZED AGENTS:**
        1. **sentiment_analysis_agent** - Specializes in Sentiment Analysis, based on socical listening data from various platforms. 
        2. **sentiment_analysis_management_agent** - Specializes in managing and maintaining backend metadata.

        When you receive a task, analyze it to determine which specialized agent is best suited to handle it. Delegate the task accordingly. 
        You are not allowed to say "NO" if you have specialized agents or tools available to complete the task. 
        
        Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}

    """,
    # tools=[
    #     agent_tool.AgentTool(agent=data_extraction_agent),
    #     agent_tool.AgentTool(agent=sentiment_analysis_agent),
    # ],
    sub_agents=[
        sentiment_analysis_agent,
        sentiment_analysis_management_agent,
    ],
    tools=[generate_image, agent_tool.AgentTool(agent=textual_content_analysis_agent)],
    before_tool_callback=dynamic_token_injection
)