"""
Video generation utilities using Google's Veo 2.0 model.
"""

import time
import os
import uuid
from typing import Dict, List, Optional, Tuple, Any
import google.auth
import mediapy as media
import requests
from io import BytesIO
import re

import google.auth.transport.requests
from google.cloud import storage

from utils.llm import call_llm
from models.config import VEO_PROJECT_ID, LOCAL_STORAGE, VEO_STORAGE_BUCKET, PROJECT_ID
from models.exceptions import APIError, StorageError, FileUploadError
from utils.logger import logger



# API endpoints
video_model = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{VEO_PROJECT_ID}/locations/us-central1/publishers/google/models/veo-2.0-generate-001"
prediction_endpoint = f"{video_model}:predictLongRunning"
fetch_endpoint = f"{video_model}:fetchPredictOperation"

# Constants
VIDEO_GENERATION_TIMEOUT = 300  # 5 minutes
POLLING_INTERVAL = 10
MAX_RETRIES = 30



def to_snake_case(input_string):
    """
    Converts a string to snake_case, keeping only numbers and letters,
    and replacing everything else with underscores.
    """
    # Replace non-alphanumeric characters with underscores
    s1 = re.sub(r'[^a-zA-Z0-9\.]+', '_', input_string)
    # Remove leading/trailing underscores
    s2 = s1.strip('_')
    # Convert to lowercase
    s3 = s2.lower()
    return s3

def upload_image(input_image_path: str, whoami: str) -> str:
    """
    Upload an image to Google Cloud Storage.
    
    Args:
        input_image_path: Path to the image file
        whoami: User identifier
        
    Returns:
        GCS path of the uploaded file
        
    Raises:
        FileUploadError: If upload fails
    """
    try:
        logger.info(f"Uploading image: {input_image_path} for user: {whoami}")
        return upload_local_file_to_gcs(
            f"{VEO_STORAGE_BUCKET}", 
            f"uploaded-images-for-marketing-short/{whoami}", 
            input_image_path
        )
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise FileUploadError(f"Failed to upload image: {str(e)}")

