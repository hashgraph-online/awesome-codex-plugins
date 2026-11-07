#!/usr/bin/env python3
"""Run many sync. lipsync generations from a CSV manifest, safely and resumably.

Usage:
  sync_batch.py estimate MANIFEST.csv [--model sync-3]
  sync_batch.py run MANIFEST.csv [--out DIR] [--concurrency N] [--model sync-3] [--only ID,ID] [--retry-failed]
  sync_batch.py submit-batch MANIFEST.csv [--dry-run] [--webhook-url URL] [--model sync-3]
  sync_batch.py batch-status MANIFEST.csv [--wait] [--out DIR]

submit-batch uses the Batch API, which is for Scale plans and above: a queued pipeline for
large runs of short rows whose results can take up to about 24 hours. On every other plan,
and for any run that should start now, use run.

Manifest columns: id, video or image, audio or (script + voice_id), optional sync_mode and model.
Values can be local paths, https URLs or sync. asset IDs. Needs SYNC_API_KEY.

State lives next to the manifest in MANIFEST.csv.state.json: uploaded asset IDs, one
idempotency key and request fingerprint per row, generation IDs and results. Re-running a
command resumes from it: completed rows are skipped, submitted rows are polled instead of
resubmitted, and a row whose inputs changed after submission is refused. Only one command
runs per manifest at a time. Results are also written to results.csv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = os.environ.get("SYNC_API_BASE", "https://api.sync.so").rstrip("/")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
TERMINAL = {"COMPLETED", "FAILED", "REJECTED"}
SYNC_MODES = {"bounce", "loop", "cut_off", "silence", "remap"}
MIME = {
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm", ".avi": "video/x-msvideo",
    ".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".aac": "audio/aac",
    ".ogg": "audio/ogg", ".flac": "audio/flac",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
}
WORDS_PER_SECOND = 2.5
MAX_TRANSIENT_RETRIES = 6
# The API protects an idempotency key for 7 days. Past that, a replay without a known
# generation ID could start a second generation, so it needs a human check first.
REPLAY_WINDOW_SECONDS = 6 * 24 * 3600


class ApiError(Exception):
    def __init__(self, status: int, body, headers=None):
        self.status, self.body, self.headers = status, body, headers or {}
        self.code = body.get("errorCode") if isinstance(body, dict) else None
        message = body.get("message") if isinstance(body, dict) else body
        super().__init__(f"HTTP {status} {self.code or ''}: {message}".replace("  ", " "))

    @property
    def json(self) -> dict:
        return self.body if isinstance(self.body, dict) else {}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow redirects with the API key attached; signed URLs are fetched without it."""

    def redirect_request(self, *args, **kwargs):
        return None


_api_opener = urllib.request.build_opener(_NoRedirect)


