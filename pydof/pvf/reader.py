from pathlib import Path
from typing import BinaryIO

from anyio import AsyncFile
from loguru import logger

from .file_tree import FileTreeNode, StringTable
from .header import PvfHeader
from .utils import decrypt_bytes


class PvfReader:

    def __init__(self, path: Path, encode: str = 'big5', lazy: bool = True):
        self.path = path
        self.header = PvfHeader(path)
        self.lazy = lazy
        self._fp: BinaryIO | AsyncFile | None = None
        self._fp_start = 0
        self._file_data = b''
        self.encode = encode

        self.files_map: dict[str, FileTreeNode] = {}
        self.string_table: StringTable = None

    def read(self):
        logger.info(f'Reading PVF {self.path}...')
        self._fp, self._fp_start = self.header.read()
        self.load_file_tree()
        self.load_string_table()
        if not self.lazy:
            self._fp.seek(self._fp_start)
            self._file_data = self._fp.read()

    def load_file_tree(self):
        logger.info('Loading file tree...')
        for f in self.header.load_file_tree():
            self.files_map[f.file_path] = f
        logger.info('File tree loaded. {} files found.', len(self.files_map))

    def load_string_table(self):
        logger.info('Loading string table...')
        b = self.read_file_content('stringtable.bin')
        self.string_table = StringTable(b, self.encode)
        logger.info('String table loaded. {} strings found.', len(self.string_table))

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


class AsyncPvfReader(PvfReader):

    async def read(self):
        logger.info(f'Async Reading PVF {self.path}...')
        self._fp, self._fp_start = await self.header.aread()
        self.load_file_tree()
        await self.load_string_table()
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
