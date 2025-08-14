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
from google.adk.agents import Agent
from app.deep_searcher_agent import deep_searcher_agent
from app.extract_agent import file_reader_agent
from app.fun_searcher_agent import fun_searcher_agent
from app.delivery_checking_agent import delivery_checking_agent
from app.config import config
from google.adk.tools import agent_tool
from google.adk.code_executors import BuiltInCodeExecutor

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

coding_agent = Agent(
    model='gemini-2.0-flash',
    name='coding_agent',
     instruction="""
     You are a code execution agent.
     When given a code, write and execute Python code to calculate the result.
     Return only the final numerical result as plain text, without markdown or code blocks.
    """,
    description="Executes Python code to perform calculations.",
    code_executor=BuiltInCodeExecutor(),
)

root_agent = Agent(
    name="root_agent",
    # LiveAPIs: gemini-live-2.5-flash-preview-native-audio
    # gemini-2.5-flash-live-preview
    model=config.worker_model,
    instruction="""
        You are a smart task dispatcher. Your primary role is to analyze user requests and delegate work to the most appropriate specialized agents or tools available to you.

        AVAILABLE SPECIALIZED AGENTS:
        1. **file_reader_agent** - Specializes in extracting and analyzing data from files (documents, images, etc.)
        2. **deep_searcher_agent** - Performs comprehensive deep research, through planning and executing phases, and creates detailed reports
        3. **fun_searcher_agent** - Conducts fun research powered by Google searches for interesting and engaging information
        4. **delivery_checking_agent** - Checks the delivery status of a package, validates items and reciept details, etc.
        5. **coding_agent** - Executes code and provides detailed output.

        DELEGATION STRATEGY:
        - **Analyze the user's request carefully** to understand what type of work is needed
        - **Choose the most appropriate agent(s)** based on the task requirements:
          * Use **file_reader_agent** for document analysis, data extraction, or file processing tasks
          * MUST USE **fun_searcher_agent** when the user explicitly mentions:
            - "simple" research/search
            - "fun" research/search
            - "quick" lookup
            - "casual" information gathering
            - "interesting" facts
            - "light" research
          * Use **deep_searcher_agent** for ALL OTHER research tasks, including:
            - Comprehensive analysis
            - Detailed investigations
            - Professional research
            - Academic inquiries
            - Business intelligence
            - Technical deep dives
            - Any serious research that requires thorough planning and execution
          * Use **delivery_checking_agent** for delivery checking tasks, including:
            - Checking the delivery status of a package
            - Validating items and reciept details
            - Any delivery related tasks
          * Use **coding_agent** for any code execution tasks, including:
            - Code execution
            - Code debugging
            - Code optimization
            - Code refactoring
            - Any code related tasks
        - **Provide clear context** to the chosen agent about what the user needs
        - **Coordinate multiple agents** if the task requires different types of expertise
        - **Synthesize results** from multiple agents when necessary

        IMPORTANT GUIDELINES:
        - Always choose real, available agents - never make up non-existent tools
        - **Default to deep_searcher_agent** for research tasks unless the user specifically indicates they want simple/fun research
        - If an agent doesn't produce satisfactory results, try a different approach or agent
        - Be proactive in expanding the scope of work if initial attempts yield insufficient results
        - Provide the user with clear explanations of which agents you're using and why
        - If unsure which research agent to use, choose deep_searcher_agent for more comprehensive results

        Remember: You are the orchestrator. Your job is to ensure the user gets the best possible results by leveraging the right combination of specialized agents. When in doubt about research depth, always err on the side of thoroughness with deep_searcher_agent.
    """,
    tools=[
        agent_tool.AgentTool(agent=deep_searcher_agent),
        agent_tool.AgentTool(agent=fun_searcher_agent),
        agent_tool.AgentTool(agent=coding_agent)
    ],
    sub_agents=[
        file_reader_agent,
        delivery_checking_agent,
    ],
)
