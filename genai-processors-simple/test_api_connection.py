#!/usr/bin/env python3
"""Simple test script to validate Google GenAI Live API connection."""

import os
import asyncio
from google.genai import types as genai_types
from genai_processors.core import live_model

# Test API key
API_KEY = os.environ.get('GOOGLE_API_KEY')

async def test_api_connection():
    """Test basic API connection without audio/video streams."""
    if not API_KEY:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        print("Please set it with: export GOOGLE_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ API Key found (first 10 chars): {API_KEY[:10]}...")
    
    try:
        print("🔗 Testing Live API connection...")
        
        # Create a minimal Live processor for testing
        live_processor = live_model.LiveProcessor(
            api_key=API_KEY,
            model_name='gemini-2.0-flash-exp',
            realtime_config=genai_types.LiveConnectConfig(
                system_instruction=["You are a helpful assistant."],
                response_modalities=['TEXT'],  # Use text only for testing
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha'),
        )
        
        print("✅ Live API processor created successfully!")
        print("🎉 Your API key and Live API access are working!")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Live API: {e}")
        print("\n🔍 Troubleshooting steps:")
        print("1. Verify your API key is valid at https://aistudio.google.com/")
        print("2. Check if your API key has Live API access enabled")
        print("3. Try regenerating your API key")
        print("4. Check your internet connection")
        return False

if __name__ == "__main__":
    asyncio.run(test_api_connection()) 