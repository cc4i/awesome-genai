import json
import os
import requests
from dotenv import load_dotenv

from tools.google_search import GoogleSearch
from tools.tweets_scraper import TweetsScraper
from shared.db.sql_cn import SqlCN
from shared.db.tb_platforms import PlatformId
from shared.c_run import get_google_cloud_run_service_url

import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

# Load environment variables
load_dotenv()

# Db
sqlcn = SqlCN()



def trigger_analysis( project_id, location, thread_id, service_name, nlp="nlp"):
    s_url = get_google_cloud_run_service_url(project_id=project_id, location=location, service_name=service_name)
    if s_url is None:
        s_url="http://localhost:8000"
    print(f"service_url: {s_url}")
    try:
        if nlp == "nlp":
            print(f"Trigger analysis {s_url}/nlp-analysis/{thread_id} again...")
            requests.get(f"{s_url}/nlp-analysis/{thread_id}", timeout=1)
        else:
            print(f"Trigger analysis {s_url}/analysis/{thread_id} again...")
            requests.get(f"{s_url}/analysis/{thread_id}", timeout=1)
    except requests.exceptions.ReadTimeout: 
        pass

# Function to main
def main():
    # All variables
    project_id = os.getenv("PROJECT_ID") or "realtime-reputation-defender"
    location = os.getenv("LOCATION") or "us-central1"
    analysis_service = os.getenv("ANALYSIS_SERVICE") or "analysis-service"
    platform_id = os.getenv("PLATFORM_ID") or "google-news"
    thread_id = os.getenv("THREAD_ID") or "1"

    if platform_id in PlatformId:
        if platform_id == PlatformId.TWITTER.value:
            try:
                ts = TweetsScraper(sqlcn=sqlcn, bearer_token=sqlcn.platforms.api_secret_by(platform_id))
                job = sqlcn.jobs.jobs_by_thread_id(thread_id)
                kw = job.get("keywords")[0]
                tss = ts.searh_tweets(kw)
                ts.save_tweets(thread_id, platform_id, tss)
                    
                # Trigger analysis after each data collecting 
                trigger_analysis(project_id, location, thread_id, analysis_service)
            except Exception as e:
                print(f"Failed to scrape {platform_id}, err: {e}")

        elif platform_id == PlatformId.GOOGLE_NEWS.value or platform_id == PlatformId.GOOGLE_SEARCH.value:
            try:
                b_url="https://browserless-chromium-6qo2cxg3rq-as.a.run.app/content"
                serper_api_key=sqlcn.platforms.api_secret_by(platform_id)
                if serper_api_key is not None:
                    gs = GoogleSearch(sqlcn=sqlcn, serper_api_key=serper_api_key.get("secret"), browserless_url=b_url)

                    job = sqlcn.jobs.the_job(thread_id=thread_id, platform_id=platform_id)
                    kws = job.get("keywords")
                    all_srs = []
                    for kw in kws:
                        print(f"keyword: {kw}")
                        if platform_id == PlatformId.GOOGLE_NEWS.value:
                            all_srs.extend(gs.search_g_news(str(kw)))
                        elif platform_id == PlatformId.GOOGLE_SEARCH.value:
                            all_srs.extend(gs.search_g_engine(kw))
                    # Save into BQ
                    gs.save_page_content(thread_id, platform_id, all_srs)
                    # Trigger analysis after each data collecting 
                    trigger_analysis(project_id, location, thread_id, analysis_service, nlp=None)
                else:
                    print("Failed to load secret & do nothing.")
            except Exception as e:
                print(f"Failed to scrape though {platform_id}, err: {e}")
        


if __name__ == "__main__":
    main()