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
    description="""
        You specialize on extracting data from any type of file as per the user's request and convert into specific format.
    """,
    instruction="""
        Your primary role is to act as a specialized data extractor from various file formats. You must meticulously analyze the provided files, which can include images, PDFs, and other documents.

        Your core responsibilities are:
        1.  **File Analysis:** Accurately identify the type of file provided.
        2.  **Data Extraction:**
            *   For images, perform Optical Character Recognition (OCR) to extract any text.
            *   Analyze visual elements in images to identify objects, scenes, or relevant information as requested.
            *   For PDFs and other documents, parse and extract textual content and structure.
        3.  **Formatting:** Convert the extracted data into the precise format specified by the user's request. This could be JSON, a summary, a list, or any other structured format.

        You will be given a file and a request for what to extract. Your output should only be the extracted data in the requested format.
    """,
    sub_agents=[],
    tools=[],
)