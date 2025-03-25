import json
import os
import gradio as gr
import pandas as pd
import random
from PIL import Image
from io import BytesIO
import numpy as np
from dotenv import load_dotenv
load_dotenv()


from utils.gen_image import gen_images
from utils.gen_video import text_to_video
from utils.gen_video import image_to_video
from utils.gen_video import download_videos
from utils.gen_video import upload_local_file_to_gcs
from utils.gen_video import random_video_prompt
from utils.gen_video import rewrite_video_prompt
from utils.ce_image import generate_image_by_gemini
from utils.ce_image import random_image_prompt
from utils.ce_image import rewrite_image_prompt
from utils.acceptance import sepia
from utils.auth import get_user
from utils.auth import app
from utils.auth import greet
import uvicorn



gr.close_all()
gr.set_static_paths(paths=[os.getenv("LOCAL_STORAGE")])


# Imagen
def generate_images(model_id, prompt, aspect_ratio, sample_count, is_enhance):
    generated_images = gen_images(model_id=model_id, prompt=prompt, negative_prompt="", number_of_images=sample_count, aspect_ratio=aspect_ratio, is_enhance=is_enhance)
    print(f"generated_images: {len(generated_images)}")
    ims = []
    for generated_image in generated_images:
        image = Image.open(BytesIO(generated_image.image.image_bytes))
        ims.append(image)
    return ims

# Checking
def show(input_image):
    return input_image

# Veo
veo_storage_bucket=os.getenv("VEO_STORAGE_BUCKET")
def upload_image(input_image_path, whoami):
    print(f"input_image_path: {input_image_path}, whoami: {whoami}")
    return upload_local_file_to_gcs(f"{veo_storage_bucket}", f"uploaded-images/{whoami}", input_image_path)


def generate_viodes(whoami, file_in_gcs, prompt, negative_prompt, type, aspect_ratio, seed, sample_count, enhance, durations):
    if type == "Text-to-Video":
        op, rr=text_to_video(prompt, seed = seed, aspect_ratio = aspect_ratio, sample_count = sample_count, output_gcs = f"gs://{veo_storage_bucket}/generated", negative_prompt=negative_prompt, enhance=enhance, durations=durations)
        if op["response"].get("raiMediaFilteredReasons") is not None:
            gr.Error(op["response"]["raiMediaFilteredReasons"])
        return download_videos(op, whoami), rr
    else:
        print(f"first image in the gcs: {file_in_gcs}")
        op, rr=image_to_video(prompt,file_in_gcs, seed, aspect_ratio, sample_count, f"gs://{veo_storage_bucket}/generated", negative_prompt=negative_prompt, enhance=enhance, durations=durations)
        if op["response"].get("raiMediaFilteredReasons") is not None:
            gr.Error(op["response"]["raiMediaFilteredReasons"])
        return download_videos(op, whoami), rr       
        
# Conversational edting
color_map = {
    "harmful": "crimson",
    "neutral": "gray",
    "beneficial": "green",
}
save_files = []
def html_src(harm_level):
    return f"""
        <div style="display: flex; gap: 5px;">
        <div style="background-color: {color_map[harm_level]}; padding: 2px; border-radius: 5px;">
        {harm_level}
        </div>
        </div>
        """
def add_message(history, message):
    for x in message["files"]:
        history.append(((x,), None))
    if message["text"] is not None:
        history.append((message["text"], None))
    return history, gr.MultimodalTextbox(value=None, interactive=False)

def bot_message(history, response_type, whoami):
    if response_type == "gallery":
        history[-1][1] = gr.Gallery(
            [
                "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
                "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
            ]
        )
    elif response_type == "image & text":
        if len(history) >1 and history[-2][1] is not None:
            saved_file, rtype = generate_image_by_gemini(history[-1][0], save_files[-1], whoami)
        else:
            saved_file, rtype = generate_image_by_gemini(history[-1][0], None, whoami)
        if rtype == "image":
            gi = gr.Image(type="filepath", value=saved_file)
            history[-1][1] = gi
            save_files.append(saved_file)
            print(f"save_files: {save_files}")
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

