"""Run one agent trial: worktree → outer_check (pre) → agent → outer_check (post) → cleanup.

Reads `<repo>/.agent-bench.toml` (5 fields: prompt, start_branch/start_commit, agents,
outer_check, inner_check). Output goes to
`<repo>/eval-results/<task>/<agent>/run-<id>-<ts>/`. The agent's work survives on branch
`eval-<agent>-run<id>-<ts>` (the worktree dir is removed at the end).

Usage:
    python run_trial.py --repo /abs/path --config /abs/path/.agent-bench.toml \\
        --agent claude --run 1

Exit codes:
    0 — trial completed (outer_check post may have failed; inspect outer_post.json)
    2 — bad arguments / preflight failure (missing CLI, dirty repo, invalid config)
    3 — outer_check failed before the agent session, so no valid baseline exists
"""

from __future__ import annotations

import argparse
import json
import shutil
import signal
import subprocess
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ANOMALY_FILE_NAME = "ai-agent-bench-anomalies.md"
ANOMALY_HEADER = (
    "# AI Agent Bench Anomalies\n\n"
    "Append-only log. Each run is delimited by `---` and a `## Run …` header; "
    "previous runs are preserved.\n"
)


def run_capture(cmd: list[str] | str, *, cwd: Path | None = None) -> tuple[int, str, str]:
    shell = isinstance(cmd, str)
    p = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, shell=shell, capture_output=True, text=True
    )
    return p.returncode, p.stdout, p.stderr


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def require_config_value(cfg: dict, key: str, repo: Path) -> str:
    value = cfg.get(key)
    if value:
        return str(value)
    append_anomaly(
        repo,
        title="required config field missing",
        step="preflight",
        severity="high",
        symptom="The simplified TOML config is missing a required field.",
        evidence=f"missing_key={key}",
        expected="The config contains prompt, outer_check, and inner_check.",
        observed=f"`{key}` is missing or empty.",
        implication="The harness cannot preserve the simplified benchmark contract.",
        disposition="aborted",
    )
    die(f"config missing `{key}`")


def append_anomaly(
    repo: Path,
    *,
    title: str,
    step: str,
    severity: str,
    symptom: str,
    evidence: str,
    expected: str,
    observed: str,
    implication: str,
    disposition: str,
    details: str = "No additional details captured.",
    run_context: dict | None = None,
) -> None:
    """Append an audit entry. Each run is preceded by a `---` divider + `## Run …` header,
    written exactly once per `run_dir`. Preflight entries (no run context) are delimited
    the same way under a `## Preflight …` header."""
    path = repo / ANOMALY_FILE_NAME
    if not path.exists():
        path.write_text(ANOMALY_HEADER)

    existing = path.read_text()
    timestamp = datetime.now(timezone.utc).isoformat()

    section_header = ""
    if run_context:
        marker = f"- Run dir: {run_context.get('run_dir', '-')}"
        if marker not in existing:
            section_header = (
                "\n---\n\n"
                f"## Run {run_context.get('agent', '-')}/"
                f"{run_context.get('run', '-')} — {timestamp}\n\n"
                f"- Agent: {run_context.get('agent', '-')}\n"
                f"- Run ID: {run_context.get('run', '-')}\n"
                f"- Start commit: {run_context.get('start_sha', '-')}\n"
                f"- Run dir: {run_context.get('run_dir', '-')}\n"
                f"- Worktree branch: {run_context.get('branch', '-')}\n"
                f"- Prompt: {run_context.get('prompt', '-')}\n"
            )
    else:
        section_header = f"\n---\n\n## Preflight — {timestamp}\n"

    entry = (
        f"{section_header}\n"
        f"### {timestamp} — {title}\n\n"
        f"- Step: {step}\n"
        f"- Severity: {severity}\n"
        f"- Symptom: {symptom}\n"
        f"- Evidence: {evidence}\n"
        "- Detailed analysis:\n"
        f"  - Expected: {expected}\n"
        f"  - Observed: {observed}\n"
        f"  - Implication: {implication}\n"
        f"  - Details: {details}\n"
        f"- Disposition: {disposition}\n"
    )
    with path.open("a") as f:
        f.write(entry)


