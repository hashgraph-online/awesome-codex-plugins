#!/usr/bin/env python3
"""The unattended contract: one disposition per decision point (D6).

Every interactive decision point in this skill resolves **without** a structured
ask tool. This module is the single owner of what that means, so no message, no
instruction file and no test has to re-derive it:

* :data:`ROWS` — the fifteen decision *sites* (not the 51 occurrences: a site
  restated in four mode files is still one decision), each keyed by a stable
  ``site_id``, the modes that reach it, the disposition it lands on and the D5a
  decision flag that answers it. Exactly three dispositions exist —
  :data:`AUTO_SELECT` (a documented default is applied *and recorded*),
  :data:`FAIL_CLOSED` (exit 3, "needs a human", nothing downstream runs) and
  :data:`EXPLICIT_FLAG` (the run proceeds only because the user typed a flag
  naming the choice). **"Ask in free text" is not a fourth option**: a headless
  run renders nothing, so a question is never a fallback — it is the failure this
  module exists to remove.
* :data:`DECISION_FLAGS` — the D5a input contract. No decision may exist only as
  a question: every gate has a flag whose values enumerate exactly the options
  the question would render, validated by ``choices`` (or by
  :func:`validate_decision_flags` for the argv-level pre-check), never guessed.
  An empty or unrecognized value is **exit 3 at parse time** (row 15).
* :func:`require_uv` — the run-time backstop half of the uv bootstrap (D6c layer
  3). The wording lives in ``hosts/uv-missing.txt`` so the shim preflight, the
  ``install-host --check`` prerequisite report and this probe can never disagree.
* :func:`record_resolution` — an auto-resolution is only "auto-select" if it is
  attributable afterwards, so every one of them prints a marker and (under
  ``--detach``) lands in ``{phase}/.status.json`` ``run.resolutions``.

**Nothing here sniffs its environment.** There is no ``isatty()`` call, no ``CI``
read and no ``--print`` detection anywhere in this skill's Python: interactivity
is *requested* (a user-typed ``--interactive``), never detected, so the same argv
produces the same phases in a terminal and in a pipe (D6b). The one former sniff
— ``full-workflow.md``'s "no TTY and no ``--yes`` → skip review-tasks" branch —
is deleted, and ``tests/test_unattended.py`` fails any reintroduction.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # normal import (utils is a package)
    from .cli_common import (
        AGENT_DECIDE_FLAG,
        LEGACY_AGENT_DECIDE_FLAGS,
        EXIT_NEEDS_HUMAN,
        EXIT_OK,
        STATE_PARTIAL,
        active_result,
        skill_dir,
    )
except ImportError:  # pragma: no cover - direct script runs with utils/ on path
    from cli_common import (  # type: ignore
        AGENT_DECIDE_FLAG,
        LEGACY_AGENT_DECIDE_FLAGS,
        EXIT_NEEDS_HUMAN,
        EXIT_OK,
        STATE_PARTIAL,
        active_result,
        skill_dir,
    )


# ---------------------------------------------------------------------------
# Dispositions
# ---------------------------------------------------------------------------

#: A documented default is applied and recorded.
AUTO_SELECT = "auto-select"
#: Exit 3, "needs a human"; nothing downstream runs.
FAIL_CLOSED = "fail-closed"
#: The run proceeds only because the user typed a flag naming the choice.
EXPLICIT_FLAG = "explicit-flag"

DISPOSITIONS: Tuple[str, ...] = (AUTO_SELECT, FAIL_CLOSED, EXPLICIT_FLAG)


class NeedsHuman(Exception):
    """A gate that cannot be resolved without a human: always exit 3.

    Distinct from the exit-2 phase-already-complete guard on purpose — a host has
    to be able to tell "needs a human" from "already done" without parsing prose.
    """

    exit_code = EXIT_NEEDS_HUMAN

    def __init__(self, message: str, *, site: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.site = site


# ---------------------------------------------------------------------------
# The fifteen rows
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Row:
    """One decision site.

    Attributes:
        number: D6 table row number (1..15). Stable; quoted by messages.
        site_id: The identifier recorded in ``run.resolutions`` and used by
            tests, so the table stays the single source of truth for what the
            default *was*.
        site: One-line description of the decision.
        modes: Mode words that can reach it.
        dispositions: Where it lands when nobody is watching, in the order the
            D6 disposition table names them.
        flags: The D5a decision flags that answer it, most specific first. Empty
            when the answer is out-of-band by design (rows 1 and 13) or when the
            row *is* the validator (row 15).
        enforced_in: Where the disposition is implemented. A markdown path means
            core-documented; a ``.py`` path means Python-resolved.
    """

    number: int
    site_id: str
    site: str
    modes: Tuple[str, ...]
    dispositions: Tuple[str, ...]
    flags: Tuple[str, ...]
    enforced_in: Tuple[str, ...]


ROWS: Tuple[Row, ...] = (
    Row(
        number=1,
        site_id="uv-missing",
        site="uv is not installed (probe before the first `uv run`)",
        modes=("*",),
        dispositions=(FAIL_CLOSED,),
        flags=(),
        enforced_in=("utils/unattended.py", "hosts/uv-missing.txt",
                     "references/uv-check.md"),
    ),
    Row(
        number=2,
        site_id="model-selection",
        site="which models to fan out to",
        modes=("review-plan", "review-tasks", "review-code", "ask", "full",
               "improve-plan", "improve-code", "review-commits",
               "improve-commits"),
        dispositions=(AUTO_SELECT, FAIL_CLOSED, EXPLICIT_FLAG),
        flags=("--models", "--quick"),
        enforced_in=("utils/interactive.py",),
    ),
    Row(
        number=3,
        site_id="partial-results-recovery",
        site="some models produced no result (partial / resume / rerun-all)",
        modes=("review-plan", "review-tasks", "review-code", "ask",
               "improve-plan", "improve-code", "review-commits",
               "improve-commits"),
        dispositions=(AUTO_SELECT, FAIL_CLOSED),
        flags=("--force", "--reaggregate", "--rerun-all"),
        enforced_in=("utils/review_orchestrator_base.py", "ask_orchestrator.py",
                     "code_review_orchestrator.py",
                     "instructions/review-plan.md"),
    ),
    Row(
        number=4,
        site_id="consolidation-offer",
        site="run consolidation after [CONSOLIDATION_RECOMMENDED]?",
        modes=("review-plan", "full", "improve-plan"),
        dispositions=(AUTO_SELECT,),
        flags=("--consolidate",),
        # improve-plan's native leg cuts the review core off before its own
        # consolidation step and runs the pass as its step 1b instead; its
        # executor leg is `full`'s step_consolidate, listed first.
        enforced_in=("full_workflow_orchestrator.py",
                     "instructions/review-plan.md",
                     "instructions/full-workflow.md",
                     "instructions/improve-plan.md"),
    ),
    Row(
        number=5,
        site_id="generate-tasks-prerequisite",
        site="unapplied plan-review suggestions before generate-tasks",
        modes=("generate-tasks", "full"),
        dispositions=(AUTO_SELECT, FAIL_CLOSED, EXPLICIT_FLAG),
        flags=("--skip-prerequisites",),
        enforced_in=("check_workflow_prerequisites.py",
                     "generate_tasks_orchestrator.py",
                     "full_workflow_orchestrator.py"),
    ),
    Row(
        number=6,
        site_id="implement-prerequisite",
        site="unapplied plan-review suggestions before implement",
        modes=("implement", "full"),
        dispositions=(AUTO_SELECT, FAIL_CLOSED, EXPLICIT_FLAG),
        flags=("--skip-prerequisites",),
        enforced_in=("check_workflow_prerequisites.py",
                     "implement_orchestrator.py",
                     "full_workflow_orchestrator.py"),
    ),
    Row(
        number=7,
        site_id="task-suggestion-advisory",
        site="unapplied task-review suggestions before implement (advisory)",
        modes=("implement",),
        dispositions=(AUTO_SELECT,),
        flags=("--no-confirm",),
        enforced_in=("implement_orchestrator.py",),
    ),
    Row(
        number=8,
        site_id="human-task-strategy",
        site="how to handle tasks that need a human",
        modes=("implement", "full"),
        dispositions=(AUTO_SELECT, EXPLICIT_FLAG),
        flags=("--force-strategy",),
        enforced_in=("implement_orchestrator.py",),
    ),
    Row(
        number=9,
        site_id="human-task-pause",
        site="per-human-task pause under --force-strategy pause-and-ask",
        modes=("implement",),
        dispositions=(FAIL_CLOSED, EXPLICIT_FLAG),
        flags=("--human-task",),
        enforced_in=("multi_llm.py", "implement_orchestrator.py"),
    ),
    Row(
        number=10,
        site_id="needs-human-decision",
        site="needs-human-decision items (per item, or the batched UI)",
        modes=("apply-suggestions", "apply-task-suggestions", "apply-code-fixes",
               "review-tasks", "full", "improve-plan", "improve-code",
               "apply-commit-fixes", "improve-commits"),
        dispositions=(AUTO_SELECT,),
        flags=(AGENT_DECIDE_FLAG, "--no-confirm"),
        enforced_in=("utils/apply_orchestrator_base.py",),
    ),
    Row(
        number=11,
        site_id="no-selections-confirmation",
        site="no user selections found — apply ALL valid items?",
        modes=("apply-suggestions", "apply-task-suggestions", "apply-code-fixes",
               "full", "improve-plan", "improve-code", "apply-commit-fixes",
               "improve-commits"),
        dispositions=(AUTO_SELECT,),
        flags=("--no-confirm",),
        enforced_in=("utils/filtering.py", "utils/apply_orchestrator_base.py"),
    ),
    Row(
        number=12,
        site_id="review-tasks-continuation",
        site="review the generated tasks before implementing?",
        modes=("full",),
        dispositions=(AUTO_SELECT, EXPLICIT_FLAG),
        flags=("--review-tasks",),
        enforced_in=("full_workflow_orchestrator.py",
                     "instructions/full-workflow.md"),
    ),
    Row(
        number=13,
        site_id="no-tasks-to-review",
        site="review-tasks against a plan that has no task list",
        modes=("review-tasks",),
        dispositions=(FAIL_CLOSED,),
        flags=(),
        enforced_in=("check_workflow_prerequisites.py",
                     "review_tasks_orchestrator.py"),
    ),
    Row(
        number=14,
        site_id="phase-failure-recovery",
        site="a phase failed — retry / run manually / cancel",
        modes=("full", "*"),
        dispositions=(FAIL_CLOSED,),
        flags=("--resume",),
        # The composites' continuation is `improve_workflow.continuation_flags`
        # (the executor leg's row-14 command, through `_phase_failed`, which
        # stays in full_workflow_orchestrator.py), and each native core's
        # step 3 stops with the `[IMPROVE_RERUN]` it prints: improve-commits'
        # spells it as the pinned range (plans/review-commits.md §2.8).
        enforced_in=("full_workflow_orchestrator.py",
                     "instructions/full-workflow.md",
                     "utils/improve_workflow.py",
                     "instructions/improve-plan.md",
                     "instructions/improve-code.md",
                     "instructions/improve-commits.md"),
    ),
    Row(
        number=15,
        site_id="empty-or-ambiguous-selection",
        site="a decision flag that arrives empty or unrecognized",
        modes=("*",),
        dispositions=(FAIL_CLOSED,),
        flags=(),
        enforced_in=("utils/unattended.py", "multi_llm.py"),
    ),
)

_ROWS_BY_NUMBER: Dict[int, Row] = {r.number: r for r in ROWS}
_ROWS_BY_SITE: Dict[str, Row] = {r.site_id: r for r in ROWS}


def row(number: int) -> Row:
    """The D6 row with this number."""
    return _ROWS_BY_NUMBER[number]


def row_for_site(site_id: str) -> Row:
    """The D6 row with this ``site_id``."""
    return _ROWS_BY_SITE[site_id]


def site_ids() -> Tuple[str, ...]:
    return tuple(r.site_id for r in ROWS)


# ---------------------------------------------------------------------------
# D5a — the decision-input contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FlagSpec:
    """One non-interactive decision flag.

    Attributes:
        name: The long flag spelling.
        rows: D6 row numbers it answers.
        choices: Legal values, when the flag is valued and enumerable. Empty for
            a boolean flag.
        value_form: ``"none"`` (boolean), ``"one"`` (single value),
            ``"list"`` (``nargs="+"``) or ``"pair"``
            (``<key>=<value>``, repeatable).
        parsers: Files whose argparse parser accepts it. ``"parent"`` means the
            shared cross-cutting parent in ``utils/cli_common.py``, i.e. every
            entry point.
        aliases: Other spellings the same parsers accept for it.
    """

    name: str
    rows: Tuple[int, ...]
    choices: Tuple[str, ...]
    value_form: str
    parsers: Tuple[str, ...]
    aliases: Tuple[str, ...] = ()


#: ``done`` and ``skip`` answer a paused human task; all three answer a task
#: the last ``implement`` run recorded ``failed`` (a check that failed, racing
#: re-run 3, 2026-10-05): ``done`` treats it as satisfied, ``skip`` leaves it
#: and its dependents undone, ``retry`` re-runs a check the unchanged-tree
#: guard would otherwise refuse. The orchestrator decides which task may take
#: which; this is the closed value set the dispatcher validates at parse time.
HUMAN_TASK_ACTIONS: Tuple[str, ...] = ("done", "skip", "retry")
HUMAN_TASK_STRATEGIES: Tuple[str, ...] = (
    "pause-and-ask", "skip-continue", "skip-dependents",
)
#: The strategy an unattended run resolves row 8 to: an unattended run cannot
#: perform manual steps, so code tasks depending on them cannot be assumed valid.
UNATTENDED_HUMAN_TASK_STRATEGY = "skip-dependents"

DECISION_FLAGS: Tuple[FlagSpec, ...] = (
    FlagSpec("--models", (2,), (), "list",
             ("review_plan_orchestrator.py", "review_tasks_orchestrator.py",
              "code_review_orchestrator.py", "ask_orchestrator.py",
              "full_workflow_orchestrator.py",
              "improve_plan_orchestrator.py", "improve_code_orchestrator.py")),
    FlagSpec("--quick", (2,), (), "none",
             ("review_plan_orchestrator.py", "review_tasks_orchestrator.py",
              "code_review_orchestrator.py", "ask_orchestrator.py",
              "full_workflow_orchestrator.py",
              "improve_plan_orchestrator.py", "improve_code_orchestrator.py")),
    FlagSpec("--force", (3,), (), "none",
             ("review_plan_orchestrator.py", "review_tasks_orchestrator.py",
              "code_review_orchestrator.py", "ask_orchestrator.py",
              "improve_plan_orchestrator.py", "improve_code_orchestrator.py")),
    FlagSpec("--reaggregate", (3,), (), "none",
             ("review_plan_orchestrator.py", "review_tasks_orchestrator.py",
              "code_review_orchestrator.py")),
    FlagSpec("--rerun-all", (3,), (), "none",
             ("review_plan_orchestrator.py", "review_tasks_orchestrator.py",
              "code_review_orchestrator.py", "ask_orchestrator.py")),
    FlagSpec("--consolidate", (4,), (), "none",
             ("review_plan_orchestrator.py",)),
    FlagSpec("--skip-prerequisites", (5, 6), (), "none", ("parent",)),
    FlagSpec("--no-confirm", (7, 10, 11), (), "none",
             ("implement_orchestrator.py", "apply_suggestions_orchestrator.py",
              "apply_task_suggestions_orchestrator.py",
              "apply_code_fixes_orchestrator.py")),
    FlagSpec("--force-strategy", (8,), HUMAN_TASK_STRATEGIES, "one",
             ("implement_orchestrator.py",)),
    FlagSpec("--human-task", (9,), HUMAN_TASK_ACTIONS, "pair",
             ("implement_orchestrator.py",
              # Fix round 18: an apply batch's partial application, `=skip`.
              "apply_suggestions_orchestrator.py",
              "apply_task_suggestions_orchestrator.py",
              "apply_code_fixes_orchestrator.py")),
    FlagSpec(AGENT_DECIDE_FLAG, (10,), (), "none",
             ("apply_suggestions_orchestrator.py",
              "apply_task_suggestions_orchestrator.py",
              "apply_code_fixes_orchestrator.py"),
             aliases=LEGACY_AGENT_DECIDE_FLAGS),
    FlagSpec("--review-tasks", (12,), (), "none",
             ("full_workflow_orchestrator.py",)),
    FlagSpec("--resume", (14,), (), "none",
             ("full_workflow_orchestrator.py", "implement_orchestrator.py",
              "apply_suggestions_orchestrator.py",
              "apply_task_suggestions_orchestrator.py",
              "apply_code_fixes_orchestrator.py",
              "improve_plan_orchestrator.py", "improve_code_orchestrator.py")),
)

_FLAGS_BY_NAME: Dict[str, FlagSpec] = {
    spelling: f for f in DECISION_FLAGS for spelling in (f.name, *f.aliases)
}


def flags_for_row(number: int) -> Tuple[FlagSpec, ...]:
    """Every decision flag that answers D6 row *number*."""
    return tuple(f for f in DECISION_FLAGS if number in f.rows)


def flag_spec(name: str) -> Optional[FlagSpec]:
    return _FLAGS_BY_NAME.get(name)


# The valued flags the argv-level pre-check validates. Boolean flags cannot
# arrive "empty", so they need no check beyond argparse's own.
_VALIDATED: Tuple[str, ...] = ("--models", "--force-strategy", "--human-task")


def _values_after(argv: Sequence[str], index: int, *, greedy: bool) -> List[str]:
    """The value tokens that belong to the flag at *index*."""
    values: List[str] = []
    cursor = index + 1
    while cursor < len(argv):
        token = argv[cursor]
        # An empty string is a *value* (the row-15 case), never a flag.
        if token.startswith("-") and token != "-" and token != "":
            break
        values.append(token)
        cursor += 1
        if not greedy:
            break
    return values


def validate_decision_flags(argv: Sequence[str]) -> None:
    """Row 15: an empty or unrecognized decision value is exit 3 at parse time.

    Runs on raw argv *before* any parser, so ``--models ""``,
    ``--human-task T001=`` and an unknown ``--force-strategy`` value all fail the
    same way — with exit 3 rather than argparse's exit 2, which a host would read
    as "nothing to do". ``choices`` on each parser is the second layer, not the
    only one.

    Raises:
        NeedsHuman: naming the flag, the offending value and the legal values.
    """
    argv = list(argv)
    for index, token in enumerate(argv):
        head, _, inline = token.partition("=")
        if head not in _VALIDATED:
            continue
        spec = _FLAGS_BY_NAME[head]
        if token.startswith(head + "="):
            values = [inline]
        else:
            values = _values_after(argv, index, greedy=spec.value_form == "list")
        _validate_values(spec, values)


def _validate_values(spec: FlagSpec, values: Sequence[str]) -> None:
    site = row(spec.rows[0]).site_id
    if not values:
        raise NeedsHuman(
            f"ERROR: {spec.name} was passed with no value. "
            f"{_legal_values(spec)}\n"
            "       A decision flag that arrives empty is never a default "
            "(D6 row 15).",
            site=site,
        )
    for value in values:
        if not value.strip():
            raise NeedsHuman(
                f"ERROR: {spec.name} was passed an empty value. "
                f"{_legal_values(spec)}\n"
                "       A decision flag that arrives empty is never a default "
                "(D6 row 15).",
                site=site,
            )
        if spec.value_form == "pair":
            parse_human_task_decision(value)
        elif spec.choices and value not in spec.choices:
            raise NeedsHuman(
                f"ERROR: {spec.name} got unrecognized value {value!r}. "
                f"{_legal_values(spec)}",
                site=site,
            )


def _legal_values(spec: FlagSpec) -> str:
    if spec.value_form == "pair":
        return f"Expected <id>={'|'.join(spec.choices)}."
    if spec.choices:
        return f"Legal values: {', '.join(spec.choices)}."
    if spec.value_form == "list":
        return "Expected one or more non-empty values."
    return "Expected a non-empty value."


def parse_human_task_decision(value: str) -> Tuple[str, str]:
    """Parse one ``--human-task <task_id>=done|skip|retry`` value (row 9).

    The only genuinely new answer channel in D5a, because it is per-task and
    mid-run: the pause becomes a process boundary (exit, print the two
    re-invocations, be re-invoked) instead of a blocked stdin.
    """
    task_id, sep, action = value.partition("=")
    site = row(9).site_id
    if not sep or not task_id.strip() or not action.strip():
        raise NeedsHuman(
            f"ERROR: --human-task expects <task_id>=done|skip|retry, got {value!r}.\n"
            "       An empty or malformed decision value is never a default "
            "(D6 row 15).",
            site=site,
        )
    if action not in HUMAN_TASK_ACTIONS:
        raise NeedsHuman(
            f"ERROR: --human-task {task_id}={action!r} is not a legal action. "
            f"Legal values: {', '.join(HUMAN_TASK_ACTIONS)}.",
            site=site,
        )
    return task_id.strip(), action


def parse_human_task_decisions(values: Optional[Iterable[str]]) -> Dict[str, str]:
    """Every ``--human-task`` value as ``{task_id: action}``.

    A repeated task id with a *different* action is a contradiction, not a
    precedence rule, so it is exit 3 like every other ambiguous answer.
    """
    decisions: Dict[str, str] = {}
    for value in values or ():
        task_id, action = parse_human_task_decision(value)
        previous = decisions.get(task_id)
        if previous is not None and previous != action:
            raise NeedsHuman(
                f"ERROR: --human-task {task_id} was given twice with different "
                f"actions ({previous!r} and {action!r}). Pass exactly one.",
                site=row(9).site_id,
            )
        decisions[task_id] = action
    return decisions


# ---------------------------------------------------------------------------
# D5d — the interactive inventory, per `ask` class
# ---------------------------------------------------------------------------
# D6 makes every gate answerable unattended, D6b makes unattended the default and
# D5a fixes the answer channel. What none of them states is *which* decision points
# a non-Claude host may render, in what order, and what happens to the ones that
# cannot be rendered at all — leaving "interactive parity" an open-ended promise the
# first user to type `--interactive` discovers empirically. So the inventory is
# closed, it lives next to the rows it indexes, and it is the same list the renderer
# below reads.

#: The three `ask` values in `hosts/capabilities.yaml`. Closed; a fourth would be a
#: schema change, not a new branch here.
ASK_STRUCTURED = "structured"
ASK_FREE_TEXT = "free-text"
ASK_NONE = "none"
ASK_CLASSES: Tuple[str, ...] = (ASK_STRUCTURED, ASK_FREE_TEXT, ASK_NONE)


@dataclass(frozen=True)
class InventoryRow:
    """What each `ask` class renders for one decision site.

    Attributes:
        rows: D6 row numbers this entry covers (5 and 6 share one line, being the
            same gate with a different mode word).
        site_id: The D6 site this indexes.
        options: How many options the block renders, in D5a's "Options as
            rendered" order. ``None`` means the count is data-dependent (one block
            per item or per paused task) rather than fixed.
        structured: One line describing the `ask: structured` presentation.
        free_text: One line describing the `ask: free-text` presentation. Rendered
            **only** under `--interactive`.
        unattended: What an `ask: none` host (and every headless run) does instead.
        renderable: False for the fail-closed rows, which no class may render — a
            host that turns one into a question has reintroduced the hang.
    """

    rows: Tuple[int, ...]
    site_id: str
    options: Optional[int]
    structured: str
    free_text: str
    unattended: str
    renderable: bool = True


INVENTORY: Tuple[InventoryRow, ...] = (
    InventoryRow(
        rows=(2,), site_id="model-selection", options=None,
        structured="multi-select ask over the configured models",
        free_text="numbered block: the resolved `defaults.models`, each named set "
                  "in `providers.yaml`, and a final `--models a,b,c` re-invocation "
                  "to edit",
        unattended="`defaults.models`; `--interactive` is exit 3",
    ),
    InventoryRow(
        rows=(3,), site_id="partial-results-recovery", options=3,
        structured="3-option ask",
        free_text="numbered block, 3 options",
        unattended="the `--yes` default: resume the missing models",
    ),
    InventoryRow(
        rows=(4,), site_id="consolidation-offer", options=2,
        structured="2-option ask",
        free_text="numbered block, 2 options",
        unattended="auto-run once on the marker",
    ),
    InventoryRow(
        rows=(5, 6), site_id="generate-tasks-prerequisite", options=3,
        structured="3-option ask",
        free_text="numbered block = D6a's `[PREREQUISITE_UNMET]` text verbatim",
        unattended="auto-run the apply phase, else exit 3",
    ),
    InventoryRow(
        rows=(7,), site_id="task-suggestion-advisory", options=2,
        structured="2-option ask",
        free_text="numbered block, 2 options",
        unattended="skip; the phase is recorded skipped",
    ),
    InventoryRow(
        rows=(8,), site_id="human-task-strategy", options=4,
        structured="4-option ask",
        free_text="numbered block, 4 options",
        unattended="`skip-dependents`",
    ),
    InventoryRow(
        rows=(9,), site_id="human-task-pause", options=3,
        structured="one ask per paused task",
        free_text="one numbered block per paused task, answered by "
                  "`--human-task <id>=done|skip`",
        unattended="unreachable under `--yes`",
    ),
    InventoryRow(
        rows=(10,), site_id="needs-human-decision", options=None,
        structured="per-item ask, or the batched approve-all / skip-all / "
                   "review-each UI",
        free_text="one numbered block per item (no 4-option cap — that was the "
                  "structured tool's)",
        unattended=f"`{AGENT_DECIDE_FLAG} --no-confirm`; the report is printed and "
                   "nothing is asked",
    ),
    InventoryRow(
        rows=(11,), site_id="no-selections-confirmation", options=2,
        structured="2-option ask",
        free_text="numbered block, 2 options",
        unattended="`--no-confirm`; every valid item is applied",
    ),
    InventoryRow(
        rows=(12,), site_id="review-tasks-continuation", options=2,
        structured="2-option ask",
        free_text="numbered block, 2 options",
        unattended="run review-tasks",
    ),
    # Struck out on purpose: D6's disposition table makes these fail closed, so no
    # `ask` class renders them. Exit 3 with the fix named is the whole behavior.
    InventoryRow(
        rows=(13,), site_id="no-tasks-to-review", options=None,
        structured="never rendered", free_text="never rendered",
        unattended="exit 3 printing both out-of-band commands", renderable=False,
    ),
    InventoryRow(
        rows=(14,), site_id="phase-failure-recovery", options=None,
        structured="never rendered", free_text="never rendered",
        unattended="exit 3 naming the phase and its `--resume` re-invocation",
        renderable=False,
    ),
    InventoryRow(
        rows=(15,), site_id="empty-or-ambiguous-selection", options=None,
        structured="never rendered", free_text="never rendered",
        unattended="exit 3 at parse time", renderable=False,
    ),
)

_INVENTORY_BY_SITE: Dict[str, InventoryRow] = {r.site_id: r for r in INVENTORY}


def inventory_row(site_id: str) -> InventoryRow:
    return _INVENTORY_BY_SITE[site_id]


def renderable_sites() -> Tuple[str, ...]:
    """The sites an interactive host may render, in D6 row order."""
    return tuple(r.site_id for r in INVENTORY if r.renderable)


def presentation(site_id: str, ask_class: str) -> str:
    """The one-line description of what *ask_class* renders for *site_id*."""
    if ask_class not in ASK_CLASSES:
        raise KeyError(
            f"unknown ask class {ask_class!r}; the vocabulary is closed at "
            f"{ASK_CLASSES}"
        )
    entry = inventory_row(site_id)
    return {
        ASK_STRUCTURED: entry.structured,
        ASK_FREE_TEXT: entry.free_text,
        ASK_NONE: entry.unattended,
    }[ask_class]


# ---------------------------------------------------------------------------
# D5a/D5d — one renderer, two presentations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecisionOption:
    """One rendered option: a label and the command that enacts it.

    ``command`` is the payload. A structured host feeds these to its ask tool and a
    free-text host prints them, but in both cases what gets copied is the command on
    the selected line — so a mis-numbered reply cannot silently enact a different
    action, and the driving agent never maps prose to a flag value.

    ``command`` is ``None`` for an option that is enacted by *not* re-invoking
    (D5a's "skip = simply do not re-invoke"), which is the one case where there is
    nothing to copy.
    """

    label: str
    command: Optional[str]
    is_default: bool = False


#: The suffix marking the option a `--yes` run would have selected. Display only.
DEFAULT_SUFFIX = " (default)"


def render_option_block(
    site_id: str,
    options: Sequence[DecisionOption],
    *,
    prompt: Optional[str] = None,
) -> str:
    """The numbered option block, identical for both presentations (D5d).

    Numbering is Python's and stable: options are numbered from 1 in the order the
    caller supplied (D5a's "Options as rendered" column), the `--yes` option is
    suffixed ``(default)``, and the driving agent may not renumber, re-order, merge,
    drop or add options.
    """
    entry = inventory_row(site_id)
    if not entry.renderable:
        raise NeedsHuman(
            f"ERROR: decision site '{site_id}' is fail-closed (D6 row "
            f"{entry.rows[0]}) and is never rendered as a question on any host. "
            "The behavior is exit 3 with the fix named.",
            site=site_id,
        )
    if not options:
        raise NeedsHuman(
            f"ERROR: decision site '{site_id}' rendered zero options. An empty "
            "option list is never a default (D6 row 15).",
            site=site_id,
        )
    lines: List[str] = []
    if prompt:
        lines.append(prompt)
        lines.append("")
    for index, option in enumerate(options, start=1):
        suffix = DEFAULT_SUFFIX if option.is_default else ""
        tail = f" — {option.command}" if option.command else " — do not re-invoke"
        lines.append(f"{index}) {option.label}{suffix}{tail}")
    lines.append("")
    lines.append(
        "Copy exactly one option's command verbatim. Do not compose flags, do not "
        "paraphrase, and do not edit run state directly. A reply that selects zero "
        "or more than one option re-renders this block unchanged."
    )
    return "\n".join(lines)


def option_commands(options: Sequence[DecisionOption]) -> List[Optional[str]]:
    """The option payloads, in order — what both presentations resolve to."""
    return [option.command for option in options]


# ---------------------------------------------------------------------------
# Row 1 / D6c layer 3 — the uv backstop
# ---------------------------------------------------------------------------

#: Where the row-1 wording lives. Interpolated into every rendered shim by
#: ``install-host`` (D7) and read here, so shim and Python can never disagree
#: about how to install uv.
UV_MISSING_FILE = os.path.join("hosts", "uv-missing.txt")

#: Explicit override, also what the hermetic tests point at a stub. Same name
#: ``utils/detach.py`` uses for the worker re-exec, so one env var covers both.
UV_ENV = "MULTI_LLM_UV"

#: Probed in order, after ``PATH``. The Windows ``.exe`` variants are what the
#: official installer creates under Git Bash.
UV_CANDIDATES: Tuple[str, ...] = (
    "~/.local/bin/uv",
    "~/.local/bin/uv.exe",
    "~/.cargo/bin/uv",
    "~/.cargo/bin/uv.exe",
    "/opt/homebrew/bin/uv",
    "/usr/local/bin/uv",
    "/opt/local/bin/uv",
)


#: The flags every multi-llm **dispatch** carries, and the single owner of them.
#:
#: A dispatch is any ``uv run`` that reaches ``multi_llm.py``: the four consumers
#: named on :func:`uv_run_args` render them from here, and ``SKILL.md`` — the one
#: shim the host reads raw, so no token in it would ever be substituted — spells
#: them literally under a guard test that compares it back to this list. The
#: maintainer invocations (``uv run --project skills/multi-llm -- pytest`` in the
#: README and AGENTS.md) are deliberately outside that: they *want* the dev group,
#: which is the whole point of ``--no-dev`` on the other path.
#:
#: ``--no-dev`` is the load-bearing half and it was missing for a long time.
#: ``--frozen`` suppresses only the *lockfile staleness check*; it does not stop
#: the sync, and ``uv run`` syncs the **dev** group by default. Measured against
#: this repo's own tree: ``uv sync --frozen --dry-run`` would install 17 packages
#: (ruff, pytest, jsonschema and the rest), while ``--frozen --no-dev`` installs
#: one (pyyaml). So without ``--no-dev`` a user's first dispatch pulls the whole
#: dev group, and every offline posture fails outright on a package it never
#: needed.
#:
#: ``--frozen`` stays because it is what stops a dispatch rewriting the shipped
#: ``uv.lock``.
#:
#: Baking ``--no-dev`` in is safe rather than merely cheap: measured on uv
#: 0.11.28, ``uv sync --frozen --no-dev`` against a dev-synced environment would
#: uninstall all 16 dev packages, but ``uv run --frozen --no-dev`` against that
#: same environment leaves them in place and installs only what is missing. The
#: guarantee holds exactly as long as nothing on these paths calls ``uv sync
#: --no-dev``.
DEFAULT_UV_RUN_ARGS: Tuple[str, ...] = ("--frozen", "--no-dev")

#: Replaces :data:`DEFAULT_UV_RUN_ARGS` wholesale. **It never appends**, and that
#: is what makes the offline value expressible at all: an appended ``--no-sync``
#: would sit beside the very sync the setter is trying to suppress.
#:
#: Split on ASCII whitespace with no quote processing and no shell — no uv flag
#: contains a space, which is why the plain split is sufficient rather than merely
#: convenient. Unset, empty or whitespace-only means the default, so a stray
#: ``export MULTI_LLM_UV_RUN_ARGS=`` cannot silently re-enable the dev-group sync.
#:
#: Because it replaces, it **can legitimately drop ``--no-dev``**. That is the
#: setter's choice and the one documented way back into the 17-package first run.
#:
#: One precondition the documented offline value carries, because violating it is
#: silent: ``--no-sync`` against a tree whose ``.venv`` was never built does not
#: fail in uv. Measured on 0.11.28, uv *creates an empty environment and runs
#: against it anyway* — no uv-level error, no "sync first" — and the dispatcher
#: dies with ``ModuleNotFoundError: No module named 'yaml'`` at exit 1, with the
#: empty ``.venv`` persisting so every later run repeats it. That is a different
#: signature from the offline default's, which fails *inside* uv at the download
#: step (``Network connectivity is disabled, but the requested data wasn't found
#: in the cache``). So ``--no-sync`` is correct only against a venv something else
#: already built — a container image, a pre-warmed lane — and never on a first run.
UV_RUN_ARGS_ENV = "MULTI_LLM_UV_RUN_ARGS"


def uv_run_args() -> Tuple[str, ...]:
    """The flags to pass to ``uv run`` before ``--project``.

    One owner for four consumers that used to disagree: the foreground launcher,
    :func:`utils.cli_common.dispatcher_prefix` (which builds every printed
    follow-up and every ``MULTI_LLM_RESULT.next``), :func:`utils.detach
    .build_child_command` (the detached worker's re-exec) and
    :func:`utils.cli_common.render_instruction_text` (the ``{UV_RUN_FLAGS}`` token
    every command in ``instructions/*.md`` and in each ``hosts/*/shim.md.tmpl``
    carries, so the file route's verbatim runbook text cannot dispatch with a
    different flag list than Python does). Only the first was ever asserted, which
    is how the worker came to re-exec with neither flag — so a careful
    ``--detach``ed launch handed off to a child that recreated the 17-package sync
    in a log where nobody would see it.

    There is exactly one hand-typed spelling, and it is deliberate: Claude Code's
    ``SKILL.md`` is read raw by the host (it expands ``${CLAUDE_SKILL_DIR}``
    itself at load time), so a token there would reach an agent unsubstituted —
    while leaving it flagless would put the first-run dev-group sync on the host
    that runs most. ``tests/test_instruction_portability.py``'s
    ``TestTheClaudeShimSpellsTheFlagsOut`` compares that spelling back to this
    function, element for element, so the second copy cannot drift. Its one
    limitation is that those two shim-level commands are pinned to the default
    list — :data:`UV_RUN_ARGS_ENV` cannot reach text an agent types verbatim — and
    the core the shim loads at step 4 *is* rendered, so it does honour the
    override.
    """
    override = os.environ.get(UV_RUN_ARGS_ENV)
    if override is None:
        return DEFAULT_UV_RUN_ARGS
    tokens = tuple(override.split())
    return tokens or DEFAULT_UV_RUN_ARGS


def find_uv() -> Optional[str]:
    """The absolute path of a usable ``uv``, or ``None``.

    ``$MULTI_LLM_UV`` → ``PATH`` → :data:`UV_CANDIDATES`. Never installs
    anything, and never falls back to bare ``python``: the skill's dependencies
    are pinned in ``uv.lock`` and resolved by ``uv run`` from ``pyproject.toml``,
    so a bare interpreter turns a clear "install uv" into a
    ``ModuleNotFoundError`` or, worse, a silently wrong dependency version
    mid-fan-out (D6c).
    """
    override = os.environ.get(UV_ENV)
    if override and os.path.isfile(override):
        return os.path.abspath(override)
    found = shutil.which("uv")
    if found:
        return os.path.abspath(found)
    for candidate in UV_CANDIDATES:
        expanded = os.path.expanduser(candidate)
        if os.path.isfile(expanded):
            return expanded
    return None


def uv_missing_text(base: Optional[str] = None) -> str:
    """The row-1 message, read from ``hosts/uv-missing.txt``."""
    path = os.path.join(str(base) if base else str(skill_dir()), UV_MISSING_FILE)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().rstrip("\n")
    except OSError:
        # The message file is the single source; a partial install is the only
        # way to get here, so say so instead of duplicating the text.
        return (
            "[UV_MISSING] uv is required and was not found, and this install is "
            f"missing {path}.\n"
            "Install uv (https://docs.astral.sh/uv/getting-started/installation/) "
            "and re-run. There is no bare-`python` fallback."
        )


def require_uv() -> None:
    """Row 1, the run-time backstop (D6c layer 3).

    ``install-host --check`` (install time) and the shim preflight (invocation
    time) cover the common cases; this covers uv removed after install, a host
    invoking ``multi_llm.py`` directly, and a shim edited by hand. Same message,
    same exit 3.
    """
    if find_uv() is None:
        raise NeedsHuman(uv_missing_text(), site=row(1).site_id)


# ---------------------------------------------------------------------------
# Recording an auto-resolution
# ---------------------------------------------------------------------------

#: Prefix of the one stdout line every auto-resolution prints. Greppable in a
#: detached log and in a foreground transcript alike.
RESOLVED_MARKER = "[AUTO_RESOLVED]"


def record_resolution(
    phase_dir: Optional[str],
    site_id: str,
    decision: str,
    *,
    quiet: bool = False,
) -> None:
    """Announce and record one auto-resolved decision point.

    An auto-selection nobody can see afterwards is indistinguishable from a
    silent degradation, so this always prints ``[AUTO_RESOLVED] <site>:
    <decision>`` and, when a detached run owns *phase_dir*, appends the entry to
    ``{phase}/.status.json`` ``run.resolutions`` (D4c) — which is what
    ``status --view run`` reports. A foreground run's ``.status.json`` still gains
    no ``run`` keys: ``detach.record_resolution`` keeps its handle guard, because
    a resolution is part of the detached hand-back and the ``[AUTO_RESOLVED]``
    marker line *is* the foreground record. (Only ``progress`` reaches a
    foreground checkpoint, via ``detach.report_progress``; ``run`` stays the
    detached worker's alone.)
    """
    if site_id not in _ROWS_BY_SITE:  # pragma: no cover - guarded by tests
        raise KeyError(f"unknown D6 site id: {site_id!r}")
    if not quiet:
        print(f"{RESOLVED_MARKER} {site_id}: {decision}")
    if not phase_dir:
        return
    try:
        from . import detach as _detach  # local: keep `status` sub-second
    except ImportError:  # pragma: no cover - direct script runs
        import detach as _detach  # type: ignore
    try:
        _detach.record_resolution(str(phase_dir), site_id, decision)
    except Exception:  # pragma: no cover - recording must never break a phase
        pass


# ---------------------------------------------------------------------------
# Fail-closed helpers
# ---------------------------------------------------------------------------

def mark_needs_human(mode: Optional[str] = None) -> None:
    """Set ``MULTI_LLM_RESULT.state`` to ``needs-human`` for this invocation.

    A no-op under direct invocation (no dispatcher run is active), which is why
    it is safe to call from an orchestrator.
    """
    ctx = active_result()
    if ctx is None:
        return
    ctx.state = "needs-human"
    if mode:
        ctx.mode = mode


def fail_closed(
    message: str,
    *,
    site_id: Optional[str] = None,
    mode: Optional[str] = None,
    stream=None,
) -> int:
    """Print a fail-closed message, mark the result line, return exit 3."""
    out = stream if stream is not None else sys.stderr
    print(message, file=out)
    mark_needs_human(mode)
    if site_id and site_id not in _ROWS_BY_SITE:  # pragma: no cover
        raise KeyError(f"unknown D6 site id: {site_id!r}")
    return EXIT_NEEDS_HUMAN


# ---------------------------------------------------------------------------
# Row 3 — partial results are usable output, not a question
# ---------------------------------------------------------------------------

PARTIAL_MARKER = "[PARTIAL_RESULTS:"


def report_partial_results(
    *,
    completed: Sequence[str],
    failed: Sequence[str],
    phase_dir: Optional[str] = None,
    retry_command: Optional[str] = None,
    unattended: bool = False,
) -> int:
    """Row 3's disposition: resume once, then reaggregate what exists.

    Returns the exit code:

    * some models produced results → ``[PARTIAL_RESULTS: a,b]`` on stdout,
      ``MULTI_LLM_RESULT.state: "partial"``, **exit 0**. A partial aggregate is
      usable output, so this is deliberately never exit 3.
    * *no* model produced a result → **exit 3**: there is nothing to aggregate,
      and the retry command is named.

    The marker and the state are unconditional (they describe the *outcome*, which
    a host has to be able to read either way); the ``[AUTO_RESOLVED]`` line is
    recorded only under ``unattended``, because attended runs may still render the
    partial/resume/rerun gate and claiming it was auto-resolved would be a lie.
    """
    failed_list = [str(m) for m in failed]
    if not completed:
        message = (
            "ERROR: no model produced a result, so there is nothing to "
            "aggregate.\n"
            f"       Failed models: {', '.join(failed_list) or 'none recorded'}"
        )
        if retry_command:
            message += f"\n       Retry with: {retry_command}"
        return fail_closed(message, site_id=row(3).site_id)
    if failed_list:
        print(f"{PARTIAL_MARKER} {','.join(failed_list)}]")
        ctx = active_result()
        if ctx is not None:
            ctx.state = STATE_PARTIAL
        if unattended:
            record_resolution(
                phase_dir,
                row(3).site_id,
                # "continued", not "reaggregated": this call is the fan-out's
                # own in-process continuation past the models that failed,
                # never a separate --reaggregate invocation.
                f"continued with partial results; failed: {','.join(failed_list)}",
            )
    return EXIT_OK
