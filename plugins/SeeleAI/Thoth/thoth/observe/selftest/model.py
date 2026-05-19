from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PYTHON = sys.executable
FIXED_CLAUDE_DIR = Path("/tmp/thoth-selftest-claude")
FIXED_CODEX_DIR = Path("/tmp/thoth-selftest-codex")
FIXED_RUNTIME_DIR = Path("/tmp/thoth-selftest-runtime")
CODEX_SKILL_NAME = "thoth"
HARD_SUITE_MAX_RUNTIME_SECONDS = 180.0
HEAVY_SUITE_MAX_RUNTIME_SECONDS = 300.0
_SELFTEST_DEADLINE: float | None = None
_SELFTEST_DEADLINE_LABEL: str | None = None
_SELFTEST_DEADLINE_SECONDS: float | None = None
_SELFTEST_STREAM_OUTPUT = False


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CommandResult:
    argv: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    artifacts: list[str] = field(default_factory=list)


__all__ = [
    "CODEX_SKILL_NAME",
    "CheckResult",
    "CommandResult",
    "FIXED_CLAUDE_DIR",
    "FIXED_CODEX_DIR",
    "FIXED_RUNTIME_DIR",
    "HARD_SUITE_MAX_RUNTIME_SECONDS",
    "HEAVY_SUITE_MAX_RUNTIME_SECONDS",
    "PYTHON",
    "ROOT",
    "_SELFTEST_DEADLINE",
    "_SELFTEST_DEADLINE_LABEL",
    "_SELFTEST_DEADLINE_SECONDS",
    "_SELFTEST_STREAM_OUTPUT",
    "utc_now",
]
