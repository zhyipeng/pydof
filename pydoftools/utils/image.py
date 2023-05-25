from io import BytesIO

from PIL import Image
from PIL.DdsImagePlugin import DdsImageFile


def load_dds(data: bytes, box: tuple[int, int, int, int] = None, rotate=0) -> Image:
    with BytesIO(data) as io_dds:
        image = DdsImageFile(io_dds)
        if box is not None:
            image = image.crop(box)

        if rotate == 1:
            image = image.transpose(Image.ROTATE_90)

        return image.copy()


def load_raw(data: bytes, w: int, h: int, rotate=0) -> Image:
    image = Image.frombytes('RGBA', (w, h), data)

    if rotate == 1:
        image = image.transpose(Image.ROTATE_90)

    return image
