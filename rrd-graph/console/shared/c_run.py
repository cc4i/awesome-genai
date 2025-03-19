from google.cloud import run_v2

def get_google_cloud_run_service_url(project_id, location, service_name):
  try:
    # Create a Cloud Run client
    client = run_v2.ServicesClient()
    # Build the service name
    name = f"projects/{project_id}/locations/{location}/services/{service_name}"
    # Make the request
    response = client.get_service(name=name)
    print(response)
    service_url = response.uri
    return service_url
  except Exception as e:
    print(f"Error getting Cloud Run service URL: {e}")
    return None

