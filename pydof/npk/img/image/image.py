import os
import typing

from pydof.npk.consts import *
from pydof.utils import image as image_util
from pydof.utils.io import read_range, read_struct, write_struct
from .exception import ImageExtraException
from .format import FormatConvertor


class Image:
    def __init__(self, fmt: int):
        self._io = None
        self._data = None
        self._offset = 0
        self._size = 0

        self.format = fmt
        self.extra = IMAGE_EXTRA_NONE
        self.w = 0
        self.h = 0
        self.x = 0
        self.y = 0
        self.mw = 0
        self.mh = 0

    def set_io_info(self, offset: int, io=None):
        self._offset = offset
        self._io = io

    def open(self, io: typing.IO, fix_size=False, **kwargs) -> 'Image':
        w, h, size, x, y, mw, mh = read_struct(io, '<7i')
        self.w = w
        self.h = h
        self._size = size
        # fix size to real size.
        if fix_size and self.extra == IMAGE_EXTRA_NONE:
            self._size = self.size_fix
        self.x = x
        self.y = y
        self.mw = mw
        self.mh = mh

        return self

    @property
    def size(self) -> int:
        return self._size

    @property
    def size_fix(self) -> int:
        return self.w * self.h * PIX_SIZE[self.format]

    def load(self, force=False):
        if self._io and (force or not self.is_loaded):
            self._data = read_range(self._io, self._offset, self._size)

    def save(self, io: typing.IO):
        # format, extra, w, h, size, x, y, mw, mh
        write_struct(io, '<9i', self.format, self.extra, self.w, self.h,
                     self.size, self.x, self.y, self.mw, self.mh)

    @property
    def is_loaded(self) -> bool:
        return self._data is not None

    @property
    def data(self) -> bytes:
        if not self.is_loaded:
            self.load()
        return self._data

    def set_data(self, data: bytes):
        self._data = data
        self._size = len(data)

    def from_image(self, image: image_util.Image):
        if self.extra not in [IMAGE_EXTRA_NONE, IMAGE_EXTRA_ZLIB]:
            raise ImageExtraException(self.extra)

        self.set_data(FormatConvertor.from_image(image, self.format))

    def convert(self, image_format: int):
        if self.extra not in [IMAGE_EXTRA_NONE, IMAGE_EXTRA_ZLIB]:
            raise ImageExtraException(self.extra)

        raw_data = FormatConvertor.to_raw(self.data, self.format)
        image = image_util.load_raw(raw_data, self.w, self.h)
        data, w, h = FormatConvertor.from_image(image, image_format)
        self._data = data
