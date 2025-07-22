#!/usr/bin/env python3
"""Audio-only version to isolate the video stream issue."""

import argparse
import asyncio
import os

from absl import logging
from genai_processors.core import audio_io
from genai_processors.core import live_model
from genai_processors.core import text
from google.genai import types as genai_types
import pyaudio

# You need to define the API key in the environment variables.
API_KEY = os.environ['GOOGLE_API_KEY']

INSTRUCTION_PARTS = [
    'You are a helpful assistant. Respond briefly and naturally to what you hear.'
]


async def run_audio_only() -> None:
    """Runs a simple live agent with audio input only (no video)."""
    try:
        pya = pyaudio.PyAudio()
        print("PyAudio initialized successfully")
        
        # Audio input only - no video
        input_processor = audio_io.PyAudioIn(pya, use_pcm_mimetype=True)
        print("Audio input processor created successfully")
        
        # Create Live API processor
        print("Creating Live API processor...")
        live_processor = live_model.LiveProcessor(
            api_key=API_KEY,
            model_name='gemini-2.0-flash-exp',
            realtime_config=genai_types.LiveConnectConfig(
                system_instruction=INSTRUCTION_PARTS,
                response_modalities=['AUDIO'],
                speech_config={'language_code': 'en-US'},
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha'),
        )
        print("Live API processor created successfully")
        
        # Audio output
        play_output = audio_io.PyAudioOut(pya)
        
        # Creates an agent as: mic -> Live API -> play audio
        live_agent = input_processor + live_processor + play_output
        
        print('Audio-only mode. Use ctrl+D to quit.')
        print('Say something...')
        
        async for part in live_agent(text.terminal_input()):
            print(f"Response part: {part}")
            
    except Exception as e:
        print(f"Error in audio-only mode: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging.',
    )
    args = parser.parse_args()
    
    if not API_KEY:
        raise ValueError(
            'API key is not set. Define a GOOGLE_API_KEY environment variable'
        )
    
    if args.debug:
        logging.set_verbosity(logging.DEBUG)
    
    asyncio.run(run_audio_only()) 