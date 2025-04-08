# Creative GeN/Studio

A powerful media generation application powered by Google's Generative AI models, featuring video and image generation capabilities with a modern web interface.

## Features

- **Video Generation**
  - Text-to-Video generation using Veo 2.0
  - Image-to-Video conversion
  - Customizable aspect ratios and durations
  - Negative prompt support
  - Multiple sample generation

- **Image Generation**
  - Text-to-Image generation using Imagen 3.0
  - Multiple model options
  - Customizable aspect ratios and styles
  - Prompt enhancement options
  - Batch generation support

- **Conversational Editing**
  - Interactive chat interface
  - Multiple response types (image, gallery, video, audio, HTML)
  - Context-aware image generation
  - Real-time feedback

- **Image Analysis**
  - Visual perception analysis
  - Sepia filter preview
  - Model perception comparison

## Prerequisites

- Python 3.12 or higher
- Google Cloud Platform account
- Gemini API key
- Skaffold


## Installation

1. Clone the repository:
```bash
git clone https://github.com/cc4i/awesome-genai.git
cd awesome-genai/media-gen
```

2. Set up Google Cloud credentials:
   - Place your `application_default_credentials.json` in the project root
   - Ensure you have the necessary permissions for Google Cloud Storage

3. Set up [OAuth 2.0](https://support.google.com/googleapi/answer/6158849?hl=en) in [Google Cloud Console](https://console.developers.google.com/).
    - Oauth consent screen
    - Create a client with following settings :
      - Authorised JavaScript origins: http://<Domain of Cloud Run>:8000
      - Authorised redirect URIs: http://<Domain of Cloud Run>:8000/auth & http://<Domain of Cloud Run>:8000/login
    - Notes Client ID and Client Secret

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your API keys and configuration.





4. Install dependencies:
```bash
skaffold run
```


## Usage

1. Start the application:
```bash
python main.py
```

2. Access the web interface at `http://localhost:8000/`

