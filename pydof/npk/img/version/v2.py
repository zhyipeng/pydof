import typing

from pydof.npk.consts import IMAGE_EXTRA_ZLIB_SPRITE, IMG_MAGIC, IMG_VERSION_2
from pydof.utils.io import write_ascii_string, write_struct
from .v1 import IMGv1
from ..image import ImageFactory, ImageLink, SpriteZlibImage, ZlibImage


class IMGv2(IMGv1):
    def _callback_images_open(self, count: int):
        io = self._io

        images = []
        for _ in range(count):
            image = ImageFactory.open(io, images, fix_size=self._version == IMG_VERSION_2)
            images.append(image)

        self._images = images

    def _callback_after_images_open(self, images_size: int):
        super()._callback_after_images_open(images_size)
        io = self._io

        # behind header.
        if self._version == IMG_VERSION_2:
            offset = images_size + 32
        else:
            offset = io.tell()

        offset = self._callback_before_count_image_offset(offset)

        # count image offset.
        for image in self._images:
            if isinstance(image, ImageLink) or image.extra == IMAGE_EXTRA_ZLIB_SPRITE:
                continue

            image.set_io_info(offset, io)
            offset += image.size

    def _callback_before_count_image_offset(self, offset: int):
        return offset

    def _callback_before_save(self, io: typing.IO):
        # images_size
        write_ascii_string(io, IMG_MAGIC)
        write_struct(io, 'i', self.images_header_size)

    @property
    def _common_size(self) -> int:
        # magic, images_size
        size = len(IMG_MAGIC) + 5

        return size

    def _callback_images_save(self, io: typing.IO):
        for image in self._images:
            image.save(io)

    def _callback_after_images_save(self, io: typing.IO):
        for image in self._images:
            if isinstance(image, (ImageLink, SpriteZlibImage)):
                data = image.data
                if isinstance(image, ZlibImage):
                    data = image.zip_data

                io.write(data)
