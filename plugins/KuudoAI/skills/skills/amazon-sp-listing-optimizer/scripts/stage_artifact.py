#!/usr/bin/env python3
"""Stage an approved image to a user-owned bucket and return a public URL.

This is the one external dependency of the AI image-improvement workflow.
Generators (Gemini, OpenAI) hand back image *bytes*; Amazon's image locators
(`main_product_image_locator`, `other_product_image_locator_1..8`) take a
`media_location` *URL* that Amazon fetches asynchronously and copies into its
own CDN. So an approved candidate has to live at a publicly reachable URL for
the few minutes Amazon needs to ingest it — and that bucket is the user's, not
ours. This skill hosts nothing; it only writes through to the store the user
configured.

The store is pluggable and chosen by env (or --store): s3 | gcs | cloudinary |
gdrive. Credentials come entirely from the environment — nothing is hardcoded,
and the SDK for the chosen store is imported lazily so users only install what
they use. See `references/07-ai-image-generation.md` for the per-store setup and
the exact variables.

    S3:         ARTIFACT_S3_BUCKET, ARTIFACT_S3_PREFIX (opt),
                AWS creds via the standard boto3 chain, AWS_REGION
    GCS:        ARTIFACT_GCS_BUCKET, ARTIFACT_GCS_PREFIX (opt),
                GOOGLE_APPLICATION_CREDENTIALS
    Cloudinary: CLOUDINARY_URL (or CLOUDINARY_CLOUD_NAME / _API_KEY / _API_SECRET)
    GDrive:     GOOGLE_APPLICATION_CREDENTIALS (service account w/ Drive scope),
                ARTIFACT_GDRIVE_FOLDER_ID (opt). Uploads, sets the file public
                ("anyone with link"), and returns a DIRECT-content URL — Amazon
                fetches unauthenticated, so the file must be public and the URL
                must serve bytes, not Drive's HTML viewer page. In Claude.ai /
                Cowork an activated Google Drive connector can do this in-session
                instead of a service account — see the reference doc.

ARTIFACT_URL_TTL (seconds, default 86400) sets the presigned-URL lifetime for
S3/GCS. It MUST comfortably outlast Amazon's ingestion fetch, which can lag —
err long. Cloudinary URLs are public and effectively permanent.

Running this publishes the file. Run it only after the user has approved the
image and given an explicit yes that names this store and bucket or folder
(`references/07-ai-image-generation.md`, End-to-end workflow, step 6).

Usage:
    python stage_artifact.py candidate.png
    python stage_artifact.py candidate.png --store s3 --ttl 86400 --json

Exit codes:
    0 — staged; URL printed (or in JSON)
    2 — missing config / SDK / credentials (message points at the setup doc)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_TTL = 86400
SETUP_HINT = "see references/07-ai-image-generation.md for setup"


def _fail(message: str) -> "NoReturn":  # type: ignore[name-defined]
    """Exit 2 for missing config / SDK / credentials."""
    print(f"[stage-error] {message} ({SETUP_HINT})", file=sys.stderr)
    sys.exit(2)


def _key(local_path: Path, prefix: str) -> str:
    prefix = prefix.strip("/")
    return f"{prefix}/{local_path.name}" if prefix else local_path.name


def _expiry_iso(ttl: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()


def stage_s3(local_path: Path, ttl: int) -> dict:
    try:
        import boto3
    except ImportError:
        _fail("boto3 not installed: pip install boto3")
    bucket = os.environ.get("ARTIFACT_S3_BUCKET")
    if not bucket:
        _fail("ARTIFACT_S3_BUCKET is not set")
    key = _key(local_path, os.environ.get("ARTIFACT_S3_PREFIX", "listing-images"))
    client = boto3.client("s3", region_name=os.environ.get("AWS_REGION"))
    client.upload_file(str(local_path), bucket, key)
    url = client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl
    )
    return {"store": "s3", "bucket": bucket, "key": key, "url": url,
            "expires_at": _expiry_iso(ttl), "public": False}


def stage_gcs(local_path: Path, ttl: int) -> dict:
    try:
        from google.cloud import storage
    except ImportError:
        _fail("google-cloud-storage not installed: pip install google-cloud-storage")
    bucket_name = os.environ.get("ARTIFACT_GCS_BUCKET")
    if not bucket_name:
        _fail("ARTIFACT_GCS_BUCKET is not set")
    key = _key(local_path, os.environ.get("ARTIFACT_GCS_PREFIX", "listing-images"))
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(key)
    blob.upload_from_filename(str(local_path))
    url = blob.generate_signed_url(
        version="v4", expiration=timedelta(seconds=ttl), method="GET"
    )
    return {"store": "gcs", "bucket": bucket_name, "key": key, "url": url,
            "expires_at": _expiry_iso(ttl), "public": False}


def stage_cloudinary(local_path: Path, ttl: int) -> dict:
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        _fail("cloudinary not installed: pip install cloudinary")
    # cloudinary.config() reads CLOUDINARY_URL automatically; the split vars
    # are honored too if CLOUDINARY_URL is absent.
    if not os.environ.get("CLOUDINARY_URL") and not os.environ.get("CLOUDINARY_CLOUD_NAME"):
        _fail("CLOUDINARY_URL (or CLOUDINARY_CLOUD_NAME/_API_KEY/_API_SECRET) is not set")
    cloudinary.config()
    folder = os.environ.get("ARTIFACT_CLOUDINARY_FOLDER", "listing-images")
    result = cloudinary.uploader.upload(str(local_path), folder=folder, resource_type="image")
    return {"store": "cloudinary", "key": result.get("public_id"),
            "url": result.get("secure_url"), "expires_at": None, "public": True}


def stage_gdrive(local_path: Path, ttl: int) -> dict:
    """Upload via a service account, make the file public, return a direct URL.

    For Claude Code / headless use. In Claude.ai / Cowork, prefer the in-session
    Google Drive connector instead of this code path: the connector's create_file
    drops the image into a pre-shared public folder (it has no permission-setting
    tool, so it relies on folder inheritance) — see references/07-ai-image-generation.md.

    Either way, Amazon's fetcher is unauthenticated, so the file must be public
    and the URL must serve bytes, not Drive's HTML viewer page.
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2 import service_account
    except ImportError:
        _fail("google-api-python-client not installed: "
              "pip install google-api-python-client google-auth")
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        _fail("GOOGLE_APPLICATION_CREDENTIALS is not set (service account with Drive scope)")
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)
    meta = {"name": local_path.name}
    folder = os.environ.get("ARTIFACT_GDRIVE_FOLDER_ID")
    if folder:
        meta["parents"] = [folder]
    media = MediaFileUpload(str(local_path), resumable=False)
    created = service.files().create(body=meta, media_body=media, fields="id").execute()
    file_id = created["id"]
    # Amazon fetches unauthenticated → the object must be world-readable.
    service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()
    # Direct-content URL — NOT the /file/d/<id>/view share link, which serves HTML.
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    return {"store": "gdrive", "key": file_id, "url": url,
            "expires_at": None, "public": True}


STAGERS = {"s3": stage_s3, "gcs": stage_gcs, "cloudinary": stage_cloudinary, "gdrive": stage_gdrive}


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage an approved image to a user bucket; print its public URL.")
    parser.add_argument("file", type=Path, help="Local image file to upload.")
    parser.add_argument("--store", choices=sorted(STAGERS), default=os.environ.get("ARTIFACT_STORE"),
                        help="Object store. Defaults to $ARTIFACT_STORE.")
    parser.add_argument("--ttl", type=int, default=int(os.environ.get("ARTIFACT_URL_TTL", DEFAULT_TTL)),
                        help=f"Presigned-URL lifetime in seconds (default {DEFAULT_TTL}; S3/GCS only).")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON.")
    args = parser.parse_args()

    if not args.file.is_file():
        _fail(f"file not found: {args.file}")
    if not args.store:
        _fail("no store selected: pass --store or set ARTIFACT_STORE to s3|gcs|cloudinary")

    result = STAGERS[args.store](args.file, args.ttl)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(result["url"])
        if result.get("expires_at"):
            print(f"# expires_at: {result['expires_at']} — patch the listing before this", file=sys.stderr)


if __name__ == "__main__":
    main()
