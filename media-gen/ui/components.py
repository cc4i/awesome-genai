"""
UI components and layouts for the media generation application.
"""

import gradio as gr
from typing import Tuple, List, Any

from utils.acceptance import sepia, show

from models.config import (
    VIDEO_MODELS,
    IMAGE_MODELS,
    ASPECT_RATIOS,
    SAMPLE_COUNTS,
    DEFAULT_SAMPLE_COUNT,
    DEFAULT_ASPECT_RATIO,
    MIN_DURATION,
    MAX_DURATION,
    DEFAULT_DURATION,
    VIDEO_EXAMPLES,
    IMAGE_EXAMPLES
)

def create_video_tab() -> Tuple[gr.Tab, List[Any]]:
    """
    Create the video generation tab.
    
    Returns:
        Tuple of (video tab, list of components)
    """
    with gr.Tab("Veo") as video_tab:
        with gr.Row():
            gr.Radio(
                label="Model",
                value="veo-2.0-generate-001",
                choices=VIDEO_MODELS,
                interactive=True
            )
        with gr.Row():
            with gr.Column(scale=2):
                tb_prompt_video = gr.Textbox(
                    label="What's your idea?!",
                    value="",
                    lines=6,
                    text_align="left",
                    show_label=True,
                    show_copy_button=True,
                    interactive=True
                )
                gr.Markdown(f"""\n## Examples[...](https://deepmind.google/technologies/veo/veo-2/)
                    \n
                    \n{chr(10).join(f" - {example}" for example in VIDEO_EXAMPLES)}
                    \n
                """)
            with gr.Column(scale=1):
                input_first_image = gr.Image(
                    label="Image for Image-to-Video (Recommended: 1280 x 720 or 720 x 1280)",
                    type="filepath",
                    show_download_button=True,
                    interactive=True
                )
        with gr.Row():
            tb_negative_prompt = gr.Textbox(
                label="Negative prompt",
                lines=1,
                text_align="left",
                show_label=True,
                show_copy_button=True,
                interactive=True
            )
        with gr.Row():
            dd_type = gr.Dropdown(
                label="Type",
                choices=["Text-to-Video", "Image-to-Video"],
                interactive=True
            )
            dd_aspect_ratio = gr.Dropdown(
                label="Aspect ratio",
                value=DEFAULT_ASPECT_RATIO,
                choices=ASPECT_RATIOS,
                interactive=True
            )
            dd_seed = gr.Textbox(
                label="Seed (0 - 4294967295)",
                value="668",
                interactive=True
            )
            dd_sample_count = gr.Dropdown(
                label="Sample count",
                value=DEFAULT_SAMPLE_COUNT,
                choices=SAMPLE_COUNTS,
                interactive=True
            )
            dd_enhancement = gr.Dropdown(
                label="Enhancement",
                value="yes",
                choices=["yes", "no"],
                interactive=True
            )
            dd_duration = gr.Slider(
                MIN_DURATION,
                MAX_DURATION,
                value=DEFAULT_DURATION,
                label="Duration",
                info="Length of video, 5-8s",
                step=1,
                interactive=True
            )
        with gr.Row():
            btn_rewrite_prompt_video = gr.Button(
                value="Rewrite",
                icon="images/painted-brush.png"
            )
            btn_random_video_prompt = gr.Button(
                "Random",
                icon="images/gemini-star.png"
            )
            btn_generate_video = gr.Button(
                "Generate",
                icon="images/gemini-star.png"
            )
        with gr.Row():
            video_gallery = gr.Gallery(
                label="Generated videos",
                show_label=False,
                elem_id="gallery",
                columns=[3],
                rows=[1],
                object_fit="contain",
                height="auto"
            )
        with gr.Row():
            rr_json = gr.JSON()
            
    components = [
        input_first_image,
        tb_prompt_video,
        tb_negative_prompt,
        dd_type,
        dd_aspect_ratio,
        dd_seed,
        dd_sample_count,
        dd_enhancement,
        dd_duration,
        btn_rewrite_prompt_video,
        btn_random_video_prompt,
        btn_generate_video,
        video_gallery,
        rr_json
    ]
    
    return video_tab, components

