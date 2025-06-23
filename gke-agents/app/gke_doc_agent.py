import os

import google
import vertexai
from google import genai
from google.adk.agents import Agent
from google.genai.types import Content
from langchain_google_vertexai import VertexAIEmbeddings

from app.gke_templates import FORMAT_DOCS, SYSTEM_INSTRUCTION
from app.vector_store import get_vector_store

# Constants
VERTEXAI = os.getenv("VERTEXAI", "true").lower() == "true"
LOCATION = "us-central1"
EMBEDDING_MODEL = "text-embedding-005"
MODEL_ID = "gemini-2.0-flash"
URLS = [
    "https://cloud.google.com/kubernetes-engine/docs",
    "https://cloud.google.com/kubernetes-engine/docs/best-practices/networking",
    "https://www.wiz.io/academy/gke-security-best-practices"
]

# Initialize Google Cloud clients
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(project=project_id, location=LOCATION, vertexai=True)
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})

# Initialize vector store and retriever
embedding = VertexAIEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = get_vector_store(embedding=embedding, urls=URLS)
retriever = vector_store.as_retriever()


def retrieve_docs(query: str) -> dict[str, str]:
    """
    Retrieves pre-formatted documents about GKE Operations and production deployment best practices.

    Args:
        query: Search query string related to GKE operations, or production deployment.

    Returns:
        A set of relevant, pre-formatted documents.
    """
    docs = retriever.invoke(query)
    formatted_docs = FORMAT_DOCS.format(docs=docs)
    return {"output": formatted_docs}


# Configure tools available to the agent and live connection
tool_functions = {"retrieve_docs": retrieve_docs}

# live_connect_config = LiveConnectConfig(
#     response_modalities=["AUDIO"],
#     tools=[retrieve_docs],
#     system_instruction=Content(parts=[{"text": SYSTEM_INSTRUCTION}]),
# )

gke_doc_agent = Agent(
    name="gke_doc_agent",
    model="gemini-2.0-flash",
    tools=[retrieve_docs],
    instruction=SYSTEM_INSTRUCTION,
)
