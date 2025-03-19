import os
import json
import datetime
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from .keywords import KeywordsBuilder
from agent.shared.db.sql_cn import SqlCN
from agent.shared.llm import init_model

# Db
sqlcn = SqlCN()



@tool
def list_threads() -> list[dict]:
    """
    List all threads are being managed by RRD.

    Returns:
        List of threads and each thread as dictionary that contains detail.
    """
    return sqlcn.threads.list_threads()


@tool
def query_thread_by_id(thread_id:str) -> dict:
    """
    Query threads based on thread_id.

    Args:
        thread_id (str): thread_id to query thread.

    Returns:
        The thread as a dictionary that contains detail.
    """
    t=sqlcn.threads.thread_by_id(thread_id)
    return t
            


@tool
def create_rrd_thread(thread: dict) -> dict:
    """
    Create a Thread from input dictinary with required infomation, store the Thread.
    And then trigger "attche_jobs_to_rrd_thread" to create jobs and attach them to it once a thread is created with success.
    Args:
        thread (dict): Input thread contains detail info to create.
        Example:
        {
            "display_name": "Apple launch event",
            "thread_type": "event",
            "context": "Monitoring Apple launch and sentiment trend in Soical Medias",
            "instructions": "- Collecting data through Twitter and Google News",
            "platform_ids": ["twitter", "google_news"],
        }

    Returns:
        The thread as a dictionary that contains detail and primary key thread_id.
        {
            "thread_id": 1,
            "display_name": "Apple launch event",
            "thread_type": "event",
            "context": "Monitoring Apple launch and sentiment trend in Soical Medias",
            "instructions": "- Collecting data through Twitter and Google News",
            "platform_ids": ["twitter", "google_news"],
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }
    """
    thread_id = sqlcn.threads.create_thread(thread)
    if thread_id is None:
        return None
    else:
        return sqlcn.threads.thread_by_id(thread_id)


@tool
def attche_jobs_to_rrd_thread(thread_id:str) -> list[dict]:
    """
    Create new jobs based on thread_id and attach them to this thread immediately. 
    The number of jobs are to be created based on how many platform the thread related to,
    for example:
        to create two jobs IF platform_ids=["twitter", "google_news"]
            - one for twitter: scraping-{thread_id}-twitter
            - one for google-news: scraping-{thread_id}-google_news
    

    The 'attche_jobs_to_rrd_thread' should be triggered whenever a thread is created successfully.

    Args:
        thread_id(str): query thread detail based on thread_id
    Returns:
        List of job and each job as dictionary that contains detail.
    """
    jobs=[]
    thread = sqlcn.threads.thread_by_id(thread_id)
    if thread is not None:
        context = thread.get("context")
        instructions = thread.get("instructions")
        kb = KeywordsBuilder()
        # kb.gen_keywords4tweets(context, instructions)
        platforms = thread.get("platform_ids")
        for p in platforms:
            job_id = f"scraping-{thread_id}-{p}"
            if p == "twitter":
                keywords = [kb.gen_keywords4tweets(context, instructions)]
            else:
                keywords = kb.gen_keywords4google()
            job = {
                "job_id": job_id,
                "thread_id": thread_id,
                "keywords": keywords,
                "platform_id": p,
                "job_interval": 10,
            }
            sqlcn.jobs.create_job(job)
            jobs.append(job)
            # TODO: Provision Cloud Run as Job Service
    else:
        print(f"thread not found, thread_id: {thread_id}")
    return jobs




@tool
def query_jobs_by_thread_id(thread_id: str) -> list[dict]:
    """
    Query jobs based on thread_id. 

    Args:
        thread_id(str): to query job detail based on thread_id
    Returns:
        List of job and each job as dictionary that contains detail.
        Example:
        [{
            "job_id": "scraping-1-twitter",
            "thread_id": thread_id,
            "keywords": ["key1", "key2"],
            "platform_id": "twitter",
            "job_interval": 10,
            "status": "running",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "job_id": "scraping-1-google-news",
            "thread_id": thread_id,
            "keywords": ["key1", "key2"],
            "platform_id": "google-news",
            "job_interval": 10,
            "status": "running",
            "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        }]

    """
    return sqlcn.jobs.jobs_by_thread_id(thread_id)



@tool
def keywords4tweets_by_context(thread_id:str) -> str:
    """
    Building the best query string based on context and instructions of a thread, 
    which is used to call X (Twitter) API v2 and search the most relavant Tweets.
    """
    t=sqlcn.threads.thread_by_id(thread_id)
    if t is not None:
        context = t.get("context")
        instructions = t.get("instructions")
        kb = KeywordsBuilder()
        return kb.gen_keywords4tweets(context, instructions)
    else:
        return None


@tool
def update_job_with_keywords(thread_id:str, platform_id:str, keywords:list[str])->dict:
    """
    Search the job by thread_id and platform_id, update the job with given keywords immediately. 
    The job_id has unique patter job-{thread_id}-{platform_id}

    Args:
        thread_id (str): a uniqe id for each thread
        platform_id (str): a uniqe id for each platform
    Returns:
        Updated job as dictionary that contains detail.
    """
    return {"job_id": "job-1-twitter", "status": "running"}

@tool
def posts_distribution() -> list[dict]:
    """
    Retrieve distribution of collected post number vs thread_id.
    """
    return sqlcn.posts.posts_distribution()


@tool
def total_posts_count() -> int:
    """
    Retrieve total number of collected posts.
    """
    sub_totals =sqlcn.posts.posts_distribution()
    print(sub_totals)
    total_number = 0
    for v in sub_totals:
       total_number = total_number + int(v.get("count"))
    return total_number



@tool
def generate_sql_run(question) -> list[dict]:
    """
    Genertate SQL based on given metadata of tables, run SQL and then look at the results of the query and return the answer, 
    especially when do not have direct tools to give an answer.
    """
    query_gen_prompt=f"""
    You are a SQL expert with a strong attention to detail.
    You have given a question: {question}
    
    Generate a syntactically correct PostgresQL query without any explanations, based on following metadata of tables:
    
    ## Tables' metadata:
    ===
    {sqlcn.jobs.table.metadata.tables}
    {sqlcn.threads.table.metadata.tables}
    {sqlcn.posts.table.metadata.tables}
    {sqlcn.platforms.table.metadata.tables}
    {sqlcn.sentiment_summaries.table.metadata.tables}
    {sqlcn.playbooks.table.metadata.tables}
    ===

    ## Notes:
    - Using NOT IN with NULL values
    - Using UNION when UNION ALL should have been used
    - Using BETWEEN for exclusive ranges
    - Data type mismatch in predicates
    - Properly quoting identifiers
    - Using the correct number of arguments for functions
    - Casting to the correct data type
    - Using the proper columns for joins
    - DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
    """
    project_id = os.getenv("PROJECT_ID", "multi-gke-ops")
    location = os.getenv("LOCATION", "us-east5")
    model_id = os.getenv("MODEL_ID", "claude-3-5-sonnet-v2@20241022")
    llm = init_model(project_id=project_id, location=location, model_id=model_id)
    g_response = llm.invoke(query_gen_prompt)
    sql_query = g_response.content
    print(f"sql_query: {sql_query}")
    try:
        results = []
        with sqlcn.engine.connect() as conn:
            rows = conn.exec_driver_sql(sql_query).fetchall()
            for r in rows:
                results.append(r._asdict())
            return results
    except Exception as e:
        print(e)
    finally:
        print("finally")
        conn.close()