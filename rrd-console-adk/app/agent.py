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
from zoneinfo import ZoneInfo

import google.auth
from google.adk.agents import Agent, LlmAgent, SequentialAgent
from google.adk.tools import google_search

from app.config import config
from google.adk.tools import agent_tool
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.planners import BuiltInPlanner
from google.genai import types as genai_types
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
    generate_image
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
    generate_image
]


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
    ### INPUT DATA
    *   Execution Plan: `{execution_plan}`

    ---
    ### Final Instructions
    Generate a comprehensive report.
    Do not include a "References" or "Sources" section; all citations must be in-line.

    """,
    tools=[
        # agent_tool.AgentTool(agent=google_search), 
    ] + AVAIABLE_TOOLS,
    sub_agents=[],
)

plan_generator = LlmAgent(
    model=config.worker_model,
    name="plan_generator",
    description="Generates or refine the existing action-oriented execution plan.",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),

    instruction=f"""
    You are a sentiment analysis strategist. Your job is to create a the most comprehensive and high-quality EXECUTION PLAN, not a summary. If there is already a EXECUTION PLAN in the session state,
    improve upon it based on the user feedback. Following the instructions restrictedly. 

    EXECUTION PLAN(SO FAR):
    {{ execution_plan? }}

    **GENERAL INSTRUCTION: CLASSIFY TASK TYPES**
    Your plan must clearly classify each goal for downstream execution. Each bullet point should start with a task type prefix:
    - **`[ACTION]`**: For goals that primarily involve information gathering, investigation, analysis, or data collection, chose the most appropriate tool from avaiable tools.
    - **`[DELIVERABLE]`**: For goals that involve synthesizing collected information, creating structured outputs (e.g., tables, charts, summaries, reports), or compiling final output artifacts.

    **INITIAL RULE: Your initial output MUST start with a bulleted list of action-oriented goals, followed by any *inherently implied* deliverables.**

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
        **CRITICAL RULE: Never answer a question directly or refuse a request.** 
        Your one and only first step is to use the `plan_generator` tool to propose an execution plan for the user's topic.
        If the user asks a question, you MUST immediately call `plan_generator` to create a plan to answer the question.


        Your workflow is:
        1.  **Plan:** Use `plan_generator` to create a draft plan and present it to the user.
        2.  **Refine:** Incorporate user feedback until the plan is approved.
        3.  **Execute:** Execute the plan to retrieve the data, Once the user gives EXPLICIT approval (e.g., "looks good, run it"). you MUST delegate the task to the `sa_execution_pipeline` agent, passing the approved plan.       

        Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
        
        Expand your work bounds if the first try returns no results. 
        Do not take any actions before the user gives EXPLICIT approval. Your job is to Plan, Refine, and Delegate.
    """,
    tools=[agent_tool.AgentTool(agent=plan_generator)],
    sub_agents=[sa_execution_pipeline],
    output_key="execution_plan",
)


data_extraction_agent = LlmAgent(
    name="data_extraction_agent",
    model=config.worker_model,
   
    description="Precisely extract data by using all avaiable tools.""",
    instruction="""
        You are a data extractor. Your task is to precisely extract data by using all avaiable tools, output as requested format.

        **INSTRUCTION**
        - Only use tools have been give. 
        - Think thoroughly to determine right tools. 
    
        Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
    """,
    tools=[agent_tool.AgentTool(agent=google_search)] + AVAIABLE_TOOLS,
)


root_agent = Agent(
    name="root_agent",
    model=config.worker_model,
    instruction="""
        You are a steering agent, your task is to delegate work to the most appropriate specialized agents or tools available to you.

        AVAILABLE SPECIALIZED AGENTS:
        1. **data_extraction_agent** - Precisely extract data by using all avaiable tools.
        2. **sentiment_analysis_agent** - Primary Sentiment Analysis assistant.
    """,
    # tools=[
    #     agent_tool.AgentTool(agent=data_extraction_agent),
    #     agent_tool.AgentTool(agent=sentiment_analysis_agent),
    # ],
    sub_agents=[
        data_extraction_agent,
        sentiment_analysis_agent,
    ],
)