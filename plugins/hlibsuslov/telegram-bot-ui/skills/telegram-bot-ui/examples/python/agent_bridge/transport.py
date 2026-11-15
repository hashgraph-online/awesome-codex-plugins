"""Transports: dry-run (default) and live (explicit opt-in).

* DryRunTransport - tgkit's FakeTransport (JSON round trip, scripted answers)
  plus `upload()` for files; it records file name, size and sha256 instead of
  bytes. Nothing leaves the machine.
* LiveTransport   - tgkit's HttpTransport plus multipart uploads. Created only
  by `live_from_env()` when the caller passed `--live` AND the token env var
  is set. The token is read from the env var NAME given by the caller; it is
  never printed, logged or put in a repr.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import urllib.error
import urllib.request
import uuid
from typing import Any

from tgkit.errors import OutcomeUnknown, from_response
from tgkit.transport import FakeTransport, HttpTransport

UPLOAD_LIMIT = 50 * 1024 * 1024      # sendDocument: "files of any type of up to 50 MB" (Bot API, 2026-11-15)


def read_file(source: "str | tuple[str, bytes]") -> tuple[str, bytes]:
    """A path, or (name, bytes) already read once by the caller (scan and upload
    must use the same bytes, or a swapped file could be sent unscanned)."""
    if isinstance(source, tuple):
        return source
    with open(source, "rb") as fh:
        return os.path.basename(source), fh.read()


def file_meta(source: "str | tuple[str, bytes]") -> dict[str, Any]:
    name, data = read_file(source)
    return {"name": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class DryRunTransport(FakeTransport):
    def __init__(self) -> None:
        super().__init__()
        self.uploads: list[dict[str, Any]] = []

    def upload(self, method: str, params: dict[str, Any], files: dict[str, Any]) -> Any:
        self.uploads.append({"method": method, **{k: file_meta(p) for k, p in files.items()}})
        return self.call(method, params)


class LiveTransport(HttpTransport):
    def __repr__(self) -> str:
        return "LiveTransport(<token hidden>)"

    def upload(self, method: str, params: dict[str, Any], files: dict[str, Any]) -> Any:
        boundary = uuid.uuid4().hex
        parts: list[bytes] = []
        for k, v in params.items():
            value = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{value}\r\n'.encode())
        for field, source in files.items():
            name, data = read_file(source)
            name = re.sub(r'["\r\n]', "_", name)    # no header injection through the file name
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{name}"\r\n'
                         f"Content-Type: application/octet-stream\r\n\r\n".encode() + data + b"\r\n")
        body = b"".join(parts) + f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(self._prefix + method, data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            payload = json.loads(err.read().decode("utf-8") or "{}") or {"ok": False, "error_code": err.code,
                                                                         "description": str(err.reason)}
        except (socket.timeout, TimeoutError, ConnectionResetError) as err:
            raise OutcomeUnknown(method, type(err).__name__) from None
        if not payload.get("ok"):
            raise from_response(method, payload)
        return payload.get("result")


def live_from_env(token_env: str, *, environ: dict[str, str] | None = None, timeout: float = 60.0) -> LiveTransport:
    env = os.environ if environ is None else environ
    token = env.get(token_env)
    if not token:
        raise SystemExit(f"--live needs the bot token in the environment variable {token_env}.")
    return LiveTransport(token, timeout=timeout)


__all__ = ["DryRunTransport", "LiveTransport", "live_from_env", "file_meta", "UPLOAD_LIMIT"]