def delete_temp_files(whoami):
    for s_file in save_files:
        if os.path.exists(s_file):
            print(f"delete {s_file}")
            os.remove(s_file)
            save_files.remove(s_file)
    local_path=os.getenv("LOCAL_STORAGE") + f"/{whoami}"
    if os.path.exists(local_path):
        print(f"delete rest of files in {local_path}/*")
        os.system(f"rm -rf {local_path}/*")
    # return history, []
    

# Main UI
with gr.Blocks(theme=gr.themes.Glass(), title="Creative GeN/Studio") as demo:
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
    # Videos
    with gr.Tab("Veo"):
        with gr.Row():
            gr.Radio(label="Model", value="veo-2.0-generate-001", choices=["veo-2.0-generate-001"], interactive=True)
        with gr.Row():
            with gr.Column(scale=2):
                tb_prompt_video = gr.Textbox(label="What's your idea?!", value="", lines=6, text_align="left", show_label=True, show_copy_button=True, interactive=True)
                gr.Markdown("""
                    ## Examples[...](https://deepmind.google/technologies/veo/veo-2/)
                    - A wide shot of a lone cowboy riding a horse across a vast, sun-drenched prairie, with a dramatic sky filled with fluffy clouds in the background. The cowboy is silhouetted against the setting sun, creating a sense of epic scale and adventure.
                    - Wide angle shot of a skier speeding down the mountain on a sunny da in the Alps.
                    - Whiteboard illustration animated video of a waiter serving food.  White background, wide angle.
                """)
            with gr.Column(scale=1):
                input_first_image = gr.Image(label="Image for Image-to-Video (Recommended: 1280 x 720 or 720 x 1280)",type= "filepath", show_download_button=True, interactive=True)
        with gr.Row():
            tb_negative_prompt = gr.Textbox(label="Negative prompt", lines=1, text_align="left", show_label=True, show_copy_button=True, interactive=True)
        with gr.Row():
            dd_type = gr.Dropdown(label="Type", choices=["Text-to-Video", "Image-to-Video"], interactive=True)
            dd_aspect_ratio = gr.Dropdown(label="Aspect ratio", value="16:9", choices=["1:1", "9:16", "16:9", "4:3", "3:4"], interactive=True)
            dd_seed = gr.Textbox(label="Seed (0 - 4294967295)", value="668", interactive=True)
            dd_sample_count = gr.Dropdown(label="Sample count", value="2", choices=["1", "2", "3", "4", "5"], interactive=True)
            dd_enhancement = gr.Dropdown(label="Enhancement", value="yes", choices=["yes", "no"], interactive=True)
            dd_duration = gr.Slider(5, 8, value=8, label="Duration", info="Length of video, 5-8s", step=1, interactive=True)
        with gr.Row():
            btn_rewrite_prompt_video = gr.Button(value="Rewrite", icon="images/painted-brush.png")
            btn_random_video_prompt=gr.Button("Random", icon="images/gemini-star.png")
            btn_generate_video = gr.Button("Generate", icon="images/gemini-star.png")
        with gr.Row():
            video_gallery = gr.Gallery(label="Generated videos", show_label=False, elem_id="gallery", columns=[3], rows=[1], 
                                 object_fit="contain", height="auto")
        with gr.Row():
            rr_json = gr.JSON()
    # Images
    with gr.Tab("Imagen"):
        with gr.Row():
            imagen_model_id = gr.Radio(label="Model", value="imagen-3.0-generate-002", choices=["imagen-3.0-generate-002","imagen-3.0-fast-generate-001"], interactive=True)
        with gr.Row():
            tb_prompt_image = gr.Textbox(label="What's your idea?!", lines=4, text_align="left", show_label=True, show_copy_button=True, interactive=True)
        with gr.Row():
            gr.Markdown("""
                ## Examples[...](https://deepmind.google/technologies/imagen-3/)
                - A woman, 35mm portrait, blue and grey duotones.
                - An expansive mountain range, landscape wide angle 10mm.
                - A technical pencil drawing of an angular sporty electric sedan with skyscrapers in the background.
            """)
        with gr.Row():
            di_aspect_ratio = gr.Dropdown(label="Aspect ratio", choices=["1:1", "9:16", "16:9", "4:3", "3:4"], interactive=True)
            di_color_tone = gr.Dropdown(label="Color & Tone", choices=[""], interactive=True)
            di_lighting = gr.Dropdown(label="Lighting", choices=[""], interactive=True)
            di_composition = gr.Dropdown(label="Composition", choices=[""], interactive=True)
            di_sample_count = gr.Dropdown(label="Sample count", value="2", choices=["1", "2", "3", "4", "5"], interactive=True)
            di_enhancement = gr.Dropdown(label="Prompt Enhancement", choices=["yes", "no"], interactive=True)
        with gr.Row():
            btn_rewrite_prompt_image = gr.Button(value="Rewrite", icon= "images/painted-brush.png")
            btn_random_image_prompt = gr.Button("Random", icon="images/gemini-star.png")
            btn_generate_image = gr.Button("Generate", icon="images/gemini-star.png")
        with gr.Row():
            gtimer = gr.Timer(5)
            image_gallery = gr.Gallery(label="Generated images", show_label=False, elem_id="gallery", columns=[3], rows=[1], object_fit="contain", height="auto", every=gtimer, preview=True)

    with gr.Tab("Conversational editing"):
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
            btn_clear_cov=gr.ClearButton(icon="images/free-reboot-icon.png", value="", components=[mt_input, cb_output])
    with gr.Tab("Checking image"):
        with gr.Row():
            input_checking_image = gr.Image(label="What YOU see")
            gr.Interface(sepia, input_checking_image, gr.Image(label="Sepia"))
        with gr.Row():
            what_models_see_image = gr.Image(label="What MODELs see")
            input_checking_image.change(show, inputs=input_checking_image, outputs=what_models_see_image)



    input_first_image.upload(upload_image, inputs=[input_first_image,tb_whoami], outputs=tb_file_in_gcs)
    btn_generate_video.click(generate_viodes, inputs=[tb_whoami, tb_file_in_gcs, tb_prompt_video, tb_negative_prompt, dd_type, dd_aspect_ratio, dd_seed, dd_sample_count, dd_enhancement, dd_duration], outputs=[video_gallery, rr_json])
    btn_random_video_prompt.click(random_video_prompt, outputs=[tb_prompt_video])
    btn_rewrite_prompt_video.click(rewrite_video_prompt, inputs=[tb_prompt_video], outputs=[tb_prompt_video])
    btn_generate_image.click(generate_images, inputs=[imagen_model_id,tb_prompt_image, di_aspect_ratio, di_sample_count, di_enhancement], outputs=[image_gallery])
    btn_random_image_prompt.click(random_image_prompt, outputs=[tb_prompt_image])
    btn_rewrite_prompt_image.click(rewrite_image_prompt, inputs=[tb_prompt_image], outputs=[tb_prompt_image])
    
    
    
    chat_msg = mt_input.submit(add_message, inputs=[cb_output, mt_input], outputs=[cb_output, mt_input])
    bot_msg = chat_msg.then(bot_message, inputs=[cb_output, response_type, tb_whoami], outputs=[cb_output], api_name="bot_response")
    bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [mt_input])
    btn_clear_cov.click(delete_temp_files, inputs=[tb_whoami], outputs=None)
    demo.load(greet, None, outputs=[cgs_markdone, tb_whoami])
    


app = gr.mount_gradio_app(app, demo, path="/gradio", auth_dependency=get_user)

if __name__ == "__main__":
    # demo.launch(server_name="0.0.0.0", allowed_paths=[os.getenv("LOCAL_STORAGE")])
    # demo.launch(server_name="0.0.0.0")
    uvicorn.run(app, host="0.0.0.0")