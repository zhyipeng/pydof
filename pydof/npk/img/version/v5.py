import typing

from PIL import Image as PILImage

from pydof.utils.io import read_struct, write_struct
from .v4 import IMGv4
from ..image import Image, Sprite, SpriteZlibImage


class IMGv5(IMGv4):
    def __init__(self):
        super().__init__()
        self._sprites: list[Sprite] = []

    def _callback_before_images_open(self):
        io = self._io

        # sprite image.
        sprite_count, file_size = read_struct(io, '<2i')

        super()._callback_before_images_open()

        sprites = []
        for _ in range(sprite_count):
            sprites.append(Sprite.open(io))

        self._sprites = sprites

    def _callback_before_count_image_offset(self, offset: int) -> int:
        for sprite in self._sprites:
            sprite.set_io_info(offset, self._io)
            offset += sprite.data_size

        return offset

    def load_all(self, force=False):
        super().load_all(force)

        for sprite in self._sprites:
            sprite.load(force)

    @property
    def sprites(self) -> list[Sprite]:
        return self._sprites

    @property
    def images_header_size(self) -> int:
        size = super().images_header_size
        for image in self._images:
            if isinstance(image, SpriteZlibImage):
                # keep, sprite_index, left, top, right, bottom, rotate
                size += 28

        return size

    @property
    def file_size(self) -> int:
        size = super().file_size
        # map_count, img_size
        size += 8
        # keep, format, index, data_size, raw_size, w, h
        size += len(self._sprites) * 28

        return size

    @property
    def images_data_size(self) -> int:
        size = super().images_data_size
        for sprite in self._sprites:
            size += len(sprite.zip_data)

        return size

    def _callback_before_images_save(self, io: typing.IO):
        # map_count, file_size
        write_struct(io, '<2i', len(self._sprites), self.file_size)

        super()._callback_before_images_save(io)

        for sprite in self._sprites:
            sprite.save(io)

    def _callback_after_images_save(self, io: typing.IO):
        for sprite in self._sprites:
            io.write(sprite.zip_data)

        super()._callback_after_images_save(io)

    def _build(self, image: Image, **kwargs) -> PILImage:
        if isinstance(image, SpriteZlibImage):
            l, t, r, b = image.left, image.top, image.right, image.bottom
            sprite = self._sprites[image.sprite_index]
            result = sprite.build((l, t, r, b), image.rotate)
        else:
            result = super()._build(image, **kwargs)

        return result

    def sprite_by_index(self, index: int) -> Sprite | None:
        if 0 <= index < len(self._sprites):
            return self._sprites[index]
