from commons.configs.model import ModelConfigQuant
from commons.logger import get_logger

from utils import pdf2images
import json
from typing import Any, Dict, Iterable, List, Optional, Union
import aiohttp

class ModelWrapperClient(object):
    query = """
Với văn bản chính sau, trích xuất thông tin trong văn bản.
đầu ra theo format JSON được mô tả sau đây:
```json
{
    **Cơ quan ban hành văn bản**
    **Số  hiệu văn bản**
    **Thể loại văn bản**
    **Tiêu đề  văn bản**
    **Tên người ký**
}
"""

    def __init__(self, config:  ModelConfigQuant):
        self.config = config
        self.headers = {
            'content-type': 'application/json',
            'Authorization': f'Bearer {config.api_key}'
        }

    async def forward(self, local_path_pdf:str):
        pages_images = pdf2images(local_path_pdf, return_base64_image= True)[:1]
        print('num pages: ', len(pages_images))

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

        # construct payload with generation params
        payload: dict[str, Any] = {
            "messages": [{
                'role':'user',
                'content': request_content
            }], 
            "model": self.config.model_id, 
            "stream": False,
            "temperature":self.config.temperature,
            "top_p":self.config.top_p,
            "top_k":self.config.top_k,
        }

        async with aiohttp.ClientSession(base_url=self.config.modal_url) as session:
            async with session.post(
                "/v1/chat/completions", 
                json=payload, 
                headers=self.headers,
                timeout=4*60
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
                    assert (
                        chunk["object"] == "chat.completion"
                    )  # or something went horribly wrong
                    print(chunk["choices"][0]["message"])
