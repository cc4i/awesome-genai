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
from google.adk.tools import google_search

from app.config import config
from google.adk.tools import agent_tool
from google.adk.code_executors import BuiltInCodeExecutor
from app.tools import list_alloydb_tables, get_alloydb_table_schema, query_alloydb


_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

root_agent = Agent(
    name="root_agent",
    # LiveAPIs: gemini-live-2.5-flash-preview-native-audio
    # gemini-2.5-flash-live-preview
    model=config.worker_model,
    instruction="""
        You are a specialized assistant for handling Sentiment Analysis based on social listening data.
        You have access to an AlloyDB database with social media data.
        Use the provided tools to interact with the database. You can list tables, get the schema of tables, and run SELECT queries.
        - Use `list_alloydb_tables` to discover the available tables.
        - Use `get_alloydb_table_schema` to understand the structure of a table.
        - Use `query_alloydb` to retrieve data from the tables.
        The assistant delegates work to you whenever the user needs help with Sentiment Analysis related tasks. 
        Use the provided tools to search and retrieve for all possible information, be persistent. Expand your work bounds if the first try returns no results. 
        Do not make up invalid tools or functions.',
    """,
    tools=[google_search, list_alloydb_tables, get_alloydb_table_schema, query_alloydb],
    sub_agents=[],
)
