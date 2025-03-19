import os
import json
import datetime
from langchain_core.tools import tool



@tool
def how_to_sentiment() -> str:

    """
    Provide information about to a user how to kick off the sentiment analysis for event, or incident, etc.
    The user must provide following information:
    
    - Either provide existed thread_id or display_name, query thread_id and then check out the sentiment through specialized assistant. 

    - Or the user can provide following information, for exmaple: 
        {
            "thread_id": 1,
            "display_name": "Apple launch event",
            "thread_type": "event",
            "context": "Monitoring Apple launch and sentiment trend in Soical Medias",
            "instructions": "- Collecting data through Twitter and Google News",
            "platform_ids": ["twitter", "google_news"],
        }
      and then specialized assistant will create a new thread, after success then send to specialized assistant for sentiment analysis.
    
    """

    return "how to instructions"

@tool
def running_model() ->str:

    """
    Query what LLM model is running in RRD.

    Returns:
        The name of LLM model.
    """

    return "running_mode_id"