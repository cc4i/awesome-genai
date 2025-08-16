import sqlalchemy
import base64
import json
from enum import Enum
import datetime
from sqlalchemy import insert, select, update
from sqlalchemy import Table, Column, Integer, String, BigInteger, ARRAY, TIMESTAMP



class PlatformId(Enum):
    TWITTER = "twitter"
    GOOGLE_NEWS = "google-news"
    GOOGLE_SEARCH = "google-search"
    INSTAGRAM = "instagram"


class Platform():
    def __init__(self, engine: sqlalchemy.engine.Engine, table_name="platforms"):
        self.engine = engine
        self.table = Table(
            table_name,
            sqlalchemy.MetaData(),
            Column("platform_id", String, primary_key=True, comment="""
                Unique identifier for each platform, which has be one of these: 
                twitter, google-news, google-search, instagram.
            """),
            Column("secret", String, comment="""
                Secret is base64 string, which include APIs key for different platforms.
            """),
            Column("endpoint", String, comment="""
                The endpoint to API service of a platform.
            """),
            Column("created_at", TIMESTAMP, nullable=False, comment="""
                The create time of this record.
            """),
            Column("updated_at", TIMESTAMP, comment="""
                The update time of this record.
            """),
            comment="The table is for all targeted platforms, which the RRD is collecting from."
        )

    # def __del__(self):
    #     print("__del__")
    #     try:
    #         self.connector.close()
    #     except Exception as e:
    #         print(e)




    def create_platform(self, pt:dict=None)->dict:
        if bool(pt):
            pt["created_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            stmt = (
                insert(self.table).values(pt)
            )
            print(stmt)
            try:
                with self.engine.connect() as conn:
                    r = conn.execute(stmt)
                    conn.commit()
                return r.inserted_primary_key_rows[0].platform_id
            except Exception as e:
                print(e)
                conn.rollback()
            finally:
                print("finally")
                conn.close()
                
            return None
        else:
            return None
    

    def platform_by_id(self, platform_id:str)->dict:
        stmt = (
            select(self.table)
                .where(self.table.c.platform_id == platform_id)
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

    def api_secret_by(self, platform_id:str) -> dict:
        pf = self.platform_by_id(platform_id)
        secret_str = pf.get("secret")
        if secret_str is not None:
            scerets = json.loads(base64.b64decode(secret_str).decode("utf-8"))
            if platform_id == PlatformId.TWITTER.value:
                secret = scerets.get("bearer_token")
            elif platform_id == PlatformId.GOOGLE_NEWS.value or platform_id == PlatformId.GOOGLE_SEARCH.value:
                secret = scerets.get("serper_api_key")
            else:
                return None
            return {"secret": secret}
        return None
        
    
if __name__ == "__main__":
    pt = Platform(engine=None)
    print(pt.table.metadata.tables)