# Python integration

`pip install syncsdk`. It brings in `httpx`, which the HTTP-only calls below also use. Python 3.8+.

```python
import json
import mimetypes
import os
import pathlib
import time
import uuid

import httpx
from sync import Sync
from sync.common import Audio, Video
from sync.core.api_error import ApiError

API = "https://api.sync.so/v2"
HEADERS = {"x-api-key": os.environ["SYNC_API_KEY"]}
client = Sync()  # reads SYNC_API_KEY


def upload(path: str, kind: str) -> str:
    """Upload a local file into sync. storage and return its asset ID. kind: VIDEO, AUDIO or IMAGE."""
    file = pathlib.Path(path)
    content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
    presign = httpx.post(f"{API}/assets/upload", headers=HEADERS, timeout=30,
                         json={"fileName": file.name, "contentType": content_type, "size": file.stat().st_size})
    presign.raise_for_status()
    target = presign.json()
    # The presigned upload URL must not receive the API key.
    with file.open("rb") as body:
        httpx.put(target["uploadUrl"], content=body, headers={"Content-Type": content_type}, timeout=600).raise_for_status()
    asset = httpx.post(f"{API}/assets", headers=HEADERS, timeout=30, json={"url": target["url"], "type": kind})
    asset.raise_for_status()
    return asset.json()["id"]


def estimate(model: str, seconds: float) -> float:
    resp = httpx.post(f"{API}/generations/estimate", headers=HEADERS, timeout=30,
                      json={"model": model, "duration": seconds})
    resp.raise_for_status()
    return resp.json()["estimatedGenerationCost"]  # USD


def start_lipsync(job: dict) -> str:
    """job is your persisted record: video/audio asset IDs and an idempotency key, all saved before this call."""
    while True:
        try:
            generation = client.generations.create(
                model="sync-3",
                input=[Video(asset_id=job["video_asset_id"]), Audio(asset_id=job["audio_asset_id"])],
                options={"sync_mode": "bounce"},
                webhook_url=job.get("webhook_url"),
                request_options={"additional_headers": {"Idempotency-Key": job["idempotency_key"]}},
            )
            return generation.id
        except ApiError as err:
            body = err.body if isinstance(err.body, dict) else {}
            if err.status_code == 429:
                time.sleep(float(body.get("retryAfterSeconds", 20)))
                continue  # same key, so no duplicate generation
            if err.status_code == 409 and body.get("generationId"):
                return body["generationId"]
            raise


def wait_for(generation_id: str) -> str:
    """Polling fallback. Prefer a webhook in production."""
    while True:
        resp = httpx.get(f"{API}/generate/{generation_id}", headers=HEADERS, timeout=30,
                         params={"wait": "true", "timeout": 10})
        resp.raise_for_status()
        generation = resp.json()
        if generation["status"] == "COMPLETED":
            return generation["outputUrl"]
        if generation["status"] in ("FAILED", "REJECTED"):
            raise RuntimeError(f"{generation['status']}: {generation.get('errorCode')} {generation.get('error')}")
        time.sleep(2)


JOB_FILE = pathlib.Path("lipsync-job.json")  # stands in for a row in your database


def load_or_create_job() -> dict:
    """Save the asset IDs and the idempotency key before creating, so a restart can't pay twice."""
    if JOB_FILE.exists():
        return json.loads(JOB_FILE.read_text())
    job = {
        "video_asset_id": upload("talk.mp4", "VIDEO"),
        "audio_asset_id": upload("new-take.wav", "AUDIO"),
        "idempotency_key": str(uuid.uuid4()),
    }
    JOB_FILE.write_text(json.dumps(job))
    return job


if __name__ == "__main__":
    job = load_or_create_job()
    if not job.get("generation_id"):
        print("Estimated cost: $%.2f" % estimate("sync-3", 12.0))
        job["generation_id"] = start_lipsync(job)
        JOB_FILE.write_text(json.dumps(job))
    # After a restart this polls the saved generation instead of creating another one.
    print("Output:", wait_for(job["generation_id"]))
```

## Variations

- **Script instead of audio:** `from sync.common import Tts, ElevenLabs`, then `Tts(provider=ElevenLabs(voice_id="<voiceId>", script="Hello!"))` in place of `Audio(...)`. List voices with `GET /v2/voices`.
- **Image input, `dubParams`, `projectId`:** if your installed `syncsdk` doesn't type them yet, send the same JSON body with `httpx.post(f"{API}/generate", headers={**HEADERS, "Idempotency-Key": key}, json=body)`.
- **Async code:** `from sync import AsyncSync` has the same methods, awaited.
