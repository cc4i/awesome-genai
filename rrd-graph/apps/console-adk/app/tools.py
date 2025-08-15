
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.




import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent.parent.parent.parent / "libs"
sys.path.insert(0, str(libs_path))


from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
# import pandas as pd
from rrd_shared.db.sql_cn import SqlCN

from google.genai import Client
from google.adk.tools.tool_context import ToolContext
from google.genai import types

# All envariables
load_dotenv()

# Db
sqlcn = SqlCN()

def thread_id_by(ctx:str) -> str:
    """
    Based on context provide to extract the most likely thread id for further process.
    Args:
        ctx: The context related to the thread.

    Returns:
         A thread id.
    """
    # all_threads = sqlcn.threads.list_threads()
    thread_id="1"
    return thread_id


def last_sentiment_distribution_by(thread_id:str, platform_id:str, duration:str) -> dict:
    """
    List all sentiment distrubution data.

    Args:
        thread_id: The Id of Thread.
        platform_id: The name of source platform, one of value from ['twitter', 'google-search', 'google-news', 'instagram']
        duration: The time range from the past to the present, the available ranges are: 
            - 1h (from 1 hour ago to now)
            - 24h (from 24 hours ago to now)
            - 7d (from 7 days ago to now )
            - 30d (from 30 days ago to now)

    Returns:
         A dictionary containing the distrubution info as per duration.
    """

    # Find out duration
    if duration == "1h":
        h = 1
    elif duration == "24h":
        h = 24
    elif duration == "7d":
        h = 7*24
    elif duration == "30d":
        h = 30*24
    else:
        h=24
    nn= datetime.now()
    nl = nn - timedelta(hours=h)
    start = nl.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    end = nn.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    sd_data = sqlcn.posts.sentiment_distribution_by_time(thread_id=thread_id, platform_id=platform_id, start=start, end=end)
    counts=[]
    sentiment_labels=[]
    platforms=[]
    if len(sd_data) > 0:
        for sd in sd_data:
            counts.append(sd.get("positive"))
            counts.append(sd.get("neutral"))
            counts.append(sd.get("negtive"))
            sentiment_labels.append("positive")
            sentiment_labels.append("neutral")
            sentiment_labels.append("negtive")
            platforms.append(sd.get("platform_id"))
            platforms.append(sd.get("platform_id"))
            platforms.append(sd.get("platform_id"))
        
        return {
            "count": counts,
            "sentiment_label": sentiment_labels,
            "platform": platforms
        }
    else:
        return {}


def last_semtiment_score_by(thread_id:str, platform_id:str, duration:str) -> dict:
    """
    List all posts with source platform, semtiment score and semtiment label

    Args:
        thread_id: The Id of Thread.
        The name of source platform, one of value from ['twitter', 'google-search', 'google-news', 'instagram'].
        duration: The time range from the past to the present, the available ranges are: 
            - 1h (from 1 hour ago to now)
            - 24h (from 24 hours ago to now)
            - 7d (from 7 days ago to now )
            - 30d (from 30 days ago to now)

    Returns:
        A dictionary containing a list of post info.
    """

    # Find out duration
    if duration == "1h":
        h = 1
    elif duration == "24h":
        h = 24
    elif duration == "7d":
        h = 7*24
    elif duration == "30d":
        h = 30*24
    else:
        h=24
    nn= datetime.now()
    nl = nn - timedelta(hours=h)
    start = nl.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    end = nn.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

    return semtiment_score_by(thread_id, platform_id, start, end)


