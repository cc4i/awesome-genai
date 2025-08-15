import os
from typing import List, Tuple, Dict, Any
from io import BytesIO
from PIL import Image as PILImage
from google import genai
from google.genai.types import (
    GenerateImagesConfig,
    Image,
    ProductImage,
    RecontextImageConfig,
    RecontextImageSource,
)

from models.exceptions import APIError, StorageError
from utils.logger import logger

PROJECT_ID = os.environ.get("PROJECT_ID", "multi-gke-ops")
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
VTO_MODEL_ID = os.environ.get("VTO_MODEL_ID", "virtual-try-on-preview-08-04")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


def gen_images(person_image, product_image, number_of_images, vto_model_id=VTO_MODEL_ID)->List[PILImage.Image]:

    # person_generation:
    #     DONT_ALLOW
    #     ALLOW_ADULT
    #     ALLOW_ALL
    # safety_filter_level:
    #     BLOCK_LOW_AND_ABOVE
    #     BLOCK_MEDIUM_AND_ABOVE
    #     BLOCK_ONLY_HIGH
    #     BLOCK_NONE

    print(f"person_image: {person_image}, product_image: {product_image}, number_of_images: {number_of_images}, vto_model_id: {vto_model_id}")
    print(type(person_image), type(product_image))
    response = client.models.recontext_image(
        model=vto_model_id,
        source=RecontextImageSource(
            person_image=Image.from_file(location=person_image),
            product_images=[
                ProductImage(product_image=Image.from_file(location=product_image))
            ],
        ),
        config=RecontextImageConfig(
            base_steps=32,
            number_of_images=number_of_images,
            safety_filter_level="BLOCK_ONLY_HIGH",
            person_generation="ALLOW_ADULT",
        ),
    )
    return [PILImage.open(BytesIO(generated_image.image.image_bytes)) for generated_image in response.generated_images]
    # response.generated_images