import pandas as pd
from random import randint, random
import gradio as gr
import os
from dateutil import parser
import json
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from google.cloud import storage
from pathlib import Path
from shared.db.sql_cn import SqlCN
from c_utils import promot_template_4_twitter, promot_template_4_google
from c_utils import call_llm_sdk
from c_utils import x_thread_by_id
from c_utils import semtiment_score_by
from c_utils import sentiment_level_by
from c_utils import sentiment_distribution_by
from c_utils import x_threads
from c_utils import last_playbook
from c_utils import generate_playbook
from c_utils import x_add_thread
from c_utils import x_update_thread
from c_utils import x_delete_thread
from c_utils import x_posts






# All
fixed_platforms = ['*', 'twitter', 'google-search', 'google-news' ]
project_id = os.getenv("PROJECT_ID") or "multi-gke-ops"
location = os.getenv("LOCATION") or "us-central1"
policy_bucket = os.getenv("POLICY_BUCKET") or "simulating_policy_bucket-multi-gke-ops"
policy_running_folder = os.getenv("SIMULATING_POLICY_FOLDER") or "running_polices"



def rescale(select: gr.SelectData):
    return select.index


# @gr.on(inputs=[tb_thread_id, dd_platform_id, dt_start, dt_end], outputs=time_graphs)
def refresh_data(thread_id, platform_id, start, end):
    if isinstance(start, datetime):
        start = start.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(end, datetime):
        end = end.strftime('%Y-%m-%d %H:%M:%S')
    print(f"start={start}, end={end}")

    ss_data = semtiment_score_by(
        thread_id=thread_id, 
        platform_id=platform_id,
        start=start,
        end=end
    )

    sl_data = sentiment_level_by(
        thread_id=thread_id,
        start=start,
        end=end
    )
    ds_data = sentiment_distribution_by(
        platform_id=platform_id,
        thread_id=thread_id,
        start=start,
        end=end
    )
    return ss_data, sl_data, sl_data, ds_data


def read_policy(blob_name):
    try:
        client = storage.Client()
        blob = client.bucket(policy_bucket).blob(blob_name)
        return blob.download_as_text()
    except Exception as e:
        print(e)



def list_policies_in_bucket():
    client = storage.Client()
    bucket_client = client.bucket(policy_bucket)
    blobs = bucket_client.list_blobs(prefix=policy_running_folder)

    blob_names = []
    for blob in blobs:
        if blob.name.endswith(".json"):
            blob_names.append(blob.name)
    print(f"Found: {blob_names}")
    return blob_names


def upload_to_bucket(blob_name, file):
    client = storage.Client()
    bucket = client.bucket(policy_bucket)
    blob = bucket.blob(blob_name)
    print(file)
    blob.upload_from_filename(file)
    
    return blob.name

def upload_file(file):
    print(file)
    blob_name = f"{policy_running_folder}/{os.path.basename(file)}"
    print(blob_name)
    print(upload_to_bucket(blob_name, file))
    return file, Path(file).read_text(), gr.Dropdown(choices=list_policies_in_bucket())

def promot_template(platform_id, context, instructions):
    print(f"platform_id: {platform_id}")
    if platform_id == "twitter":
        return promot_template_4_twitter(context, instructions)
    elif platform_id == "google-search" or platform_id == "google-news":
        return promot_template_4_google(context, instructions)




def retrieve_thread_id(evt: gr.SelectData, df):
    print(evt.index[0],evt.index, evt.value, evt.target)
    print(df.iloc[evt.index[0], :])
    thread_id = df.iloc[evt.index[0], 0]
    # display_name = df.iloc[evt.index[0], 1]
    return x_thread_by_id(thread_id)



