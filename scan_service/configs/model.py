from pydantic import BaseModel, Field
from typing import Union, Tuple, Dict, List

class FewShotConfig(BaseModel):
    r"""
    Config for few shot examples
    """
    build_examples:bool = Field(
        default = False,
        description="wether or not build few-shot examples"   
    )

    num_examples_to_use:int = Field(
        default = 1,
        description="number of examples to be used"   
    )


class GenerationConfig(BaseModel):
    max_new_tokens: int = 1024 
    do_sample: bool = False
    num_beams: int = 3
    repetition_penalty:float = 2.0

class ModelConfig(BaseModel):
    model_id:str = Field(
        default = "5CD-AI/Vintern-1B-v3_5",
        description="repo id on huggingface"
    )
    transform_mean: Tuple[float] = Field(
        default = (0.485, 0.456, 0.406),
        description="mean for normalization"
    )
    transform_std:Tuple[float] = Field(
        default = (0.229, 0.224, 0.225),
        description="std for normalization"
    )

    target_title_size: Union[int, Tuple[int]] = Field(
        default = 448,
        description="target titles'size to resize"
    )

    max_num: int = 12
    
    generation_config: Dict[str, Union[bool, int, float]] = GenerationConfig().model_dump()

    fewshotconfig: FewShotConfig = FewShotConfig()