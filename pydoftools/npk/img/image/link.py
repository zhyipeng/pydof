import typing

from pydoftools.npk.consts import IMAGE_FORMAT_LINK
from pydoftools.utils.io import read_struct, write_struct

if typing.TYPE_CHECKING:
    from .image import Image


class ImageLink:
    def __init__(self, images: 'list[Image]', index: int):
        self._images = images
        self._index = index
        self._image: typing.Optional['Image'] = None

    def load_image(self):
        self._image = self._images[self.index]

    @classmethod
    def open(cls, io: typing.IO, images: 'list[Image]', **kwargs) -> 'ImageLink':
        index, = read_struct(io, '<i')
        link = cls(images, index)
        return link

    def save(self, io: typing.IO):
        # format, link_index
        write_struct(io, '<2i', IMAGE_FORMAT_LINK, self.index)

    def set_image(self, image: 'Image') -> bool:
        if image in self._images:
            self._image = image
            return True

        return False

    @property
    def index(self) -> int:
        if self._image is None:
            return self._index
        return self._images.index(self._image)

    @property
    def image(self) -> 'Image':
        return self._image

    @property
    def final_image(self) -> 'Image':
        final = self
        repeat = set()
        while isinstance(final, ImageLink):
            if final in repeat:
                raise Exception('Circular Link:', final._index)
            else:
                repeat.add(final)

            final = final.image

        return final