def api_raw(method: str, path: str, body=None, headers=None, timeout=70):
    """Call the sync. API and return (status, headers, bytes). Redirects are returned, not followed."""
    key = os.environ.get("SYNC_API_KEY")
    if not key:
        sys.exit("SYNC_API_KEY is not set. Create a key at https://sync.so/settings/api-keys.")
    data = json.dumps(body).encode() if body is not None else None
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("x-api-key", key)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with _api_opener.open(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as err:
        if err.code in (301, 302, 303, 307, 308):
            return err.code, dict(err.headers), b""
        raw = err.read().decode(errors="replace")
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = raw
        raise ApiError(err.code, parsed, dict(err.headers)) from None


def api(method: str, path: str, body=None, headers=None, timeout=70):
    _, _, raw = api_raw(method, path, body, headers, timeout)
    return json.loads(raw) if raw else {}


def fetch(url: str, dest: Path | None = None):
    """GET a signed or public URL, without the API key."""
    with urllib.request.urlopen(url, timeout=300) as resp:
        if dest is None:
            return resp.read()
        tmp = dest.with_name(f"{dest.name}.{os.getpid()}.part")
        with open(tmp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        tmp.replace(dest)
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ManifestLock:
    """One command per manifest at a time, across processes."""

    def __init__(self, manifest: Path):
        self.path = manifest.with_name(manifest.name + ".lock")
        self.fh = None

    def __enter__(self):
        self.fh = open(self.path, "a+")
        try:
            import fcntl
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except ImportError:  # Windows: fall back to an exclusive lock file
            self.fh.close()
            try:
                self.fh = os.fdopen(os.open(str(self.path) + ".win", os.O_CREAT | os.O_EXCL | os.O_WRONLY), "w")
            except FileExistsError:
                sys.exit(f"Another sync_batch.py command is already running on this manifest ({self.path}.win).")
        except OSError:
            sys.exit("Another sync_batch.py command is already running on this manifest. Wait for it to finish.")
        return self

    def __exit__(self, *exc):
        win = Path(str(self.path) + ".win")
        if self.fh:
            self.fh.close()
        if win.exists():
            win.unlink()


class State:
    def __init__(self, manifest: Path):
        self.path = manifest.with_name(manifest.name + ".state.json")
        self.lock = threading.RLock()
        self.data = {"run": uuid.uuid4().hex[:12], "assets": {}, "rows": {}, "batch": None}
        if self.path.exists():
            self.data.update(json.loads(self.path.read_text()))

    def row(self, row_id: str) -> dict:
        with self.lock:
            return dict(self.data["rows"].get(row_id, {}))

    def update(self, row_id: str, **fields):
        with self.lock:
            self.data["rows"].setdefault(row_id, {}).update(fields)
            self.save()

    def save(self):
        with self.lock:
            tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
            tmp.write_text(json.dumps(self.data, indent=2))
            tmp.replace(self.path)

    def batch_unresolved(self) -> bool:
        batch = self.data.get("batch") or {}
        return bool(batch.get("submitting") or (batch.get("id") and batch.get("status") not in ("COMPLETED", "FAILED")))


def read_manifest(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    problems, seen = [], set()
    for n, r in enumerate(rows, start=2):
        rid = r.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", rid):
            problems.append(f"line {n}: id must be 1-80 letters, digits, '_' or '-'")
        if rid in seen:
            problems.append(f"line {n}: duplicate id {rid}")
        seen.add(rid)
        if bool(r.get("video")) == bool(r.get("image")):
            problems.append(f"line {n} ({rid}): set exactly one of video or image")
        if bool(r.get("audio")) == bool(r.get("script")):
            problems.append(f"line {n} ({rid}): set exactly one of audio or script")
        if r.get("script") and not r.get("voice_id"):
            problems.append(f"line {n} ({rid}): script needs voice_id")
        if r.get("sync_mode") and r["sync_mode"] not in SYNC_MODES:
            problems.append(f"line {n} ({rid}): sync_mode must be one of {', '.join(sorted(SYNC_MODES))}")
        for col in ("video", "image", "audio"):
            v = r.get(col)
            if v and not (v.startswith("https://") or UUID_RE.match(v) or (path.parent / Path(v).expanduser()).is_file()):
                problems.append(f"line {n} ({rid}): {col} {v!r} is not a file, https URL or asset ID")
    if not rows:
        problems.append("the manifest has no rows")
    if problems:
        sys.exit("Fix the manifest first:\n  " + "\n  ".join(problems))
    return rows


def local_path(value: str, manifest_dir: Path) -> Path | None:
    if value.startswith("https://") or UUID_RE.match(value):
        return None
    return (manifest_dir / Path(value).expanduser()).resolve()


def fingerprint(row: dict, args, manifest_dir: Path) -> str:
    """Identity of what a row asks for, including the bytes of local files."""
    parts = {"model": row.get("model") or args.model, "sync_mode": row.get("sync_mode", ""),
             "script": row.get("script", ""), "voice_id": row.get("voice_id", "")}
    for col in ("video", "image", "audio"):
        value = row.get(col, "")
        path = local_path(value, manifest_dir) if value else None
        parts[col] = f"sha256:{sha256_file(path)}" if path else value
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def check_unchanged(rows: list[dict], args, state: State, manifest_dir: Path) -> dict:
    """Refuse rows whose inputs changed after they were submitted; returns id -> fingerprint."""
    prints, changed = {}, []
    for row in rows:
        prints[row["id"]] = fp = fingerprint(row, args, manifest_dir)
        saved = state.row(row["id"])
        if saved.get("fingerprint") and saved["fingerprint"] != fp and (saved.get("key") or saved.get("generationId")):
            changed.append(row["id"])
    if changed:
        sys.exit("These rows changed after they were submitted: " + ", ".join(changed) +
                 ".\nGive each changed row a new id (a new paid generation), or restore its original inputs.")
    return prints


def resolve_media(value: str, kind: str, state: State, manifest_dir: Path) -> dict:
    """Return {"url": ...} or {"assetId": ...}, uploading each local file only once."""
    path = local_path(value, manifest_dir)
    if path is None:
        return {"url": value} if value.startswith("https://") else {"assetId": value}
    with state.lock:  # one upload per file content, even when rows share it
        cache_key = f"sha256:{sha256_file(path)}"
        cached = state.data["assets"].get(cache_key)
        if cached:
            return {"assetId": cached}
        content_type = MIME.get(path.suffix.lower())
        if not content_type:
            sys.exit(f"Unsupported file type: {path}")
        size = path.stat().st_size
        presign = api("POST", "/v2/assets/upload", {"fileName": path.name, "contentType": content_type, "size": size})
        with open(path, "rb") as fh:
            put = urllib.request.Request(presign["uploadUrl"], data=fh.read(), method="PUT")
        put.add_header("Content-Type", content_type)
        urllib.request.urlopen(put, timeout=600).read()
        asset = api("POST", "/v2/assets", {"url": presign["url"], "type": kind.upper(), "name": path.name})
        state.data["assets"][cache_key] = asset["id"]
        state.save()
        return {"assetId": asset["id"]}


def payload_for(row: dict, args, state: State, manifest_dir: Path) -> dict:
    visual = "video" if row.get("video") else "image"
    inputs = [{"type": visual, **resolve_media(row[visual], visual, state, manifest_dir)}]
    if row.get("audio"):
        inputs.append({"type": "audio", **resolve_media(row["audio"], "audio", state, manifest_dir)})
    else:
        inputs.append({"type": "text", "provider": {"name": "elevenlabs", "voiceId": row["voice_id"], "script": row["script"]}})
    body = {"model": row.get("model") or args.model, "input": inputs, "outputFileName": row["id"]}
    if row.get("sync_mode") and visual == "video":
        body["options"] = {"sync_mode": row["sync_mode"]}
    return body


def media_seconds(value: str, manifest_dir: Path):
    if UUID_RE.match(value):
        try:
            return api("GET", f"/v2/assets/{value}").get("durationSeconds")
        except ApiError:
            return None
    if not shutil.which("ffprobe"):
        return None
    path = local_path(value, manifest_dir)
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path or value)],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return None


def billable_seconds(row: dict, manifest_dir: Path):
    """The output length sync. bills: the speech, adjusted for cut_off and silence on video."""
    speech = (max(1.0, len(row["script"].split()) / WORDS_PER_SECOND) if row.get("script")
              else media_seconds(row["audio"], manifest_dir))
    if not speech:
        return None
    mode = row.get("sync_mode")
    if row.get("video") and mode in ("cut_off", "silence"):
        video = media_seconds(row["video"], manifest_dir)
        if not video:
            return None
        return min(speech, video) if mode == "cut_off" else max(speech, video)
    return speech


def cmd_estimate(args):
    manifest = Path(args.manifest)
    rows = read_manifest(manifest)
    total, unpriced, approx = 0.0, [], False
    print(f"{'id':<28} {'seconds':>8} {'usd':>9}")
    for row in rows:
        seconds = billable_seconds(row, manifest.parent)
        cost = None
        if seconds:
            est = api("POST", "/v2/generations/estimate", {"model": row.get("model") or args.model, "duration": round(seconds, 2)})
            cost = est.get("estimatedGenerationCost")
        if not isinstance(cost, (int, float)):
            unpriced.append(row["id"])
            print(f"{row['id']:<28} {seconds or '?':>8} {'?':>9}")
            continue
        total += cost
        approx = approx or bool(row.get("script"))
        print(f"{row['id']:<28} {seconds:>8.1f} {cost:>9.2f}")
    note = " Rows with a script are approximate, and speech synthesis is billed separately." if approx else ""
    if unpriced:
        print(f"\nKnown subtotal ${total:.2f} for {len(rows) - len(unpriced)} of {len(rows)} rows.{note}")
        print(f"Couldn't price {len(unpriced)} rows (install ffprobe, or check them by hand): {', '.join(unpriced)}")
        sys.exit(2)
    print(f"\n{len(rows)} rows, estimated total ${total:.2f}.{note}")


class Slots:
    """A concurrency limit that shrinks to the plan's real limit when the API reports it."""

    def __init__(self, limit: int):
        self.limit, self.active, self.cond = max(1, limit), 0, threading.Condition()

    def acquire(self):
        with self.cond:
            while self.active >= self.limit:
                self.cond.wait()
            self.active += 1

    def release(self):
        with self.cond:
            self.active -= 1
            self.cond.notify_all()

    def learn(self, limit):
        if isinstance(limit, int) and limit > 0:
            with self.cond:
                self.limit = min(self.limit, limit)


def submit(body: dict, key: str, slots: Slots) -> dict:
    """POST /v2/generate with a fixed idempotency key; every retry reuses it."""
    attempt = 0
    while True:
        try:
            return api("POST", "/v2/generate", body, {"Idempotency-Key": key})
        except ApiError as err:
            info = err.json
            if err.status == 429:
                slots.learn(info.get("concurrencyLimit"))
                time.sleep(float(info.get("retryAfterSeconds") or err.headers.get("Retry-After") or 20))
                continue
            if err.status == 409 and err.code == "IDEMPOTENCY_IN_PROGRESS":
                time.sleep(2)
                continue
            if info.get("generationId") and err.status in (409, 503):
                return {"id": info["generationId"], "status": "PENDING"}
            attempt += 1
            if (err.status >= 500 or err.status == 408) and attempt <= MAX_TRANSIENT_RETRIES:
                time.sleep(float(err.headers.get("Retry-After") or min(60, 2 ** attempt)))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            attempt += 1
            if attempt > MAX_TRANSIENT_RETRIES:
                raise
            time.sleep(min(60, 2 ** attempt))


def wait_for(gen_id: str) -> dict:
    while True:
        try:
            gen = api("GET", f"/v2/generate/{gen_id}?wait=true&timeout=10")
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(5)
            continue
        except ApiError as err:
            if err.status == 429 or err.status >= 500:
                time.sleep(10)
                continue
            raise
        if gen.get("status") in TERMINAL:
            return gen
        time.sleep(3)


def download(rid: str, url: str, out: str | None, state: State):
    if not out or not url:
        return
    dest = Path(out).resolve() / f"{rid}.mp4"
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    fetch(url, dest)
    state.update(rid, file=str(dest))


def process_row(row, args, state: State, slots: Slots, manifest_dir: Path, fp: str):
    rid = row["id"]
    saved = state.row(rid)
    if saved.get("status") == "COMPLETED" and saved.get("outputUrl"):
        download(rid, saved["outputUrl"], args.out, state)
        print(f"{rid}: already completed", flush=True)
        return
    retry = saved.get("status") in {"FAILED", "REJECTED"} and args.retry_failed
    if saved.get("status") in {"FAILED", "REJECTED"} and not retry:
        print(f"{rid}: {saved['status']} earlier ({saved.get('error')}); pass --retry-failed to try again", flush=True)
        return
    key = saved.get("key") or f"{state.data['run']}-{rid}"[:128]
    try:
        if saved.get("generationId") and not retry:
            gen = wait_for(saved["generationId"])
        else:
            submitted_at = saved.get("submittedAt")
            if submitted_at and not saved.get("generationId") and time.time() - submitted_at > REPLAY_WINDOW_SECONDS:
                print(f"{rid}: submitted {int((time.time() - submitted_at) / 86400)} days ago with no confirmed generation. "
                      f"Check GET /v2/generations for it before retrying; skipped.", flush=True)
                return
            body = payload_for(row, args, state, manifest_dir)
            # Save the key, request identity and time before the request, so a crash can't lose them.
            state.update(rid, key=key, fingerprint=fp, mode="single", submittedAt=submitted_at or time.time())
            slots.acquire()
            try:
                # After a confirmed failure the same key starts a fresh attempt, per the API's idempotency rules.
                created = submit(body, key, slots)
                state.update(rid, generationId=created["id"], status=created.get("status", "PENDING"), error=None)
                gen = wait_for(created["id"])
            finally:
                slots.release()
        state.update(rid, status=gen["status"], outputUrl=gen.get("outputUrl"), error=gen.get("error") or gen.get("errorCode"))
        if gen["status"] == "COMPLETED":
            download(rid, gen.get("outputUrl"), args.out, state)
        suffix = "" if gen["status"] == "COMPLETED" else f" ({gen.get('error') or gen.get('errorCode')})"
        print(f"{rid}: {gen['status']}{suffix}", flush=True)
    except ApiError as err:
        state.update(rid, status="FAILED", error=str(err))
        print(f"{rid}: FAILED ({err})", flush=True)


def write_results(manifest: Path, rows: list[dict], state: State):
    out = manifest.with_name("results.csv")
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "status", "generation_id", "output_url", "file", "error"])
        for row in rows:
            s = state.data["rows"].get(row["id"], {})
            w.writerow([row["id"], s.get("status", "NOT_STARTED"), s.get("generationId") or "",
                        s.get("outputUrl") or "", s.get("file", ""), s.get("error") or ""])
    statuses = [state.data["rows"].get(r["id"], {}).get("status") for r in rows]
    print(f"\n{statuses.count('COMPLETED')}/{len(rows)} completed, "
          f"{sum(s in ('FAILED', 'REJECTED') for s in statuses)} failed. Results: {out}")


