# Example modeling for fewshot example
from pydantic import BaseModel, Field, computed_field
from typing import Union, Tuple, Dict, List
from commons.schemas.model import CoverDocumentExtraction
import json
import os

EXAMPLE_DATA_DIR = os.path.dirname(__file__).replace("scan_service/model","example_data")

# đầu ra theo format JSON được mô tả sau đây:
# {json.dumps(CoverDocumentExtraction.model_json_schema(),ensure_ascii=False)}

class ExampleModel(BaseModel):
    path: str
    question: str = Field(
        default=f"""Với văn bản viết tay, hãy nhận diện thông tin trong văn bản."""
    )
    answer: str

    @computed_field
    @property
    def tostring(self)->str:
        return f"Câu hỏi: {self.question}\nTrả lời: {self.answer}\n"

class Examples(BaseModel):
    example_list: List[ExampleModel] = Field(
        default=[
            ExampleModel(
                path = os.path.join(EXAMPLE_DATA_DIR,"BIA.pdf"),
                answer = """
```json
{
    "main_content": "Hồ sơ: Biểu thống kê công tác Tuyên giáo năm 2017",
    "start_day": {
        "day": None,
        "month": 12,
        "year": 2017
    },
    "end_day": {
        "day": None,
        "month": 12,
        "year": 2017
    },
    "storage_period": "V2"
}
```
"""
            )
        ]
    )
