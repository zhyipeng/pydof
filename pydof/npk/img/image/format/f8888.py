from pydof.npk.consts import IMAGE_FORMAT_8888, PIX_SIZE
from pydof.utils.io import read_struct, write_struct
from .format import Format


class Format8888(Format):
    ps = PIX_SIZE[IMAGE_FORMAT_8888]

    def callback_to_raw(self, io, io_raw):
        temp = read_struct(io, '<4B', False)
        while temp is not None:
            b, g, r, a = temp
            write_struct(io_raw, '<4B', r, g, b, a)

            temp = read_struct(io, '<4B', False)

    def callback_to_raw_crop_convert(self, io, io_raw):
        temp = read_struct(io, '<4B', False)
        if temp is not None:
            b, g, r, a = temp
            write_struct(io_raw, '<4B', r, g, b, a)

    def callback_from_image_convert(self, io, pixel):
        r, g, b, a = pixel
        write_struct(io, "<4B", b, g, r, a)
