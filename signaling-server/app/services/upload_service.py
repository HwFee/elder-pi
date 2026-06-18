import uuid
from pathlib import Path

from fastapi import UploadFile


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024

# Magic byte signatures for common image formats
MAGIC_BYTES = {
    "image/jpeg": [(b"\xff\xd8\xff",)],
    "image/png": [(b"\x89PNG\r\n\x1a\n",)],
    "image/webp": [(b"RIFF", b"WEBP")],
}


def _content_type_by_magic(contents: bytes) -> str | None:
    for content_type, signatures in MAGIC_BYTES.items():
        for signature in signatures:
            if len(signature) == 1:
                if contents.startswith(signature[0]):
                    return content_type
            elif len(signature) == 2:
                if contents.startswith(signature[0]) and signature[1] in contents[:12]:
                    return content_type
    return None


async def save_avatar(file: UploadFile, upload_dir: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Only JPEG, PNG, WebP images are allowed")
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise ValueError("File too large")
    detected = _content_type_by_magic(contents)
    if detected != file.content_type:
        raise ValueError("File content does not match declared image type")
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    path = Path(upload_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(contents)
    return filename
