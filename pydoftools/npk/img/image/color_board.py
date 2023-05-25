import typing

from pydoftools.utils.io import read_struct, write_struct


class ColorBoard:
    def __init__(self):
        self._colors: list[tuple[int]] = []

    def add_color(self, color: tuple[int]):
        self._colors.append(color)

    @classmethod
    def open(cls, io: typing.IO) -> 'ColorBoard':
        cb = cls()

        count, = read_struct(io, 'i')
        for _ in range(count):
            color = read_struct(io, '<4B')
            cb.add_color(color)

        return cb

    def save(self, io: typing.IO):
        # color_count
        write_struct(io, 'i', len(self._colors))
        for color in self._colors:
            # color
            write_struct(io, '<4B', *color)

    @property
    def colors(self) -> list[tuple[int]]:
        return self._colors
