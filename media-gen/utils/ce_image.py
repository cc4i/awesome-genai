"""
Image generation utilities using Google's Gemini model.
"""

import os
import logging
import uuid
from typing import Tuple, Optional, Union
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import PIL.Image

from utils.llm import call_llm
from models.config import GEMINI_API_KEY, LOCAL_STORAGE
from models.exceptions import APIError, StorageError

from utils.logger import logger

# Constants
MODEL_ID = "gemini-2.0-flash-exp-image-generation"
MAX_OUTPUT_TOKENS = 8192
TEMPERATURE = 1
TOP_P = 0.95
TOP_K = 40



def generate_image_by_gemini(
    prompt: str,
    last_image: Optional[str],
    whoami: str
) -> Tuple[Union[str, None], str]:
    """
    Generates an image using Google's Gemini model.

    Args:
        prompt: Text prompt for image generation
        last_image: Optional path to previous image for context
        whoami: User identifier for storage path

    Returns:
        Tuple containing:
        - Generated image path or text response
        - Response type ("image" or "text")

    Raises:
        APIError: If the API request fails
        StorageError: If file operations fail
    """
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Prepare content based on whether there's a previous image
        contents = [prompt]
        if last_image:
            contents.append(PIL.Image.open(last_image))

        # Configure generation parameters
        generate_content_config = types.GenerateContentConfig(
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            response_modalities=["image", "text"],
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_CIVIC_INTEGRITY",
                    threshold="OFF",
                ),
            ],
            response_mime_type="text/plain",
        )

        # Generate content
        logger.info(f"Generating image with prompt: {prompt}")
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=generate_content_config
        )

        # Process response
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                logger.info("Received text response")
                return part.text, "text"
            elif part.inline_data is not None:
                try:
                    # Create user storage directory
                    local_storage = Path(LOCAL_STORAGE) / whoami
                    local_storage.mkdir(parents=True, exist_ok=True)
                    
                    # Save generated image
                    generated_image = Image.open(BytesIO(part.inline_data.data))
                    saved_file = local_storage / f"{uuid.uuid4()}-gemini-native-image.png"
                    generated_image.save(saved_file)
                    logger.info(f"Generated image saved to {saved_file}")
                    return str(saved_file), "image"
                except Exception as e:
                    logger.error(f"Error saving generated image: {str(e)}")
                    raise StorageError(f"Failed to save generated image: {str(e)}")

        raise APIError("No valid response received from Gemini API")

    except Exception as e:
        logger.error(f"Error in image generation: {str(e)}")
        raise APIError(f"Failed to generate image: {str(e)}")

def random_image_prompt() -> str:
    """
    Generates a random prompt for image generation using LLM.

    Returns:
        A randomly generated prompt string
    """
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt="""
            Generate a random prompt to text-to-image for Google Imagen 3 to generate a creative, brilliant image for landscapes, or cars, or nature, or technology, etc., which should be breathtaking, a true feast for the eyes.
            *INSTRUCTION*:
            The following elements should be included in your prompt:
                1. Subject: The first thing to think about with any prompt is the subject: the object, person, animal, or scenery you want an image of.
                2. Context and background: Just as important is the background or context in which the subject will be placed. Try placing your subject in a variety of backgrounds. For example, a studio with a white background, outdoors, or indoor environments.

            *OUTPUT*:
            Output as string only, without explanation.
        """,
        history=""
    )

def rewrite_image_prompt(prompt: str) -> str:
    """
    Rewrites an image prompt to improve its quality using LLM.

    Args:
        prompt: The original prompt to improve

    Returns:
        An improved version of the prompt
    """
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt=f"""
            Rewrite the followng prompt for Google Imagen 3 to generate the best image ever. Output as string only, without explanation.

            *PROMPT*: 
            {prompt}
        """,
        history=""
    )