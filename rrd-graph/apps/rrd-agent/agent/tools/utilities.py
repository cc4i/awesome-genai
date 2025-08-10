import os
from langchain_core.tools import tool
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, Part

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode


project_id = os.getenv("PROJECT_ID") or "realtime-reputation-defender"
location = os.getenv("LOCATION") or "us-central1"
model_id = os.getenv("MODEL_ID") or "gemini-1.5-pro-002"

def call_gemini_sdk(prompt)->str:
    """ Function to invoke Vertex AI LLMs
    Args:
        prompt: prompt string for Gemini.

    Returns:
        The amazing result.
    """
    vertexai.init(project=project_id, location=location)
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }
    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
    ]
    model = GenerativeModel(
        model_name=model_id,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    chat = model.start_chat()
    try:
        g_response = chat.send_message(prompt).to_dict()
        out = g_response.get("candidates")[0].get("content").get("parts")[0].get("text")
        if out.startswith(" ```json") or out.startswith("```json"):
            out = out.replace("```json", "").replace("```", "")
        elif out.startswith(" ```JSON") or out.startswith("```JSON"):
            out = out.replace("```JSON", "").replace("```", "")
        return out
    except Exception as e:
        print(e)
        return None



def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)
            return msg_repr

