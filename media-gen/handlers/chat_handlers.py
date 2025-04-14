"""
Handlers for chat functionality and message processing.
"""

import random
from typing import List, Tuple, Dict, Any, Union, Optional
import gradio as gr

from utils.logger import logger
from utils.ce_image import generate_image_by_gemini
from models.config import COLOR_MAP
from handlers.media_handlers import save_files

def html_src(harm_level: str) -> str:
    """
    Generate HTML for harm level display.
    
    Args:
        harm_level: Level of harm ("harmful", "neutral", or "beneficial")
        
    Returns:
        HTML string for displaying the harm level
    """
    return f"""
        <div style="display: flex; gap: 5px;">
        <div style="background-color: {COLOR_MAP[harm_level]}; padding: 2px; border-radius: 5px;">
        {harm_level}
        </div>
        </div>
        """

def add_message(
    history: List[Tuple[Union[str, Tuple[str, ...]], Optional[Any]]],
    message: Dict[str, Any]
) -> Tuple[List[Tuple[Union[str, Tuple[str, ...]], Optional[Any]]], gr.MultimodalTextbox]:
    """
    Add a message to the chat history.
    
    Args:
        history: Current chat history
        message: New message to add
        
    Returns:
        Updated history and cleared input box
    """
    for x in message["files"]:
        print(x)
        history.append(((x,), None))
    if message["text"] is not None:
        history.append((message["text"], None))
    print(history)
    return history, gr.MultimodalTextbox(value=None, interactive=False)

def bot_message(
    history: List[Tuple[Union[str, Tuple[str, ...]], Optional[Any]]],
    response_type: str,
    whoami: str
) -> List[Tuple[Union[str, Tuple[str, ...]], Optional[Any]]]:
    """
    Generate bot response based on response type.
    
    Args:
        history: Current chat history
        response_type: Type of response to generate
        whoami: User identifier
        
    Returns:
        Updated history with bot response
    """
    try:
        if response_type == "gallery":
            history[-1][1] = gr.Gallery([
                "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
                "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
            ])
        elif response_type == "image & text":
            if len(history) > 1 and history[-2][1] is not None:
                saved_file, rtype = generate_image_by_gemini(history[-1][0], save_files[-1], whoami)
            else:
                saved_file, rtype = generate_image_by_gemini(history[-1][0], None, whoami)
                
            if rtype == "image":
                gi = gr.Image(type="filepath", value=saved_file)
                history[-1][1] = gi
                save_files.append(saved_file)
                logger.info(f"Updated save_files: {save_files}")
            else:
                history[-1][1] = saved_file
        elif response_type == "video":
            history[-1][1] = gr.Video(
                "https://github.com/gradio-app/gradio/raw/main/demo/video_component/files/world.mp4"
            )
        elif response_type == "audio":
            history[-1][1] = gr.Audio(
                "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav"
            )
        elif response_type == "html":
            history[-1][1] = gr.HTML(
                html_src(random.choice(["harmful", "neutral", "beneficial"]))
            )
        else:
            history[-1][1] = "Cool!"
            
        return history
    except Exception as e:
        logger.error(f"Failed to generate bot message: {str(e)}")
        history[-1][1] = "Sorry, I encountered an error. Please try again."
        return history 