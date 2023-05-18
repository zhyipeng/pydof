import typing
import zlib

from pydof.npk.consts import IMAGE_FORMATS_DDS
from pydof.utils import image as image_util
from pydof.utils.io import read_range, read_struct, write_struct
from pydof.utils.zlib import zlib_decompress
from .format import FormatConvertor


class Sprite:
    def __init__(self):
        self._io: typing.IO | None = None
        self._offset = 0
        self._data: bytes | None = None
        self._zip_data: bytes | None = None

        self.keep = 0
        self.format = 0
        self.index = 0
        self.data_size = 0
        self.raw_size = 0
        self.w = 0
        self.h = 0

    def set_io_info(self, offset: int, io: typing.IO):
        self._io = io
        self._offset = offset

    @classmethod
    def open(cls, io: typing.IO) -> 'Sprite':
        keep, fmt, index, data_size, raw_size, w, h = read_struct(io, '<7i')

        sprite = cls()
        sprite.keep = keep
        sprite.format = fmt
        sprite.index = index
        sprite.data_size = data_size
        sprite.raw_size = raw_size
        sprite.w = w
        sprite.h = h

        return sprite

    def load(self, force=False):
        if self._io and (force or not self.is_loaded):
            self._zip_data = read_range(self._io, self._offset, self.data_size)
            self._data = zlib_decompress(self._zip_data)

    def save(self, io: typing.IO):
        self.compress()
        write_struct(io, '<7i', self.keep, self.format, self.index,
                     self.data_size, self.raw_size, self.w, self.h)

    @property
    def is_loaded(self) -> bool:
        return self._data is not None

    @property
    def data(self) -> bytes:
        if not self.is_loaded:
            self.load()
        return self._data

    def set_data(self, data: bytes):
        self.raw_size = len(data)
        self._data = data
        self.data_size = 0
        self._zip_data = None

    def compress(self):
        data = self.data
        self.raw_size = len(data)
        data = zlib.compress(data)
        self.data_size = len(data)
        self._zip_data = data

    @property
    def zip_data(self) -> bytes:
        if not self.is_loaded:
            self.load()
        if self._zip_data is None and self._data:
            self.compress()
        return self._zip_data

    def build(self, box: tuple[int, int, int, int] = None, rotate=0) -> image_util.Image:
        data = self.data

        if self.format in IMAGE_FORMATS_DDS:
            image = image_util.load_dds(data, box, rotate)
        else:
            if box:
                data = FormatConvertor.to_raw_crop(data, self.format, self.w, box)
                [l, t, r, b] = box
                w, h = r - l, b - t
            else:
                data = FormatConvertor.to_raw(data, self.format)
                w, h = self.w, self.h
            image = image_util.load_raw(data, w, h, rotate)

        return image
