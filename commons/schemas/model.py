from pydantic import BaseModel, Field, computed_field
from typing import Union, Tuple, Dict


class DayFormat(BaseModel):
    r"""
    Date of signing of the document in format DD/MM/YYYY
    """
    day: int|None = Field(
        description="day in month, None if cannot find in document",
        ge = 1, 
        le=31
    )
    month: int|None = Field(
        description="month in year, None if cannot find in document",
        ge = 1, 
        le = 12
    )
    year: int|None = Field(
        description="year number, None if cannot find in document",
        ge=1900, 
        le= 2030
    )


class DocumentDetailsExtraction(BaseModel):
    issuing_agency: str = Field(
        description = "Cơ quan ban hành văn bản"
    )

    document_number_signature :str = Field(
       description="Số  hiệu và ký hiệu văn bản gồm nhóm chữ viết tắt của tên loại văn bản và tên cơ quan ban hành văn bản",
       examples=["123-QĐ/BKTTW","456-HD/TU","3569-CV/BTCTU","28492-BC/HU","3827-QĐ/TU","9274/TT-BTP"]
    )

    date_of_signing: DayFormat

    document_type: str = Field(
        description="Thể loại văn bản",
        examples=["quyết định","nghị quyết","thông tư","pháp lệnh"]
    )

    summarization: str = Field(
        description="tóm tắt trích yếu nội dung trong văn bản"
    )

    signing_person: str = Field(
        description="Tên người ký ở cuối văn bản"
    )

class CoverDocumentExtraction(BaseModel):
    r"""thông tin trích xuất cho văn bản chữ viết tay"""
    main_content: str = Field(
        description = "nội dung chính chữ viết tay hồ sơ"
    )

    start_day: DayFormat = Field(
        description = "thời gian bắt đầu"
    )

    end_day: DayFormat = Field(
        description = "thời gian kết thúc"
    )

    storage_period: str = Field(
        description="thời hạn bảo quản hồ sơ"
    )
