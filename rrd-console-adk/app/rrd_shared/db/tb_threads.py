import pg8000
import sqlalchemy
from sqlalchemy import insert, select, update, delete
import datetime
from sqlalchemy import Table, Column, Integer, String, BigInteger, ARRAY, TIMESTAMP



class Thread():
    def __init__(self, engine: sqlalchemy.engine.Engine, table_name="threads"):
        self.engine = engine
        self.table = Table(
            table_name,
            sqlalchemy.MetaData(),
            Column("thread_id", BigInteger, primary_key=True, comment="""
                Unique identifier for each thread.
            """),
            Column("display_name", String, nullable=False, comment="""
                The name for this thread.
            """),
            Column("thread_type", String, comment="""
                The thread type could be event, incident, etc, which helps category the thread.
            """),
            Column("context", String, nullable=False, comment="""
                The context is key for LLMs to understand what the thread and help to make decision in later tasks.
            """),
            Column("instructions", String, comment="""
                The instructions is to tell LLMs what needs to be done or detail of purpose.
            """),
            Column("platform_ids", ARRAY(String), nullable=False, comment="""
                Platform IDs is array of string, each item of array is refer to platform_id in platforms table.
            """),
            Column("created_at", TIMESTAMP, comment="""
                The create time of this record.
            """),
            Column("updated_at", TIMESTAMP, comment="""
                The update time of this record.
            """),
            comment="""
                The threads table is to store thread, each thread is related to sentiment event and  containes 
                type of thread, context, instructions, target media platforms, etc.
            """
        )

    # def __del__(self):
    #     print("__del__")
    #     try:
    #         self.connector.close()
    #     except Exception as e:
    #         print(e)
            

    def create_thread(self, th:dict=None)->dict:
        if bool(th):
            th["created_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            stmt = (
                insert(self.table).values(th)
            )
            print(stmt)
            try:
                with self.engine.connect() as conn:
                    r = conn.execute(stmt)
                    conn.commit()
                th["thread_id"] = r.inserted_primary_key_rows[0].thread_id
                return th
            except Exception as e:
                print(e)
                conn.rollback()
            finally:
                print("finally")
                conn.close()
                
            return None
        else:
            return None

    def delete_thread(self, thread_id:str)->str:
        stmt = (
            delete(self.table)
                .where(self.table.c.thread_id == int(thread_id))
            )
        print(stmt)
        try:
            with self.engine.connect() as conn:
                r = conn.execute(stmt)
                conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        finally:
            print("finally")
            conn.close()
        return thread_id


    def update_thread(self, th:dict=None)->dict:
        th["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        stmt = (
            update(self.table)
                .where(self.table.c.thread_id == int(th.get("thread_id")))
                .values(th)
            )
        try:
            with self.engine.connect() as conn:
                r = conn.execute(stmt)
                conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()
        finally:
            print("finally")
            conn.close()
        return th
    

    def thread_by_id(self, thread_id:str)->dict:
        stmt = (
            select(self.table)
                .where(self.table.c.thread_id == int(thread_id))
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

    def list_threads(self)->list[dict]:
        stmt = (
            select(self.table)
        )
        ths = []
        print(stmt)
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(stmt).fetchall()
                for r in rows:
                    ths.append(r._asdict())
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return ths
       
        


if __name__ == "__main__":
    th = Thread()
    # thread_id = th.create_thread(
    #     {
    #         "display_name": "test thread",
    #         "thread_type": "event",
    #         "context": "test",
    #         "instructions": "test",
    #         "platform_ids": ["twitter", "google_news"],
    #         "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    #     }
    # )
    # if thread_id is None:
    #     print("failed to insert thread")
    th.thread_by_id(1)