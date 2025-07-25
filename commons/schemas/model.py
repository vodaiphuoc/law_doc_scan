from pydantic import (
    BaseModel, 
    Field, 
    computed_field,
    AliasChoices
)

import re
from typing import Dict

DATE_PATTERNS = [
    {
        'pattern': r"(?:Ngày\s*)?(\d+)(?:\s*tháng)",
        'name': 'date'
    },
    {
        'pattern': r"(?:tháng)?\s*(\d+)\s*năm",
        'name': 'month'
    },
    {
        'pattern': r"năm\s*(\d+)",
        'name': 'year'
    }
]

class CoverDocumentExtraction(BaseModel):
    r"""thông tin trích xuất cho văn bản chữ viết tay"""
    content_description: str = Field(
        validation_alias = AliasChoices("Nội dung viết tay trong hồ sơ"),
        description = "mô tả nội dung chính chữ viết tay hồ sơ"
    )

    start_day: str = Field(
        validation_alias = AliasChoices("Thời gian bắt đầu"),
        description = "thời gian bắt đầu"
    )

    end_day: str = Field(
        validation_alias = AliasChoices("Thời gian kết thúc"),
        description = "thời gian kết thúc"
    )

    storage_period: str = Field(
        validation_alias = AliasChoices("THỜI HẠN BẢO QUẢN HỒ SƠ"),
        description="thời hạn bảo quản hồ sơ"
    )

class DocumentDetailsExtraction(BaseModel):
    issuing_agency: str = Field(
        validation_alias = AliasChoices("cơ quan ban hành"),
        description = "Cơ quan ban hành văn bản",
        examples= ['văn phòng chính phủ', 'ban chấp hành trung ương']
    )

    document_number_signature :str = Field(
        validation_alias = AliasChoices("số  hiệu","số hiệu"),
        description="Số  hiệu và ký hiệu văn bản gồm nhóm chữ viết tắt của tên loại văn bản và tên cơ quan ban hành văn bản",
        examples=["123-QĐ/BKTTW","456-HD/TU","3569-CV/BTCTU","28492-BC/HU","3827-QĐ/TU","9274/TT-BTP"]
    )

    date_of_signing: str = Field(
        validation_alias = AliasChoices("thời gian thực hiện văn bản"),
        description="ngày thực hiện văn bản",
    )

    document_type: str = Field(
        validation_alias = AliasChoices("loại văn bản"),
        description="loại văn bản quy phạm pháp luật",
        examples=["quyết định","nghị quyết","thông tư","pháp lệnh","thông báo"]
    )

    summarization: str = Field(
        validation_alias = AliasChoices("tóm tắt nội dung"),
        description="tóm tắt nội dung trong văn bản"
    )

    signing_person: str = Field(
        validation_alias = AliasChoices("tên người ký","người ký"),
        description="Tên người ký ở cuối văn bản"
    )

    @computed_field # type: ignore[misc] 
    @property
    def convert_date_to_dict(self)->Dict[str,int|None]:
        extract_datetime: Dict[str,int|None] = {}

        for _pattern in DATE_PATTERNS:
            _match = re.search(_pattern['pattern'], self.date_of_signing)
            if _match is not None:
                extract_datetime[_pattern['name']] = int(_match.group(1))
            else:
                extract_datetime[_pattern['name']] = None

        return extract_datetime