from pydantic import BaseModel

class JobRequest(BaseModel):
    thread_id: str
    platform_ids: list[str]
    image: str
    interval: str | None = None


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "thread_id": "1",
                    "platform_ids": ["twitter", "google-news"],
                    "interval": "*/10 * * *",
                    "image": "asia-southeast1-docker.pkg.dev/multi-gke-ops/gke-repo/scraping-job",
                },
                {
                    "thread_id": "1",
                    "platform_ids": ["twitter"],
                    "interval": "0 */2 * * *",
                    "image": "asia-southeast1-docker.pkg.dev/multi-gke-ops/gke-repo/loadgen-job",
                },

            ]
        }
    }