def create_image_tab() -> Tuple[gr.Tab, List[Any]]:
    """
    Create the image generation tab.
    
    Returns:
        Tuple of (image tab, list of components)
    """
    with gr.Tab("Imagen") as image_tab:
        with gr.Row():
            imagen_model_id = gr.Radio(
                label="Model",
                value="imagen-3.0-generate-002",
                choices=IMAGE_MODELS,
                interactive=True
            )
        with gr.Row():
            tb_prompt_image = gr.Textbox(
                label="What's your idea?!",
                lines=4,
                text_align="left",
                show_label=True,
                show_copy_button=True,
                interactive=True
            )
        with gr.Row():
            gr.Markdown(f"""\n## Examples[...](https://deepmind.google/technologies/imagen-3/)
                \n
                \n{chr(10).join(f"- {example}" for example in IMAGE_EXAMPLES)}
                \n
            """)
        with gr.Row():
            di_aspect_ratio = gr.Dropdown(
                label="Aspect ratio",
                choices=ASPECT_RATIOS,
                interactive=True
            )
            di_color_tone = gr.Dropdown(
                label="Color & Tone",
                choices=[""],
                interactive=True
            )
            di_lighting = gr.Dropdown(
                label="Lighting",
                choices=[""],
                interactive=True
            )
            di_composition = gr.Dropdown(
                label="Composition",
                choices=[""],
                interactive=True
            )
            di_sample_count = gr.Dropdown(
                label="Sample count",
                value=DEFAULT_SAMPLE_COUNT,
                choices=SAMPLE_COUNTS,
                interactive=True
            )
            di_enhancement = gr.Dropdown(
                label="Prompt Enhancement",
                choices=["yes", "no"],
                interactive=True
            )
        with gr.Row():
            btn_rewrite_prompt_image = gr.Button(
                value="Rewrite",
                icon="images/painted-brush.png"
            )
            btn_random_image_prompt = gr.Button(
                "Random",
                icon="images/gemini-star.png"
            )
            btn_generate_image = gr.Button(
                "Generate",
                icon="images/gemini-star.png"
            )
        with gr.Row():
            gtimer = gr.Timer(5)
            image_gallery = gr.Gallery(
                label="Generated images",
                format="png",
                show_label=False,
                elem_id="gallery",
                columns=[3],
                rows=[1],
                object_fit="contain",
                height="auto",
                every=gtimer,
                preview=True
            )
            
    components = [
        imagen_model_id,
        tb_prompt_image,
        di_aspect_ratio,
        di_color_tone,
        di_lighting,
        di_composition,
        di_sample_count,
        di_enhancement,
        btn_rewrite_prompt_image,
        btn_random_image_prompt,
        btn_generate_image,
        image_gallery
    ]
    
    return image_tab, components

def create_chat_tab() -> Tuple[gr.Tab, List[Any]]:
    """
    Create the conversational editing tab.
    
    Returns:
        Tuple of (chat tab, list of components)
    """
    with gr.Tab("Conversational editing") as chat_tab:
        with gr.Row():
            cb_output = gr.Chatbot(type="tuples")
        with gr.Row():
            response_type = gr.Radio(
                [
                    "image & text",
                    "gallery",
                    "video",
                    "audio",
                    "html",
                ],
                value="image & text",
                label="Response Type"
            )
        with gr.Row():
            mt_input = gr.MultimodalTextbox(label="Ask ME")
        with gr.Row():
            btn_clear_cov = gr.ClearButton(
                icon="images/free-reboot-icon.png",
                value="",
                components=[mt_input, cb_output]
            )
            
    components = [cb_output, response_type, mt_input, btn_clear_cov]
    return chat_tab, components

def create_checking_tab() -> Tuple[gr.Tab, List[Any]]:
    """
    Create the image checking tab.
    
    Returns:
        Tuple of (checking tab, list of components)
    """
    with gr.Tab("Checking image") as checking_tab:
        with gr.Row():
            input_checking_image = gr.Image(label="What YOU see")
            gr.Interface(sepia, input_checking_image, gr.Image(label="Sepia"))
        with gr.Row():
            what_models_see_image = gr.Image(label="What MODELs see")
            input_checking_image.change(show, inputs=input_checking_image, outputs=what_models_see_image)
            
    components = [input_checking_image, what_models_see_image]
    return checking_tab, components 