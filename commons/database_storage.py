import os
from supabase import create_client, Client
from storage3.types import UploadResponse

from dotenv import load_dotenv
from typing import Dict


RESPONSE_TYPES = Dict[str,str]

class DB_Storage_Client(object):

    def __init__(self):
        load_dotenv()
        self._client: Client = create_client(
            os.environ["SUPABASE_URL"], 
            os.environ["SUPABASE_KEY"]
        )

    def create_table(self):
        ...

    

    def create_bucket(self, bucket_name:str)->RESPONSE_TYPES:
        response = (
            self._client.storage
            .create_bucket(
                bucket_name,
                options={
                    "public": False,
                    "allowed_mime_types": ["application/pdf"],
                    "file_size_limit": 1024*5,  # bytes unit
                }
            )
        )

        return response

    def upload_pdf(
            self,
            file_content: bytes, 
            bucket_name:str, 
            remote_path:str
            )->UploadResponse:
        r"""
        Take bypes content of PDF and upload to object storage
        """
        response = (
            self._client.storage
            .from_(bucket_name)
            .upload(
                file=file_content,
                path=remote_path,
                file_options={
                    "cache-control": "3600", 
                    "upsert": "false"
                }
            )
        )
        return response

    def download_pdf(
            self,
            bucket_name:str, 
            remote_path:str
            )->bytes:
        r"""
        Download file data from storage
        """
        response = (
            self._client.storage
            .from_(bucket_name)
            .download(remote_path)
        )
    
        return response

