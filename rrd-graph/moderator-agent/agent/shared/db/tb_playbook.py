import pg8000
import sqlalchemy
from sqlalchemy import insert, select, update
import datetime
from sqlalchemy import Table, Column, Integer, String, BigInteger, ARRAY, TIMESTAMP, JSON



class Playbook():
    def __init__(self, engine: sqlalchemy.engine.Engine, table_name="playbooks"):
        self.engine = engine
        self.table = Table(
            table_name,
            sqlalchemy.MetaData(),
            Column("playbook_id", BigInteger, primary_key=True),
            Column("display_name", String, nullable=False),
            Column("thread_id", BigInteger, nullable=False),
            Column("assessment", JSON, nullable=False),
            Column("plan", JSON, nullable=False),
            Column("created_at", TIMESTAMP, nullable=False),
            Column("updated_at", TIMESTAMP),
        )

    # def __del__(self):
    #     print("__del__")
    #     try:
    #         self.connector.close()
    #     except Exception as e:
    #         print(e)




    def create_playbook(self, pb:dict=None)->dict:
        if bool(pb):
            pb["created_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            stmt = (
                insert(self.table).values(pb)
            )
            print(stmt)
            try:
                with self.engine.connect() as conn:
                    r = conn.execute(stmt)
                    conn.commit()
                return r.inserted_primary_key_rows[0].playbook_id
            except Exception as e:
                print(e)
                conn.rollback()
            finally:
                print("finally")
                conn.close()
                
            return None
        else:
            return None
    

    def last_playbook(self, thread_id:str)->dict:
        stmt = (
            select(self.table)
                .where(self.table.c.thread_id == int(thread_id))
                .order_by(self.table.c.created_at.desc())
                .limit(1)
        )
        print(stmt)
        try:
            with self.engine.connect() as conn:
                r = conn.execute(stmt).fetchone()
            return r._asdict()
        except Exception as e:
            print(e)
            conn.rollback()
        finally:
            print("finally")
            conn.close()
            
        return None

        
    
if __name__ == "__main__":
    pass