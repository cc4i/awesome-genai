import gradio as gr
import json
import os
import random
import time
import re

from utils.llm import call_llm
from utils.gen_image import gen_images
from utils.logger import logger
from PIL import Image
from io import BytesIO
from utils.gen_video import upload_image, image_to_video, download_videos
from utils.ce_audio import generate_audio_by_gemini, choose_random_voice
from models.config import VEO_STORAGE_BUCKET
from utils.prompt_templates import generate_story_prompt, develop_story_prompt
from utils.video_ts import merge_videos_moviepy, merge_audio_at_time


# Handler functions
def check_folder(path):
    # check folder tmp/ and subfolder tmp/images/default
    if not os.path.exists(path):
        os.makedirs(path)

def clear_temp_files(path:str, extension:str):
    check_folder(path)
    for file in os.listdir(path):
        if extension==".*":
            os.remove(f"{path}/{file}")
        elif file.endswith(extension):
            os.remove(f"{path}/{file}")


    
def generate_video(chosen_veo_model_id, is_generate_audio):
    clear_temp_files("tmp/default", ".mp4")

    all_files = []
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_") and file.endswith(".png"):
            image_path = f"tmp/images/default/{file}"
            seqence = file.split('.')[0].split('_')[1]
            video_prompt_path = f"tmp/images/default/scene_prompt_{seqence}.txt"
            video_prompt = open(video_prompt_path, "r").read()
            print(f"image_path: {image_path}")
            print(f"video_prompt: {video_prompt}")

            # generate video
            image_gcs_path = upload_image(image_path, "default")
            output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated-for-marketing-short"
            op, rr = image_to_video(
                model_id=chosen_veo_model_id,
                prompt=video_prompt,
                image_gcs=image_gcs_path,
                image_gcs_last=None,
                seed=random.randint(0, 1000000),
                aspect_ratio="16:9",
                sample_count=1,
                output_gcs=output_gcs,
                negative_prompt="",
                enhance="true",
                durations=8,
                generate_audio=is_generate_audio,
                resolution="1080p"
            )
            files = download_videos(op, "default", seqence, False)
            all_files.extend(files)
    all_files.sort()
    return all_files

def develope_story(characters, setting, plot, number_of_scenes, duration_per_scene, style):
    clear_temp_files("tmp/images/default", ".*")

    system_instruction, prompt = develop_story_prompt(characters, setting, plot, number_of_scenes, duration_per_scene, style)
    history = ""
    logger.info(f"Developing story with prompt: {prompt}")
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    # Save full string respose to file
    with open("tmp/images/default/story.json", "w") as f:
        f.write(string_response)
    json_response = json.loads(string_response)
    
    for i, scene in enumerate(json_response, 1):
        image_prompt = {
            "title": scene["title"],
            "description": scene["description"], 
            "characters": scene["characters"],
            "image_prompt": scene["image_prompt"]
        }
        
        generated_image_response = gen_images(
            model_id="imagen-4.0-generate-preview-06-06",
            prompt=json.dumps(image_prompt),
            negative_prompt="",
            number_of_images=1,
            aspect_ratio="16:9", 
            is_enhance="yes"
        )[0]
        
        image = Image.open(BytesIO(generated_image_response.image.image_bytes))
        image.save(f"tmp/images/default/scene_{i}.png")
        video_prompt_file = f"tmp/images/default/scene_prompt_{i}.txt"
        with open(video_prompt_file, "w") as f:
            f.write(scene["description"]) # f.write(scene["video_prompt"])
        video_script_file = f"tmp/images/default/scene_script_{i}.txt"
        with open(video_script_file, "w") as f:
            f.write(json.dumps(scene["scripts"]))
    return string_response

def show_images_and_prompts(number_of_scenes):
    MAX_SCENES = 12
    path = "tmp/images/default"
    
    # Get images
    scene_image_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_") and file.endswith(".png"):
                scene_image_files.append(os.path.join(path, file))
    # Pad with None if fewer images than scenes are found
    padded_images = (scene_image_files + [None] * MAX_SCENES)[:MAX_SCENES]
    
    # Get prompts
    scene_prompt_files = []
    if os.path.exists(path):
        for file in sorted(os.listdir(path)):
            if file.startswith("scene_prompt_") and file.endswith(".txt"):
                scene_prompt_files.append(os.path.join(path, file))
    
    generated_scene_prompts = []
    for f in scene_prompt_files:
        with open(f, "r") as file:
            generated_scene_prompts.append(file.read())
    # Pad with empty strings if fewer prompts than scenes are found
    padded_prompts = (generated_scene_prompts + [""] * MAX_SCENES)[:MAX_SCENES]

    # Return a single, flat list: all image paths, then all prompts
    # The order and length must match the `outputs` in the click event
    return padded_images + padded_prompts



