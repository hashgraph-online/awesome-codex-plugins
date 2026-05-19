"""Deterministic Python seed repo for Thoth heavy selftests."""

from __future__ import annotations

from pathlib import Path


SEED_FILES: dict[str, str] = {
    ".gitignore": """\
__pycache__/
.pytest_cache/
""",
    "README.md": """\
# Thoth Command Probe Repo

This repository is a disposable probe used by the Thoth heavy selftest.

The heavy gate is allowed to verify only Thoth public-command conformance:

- `run --sleep` and `loop --sleep` must create durable ledgers and stop cleanly
- `review` must return one fixed structured finding
- source files under `tracker/` must remain unchanged
""",
    "tracker/__init__.py": """\
\"\"\"Minimal Python package used by the Thoth command-probe selftest.\"\"\"
""",
    "tracker/runtime_probe.py": """\
from __future__ import annotations


def current_runtime_probe() -> str:
    return "runtime-probe-ok"
""",
    "tracker/review_probe.py": """\
from __future__ import annotations


def rename_task(task: dict, title: str) -> dict:
    task["title"] = title.strip()
    return task
""",
    "scripts/runtime_probe.py": """\
from __future__ import annotations


def main() -> int:
    print("RUNTIME_PROBE_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
}


def seed_host_real_app(project_dir: Path) -> None:
    """Materialize the deterministic Python selftest repo into project_dir."""
    for relative_path, content in SEED_FILES.items():
        target = project_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
