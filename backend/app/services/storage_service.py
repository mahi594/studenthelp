"""
File storage service - S3-compatible, works with either AWS S3 or
Cloudflare R2 (same boto3 client either way; R2 just needs S3_ENDPOINT_URL
set to your account's R2 endpoint). See .env.example for setup notes.

Before this existed, resumes were parsed in-memory and never actually saved
- `Resume.file_url` was a placeholder string. This makes it real: the PDF
bytes are uploaded to the bucket and a retrievable URL is stored.

DEV FALLBACK: if S3_ACCESS_KEY_ID/S3_SECRET_ACCESS_KEY aren't set, uploads
go to local disk (settings.LOCAL_STORAGE_DIR) instead of raising, and are
served back via the /media static mount in main.py. This is only meant to
unblock local development before R2/S3 is configured - swap to real bucket
credentials before shipping, since local files don't survive a rebuild
unless that directory is a mounted volume.
"""
import os
import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def _s3_configured() -> bool:
    return bool(settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY)


def _get_s3_client():
    kwargs = {
        "aws_access_key_id": settings.S3_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.S3_SECRET_ACCESS_KEY,
        "region_name": settings.S3_REGION,
    }
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

    return boto3.client("s3", **kwargs)


def _build_key(original_filename: str, user_id) -> str:
    """Builds a safe, generated storage key. Deliberately ignores almost all
    of `original_filename` beyond the extension - a filename is untrusted
    user input, so the only thing pulled from it is a short, sanitized
    display fragment, and the extension is checked against an allow-list
    rather than trusted outright. This closes the path-traversal hole
    that existed when the original filename (e.g. "../../etc/cron.d/x" or
    an embedded null byte) was concatenated directly into the storage key.
    """
    base = os.path.basename(original_filename or "resume")  # strips any directory components
    _, ext = os.path.splitext(base)
    ext = ext.lower()
    if ext != ".pdf":
        ext = ".pdf"  # upload_resume() already enforces PDF-only before this is called

    safe_stem = "".join(c for c in os.path.splitext(base)[0] if c.isalnum() or c in ("-", "_"))[:40]
    if not safe_stem:
        safe_stem = "resume"

    key = f"resumes/{user_id}/{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:12]}-{safe_stem}{ext}"
    return key


def _upload_resume_local(file_bytes: bytes, original_filename: str, user_id) -> dict:
    key = _build_key(original_filename, user_id)
    base_dir = os.path.abspath(settings.LOCAL_STORAGE_DIR)
    dest_path = os.path.abspath(os.path.join(base_dir, key))

    # Defense in depth: even though _build_key() no longer allows directory
    # components through, refuse to write anywhere outside the configured
    # upload directory.
    if os.path.commonpath([dest_path, base_dir]) != base_dir:
        raise RuntimeError("Refusing to write outside the configured upload directory.")

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    url = f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}/media/{key}"
    return {"url": url, "key": key}


def validate_pdf_content(file_bytes: bytes, max_bytes: int = None):
    if not file_bytes or not file_bytes.startswith(b"%PDF"):
        raise ValueError("Invalid PDF file format. File signature magic bytes check failed.")
    limit = max_bytes if max_bytes is not None else settings.MAX_RESUME_UPLOAD_BYTES
    if len(file_bytes) > limit:
        raise ValueError(f"Resume file is too large. Maximum size is {limit // (1024 * 1024)}MB.")


def upload_resume(file_bytes: bytes, original_filename: str, user_id, content_type: str = "application/pdf") -> dict:
    validate_pdf_content(file_bytes)
    if not _s3_configured():
        return _upload_resume_local(file_bytes, original_filename, user_id)

    client = _get_s3_client()
    key = _build_key(original_filename, user_id)

    try:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
    except ClientError as exc:
        raise RuntimeError(f"Failed to upload resume to storage: {exc}") from exc

    if settings.S3_PUBLIC_URL_BASE:
        url = f"{settings.S3_PUBLIC_URL_BASE.rstrip('/')}/{key}"
    else:
        url = get_presigned_resume_url(key)

    return {"url": url, "key": key}


def get_presigned_resume_url(key: str, expires_in_seconds: int = 60 * 60 * 24 * 7) -> str:
    """Generates a fresh presigned URL for a private-bucket object. Store the
    `key` (not the URL) long-term if using presigned URLs, since the URL
    itself expires - call this again whenever you need a working link.

    Not applicable to locally-stored files (no S3 client involved for
    those) - their /media URL is already permanent as long as the file's
    still on disk."""
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in_seconds,
    )