import os
from langchain_core.tools import tool

@tool
def scraping_google_news() -> str:
    """
    Scraping google news to feed into sentiment analysis.
    """
    return "scape_google_news"