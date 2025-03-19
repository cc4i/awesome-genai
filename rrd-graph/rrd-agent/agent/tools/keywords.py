import os
from agent.shared.llm import init_model


class KeywordsBuilder():
    def __init__(self):
         # All variables
        project_id = os.getenv("PROJECT_ID", "multi-gke-ops")
        location = os.getenv("LOCATION", "us-central1")
        model_id = os.getenv("MODEL_ID", "claude-3-5-sonnet-v2@20241022")
        self.llm = init_model(project_id=project_id, location=location, model_id=model_id)


    def tweets_prompt(self, context, instructions) -> str:
        prompt = f"""
            # Instruction
            You are an X/Twitter platform expert with extensive experience using the X/Twitter API v2. Your task is to build the best query string to retrieve the most relevant tweets based on the provided context, tasks, and considerations. 

            # Notes
            - Restrictedly follow X(Twitter) documentation for building query string.
            - Return only the valid query string without any explanations.

            # Examples
            ## Example 1 
            Build a query string based on the following information:

            ### Context: 
            Hurricane Harvey, a devastating Category 4 hurricane, struck the Gulf Coast of Texas in August 2017. It was one of the most powerful hurricanes to hit the United States in decades. Harvey's most catastrophic impact was the unprecedented rainfall, making it the wettest storm system on record.

            ### Instructions: 
            - Collect any Tweets related this topic to gauge that discuss Hurricane Harvey
            - Prioritize collecting from high ranked influencers
            - Exclude re-tweet and marketing messages.
            
            ### Query String
            has:geo (from:NWSNHC OR from:NHC_Atlantic OR from:NWSHouston OR from:NWSSanAntonio OR from:USGS_TexasRain OR from:USGS_TexasFlood OR from:JeffLindner1) -is:retweet

            ## Example 2
            Build a query string based on the following information:

            ### Context: 
            Better understand the sentiment of the conversation developing around the hashtag, #nowplaying.

            ### Instructions: 
            - Collect any Tweets has the hashtag #nowplaying
            - Prioritize collecting from high ranked influencers
            - Exclude re-tweet and marketing messages.
            - Scoped to just Posts published within North America

            ### Query String
            #nowplaying (happy OR exciting OR excited OR favorite OR fav OR amazing OR lovely OR incredible) (place_country:US OR place_country:MX OR place_country:CA) -horrible -worst -sucks -bad -disappointing


            # Task
            Build a query string based on the following information:

            ## Context: 
            {context}

            ## Instructions: 
            {instructions}

            ## Query String
        """
        return prompt

    def gen_keywords4tweets(self, context, instructions)->str:
        prompt = self.tweets_prompt(context, instructions)
        return self.llm.predict(prompt)


    def gen_keywords4google(self, context, instructions)->dict:
        prompt = f"""
            You are a Google Search expert with extensive experience in optimizing search results. Your task is to analyze the provided context and instructions to generate a list of relevant Google search keywords.

            Context:
            {context}

            Instructions:
            {instructions}

            Please follow these steps:

            1. Carefully analyze the provided context and instructions.
            2. Identify the main topics and themes discussed in the text.
            3. Generate a list of primary keywords that accurately reflect the most important topics.
            4. Generate a list of secondary keywords that provide additional context and related terms.
            5. Organize the keywords into a JSON object with the following structure:
            """ + """
            ```json
            {
            "primary_keywords": [
                "keyword1",
                "keyword2",
                "keyword3"
                // ... more primary keywords
            ],
            "secondary_keywords": [
                "keyword4",
                "keyword5",
                "keyword6"
                // ... more secondary keywords
            ]
            }
            ```

            Output the JSON object without any additional explanations or text.

        """
        g_response = self.llm.invoke(prompt)
        return g_response.content




