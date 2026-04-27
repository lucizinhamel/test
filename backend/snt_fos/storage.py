"""Content-addressable document storage. SHA-256 over the raw bytes; files
land at  <DATA_DIR>/documents/<sha[0:2]>/<sha[2:4]>/<sha>  so the directory
fan-out scales and de-duplication is automatic."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO

from .db import DOCUMENTS_DIR


def _path_for(sha256_hex: str) -> Path:
    return DOCUMENTS_DIR / sha256_hex[0:2] / sha256_hex[2:4] / sha256_hex


def store_stream(src: BinaryIO) -> tuple[str, int, Path]:
    """Stream `src` to a temp file while hashing, then move to final path.

    Returns (sha256_hex, byte_size, final_path). If the file already exists at
    the final path, the temp file is discarded — bytes are byte-identical by
    definition.
    """
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DOCUMENTS_DIR / ".tmp"
    tmp.mkdir(exist_ok=True)
    tmp_file = tmp / f"upload-{id(src)}.part"

    h = hashlib.sha256()
    size = 0
    with open(tmp_file, "wb") as out:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            out.write(chunk)
            size += len(chunk)

    sha = h.hexdigest()
    final = _path_for(sha)
    final.parent.mkdir(parents=True, exist_ok=True)

    if final.exists():
        tmp_file.unlink(missing_ok=True)
    else:
        shutil.move(str(tmp_file), str(final))

    return sha, size, final


def open_for_read(sha256_hex: str) -> Path:
    return _path_for(sha256_hex)
