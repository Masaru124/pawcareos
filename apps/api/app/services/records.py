"""Storage for records a pet parent photographed themselves.

Dev keeps them on local disk under `record_storage_dir`; the database only ever
holds the key, so swapping in object storage means changing this module alone.
"""

import hashlib
import uuid
from pathlib import Path

from app.config import Settings

# Phone photos of a vaccine card are the common case; a 5 MB ceiling still allows
# a scanned multi-page PDF without letting one upload exhaust the disk.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

CONTENT_TYPES: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def storage_root(settings: Settings) -> Path:
    return Path(settings.record_storage_dir).resolve()


def write_legacy_file(settings: Settings, content: bytes, content_type: str) -> tuple[str, str]:
    """Store the bytes and return (storage_key, sha256)."""
    key = f"{uuid.uuid4().hex}{CONTENT_TYPES[content_type]}"
    root = storage_root(settings)
    root.mkdir(parents=True, exist_ok=True)
    (root / key).write_bytes(content)
    return key, hashlib.sha256(content).hexdigest()


def legacy_file_path(settings: Settings, storage_key: str) -> Path:
    """Resolve a key without letting a crafted key escape the storage directory."""
    root = storage_root(settings)
    path = (root / Path(storage_key).name).resolve()
    if path.parent != root:
        raise ValueError("Record path escapes storage root")
    return path
