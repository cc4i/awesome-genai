import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent.parent.parent / "libs"
sys.path.insert(0, str(libs_path))

import uuid
import os
import datetime
import random
import time
import requests
import json
import threading
from dotenv import load_dotenv

from google.cloud import storage

from rrd_shared.llm import call_llm
from rrd_shared.llm import init_model
from rrd_shared.c_run import get_google_cloud_run_service_url
from rrd_shared.db.sql_cn import SqlCN
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser



# Initial variables
print("Loading environment variables from .env")
load_dotenv()
project_id = os.getenv("PROJECT_ID")
cr_location = os.getenv("CR_LOCATION")
model_id = os.getenv("MODEL_ID")
model_location = os.getenv("MODEL_LOCATION")
service_name = os.getenv("SERVICE_NAME")
policy_bucket = os.getenv("POLICY_BUCKET") or "simulating_policy_bucket-multi-gke-ops"
policy_running_folder = os.getenv("SIMULATING_POLICY_FOLDER") or "running_polices"
# Db
sqlcn = SqlCN()



class GeneratedTweet(BaseModel):
    sentiment: str = Field(description="sentiment of tweet")
    tweet: str = Field(description="tweet content")
    hastags: list[str] = Field(description="hastags for tweet")

class Tweets(BaseModel):
    tweets: list[GeneratedTweet] = Field(description="list of genrated tweets")


def trigger_analysis(thread_id, project_id, cr_location, service_name="analysis-service"):
    s_url = get_google_cloud_run_service_url(service_name="analysis-service", project_id=project_id, location=cr_location)
    if s_url is None:
        s_url="http://localhost:8000"
    print(f"service_url: {s_url}")
    try:
        if s_url.startswith("http://localhost:8000"):
            print(f"Trigger analysis {s_url}/nlp-analysis/{thread_id}")
        else:
            print(f"Trigger analysis {s_url}/nlp-analysis/{thread_id} again...")
            requests.get(f"{s_url}/nlp-analysis/{thread_id}", timeout=1)
    except requests.exceptions.ReadTimeout: 
        pass

def generate_tweets_sdk(project_id, model_location, model_id, context, total_tweets, positive_percentage, neutral_percentage, negative_percentage):
    llm = init_model(project_id=project_id, location=model_location, model_id=model_id)
    prompt = f"""
        You are a social media influencer with extensive experience in cultivating engaged audiences across various platforms. Your expertise lies in developing impactful messaging strategies and mitigating potential PR risks through effective communication.

        Your task is to generate tweets based on the following context:

        ```
        {context}
        ```

        Prepare a total of {total_tweets} tweets, with {positive_percentage}% positive, {neutral_percentage}% neutral, and {negative_percentage}% negative sentiment.  Simulate the writing style of different personalities for each tweet (e.g., tech enthusiast, casual user, critic, professional).

        The output must be in JSON format without explanation.  Follow the example below for the desired output structure:        
        """+ """
        
        {
            "tweets": [
                    {
                        "sentiment": "positive",
                        "tweet": "Apple Intelligence is a game-changer! 🤩 Seamless AI integration across devices is what I've been waiting for. #AppleGlowtime #iOS18 #AppleWatchSeries10",
                        "hastags": ["#AppleGlowtime", "#iOS18", "#AppleWatchSeries10"]
                    },
                    {
                        "sentiment": "neutral",
                        "tweet": "Interesting to see Apple's approach to AI with Apple Intelligence. Will be watching how it evolves. #AppleGlowtime",
                        "hastags": ["#AppleGlowtime"]
                    },
                    {
                        "sentiment": "negative",
                        "tweet": "Underwhelmed by the AI features at #AppleGlowtime. Expected more innovation, especially with all the hype.",
                        "hastags": ["#AppleGlowtime"]
                    }
                ]
            }
        
    """
    try:
        parser = JsonOutputParser(pydantic_object=Tweets)
        chain = llm | parser
        g_response = chain.invoke(prompt)
        # print(g_response)
        return g_response.get("tweets")
        
    except Exception as e:
        print(e)
        return None


