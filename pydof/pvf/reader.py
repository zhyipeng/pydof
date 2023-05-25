import struct
import typing
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from anyio import AsyncFile
from loguru import logger

from .file_tree import FileTreeNode, StringTable
from .header import PvfHeader
from .utils import decrypt_bytes
from .parser import FileContentField, LstParser, StrParser


def fake_tqdm(g: typing.Iterable, **kwargs):
    return g


class PvfReader:

    def __init__(self,
                 path: Path,
                 encode: str = 'big5',
                 lazy: bool = True,
                 use_tqdm=False):
        self.path = path
        self.header = PvfHeader(path)
        self.lazy = lazy
        self._fp: BinaryIO | AsyncFile | None = None
        self._fp_start = 0
        self._file_data = b''
        self.encode = encode

        self.files_map: dict[str, FileTreeNode] = {}
        self.string_table: StringTable = None
        self.n_string: LstParser = None
        self.tqdm = fake_tqdm
        if use_tqdm:
            try:
                from tqdm import tqdm
                self.tqdm = tqdm
            except ImportError:
                logger.warning('tqdm not found, use_tqdm will be ignored.')

    def read(self):
        logger.info(f'Reading PVF {self.path}...')
        self._fp, self._fp_start = self.header.read()
        self.load_file_tree()
        self.load_string_table()
        self.load_n_string()
        if not self.lazy:
            self._fp.seek(self._fp_start)
            self._file_data = self._fp.read()

    def load_file_tree(self):
        logger.info('Loading file tree...')
        for f in self.tqdm(self.header.load_file_tree(), total=self.header.file_count):
            self.files_map[f.file_path] = f
        logger.info('File tree loaded. {} files found.', len(self.files_map))

    def load_string_table(self):
        logger.info('Loading string table...')
        b = self.read_file_content('stringtable.bin')
        self.string_table = StringTable(b, self.encode)
        logger.info('String table loaded. {} strings found.', len(self.string_table))

    def load_n_string(self):
        logger.info('Loading n string ...')
        c = self.read_file_content('n_string.lst')
        self.n_string = LstParser.parse(c, self.string_table, self.encode)
        logger.info('NString loaded.')

    @lru_cache(maxsize=50)
    def read_file_content(self, path: str) -> bytes:
        path = path.lower().replace('\\', '/')
        path.removeprefix('/')
        file = self.files_map.get(path)
        if file is None:
            raise FileNotFoundError(f'File {path} not found in PVF {self.path}')

        content = self._read_bytes(file.relative_offset, file.file_length)
        return decrypt_bytes(content, file.file_crc32)

    def _read_bytes(self, start: int, length: int) -> bytes:
        if self._fp is None:
            raise RuntimeError('File not opened.')
        self._fp.seek(self._fp_start + start)
        return self._fp.read(length)

    def parse_file_content(self,
                           c: bytes,
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
                    fields.append(FileContentField(types[i], self.string_table[values[i]]))
                case 7:
                    fields.append(FileContentField(
                        types[i],
                        string_quote + self.string_table[values[i]] + string_quote
                    ))
                case 9:
                    p = self.n_string[values[i]].lower()
                    str_c = self.read_file_content(p)
                    parser = StrParser.parser(str_c, self.encode)
                    v = parser[self.string_table[values[i+1]]]
                    fields.append(FileContentField(types[i], v))

        return fields


class AsyncPvfReader(PvfReader):

    async def read(self):
        logger.info(f'Async Reading PVF {self.path}...')
        self._fp, self._fp_start = await self.header.aread()
        self.load_file_tree()
        await self.load_string_table()
        await self.load_n_string()
        if not self.lazy:
            await self._fp.seek(self._fp_start)
            self._file_data = await self._fp.read()

    async def close(self):
        await self._fp.aclose()

    async def __aenter__(self):
        await self.read()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _read_bytes(self, start: int, length: int) -> bytes:
        if self._fp is None:
            raise RuntimeError('File not opened.')
        await self._fp.seek(self._fp_start + start)
        return await self._fp.read(length)

    async def read_file_content(self, path: str) -> bytes:
        path = path.lower().replace('\\', '/')
        path.removeprefix('/')
        file = self.files_map.get(path)
        if file is None:
            raise FileNotFoundError(f'File {path} not found in PVF {self.path}')

        content = await self._read_bytes(file.relative_offset, file.file_length)
        return decrypt_bytes(content, file.file_crc32)

    async def load_string_table(self):
        logger.info('Loading string table...')
        b = await self.read_file_content('stringtable.bin')
        self.string_table = StringTable(b, self.encode)
        logger.info('String table loaded. {} strings found.', len(self.string_table))

    async def load_n_string(self):
        logger.info('Loading n string ...')
        c = await self.read_file_content('n_string.lst')
        self.n_string = LstParser.parse(c, self.string_table, self.encode)
        logger.info('NString loaded.')
