import atexit
import struct
import typing
from pathlib import Path
from typing import BinaryIO

from anyio import AsyncFile, Path as AsyncPath

from .file_tree import FileTreeNode
from .utils import decrypt_bytes


class PvfHeader:

    def __init__(self, path: Path):
        self.path = path
        self.loaded = False

        self.uuid_len = 0
        self.uuid = b''
        self.version = 0
        self.dir_tree_len = 0
        self.dir_tree_crc32 = 0
        self.file_count = 0
        self.file_pack_idx = 0
        self.header_len = 0
        self._header_bytes = b''
        self._header_decrypted = b''
        self._file_pack_bytes = b''

    def read(self) -> tuple[BinaryIO, int]:
        f = self.path.open('rb')
        atexit.register(f.close)
        self.uuid_len = struct.unpack('i', f.read(4))[0]
        self.uuid = f.read(self.uuid_len)
        self.version = struct.unpack('i', f.read(4))[0]
        self.dir_tree_len = struct.unpack('i', f.read(4))[0]
        self.dir_tree_crc32 = struct.unpack('I', f.read(4))[0]
        self.file_count = struct.unpack('i', f.read(4))[0]
        self.file_pack_idx = f.tell() + self.dir_tree_len
        self.header_len = f.tell()

        self._header_bytes = f.read(self.dir_tree_len)
        self._header_decrypted = decrypt_bytes(self._header_bytes, self.dir_tree_crc32)
        self.loaded = True
        return f, f.tell()

    async def aread(self) -> tuple[AsyncFile, int]:
        p = AsyncPath(str(self.path))
        f = await p.open('rb')
        self.uuid_len = struct.unpack('i', await f.read(4))[0]
        self.uuid = await f.read(self.uuid_len)
        self.version = struct.unpack('i', await f.read(4))[0]
        self.dir_tree_len = struct.unpack('i', await f.read(4))[0]
        self.dir_tree_crc32 = struct.unpack('I', await f.read(4))[0]
        self.file_count = struct.unpack('i', await f.read(4))[0]
        self.file_pack_idx = await f.tell() + self.dir_tree_len
        self.header_len = await f.tell()

        self._header_bytes = await f.read(self.dir_tree_len)
        self._header_decrypted = decrypt_bytes(self._header_bytes, self.dir_tree_crc32)

        self.loaded = True
        return f, await f.tell()

    def load_file_tree(self) -> typing.Generator[FileTreeNode, None, None]:
        idx = 0
        for _ in range(self.file_count):
            file_index = idx
            fn_bytes, idx = self._get_header_tree_bytes(idx)
            file_path_length_bytes, idx = self._get_header_tree_bytes(idx)
            file_path_length = struct.unpack('I', file_path_length_bytes)[0]
            file_path_bytes, idx = self._get_header_tree_bytes(idx, file_path_length)
            file_length_bytes, idx = self._get_header_tree_bytes(idx)
            file_crc32_bytes, idx = self._get_header_tree_bytes(idx)
            relative_offset_bytes, idx = self._get_header_tree_bytes(idx)

            yield FileTreeNode(
                index=file_index,
                fn=struct.unpack('I', fn_bytes)[0],
                file_path_len=file_path_length,
                file_path=file_path_bytes.decode('CP949').lower().removeprefix('/'),
                file_length=(struct.unpack('I', file_length_bytes)[0] + 3) & 0xFFFFFFFC,
                file_crc32=struct.unpack('I', file_crc32_bytes)[0],
                relative_offset=struct.unpack('I', relative_offset_bytes)[0],
            )

    def _get_header_tree_bytes(self, start: int, length: int = 4) -> tuple[bytes, int]:
        return self._header_decrypted[start:start + length], start + length