def update_status(run_dir: Path, phase: str) -> None:
    """Append a phase transition. Read by the monitor.py sidecar for heartbeat."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with (run_dir / "status.txt").open("a") as f:
        f.write(f"{ts}\t{phase}\n")


def run_outer_check(cmd: str, *, cwd: Path, log_path: Path) -> dict:
    """Run outer_check, time it, capture stdout/stderr to log_path. Returns {exit, wall_s}."""
    t0 = time.perf_counter()
    with log_path.open("w") as log:
        p = subprocess.run(cmd, shell=True, cwd=str(cwd), stdout=log, stderr=log)
    wall_s = time.perf_counter() - t0
    return {"exit_code": p.returncode, "wall_s": round(wall_s, 3), "log": log_path.name}


def build_agent_command(agent: str, prompt: str, worktree: Path, run_dir: Path) -> list[str]:
    if agent == "claude":
        return [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--include-partial-messages",
            "--include-hook-events",
            "--verbose",
            "--dangerously-skip-permissions",
            "--add-dir",
            str(worktree),
        ]
    if agent == "codex":
        return [
            "codex",
            "exec",
            "--json",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--output-last-message",
            str(run_dir / "last_message.txt"),
            "--cd",
            str(worktree),
            prompt,
        ]
    if agent == "opencode":
        # Stub — parser captures nothing meaningful yet.
        return ["bash", "-c", 'echo \'{"type":"opencode_stub","note":"parser not implemented"}\'']
    raise ValueError(f"unknown agent: {agent}")


def run_agent(agent: str, prompt: str, worktree: Path, run_dir: Path) -> tuple[int, int]:
    cmd = build_agent_command(agent, prompt, worktree, run_dir)
    session = run_dir / "session.jsonl"
    stderr = run_dir / "stderr.log"
    t0 = time.time()
    with session.open("w") as out, stderr.open("w") as err:
        p = subprocess.run(cmd, cwd=str(worktree), stdout=out, stderr=err)
    return p.returncode, int(time.time() - t0)


def spawn_monitor(run_dir: Path) -> subprocess.Popen | None:
    """Sidecar — writes run_dir/progress.md every ~3 min. Best-effort, non-fatal if missing."""
    monitor = SCRIPT_DIR / "monitor.py"
    if not monitor.exists():
        return None
    return subprocess.Popen([sys.executable, str(monitor), "--run-dir", str(run_dir)])


def kill_monitor(proc: subprocess.Popen | None) -> None:
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--agent", choices=["claude", "codex", "opencode"], required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--output-base", type=Path)
    ap.add_argument("--skip-pre", action="store_true")
    ap.add_argument("--skip-post", action="store_true")
    ap.add_argument("--skip-agent", action="store_true", help="harness dry-run only")
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        die(f"not a git repository: {repo}")

    cfg_path = args.config.resolve()
    if not cfg_path.exists():
        append_anomaly(
            repo,
            title="config file missing",
            step="preflight",
            severity="high",
            symptom="run_trial.py could not start because the configured TOML file is missing.",
            evidence=f"config={cfg_path}",
            expected="A readable .agent-bench.toml is present before launch.",
            observed="The config path does not exist.",
            implication="No prompt, start ref, agent list, outer_check, or inner_check can be resolved.",
            disposition="aborted",
        )
        die(f"config not found: {cfg_path}")
    try:
        with cfg_path.open("rb") as f:
            cfg = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        append_anomaly(
            repo,
            title="config file is invalid TOML",
            step="preflight",
            severity="high",
            symptom="run_trial.py could not parse .agent-bench.toml.",
            evidence=f"config={cfg_path}; error={e}",
            expected="The simplified TOML schema parses cleanly.",
            observed="tomllib rejected the file.",
            implication="The trial cannot safely infer its prompt, start ref, agent, or checks.",
            disposition="aborted",
        )
        die(f"invalid TOML in {cfg_path}: {e}")

    prompt_file = require_config_value(cfg, "prompt", repo)
    prompt_path = (repo / prompt_file) if not Path(prompt_file).is_absolute() else Path(prompt_file)
    if not prompt_path.exists():
        append_anomaly(
            repo,
            title="prompt file missing",
            step="preflight",
            severity="high",
            symptom="run_trial.py could not find the task prompt.",
            evidence=f"prompt={prompt_path}",
            expected="The task prompt exists and is readable.",
            observed="The configured prompt path does not exist.",
            implication="The agent would receive no task definition, so the trial is invalid.",
            disposition="aborted",
        )
        die(f"prompt file not found: {prompt_path}")
    prompt_text = prompt_path.read_text()
    task_name = prompt_path.stem

    outer_check = require_config_value(cfg, "outer_check", repo)
    inner_check = require_config_value(cfg, "inner_check", repo)

    # Resolve start point: explicit start_commit wins over start_branch.
    start_ref = cfg.get("start_commit") or cfg.get("start_branch") or "HEAD"
    rc, sha, err = run_capture(["git", "rev-parse", start_ref], cwd=repo)
    if rc != 0:
        append_anomaly(
            repo,
            title="start ref could not be resolved",
            step="preflight",
            severity="high",
            symptom="git rev-parse failed for the configured start ref.",
            evidence=f"start_ref={start_ref}; stderr={err.strip()}",
            expected="start_branch or start_commit resolves to a concrete commit.",
            observed="git could not resolve the configured ref.",
            implication="The worktree cannot be created from a stable baseline.",
            disposition="aborted",
        )
        die(f"could not resolve start ref '{start_ref}': {err.strip()}")
    start_sha = sha.strip()

    # Preflight: agent CLI present
    if not args.skip_agent and args.agent != "opencode" and shutil.which(args.agent) is None:
        append_anomaly(
            repo,
            title="agent CLI missing",
            step="preflight",
            severity="high",
            symptom="The requested agent executable is not available in PATH.",
            evidence=f"agent={args.agent}; PATH lookup failed",
            expected="The selected agent CLI is installed before trial launch.",
            observed="shutil.which returned no executable.",
            implication="The agent session cannot be started.",
            disposition="aborted",
        )
        die(f"{args.agent} CLI not found in PATH")

    # Preflight: clean repo
    rc, stdout, _ = run_capture(["git", "status", "--porcelain"], cwd=repo)
    if stdout.strip():
        append_anomaly(
            repo,
            title="target repo is dirty",
            step="preflight",
            severity="high",
            symptom="The target repo has uncommitted changes at launch.",
            evidence="git status --porcelain: " + stdout.strip().replace("\n", " | "),
            expected="The target repo is clean so the worktree starts from only the configured ref.",
            observed="Git reported uncommitted or untracked files.",
            implication="Stray changes could pollute the baseline and invalidate the comparison.",
            disposition="aborted",
        )
        die("target repo has uncommitted changes — commit or stash first")

    # Layout
    output_base = (args.output_base or (repo / "eval-results")).resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_base / task_name / args.agent / f"run-{args.run}-{timestamp}"
    branch = f"eval-{args.agent}-run{args.run}-{timestamp}"
    worktree = repo / f".worktree-eval-{args.agent}-run{args.run}"

    print("=" * 72)
    print(f"  ai-agent-bench  task={task_name}  agent={args.agent}  run={args.run}")
    print(f"  start={start_sha[:12]} ({start_ref})")
    print(f"  worktree={worktree}")
    print(f"  branch={branch}")
    print(f"  run_dir={run_dir}")
    print(f"  outer_check={outer_check}")
    print(f"  inner_check={inner_check}")
    print("=" * 72)

    run_dir.mkdir(parents=True, exist_ok=True)
    run_context = {
        "agent": args.agent,
        "run": args.run,
        "start_sha": start_sha,
        "run_dir": str(run_dir),
        "branch": branch,
        "prompt": str(prompt_path),
    }
    (run_dir / "start_commit.txt").write_text(start_sha + "\n")
    (run_dir / "branch_name.txt").write_text(branch + "\n")
    (run_dir / "config.json").write_text(
        json.dumps(
            {
                "task": task_name,
                "agent": args.agent,
                "run": args.run,
                "outer_check": outer_check,
                "inner_check": inner_check,
                "start_ref": start_ref,
                "start_sha": start_sha,
            },
            indent=2,
        )
        + "\n"
    )
    update_status(run_dir, "init")

    # Worktree
    update_status(run_dir, "worktree")
    print(f"\n[1/5] worktree at {start_sha[:12]} on {branch}...")
    run_capture(["git", "worktree", "prune"], cwd=repo)
    if worktree.exists():
        run_capture(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo)
        if worktree.exists():
            shutil.rmtree(worktree)
    rc, _, err = run_capture(
        ["git", "worktree", "add", "-b", branch, str(worktree), start_sha], cwd=repo
    )
    if rc != 0:
        append_anomaly(
            repo,
            title="worktree creation failed",
            step="worktree",
            severity="high",
            symptom="git worktree add failed before checks or agent launch.",
            evidence=f"branch={branch}; worktree={worktree}; stderr={err.strip()}",
            expected="The harness can create an isolated worktree from the start commit.",
            observed="git worktree add returned a non-zero exit code.",
            implication="The trial cannot isolate the agent diff from the user's working tree.",
            disposition="aborted",
            run_context=run_context,
        )
        die(f"git worktree add failed: {err.strip()}")
    print(f"  ✓ {worktree}")

    # Build resolved prompt — minimal note appended so the agent knows what's harness-owned
    resolved = prompt_text + (
        f"\n\n---\n"
        f"HARNESS NOTE (auto-appended by ai-agent-bench)\n\n"
        f"For fast iteration, use: `{inner_check}`\n"
        f"Do NOT run `{outer_check}` yourself — the orchestrator runs it once before "
        f"your session and once after, on clean conditions.\n"
    )
    (run_dir / "prompt_resolved.md").write_text(resolved)

    def cleanup() -> None:
        if worktree.exists():
            print(f"\n  cleanup: removing worktree {worktree} (branch {branch} preserved)")
            rc, _, _ = run_capture(
                ["git", "worktree", "remove", "--force", str(worktree)], cwd=repo
            )
            if rc != 0 and worktree.exists():
                shutil.rmtree(worktree, ignore_errors=True)

    def handle_signal(signum, _frame):
        cleanup()
        sys.exit(128 + signum)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    monitor = spawn_monitor(run_dir)
    if monitor is None:
        append_anomaly(
            repo,
            title="monitor sidecar missing",
            step="monitor",
            severity="medium",
            symptom="run_trial.py could not spawn monitor.py.",
            evidence=f"expected_monitor={SCRIPT_DIR / 'monitor.py'}",
            expected="monitor.py exists and writes progress.md every 3 minutes.",
            observed="The monitor script was missing.",
            implication="The trial can continue, but heartbeat visibility is degraded.",
            disposition="logged and continuing",
            run_context=run_context,
        )
    exit_code = 0
    try:
        # outer_check pre
        if not args.skip_pre:
            update_status(run_dir, "outer_pre")
            print("\n[2/5] outer_check (pre)...")
            stats = run_outer_check(outer_check, cwd=worktree, log_path=run_dir / "outer_pre.log")
            (run_dir / "outer_pre.json").write_text(json.dumps(stats, indent=2) + "\n")
            print(f"  exit={stats['exit_code']}, wall_s={stats['wall_s']}")
            if stats["exit_code"] != 0:
                append_anomaly(
                    repo,
                    title="outer_check failed before agent session",
                    step="outer_pre",
                    severity="high",
                    symptom="The orchestrator-owned live e2e check failed before the agent ran.",
                    evidence=(
                        f"cmd={outer_check}; exit={stats['exit_code']}; "
                        f"wall_s={stats['wall_s']}; log={run_dir / 'outer_pre.log'}"
                    ),
                    expected="outer_check exits 0 on the baseline worktree.",
                    observed=f"outer_check exited {stats['exit_code']} before the agent session.",
                    implication="There is no valid reference benchmark, so launching the agent would contaminate the trial.",
                    disposition="aborted",
                    run_context=run_context,
                )
                update_status(run_dir, "done")
                return 3

        # Agent
        agent_exit = 0
        if not args.skip_agent:
            update_status(run_dir, "agent:running")
            print(f"\n[3/5] agent: {args.agent}...")
            agent_exit, agent_wall = run_agent(args.agent, resolved, worktree, run_dir)
            (run_dir / "agent_exit_code.txt").write_text(str(agent_exit) + "\n")
            (run_dir / "agent_wall_seconds.txt").write_text(str(agent_wall) + "\n")
            print(f"  exit={agent_exit}, wall={agent_wall}s")
        else:
            (run_dir / "session.jsonl").write_text("")

        # Diff + snapshot commit
        update_status(run_dir, "diff")
        print("\n[4/5] diff + snapshot commit...")
        run_capture(["git", "add", "-A"], cwd=worktree)
        _, diff_patch, _ = run_capture(["git", "diff", start_sha, "--staged"], cwd=worktree)
        (run_dir / "diff.patch").write_text(diff_patch)
        _, diff_stat, _ = run_capture(
            ["git", "diff", start_sha, "--staged", "--stat"], cwd=worktree
        )
        (run_dir / "diff_stat.txt").write_text(diff_stat)
        rc, _, _ = run_capture(["git", "diff", "--cached", "--quiet"], cwd=worktree)
        if rc != 0:
            run_capture(
                [
                    "git",
                    "-c",
                    "user.name=agent-eval",
                    "-c",
                    "user.email=agent-eval@local",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "--no-verify",
                    "-m",
                    f"eval: {args.agent} run-{args.run} snapshot ({timestamp})",
                ],
                cwd=worktree,
            )
            print(f"  ✓ snapshot committed on {branch}")
        else:
            print("  - no changes; no snapshot")

        # Skip post if agent failed
        if agent_exit != 0:
            update_status(run_dir, "agent_failed")
            print(f"\n  agent exit {agent_exit} — skipping outer_check post")
            (run_dir / "run_status.txt").write_text("failed_agent_session\n")
            append_anomaly(
                repo,
                title="agent session failed",
                step="agent",
                severity="high",
                symptom="The inner AI agent exited non-zero.",
                evidence=(
                    f"agent={args.agent}; exit={agent_exit}; "
                    f"stderr={run_dir / 'stderr.log'}; session={run_dir / 'session.jsonl'}"
                ),
                expected="The selected agent completes its task session and exits 0.",
                observed=f"The agent process exited {agent_exit}.",
                implication="Post-run e2e timing would be misleading, so the harness skipped it.",
                disposition="aborted",
                run_context=run_context,
            )
            update_status(run_dir, "done")
            return agent_exit

        # outer_check post
        if not args.skip_post:
            update_status(run_dir, "outer_post")
            print("\n[5/5] outer_check (post)...")
            stats = run_outer_check(outer_check, cwd=worktree, log_path=run_dir / "outer_post.log")
            (run_dir / "outer_post.json").write_text(json.dumps(stats, indent=2) + "\n")
            print(f"  exit={stats['exit_code']}, wall_s={stats['wall_s']}")
            if stats["exit_code"] != 0:
                append_anomaly(
                    repo,
                    title="outer_check failed after agent session",
                    step="outer_post",
                    severity="high",
                    symptom="The orchestrator-owned live e2e check failed after the agent ran.",
                    evidence=(
                        f"cmd={outer_check}; exit={stats['exit_code']}; "
                        f"wall_s={stats['wall_s']}; log={run_dir / 'outer_post.log'}"
                    ),
                    expected="outer_check exits 0 after the agent's changes.",
                    observed=f"outer_check exited {stats['exit_code']} after the agent session.",
                    implication="The agent branch is a behavioral regression unless manual review proves the check is faulty.",
                    disposition="logged and continuing",
                    run_context=run_context,
                )

        # Parse
        update_status(run_dir, "parse")
        print("\n[parse] aggregating metrics...")
        parse = SCRIPT_DIR / "parse_transcript.py"
        p = subprocess.run(
            [
                sys.executable,
                str(parse),
                "--agent",
                args.agent,
                "--run-dir",
                str(run_dir),
                "--output",
                str(run_dir / "metrics.json"),
                "--render-report",
                str(run_dir / "report.md"),
            ],
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            print(f"  ✗ parse failed: {p.stderr.strip()}")
            append_anomaly(
                repo,
                title="metrics parser failed",
                step="parse",
                severity="medium",
                symptom="parse_transcript.py failed while aggregating the run artifacts.",
                evidence=f"exit={p.returncode}; stderr={p.stderr.strip()}",
                expected="metrics.json and report.md are produced from the saved artifacts.",
                observed="The parser returned a non-zero exit code.",
                implication="The raw trial artifacts still exist, but categorized metrics are incomplete.",
                disposition="logged and continuing",
                run_context=run_context,
            )
            exit_code = 1
        else:
            print("  ✓ metrics.json + report.md written")
            try:
                metrics = json.loads((run_dir / "metrics.json").read_text())
                dup_count = (
                    (metrics.get("session") or {})
                    .get("trajectory", {})
                    .get("harness_duplications_count", 0)
                )
                if dup_count:
                    append_anomaly(
                        repo,
                        title="agent invoked outer_check",
                        step="parse",
                        severity="medium",
                        symptom="The inner agent ran a command owned by the orchestrator.",
                        evidence=f"harness_duplications_count={dup_count}; metrics={run_dir / 'metrics.json'}",
                        expected="The agent uses inner_check only; outer_check runs once before and once after by the orchestrator.",
                        observed="The transcript contains at least one outer_check command invocation.",
                        implication="Agent wall time and system load may be inflated, weakening timing comparisons.",
                        disposition="logged and continuing",
                        run_context=run_context,
                    )
            except (json.JSONDecodeError, OSError):
                pass

        update_status(run_dir, "done")

    finally:
        kill_monitor(monitor)
        cleanup()

    print("\n" + "=" * 72)
    print("  TRIAL COMPLETE")
    print(f"  run_dir: {run_dir}")
    print(f"  branch:  {branch}  (preserved — git checkout {branch} to inspect)")
    if (run_dir / "outer_post.json").exists():
        post = json.loads((run_dir / "outer_post.json").read_text())
        print(f"  outer_check post: exit={post['exit_code']}, wall_s={post['wall_s']}")
    print("=" * 72)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
