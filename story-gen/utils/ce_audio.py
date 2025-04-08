import base64
import os
import mimetypes
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from models.config import GEMINI_API_KEY
import random
import time
female_voices = [
    "Zephyr",
    "Kore",
    "Leda",
    "Aoede",
]

male_voices = [
    "Puck",
    "Charon",
    "Fenrir",
    "Orus"
]

def choose_random_voice(gender):
    if gender == "female":
        voice_name = female_voices[random.randint(0, len(female_voices) - 1)]
    else:
        voice_name = male_voices[random.randint(0, len(male_voices) - 1)]
    return voice_name

def save_binary_file(file_name, data):
    file_path = f"tmp/default/{file_name}"
    f = open(file_path, "wb")
    f.write(data)
    f.close()
    return file_path


def generate_audio_by_gemini(message, gender, order, character_name, start_time, voice_name, model_id="gemini-2.0-flash-exp"):
    client = genai.Client(
        vertexai=True, project="cloud-llm-preview3", location="us-central1"
    )
    model = model_id
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=message),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name))),
    )

    try:
        response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config
            )
    except ClientError as e:
        print(f"Error generating audio: {e}, retry...")
        if e.code == 429:
            print("Rate limit exceeded")
            # Incremental and max 10 retry
            for i in range(10):
                time.sleep(6 * (i + 1))
                return generate_audio_by_gemini(message, gender, order, character_name, start_time, model_id)

    try:
        if response.candidates[0].content.parts is not None:
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print("Received text response")
                    return part.text
                elif part.inline_data is not None:
                    file_name = f"{order}-{character_name}-{start_time}.wav"
                    file_path = save_binary_file(
                        file_name, part.inline_data.data
                    )
                    return file_path
    except UnboundLocalError as e:
        print(f"Repose from Gemini is None, {e}, retry...")
        for i in range(10):
            time.sleep(6 * (i + 1))
            return generate_audio_by_gemini(message, gender, order, character_name, start_time, model_id)

    