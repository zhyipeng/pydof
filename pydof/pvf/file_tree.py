import dataclasses
import struct

from zhconv import convert


@dataclasses.dataclass
class FileTreeNode:
    index: int
    fn: int
    file_path_len: int
    file_path: str
    file_length: int
    file_crc32: int
    relative_offset: int
    # content: bytes = None


class StringTable:

    def __init__(self, content: bytes, encode: str = 'big5'):
        self.length = struct.unpack('I', content[:4])[0]
        self.content = content[4:]
        self.chunk = bytearray(content[4 + self.length * 4 + 4:])
        self.add_count = 0
        self.cached: dict[int, str] = {}
        self.encode = encode

    def __len__(self):
        return self.length * 2

    def __getitem__(self, item: int) -> str:
        if item not in self.cached:
            self.cached[item] = self._convert(self.content[item * 4: item * 4 + 8])

        return self.cached[item]

    def _convert(self, c: bytes):
        str_idx = struct.unpack('<II', c)
        bias = self.length * 4 + 4
        return convert(
            self.chunk[str_idx[0] - bias:str_idx[1] - bias].decode(self.encode,
                                                                   'ignore'),
            'zh-cn'
        )
