# Console Service

The Console Service is part of the RRD Graph application suite, providing a web-based interface for managing and monitoring various operations.

## Prerequisites

- Python 3.13+
- Google Cloud Platform access
- Access to the required databases and services

## Setup

### 1. Environment Configuration

Create a `.env` file in the console directory with the following variables:

```bash
PROJECT_ID=your-gcp-project-id
REGION=asia-southeast1
```

### 2. Secret Manager Configuration

**Important**: You must create a secret in Google Cloud Secret Manager with the key `dp-pass` to store the database password.

#### Create the Secret:

```bash
# Using gcloud CLI
gcloud secrets create dp-pass \
    --replication-policy="automatic" \
    --project=your-gcp-project-id

# Set the secret value (replace 'your-db-password' with actual password)
echo -n "your-db-password" | \
gcloud secrets versions add dp-pass --data-file=- \
    --project=your-gcp-project-id
```

#### Alternative: Using Google Cloud Console

1. Go to [Secret Manager](https://console.cloud.google.com/security/secret-manager)
2. Click "Create Secret"
3. Set Secret name to: `dp-pass`
4. Set Secret value to your database password
5. Click "Create Secret"

### 3. Service Account Permissions

Ensure your service account has the following roles:
- `Secret Manager Secret Accessor`
- `Cloud SQL Client` (if using Cloud SQL)
- `AlloyDB Client` (if using AlloyDB)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using uv
uv sync
```

## Running the Service

### Local Development

```bash
# Run the service locally
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Using Docker

```bash
# Build the image
docker build -f Dockerfile.console -t console-service .

# Run the container
docker run -p 8000:8000 console-service
```

### Using Skaffold

```bash
# Build and deploy
skaffold run --profile console

# Build only
skaffold build --profile console
```

## API Endpoints

The service exposes various endpoints for console operations. Check the main application file for specific endpoint details.

## Configuration

The service configuration can be customized through environment variables and configuration files. Key configuration options include:

- Database connection settings
- Authentication configuration
- Service-specific parameters

## Troubleshooting

### Common Issues

1. **Secret Access Error**: Ensure the service account has `Secret Manager Secret Accessor` role
2. **Database Connection**: Verify the `dp-pass` secret exists and contains the correct password
3. **Permissions**: Check that all required IAM roles are assigned

### Logs

Check the application logs for detailed error information:

```bash
# If running locally
tail -f console.log

# If running in Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=console-service"
```

## Contributing

1. Follow the project's coding standards
2. Test your changes thoroughly
3. Update this README if adding new features or configuration options

## Support

For issues and questions, please refer to the main project documentation or contact the development team.