def show_generated_videos():
    generated_videos = []
    for file in os.listdir("tmp/default"):
        if file.endswith("_0.mp4"):
            generated_videos.append(f"tmp/default/{file}")
    generated_videos.sort()
    return generated_videos

def generate_story(idea):
    system_instruction, prompt = generate_story_prompt(idea)
    history = ""
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-flash")
    json_response = json.loads(string_response)
    characters = ""
    for c in json_response["characters"]:
        characters += f"{c['name']}: {c['description']}\n"
    setting = json_response["setting"]
    plot = json_response["plot"]

    return characters, setting, plot

def generate_audio():
    clear_temp_files("tmp/default", ".wav")
    all_audio_files = {}
    audio_files = []
    random_voice={}
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_script_") and file.endswith(".txt"):
            logger.info(f"script file: {file}")
            order = file.split(".")[0].split("_")[2]
            string_script = open(f"tmp/images/default/{file}", "r").read()
            json_script = json.loads(string_script)
            for script in json_script:
                character_name=script["character"]
                gender=script["gender"]
                message=script["dialogue"]
                start_time=script["time"]
                # message = f"Say in Singaporean TONE: {message}"
                # Ignore feeling in the message, eg: (Gasps softly)
                message = re.sub(r"\(.*?\)", '', message)
                if len(message) > 0:
                    message = f"Say: {message}"
                    if random_voice.get(character_name) is None:
                        random_voice[character_name] = choose_random_voice(gender)
                    voice_name = random_voice[character_name]
                    print(f"Generating audio for {character_name} with voice {voice_name}")
                    audio_files.append(generate_audio_by_gemini(message, gender, order, character_name, start_time, voice_name))
                    # Add a small delay between audio generation due to rate limit
                    time.sleep(5)
    for f in audio_files:
        order = f.split("/")[-1].split("-")[0]
        if all_audio_files.get(order) is None:
            all_audio_files[order]= [f]
        else:
            all_audio_files[order].append("None")
            all_audio_files[order].append(f)
    for i in range (1, 13):
        if all_audio_files.get(str(i)) is None:
            all_audio_files[str(i)]= ["None"]
    print(all_audio_files)
    
    # Create a list of Dropdown updates
    dropdown_updates = []
    for i in range(1, 13):
        dropdown_updates.append(gr.Dropdown(choices=all_audio_files[str(i)]))
    return dropdown_updates

def show_generated_audios():
    all_audio_files = {}
    path = "tmp/default"
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith(".wav"):
                order = file.split("-")[0]
                if all_audio_files.get(order) is None:
                    all_audio_files[order]= [f"tmp/default/{file}"]
                else:
                    all_audio_files[order].append(f"tmp/default/{file}")
    
    # Ensure all possible keys exist
    for i in range (1, 13):
        if all_audio_files.get(str(i)) is None:
            all_audio_files[str(i)]= []

    # Return a list of Dropdown update objects
    dropdown_updates = []
    for i in range(1, 13):
        choices = all_audio_files[str(i)]
        choices.append("None")
        # Set the initial value to the first choice if available, otherwise None
        value = choices[0] if choices else None
        dropdown_updates.append(gr.Dropdown(choices=choices, value=value))
    return dropdown_updates

def show_merged_videos():
    merged_video = "tmp/default/merged_video.mp4"
    return merged_video


