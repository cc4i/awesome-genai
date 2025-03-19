import os
import json
import datetime
from langchain_core.tools import tool


@tool
def last_sentiment_summary(thread_id: str) -> dict:

    """
    Query latest sentiment analysis by thread_id.
    Beware of the new created thread might not have data due to data collecting take time.

    Args:
        thread_id(str): use thread_id to query sentiment analysis
    
    Returns:
        The summary as a dictionary that contains detail.
    """

    return {"sentiment": "positive"}


@tool
def sentiment_analysis_by_thread(thread_id: str)->str:
    """
    Do Sentiment Analysis based on given thread_id related thread and provide report as result.
    Beware of the new created thread might not have data due to data collecting take time.
    """
    context=""
    platforms=""
    positive_records=""
    negative_records=""
    neutral_records=""
    sentiment_level=""
    top_10_positive_records=""
    top_10_negative_records=""
    
    out_format = {
            "report_name": "Give a creative name for this reputation report within five words.",
            "summary": "Key findings and data points summarized, including reputational strengths and weaknesses.",
            "severity_assessment": "Evaluation of the potential impact on brand reputation.",
            "incident_categorization": {
                "category": "Category of the incident (e.g., unmet expectations, product failure, etc.)",
                "explanation": "Explanation for the chosen category"
            },
            "recommendations": {
                "response_strategy": "Comprehensive communication plan to address concerns and manage public perception.",
                "performance_monitoring": "Methods for tracking the effectiveness of the response strategy.",
                "post_incident_analysis": "Process for reviewing the incident and improving future strategies.",
                "reputation_building": "Proactive measures to strengthen online reputation."
            }
        }
    prompt = f"""
        You are a public relations expert with extensive experience in mitigating reputation incidents and in-depth knowledge of organizational strategies. Your task is to analyze the provided context and analytic data to generate a comprehensive reputation report in JSON format.

        ## Context
        {context}

        ## Analytic Data

        **The sentiment results are based on contet collected from media platforms: {platforms}.** 

        Positive  records: {positive_records}
        Negative records:  {negative_records}
        Neutral records: {neutral_records} 

        ** Sentiment level (sentiment_level = (0.7 * sentiment_score) + (0.3 * sentiment_magnitude)) is formulated by last two hours sentiment records and the value is between 1 and 100 after normalization. ** 

        Average Sentiment level:  {sentiment_level}
        ?

        **Top 10 positive records**

        {top_10_positive_records}

        **Top 10 negative records**

        {top_10_negative_records}

        ## Instructions

        Based on the provided context and analytic data, create a reputation report following this structure:

        {out_format}

        Ensure your report adheres strictly to the JSON structure above.  Use the provided context and analytic data to populate each section of the JSON object with relevant information.
    """
    return prompt