import os
import json
import ast
from dotenv import load_dotenv
import pandas as pd
from shared.db.sql_cn import SqlCN
from shared.llm import init_model, call_llm

# All envariables
load_dotenv()

# Db
sqlcn = SqlCN()

def semtiment_score_by(thread_id:str, platform_id:str, start:str, end:str):
    posts = sqlcn.posts.semtiment_score_by(thread_id, platform_id, start, end)
    post_dates=[]
    sentiment_scores=[]
    sentiment_labels=[]
    platforms=[]
    print(f"posts: {len(posts)}")
    if len(posts) > 0:
        for post in posts:
            # print(post)
            post_dates.append(pd.to_datetime(post.get("sentiment_at")).strftime("%Y-%m-%d %H:%M:%S"))
            sentiment_scores.append(post.get("sentiment_score"))
            sentiment_labels.append(post.get("sentiment_label"))
            platforms.append(post.get("platform_id"))
        
        print(f"post_dates: {len(post_dates)}" )
        print(f"sentiment_scores: {len(sentiment_scores)}" )
        print(f"sentiment_labels: {len(sentiment_labels)}" )
        print(f"platforms: {len(platforms)}")

        return pd.DataFrame(
            {
                "time": pd.DatetimeIndex(post_dates),
                "sentiment_score": sentiment_scores,
                "sentiment_labels": sentiment_labels,
                "platforms": platforms
            }
        )
    else:
        return pd.DataFrame()


def sentiment_level_by(thread_id, start, end):
    ss_data = sqlcn.sentiment_summaries.sentiment_level_by_timestamp(thread_id, start, end)
    
    created_dates=[]
    sentiment_levels=[]
    platform_ids=[]
    if len(ss_data) > 0:
        for row in ss_data:
            created_dates.append(pd.to_datetime(row.get("created_at")).strftime("%Y-%m-%d %H:%M:%S"))
            sentiment_levels.append(row.get("sentiment_level"))
            platform_ids.append(row.get("platform_id"))

            # print(row)
        return pd.DataFrame(
            {
                "time": pd.DatetimeIndex(created_dates),
                "sentiment_level": sentiment_levels,
                "platform": platform_ids
            }
        )
    else:
        return pd.DataFrame()



def sentiment_distribution_by(thread_id, platform_id, start, end):
    sd_data = sqlcn.posts.sentiment_distribution_by_time(thread_id=thread_id, platform_id=platform_id, start=start, end=end)
    counts=[]
    sentiment_labels=[]
    platforms=[]
    if len(sd_data) > 0:
        for sd in sd_data:
            counts.append(sd.get("positive"))
            counts.append(sd.get("neutral"))
            counts.append(sd.get("negtive"))
            sentiment_labels.append("positive")
            sentiment_labels.append("neutral")
            sentiment_labels.append("negtive")
            platforms.append(sd.get("platform_id"))
            platforms.append(sd.get("platform_id"))
            platforms.append(sd.get("platform_id"))
        
        return pd.DataFrame({
            "count": counts,
            "sentiment_label": sentiment_labels,
            "platform": platforms
        })
    else:
        return pd.DataFrame()

def x_posts(thread_id: str):
    posts = sqlcn.posts.recent_top100_worst_posts(thread_id)
    print (f"posts: {len(posts)}")
    pt_data = []
    for row in posts:
        pt_data.append({
            "post_id": row.post_id,
            "thread_id": row.thread_id,
            "platform_id": row.platform_id,
            "content": row.content,
            "scraped_at": row.scraped_at
        })
    return pd.DataFrame(
                data=pt_data,
                columns=["post_id", "thread_id", "platform_id", "content", "scraped_at"],
            )




def x_threads():
    return sqlcn.threads.list_threads()


def x_thread_by_id(thread_id: str):
    thread = sqlcn.threads.thread_by_id(thread_id)
    print(thread)
    return thread_id, thread.get("display_name"), thread.get("context"), thread.get("instructions"), thread.get("platform_ids")

