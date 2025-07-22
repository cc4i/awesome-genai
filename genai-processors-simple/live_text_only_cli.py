#!/usr/bin/env python3
"""Text-only version to test basic Live API functionality."""

import asyncio
import os

from genai_processors.core import live_model
from genai_processors.core import text
from google.genai import types as genai_types

# API key
API_KEY = os.environ['GOOGLE_API_KEY']

INSTRUCTION_PARTS = [
    'You are a helpful assistant. Respond to text input briefly and helpfully.'
]


async def run_text_only() -> None:
    """Test Live API with text input/output only."""
    try:
        print("Creating Live API processor for text-only mode...")
        
        live_processor = live_model.LiveProcessor(
            api_key=API_KEY,
            model_name='gemini-2.0-flash-exp',
            realtime_config=genai_types.LiveConnectConfig(
                system_instruction=INSTRUCTION_PARTS,
                response_modalities=['TEXT'],  # Text only
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha'),
        )
        print("Live API processor created successfully")
        
        # Text input/output only
        live_agent = text.terminal_input() | live_processor | text.terminal_output()
        
        print('Text-only mode. Type messages and press Enter. Use ctrl+D to quit.')
        
        async for part in live_agent:
            print(f"Processing: {part}")
            
    except Exception as e:
        print(f"Error in text-only mode: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    if not API_KEY:
        raise ValueError('GOOGLE_API_KEY environment variable not set')
    
    asyncio.run(run_text_only()) 