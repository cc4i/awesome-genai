import os
import json
from datetime import datetime, UTC
from dotenv import load_dotenv
import requests

from fastapi import FastAPI, Request

from google.cloud import storage
from google.cloud import language_v2
from google.cloud import run_v2

from shared.db.sql_cn import SqlCN
from shared.c_run import get_google_cloud_run_service_url
from utiles.playbook_tools import PlaybookTools
from utiles.sentiment import Sentiment



# Load environment variables
load_dotenv()

# FastAPI 
fapp = FastAPI()

# Db & Utiles
sqlcn = SqlCN()
pbt = PlaybookTools(sqlcn)
ss = Sentiment(sqlcn)


def trigger_analysis(project_id, location, thread_id, service_name="analysis-service", nlp="nlp"):
    s_url = get_google_cloud_run_service_url(project_id=project_id, location=location, service_name=service_name)
    if s_url is None:
        s_url="http://localhost:8000"
    print(f"service_url: {s_url}")
    try:
        if nlp == "nlp":
            print(f"Trigger analysis {s_url}/nlp-analysis/{thread_id} again...")
            requests.get(f"{s_url}/nlp-analysis/{thread_id}", timeout=2)
        else:
            print(f"Trigger analysis {s_url}/analysis/{thread_id} again...")
            requests.get(f"{s_url}/analysis/{thread_id}", timeout=2)
    except requests.exceptions.ReadTimeout: 
        pass


