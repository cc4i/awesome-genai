import asyncio
import json
from google import genai
from google.genai import types
from models.config import DEFAULT_MODEL_ID, GEMINI_API_KEY

def string_to_pjson(json_string: str) -> str:
    try:
        # Remove the ```json and ``` markers
        json_str = json_string.strip().replace("```json", "").replace(" ```json", "").replace("```JSON", "").replace("``` JSON", "").replace("```", "")
        return json_str
    except json.JSONDecodeError:
        print("Invalid JSON string")
        return None
    
def call_llm(system_instruction, prompt, history, model_id=DEFAULT_MODEL_ID):
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=65536,
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_CIVIC_INTEGRITY",
                threshold="OFF",  # Off
            ),
        ],
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text=system_instruction),
        ],
    )
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    response = client.models.generate_content(model=model_id, contents=contents, config=generate_content_config)
    return string_to_pjson(response.text)



