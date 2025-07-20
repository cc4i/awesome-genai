from datetime import datetime
from google.adk.agents import LlmAgent
from app.config import config
from app.extract_agent import file_reader_agent
from google.adk.tools import google_search
from google.adk.planners import BuiltInPlanner
from google.genai import types as genai_types
from google.adk.tools import agent_tool




delivery_checking_agent = LlmAgent(
    name="delivery_checking_agent",
    model=config.critic_model,
    
    # planner=BuiltInPlanner(
    #     thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    # ),
    description= """
        You are a delivery checking agent, specialized in:
        - validating items and receipt details, 
        - checking quality of the dilivery, 
        - other related tasks, etc.
    """,
    instruction="""
        Follow these instructions to provide concise and easy-to-understand summaries:

        1. **Extract the necessary information from the user's request.**
        2. **Analyze the information and determine the best approach to solve the user's request.**
        3. **Execute the best approach to solve the user's request.**
        4. **Output the results in a well-written summary.**
    """,
    # sub_agents=[file_reader_agent],
    tools=[ google_search],

)