def append_line_to_gcs_file(bucket_name, blob_name, new_line):
    """
    Appends a line to a file in a GCS bucket.
    Args:
        bucket_name: The name of the GCS bucket.
        blob_name: The name of the file (blob) in the bucket.
        new_line: The line to append to the file.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        # Download the file
        try:
            file_content = blob.download_as_string().decode('utf-8')
        except:
            file_content = ""  # If the file doesn't exist, start with empty content

        # Append the new line
        file_content += new_line + "\n"

        # Upload the modified file
        blob.upload_from_string(file_content)
        print(f"Line appended to {blob_name} in bucket {bucket_name}")
    except Exception as e:
        print(f"Error appending line to GCS file: {e}")



@fapp.get("/")
def index():
    return {"ok": True, "message": "It's Analysis Service for RRD.", "time": datetime.now(UTC).isoformat()}


@fapp.get("/nlp-analysis/{thread_id}")
def nlp_analyze_sentiment(thread_id):
    analysis_gcs_bucket = os.getenv("ANALYSIS_GCS_BUCKET") or "rrd-sentiment-analysis-multi-gke-ops"

    results = ss.retrieve_unprocessed_posts(thread_id)
    if results is not None and len(results.get("data"))>0:
        rows = results.get("data")
        batch_id = results.get("batch_id")
        ls_client = language_v2.LanguageServiceClient()
        # Available types: PLAIN_TEXT, HTML
        document_type_in_plain_text = language_v2.Document.Type.PLAIN_TEXT
        # Optional. If not specified, the language is automatically detected.
        # For list of supported languages:
        # https://cloud.google.com/natural-language/docs/languages
        # language_code = "en"
        analysis_file = f"nlp-analysis-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.jsonl"
        with open(f"/tmp/{analysis_file}", "a") as f:
            for row in rows:
                document = {
                    "content": json.dumps(row.content),
                    "type_": document_type_in_plain_text,
                }

                # Available values: NONE, UTF8, UTF16, UTF32
                # See https://cloud.google.com/natural-language/docs/reference/rest/v2/EncodingType.
                encoding_type = language_v2.EncodingType.UTF8
                try:
                    response = ls_client.analyze_sentiment(
                        request={"document": document, "encoding_type": encoding_type}
                    )
                except Exception as e: 
                    print(e)
                    print(f"Ignored this row due to error!!! post_id:{row.post_id} in batch_id:{batch_id}")
                    continue

                print(f"Language of the text: {response.language_code}")
                if response.document_sentiment.score > 0:
                    label ="positive" 
                elif response.document_sentiment.score == 0:
                    label = "neutral"
                else:
                    label = "negative"
                r_data = {
                    "content_id": row.post_id,
                    "thread_id": row.thread_id,
                    "platform_id": row.platform_id,
                    "sentiment" : {
                        "score": response.document_sentiment.score,
                        "magnitude": response.document_sentiment.magnitude,
                        "label": label
                    }
                }
                f.write(json.dumps(r_data) + '\r')
                f.write('\n')
            f.close()

            if len(rows)>0:
                # Upload the analysis_file into GCS bucket 
                blob_name = ss.upload_to_bucket(f"processed/{analysis_file}", analysis_file, analysis_gcs_bucket)
                print(f"Uploaded file: {blob_name} with success")



@fapp.get("/analysis/{thread_id}")
def analysis(thread_id: str):
    """
    Main function for batch prediction, which includes the following flows:
        1. Extract unprocessed rows from BQ and save it into /to_be_process/ folder in GCS.
        2. Submit a batch predition job for process
        3. Output file will be pushed into /processed/ folder in GCS.
    """

    # Get environment variables
    project_id = os.getenv("PROJECT_ID") or "multi-gke-ops"
    location = os.getenv("LOCATION") or "us-central1"
    batch_model_id = os.getenv("BATCH_MODEL_ID") or "gemini-1.5-pro-002"
    batch_model_location = os.getenv("BATCH_MODEL_LOCATION") or "us-central1"
    analysis_gcs_bucket = os.getenv("ANALYSIS_GCS_BUCKET") or "rrd-sentiment-analysis-multi-gke-ops"
    input_file=f"{thread_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.jsonl"

    print(f"""
        project_id: {project_id}, 
        location: {location}, 
        batch_model_id: {batch_model_id}, 
        thread_id: {thread_id}, 
        analysis_gcs_bucket: {analysis_gcs_bucket}
    """)

    # Initialize VertexAI client
    # initialize_vertexai_client(project_id, location)

    records = ss.propagate_prompt_gcs(project_id=project_id, 
        location=location,
        thread_id=thread_id,
        analysis_gcs_bucket=analysis_gcs_bucket,
        input_file=input_file
    )

    if records is not None:
        job = ss.batch_prediction_gcs(
            batch_model_id=batch_model_id,
            analysis_gcs_bucket=analysis_gcs_bucket,
            input_file=input_file
        )
        # check_job_status(job)
        return {"status": job.state, "dashboard_url": job._dashboard_uri()}
    else:
        return {"ok": "empty_run"}


@fapp.post("/post-analysis")
async def post_analysis(request: Request, q: str | None = None):
    """
    Process the response after prodiction job finished and sync result into buccket. 
    Automatically trigger by object event, post body should be JSON, for eaxmple:
    ```json
    {
        "name": "",
        "bucket": ""
    }
    ```
    """
    # Get POST body
    print(request.headers)  # Log the event headers
    bdata = await request.json()
    print(bdata)  # Log the event data
    bucket_name = bdata['bucket']
    file_name = bdata['name']
    print(f"File {file_name} from bucket {bucket_name}")
    print(f"q={q}")
    if ss.is_marked_blob(blob_name=bdata['name']):
        return {"status": "duplicated event, ignored."}

    # Get environment variables
    project_id = os.getenv("PROJECT_ID") or "multi-gke-ops"
    location = os.getenv("LOCATION") or "us-central1"

    if file_name.startswith("processed"):
        if file_name.startswith("processed/nlp-analysis-"):
            sents = ss.read_analysis_response(gcs_bucket=bucket_name, blob_name=file_name, nlp=q)
        else:
            sents = ss.read_analysis_response(gcs_bucket=bucket_name, blob_name=file_name)
        print(sents)
        
        # Save sentiment core, sentiment_magnitude, sentiment_label
        rows_to_update=[]
        for st in sents:
            try: 
                thread_id = st["thread_id"]
                if st["content_id"].startswith("tw"):
                    platform_id = "twitter"
                elif st["content_id"].startswith("gs"):
                    platform_id = "google-search"
                elif st["content_id"].startswith("gn"):
                    platform_id = "google-news"
                else:
                    platform_id = st["platform_id"]
                
                row = {
                    "post_id": st["content_id"],
                    "thread_id": st["thread_id"],
                    "platform_id": platform_id,
                    "sentiment_score": st["sentiment"]["score"],
                    "sentiment_magnitude": st["sentiment"]["magnitude"],
                    "sentiment_label": st["sentiment"]["label"],
                    "status": "sentimented",
                    "sentiment_at": datetime.now(UTC).isoformat(),
                }
                rows_to_update.append(row)
            except Exception as e:
                print(e)
                pass
        
        if len(rows_to_update)>0:
            # Update sentiment results
            print(f"{len(rows_to_update)} rows will be updated.")
            print(f"{len(sqlcn.posts.save_sentiment_results(rows_to_update))} rows have be updated.")
        
            # Get last sentiment level
            s_level, is_new_level = sqlcn.sentiment_summaries.calculate_sentiment_level(thread_id, platform_id)
            
            if is_new_level:    
                # Trigger generate playbook when sentiment level changed
                pbt.gen_playbook(thread_id=thread_id)

            # Trigger analysis again
            if file_name.startswith("processed/nlp-analysis-"):
                trigger_analysis(project_id=project_id, location=location, thread_id=thread_id)
            else:
                trigger_analysis(project_id=project_id, location=location, thread_id=thread_id, nlp=None)
        else:
            print(f"Triggered but nothing processed, recorded  name: {file_name} into unknown-issues.txt.")
            append_line_to_gcs_file(bucket_name=bucket_name, blob_name="unknown-issues.txt", new_line=file_name)
        return {"status": "post-analysis was done"}



@fapp.get("/playbook/{thread_id}")
def latest_playbook(thread_id: str):
    return sqlcn.playbooks.last_playbook(thread_id)