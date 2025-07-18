from transformers import AutoModel, AutoTokenizer
import torch

from configs.model import ModelConfig
from utils import get_device, pdf2images
from model.preprocessing import Image_PreProcessing
from commons.schemas.model import Fields2Extract

MODEL_DTYPE = torch.bfloat16

class ModelWrapper(object):

    question = f"""<image>\nTrích xuất thông tin trong văn bản. 
đầu ra theo format JSON được mô tả sau đây:
{Fields2Extract.model_json_schema()}
"""

    def __init__(self, config:  ModelConfig):
        self.device, can_use_flash_attn = get_device()

        self.model = AutoModel.from_pretrained(
            config.model_id,
            load_in_8bit=True,
            torch_dtype = MODEL_DTYPE,
            trust_remote_code = True,
            use_flash_attn = can_use_flash_attn,
            revision="main",  # Pin to main branch
        ).eval()

        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_id,
            trust_remote_code=True,
            use_fast=False,
            revision="main"  # Pin to main branch
        )

        self.pre_process = Image_PreProcessing(config = config)

        self._generation_config = config.generation_config

    def forward(self, local_path_pdf:str):
        print('local_path_pdf: ', local_path_pdf)
        pages_images = pdf2images(local_path_pdf)[0]
        batch_titles = self.pre_process.transform(pages_images).to(MODEL_DTYPE).to(self.model.device)

        response = self.model.chat(
            tokenizer = self.tokenizer, 
            pixel_values = batch_titles,
            question = self.question, 
            generation_config = self._generation_config
        )

        print('response: ',response)