def x_add_thread(thread_name, context, instructions, platform_ids):
    thread = {
        "display_name": thread_name,
        "context": context,
        "instructions": instructions,
        "platform_ids": platform_ids,
    }
    th = sqlcn.threads.create_thread(thread)
    print(f"Added thread: {th.get('thread_id')} with success")
    return pd.DataFrame(
                    data=x_threads(),
                    columns=["thread_id", "display_name", "platform_ids", "created_at"],
                )
def x_delete_thread(thread_id):
    sqlcn.threads.delete_thread(thread_id)
    print(f"deleted thread: {thread_id} with success")
    return pd.DataFrame(
                    data=x_threads(),
                    columns=["thread_id", "display_name", "platform_ids", "created_at"],
                )

def x_update_thread(thread_id, thread_name, context, instructions, platform_ids):
    thread = {
        "thread_id": thread_id,
        "display_name": thread_name,
        "context": context,
        "instructions": instructions,
        "platform_ids": platform_ids,
    }
    sqlcn.threads.update_thread(thread)
    print(f"updated thread: {thread_id} with success")
    return pd.DataFrame(
                    data=x_threads(),
                    columns=["thread_id", "display_name", "platform_ids", "created_at"],
                )



def promot_template_4_twitter(context, instructions):
    tpl = f"""

        # Instruction
        You are an X/Twitter platform expert with extensive experience using the X/Twitter API v2. Your task is to build the best query string to retrieve the most relevant tweets based on the provided context, tasks, and considerations. 

        # Notes
        - Restrictedly follow X(Twitter) documentation for building query string.
        - Return only the valid query string without any explanations.

        # Example 1 
        Build a query string based on the following information:

        ## Context: 
        Hurricane Harvey, a devastating Category 4 hurricane, struck the Gulf Coast of Texas in August 2017. It was one of the most powerful hurricanes to hit the United States in decades. Harvey's most catastrophic impact was the unprecedented rainfall, making it the wettest storm system on record.

        ## Instructions: 
        - Collect any Tweets related this topic to gauge that discuss Hurricane Harvey
        - Prioritize collecting from high ranked influencers
        - Exclude re-tweet and marketing messages.

        ## Query string
        has:geo (from:NWSNHC OR from:NHC_Atlantic OR from:NWSHouston OR from:NWSSanAntonio OR from:USGS_TexasRain OR from:USGS_TexasFlood OR from:JeffLindner1) -is:retweet

        # Example 2
        Build a query string based on the following information:

        ## Context: 
        Better understand the sentiment of the conversation developing around the hashtag, #nowplaying.

        ## Instructions: 
        - Collect any Tweets has the hashtag #nowplaying
        - Prioritize collecting from high ranked influencers
        - Exclude re-tweet and marketing messages.
        - Scoped to just Posts published within North America

        ## Query string
        #nowplaying (happy OR exciting OR excited OR favorite OR fav OR amazing OR lovely OR incredible) (place_country:US OR place_country:MX OR place_country:CA) -horrible -worst -sucks -bad -disappointing


        # Mission
        Build a query string based on the following information:

        ## Context: 
        {context}

        ## Instructions: 
        {instructions}

        ## Query string

    """
    return tpl


def promot_template_4_google(context, instructions):
    tpl = f"""
        You are a Google Search expert with extensive experience in optimizing search results. Your task is to analyze the provided context and instructions to generate a list of relevant Google search keywords.

        Context:
        {context}

        Instructions:
        {instructions}

        Please follow these steps:

        1. Carefully analyze the provided context and instructions.
        2. Identify the main topics and themes discussed in the text.
        3. Generate a list of primary keywords that accurately reflect the most important topics.
        4. Generate a list of secondary keywords that provide additional context and related terms.
        5. Organize the keywords into a JSON object with the following structure:
        """ + """
        ```json
        {
        "primary_keywords": [
            "keyword1",
            "keyword2",
            "keyword3"
            // ... more primary keywords
        ],
        "secondary_keywords": [
            "keyword4",
            "keyword5",
            "keyword6"
            // ... more secondary keywords
        ]
        }
        ```

        Output the JSON object without any additional explanations or text.

    """
    return tpl

