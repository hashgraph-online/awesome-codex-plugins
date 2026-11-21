"""``util improve-steps``: the native leg's planner for every review-then-apply composite.

``--improve-plan``, ``--improve-code`` and ``--improve-commits``: the
``--mode`` choices are the composite rows of the mode table
(``improve_workflow.COMPOSITE_ROWS``), never a list kept here.

On the native leg (Claude Code, and the Codex and OpenCode file shims) the
composite is an instruction core that loads each phase's own core in turn. Its
first step is this util: it answers, from the files as they are now, which
steps the run takes and with exactly which flags, so no instruction file ever
shows a model how to compose them (plan improve-plan-and-improve-code §2.4).

``--mode improve-commits`` plans a commit brief (plans/review-commits.md
§2.8, "The shared planner reads the brief"): ``util commit-brief`` prepared it
and printed ``[COMMIT_BRIEF] <brief>`` and ``[COMMIT_REMAINING_FLAGS]
<tokens>``, and the core calls ``util improve-steps <brief> --mode
improve-commits <tokens>``. The range's refs come from the brief's
``commit_range``, strictly re-resolved (``[RANGE_UNRESOLVED]`` is exit 3),
never from a flag: step 1's flags line gets ``--base-ref <base> --head-ref
<head>`` and step 2's ``--base-ref <base>`` (the empty-tree id for a range from
the root commit), the refs the executor's front door hands ``step_flags``. A
brief whose header changed since the review on record answered it
(``header_sha256`` against ``reviewed_header_sha256``) plans step 1 as ``run
(commit brief changed)``, fresh, with ``--force --rerun-all``. A brief with no
``commit_range`` is exit 3, and so is a typed ``--base-ref`` or ``--head-ref``
(``[COMMIT_FLAG_CONFLICT]``, as on every commit door). ``[IMPROVE_RERUN]``
names the pinned range, never the brief: ``--improve-commits
<base12>..<head12> --resume`` plus the typed selectors.

It calls the functions the executor leg calls, never a copy of them:
``improve_workflow.read_records`` reads the state once,
``improve_workflow.plan_steps`` gives each step's decision (from
``skip_reason`` alone) and its flags (``step_flags``), and
``improve_workflow.preflight`` makes the checks before any step in the order
the executor's entry point makes them. It builds no ``ImproveWorkflow``.

The text block, one per step::

    [IMPROVE_SCOPE_CHANGED] … | NOTE: …         (improve-code; before the steps)
    [IMPROVE_STEP] <index> <step> <decision> (<reason>)
    [IMPROVE_STEP_FRESH] <index>                (a review that must start over)
    [IMPROVE_STEP_FLAGS] <index> <shell-quoted flags>
    [ALREADY_COMPLETE] …                        (exit 2: every step passed over)
    [IMPROVE_RERUN] <the continuation, in the host's spelling>

A cascade (``--cascade`` typed, or an unfinished cascade on record:
``improve_cascade.applies``) is not planned here, since planning a stage
binds rounds and archives stages, and this util writes nothing. After the
same checks it hands off instead, with no step block::

    [IMPROVE_CASCADE_NEXT] <util improve-cascade next, the plan and every typed flag>
    [IMPROVE_RERUN] <the user's continuation, with --cascade>

``utils/improve_cascade_next.py`` is that command: the cascade's planner and
its only writer on this leg. ``--force`` without ``--cascade`` over an
unfinished cascade hands off too (abandoning it is a write), and its
``[IMPROVE_RERUN]`` is today's plain one: the call it names abandons the
cascade and plans one plain round. Under ``--dry-run-subagents`` nothing is
handed off: the plain round is planned with a ``NOTE:`` line
(``improve_workflow.dry_run_cascade_note``), and ``plan_steps`` passes over
every step after its first ``run`` one, the single step the executor leg's
preview runs too. ``improve_cascade.peek``'s refusals
(``[CASCADE_CONFLICT]``) print here, on stderr, with nothing on stdout, and a
finished cascade's command typed again is ``[ALREADY_COMPLETE]``, exit 2
(docs/development/workflows.md, "A cascade (``--cascade``)").

``--json`` prints the same facts as one object (§2.4's table), never both.
Exit codes: 0 a plan with a step to run, or a cascade's hand-off; 2
``[ALREADY_COMPLETE]``; 3 a refusal
(row 15, ``--interactive``, an unknown host, a live run, a ``state.json`` it
cannot read; for improve-commits a brief with no ``commit_range``, recorded
refs that no longer resolve, a typed ``--base-ref``/``--head-ref``); 1 a plan
file not found, a scope it cannot read, or ``--files-from -`` for a review it
plans as ``run``. A refusal prints nothing on stdout, with or without
``--json``, and its lines on stderr (one line; a ``[RANGE_UNRESOLVED]`` adds
its recovery line).

Read-only: it writes nothing, takes no lock and never reads stdin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import improve_cascade
from . import improve_workflow as iw
from . import unattended as unattended_mod
from .cli_common import (
    AGENT_DECIDE_FLAG,
    EXIT_ERROR,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    LEGACY_AGENT_DECIDE_FLAGS,
    _quote,
    add_scope_policy_argument,
    build_parent_parser,
    dispatcher_command,
    dispatcher_prefix,
)
from .stream_bootstrap import bootstrap_streams
from .text_clip import plain_line
from . import next_phase
from . import commit_range as range_mod
from . import host_capabilities
from .commit_paths import CommitReviewError, repo_root_of
from .output_handler import output_dir_path

#: The composites this util plans, in table order: every review-then-apply
#: composite row (``improve_workflow.COMPOSITE_ROWS``), so a composite added to
#: the table is a ``--mode`` choice with no edit here.
MODES: Tuple[str, ...] = tuple(row.name for row in iw.COMPOSITE_ROWS)

#: The composites whose parser takes the scope flags (review-code's
#: ``--files``, ``--files-from``, ``--base-ref``): those whose review is the
#: scoped one, read off each row's ``sequence`` (improve-code, improve-commits).
_SCOPED_MODES: Tuple[str, ...] = tuple(mode for mode in MODES if iw._reviews_code(mode))

#: Of those, the composites whose range a commit front door pins
#: (improve-commits): their parser also takes ``--head-ref``, and their refs
#: come from the brief's ``commit_range``, never from a typed flag.
_PINNED_MODES: Tuple[str, ...] = tuple(mode for mode in MODES if iw.pins_commit_range(mode))

#: The scoped composite that names the scope flags in ``--help`` when no
#: ``--mode`` is typed (kept for readers of the old single-mode constant).
_SCOPED_MODE = _SCOPED_MODES[0]

#: A typed ref a pinned composite refuses (``[COMMIT_FLAG_CONFLICT]``).
_PINNED_REFS: Tuple[Tuple[str, str], ...] = (("--base-ref", "base_ref"),
                                             ("--head-ref", "head_ref"))

STEP_MARKER = "[IMPROVE_STEP]"
FRESH_MARKER = "[IMPROVE_STEP_FRESH]"
FLAGS_MARKER = "[IMPROVE_STEP_FLAGS]"
RERUN_MARKER = "[IMPROVE_RERUN]"
ALREADY_COMPLETE_MARKER = "[ALREADY_COMPLETE]"
#: A cascade's hand-off: the ``util improve-cascade next`` command the core
#: runs once, in place of a step block.
CASCADE_NEXT_MARKER = "[IMPROVE_CASCADE_NEXT]"

#: The util that plans and records a cascade on this leg, and its one command.
CASCADE_UTIL = ("improve-cascade", "next")

#: The keys of the ``--json`` object and of each of its ``steps`` entries,
#: exactly §2.4's table. A later change adds a key, never renames or retypes
#: one; there is no ``schema_version`` (no reader outside this checkout).
#: ``cascade_next`` is the hand-off's command, ``null`` with no cascade.
JSON_KEYS: Tuple[str, ...] = (
    "mode", "plan", "already_complete", "notices", "steps", "rerun", "rerun_argv",
    "cascade_next",
)
STEP_KEYS: Tuple[str, ...] = ("index", "step", "decision", "reason", "fresh", "argv")


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------

def _typed_mode(argv: Sequence[str]) -> Optional[str]:
    """The ``--mode`` value as typed, to build that composite's own flags.

    A scan, not a parse: the parser itself depends on the answer (improve-code
    takes the scope flags, improve-plan refuses them, improve-commits also
    takes ``--head-ref``, as each composite's own parser does). ``None`` when
    it is missing or not a composite; the parser built then takes every flag
    and argparse names the missing or bad value.
    """
    for index, token in enumerate(argv):
        if token == "--":
            break
        if token == "--mode" and index + 1 < len(argv):
            value = argv[index + 1]
            return value if value in MODES else None
        if token.startswith("--mode="):
            value = token.partition("=")[2]
            return value if value in MODES else None
    return None


def _add_composite_flags(parser: argparse.ArgumentParser, mode: Optional[str]) -> None:
    """The composite's own flags, as ``improve_workflow.build_parser`` defines them.

    Same option strings, dests, ``nargs`` and defaults, so ``skip_reason``,
    ``step_flags`` and ``continuation_flags`` read the namespace they read on
    the executor leg (a test holds the two parsers together). No
    ``--plan-file`` (the plan is the positional), no hidden ``--commit-stage``
    (a detached launch's, never typed on this leg) and no
    ``set_defaults(consolidate=False, review_tasks=False)``: nothing here
    builds an ``ImproveWorkflow``. *mode* ``None`` (``--help`` with no
    ``--mode``) adds every composite's flags: improve-commits' set, which
    holds improve-code's, which holds improve-plan's, plus ``--cascade``,
    which every composite but the pinned-range one takes
    (``improve_workflow.takes_cascade``).
    """
    group = parser.add_argument_group("the composite's own flags")
    group.add_argument(
        "--models", nargs="+", default=None, metavar="PROVIDER:MODEL",
        help="Models for the review's fan-out, as the composite takes them.",
    )
    group.add_argument(
        "--quick", action="store_true",
        help="The quick model set for the review's fan-out.",
    )
    group.add_argument(
        "--resume", action="store_true",
        help="As the composite takes it: reaches the apply step only when the "
             "review is not run again.",
    )
    group.add_argument(
        "--force", action="store_true",
        help="A new review round (the review gets --force --rerun-all).",
    )
    if mode is None or iw.takes_cascade(mode):
        cascading = [name for name in MODES if iw.takes_cascade(name)]
        only = f" ({' and '.join(cascading)} only)" if mode is None else ""
        group.add_argument(
            "--cascade", action="store_true",
            help="One review-then-apply round per model, in the resolved model "
                 f"order, as the composite takes it{only}.",
        )
    if mode is None or mode in _SCOPED_MODES:
        only = f" ({' and '.join(_SCOPED_MODES)} only)" if mode is None else ""
        group.add_argument(
            "--files", action="append", default=[], metavar="PATH",
            help=f"Review exactly these files (repeatable){only}.",
        )
        group.add_argument(
            "--files-from", metavar="FILE", default=None,
            help="Like --files, one path per line read from FILE. \"-\" is "
                 f"refused for a review this plans to run: no phase it launches "
                 f"reads your stdin{only}.",
        )
        refused = ""
        if mode is None:
            refused = (f" {' and '.join(_PINNED_MODES)} refuses it: its base is the "
                       "commit brief's recorded range.")
        elif mode in _PINNED_MODES:
            refused = " Refused here: the base is the commit brief's recorded range."
        group.add_argument(
            "--base-ref", type=str, default=None,
            help=f"Git ref the review diffs against, and the apply's diff "
                 f"context{only}.{refused}",
        )
    if mode is None or mode in _PINNED_MODES:
        group.add_argument(
            "--head-ref", type=str, default=None,
            help="Refused, as on every commit door: improve-commits reads the "
                 "range's head from the commit brief's state.json and puts it "
                 "on step 1's flags line itself.",
        )
    add_scope_policy_argument(group, role="composite")
    group.add_argument(
        AGENT_DECIDE_FLAG, *LEGACY_AGENT_DECIDE_FLAGS, dest="agent_decide",
        action="store_true", help="Accepted and implied; changes nothing.",
    )
    group.add_argument(
        "--no-confirm", action="store_true",
        help="Accepted and implied; changes nothing.",
    )


def build_parser(mode: Optional[str] = None) -> argparse.ArgumentParser:
    """The util's parser: the shared parent, the plan, ``--mode``, the
    composite's own flags and ``--json``.

    Built on ``cli_common.build_parent_parser``, as the composites' parsers
    are, so every token a host's dispatcher command bakes in parses: ``--host
    <id>``, and ``--yes --exec-subagents`` on the file shims. ``util
    next-command``'s own parser rejects ``--yes``, and argparse's exit 2 here
    would read as a finished run. ``--interactive`` and ``-i`` are accepted
    only to be refused.
    """
    run = dispatcher_prefix()
    plan = "plans/my-plan.md"
    brief = "plans/commit-reviews/a1b2c3d4e5f6-e4f5a6b7c8d9.md"
    epilog = "\n".join([
        "",
        "Prints one block per step, in order (improve-plan's consolidation pass",
        "is step 1b):",
        f"  {STEP_MARKER} <index> <step> run|skip|after-review (<why>)",
        f"  {FRESH_MARKER} <index>     the review starts over: skip its",
        "                               Resume Detection step",
        f"  {FLAGS_MARKER} <index> <flags>  shell-quoted; pass them verbatim",
        f"then {RERUN_MARKER} <command>, the command that continues the run in",
        "the host's spelling, or, when every step is done for the review on",
        f"record, {ALREADY_COMPLETE_MARKER} … and exit 2. improve-code and",
        "improve-commits can print [IMPROVE_SCOPE_CHANGED] or a NOTE: line before",
        "the steps.",
        "",
        "improve-commits plans the commit brief `util commit-brief` printed as",
        "[COMMIT_BRIEF], with the tokens of its [COMMIT_REMAINING_FLAGS]: the",
        "range's refs come from the brief's state.json (step 1 gets --base-ref and",
        "--head-ref, step 2 --base-ref), and [IMPROVE_RERUN] names the pinned range.",
        "",
        "A cascade (--cascade typed, or an unfinished one on record) prints no step",
        f"block: {CASCADE_NEXT_MARKER} <command> names the `util improve-cascade",
        "next` call that plans and records each stage, then [IMPROVE_RERUN]. So",
        "does --force without --cascade over an unfinished cascade, whose call",
        "abandons it and plans one plain round.",
        "",
        "--json prints the same facts as one object: mode, plan,",
        "already_complete, notices, steps (index, step, decision, reason, fresh,",
        "argv), rerun, rerun_argv and cascade_next.",
        "",
        "exit codes: 0 a plan with a step to run, or a cascade's hand-off | 2",
        "[ALREADY_COMPLETE] | 3 a refusal (an empty decision flag, --interactive,",
        "an unknown --host, a live run owning a dir the composite writes, a",
        "state.json it cannot read, a [CASCADE_CONFLICT];",
        "improve-commits: a brief with no recorded range, a recorded commit that",
        "no longer resolves, a typed --base-ref or --head-ref) | 1 the plan is",
        "missing, the scope cannot be read, or --files-from - for a review it",
        "would run. A refusal prints its line on stderr and nothing on stdout.",
        "Read-only: it writes nothing and never reads stdin.",
        "",
        "Examples:",
        f"  {run} util improve-steps {plan} --mode improve-plan --host claude-code --quick",
        f"  {run} util improve-steps {plan} --mode improve-code --host codex --files src/app.py",
        f"  {run} util improve-steps {plan} --mode improve-plan --force --json",
        f"  {run} util improve-steps {plan} --mode improve-code --scope-policy preserve",
        f"  {run} util improve-steps {brief} --mode improve-commits --host claude-code --quick",
    ]) + "\n"
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util improve-steps",
        description=(
            "Plan an --improve-plan, --improve-code or --improve-commits run on "
            "the native leg: which steps run, each step's exact flags, and the "
            "command that continues the run. Read-only."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[build_parent_parser()],
        epilog=epilog,
    )
    parser.add_argument(
        "plan",
        help="The plan, as the user typed it (improve-commits: the commit brief "
             "[COMMIT_BRIEF] named)",
    )
    parser.add_argument(
        "--mode", required=True, choices=MODES,
        help="The composite to plan.",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json",
        help="Print the plan as one JSON object instead of the text block.",
    )
    _add_composite_flags(parser, mode)
    return parser


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """*argv* parsed with the parser of the composite its ``--mode`` names."""
    argv = list(argv)
    return build_parser(_typed_mode(argv)).parse_args(argv)


# ---------------------------------------------------------------------------
# The plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StepLine:
    """One step block: an ``[IMPROVE_STEP]`` line and its flags line."""

    index: str
    step: str
    decision: str
    reason: Optional[str]
    fresh: bool
    argv: Tuple[str, ...]


@dataclass(frozen=True)
class StepsPlan:
    """Everything the util prints, built once and rendered as text or JSON."""

    mode: str
    plan: str
    already_complete: Optional[str]
    notices: Tuple[str, ...]
    steps: Tuple[StepLine, ...]
    rerun: Optional[str]
    rerun_argv: Optional[Tuple[str, ...]]
    #: A cascade's hand-off (:func:`cascade_handoff`): the command after
    #: ``[IMPROVE_CASCADE_NEXT]``; ``None`` for every plan with steps.
    cascade_next: Optional[str] = None


def _rerun(
    mode: str, args: argparse.Namespace, plan_path: Path, host_id: str
) -> Tuple[str, Tuple[str, ...]]:
    """``[IMPROVE_RERUN]``: the continuation in the host's own spelling.

    ``continuation_flags``, the row-14 command's list (the selectors the user
    typed, never ``--force``, plus ``--resume``; no ``--host``, ``--yes`` or
    ``--exec-subagents``), after the plan as typed, from the host's
    ``next_command`` template. Host and route are resolved as ``util
    next-command`` resolves them.

    On improve-commits the positional is the pinned ``<base12>..<head12>``
    (the brief as typed, for a root range) and no front-door flag is carried,
    through ``improve_workflow.continuation_args``, the executor stop's own
    spelling. The ``rerun_argv`` stays the flags after it.
    """

    word, rest = iw.continuation_args(mode, plan_path, args, plan_arg=args.plan)
    positional, flags = rest[0], tuple(rest[1:])
    route = next_phase.resolve_route(
        host_id, recorded=next_phase.recorded_route(plan_path, host_id, mode),
    )
    command = next_phase.phase_command(positional, host_id, route, word, *flags)
    return command, flags


def build_plan(
    mode: str,
    args: argparse.Namespace,
    records: "iw.Records",
    *,
    finished: bool,
    plan_path: Path,
    host_id: str,
    extra_notices: Sequence[str] = (),
) -> StepsPlan:
    """The plan for *records*: the notices, every step block, then the end line.

    Each step's ``argv`` is ``step_flags`` followed by the cross-cutting tail
    without its ``--host`` pair (the phase core's launch step takes that from
    the host's dispatcher command): what the executor leg forwards, less that
    one pair. Under ``[ALREADY_COMPLETE]`` there is no ``1b`` and no
    continuation. *extra_notices* follow the scope notices (a dry run's
    cascade note).
    """
    tail = tuple(iw.cross_cutting_flags(args, include_host=False))
    steps = tuple(
        StepLine(
            index=step.index,
            step=step.step,
            decision=step.decision,
            reason=None if step.reason is None else plain_line(step.reason),
            fresh=bool(step.fresh),
            argv=tuple(step.flags) + tail,
        )
        for step in iw.plan_steps(mode, args, records)
    )
    already: Optional[str] = None
    rerun: Optional[str] = None
    rerun_argv: Optional[Tuple[str, ...]] = None
    if finished:
        line = plain_line(iw.already_complete_line(mode, args, records))
        already = line[len(ALREADY_COMPLETE_MARKER):].strip()
    else:
        rerun, rerun_argv = _rerun(mode, args, plan_path, host_id)
    return StepsPlan(
        mode=mode,
        plan=args.plan,
        already_complete=already,
        notices=tuple(
            plain_line(n)
            for n in [*iw.scope_notices(mode, args, records), *extra_notices]
        ),
        steps=steps,
        rerun=rerun,
        rerun_argv=rerun_argv,
    )


def render_text(plan: StepsPlan) -> str:
    """The text block the cores read."""
    lines: List[str] = list(plan.notices)
    for step in plan.steps:
        head = f"{STEP_MARKER} {step.index} {step.step} {step.decision}"
        lines.append(head if step.reason is None else f"{head} ({step.reason})")
        if step.fresh:
            lines.append(f"{FRESH_MARKER} {step.index}")
        lines.append(" ".join(
            [FLAGS_MARKER, step.index, *(_quote(token) for token in step.argv)]
        ))
    if plan.already_complete is not None:
        lines.append(f"{ALREADY_COMPLETE_MARKER} {plan.already_complete}")
    if plan.cascade_next is not None:
        lines.append(f"{CASCADE_NEXT_MARKER} {plan.cascade_next}")
    if plan.rerun is not None:
        lines.append(f"{RERUN_MARKER} {plan.rerun}")
    return "\n".join(lines)


def as_json(plan: StepsPlan) -> Dict[str, Any]:
    """§2.4's object: the same facts as the text block, the argv arrays unquoted."""
    return {
        "mode": plan.mode,
        "plan": plan.plan,
        "already_complete": plan.already_complete,
        "notices": list(plan.notices),
        "steps": [
            {
                "index": step.index,
                "step": step.step,
                "decision": step.decision,
                "reason": step.reason,
                "fresh": step.fresh,
                "argv": list(step.argv),
            }
            for step in plan.steps
        ],
        "rerun": plan.rerun,
        "rerun_argv": None if plan.rerun_argv is None else list(plan.rerun_argv),
        "cascade_next": plan.cascade_next,
    }


# ---------------------------------------------------------------------------
# improve-commits: the refs come from the brief
# ---------------------------------------------------------------------------

#: The markers of the two refusals only a commit brief meets (a third,
#: ``[RANGE_UNRESOLVED]``, is ``commit_range``'s own).
COMMIT_FLAG_CONFLICT = "[COMMIT_FLAG_CONFLICT]"
COMMIT_REVIEW_NOT_FOUND = "[COMMIT_REVIEW_NOT_FOUND]"


def pin_commit_range(
    mode: str, args: argparse.Namespace, plan_path: Path
) -> Optional[int]:
    """Put the brief's recorded range on *args*, or refuse (exit 3); improve-commits only.

    The executor leg gets ``--base-ref <base> --head-ref <head>`` from its
    front door; this leg never meets one, so the same refs are read here from
    the ``commit_range`` that ``util commit-brief`` recorded, and set as the
    parsed ``base_ref`` and ``head_ref``: ``step_flags`` then writes them onto
    step 1's flags line and the base onto step 2's, exactly as it does for the
    executor (plans/review-commits.md §2.8). Read raw, as every planner read
    is: nothing is created, migrated or locked.

    In order, each a refusal that prints on stderr only: a typed
    ``--base-ref`` or ``--head-ref`` (``[COMMIT_FLAG_CONFLICT]``: the refs are
    the brief's, and every commit door refuses a typed one); a
    ``state.json`` that cannot be read (the executor's own line); a brief with
    no ``commit_range`` (``[COMMIT_REVIEW_NOT_FOUND]``); recorded SHAs that no
    longer name commits (``commit_range.resolve_recorded``'s
    ``[RANGE_UNRESOLVED]``, strict, never a fallback). ``None`` when *args*
    now carries the pinned refs (``base_ref`` is the empty-tree id on a root
    range, as the front door passes it).
    """
    for flag, dest in _PINNED_REFS:
        if getattr(args, dest, None) is not None:
            return unattended_mod.fail_closed(
                f"{COMMIT_FLAG_CONFLICT} {flag}: util improve-steps --mode {mode} takes "
                f"no {flag}: the range's refs are read from the commit brief's "
                "state.json (util commit-brief recorded them)."
            )

    shown = iw._display_path(args.plan)
    try:
        document = iw.read_state_document(output_dir_path(plan_path) / "state.json")
    except iw.StateReadError as exc:
        return unattended_mod.fail_closed(iw.state_read_error_line(mode, exc))
    record = (document or {}).get("commit_range")
    if not isinstance(record, dict):
        return unattended_mod.fail_closed(
            f"{COMMIT_REVIEW_NOT_FOUND} {shown}: no commit range recorded for this "
            f"brief, so --mode {mode} cannot plan it. Prepare the range with util "
            "commit-brief <range> and plan the [COMMIT_BRIEF] path it prints."
        )
    try:
        resolved = range_mod.resolve_recorded(
            record, cwd=str(repo_root_of(plan_path)), label=shown,
            recovery=(f"Re-run --{mode} <range> (or util commit-brief <range>) on "
                      "the commits as they are now: it resolves to new SHAs and a "
                      "new brief, since this review can no longer be resumed."),
        )
    except (range_mod.RangeError, CommitReviewError) as exc:
        return unattended_mod.fail_closed(exc.message)
    args.base_ref = resolved.base_ref
    args.head_ref = resolved.head
    return None


# ---------------------------------------------------------------------------
# A cascade: handed off to `util improve-cascade next`
# ---------------------------------------------------------------------------

def cascade_next_command(argv: Sequence[str], host_id: str) -> str:
    """``util improve-cascade next`` with every token this util was given, in the dispatcher's spelling.

    *argv* verbatim (the plan where it was typed, ``--mode``, the user's
    flags, ``--json`` included), so the first ``next`` call parses what this
    call parsed; plus ``--host <id>`` when none was typed, so its printed
    continuation names the host this call resolved. Every token is quoted as
    every printed follow-up is (``cli_common.dispatcher_command``).
    """
    tokens = list(argv)
    if not any(token == "--host" or token.startswith("--host=") for token in tokens):
        cut = tokens.index("--") if "--" in tokens else len(tokens)
        tokens[cut:cut] = ["--host", host_id]
    return dispatcher_command("util", *CASCADE_UTIL, *tokens)


def user_continuation(
    mode: str, args: argparse.Namespace, plan_path: Path, host_id: str, *, cascade: bool,
) -> Tuple[str, Tuple[str, ...]]:
    """``[IMPROVE_RERUN]`` for the user's own namespace: with ``--cascade`` while one runs.

    ``continuation_flags`` on a copy of *args* with ``cascade`` set to
    *cascade*: the typed selectors, then ``--cascade`` (when *cascade*), then
    ``--resume``, never ``--force``. Shared with ``util improve-cascade next``,
    so the hand-off and every stage print the same kind of line.
    """
    shown = copy.copy(args)
    shown.cascade = bool(cascade)
    return _rerun(mode, shown, plan_path, host_id)


def cascade_handoff(
    mode: str, args: argparse.Namespace, argv: Sequence[str], plan_path: Path,
    host_id: str, *, cascading: bool,
) -> StepsPlan:
    """The hand-off a cascade gets in place of a step block: no step, two lines.

    *cascading* is false for ``--force`` without ``--cascade`` over an
    unfinished cascade: ``next`` abandons it and plans one plain round, so
    the continuation is today's plain one.
    """
    rerun, rerun_argv = user_continuation(mode, args, plan_path, host_id, cascade=cascading)
    return StepsPlan(
        mode=mode, plan=args.plan, already_complete=None, notices=(), steps=(),
        rerun=rerun, rerun_argv=rerun_argv,
        cascade_next=cascade_next_command(argv, host_id),
    )


def _cascading(mode: str, args: argparse.Namespace, plan_path: Path) -> Optional[bool]:
    """Whether this call hands off: ``None`` when no cascade decides it.

    ``True`` for a cascade with a stage to run or a close-out owed, ``False``
    for ``--force`` without ``--cascade`` over an unfinished one (no cascade
    runs, but abandoning it is a write). Read-only, as
    ``improve_cascade.peek`` is; its refusals raise
    ``improve_cascade.CascadeRefusal``. ``preflight`` has already answered a
    finished cascade's command typed again.
    """
    if not iw.takes_cascade(mode) or not improve_cascade.applies(plan_path, mode, args):
        return None
    return improve_cascade.peek(plan_path, mode, args).kind == "work"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    """``util improve-steps <plan> --mode improve-plan|improve-code|improve-commits [flags…]``.

    In order: row 15 on the raw argv (the ``util`` route skips the mode
    route's ``validate_decision_flags``, so ``--models ""`` would otherwise
    plan the default list); the parse; the ``--interactive`` refusal; an
    unknown ``--host``; the plan exists; for improve-commits the brief's
    recorded range (:func:`pin_commit_range`); then
    ``improve_workflow.preflight``, the executor entry point's own checks in
    its order (a live owner, the records, ``[ALREADY_COMPLETE]``,
    ``--files-from -`` for a review planned ``run``), with *detached* true
    because no phase this leg launches reads the user's stdin. A finished
    cascade's command typed again is its ``[ALREADY_COMPLETE]`` line alone,
    exit 2. Then, when a cascade decides the call, the hand-off
    (:func:`cascade_handoff`, nothing written); otherwise the plan. Either
    as text or ``--json``.
    """
    bootstrap_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        unattended_mod.validate_decision_flags(argv)
    except unattended_mod.NeedsHuman as exc:
        return unattended_mod.fail_closed(exc.message)
    args = parse_args(argv)
    mode = args.mode
    if getattr(args, "interactive", False):
        return unattended_mod.fail_closed(iw.interactive_refusal(mode))

    host_id = host_capabilities.resolve_host_id(explicit=args.host)
    try:
        host_capabilities.entry(host_id)
    except unattended_mod.NeedsHuman as exc:
        return unattended_mod.fail_closed(exc.message)

    plan_path = Path(os.path.abspath(args.plan))
    pinned = iw.pins_commit_range(mode)
    if not plan_path.is_file():
        label = "Commit brief" if pinned else "Plan file"
        print(f"ERROR: {label} not found: {args.plan}", file=sys.stderr)
        print(f"       Resolved path: {plan_path}", file=sys.stderr)
        return EXIT_ERROR
    if pinned:
        refused = pin_commit_range(mode, args, plan_path)
        if refused is not None:
            return refused

    read: Dict[str, "iw.Records"] = {}

    def records() -> "iw.Records":
        if "records" not in read:
            read["records"] = iw.read_records(mode, plan_path, args)
        return read["records"]

    outcome = iw.preflight(
        mode, plan_path, args, records, skip_own_run_dir=False, detached=True,
    )
    if isinstance(outcome, iw.CascadeFinished):
        line = plain_line(outcome.line)
        plan = StepsPlan(
            mode=mode, plan=args.plan, notices=(), steps=(), rerun=None,
            rerun_argv=None,
            already_complete=line[len(ALREADY_COMPLETE_MARKER):].strip(),
        )
        print(json.dumps(as_json(plan), indent=2) if args.json else render_text(plan))
        return outcome.code
    finished = outcome is iw.FINISHED
    if outcome is not None and not finished:
        return int(outcome)

    cascading: Optional[bool] = None
    if not finished:
        try:
            cascading = _cascading(mode, args, plan_path)
        except improve_cascade.CascadeRefusal as exc:
            return improve_cascade.refusal_exit(exc)
    if cascading is not None and not iw.dry_run_preview(args):
        plan = cascade_handoff(mode, args, argv, plan_path, host_id, cascading=cascading)
    else:
        # A dry run never hands a cascade off (planning a stage records it):
        # it plans one plain round, whose first step alone runs, as the
        # executor leg's preview does.
        plan = build_plan(
            mode, args, records(), finished=finished, plan_path=plan_path,
            host_id=host_id,
            extra_notices=(iw.dry_run_cascade_note(),) if cascading else (),
        )
    if args.json:
        print(json.dumps(as_json(plan), indent=2))
    else:
        print(render_text(plan))
    return EXIT_NOTHING_TO_DO if finished else EXIT_OK


if __name__ == "__main__":  # pragma: no cover - reached through multi_llm.py util
    sys.exit(main(sys.argv[1:]))
