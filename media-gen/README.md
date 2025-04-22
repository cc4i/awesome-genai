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

2. Grant permissions to service account
```bash
# Get project number
PROJECT_ID=<YOUR_PROJECT_ID>
PROJECT_NUMBER=$(gcloud projects list --filter="name:${PROJECT_ID}" --format="value(PROJECT_NUMBER)")

# Grant permission
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/iam.serviceAccountUser

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectAdmin
  
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/aiplatform.user
```

3. Create a API key in [Google AI Studio](https://aistudio.google.com/app/apikey)

4. Set up [OAuth 2.0](https://support.google.com/googleapi/answer/6158849?hl=en) in [Google Cloud Console](https://console.developers.google.com/).
    - Oauth consent screen
    - Create a client with following settings :
      - Authorised JavaScript origins: https://<DOMAIN-OF-CLOUD-RUN>
      - Authorised redirect URIs: 
        - https://<DOMAIN-OF-CLOUD-RUN>/auth 
        - https://<DOMAIN-OF-CLOUD-RUN>/login
    - Notes Client ID and Client Secret

5. Create datastore to store user sessions
```bash
gcloud firestore databases create \
    --location=nam5 \
    --type=datastore-mode
```
6. Configure environment variables in `quickstart.sh`

7. Deploy the application.
```bash
./quickstart.sh
```


## Usage

```bash
# Get the URL of Cloud Run
gcloud run services describe media-gen --region=us-central1 --format="value(status.url)"

# Access the web interface in Mac
open `gcloud run services describe media-gen --region=us-central1 --format="value(status.url)"`
```


