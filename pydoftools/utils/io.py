import struct
import typing

from .zlib import zfill_bytes


def read_struct(io: typing.IO, fmt: str, zfill=True) -> tuple | None:
    struct_size = struct.calcsize(fmt)
    data = io.read(struct_size)
    if zfill:
        data = zfill_bytes(data, struct_size)
    elif len(data) == 0:
        return None

    result = struct.unpack(fmt, data)
    return result


def read_ascii_string(io: typing.IO, max_size=-1, ignore_zero=False) -> str:
    result = ''
    zero_break = not ignore_zero and max_size != -1
    while max_size == -1 or len(result) < max_size:
        ret = read_struct(io, 'B')
        if not ret:
            break
        char = ret[0]
        if char == 0 and zero_break:
            break

        result += chr(char)
    return result


def read_range(io: typing.IO, offset=0, size=-1):
    io.seek(offset)
    return io.read(size)


def write_struct(io: typing.IO, fmt, *values):
    data = struct.pack(fmt, *values)
    return io.write(data)


def write_ascii_string(io: typing.IO, content: str):
    data = content.encode('ascii') + b'\x00'
    return io.write(data)
