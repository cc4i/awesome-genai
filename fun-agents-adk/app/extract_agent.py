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
    generate_content_config=genai_types.GenerateContentConfig(
        temperature=1,
        response_mime_type="text/plain",
    ),
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=-1,
        )
    ),
    description="""
        You are an expert data extractor. Your task is to precisely extract data from given files and output as requested format.
    """,
    instruction="""
        **Analyzing Receipt Data**

        My goal is to distill the image into a structured object. 
        I'm focusing on key fields to establish a clear structure. 
        I'm prioritizing the efficient extraction and mapping of data points, ensuring a robust representation.


        **Extracting Key Receipt Fields**

        I'm now zeroing in on defining the precise fields for our object. 
        My focus is on robust data capture; for example, I will handle edge cases for time and date formats. 
        The preliminary structure is in progress, with key-value pairs represented, along with other essential details. 
        I'm aiming for a straightforward format, keeping in mind flexibility for future refinements.

        **Output Format**
        Output format MUST be matching the requested format by the user.
        Output format MUST be in the requested language if specified, otherwise default to English.

    """,
    # sub_agents=[validator_agent],
    output_key="extracted_data",
    # tools=[],
)