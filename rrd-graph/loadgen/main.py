import uuid
import os
import datetime
import random
import time
import requests
import json
import threading

from google.cloud import run_v2
from google.cloud import storage

from shared.llm import init_model
from shared.c_run import get_google_cloud_run_service_url
from shared.db.sql_cn import SqlCN





# Initial variables 
project_id = os.getenv("PROJECT_ID") or "multi-gke-ops"
location = os.getenv("LOCATION") or "us-central1"
model_id = os.getenv("MODEL_ID") or "gemini-1.5-pro-002"
service_name = os.getenv("SERVICE_NAME") or "analysis-service"
policy_bucket = os.getenv("POLICY_BUCKET") or "simulating_policy_bucket-multi-gke-ops"
policy_running_folder = os.getenv("SIMULATING_POLICY_FOLDER") or "running_polices"
# Db
sqlcn = SqlCN()



def trigger_analysis(thread_id, project_id, location, service_name="analysis-service"):
    s_url = get_google_cloud_run_service_url(service_name="analysis-service", project_id=project_id, location=location)
    if s_url is None:
        s_url="http://localhost:8000"
    print(f"service_url: {s_url}")
    try:
        print(f"Trigger analysis {s_url}/nlp-analysis/{thread_id} again...")
        requests.get(f"{s_url}/nlp-analysis/{thread_id}", timeout=1)
    except requests.exceptions.ReadTimeout: 
        pass

def generate_tweets_sdk(project_id, location, model_id, context, total_tweets, positive_percentage, neutral_percentage, negative_percentage):
    llm = init_model(project_id="multi-gke-ops", location="us-east5", model_id="claude-3-5-sonnet-v2@20241022")
    prompt = f"""
        You are a social media influencer with extensive experience in cultivating engaged audiences across various platforms. Your expertise lies in developing impactful messaging strategies and mitigating potential PR risks through effective communication.

        Your task is to generate tweets based on the following context:

        ```
        {context}
        ```

        Prepare a total of {total_tweets} tweets, with {positive_percentage}% positive, {neutral_percentage}% neutral, and {negative_percentage}% negative sentiment.  Simulate the writing style of different personalities for each tweet (e.g., tech enthusiast, casual user, critic, professional).

        The output must be in JSON format without explanation.  Follow the example below for the desired output structure:        
        """+ """
        ```json
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
        ```
    """
    try:
        g_response = llm.invoke(prompt)
        # tweets = g_response.get("candidates")[0].get("content").get("parts")[0].get("text")
        # if tweets.startswith(" ```json") or tweets.startswith("```json"):
        #     tweets = tweets.replace("```json", "").replace("```", "")
        # elif tweets.startswith(" ```JSON") or tweets.startswith("```JSON"):
        #     tweets = tweets.replace("```JSON", "").replace("```", "")
        # print(g_response)
        return json.loads(g_response.content).get("tweets")
        
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
    print(f"thread_id: {thread_id}, {type(tweets)}, tweets: {tweets}")
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
 

def gen_content_by_threads(simulation_policy:dict, thread_id:str):
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
                    location=location,
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
                    trigger_analysis(thread_id, project_id, location, service_name)
                    time.sleep(policy["pause_time"])
                elapsed_time = time.time() - start_time




def exec_simulating_policy(bucket, blob_name):
    print(f"bucket={bucket}, blob_name={blob_name}")
    client = storage.Client()
    blob = client.bucket(bucket).blob(blob_name)

    try:
        policy = json.loads(blob.download_as_string())
        thread_id = policy["thread_id"]
        actions = policy["actions"]
        gen_content_by_threads(actions, thread_id)
    except Exception as e:
        print(e)




def read_simulating_policies(bucket:str, folder:str):
    print(f"bucket={bucket}, folder={folder}")
    client = storage.Client()
    bucket_client = client.bucket(bucket)
    blobs = bucket_client.list_blobs(prefix=folder)

    all_thd=[]
    for blob in blobs:
        if blob.name.endswith(".json"):
            thd = threading.Thread(target=exec_simulating_policy, args=(bucket, blob.name))
            thd.start()
            print(f"Thread {thd.name}: {thd.ident} is running...for gs://{bucket}/{blob.name}")
            all_thd.append(thd)

    for ta in all_thd:
        ta.join()




if __name__ == "__main__":
    read_simulating_policies(bucket=policy_bucket, folder=policy_running_folder)

