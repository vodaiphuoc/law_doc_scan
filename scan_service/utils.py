import torch
from typing import Tuple, List, Union
import pymupdf
from PIL import Image
import io
import requests
import base64

def get_device()->Tuple[torch.device, bool]:
    """
    Get device and able to use flash attention or not
    """
    if torch.cuda.is_available():
        major, minor = torch.cuda.get_device_capability(device="cuda")
        device = torch.device("cuda")
        if major >= 7 and minor >= 5:
            return device, True
        else:
            return device, False
    else:
        return torch.device("cpu"), False

def pil_image_to_base64(image: Image.Image, format="PNG") -> str:
    """
    Converts a PIL.Image object to a Base64 encoded string.

    Args:
        image: The PIL.Image object.
        format: The format to save the image in (e.g., "PNG", "JPEG").

    Returns:
        A Base64 encoded string of the image.
    """
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


ZOOM_MATRIX = pymupdf.Matrix(2.0, 2.0)

def pdf2images(
        img_path:str, 
        is_remote_path: bool = False,
        return_base64_image:bool = False
        )->Union[List[Image.Image],List[str]]:
    r"""
    Conver one PDF doc to list of page images
    Args:
        img_path (str):  path to the pdf file, for remote file, its a url
        is_remote_path (bool): local or remote path
        return_base64_image (bool): wether or not return encode base64 string
    """
    if is_remote_path:
        response_data = requests.get(
            url = img_path,    
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            })

        doc = pymupdf.Document(stream=response_data.content)
    else:
        doc = pymupdf.open(img_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Render page to image with higher resolution
        pix = page.get_pixmap(matrix=ZOOM_MATRIX)
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data)).convert('RGB')
        images.append(image)
    
    if return_base64_image:
        return [pil_image_to_base64(_img) for _img in images]
    else:
        return images


