from commons.configs.model import ModelConfigQuant
from commons.schemas.model import (
    DocumentDetailsExtraction, 
    CoverDocumentExtraction
)
from commons.schemas.mq_messages import DOCUMENT_TASKS

from commons.logger import get_logger
from utils import pdf2images

import json
from typing import Any, List, Dict,Type, cast
import aiohttp
from pydantic import AliasChoices
import re

logger = get_logger("ModelClient")

SCHEMAS_TYPES = Type[DocumentDetailsExtraction]|Type[CoverDocumentExtraction]
SINGLE_RESPONSE_TYPES = DocumentDetailsExtraction | CoverDocumentExtraction
FINAL_RESPONSE_TYPES = List[DocumentDetailsExtraction|CoverDocumentExtraction]


def _aliases2format(schemas:  SCHEMAS_TYPES)->str:
    r"""
    Conver aliases in `schemas` into JSON format
    """
    output = '```json\n{\n'
    for _, v in schemas.model_fields.items():
        _alias_choices: AliasChoices = cast(AliasChoices, v.validation_alias)
        output+="    **"+cast(str,_alias_choices.choices[0])+"**\n"
    output += '}```'
    return output

_COVER_DOC_TEMPATE = """
Với văn bản viết tay chính sau, hãy nhận diện thông tin trong văn bản.
đầu ra theo format được mô tả sau đây:
{format_with_aliases}
"""

COVER_DOC_QUERY = _COVER_DOC_TEMPATE.format(
    format_with_aliases = _aliases2format(CoverDocumentExtraction)
)


_LAW_DOC_TEMPATE = """
Với văn bản chính sau, trích xuất thông tin trong văn bản.
đầu ra theo format được mô tả sau đây:
{format_with_aliases}
"""

LAW_DOC_QUERY = _LAW_DOC_TEMPATE.format(
    format_with_aliases = _aliases2format(DocumentDetailsExtraction)
)



class ModelWrapperClient(object):
    
    def __init__(self, config: ModelConfigQuant):
        self.config = config
        self.headers: Dict[str, str] = {
            'content-type': 'application/json',
            'Authorization': f'Bearer {config.api_key}'
        }

        self._default_payload: Dict[str, str|bool|int|float] = {
            "model": self.config.model_id,
            "stream": False,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "min_p": self.config.min_p,
            "repetition_penalty": self.config.repetition_penalty,
            "max_tokens": 512
        }

    async def forward(
            self, 
            local_path_pdf:str, 
            task: DOCUMENT_TASKS
        )->None|FINAL_RESPONSE_TYPES:
        r"""Main processing of model"""

        original_pages_images = pdf2images(local_path_pdf, return_base64_image= True)[:1]

        # select pages in dedicated index
        _num_pages = len(original_pages_images)
        if task == "cover":
            page_idx = [0]
        else:    
            page_idx = list(range(_num_pages))
        pages_images = list(map(original_pages_images.__getitem__, page_idx))

        # construct content field in standard format
        request_content: List[Dict[str, str]|Dict[str, str|Dict[str,str]]] = [{
            'type': 'text',
            'text': COVER_DOC_QUERY \
                if task == "cover" \
                else LAW_DOC_QUERY
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

        # print(json.dumps(payload, indent = 4, ensure_ascii=False))

        async with aiohttp.ClientSession(
            base_url=self.config.modal_url
            ) as session:
            responses = await ModelWrapperClient._send(
                session = session, 
                headers = self.headers,
                payload = payload,
                timeout = 7*60,
                
            )
            if responses is not None:
                return ModelWrapperClient._post_prosessing(
                    responses=responses, 
                    output_format = CoverDocumentExtraction \
                        if task == 'cover' \
                        else DocumentDetailsExtraction
                )
            else:
                return None

    @staticmethod
    async def _send(
            session: aiohttp.ClientSession, 
            headers: dict[str, str],
            payload: dict[str, Any], 
            timeout: int
        )->List[str]|None:
        
        try:
            total_response: List[str] = []
            async with session.post(
                    "/v1/chat/completions", 
                    json=payload, 
                    headers=headers,
                    timeout=timeout
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
                        )
                        total_response.append(chunk["choices"][0]["message"]['content'])
            return total_response
        
        except (TimeoutError, Exception) as e:
            logger.error("error in `_send` function, msg: {}".format(e))
            return None

    @staticmethod
    def _post_prosessing(
        responses: List[str], 
        output_format: SCHEMAS_TYPES
        )->FINAL_RESPONSE_TYPES:

        outputs:FINAL_RESPONSE_TYPES = []
        for _res in responses:
            try:
                json_data = re.sub(r'```json\n|\n```','',_res)

                # validation via alias
                parsed: SINGLE_RESPONSE_TYPES = output_format.model_validate_json(
                    json_data, 
                    by_alias=True
                )
                outputs.append(parsed)

            except Exception as e:
                logger.error("error in `_post_prosessing` function, msg: {}".format(e))
                continue
        
        return outputs

    async def health_check(self):
        async with aiohttp.ClientSession(base_url=self.config.modal_url) as session:
            async with session.get(
                "health",
                headers=self.headers,
                timeout=6*60
            ) as resp:
                async for raw in resp.content:
                    print('health_check',raw)