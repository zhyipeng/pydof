import dataclasses
import struct
import typing
from collections import defaultdict

from loguru import logger

from .enums import FieldType
from .file_tree import StringTable


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


def parse_file_content(c: bytes,
                       string_table: StringTable,
                       string_quote: str = '') -> list[FileContentField]:
    shift = 2
    unit_num = (len(c) - 2) // 5
    struct_pattern = '<'
    unit_types = []
    for i in range(unit_num):
        unit_type = c[i * 5 + shift]
        unit_types.append(unit_type)
        if unit_type == 4:
            struct_pattern += 'Bf'
        else:
            struct_pattern += 'Bi'

    units = struct.unpack(struct_pattern, c[2:2 + 5 * unit_num])
    types = units[::2]
    values = units[1::2]
    fields = []
    for i in range(unit_num):
        match types[i]:
            case 2 | 3 | 4:
                fields.append(FileContentField(types[i], values[i]))
            case 5 | 6 | 8:
                fields.append(FileContentField(types[i], string_table[values[i]]))
            case 7:
                fields.append(FileContentField(
                    types[i],
                    string_quote + string_table[values[i]] + string_quote
                ))
            case 9:
                # TODO: handle 9
                fields.append(FileContentField(types[i], values[i]))

    return fields


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
    def parse(cls, c: bytes, string_table: 'StringTable') -> 'Parser':
        fields = parse_file_content(c, string_table)
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

    def get_field_value(self, key: str) -> list[int | str | float]:
        fields = self.get_field(key)
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
        self.cache = {}
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
