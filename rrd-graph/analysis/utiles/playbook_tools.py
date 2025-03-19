import os
import json
import datetime
import ast
from shared.db.sql_cn import SqlCN
from shared.llm import init_model, call_llm


class PlaybookTools():
    def __init__(self, sqlcn: SqlCN):
        self.sqlcn = sqlcn


    def save_playbook(self, thread_id: str, playbook: dict):
        if bool(playbook):
            p = {
                    "display_name": playbook.get("report_name"),
                    "thread_id": int(thread_id),
                    "assessment": json.dumps({
                        "summary": playbook["summary"],
                        "severity_assessment": playbook["severity_assessment"],
                        "incident_categorization": playbook["incident_categorization"]
                    }),
                    "plan": json.dumps(playbook["recommendations"]),
                    "created_at": datetime.datetime.now(datetime.UTC).isoformat()
            }
            r = self.sqlcn.playbooks.create_playbook(p)


    def gen_positive_content(self, project_id: str, location: str, model_id: str, thread_id: str) -> dict:
        # Query thread detail from threads
        thread = self.sqlcn.threads.thread_by_id(thread_id)
        thread_context = thread.get("context")
        # Query records from posts
        posts = self.sqlcn.posts.recent_top100_worst_posts(thread_id)
        neg_content = []
        for row in posts:
            neg_content.append({
                "post_id": row.post_id,
                "platform_id": row.platform_id,
                "content": json.dumps(row.content)
            })

        if len(neg_content)>0:
            neg_content_sample = [
                    {
                        "post_id": "tw-123910239012313834348",
                        "platform_id": "twitter",
                        "centent": "Disappointed with the lack of groundbreaking AI features.  Feeling a bit underwhelmed.#AppleGlowtime #AI"
                    }
                ]
            neg_content_response_sample = [
                    {
                        "post_id": "tw-123910239012313834348",
                        "platform_id": "twitter",
                        "centent": "We appreciate your honest feedback on #AppleGlowtime! While we're proud of its current AI features, we're always pushing the boundaries of what's possible. Exciting updates are coming that will truly illuminate your world! ✨ #AI #innovation"
                    }
                ]
            prompt = f"""
                You’re an expert of public relations and have intensive experience mitigating reputation incidents on the internet. 
                You’re responsible to come up with an effective response, based on following conext and align with principles. 
                
                ## Conext 
                {thread_context}

                ## Principles:
                * **Be swift: Don't let negative sentiment fester. Address it promptly.**
                * **Be empathetic: Acknowledge the user's feelings, even if you disagree. No need to point out specific user handlers. **
                * **Be solutions-oriented: Offer help, information, or a glimpse into the future. **Any help information should be accessible, not a template. **
                * **Be short and concise.**
                * **Stay positive: Focus on the good and encourage others to do the same.**
                * **The response should be able to be used straightway without any changes.**
                
                ## Notes
                * **A Tweet is limited to less than 280 characters.**
                * **Output should be JSON formatted and follow the examples as guidelines.** 
                * **Output does not require any explanation. **
            
                ===
                Here’s example:
                Negative Content:
                {neg_content_sample}
                Responding:
                {neg_content_response_sample}
                ===

                Negative Content:
                {neg_content}
                Responding:
            
            """
            
            llm = init_model(project_id=project_id, location=location, model_id=model_id)
            return call_llm(llm, prompt)
            



  
    def gen_assessment(self, project_id: str, location: str, model_id: str, thread_id: str) -> dict:
        # Top 100 Negative content
        negative_content = self.sqlcn.posts.recent_top100_worst_posts(thread_id)
        # Top 10 positive content
        positive_content = self.sqlcn.posts.recent_top100_best_posts(thread_id)
        # Top 10 Neutral content
        neutral_content = self.sqlcn.posts.recent_top100_neutral_posts(thread_id)
        # Sentiment distribution as count
        s_distribution = self.sqlcn.posts.sentiment_distribution_by_score(thread_id)
        # Last sentiment level
        sentiment_level=self.sqlcn.sentiment_summaries.last_overall_sentiment_level(thread_id)
        # Query thread detail from threads
        thread = self.sqlcn.threads.thread_by_id(thread_id)

        json_format = {
                "report_name": "Give a creative name for this reputation report within five words.",
                "summary": "Key findings and data points summarized, including reputational strengths and weaknesses.",
                "severity_assessment": "Evaluation of the potential impact on brand reputation.",
                "incident_categorization": {
                    "category": "Category of the incident (e.g., unmet expectations, product failure, etc.)",
                    "explanation": "Explanation for the chosen category"
                },
                "recommendations": {
                    "response_strategy": "Comprehensive communication plan to address concerns and manage public perception.",
                    "performance_monitoring": "Methods for tracking the effectiveness of the response strategy.",
                    "post_incident_analysis": "Process for reviewing the incident and improving future strategies.",
                    "reputation_building": "Proactive measures to strengthen online reputation."
                }
            }
        prompt = f"""
            You are a public relations expert with extensive experience in mitigating reputation incidents and in-depth knowledge of organizational strategies. Your task is to analyze the provided context and analytic data to generate a comprehensive reputation report in JSON format.

            ## Context
            {thread.get("context")}

            ## Analytic Data

            **The sentiment results are based on content collected from media platforms: {thread.get("platform_ids")}.** 

            Positive  records: {s_distribution.get("positive")}
            Negative records:  {s_distribution.get("negative")}
            Neutral records: {s_distribution.get("neutral")} 

            ** Sentiment level (sentiment_level = (0.7 * sentiment_score) + (0.3 * sentiment_magnitude)) is formulated by last two hours sentiment records and the value is between 1 and 100 after normalization. ** 

            Sentiment level:  {sentiment_level}

            **Top 100 positive records**

            {positive_content}

            **Top 100 neutral records**

            {negative_content}
            
            **Top 100 negative records**

            {neutral_content}

            ## Instructions

            Based on the provided context and analytic data, create a reputation report following this structure:

            {json_format}

            Ensure your report adheres strictly to the JSON structure above.  Use the provided context and analytic data to populate each section of the JSON object with relevant information.
        """
            
        llm = init_model(project_id=project_id, location=location, model_id=model_id)

        responding = call_llm(llm, prompt)
        print(f"responding from call_llm: {responding}")
        return ast.literal_eval(responding)






    def   gen_playbook(self, thread_id: str):
        project_id = os.getenv("PROJECT_ID") or "realtime-reputation-defender"
        location = os.getenv("MODEL_LOCATION") or "us-central1"
        model_id = os.getenv("MODEL_ID") or "gemini-1.5-pro-002"

        # Get request
        try:
            pbook = self.gen_assessment(
                project_id=project_id, 
                location=location, 
                model_id=model_id,
                thread_id=thread_id
            )
            # TODO: Maybe gen_positive content seperately
            # pcontent = gen_positive_content(
            #     project_id=project_id, 
            #     location=location, 
            #     bq_dataset_id=bq_dataset_id, 
            #     thread_id=thread_id, 
            #     thread_context=thread_context, 
            #     model_id=model_id
            # )
            self.save_playbook(thread_id=thread_id, playbook=pbook)
        except Exception as e:
            print(f"Failed to exec gen_playbook(), with error: {e}")
            pbook = None
        
        return pbook

