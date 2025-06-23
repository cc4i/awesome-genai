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
import asyncio
import time

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")



def create_investigator_agent():
    # common_exit_stack = AsyncExitStack()

    # remote_tools, _ = await MCPToolset.from_server(
    #     connection_params=SseServerParams(
    #         # TODO: IMPORTANT! Change the path below to your remote MCP Server path
    #         url="https://104.16.28.34/sse"
    #     ),
    #     async_exit_stack=common_exit_stack
    # )
    local_tools = MCPToolset(
      connection_params=StdioServerParameters(
          command='npx',
          args=["-y",    # Arguments for the command
            "mcp-server-kubernetes",
            # TODO: IMPORTANT! Change the path below to an ABSOLUTE path on your system.
            # "/path/to/your/folder",
          ],
      ),
      # async_exit_stack=common_exit_stack
    )
    # time.sleep(3)

    print("local_tools: ", local_tools)


    agent = Agent(
        name="gke_investigator_agent",
        model="gemini-2.5-flash-preview-04-17",
        instruction="""
            You are the most experienced GKE Engineer and task to gather detailed information and context:
            - Retrieve detailed logs from specific pods, nodes, events, services, etc.
            - Fetch current configurations of relevant GKE resources (Deployments, Services, Ingress, Nodes, etc.) using tools provided.
            - Query logs and configurations from GKE cluster and nodes.
            
            Outputs/Actions:
            - A structured report of collected diagnostic data.
            - Enriched alerts with detailed context.
        """,
        tools=[local_tools],
    )

    # return agent, common_exit_stack
    return agent
