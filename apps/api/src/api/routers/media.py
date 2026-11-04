from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.storage import StorageService

router = APIRouter(tags=["media"])


@router.get("/v1/media/{storage_path:path}")
def get_local_media(storage_path: str) -> FileResponse:
    storage = StorageService()
    if storage.settings.effective_storage_backend != "local":
        raise HTTPException(status_code=404, detail="Local media is disabled")
    path = storage.resolve_local_path(storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type = "application/octet-stream"
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        media_type = "image/jpeg"
    elif suffix == ".png":
        media_type = "image/png"
    elif suffix == ".webp":
        media_type = "image/webp"
    return FileResponse(path, media_type=media_type)
