from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig
import torch

from configs.model import ModelConfig
from utils import get_device, pdf2images
from model.preprocessing import Image_PreProcessing
from model.examples import Examples
from commons.schemas.model import Fields2Extract
from typing import List, Tuple, Union
from PIL import Image

MODEL_DTYPE = torch.float16

class ModelWrapper(object):

    example_inst = "Dưới đây là một số ví dụ bao gồm câu hỏi, trả lời tương ứng:\n{example_details}"

    inst = "Nhiệm vụ của bạn là trích xuất thông tin trong văn bản luật được cung cấp.\n{example_content}"

    query = """
Bây giờ, với văn bản:\n<image>\n, trích xuất thông tin trong văn bản
đầu ra theo format JSON được mô tả sau đây:
**Cơ quan ban hành văn bản**
**Số  hiệu văn bản**
**Ký hiệu văn bản**
**Thể loại văn bản**
**Tóm tắt văn bản**
**Tên người ký**
"""

    def __init__(self, config:  ModelConfig):
        self.device, can_use_flash_attn = get_device()
        self.config = config
        self.model = AutoModel.from_pretrained(
            config.model_id,
            torch_dtype = MODEL_DTYPE,
            # torch_dtype="auto",
            trust_remote_code = True,
            # use_flash_attn = can_use_flash_attn,
            revision="main",
            device_map="auto",
            quantization_config=BitsAndBytesConfig(load_in_8bit=True)
        ).eval()

        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_id,
            trust_remote_code=True,
            use_fast=False,
            revision="main"
        )

        print('model device: ', self.model.device)

        self.pre_process = Image_PreProcessing(config = config)

        self._generation_config = config.generation_config

        self.default_pixel_values_list = []
        self.default_num_patches_list = []
        if config.fewshotconfig.build_examples:    
            example_details = ""

            # loop over each example
            for _ith, _exp in \
                enumerate(Examples().example_list[:config.fewshotconfig.num_examples_to_use]):
                
                pages_images = pdf2images(_exp.url.encoded_string(), is_remote_path = True)
                print(f'example: {_ith}: ',len(pages_images),'pages')
                _batch_titles_per_doc = self.pre_process.transform(pages_images)
                assert len(pages_images) == len(_batch_titles_per_doc)
                
                self.default_pixel_values_list.extend(_batch_titles_per_doc)
                self.default_num_patches_list.extend([_batch_titles.shape[0] for _batch_titles in _batch_titles_per_doc])

                # modeling <image> respect to number of pages of each example's doc
                _multi_pages_image_token = "".join([f"\nTrang {_ith + 1}: <image>\n" for _ith in range(len(_batch_titles_per_doc))])
                example_details += f"Ví dụ {_ith + 1}:\n" + _exp.tostring.replace('<image>',_multi_pages_image_token)
            
            self.question = self.inst.format(
                example_content = self.example_inst.format(example_details = example_details)
            )
            
        else:
            self.question = ""

    def forward(self, local_path_pdf:str):
        r"""
        <https://huggingface.co/OpenGVLab/InternVL-Chat-V1-5>
        # multi-image multi-round conversation, separate images (多图多轮对话，独立图像)
        pixel_values1 = load_image('./examples/image1.jpg', max_num=12).to(torch.bfloat16).cuda()
        pixel_values2 = load_image('./examples/image2.jpg', max_num=12).to(torch.bfloat16).cuda()
        pixel_values = torch.cat((pixel_values1, pixel_values2), dim=0)
        num_patches_list = [pixel_values1.size(0), pixel_values2.size(0)]

        question = 'Image-1: <image>\nImage-2: <image>\nDescribe the two images in detail.'
        response, history = model.chat(tokenizer, pixel_values, question, generation_config,
                                    num_patches_list=num_patches_list,
                                    history=None, return_history=True)
        print(f'User: {question}\nAssistant: {response}')

        question = 'What are the similarities and differences between these two images.'
        response, history = model.chat(tokenizer, pixel_values, question, generation_config,
                                    num_patches_list=num_patches_list,
                                    history=history, return_history=True)
        print(f'User: {question}\nAssistant: {response}')
        """
        pages_images = pdf2images(local_path_pdf)
        print('num pages: ', len(pages_images))
        batch_titles_per_doc = self.pre_process.transform(pages_images)

        assert len(batch_titles_per_doc) == len(pages_images)

        # intitalize for current doc request
        pixel_values_list = []
        num_patches_list = []
        question = ""

        # incase fewshot
        if self.config.fewshotconfig.build_examples:
            
            pixel_values_list.extend(self.default_pixel_values_list)
            num_patches_list.extend(self.default_num_patches_list)

            question += self.question

        # process pixcel values
        pixel_values_list.extend(batch_titles_per_doc)
        pixel_values = torch.cat(pixel_values_list, dim=0).to(MODEL_DTYPE).to(self.model.device)

        # process num_patches_list
        num_patches_list.extend([_batch_titles.shape[0] for _batch_titles in batch_titles_per_doc])

        # process question
        multi_pages_image_token = "".join([f"Trang {_ith + 1}: <image>\n" for _ith in range(len(batch_titles_per_doc))])
        question += self.query.replace('<image>',multi_pages_image_token)

        print('debugging: ')
        print('question: ', question)
        print('num_patches_list: ', num_patches_list)
        print('pixel_values: ', pixel_values.shape, pixel_values.dtype)

        response = self.model.chat(
            tokenizer = self.tokenizer, 
            pixel_values = pixel_values,
            question = question,
            num_patches_list = num_patches_list,
            generation_config = self._generation_config
        )

        print('response: ',response)


