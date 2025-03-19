import pg8000
import sqlalchemy
from sqlalchemy import insert, select, update, and_, or_
import datetime
from sqlalchemy import Table, Column, Integer, String, BigInteger, ARRAY, TIMESTAMP, ForeignKey




class Job():
    def __init__(self, engine: sqlalchemy.engine.Engine, table_name="jobs"):
        self.engine = engine
        self.table = Table(
            table_name,
            sqlalchemy.MetaData(),
            Column("job_id", String, primary_key=True, comment="""
                Unique identifier for each Job, which follows this pattern: scraping-job-{thread_id}-{platform_id}
            """),
            Column("thread_id", BigInteger, ForeignKey("threads.thread_id"), nullable=False, comment="""
                Unique identifier, acts as foreign key to threads table.
            """),
            Column("keywords", ARRAY(String), nullable=False, comment="""
                Multiple keywords stores as an array of string, number of keywords are varied and depends on target platform.
            """),
            Column("platform_id", String, ForeignKey("platforms.platform_id"), nullable=False, comment="""
                Platform ID is uniqe string, act as foreign key to platforms table.
            """),
            Column("job_interval", Integer, comment="""
                The intervening time to run the job.
            """),
            Column("status", String, comment="""
                The current status of the job.
            """),
            Column("created_at", TIMESTAMP, nullable=False, comment="""
                Created time of the job.
            """),
            Column("updated_at", TIMESTAMP, comment="""
                Updated time of the job
            """),
            comment="""The table for Job related information and current status.""",
        )

    # def __del__(self):
    #     print("__del__")
    #     try:
    #         self.connector.close()
    #     except Exception as e:
    #         print(e)

    def the_job(self, thread_id:str, platform_id:str)->dict:
        stmt = (
            select(self.table)
                .where(
                    and_(
                        self.table.c.thread_id == int(thread_id),
                        self.table.c.platform_id == platform_id
                    )
                )
        )
        print(stmt)
        try:
            with self.engine.connect() as conn:
                r = conn.execute(stmt).fetchone()
                print(r._asdict())
                return r._asdict()
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return None

    def jobs_by_thread_id(self, thread_id:str)->list[dict]:
        stmt = (
            select(self.table)
                .where(self.table.c.thread_id == int(thread_id))
        )
        print(stmt)
        jobs = []
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(stmt).fetchall()
                for r in rows:
                    jobs.append(r._asdict())
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return jobs

    def create_job(self, job:dict=None)->dict:
        if bool(job):
            job["created_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            stmt = (
                insert(self.table).values(job)
            )
            print(stmt)
            try:
                with self.engine.connect() as conn:
                    r = conn.execute(stmt)
                    conn.commit()
                return r.inserted_primary_key_rows[0].job_id
            except Exception as e:
                print(e)
                conn.rollback()
            finally:
                print("finally")
                conn.close()
                
            return None
        else:
            return None
    

        
    
if __name__ == "__main__":
    j = Job(engine=None)
    # j.create_job(
    #     {
    #         "job_id": "test_job_id",
    #         "thread_id": "0123456789",
    #         "keywords": ["key1", "key2"],
    #         "platform_id": "twitter",
    #         "job_interval": 10,
    #         "status": "running",
    #         "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    #     }
    # )
    print(j.table.metadata.tables)