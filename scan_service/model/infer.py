from commons.configs.model import ModelConfigQuant
from commons.schemas.model import FieldsToExtract
from commons.logger import get_logger

from utils import pdf2images
import json
from typing import Any, Dict, Iterable, List, Optional, Union
import aiohttp

class ModelWrapperClient(object):
    query = """
Với văn bản chính sau, trích xuất thông tin trong văn bản.
"""

    def __init__(self, config: ModelConfigQuant):
        self.config = config
        self.headers = {
            'content-type': 'application/json',
            'Authorization': f'Bearer {config.api_key}'
        }

        self._default_payload = {
            "model": self.config.model_id,
            "stream": False,
            "temperature":self.config.temperature,
            "top_p":self.config.top_p,
            "top_k":self.config.top_k,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "fields-to-extract",
                    "schema": FieldsToExtract.model_json_schema()
                }
            }
        }

    async def forward(self, local_path_pdf:str):
        original_pages_images = pdf2images(local_path_pdf, return_base64_image= True)

        # select pages in dedicated index
        _num_pages = len(original_pages_images)
        page_idx = [0,1, _num_pages-1] if _num_pages >= 3 else [0,_num_pages-1]
        pages_images = list(map(original_pages_images.__getitem__, page_idx))

        # construct content field in standard format
        request_content = [{
            'type': 'text',
            'text': self.query
        }]
        
        request_content.extend([{
                'type': 'image_url',
                'image_url': {
                    'url': f"data:image/png;base64,{_encoded_image}"
                }
            }
            for _encoded_image in pages_images
        ])

        # construct payload and update with `self._default_payload`
        payload: dict[str, Any] = {
            "messages": [{
                'role':'user',
                'content': request_content
            }]
        }
        payload.update(self._default_payload)

        async with aiohttp.ClientSession(base_url=self.config.modal_url) as session:
            async with session.post(
                "/v1/chat/completions", 
                json=payload, 
                headers=self.headers,
                timeout=60
            ) as resp:
                
                async for raw in resp.content:
                    resp.raise_for_status()
                    # extract new content and stream it
                    line = raw.decode().strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):  # SSE prefix
                        line = line[len("data: ") :]

                    chunk = json.loads(line)
                    print(chunk)
                    assert (
                        chunk["object"] == "chat.completion"
                    )  # or something went horribly wrong
                    print(chunk["choices"][0]["message"])

    async def health_check(self):
        async with aiohttp.ClientSession(base_url=self.config.modal_url) as session:
            async with session.get(
                "health",
                headers=self.headers,
                timeout=6*60
            ) as resp:
                async for raw in resp.content:
                    print('health_check',raw)