def call_llm_sdk(prompt):
    print(f"prompt: ===\n\n{prompt}\n\n===")
    project_id = os.getenv("PROJECT_ID") or "realtime-reputation-defender"
    location = os.getenv("MODEL_LOCATION") or "us-central1"
    model_id = os.getenv("MODEL_ID") or "gemini-1.5-pro-002"
    llm = init_model(project_id=project_id, location=location, model_id=model_id)
    return call_llm(llm, f"{prompt}")


def promot_template_4_playbook(thread_id):
    # Top 100 Negative content
    negative_content = sqlcn.posts.recent_top100_worst_posts(thread_id)
    # Top 10 positive content
    positive_content = sqlcn.posts.recent_top100_best_posts(thread_id)
    # Top 10 Neutral content
    neutral_content = sqlcn.posts.recent_top100_neutral_posts(thread_id)
    # Sentiment distribution as count
    s_distribution = sqlcn.posts.sentiment_distribution_by_score(thread_id)
    # Last sentiment level
    sentiment_level=sqlcn.sentiment_summaries.last_overall_sentiment_level(thread_id)
    # Query thread detail from threads
    thread = sqlcn.threads.thread_by_id(thread_id)

    json_format = {
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
        {thread.get("context")}

        ## Analytic Data

        **The sentiment results are based on contet collected from media platforms: {thread.get("platform_ids")}.** 

        Positive  records: {s_distribution.get("positive")}
        Negative records:  {s_distribution.get("negative")}
        Neutral records: {s_distribution.get("neutral")} 

        ** Sentiment level (sentiment_level = (0.7 * sentiment_score) + (0.3 * sentiment_magnitude)) is formulated by last two hours sentiment records and the value is between 1 and 100 after normalization. ** 

        Sentiment level:  {sentiment_level}

        **Top 100 positive records**

        {positive_content}

        **Top 100 neutral records**

        {negative_content}
        
        **Top 100 negative records**

        {neutral_content}

        ## Instructions

        Based on the provided context and analytic data, create a reputation report following this structure:

        {json_format}

        Ensure your report adheres strictly to the JSON structure above.  Use the provided context and analytic data to populate each section of the JSON object with relevant information.
    """
    return prompt


def last_playbook(thread_id: str):
    pb = sqlcn.playbooks.last_playbook(thread_id)
    print(pb)
    p_summary = json.loads(pb.get("assessment")).get("summary")
    p_severity = json.loads(pb.get("assessment")).get("severity_assessment")

    p_category = json.loads(pb.get("assessment")).get("incident_categorization")
    p_category_str = f"""{p_category.get("category")}, {p_category.get("explanation")}"""

    p_plan = json.loads(pb.get("plan"))
    p_plan_str= ""
    for k,v in p_plan.items():
        p_plan_str = p_plan_str + f"## {k}:\n {v}\n\n"
    
    return p_summary, p_severity, p_category_str, p_plan_str, promot_template_4_playbook(thread_id)



def generate_playbook(prompt: str):
    responding = call_llm_sdk(prompt)
    j_responding = ast.literal_eval(responding)
    print(j_responding)
    p_summary = j_responding.get("summary")
    p_severity = j_responding.get("severity_assessment")

    p_category = j_responding.get("incident_categorization")
    p_category_str = f"""{p_category.get("category")}, {p_category.get("explanation")}"""

    p_plan = j_responding.get("recommendations")
    p_plan_str= ""
    for k,v in p_plan.items():
        p_plan_str = p_plan_str + f"## {k}:\n {v}\n\n"
    return p_summary, p_severity, p_category_str, p_plan_str, prompt