def merge_audios():
    audio_files = []
    video_files = {}
    merged_list = {}
    for file in os.listdir("tmp/default"):
        if file.endswith(".wav"):
            audio_files.append(f"tmp/default/{file}")
    print("===========audio_files=============")
    print(audio_files)
    print("===========audio_files=============")

    for file in os.listdir("tmp/default"):
        if file.endswith(".mp4"):
            # video_files.append(f"tmp/default/{file}")
            order = file.split("-")[0]
            video_files[order] = f"tmp/default/{file}"
    print("===========video_files=============")
    print(video_files)
    print("===========video_files=============")
    
    for audio_file in audio_files:
        print(f"audio_file: {audio_file}")
        strings = audio_file.split("/")[-1].split("-")
        print(f"strings: {strings}")
        order = strings[0]
        character_name = strings[1]
        start_time = strings[2].split(".")[0]
        video_file = video_files[order]
        print(f"video_file: {video_file}")

        if merged_list.get(video_file) is None:
            merged_list[video_file] = {"audios": [{"audio_file": audio_file, "start_time": start_time}]}
        else:
            merged_list[video_file]["audios"].append({"audio_file": audio_file, "start_time": start_time})
    print("===========merged_list=============")
    print(merged_list)
    print("===========merged_list=============")

    
    for video_file in merged_list.keys():
        merged_video=video_file.split(".")[0] + "-merged.mp4"
        audios = merged_list[video_file]["audios"]
        for audio in audios:
            print(f"audio: {audio}")
            if os.path.exists(merged_video):
                merge_audio_at_time(merged_video, audio["audio_file"], merged_video, int(audio["start_time"]))
            else:
                merge_audio_at_time(video_file, audio["audio_file"], merged_video, int(audio["start_time"]))
        

def play_audio(audio_file):
    print(f"audio_file: {audio_file}")
    return audio_file


