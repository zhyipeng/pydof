import typing
from io import BytesIO

from PIL import Image as PILImage

from pydoftools.utils.io import read_range


class Format:
    ps = 0

    def to_raw(self, data: bytes) -> bytes:
        with BytesIO(data) as io:
            with BytesIO() as io_raw:
                self.callback_to_raw(io, io_raw)
                data_raw = read_range(io_raw)
        return data_raw

    def to_raw_crop(self, data: bytes, w: int, box: tuple[int, int, int, int]) -> bytes:
        with BytesIO(data) as io:
            with BytesIO() as io_raw:
                [left, top, right, bottom] = box
                for y in range(top, bottom):
                    o = y * w * self.ps
                    for x in range(left, right):
                        io.seek(o + x * self.ps)
                        self.callback_to_raw_crop_convert(io, io_raw)

                data_raw = read_range(io_raw)
        return data_raw

    def from_image(self, image: 'PILImage') -> tuple[bytes, int, int]:
        with BytesIO() as io:
            w, h = image.width, image.height

            for y in range(h):
                for x in range(w):
                    pixel = image.getpixel((x, y))
                    self.callback_from_image_convert(io, pixel)

            data_raw = read_range(io)

        return data_raw, w, h

    def callback_to_raw(self, io: typing.IO, io_raw: typing.IO):
        pass

    def callback_to_raw_crop_convert(self, io: typing.IO, io_raw: typing.IO):
        pass

    def callback_from_image_convert(self, io: typing.IO, pixel: tuple[int, int, int, int]):
        pass
