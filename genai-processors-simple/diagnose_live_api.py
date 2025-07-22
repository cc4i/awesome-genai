#!/usr/bin/env python3
"""Comprehensive diagnosis script for Live API issues."""

import asyncio
import os
import sys

from google.genai import types as genai_types
from genai_processors.core import live_model

API_KEY = os.environ.get('GOOGLE_API_KEY')

async def test_basic_connection():
    """Test 1: Basic API connection"""
    print("🔍 Test 1: Basic API connection")
    try:
        live_processor = live_model.LiveProcessor(
            api_key=API_KEY,
            model_name='gemini-2.0-flash-exp',
            realtime_config=genai_types.LiveConnectConfig(
                system_instruction=["You are a helpful assistant."],
                response_modalities=['TEXT'],
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha'),
        )
        print("✅ Basic connection successful")
        return True
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        return False


async def test_audio_response():
    """Test 2: Audio response capability"""
    print("\n🔍 Test 2: Audio response capability")
    try:
        live_processor = live_model.LiveProcessor(
            api_key=API_KEY,
            model_name='gemini-2.0-flash-exp',
            realtime_config=genai_types.LiveConnectConfig(
                system_instruction=["You are a helpful assistant."],
                response_modalities=['AUDIO'],
                speech_config={'language_code': 'en-US'},
            ),
            http_options=genai_types.HttpOptions(api_version='v1alpha'),
        )
        print("✅ Audio response capability successful")
        return True
    except Exception as e:
        print(f"❌ Audio response capability failed: {e}")
        return False


async def test_different_models():
    """Test 3: Different model compatibility"""
    print("\n🔍 Test 3: Testing different models")
    
    models_to_test = [
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.5-flash-preview-native-audio-dialog'
    ]
    
    working_models = []
    
    for model in models_to_test:
        try:
            live_processor = live_model.LiveProcessor(
                api_key=API_KEY,
                model_name=model,
                realtime_config=genai_types.LiveConnectConfig(
                    system_instruction=["You are a helpful assistant."],
                    response_modalities=['TEXT'],
                ),
                http_options=genai_types.HttpOptions(api_version='v1alpha'),
            )
            print(f"✅ {model} works")
            working_models.append(model)
        except Exception as e:
            print(f"❌ {model} failed: {e}")
    
    return working_models


async def test_audio_models():
    """Test 4: Audio-capable models"""
    print("\n🔍 Test 4: Testing audio-capable models")
    
    models_to_test = [
        'gemini-2.0-flash-exp',
        'gemini-2.5-flash-preview-native-audio-dialog'
    ]
    
    working_audio_models = []
    
    for model in models_to_test:
        try:
            live_processor = live_model.LiveProcessor(
                api_key=API_KEY,
                model_name=model,
                realtime_config=genai_types.LiveConnectConfig(
                    system_instruction=["You are a helpful assistant."],
                    response_modalities=['AUDIO'],
                    speech_config={'language_code': 'en-US'},
                ),
                http_options=genai_types.HttpOptions(api_version='v1alpha'),
            )
            print(f"✅ {model} supports audio")
            working_audio_models.append(model)
        except Exception as e:
            print(f"❌ {model} audio failed: {e}")
    
    return working_audio_models


async def main():
    """Run all diagnostic tests"""
    print("🚀 Starting Live API Diagnosis")
    print("=" * 50)
    
    if not API_KEY:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        sys.exit(1)
    
    print(f"✅ API Key found (first 10 chars): {API_KEY[:10]}...")
    
    # Run tests
    basic_ok = await test_basic_connection()
    if not basic_ok:
        print("\n❌ Basic connection failed. Check your API key and network.")
        sys.exit(1)
    
    audio_ok = await test_audio_response()
    working_models = await test_different_models()
    working_audio_models = await test_audio_models()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    print(f"Basic API Access: {'✅ Working' if basic_ok else '❌ Failed'}")
    print(f"Audio Response: {'✅ Working' if audio_ok else '❌ Failed'}")
    print(f"Working Models: {working_models}")
    print(f"Audio-capable Models: {working_audio_models}")
    
    if not audio_ok:
        print("\n🔍 RECOMMENDATIONS:")
        print("- Your API key may not have Live API audio access")
        print("- Try using text-only mode first")
        print("- Contact Google support for Live API access")
    elif len(working_audio_models) > 0:
        print(f"\n✅ RECOMMENDED MODEL: {working_audio_models[0]}")
        print("The audio streaming issue might be with:")
        print("- Camera/video stream format")
        print("- Audio encoding (PCM vs L16)")
        print("- macOS permissions for microphone/camera")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Try the text-only version: python live_text_only_cli.py")
    print("2. Try the audio-only version: python live_audio_only_cli.py")
    print("3. Check macOS permissions for camera/microphone")


if __name__ == '__main__':
    asyncio.run(main()) 