def semtiment_score_by(thread_id:str, platform_id:str, start:str, end:str) -> dict:
    """
    List all posts with source platform, semtiment score and semtiment label

    Args:
        thread_id: The Id of Thread.
        The name of source platform, one of value from ['twitter', 'google-search', 'google-news', 'instagram'].
        start: Start date of data, format: "%Y-%m-%d %H:%M:%S"
        end: End date of date, format: "%Y-%m-%d %H:%M:%S"

    Returns:
        A dictionary containing a list of post info.
    """
    posts = sqlcn.posts.semtiment_score_by(thread_id, platform_id, start, end)
    post_dates=[]
    sentiment_scores=[]
    sentiment_labels=[]
    platforms=[]
    print(f"posts: {len(posts)}")
    if len(posts) > 0:
        for post in posts:
            # print(post)
            post_dates.append(post.get("sentiment_at"))
            sentiment_scores.append(post.get("sentiment_score"))
            sentiment_labels.append(post.get("sentiment_label"))
            platforms.append(post.get("platform_id"))
        
        print(f"post_dates: {len(post_dates)}" )
        print(f"sentiment_scores: {len(sentiment_scores)}" )
        print(f"sentiment_labels: {len(sentiment_labels)}" )
        print(f"platforms: {len(platforms)}")

        
        return {
                "time": post_dates,
                "sentiment_score": sentiment_scores,
                "sentiment_labels": sentiment_labels,
                "platforms": platforms
            }
    else:
        return {}



def last_top100_worst_posts(thread_id:str) -> list[dict]:
    """
    List the top hundred of the most negative posts in all social platforms.

    Args:
        thread_id: The Id of Thread.

    Returns:
        A list of posts.
    """
    return sqlcn.posts.recent_top100_worst_posts(thread_id)


def last_top100_best_posts(thread_id:str) -> list[dict]:
    """
    List the top hundred of the most positive posts in all social platforms.
    Args:
        thread_id: The Id of Thread.

    Returns:
        A list of posts.
    """
    return sqlcn.posts.recent_top100_best_posts(thread_id)


def last_top100_neutral_posts(thread_id:str) -> list[dict]:
    """
    List the top hundred of the most neutral posts in all social platforms.
    Args:
        thread_id: The Id of Thread.

    Returns:
        A list of posts.
    """
    return sqlcn.posts.recent_top100_neutral_posts(thread_id)


def last_sentiment_level(thread_id:str, platform_id:str) -> str:
    """
    Get the sentiment level of the thread in specific paltform, which is the average value of all sentiment level in the last 1 hours.

    A sentiment level is calculated base sentiment analysis to each post. Use following formula: 
                    sentiment_level = (w1 * sentiment_score) + (w2 * sentiment_magnitude), 
    and then do normalization:
                    normalized_sentiment = ((sentiment_level - min_sentiment) / (max_sentiment - min_sentiment)) * 100.

    Args:
        thread_id: The Id of Thread.
        platform_id: The name of source platform

    Returns:
        The sentiment level of the thread.
    """
    return str(sqlcn.sentiment_summaries.last_sentiment_level(thread_id, platform_id))


def last_100_posts(thread_id:str) -> list[dict]:
    """
    List the last 100 posts in all social platforms.

    Args:
        thread_id: The Id of Thread.

    Returns:
        A list of posts.
    """
    return sqlcn.posts.latest_100_posts(thread_id)



def thread_detail_by(thread_id:str) -> dict:
    """
    Get all detail of Thread.

    Args:
        thread_id: The Id of Thread.

    Returns:
        A dictionary containing the thread info.
    """
    return sqlcn.threads.thread_by_id(thread_id)


# Try output images 
async def generate_image(prompt: str, tool_context: 'ToolContext'):
    
  """Generates an image based on the prompt."""
  client = Client()
  response = client.models.generate_images(
      model='imagen-3.0-generate-002',
      prompt=prompt,
      config={'number_of_images': 1},
  )
  if not response.generated_images:
    return {'status': 'failed'}
  image_bytes = response.generated_images[0].image.image_bytes
#   return types.Part(
#     inline_data=types.Blob(
#         mime_type="image/png",
#         data=image_bytes
#     )
#   )
  await tool_context.save_artifact(
      'image.png',
      types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
  )
  return {
      'status': 'success',
      'detail': 'Image generated successfully and stored in artifacts.',
      'filename': 'image.png',
      'part': types.Part(
            inline_data=types.Blob(
                mime_type="image/png",
                data=image_bytes
            )
        )
  }