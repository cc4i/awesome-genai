import json
import os
import http.client
import uuid
import requests
import datetime
import threading
from unstructured.partition.html import partition_html
from utils.llm import call_llm


# Function to scrape a page
def scrape_page(req, srs):
    page_url=req.get('link')
    browserless_url = os.getenv("BROWSERLESS_URL")
    payload = json.dumps({"url": page_url})
    headers = {'cache-control': 'no-cache', 'content-type': 'application/json'}
    response = requests.request("POST", browserless_url, headers=headers, data=payload)
    elements = partition_html(text=response.text)
    content = "\n\n".join([str(el) for el in elements])
    # content = [content[i:i + 8000] for i in range(0, len(content), 8000)]

    pid = uuid.uuid4()
    srs.append({
        "post_id": f"{pid}",
        "page_url": page_url,
        "title": req.get('title'),
        "snippet": req.get('snippet'),
        "content": content,
        "content_summary": f"Title: {req.get('title')}, Snippet: {req.get('snippet')}, Link: {req.get('link')}, ",
        "scraped_at": datetime.datetime.now(datetime.UTC),
    })


# Function to search through Search Engine
top_result_to_return = 5
def search_engine(s_path, query, date_range):
    
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
        "q": query,
        "num": top_result_to_return,
        #TODO To be configured.
        "location": "Singapore",
        "gl": "sg",
        # Past 24H/r week/w
        "tbs": "qdr:"+date_range
    })
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'content-type': 'application/json'
    }
    conn.request("POST", s_path, payload, headers)
    res = conn.getresponse()
    data = res.read()
    if s_path == "/news":
        results = json.loads(data).get('news')
    else:
        results = json.loads(data).get('organic')
    
    return results


def do_scraping(results):
    srs = []
    sthreads = []
    for result in results:
        try:
            print('\n'.join([
                f"Title: {result.get('title')}", f"Link: {result.get('link')}",
                f"Snippet: {result.get('snippet')}", "\n-----------------"
            ]))

            th = threading.Thread(target=scrape_page, args=(result, srs))
            th.start()
            print(f"Thread {th.name}: {th.ident} is running...")
            
            sthreads.append(th)
        except KeyError:
            next

    # Waiting thread to be finish
    for th in sthreads:
        th.join()

    return srs

# Function to search Google News
def search_g_news(query, date_range):
    s_path = "/news"
    return search_engine(s_path, query, date_range)

# Function to search Google Search
def search_g_engine(query, date_range):
    s_path = "/search"
    return search_engine(s_path, query, date_range)
    
# Generate keywords
def gen_keywords4google(context)->str:

    system_instruction = """
    You are a Google Search expert with extensive experience in optimizing products searching results. Very carefully analyze the provided context and finish following tasks.
    """
    prompt = f"""
    *CONTEXT*
    {context}

    *TASKS*
    1. Identify the real, commercially products or catagories, do not include generic words, accessories of products.
    2. Generate the best Google search keywords, which could leads the best search result.

    *OUTPUT FORMAT*
    JSON format with the following structure:
    """ + """
    {
        "products": [
            "Product Name1",
            "Product Name2",
            "Product Name3"
            // ... more products
        ],
        "keywords": [
            "keyword1",
            "keyword2",
            "keyword3"
            // ... more keywords
        ]
    }
    """
    return call_llm(system_instruction, prompt, "", "gemini-2.0-flash-thinking-exp-01-21")


def  extract_key_products(orginal_context:str, content:str):
    system_instruction = f"""
    You are an e-commerce expert specializing in product identification. Analyze the provided content thoroughly and finish following tasks.
    """

    prompt = f"""
    *CONTENT*
    {content}

    *TASKS*
    1. Identify real, commercially available products from content, which replated to {orginal_context}.
    2. Exclude generic words and words that are brand related non-product words.

    *OUTPUT FORMAT*
    JSON format with the following structure:
    """ + """
    {
        "products": [
            "Product Name 1",
            "Product Name 2",
            "Product Name 3" 
        ]
    }
    """
    return call_llm(system_instruction, prompt, "")

def  extract_key_atrributes(orginal_context:str, content:str):
    system_instruction = f"""
    You are an e-commerce expert specializing in product management. Analyze the provided content thoroughly and finish following tasks.
    """

    prompt = f"""
    *CONTENT*
    {content}

    *TASKS*
    1. Identify attributes to describe the products, which replated to {orginal_context}.
    2. Exclude generic words.

    *OUTPUT FORMAT*
    JSON format with the following structure:
    """ + """
    {
        "products": [
            "Product Name 1",
            "Product Name 2",
            "Product Name 3" 
        ]
    }
    """

    return call_llm(system_instruction, prompt, "")


def trending_summary(content:str, research_sites:list):
    system_instruction =f"""
     You are an e-commerce analyst. Your task is to analyze trending from provide context and give concise summary.  
    """
    prompt = f"""

    *CONTEXT*
    Trending Words: {content}
    Source information: {research_sites}

    *INSTRUCTIONS*

    1. Analyze the provided trending words and their frequency.
    2. Identify the overarching theme or topic that connects these trending words.  If no single theme emerges, classify the trends into multiple categories.
    3. Focus on the most prominent trends and their potential impact on the e-commerce landscape.
    4. If the trending words do not indicate a clear trend, state that "No discernible trend is identified based on the provided data."

    """
    return call_llm(system_instruction, prompt, "")

def remove_nosie_words(product:str, content:str):
    prompt = f"""
    From the following JSON, identify and the names of real, commercially {product} products Remove not related product.

    {content}

    OUTPUT AS SAME JSON FORMAT!!!
    """
    print(prompt)

    return call_llm("", prompt, "")

def stat_products(content):
    pp = {}
    pp_count = {}
    print("===========================")
    print(content)
    print("===========================\n")
    for c in content:
        try:
            products = c.get("products")
            for p in products:
                if p in pp:
                    pp_count[p] += 10
                else:
                    pp_count[p] = 10
                pp[p]=p
        except Exception as e:
            print(f"Error at stat_products(): {e}")
            continue
    return {
        "items": list(pp.keys()),
        "rates": list(pp_count.values()),
    }