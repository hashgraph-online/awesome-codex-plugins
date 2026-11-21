"""``util improve-cascade next``: a cascade's planner and recorder on the native leg.

``--cascade`` runs one review-then-apply round per model, one model after the
other (``utils/improve_cascade.py``). On the native leg (the instruction
cores) ``util improve-steps`` stays read-only: when a cascade decides the run
it prints ``[IMPROVE_CASCADE_NEXT] <this util's command>`` in place of a step
block, and the core runs that command once. Each call here is the cascade's
one writer, ``improve_cascade.advance``, followed by the current stage's step
block, printed with the very functions ``util improve-steps`` prints with
(``improve_steps.build_plan`` and ``render_text`` on the stage's derived
namespace), so a stage's flags lines are the ones the executor leg forwards::

    <advance's notices: [IMPROVE_CASCADE] …, [CASCADE_STAGE_SKIPPED] …, NOTE: …, [AUTO_RESOLVED] …>
    [IMPROVE_CASCADE] stage <k> of <n>: <model>
    [IMPROVE_STEP] … / [IMPROVE_STEP_FRESH] … / [IMPROVE_STEP_FLAGS] …   (step 1b: skip (cascade))
    [IMPROVE_CASCADE_CONTINUE] <util improve-cascade next <plan> --mode … --host … --cascade-id <id> --after-stage <k>>
    [IMPROVE_RERUN] <the user's continuation, with --cascade>

The first call (from ``[IMPROVE_CASCADE_NEXT]``, no ``--cascade-id``) carries
the flags the user typed and may start, continue or restart a cascade, or
abandon one (``--force`` without ``--cascade``: today's plain step block
follows, with the plain ``[IMPROVE_RERUN]`` and no continue line, so the core
runs one round). Each ``[IMPROVE_CASCADE_CONTINUE]`` call is bound to the
cascade's id and to the stage it follows (``--after-stage <k>``), and carries
no restart or selector flag: it closes out the stage just run and hands out
the next one, or stops at exit 3: ``[CASCADE_CONFLICT]`` when the pointer
names another cascade, and ``improve_cascade.StageNotFinished`` when stage
<k> is still open (its steps stopped before it was done), so a call never
prints the block it was called after.

Exit codes: 0 a stage to run (or the plain block after an abandon); 2
``[CASCADE_COMPLETE] <n> stages; table: <summary.md>`` once every stage is
closed (or ``[ALREADY_COMPLETE]`` for a plain block with nothing to do); 3 a
refusal (row 15, ``--interactive``, an unknown host, a live run, a
``state.json`` or cascade record it cannot read, ``[CASCADE_CONFLICT]``, an
archive it cannot trust) or a continue call's stop at its stage (the last
stage's review produced no result, or the stage it follows did not finish),
which prints the stop on stderr and the user's ``[IMPROVE_RERUN]`` on stdout;
1 a plan not found or a scope it cannot read.
Every other refusal prints nothing on stdout. ``--json`` prints the
``util improve-steps`` object plus a ``cascade`` key.

The contract, its tables and its history: docs/development/workflows.md,
"A cascade (``--cascade``)".
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from . import host_capabilities
from . import improve_cascade as ic
from . import improve_steps as steps_mod
from . import improve_workflow as iw
from . import unattended as unattended_mod
from .cli_common import (
    EXIT_ERROR,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    build_parent_parser,
    dispatcher_command,
    dispatcher_prefix,
)
from .improve_cascade import CASCADE_MARKER
from .improve_steps import ALREADY_COMPLETE_MARKER, RERUN_MARKER
from .stream_bootstrap import bootstrap_streams
from .text_clip import plain_line

#: The util's word and its one command.
UTIL, COMMAND = steps_mod.CASCADE_UTIL

#: The composites a cascade runs on: improve-steps' modes that take ``--cascade``.
MODES: Tuple[str, ...] = tuple(mode for mode in steps_mod.MODES if iw.takes_cascade(mode))

#: The cascade composite whose flags hold every other's (improve-code's scope
#: flags beside improve-plan's), for a parse with no ``--mode`` to go by.
_WIDEST_MODE = next(mode for mode in MODES if iw._reviews_code(mode))

#: The command that hands out the next stage, bound to the cascade's id.
CONTINUE_MARKER = "[IMPROVE_CASCADE_CONTINUE]"
#: Every stage is closed: the line names the stage count and the per-round table.
COMPLETE_MARKER = "[CASCADE_COMPLETE]"

CASCADE_ID_FLAG = "--cascade-id"
#: A continue call's stage: the one the call that printed it handed out.
AFTER_STAGE_FLAG = "--after-stage"

#: The ``--json`` object: ``util improve-steps``' keys, then ``cascade``.
JSON_KEYS: Tuple[str, ...] = steps_mod.JSON_KEYS + ("cascade",)
#: The ``cascade`` object's keys (``null`` for a call that ran no cascade).
#: *state*: ``stage`` (a stage to run), ``complete`` or ``stopped`` (a
#: continue call's stop at its stage: the last stage's review produced no
#: result, or the stage it follows did not finish).
CASCADE_KEYS: Tuple[str, ...] = (
    "state", "cascade_id", "stage", "of", "model", "continue", "continue_argv", "summary",
)


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """``util improve-cascade``'s own parser: the one command, for ``--help``."""
    run = dispatcher_prefix()
    plan = "plans/my-plan.md"
    parser = argparse.ArgumentParser(
        prog=f"multi_llm.py util {UTIL}",
        description=(
            "Plan and record an --improve-plan or --improve-code --cascade run on "
            "the native leg, one stage per call. `util improve-steps` hands off "
            f"to it with [IMPROVE_CASCADE_NEXT]; `{UTIL} {COMMAND} --help` lists "
            "its flags."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "",
            "Examples:",
            f"  {run} util {UTIL} {COMMAND} {plan} --mode improve-plan --host claude-code "
            "--cascade --models m1 m2",
            f"  {run} util {UTIL} {COMMAND} {plan} --mode improve-plan --host claude-code "
            f"{CASCADE_ID_FLAG} <id> {AFTER_STAGE_FLAG} 1",
        ]) + "\n",
    )
    commands = parser.add_subparsers(dest="command", title="commands", metavar="COMMAND",
                                     required=True)
    commands.add_parser(
        COMMAND, add_help=False,
        help="Close out the stage just run, then print the next stage's steps "
             "(or [CASCADE_COMPLETE]).",
    )
    return parser


