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
from prompt_templates import generate_story_prompt, develop_story_prompt
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



def generate_video():
    clear_temp_files("tmp/default", ".mp4")

    all_files = []
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_") and file.endswith(".png"):
            image_path = f"tmp/images/default/{file}"
            order = file.split('.')[0].split('_')[1]
            video_prompt_path = f"tmp/images/default/scene_prompt_{order}.txt"
            video_prompt = open(video_prompt_path, "r").read()
            print(f"image_path: {image_path}")
            print(f"video_prompt: {video_prompt}")

            # generate video
            image_gcs_path = upload_image(image_path, "default")
            output_gcs = f"gs://{VEO_STORAGE_BUCKET}/generated-for-marketing-short"
            op, rr = image_to_video(
                prompt=video_prompt,
                image_gcs=image_gcs_path,
                seed=random.randint(0, 1000000),
                aspect_ratio="16:9",
                sample_count=1,
                output_gcs=output_gcs,
                negative_prompt="",
                enhance="yes",
                durations=8
            )
            files = download_videos(op, "default", order)
            all_files.extend(files)
    all_files.sort()
    return all_files

def develope_story(characters, setting, plot, number_of_scenes, duration_per_scene, style):
    clear_temp_files("tmp/images/default", ".*")

    system_instruction, prompt = develop_story_prompt(characters, setting, plot, number_of_scenes, duration_per_scene, style)
    history = ""
    logger.info(f"Developing story with prompt: {prompt}")
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-pro-exp-03-25")
    # Save full string respose to file
    with open("tmp/images/default/story.json", "w") as f:
        f.write(string_response)
    json_response = json.loads(string_response)
    
    # scene_images = []
    for i, scene in enumerate(json_response, 1):
        image_prompt = {
            "title": scene["title"],
            "description": scene["description"], 
            "characters": scene["characters"],
            "image_prompt": scene["image_prompt"]
        }
        
        generated_image_response = gen_images(
            model_id="imagen-3.0-generate-002",
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


def show_images_n_prompts():
    
    scene_image_files = []
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_") and file.endswith(".png"):
            scene_image_files.append(file)
    scene_image_files.sort()
    print("Found scene image files:", scene_image_files)
 
    generated_scene_images = []
    for i in range(6):
        if i < len(scene_image_files):
            generated_scene_images.append("tmp/images/default/" + scene_image_files[i])
        else:
            generated_scene_images.append(None)
            
    generated_scene_image_1 = generated_scene_images[0]
    generated_scene_image_2 = generated_scene_images[1] 
    generated_scene_image_3 = generated_scene_images[2]
    generated_scene_image_4 = generated_scene_images[3]
    generated_scene_image_5 = generated_scene_images[4]
    generated_scene_image_6 = generated_scene_images[5]

    # 
    scene_prompt_files = []
    for file in os.listdir("tmp/images/default"):
        if file.startswith("scene_prompt_") and file.endswith(".txt"):
            scene_prompt_files.append(file)
    scene_prompt_files.sort()
    print("Found scene prompt files:", scene_prompt_files)
    
    generated_scene_prompts = []
    for i in range(6):
        if i < len(scene_prompt_files):
            generated_scene_prompts.append(open(f"tmp/images/default/{scene_prompt_files[i]}", "r").read())
        else:
            generated_scene_prompts.append(None)
    
    generated_scene_prompt_1 = generated_scene_prompts[0]
    generated_scene_prompt_2 = generated_scene_prompts[1]
    generated_scene_prompt_3 = generated_scene_prompts[2]
    generated_scene_prompt_4 = generated_scene_prompts[3]
    generated_scene_prompt_5 = generated_scene_prompts[4]
    generated_scene_prompt_6 = generated_scene_prompts[5]

    return generated_scene_image_1, generated_scene_image_2, generated_scene_image_3, generated_scene_image_4, generated_scene_image_5, generated_scene_image_6, generated_scene_prompt_1, generated_scene_prompt_2, generated_scene_prompt_3, generated_scene_prompt_4, generated_scene_prompt_5, generated_scene_prompt_6

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
    string_response = call_llm(system_instruction, prompt, history, "gemini-2.5-pro-exp-03-25")
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
            all_audio_files[order].append(f)
    for i in range (1, 7):
        if all_audio_files.get(str(i)) is None:
            all_audio_files[str(i)]= []
    print(all_audio_files)
    return gr.Dropdown(choices=all_audio_files["1"]), gr.Dropdown(choices=all_audio_files["2"]), gr.Dropdown(choices=all_audio_files["3"]), gr.Dropdown(choices=all_audio_files["4"]), gr.Dropdown(choices=all_audio_files["5"]), gr.Dropdown(choices=all_audio_files["6"])

def show_generated_audios():
    all_audio_files = {}
    for file in os.listdir("tmp/default"):
        if file.endswith(".wav"):
            order = file.split("-")[0]
            if all_audio_files.get(order) is None:
                all_audio_files[order]= [f"tmp/default/{file}"]
            else:
                all_audio_files[order].append(f"tmp/default/{file}")
    for i in range (1, 7):
        if all_audio_files.get(str(i)) is None:
            all_audio_files[str(i)]= []
    print(all_audio_files)
    return gr.Dropdown(choices=all_audio_files["1"]), gr.Dropdown(choices=all_audio_files["2"]), gr.Dropdown(choices=all_audio_files["3"]), gr.Dropdown(choices=all_audio_files["4"]), gr.Dropdown(choices=all_audio_files["5"]), gr.Dropdown(choices=all_audio_files["6"])

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
    return audio_file


# UI
with gr.Blocks(theme=gr.themes.Glass(), title="Story GeN/Video ") as demo:
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
            ta_idea = gr.TextArea(label="What's the Idea", lines=4, value="""In a near-future city where bio-luminescent tattoos display real-time personal data and aesthetics, a disillusioned data broker gets a complex, experimental tattoo, only to realize the intricate, shifting patterns aren't just code – they're the emergent consciousness of an AI living in his skin, and it has its own agenda.""")
        with gr.Row():
            btn_random_idea = gr.Button("Genarate random idea")
            btn_generate_story = gr.Button("Generate story")
    with gr.Tab("2. Story >>"):
        with gr.Row():
            ta_characters = gr.TextArea(label="Characters", lines=4, value="""MAYA: (20s) Curious, ordinary person living in a slightly worn-down futuristic city.""")
        with gr.Row():
            ta_setting = gr.TextArea(label="Setting", lines=2, value="""A cluttered apartment filled with a mix of old tech and sleek, functional futuristic items. Overlooks a dense cityscape with flickering lights and passing vehicles (maybe hovercars, drones).""")
        with gr.Row():
            ta_plot = gr.TextArea(label="Plot", lines=5, value="""A woman discovers a strange device that predicts future events, leading her to a startling realization about her origin.""")
        with gr.Row():
            sl_number_of_scenes = gr.Slider(label="Number of Scenes", minimum=1, maximum=6, step=1, interactive=True, value=3)
            sl_duration_per_scene = gr.Slider(label="Duration per Scene", minimum=5, maximum=8, step=1, interactive=True, value=8)
            dd_style = gr.Dropdown(choices=["Studio Ghibli", "Anime", "Photorealistic", "Pencil Sketch", "Oil Painting", "Matte Painting"], label="Style", interactive=True, value="Studio Ghibli") 
        with gr.Row():
            btn_developing = gr.Button("Developing")
        with gr.Row():
            tb_developed_story = gr.TextArea(label="Developed story")
        
            
    with gr.Tab("3. Visual Storyboarding >>"):
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group():
                    scene_image_1=gr.Image(label="Scene #1", type="filepath")
                    scene_text_1=gr.TextArea(label="Prompt #1", interactive=True)
                    scene_audio_1=gr.Audio(type="filepath", interactive=False)
                    scene_audio_1_dropdown=gr.Dropdown(label="Audio #1")
            with gr.Column(scale=1):
                with gr.Group():
                    scene_image_2=gr.Image(label="Scene #2", type="filepath")
                    scene_text_2=gr.TextArea(label="Prompt #2", interactive=True)
                    scene_audio_2=gr.Audio(type="filepath", interactive=False)
                    scene_audio_2_dropdown=gr.Dropdown(label="Audio #2")
            with gr.Column(scale=1):
                with gr.Group():
                    scene_image_3=gr.Image(label="Scene #3", type="filepath")
                    scene_text_3=gr.TextArea(label="Prompt #3", interactive=True)
                    scene_audio_3=gr.Audio(type="filepath", interactive=False)
                    scene_audio_3_dropdown=gr.Dropdown(label="Audio #3")
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group():
                    scene_image_4=gr.Image(label="Scene #4", type="filepath")
                    scene_text_4=gr.TextArea(label="Prompt #4", interactive=True)
                    scene_audio_4=gr.Audio(type="filepath", interactive=False)
                    scene_audio_4_dropdown=gr.Dropdown(label="Audio #4")
            with gr.Column(scale=1):
                with gr.Group():
                    scene_image_5=gr.Image(label="Scene #5", type="filepath")
                    scene_text_5=gr.TextArea(label="Prompt #5", interactive=True)
                    scene_audio_5=gr.Audio(type="filepath", interactive=False)
                    scene_audio_5_dropdown=gr.Dropdown(label="Audio #5")
            with gr.Column(scale=1):
                with gr.Group():
                    scene_image_6=gr.Image(label="Scene #6", type="filepath")
                    scene_text_6=gr.TextArea(label="Prompt #6", interactive=True)
                    scene_audio_6=gr.Audio(type="filepath", interactive=False)
                    scene_audio_6_dropdown=gr.Dropdown(label="Audio #6")
        with gr.Row():
            btn_generate_videos = gr.Button("Generate videos")
            btn_generate_audios = gr.Button("Generate audios(Optional)")
            btn_merge_audios = gr.Button("Merge audios(Optional)")
        with gr.Row():
            generated_videos = gr.Gallery(label="Generated videos", type="filepath", show_label=False, elem_id="gallery", columns=[3], rows=[2], object_fit="contain", height="auto")
        with gr.Row():
            btn_merge_videos = gr.Button("Merge videos")
            btn_merge_videos_with_audios = gr.Button("Merge videos with audios")
        with gr.Row():
            merged_video = gr.Video(label="Merged video", show_label=False, elem_id="video", height="auto")
    with gr.Tab("History >>"):
        with gr.Row():
            gr.TextArea()
    
    demo.load(show_images_n_prompts, inputs=None, outputs=[scene_image_1, scene_image_2, scene_image_3, scene_image_4, scene_image_5, scene_image_6, scene_text_1, scene_text_2, scene_text_3, scene_text_4, scene_text_5, scene_text_6])
    demo.load(show_generated_videos, inputs=None, outputs=[generated_videos])
    demo.load(show_generated_audios, inputs=None, outputs=[scene_audio_1_dropdown, scene_audio_2_dropdown, scene_audio_3_dropdown, scene_audio_4_dropdown, scene_audio_5_dropdown, scene_audio_6_dropdown])

    step1 = btn_developing.click(develope_story, 
            inputs=[ta_characters, ta_setting, ta_plot, sl_number_of_scenes, sl_duration_per_scene, dd_style], 
            outputs=[tb_developed_story])
    step1.then(show_images_n_prompts, inputs=None, outputs=[scene_image_1, scene_image_2, scene_image_3, scene_image_4, scene_image_5, scene_image_6, scene_text_1, scene_text_2, scene_text_3, scene_text_4, scene_text_5, scene_text_6])

    btn_generate_videos.click(generate_video, inputs=None, outputs=[generated_videos])
    btn_generate_audios.click(generate_audio, inputs=None, outputs=[scene_audio_1_dropdown, scene_audio_2_dropdown, scene_audio_3_dropdown, scene_audio_4_dropdown, scene_audio_5_dropdown, scene_audio_6_dropdown])
    btn_merge_audios.click(merge_audios, inputs=None, outputs=None)
    btn_merge_videos.click(merge_videos_moviepy, inputs=None, outputs=[merged_video])

    btn_generate_story.click(generate_story, inputs=[ta_idea], outputs=[ta_characters, ta_setting, ta_plot])

    scene_audio_1_dropdown.change(play_audio, inputs=[scene_audio_1_dropdown], outputs=[scene_audio_1])
    scene_audio_2_dropdown.change(play_audio, inputs=[scene_audio_2_dropdown], outputs=[scene_audio_2])
    scene_audio_3_dropdown.change(play_audio, inputs=[scene_audio_3_dropdown], outputs=[scene_audio_3])
    scene_audio_4_dropdown.change(play_audio, inputs=[scene_audio_4_dropdown], outputs=[scene_audio_4])
    scene_audio_5_dropdown.change(play_audio, inputs=[scene_audio_5_dropdown], outputs=[scene_audio_5])
    scene_audio_6_dropdown.change(play_audio, inputs=[scene_audio_6_dropdown], outputs=[scene_audio_6])
    
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8000)