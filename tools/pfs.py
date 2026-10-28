"""Read PF8 and rebuild its payload while preserving the original directory index."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct


@dataclass
class Entry:
    name: str
    offset: int
    size: int
    position: int


def crypt(data, key):
    return bytes(value ^ key[i % 20] for i, value in enumerate(data))


class Archive:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open('rb') as stream:
            header = stream.read(7)
            if header[:3] != b'pf8':
                raise ValueError('Expected a PF8 archive')
            self.index = stream.read(struct.unpack_from('<I', header, 3)[0])
        self.key = hashlib.sha1(self.index).digest()
        self.entries = []
        position = 4
        for _ in range(struct.unpack_from('<I', self.index)[0]):
            length = struct.unpack_from('<I', self.index, position)[0]
            position += 4
            name = self.index[position:position + length].decode('utf-8')
            position += length
            _, offset, size = struct.unpack_from('<III', self.index, position)
            self.entries.append(Entry(name, offset, size, position + 4))
            position += 12
        if any(e.offset < 7 + len(self.index) or
               e.offset + e.size > self.path.stat().st_size for e in self.entries):
            raise ValueError('Invalid PF8 directory offsets')

    def read(self, entry):
        if isinstance(entry, str):
            entry = next(e for e in self.entries if e.name == entry)
        with self.path.open('rb') as stream:
            stream.seek(entry.offset)
            return crypt(stream.read(entry.size), self.key)

    def rebuild(self, destination, replacements):
        unknown = replacements.keys() - {e.name for e in self.entries}
        if unknown:
            raise ValueError(f'Cannot introduce entries without rebuilding lookup table: {unknown}')
        index = bytearray(self.index)
        offset = 7 + len(index)
        payloads = []
        for entry in sorted(self.entries, key=lambda e: e.offset):
            payload = replacements.get(entry.name)
            if payload is None:
                payload = self.read(entry)
            struct.pack_into('<II', index, entry.position, offset, len(payload))
            payloads.append(payload)
            offset += len(payload)
        key = hashlib.sha1(index).digest()
        with Path(destination).open('wb') as stream:
            stream.write(b'pf8' + struct.pack('<I', len(index)) + index)
            for payload in payloads:
                stream.write(crypt(payload, key))
