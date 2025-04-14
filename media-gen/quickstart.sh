#!/bin/bash

# Fill following variables as your environment
#
# Gemini API key
export GEMINI_API_KEY=""

# VEO project ID
export VEO_PROJECT_ID=""
# VEO storage bucket for generated videos
export VEO_STORAGE_BUCKET=""

# Local storage
export LOCAL_STORAGE="tmp"

# Default model ID
export DEFAULT_MODEL_ID="gemini-2.0-flash"

# Default credential for GCP
export PROJECT_ID=""

# Google client ID and secret for OAuth
export GOOGLE_CLIENT_ID=""
export GOOGLE_CLIENT_SECRET=""

# Development mode would ignore oAuth
export DEV_MODE="false"
#


# Generate yaml
mkdir release
cd release
cp ../resources/media-gen-service.yaml .
cat << EOF > kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- media-gen-service.yaml

images:
- name: "media-gen"
  newName: asia-southeast1-docker.pkg.dev/multi-gke-ops/gke-repo/media-gen
  newTag: v1
EOF

kustomize build . | envsubst > cr.yaml

# Deploy cr
gcloud run services replace cr.yaml --region=us-central1
