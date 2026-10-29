#!/usr/bin/env python3
"""
Shared validation utility for plan review and code review orchestrators.

Validates grouped suggestions/issues using an LLM to filter false positives
and identify items needing human review.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import the invoke_for_json utility
try:
    from .llm_client import invoke_for_json
    from .providers.base import (
        CATEGORY_CONNECTION_ERROR,
        CATEGORY_INVALID_MODEL,
        CATEGORY_PERMISSION_DENIED,
        CATEGORY_SERVER_ERROR,
        classify_streams,
    )
    from .retry_ladder import (
        STATUS_AUTH_FAILED,
        STATUS_CONTEXT_LENGTH_EXCEEDED,
        STATUS_RATE_LIMITED,
        STATUS_RUNNER_ERROR,
        STATUS_SPAWN_FAILED,
        STATUS_TIMEOUT,
    )
    from .state_manager import generate_group_id, CURRENT_FORMAT_VERSION
    from .cli_common import (
        current_replay_flags, durable_reaggregate_fields, retry_command,
    )
    from .subagent_prompts import build_validation_prompt, code_review_validation_guidance
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
except ImportError:
    from utils.llm_client import invoke_for_json
    from utils.providers.base import (
        CATEGORY_CONNECTION_ERROR,
        CATEGORY_INVALID_MODEL,
        CATEGORY_PERMISSION_DENIED,
        CATEGORY_SERVER_ERROR,
        classify_streams,
    )
    from utils.retry_ladder import (
        STATUS_AUTH_FAILED,
        STATUS_CONTEXT_LENGTH_EXCEEDED,
        STATUS_RATE_LIMITED,
        STATUS_RUNNER_ERROR,
        STATUS_SPAWN_FAILED,
        STATUS_TIMEOUT,
    )
    from utils.state_manager import generate_group_id, CURRENT_FORMAT_VERSION
    from utils.cli_common import (
        current_replay_flags, durable_reaggregate_fields, retry_command,
    )
    from utils.subagent_prompts import build_validation_prompt, code_review_validation_guidance
    from utils.subagent_tasks import (
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


#: The shared-context ceiling for a validation prompt, applied **per context
#: block**. Excerpted **once per phase** and the identical excerpt reused across
#: every batch: per-batch re-truncation would both bloat the file and break
#: prompt determinism.
#:
#: 60 000 rather than the original 30 000, because 30 000 was under the size of
#: a real plan and the prompt asks the validator to judge against it. Measured
#: on a review-code run over a 44 374-char plan: the excerpt ended mid-§4.6, so
#: §4.7–§11 — the acceptance criteria and the single source of truth for every
#: tunable — reached no validator, and four of the nine verdicts cited exactly
#: those sections (they were right only because that runner could open the file
#: itself, which ``context_mode: inline`` does not promise).
#:
#: Above the limit a plan or tasks document is no longer silently cut: the
#: excerpt stays (so prompts are deterministic and the common case needs no
#: read) and the round's hash-bound snapshot is named by path, the task
#: materializing ``context_mode: workspace-read`` (§2.3 of
#: ``plans/validation-context-by-path-and-codex-0156-fallout.md``). Only a
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
#: ``context_mode: workspace-read`` for an over-limit document (§2.3 of
#: ``plans/validation-context-by-path-and-codex-0156-fallout.md``), but that is
#: decided per document by :data:`VALIDATION_CONTEXT_LIMIT`, never by this
#: file total: the excerpt stays in every batch either way, so a path cannot
#: shrink the file, and failing a phase outright would throw away a completed
#: fan-out over a scratch file being large (the D2f deviation note in
#: ``plans/host-harness-portability.md`` says the same).
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
    §2, §4, §6, the implementation notes at the tail — that no validator had
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
# Validation context by path (plans/validation-context-by-path-and-codex-0156-fallout.md §2)
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
#: read the document it was pointed at (§2.3 step 3a); the aggregate counts them
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
    import hashlib

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
    """One context document bound for a validation round (§2.3 steps 5 and 7).

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
    """temp file + ``os.replace``, so a reader never sees a half-written snapshot."""
    tmp = os.path.join(
        os.path.dirname(target), f".{os.path.basename(target)}.{os.getpid()}.tmp"
    )
    try:
        with open(tmp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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

    One read, one snapshot, one hash domain (§2.3 step 5): the snapshot is
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
    """``(excerpt, context source record)`` for one context block (§2.3 step 7).

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
    """Verdicts whose reason starts ``insufficient-context:`` (§2.3 step 3a)."""
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
    """The one writer of ``.status.json``'s ``validation_context`` (§2.4).

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
    try:
        from .validation_context import (
            build_validation_context,
            validation_context_notice,
        )
        from .status_file import read_status, remove_status_keys, update_status
        from . import cli_common as _cli
    except ImportError:  # pragma: no cover - flat-import fallback
        from utils.validation_context import (  # type: ignore[no-redef]
            build_validation_context,
            validation_context_notice,
        )
        from utils.status_file import (  # type: ignore[no-redef]
            read_status, remove_status_keys, update_status,
        )
        from utils import cli_common as _cli  # type: ignore[no-redef]

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
        # leave a ``"validation_context": null`` member behind (§7.2a).
        if "validation_context" in read_status(phase_dir):
            remove_status_keys(phase_dir, ["validation_context"])
        recorder = getattr(_cli, "record_validation_context", None)
        if recorder is not None:
            recorder(None)
        _cli.record_notice(None)
        return None
    update_status(phase_dir, {"validation_context": obj})
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

    ``newline=""`` is load-bearing: a text-mode open on Windows would rewrite
    ``\n`` as ``\r\n`` and the file would no longer equal ``prompt`` — and
    byte identity is the whole contract, since a host hands a subagent this file
    *instead of* the prompt. Same temp-then-``os.replace`` shape as
    ``subagent_executor._atomic_write_json``, written out here because importing
    that module from this one would close a cycle.
    """
    tmp = os.path.join(
        os.path.dirname(target), f".{os.path.basename(target)}.{os.getpid()}.tmp"
    )
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(prompt)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except OSError:
        # The all-or-none rule above removes the sidecars this one already
        # wrote; without this the *partial* write would survive as a hidden
        # `.…tmp` in the phase dir, matched by no glob and cleaned by nothing.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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
    generation (``task_generation.prompt.txt``) pass theirs (live run 8:
    the Claude Code host wrote both kinds' prompts to temp files by hand, or
    pasted a 21 KB prompt into its subagent call). A phase where some
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
    changes before handing the task file back to a native host.
    """
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


#: Our *own* extraction failing, which is not a transport category at all — the
#: provider answered, and this codebase could not turn the answer into JSON.
#: Lane B's equivalent is D3k rung 5 (``unparseable_result``), not anything
#: ``classify_failure`` returns, which is why this half deliberately stays local
#: while the four transport categories delegate (§7.1.a).
#:
#: The bare ``"json"`` this list used to open with is gone: it classified *any*
#: error merely **naming** a ``.json`` path — "output file …/plan_review.json was
#: never written" — as a parsing error, hence ``recoverable``, hence worth a
#: whole revalidation dispatch on a condition no re-ask can fix. Every entry now
#: names a parse *event*.
_PARSING_PATTERNS = (
    "json parse",
    "parse json",
    "json decode",
    "jsondecodeerror",
    "invalid json",
    "no valid json",
    "no json found",
    "malformed json",
    "parse error",
    "parsing error",
    "decode error",
    "decodeerror",
    "syntax error",
    "unexpected token",
    "expecting value",
    "expecting property",
)

#: The shared classifier's categories, mapped onto the vocabulary this module
#: **persists** (§7.1.a). The mapping is deliberately lossy in one direction
#: only: several distinct infrastructure verdicts collapse onto
#: ``ERROR_TYPE_MODEL_FAILURE``, which is correctly **not** in
#: :data:`RECOVERABLE_ERROR_TYPES` — none of them is fixed by re-asking.
_CATEGORY_TO_ERROR_TYPE = {
    STATUS_RATE_LIMITED: ERROR_TYPE_RATE_LIMITED,
    STATUS_TIMEOUT: ERROR_TYPE_TIMEOUT,
    CATEGORY_CONNECTION_ERROR: ERROR_TYPE_MODEL_FAILURE,
    CATEGORY_SERVER_ERROR: ERROR_TYPE_MODEL_FAILURE,
    STATUS_AUTH_FAILED: ERROR_TYPE_MODEL_FAILURE,
    STATUS_SPAWN_FAILED: ERROR_TYPE_MODEL_FAILURE,
    CATEGORY_PERMISSION_DENIED: ERROR_TYPE_MODEL_FAILURE,
    CATEGORY_INVALID_MODEL: ERROR_TYPE_MODEL_FAILURE,
    # A broken OS sandbox (D6) is a property of the machine, never of the turn.
    "sandbox_unavailable": ERROR_TYPE_MODEL_FAILURE,
    STATUS_RUNNER_ERROR: ERROR_TYPE_MODEL_FAILURE,
    # A prompt that does not fit is terminal (§7.6(a)) and must never be
    # recorded recoverable: a revalidation pass would resend it unchanged.
    STATUS_CONTEXT_LENGTH_EXCEEDED: ERROR_TYPE_MODEL_FAILURE,
}


def _classify_validation_error(error: str, http_status: Optional[int] = None) -> str:
    """
    Classify a validation error by type.

    Note: This function is for FAILURES during validation (parsing, timeout, etc.).
    For genuine ambiguity where the LLM returns needs-human-decision, use
    ERROR_TYPE_AMBIGUOUS directly in the validation result handler.

    **Signature, return vocabulary and the ``http_status`` fast path are frozen**
    (§7.1.a): callers branch on the ``ERROR_TYPE_*`` constants, and
    ``error_type``/``recoverable`` are written into every persisted group result
    and read downstream by ``filtering.RECOVERABLE_ERROR_TYPES``. What changed is
    the *body*: this used to be a second, complete classifier — five ordered
    substring lists including a bare ``"429"`` with the same boundary flaw Lane A
    had, and a bare ``"json"`` — living three modules away from the one in
    ``providers/base.py`` and disagreeing with it. The four transport categories
    now delegate, and only the parse half stays local, because that classifies
    *our own* extraction failure rather than the provider's transport.

    Args:
        error: The error message string
        http_status: Optional HTTP status code if available (e.g., 429 for rate limit)

    Returns:
        One of the ERROR_TYPE_* constants
    """
    error_lower = (error or "").lower()

    # Check HTTP status codes first (most reliable). It stays *first* and stays
    # local: it is the one input that needs no patterns at all.
    if http_status:
        if http_status == 429:
            return ERROR_TYPE_RATE_LIMITED
        elif http_status in (408, 504):
            return ERROR_TYPE_TIMEOUT
        elif http_status in (500, 502, 503):
            return ERROR_TYPE_MODEL_FAILURE

    if any(pattern in error_lower for pattern in _PARSING_PATTERNS):
        return ERROR_TYPE_PARSING

    # Also classify non-success-but-parsable responses (raw/malformed data) as parsing errors
    if "raw" in error_lower and ("response" in error_lower or "output" in error_lower):
        return ERROR_TYPE_PARSING

    category = classify_streams(error or "", "")
    return _CATEGORY_TO_ERROR_TYPE.get(category, ERROR_TYPE_UNKNOWN)


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


VALIDATION_PROMPT_TEMPLATE = '''You are validating review suggestions/issues for accuracy.

## Context
{context}

## Suggestions to Validate
{suggestions_json}

## Your Task
For each suggestion, determine if it is:
- "valid": The issue is real and should be addressed
- "invalid": False positive, the suggestion is incorrect or not applicable
- "needs-human-decision": Cannot be determined automatically, requires human judgment

## Output Format
Return ONLY a valid JSON array with one entry per suggestion group:
[
  {{
    "group_index": 0,
    "status": "valid" | "invalid" | "needs-human-decision",
    "reason": "Brief explanation for the classification",
    "confidence": 0.0-1.0
  }}
]
'''


async def validate_groups(
    groups: List[Dict[str, Any]],
    context: str,
    model: str = "auto",
    timeout: int = 120
) -> List[Dict[str, Any]]:
    """
    Validate grouped suggestions/issues using an LLM.

    Args:
        groups: List of suggestion groups (from group_similar_suggestions or similar)
                Each group should have 'theme', 'suggestions', etc.
        context: Context for validation (plan content or diff)
        model: Model to use for validation (default: "auto")
        timeout: Timeout in seconds

    Returns:
        List of validation results:
        [
            {
                "group_index": int,
                "status": "valid" | "invalid" | "needs-human-decision",
                "reason": str,
                "confidence": float
            }
        ]
    """
    if not groups:
        return []

    # Pre-compute group_ids for stable matching after reaggregation
    group_ids = []
    for group in groups:
        if hasattr(group, 'to_dict'):
            group_dict = group.to_dict()
        else:
            group_dict = group
        group_ids.append(generate_group_id(group_dict))

    # Prepare suggestions JSON for the prompt
    # Extract key info from each group for validation
    validation_input = []
    for i, group in enumerate(groups):
        # Handle both dict and SuggestionGroup objects
        if hasattr(group, 'to_dict'):
            group_dict = group.to_dict()
        else:
            group_dict = group

        validation_input.append({
            "index": i,
            "group_id": group_ids[i],
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

    prompt = VALIDATION_PROMPT_TEMPLATE.format(
        context=context,
        suggestions_json=suggestions_json
    )

    print(f"[validation] Starting validation of {len(groups)} groups with model '{model}'...")

    result = invoke_for_json(
        prompt=prompt,
        model=model,
        timeout=timeout
    )

    if not result.get("success"):
        error = result.get("error", "Unknown error")
        error_type = _classify_validation_error(error)
        print(f"[validation] Failed: {error} (type: {error_type})")

        # Use validation_failed status for recoverable errors
        status = "validation_failed" if error_type in RECOVERABLE_ERROR_TYPES else "needs-human-decision"

        # Return all as validation_failed or needs-human-decision on failure WITH error type
        return [
            {
                "group_index": i,
                "group_id": group_ids[i],
                "status": status,
                "reason": f"Validation failed: {error}",
                "confidence": 0.0,
                "error_type": error_type,
                "recoverable": error_type in RECOVERABLE_ERROR_TYPES
            }
            for i in range(len(groups))
        ]

    data = result.get("data", [])

    # Handle case where data is wrapped or malformed
    if isinstance(data, dict) and "raw" in data:
        print("[validation] Warning: Could not parse validation response")
        return [
            {
                "group_index": i,
                "group_id": group_ids[i],
                "status": "validation_failed",
                "reason": "Could not parse validation response",
                "confidence": 0.0,
                "error_type": ERROR_TYPE_PARSING,
                "recoverable": True
            }
            for i in range(len(groups))
        ]

    if not isinstance(data, list):
        print("[validation] Warning: Unexpected response format")
        return [
            {
                "group_index": i,
                "group_id": group_ids[i],
                "status": "validation_failed",
                "reason": "Unexpected validation response format",
                "confidence": 0.0,
                "error_type": ERROR_TYPE_PARSING,
                "recoverable": True
            }
            for i in range(len(groups))
        ]

    # Validate and normalize results
    validation_results = []
    valid_statuses = {"valid", "invalid", "needs-human-decision"}

    for item in data:
        # Coerced, not read raw: an echo that is not an index (a copied reply
        # placeholder, a null) must not reach the `0 <= group_index` comparison
        # below or the sort at the end of this function as a string.
        group_index = _reported_group_index(item)
        status = item.get("status", "needs-human-decision")
        reason = item.get("reason", "No reason provided")
        # `.get(..., 0.5)`'s default only fires when the key is absent; an LLM
        # that replies with an explicit `"confidence": null` would otherwise
        # reach the clamp below as None and crash `float(None)`.
        confidence = item.get("confidence", 0.5)
        if confidence is None:
            confidence = 0.5

        # Normalize status
        if status not in valid_statuses:
            status = "needs-human-decision"

        # Clamp confidence
        confidence = max(0.0, min(1.0, float(confidence)))

        result_entry = {
            "group_index": group_index,
            "status": status,
            "reason": reason,
            "confidence": confidence
        }
        # Add group_id - prefer from LLM response, else compute from index
        if item.get("group_id"):
            result_entry["group_id"] = item["group_id"]
        elif 0 <= group_index < len(group_ids):
            result_entry["group_id"] = group_ids[group_index]
        validation_results.append(result_entry)

    # Fill in any missing groups
    validated_indices = {r["group_index"] for r in validation_results}
    for i in range(len(groups)):
        if i not in validated_indices:
            validation_results.append({
                "group_index": i,
                "group_id": group_ids[i],
                "status": "needs-human-decision",
                "reason": "Not included in validation response",
                "confidence": 0.0
            })

    # Sort by group index
    validation_results.sort(key=lambda x: x["group_index"])

    # Summary
    valid_count = sum(1 for r in validation_results if r["status"] == "valid")
    invalid_count = sum(1 for r in validation_results if r["status"] == "invalid")
    needs_human = sum(1 for r in validation_results if r["status"] == "needs-human-decision")
    validation_failed = sum(1 for r in validation_results if r["status"] == "validation_failed")
    summary_parts = [f"{valid_count} valid", f"{invalid_count} invalid", f"{needs_human} needs-human-decision"]
    if validation_failed > 0:
        summary_parts.append(f"{validation_failed} validation_failed")
    print(f"[validation] Complete: {', '.join(summary_parts)}")

    return validation_results


def apply_validation_to_groups(
    groups: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply validation results to groups by adding validation status.

    Uses group_id (stable content hash) for matching when available. This
    ensures validation results remain correctly associated with groups even
    after reaggregation changes the sort order.

    The ``group_index`` fallback exists for *hash-less* records only — the
    pre-hash ``validation.json`` format, where the index was the identity. A
    hashed record that matches no group is a verdict about a group that no
    longer exists (the grouping changed underneath it, D7); handing it to
    whichever group now sits at its index attributes another group's status,
    reason and confidence to it, so such a group is left at the default
    "No validation result" and the count of those groups is printed.

    Args:
        groups: Original groups (list of dicts or SuggestionGroup objects)
        validation_results: Results from validate_groups()

    Returns:
        Groups with validation_status and validation_reason added
    """
    # Build lookups - group_id for hashed records, group_index for the rest
    validation_by_id = {
        r.get("group_id"): r
        for r in validation_results
        if r.get("group_id")
    }
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
    for i, group in enumerate(groups):
        # Handle both dict and SuggestionGroup objects
        if hasattr(group, 'to_dict'):
            group_dict = group.to_dict()
        else:
            group_dict = dict(group)

        # Compute group_id for matching
        gid = generate_group_id(group_dict)

        # group_id first; the index only reaches records that carry no hash
        validation = (
            validation_by_id.get(gid) or
            validation_by_index.get(i)
        )
        if validation is None:
            validation = default_validation
            unmatched += 1

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
    if not isinstance(document, dict):
        return None, []
    return batch_manifest(document), tasks_of(document)


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
) -> Tuple[Optional[str], str]:
    """``(stale_reason, use_note)`` for a ``validation.json`` (D7, §7.1).

    ``stale_reason`` is ``None`` when the file may be used, else the one-line
    reason it must be retired and the batch files re-merged. ``use_note`` is the
    parenthetical the caller prints when it *does* use the file, naming what was
    checked (§7.1b).

    The checks, in order:

    1. **Grouping (D7).** ``metadata.grouped_sha256`` must match the
       ``grouped.json`` beside it now.
    2. **Batch bytes (§7.1a).** A file written by ``merge_validation_batches``
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
       §7.1, or by a writer that merges no batches of this round) keeps the old
       mtime test: it is honoured only if no ``validation_batch_*.json`` beside
       it is newer. No merge writes a file without the binding any more.

    Hook point: a further check on a bound, up-to-date file (the context
    contract, task 2.10) belongs after check 2, before the use note is built.

    Args:
        validation_path: The ``validation.json`` to judge.
        grouped_path: The ``grouped.json`` it must belong to.
        tasks_path: The current task file; defaults to the
            ``validation_tasks.json`` beside ``validation_path``.
    """
    try:
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
        current_hash = file_content_hash(str(grouped_path))
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
        current_manifest, current_tasks = _read_task_manifest(tasks_path)
        recorded_manifest = metadata.get("batch_manifest")
        problems: List[str] = []
        # The round check needs both sides: a file that merged no batch round
        # (an internal validation) records none, and a task file deleted by hand
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
        legacy = _legacy_contract_reason(metadata, phase_dir)
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
    legacy = _legacy_contract_reason(metadata, validation_path.parent)
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


def _legacy_contract_reason(metadata: Dict[str, Any], phase_dir: Path) -> Optional[str]:
    """7.1d: a ``validation.json`` from before contract 2 over an over-limit round."""
    try:
        contract = int(metadata.get("context_contract") or 1)
    except (TypeError, ValueError):
        contract = 1
    if contract >= CONTEXT_CONTRACT:
        return None
    return legacy_context_round_reason(str(phase_dir))


def stale_validation_reason(
    validation_path: Path,
    grouped_path: Path,
    tasks_path: Optional[Path] = None,
) -> Optional[str]:
    """Why a ``validation.json`` must not be trusted over the batch files, or ``None``.

    The reason half of :func:`validation_source_decision`, which documents the
    rules: the ``grouped_sha256`` binding (D7), the ``batch_sha256`` +
    ``batch_manifest`` binding to the exact batch bytes it merged (§7.1), and —
    for a file without ``batch_sha256`` only — the legacy "a batch file is
    newer" mtime test.

    Returns:
        ``None`` when the file may be used, else a one-line reason for the log.
    """
    return validation_source_decision(validation_path, grouped_path, tasks_path)[0]


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
    comma-joined list — never ``"mixed"`` (§7.3b).

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
) -> None:
    """
    Save validation results to a JSON file with metadata.

    When groups are provided, computes and stores group_id for each result
    to enable stable matching after reaggregation.

    ``metadata.grouped_sha256`` binds the file to the ``grouped.json`` it was
    produced for (D7) — the same ``file_content_hash`` value
    ``validation_tasks.json`` records under ``inputs.grouped_sha256`` — so
    ``reaggregate_from_existing_files`` can tell a file left behind by an
    earlier grouping from one that belongs to the current one. Defaults to the
    ``grouped.json`` beside ``output_path``; the key is omitted when that file
    does not exist.

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
        groups: Optional list of groups to compute group_ids from
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
        runners: ``{batch_index: model}`` — who answered each batch (§7.3b),
            stored as ``metadata.runners`` so the per-batch answer survives a
            joined ``model``.
        batch_sha256: ``{batch_index: sha256}`` over the bytes of every batch
            merged into this file (§7.1a). An empty dict is still a binding
            (a writer that merged no batches); ``None`` omits the key and leaves
            the file on the legacy mtime test in ``stale_validation_reason``.
        batch_manifest: ``{kind, round}`` of the task file those batches
            answered (§7.1a), so a hash recorded under one round is never
            matched against another round's file of the same name.
    """
    if not model:
        model = _derive_model_from_results(validation_results) or "unknown"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if grouped_file is None:
        grouped_file = str(output_path.parent / "grouped.json")
    grouped_sha256 = file_content_hash(grouped_file)

    # Build a mapping from index to group_id if groups provided
    group_id_by_index = {}
    if groups:
        for i, group in enumerate(groups):
            if hasattr(group, 'to_dict'):
                group_dict = group.to_dict()
            else:
                group_dict = group
            group_id_by_index[i] = generate_group_id(group_dict)

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
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_data, f, indent=2)
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

        # Compute group_id for stable matching after reaggregation
        gid = generate_group_id(group_dict)

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


def prepare_revalidation_task(
    groups: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]],
    context: str,
    output_path: str,
    include_all_human: bool = False,
    model: str = "auto"
) -> Dict[str, Any]:
    """
    Prepare revalidation input for Claude Code subagent.

    Similar to prepare_validation_task, but only includes items that need
    revalidation (validation_failed status, optionally needs-human-decision).

    Args:
        groups: Original grouped suggestions/issues
        validation_results: Previous validation results
        context: Context for validation (plan content or diff)
        output_path: Path where subagent should write results
        include_all_human: If True, also revalidate needs-human-decision items
        model: Model hint for reference

    Returns:
        Dict with:
        - prompt: Full validation prompt for subagent (or None if nothing to revalidate)
        - output_path: Where subagent should write results
        - items_to_revalidate: Count of items needing revalidation
        - item_indices: List of original indices being revalidated
        - original_validation: The original validation results (for merging later)
    """
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
        return {
            "prompt": None,
            "output_path": output_path,
            "items_to_revalidate": 0,
            "item_indices": [],
            "original_validation": validation_results,
            "model_hint": model,
        }

    # Prepare the validation task for the subset
    validation_task = prepare_validation_task(
        groups=items_to_revalidate,
        context=context,
        output_path=output_path,
        model=model
    )

    return {
        "prompt": validation_task["prompt"],
        "output_path": output_path,
        "items_to_revalidate": len(items_to_revalidate),
        "item_indices": item_indices,
        "original_validation": validation_results,
        "suggestions_json": validation_task["suggestions_json"],
        "model_hint": model,
    }


def load_validation_results(validation_path: Path) -> List[Dict[str, Any]]:
    """
    Load validation results with migration for older format files.

    Older validation.json files may not have error_type, recoverable, or
    revalidated fields. This function applies sensible defaults to ensure
    compatibility.

    Args:
        validation_path: Path to the validation.json file

    Returns:
        List of validation results with all fields populated
    """
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


async def revalidate_failed_items(
    groups: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]],
    context: str,
    model: str = "auto",
    include_all_human: bool = False,
    timeout: int = 180
) -> List[Dict[str, Any]]:
    """
    Re-run validation only on items that previously failed.

    Args:
        groups: Original grouped suggestions/issues
        validation_results: Previous validation results
        context: Context for validation (plan content or diff)
        model: Model to use for revalidation
        include_all_human: If True, also revalidate needs-human-decision items
        timeout: Timeout in seconds (default higher for retry)

    Returns:
        Updated validation results
    """
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
        print("[revalidate] No items need revalidation")
        return validation_results

    print(f"[revalidate] Re-validating {len(items_to_revalidate)} items with model '{model}'...")

    # Run validation on subset with error handling
    try:
        new_results = await validate_groups(
            groups=items_to_revalidate,
            context=context,
            model=model,
            timeout=timeout
        )
    except Exception as e:
        # Revalidation itself failed - apply fallback strategy
        print(f"[revalidate] ERROR: Revalidation failed: {e}", file=sys.stderr)
        error_type = _classify_validation_error(str(e))

        # Fallback strategies based on error type
        if error_type == ERROR_TYPE_RATE_LIMITED:
            print("[revalidate] Fallback: Rate limited. Try again later or use --revalidate-model with a different provider.", file=sys.stderr)
        elif error_type == ERROR_TYPE_TIMEOUT:
            print("[revalidate] Fallback: Timeout. Try --revalidate-model with a faster model.", file=sys.stderr)
        else:
            print(f"[revalidate] Fallback: Keeping original validation status for {len(items_to_revalidate)} items.", file=sys.stderr)

        # Return original results unchanged on failure
        return validation_results

    # Check if revalidation produced more failures
    revalidation_failures = sum(1 for r in new_results if r.get("status") == "validation_failed")
    if revalidation_failures > 0:
        print(f"[revalidate] Warning: {revalidation_failures} items still failed validation after retry.", file=sys.stderr)
        print("[revalidate] Consider using --approve-validation-failed or trying a different model.", file=sys.stderr)

    # Merge results back
    updated_results = list(validation_results)
    for j, original_idx in enumerate(item_indices):
        new_result = new_results[j] if j < len(new_results) else validation_results[original_idx]
        new_result["group_index"] = original_idx
        new_result["revalidated"] = True
        new_result["revalidation_model"] = model
        updated_results[original_idx] = new_result

    # Summary of changes
    improved = sum(
        1 for j, idx in enumerate(item_indices)
        if j < len(new_results) and new_results[j].get("status") == "valid"
    )
    print(f"[revalidate] Complete: {improved} items now valid after revalidation")

    return updated_results


# --- Batched Validation Functions ---

try:
    from .validation_batcher import (
        batch_validation_groups,
        estimate_validation_batching_stats,
        ValidationBatch,
    )
except ImportError:
    from utils.validation_batcher import (
        batch_validation_groups,
        estimate_validation_batching_stats,
        ValidationBatch,
    )


def build_validation_batch_records(
    groups: List[Dict[str, Any]],
    group_indices: List[str],
    group_ids: List[str],
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
                    **({"file": s["file"]} if s.get("file") else {}),
                    **(
                        {"line_range": s["line_range"]}
                        if s.get("line_range") else {}
                    ),
                }
                for s in group_dict.get("suggestions", [])
            ],
        })
    return records


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

    *typed_plan* (the native hand-off's printed command, fix round 14) names
    the plan as this invocation's user typed it when that spelling names the
    same file (``cli_common.typed_plan_for``).
    """
    mode = document.get("reaggregate_mode")
    plan = document.get("plan_file")
    if mode and plan and typed_plan:
        from .cli_common import typed_plan_for

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
    context_label: str = "Plan content",
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
) -> Dict[str, Any]:
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

    The shared context is excerpted **once** and the identical excerpt reused
    across batches: per-batch re-truncation would break prompt determinism.

    Args:
        groups: List of suggestion groups to validate
        context: Context for validation (plan content or diff); excerpted once
            and embedded in every batch prompt
        output_dir: Directory where subagents should write batch results
        plan_file: Path to the plan file (provenance and the ``inputs`` hash;
            never interpolated into prompt text)
        model: Model hint, preserved verbatim (free-form model string or ``auto``)
        max_per_batch: Maximum groups per batch for normal items
        orchestrator: Name of the orchestrator script for reaggregate command
        base_ref: Git ref for code diff context (empty string for plan reviews);
            recorded as ``inputs.diff_base``
        tasks_file: Path to the tasks file for review-tasks validation context;
            recorded as provenance *and* hashed into ``inputs.tasks_sha256``
        kind: ``"validation"`` or ``"revalidation"`` — the task ``kind``
        context_label: What the embedded context is (``"Plan content"``, …)
        secondary_context: An optional second document to embed beside
            ``context`` (review-tasks: the task list its suggestions are about).
            Excerpted **separately**, against the same per-context limit, so a
            long plan cannot squeeze the artifact under review out of the prompt
        secondary_context_label: What that second document is; required with it
        reviewed_code: The code-under-review excerpt to hash into
            ``inputs.reviewed_code_sha256`` (code-review). Passed rather than
            derived from ``secondary_context`` because a phase is free to embed
            more than the code in its second block, and the hash has to name
            the code alone
        extra_instructions: Optional capability-neutral phase guidance appended
            to every batch prompt (e.g. the code-review issue-location guidance)
        prompt_budget: Optional D2d budget. Over-budget batches are split; a
            single group that still does not fit fails loudly rather than being
            truncated.
        context_document: The round's bound primary document (§2.3 step 5):
            the plan read once as bytes, with its hash-bound snapshot. Its text
            hash becomes ``inputs.plan_sha256`` (label ``plan``) instead of a
            re-read of the live ``plan_file``, and over the limit its snapshot
            is what the prompt names. ``None`` keeps the legacy behaviour: no
            path, and an over-limit block is ``mode: truncated``.
        secondary_document: The same for the second block (review-tasks'
            tasks file, label ``tasks``; review-code's reviewed-code block,
            label ``reviewed-code``, which is never named by path).
        runner_read_refusal: Who will read a ``mode: path`` source (§2.3 step
            4a, decided at materialization): ``None`` (assume a capable reader
            — every ``agent-readonly`` adapter declares workspace reads, and a
            native host reads), a string (the reason no source may be named by
            path, e.g. "runner R cannot read files"), or a callable taking the
            absolute path and returning ``None`` or such a reason (a runner
            that cannot read outside its cwd). An explicit ``prompt_budget``
            whose ``supports_workspace_reads`` is false counts as a refusal.
        phase: The phase name the published ``validation_context`` carries
            (defaults to the phase dir's basename).
        publish: Publish ``validation_context`` for this round (the
            materialization caller of :func:`publish_validation_context`).
        head_ref: The commit a review pinned to two commits ends at
            (``review-code --head-ref``, plans/review-commits.md §2.5). Then
            ``inputs.diff_base`` records ``<base_ref>..<head_ref>``, the pair
            the excerpts were read from; ``None`` keeps ``base_ref`` alone.
        context_plan_sha256: A commit review's ``commit_range.plan_sha256``
            (§2.4 "The context plan is frozen"), recorded as
            ``inputs.context_plan_sha256`` so a resume or reaggregate whose
            snapshot no longer hashes to it is refused. ``None`` adds no key.
        context_plan_file: The frozen snapshot's path, recorded relative to the
            phase directory so executor resumes can verify that raw-byte hash.

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
        # One read, one hash domain (§2.3 step 5): a bound document's hash is
        # taken over the bytes the round read, never over a second read of the
        # live file, so the excerpt, the snapshot and `inputs` cannot come from
        # two versions. The value keeps the 16-char text-hash domain the
        # resume guard and `state.plan_hash` compare in.
        plan_file=None if bound_plan is not None else plan_file,
        grouped_file=grouped_file,
        tasks_file=None if bound_tasks is not None else tasks_file,
        diff_base=(
            f"{base_ref}..{head_ref}" if base_ref and head_ref else base_ref
        ),
        reviewed_code=reviewed_code,
        context_plan_sha256=context_plan_sha256,
    )
    if bound_plan is not None:
        inputs["plan_sha256"] = content_hash(bound_plan.text)
    if bound_tasks is not None and tasks_file:
        inputs["tasks_sha256"] = content_hash(bound_tasks.text)

    if not groups:
        if publish:
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
        })
        return empty

    # Create batches
    validation_batches = batch_validation_groups(
        groups=groups,
        max_per_batch=max_per_batch,
        isolate_high=True
    )

    # Pre-compute group_ids for all groups
    group_ids = []
    for group in groups:
        if hasattr(group, 'to_dict'):
            group_dict = group.to_dict()
        else:
            group_dict = group
        group_ids.append(generate_group_id(group_dict))

    # The one shared excerpt, reused verbatim by every batch below. A second
    # document is excerpted on its own budget rather than appended to the first:
    # concatenating would let a plan at the limit truncate the artifact under
    # review down to nothing, which is the failure two contexts exist to fix.
    #
    # Each block becomes one context source record (§2.3 step 7): inline when
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
    if secondary_context:
        secondary_label = secondary_document.label if secondary_document is not None else (
            "tasks" if tasks_file else "reviewed-code"
        )
        shared_secondary, secondary_source = build_context_source(
            secondary_context, secondary_document, label=secondary_label,
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
    any_path = any(source["mode"] == "path" for source in sources)
    context_mode = "workspace-read" if any_path else "inline"
    # Only a round that is not wholly inline records its sources on the task:
    # an under-limit task is byte-identical to what contract 1 wrote, so its
    # goldens do not move.
    task_sources = sources if any(s["mode"] != "inline" for s in sources) else None
    prompt_sources = [s for s in sources if s["mode"] == "path"] or None
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
        prompt = build_validation_prompt(
            plan_excerpt=shared_context,
            suggestion_records=records,
            kind=kind,
            context_label=context_label,
            secondary_excerpt=shared_secondary,
            secondary_label=secondary_context_label,
            extra_instructions=extra_instructions,
            context_sources=prompt_sources,
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
            # by VALIDATION_CONTEXT_LIMIT (§2.3), not by the transport budget,
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
        **durable_reaggregate_fields(orchestrator, plan_file),
        "model_hint": model,
        "base_ref": base_ref,
    }
    if tasks_file:
        extra["tasks_file"] = tasks_file
    document = make_task_file(
        kind=kind,
        tasks=batch_tasks,
        inputs=inputs,
        task_list_key="batches",
        extra=extra,
    )
    if publish:
        publish_validation_context(output_dir, sources, phase=phase)
    return document


def merge_batched_validation_results(
    output_dir: str,
    batch_metadata: Dict[str, Any],
    total_groups: int
) -> List[Dict[str, Any]]:
    """
    Merge results from multiple validation batch files.

    Args:
        output_dir: Directory containing validation_batch_N.json files
        batch_metadata: The batch metadata from prepare_batched_validation_tasks()
        total_groups: Total number of original groups

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
            "reason": "Batch result not found",
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

    for batch_info in batches:
        batch_index = batch_info["batch_index"]
        batch_file = output_path / f"validation_batch_{batch_index}.json"

        if not batch_file.exists():
            print(f"[merge] Warning: Batch file not found: {batch_file}")
            batches_missing += 1
            continue

        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)

            # Handle both wrapped format and direct list
            if isinstance(batch_data, dict):
                batch_results = batch_data.get("groups", [])
                batch_model = batch_data.get("metadata", {}).get("model")
            else:
                batch_results = batch_data
                batch_model = None

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
                result_hash = result.get("group_hash") or result.get("group_id")
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
                    merged_results[original_index] = result
                    filled_indices.add(original_index)
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
                    merged_results[original_index] = result
                continue

            # Strategy 2: Positional match — correct count, wrong indices
            if len(batch_results) == len(group_indices):
                for i, result in enumerate(batch_results):
                    original_index = group_indices[i]
                    result["group_index"] = original_index
                    if i < len(batch_group_ids):
                        result["group_id"] = batch_group_ids[i]
                    merged_results[original_index] = result
                continue

            # Strategy 3: Salvage partial global matches
            if matched_globals:
                for original_index, result in matched_globals.items():
                    result["group_index"] = original_index
                    local_idx = group_indices.index(original_index)
                    if local_idx < len(batch_group_ids):
                        result["group_id"] = batch_group_ids[local_idx]
                    merged_results[original_index] = result
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
                    merged_results[original_index] = result
                else:
                    print(f"[merge] Warning: Index {result_index} out of range for batch {batch_index} (expected 0-{len(group_indices)-1})")

        except (json.JSONDecodeError, IOError) as e:
            print(f"[merge] Error reading batch file {batch_file}: {e}")
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
        from .commit_range import display_range, pinned_endpoints, pinned_head_read_rule
        from .output_handler import output_dir_path
    except ImportError:  # pragma: no cover - flat import layout
        from utils.commit_range import display_range, pinned_endpoints, pinned_head_read_rule
        from utils.output_handler import output_dir_path
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
            own validators did (plans/review-commits.md §2.5); anything else
            gets none, as before. apply-code-fixes passes it explicitly
            (``get_revalidation_instructions``), because its batches carry
            the plan fallback as their context, not a ``diff``.

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
    try:
        from .commit_report import context_plan_path, run_commit_range
        from .git_utils import get_project_root
    except ImportError:  # pragma: no cover - flat import layout
        from utils.commit_report import context_plan_path, run_commit_range
        from utils.git_utils import get_project_root

    commit_record = run_commit_range(plan_file)
    context_plan_file = (
        context_plan_path(commit_record, repo_root=get_project_root(plan_file))
        if commit_record else None
    )
    batched_tasks = prepare_batched_validation_tasks(
        groups=items_to_revalidate,
        context=context,
        output_dir=output_dir,
        plan_file=plan_file,
        model=model,
        max_per_batch=max_per_batch,
        orchestrator=orchestrator,
        base_ref=base_ref,
        kind="revalidation",
        context_plan_file=context_plan_file,
        context_plan_sha256=(commit_record or {}).get("plan_sha256"),
        extra_instructions=extra_instructions,
        # The block says which document it carries: the diff a code-fix
        # revalidation judges is labelled a diff, and the plan fallback a plan.
        context_label={
            "diff": "Diff context",
            "tasks": "Tasks file",
        }.get(kind_of_context, "Plan content"),
        context_document=context_document if context_document is not None else (
            bind_document_text(context, label=kind_of_context)
            if kind_of_context == "diff" else None
        ),
        runner_read_refusal=runner_read_refusal,
        phase=phase,
    )

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
    revalidation_metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Merge batched revalidation results back into original validation results.

    Args:
        output_dir: Directory containing revalidation batch files
        revalidation_metadata: Metadata from prepare_batched_revalidation_tasks()

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
        total_groups=revalidated_count
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
