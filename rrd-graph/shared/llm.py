import os
import json
import time
import vertexai
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai._enums import HarmBlockThreshold, HarmCategory
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
from langchain_google_vertexai.model_garden_maas.llama import VertexModelGardenLlama
from langchain_google_genai import ChatGoogleGenerativeAI
from google.auth import default, transport

os.environ["LANGSMITH_API_KEY"]="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"



def init_model(project_id:str, location:str, model_id:str):
    # Only for local test in LangGraph Studio
    file_path="/deps/__outer_agent/agent/multi-gke-ops-aa82224eed72.json"
    if os.path.exists(file_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=file_path
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

    if model_id.startswith("claude"):
        # Vertex Anthropic
        llm = ChatAnthropicVertex(
            project=project_id, location=location, model=model_id, 
            max_tokens=8192, 
            temperature=0.5,
            safety_settings = {
                HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }

        )
    elif model_id.startswith("gemini") and os.getenv("GOOGLE_GENERATIVEAI_API_KEY") is None:
        # VertexAI Gemini
        vertexai.init(project=project_id, location=location)
        llm = ChatVertexAI(
            credentials=credentials, model_name=model_id, temperature=0.5,
            safety_settings = {
                        HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    }
            )
    else:
        # GoogleGenerativeAI
        if os.getenv("GOOGLE_GENERATIVEAI_API_KEY") is not None:
            llm = ChatGoogleGenerativeAI(model=model_id, google_api_key=os.getenv("GOOGLE_GENERATIVEAI_API_KEY"), temperature=1)
        else:
            llm=None
    print(f"llm > {llm}")
    return llm

def string_to_pjson(json_string: str) -> str:
    try:
        # Remove the ```json and ``` markers
        json_str = json_string.strip().replace("```json", "").replace(" ```json", "").replace("```JSON", "").replace("``` JSON", "").replace("```", "")
        return json_str
    except json.JSONDecodeError:
        print("Invalid JSON string")
        return None

def call_llm(llm, prompt: str):
    retry_count = 0
    max_retries = 3
    retry_delay = 1
    while retry_count < max_retries:
        try: 
            while retry_count < 3:
                responding = llm.invoke(prompt)
                print(f"responding: {responding.content}")
                ct = string_to_pjson(responding.content)
                return ct
        except Exception as e:
            print(f"Error to call LLM: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_count += 1
            retry_delay *= 2

    return None