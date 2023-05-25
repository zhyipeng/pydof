import typing
import zlib

from pydoftools.npk.consts import IMAGE_EXTRA_ZLIB
from pydoftools.utils.zlib import zlib_decompress
from ..image import Image


class ZlibImage(Image):

    def __init__(self, fmt: int):
        super().__init__(fmt)
        self.extra = IMAGE_EXTRA_ZLIB

        self._zip_data: bytes | None = None

    def load(self, force=False):
        super().load(force)
        self._zip_data = self._data
        self._data = zlib_decompress(self._zip_data)

    def compress(self):
        data = zlib.compress(self.data)
        self._size = len(data)
        self._zip_data = data

    def set_data(self, data: bytes):
        super().set_data(data)
        self._size = 0
        self._zip_data = None

    @property
    def zip_data(self) -> bytes:
        if not self.is_loaded:
            self.load()
        if self._zip_data is None and self._data:
            self.compress()
        return self._zip_data

    def save(self, io: typing.IO):
        self.compress()
        super().save(io)
