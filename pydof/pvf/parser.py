import dataclasses
import struct
import typing
from collections import defaultdict

from loguru import logger
from zhconv import convert

from .enums import FieldType
from .file_tree import StringTable

if typing.TYPE_CHECKING:
    from .reader import PvfReader


@dataclasses.dataclass
class FileContentField:
    """文件原始内容解析的字段"""
    tp: int
    value: typing.Any

    def __str__(self):
        if self.tp == FieldType.KEY:
            return self.value
        return f'\t{self.value}'

    __repr__ = __str__


@dataclasses.dataclass
class ReadableField:
    key: str
    values: list[FileContentField]
    self_closing: bool = False

    @property
    def value(self) -> list | int | str | float:
        if len(self.values) == 1:
            return self.values[0].value
        return [f.value for f in self.values]


class Parser:

    def __init__(self):
        self.fields: dict[str, list[ReadableField]] = defaultdict(list)

    @classmethod
    def parse(cls, c: bytes, pvf: 'PvfReader') -> 'Parser':
        fields = pvf.parse_file_content(c)
        parser = cls()
        parser._parse(fields)
        return parser

    def _parse(self, fields: list[FileContentField]):
        key: str = None
        values: list[FileContentField] = None
        for f in fields:
            if f.tp == 5:
                if f.value.startswith('[/'):
                    self.fields[key].append(ReadableField(
                        key=key,
                        values=values,
                        self_closing=True
                    ))
                else:
                    if key:
                        self.fields[key].append(ReadableField(
                            key=key,
                            values=values,
                        ))

                    values = []
                    key = f.value[1:-1]
            elif key:
                values.append(f)

        if key:
            self.fields[key].append(ReadableField(
                key=key,
                values=values,
            ))

    def get_field(self, key: str) -> list[ReadableField]:
        return self.fields[key]

    def get_field_value(self, key: str) -> list[int | str | float] | None:
        fields = self.get_field(key)
        if not fields:
            return None
        if len(fields) == 1:
            return fields[0].value
        return [f.value for f in fields]

    def get_simple_field_value(self, key: str):
        fields = self.get_field(key)
        if not fields:
            return None
        if len(fields) == 1:
            return fields[0].value
        return '\t'.join(str(f.value) for f in fields)


class LstParser:

    def __init__(self,
                 data: dict[int, str],
                 encode: str = 'big5'):
        # 代码: 路径
        self.data = data
        self.encode = encode

    @classmethod
    def parse(cls,
              content: bytes,
              string_table: StringTable,
              encode: str = 'big5') -> 'LstParser':
        data = {}
        i = 2
        while i + 10 < len(content):
            a, aa, b, bb = struct.unpack('<bIbI', content[i:i + 10])
            index = str_idx = 0
            if a == 2:
                index = aa
            elif a == 7:
                str_idx = aa
            if b == 2:
                index = bb
            elif b == 7:
                str_idx = bb

            string = string_table[str_idx]
            if index in data:
                logger.warning(
                    f'Duplicate index {index}, path {string} in LST file')
            data[index] = string
            i += 10

        return cls(data, encode)

    def __getitem__(self, item):
        return self.data[item]

    def items(self) -> typing.ItemsView[int, str]:
        return self.data.items()


class StrParser:

    def __init__(self, data: dict[str, str]):
        self.data = data

    @classmethod
    def parser(cls, content: bytes, encode: str = 'big5') -> 'StrParser':
        s = content.decode(encode, 'ignore')
        c = convert(s, 'zh-cn')
        data = {}
        for line in c.splitlines():
            if '>' not in line:
                continue
            k, v = line.split('>', 1)
            data[k] = v
        return cls(data)

    def __getitem__(self, item):
        ret = self.data.get(item)
        if ret is not None:
            return ret.replace('\r', '')
        return 'None'
