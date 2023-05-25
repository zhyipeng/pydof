import typing

from pydoftools.npk.consts import *
from pydoftools.utils.io import read_ascii_string, read_struct
from .img import IMG
from .v1 import IMGv1
from .v2 import IMGv2
from .v4 import IMGv4
from .v5 import IMGv5
from .v6 import IMGv6


class NotIMGFileException(Exception):
    pass


class IMGVersionException(Exception):
    pass


class IMGFactory:
    cls_version_map = {
        IMG_VERSION_1: IMGv1,
        IMG_VERSION_2: IMGv2,
        IMG_VERSION_4: IMGv4,
        IMG_VERSION_5: IMGv5,
        IMG_VERSION_6: IMGv6,
    }

    @classmethod
    def instance(cls, version: int):
        _cls = cls.cls_version_map.get(version)
        if _cls is None:
            raise IMGVersionException(version)

        return _cls()

    @classmethod
    def open(cls, io: typing.IO) -> 'IMG':
        magic = read_ascii_string(io, 18)
        if magic not in [IMG_MAGIC, IMG_MAGIC_OLD]:
            raise NotIMGFileException

        images_size = 0
        if magic == IMG_MAGIC:
            # images_size without version,count,extra(color_board,sprites)...
            images_size, = read_struct(io, 'i')
        elif magic == IMG_MAGIC_OLD:
            # unknown.
            read_struct(io, 'h')

        # keep: 0
        keep, version = read_struct(io, '<2i')

        img = IMGFactory.instance(version)
        img.open(io, version, images_size, keep)

        return img
