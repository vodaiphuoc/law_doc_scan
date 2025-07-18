import torch
from typing import Tuple, List
import pymupdf
from PIL import Image
import io

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
    
ZOOM_MATRIX = pymupdf.Matrix(2.0, 2.0)

def pdf2images(local_img_path:str)->List[Image.Image]:
    r"""
    Conver one PDF doc to list of page images
    """
    doc = pymupdf.open(local_img_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Render page to image with higher resolution
        pix = page.get_pixmap(matrix=ZOOM_MATRIX)
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data)).convert('RGB')
        images.append(image)
    
    return images