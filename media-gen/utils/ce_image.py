import os

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import io
import uuid
import PIL.Image
from utils.llm import call_llm


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()


def generate_image_by_gemini(prompt, last_image):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model_id = "gemini-2.0-flash-exp-image-generation"
    if last_image is None:
        contents = [prompt]
    else:
        contents = [
            prompt,
            PIL.Image.open(last_image)
        ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_modalities=[
            "image",
            "text",
        ],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="OFF",  # Off
            ),
        ],
        response_mime_type="text/plain",
    )

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=generate_content_config
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
            return part.text, "text"
        elif part.inline_data is not None:
            generated_image = Image.open(BytesIO((part.inline_data.data)))
            local_storage = os.getenv("LOCAL_STORAGE")
            print(f"local_storage: {local_storage}")
            saved_file = f"{local_storage}/{str(uuid.uuid4())}-gemini-native-image.png"
            generated_image.save(saved_file)
            return saved_file, "image"
            # image.save('gemini-native-image.png')
            # image.show()
    

def random_image_prompt():
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt="Generate a random prompt to text-to-image for Google Imagen 3 to generate a creative, brilliant image. Output as string only, without explanation.",
        history=""
    )

def rewrite_image_prompt(prompt):
    return call_llm(
        system_instruction="You're prompt engineer, your task is to create a best prompt for specific model from Google.",
        prompt=f"""
            Rewrite the followng prompt for Google Imagen 3 to generate the best image ever. Output as string only, without explanation.

            *PROMPT*: 
            {prompt}
        """,
        history=""
    )