import datetime
import logging
import re
from collections.abc import AsyncGenerator
from typing import Literal

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.planners import BuiltInPlanner
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from app.config import config



file_reader_agent = LlmAgent(
    name="file_reader_agent",
    model=config.worker_model,
    description="You specialize on extracting data from any type of file as per the user's request and convert into specific format.",
    instruction=f"""
    The primary function is to extract data from ANY type of files, conducting image analysis or object recognition if necessary. 
    Convert into required format as output.

    """,
    sub_agents=[],
    tools=[],

)