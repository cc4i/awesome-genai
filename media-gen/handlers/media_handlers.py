"""
Handlers for media generation and processing functionality.
"""

import os
from typing import List, Tuple, Dict, Any
from PIL import Image
from io import BytesIO
import gradio as gr

from utils.logger import logger
from utils.gen_image import gen_images
from utils.gen_video import text_to_video, image_to_video, download_videos
from utils.gen_video import upload_local_file_to_gcs
from models.exceptions import FileUploadError, GenerationError, ValidationError
from models.config import (
    VEO_STORAGE_BUCKET,
    MAX_FILE_SIZE,
    ERROR_MESSAGES,
    VIDEO_MODELS,
    IMAGE_MODELS
)

# Global state for temporary files
save_files: List[str] = []

def validate_file_size(file_path: str) -> None:
    """
    Validate that the file size is within limits.
    
    Args:
        file_path: Path to the file to validate
        
    Raises:
        FileUploadError: If file size exceeds maximum allowed size
    """
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise FileUploadError(ERROR_MESSAGES["file_too_large"])

def generate_images(
    model_id: str,
    prompt: str,
    aspect_ratio: str,
    lighting: str,
    style: str,
    sample_count: int,
    is_enhance: bool
) -> List[Image.Image]:
    """
    Generate images using the specified model and parameters.
    
    Args:
        model_id: The ID of the model to use
        prompt: Text prompt for image generation
        aspect_ratio: Desired aspect ratio of the output images
        sample_count: Number of images to generate
        is_enhance: Whether to apply enhancement
        
    Returns:
        List of generated PIL Images
        
    Raises:
        ValueError: If parameters are invalid
        GenerationError: If image generation fails
    """
    try:
        if model_id not in IMAGE_MODELS:
            raise ValueError(f"Invalid model_id: {model_id}")
            
        logger.info(f"Generating images with model {model_id}")
        prompt = f"{prompt}. Lighting: {lighting}. Style: {style}."
        generated_images = gen_images(
            model_id=model_id,
            prompt=prompt,
            negative_prompt="",
            number_of_images=sample_count,
            aspect_ratio=aspect_ratio,
            is_enhance=is_enhance
        )
        
        logger.info(f"Successfully generated {len(generated_images)} images")
        return [
            Image.open(BytesIO(generated_image.image.image_bytes))
            for generated_image in generated_images
        ]
    except Exception as e:
        logger.error(f"Failed to generate images: {str(e)}")
        raise GenerationError(f"Image generation failed: {str(e)}")

def show(input_image: Image.Image) -> Image.Image:
    """
    Return the input image as is.
    
    Args:
        input_image: Input PIL Image
        
    Returns:
        The same input image
    """
    return input_image

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
        validate_file_size(input_image_path)
        return upload_local_file_to_gcs(
            f"{VEO_STORAGE_BUCKET}", 
            f"uploaded-images/{whoami}", 
            input_image_path
        )
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise FileUploadError(f"Failed to upload image: {str(e)}")

def generate_videos(
    whoami: str,
    file_in_gcs: str,
    prompt: str,
    negative_prompt: str,
    type: str,
    aspect_ratio: str,
    seed: str,
    sample_count: int,
    enhance: bool,
    durations: int,
    loop_seamless: bool
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate videos using either text or image input.
    
    Args:
        whoami: User identifier
        file_in_gcs: GCS path of input image (for image-to-video)
        prompt: Text prompt for generation
        negative_prompt: Negative prompt for generation
        type: Type of video generation ("Text-to-Video" or "Image-to-Video")
        aspect_ratio: Video aspect ratio
        seed: Random seed for generation (as string from UI)
        sample_count: Number of videos to generate
        enhance: Whether to apply enhancement
        durations: Duration of each video in seconds
        
    Returns:
        Tuple of (list of video paths, response metadata)
        
    Raises:
        GenerationError: If video generation fails
    """
    try:
            
        output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated"
        
        if type == "Text-to-Video":
            op, rr = text_to_video(
                prompt=prompt,
                seed=int(seed),
                aspect_ratio=aspect_ratio,
                sample_count=int(sample_count),
                output_gcs=output_gcs,
                negative_prompt=negative_prompt,
                enhance=enhance,
                durations=int(durations)
            )
            return download_videos(op, whoami, loop_seamless), rr
        else:
            print(f"first image in the gcs: {file_in_gcs}")
            op, rr = image_to_video(
                prompt=prompt,
                image_gcs=file_in_gcs,
                seed=int(   seed),
                aspect_ratio=aspect_ratio,
                sample_count=int(sample_count),
                output_gcs=output_gcs,
                negative_prompt=negative_prompt,
                enhance=enhance,
                durations=int(durations)
            )
            return download_videos(op, whoami, loop_seamless), rr
    except Exception as e:
        logger.error(f"Failed to generate videos: {str(e)}")
        raise GenerationError(f"Video generation failed: {str(e)}")

def delete_temp_files(whoami: str) -> None:
    """
    Delete temporary files for a specific user.
    
    Args:
        whoami: User identifier
        
    Raises:
        RuntimeError: If file deletion fails
    """
    try:
        for s_file in save_files:
            if os.path.exists(s_file):
                logger.info(f"Deleting temporary file: {s_file}")
                os.remove(s_file)
                save_files.remove(s_file)
                
        local_path = os.path.join(os.getenv("LOCAL_STORAGE", "tmp"), whoami)
        if os.path.exists(local_path):
            logger.info(f"Deleting temporary directory: {local_path}")
            os.system(f"rm -rf {local_path}/*")
    except Exception as e:
        logger.error(f"Failed to delete temporary files: {str(e)}")
        raise RuntimeError(f"Failed to delete temporary files: {str(e)}") 