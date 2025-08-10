import pg8000
import sqlalchemy
from sqlalchemy import insert, select, update
import datetime
from sqlalchemy import Table, Column, Integer, String, BigInteger, ARRAY, TIMESTAMP



class MarkedBlob():
    def __init__(self, engine: sqlalchemy.engine.Engine, table_name="marked_blob"):
        self.engine = engine
        self.table = Table(
            table_name,
            sqlalchemy.MetaData(),
            Column("blob_name", String, primary_key=True),
            Column("ops_id", String),
            Column("created_at", TIMESTAMP, nullable=False),
        )

    # def __del__(self):
    #     print("__del__")
    #     try:
    #         self.connector.close()
    #     except Exception as e:
    #         print(e)




    def create_marked_blob(self, mb:dict=None)->dict:
        if bool(mb):
            mb["created_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            stmt = (
                insert(self.table).values(mb)
            )
            print(stmt)
            try:
                with self.engine.connect() as conn:
                    r = conn.execute(stmt)
                    conn.commit()
                return r.inserted_primary_key_rows[0].blob_name
            except Exception as e:
                print(e)
                conn.rollback()
            finally:
                print("finally")
                conn.close()
                
            return None
        else:
            return None
    

    def marked_blob_by_name(self, blob_name:str)->dict:
        stmt = (
            select(self.table)
                .where(self.table.c.blob_name == blob_name)
        )
        print(stmt)
        try:
            with self.engine.connect() as conn:
                r = conn.execute(stmt).fetchone()
                if r is None:
                    return None
                else:
                    return r._asdict()
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return None

        
    
if __name__ == "__main__":
    pass