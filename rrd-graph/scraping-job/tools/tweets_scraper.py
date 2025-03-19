import os
import time
import datetime
import tweepy
from shared.db.sql_cn import SqlCN
from shared.db.tb_posts import PostType

class TweetsScraper:

    def __init__(self, sqlcn:SqlCN, bearer_token, consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None):
        self.sqlcn = sqlcn
        self.bearer_token = bearer_token
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    
    # Function to search tweets, One query(str) for matching Tweets. Up to 1024 characters.
    # query: https://developer.x.com/en/docs/x-api/tweets/search/integrate/build-a-query
    def searh_tweets(self, query, next_token=None):
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=False)

        tss = []
        # TODO: Come back later to process paginated tweets
        # max_loop = 10 for now
        for i in range(1, 11):
            # https://docs.tweepy.org/en/stable/client.html#search-tweets
            try: 
                response = client.search_recent_tweets(query, next_token=next_token)
                print("------------------")
                print(response.meta)
                print("------------------")
            except Exception as e:
                print(e)
                break
            
            ids = []
            tsd = {}
            if response.meta['result_count']!=0:
                for twe in response.data:
                    print(twe.id)
                    print(twe.text)
                    print("------------------")
                    ids.append(twe.id)
                    t = {
                        "post_id": f"tw-{twe.id}",
                        "content": [twe.text],
                        "content_summary": twe.text,
                        "scraped_at": datetime.datetime.now(datetime.UTC),
                        "created_at": datetime.datetime.now(datetime.UTC),
                    }
                    tsd[twe.id] = t
                
                if response.meta['next_token'] is not None:
                    next_token=response.meta['next_token']

                # Tweet Respose: https://developer.x.com/en/docs/x-api/tweets/lookup/api-reference/get-tweets-id
                try:
                    for id in ids:
                        tweet = client.get_tweet(ids, tweet_fields=["created_at", "public_metrics"])
                        print(tweet)
                        time.sleep(5)
                        tsd[id]["likes"] = tweet.data.public_metrics['like_count']
                        tsd[id]["shares"] = tweet.data.public_metrics['retweet_count']
                        tsd[id]["comments"] = tweet.data.public_metrics['reply_count']
                        tsd[id]["created_at"] = tweet.data.created_at
                except Exception as e:
                    print(e)
                finally:
                    print("An unexpected error occurred.")
                for (k, v) in tsd.items():
                    tss.append(v)
        return tss

    def save_tweets(self, thread_id, platform_id, contents):
        if len(contents) > 0:
            rows_to_insert=[]
            for v in contents:
                row = {
                    "post_id": v['post_id'],
                    "thread_id": thread_id,
                    "platform_id": platform_id,
                    "user_id": v.get('user_id'),
                    "content": v['content'],
                    "conent_type": PostType.POST.value,
                    "likes": v.get('likes'),
                    "shares": v.get('shares'),
                    "comments": v.get('comments'),
                    "created_at": v.get('created_at'),
                    "scraped_at": v.get('scraped_at').isoformat(),
                }
                rows_to_insert.append(row)
            self.sqlcn.posts.create_posts_in_batch(rows_to_insert)



def test():
    ts = TweetsScraper(bearer_token=os.environ['X_BEARER_TOKEN'])
    ts.searh_tweets(query='(glowtime OR "Glowtime event" OR "Apple event" OR "iPhone 16" OR "Apple Watch Series 10" OR "AirPods 4" OR "iOS 18" OR "Apple Intelligence") (apple OR iPhone OR iPad OR Mac OR "Apple Watch" OR Huawei OR Xiaomi) -is:retweet lang:en')

# main for local test
if __name__ == "__main__":
    test()