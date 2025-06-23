
export PROJECT_ID="multi-gke-ops"
export PROJECT_NUMBER="1094752696945"
export REASONING_ENGINE="projects/1094752696945/locations/us-central1/reasoningEngines/9173911605790900224"
export AGENT_DISPLAY_NAME="gke-agents"
export AGENT_DESCRIPTION="The agent can only answer questions about Weather."
export AGENT_ID="gke-agents"
export AS_APP="enterprise-search-17458256_1745825690257"

curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "x-goog-user-project: ${PROJECT_ID}" \
https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/default_assistant?updateMask=agent_configs -d '{
    "name": "projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/default_assistant",
    "displayName": "Default Assistant",
    "agentConfigs": [{
      "displayName": "'"${AGENT_DISPLAY_NAME}"'",
      "vertexAiSdkAgentConnectionInfo": {
        "reasoningEngine": "'"${REASONING_ENGINE}"'"
      },
      "toolDescription": "'"${AGENT_DESCRIPTION}"'",
      "icon": {
        "uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/corporate_fare/default/24px.svg"
      },
      "id": "'"${AGENT_ID}"'"
    }]
  }'