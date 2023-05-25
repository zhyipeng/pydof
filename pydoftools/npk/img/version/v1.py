import typing
from io import SEEK_CUR

from pydoftools.npk.consts import IMG_MAGIC_OLD
from pydoftools.utils.io import write_ascii_string, write_struct
from .img import IMG
from ..image import ImageFactory, ImageLink


class IMGv1(IMG):

    def _callback_images_open(self, count: int):
        io = self._io

        images = []
        for _ in range(count):
            image = ImageFactory.open(io, images, fix_size=True)
            images.append(image)

            offset = io.tell()
            image.set_io_info(offset, io)
            io.seek(image.size, SEEK_CUR)

        self._images = images

    def _callback_after_images_open(self, images_size: int):
        for image in self._images:
            if isinstance(image, ImageLink):
                image.load_image()

    def _callback_before_save(self, io: typing.IO):
        write_ascii_string(io, IMG_MAGIC_OLD)
        # TODO: unknown, now be zero.
        write_struct(io, 'h', 0)

    @property
    def _common_size(self) -> int:
        # magic, unknown
        size = len(IMG_MAGIC_OLD) + 3

        return size

    def _callback_images_save(self, io: typing.IO):
        for image in self._images:
            image.save(io)
            io.write(image.data)
