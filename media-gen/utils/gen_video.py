import time
import os

import google.auth
import google.auth.transport.requests
import mediapy as media
import requests
from google.cloud import storage
from io import BytesIO

PROJECT_ID=os.getenv("VEO_PROJECT_ID")

video_model = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/us-central1/publishers/google/models/veo-2.0-generate-001"
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
    return fetch_operation(resp["name"],30), {"req":req, "resp":resp}


def image_to_video(
    prompt, image_gcs, seed, aspect_ratio, sample_count, output_gcs, negative_prompt, enhance, durations
):
    req = compose_videogen_request(
        prompt, image_gcs, output_gcs, seed, aspect_ratio, sample_count, negative_prompt, "allow_adult", enhance, durations
    )
    print(f"image_to_video: \n{req}")
    resp = send_request_to_google_api(prediction_endpoint, req)
    print(resp)
    return fetch_operation(resp["name"], 30), {"req":req, "resp":resp}


# copy file from gcs to local file using python sdk
def copy_gcs_file_to_local(gcs_uri, local_file_path):
    """Copies a file from Google Cloud Storage to a local file path.

    Args:
        gcs_uri: The GCS URI of the file to copy (e.g., "gs://bucket-name/path/to/file.txt").
        local_file_path: The local file path where the file should be copied.
    """

    try:
        client = storage.Client()
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
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        local_file_path.split("/")
        blob_name = local_file_path.split("/")[-1]
        if sub_folder:
            blob_name = f"{sub_folder}/{blob_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        print(f"File {local_file_path} uploaded to gs://{bucket_name}/{blob_name}.")
        return f"gs://{bucket_name}/{blob_name}"
    except Exception as e:
        print(f"Error uploading file: {e}")



def download_videos(op):
    print(op)
    # create 'tmp' folder if not exist
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
 
    l_files=[]
    if op["response"]:
        for video in op["response"]["videos"]:
            gcs_uri = video["gcsUri"]
            file_name = "tmp/" + gcs_uri.split("/")[-1]
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
            file_name = "tmp/" + gcs_uri.split("/")[-1]
            # !gsutil cp {gcs_uri} {file_name}
            copy_gcs_file_to_local(gcs_uri, file_name)
            media.show_video(media.read_video(file_name), height=500)