with gr.Blocks(theme=gr.themes.Default(), title=f"RRD Pro") as rrd_console:
    gr.Markdown("## Realtime Reputation Defender Pro")
    with gr.Tab("Sentiment Dashboard"):
        with gr.Row():
            tb_thread_id = gr.Textbox(label="Thread ID", value="1", interactive=True)
            dd_platform_id = gr.Dropdown(choices=fixed_platforms, value="*", label="Media Platform", interactive=True)
            dt_start = gr.DateTime((datetime.now()- timedelta(hours = 4)).strftime('%Y-%m-%d %H:%M:%S'), label="Start", type="datetime")
            dt_end = gr.DateTime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), label="End", type="datetime")
            apply_btn = gr.Button("Apply", scale=0)

        with gr.Row():
            ss_data = semtiment_score_by(
                thread_id=tb_thread_id.value, 
                platform_id=dd_platform_id.value,
                start=dt_start.value,
                end=dt_end.value
            )

            sl_data = sentiment_level_by(
                thread_id=tb_thread_id.value,
                start=dt_start.value,
                end=dt_end.value
            )
            ds_data = sentiment_distribution_by(
                thread_id=tb_thread_id.value,
                platform_id=dd_platform_id.value,
                start=dt_start.value,
                end=dt_end.value
            )
            group_by = gr.Radio(["None", "30m", "1h", "4h", "1d"], value="None", label="Group by")
            aggregate = gr.Radio(["sum", "mean", "median", "min", "max"], value="sum", label="Aggregation")

        with gr.Row():
            with gr.Column(scale=1, min_width=500):
                sl_by_time_scatter = gr.ScatterPlot(
                    sl_data,
                    x="time",
                    y="sentiment_level",
                    color="sentiment_level",
                )
            with gr.Column(scale=1, min_width=500):
                sl_by_time_line = gr.LinePlot(
                    sl_data,
                    x="time",
                    y="sentiment_level",
                    color="platform",
                )
        with gr.Row():
            ss_by_time_bar = gr.BarPlot(
                ss_data,
                x="time",
                y="sentiment_score",
                color="sentiment_labels",
            )
        with gr.Row():
            ds_bar = gr.BarPlot(
                ds_data,
                x= "platform",
                y= "count",
                y_bin=200,
                color = "sentiment_label"
            )

        time_graphs = [ss_by_time_bar, sl_by_time_scatter, sl_by_time_line, ds_bar]
        group_by.change(
            lambda group: [gr.ScatterPlot(x_bin=None if group == "None" else group)] * len(time_graphs),
            group_by,
            time_graphs
        )
        aggregate.change(
            lambda aggregate: [gr.ScatterPlot(y_aggregate=aggregate)] * len(time_graphs),
            aggregate,
            time_graphs
        )
    

        apply_btn.click(
            fn=lambda tb_thread_id, dd_platform_id, dt_start, dt_end: refresh_data(tb_thread_id, dd_platform_id, dt_start, dt_end), 
            inputs=[tb_thread_id, dd_platform_id, dt_start, dt_end],
            outputs=time_graphs)
        
    with gr.Tab("Content Analysis"):
        tb_pt_thread_id = gr.Textbox(label="Thread ID")
        btn_post_query = gr.Button("Query")
        df_top100_worst_threads = gr.Dataframe(
            value=pd.DataFrame(),
            headers=["post_id", "thread_id", "platform_id", "content", "scraped_at"],
            datatype=["str", "str", "str", "str", "date"],
            max_height=400,
            label= "Top 100 Worst Posts",
            show_label=True,
        )
        
        btn_post_query.click(x_posts, inputs=tb_pt_thread_id, outputs=df_top100_worst_threads)
    

    with gr.Tab("Thread"):
        # gr.ChatInterface(random_response, type="messages").launch()
        with gr.Row():
            th_data=x_threads()
            print(len(th_data))
            df_threads = gr.Dataframe(
                value=pd.DataFrame(
                    data=th_data,
                    columns=["thread_id", "display_name", "platform_ids", "created_at"],
                ),
                headers=["Thread ID", "Thread Name", "Platforms", "Created_at"],
                datatype=["str", "str", "str", "str"],
                max_height=200,
                show_label=True,
            )
            
        with gr.Row():
            tb_tt_thread_id = gr.Textbox(value="", interactive=True, label="Thread ID")
            tb_tt_thread_name = gr.Textbox(value="", interactive=True, label="Thread Name")

        with gr.Row():
            with gr.Column(scale=1):
                tb_context = gr.Textbox(value="", lines=8, label="Context")
                tb_instructions = gr.Textbox(value="", lines=4, label="Instructions")
                cg_platform = gr.CheckboxGroup(choices=["twitter", "google-search", "google-news"],label="Platform", interactive=True)
            with gr.Column(scale=1):
                with gr.Row():
                    rd_template = gr.Radio(choices=["twitter", "google-search", "google-news"],label="Prompt templates", interactive=True)
                with gr.Row():
                    ta_prompt = gr.TextArea(
                        value="Click platform to tweak prompt and get better search strategy...",
                        label="!!!Tweak prompt!!!", lines=16, text_align='left', show_label=True, show_copy_button=True, interactive=True
                    )
            rd_template.change(promot_template, inputs=[rd_template, tb_context, tb_instructions], outputs=[ta_prompt])
            tb_context.change(promot_template, inputs=[rd_template, tb_context, tb_instructions], outputs=[ta_prompt])
            tb_instructions.change(promot_template, inputs=[rd_template, tb_context, tb_instructions], outputs=[ta_prompt])
        with gr.Row():
            btn_add_thread = gr.Button(value="Add")
            btn_delete_thread = gr.Button(value="Delete")
            btn_update_thread = gr.Button(value="Update")
        with gr.Row():
            ta_keywords = gr.TextArea(value="", label="Keywords", lines=4)
        with gr.Row():
            btn_generate = gr.Button("Generate Keywords")
            btn_update_kws = gr.Button("Update Keywords >>> Job")
        
        # btn_query.click(x_thread_by_id, inputs=[tb_tt_thread_id], outputs=[tb_tt_thread_name, tb_context, tb_instructions,cg_platform])
        btn_generate.click(call_llm_sdk, inputs=ta_prompt, outputs=ta_keywords)
        df_threads.select(fn=retrieve_thread_id, inputs=df_threads, outputs=[tb_tt_thread_id,tb_tt_thread_name, tb_context, tb_instructions,cg_platform])
        btn_add_thread.click(x_add_thread, inputs=[tb_tt_thread_name, tb_context, tb_instructions, cg_platform], outputs=[df_threads])
        btn_delete_thread.click(x_delete_thread, inputs=[tb_tt_thread_id], outputs=[df_threads])
        btn_update_thread.click(x_update_thread, inputs=[tb_tt_thread_id, tb_tt_thread_name, tb_context, tb_instructions, cg_platform], outputs=[df_threads])



    with gr.Tab("Playbook"):
        with gr.Row():
            tb_pb_thread_id = gr.Text(value = tb_tt_thread_id.value, interactive=True, label="Thread ID")
            btn_q_palybook = gr.Button("Query")
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    ta_summary = gr.TextArea(label="Summary")
                with gr.Row():
                    ta_sereverity = gr.TextArea(label="Severity")
                    ta_category = gr.TextArea(label="Category")
                with gr.Row():
                    ta_plan = gr.TextArea(label="Stategy Plan")
            with gr.Column(scale=1):
                with gr.Row():
                    ta_playbook_prompt = gr.TextArea(
                        value="",
                        label="!!!Tweak Playbook Prompt (DO NOT CHANGE OUTPUT FORMAT)!!!", lines=24, 
                        text_align='left', show_label=True, show_copy_button=True, interactive=True
                    )
                with gr.Row():
                    btn_gen_palybook = gr.Button("Regenerate")
        with gr.Row():
            with gr.Column(scale=1):
                gr.DataFrame(
                    label="Engaged Content",
                    value=pd.DataFrame(),
                    headers=["ID", "Origin Content", "Engaged Content"],
                    datatype=["str", "str", "str"],
                )
            with gr.Column(scale=1):
                with gr.Row():
                    gr.TextArea(label="Stategy Plan")
                with gr.Row():
                    gr.Button("Postive!!!")
        
        btn_q_palybook.click(last_playbook, inputs=tb_pb_thread_id, outputs=[ta_summary, ta_sereverity, ta_category, ta_plan, ta_playbook_prompt])
        btn_gen_palybook.click(generate_playbook, inputs=ta_playbook_prompt, outputs=[ta_summary, ta_sereverity, ta_category, ta_plan, ta_playbook_prompt])


    with gr.Tab("Load Generator"):
        gr.Markdown("Upload load policy files and then you'll be able to generate Tweets!")
        policy_list=gr.Dropdown(
            choices=list_policies_in_bucket(), value=None, interactive=True,
            label="Animal", info="Exsited simulating policies"
        )
        
        file_output = gr.File()
        json_viewer = gr.JSON(file_output.value)
        upload_button = gr.UploadButton("Click to Upload a File", file_types=["file"], file_count="single")
        upload_button.upload(upload_file, inputs=upload_button, outputs=[file_output, json_viewer,policy_list])
        policy_list.select(read_policy, inputs=policy_list, outputs=json_viewer)

    with gr.Tab("Webhooks"):
        gr.Markdown("TODO")

if __name__ == "__main__":
    rrd_console.launch(server_name="0.0.0.0")