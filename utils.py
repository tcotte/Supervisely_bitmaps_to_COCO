import base64
import typing
import zlib

import cv2
import numpy as np

# according to Supervisely documentation -> https://developer.supervisely.com/getting-started/supervisely-annotation-format/objects#bitmap
def base64_2_mask(s: str) -> np.array:
    """
    This function takes a base64 encoded (encoded bitmap from Supervisely) and converts it to a binary numpy array
    :param s: the base64 encoded
    :return: a binary numpy array
    """
    z = zlib.decompress(base64.b64decode(s))
    n = np.fromstring(z, np.uint8)
    mask = cv2.imdecode(n, cv2.IMREAD_UNCHANGED)[:, :, 3].astype(bool)
    return mask

def bitmap_to_array(bitmap: typing.Dict, img_size: typing.Tuple[int, int]) -> np.ndarray:
    """
    This function takes a bitmap dictionary from Supervisely .json annotation file + the associated image size and returns a binary numpy array.
    It enables to do the offset of the bitmap depending on the origin of the bitmap on the full-size mask.
    :param bitmap: Supervisely dictionary bitmap
    :param img_size: tuple of image size (-> height, width)
    :return: full-size mask
    """
    mask = np.zeros(img_size, np.uint8)
    stamp = base64_2_mask(s=bitmap["data"])
    origin_x, origin_y = bitmap["origin"]
    mask[origin_y: origin_y + stamp.shape[0],
       origin_x : origin_x + stamp.shape[1]] = stamp
    return mask

def create_empty_coco_file(classes: typing.List) -> typing.Dict:
    """
    Create an empty coco file filling in only categories.
    :param classes: categories used in the dataset that we want to annotate through the COCO file.
    :return: annotation file that we will use.
    """
    coco_format = {
        'images': [],
        'annotations': [],
        'categories': []
    }

    for i, c in enumerate(classes):
        category = {
            'id': i + 1,
            'name': c,
            'supercategory': 'none'
        }

        coco_format["categories"].append(category)

    return coco_format