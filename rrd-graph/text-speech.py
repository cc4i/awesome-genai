#!/usr/bin/env python
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Google Cloud Text-To-Speech API sample application .

Example usage:
    python synthesize_text.py --text "hello"
    python synthesize_text.py --ssml "<speak>Hello there.</speak>"
"""

import argparse


# Function to upload file into into GCS bucket
def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    from google.cloud import storage

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )


# [START tts_synthesize_text]
def synthesize_text(text):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    # text = "Hello there."
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    from pydub import AudioSegment
    from pydub.playback import play
    # import time
    import io
    print(f"type of response.audio_content -> {type(response.audio_content)}, len -> {len(response.audio_content)}")
    # time.sleep(2)
   
    song = AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")
    play(song)
    # The response's audio_content is binary.
    # with open("output.mp3", "wb") as out:
    #     out.write(response.audio_content)
    #     print('Audio content written to file "output.mp3"')


# [END tts_synthesize_text]


# [START tts_synthesize_ssml]
def synthesize_ssml():
    """Synthesizes speech from the input string of ssml.

    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/

    """
    from google.cloud import texttospeech

    ssml = "<speak>Hello there.</speak>"
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(ssml=ssml)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')


# [END tts_synthesize_ssml]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="The text from which to synthesize speech.")
    group.add_argument(
        "--ssml", help="The ssml string from which to synthesize speech."
    )

    args = parser.parse_args()

    print(f"args.text -> {args.text}")

    if args.text:
        synthesize_text(args.text)
    else:
        synthesize_ssml(args.ssml)