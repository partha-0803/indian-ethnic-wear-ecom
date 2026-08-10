"""Cloud file storage backends for production (Vercel filesystem is read-only)."""

from __future__ import annotations

import mimetypes
import os

import requests
import vercel_blob
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


def using_vercel_blob() -> bool:
    return bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))


@deconstructible
class VercelBlobStorage(Storage):
    """
    Django storage that uploads media to Vercel Blob.

    Requires BLOB_READ_WRITE_TOKEN (auto-added when you create a Blob store
    and link it to the Vercel project).

    FileField values are stored as absolute public blob URLs so .url works
    without a separate CDN domain mapping.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timeout = int(getattr(settings, "VERCEL_BLOB_TIMEOUT", 60))

    def _normalize_name(self, name: str) -> str:
        return (name or "").lstrip("/")

    def get_available_name(self, name, max_length=None):
        # Blob URLs are unique (random suffix); keep the logical upload path.
        return self._normalize_name(name)

    def _save(self, name, content):
        name = self._normalize_name(name)
        if hasattr(content, "open"):
            content.open()
        if hasattr(content, "seek"):
            content.seek(0)
        data = content.read()
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)

        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        # vercel_blob guesses type from path; ensure extension is present
        if "." not in name.split("/")[-1] and content_type.startswith("image/"):
            ext = mimetypes.guess_extension(content_type) or ".bin"
            name = f"{name}{ext}"

        options = {
            "addRandomSuffix": "true",
            "allowOverwrite": "true",
            "cacheControlMaxAge": "31536000",
        }
        use_multipart = len(data) >= 4 * 1024 * 1024
        result = vercel_blob.put(
            name,
            bytes(data),
            options,
            timeout=self.timeout,
            multipart=use_multipart,
        )
        url = result.get("url")
        if not url:
            raise IOError(f"Vercel Blob upload failed for {name}: {result}")
        return url

    def _open(self, name, mode="rb"):
        url = self.url(name)
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return ContentFile(response.content, name=name)

    def delete(self, name):
        if not name:
            return
        url = self.url(name)
        if not url.startswith("http"):
            return
        try:
            vercel_blob.delete(url, timeout=self.timeout)
        except Exception:
            # Deleting a missing blob should not break admin saves.
            pass

    def exists(self, name):
        if not name:
            return False
        url = self.url(name)
        if not url.startswith("http"):
            return False
        try:
            vercel_blob.head(url, timeout=self.timeout)
            return True
        except Exception:
            return False

    def size(self, name):
        url = self.url(name)
        if not url.startswith("http"):
            return 0
        try:
            meta = vercel_blob.head(url, timeout=self.timeout)
            return int(meta.get("size") or 0)
        except Exception:
            return 0

    def url(self, name):
        if not name:
            return ""
        if name.startswith("http://") or name.startswith("https://"):
            return name
        # Legacy local paths (products/..., brand/...) — best-effort local URL.
        base = settings.MEDIA_URL or "/media/"
        if not base.endswith("/"):
            base += "/"
        return f"{base}{name.lstrip('/')}"

    def listdir(self, path):
        return [], []

    def path(self, name):
        raise NotImplementedError("Vercel Blob storage has no local filesystem path.")

    def get_accessed_time(self, name):
        raise NotImplementedError

    def get_created_time(self, name):
        raise NotImplementedError

    def get_modified_time(self, name):
        raise NotImplementedError