def build_next_parser(mode: Optional[str] = None) -> argparse.ArgumentParser:
    """``next``'s parser: improve-steps' flags for *mode*, plus ``--cascade-id``.

    The same parent parser and the same composite flags
    (``improve_steps._add_composite_flags``), so ``advance`` and the step
    functions read the namespace ``util improve-steps`` built from the same
    tokens. *mode* ``None`` (no ``--mode`` typed, or not a cascade
    composite) takes improve-code's set, which holds improve-plan's.
    """
    run = dispatcher_prefix()
    plan = "plans/my-plan.md"
    epilog = "\n".join([
        "",
        "Prints the notices, then one block per step of the current stage, as",
        "`util improve-steps` prints them (step 1b reads skip (cascade)), then:",
        f"  {CONTINUE_MARKER} <command>  run it once the stage's last step is done",
        f"  {RERUN_MARKER} <command>  the user's continuation, with --cascade",
        "",
        f"The first call has no {CASCADE_ID_FLAG}: it carries the flags the user",
        "typed and may start, continue or restart the cascade. A continue call",
        f"carries {CASCADE_ID_FLAG}, {AFTER_STAGE_FLAG} <k> (the stage it follows)",
        "and no selector; a [CASCADE_CONFLICT] refuses it when the cascade is no",
        "longer the current one, and it stops at exit 3 when stage <k> is still",
        "open, never printing that stage's block again.",
        "The scope flags (--files, --files-from, --base-ref) are improve-code's.",
        "",
        f"--json prints `util improve-steps`' object plus cascade ({', '.join(CASCADE_KEYS)}).",
        "",
        "exit codes: 0 a stage to run | 2 [CASCADE_COMPLETE] (every stage closed) |",
        "3 a refusal, or a continue call's stage stopped: the last stage's review",
        "produced no result, or the stage it follows did not finish (the stop on",
        f"stderr, {RERUN_MARKER} on stdout) | 1 the plan is missing or the scope",
        "cannot be read.",
        "",
        "Examples:",
        f"  {run} util {UTIL} {COMMAND} {plan} --mode improve-code --host claude-code "
        "--cascade --files src/app.py",
        f"  {run} util {UTIL} {COMMAND} {plan} --mode improve-plan --host claude-code "
        f"{CASCADE_ID_FLAG} <id> {AFTER_STAGE_FLAG} 2 --json",
    ]) + "\n"
    parser = argparse.ArgumentParser(
        prog=f"multi_llm.py util {UTIL} {COMMAND}",
        description=(
            "Advance an --improve-plan or --improve-code --cascade run: close out "
            "the stage just run, start the next, and print its steps with their "
            "exact flags. The cascade's only writer on the native leg."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[build_parent_parser()],
        epilog=epilog,
    )
    parser.add_argument("plan", help="The plan, as the user typed it.")
    parser.add_argument("--mode", required=True, choices=MODES,
                        help="The composite the cascade runs.")
    parser.add_argument(
        "--json", action="store_true", dest="json",
        help="Print the stage as one JSON object instead of the text block.",
    )
    parser.add_argument(
        CASCADE_ID_FLAG, dest="cascade_id", default=None, metavar="ID",
        help="A continue call: the cascade the previous call named. Never "
             "starts or restarts one.",
    )
    parser.add_argument(
        AFTER_STAGE_FLAG, dest="after_stage", default=None, type=int, metavar="K",
        help=f"With {CASCADE_ID_FLAG}: the stage the previous call handed out. "
             "Still open, the call stops at exit 3 instead of printing it again.",
    )
    steps_mod._add_composite_flags(parser, mode if mode in MODES else _WIDEST_MODE)
    return parser


def parse_next_args(argv: Sequence[str]) -> argparse.Namespace:
    argv = list(argv)
    parser = build_next_parser(steps_mod._typed_mode(argv))
    args = parser.parse_args(argv)
    if args.after_stage is not None and args.cascade_id is None:
        parser.error(f"{AFTER_STAGE_FLAG} goes with {CASCADE_ID_FLAG}: only a continue "
                     "call follows a stage")
    return args


# ---------------------------------------------------------------------------
# What each answer prints
# ---------------------------------------------------------------------------

def continue_argv(
    args: argparse.Namespace, host_id: str, cascade_id: str, stage: int,
) -> List[str]:
    """The tokens after ``util improve-cascade``: the plan, the mode, the host, the id, the stage.

    *stage* is the stage this call hands out, which the continue call
    follows (``--after-stage``): if it is still open then, that call stops
    instead of printing it again. No restart flag (``--force``, ``--cascade``) and no selector (models,
    files, base ref, scope policy: the record holds them), only the tokens
    a host's dispatcher command bakes in, as ``util improve-steps``' own
    command carries them (``--yes``, ``--exec-subagents``,
    ``--dry-run-subagents``), and ``--json`` when this call was asked for it.
    """
    tokens = [COMMAND, args.plan, "--mode", args.mode, "--host", host_id,
              CASCADE_ID_FLAG, cascade_id, AFTER_STAGE_FLAG, str(int(stage))]
    if getattr(args, "yes", False):
        tokens.append("--yes")
    tokens += iw.cross_cutting_flags(args, include_host=False)
    if getattr(args, "json", False):
        tokens.append("--json")
    return tokens


def _cascade_object(state: str, *, cascade_id: Optional[str], stage: Optional[int],
                    of: Optional[int], model: Optional[str], summary: Optional[Path],
                    continue_tokens: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "state": state,
        "cascade_id": cascade_id,
        "stage": stage,
        "of": of,
        "model": model,
        "continue": (dispatcher_command("util", UTIL, *continue_tokens)
                     if continue_tokens else None),
        "continue_argv": list(continue_tokens) if continue_tokens else None,
        "summary": None if summary is None else str(summary),
    }


def _emit(plan: "steps_mod.StepsPlan", cascade: Optional[Dict[str, Any]],
          as_json: bool, text: str) -> None:
    if as_json:
        payload = steps_mod.as_json(plan)
        payload["cascade"] = cascade
        print(json.dumps(payload, indent=2))
    else:
        print(text)


def _split_already_complete(notices: Sequence[str]) -> Tuple[Optional[str], Tuple[str, ...]]:
    """A finished cascade's ``[ALREADY_COMPLETE]`` notice, apart from the others."""
    for index, line in enumerate(notices):
        if line.startswith(ALREADY_COMPLETE_MARKER):
            rest = tuple(notices[:index]) + tuple(notices[index + 1:])
            return line[len(ALREADY_COMPLETE_MARKER):].strip(), rest
    return None, tuple(notices)


def _stage_records(mode: str, plan_path: Path, stage_args: argparse.Namespace):
    """The records read for the stage's namespace, or the exit code of a refusal."""
    try:
        return iw.read_records(mode, plan_path, stage_args), None
    except iw.StateReadError as exc:
        return None, unattended_mod.fail_closed(iw.state_read_error_line(mode, exc))
    except ValueError as exc:
        if not iw.is_scope_files_error(exc):
            raise
        print(iw.scope_error_line(exc), file=sys.stderr)
        return None, EXIT_ERROR


def print_stage(
    mode: str, args: argparse.Namespace, stage: "ic.StagePlan", plan_path: Path,
    host_id: str,
) -> int:
    """A stage to run: notices, the stage line, its step block, continue, then rerun."""
    records, refused = _stage_records(mode, plan_path, stage.stage_args)
    if refused is not None:
        return refused
    built = steps_mod.build_plan(
        mode, stage.stage_args, records, finished=False, plan_path=plan_path,
        host_id=host_id,
    )
    rerun, rerun_argv = steps_mod.user_continuation(
        mode, args, plan_path, host_id, cascade=True)
    tokens = continue_argv(args, host_id, stage.cascade_id, stage.stage)
    head = [plain_line(n) for n in stage.notices]
    head.append(f"{CASCADE_MARKER} stage {stage.stage} of {stage.of}: {stage.model}")
    lines = head + [steps_mod.render_text(dataclasses.replace(built, rerun=None,
                                                              rerun_argv=None))]
    lines.append(f"{CONTINUE_MARKER} {dispatcher_command('util', UTIL, *tokens)}")
    lines.append(f"{RERUN_MARKER} {rerun}")
    plan = dataclasses.replace(built, notices=tuple(head) + built.notices, rerun=rerun,
                               rerun_argv=rerun_argv)
    cascade = _cascade_object("stage", cascade_id=stage.cascade_id, stage=stage.stage,
                              of=stage.of, model=stage.model, summary=stage.summary_path,
                              continue_tokens=tokens)
    _emit(plan, cascade, args.json, "\n".join(lines))
    return EXIT_OK


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def complete_line(done: "ic.Complete") -> str:
    """``[CASCADE_COMPLETE] <n> stages; table: <summary.md>``."""
    return (f"{COMPLETE_MARKER} {_plural(done.of, 'stage')}; "
            f"table: {iw._display_path(done.summary_path)}")


def print_complete(args: argparse.Namespace, done: "ic.Complete") -> int:
    """Every stage closed: the notices, then ``[CASCADE_COMPLETE]``; exit 2."""
    notices = [plain_line(n) for n in done.notices]
    line = complete_line(done)
    already, others = _split_already_complete(notices)
    plan = steps_mod.StepsPlan(
        mode=args.mode, plan=args.plan, already_complete=already,
        notices=others + (line,), steps=(), rerun=None, rerun_argv=None,
    )
    cascade = _cascade_object("complete", cascade_id=done.cascade_id, stage=None,
                              of=done.of, model=None, summary=done.summary_path)
    _emit(plan, cascade, args.json, "\n".join(notices + [line]))
    return EXIT_NOTHING_TO_DO


def print_stopped(
    mode: str, args: argparse.Namespace,
    exc: "Union[ic.LastStageStopped, ic.StageNotFinished]", plan_path: Path, host_id: str,
) -> int:
    """A continue call's stop at its stage, and the way to take the stage up again.

    *exc* is :class:`~utils.improve_cascade.LastStageStopped` (the last
    stage's review produced no result: the user's command starts it over)
    or :class:`~utils.improve_cascade.StageNotFinished` (the stage the call
    follows is still open: the user's command continues it once its stop is
    dealt with). The stop is printed whole on stderr (exit 3, the result
    marked needs-human); the user's continuation, with ``--cascade``, on
    stdout, so the report check holds the report to this call's
    ``[IMPROVE_RERUN]``.
    """
    code = unattended_mod.fail_closed(exc.message)
    rerun, rerun_argv = steps_mod.user_continuation(
        mode, args, plan_path, host_id, cascade=True)
    plan = steps_mod.StepsPlan(
        mode=mode, plan=args.plan, already_complete=None, notices=(), steps=(),
        rerun=rerun, rerun_argv=rerun_argv,
    )
    cascade = _cascade_object("stopped", cascade_id=exc.cascade_id, stage=exc.stage,
                              of=exc.of, model=exc.model,
                              summary=_summary_of(plan_path, mode))
    _emit(plan, cascade, args.json, f"{RERUN_MARKER} {rerun}")
    return code


def _summary_of(plan_path: Path, mode: str) -> Optional[Path]:
    """The current cascade's ``summary.md`` path (written or not), or ``None``."""
    try:
        status = ic.cascade_status(plan_path, mode)
    except ic.CascadeRefusal:
        return None
    return None if status is None else Path(status["dir"]) / ic.SUMMARY_NAME


def print_plain(
    mode: str, args: argparse.Namespace, notices: Sequence[str], plan_path: Path,
    host_id: str,
) -> int:
    """No cascade runs: the notices, then today's step block for the user's own flags.

    ``improve_workflow.preflight`` again, now that no cascade decides the run
    (the abandoned one's pointer is gone): ``[ALREADY_COMPLETE]`` (exit 2),
    or ``--files-from -`` for a review that runs (exit 1), as ``util
    improve-steps`` answers them.
    """
    read: Dict[str, "iw.Records"] = {}

    def records() -> "iw.Records":
        if "records" not in read:
            read["records"] = iw.read_records(mode, plan_path, args)
        return read["records"]

    outcome = iw.preflight(mode, plan_path, args, records, skip_own_run_dir=False,
                           detached=True)
    finished = outcome is iw.FINISHED
    if outcome is not None and not finished:
        if isinstance(outcome, iw.CascadeFinished):  # pragma: no cover - no cascade decides now
            print(outcome.line)
            return outcome.code
        return int(outcome)
    built = steps_mod.build_plan(mode, args, records(), finished=finished,
                                 plan_path=plan_path, host_id=host_id)
    head = tuple(plain_line(n) for n in notices)
    plan = dataclasses.replace(built, notices=head + built.notices)
    _emit(plan, None, args.json, steps_mod.render_text(plan))
    return EXIT_NOTHING_TO_DO if finished else EXIT_OK


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def next_main(argv: Sequence[str]) -> int:
    """``util improve-cascade next <plan> --mode … --host … <typed flags> [--cascade-id <id> --after-stage <k>]``.

    In order, as ``util improve-steps`` checks: row 15 on the raw argv; the
    parse; the ``--interactive`` refusal; an unknown ``--host``; the plan
    exists; ``improve_workflow.safety_checks`` (a live owner, the records, a
    scope it cannot read). Then ``improve_cascade.advance``, initial when no
    ``--cascade-id`` was typed, and what its answer prints.
    """
    argv = list(argv)
    try:
        unattended_mod.validate_decision_flags(argv)
    except unattended_mod.NeedsHuman as exc:
        return unattended_mod.fail_closed(exc.message)
    args = parse_next_args(argv)
    mode = args.mode
    if getattr(args, "interactive", False):
        return unattended_mod.fail_closed(iw.interactive_refusal(mode))

    host_id = host_capabilities.resolve_host_id(explicit=args.host)
    try:
        host_capabilities.entry(host_id)
    except unattended_mod.NeedsHuman as exc:
        return unattended_mod.fail_closed(exc.message)

    plan_path = Path(os.path.abspath(args.plan))
    if not plan_path.is_file():
        print(f"ERROR: Plan file not found: {args.plan}", file=sys.stderr)
        print(f"       Resolved path: {plan_path}", file=sys.stderr)
        return EXIT_ERROR

    refused = iw.safety_checks(mode, plan_path, lambda: iw.read_records(mode, plan_path, args),
                               skip_own_run_dir=False)
    if refused is not None:
        return refused

    initial = args.cascade_id is None
    try:
        outcome = ic.advance(plan_path, mode, args, initial=initial,
                             cascade_id=args.cascade_id, after_stage=args.after_stage)
    except (ic.LastStageStopped, ic.StageNotFinished) as exc:
        return print_stopped(mode, args, exc, plan_path, host_id)
    except ic.CascadeRefusal as exc:
        return ic.refusal_exit(exc)
    if isinstance(outcome, ic.StagePlan):
        return print_stage(mode, args, outcome, plan_path, host_id)
    if isinstance(outcome, ic.Complete):
        return print_complete(args, outcome)
    return print_plain(mode, args, outcome.notices, plan_path, host_id)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """``util improve-cascade next …``; ``util improve-cascade --help`` names the command."""
    bootstrap_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == COMMAND:
        return next_main(argv[1:])
    build_parser().parse_args(argv)
    return EXIT_ERROR  # pragma: no cover - argparse exits on every other argv


if __name__ == "__main__":  # pragma: no cover - reached through multi_llm.py util
    sys.exit(main(sys.argv[1:]))
