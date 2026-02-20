"""Optional OCI Object Storage integration hooks."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger("prereq.object_storage")


def _is_enabled() -> bool:
    return (
        settings.OCI_OBJECT_STORAGE_ENABLED
        and bool(settings.OCI_BUCKET_UPLOADS or settings.OCI_BUCKET_EXPORTS)
    )


def _put_object_blocking(bucket_name: str, object_name: str, payload: bytes, content_type: str) -> bool:
    try:
        import oci  # type: ignore
    except Exception:
        logger.warning("OCI SDK unavailable; skipping upload for %s", object_name)
        return False

    config = oci.config.from_file(
        file_location=settings.OCI_CONFIG_FILE,
        profile_name=settings.OCI_CONFIG_PROFILE,
    )
    client = oci.object_storage.ObjectStorageClient(config)
    namespace = settings.OCI_OBJECT_STORAGE_NAMESPACE or client.get_namespace().data
    client.put_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=object_name,
        put_object_body=payload,
        content_type=content_type,
    )
    return True


async def upload_raw_upload_artifact(
    exam_id: str,
    artifact_kind: str,
    payload: bytes,
    content_type: str = "text/csv",
) -> bool:
    """Best-effort upload hook for raw uploaded files."""
    if not _is_enabled() or not settings.OCI_BUCKET_UPLOADS:
        return False
    object_name = f"uploads/{exam_id}/{artifact_kind}"
    try:
        return await asyncio.to_thread(
            _put_object_blocking,
            settings.OCI_BUCKET_UPLOADS,
            object_name,
            payload,
            content_type,
        )
    except Exception:
        logger.exception("Failed object storage upload: %s", object_name)
        return False


async def upload_export_bundle_artifact(exam_id: str, file_path: str) -> bool:
    """Best-effort upload hook for generated export bundles."""
    if not _is_enabled() or not settings.OCI_BUCKET_EXPORTS:
        return False
    filename = Path(file_path).name
    object_name = f"exports/{exam_id}/{filename}"
    try:
        payload = Path(file_path).read_bytes()
        return await asyncio.to_thread(
            _put_object_blocking,
            settings.OCI_BUCKET_EXPORTS,
            object_name,
            payload,
            "application/zip",
        )
    except Exception:
        logger.exception("Failed object storage export upload: %s", object_name)
        return False
