"""Redaction of tokens and secrets before anything is sent or logged.

Two layers, both applied to every outgoing text and every log line:
* exact values the process knows are secret (the bot token, any value the
  caller registers) - replaced wherever they appear, including inside URLs;
* shape patterns for secrets the process does not know (other bot tokens,
  common API-key prefixes, `password=...` style assignments, private keys).

Redaction is a safety net, not a licence to send logs anywhere: file contents
and logs still go only to the operator's private chat (see security.py).
"""
from __future__ import annotations

import re
from typing import Any, Iterable

MASK = "[REDACTED]"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # no leading \b: the token also hides inside api.telegram.org/bot<id>:<secret> URLs
    ("bot_token", re.compile(r"(?<!\d)\d{6,12}:[A-Za-z0-9_-]{30,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)),
    ("api_key", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    # `\w*` around the keyword so `.env` names such as OPENAI_API_KEY or DB_PASSWORD match too
    ("assignment", re.compile(
        r"(?i)\b(\w*(?:password|passwd|secret|token|api[_-]?key)\w*)(\s*[:=]\s*)(['\"]?)[^\s'\"]{4,}\3")),
    ("url_credentials", re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s@/]{3,})(@)")),
]


class Redactor:
    def __init__(self, secrets: Iterable[str] = ()):  # values, never names
        self._secrets: list[str] = []
        for s in secrets:
            self.add(s)

    def add(self, secret: str | None) -> None:
        if secret and len(secret) >= 6 and secret not in self._secrets:
            self._secrets.append(secret)
            self._secrets.sort(key=len, reverse=True)

    def text(self, value: str) -> str:
        for s in self._secrets:
            value = value.replace(s, MASK)
        for name, rx in PATTERNS:
            if name == "assignment":
                value = rx.sub(lambda m: f"{m.group(1)}{m.group(2)}{MASK}", value)
            elif name == "url_credentials":
                value = rx.sub(lambda m: f"{m.group(1)}{MASK}{m.group(3)}", value)
            else:
                value = rx.sub(MASK, value)
        return value

    def obj(self, value: Any) -> Any:
        """Deep-redact a JSON-like value (strings only; keys are kept)."""
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, list):
            return [self.obj(v) for v in value]
        if isinstance(value, dict):
            return {k: self.obj(v) for k, v in value.items()}
        return value

    def findings(self, value: str) -> list[str]:
        """Names of the secret shapes found (for refusing to upload a file)."""
        found = [n for n, rx in PATTERNS if rx.search(value)]
        if any(s in value for s in self._secrets):
            found.insert(0, "known_secret")
        return found


__all__ = ["Redactor", "MASK", "PATTERNS"]
