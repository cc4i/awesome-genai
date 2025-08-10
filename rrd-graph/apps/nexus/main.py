from typing import Union
from fastapi import FastAPI,Request

import time
import os
import requests
from google.cloud import run_v2
from utils.job import RunJob, retrieve_run_metadata
from utils.ctl_request import JobRequest

# FastAPI 
fapp = FastAPI()


@fapp.get("/")
def index():
    return {"ok": True, "message": "It's a RRD Nexus"}



@fapp.get("/job/{thread_id}/{platform_id}")
def query_job(thread_id: str, platform_id: str):
    """
    Check job status by thread_id and platform_id.
    """
    image=os.environ["RRD_JOB_IMAGE"] or "us-docker.pkg.dev/cloudrun/container/job:latest"

    rubJob = RunJob(
           thread_id = thread_id, 
           platform_id=platform_id, 
           image=image 
          )
    return rubJob.check_job_status()


@fapp.post("/job")
def provision_job(jreq: JobRequest, q: str | None = None):
    """
    Creates a Cloud Run Job for scraping, load generator, etc.
    """
    # Parse POST body
    thread_id = jreq.thread_id
    platform_ids = jreq.platform_ids
    image=jreq.image
    print(f"thread_id: {thread_id}, platform_ids: {platform_ids}, image: {image}")

    # Create jobs and triggers
    jobs=[]
    triggers=[]
    if platform_ids:
       for pid in platform_ids:
         if pid.startswith("google-"):
           job_interval = "0 */2 * * *"
         else:
           job_interval = "*/10 * * *"
         rubJob = RunJob(
           thread_id = thread_id, 
           platform_id=pid, 
           image=image, 
           interval=job_interval,
          )
         jb= rubJob.create_rubjob()
         if jb is not None:
          jobs.append(jb)
          time.sleep(2)
          tg = rubJob.create_trigger()
          if tg is not None:
            triggers.append(tg)
          else:
            return {"failed": "to create trigger"}
         else:
           return {"failed": "to create scraping-job"}

    return {"thread_id": thread_id, "jobs": jobs, "triggers": tg}


@fapp.get("/loadgen")
async def check_loadgen():
  project_id=retrieve_run_metadata("project/project-id")
  location=retrieve_run_metadata("instance/region").split("/")[3]
  print(f"project_id: {project_id}, location: {location}")
  try:
    client = run_v2.JobsClient()
    request = run_v2.GetJobRequest(
        name=f"projects/{project_id}/locations/{location}/jobs/loadgen-job",
    )
    response = client.get_job(request=request)
    # print(response)
  except Exception as e:
    print(f"check_loadgen error: {e}")
    return None
  return {
    "name": response.name,
    "create_time": response.create_time,
    "update_time": response.update_time,
    "creator": response.creator
  }