# UI
with gr.Blocks(theme=gr.themes.Glass(), title="Story GeN/Video ") as demo:
    scene_images = []
    scene_texts = []
    scene_audios = []
    scene_audios_dropdown = []
    short_ingredients = []
    
    with gr.Row():
        with gr.Column(scale=20):
            cgs_markdone = gr.Markdown("""
                # Story GeN/Video
                Tell me a story and give back a video ... powered by <b>CC</b>
            """)
        with gr.Column(scale=1):
            tb_whoami = gr.Textbox(value="", interactive=False, visible=False)
            gr.Button("Logout", link="/logout", scale=1)

    with gr.Tab("1. Idea >>"):
        with gr.Row():
            ta_idea = gr.TextArea(label="What's the Idea", lines=4, 
                value="""
                    The Path Engine is built from the ground up around a central, all-powerful AI. It's a perfect fit! We could also weave a powerful AI into the other concepts, but the story of a system designed for "perfect" lives feels like the strongest starting point.
                """)
        with gr.Row():
            btn_random_idea = gr.Button("Genarate random idea")
            btn_generate_story = gr.Button("Generate story")
    with gr.Tab("2. Story >>"):
        with gr.Row():
            ta_characters = gr.TextArea(label="Characters", lines=4, value="""Dr. Elara Vance: (20s) a mid-level Data Ecologist, her job is to study the "waste data" from the AI.""")
        with gr.Row():
            ta_setting = gr.TextArea(label="Setting", lines=2, value="""When she runs it through a deep-level simulation, she's horrified by what she discovers.""")
        with gr.Row():
            ta_plot = gr.TextArea(label="Plot", lines=5, value="""Elara then discovers more of these "ghosts" in the data waste—the digital echoes of humanity's greatest suppressed minds.""")
        with gr.Row():
            sl_number_of_scenes = gr.Slider(label="Number of Scenes", minimum=1, maximum=12, step=1, interactive=True, value=3)
            sl_duration_per_scene = gr.Slider(label="Duration per Scene", minimum=5, maximum=8, step=1, interactive=True, value=8)
            dd_style = gr.Dropdown(choices=["Studio Ghibli", "Anime", "Photorealistic", "Pencil Sketch", "Oil Painting", "Matte Painting"], label="Style", interactive=True, value="Studio Ghibli") 
        with gr.Row():
            btn_developing = gr.Button("Developing")
        with gr.Row():
            tb_developed_story = gr.TextArea(label="Developed story")
            
    with gr.Tab("3. Visual Storyboard >>"):

        # Create a fixed number of components and control their visibility
        max_scenes = 12
        storyboard_rows = []
        for i in range(max_scenes):
            # Use the slider's default value to set initial visibility
            with gr.Row(visible=(i < sl_number_of_scenes.value)) as row:
                storyboard_rows.append(row)
                scene_images.append(gr.Image(label=f"Scene #{i+1}", type="filepath", scale=1))
                with gr.Column(scale=2):
                    scene_texts.append(gr.TextArea(label=f"Prompt #{i+1}", interactive=True))
                    with gr.Row():
                         audio_file_path = gr.Dropdown(label=f"Audio #{i+1}", scale=3, allow_custom_value=True, interactive=True)
                         audio_file_player = gr.Audio(type="filepath", interactive=False, scale=1)
                         audio_file_path.change(play_audio, inputs=[audio_file_path], outputs=[audio_file_player])

                         scene_audios_dropdown.append(audio_file_path)
                         scene_audios.append(audio_file_player)

        # This function updates which rows are visible when the slider changes
        def update_storyboard_visibility(count):
            # The function must return an update for each row component
            return [gr.update(visible=i < int(count)) for i in range(max_scenes)]
        
        # When the slider value changes, call the function to update row visibility
        sl_number_of_scenes.change(
            fn=update_storyboard_visibility, 
            inputs=[sl_number_of_scenes], 
            outputs=storyboard_rows,
            queue=False  # Use a faster queue for UI-only updates
        )

        with gr.Row():
            veo_model_id = gr.Radio(
                label="Model for generating videos",
                choices=["veo-2.0-generate-001", "veo-3.0-generate-001", "veo-3.0-generate-preview", "veo-3.0-fast-generate-preview"],
                value="veo-3.0-generate-preview",
                interactive=True
            )
            cb_generate_audio = gr.Dropdown(
                label="Generate audio (Only for Veo3)",
                choices=["true", "false"],
                value="true",
                interactive=True
            )
        with gr.Row():
            btn_generate_videos = gr.Button("Generate videos")
            btn_generate_audios = gr.Button("Generate audios(Optional)")
            btn_merge_audios = gr.Button("Merge audios(Optional)")

    with gr.Tab("4. Short ingredients >>"):
 
        with gr.Row():
            short_ingredients=gr.Gallery(label="Generated videos", type="filepath", show_label=False, elem_id="gallery", columns=[3], rows=[4], object_fit="contain", height="auto")
        with gr.Row():
            btn_merge_videos = gr.Button("Merge videos")
            btn_merge_videos_with_audios = gr.Button("Merge videos with audios")

    with gr.Tab("5. BigThing @"):
        with gr.Row():
            merged_video = gr.Video(label="Merged video", show_label=False, elem_id="video", height="auto")
    
    # Load the existed images and prompts if any
    demo.load(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)
    demo.load(show_generated_videos, inputs=None, outputs=[short_ingredients])
    demo.load(show_generated_audios, inputs=None, outputs=scene_audios_dropdown)
    demo.load(show_merged_videos, inputs=None, outputs=[merged_video])

    step1 = btn_developing.click(develope_story, 
            inputs=[ta_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style], 
            outputs=[tb_developed_story])
    step1.then(show_images_and_prompts, inputs=[sl_number_of_scenes], outputs=scene_images + scene_texts)

    btn_generate_videos.click(generate_video, inputs=[veo_model_id, cb_generate_audio], outputs=[short_ingredients])
    btn_generate_audios.click(generate_audio, inputs=None, outputs=scene_audios_dropdown)
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    btn_generate_story.click(generate_story, inputs=[ta_idea], outputs=[ta_characters, ta_setting, ta_plot])

    # scene_audio_1_dropdown.change(play_audio, inputs=[scene_audio_1_dropdown], outputs=[scene_audio_1])
    # scene_audio_2_dropdown.change(play_audio, inputs=[scene_audio_2_dropdown], outputs=[scene_audio_2])
    # scene_audio_3_dropdown.change(play_audio, inputs=[scene_audio_3_dropdown], outputs=[scene_audio_3])
    # scene_audio_4_dropdown.change(play_audio, inputs=[scene_audio_4_dropdown], outputs=[scene_audio_4])
    # scene_audio_5_dropdown.change(play_audio, inputs=[scene_audio_5_dropdown], outputs=[scene_audio_5])
    # scene_audio_6_dropdown.change(play_audio, inputs=[scene_audio_6_dropdown], outputs=[scene_audio_6])
    
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)