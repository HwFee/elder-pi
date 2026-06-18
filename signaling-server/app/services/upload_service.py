import uuid
from pathlib import Path

from fastapi import UploadFile


ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024


async def save_avatar(file: UploadFile, upload_dir: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Only JPEG, PNG, WebP images are allowed")
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise ValueError("File too large")
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    path = Path(upload_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(contents)
    return filename
