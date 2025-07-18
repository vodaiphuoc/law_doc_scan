import torchvision.transforms as T
from torchvision.transforms.functional import InterpolationMode
from typing import List, Tuple,Union
from PIL import Image
import torch

from configs.model import ModelConfig

class Image_PreProcessing(object):
    def __init__(self, config: ModelConfig):
        self.config = config
        self.transform_compose = T.Compose([
            T.Resize(
                size = (config.target_title_size, config.target_title_size), 
                interpolation=InterpolationMode.BILINEAR
            ),
            T.Normalize(mean=config.transform_mean, std=config.transform_std)
        ])
    
    @staticmethod
    def _find_closest_aspect_ratio(
            aspect_ratio: float, 
            target_ratios: List[Tuple[int]], 
            width: int, 
            height:int, 
            image_size:int
        ):
        best_ratio_diff = float('inf')
        best_ratio = (1, 1)
        area = width * height
        for ratio in target_ratios:
            target_aspect_ratio = ratio[0] / ratio[1]
            ratio_diff = abs(aspect_ratio - target_aspect_ratio)
            if ratio_diff < best_ratio_diff:
                best_ratio_diff = ratio_diff
                best_ratio = ratio
            elif ratio_diff == best_ratio_diff:
                if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                    best_ratio = ratio
        return best_ratio

    @staticmethod
    def _dynamic_preprocess(
            image: Image.Image, 
            min_num=1, 
            max_num=12, 
            title_size=448, 
            use_thumbnail=False
        ):
        orig_width, orig_height = image.size
        aspect_ratio = orig_width / orig_height

        # calculate the existing image aspect ratio
        target_ratios = set(
            (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
            i * j <= max_num and i * j >= min_num)
        target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

        # find the closest aspect ratio to the target
        target_aspect_ratio = Image_PreProcessing._find_closest_aspect_ratio(
            aspect_ratio, target_ratios, orig_width, orig_height, title_size)

        # calculate the target width and height
        target_width = title_size * target_aspect_ratio[0]
        target_height = title_size * target_aspect_ratio[1]
        blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

        # resize the image
        resized_img = image.resize((target_width, target_height))
        processed_titles = []
        for i in range(blocks):
            box = (
                (i % (target_width // title_size)) * title_size,
                (i // (target_width // title_size)) * title_size,
                ((i % (target_width // title_size)) + 1) * title_size,
                ((i // (target_width // title_size)) + 1) * title_size
            )
            # split the image
            split_img = resized_img.crop(box)
            processed_titles.append(split_img)
        assert len(processed_titles) == blocks

        if use_thumbnail and len(processed_titles) != 1:
            thumbnail_img = image.resize((title_size, title_size))
            processed_titles.append(thumbnail_img)
        return processed_titles

    def transform(self, page_imgs: Union[Image.Image, List[Image.Image]])->List[torch.Tensor]:
        r"""
        Args:
            page_imgs (Union[Image.Image, List[Image.Image]]): single or list of page image

        Returns:
            stack tensor of titles of all pages in a document
        """
        if not isinstance(page_imgs, list):
            page_imgs = [page_imgs]

        batch_titles = []
        for _page_img in page_imgs:
            titles = Image_PreProcessing._dynamic_preprocess(
                _page_img,
                title_size=self.config.target_title_size, 
                use_thumbnail=True, 
                max_num=self.config.max_num
            )
            batch_titles.extend([
                T.functional.pil_to_tensor(_title).to(torch.bfloat16)
                for _title in titles
            ])
        
        titles_tensor = torch.stack(batch_titles)
        print('titles_tensor shape: ', titles_tensor.shape)
        return self.transform_compose(titles_tensor)
