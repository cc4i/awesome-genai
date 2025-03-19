import pg8000
import sqlalchemy
import time
import os
from dotenv import load_dotenv
from google.cloud.alloydb.connector import Connector, IPTypes
from google.auth import default, transport

from .tb_jobs import Job
from .tb_marked_blob import MarkedBlob
from .tb_platforms import Platform
from .tb_playbook import Playbook
from .tb_posts import Post
from .tb_sentiment_summary import SentimentSummary
from .tb_threads import Thread


class SqlCN():
    def __init__(self):
        # Load environment variables
        print("Loading environment variables from .env")
        load_dotenv()

        # All variables
        project_id = os.getenv("PROJECT_ID", "multi-gke-ops")
        location = os.getenv("LOCATION", "us-central1")
        cluster_id = os.getenv("CLUSTER_ID", "rrd-all-in-one")
        instance_id = os.getenv("INSTANCE_ID", "rrd-all-in-one-primary")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASS")
        db = os.getenv("DB_NAME")

        # Only for local test in LangGraph Studio
        file_path="/deps/__outer_agent/agent/multi-gke-ops-aa82224eed72.json"
        if os.path.exists(file_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=file_path
        self.credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

        # Create DB Pool
        self.engine, self.connector = self.create_sqlalchemy_engine(
            project_id=project_id, location=location, 
            cluster_id=cluster_id, 
            instance_id=instance_id, 
            user=user, 
            password=password, 
            db=db
        )
        self.jobs = Job(self.engine)
        self.marked_blobs = MarkedBlob(self.engine)
        self.platforms = Platform(self.engine)
        self.playbooks = Playbook(self.engine)
        self.posts = Post(self.engine)
        self.sentiment_summaries = SentimentSummary(self.engine)
        self.threads = Thread(self.engine)


    def create_sqlalchemy_engine(self,
        project_id: str, location: str, cluster_id: str, instance_id: str,
        user: str,
        password: str,
        db: str,
        refresh_strategy: str = "background",
    ) -> tuple[sqlalchemy.engine.Engine, Connector]:
        
        db_secret = os.getenv("DB_SECRET")
        connector = Connector(credentials=self.credentials, refresh_strategy=refresh_strategy)

        def getconn() -> pg8000.dbapi.Connection:
            retry_count = 0
            max_retries = 3
            retry_delay = 1
            while retry_count < max_retries:
                try:
                    if db_secret is None:
                        ip_type = IPTypes.PUBLIC
                    else:
                        ip_type = IPTypes.PRIVATE
                    conn: pg8000.dbapi.Connection = connector.connect(
                        f"projects/{project_id}/locations/{location}/clusters/{cluster_id}/instances/{instance_id}",
                        "pg8000",
                        user=user,
                        password=password,
                        db=db,
                        ip_type=ip_type,
                    )
                    return conn
                except Exception as e:
                    print(f"Error connecting to AlloyDB: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_count += 1
                    retry_delay *= 2

        # create SQLAlchemy connection pool
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=40,
            max_overflow=10,
            pool_recycle=1800,
        )
        engine.dialect.description_encoding = None
        return engine, connector

    def __del__(self):
        print("__del__")
        try:
            print("dispose engine")
            self.engine.dispose(False)
            print("close connector")
            self.connector.close()
        except Exception as e:
            print(e)