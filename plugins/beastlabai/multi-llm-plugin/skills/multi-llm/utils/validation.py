#!/usr/bin/env python3
"""
Shared validation utility for plan review and code review orchestrators.

Prepares the validation of grouped suggestions/issues for delegated subagents,
which filter false positives and identify items needing human review, then
merges and records their verdicts.
"""

import contextlib
import hashlib
import json
import os
import re
import sys
import threading
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from .atomic_io import atomic_write_bytes, read_back_text
from .held_folder import write_in_plan_dir
from .state_manager import generate_group_id, CURRENT_FORMAT_VERSION  # noqa: F401 - re-export
from .state_manager import group_join_ids, records_by_unique_id, stamped_group_id
from .cli_common import (
    current_replay_flags, durable_reaggregate_fields, retry_command,
    typed_plan_for,
)
from .subagent_prompts import build_validation_prompt, code_review_validation_guidance
from . import scope_policy as _sp
from . import review_round as _review_round
from . import scope_round as _scope_round
from . import validation_sections as _sections
from .schema_validator import VALIDATION_VERDICTS
from .subagent_tasks import (
    PromptBudget,
    TaskFileError,
    batch_manifest,
    build_inputs,
    content_hash,
    file_bytes_sha256,
    file_content_hash,
    make_task,
    make_task_file,
    split_indices,
    tasks_of,
)
from . import status_file
from . import cli_common as _cli
from . import process_control
from .validation_context import build_validation_context, validation_context_notice
from .status_file import read_status, remove_status_keys
from .commit_range import display_range, pinned_endpoints, pinned_head_read_rule
from .output_handler import output_dir_path
from .commit_report import context_plan_path, run_commit_range
from .git_utils import get_project_root


#: The shared-context ceiling for a validation prompt, applied **per context
#: block**. The whole-document excerpt is cut **once per phase** and reused by
#: every batch that embeds it; a batch never re-truncates it. A batch may
#: instead carry a *selection* — the plan sections its groups cite
#: (:mod:`utils.validation_sections`) or the code windows its issues cite —
#: which is a pure function of the round's inputs and the batch's records, so
#: prompts stay deterministic (docs/development/delegation.md, "Cited plan
#: sections").
#:
#: 60 000 rather than the original 30 000, because 30 000 was under the size of
#: a real plan and the prompt asks the validator to judge against it. Measured
#: on a review-code run over a 44 374-char plan: the excerpt ended in the middle
#: of one section, so every later section — the acceptance criteria and the
#: single source of truth for every tunable — reached no validator, and four of
#: the nine verdicts cited exactly those sections (they were right only because
#: that runner could open the file itself, which ``context_mode: inline`` does
#: not promise).
#:
#: Above the limit a plan or tasks document is no longer silently cut: the
#: excerpt stays (so prompts are deterministic and the common case needs no
#: read) and the round's hash-bound snapshot is named by path, the task
#: materializing ``context_mode: workspace-read``
#: (docs/development/delegation.md#code-review-validation-context). Only a
#: document with no readable file keeps the bare cut, and that is surfaced.
#:
#: What the raise costs, checked both ways. The **runner**: a prompt never
#: reaches a command line on a ``stdin``/``file`` transport and is unbounded on
#: POSIX (``subagent_tasks.prompt_budget_utf16``); the one bounded case is a
#: Windows ``argv`` runner at 32 511 units (7 935 through a cmd.exe shim), which
#: a single 30 000-char context already overran — so this moves no runner from
#: working to not working, and `PromptBudget` still splits or fails loudly
#: rather than truncating. The **file**: two full blocks put 120 000 chars in
#: every batch, so :data:`VALIDATION_TASKS_TOTAL_CHARS_CEILING` is only reached
#: at ~16 batches, and it is reported rather than enforced, with the same lever
#: (a larger ``max_per_batch``) still available.
VALIDATION_CONTEXT_LIMIT = 60000

#: The documented per-file ceiling on a phase's **materialized total** (D2f).
#: Embedding prompts reverses the reference-based design at a stated cost: the
#: one shared excerpt is duplicated into every batch, so the file grows with
#: batch count (D2f's own worked example is ~300–400 KB for ten batches). The
#: lever that shrinks it is a *larger* ``max_per_batch`` — fewer batches means
#: fewer copies of the excerpt — bounded above by the D2d per-task budget.
#: Crossing this ceiling is **reported, not resolved**. Validation now emits
#: ``context_mode: workspace-read`` for an over-limit document, but that is
#: decided per document by :data:`VALIDATION_CONTEXT_LIMIT`, never by this
#: file total: the excerpt stays in every batch either way, so a path cannot
#: shrink the file, and failing a phase outright would throw away a completed
#: fan-out over a scratch file being large.
VALIDATION_TASKS_TOTAL_CHARS_CEILING = 2_000_000

#: Sidecar beside ``validation_batch_{N}.json``, holding exactly the bytes of
#: that task's ``prompt``. ``.prompt.txt``, never ``.json``: the reaggregation
#: glob is ``*.json`` and both ``validation_batch_*.json`` globs (here and in
#: ``review_orchestrator_base.retire_stale_validation_round``) must keep
#: ignoring it. Invoker plumbing for a native-subagent host, whose only other
#: way to run a batch is to re-emit a ~65 KB prompt through its own context —
#: three real runs improvised the same dump-to-file by hand before this existed.
#: ``prompt`` stays the source of truth; the executor never opens this file.
PROMPT_SIDECAR_TEMPLATE = "validation_batch_{index}.prompt.txt"

#: The host index beside a task file: ``validation_tasks.json`` →
#: ``validation_tasks.index.json``. A view a native host reads instead of the
#: full file, whose ``prompt`` strings are ~90% of its bytes and are never read
#: by a host that hands its subagent the sidecar. The full file stays the source
#: of truth for the executor, ``check-reply``, the audit and the container
#: digest; nothing but a host reads the index
#: (docs/development/delegation.md#the-host-index).
HOST_INDEX_SUFFIX = ".index.json"

#: Per-task keys the index copies, in this order, from each task that has them.
#: A task whose sidecar was skipped has no ``prompt_path``, so its entry has none
#: either, and the host runs that task's ``prompt`` from the full file.
HOST_INDEX_TASK_KEYS = (
    "task_id", "batch_index", "prompt_path", "prompt_lines", "output_path",
    "subagent_type", "context_mode",
)

#: File-level keys the index copies when the task file has them: the batch
#: count and the durable pair the reaggregation command is rebuilt from.
HOST_INDEX_DOCUMENT_KEYS = ("total_batches", "reaggregate_mode", "plan_file")

#: The task files that have a host index beside them.
HOST_INDEXED_TASK_FILES = frozenset({
    "validation_tasks.json", "revalidation_tasks.json", "consolidation_tasks.json",
})

#: The phase dir's views mutex (:func:`host_views_lock`): held across every
#: invalidate → source or sidecar change → publish sequence of a host index.
#: Like every lock file here it is never unlinked.
HOST_VIEWS_LOCK_FILENAME = ".views.lock"

#: How long a views transaction waits for another holder before the run stops
#: with exit 3. A holder keeps it for one materialization and its task-file
#: write, one repair and its commit, or one read-and-publish.
HOST_VIEWS_LOCK_TIMEOUT_S = 60.0


def excerpt_context(context: str, limit: int = VALIDATION_CONTEXT_LIMIT) -> str:
    """Return the one shared context excerpt a phase's batches all embed."""
    if len(context) <= limit:
        return context
    return context[:limit] + "\n\n[... truncated ...]"


#: How many of a cut context's dropped section headings the stderr line names
#: before folding the rest into ``(+n more)``, and how long each may be.
_CUT_SECTIONS_NAMED = 3
_CUT_SECTION_TITLE_CHARS = 60

_ATX_HEADING = re.compile(r"^(#{1,3}) \S")
_CODE_FENCE = re.compile(r"^\s*(```|~~~)")


def _markdown_headings(text: str) -> Dict[int, List[Tuple[int, str]]]:
    """``{level: [(offset, line), …]}`` for the ATX headings outside code fences.

    A line scan rather than a multiline regex because a plan's ```bash``
    blocks are full of ``# comment`` lines, which a regex would file as level-1
    headings — and two of them would outnumber the real title.
    """
    by_level: Dict[int, List[Tuple[int, str]]] = {}
    offset = 0
    in_fence = False
    for line in text.splitlines(keepends=True):
        if _CODE_FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            match = _ATX_HEADING.match(line)
            if match:
                by_level.setdefault(len(match.group(1)), []).append(
                    (offset, line.rstrip("\n"))
                )
        offset += len(line)
    return by_level


def context_cut_sections(context: str, limit: int) -> Optional[Dict[str, Any]]:
    """The section arithmetic of a head-kept cut, or ``None`` (no cut, no headings).

    ``{"total", "kept", "cut", "dropped"}``: how many sections there are at the
    level :func:`describe_context_cut` counts, how many the excerpt keeps whole,
    the title of the one it cuts mid-way (``None`` when the cut lands on a
    boundary) and the titles it never shows. Shared by the stderr line, the
    in-prompt marker of a ``mode: path`` source and the published
    ``validation_context`` entry, so all three count the same sections.
    """
    if len(context) <= limit:
        return None
    by_level = _markdown_headings(context)
    if not by_level:
        return None
    level = next(
        (lvl for lvl in sorted(by_level) if len(by_level[lvl]) > 1),
        min(by_level),
    )
    headings = by_level[level]
    # A section is whole when the next one still starts inside the excerpt.
    starts = [start for start, _ in headings] + [len(context)]
    kept = sum(1 for nxt in starts[1:] if nxt <= limit)
    dropped = [title for start, title in headings if start >= limit]
    cut_mid = len(headings) - kept - len(dropped)
    return {
        "total": len(headings),
        "kept": kept,
        "cut": headings[kept][1] if cut_mid else None,
        "dropped": dropped,
    }


def describe_context_cut(context: str, limit: int) -> str:
    """What a head-kept cut of ``context`` at ``limit`` leaves out, by section.

    A raw "N chars over" says how much was lost and nothing about *what*: the
    run this was measured on cut a 336 026-char plan at 60 000 and printed
    ``276143 chars over``, while every verdict that came back cited a section —
    among them the implementation notes at the tail — that no validator had
    been shown. Named sections make the same line answer "did the part this
    review is about survive?" without opening the task file.

    Sections are the ATX headings (``#``/``##``/``###``) at the shallowest
    level that occurs more than once, so a plan's ``##`` phases count and its
    single ``#`` title does not; a document with no headings (a diff, plain
    text) gets the empty string and the line stays as it was.
    """
    cut = context_cut_sections(context, limit)
    if cut is None:
        return ""
    headings_total = cut["total"]
    kept = cut["kept"]
    dropped = cut["dropped"]

    def name(title: str) -> str:
        title = title.strip()
        if len(title) > _CUT_SECTION_TITLE_CHARS:
            title = title[: _CUT_SECTION_TITLE_CHARS - 1] + "…"
        return f"'{title}'"

    parts = [f"kept {kept} of {headings_total} sections whole"]
    if cut["cut"]:
        parts.append(f"cut {name(cut['cut'])} mid-section")
    if dropped:
        named = ", ".join(name(title) for title in dropped[:_CUT_SECTIONS_NAMED])
        more = len(dropped) - _CUT_SECTIONS_NAMED
        parts.append(
            f"dropped {len(dropped)}: {named}"
            + (f" (+{more} more)" if more > 0 else "")
        )
    return "; ".join(parts)


def excerpt_context_reported(
    context: str, block: str, limit: int = VALIDATION_CONTEXT_LIMIT
) -> str:
    """:func:`excerpt_context`, with the cut named on stderr.

    The only trace of a trim used to be the ``[... truncated ...]`` line inside
    the prompt, which nobody reads — so a 200 KB plan lost its whole tail (the
    acceptance criteria live there) and the run said nothing about it. One line
    per block, from the site that owns the budget, so an operator reading the
    log can see which half was over, by how much, and — for a document with
    headings — which sections went (:func:`describe_context_cut`).
    """
    if len(context) > limit:
        detail = describe_context_cut(context, limit)
        print(
            f"[VALIDATION_CONTEXT_TRUNCATED] {block} {len(context) - limit} "
            f"chars over" + (f"; {detail}" if detail else ""),
            file=sys.stderr,
        )
    return excerpt_context(context, limit)


# ---------------------------------------------------------------------------
# Validation context by path
# ---------------------------------------------------------------------------

#: The context contract a validation round is materialized under (task 2.10).
#: Contract 1 (no stamp) cut an over-limit document at the inline limit and
#: said so only inside the prompt; contract 2 keeps the excerpt and names a
#: hash-bound snapshot of the whole document by path. Every task file and every
#: merged ``validation.json`` carries the number, so a round built under the
#: old contract from an over-limit document can be recognised and retired
#: rather than reused.
CONTEXT_CONTRACT = 2

#: The round's hash-bound plan snapshot, written into *each* validating phase
#: dir (review-plan, review-tasks, review-code) from the one in-memory read of
#: the plan. Never ``backup.md``: that keeps its rollback/record meaning and is
#: a byte copy of the live file taken at a different moment.
PLAN_SNAPSHOT_NAME = "validation-snapshot.md"
#: review-tasks' second document, when ``tasks-backup.md`` does not hash-match.
TASKS_SNAPSHOT_NAME = "validation-tasks-snapshot.md"
TASKS_BACKUP_NAME = "tasks-backup.md"
#: A revalidation judges the *current* document (the one the apply step just
#: wrote), bound to its own fresh snapshot — never overwriting the original
#: round's ``validation-snapshot.md``, which the round's task file still binds.
REVALIDATION_SNAPSHOT_NAME = "revalidation-snapshot.md"

#: The bare cut :func:`excerpt_context` appends — what every contract-1 prompt
#: over the limit ends its context block with, and the evidence 2.10 reads.
LEGACY_TRUNCATION_MARKER = "[... truncated ...]"

#: A verdict whose reason starts with this is a validator saying it could not
#: read the document it was pointed at; the aggregate counts them
#: into ``validation_context.insufficient``.
INSUFFICIENT_CONTEXT_PREFIX = "insufficient-context:"

#: The named refusal for a snapshot that moved or vanished under a round.
SNAPSHOT_ERROR = "validation snapshot changed/missing; re-run validation"

#: Labels a ``mode: path`` source may carry. A diff and review-code's
#: reviewed-code block never get a path (2.1b, 2.6).
PATH_CAPABLE_LABELS = ("plan", "tasks")

_DOCUMENT_NOUN = {"plan": "plan", "tasks": "tasks file"}


class ValidationContextError(TaskFileError):
    """A validation round cannot bind its context; exit 3, nothing dispatched."""