LMDEPLOY_PROMPTS_TYPE = List[Tuple[Union[str, List[Image.Image]]]]

class ModelWrapper2(object):

    example_inst = "Dưới đây là một số  **ví dụ** bao gồm câu hỏi, trả lời theo format JSON tương ứng:\n{example_details}"

    inst = "Nhiệm vụ của bạn là trích xuất thông tin trong văn bản luật được cung cấp.\n{example_content}.**Hết ví dụ**"

    query = """
Bây giờ, với văn bản chính sau:\n<image>\n, **trích xuất thông tin trong văn bản**.
đầu ra theo format JSON được mô tả sau đây:
    **Cơ quan ban hành văn bản**
    **Số  hiệu văn bản**
    **Thể loại văn bản**
    **Tên người ký**
- thông tin trích xuất phải bằng ngôn ngữ tiếng việt.
"""

    def __init__(self, config:  ModelConfig):
        self.device, can_use_flash_attn = get_device()
        self.config = config

        from lmdeploy import pipeline, TurbomindEngineConfig, ChatTemplateConfig
        from lmdeploy import GenerationConfig as LD_GenerationConfig
        from lmdeploy.vl import load_image
        from lmdeploy.vl.constants import IMAGE_TOKEN

        self._image_token = IMAGE_TOKEN

        # will be instance of 'lmdeploy.serve.vl_async_engine.VLAsyncEngine'
        self._engine = pipeline(
            config.model_id, 
            backend_config=TurbomindEngineConfig(
                model_format = 'hf',
                session_len=16384, 
                tp=1, 
                quant_policy = 8,
                revision ='main'
                ), 
            chat_template_config=ChatTemplateConfig(model_name='internvl2_5'),
        )

        self._gen_config = LD_GenerationConfig(**config.generation_config)

        self.default_images_list = []
        if config.fewshotconfig.build_examples:    
            example_details = ""

            # loop over each example
            for _ith, _exp in \
                enumerate(Examples().example_list[:config.fewshotconfig.num_examples_to_use]):
                
                pages_images = pdf2images(_exp.url.encoded_string(), is_remote_path = True)
                print(f'example: {_ith}: ',len(pages_images),'pages')
                self.default_images_list.extend(pages_images)
                

                # modeling <image> respect to number of pages of each example's doc
                _multi_pages_image_token = "".join([
                    f"\nTrang {_ith + 1}: {self._image_token}\n" 
                    for _ith in range(len(pages_images))
                ])
                example_details += f"**Ví dụ {_ith + 1}**:\n" + _exp.tostring.replace('<image>',_multi_pages_image_token)
            
            self.question = self.inst.format(
                example_content = self.example_inst.format(example_details = example_details)
            )
            
        else:
            self.question = ""

    def forward(self, local_path_pdf:str):
        r"""
        Example
        response = pipe((f'Image-1: {IMAGE_TOKEN}\nImage-2: {IMAGE_TOKEN}\ndescribe these two images', images))
        """
        pages_images = pdf2images(local_path_pdf)
        print('num pages: ', len(pages_images))

        # intitalize for current doc request
        pixel_images_list = []
        question = ""

        # incase fewshot
        if self.config.fewshotconfig.build_examples:
            pixel_images_list.extend(self.default_images_list)

            question += self.question

        # process pixcel values
        pixel_images_list.extend(pages_images)

        # process question
        multi_pages_image_token = "".join([f"Trang {_ith + 1}: {self._image_token}\n" for _ith in range(len(pages_images))])
        question += self.query.replace('<image>',multi_pages_image_token)

        print('debugging: ')
        print('question: ', question)
        print('pixel_images_list: ', len(pixel_images_list))
        
        _prompts: LMDEPLOY_PROMPTS_TYPE = [(question, pixel_images_list)]
        response = self._engine(_prompts, gen_config = self._gen_config)

        print('response: ',response)