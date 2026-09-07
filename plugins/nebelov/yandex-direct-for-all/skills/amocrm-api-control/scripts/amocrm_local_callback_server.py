#!/usr/bin/env python3
"""Принять один код amoCRM, проверив состояние запроса."""

from __future__ import annotations

import argparse
import http.server
import json
import os
import socketserver
import stat
import tempfile
import urllib.parse
from pathlib import Path


HTML_OK = "<!doctype html><html lang='ru'><meta charset='utf-8'><title>amoCRM</title><h1>Код получен</h1><p>Окно можно закрыть.</p></html>"
HTML_BAD = "<!doctype html><html lang='ru'><meta charset='utf-8'><title>amoCRM</title><h1>Запрос отклонён</h1></html>"


def private_text(path: Path) -> str:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise SystemExit("Файл состояния должен иметь права 0600")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("Файл состояния пуст")
    return value


def atomic_code(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"authorization_code": code}, handle, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_handler(output: Path, expected_state: str, callback_path: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            code = (params.get("code") or [""])[0]
            state = (params.get("state") or [""])[0]
            if parsed.path != callback_path or not code or state != expected_state:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(HTML_BAD.encode("utf-8"))
                return
            atomic_code(output, code)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_OK.encode("utf-8"))

        def log_message(self, fmt, *args_):  # noqa: A003
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8031)
    parser.add_argument("--path", default="/callback")
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"} or not args.path.startswith("/"):
        parser.error("Приёмник разрешён только на локальном адресе и явном пути")
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        parser.error("Файл кода уже существует; удалите старый файл перед новой авторизацией")
    expected_state = private_text(Path(args.state_file).expanduser().resolve())
    handler = build_handler(output, expected_state, args.path)
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        print(f"Ожидается обратный вызов на http://{args.host}:{args.port}{args.path}")
        while not output.exists():
            server.handle_request()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
