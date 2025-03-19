import datetime
import requests

from google.cloud import run_v2
from google.cloud import scheduler_v1



# Function to get metadata from Runtime
def retrieve_run_metadata(metadata_path):
    """
    Retrieves metadata from the Cloud Run Job environment.

    Args:
        metadata_path: The path to the metadata value.

    Returns:
        The metadata value as a string, or None if not found.
    """
    try:
        response = requests.get(
            f"http://metadata.google.internal/computeMetadata/v1/{metadata_path}",
            headers={"Metadata-Flavor": "Google"},
            timeout=5,
        )
        response.raise_for_status()  # Raise an exception for error responses
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error getting metadata: {e}")
        return None


class RunJob:
    def __init__(self, thread_id, platform_id, image, entrypoint=None, interval="*/10 * * * *", max_retries=None, model_id=None):

        # Retrieve metadata
        self.project_id=retrieve_run_metadata("project/project-id") or "play-dev-ops"
        self.project_number=retrieve_run_metadata("project/numeric-project-id") or "685974231709"
        if retrieve_run_metadata("instance/region"):
            self.location=retrieve_run_metadata("instance/region").split("/")[3] 
        else:
            self.location="us-central1"

        self.job_id = f"scraping-job-{thread_id}-{platform_id}"
        self.thread_id = thread_id
        self.platform_id = platform_id
        self.image = image
        self.sa_email = retrieve_run_metadata("instance/service-accounts/default/email")
        self.entrypoint = entrypoint
        self.interval = interval
        self.max_retries = max_retries
        self.model_id = model_id





    def check_job_status(self):
        client = run_v2.JobsClient()
        request = run_v2.GetJobRequest(
            name=f"projects/{self.project_id}/locations/{self.location}/jobs/{self.job_id}",
        )
        response = client.get_job(request=request)
        return response


    # https://cloud.google.com/python/docs/reference/cloudscheduler/latest/google.cloud.scheduler_v1.services.cloud_scheduler
    def create_trigger(self):
        client = scheduler_v1.CloudSchedulerClient()
        parent = f"projects/{self.project_id}/locations/{self.location}"
        job_path = f"https://{self.location}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/{self.project_id}/jobs/{self.job_id}:run"
        trigger = scheduler_v1.Job({
                "name": f"{parent}/jobs/trigger-{self.job_id}",
                "schedule": self.interval,
                "time_zone": "Asia/Singapore",
                "http_target": {
                    "http_method": scheduler_v1.HttpMethod.POST,
                    "uri": job_path,
                    "oauth_token": {
                        "service_account_email": self.sa_email,
                        "scope": "https://www.googleapis.com/auth/cloud-platform"
                    },
                },
            })

        try:
            # Send the request to create the trigger
            response = client.create_job(request={"parent": parent, "job": trigger})
            # Print the trigger
            print(f"Created trigger: {response.name}")
            return response.name
        except Exception as e:
            print(e)
            return None


    # https://cloud.google.com/python/docs/reference/run/latest/google.cloud.run_v2.services.jobs.JobsClient
    def create_rub_job(self):
        """Creates a Cloud Run job."""
        client = run_v2.JobsClient()
        parent = f"projects/{self.project_id}/locations/{self.location}"
    
        # opt = os.getenv("JOB_OPTION") or "twitter"
        # job_id = os.getenv("JOB_ID") or "10001"
        # project_id = os.getenv("PROJECT_ID") or "play-dev-ops"
        # location = os.getenv("LOCATION") or "us-central1"
        job = run_v2.Job(
            {
                # "name": f"projects/{project_id}/locations/{location}/jobs/{job_id}",
                "template": run_v2.ExecutionTemplate({
                    "template": run_v2.TaskTemplate({
                        "timeout": "900s",
                        "containers": [
                            run_v2.Container({
                                "name": "hello",
                                "image": self.image,
                                # "command": entrypoint,
                                "env": [
                                    # run_v2.EnvVar({
                                    #     "name": "TZ",
                                    #     "value": "Asia/Singapore"
                                    # }),
                                    run_v2.EnvVar({
                                        "name": "PROJECT_ID",
                                        "value": self.project_id
                                    }),
                                    run_v2.EnvVar({
                                        "name": "LOCATION",
                                        "value": self.location
                                    }),
                                    run_v2.EnvVar({
                                        "name": "ANALYSIS_SERVICE",
                                        "value": "analysis-service"
                                    }),
                                    run_v2.EnvVar({
                                        "name": "PLATFORM_ID",
                                        "value": self.platform_id
                                    }),
                                    run_v2.EnvVar({
                                        "name": "THREAD_ID",
                                        "value": self.thread_id
                                    }),
                                ],
                                "resources": run_v2.ResourceRequirements({
                                    "limits": {
                                        "cpu": "1",
                                        "memory": "2Gi"
                                    },
                                    "startup_cpu_boost": True,
                                })
                            })
                        ],
                    })
                })
            }
        )

        jobReq = run_v2.CreateJobRequest({
            "parent": parent,
            "job_id": self.job_id,
            "job": job
        })
        try:
            ref= client.create_job(jobReq)
            print(ref.result())
            return self.job_id
        except Exception as e:
            print(e)
            return None

