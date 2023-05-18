from pydof.npk.consts import (IMAGE_FORMAT_1555, IMAGE_FORMAT_4444,
                              IMAGE_FORMAT_8888)
from .f1555 import Format1555
from .f4444 import Format4444
from .f8888 import Format8888
from .format import Format


class ImageFormatException(Exception):
    pass


class FormatFactory:
    cls_format_map = {
        IMAGE_FORMAT_1555: Format1555,
        IMAGE_FORMAT_4444: Format4444,
        IMAGE_FORMAT_8888: Format8888,
    }

    @classmethod
    def instance(cls, image_format: int) -> 'Format':
        _cls = cls.cls_format_map.get(image_format)
        if _cls is None:
            raise ImageFormatException(image_format)

        return _cls()
