from commons.configs.model import ModelConfigQuant
from commons.schemas.model import DocumentDetailsExtraction, CoverDocumentExtraction
from commons.logger import get_logger

from .examples import Examples

from utils import pdf2images
import json
from typing import Any, Literal
import aiohttp
from copy import deepcopy

DOCUMENT_TASKS = Literal['cover_document','law_document']


# print(json.dumps(CoverDocumentExtraction.model_json_schema(), ensure_ascii=False))
# print('---------------------------------------')
class ModelWrapperClient(object):
    cover_doc_inst = """
nhiệm vụ chính nhận diện thông tin viết tay trong văn bản.
"""
    cover_doc_query = """
Với văn bản viết tay chính sau, hãy nhận diện thông tin trong văn bản.
"""
    cover_doc_reponse_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "Cover-Document-Extraction",
            "schema": CoverDocumentExtraction.model_json_schema()
        }
    }

    law_doc_query = """
Với văn bản chính sau, trích xuất thông tin trong văn bản.
"""
    law_doc_reponse_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "Document-Details-Extraction",
            "schema": DocumentDetailsExtraction.model_json_schema()
        }
    }

    def __init__(self, config: ModelConfigQuant):
        self.config = config
        self.headers = {
            'content-type': 'application/json',
            'Authorization': f'Bearer {config.api_key}'
        }

        _default_payload = {
            "model": self.config.model_id,
            "stream": False,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "max_tokens": 500
        }

        self._cover_payload = deepcopy(_default_payload)
        self._cover_payload["response_format"] = self.cover_doc_reponse_format

        self._law_payload = deepcopy(_default_payload)
        self._law_payload["response_format"] = self.law_doc_reponse_format

        # build examples
        self.example_msgs = [{
            'role':'system',
            'content': self.cover_doc_inst
        }]

        for _ith, exp in enumerate(Examples().example_list):
            _encoded_image = pdf2images(exp.path, return_base64_image= True)[0]
            self.example_msgs.extend([{
                'role':'user',
                'content': [{
                        'type': 'text',
                        'text': f"\nVí dụ {_ith+1}:\nCâu hỏi: {exp.question}"
                    },{
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/png;base64,{_encoded_image}"
                        }
                    }]
            },{
                'role':'assistant',
                'content': exp.answer
            }])


    async def forward(self, local_path_pdf:str, task: DOCUMENT_TASKS):
        original_pages_images = pdf2images(local_path_pdf, return_base64_image= True)

        # select pages in dedicated index
        _num_pages = len(original_pages_images)
        if task == "cover_document":
            page_idx = [0]
        else:    
            page_idx = [0,1, _num_pages-1] if _num_pages >= 3 else [0,_num_pages-1]
        pages_images = list(map(original_pages_images.__getitem__, page_idx))

        # construct content field in standard format
        if task == "cover_document":
            request_content = [{
                'type': 'text',
                'text': self.cover_doc_query
            }]

        else:
            request_content = [{
                'type': 'text',
                'text': self.law_doc_query
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
        if task == "cover_document":
            msg = []
            msg.extend(self.example_msgs)
            msg.append({
                'role':'user',
                'content': request_content
            })
            payload: dict[str, Any] = {
                "messages": msg
            }
        else:
            payload: dict[str, Any] = {
                "messages": [{
                    'role':'user',
                    'content': request_content
                }]
            }
        
        if task == "cover_document":
            payload.update(self._cover_payload)
        else:
            payload.update(self._law_payload)


        # print(json.dumps(payload, indent = 4, ensure_ascii=False))


        async with aiohttp.ClientSession(base_url=self.config.modal_url) as session:
            async with session.post(
                "/v1/chat/completions", 
                json=payload, 
                headers=self.headers,
                timeout=7*60
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

    async def health_check(self):
        async with aiohttp.ClientSession(base_url=self.config.modal_url) as session:
            async with session.get(
                "health",
                headers=self.headers,
                timeout=6*60
            ) as resp:
                async for raw in resp.content:
                    print('health_check',raw)