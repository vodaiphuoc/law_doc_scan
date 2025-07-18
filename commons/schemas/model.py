from pydantic import BaseModel, Field, computed_field
from typing import Union, Tuple, Dict


class SigningDay(BaseModel):
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


class Fields2Extract(BaseModel):
    issuing_agency: str = Field(
        description = "Cơ quan ban hành văn bản"
    )

    document_number: int = Field(
        description = "Số  hiệu văn bản"
    )

    doc_signature :str = Field(
       description="Ký hiệu văn bản gồm nhóm chữ viết tắt của tên loại văn bản và tên cơ quan ban hành văn bản",
       examples=["QĐ/BKTTW","HD/TU","CV/BTCTU","BC/HU","QĐ/TU","QC/BTCTU-BDVTU","TT-BTP"]
    )

    date_of_signing: SigningDay

    document_type: str = Field(
        description="Thể loại văn bản",
        examples=["quyết định","nghị quyết","thông tư","pháp lệnh"]
    )

    summarization: str = Field(
        description="Trích yếu nội dung trong văn bản"
    )
 

    signing_person: str = Field(
        description="Tên người ký ở cuối văn bản"
    )
