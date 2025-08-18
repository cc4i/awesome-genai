# Real-time Reputation Defender Console (rrd-console-adk)

This project contains a real-time reputation monitoring agent built with Google's Agent Development Kit (ADK). It can analyze sentiment from various data sources to provide insights into public perception.


## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager - Install
- **Google Cloud SDK**: For GCP services - Install
- **make**: Build automation tool - Install (pre-installed on most Unix-based systems)


## Setup and Configuration

Before running or deploying the agent, complete the following setup steps.

### 1. Prepare Environment File

Create a `.env` file under the `app/` folder. This file stores credentials and configuration that your agent needs to run locally.

**Example `app/.env`:**
```.env
# --- Database Configuration ---
# Replace with your actual database credentials
DB_USER="your-db-user"
DB_PASS="your-db-password"

# --- Google Cloud Configuration ---
# The project ID where your agent and resources are deployed.
PROJECT_ID="your-gcp-project-id"
```

### 2. Configure Service Account Permissions

When the agent is deployed to Vertex AI Agent Engine, it runs as a specific service account: `service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`. This service account needs permission to access any Google Cloud resources your agent's tools use (e.g., Cloud SQL, BigQuery, etc.).

You must grant the necessary IAM roles to this service account.

**Example: Granting the `Vertex AI User` role:**
```bash
# 1. Set your Project ID
export PROJECT_ID="your-gcp-project-id"

# 2. Grant permissions to the Agent Engine service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:service-$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

## Quick Start (Local Testing)

Install required packages and launch the local development environment:

```bash
make install && make playground
```

## Commands

| Command | Description |
| --- | --- |
| `make install` | Install all required dependencies using uv |
| `make playground` | Launch local development environment with backend and frontend - leveraging `adk web` command.|
| `make cloud-run-backend` | Deploy agent to Cloud Run |
| `make agent-engine-backend` | Launch local agent engine server |
| `make local-backend` | Launch local development server |

For full command options and usage, refer to the `Makefile`.


## Deployment

### Deploy into Cloud Run

```bash
gcloud config set project <your-dev-project-id>
make cloud-run-backend
```

### Deploy into Agent Engine
