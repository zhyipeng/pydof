import typing

from pydof.npk.consts import *
from pydof.utils.io import read_struct
from .exception import *
from .extra import SpriteZlibImage, ZlibImage
from .image import Image
from .link import ImageLink


class ImageFactory:
    cls_extra_map = {
        IMAGE_EXTRA_NONE: Image,
        IMAGE_EXTRA_ZLIB: ZlibImage,
        IMAGE_EXTRA_ZLIB_SPRITE: SpriteZlibImage,
    }

    @classmethod
    def instance(cls, fmt=IMAGE_FORMAT_8888, extra=IMAGE_EXTRA_NONE) -> Image:
        _cls = cls.cls_extra_map.get(extra)
        if _cls is None:
            raise ImageExtraException(extra)

        return _cls(fmt)

    @classmethod
    def open(cls, io: typing.IO, images: list[Image], **kwargs) -> Image | ImageLink:
        fmt, = read_struct(io, '<i')
        if fmt not in IMAGE_FORMATS_ALL:
            raise ImageFormatException(fmt)

        if fmt == IMAGE_FORMAT_LINK:
            return ImageLink.open(io, images, **kwargs)
        else:
            extra, = read_struct(io, '<i')
            return ImageFactory.instance(fmt, extra).open(io, **kwargs)
