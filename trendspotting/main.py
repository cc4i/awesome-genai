import json
import gradio as gr
import pandas as pd
from random import random, randint
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.llm import gen_images
from utils.llm import call_llm
from utils.google import gen_keywords4google
from utils.google import search_g_engine
from utils.google import search_g_news
from utils.google import do_scraping
from utils.google import extract_key_atrributes
from utils.google import extract_key_products
from utils.google import stat_products
from utils.google import  trending_summary




#TODO: 
# Feb21, discussed with Edi
# - Summary based output of analysis : trending/source/chart
# - Multiple data sources?(no time)
# - Last analysis history and display history data

#Mar 15
# - Remove noise words 
# - Changing theme



def get_top_10_sorted_dict(input_dict):
    """
    Sorts a dictionary by value in descending order and returns the top 10 items.

    Args:
        input_dict (dict): The dictionary to sort.

    Returns:
        dict: A dictionary containing the top 10 items sorted by value, or all items if less than 10.
    """
    sorted_items = sorted(input_dict.items(), key=lambda item: item[1], reverse=True)
    top_10_items = dict(sorted_items[:10])  # Convert back to dict, and slice to top 10
    return top_10_items


def google_search(keywords_dict, date_range)-> tuple[dict, list]:

    print("keywords_dict------------")
    print(keywords_dict)
    print("keywords_dict------------\n\n")

    if date_range=="Last 24H":
        date_range="d"
    elif date_range=="Last week":
        date_range="w"
    elif date_range=="Last month":
        date_range="m"
    
    primary_keywords = keywords_dict.get("keywords")
    all_serper_results = []
    for pk in primary_keywords:
        print(pk)
        sp_results = search_g_engine(pk, date_range)
        # sp_results = search_g_news(pk)
        for sp_result in sp_results:
            print(sp_result.get("title"))
            print(sp_result.get("link"))
            print(sp_result.get("snippet"))
            all_serper_results.append(sp_result)

    return keywords_dict, all_serper_results


def generate_search_strategy(message):
    # model_id: gemini-2.0-flash, gemini-2.0-flash-thinking-exp-01-21
    return gen_keywords4google(message, "gemini-2.0-flash-thinking-exp-01-21")


def analyze_question(message, search_strategy, analysed_by, date_range):
    print(f"search_strategy: {search_strategy}")
    if search_strategy is None:
        keywords = generate_search_strategy(message)
        keywords_dict = json.loads(keywords)
    else:
        keywords_dict = search_strategy
    keywords, research_list = google_search(keywords_dict, date_range)
    
    research_sites=""
    non_duplicated_product={}
    
    trends = []
    srs = do_scraping(research_list)
    for s in srs:
        try:

            if analysed_by=="Products":
                x=json.loads(extract_key_products(keywords.get("products"), s.get("content")))
            elif analysed_by=="Attribute of products":
                x=json.loads(extract_key_atrributes(keywords.get("products"), s.get("content")))
            
            research_sites+=s.get("title")+"\n"
            research_sites+=s.get("page_url")+"\n"
            # Count products to display (TOO MUCH)
            # for p in x.get("products"):
            #     non_duplicated_product[p]="1"
            # research_sites+=" #".join(list(non_duplicated_product.keys()))
            research_sites+="...\n\n"
            
            print("x-------")
            print(x)
            print("x-------\n")
            trends.append(x)
        except Exception as e:
            print(f"Error at analyze_question(): {e}")


    sp = stat_products(trends)
    
    print(sp)
    summary = trending_summary(sp, research_sites)

    all_items = {}
    total = 0
    for rate in sp.get("rates"):
        total = total + rate
    print(f"total: {total}")
    for item in sp.get("items"):
        print(f"item: {item}, rate: {sp.get('rates')[sp.get('items').index(item)]}")
        all_items[item]=float(sp.get("rates")[sp.get("items").index(item)]/total)

    print(all_items)

    # return pd.DataFrame(sp), "\n".join(sp.get("items")), research_sites, summary
    return pd.DataFrame(sp), get_top_10_sorted_dict(all_items), "\n".join(sp.get("items")), research_sites, summary



def show_images(message):
    generated_images = gen_images(message, "")
    print(f"generated_images: {len(generated_images)}")
    ims = []
    for generated_image in generated_images:
        image = Image.open(BytesIO(generated_image.image.image_bytes))
        ims.append(image)
    return ims



empty_trends_data = pd.DataFrame(
    {
        "items": [],
        "rates": [],
    }
)

with gr.Blocks() as demo:
    gr.Markdown("""
                # Trend Spotting
                Ask researchers to find out what trends are...
                """)
    with gr.Row():
        with gr.Column(scale=1):
            gr.Radio(label="Sources", choices=["Google","Instagram","Youtube"], value="Google", interactive=True)
            gr.Markdown("""
            ## Examples:
            - The most popular mobile phone in Singapore 2025
            - The lego set for kids between 7 and 12 in Singapore 2025
            """)
            tb_search_keywords = gr.Textbox(label="What to research", value="The mobile phone in Singapore 2025", lines=6, interactive=True)
            dd_search_strategy = gr.JSON(label="Search strategy", show_indices=True)
            btn_search_strategy = gr.Button("", icon="images/gemini-star.png")
            dd_analysed_by = gr.Dropdown(label="Analysed by", choices=["Products", "Attribute of products"], interactive=True, scale=1)
            dd_date_range = gr.Dropdown(label="Date range", choices=["Last 24H", "Last week", "Last month"], interactive=True,scale=1)
            btn_research = gr.Button("Research", icon="images/gemini-star.png", scale=1)
            
        # with gr.Column():
        #     gr.Markdown("Sample you may want to ask: * The most popular mobile phone in Singapore 2025")
        with gr.Column(scale=3):
            sp_trends_plot = gr.BarPlot(
                empty_trends_data,
                x="items",
                x_label_angle=90,
                y="rates",
                title="Words count",
                height=600,
            )
            ta_ts_output = gr.Textbox(value="...", label="Trending Summary", lines=10, text_align='left', show_label=True, show_copy_button=True, interactive=True)
            lb_kw_output = gr.Label(label="Top 10 of Trending words", show_heading=False)
            ta_kw_output = gr.Textbox(value="...", label="Trending words", lines=6, text_align='left', show_label=True, show_copy_button=True, interactive=True)
            ta_as_output = gr.Textbox(value="...", label="Analysed sources FRom", lines=6, text_align='left', show_label=True, show_copy_button=True, interactive=True)
            tb_input_image = gr.Textbox(label="What it looks like", value="", interactive=True)
            btn_show_image = gr.Button("SHow Images", scale=0)
            gallery = gr.Gallery(label="Generated images", show_label=False, elem_id="gallery", columns=[3], rows=[1], object_fit="contain", height="auto")
    
    btn_search_strategy.click(generate_search_strategy, inputs=[tb_search_keywords], outputs=[dd_search_strategy])
    pt = btn_research.click(analyze_question, inputs=[tb_search_keywords, dd_search_strategy, dd_analysed_by, dd_date_range], outputs=[sp_trends_plot, lb_kw_output, ta_kw_output, ta_as_output, ta_ts_output])
    # TODO: add actions after click =>pt.then()
    btn_show_image.click(show_images, inputs=[tb_input_image], outputs=[gallery])   

if __name__ == "__main__":
    demo.launch()