def cmd_run(args):
    manifest = Path(args.manifest)
    all_rows = read_manifest(manifest)
    rows = all_rows
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        rows = [r for r in all_rows if r["id"] in wanted]
        missing = wanted - {r["id"] for r in rows}
        if missing:
            sys.exit(f"Unknown row ids: {', '.join(sorted(missing))}")
    state = State(manifest)
    if state.batch_unresolved():
        in_batch = [r["id"] for r in rows if state.row(r["id"]).get("mode") == "batch"]
        if (state.data["batch"] or {}).get("submitting") or in_batch:
            sys.exit("A batch for this manifest is still running or its submission is unconfirmed. "
                     "Run batch-status first, so its rows aren't submitted twice.")
    prints = check_unchanged(rows, args, state, manifest.parent)
    state.save()
    slots = Slots(args.concurrency)
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        for future in [pool.submit(process_row, r, args, state, slots, manifest.parent, prints[r["id"]]) for r in rows]:
            future.result()
    write_results(manifest, all_rows, state)


NO_BATCH_ACCESS = ("The Batch API is for Scale plans and above, and this plan doesn't include it ({error}). "
                   "Nothing was submitted. Use run instead: it starts every row now, within the plan's concurrency.")


def cmd_submit_batch(args):
    manifest = Path(args.manifest)
    rows = read_manifest(manifest)
    state = State(manifest)
    batch = state.data.get("batch") or {}
    if batch.get("submitting") and not args.dry_run:
        sys.exit("A previous submit may have reached sync. without a reply. List your batches with GET /v2/batch "
                 "and check for it before submitting again; then remove the 'batch' entry from the state file.")
    if state.batch_unresolved() and not args.dry_run:
        sys.exit(f"Batch {batch['id']} is still running. Use batch-status.")
    prints = check_unchanged(rows, args, state, manifest.parent)
    # Rows already submitted on their own (a pilot, or an earlier run) stay out of the batch.
    pending = [r for r in rows if not state.row(r["id"]).get("generationId") and state.row(r["id"]).get("status") != "COMPLETED"]
    skipped = len(rows) - len(pending)
    if not pending:
        sys.exit("Every row was already submitted. Use run to follow them up.")
    body = {"rows": [{"request_id": r["id"], "endpoint": "/v2/generate",
                      "payload": payload_for(r, args, state, manifest.parent)} for r in pending]}
    if args.webhook_url:
        body["webhook_url"] = args.webhook_url
    if args.dry_run:
        body["dry_run"] = True
        try:
            validated = api("POST", "/v2/batch", body)
        except ApiError as err:
            if err.status == 402:
                sys.exit(NO_BATCH_ACCESS.format(error=err))
            raise
        print(json.dumps(validated) + (f" ({skipped} rows already submitted were left out)" if skipped else ""))
        return
    state.data["batch"] = {"submitting": True, "rows": [r["id"] for r in pending], "submittedAt": time.time()}
    for r in pending:
        state.data["rows"].setdefault(r["id"], {}).update(mode="batch", fingerprint=prints[r["id"]])
    state.save()
    try:
        created = api("POST", "/v2/batch", body)
    except ApiError as err:
        if err.status != 402:
            raise
        # A 402 is a refusal before anything is created, so the rows are free for run again.
        state.data["batch"] = batch or None
        for r in pending:
            state.data["rows"][r["id"]].pop("mode", None)
        state.save()
        sys.exit(NO_BATCH_ACCESS.format(error=err))
    state.data["batch"] = {"id": created["id"], "status": created.get("status"), "rows": [r["id"] for r in pending]}
    state.save()
    print(f"Batch {created['id']} submitted with {len(pending)} rows"
          + (f" ({skipped} already submitted rows left out)" if skipped else "") + ". Check on it with batch-status.")