def _bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_document(data: bytes, path: str) -> str:
    """Decode a document's bytes the way the round's excerpt is derived from them.

    Strict UTF-8 plus universal-newline translation — what ``read_plan``'s
    text-mode ``open`` did — so the excerpt a prompt carries is the text a
    reader of the file sees. The hash is always taken over the **bytes**, never
    over this. A document that does not decode refuses the round with a named
    error instead of hashing to ``""`` (which ``file_content_hash`` does).
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationContextError(
            f"{path} is not valid UTF-8 ({exc}); a validation round refuses a "
            f"document it cannot excerpt and hash from the same bytes. Re-save "
            f"it as UTF-8 and re-run. Nothing was dispatched."
        ) from exc
    return text.replace("\r\n", "\n").replace("\r", "\n")


class BoundDocument:
    """One context document bound for a validation round.

    ``text`` is what the excerpt is cut from, ``sha256``/``size`` are over the
    bytes the round read once, and ``path`` is the one absolute path a prompt
    may name for it — a snapshot inside the phase dir (``in_phase_dir``), or,
    only when the snapshot could not be written and the live file still
    hash-matches, the live file. ``path is None`` means nothing readable is
    bound and ``reason`` says why; an over-limit source then materializes
    ``mode: truncated``. ``forced_truncated`` marks a block the caller already
    cut on its own budget (review-code's reviewed-code windows), which is
    truncated whatever its final length.
    """

    def __init__(
        self,
        *,
        label: str,
        text: str,
        sha256: str,
        size: int,
        path: Optional[str] = None,
        in_phase_dir: bool = False,
        reason: Optional[str] = None,
        forced_truncated: bool = False,
        dropped_files: Optional[List[str]] = None,
        source_path: Optional[str] = None,
        files_total: Optional[int] = None,
    ) -> None:
        self.label = label
        self.text = text
        self.sha256 = sha256
        self.size = size
        self.path = path
        self.in_phase_dir = in_phase_dir
        self.reason = reason
        self.forced_truncated = forced_truncated
        self.dropped_files = list(dropped_files) if dropped_files else None
        self.source_path = source_path
        self.files_total = files_total

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"BoundDocument(label={self.label!r}, size={self.size}, "
            f"path={self.path!r}, reason={self.reason!r})"
        )


def _atomic_write_bytes(target: str, data: bytes) -> None:
    """Atomic write, so a reader never sees a half-written snapshot."""
    atomic_write_bytes(target, data)


def bind_document_file(
    source_path: str,
    phase_dir: str,
    *,
    label: str = "plan",
    snapshot_name: str = PLAN_SNAPSHOT_NAME,
    reuse_names: Tuple[str, ...] = (),
    data: Optional[bytes] = None,
) -> BoundDocument:
    """Read a document once, as bytes, and bind a snapshot of exactly those bytes.

    One read, one snapshot, one hash domain: the snapshot is
    written from the bytes read here, never copied from the live path, so its
    sha256 is the recorded one by construction. ``reuse_names`` are existing
    phase-dir files that may stand in for the snapshot when their raw sha256
    matches (review-tasks' ``tasks-backup.md``). When the snapshot cannot be
    written, the live file is named instead only if it still hash-matches the
    bytes read; otherwise nothing is bound and the source will be surfaced as
    ``mode: truncated``.

    Raises:
        ValidationContextError: the document is not UTF-8.
        OSError: the document itself cannot be read (the caller's existing
            "cannot read the plan" handling applies).
    """
    if data is None:
        data = Path(source_path).read_bytes()
    text = decode_document(data, source_path)
    digest = _bytes_sha256(data)
    common = dict(label=label, text=text, sha256=digest, size=len(data),
                  source_path=os.path.abspath(source_path))
    for name in reuse_names:
        candidate = os.path.join(phase_dir, name)
        if file_bytes_sha256(candidate) == digest:
            return BoundDocument(
                path=os.path.abspath(candidate), in_phase_dir=True, **common
            )
    target = os.path.join(phase_dir, snapshot_name)
    try:
        os.makedirs(phase_dir, exist_ok=True)
        _atomic_write_bytes(target, data)
        return BoundDocument(path=os.path.abspath(target), in_phase_dir=True, **common)
    except OSError as exc:
        live = file_bytes_sha256(source_path)
        if live and live == digest:
            print(
                f"Warning: could not write {target} ({exc}); the validation "
                f"prompts name the live file, which still matches the content "
                f"read.",
                file=sys.stderr,
            )
            return BoundDocument(path=os.path.abspath(source_path), **common)
        return BoundDocument(
            reason=(
                f"snapshot {snapshot_name} could not be written ({exc}) and "
                f"{os.path.basename(source_path)} no longer matches the content "
                f"read"
            ),
            **common,
        )


def bind_document_text(
    text: str,
    *,
    label: str,
    reason: Optional[str] = None,
    forced_truncated: bool = False,
    dropped_files: Optional[List[str]] = None,
    files_total: Optional[int] = None,
) -> BoundDocument:
    """A document with no file to name (a diff, review-code's reviewed-code block)."""
    data = text.encode("utf-8")
    return BoundDocument(
        label=label,
        text=text,
        sha256=_bytes_sha256(data),
        size=len(data),
        reason=reason or "the block has no file a validator could read",
        forced_truncated=forced_truncated,
        dropped_files=dropped_files,
        files_total=files_total,
    )


def _marker_title(title: str) -> str:
    title = title.lstrip("#").strip()
    if len(title) > _CUT_SECTION_TITLE_CHARS:
        title = title[: _CUT_SECTION_TITLE_CHARS - 1] + "…"
    return title


def path_marker(
    context: str, *, label: str, path: str, limit: int = VALIDATION_CONTEXT_LIMIT
) -> str:
    """The ``[... … truncated at N of M chars; …]`` marker of a ``mode: path`` source.

    Ask's marker (``ask_orchestrator.build_inline_plan``), extended with the
    sections the excerpt does not show and a read rule that is **not** tied to
    a citation: an absence claim ("the plan never defines retention") may cite
    an early section or none while its answer sits after the cut.
    """
    noun = _DOCUMENT_NOUN.get(label, label)
    cut = context_cut_sections(context, limit)
    if cut is not None and (cut["cut"] or cut["dropped"]):
        names = ([f"{_marker_title(cut['cut'])} (cut)"] if cut["cut"] else []) + [
            _marker_title(title) for title in cut["dropped"]
        ]
        not_shown = f"sections not shown: {', '.join(names)}"
    else:
        not_shown = f"everything after char {limit} is not shown"
    return (
        f"[... {noun} truncated at {limit} of {len(context)} chars; {not_shown}. "
        f"The file at {path} is the {noun} under review. Read it in full before "
        f"judging any suggestion that cites these sections, and before judging "
        f"any claim that the {noun} omits, never defines or never says "
        f"something, whichever section it cites ...]"
    )


def build_context_source(
    block_text: str,
    document: Optional[BoundDocument],
    *,
    label: str,
    block: str,
    phase_dir: str,
    limit: int = VALIDATION_CONTEXT_LIMIT,
    read_refusal: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """``(excerpt, context source record)`` for one context block.

    ``block_text`` is what the prompt embeds (not always ``document.text``: a
    caller may frame the document). The mode:

    * ``inline`` — the block fits, and no caller cut it on its own budget;
    * ``path`` — over the limit, a plan or tasks document with a readable bound
      file, and a runner that can read it (``read_refusal is None``);
    * ``truncated`` — every other over-limit case, with the reason.

    The record is JSON-able and is what the task stores under
    ``context_sources``: ``path`` relative to the phase dir when the file is a
    snapshot there (so a moved phase dir can rebind it, 2.9), ``abs_path`` the
    absolute path the prompt names.
    """
    size = document.size if document is not None else len(block_text.encode("utf-8"))
    record: Dict[str, Any] = {
        "label": label,
        "kind": label,
        "path": None,
        "abs_path": None,
        "sha256": document.sha256 if document is not None else None,
        "bytes": size,
        "chars_shown": len(block_text),
        "truncated": False,
        "mode": "inline",
    }
    forced = bool(document is not None and document.forced_truncated)
    if forced and document.dropped_files:
        record["dropped_files"] = list(document.dropped_files)
    if forced and document.files_total:
        # review-code's reviewed-code block counts cited FILES, not headings.
        record["sections_total"] = document.files_total
        record["sections_shown"] = document.files_total - len(document.dropped_files or [])
    if len(block_text) <= limit and not forced:
        return block_text, record

    cut = context_cut_sections(block_text, limit)
    if cut is not None and "sections_total" not in record:
        record["sections_total"] = cut["total"]
        record["sections_shown"] = cut["kept"]
        record["dropped_sections"] = (
            ([cut["cut"]] if cut["cut"] else []) + list(cut["dropped"])
        )
    over = len(block_text) > limit
    record["chars_shown"] = min(len(block_text), limit)
    record["truncated"] = True

    readable = (
        not forced
        and over
        and document is not None
        and document.path
        and label in PATH_CAPABLE_LABELS
    )
    if readable and read_refusal is None:
        abs_path = str(document.path)
        record["mode"] = "path"
        record["abs_path"] = abs_path
        record["path"] = (
            os.path.relpath(abs_path, os.path.abspath(phase_dir))
            if document.in_phase_dir else abs_path
        )
        record["in_phase_dir"] = bool(document.in_phase_dir)
        excerpt = block_text[:limit] + "\n\n" + path_marker(
            block_text, label=label, path=abs_path, limit=limit
        )
        detail = describe_context_cut(block_text, limit)
        print(
            f"[VALIDATION_CONTEXT_EXCERPTED] {label} {len(block_text) - limit} "
            f"chars over" + (f"; {detail}" if detail else "")
            + f"; full {_DOCUMENT_NOUN.get(label, label)} at {abs_path}",
            file=sys.stderr,
        )
        return excerpt, record

    record["mode"] = "truncated"
    if forced:
        reason = document.reason
    elif readable:
        reason = read_refusal
    elif document is None:
        reason = "no readable file is bound to this block"
    elif label not in PATH_CAPABLE_LABELS:
        reason = f"a {label} block is never named by path"
    else:
        reason = document.reason or "no readable file is bound to this block"
    record["reason"] = reason
    if over:
        excerpt = excerpt_context_reported(block_text, block, limit)
    else:
        # Cut upstream on the caller's own budget (review-code's windows), and
        # already reported there; the block itself fits.
        excerpt = block_text
    if reason:
        print(f"  (reason: {reason})", file=sys.stderr)
    return excerpt, record


def _path_inside(path: str, root: str) -> bool:
    real_root = os.path.realpath(root)
    real = os.path.realpath(path)
    return real == real_root or real.startswith(real_root.rstrip(os.sep) + os.sep)


def cited_plan_for_round(
    context: str,
    document: Optional[BoundDocument],
    *,
    read_refusal: Optional[str],
    runner_read_refusal: Optional[Any] = None,
) -> Optional["_sections.CitedPlan"]:
    """The round's parsed plan when its batches may carry cited sections, else ``None``.

    A batch that carries only the sections its groups cite still has to be able
    to reach the rest — an omission claim, or a group whose verdict turns on a
    section it does not cite — so a round qualifies only when every batch can
    name a readable, hash-bound snapshot of the whole plan:

    * the block is the bound ``plan`` document with a snapshot path;
    * the runner may read it (``read_refusal is None``) and, on a native host,
      the snapshot lies inside the project root the advisory checks;
    * the plan is at least :data:`validation_sections.CITED_MIN_CHARS` long and
      has section headings;
    * ``MULTI_LLM_VALIDATION_CONTEXT`` is ``cited``: the whole plan is the
      default until a live check shows verdicts hold up without it.

    Every other round embeds the whole plan in every batch.
    """
    if document is None or document.label != "plan" or not document.path:
        return None
    if len(context) < _sections.CITED_MIN_CHARS:
        return None
    if read_refusal is not None:
        return None
    if getattr(runner_read_refusal, "advisory_only", False):
        root = getattr(runner_read_refusal, "root", None)
        if root and not _path_inside(str(document.path), str(root)):
            return None
    if not _sections.cited_context_enabled():
        return None
    return _sections.CitedPlan.parse(context)


def cited_context_source(
    document: BoundDocument,
    excerpt: str,
    selection: "_sections.CitedSelection",
    *,
    phase_dir: str,
    sections_total: int,
) -> Dict[str, Any]:
    """The context source record of one batch's cited plan block.

    ``mode: path`` like an over-limit excerpt — the prompt names the snapshot
    and the task is ``workspace-read``, so dispatch, resume re-hashing and
    phase-dir rebinding treat it the same — with ``selection: cited`` saying
    the excerpt is the cited sections rather than the document's head.
    """
    abs_path = str(document.path)
    return {
        "label": "plan",
        "kind": "plan",
        "path": (
            os.path.relpath(abs_path, os.path.abspath(phase_dir))
            if document.in_phase_dir else abs_path
        ),
        "abs_path": abs_path,
        "sha256": document.sha256,
        "bytes": document.size,
        "chars_shown": len(excerpt),
        "truncated": True,
        "mode": "path",
        "in_phase_dir": bool(document.in_phase_dir),
        "selection": _sections.SELECTION_CITED,
        "sections_total": sections_total,
        "sections_shown": selection.sections_shown,
    }


def context_sources_of(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every task's ``context_sources`` records in a task file, flattened."""
    records: List[Dict[str, Any]] = []
    for task in tasks_of(document):
        for record in task.get("context_sources") or []:
            if isinstance(record, dict):
                records.append(record)
    return records


def verify_context_sources(document: Dict[str, Any], phase_dir: str) -> bool:
    """Re-hash every ``mode: path`` source; rebind a moved phase dir (2.3 step 5, 2.9).

    Runs right before dispatch, on every resume and on every ``--reaggregate``
    that reuses a materialized round. Each record's snapshot is resolved in the
    *current* phase dir (its ``path`` is phase-dir-relative) and its raw sha256
    compared with the recorded one. A missing file or a moved hash refuses the
    round (:data:`SNAPSHOT_ERROR`); it never re-points at whatever is on disk.
    When the phase dir was copied or moved, the prompt still names the old
    absolute path, so it is rematerialized with the rebound one — a prompt that
    names a path outside the current phase dir is never dispatched.

    Returns:
        Whether any task was rebound (the caller persists the document and its
        prompt sidecars).

    Raises:
        ValidationContextError: a snapshot is missing or changed.
    """
    changed = False
    here = os.path.abspath(phase_dir)
    for task in tasks_of(document):
        for record in task.get("context_sources") or []:
            if not isinstance(record, dict) or record.get("mode") != "path":
                continue
            old_abs = str(record.get("abs_path") or "")
            rel = record.get("path")
            if record.get("in_phase_dir") and rel and not os.path.isabs(str(rel)):
                expected = os.path.normpath(os.path.join(here, str(rel)))
                task_id = task.get("task_id", "<unnamed>")
                # 2.9: an in-phase-dir record rebinds only inside the current
                # phase dir. A forged or hand-edited ``..`` path would otherwise
                # rebind the prompt to a file outside it.
                if os.path.commonpath([here, expected]) != here:
                    raise ValidationContextError(
                        f"{SNAPSHOT_ERROR}: {rel} resolves to {expected}, outside "
                        f"the phase dir (task {task_id}, {record.get('label')}). "
                        f"Phase dir: {here}. Re-run the phase with --force to "
                        f"rematerialize it. Nothing was dispatched."
                    )
            else:
                expected = old_abs
            actual = file_bytes_sha256(expected)
            task_id = task.get("task_id", "<unnamed>")
            if not actual:
                raise ValidationContextError(
                    f"{SNAPSHOT_ERROR}: {expected} is missing (task {task_id}, "
                    f"{record.get('label')}). Phase dir: {here}. Re-run the phase "
                    f"with --force to rematerialize it. Nothing was dispatched."
                )
            if actual != record.get("sha256"):
                raise ValidationContextError(
                    f"{SNAPSHOT_ERROR}: {expected} changed (sha256 {actual[:12]} != "
                    f"recorded {str(record.get('sha256'))[:12]}; task {task_id}, "
                    f"{record.get('label')}). Phase dir: {here}. Re-run the phase "
                    f"with --force to rematerialize it. Nothing was dispatched."
                )
            if old_abs and expected != old_abs:
                task["prompt"] = str(task.get("prompt", "")).replace(old_abs, expected)
                if task.get("prompt_lines"):
                    task["prompt_lines"] = task["prompt"].count("\n") + 1
                record["abs_path"] = expected
                changed = True
                print(
                    f"[VALIDATION_CONTEXT_REBOUND] {task_id}: {old_abs} -> "
                    f"{expected} (sha256 verified)",
                    file=sys.stderr,
                )
    return changed


def legacy_context_round_reason(
    phase_dir: str,
    tasks_name: str = "validation_tasks.json",
) -> Optional[str]:
    """Why a round in ``phase_dir`` was built under context contract 1, or ``None``.

    A task file with no ``context_contract`` (or an older one) whose stored
    prompts carry the contract-1 cut (:data:`LEGACY_TRUNCATION_MARKER`) judged
    an over-limit document from its head alone. Its prompts, and every verdict
    reached from them, must not be reused (task 2.10). A round under the limit
    carries no marker and stays valid.
    """
    path = os.path.join(phase_dir, tasks_name)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return None
    return legacy_context_document_reason(document, tasks_name)


def legacy_context_document_reason(
    document: Any, tasks_name: str = "validation_tasks.json",
) -> Optional[str]:
    """:func:`legacy_context_round_reason` for a task document already read."""
    if not isinstance(document, dict):
        return None
    try:
        contract = int(document.get("context_contract") or 1)
    except (TypeError, ValueError):
        contract = 1
    if contract >= CONTEXT_CONTRACT:
        return None
    truncated = [
        str(task.get("task_id", "?"))
        for task in tasks_of(document)
        if LEGACY_TRUNCATION_MARKER in str(task.get("prompt", ""))
    ]
    if not truncated:
        return None
    return (
        f"validation built from truncated context (contract {contract}); "
        f"rematerializing — {tasks_name} batches {', '.join(truncated[:3])}"
        + (" ..." if len(truncated) > 3 else "")
        + f" cut the document at {VALIDATION_CONTEXT_LIMIT} chars"
    )


def count_insufficient(results: List[Dict[str, Any]]) -> int:
    """Verdicts whose reason starts ``insufficient-context:``."""
    return sum(
        1
        for result in results or []
        if isinstance(result, dict)
        and str(result.get("reason", "")).strip().lower().startswith(
            INSUFFICIENT_CONTEXT_PREFIX
        )
    )


def publish_validation_context(
    phase_dir: str,
    sources: List[Dict[str, Any]],
    insufficient: Optional[int] = None,
    *,
    phase: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """The one writer of ``.status.json``'s ``validation_context``.

    Aggregates the round's context source records (one entry per document
    label, worst mode wins), writes the object wholesale with
    ``update_status`` and records the same object on the dispatcher's result
    line (``cli_common.record_validation_context``); a round with a
    ``truncated`` source also sets the result ``notice`` (a round without one
    clears it). When every source is inline the key is deleted
    (``remove_status_keys``, never written ``null``) and nothing is recorded,
    so a rerun whose context fits leaves no trace of an earlier round.

    Returns:
        The published object, or ``None`` when the round is all inline.
    """

    obj = build_validation_context(
        phase=phase or os.path.basename(os.path.abspath(phase_dir)),
        sources=sources,
        limit=VALIDATION_CONTEXT_LIMIT,
        insufficient=insufficient,
    )
    if obj is None:
        # Remove an earlier round's key, but never create a checkpoint just to
        # say "nothing": a phase with no .status.json keeps having none.
        # ``update_status`` merges and cannot delete: ``{"k": None}`` would
        # leave a ``"validation_context": null`` member behind.
        if "validation_context" in read_status(phase_dir):
            remove_status_keys(phase_dir, ["validation_context"])
        recorder = getattr(_cli, "record_validation_context", None)
        if recorder is not None:
            recorder(None)
        _cli.record_notice(None)
        return None
    status_file.update_status(phase_dir, {"validation_context": obj})
    recorder = getattr(_cli, "record_validation_context", None)
    if recorder is not None:
        recorder(obj)
    # A same-process republish must not keep an earlier round's sentence.
    _cli.record_notice(validation_context_notice(obj) or None)
    return obj


def publish_from_task_document(
    phase_dir: str,
    document: Optional[Dict[str, Any]],
    results: Optional[List[Dict[str, Any]]] = None,
    *,
    phase: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Re-publish at aggregation from a task file's own recorded sources.

    The aggregation callers (first run, ``--reaggregate``, the executor lane)
    publish from the bound round's ``context_sources`` — never from the live
    plan — plus the ``insufficient`` count of the merged verdicts.
    """
    if not isinstance(document, dict):
        return None
    return publish_validation_context(
        phase_dir,
        context_sources_of(document),
        count_insufficient(results or []) if results is not None else None,
        phase=phase,
    )


def materialized_total_chars(tasks: List[Dict[str, Any]]) -> int:
    """Prompt characters a phase's task file will carry — the D2f file total."""
    return sum(len(task.get("prompt", "")) for task in tasks)


def sidecar_path(phase_dir: str, batch_index: int) -> str:
    """Absolute path of one batch's prompt sidecar inside ``phase_dir``."""
    return os.path.join(phase_dir, PROMPT_SIDECAR_TEMPLATE.format(index=batch_index))


def _write_one_sidecar(target: str, prompt: str) -> None:
    r"""Atomic, byte-identical write.

    No newline translation (the UTF-8 bytes of ``prompt``, ``\n`` as ``\n``) is
    load-bearing: a text-mode write on Windows would rewrite ``\n`` as
    ``\r\n`` and the file would no longer equal ``prompt`` — and byte
    identity is the whole contract, since a host hands a subagent this file
    *instead of* the prompt. A failed write leaves no temp file behind, so the
    all-or-none rule's cleanup of the sidecars already written is complete.
    Published through the phase folder held below the plan's directory: a link
    swapped in for it during the run is refused (``OSError``), never written
    through (docs/development/write-safety.md#plan-output-containment).
    """
    write_in_plan_dir(target, prompt.encode("utf-8"))


def write_prompt_sidecars(
    tasks: List[Dict[str, Any]],
    phase_dir: str,
    stale_glob: str = "validation_batch_*.prompt.txt",
) -> bool:
    """Write every task's prompt sidecar; all tasks or none.

    Each task already carries ``prompt_path``/``prompt_lines`` (set by the
    caller before :func:`make_task`, so the schema saw them). *stale_glob*
    names the kind's own sidecars in *phase_dir*, removed first: validation's
    by default; consolidation (``consolidation_batch_*.prompt.txt``) and task
    generation (``task_generation.prompt.txt``) pass theirs. A phase where some
    tasks carry the key and others do not invites non-identical prompt bytes
    across batches, so on any ``OSError`` every written file is removed, both
    keys are popped from every task, one ``[PROMPT_SIDECAR_SKIPPED]`` line goes
    to stderr and ``False`` comes back: the run continues on ``prompt`` alone.
    Degrades rather than raises — a scratch-file write failing must not throw
    away a completed fan-out.

    Returns:
        Whether the sidecars are on disk and the keys still on the tasks.
    """
    written: List[str] = []
    try:
        os.makedirs(phase_dir, exist_ok=True)
        # A wider previous round may have left higher-numbered sidecars.
        # Cleanup is optional too: a locked file must not abort materialization
        # or leave any task advertising a prompt from that earlier round.
        for stale in Path(phase_dir).glob(stale_glob):
            stale.unlink(missing_ok=True)
        for task in tasks:
            _write_one_sidecar(task["prompt_path"], task["prompt"])
            written.append(task["prompt_path"])
    except OSError as exc:
        for path in written:
            try:
                os.unlink(path)
            except OSError:
                pass
        for task in tasks:
            task.pop("prompt_path", None)
            task.pop("prompt_lines", None)
        print(
            f"[PROMPT_SIDECAR_SKIPPED] {exc}; every task keeps `prompt` only",
            file=sys.stderr,
        )
        return False
    return True


def host_index_path(task_file: str) -> str:
    """The host index beside *task_file* (:data:`HOST_INDEX_SUFFIX`)."""
    stem, _ext = os.path.splitext(task_file)
    return stem + HOST_INDEX_SUFFIX


def task_file_for_kind(phase_dir: str, kind: str) -> str:
    """Where a sidecar-carrying kind's task file lives: ``<kind>_tasks.json``.

    True of all four (``validation``, ``revalidation``, ``consolidation``,
    ``task_generation``); ``task_result.RESERVED_OUTPUT_SUFFIXES`` keys
    on the same shape.
    """
    return os.path.join(phase_dir, f"{kind}_tasks.json")


def build_host_index(document: Dict[str, Any], task_file: str) -> Dict[str, Any]:
    """The host's view of *document*: what a host dispatches from, no prompts."""
    list_key = "batches" if "batches" in document else "tasks"
    index: Dict[str, Any] = {"index_of": os.path.basename(task_file)}
    for key in HOST_INDEX_DOCUMENT_KEYS:
        if key in document:
            index[key] = document[key]
    index[list_key] = [
        {key: task[key] for key in HOST_INDEX_TASK_KEYS if key in task}
        for task in tasks_of(document)
        if isinstance(task, dict)
    ]
    return index


def remove_host_view(path: str) -> None:
    """Remove the host view at *path*, or stop the run with exit 3 naming it.

    A view (a task file's index, an apply phase's summary or batch detail) goes
    before the file it describes changes, and whenever it cannot be rebuilt, so
    a host finds a view of that file as it is or none, and then reads the file.
    One that cannot be removed would be read in the file's place, so the run
    stops instead of going on beside it
    (docs/development/delegation.md#the-host-index).
    """
    if not os.path.lexists(path):
        return
    try:
        os.unlink(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        print(
            f"ERROR: Cannot remove {path} ({exc}). It is a host's view of a file "
            f"this run is changing, and a host would read it in that file's "
            f"place. Nothing was handed out: make "
            f"{os.path.dirname(os.path.abspath(path))} writable or remove the "
            f"file, then run the command again.",
            file=sys.stderr,
        )
        sys.exit(3)


def publish_host_view(path: str, text: str) -> bool:
    """Write the host view *path* atomically; ``False``, with none on disk, if not.

    Degrades like the sidecars: a host that finds no view reads the file it
    would have described, the fallback every instruction names.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        _write_one_sidecar(path, text)
    except OSError as exc:
        remove_host_view(path)
        print(
            f"WARNING: {os.path.basename(path)} not written ({exc}); a host reads "
            "the file it describes instead",
            file=sys.stderr,
        )
        return False
    return True


class _ViewsLockState:
    """One phase dir's views lock in this process: a thread lock, then the file."""

    def __init__(self) -> None:
        self.thread_lock = threading.RLock()
        self.depth = 0
        self.mutex: Any = None


_VIEWS_LOCKS_GUARD = threading.Lock()
_VIEWS_LOCKS: Dict[str, _ViewsLockState] = {}


def host_views_lock_path(phase_dir: str) -> str:
    """The phase dir's views mutex (:data:`HOST_VIEWS_LOCK_FILENAME`)."""
    return os.path.join(str(phase_dir), HOST_VIEWS_LOCK_FILENAME)


@contextlib.contextmanager
def host_views_lock(phase_dir: str) -> Iterator[bool]:
    """Hold *phase_dir*'s views mutex, across threads and processes.

    Every sequence that invalidates a host index, changes its task file or the
    sidecars the index points at, and publishes the index again runs inside one
    of these, so a refresh never reads the file before a change and publishes
    after it (docs/development/delegation.md#the-host-index). Reentrant in one
    thread: only the outermost frame takes the interprocess lock, which is held
    per open file description.

    Yields whether the interprocess lock is held. A lock file that cannot be
    opened or locked at all (a missing or read-only phase dir, a file system
    without locks) yields ``False`` at once: the body still runs and still
    invalidates, but publishes no view, so a host reads the full file. Another
    holder that keeps the lock for :data:`HOST_VIEWS_LOCK_TIMEOUT_S` stops the
    run with exit 3 naming the lock file.
    """
    key = os.path.realpath(host_views_lock_path(phase_dir))
    with _VIEWS_LOCKS_GUARD:
        state = _VIEWS_LOCKS.setdefault(key, _ViewsLockState())
    deadline = time.monotonic() + HOST_VIEWS_LOCK_TIMEOUT_S
    if not state.thread_lock.acquire(timeout=HOST_VIEWS_LOCK_TIMEOUT_S):
        _views_lock_timeout(key)
    try:
        if state.depth == 0:
            mutex = process_control.FileMutex(key)
            taken = mutex.acquire(
                timeout_s=max(0.0, deadline - time.monotonic()), poll_interval_s=0.02,
            )
            if not taken and time.monotonic() >= deadline:
                _views_lock_timeout(key)
            state.mutex = mutex if taken else None
        state.depth += 1
        try:
            yield state.mutex is not None
        finally:
            state.depth -= 1
            if state.depth == 0 and state.mutex is not None:
                state.mutex.release()
                state.mutex = None
    finally:
        state.thread_lock.release()


def _views_lock_timeout(key: str) -> None:
    print(
        f"ERROR: {key} was not free within {HOST_VIEWS_LOCK_TIMEOUT_S:g}s: another "
        f"multi-llm command is updating this phase's task file and its host "
        f"index. Nothing was handed out: run the command again once that one has "
        f"finished.",
        file=sys.stderr,
    )
    sys.exit(3)


def _view_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def invalidate_host_index(task_file: str) -> None:
    """Remove *task_file*'s host index before the file or its sidecars change.

    Under the views lock (:func:`host_views_lock`). Exit 3 when it cannot be
    removed (:func:`remove_host_view`).
    """
    with host_views_lock(os.path.dirname(os.path.abspath(task_file))):
        remove_host_view(host_index_path(task_file))


def refresh_host_index(task_file: str) -> bool:
    """Rebuild *task_file*'s host index from the file as it is on disk.

    The only writer of an index, run once the file has been written: at every
    hand-back of a round to the host (``dispatch_subagent_tasks``) and by
    ``prepare_consolidation_tasks``. Built from the committed file, never from a
    document in memory, so the index never describes a file newer or older than
    the one beside it. The read and the publication are one step under the
    views lock (:func:`host_views_lock`). An index whose bytes are already the
    ones it would write is left alone: nothing is replaced or removed. A
    missing or unreadable task file leaves no index; a file not in
    :data:`HOST_INDEXED_TASK_FILES` is left alone. Returns whether an index is
    on disk.
    """
    if os.path.basename(task_file) not in HOST_INDEXED_TASK_FILES:
        return False
    target = host_index_path(task_file)
    with host_views_lock(os.path.dirname(os.path.abspath(task_file))) as serialized:
        try:
            with open(task_file, "r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, ValueError):
            document = None
        if not isinstance(document, dict):
            remove_host_view(target)
            return False
        text = json.dumps(build_host_index(document, task_file), indent=2) + "\n"
        if _view_bytes(target) == text.encode("utf-8"):
            return True
        if not serialized:
            remove_host_view(target)
            print(
                f"WARNING: {os.path.basename(target)} not written (its views lock "
                f"{HOST_VIEWS_LOCK_FILENAME} cannot be taken); a host reads the "
                "file it describes instead",
                file=sys.stderr,
            )
            return False
        return publish_host_view(target, text)


def ensure_prompt_sidecars(document: Dict[str, Any], phase_dir: str) -> bool:
    """Rewrite any sidecar that is missing or whose bytes differ from ``prompt``.

    Covers a moved or copied phase dir (whose recorded absolute ``prompt_path``
    is stale) and a hand-edited sidecar. Tasks without sidecar metadata keep
    using their inline prompt. The comparison target is derived from the
    *loaded-from* ``phase_dir``, the same rule
    :func:`subagent_tasks.resolve_output_path` follows for ``output_name`` — so
    a copied dir heals itself rather than rewriting a file next to the original.
    No new ``inputs`` key and no new refusal: ``prompt`` is right there to
    compare against, so a ``prompt_sha256`` field would only restate it.

    Returns whether task metadata changed. The caller must persist those
    changes before handing the task file back to a native host, holding
    :func:`host_views_lock` across this call and that write.

    The round's host index is removed before the first sidecar or pointer
    changes, and left alone when nothing does: the caller may persist the
    document next, and the hand-back rebuilds the index from the file it
    persisted (:func:`refresh_host_index`).
    """
    index_of = task_file_for_kind(phase_dir, str(document.get("kind") or "validation"))
    with host_views_lock(phase_dir):
        changed = False
        for task in document.get("batches", []):
            if not task.get("prompt_path"):
                continue
            expected = sidecar_path(os.path.abspath(phase_dir), task["batch_index"])
            try:
                with open(expected, "rb") as handle:
                    same = handle.read() == task["prompt"].encode("utf-8")
            except OSError:
                same = False
            if not same:
                invalidate_host_index(index_of)
                try:
                    _write_one_sidecar(expected, task["prompt"])
                except OSError as exc:
                    # The incorrect file may still exist. Remove its advertised
                    # pointer so the native host actually takes the inline fallback.
                    task.pop("prompt_path", None)
                    task.pop("prompt_lines", None)
                    changed = True
                    print(
                        f"[PROMPT_SIDECAR_SKIPPED] {exc}; "
                        f"{os.path.basename(expected)} keeps `prompt` only",
                        file=sys.stderr,
                    )
                    continue
                print(
                    f"[PROMPT_SIDECAR_REWRITTEN] {os.path.basename(expected)}",
                    file=sys.stderr,
                )
            lines = task["prompt"].count("\n") + 1
            if task["prompt_path"] != expected or task.get("prompt_lines") != lines:
                invalidate_host_index(index_of)
                task["prompt_path"] = expected
                task["prompt_lines"] = lines
                changed = True
        return changed


# Error type constants - ALWAYS use these constants, never raw strings
ERROR_TYPE_PARSING = "parsing_error"
ERROR_TYPE_TIMEOUT = "timeout"
ERROR_TYPE_RATE_LIMITED = "rate_limited"
ERROR_TYPE_AMBIGUOUS = "real_ambiguity"  # For genuine LLM-determined ambiguity
ERROR_TYPE_MODEL_FAILURE = "model_failure"
ERROR_TYPE_UNKNOWN = "unknown"

# Define which error types are recoverable (can be retried/auto-approved)
RECOVERABLE_ERROR_TYPES = frozenset({
    ERROR_TYPE_PARSING,
    ERROR_TYPE_TIMEOUT,
    ERROR_TYPE_RATE_LIMITED,
})


def _reported_group_index(result: Dict[str, Any]) -> int:
    """The ``group_index`` a verdict echoed, as an int, or ``-1`` when it is not one.

    The echo is advisory — ``group_hash`` is what results are joined on — so an
    echo that is not an index must degrade to "matches nothing", never to a
    ``TypeError`` inside the index-based fallbacks that compare it against real
    indices. The reply contract now shows ``group_index`` as an unfillable
    placeholder (``<the group's group_index value>``) precisely so a model cannot
    copy a literal ``0``; a model that copies the *placeholder* instead sends a
    string, which is exactly the input this function absorbs. A numeric string
    (``"3"``) is a transcription of a real index and is accepted as one.

    Args:
        result: One verdict record as the subagent returned it.

    Returns:
        The echoed index, or ``-1`` for an absent, null or unparseable one.
    """
    raw = result.get("group_index", result.get("index", -1))
    if isinstance(raw, bool):  # bools are ints in Python; an index they are not
        return -1
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw) if raw.is_integer() else -1
    if isinstance(raw, str):
        try:
            return int(raw.strip())
        except ValueError:
            return -1
    return -1


def apply_validation_to_groups(
    groups: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply validation results to groups by adding validation status.

    Uses group_id (the group's stamped ``group_hash``) for matching when
    available. This ensures validation results remain correctly associated
    with groups even after reaggregation changes the sort order, and keeps
    same-content groups apart: each joins only a record filed under an id
    that names it alone (``state_manager.group_join_ids``), and an id two
    records carry joins neither.

    The ``group_index`` fallback exists for *hash-less* records only — the
    pre-hash ``validation.json`` format, where the index was the identity. A
    hashed record that matches no group is a verdict about a group that no
    longer exists (the grouping changed underneath it, D7); handing it to
    whichever group now sits at its index attributes another group's status,
    reason and confidence to it, so such a group is left at the default
    "No validation result" and the count of those groups is printed.

    Scope authority follows the same rule, only stricter: a group's
    ``scope_verdict`` is attached (``scope_policy.attach_verdict``) only from a
    record its stable hash joined, and only when the host stamped that record
    at merge time. The ``group_index`` fallback carries validity alone and
    removes any verdict, so a hash-less legacy record reads ``Scope unclear``.

    Args:
        groups: Original groups (list of dicts or SuggestionGroup objects)
        validation_results: The merged validation records (one per group)

    Returns:
        Groups with validation_status and validation_reason added
    """
    # Build lookups - group_id for hashed records, group_index for the rest
    validation_by_id = records_by_unique_id(validation_results, "group_id")
    validation_by_index = {
        r["group_index"]: r
        for r in validation_results
        if not r.get("group_id")
    }

    default_validation = {
        "status": "needs-human-decision",
        "reason": "No validation result",
        "confidence": 0.0
    }

    updated_groups = []
    unmatched = 0
    join_ids = group_join_ids(groups)
    for i, group in enumerate(groups):
        # Handle both dict and SuggestionGroup objects
        if hasattr(group, 'to_dict'):
            group_dict = group.to_dict()
        else:
            group_dict = dict(group)

        # group_id first; the index only reaches records that carry no hash
        by_hash = next(
            (validation_by_id[key] for key in join_ids[i] if key in validation_by_id),
            None,
        )
        validation = by_hash or validation_by_index.get(i)
        if validation is None:
            validation = default_validation
            unmatched += 1
        # Scope authority by stable hash only — never by index.
        _sp.attach_verdict(group_dict, by_hash, hash_matched=by_hash is not None)

        group_dict["validation_status"] = validation.get("status", "needs-human-decision")
        group_dict["validation_reason"] = validation.get("reason", "")
        # `default_validation` above sets an explicit 0.0 for "no result at all"
        # (a real, meaningful zero); omitting the `.get()` default here only
        # changes the other case — a real record that omitted `confidence` —
        # which now comes through as None instead of a manufactured 0.0.
        group_dict["validation_confidence"] = validation.get("confidence")
        # Copy error_type and recoverable fields if present
        if "error_type" in validation:
            group_dict["validation_error_type"] = validation.get("error_type")
        if "recoverable" in validation:
            group_dict["validation_recoverable"] = validation.get("recoverable")

        updated_groups.append(group_dict)

    if unmatched:
        print(
            f"[validation] {unmatched} of {len(updated_groups)} groups have no "
            f"validation result (left at needs-human-decision)"
        )

    return updated_groups


def _short_hash(value: Optional[str]) -> str:
    """The first 12 hex of a sha256 for a log line (``missing`` when empty)."""
    return value[:12] if value else "missing"


def _read_task_manifest(tasks_path: Optional[Path]) -> Tuple[Optional[Dict[str, str]], List[Dict[str, Any]]]:
    """``(batch_manifest, tasks)`` of the task file at ``tasks_path``, or ``(None, [])``.

    A plain read, not :func:`subagent_tasks.read_task_file`: this only asks
    *which round* the file describes, and the caller that goes on to use the
    file runs the full version/inputs guard itself.
    """
    if tasks_path is None:
        return None, []
    try:
        with open(tasks_path, 'r', encoding='utf-8') as f:
            document = json.load(f)
    except (OSError, ValueError):
        return None, []
    return _task_manifest_of(document)


def _task_manifest_of(document: Any) -> Tuple[Optional[Dict[str, str]], List[Dict[str, Any]]]:
    """:func:`_read_task_manifest` for a task document already read (``None``:
    there was none to read, or it could not be)."""
    if not isinstance(document, dict):
        return None, []
    return batch_manifest(document), tasks_of(document)


#: :func:`validation_source_decision`'s *task_document* when the caller read no
#: task file: the decision reads it itself.
UNREAD = object()


def _batch_file_group_hashes(path: Path) -> set:
    """The ``group_hash`` values a batch file's verdicts echo (empty when unreadable)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return set()
    results = data.get("groups", []) if isinstance(data, dict) else data
    if not isinstance(results, list):
        return set()
    return {
        str(r.get("group_hash") or r.get("group_id"))
        for r in results
        if isinstance(r, dict) and (r.get("group_hash") or r.get("group_id"))
    }


def validation_source_decision(
    validation_path: Path,
    grouped_path: Path,
    tasks_path: Optional[Path] = None,
    *,
    validation_bytes: Optional[bytes] = None,
    grouped_text: Optional[str] = None,
    task_document: Any = UNREAD,
) -> Tuple[Optional[str], str]:
    """``(stale_reason, use_note)`` for a ``validation.json``.

    ``stale_reason`` is ``None`` when the file may be used, else the one-line
    reason it must be retired and the batch files re-merged. ``use_note`` is the
    parenthetical the caller prints when it *does* use the file, naming what was
    checked.

    The checks, in order:

    1. **Grouping (D7).** ``metadata.grouped_sha256`` must match the
       ``grouped.json`` beside it now.
    2. **Batch bytes.** A file written by ``merge_validation_batches``
       records ``metadata.batch_sha256 = {batch_index: sha256}`` over the bytes
       of every batch it merged, plus ``metadata.batch_manifest = {kind,
       round}`` of the task file those batches answered. It is retired when a
       listed non-``.stale`` batch's bytes now hash differently, a listed batch
       is missing, the recorded ``kind``/``round`` differs from the current
       ``validation_tasks.json`` (revalidation reuses the
       ``validation_batch_<n>.json`` names with a different subset mapping), or
       the current round has a batch file on disk the file never merged.
       Content, never mtime: a ``cp -p`` restore keeps an old mtime and a
       ``git checkout`` sets every mtime to now, and neither says anything
       about which verdicts the file holds.
    3. **Legacy fallback only.** A file with no ``batch_sha256`` (written before
       the binding existed, or by a writer that merges no batches of this round)
       keeps the old
       mtime test: it is honoured only if no ``validation_batch_*.json`` beside
       it is newer. No merge writes a file without the binding any more.

    Hook point: a further check on a bound, up-to-date file (the context
    contract, task 2.10) belongs after check 2, before the use note is built.

    Args:
        validation_path: The ``validation.json`` to judge.
        grouped_path: The ``grouped.json`` it must belong to.
        tasks_path: The current task file; defaults to the
            ``validation_tasks.json`` beside ``validation_path``.
        validation_bytes: ``validation_path``'s bytes, when the caller has read
            them to use the verdicts they hold: they are judged, never the
            file again.
        grouped_text: ``grouped_path``'s text, when the caller holds the
            grouping it reports (read, or written, as a text-mode read returns
            it): its digest is checked, never the file's
            (docs/development/review-results.md, "Consuming checked bytes").
        task_document: ``tasks_path`` as the caller read it, once, to reuse
            the verdicts against (``None``: absent or unreadable): the round
            and contract checks read this document, never the file again.
            :data:`UNREAD` (the default) reads the file here.
    """
    try:
        if validation_bytes is not None:
            data = json.loads(read_back_text(validation_bytes))
        else:
            with open(validation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except (OSError, ValueError) as exc:
        return f"could not read {validation_path.name}: {exc}", ""

    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}
    bound_hash = metadata.get("grouped_sha256")
    grouping_note = ""
    if bound_hash:
        current_hash = (
            content_hash(grouped_text) if grouped_text is not None
            else file_content_hash(str(grouped_path))
        )
        if bound_hash != current_hash:
            return (
                f"{validation_path.name} belongs to grouping {bound_hash}, current "
                f"{grouped_path.name} is {current_hash or 'missing'}"
            ), ""
        grouping_note = f"bound to grouping {bound_hash}"

    batch_hashes = metadata.get("batch_sha256")
    if isinstance(batch_hashes, dict):
        phase_dir = validation_path.parent
        if tasks_path is None:
            tasks_path = phase_dir / "validation_tasks.json"
        current_manifest, current_tasks = (
            _read_task_manifest(tasks_path) if task_document is UNREAD
            else _task_manifest_of(task_document)
        )
        recorded_manifest = metadata.get("batch_manifest")
        problems: List[str] = []
        # The round check needs both sides: a file that merged no batch round
        # (one the retired in-process lane wrote) records none, and a task file deleted by hand
        # leaves no current mapping for the recorded hashes to disagree with.
        if isinstance(recorded_manifest, dict) and current_manifest is not None:
            if (
                recorded_manifest.get("kind") != current_manifest["kind"]
                or recorded_manifest.get("round") != current_manifest["round"]
            ):
                return (
                    f"{validation_path.name} was merged from a "
                    f"{recorded_manifest.get('kind')} round "
                    f"({_short_hash(recorded_manifest.get('round'))}), current "
                    f"{tasks_path.name} is a {current_manifest['kind']} round "
                    f"({_short_hash(current_manifest['round'])}); re-merging its "
                    f"batch files"
                ), ""
        # A batch whose bytes moved is either a rewrite for *this* round (its
        # verdicts echo this batch's group_ids, so re-merging picks them up) or
        # another round's file of the same name — a revalidation reuses the
        # `validation_batch_<n>.json` names for a different subset. Re-merging
        # the latter under this round's group_ids discards every verdict as a
        # foreign group_hash and reverts the groups to validation_failed, so it
        # never retires the still-correct bound file.
        group_ids_by_index = {
            str(task.get("batch_index")): task.get("group_ids") or []
            for task in current_tasks
            if task.get("batch_index") is not None
        }
        foreign: List[str] = []
        for index in sorted(batch_hashes, key=lambda k: (len(str(k)), str(k))):
            name = f"validation_batch_{index}.json"
            current = file_bytes_sha256(str(phase_dir / name))
            recorded = batch_hashes[index]
            if not current:
                problems.append(f"{name} missing")
            elif current != recorded:
                echoed = _batch_file_group_hashes(phase_dir / name)
                expected_ids = {str(g) for g in group_ids_by_index.get(str(index), [])}
                if echoed and expected_ids and echoed != expected_ids:
                    outside = len(echoed - expected_ids)
                    absent = len(expected_ids - echoed)
                    foreign.append(
                        f"{name} belongs to another round (sha256 "
                        f"{_short_hash(current)} != recorded {_short_hash(recorded)}; "
                        f"its group_hash set differs from this batch's group_ids: "
                        f"{outside} foreign, {absent} absent)"
                    )
                else:
                    problems.append(
                        f"{name} changed (sha256 {_short_hash(current)} != recorded "
                        f"{_short_hash(recorded)})"
                    )
        if isinstance(recorded_manifest, dict) and current_manifest is not None:
            listed = {str(index) for index in batch_hashes}
            for task in current_tasks:
                index = task.get("batch_index")
                if index is None or str(index) in listed:
                    continue
                name = f"validation_batch_{index}.json"
                if (phase_dir / name).exists():
                    problems.append(f"{name} was never merged into it")
        if problems:
            total = len(current_tasks) or len(batch_hashes)
            return (
                f"Re-merging {total} batch files: {', '.join(problems + foreign)}"
            ), ""
        # 7.1d / task 2.10: a bound, up-to-date file is still not reusable when
        # it predates the context contract and its round's prompts carry the
        # contract-1 cut of an over-limit document.
        legacy = _legacy_contract_reason(metadata, phase_dir, task_document)
        if legacy:
            return legacy, ""
        batch_note = (
            f"{len(batch_hashes)} batch hashes match" if batch_hashes
            else "merged from no batch files"
        )
        if foreign:
            # Refuse the re-merge: the bound file still holds this round's
            # verdicts, and the batch bytes on disk answer a different subset.
            batch_note = f"not re-merging: {', '.join(foreign)}"
        parts = [p for p in (grouping_note, batch_note) if p]
        return None, ", ".join(parts)

    # Legacy file: no binding to its batches, so fall back to what the phase dir
    # says happened after it was written — after the 2.10 check, which retires
    # it outright when its round cut an over-limit document.
    legacy = _legacy_contract_reason(metadata, validation_path.parent, task_document)
    if legacy:
        return legacy, ""
    try:
        validation_mtime = validation_path.stat().st_mtime
    except OSError as exc:
        return f"could not stat {validation_path.name}: {exc}", ""
    # A retired round's `validation_batch_<n>.<stamp>.stale.json` (D7) matches
    # the glob too; it keeps its mtime through the rename and belongs to no
    # round this file could have come from.
    newer = sorted(
        batch.name
        for batch in validation_path.parent.glob("validation_batch_*.json")
        if not batch.name.endswith(".stale.json")
        and batch.stat().st_mtime > validation_mtime
    )
    if newer:
        return (
            f"{validation_path.name} carries no batch_sha256 and "
            f"{len(newer)} batch file(s) are newer than it "
            f"({', '.join(newer[:3])}{', ...' if len(newer) > 3 else ''}) "
            f"(legacy: no batch_sha256, mtime test)"
        ), ""
    parts = [p for p in (grouping_note, "legacy: no batch_sha256, mtime test") if p]
    return None, ", ".join(parts)


def _legacy_contract_reason(
    metadata: Dict[str, Any], phase_dir: Path, task_document: Any = UNREAD,
) -> Optional[str]:
    """7.1d: a ``validation.json`` from before contract 2 over an over-limit
    round, judged on *task_document* when the caller read it."""
    try:
        contract = int(metadata.get("context_contract") or 1)
    except (TypeError, ValueError):
        contract = 1
    if contract >= CONTEXT_CONTRACT:
        return None
    if task_document is UNREAD:
        return legacy_context_round_reason(str(phase_dir))
    return legacy_context_document_reason(task_document)


def _derive_model_from_results(validation_results: List[Dict[str, Any]]) -> Optional[str]:
    """Best-effort ``metadata.model`` for a caller that passed none.

    ``merge_batched_validation_results`` tags every merged result with the
    ``_source_model`` its own batch file's ``metadata.model`` reported (every
    materialized validation batch carries one — the model that answered it).
    A single value wins outright; two or more distinct values join as a
    sorted, comma-separated list rather than silently picking one, since the
    merge output is honestly mixed-provenance when batches ran on different
    models. Returns ``None`` when no result carries the tag at all (a legacy
    caller, or results that never went through the batched merge).
    """
    return join_model_names(
        r["_source_model"] for r in validation_results if r.get("_source_model")
    )


def join_model_names(names: Any) -> Optional[str]:
    """One ``metadata.model`` value from several: the single name, or the sorted,
    comma-joined list — never ``"mixed"``.

    Shared by :func:`_derive_model_from_results` and the per-batch attribution
    in ``merge_validation_batches``, so both de-duplicate the same way. Returns
    ``None`` for no names at all.
    """
    models = {str(m) for m in names if m}
    if not models:
        return None
    # A subagent reports its own model name free-hand, and the same runner
    # answers as both ``nemotron-3-ultra-free`` and
    # ``opencode/nemotron-3-ultra-free`` across batches. A bare name that is
    # the model half of a prefixed sibling is that sibling, not a second model.
    bare = {m for m in models if "/" not in m}
    for prefixed in {m for m in models if "/" in m}:
        bare.discard(prefixed.rsplit("/", 1)[1])
    models = bare | {m for m in models if "/" in m}
    return ",".join(sorted(models))


def save_validation_results(
    validation_results: List[Dict[str, Any]],
    output_path: Path,
    model: Optional[str] = None,
    groups: Optional[List[Dict[str, Any]]] = None,
    grouped_file: Optional[str] = None,
    runner: Optional[str] = None,
    runners: Optional[Dict[Any, str]] = None,
    batch_sha256: Optional[Dict[Any, str]] = None,
    batch_manifest: Optional[Dict[str, Any]] = None,
    scope: Optional[Dict[str, Any]] = None,
    scope_decisions: Optional[Dict[str, Any]] = None,
    round_id: Optional[str] = None,
    claim: Optional["_review_round.Claim"] = None,
) -> None:
    """
    Save validation results to a JSON file with metadata.

    When groups are provided, stores each group's stamped id as the result's
    group_id to enable stable matching after reaggregation.

    ``metadata.grouped_sha256`` binds the file to the ``grouped.json`` it was
    produced for (D7) — the same ``file_content_hash`` value
    ``validation_tasks.json`` records under ``inputs.grouped_sha256`` — so
    ``reaggregate_from_existing_files`` can tell a file left behind by an
    earlier grouping from one that belongs to the current one. Defaults to the
    ``grouped.json`` beside ``output_path``, and then to the text of it *claim*
    holds (``review_round.Claim.grouping_text``: the grouping the merge joined
    its verdicts to), never the file read again
    (docs/development/review-results.md, "Consuming checked bytes"); the key is
    omitted when that file does not exist.

    Args:
        validation_results: List of validation results
        output_path: Path to save the JSON file
        model: Model used for validation. When omitted (``None``), derived
            from the batch files via :func:`_derive_model_from_results`
            (``_source_model``, stamped by
            :func:`merge_batched_validation_results`) and falls back to
            ``"unknown"`` only when no batch tagged a model at all — several
            call sites merge then save without ever naming a model, which used
            to write the literal string ``"unknown"`` even though every batch
            file on disk carried its own ``metadata.model``.
        groups: Optional list of groups to read group_ids from
        grouped_file: The ``grouped.json`` this validation belongs to
        runner: The executor's own dispatch record for this batch (F3) —
            e.g. ``opencode:openrouter/~deepseek/deepseek-flash-latest``, read
            back from ``subagent_batch_report.json`` rather than trusted from
            a subagent's free-hand self-report. Stored verbatim under
            ``metadata.runner`` when the caller has it (an ``--exec-subagents``
            dispatch); omitted otherwise — the host-native (Claude Code Task
            tool) path has no executor record to attribute. Does not change
            how ``model`` is derived; a caller that wants the authoritative
            spec to also win ``metadata.model`` passes it as both.
        runners: ``{batch_index: model}`` — who answered each batch,
            stored as ``metadata.runners`` so the per-batch answer survives a
            joined ``model``.
        batch_sha256: ``{batch_index: sha256}`` over the bytes of every batch
            merged into this file. An empty dict is still a binding
            (a writer that merged no batches); ``None`` omits the key and leaves
            the file on the legacy mtime test in ``validation_source_decision``.
        batch_manifest: ``{kind, round}`` of the task file those batches
            answered, so a hash recorded under one round is never
            matched against another round's file of the same name.
        scope: The round's task-file scope block (``scope_round.scope_block``):
            recorded as ``metadata.scope_policy`` / ``scope_baseline_id`` /
            ``scope_round_baseline_id``. ``None`` adds no key.
        scope_decisions: A ``preserve`` round's validation-stage decision
            counts (``scope_round.annotate_decisions``), recorded as
            ``metadata.scope_policy_decisions``.
        round_id: The review round the merged task file records
            (``utils/review_round.py``), as ``metadata.round_id``. ``None``
            adds no key.
        claim: The writing invocation's round claim: the file is published
            only while the phase's checkpoint still records that round, and
            the bytes written become the claim's verdicts, which the report's
            seal binds (``review_round.Claim.publish_verdicts``). Either way it
            is written to a temp file and renamed into place, so no reader sees
            part of it.

    Each record keeps the scope keys it carries — the normalized
    ``scope_relation``/``scope_reason``/``scope_reference``, a ``preserve``
    round's ``selected_remedy``, the host stamps (``scope_baseline_id``,
    ``scope_proposal_digest``, ``scope_source``, ``scope_missing``) and a
    ``scope_policy_decision`` — and a record that carries none is written
    exactly as before.
    """
    if not model:
        model = _derive_model_from_results(validation_results) or "unknown"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    held_grouping = None
    if grouped_file is None:
        grouped_file = str(output_path.parent / "grouped.json")
        held_grouping = claim.grouping_text if claim is not None else None
    grouped_sha256 = (
        content_hash(held_grouping) if held_grouping is not None
        else file_content_hash(grouped_file)
    )

    # Build a mapping from index to group_id if groups provided
    group_id_by_index = {}
    if groups:
        for i, group in enumerate(groups):
            if hasattr(group, 'to_dict'):
                group_dict = group.to_dict()
            else:
                group_dict = group
            group_id_by_index[i] = stamped_group_id(group_dict)

    # Build validation data with metadata
    saved_groups = []
    for v in validation_results:
        group_index = v["group_index"]
        group_entry = {
            "group_index": group_index,
            "status": v["status"],
            "reason": v.get("reason", ""),
            # Absent, not 0.0: a batch that omitted `confidence` (a subagent
            # replied without one) is genuinely unknown, not a real zero. Only
            # `v.get("confidence")` preserves an explicit 0.0 the subagent did
            # report while letting a missing key come through as None.
            "confidence": v.get("confidence"),
            "error_type": v.get("error_type", ERROR_TYPE_UNKNOWN),
            "recoverable": v.get("recoverable", False),
            "revalidated": v.get("revalidated", False),
        }
        # Add group_id - compute from groups if available, else preserve existing
        if group_index in group_id_by_index:
            group_entry["group_id"] = group_id_by_index[group_index]
        elif v.get("group_id"):
            group_entry["group_id"] = v["group_id"]
        for key in _scope_round.RECORD_SCOPE_KEYS:
            if key in v:
                group_entry[key] = v[key]
        saved_groups.append(group_entry)

    validation_data = {
        "format_version": CURRENT_FORMAT_VERSION,
        "groups": saved_groups,
        "metadata": {
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "schema_version": "2.1",
            **({"runner": runner} if runner else {}),
            **({"grouped_sha256": grouped_sha256} if grouped_sha256 else {}),
            **({"runners": {str(k): v for k, v in runners.items()}}
               if runners is not None else {}),
            **({"batch_sha256": {str(k): v for k, v in batch_sha256.items()}}
               if batch_sha256 is not None else {}),
            **({"batch_manifest": dict(batch_manifest)}
               if batch_manifest is not None else {}),
            # Task 2.10: the context contract these verdicts were reached
            # under. A file without it, from a round whose context exceeded
            # the limit, judged a cut document and is never reused.
            "context_contract": CONTEXT_CONTRACT,
            **(_scope_round.validation_metadata(scope, scope_decisions)
               if scope is not None else {}),
            **({_review_round.ROUND_KEY: round_id}
               if _review_round.valid_round(round_id) else {}),
        }
    }

    payload = json.dumps(validation_data, indent=2)
    if claim is not None:
        # The bytes written are the report's verdicts (`claim.verdicts`).
        claim.publish_verdicts(output_path, payload)
    else:
        _review_round.replace_file(output_path, payload)
    print(f"[validation] Saved validation results to: {output_path}")


def build_validation_subagent_prompt(
    context: str,
    suggestions_json: str,
    output_path: str
) -> str:
    """
    Build the prompt for the validation subagent.

    Args:
        context: The plan content or diff context for validation
        suggestions_json: JSON string of suggestions to validate
        output_path: Path where the subagent should write results

    Returns:
        Full prompt string for the validation subagent
    """
    return f'''You are validating review suggestions for accuracy.

## Context (Plan Content)
{context}

## Suggestions to Validate
{suggestions_json}

## Task
For each suggestion group (indexed 0 to N-1), determine:
- "valid": Issue is real, should be addressed
- "invalid": False positive, not applicable
- "needs-human-decision": Requires human judgment

## Output
Write a JSON file to: {output_path}

Format:
{{
  "groups": [
    {{"group_index": 0, "group_hash": "<copy from group's group_hash field>", "status": "valid|invalid|needs-human-decision", "reason": "...", "confidence": 0.0-1.0}}
  ],
  "metadata": {{"model": "claude", "timestamp": "ISO", "schema_version": "2.1"}}
}}

IMPORTANT:
1. Read each suggestion group carefully
2. Compare against the plan context to verify accuracy
3. Be conservative - if unsure, use "needs-human-decision"
4. Write ONLY valid JSON to the output file
5. Include a reason for each classification
6. Copy the exact group_hash value from each input group to the corresponding output result
'''


def prepare_validation_task(
    groups: List[Dict[str, Any]],
    context: str,
    output_path: str,
    model: str = "auto"
) -> Dict[str, Any]:
    """
    Prepare validation input for Claude Code subagent.

    Instead of running validation internally, this prepares all the data
    needed for Claude Code to spawn a validation subagent.

    Args:
        groups: List of suggestion groups to validate
        context: Context for validation (plan content or diff)
        output_path: Path where subagent should write validation.json
        model: Model hint (not used by Claude Code, but preserved for reference)

    Returns:
        Dict with:
        - prompt: Full validation prompt for subagent
        - output_path: Where subagent should write results
        - groups_count: Number of groups to validate
        - suggestions_json: The JSON representation of suggestions
    """
    # Prepare suggestions JSON for the prompt
    validation_input = []
    for i, group in enumerate(groups):
        # Handle both dict and SuggestionGroup objects
        if hasattr(group, 'to_dict'):
            group_dict = group.to_dict()
        else:
            group_dict = group

        # The stamped id, for stable matching after reaggregation
        gid = stamped_group_id(group_dict)

        validation_input.append({
            "index": i,
            "group_id": gid,
            "theme": group_dict.get("theme", "Unknown"),
            "category": group_dict.get("category", "unknown"),
            "models": group_dict.get("models", []),
            "suggestions": [
                {
                    "title": s.get("title", ""),
                    "desc": s.get("desc", ""),
                    "importance": s.get("importance", "medium"),
                    "type": s.get("type", "unknown")
                }
                for s in group_dict.get("suggestions", [])
            ]
        })

    suggestions_json = json.dumps(validation_input, indent=2)

    # Truncate context if too long
    max_context_len = 30000
    if len(context) > max_context_len:
        context = context[:max_context_len] + "\n\n[... truncated ...]"

    prompt = build_validation_subagent_prompt(
        context=context,
        suggestions_json=suggestions_json,
        output_path=output_path
    )

    return {
        "prompt": prompt,
        "output_path": output_path,
        "groups_count": len(groups),
        "suggestions_json": suggestions_json,
        "model_hint": model,
    }


def load_validation_results(
    validation_path: Path, *, raw: Optional[bytes] = None
) -> List[Dict[str, Any]]:
    """
    Load validation results with migration for older format files.

    Older validation.json files may not have error_type, recoverable, or
    revalidated fields. This function applies sensible defaults to ensure
    compatibility.

    Args:
        validation_path: Path to the validation.json file
        raw: The file's bytes, when the caller read them already (a report
            built from them binds those exact bytes, ``review_round.Verdicts``);
            the path is not read again.

    Returns:
        List of validation results with all fields populated
    """
    if raw is not None:
        data = json.loads(raw)
    else:
        with open(validation_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    # Handle both old format (list) and new format (dict with groups/metadata)
    if isinstance(data, list):
        # Old format: direct list of validation results
        groups = data
        schema_version = "1.0"
    else:
        # New format: dict with groups and metadata
        schema_version = data.get("metadata", {}).get("schema_version", "1.0")
        groups = data.get("groups", [])

    if schema_version < "2.0":
        # Migrate v1 format to v2
        for group in groups:
            # Default error_type based on status
            if "error_type" not in group:
                if group.get("status") == "needs-human-decision":
                    # Assume older needs-human-decision items were from parsing errors
                    # unless the reason suggests genuine ambiguity
                    reason = group.get("reason", "").lower()
                    if any(word in reason for word in ["ambiguous", "unclear", "judgment"]):
                        group["error_type"] = ERROR_TYPE_AMBIGUOUS
                    else:
                        group["error_type"] = ERROR_TYPE_PARSING
                elif group.get("status") == "validation_failed":
                    group["error_type"] = ERROR_TYPE_PARSING
                else:
                    group["error_type"] = ERROR_TYPE_UNKNOWN

            # Default recoverable based on error_type
            if "recoverable" not in group:
                group["recoverable"] = group.get("error_type") in RECOVERABLE_ERROR_TYPES

            # Default revalidated to False
            if "revalidated" not in group:
                group["revalidated"] = False

        print(f"[validation] Migrated {len(groups)} items from schema v1 to v2", file=sys.stderr)

    return groups


# --- Batched Validation Functions ---

from .validation_batcher import (
    batch_validation_groups,
    estimate_validation_batching_stats,
)


def build_validation_batch_records(
    groups: List[Dict[str, Any]],
    group_indices: List[str],
    group_ids: List[str],
    *,
    with_reference: bool = False,
) -> List[Dict[str, Any]]:
    """Build the suggestion records one validation batch embeds in its prompt.

    The records travel as *values* inside the prompt (``context_mode: inline``),
    never as a path to ``grouped.json``, because a headless runner is not
    guaranteed a workspace-read tool.

    Args:
        groups: All groups for the phase.
        group_indices: This batch's indices into ``groups``.
        group_ids: ``group_ids[i]`` is the stable id of ``groups[i]``.

    Returns:
        One record per group in the batch, carrying the global index under
        ``group_index`` — the same key the reply contract asks the subagent to
        echo back, rather than a differently-named ``index`` the subagent has
        to translate — and the ``group_hash`` the subagent must also echo.

        A suggestion's ``file`` and ``line_range`` ride along **when the
        finding has them**. ``CODE_REVIEW_VALIDATION_GUIDANCE`` has promised
        the validator "each issue record carries `file` and `line_range`" since
        D2 lifted that sentence out of the instruction markdown — where it was
        true, because the markdown pointed the validator at ``grouped.json``
        itself — but this builder kept the four-field shape the plan-review
        records have, so every code-review validator was told to open
        locations it was never given, beside a code block that names five
        files and says nothing about which finding each window belongs to.
        Measured 2026-09-17: six groups over five files, and the verdicts
        located every one by reading the repository, which ``context_mode:
        inline`` does not promise. Keyed on presence, so a plan-review record
        (no location) renders byte-identically to before.

        A suggestion's ``reference`` (the plan section a reviewer says it is
        about) rides along only ``with_reference``: a batch that carries only
        the plan sections its groups cite selects them from exactly these
        values and shows them, so the validator sees which section each
        suggestion names. Every other batch renders as it did before cited
        sections existed.
    """
    records: List[Dict[str, Any]] = []
    for idx in group_indices:
        group = groups[idx]
        group_dict = group.to_dict() if hasattr(group, 'to_dict') else group
        records.append({
            "group_index": idx,
            # Both spellings carry the same value: the prompt tells the subagent
            # to copy `group_hash`, while `merge_batched_validation_results`
            # accepts either, so no reader can miss it.
            "group_hash": group_ids[idx],
            "group_id": group_ids[idx],
            "theme": group_dict.get("theme", "Unknown"),
            "category": group_dict.get("category", "unknown"),
            "models": group_dict.get("models", []),
            "suggestions": [
                {
                    "title": s.get("title", ""),
                    "desc": s.get("desc", ""),
                    "importance": s.get("importance", "medium"),
                    "type": s.get("type", "unknown"),
                    **(
                        {"reference": s["reference"]}
                        if with_reference and s.get("reference") else {}
                    ),
                    **({"file": s["file"]} if s.get("file") else {}),
                    **(
                        {"line_range": s["line_range"]}
                        if s.get("line_range") else {}
                    ),
                    **_reviewer_scope_fields(s),
                }
                for s in group_dict.get("suggestions", [])
            ],
        })
    return records


def _reviewer_scope_fields(suggestion: Dict[str, Any]) -> Dict[str, Any]:
    """A member's provisional scope tag, for the validator to see (and to judge
    independently of), keyed on presence like ``file``: a finding a reviewer
    gave no tag renders exactly as before."""
    if not _sp.has_scope_fields(suggestion):
        return {}
    fields = _sp.normalize_scope_fields(suggestion)
    return {
        _sp.RELATION_FIELD: fields[_sp.RELATION_FIELD],
        **({_sp.REASON_FIELD: fields[_sp.REASON_FIELD]}
           if fields[_sp.REASON_FIELD] else {}),
    }


def resolved_reaggregate_command(
    document: Dict[str, Any], *, typed_plan: bool = False,
) -> Optional[str]:
    """Rebuild a task document's follow-up command from the *running* skill dir.

    ``validation_tasks.json`` stores the durable, rebindable pair
    (``reaggregate_mode`` + ``plan_file``) and never the resolved
    skill-dir-absolute command (D1c). Resolution therefore happens here, at
    print time, exactly as :func:`utils.detach.resolved_reaggregate_command`
    does for ``.status.json``: printing an absolute path is safe because it is
    session-scoped, persisting one is not.

    Returns ``None`` when the document carries neither the durable pair nor a
    legacy resolved command (an empty phase, which owes no follow-up).

    *typed_plan* (the native hand-off's printed command) names
    the plan as this invocation's user typed it when that spelling names the
    same file (``cli_common.typed_plan_for``).
    """
    mode = document.get("reaggregate_mode")
    plan = document.get("plan_file")
    if mode and plan and typed_plan:
        plan = typed_plan_for(str(plan))
    if mode and plan:
        # The live invocation of this mode wins over the document's stored
        # `replay_flags` (D2's precedence rule); the stored list is the fallback
        # for a reader in a later process, and is never sanitized.
        return retry_command(
            str(mode), str(plan), "--reaggregate",
            flags=current_replay_flags(
                document.get("replay_flags"), mode=str(mode)
            ),
        )
    # Written before the durable pair existed. Its stored command is only as
    # good as the skill dir it was written under — precisely the staleness this
    # key stopped persisting — but honouring it is never worse than the build
    # that wrote it, and it keeps an in-flight phase resumable across the change.
    legacy = document.get("reaggregate_command")
    return str(legacy) if legacy else None


#: The heading a validation prompt gives its first block unless told otherwise.
PLAN_CONTEXT_LABEL = "Plan content"


@dataclass(frozen=True)
class ContextBlock:
    """One document a validation prompt embeds.

    *text* is excerpted on its own per-context budget, so a long first block
    cannot squeeze a second one out of the prompt. *label* is the block's
    heading (``"Plan content"``, …). *document* is the bound document the text
    was read from: its hash becomes ``inputs.plan_sha256``
    (label ``plan``) or ``inputs.tasks_sha256`` (label ``tasks``) instead of a
    re-read of the live file, and over the limit its snapshot is what the
    prompt names. ``None`` keeps the legacy behaviour: no path, and an
    over-limit block is ``mode: truncated``. Review-code's reviewed-code block
    (label ``reviewed-code``) is never named by path.
    """

    text: str
    label: str = PLAN_CONTEXT_LABEL
    document: Optional[BoundDocument] = None


@dataclass(frozen=True)
class RoundProvenance:
    """Where a validation round came from: recorded on its task file, never
    interpolated into prompt text.

    * ``model``: the hint every task carries, preserved verbatim.
    * ``orchestrator``: the script whose ``--reaggregate`` continues the round
      (the document's durable ``reaggregate_mode``).
    * ``phase``: the phase the published ``validation_context`` names
      (default: the phase dir's basename).
    * ``base_ref`` / ``head_ref``: ``inputs.diff_base``; ``<base>..<head>``
      for a review pinned to two commits.
    * ``tasks_file``: review-tasks' task list, recorded and hashed into
      ``inputs.tasks_sha256``.
    * ``context_plan_sha256`` / ``context_plan_file``: a commit review's
      frozen context plan, recorded as ``inputs.context_plan_sha256``
      and, relative to the phase dir, ``context_plan_file``, so a resume
      whose snapshot no longer hashes to it is refused.
    * ``round_id``: the review round the phase's ``.status.json`` records
      (``utils/review_round.py``), written as the task file's last top-level
      key; ``None`` writes no key, so the file is byte-identical to one from
      before round ids.
    """

    model: str = "auto"
    orchestrator: str = "review_plan_orchestrator.py"
    phase: Optional[str] = None
    base_ref: str = ""
    head_ref: Optional[str] = None
    tasks_file: Optional[str] = ""
    context_plan_sha256: Optional[str] = None
    context_plan_file: Optional[str] = None
    round_id: Optional[str] = None


@dataclass(frozen=True)
class ValidationRound:
    """Everything one validation or revalidation round is materialized from
    (:func:`materialize_validation_round`).

    * ``groups``: the suggestion groups to validate; ``output_dir``: the
      phase dir the batch results are written to.
    * ``plan_file``: the plan's path, for provenance and the ``inputs`` hash.
    * ``primary``: the first block (the plan, or a code fix's diff);
      ``secondary``: an optional second one (review-tasks' task list,
      review-code's reviewed code, a revalidation's original baseline).
    * ``secondary_for_batch``: the second block per batch. Called with a
      batch's indices into ``groups``, it returns that batch's ``(text,
      document, extra_instructions)``, which replace ``secondary.text``,
      ``secondary.document`` and ``extra_instructions`` for that batch;
      ``secondary.text`` is then not embedded.
    * ``reviewed_code``: the code-under-review excerpt hashed into
      ``inputs.reviewed_code_sha256``. Passed rather than derived from the
      second block, which may hold more than the code; it hashes the round's
      whole excerpt even with ``secondary_for_batch``.
    * ``extra_instructions``: capability-neutral phase guidance appended to
      every batch prompt.
    * ``scope``: the round's scope block (``scope_round.scope_block``),
      rendered into every prompt (``scope_policy.validator_guidance``) and
      recorded under ``scope``, which the merge stamps each hash-joined
      verdict with. ``None`` is a default ``expand`` round with no baseline.
    * ``runner_read_refusal``: who will read a ``mode: path`` source: ``None`` (a
      capable reader), a string (the reason no source
      may be named by path) or a callable taking the absolute path and
      returning ``None`` or such a reason. A ``prompt_budget`` whose
      ``supports_workspace_reads`` is false counts as a refusal.
    * ``kind``: ``"validation"`` or ``"revalidation"``, the task ``kind``.
    * ``max_per_batch``: the most groups a normal batch holds.
    * ``prompt_budget``: the D2d budget; an over-budget batch is split, and a
      single group that still does not fit fails loudly, never truncated.
    * ``publish``: publish ``validation_context`` for this round.
    * ``grouped_text``: the ``grouped.json`` text the round's groups were
      written as (``review_round.Claim.grouping_text``), hashed into
      ``inputs.grouped_sha256`` in place of a read of the file; ``None`` reads
      the file (docs/development/review-results.md, "Consuming checked
      bytes").
    """

    groups: List[Dict[str, Any]]
    output_dir: str
    primary: ContextBlock
    plan_file: str = ""
    secondary: Optional[ContextBlock] = None
    secondary_for_batch: Optional[
        Callable[[List[int]], Tuple[str, Optional[BoundDocument], str]]
    ] = None
    reviewed_code: Optional[str] = None
    extra_instructions: str = ""
    scope: Optional[Dict[str, Any]] = None
    runner_read_refusal: Optional[Any] = None
    provenance: RoundProvenance = RoundProvenance()
    kind: str = "validation"
    max_per_batch: int = 4
    prompt_budget: Optional[PromptBudget] = None
    publish: bool = True
    grouped_text: Optional[str] = None


def prepare_batched_validation_tasks(
    groups: List[Dict[str, Any]],
    context: str,
    output_dir: str,
    plan_file: str = "",
    model: str = "auto",
    max_per_batch: int = 4,
    orchestrator: str = "review_plan_orchestrator.py",
    base_ref: str = "",
    tasks_file: str = "",
    kind: str = "validation",
    context_label: str = PLAN_CONTEXT_LABEL,
    secondary_context: str = "",
    secondary_context_label: str = "",
    reviewed_code: Optional[str] = None,
    extra_instructions: str = "",
    prompt_budget: Optional[PromptBudget] = None,
    context_document: Optional[BoundDocument] = None,
    secondary_document: Optional[BoundDocument] = None,
    runner_read_refusal: Optional[Any] = None,
    phase: Optional[str] = None,
    publish: bool = True,
    head_ref: Optional[str] = None,
    context_plan_sha256: Optional[str] = None,
    context_plan_file: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None,
    secondary_for_batch: Optional[
        Callable[[List[int]], Tuple[str, Optional[BoundDocument], str]]
    ] = None,
    round_id: Optional[str] = None,
) -> Dict[str, Any]:
    """The keyword form of :func:`materialize_validation_round`.

    Every field of :class:`ValidationRound`, :class:`ContextBlock` and
    :class:`RoundProvenance` spelled as one keyword, for the tests that still
    call it this way; the orchestrators build a :class:`ValidationRound`.
    """
    has_secondary = bool(
        secondary_context or secondary_context_label or secondary_document is not None
    )
    return materialize_validation_round(ValidationRound(
        groups=groups,
        output_dir=output_dir,
        plan_file=plan_file,
        primary=ContextBlock(context, context_label, context_document),
        secondary=ContextBlock(
            secondary_context, secondary_context_label, secondary_document,
        ) if has_secondary else None,
        secondary_for_batch=secondary_for_batch,
        reviewed_code=reviewed_code,
        extra_instructions=extra_instructions,
        scope=scope,
        runner_read_refusal=runner_read_refusal,
        provenance=RoundProvenance(
            model=model, orchestrator=orchestrator, phase=phase,
            base_ref=base_ref, head_ref=head_ref, tasks_file=tasks_file,
            context_plan_sha256=context_plan_sha256,
            context_plan_file=context_plan_file,
            round_id=round_id,
        ),
        kind=kind,
        max_per_batch=max_per_batch,
        prompt_budget=prompt_budget,
        publish=publish,
    ))


def _round_key(provenance: RoundProvenance) -> Dict[str, str]:
    """The task file's round key (``utils/review_round.py``), or ``{}``."""
    round_id = _review_round.valid_round(provenance.round_id)
    return {_review_round.ROUND_KEY: round_id} if round_id else {}


def materialize_validation_round(round_: ValidationRound) -> Dict[str, Any]:
    """
    Prepare batched validation tasks for sequential subagent processing.

    Instead of creating one task with all groups, this creates multiple batch
    tasks that can be processed sequentially by subagents with fresh context.

    Each batch carries a **complete prompt** (D2/D2f). This deliberately
    reverses this function's original reference-based design, in which the file
    stored only references to ``grouped.json`` and the plan and a Claude reading
    the instruction markdown assembled the prompt itself. Prompt-in-JSON is what
    makes one task file executable by a native-subagent host *and* by the Python
    executor with byte-identical prompt text; resolving the references at
    dispatch time would only fix the executor path, since a native host has no
    Python at dispatch time. The reference-based approach survives as
    ``context_mode: workspace-read`` — declared in the task and capability-gated,
    instead of implicit in who reads the file.

    The whole-document excerpt is cut **once** and reused by every batch that
    embeds it; a batch never re-truncates it. Two blocks may instead be
    selected per batch, each a pure function of the round's inputs and the
    batch's own records, so identical inputs still render identical prompts:

    * the plan block carries only the sections the batch's groups cite, when
      :func:`cited_plan_for_round` qualifies the round and
      ``validation_sections.CitedPlan.select`` finds a section for every group
      (else that batch embeds the whole plan);
    * the second block comes from ``secondary_for_batch`` when given
      (review-code: the windows its own issues cite).

    The fields are described on :class:`ValidationRound`.

    Returns:
        Dict with:
        - tasks / batches: the materialized tasks (same objects under both keys)
        - tasks_schema_version, kind, inputs: the D2g file envelope
        - total_batches: Number of batches
        - batching_stats: Statistics about the batching
        - grouped_file, plan_file, phase_dir, base_ref
        - reaggregate_mode: the durable half of the follow-up command; the
          resolved string is rebuilt at print time by
          :func:`resolved_reaggregate_command`, never persisted (D1c)
    """
    # The round's fields under the names the steps below read them by.
    groups, output_dir, plan_file, kind = (
        round_.groups, round_.output_dir, round_.plan_file, round_.kind,
    )
    # The index describes the task file this round replaces: it goes before a
    # sidecar changes, and the hand-back rebuilds it from the file the caller
    # commits. The caller holds `host_views_lock` across this call and that
    # write (docs/development/delegation.md#the-host-index).
    invalidate_host_index(task_file_for_kind(output_dir, kind))
    context, context_label, context_document = (
        round_.primary.text, round_.primary.label, round_.primary.document,
    )
    secondary = round_.secondary or ContextBlock("", "")
    secondary_context, secondary_context_label, secondary_document = (
        secondary.text, secondary.label, secondary.document,
    )
    provenance = round_.provenance
    model, base_ref, head_ref, tasks_file, phase = (
        provenance.model, provenance.base_ref, provenance.head_ref,
        provenance.tasks_file, provenance.phase,
    )
    context_plan_sha256, context_plan_file = (
        provenance.context_plan_sha256, provenance.context_plan_file,
    )
    runner_read_refusal, prompt_budget = round_.runner_read_refusal, round_.prompt_budget
    max_per_batch, scope = round_.max_per_batch, round_.scope
    secondary_for_batch, extra_instructions = (
        round_.secondary_for_batch, round_.extra_instructions,
    )

    grouped_file = str(Path(output_dir) / "grouped.json")
    context_provenance: Dict[str, str] = {}
    if context_plan_file and context_plan_sha256:
        try:
            source = os.path.relpath(os.path.abspath(context_plan_file), os.path.abspath(output_dir))
        except ValueError:  # another drive on Windows
            source = os.path.abspath(context_plan_file)
        context_provenance["context_plan_file"] = source
    bound_plan = context_document if (
        context_document is not None and context_document.label == "plan"
    ) else None
    bound_tasks = secondary_document if (
        secondary_document is not None and secondary_document.label == "tasks"
    ) else None
    inputs = build_inputs(
        # One read, one hash domain: a bound document's hash is
        # taken over the bytes the round read, never over a second read of the
        # live file, so the excerpt, the snapshot and `inputs` cannot come from
        # two versions. The value keeps the 16-char text-hash domain the
        # resume guard and `state.plan_hash` compare in.
        plan_file=None if bound_plan is not None else plan_file,
        grouped_file=grouped_file,
        grouped_text=round_.grouped_text,
        tasks_file=None if bound_tasks is not None else tasks_file,
        diff_base=(
            f"{base_ref}..{head_ref}" if base_ref and head_ref else base_ref
        ),
        reviewed_code=round_.reviewed_code,
        context_plan_sha256=context_plan_sha256,
    )
    if bound_plan is not None:
        inputs["plan_sha256"] = content_hash(bound_plan.text)
    if bound_tasks is not None and tasks_file:
        inputs["tasks_sha256"] = content_hash(bound_tasks.text)

    # The round's scope block, rendered per call: the template text is never
    # cached with a policy in it, so an `expand` rendering cannot be served to
    # a `preserve` round.
    scope_meta = dict(scope) if scope else _scope_round.scope_block(
        None, _sp.review_phase_of(phase or os.path.basename(os.path.normpath(output_dir))),
    )
    scope_text = _sp.validator_guidance(
        scope_meta.get("policy"), str(scope_meta.get("phase") or "review-plan"),
        revalidation_baseline_differs=bool(scope_meta.get("revalidation_baseline_differs")),
    )

    if not groups:
        if round_.publish:
            publish_validation_context(output_dir, [], phase=phase)
        empty = make_task_file(kind=kind, tasks=[], inputs=inputs, task_list_key="batches", extra={
            **context_provenance,
            "context_contract": CONTEXT_CONTRACT,
            "total_batches": 0,
            "batching_stats": estimate_validation_batching_stats([]),
            "grouped_file": grouped_file,
            "plan_file": plan_file,
            "phase_dir": output_dir,
            "model_hint": model,
            "base_ref": base_ref,
            _scope_round.TASK_SCOPE_KEY: scope_meta,
            **_round_key(provenance),
        })
        return empty

    # Create batches
    validation_batches = batch_validation_groups(
        groups=groups,
        max_per_batch=max_per_batch,
        isolate_high=True
    )

    # Each group's stamped id: the one key that tells same-content groups
    # apart, so each verdict joins its own group (docs/development/
    # review-results.md, "Stable group IDs").
    group_ids = [stamped_group_id(group) for group in groups]

    # The whole-document excerpts, reused verbatim by every batch that embeds
    # them. A second document is excerpted on its own budget rather than
    # appended to the first: concatenating would let a plan at the limit
    # truncate the artifact under review down to nothing, which is the failure
    # two contexts exist to fix.
    #
    # Each block becomes one context source record: inline when
    # it fits, `path` when it is over the limit and a readable hash-bound
    # snapshot names the whole document, `truncated` otherwise — decided here,
    # at materialization, and reported one stderr line per non-inline source.
    if (
        runner_read_refusal is None
        or getattr(runner_read_refusal, "advisory_only", False)
    ) and prompt_budget is not None and not getattr(
        prompt_budget, "supports_workspace_reads", True
    ):
        runner_read_refusal = "the configured runner cannot read files"

    def refusal_for(document: Optional[BoundDocument]) -> Optional[str]:
        if runner_read_refusal is None:
            return None
        if callable(runner_read_refusal):
            return runner_read_refusal(document.path) if (
                document is not None and document.path
            ) else None
        return str(runner_read_refusal)

    def secondary_label_for(document: Optional[BoundDocument]) -> str:
        if document is not None:
            return document.label
        return "tasks" if tasks_file else "reviewed-code"

    # With no bound document the label names the block's kind explicitly
    # (plan | tasks | diff) — a "Tasks file" block is a tasks document, not a
    # diff, so its notice and recorded reason name the right document.
    if context_document is not None:
        primary_label = context_document.label
    elif "Plan" in context_label:
        primary_label = "plan"
    elif "Tasks" in context_label:
        primary_label = "tasks"
    else:
        primary_label = "diff"
    shared_context, primary_source = build_context_source(
        context, context_document, label=primary_label, block="context",
        phase_dir=output_dir, read_refusal=refusal_for(context_document),
    )
    sources: List[Dict[str, Any]] = [primary_source]
    shared_secondary = ""
    secondary_source: Optional[Dict[str, Any]] = None
    if secondary_context and secondary_for_batch is None:
        shared_secondary, secondary_source = build_context_source(
            secondary_context, secondary_document,
            label=secondary_label_for(secondary_document),
            block="secondary-context", phase_dir=output_dir,
            read_refusal=refusal_for(secondary_document),
        )
        sources.append(secondary_source)
    # A native host refuses nothing, but a `mode: path` source outside the
    # project root is flagged (one printed notice, a recorded reason).
    advisory = getattr(runner_read_refusal, "advisory", None)
    if callable(advisory):
        for source in sources:
            if source["mode"] == "path":
                note = advisory(source.get("abs_path"))
                if note:
                    source["reason"] = note
    # The plan sections each batch's groups cite, when the round qualifies
    # (docs/development/delegation.md, "Cited plan sections").
    cited_plan = cited_plan_for_round(
        context, context_document,
        read_refusal=refusal_for(context_document),
        runner_read_refusal=runner_read_refusal,
    )
    selections: List[Any] = []
    published: List[Dict[str, Any]] = []
    budget = prompt_budget or PromptBudget(None)

    # Work list of (group_indices, is_high_priority). A batch whose materialized
    # prompt exceeds the D2d budget is split in half and re-queued; a single
    # group that still does not fit raises (never truncated).
    pending: List[Tuple[List[int], bool]] = [
        (list(batch.group_indices), batch.is_high_priority)
        for batch in validation_batches
    ]

    batch_tasks: List[Dict[str, Any]] = []
    next_index = 0
    while pending:
        indices, is_high = pending.pop(0)
        records = build_validation_batch_records(groups, indices, group_ids)
        batch_context, batch_primary = shared_context, primary_source
        selection = None
        if cited_plan is not None:
            cited_records = build_validation_batch_records(
                groups, indices, group_ids, with_reference=True,
            )
            selection = cited_plan.select(cited_records, limit=VALIDATION_CONTEXT_LIMIT)
            if selection.excerpt is not None:
                records = cited_records
                batch_context = selection.excerpt
                batch_primary = cited_context_source(
                    context_document, selection.excerpt, selection,
                    phase_dir=output_dir, sections_total=len(cited_plan.headings),
                )
        batch_secondary, batch_secondary_source = shared_secondary, secondary_source
        batch_extra = extra_instructions
        if secondary_for_batch is not None:
            text, document, batch_extra = secondary_for_batch(list(indices))
            batch_secondary, batch_secondary_source = "", None
            if text:
                batch_secondary, batch_secondary_source = build_context_source(
                    text, document, label=secondary_label_for(document),
                    block="secondary-context", phase_dir=output_dir,
                    read_refusal=refusal_for(document),
                )
        batch_sources = [batch_primary] + (
            [batch_secondary_source] if batch_secondary_source is not None else []
        )
        # Only a batch that is not wholly inline records its sources on the
        # task: an under-limit task is byte-identical to what contract 1 wrote,
        # so its goldens do not move.
        task_sources = (
            batch_sources if any(s["mode"] != "inline" for s in batch_sources) else None
        )
        prompt_sources = [s for s in batch_sources if s["mode"] == "path"] or None
        context_mode = "workspace-read" if prompt_sources else "inline"
        prompt = build_validation_prompt(
            plan_excerpt=batch_context,
            suggestion_records=records,
            kind=kind,
            context_label=context_label,
            secondary_excerpt=batch_secondary,
            secondary_label=secondary_context_label,
            extra_instructions=batch_extra,
            context_sources=prompt_sources,
            scope_guidance=scope_text,
        )
        if not budget.fits(prompt):
            first, second = split_indices(indices)
            if second:
                pending.insert(0, (second, is_high))
                pending.insert(0, (first, is_high))
                continue
            # Unsplittable and over budget: fail loudly with the actionable fix.
            # `resolution` raises for a runner with no workspace-read capability,
            # but *returns* "workspace-read" for one that has it. That return is
            # still not a further downgrade: each source's context mode is set
            # by VALIDATION_CONTEXT_LIMIT, not by the transport budget,
            # and an unsplittable batch that is still over is over because of
            # its INLINE part — the excerpt and its suggestion records — which
            # naming a path cannot shrink.
            budget.resolution(prompt, splittable=False)
            raise TaskFileError(
                f"A {kind} batch holding a single group materializes a prompt of "
                f"{budget.units(prompt)} UTF-16 code units against the runner's "
                f"{budget.max_units}-unit {budget.transport} budget, so it can be "
                f"neither split nor sent. What is over is the inline part — the "
                f"context excerpt and this group's suggestion records — which no "
                f"workspace-read path can shrink (an over-limit document is "
                f"already named by path and its excerpt is capped at "
                f"{VALIDATION_CONTEXT_LIMIT} chars), so configure a runner with a "
                f"stdin/file prompt transport (driver.subagent_runner). The "
                f"prompt is never truncated."
            )
        if selection is not None:
            selections.append(selection)
        published.extend(batch_sources)

        output_name = f"validation_batch_{next_index}.json"
        batch_tasks.append(make_task(
            kind=kind,
            task_id=f"{kind}-batch-{next_index}",
            prompt=prompt,
            output_name=output_name,
            inputs=inputs,
            phase_dir=output_dir,
            model_hint=model,
            prompt_path=sidecar_path(output_dir, next_index),
            prompt_lines=prompt.count("\n") + 1,
            context_mode=context_mode,
            extra={
                "batch_index": next_index,
                "group_indices": indices,
                "group_ids": [group_ids[idx] for idx in indices],
                "groups_count": len(indices),
                "is_high_priority": is_high,
                "plan_file": plan_file,
                "grouped_file": grouped_file,
                **(
                    {"context_sources": [dict(s) for s in task_sources]}
                    if task_sources else {}
                ),
            },
        ))
        next_index += 1

    write_prompt_sidecars(batch_tasks, output_dir)
    if cited_plan is not None:
        line = _sections.summary_line(selections, len(context))
        if line:
            print(line, file=sys.stderr)

    stats = estimate_validation_batching_stats(groups, max_per_batch)

    # D2f's per-file ceiling on the materialized total. Reported rather than
    # enforced — see VALIDATION_TASKS_TOTAL_CHARS_CEILING for why a phase that
    # crosses it is still written.
    total_chars = materialized_total_chars(batch_tasks)
    if total_chars > VALIDATION_TASKS_TOTAL_CHARS_CEILING:
        print(
            f"[VALIDATION_TASKS_OVERSIZE] {kind}: {len(batch_tasks)} batches "
            f"materialize {total_chars} prompt chars, over the "
            f"{VALIDATION_TASKS_TOTAL_CHARS_CEILING}-char per-file ceiling "
            f"(D2f). The shared context excerpt is embedded once per batch, so "
            f"raise max_per_batch (currently {max_per_batch}) to cut the number "
            f"of copies, or validate fewer groups. Writing it anyway.",
            file=sys.stderr,
        )

    # The follow-up command is stored in its **durable, rebindable** form (mode
    # word + plan path), never as the resolved skill-dir-absolute string: this
    # document outlives the run that wrote it, and the Claude plugin cache is
    # keyed by commit hash, so a persisted absolute command names a directory
    # the next plugin update deletes (D1c). `resolved_reaggregate_command()`
    # rebuilds it at print time from the *running* skill dir — the same split
    # `.status.json` already makes via `cli_common.durable_reaggregate_fields`.
    extra: Dict[str, Any] = {
        **context_provenance,
        "context_contract": CONTEXT_CONTRACT,
        "total_batches": len(batch_tasks),
        "batching_stats": stats,
        "grouped_file": grouped_file,
        "phase_dir": output_dir,
        **durable_reaggregate_fields(provenance.orchestrator, plan_file),
        "model_hint": model,
        "base_ref": base_ref,
        _scope_round.TASK_SCOPE_KEY: scope_meta,
    }
    if tasks_file:
        extra["tasks_file"] = tasks_file
    extra.update(_round_key(provenance))
    document = make_task_file(
        kind=kind,
        tasks=batch_tasks,
        inputs=inputs,
        task_list_key="batches",
        extra=extra,
    )
    if round_.publish:
        # Every batch's own records: a cited plan block or a per-batch second
        # block differs between batches, and the aggregate keeps the worst.
        publish_validation_context(output_dir, published or sources, phase=phase)
    return document


def _verdict_or_failure(result: Dict[str, Any]) -> Dict[str, Any]:
    """``result`` as placed, or a ``validation_failed`` record in its stead
    when its status is not one of :data:`VALIDATION_VERDICTS`.

    An out-of-vocabulary status is no verdict, so the group stays
    ``validation_failed`` as a discarded foreign hash leaves it, keeping the
    ``group_id`` it was placed under. The executor lane persists such a reply
    (``schema_validator.validation_reply_problems``), so this is where the word
    stops before it reaches ``validation.json``. The record carries no scope
    authority: it is never stamped.
    """
    status = result.get("status")
    if status in VALIDATION_VERDICTS:
        return result
    failed: Dict[str, Any] = {"group_index": result.get("group_index")}
    if result.get("group_id"):
        failed["group_id"] = result["group_id"]
    failed.update({
        "status": "validation_failed",
        "reason": (
            f"the reply's status {status!r} is not one of "
            + ", ".join(VALIDATION_VERDICTS)
        ),
        "confidence": 0.0,
        "error_type": ERROR_TYPE_PARSING,
        "recoverable": True,
    })
    return failed


def _batch_verdicts(
    batch_data: Any,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], int]:
    """``(verdict records, the batch's model, entries dropped)`` of one parsed
    batch file; records are ``None`` when the file is not a reply at all.

    A reply is a list of verdict objects, bare or under ``groups`` in an object
    whose ``metadata.model`` names the model that wrote it. The file is model
    output a native host wrote unchecked, so neither shape is assumed: a
    ``groups`` that is not a list, or a document that is neither, is no reply
    (its groups stay ``validation_failed``, as a batch that does not parse
    leaves them), and an entry that is not an object is dropped while the rest
    of the batch merges (docs/development/review-results.md, "Snapshots and
    empty review outcomes").
    """
    model: Optional[str] = None
    if isinstance(batch_data, dict):
        metadata = batch_data.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("model"), str):
            model = metadata["model"] or None
        entries = batch_data.get("groups", [])
    else:
        entries = batch_data
    if not isinstance(entries, list):
        return None, model, 0
    records = [entry for entry in entries if isinstance(entry, dict)]
    return records, model, len(entries) - len(records)


def _echoed_hash(result: Dict[str, Any]) -> Optional[str]:
    """The group hash a verdict echoed, ``None`` when it echoed none.

    A value that is not text names no group of any batch, so it comes back as
    its ``repr``: a foreign hash the join discards, never an unhashable key.
    """
    raw = result.get("group_hash") or result.get("group_id")
    if not raw:
        return None
    return raw if isinstance(raw, str) else repr(raw)


#: The reason every group's slot starts the merge with.
_BATCH_NOT_FOUND = "Batch result not found"


def _unusable_batch(
    merged_results: List[Dict[str, Any]],
    batch_info: Dict[str, Any],
    reason: str,
) -> None:
    """Give every group of a batch whose file holds no usable reply *reason*.

    The groups were already ``validation_failed`` ("Batch result not found");
    this only says why, so the report and ``--revalidate`` name the file.
    """
    for index in batch_info.get("group_indices", []):
        if (isinstance(index, int) and 0 <= index < len(merged_results)
                and merged_results[index].get("reason") == _BATCH_NOT_FOUND):
            merged_results[index] = {
                **merged_results[index],
                "reason": reason,
                "error_type": ERROR_TYPE_PARSING,
            }


def merge_batched_validation_results(
    output_dir: str,
    batch_metadata: Dict[str, Any],
    total_groups: int,
    groups: Optional[List[Any]] = None,
    *,
    batch_bytes: Optional[Dict[Any, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Merge results from multiple validation batch files.

    Scope: every verdict that joined its group **by hash** is stamped
    (``scope_round.stamp``) against the host's own copy of that group from
    ``groups`` — the proposal digest and the baseline id recorded in the task
    file's ``scope`` block, never a model's echo of either — and under
    ``preserve`` only it may keep a ``selected_remedy``. A verdict placed by
    any index strategy, a placeholder, and every verdict of a merge without
    ``groups`` has its scope stamps removed (no authority) while its
    normalized scope fields and its validity are kept.

    Args:
        output_dir: Directory containing validation_batch_N.json files
        batch_metadata: The batch metadata from prepare_batched_validation_tasks()
        total_groups: Total number of original groups
        groups: The host's groups the batches were materialized from
            (``grouped.json``), looked up by stable hash; ``None`` stamps
            nothing.
        batch_bytes: ``{batch_index: bytes}`` for the batches the caller has
            already read or taken from its dispatch, ``None`` for one it found
            missing and the ``OSError`` for one it could not read; a batch
            named here is never read from disk
            (docs/development/review-results.md, "Consuming checked bytes").

    Returns:
        Merged validation results list with proper group indices
    """
    output_path = Path(output_dir)

    # Compute required size from batch metadata — during reaggregation the
    # caller may pass a smaller total_groups (new group count) while the
    # batch metadata still references indices from the original grouping.
    effective_total = total_groups
    for batch_info in batch_metadata.get("batches", []):
        for idx in batch_info.get("group_indices", []):
            if idx >= effective_total:
                effective_total = idx + 1

    # Initialize results with failures for all groups
    merged_results: List[Dict[str, Any]] = [
        {
            "group_index": i,
            "status": "validation_failed",
            "reason": _BATCH_NOT_FOUND,
            "confidence": 0.0,
            "error_type": ERROR_TYPE_UNKNOWN,
            "recoverable": True,
        }
        for i in range(effective_total)
    ]

    batches = batch_metadata.get("batches", [])
    batches_found = 0
    batches_missing = 0
    # Counters behind the single end-of-merge summary line below, instead of
    # one `[merge] Warning:` line printed per mismatched verdict.
    hash_join_total = 0
    hash_join_mismatched = 0
    #: original index -> the hash its verdict joined on (Strategy 0 only).
    hash_joined: Dict[int, str] = {}

    for batch_info in batches:
        batch_index = batch_info["batch_index"]
        batch_file = output_path / f"validation_batch_{batch_index}.json"
        given = batch_bytes is not None and batch_index in batch_bytes
        held = batch_bytes[batch_index] if given else None
        missing = held is None if given else not batch_file.exists()

        if missing:
            print(f"[merge] Warning: Batch file not found: {batch_file}")
            batches_missing += 1
            continue

        try:
            if isinstance(held, OSError):
                raise held
            if given:
                batch_data = json.loads(read_back_text(held))
            else:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)

            # Both the wrapped format and a direct list; any other shape is no
            # reply, read as a batch that does not parse is read.
            batch_results, batch_model, dropped = _batch_verdicts(batch_data)
            named = f"{batch_file} (model: {batch_model or 'not named'})"
            if batch_results is None:
                print(f"[merge] Error: {named} is not a list of verdicts "
                      f"({type(batch_data).__name__}); its groups stay "
                      f"validation_failed")
                _unusable_batch(merged_results, batch_info, (
                    f"{batch_file.name} holds no list of verdicts"
                ))
                batches_missing += 1
                continue
            if dropped:
                print(f"[merge] Warning: {named}: dropped {dropped} entr"
                      f"{'y' if dropped == 1 else 'ies'} that are not verdict "
                      f"objects; the rest of the batch is merged")

            # Tag every result with the model its own batch file reported, so
            # `save_validation_results` can derive an overall model when its
            # caller passes none (`_derive_model_from_results`), without this
            # function's return type growing a second value that every one of
            # its several cross-file callers would have to unpack.
            if batch_model:
                for _result in batch_results:
                    _result.setdefault("_source_model", batch_model)

            batches_found += 1

            # Map batch results to original group indices using cascading strategies.
            # LLMs may return global indices, local indices, extra results (filling
            # gaps in non-contiguous batches), or fewer results than expected.
            group_indices = batch_info["group_indices"]
            batch_group_ids = batch_info.get("group_ids", [])

            # Build reverse lookup: group_hash -> original_index
            hash_to_original_index: Dict[str, int] = {}
            for local_idx, gidx in enumerate(group_indices):
                if local_idx < len(batch_group_ids):
                    hash_to_original_index[batch_group_ids[local_idx]] = gidx

            # An id this batch assigned to more than one group (a task file
            # written before ids were stamped) cannot say which of them a
            # verdict echoing it judged: like a foreign hash, the verdict is
            # discarded and its groups are left for revalidation.
            shared_ids = {
                gid for gid in batch_group_ids if batch_group_ids.count(gid) > 1
            }
            if shared_ids:
                kept = [
                    r for r in batch_results
                    if _echoed_hash(r) not in shared_ids
                ]
                if len(kept) != len(batch_results):
                    print(f"[merge] Warning: Batch {batch_index}: discarding "
                          f"{len(batch_results) - len(kept)} result(s) whose "
                          f"group_hash names more than one group of this batch; "
                          f"leaving those groups for revalidation")
                batch_results = kept

            # Strategy 0: Hash-based matching (group_hash is AUTHORITATIVE).
            # Whenever a result echoes a group_hash, route it by hash and ignore
            # its self-reported group_index — this corrects off-by-one and other
            # counting mistakes. Crucially, a result whose hash is *present but
            # foreign* to this batch means the subagent validated the WRONG group;
            # we discard it rather than letting it fall through to the index-based
            # strategies, where its (correct-looking) index would silently stamp
            # the wrong-group reasoning onto a correct slot. The unfilled target is
            # left as validation_failed so it gets revalidated instead of reported
            # with someone else's reasoning. Only results that omit a hash entirely
            # fall through. (See validation-join-by-hash: join by hash, never by
            # position.)
            filled_indices: set = set()
            unhashed_results: List[Dict[str, Any]] = []
            for result in batch_results:
                result_hash = _echoed_hash(result)
                if not result_hash:
                    unhashed_results.append(result)
                    continue
                if result_hash in hash_to_original_index:
                    original_index = hash_to_original_index[result_hash]
                    reported_idx = _reported_group_index(result)
                    hash_join_total += 1
                    if reported_idx != original_index:
                        hash_join_mismatched += 1
                    result["group_index"] = original_index
                    result["group_id"] = result_hash
                    placed = _verdict_or_failure(result)
                    merged_results[original_index] = placed
                    filled_indices.add(original_index)
                    # A later row for the same hash replaces the slot, so it
                    # also decides the slot's scope authority: a failure in
                    # place of a verdict is never stamped.
                    if placed is result:
                        hash_joined[original_index] = result_hash
                    else:
                        hash_joined.pop(original_index, None)
                else:
                    print(f"[merge] Warning: Batch {batch_index}: discarding result with "
                          f"foreign group_hash {result_hash} (not assigned to this batch — "
                          f"subagent likely validated the wrong group); leaving target "
                          f"group for revalidation")

            # Every expected group resolved by hash — nothing left to fall back on.
            if filled_indices and len(filled_indices) == len(group_indices):
                continue

            # Narrow the index-based fallback to groups still unfilled and to
            # results that carried no usable hash (hash-bearing results were already
            # routed or discarded above). Keep group_indices/batch_group_ids aligned.
            remaining_pairs = [
                (gidx, batch_group_ids[i] if i < len(batch_group_ids) else None)
                for i, gidx in enumerate(group_indices)
                if gidx not in filled_indices
            ]
            group_indices = [gi for gi, _ in remaining_pairs]
            batch_group_ids = [gid for _, gid in remaining_pairs]
            batch_results = unhashed_results
            global_indices_set = set(group_indices)

            # Strategy 1: Partial global index match — extract results whose
            # group_index matches an expected global index (ignore extras)
            matched_globals: Dict[int, Dict] = {}
            for result in batch_results:
                result_index = _reported_group_index(result)
                if result_index in global_indices_set:
                    matched_globals[result_index] = result

            if len(matched_globals) == len(group_indices):
                # All expected indices found via global match
                for original_index, result in matched_globals.items():
                    result["group_index"] = original_index
                    local_idx = group_indices.index(original_index)
                    if local_idx < len(batch_group_ids):
                        result["group_id"] = batch_group_ids[local_idx]
                    merged_results[original_index] = _verdict_or_failure(result)
                continue

            # Strategy 2: Positional match — correct count, wrong indices. Not
            # once entries were dropped (`_batch_verdicts`): a dropped entry
            # may have been any group's slot, so the order no longer says
            # which group a verdict judged; index matches below still place
            # theirs and the rest stay validation_failed.
            if len(batch_results) == len(group_indices) and not dropped:
                for i, result in enumerate(batch_results):
                    original_index = group_indices[i]
                    result["group_index"] = original_index
                    if i < len(batch_group_ids):
                        result["group_id"] = batch_group_ids[i]
                    merged_results[original_index] = _verdict_or_failure(result)
                continue

            # Strategy 3: Salvage partial global matches
            if matched_globals:
                for original_index, result in matched_globals.items():
                    result["group_index"] = original_index
                    local_idx = group_indices.index(original_index)
                    if local_idx < len(batch_group_ids):
                        result["group_id"] = batch_group_ids[local_idx]
                    merged_results[original_index] = _verdict_or_failure(result)
                unmatched = global_indices_set - set(matched_globals.keys())
                if unmatched:
                    print(f"[merge] Warning: Batch {batch_index}: matched {len(matched_globals)}/{len(group_indices)}, missing {unmatched}")
                continue

            # Strategy 4: Legacy local index fallback
            for result in batch_results:
                result_index = _reported_group_index(result)
                if 0 <= result_index < len(group_indices):
                    original_index = group_indices[result_index]
                    result["group_index"] = original_index
                    if result_index < len(batch_group_ids):
                        result["group_id"] = batch_group_ids[result_index]
                    merged_results[original_index] = _verdict_or_failure(result)
                else:
                    print(f"[merge] Warning: Index {result_index} out of range for batch {batch_index} (expected 0-{len(group_indices)-1})")

        except (json.JSONDecodeError, IOError) as e:
            print(f"[merge] Error reading batch file {batch_file}: {e}")
            _unusable_batch(merged_results, batch_info, (
                f"{batch_file.name} could not be read as JSON"
            ))
            batches_missing += 1

    print(f"[merge] Merged {batches_found} batches, {batches_missing} missing")
    # One summary line for the whole merge rather than one `[merge] Warning:`
    # per verdict (a correct 16-batch run used to print 41 of them): the hash
    # join is authoritative regardless, so a per-verdict echo mismatch is
    # advisory noise, not an error to itemize. The codebase has no
    # MULTI_LLM_DEBUG/verbose convention for validation.py to gate a per-line
    # form behind, so the summary is what prints.
    if hash_join_mismatched:
        print(f"[merge] {hash_join_mismatched} of {hash_join_total} verdicts "
              f"echoed a different group_index; all joined by hash")

    # Scope authority by hash only. A record left in a slot by an
    # index strategy may be the very object a hash join also placed elsewhere,
    # so stamping replaces the slot's record rather than editing it in place.
    scope_meta = _scope_round.task_scope(batch_metadata)
    host_groups = _scope_round.groups_by_hash(groups)
    stamp_source = "revalidation" if batch_metadata.get("kind") == "revalidation" else "validation"
    for position, record in enumerate(merged_results):
        if not isinstance(record, dict):
            continue
        index = record.get("group_index", position)
        joined = hash_joined.get(index) if isinstance(index, int) else None
        group = host_groups.get(joined) if joined and record.get("group_id") == joined else None
        if group is not None:
            merged_results[position] = _scope_round.stamp(
                record, group, scope_meta, source=stamp_source,
            )
        else:
            merged_results[position] = _scope_round.unbound_record(dict(record))

    # Sort by group index
    merged_results.sort(key=lambda x: x.get("group_index", 0))

    return merged_results


def pinned_validation_guidance(plan_file: Optional[str]) -> str:
    """The code-review validation guidance for a plan whose review is pinned.

    Reads the plan's ``state.json`` (computed beside the plan, never created)
    and, when ``utils.commit_range.pinned_endpoints`` finds a ``commit_range``
    or ``head_ref`` record, returns
    :func:`~utils.subagent_prompts.code_review_validation_guidance` with the
    pinned-head read rule (and the frozen context plan's snapshot, on a commit
    brief that has one). ``""`` when nothing is pinned or the state cannot be
    read, so an unpinned round's prompts are unchanged. Only reads: a
    revalidation materializes against the review on record, and must not be
    the thing that writes the run's state.
    """
    if not plan_file:
        return ""
    try:
        document = json.loads(
            (output_dir_path(Path(plan_file)) / "state.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return ""
    if not isinstance(document, dict):
        return ""
    pinned = pinned_endpoints(document)
    if pinned is None or not pinned.head:
        return ""
    record = document.get("commit_range")
    record = record if isinstance(record, dict) else {}
    return code_review_validation_guidance(
        read_rule=pinned_head_read_rule(pinned.base, pinned.head),
        head=pinned.head,
        change=display_range(pinned.base, pinned.head),
        plan_snapshot=record.get("plan_snapshot") or None,
        plan_sha256=record.get("plan_sha256") or None,
    )


#: The second context block of a revalidation whose current document is not
#: the review round's scope baseline (both labelled contexts).
REVALIDATION_BASELINE_LABEL = (
    "Original scope baseline \u2014 the plan as this review round read it; "
    "judge scope against this, correctness against the context above"
)


def revalidation_scope_binding(
    output_dir: str,
    plan_file: str,
    context_document: Optional[BoundDocument],
    *,
    explicit_policy: Optional[str] = None,
    phase: Optional[str] = None,
) -> Tuple[Dict[str, Any], Optional[BoundDocument]]:
    """``(scope block, original baseline document or None)`` for a revalidation.

    Reads only: the plan's ``state.json`` round record of the review phase
    ``output_dir`` is, and that phase dir's own plan snapshot. The policy is
    resolved as the apply phase resolves it (explicit → recorded apply
    override → recorded review policy → ``expand``). The original document is
    returned only when it hash-matches the round's recorded baseline and the
    current ``context_document`` is not those same bytes.
    """
    review_phase = _sp.review_phase_of(
        phase or os.path.basename(os.path.normpath(output_dir))
    )
    state: Dict[str, Any] = {}
    if plan_file:
        try:
            loaded = json.loads(
                (output_dir_path(Path(plan_file)) / "state.json").read_text(encoding="utf-8")
            )
            state = loaded if isinstance(loaded, dict) else {}
        except (OSError, ValueError):
            state = {}
    record = _sp.round_record(state, review_phase) or {}
    policy, source = _sp.resolve_policy(
        explicit=explicit_policy,
        continuation=record.get("apply_policy"),
        recorded=record.get("review_policy"),
    )
    commit_review = isinstance(state.get("commit_range"), dict)
    prompt_phase = _scope_round.guidance_phase(review_phase, commit_review=commit_review)
    recorded = record.get("baseline") if isinstance(record.get("baseline"), dict) else None
    round_id = _sp.baseline_id_of(recorded)

    primary = None
    for source_record in (recorded or {}).get("sources") or []:
        if isinstance(source_record, dict) and source_record.get("role") in _scope_round.PRIMARY_ROLES:
            primary = source_record
            break

    if context_document is not None and primary is not None and (
        context_document.sha256 == primary.get("sha256")
    ):
        # The current document IS the baseline's: one context serves both.
        return _scope_round.scope_block(
            policy, prompt_phase, source=source, baseline=recorded,
            round_baseline_id=round_id,
        ), None

    original: Optional[BoundDocument] = None
    snapshot = primary.get("snapshot") if primary else None
    if snapshot and primary.get("sha256"):
        path = os.path.join(output_dir, os.path.basename(str(snapshot)))
        try:
            data = Path(path).read_bytes()
        except OSError:
            data = None
        if data is not None and _bytes_sha256(data) == primary.get("sha256"):
            try:
                text = decode_document(data, path)
            except ValidationContextError:
                text = None
            if text is not None:
                original = BoundDocument(
                    label="scope-baseline", text=text, sha256=primary["sha256"],
                    size=len(data), path=os.path.abspath(path), in_phase_dir=True,
                    source_path=primary.get("path") or path,
                )
    if original is not None:
        return _scope_round.scope_block(
            policy, prompt_phase, source=source, baseline=recorded,
            round_baseline_id=round_id, revalidation_baseline_differs=True,
        ), original

    # No readable original baseline: the verdicts are bound to the current
    # document alone, which is a different baseline from the round's (unclear).
    current = _scope_round.build_round_baseline(
        review_phase, plan_document=context_document,
    ) if context_document is not None else None
    return _scope_round.scope_block(
        policy, prompt_phase, source=source, baseline=current,
        round_baseline_id=round_id,
    ), None


def prepare_batched_revalidation_tasks(
    groups: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]],
    context: str,
    output_dir: str,
    plan_file: str = "",
    include_all_human: bool = False,
    model: str = "auto",
    max_per_batch: int = 4,
    orchestrator: str = "review_plan_orchestrator.py",
    base_ref: str = "",
    context_document: Optional[BoundDocument] = None,
    context_kind: Optional[str] = None,
    runner_read_refusal: Optional[Any] = None,
    phase: Optional[str] = None,
    extra_instructions: Optional[str] = None,
    scope_policy: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Prepare batched revalidation tasks for items that failed validation.

    Similar to prepare_batched_validation_tasks, but only includes items that
    need revalidation (validation_failed status, optionally needs-human-decision).

    Args:
        groups: Original grouped suggestions/issues
        validation_results: Previous validation results
        context: Context for validation (plan content or diff)
        output_dir: Directory for batch result files
        plan_file: Path to the plan file for reference
        include_all_human: If True, also revalidate needs-human-decision items
        model: Model hint for reference
        max_per_batch: Maximum groups per batch
        orchestrator: Name of the orchestrator script for reaggregate command
        base_ref: Git ref for code diff context (empty string for plan reviews)
        context_document: The document this revalidation judges against,
            bound when revalidation is materialized (2.1b): the **current**
            document — the one the apply step just wrote — read once and
            snapshotted as ``revalidation-snapshot.md``, never the original
            round's snapshot (recorded alongside for provenance only). Its text
            replaces ``context``.
        context_kind: ``plan``, ``tasks`` or ``diff`` — which document the
            context block carries. A ``diff`` is never named by path and never
            gets the "read the full plan" marker; an oversized one stays
            inline-truncated and is surfaced. Defaults to the document's label,
            else ``plan``.
        runner_read_refusal: As for :func:`prepare_batched_validation_tasks`.
        phase: The phase name the published ``validation_context`` carries.
        extra_instructions: Phase guidance appended to every batch prompt, as
            for :func:`prepare_batched_validation_tasks`. ``None`` derives it:
            a ``diff`` round (a code review's findings) whose plan state pins
            the review to a commit gets :func:`pinned_validation_guidance`, so
            its revalidators read the reviewed code at ``head`` as the review's
            own validators did; anything else
            gets none, as before. apply-code-fixes passes it explicitly
            (``get_revalidation_instructions``), because its batches carry
            the plan fallback as their context, not a ``diff``.
        scope_policy: This invocation's explicit ``--scope-policy``, if any.
            The effective policy is resolved from it, then the review round's
            recorded apply override, then its review policy, then ``expand``
            (``state.json``'s ``scope_policy`` record of the review phase this
            revalidation writes into). Correctness is judged against the
            current document; scope against the round's **original** baseline
            When the current document is not that baseline's
            primary document, the round's own ``validation-snapshot.md`` (hash
            verified) is embedded as a second, labelled context and the
            validators are told so. Without it the verdicts are bound to the
            current document's baseline, which reads ``Scope unclear`` against
            the round's.

    Returns:
        Dict with batches and metadata, or empty batches if nothing to revalidate
    """
    kind_of_context = context_kind or (
        context_document.label if context_document is not None else "plan"
    )
    if context_document is not None:
        context = context_document.text
    if extra_instructions is None:
        extra_instructions = (
            pinned_validation_guidance(plan_file) if kind_of_context == "diff" else ""
        )
    original_sources: List[Dict[str, Any]] = []
    try:
        with open(os.path.join(output_dir, "validation_tasks.json"), "r", encoding="utf-8") as handle:
            original_sources = context_sources_of(json.load(handle))
    except (OSError, ValueError, AttributeError):
        original_sources = []
    # Identify items needing revalidation
    items_to_revalidate = []
    item_indices = []

    for i, val in enumerate(validation_results):
        status = val.get("status", "needs-human-decision")
        error_type = val.get("error_type", ERROR_TYPE_UNKNOWN)

        should_revalidate = (
            status == "validation_failed" or
            (include_all_human and status == "needs-human-decision" and
             error_type != ERROR_TYPE_AMBIGUOUS)
        )

        if should_revalidate and i < len(groups):
            items_to_revalidate.append(groups[i])
            item_indices.append(i)

    if not items_to_revalidate:
        grouped_file = str(Path(output_dir) / "grouped.json")
        return make_task_file(
            kind="revalidation",
            tasks=[],
            inputs=build_inputs(
                plan_file=plan_file,
                grouped_file=grouped_file,
                diff_base=base_ref,
            ),
            task_list_key="batches",
            extra={
                "total_batches": 0,
                "items_to_revalidate": 0,
                "item_indices": [],
                "context_contract": CONTEXT_CONTRACT,
                "original_validation": validation_results,
                "batching_stats": estimate_validation_batching_stats([]),
                "grouped_file": grouped_file,
                "plan_file": plan_file,
                "phase_dir": output_dir,
                "model_hint": model,
                "base_ref": base_ref,
            },
        )

    # Create batched tasks for the subset
    # Revalidation reads the same frozen context plan, including when invoked
    # from apply-code-fixes. Carry its expected hash and source into the task file.
    commit_record = run_commit_range(plan_file)
    context_plan_file = (
        context_plan_path(commit_record, repo_root=get_project_root(plan_file))
        if commit_record else None
    )
    revalidation_scope, original_document = revalidation_scope_binding(
        output_dir, plan_file, context_document,
        explicit_policy=scope_policy,
        phase=phase,
    )
    batched_tasks = materialize_validation_round(ValidationRound(
        groups=items_to_revalidate,
        output_dir=output_dir,
        plan_file=plan_file,
        # The block says which document it carries: the diff a code-fix
        # revalidation judges is labelled a diff, and the plan fallback a plan.
        primary=ContextBlock(
            context,
            {"diff": "Diff context", "tasks": "Tasks file"}.get(
                kind_of_context, PLAN_CONTEXT_LABEL,
            ),
            context_document if context_document is not None else (
                bind_document_text(context, label=kind_of_context)
                if kind_of_context == "diff" else None
            ),
        ),
        secondary=ContextBlock(
            original_document.text, REVALIDATION_BASELINE_LABEL, original_document,
        ) if original_document is not None else None,
        extra_instructions=extra_instructions,
        scope=revalidation_scope,
        runner_read_refusal=runner_read_refusal,
        provenance=RoundProvenance(
            model=model, orchestrator=orchestrator, phase=phase, base_ref=base_ref,
            context_plan_sha256=(commit_record or {}).get("plan_sha256"),
            context_plan_file=context_plan_file,
        ),
        kind="revalidation",
        max_per_batch=max_per_batch,
    ))

    batched_tasks["context_kind"] = kind_of_context
    if original_sources:
        # Provenance only: the original round's snapshot is not the artifact
        # under review — the current document is (2.1b).
        batched_tasks["original_context_sources"] = original_sources

    # Add mapping info for merging back
    batched_tasks["items_to_revalidate"] = len(items_to_revalidate)
    batched_tasks["item_indices"] = item_indices
    batched_tasks["original_validation"] = validation_results

    return batched_tasks


def merge_batched_revalidation_results(
    output_dir: str,
    revalidation_metadata: Dict[str, Any],
    groups: Optional[List[Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Merge batched revalidation results back into original validation results.

    Args:
        output_dir: Directory containing revalidation batch files
        revalidation_metadata: Metadata from prepare_batched_revalidation_tasks()
        groups: The host's current groups, so each revalidated verdict that
            joined by hash is stamped against the proposal it judged (see
            :func:`merge_batched_validation_results`); ``None`` stamps none.

    Returns:
        Updated validation results with revalidated items merged in
    """
    original_validation = revalidation_metadata.get("original_validation", [])
    item_indices = revalidation_metadata.get("item_indices", [])

    if not item_indices:
        return original_validation

    # Merge the batch results
    revalidated_count = revalidation_metadata.get("items_to_revalidate", 0)
    batch_results = merge_batched_validation_results(
        output_dir=output_dir,
        batch_metadata=revalidation_metadata,
        total_groups=revalidated_count,
        groups=groups,
    )

    # Map back to original indices
    updated_results = list(original_validation)
    for j, original_idx in enumerate(item_indices):
        if j < len(batch_results):
            result = batch_results[j]
            result["group_index"] = original_idx
            result["revalidated"] = True
            updated_results[original_idx] = result

    return updated_results
