import time
import os
import uuid
import google.auth
import google.auth.transport.requests
import mediapy as media
import requests
from google.cloud import storage
from io import BytesIO

from utils.llm import call_llm
from models.config import VEO_PROJECT_ID, LOCAL_STORAGE
from utils.acceptance import to_snake_case




video_model = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{VEO_PROJECT_ID}/locations/us-central1/publishers/google/models/veo-2.0-generate-001"
prediction_endpoint = f"{video_model}:predictLongRunning"
fetch_endpoint = f"{video_model}:fetchPredictOperation"

def send_request_to_google_api(api_endpoint, data=None):
    """
    Sends an HTTP request to a Google API endpoint.

    Args:
        api_endpoint: The URL of the Google API endpoint.
        data: (Optional) Dictionary of data to send in the request body (for POST, PUT, etc.).

    Returns:
        The response from the Google API.
    """

    # Get access token calling API
    creds, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    access_token = creds.token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(api_endpoint, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def compose_videogen_request(
    prompt,
    image_uri,
    gcs_uri,
    seed,
    aspect_ratio,
    sample_count,
    negative_prompt,
    person_generation="allow_adult",
    enhance_prompt="yes", # "no"
    duration_seconds = 8
):
    instance = {"prompt": prompt}
    if image_uri:
        instance["image"] = {"gcsUri": image_uri, "mimeType": "png"}
    request = {
        "instances": [instance],
        "parameters": {
            "storageUri": gcs_uri,
            "sampleCount": sample_count,
            "seed": seed,
            "aspectRatio": aspect_ratio,
            "negativePrompt": negative_prompt,
            "personGeneration": person_generation,
            "enhancePrompt": enhance_prompt,
            "durationSeconds": duration_seconds
        },
    }
    return request


def fetch_operation(lro_name,itr):
    request = {"operationName": lro_name}
    # The generation usually takes 2 minutes. Loop 30 times, around 5 minutes.
    for i in range(itr):
        resp = send_request_to_google_api(fetch_endpoint, request)
        if "done" in resp and resp["done"]:
            print(resp)
            return resp
        #print(resp)
        time.sleep(10)



def print_ops(lro_name,itr):
    request = {"operationName": lro_name}
    # The generation usually takes 2 minutes. Loop 30 times, around 5 minutes.
    resp = send_request_to_google_api(fetch_endpoint, request)
    #print(resp)
    return resp

def text_to_video(prompt, seed, aspect_ratio, sample_count, output_gcs, negative_prompt, enhance, durations):
    req = compose_videogen_request(
        prompt, None, output_gcs, seed, aspect_ratio, sample_count, negative_prompt, "allow_adult", enhance, durations
    )
    resp = send_request_to_google_api(prediction_endpoint, req)
    print(resp)
    print(resp["name"])
    r_resp = fetch_operation(resp["name"],30)
    return r_resp, {"req":req, "resp":r_resp}


def image_to_video(
    prompt, image_gcs, seed, aspect_ratio, sample_count, output_gcs, negative_prompt, enhance, durations
):
    req = compose_videogen_request(
        prompt, image_gcs, output_gcs, seed, aspect_ratio, sample_count, negative_prompt, "allow_adult", enhance, durations
    )
    print(f"image_to_video: \n{req}")
    resp = send_request_to_google_api(prediction_endpoint, req)
    print(resp)
    r_resp = fetch_operation(resp["name"],30)
    return r_resp, {"req":req, "resp":r_resp}


# copy file from gcs to local file using python sdk
def copy_gcs_file_to_local(gcs_uri, local_file_path):
    """Copies a file from Google Cloud Storage to a local file path.

    Args:
        gcs_uri: The GCS URI of the file to copy (e.g., "gs://bucket-name/path/to/file.txt").
        local_file_path: The local file path where the file should be copied.
    """

    try:
        client = storage.Client(project=os.getenv("PROJECT_ID"))
        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_file_path)
        print(f"File {gcs_uri} copied to {local_file_path}.")
    except Exception as e:
        print(f"Error copying file: {e}")

# upload a local file to gcs
def upload_local_file_to_gcs(bucket_name, sub_folder, local_file_path):
    try:
        client = storage.Client(project=os.getenv("PROJECT_ID"))
        bucket = client.bucket(bucket_name)

        local_file_path.split("/")
        blob_name = to_snake_case(local_file_path.split("/")[-1])
        if sub_folder:
            blob_name = f"{sub_folder}/{blob_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        print(f"File {local_file_path} uploaded to gs://{bucket_name}/{blob_name}.")
        return f"gs://{bucket_name}/{blob_name}"
    except Exception as e:
        print(f"Error uploading file: {e}")



def download_videos(op, whoami):
    print(op)
    local_path = f"{LOCAL_STORAGE}/{whoami}"
    # create 'tmp' folder if not exist
    if not os.path.exists(local_path):
        os.makedirs(local_path)
 
    l_files=[]
    if op["response"]:
        if op["response"].get("raiMediaFilteredReasons") is None:
            for video in op["response"]["videos"]:
                gcs_uri = video["gcsUri"]
                file_name = f"{local_path}/{str(uuid.uuid4())}-" + gcs_uri.split("/")[-1]
                # !gsutil cp {gcs_uri} {file_name}
                copy_gcs_file_to_local(gcs_uri, file_name)
                l_files.append(file_name)
    return l_files

def show_sdk_video(op):
    print(op)
    # create 'tmp' folder if not exist
    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    if op.generate_videos_response.videos:
        for video in op.generate_videos_response.videos:
            gcs_uri = video.uri
            file_name = f"{LOCAL_STORAGE}/" + gcs_uri.split("/")[-1]
            # !gsutil cp {gcs_uri} {file_name}
            copy_gcs_file_to_local(gcs_uri, file_name)
            media.show_video(media.read_video(file_name), height=500)


def random_video_prompt():
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt="Generate a random prompt to text-to-image for Google Veo2 to generate a creative, brilliant short video. Output as string only, without explanation.",
        history=""
    )

def rewrite_video_prompt(prompt):
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt=f"""
            Rewrite the followng prompt for Google Veo2 to generate the best short video ever. Output as string only, without explanation.

            *PROMPT*: 
            {prompt}
        """,
        history=""
    )
