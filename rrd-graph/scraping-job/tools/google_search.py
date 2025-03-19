import json
import os
import http.client
import uuid
import requests
import datetime
import threading
from unstructured.partition.html import partition_html
from shared.db.sql_cn import SqlCN
from shared.db.tb_posts import PostType



class GoogleSearch:
    def __init__(self, sqlcn: SqlCN, serper_api_key: str, browserless_url: str):
        self.sqlcn = sqlcn
        self.serper_api_key = serper_api_key
        self.browserless_url = browserless_url

    # Function to scrape a page
    def scrape_page(self, req, abbr, srs):
        page_url=req.get('link')
        browserless_url = self.browserless_url
        payload = json.dumps({"url": page_url})
        headers = {'cache-control': 'no-cache', 'content-type': 'application/json'}
        response = requests.request("POST", browserless_url, headers=headers, data=payload)
        elements = partition_html(text=response.text)
        content = "\n\n".join([str(el) for el in elements])
        # content = [content[i:i + 8000] for i in range(0, len(content), 8000)]

        pid = uuid.uuid4()
        srs.append({
            "post_id": f"{abbr}-{pid}",
            "content": content,
            "content_summary": f"Title: {req.get('title')}, Snippet: {req.get('snippet')}, Link: {req.get('link')}, ",
            "scraped_at": datetime.datetime.now(datetime.UTC),
            #TODO: Using same time as scraped_at for created_at for now, don't know how to get right time!!!
            "created_at": datetime.datetime.now(datetime.UTC),
        })

    def save_page_content(self, thread_id, platform_id, contents):
        if len(contents) > 0:
            rows_to_insert=[]
            for v in contents:
                row = {
                    "post_id": v['post_id'],
                    "thread_id": thread_id,
                    "platform_id": platform_id,
                    "content": v['content'],
                    "summary": v['content_summary'],
                    "conent_type": PostType.PAGE.value,
                    "created_at": v.get('created_at'),
                    "scraped_at": v.get('scraped_at').isoformat(),
                }
                rows_to_insert.append(row)
            self.sqlcn.posts.create_posts_in_batch(rows_to_insert)


    # Function to search through Search Engine
    def search_engine(self, s_path, query):
        top_result_to_return = 10
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({
            "q": query,
            "num": top_result_to_return,
            #TODO To be configured.
            "location": "Singapore",
            "gl": "sg",
            # Past 24H
            "tbs": "qdr:d"
        })
        headers = {
            'X-API-KEY': self.serper_api_key,
            'content-type': 'application/json'
        }
        conn.request("POST", s_path, payload, headers)
        res = conn.getresponse()
        data = res.read()
        if s_path == "/news":
            results = json.loads(data).get('news')
            abbr = "gn"
        else:
            results = json.loads(data).get('organic')
            abbr = "gs"
        
        srs = []
        sthreads = []
        for result in results[:top_result_to_return]:
            try:
                print('\n'.join([
                    f"Title: {result.get('title')}", f"Link: {result.get('link')}",
                    f"Snippet: {result.get('snippet')}", "\n-----------------"
                ]))

                th = threading.Thread(target=self.scrape_page, args=(result, abbr, srs))
                th.start()
                print(f"Thread {th.name}: {th.ident} is running...")
                
                sthreads.append(th)
            except KeyError:
                next

        # Waiting thread to be finish
        for th in sthreads:
            th.join()

        # for th in sthreads:
        #     ret, content = th.result
        #     # Using UUID as post_id for search result
        #     pid = uuid.uuid4()
        #     srs.append({
        #         "post_id": f"{abbr}-{pid}",
        #         "content": content,
        #         "content_summary": f"Title: {ret.get('title')}, Snippet: {ret.get('snippet')}, Link: {ret.get('link')}, ",
        #         "scraped_at": datetime.datetime.now(datetime.UTC),
        #     })

        return srs

    # Function to search Google News
    def search_g_news(self, query):
        s_path = "/news"
        return self.search_engine(s_path, query)

    # Function to search Google Search
    def search_g_engine(self, query):
        s_path = "/search"
        return self.search_engine(s_path, query)






def test():
    json_string = """
    {'primaryKeywords': ['iPhone 16', 'Apple Watch Series 10', 'AirPods 4', 'iOS 18', 'Apple Glowtime Event', 'Apple Intelligence AI', 'Apple September Event'], 'secondaryKeywords': ['iPhone 16 vs iPhone 15', 'iPhone 16 Pro Max', 'iPhone 16 specs', 'Apple Watch Series 10 features', 'AirPods 4 release date', 'iOS 18 features', 'iOS 18 release date', 'Apple AI features', 'Apple event Cupertino', 'Apple September event review', 'iPhone 16 vs Huawei Mate 60', 'iPhone 16 vs Xiaomi 14', 'Apple Watch Series 10 vs Samsung Galaxy Watch', 'AirPods 4 vs AirPods Pro', 'Apple event livestream', 'Apple product launch', 'Apple Glowtime Event reviews', 'Apple event highlights', 'Apple Intelligence AI review']}
    """
    serper_api_key=os.environ['SERPER_API_KEY']
    browserless_url=os.environ['BROWSERLESS_URL']
    gs = GoogleSearch(serper_api_key=serper_api_key, browserless_url=browserless_url)
    kys = json.loads(json_string.replace("'", '"'))
    # for p in kys['primaryKeywords']:
    #     print(gs.search_g_news(p))
    for s in kys['secondaryKeywords']:
        rs=gs.search_g_engine(s)
        for r in rs:
            print(r)
            print("------------------\n")

    

# main for local test
if __name__ == "__main__":
    test()