# Example modeling for fewshot example
from pydantic import BaseModel, Field, FileUrl, computed_field, HttpUrl
from typing import Union, Tuple, Dict, List

class ExampleModel(BaseModel):
    url: HttpUrl
    question: str = Field(
        default="""<image>\n, trích xuất thông tin trong văn bản sau.
đầu ra theo format JSON được mô tả sau đây:
**Cơ quan ban hành văn bản**
**Số ,ký hiệu văn bản**
**Thể loại văn bản**
**Tóm tắt văn bản**
**Tên người ký**
"""
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
                url = "https://tulieuvankien.dangcongsan.vn/Uploads/2025/6/7/20/QD-331-TW.pdf",
                answer = """
```json
{
    "Cơ quan ban hành văn bản": "Ban Chấp hành Trung ương",
    "Số ,ký hiệu văn bản": "331-QĐ/TW",
    "Thể loại văn bản": "QUYẾT ĐỊNH",
    "Tóm tắt văn bản": "Quyết định số 331-QĐ/TW, được Ban Bí thư Trung ương Đảng Cộng sản Việt Nam ban hành vào ngày 18 tháng 6 năm 2025, ban hành quy trình 
mẫu thực hiện kiểm tra, giám sát của các cơ quan tham mưu, giúp việc cấp ủy. Quyết định này nêu rõ trách nhiệm của các cơ quan Đảng và 
đảng viên liên quan trong việc thực hiện quy trình này. Đồng thời, quyết định có hiệu lực từ ngày ký. Tài liệu được gửi đến các tỉnh ủy, 
thành ủy, đảng ủy trực thuộc Trung ương, các ban Đảng Trung ương, các đảng ủy bộ, ngành, tổ chức chính trị - xã hội ở Trung ương, 
các đảng ủy đơn vị sự nghiệp Trung ương, các đồng chí Ủy viên Ban Chấp hành Trung ương Đảng, và được lưu tại Văn phòng Trung ương Đảng.",
    "Tên người ký": "Trần Cẩm Tú"
}
```
"""
            )
        ]
    )