def cmd_batch_status(args):
    manifest = Path(args.manifest)
    rows = read_manifest(manifest)
    state = State(manifest)
    batch_id = (state.data.get("batch") or {}).get("id")
    if not batch_id:
        sys.exit("No confirmed batch in the state file. Run submit-batch first, or reconcile with GET /v2/batch.")
    while True:
        batch = api("GET", f"/v2/batch/{batch_id}")
        print(f"{batch_id}: {batch.get('status')} {json.dumps(batch.get('metrics') or {})}", flush=True)
        if batch.get("status") in {"COMPLETED", "FAILED"} or not args.wait:
            break
        time.sleep(args.interval)
    state.data["batch"]["status"] = batch.get("status")
    state.save()
    if batch.get("status") != "COMPLETED" or not batch.get("outputUrl"):
        return
    # The results URL answers with a redirect to a signed file; fetch that without the API key.
    status, headers, raw = api_raw("GET", batch["outputUrl"])
    text = fetch(headers.get("Location") or headers.get("location")).decode() if 300 <= status < 400 else raw.decode()
    for line in filter(None, (ln.strip() for ln in text.splitlines())):
        rec = json.loads(line)
        rid, resp, error = rec["request_id"], rec.get("response") or {}, rec.get("error")
        state.update(rid, status=rec.get("status"), generationId=resp.get("id"),
                     outputUrl=resp.get("output_url") or resp.get("outputUrl"),
                     error=error.get("message") if isinstance(error, dict) else error)
        if rec.get("status") == "COMPLETED":
            download(rid, state.row(rid).get("outputUrl"), args.out, state)
    write_results(manifest, rows, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("estimate", "run", "submit-batch", "batch-status"):
        p = sub.add_parser(name)
        p.add_argument("manifest")
        p.add_argument("--model", default="sync-3")
        if name in ("run", "batch-status"):
            p.add_argument("--out", help="download finished videos into this directory")
        if name == "run":
            p.add_argument("--concurrency", type=int, default=1,
                           help="generations in flight; set it to the plan's generationLimits.concurrency")
            p.add_argument("--only", help="comma-separated row ids, for a pilot run")
            p.add_argument("--retry-failed", action="store_true", help="start new attempts for FAILED or REJECTED rows")
        if name == "submit-batch":
            p.add_argument("--dry-run", action="store_true", help="validate only; creates nothing")
            p.add_argument("--webhook-url")
        if name == "batch-status":
            p.add_argument("--wait", action="store_true", help="keep checking until the batch finishes")
            p.add_argument("--interval", type=float, default=60, help="seconds between checks with --wait")
    args = parser.parse_args()
    commands = {"estimate": cmd_estimate, "run": cmd_run, "submit-batch": cmd_submit_batch, "batch-status": cmd_batch_status}
    if args.command == "estimate":
        commands[args.command](args)
        return
    with ManifestLock(Path(args.manifest)):
        commands[args.command](args)


if __name__ == "__main__":
    main()
