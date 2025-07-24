from pydantic import BaseModel, Field
from typing import Union, Tuple, Dict, List
import json
import shlex

MAX_BATCH_SIZE = 2

class CompilationConfig(BaseModel):
    level:int = 3
    splitting_ops:List[str]=["vllm.unified_attention","vllm.unified_attention_with_output"]
    use_inductor:bool = True
    use_cudagraph: bool = True
    cudagraph_num_of_warmups:int = 1
    cudagraph_capture_sizes: List[int] = list(range(1,MAX_BATCH_SIZE+1))

class ModelConfigBase(BaseModel):
    """
    Main config for model
    """
    model_id:str
    model_revision: str = "main"
    server_name: str = '0.0.0.0'
    server_port: int = 23333
    tp:int = 1
    max_model_len:int=Field(
        default = 1024,
        description= "Limit context window"
    )
    max_num_seqs:int=Field(
        default = MAX_BATCH_SIZE,
        description= "Limit batch size"
    )
    limit_mm_per_prompt: int = Field(
        default = 3,
        description= "Limit num image per request"
    )

    compilation_config: str = shlex.quote(json.dumps(CompilationConfig().model_dump(mode='json')))

    quant_policy:int = 8
    api_key:str = "123"
    temperature:float = 1.0
    top_k:int= 50
    top_p:float = 1.0

    modal_url: str = Field(
        default = 'https://phuocvodn98--inference-server-internvl3-serve.modal.run',
        description= "url given by Modal.com, for testing only"
    )

    def model_post_init(self, __context: any) -> None:
        self.limit_mm_per_prompt = 'image='+str(self.limit_mm_per_prompt)


class ModelConfigQuant(ModelConfigBase):
    """
    Main config for AWQ model
    """
    model_id:str = Field(
        default="RedHatAI/gemma-3-4b-it-quantized.w4a16",
        description="repo id on huggingface"
    )
    temperature:float = 1.0
    top_k:int= 64
    top_p:float = 0.95