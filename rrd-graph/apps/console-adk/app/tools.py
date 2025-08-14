
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine


async def list_alloydb_tables() -> dict:
    """
    Lists all tables in the AlloyDB database.

    Returns:
        A dictionary containing a list of table names.
    """
    try:
        engine = create_async_engine(
            f"postgresql+asyncpg://{os.environ['ALLOYDB_USER']}:{os.environ['ALLOYDB_PASS']}@{os.environ['ALLOYDB_HOST']}/{os.environ['ALLOYDB_DB']}"
        )
        async with engine.connect() as conn:
            result = await conn.execute(sqlalchemy.text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"))
            tables = [row[0] for row in result]
            return {"tables": tables}
    except Exception as e:
        return {"error": str(e)}


async def get_alloydb_table_schema(table_name: str) -> dict:
    """
    Gets the schema of a specific table in the AlloyDB database.

    Args:
        table_name: The name of the table.

    Returns:
        A dictionary containing the table schema.
    """
    try:
        engine = create_async_engine(
            f"postgresql+asyncpg://{os.environ['ALLOYDB_USER']}:{os.environ['ALLOYDB_PASS']}@{os.environ['ALLOYDB_HOST']}/{os.environ['ALLOYDB_DB']}"
        )
        async with engine.connect() as conn:
            result = await conn.execute(sqlalchemy.text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';"))
            schema = {row[0]: row[1] for row in result}
            return {"schema": schema}
    except Exception as e:
        return {"error": str(e)}


async def query_alloydb(query: str) -> dict:
    """
    Executes a read-only SQL query against the AlloyDB database.
    IMPORTANT: This tool is restricted to SELECT statements to ensure data privacy and security.

    Args:
        query: The SQL SELECT query to execute.

    Returns:
        A dictionary containing the query results.
    """
    if not query.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed for security reasons."}
    try:
        engine = create_async_engine(
            f"postgresql+asyncpg://{os.environ['ALLOYDB_USER']}:{os.environ['ALLOYDB_PASS']}@{os.environ['ALLOYDB_HOST']}/{os.environ['ALLOYDB_DB']}"
        )
        async with engine.connect() as conn:
            result = await conn.execute(sqlalchemy.text(query))
            rows = [list(row) for row in result]
            return {"result": rows}
    except Exception as e:
        return {"error": str(e)}
