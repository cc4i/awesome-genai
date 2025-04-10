"""
Main entry point for the media generation application.
"""

import gradio as gr
import uvicorn

from utils.auth import get_user, app, greet
from ui.components import (
    create_video_tab,
    create_image_tab,
    create_chat_tab,
    create_checking_tab
)
from handlers.media_handlers import (
    generate_images,
    generate_videos,
    upload_image,
    delete_temp_files
)
from handlers.chat_handlers import add_message, bot_message
from utils.gen_video import random_video_prompt, rewrite_video_prompt
from utils.ce_image import random_image_prompt, rewrite_image_prompt
from utils.logger import logger
from models.config import validate_config, LOCAL_STORAGE, DEV_MODE
from models.exceptions import ConfigurationError

# Validate configuration
try:
    validate_config()
except ConfigurationError as e:
    logger.error(f"Configuration error: {str(e)}")
    raise

# Initialize Gradio
gr.close_all()
gr.set_static_paths(paths=[LOCAL_STORAGE])

# Create the main UI
with gr.Blocks(theme=gr.themes.Glass(), title="Creative GeN/Studio") as demo:
    # Header
    with gr.Row():
        with gr.Column(scale=20):
            cgs_markdone = gr.Markdown("""
                # Creative GeN/Studio
                Ignite the spark of your inner creator ... powered by <b>CC</b>
            """)
        with gr.Column(scale=1):
            tb_whoami = gr.Textbox(value="", interactive=False, visible=False)
            tb_file_in_gcs = gr.Textbox(value="", interactive=False, visible=False)
            gr.Button("Logout", link="/logout", scale=1)
            
    # Create tabs
    video_tab, video_components = create_video_tab()
    image_tab, image_components = create_image_tab()
    chat_tab, chat_components = create_chat_tab()
    checking_tab, checking_components = create_checking_tab()
    
    # Extract components
    (
        input_first_image,
        tb_prompt_video,
        tb_negative_prompt,
        dd_type,
        dd_aspect_ratio,
        dd_seed,
        dd_sample_count,
        dd_enhancement,
        dd_duration,
        cb_loop_seamless,
        btn_rewrite_prompt_video,
        btn_random_video_prompt,
        btn_generate_video,
        video_gallery,
        rr_json
    ) = video_components
    
    (
        imagen_model_id,
        tb_prompt_image,
        di_aspect_ratio,
        di_lighting,
        di_style,
        di_sample_count,
        di_enhancement,
        btn_rewrite_prompt_image,
        btn_random_image_prompt,
        btn_generate_image,
        image_gallery
    ) = image_components
    
    (cb_output, response_type, mt_input, btn_clear_cov) = chat_components
    (input_checking_image, what_models_see_image) = checking_components
    
    # Set up event handlers
    input_first_image.upload(
        upload_image,
        inputs=[input_first_image, tb_whoami],
        outputs=tb_file_in_gcs
    )
    
    btn_generate_video.click(
        generate_videos,
        inputs=[
            tb_whoami,
            tb_file_in_gcs,
            tb_prompt_video,
            tb_negative_prompt,
            dd_type,
            dd_aspect_ratio,
            dd_seed,
            dd_sample_count,
            dd_enhancement,
            dd_duration,
            cb_loop_seamless
        ],
        outputs=[video_gallery, rr_json]
    )
    
    btn_random_video_prompt.click(
        random_video_prompt,
        outputs=[tb_prompt_video]
    )
    
    btn_rewrite_prompt_video.click(
        rewrite_video_prompt,
        inputs=[tb_prompt_video],
        outputs=[tb_prompt_video]
    )
    
    btn_generate_image.click(
        generate_images,
        inputs=[
            imagen_model_id,
            tb_prompt_image,
            di_aspect_ratio,
            di_lighting,
            di_style,
            di_sample_count,
            di_enhancement
        ],
        outputs=[image_gallery]
    )
    
    btn_random_image_prompt.click(
        random_image_prompt,
        outputs=[tb_prompt_image]
    )
    
    btn_rewrite_prompt_image.click(
        rewrite_image_prompt,
        inputs=[tb_prompt_image],
        outputs=[tb_prompt_image]
    )
    
    # Chat functionality
    chat_msg = mt_input.submit(
        add_message,
        inputs=[cb_output, mt_input],
        outputs=[cb_output, mt_input]
    )
    
    bot_msg = chat_msg.then(
        bot_message,
        inputs=[cb_output, response_type, tb_whoami],
        outputs=[cb_output],
        api_name="bot_response"
    )
    
    bot_msg.then(
        lambda: gr.MultimodalTextbox(interactive=True),
        None,
        [mt_input]
    )
    
    btn_clear_cov.click(
        delete_temp_files,
        inputs=[tb_whoami],
        outputs=None
    )
    
    # Initialize UI
    demo.load(greet, None, outputs=[cgs_markdone, tb_whoami])

# Mount the Gradio app
if DEV_MODE != "true":
    app = gr.mount_gradio_app(app, demo, path="/gradio", auth_dependency=get_user)
else:
    app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")