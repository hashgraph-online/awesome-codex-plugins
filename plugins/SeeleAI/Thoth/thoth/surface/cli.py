"""Canonical `$thoth` CLI surface."""

from __future__ import annotations

import argparse
from pathlib import Path

from thoth.run.model import default_executor
from .handlers import handle_command


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thoth")
    public_commands = "{init,discuss,run,loop,review,auto,status,doctor,dashboard}"
    sub = parser.add_subparsers(dest="command", required=True, metavar=public_commands)

    def add_internal_parser(name: str) -> argparse.ArgumentParser:
        internal = sub.add_parser(name, help=argparse.SUPPRESS)
        sub._choices_actions = [action for action in sub._choices_actions if action.dest != name]
        return internal

    run_parser = sub.add_parser("run")
    run_parser.add_argument("--work-id")
    run_parser.add_argument("--host", default="codex")
    run_parser.add_argument("--executor")
    run_parser.add_argument("--sleep", action="store_true")
    run_parser.add_argument("--attach")
    run_parser.add_argument("--watch")
    run_parser.add_argument("--stop")

    loop_parser = sub.add_parser("loop")
    loop_parser.add_argument("--goal", default="loop")
    loop_parser.add_argument("--work-id")
    loop_parser.add_argument("--host", default="codex")
    loop_parser.add_argument("--executor")
    loop_parser.add_argument("--sleep", action="store_true")
    loop_parser.add_argument("--attach")
    loop_parser.add_argument("--resume")
    loop_parser.add_argument("--watch")
    loop_parser.add_argument("--stop")

    orchestration_parser = add_internal_parser("orchestration")
    orchestration_parser.add_argument("--work-id", action="append", dest="work_ids", default=[])
    orchestration_parser.add_argument("--host", default="codex")
    orchestration_parser.add_argument("--executor", default=default_executor())

    auto_parser = sub.add_parser("auto")
    auto_parser.add_argument("--work-id", action="append", dest="work_ids", default=[])
    auto_parser.add_argument("--mode", choices=("loop",), default="loop")
    auto_parser.add_argument("--scope", choices=("all-open", "ready", "priority-top"), default="all-open")
    auto_parser.add_argument("--rounds", type=int)
    auto_parser.add_argument("--min-runtime-seconds", type=int, default=8 * 60 * 60)
    auto_parser.add_argument("--host", default="codex")
    auto_parser.add_argument("--executor", default=default_executor())
    auto_parser.add_argument("--sleep", action="store_true")
    auto_parser.add_argument("--watch")
    auto_parser.add_argument("--stop")
    auto_parser.add_argument("--follow", action="store_true")
    auto_parser.add_argument("--stream-json", action="store_true")
    auto_parser.add_argument("--monitor-packet", action="store_true")

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--json", action="store_true")
    status_parser.add_argument("--doctor", action="store_true")
    status_parser.add_argument("--version", action="store_true")
    status_parser.add_argument("--report", action="store_true")
    status_parser.add_argument("--dashboard", nargs="?", const="start", choices=("start", "stop", "rebuild"))
    status_parser.add_argument("--fix", nargs="?", const="requested", choices=("preview", "apply", "requested"))
    status_parser.add_argument("--preview", action="store_true")
    status_parser.add_argument("--apply", action="store_true")

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--config-json")
    init_parser.add_argument("--sync", action="store_true")
    init_parser.add_argument("--migrate", nargs="?", const="requested", choices=("preview", "apply", "requested"))
    init_parser.add_argument("--preview", action="store_true")
    init_parser.add_argument("--apply", action="store_true")

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--quick", action="store_true")
    doctor.add_argument("--version", action="store_true")
    doctor.add_argument("--fix", nargs="?", const="requested", choices=("preview", "apply", "requested"))
    doctor.add_argument("--preview", action="store_true")
    doctor.add_argument("--apply", action="store_true")
    doctor.add_argument("--json", action="store_true")

    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("action", nargs="?", default="start", choices=("start", "stop", "rebuild"))

    add_internal_parser("sync")

    report = add_internal_parser("report")
    report.add_argument("--format", choices=("md", "json"), default="md")

    discuss = sub.add_parser("discuss")
    discuss.add_argument("--goal")
    discuss.add_argument("--decision-json")
    discuss.add_argument("--work-json")
    discuss.add_argument("rest", nargs="*")

    record_discussion = add_internal_parser("record-discussion-authority")
    record_discussion.add_argument("--project-root", required=True)
    record_discussion.add_argument("--discussion-id", required=True)
    record_discussion.add_argument("--mode", required=True, choices=("draft", "close"))
    record_discussion.add_argument("--authority-json-file", required=True)

    extend = add_internal_parser("extend")
    extend.add_argument("changed", nargs="*")

    review = sub.add_parser("review")
    review.add_argument("--goal")
    review.add_argument("--work-id")
    review.add_argument("--host", default="codex")
    review.add_argument("--executor")
    review.add_argument("rest", nargs="*")

    hook = add_internal_parser("hook")
    hook.add_argument("--host", required=True, choices=("claude", "codex"))
    hook.add_argument("--event", required=True, choices=("start", "end", "stop"))

    supervise = add_internal_parser("supervise")
    supervise.add_argument("--project-root", required=True)
    supervise.add_argument("--run-id", required=True)

    worker = add_internal_parser("worker")
    worker.add_argument("--project-root", required=True)
    worker.add_argument("--run-id", required=True)

    auto_worker = add_internal_parser("auto-worker")
    auto_worker.add_argument("--project-root", required=True)
    auto_worker.add_argument("--controller-id", required=True)

    prepare = add_internal_parser("prepare")
    prepare.add_argument("--project-root")
    prepare.add_argument("--command-id", required=True, choices=("run", "loop", "review"))
    prepare.add_argument("--work-id")
    prepare.add_argument("--goal")
    prepare.add_argument("--target")
    prepare.add_argument("--host", default="codex")
    prepare.add_argument("--executor")
    prepare.add_argument("--sleep", action="store_true")

    append_event = add_internal_parser("append-event")
    append_event.add_argument("--project-root", required=True)
    append_event.add_argument("--run-id", required=True)
    append_event.add_argument("--message", required=True)
    append_event.add_argument("--kind", default="log")
    append_event.add_argument("--level", default="info")
    append_event.add_argument("--phase")
    append_event.add_argument("--progress", type=int)
    append_event.add_argument("--payload-json")

    record = add_internal_parser("record-artifact")
    record.add_argument("--project-root", required=True)
    record.add_argument("--run-id", required=True)
    record.add_argument("--path", required=True)
    record.add_argument("--label")
    record.add_argument("--kind", default="file")
    record.add_argument("--metadata-json")

    heartbeat = add_internal_parser("heartbeat")
    heartbeat.add_argument("--project-root", required=True)
    heartbeat.add_argument("--run-id", required=True)
    heartbeat.add_argument("--phase")
    heartbeat.add_argument("--progress", type=int)
    heartbeat.add_argument("--note")

    next_phase = add_internal_parser("next-phase")
    next_phase.add_argument("--project-root", required=True)
    next_phase.add_argument("--run-id", required=True)

    submit_phase = add_internal_parser("submit-phase")
    submit_phase.add_argument("--project-root", required=True)
    submit_phase.add_argument("--run-id", required=True)
    submit_phase.add_argument("--phase", required=True)
    submit_phase.add_argument("--output-json", required=True)

    complete = add_internal_parser("complete")
    complete.add_argument("--project-root", required=True)
    complete.add_argument("--run-id", required=True)
    complete.add_argument("--summary", required=True)
    complete.add_argument("--result-json")
    complete.add_argument("--checks-json")

    fail = add_internal_parser("fail")
    fail.add_argument("--project-root", required=True)
    fail.add_argument("--run-id", required=True)
    fail.add_argument("--summary", required=True)
    fail.add_argument("--reason")
    fail.add_argument("--result-json")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_cli_parser()
    args, extras = parser.parse_known_args(argv)
    if extras:
        if args.command in {"run", "loop"}:
            free_text = [token for token in extras if not token.startswith("-")]
            unknown_flags = [token for token in extras if token.startswith("-")]
            if unknown_flags:
                parser.error(f"unrecognized arguments: {' '.join(extras)}")
            setattr(args, "prompt_query", " ".join(free_text).strip())
            extras = []
        else:
            parser.error(f"unrecognized arguments: {' '.join(extras)}")
    elif args.command in {"run", "loop"}:
        setattr(args, "prompt_query", "")
    return handle_command(args, parser, project_root=Path.cwd())