def get_random_time_in_past(minutes_ago_min=1, minutes_ago_max=10):
    """
    Generate a random time in past between minutes_ago_min and minutes_ago_max.
    """
    now = datetime.datetime.now(datetime.UTC)
    random_minutes_ago = random.uniform(minutes_ago_min, minutes_ago_max) 
    time_in_past = now - datetime.timedelta(minutes=random_minutes_ago)
    return time_in_past

def save_tweets(thread_id: str, tweets: list[dict]):
    print(f"thread_id: {thread_id}, generated tweets: {len(tweets)}")
    post_data=[]
    if len(tweets)>0:
        for tw in tweets:
            print(f"###{tw}###")
            pid = uuid.uuid4()
            row = {
                "post_id": f"tw-{pid}",
                "thread_id": int(thread_id),
                "platform_id": "twitter",
                "content": tw.get("tweet"),
                "conent_type": "post",
                "summary": tw.get("tweet"),
                "hastags": tw.get("hastags"),
                "status": "pending",
                "created_at": get_random_time_in_past().isoformat(),
                "scraped_at": datetime.datetime.now(datetime.UTC).isoformat(),
            }
            post_data.append(row)

        print(f"{len(post_data)} rows will be inserted.")
        sqlcn.posts.create_posts_in_batch(post_data)


def thread_by_id(thread_id:str):
    thread = sqlcn.threads.thread_by_id(thread_id)
    print(thread)
    return thread
 

def gen_content_by_threads(project_id:str, cr_location:str, model_location:str, model_id:str, simulation_policy:dict, thread_id:str):
    thread = thread_by_id(thread_id)
    print(thread)
    if thread is None:
        print(f"Pls insert Thread record into database with thread_id={thread_id}")
    else:
        for policy in simulation_policy:
            print(policy)
            start_time = time.time()
            elapsed_time = 0
            while elapsed_time < policy["last_time"]*60:
                tweets =  generate_tweets_sdk(
                    project_id=project_id,
                    model_location=model_location,
                    model_id=model_id,
                    context=thread.get("context"),
                    total_tweets=policy["total_tweets_per_ask"],
                    positive_percentage=policy["positive_percentage"],
                    neutral_percentage=policy["neutral_percentage"],
                    negative_percentage=policy["negative_percentage"]
                )
                
                if len(tweets)>0:
                    save_tweets(thread_id, tweets)
                    # Trigger analysis after each data collecting 
                    trigger_analysis(thread_id, project_id, cr_location, service_name)
                    time.sleep(policy["pause_time"])
                elapsed_time = time.time() - start_time




def exec_simulating_policy(project_id, cr_location, model_location, model_id, bucket, blob_name):
    print(f"project_id={project_id}, bucket={bucket}, blob_name={blob_name}")
    client = storage.Client(project=project_id)
    blob = client.bucket(bucket).blob(blob_name)

    try:
        policy = json.loads(blob.download_as_string())
        thread_id = policy["thread_id"]
        actions = policy["actions"]
        gen_content_by_threads(project_id, cr_location, model_location, model_id, actions, thread_id)
    except Exception as e:
        print(e)




def read_simulating_policies(project_id:str, cr_location:str, model_location:str, model_id:str, bucket:str, folder:str):
    print(f"project_id={project_id}, cr_location={cr_location}, model_location={model_location}, model_id={model_id}, bucket={bucket}, folder={folder}")
    client = storage.Client(project=project_id)
    bucket_client = client.bucket(bucket)
    blobs = bucket_client.list_blobs(prefix=folder)

    all_thd=[]
    for blob in blobs:
        if blob.name.endswith(".json"):
            print(blob.name)
            thd = threading.Thread(target=exec_simulating_policy, args=(project_id, cr_location, model_location, model_id, bucket, blob.name))
            thd.start()
            print(f"Thread {thd.name}: {thd.ident} is running...for gs://{bucket}/{blob.name}")
            all_thd.append(thd)

    for ta in all_thd:
        ta.join()




if __name__ == "__main__":
    read_simulating_policies(project_id=project_id, cr_location=cr_location, model_location=model_location,  model_id=model_id, bucket=policy_bucket, folder=policy_running_folder)

