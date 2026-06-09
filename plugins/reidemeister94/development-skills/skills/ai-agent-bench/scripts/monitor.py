"""Heartbeat sidecar — writes `<run_dir>/progress.md` every ~3 minutes.

Spawned by `run_trial.py` at trial start, terminated at trial end. The wizard reads
`progress.md` whenever the user sends a new message to surface a human-readable
status to the user (Claude Code has no native timer-driven hook).

Sources sampled per tick:
- `<run_dir>/status.txt` last line  → current phase + age
- `<run_dir>/session.jsonl` size  → growing = agent active; flat for >10 min = probable stall
- `<run_dir>/agent_exit_code.txt` if present → agent already exited

Usage:
    python monitor.py --run-dir /abs/run-dir [--interval 180]
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STALL_THRESHOLD_S = 10 * 60  # 10 min flat session.jsonl while agent:running


def _last_line(path: Path) -> str:
    try:
        with path.open("rb") as f:
            try:
                f.seek(-2, 2)
                while f.read(1) != b"\n":
                    f.seek(-2, 1)
            except OSError:
                f.seek(0)
            return f.readline().decode(errors="replace").rstrip()
    except (OSError, FileNotFoundError):
        return ""


def _phase_and_age(status_path: Path) -> tuple[str, float | None]:
    line = _last_line(status_path)
    if not line or "\t" not in line:
        return "unknown", None
    ts_str, _, phase = line.partition("\t")
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return phase.strip(), (datetime.now(timezone.utc) - ts).total_seconds()
    except ValueError:
        return phase.strip() or "unknown", None


def _fmt_dur(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"


def write_progress(run_dir: Path) -> None:
    phase, age_s = _phase_and_age(run_dir / "status.txt")
    session = run_dir / "session.jsonl"
    session_bytes = session.stat().st_size if session.exists() else 0
    last_session_line = _last_line(session) if session.exists() else ""

    # Stall detection: track session size between ticks via a small state file.
    state = run_dir / ".monitor_state"
    prev_bytes = 0
    prev_ts = 0.0
    if state.exists():
        try:
            parts = state.read_text().strip().split()
            prev_bytes = int(parts[0])
            prev_ts = float(parts[1])
        except (ValueError, IndexError):
            pass
    now = time.time()
    flat_for = (now - prev_ts) if (session_bytes == prev_bytes and prev_ts) else 0.0
    state.write_text(f"{session_bytes} {prev_ts if session_bytes == prev_bytes else now}\n")

    stall_warn = ""
    if phase == "agent:running" and flat_for > STALL_THRESHOLD_S:
        stall_warn = f"\n\n⚠ session.jsonl flat for {_fmt_dur(flat_for)} — possible stall"

    agent_exit = ""
    exit_file = run_dir / "agent_exit_code.txt"
    if exit_file.exists():
        agent_exit = f"\nAgent exit code: `{exit_file.read_text().strip()}`"

    snippet = (last_session_line[:240] + "…") if len(last_session_line) > 240 else last_session_line

    body = f"""# Trial progress

Updated: `{datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}`

| | |
|---|---|
| Phase | `{phase}` |
| Phase age | {_fmt_dur(age_s)} |
| session.jsonl | {session_bytes:,} bytes |
{f"| Tail | `{snippet}` |" if snippet else ""}{agent_exit}{stall_warn}
"""
    (run_dir / "progress.md").write_text(body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--interval", type=int, default=180, help="seconds between ticks (default 180)")
    args = ap.parse_args()

    run_dir = args.run_dir.resolve()
    if not run_dir.exists():
        print(f"ERROR: run dir does not exist: {run_dir}", file=sys.stderr)
        return 2

    while True:
        try:
            write_progress(run_dir)
            # Stop monitoring once the trial is fully done.
            phase, _ = _phase_and_age(run_dir / "status.txt")
            if phase == "done":
                return 0
        except Exception as e:
            # Best-effort: never crash the sidecar; log and continue.
            (run_dir / "monitor.errors.log").open("a").write(
                f"{datetime.now(timezone.utc).isoformat()}\t{type(e).__name__}\t{e}\n"
            )
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
