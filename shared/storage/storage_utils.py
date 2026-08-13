from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class StorageClient:
    """A lightweight file-backed storage client for shared platform use."""

    def __init__(self, root_dir: str) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, content: bytes) -> Path:
        path = self.root_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def get(self, key: str) -> Optional[bytes]:
        path = self.root_dir / key
        if not path.exists():
            return None
        return path.read_bytes()

    def delete(self, key: str) -> bool:
        path = self.root_dir / key
        if not path.exists():
            return False
        path.unlink()
        return True
