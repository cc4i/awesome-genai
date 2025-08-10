import os
import json
import datetime
from langchain_core.tools import tool
from agent.shared.db.sql_cn import SqlCN


# Db
sqlcn = SqlCN()

@tool
def latest_playbook(thread_id: str) -> dict:
    """
    Get the latest playbook by gaven thread_id.
    """
    return sqlcn.playbooks.last_playbook(thread_id)