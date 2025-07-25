# DEFINE types of messages communication between main_app service and scan_service through RabbitMQ

from pydantic import (
    BaseModel
)
from typing import Literal


DOCUMENT_TASKS = Literal['cover','law']

class ScanRequest(BaseModel):
    r"""
    Represent a request data
    Args:
        bucket_name (str): remote bucket name
        remote_path (str): remote path to download
        task (DOCUMENT_TASKS): name of task to process 
    """
    bucket_name: str
    remote_path: str
    task: DOCUMENT_TASKS

