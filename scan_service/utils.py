from typing import List, Union
import pymupdf
from pymupdf import Page, Document
from PIL import Image
import io
import requests
import base64


def pil_image_to_base64(image: Image.Image, format:str="PNG") -> str:
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


# ZOOM_MATRIX = pymupdf.Matrix(1.3, 1.3)
ZOOM_MATRIX = pymupdf.Matrix(1.0, 1.0)

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
    doc: Document| None = None

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
    
    images: List[Image.Image] = []

    for page_num in range(len(doc)):
        page: Page = doc.load_page(page_id = page_num) # type: ignore
        # Render page to image with higher resolution
        pix = page.get_pixmap(matrix=ZOOM_MATRIX) # type: ignore
        img_data = pix.tobytes("ppm") # type: ignore
        image = Image.open(io.BytesIO(img_data)).convert('RGB') # type: ignore
        print('image sizze:', image.size)

        W, H = image.size
        if H > W:
            images.append(image)
        else:
            continue
    
    if return_base64_image:
        return [pil_image_to_base64(_img) for _img in images]
    else:
        return images


