from pydantic import BaseModel, Field
from typing import Union, Tuple, Dict, List


class ModelConfig(BaseModel):
    """
    Main config for model
    """
    model_id:str = Field(
        default="OpenGVLab/InternVL3-1B",
        description="repo id on huggingface"
    )
    model_revision: str = "main"
    backend: str= "turbomind"
    server_name: str = '0.0.0.0'
    server_port: int = 23333
    tp:int = 1
    session_len:int = 16384
    quant_policy:int = 8
    api_key:str = "123"
    temperature:float = 0.0
    top_k:int= 50
    top_p:float = 1.0

    modal_url: str = Field(
        default = 'https://phuocvodn98--inference-server-internvl3-serve.modal.run',
        description= "url given by Modal.com, for testing only"
    )
