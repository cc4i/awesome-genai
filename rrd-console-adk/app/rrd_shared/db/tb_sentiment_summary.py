import pg8000
import sqlalchemy
from sqlalchemy import insert, select, update, and_, or_
from datetime import datetime, UTC
from sqlalchemy import Table, Column, Integer, String, BigInteger, ARRAY, TIMESTAMP, Double
from decimal import Decimal
import pytz



class SentimentSummary():
    def __init__(self, engine: sqlalchemy.engine.Engine, table_name="sentiment_summary"):
        self.engine = engine
        self.table = Table(
            table_name,
            sqlalchemy.MetaData(),
            Column("sentiment_id", BigInteger, primary_key=True, comment="""
                Unique identifier for each sentiment analysis happened.
            """),
            Column("thread_id", BigInteger, nullable=False, comment="""
                Unique identifier, acts as foreign key to threads table.
            """),
            Column("platform_id", String, nullable=False, comment="""
                Unique identifier, acts as foreign key to platforms table.
            """),
            Column("sentiment_level", Double, nullable=False, comment="""
                The sentiment level is calculated base sentiment analysis to each post. Use following 
                   formula: 
                    sentiment_level = (w1 * sentiment_score) + (w2 * sentiment_magnitude), 
                   and then do normalization:
                    normalized_sentiment = ((sentiment_level - min_sentiment) / (max_sentiment - min_sentiment)) * 100.
            """),
            Column("created_at", TIMESTAMP, nullable=False, comment="""
                The create time of this record.
            """),
            Column("updated_at", TIMESTAMP, comment="""
                The update time of this record.
            """),
            comment="""
                The semtiment_summary table is to store sentiment analysis aggeragation by platform and thread.
            """
        )


    # def __del__(self):
    #     print("__del__")
    #     try:
    #         self.connector.close()
    #     except Exception as e:
    #         print(e)




    def create_sentiment_summary(self, ss:dict=None)->dict:
        if bool(ss):
            ss["created_at"] = datetime.now(UTC).isoformat()
            stmt = (
                insert(self.table).values(ss)
            )
            print(stmt)
            try:
                with self.engine.connect() as conn:
                    r = conn.execute(stmt)
                    conn.commit()
                return r.inserted_primary_key_rows[0].sentiment_id
            except Exception as e:
                print(e)
                conn.rollback()
            finally:
                print("finally")
                conn.close()
                
            return None
        else:
            return None


    def last_overall_sentiment_level(self, thread_id:str)->Decimal:
        stmt = f"""
            select 
                AVG(sentiment_level) as sentiment_level 
            from 
                sentiment_summary
            where 
                thread_id = {thread_id}
                and created_at >= (select max(created_at) from sentiment_summary) - INTERVAL '1 hour'
        """
        print(stmt)
        sentiment_level=None
        try:
            with self.engine.connect() as conn:
                r = conn.exec_driver_sql(stmt).fetchone()
                sentiment_level=Decimal(r.__getattr__("sentiment_level"))
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return sentiment_level

    def last_sentiment_level(self, thread_id:str, platform_id: str)->Decimal:
        stmt = f"""
            select 
                AVG(sentiment_level) as sentiment_level 
            from 
                sentiment_summary
            where 
                thread_id = {thread_id}
                and platform_id = '{platform_id}'
                and created_at >= (select max(created_at) from sentiment_summary) - INTERVAL '1 hour'
        """
        print(stmt)
        sentiment_level=None
        try:
            with self.engine.connect() as conn:
                r = conn.exec_driver_sql(stmt).fetchone()
                sentiment_level=Decimal(r.__getattr__("sentiment_level"))
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return sentiment_level



    def last_sentiment_by_platform(self, thread_id:str)->list[dict]:
        stmt = f"""
            select 
                AVG(sentiment_level) as sentiment_level,platform_id 
            from 
                sentiment_summary
            where 
                thread_id = {thread_id}
                and created_at >= (select max(created_at) from sentiment_summary) - INTERVAL '1 hour'
            group by platform_id
        """
        print(stmt)
        ssp = []
        try:
            with self.engine.connect() as conn:
                rows = conn.exec_driver_sql(stmt).fetchall()
                for r in rows:
                    ssp.append(r._asdict())
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return ssp



    def calculate_sentiment_level(self, thread_id: str, platform_id: str) -> tuple[Decimal, bool]:
        old_sentiment_level = self.last_sentiment_level(thread_id, platform_id)
        stmt = f"""
            SELECT
                SUM((((0.7*sentiment_score + 0.3*sentiment_magnitude)+1)/2)*100)/COUNT(*) AS sentiment_level
            FROM
                posts
            WHERE
                thread_id={thread_id}
                AND platform_id = '{platform_id}'
                AND status IN ('sentimented', 'generated')
                AND sentiment_at>= (
                    SELECT
                        MAX(sentiment_at)
                    FROM
                        posts
                    WHERE
                thread_id={thread_id}
                AND platform_id = '{platform_id}'
                AND status IN ('sentimented','generated') ) - INTERVAL '1 HOUR'
        """
        print(stmt)
        sentiment_level=None
        try:
            with self.engine.connect() as conn:
                r = conn.exec_driver_sql(stmt).fetchone()
                sentiment_level = Decimal(r.__getattr__("sentiment_level"))
                if old_sentiment_level!=sentiment_level:
                    insert_stmt = (
                        insert(self.table).values({
                            "thread_id": int(thread_id),
                            "platform_id": platform_id,
                            "sentiment_level": sentiment_level,
                            "created_at": datetime.now(UTC).isoformat()
                        })
                    )
                    print(insert_stmt)
                    conn.execute(insert_stmt)
                    conn.commit()
                    return sentiment_level, True
        except Exception as e:
            print(e)
            conn.rollback()
        finally:
            print("finally")
            conn.close()
            
        return sentiment_level, False


    def sentiment_level_by_timestamp(self, thread_id: str, start: str, end: str) -> list[dict]:
        stmt = (
            select(self.table)
            .where(
                and_(
                    self.table.c.thread_id == int(thread_id),
                    self.table.c.created_at >= datetime.strptime(start, '%Y-%m-%d %H:%M:%S').astimezone(pytz.utc),
                    self.table.c.created_at <= datetime.strptime(end, '%Y-%m-%d %H:%M:%S').astimezone(pytz.utc)
                )
            )
            .order_by(self.table.c.created_at)
            
        )
        sls=[]
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(stmt).fetchall()
                for r in rows:
                    sls.append(r._asdict())
        except Exception as e:
            print(e)
        finally:
            print("finally")
            conn.close()
            
        return sls


if __name__ == "__main__":
    pass