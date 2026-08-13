from __future__ import annotations

from pathlib import Path
from typing import Optional


class FileTransport:
    """A simple abstraction for storing uploaded files and serving them later."""

    def __init__(self, root_dir: str) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, filename: str, content: bytes) -> Path:
        path = self.root_dir / filename
        path.write_bytes(content)
        return path

    def download(self, filename: str) -> Optional[bytes]:
        path = self.root_dir / filename
        if not path.exists():
            return None
        return path.read_bytes()

    def remove(self, filename: str) -> bool:
        path = self.root_dir / filename
        if not path.exists():
            return False
        path.unlink()
        return True
