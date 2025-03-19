import os
import json
import time
import requests
import uuid

from vertexai.preview.batch_prediction import BatchPredictionJob
from google.cloud import storage

from shared.db.sql_cn import SqlCN

class Sentiment():
    def __init__(self, sqlcn: SqlCN):
        self.sqlcn = sqlcn



    def upload_to_bucket(self, blob_name, file, gcs_bucket):
        """ 
        Upload a file to the given Google Cloud Storage bucket.
        """

        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(f"/tmp/{file}")
        
        return blob.name


    def retrieve_unprocessed_posts(self, thread_id):
        batch_id = f"bt-{uuid.uuid4()}"    
        return {"batch_id": batch_id, "data": self.sqlcn.posts.latest_100_posts(thread_id)}


    def propagate_prompt_gcs(self, project_id, location, thread_id, analysis_gcs_bucket, input_file):
        """
        Propagate the prompt to GCS for batch prediction.
        """

        print(f"""
            project_id: {project_id}, 
            location: {location}, 
            thread_id: {thread_id},
            analysis_gcs_bucket: {analysis_gcs_bucket},
            input_file: {input_file}
        """)

        results = self.retrieve_unprocessed_posts(thread_id)
        if results is not None and len(results.get("data"))>0:
            rows = results.get("data")
            analysis_file = input_file
            with open(f"/tmp/{analysis_file}", "a") as f:
                for row in rows:
                    # Create the JSON structure for each row
                    data = {
                        "request": {
                            "contents": [
                                {
                                    "role": "user",
                                    "parts": {
                                        "text": f"""
                                            Content_ID: {row.post_id}
                                            Thread_ID: {row.thread_id}
                                            Platform_ID: {row.platform_id}
                                            Content: {row.content}
                                            Output: 
                                        """
                                    }
                                }
                            ],
                            "system_instruction": {
                                "role": "system",
                                "parts": [
                                    {"text": """
                                    
                                    You are an expert at analyzing the sentiment of the content of Tweet from X(Twitter) to determine whether they reflect positively or negatively on a location. Please consider the following factors:

                                    * **Overall Tone:**  Assess the general sentiment expressed in the review. Is it predominantly positive, negative, or neutral?
                                    * **Specific Aspects:**  Pay attention to mentions of key aspects like service, atmosphere, quality, price, and cleanliness. How does the reviewer evaluate these aspects?
                                    * **Subjectivity:**  Recognize that some experiences are inherently subjective (e.g., taste preferences). Focus on the reviewer's experience rather than your personal opinions.
                                    * **Sentiment Score:** The value is between -1.0 (very negative) and 1.0 (very positive)
                                    * **Magnitude:** The value is between -1.0 and 1.0
                                    * **Label:** The value should be either "positive", "negative", or "neutral"

                                    Based on your analysis and give JSON out as following.

                                    For example:
                                    Content_ID: 100010001
                                    Thread_ID: 10001
                                    Platform_ID: twitter
                                    Content: "I'm slightly happy with the iPhone 16 plus due to new camera control button."
                                    Output: 
                                    {
                                        "content_id": "100010001",
                                        "thread_id": "10001",
                                        "platform_id": "twitter",
                                        "sentiment": {
                                            "score": 0.4,
                                            "magnitude": 0.3,
                                            "label": "positive"
                                        }
                                    }

                                    Content_ID: 100010002
                                    Thread_ID: 10001
                                    Platform_ID: google-search
                                    Content: "I'm tired with iPhone, which only provides minor upgrade, nothing special excepted updated hardware."
                                    Output:
                                    {
                                        "content_id": "100010002",
                                        "thread_id": "10001",
                                        "platform_id": "google-search",
                                        "sentiment": {
                                            "score": -0.5,
                                            "magnitude": 0.6,
                                            "label": "negative"
                                        }
                                    }
                                    """}
                                ]
                            },
                            "generation_config": {"top_k": 5}
                        }
                    }
                    f.write(json.dumps(data) + '\r')
                    f.write('\n')
                f.close()

                if len(rows)>0:
                    # Upload the analysis_file into GCS bucket 
                    blob_name = self.upload_to_bucket(f"to_be_process/{analysis_file}", analysis_file, analysis_gcs_bucket)
                    print(f"Uploaded file: {blob_name} with success")


    def batch_prediction_gcs(self, model_id, analysis_gcs_bucket, input_file):
        """
        Submit a batch prediction job to Vertex AI.
        """

        job = BatchPredictionJob.submit(
            source_model=model_id,
            # gs://path/to/input/data.jsonl
            input_dataset=f'gs://{analysis_gcs_bucket}/to_be_process/{input_file}',
            output_uri_prefix=f'gs://{analysis_gcs_bucket}/processed/',
        )
        return job


    def check_job_status(self, job):
        """
        Check the status of the batch prediction job.
        """

        print(f"Job resouce name: {job.resource_name}")
        print(f"Model resource name with the job: {job.model_name}")
        print(f"Job state: {job.state.name}")

        # Refresh the job until complete
        while not job.has_ended:
            print(f"Job state: {job.state.name}")
            time.sleep(5)
            job.refresh()

        # Check if the job succeeds
        if job.has_succeeded:
            print("Job succeeded!")
        else:
            print(f"Job failed: {job.error}")


    def read_analysis_response(self, gcs_bucket, blob_name, nlp=None):
        """
        Read the analysis response from GCS.
        """

        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        blob = bucket.blob(blob_name)
        print(f"nlp={nlp}")
        # Iterate over the lines in the stream
        with blob.open("r") as stream:
            outputs=[]
            for line in stream:
                # Process each line here
                if len(line) == 0:
                    continue
                else:
                    jdata = json.loads(line)
                    if nlp is None:
                        if jdata.get("response"):
                            x = jdata["response"]["candidates"][0]["content"]["parts"][0]["text"]
                            # print(x)
                            output = json.loads(x.split("\n```")[0].replace("```json\n", ""))
                            outputs.append(output)
                    else:
                        outputs.append(jdata)

            stream.close()
            return outputs
        return None


    def is_marked_blob(self, blob_name:str) -> bool:
        try:
            r = self.sqlcn.marked_blobs.marked_blob_by_name(blob_name)
            if r is not None:
                print(f"Duplicated event has been delivered before, blob: {blob_name}")
                return True
            else:
                self.sqlcn.marked_blobs.create_marked_blob({"blob_name": blob_name})
                print(f"Marked blob: {blob_name} is processing.")
                return False
        except Exception as e:
            print(f"Failed to mark repeated blob name, err: {e}")
            return False


    def http_post(self, url, data):
        try:
            response = requests.post(url, json=data)
        except Exception as e:
            print(f"Failed to post /playbook, with error: {e}")