def send_request_to_google_api(api_endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Sends an HTTP request to a Google API endpoint.

    Args:
        api_endpoint: The URL of the Google API endpoint.
        data: Optional dictionary of data to send in the request body.

    Returns:
        The response from the Google API.

    Raises:
        APIError: If the API request fails.
    """
    try:
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
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise APIError(f"Failed to send request to Google API: {str(e)}")


def compose_videogen_request(
    prompt: str,
    image_uri: Optional[str],
    gcs_uri: str,
    seed: int,
    aspect_ratio: str,
    sample_count: int,
    negative_prompt: str,
    person_generation: str = "allow_adult",
    enhance_prompt: str = "yes",
    duration_seconds: int = 8
) -> Dict[str, Any]:
    """
    Composes a request for video generation.

    Args:
        prompt: Text prompt for video generation
        image_uri: Optional GCS URI of input image
        gcs_uri: GCS URI for output storage
        seed: Random seed for generation
        aspect_ratio: Video aspect ratio
        sample_count: Number of videos to generate
        negative_prompt: Text describing what to avoid
        person_generation: Person generation policy
        enhance_prompt: Whether to enhance the prompt
        duration_seconds: Video duration in seconds

    Returns:
        Dictionary containing the composed request
    """
    
    instance = {"prompt": prompt}
    if image_uri:
        instance["image"] = {"gcsUri": image_uri, "mimeType": "png"}
    
    return {
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

def fetch_operation(lro_name: str, itr: int = MAX_RETRIES) -> Dict[str, Any]:
    """
    Fetches the status of a long-running operation.

    Args:
        lro_name: Name of the long-running operation
        itr: Maximum number of iterations to wait

    Returns:
        Operation response from Google API

    Raises:
        APIError: If the operation fails or times out
    """
    request = {"operationName": lro_name}
    for i in range(itr):
        try:
            resp = send_request_to_google_api(fetch_endpoint, request)
            if "done" in resp and resp["done"]:
                logger.info(f"Operation {lro_name} completed successfully")
                return resp
            time.sleep(POLLING_INTERVAL)
        except APIError as e:
            logger.error(f"Error fetching operation {lro_name}: {str(e)}")
            raise
    
    raise APIError(f"Operation {lro_name} timed out after {itr * POLLING_INTERVAL} seconds")

def text_to_video(
    prompt: str,
    seed: int,
    aspect_ratio: str,
    sample_count: int,
    output_gcs: str,
    negative_prompt: str,
    enhance: str,
    durations: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a video from text using Google's Veo 2.0 model.

    Args:
        prompt: The text prompt describing the video to generate
        seed: Random seed for generation (0-4294967295)
        aspect_ratio: Video aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4)
        sample_count: Number of videos to generate (1-5)
        output_gcs: Google Cloud Storage URI for output
        negative_prompt: Text describing what to avoid in generation
        enhance: Whether to enhance the prompt ("yes" or "no")
        durations: Video duration in seconds (5-8)

    Returns:
        Tuple containing:
        - Operation response from Google API
        - Dictionary containing request and response details

    Raises:
        ValueError: If input parameters are invalid
        APIError: If the API request fails
    """
    logger.info(f"Starting text-to-video generation with prompt: {prompt}")
    req = compose_videogen_request(
        prompt, None, output_gcs, seed, aspect_ratio, sample_count, 
        negative_prompt, "allow_adult", enhance, durations
    )
    resp = send_request_to_google_api(prediction_endpoint, req)
    logger.info(f"Received initial response for operation: {resp}")
    r_resp = fetch_operation(resp["name"])
    return r_resp, {"req": req, "resp": r_resp}

def image_to_video(
    prompt: str,
    image_gcs: str,
    seed: int,
    aspect_ratio: str,
    sample_count: int,
    output_gcs: str,
    negative_prompt: str,
    enhance: str,
    durations: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a video from an image using Google's Veo 2.0 model.

    Args:
        prompt: The text prompt describing the video to generate
        image_gcs: GCS URI of the input image
        seed: Random seed for generation (0-4294967295)
        aspect_ratio: Video aspect ratio (1:1, 9:16, 16:9, 4:3, 3:4)
        sample_count: Number of videos to generate (1-5)
        output_gcs: Google Cloud Storage URI for output
        negative_prompt: Text describing what to avoid in generation
        enhance: Whether to enhance the prompt ("yes" or "no")
        durations: Video duration in seconds (5-8)

    Returns:
        Tuple containing:
        - Operation response from Google API
        - Dictionary containing request and response details

    Raises:
        ValueError: If input parameters are invalid
        APIError: If the API request fails
    """
    logger.info(f"Starting image-to-video generation with prompt: {prompt}")
    req = compose_videogen_request(
        prompt, image_gcs, output_gcs, seed, aspect_ratio, sample_count,
        negative_prompt, "allow_adult", enhance, durations
    )
    logger.debug(f"Composed request: {req}")
    resp = send_request_to_google_api(prediction_endpoint, req)
    logger.info(f"Received initial response for operation: {resp['name']}")
    r_resp = fetch_operation(resp["name"])
    return r_resp, {"req": req, "resp": r_resp}

def copy_gcs_file_to_local(gcs_uri: str, local_file_path: str) -> None:
    """
    Copies a file from Google Cloud Storage to a local file path.

    Args:
        gcs_uri: The GCS URI of the file to copy
        local_file_path: The local file path where the file should be copied

    Raises:
        StorageError: If the file copy operation fails
    """
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_file_path)
        logger.info(f"File {gcs_uri} copied to {local_file_path}")
    except Exception as e:
        logger.error(f"Error copying file: {str(e)}")
        raise StorageError(f"Failed to copy file from GCS: {str(e)}")

def upload_local_file_to_gcs(bucket_name: str, sub_folder: str, local_file_path: str) -> str:
    """
    Uploads a local file to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        sub_folder: Subfolder path in the bucket
        local_file_path: Path to the local file

    Returns:
        The GCS URI of the uploaded file

    Raises:
        StorageError: If the upload operation fails
    """
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(bucket_name)

        blob_name = to_snake_case(local_file_path.split("/")[-1])
        if sub_folder:
            blob_name = f"{sub_folder}/{blob_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"File {local_file_path} uploaded to {gcs_uri}")
        return gcs_uri
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise StorageError(f"Failed to upload file to GCS: {str(e)}")

def download_videos(op: Dict[str, Any], whoami: str, order: str) -> List[str]:
    """
    Downloads generated videos from GCS to local storage.

    Args:
        op: Operation response containing video information
        whoami: User identifier for local storage path

    Returns:
        List of local file paths for downloaded videos

    Raises:
        StorageError: If video download fails
    """
    logger.info("--------------------------------")
    logger.info(f"op: {op}")
    logger.info("--------------------------------")
    logger.info(f"Starting video download for user: {whoami}")
    local_path = f"{LOCAL_STORAGE}/{whoami}"
    logger.info(f"local_path: {local_path}")

    if not os.path.exists(local_path):
        os.makedirs(local_path)
 
    l_files = []
    if op.get("error") is None:
        if op["response"]:
            if op["response"].get("raiMediaFilteredReasons") is None:
                for video in op["response"]["videos"]:
                    gcs_uri = video["gcsUri"]
                    file_name = f"{local_path}/{order}-{str(uuid.uuid4())}-" + gcs_uri.split("/")[-1]
                    try:
                        copy_gcs_file_to_local(gcs_uri, file_name)
                        l_files.append(file_name)
                    except StorageError as e:
                        logger.error(f"Failed to download video: {str(e)}")
                        continue
    return l_files

def random_video_prompt() -> str:
    """
    Generates a random prompt for video generation using LLM.

    Returns:
        A randomly generated prompt string
    """
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt="Generate a random prompt to text-to-image for Google Veo2 to generate a creative, brilliant short video. Output as string only, without explanation.",
        history=""
    )

def rewrite_video_prompt(prompt: str) -> str:
    """
    Rewrites a video prompt to improve its quality using LLM.

    Args:
        prompt: The original prompt to improve

    Returns:
        An improved version of the prompt
    """
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt=f"""
            Rewrite the followng prompt for Google Veo2 to generate the best short video ever. Output as string only, without explanation.

            *PROMPT*: 
            {prompt}
        """,
        history=""
    )
