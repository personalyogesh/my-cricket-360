"""Sponsor asset storage — local filesystem or Supabase Storage."""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException, UploadFile, status

from api.config import Settings, get_settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _signature_matches(data: bytes, content_type: str) -> bool:
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type == "image/webp":
        return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return False


async def read_validated_image(file: UploadFile, settings: Settings | None = None) -> tuple[bytes, str, str]:
    settings = settings or get_settings()
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {content_type}. Allowed: jpeg, png, webp.",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")
    if not _signature_matches(data, content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File contents do not match the declared image type",
        )
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds max size of {settings.max_upload_bytes} bytes",
        )
    ext = ALLOWED_CONTENT_TYPES[content_type]
    return data, content_type, ext


def build_storage_path(
    *,
    organization_id: uuid.UUID,
    sponsor_id: uuid.UUID,
    asset_id: uuid.UUID,
    ext: str,
) -> str:
    return f"{organization_id}/{sponsor_id}/{asset_id}{ext}"


class StorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def put_bytes(self, storage_path: str, data: bytes, content_type: str) -> str:
        backend = self.settings.effective_storage_backend
        if backend == "local":
            return self._put_local(storage_path, data)
        return await self._put_supabase(storage_path, data, content_type)

    def public_url(self, storage_path: str | None) -> str | None:
        if not storage_path:
            return None
        backend = self.settings.effective_storage_backend
        if backend == "local":
            return f"/v1/media/{storage_path}"
        base = self.settings.supabase_url.rstrip("/")
        bucket = self.settings.supabase_storage_bucket
        return f"{base}/storage/v1/object/public/{bucket}/{storage_path}"

    def resolve_local_path(self, storage_path: str) -> Path:
        root = Path(self.settings.local_storage_dir).resolve()
        full = (root / storage_path).resolve()
        if not str(full).startswith(str(root)):
            raise HTTPException(status_code=400, detail="Invalid storage path")
        return full

    def _put_local(self, storage_path: str, data: bytes) -> str:
        path = self.resolve_local_path(storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return storage_path

    async def _put_supabase(self, storage_path: str, data: bytes, content_type: str) -> str:
        if not self.settings.supabase_url or not self.settings.secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase Storage is not configured",
            )
        bucket = self.settings.supabase_storage_bucket
        url = (
            f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{storage_path}"
        )
        headers = {
            "Authorization": f"Bearer {self.settings.secret_key}",
            "apikey": self.settings.secret_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=data, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase Storage upload failed: {response.text}",
            )
        return storage_path
