"""Decide whether a file is humanizable natural language."""

from __future__ import annotations

import re
from pathlib import Path

NATURAL_LANGUAGE_EXTENSIONS = {".md", ".markdown", ".txt", ".rst"}

CODE_OR_CONFIG_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".rb", ".go", ".rs", ".java", ".kt", ".swift", ".m",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".xml", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".sql", ".graphql", ".proto",
    ".lock", ".env",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".dll", ".so", ".dylib", ".exe", ".bin",
}

EXTENSIONLESS_NATURAL_LANGUAGE_BASENAMES = {
    "readme",
    "license",
    "copying",
    "authors",
    "changelog",
    "changes",
    "todo",
    "notes",
    "notice",
}

EXTENSIONLESS_CODE_OR_CONFIG_BASENAMES = {
    "dockerfile",
    "makefile",
    "justfile",
    "jenkinsfile",
    "gemfile",
    "rakefile",
    "procfile",
    "podfile",
    "vagrantfile",
    "brewfile",
}

SENSITIVE_PATH_FRAGMENTS = (
    "/.env", "/.env.", ".env.local", ".env.production", ".env.staging",
    "/.ssh/", "/.aws/", "/.gnupg/", "/.kube/", "/.docker/",
    "id_rsa", "id_dsa", "id_ed25519", "id_ecdsa",
    ".pem", ".key", ".crt", ".cer", ".pfx", ".p12",
    "secret", "credential", "password", "token",
    ".npmrc", ".pypirc", ".netrc",
)

SENSITIVE_CONTENT_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\bASIA[0-9A-Z]{16}\b",
        r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
        r"\bsk-(?:proj|svcacct)-[A-Za-z0-9_-]{20,}\b",
        r"\bsk-[A-Za-z0-9]{32,}\b",
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b",
        r"\bgithub_pat_[A-Za-z0-9_]{30,}\b",
        r"\bhf_[A-Za-z0-9]{30,}\b",
        r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b",
    )
)


def _looks_like_plain_prose(sample_text: str) -> bool:
    """Heuristic guard for extensionless files.

    We only treat extensionless files as natural language when they look like
    prose and not code/config. Conservative by design.
    """
    text = sample_text.strip()
    if not text:
        return False

    symbol_count = sum(ch in "{}[]();<>=$`\\|" for ch in text)
    symbol_ratio = symbol_count / len(text)
    if symbol_ratio > 0.06:
        return False

    non_space = [ch for ch in text if not ch.isspace()]
    if not non_space:  # pragma: no cover  (unreachable: strip() above guarantees content)
        return False
    alpha_ratio = sum(ch.isalpha() for ch in non_space) / len(non_space)
    return alpha_ratio >= 0.65


def is_sensitive_path(path: Path) -> bool:
    p = str(path).lower()
    return any(fragment in p for fragment in SENSITIVE_PATH_FRAGMENTS)


def has_sensitive_content(text: str) -> bool:
    """Return True when prose contains token/private-key shapes.

    Path checks catch obvious secret files. This content check protects allowed
    Markdown/text files from being sent to LLM mode with embedded credentials.
    Deterministic mode can still run locally because it makes no network call.
    """
    return any(pattern.search(text) for pattern in SENSITIVE_CONTENT_PATTERNS)


def is_already_humanized_backup(path: Path) -> bool:
    return path.name.endswith(".original.md") or path.name.endswith(".original.txt")


def detect_file_type(path: Path) -> str:
    if is_sensitive_path(path):
        return "sensitive"
    if is_already_humanized_backup(path):
        return "backup"

    suffix = path.suffix.lower()
    if suffix in NATURAL_LANGUAGE_EXTENSIONS:
        return "natural-language"
    if suffix in CODE_OR_CONFIG_EXTENSIONS:
        return "code-or-config"

    if suffix == "":
        basename = path.name.lower()
        if path.name.startswith("."):
            return "code-or-config"
        if basename in EXTENSIONLESS_CODE_OR_CONFIG_BASENAMES:
            return "code-or-config"
        try:
            sample = path.read_bytes()[:4096]
        except OSError:
            return "unknown"
        if b"\x00" in sample:
            return "binary"
        if sample.startswith(b"#!"):
            return "code-or-config"
        try:
            decoded = sample.decode("utf-8")
        except UnicodeDecodeError:
            return "binary"
        if basename in EXTENSIONLESS_NATURAL_LANGUAGE_BASENAMES:
            return "natural-language-extensionless"
        if _looks_like_plain_prose(decoded):
            return "natural-language-extensionless"
        return "unknown"

    return "other"


MAX_BYTES = 500 * 1024  # 500 KB


def should_compress(path: Path) -> bool:
    """True iff this path is safe and worthwhile to humanize."""
    file_type = detect_file_type(path)
    if file_type in ("sensitive", "backup", "code-or-config", "binary", "other", "unknown"):
        return False

    try:
        size = path.stat().st_size
    except OSError:
        return False
    return not (size == 0 or size > MAX_BYTES)
