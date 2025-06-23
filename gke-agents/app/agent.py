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

from contextlib import AsyncExitStack
import google.auth
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, SseServerParams

from app.gke_doc_agent import gke_doc_agent
from app.gke_investigator_agent import create_investigator_agent
import asyncio

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")



# Define an async function to create the root agent
def create_root_agent():

    investigator_agent = create_investigator_agent()

    agent = Agent(
        name="root_agent",
        model="gemini-2.5-flash-preview-04-17",
        instruction="You are a help AI assistant, serve as the primary interface for human operators and to coordinate the activities of other specialized agents.",
        sub_agents=[gke_doc_agent, investigator_agent], # Use the awaited agent
    )
    # Return the root agent AND the exit stack
    return agent

# Assign the coroutine (the ADK framework will await it)
root_agent = create_root_agent()


