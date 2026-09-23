"""Private storage abstraction for generated business documents."""

import re
from pathlib import Path
from typing import Protocol


DOCUMENT_ROOT = Path(__file__).with_name("data") / "documents"
STORAGE_KEY_PATTERN = re.compile(r"[a-f0-9]{32}\.pdf")


class DocumentStorage(Protocol):
    def save(self, storage_key: str, content: bytes) -> None: ...
    def read(self, storage_key: str) -> bytes: ...


class PrivateFileSystemDocumentStorage:
    """Stores opaque document keys outside static and public file roots."""

    def __init__(self, root: Path = DOCUMENT_ROOT):
        self.root = root

    def _path(self, storage_key: str) -> Path:
        if not isinstance(storage_key, str) or STORAGE_KEY_PATTERN.fullmatch(storage_key) is None:
            raise ValueError("Document storage key is invalid.")
        root = self.root.resolve()
        path = (root / storage_key).resolve()
        if path.parent != root:
            raise ValueError("Document storage key is invalid.")
        return path

    def save(self, storage_key: str, content: bytes) -> None:
        if not isinstance(content, bytes) or not content:
            raise ValueError("Document content is invalid.")
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as document_file:
            document_file.write(content)

    def read(self, storage_key: str) -> bytes:
        return self._path(storage_key).read_bytes()
