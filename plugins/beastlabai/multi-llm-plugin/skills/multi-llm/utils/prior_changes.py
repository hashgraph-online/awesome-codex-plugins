#!/usr/bin/env python3
"""CLI utility for managing prior batch changes in a JSONL file.

Commands: read, append, clear.
Storage: {output-dir}/prior_changes.jsonl
"""

import argparse
import hashlib
import json
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Collection, Iterable, List, Optional, Sequence, Tuple

try:
    from .stream_bootstrap import bootstrap_streams
    from .text_clip import plain_line
except ImportError:
    # Direct script invocation (`python utils/prior_changes.py`): sys.path[0]
    # is the utils/ directory, so import the sibling module directly.
    from stream_bootstrap import bootstrap_streams
    from text_clip import plain_line

FILENAME = "prior_changes.jsonl"
DEFAULT_TAIL = 15
MAX_CHARS = 2000
DEFAULT_TEXT = "(none — this is the first batch)"

#: The phase's materialized write task file, ``utils.write_phase_bridge``'s
#: ``WRITE_TASK_FILENAME`` (spelled here: the bridge imports this module).
#: :func:`append` reads it to name the batch an entry came from.
WRITE_TASK_FILENAME = "write_tasks.json"

#: Distinct spellings that name the *same* phase for this file's purposes
#: (F6, 2026-09-16). ``apply-code-fixes`` is the write executor's own phase
#: word (``PHASE_BY_WRITE_KIND`` — the mode/``state.json`` spelling);
#: ``apply-fixes`` is the on-disk phase-directory word,
#: ``instructions/apply-code-fixes.md`` step 5.7's documented `--phase` for
#: this CLI on the native leg. That is a deliberate divergence *elsewhere*
#: (`state.json.phases_completed` keys on the mode word — see the same
#: instruction file's step 10) but not here: `append` dedupes and `render`
#: prefers entries on the bare `(id, phase)` / `phase` value, so a run that
#: starts on one leg and resumes on the other must not see two phases where
#: there is one. Canonicalised to the phase-directory word, since that is the
#: spelling steps 5.1/5.7 already put in front of a human. Add a row here,
#: never a special case in `append`/`render`, if a future phase grows the
#: same split.
PHASE_ALIASES = {
    "apply-code-fixes": "apply-fixes",
}


def canonical_phase(phase: Optional[str]) -> Optional[str]:
    """Normalize *phase* through :data:`PHASE_ALIASES`; passes through unknowns."""
    if phase is None:
        return None
    return PHASE_ALIASES.get(phase, phase)

#: Hex digits kept from the member-id digest in :func:`entry_id`. Eight is the
#: same width the state manager's group ids are truncated to for display, and it
#: is far wider than the handful of batches one phase ever produces.
ENTRY_ID_DIGEST_CHARS = 8

#: What :func:`entry_id` uses as the base when a batch carries no content key of
#: its own, so the two invokers (the Python bridge and a native agent reading the
#: serialized batch) still spell the same id.
ENTRY_ID_KEYLESS_BASE = "batch"


def stable_key(candidates: Sequence[Any], fallback: str) -> str:
    """The first non-empty candidate, else *fallback*. Never a loop index.

    The content-key primitive :func:`entry_id` is built on, and the one the write
    bridge and the batchers both spell their member ids with — it lives here so
    the id semantics have exactly one owner.
    """
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            return text
    return fallback


def _short_digest(member_ids: Sequence[str]) -> str:
    """A stable short digest of an ordered member-id list."""
    payload = "\n".join(member_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:ENTRY_ID_DIGEST_CHARS]


def entry_id(key: str, member_ids: Sequence[str], *, fallback: str) -> str:
    """The ``--id`` for one batch: ``{key}#{digest of member_ids}``.

    The id handed to :func:`append` has to be **both** unique per batch and
    stable across a re-dispatch, and getting either half wrong fails silently:

    * a **colliding** id silently DROPS an entry. Every reader sees one entry
      per ``(id, phase)`` (the newest, :func:`latest_entries`), so the second
      batch that presents an id an earlier batch already used replaces that
      batch's entry (until fix round 14 it was skipped with a `Notice:`
      instead) — and every later batch then reads a prior-changes context
      missing a predecessor,
      which is the whole signal the step exists to provide. This is not
      hypothetical: the batchers emit **many** batches per file key and per
      section key (``MAX_FIXES_PER_BATCH``, the char caps, and the one-per-batch
      isolation of security/HIGH fixes), so keying on the bare file/section key
      records only the first batch of each.
    * an **unstable** id silently DOUBLES one — that is the failure ``append``'s
      idempotency exists to prevent, and it is why the digest is taken over a
      stable *content* key (the batch's own member ids) rather than over a loop
      index, which moves the moment a resumed run re-materializes a different
      subset of batches.

    Args:
        key: The batch's content key (``file_key``/``section_key``). May be empty.
        member_ids: The batch's member ids, in order — the same list the write
            task carries as ``expected_ids``, so both invokers digest the same
            bytes and derive the same id for the same batch.
        fallback: Used only when *member_ids* is empty, i.e. when there is no
            content to digest at all. The batchers never emit an empty batch, so
            this is a degenerate-input guard rather than a live path.

    Returns:
        ``"{key}#{digest}"``, or ``"batch#{digest}"`` for a batch with no key,
        or *fallback*/*key* when there are no member ids to digest.
    """
    ids = [text for text in (str(m or "").strip() for m in member_ids) if text]
    base = str(key or "").strip()
    if not ids:
        return base or fallback
    return f"{base or ENTRY_ID_KEYLESS_BASE}#{_short_digest(ids)}"


def _jsonl_path(output_dir: str) -> Path:
    return Path(output_dir) / FILENAME


def _load_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            warnings.warn(f"Skipping corrupted JSONL line: {line!r}", stacklevel=2)
            continue
    return entries


def latest_entries(raw: Sequence[dict]) -> list[dict]:
    """One entry per ``(id, phase)``: the last one recorded, at its position.

    ``append`` keeps the log append-only and records a batch again when its
    summary changed (a check that reported problems and later passed, a task
    refused before dispatch that later ran), so a task can hold several lines.
    Every reader wants what the task did *last*: fix round 14 (stop fixture,
    Claude Code fix 02) — T002's re-run passed, but ``append`` skipped its new
    line as "already exists", so T007's prompt still said T002's check failed
    and its subagent refused to write the release note. The view keeps the
    newest line of each ``(id, phase)`` in the order those newest lines were
    written, so a re-recorded task moves to where it last ran. An entry with
    no id is never folded into another.
    """
    last: dict = {}
    for index, entry in enumerate(raw):
        eid = entry.get("id")
        key = (
            (str(eid), canonical_phase(entry.get("phase")))
            if eid not in (None, "") else ("", index)
        )
        last[key] = index
    keep = sorted(last.values())
    return [raw[index] for index in keep]


def _latest_for(raw: Sequence[dict], entry_id: str, phase: Optional[str]) -> Optional[dict]:
    """The newest entry recorded for ``(entry_id, phase)``, or ``None``."""
    for entry in reversed(raw):
        if entry.get("id") == entry_id and canonical_phase(entry.get("phase")) == phase:
            return entry
    return None


def parse_stamp(value: Any) -> Optional[datetime]:
    """An entry's ``timestamp`` (or a ``state.json`` stamp) as a naive local
    datetime, or ``None`` when it does not parse."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def run_entries(
    output_dir: str, phase: Optional[str], since: Optional[str] = None,
) -> list[dict]:
    """The newest entry per id of *phase* alone (:func:`latest_entries`),
    recorded after *since* (an ISO stamp; ``None`` keeps them all, and so
    does an entry whose own stamp does not parse), in log order: one run's
    own batches, never another phase's (fix round 22)."""
    scoped = canonical_phase(phase)
    boundary = parse_stamp(since)
    out = []
    for entry in latest_entries(_load_entries(_jsonl_path(output_dir))):
        if canonical_phase(entry.get("phase")) != scoped:
            continue
        stamp = parse_stamp(entry.get("timestamp"))
        if boundary is not None and stamp is not None and stamp <= boundary:
            continue
        out.append(entry)
    return out


#: A batch id a prompt line may show (``T003``, ``apply-fix-batch-0``): the
#: log and the phase's task file sit where a batch can write, so a recorded
#: ``task_id`` of any other shape (a newline forging a prompt line, markup) is
#: never shown, and the entry is named by its own id.
_PLAIN_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._#:-]{0,79}\Z")

#: A phase folder name :func:`append` may read a task file from.
_PHASE_DIR_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


def plain_task_id(value: Any) -> str:
    """*value* as a batch id a line may show, or ``""``."""
    text = str(value or "").strip()
    return text if _PLAIN_TASK_ID.match(text) else ""


#: An entry id a line may show: the same guard as a batch id's, widened to
#: what the batchers' ids are made of (:func:`entry_id`'s
#: ``<file or section key>#<digest>``: ``.github/workflows/test.yml#f7ee6a5d``,
#: ``file:src/api.ts#…``) and to the ``<file> (batch 28)`` an older native
#: host chose. Every id in the live runs' logs passes it; the batch id's own
#: class would have shown ``?`` for 391 of their 1613. Never a newline, a
#: control character or markup (``*``, a backtick, a bracket).
_PLAIN_ENTRY_ID = re.compile(r"[A-Za-z0-9._][A-Za-z0-9._#:/@+=,() -]{0,199}\Z")


def plain_entry_id(value: Any) -> str:
    """*value* as an entry id a line may show, else ``"?"`` (review of fix
    round 24: the log is batch-writable, and the id a line falls back to
    was printed raw, so a planted one forged a prompt line)."""
    text = str(value or "").strip()
    return text if _PLAIN_ENTRY_ID.match(text) else "?"


#: What may follow a leading id for :func:`summary_without_ids` to read it as
#: a label: a colon or a dash, spaced or not (a hyphen only after a space,
#: so ``T002-fix`` stays whole).
_LABEL_SEPARATOR = r"\s*(?::|—|–|\s-)\s*"


def summary_without_ids(summary: str, ids: Iterable[Any]) -> str:
    """*summary* without a leading copy of one of *ids* used as its label.

    Live run 10 (OpenCode racing 08): a subagent opened its summary with its
    own task id, and the line that names the entry read
    ``- (T002): T002: 8-point closed CatmullRom track…``. A line names its id
    once: ``T002: …``, ``T002 — …``, ``(T002) …`` and ``[T002]: …`` lose
    the id; one that only mentions it (``T002 and T003 share…``,
    ``Fixed T002: …``) is kept word for word, and so is a summary that would
    be left empty.
    """
    text = str(summary or "")
    for ident in ids:
        ident = str(ident or "").strip()
        if not ident:
            continue
        name = re.escape(ident)
        match = re.match(
            rf"\s*(?:\(\s*{name}\s*\)|\[\s*{name}\s*\])(?:{_LABEL_SEPARATOR}|\s+)"
            rf"|\s*{name}{_LABEL_SEPARATOR}",
            text,
        )
        if match and text[match.end():].strip():
            return text[match.end():]
    return text


def entry_task_id(entry: dict) -> str:
    """The id of the batch that wrote *entry* — what summary.md, ``status``
    and ``--human-task <id>=…`` call it — else the entry's own id."""
    return plain_task_id(entry.get("task_id")) or plain_entry_id(entry.get("id"))


def entry_summary(entry: dict, ids: Iterable[Any]) -> str:
    """*entry*'s summary as one plain line (:func:`plain_line`), without a
    leading copy of one of *ids* (:func:`summary_without_ids`): the log is
    batch-writable, and a newline in a summary forged a prompt line (review of
    fix round 24)."""
    return summary_without_ids(plain_line(entry.get("summary", "")), ids)


def entry_line(entry: dict) -> str:
    """One earlier batch, as every list of them shows it (fix round 24, live
    run 10 #6): named by its batch id, with the entry id beside it when the
    two differ (an apply batch's ``index.html#a4d7fa43``), never by a list
    position — "Batch 1" read as the second of ``apply-fix-batch-0/1/2`` —
    and never an id twice. One plain line (fix round 25): an id that is not
    a plain one shows as ``?`` and the summary is :func:`entry_summary`."""
    eid = plain_entry_id(entry.get("id"))
    task_id = entry_task_id(entry)
    label = f"**{task_id}**" if task_id == eid else f"**{task_id}** ({eid})"
    return f"- {label}: {entry_summary(entry, [task_id, eid])}"


def record_line(entry: dict) -> str:
    """``- (<id>): <summary>``: an implement entry as apply-code-fixes'
    ``## Implementation record`` quotes it (``code_fix_batcher``), and the
    shape :func:`quoted_in` looks for. One plain line, as :func:`entry_line`."""
    eid = plain_entry_id(entry.get("id"))
    return f"- ({eid}): {entry_summary(entry, [eid])}"


def render(
    output_dir: str,
    phase: Optional[str] = None,
    *,
    tail: int = DEFAULT_TAIL,
    max_chars: int = MAX_CHARS,
    quoted: Collection[Tuple[str, Optional[str]]] = (),
    own_run_only: bool = False,
    since: Optional[str] = None,
) -> str:
    """The prior-batch context block, exactly as `read` prints it.

    Extracted from :func:`cmd_read` so the D3n write-batch scheduler can bind
    ``{prior_changes_context}`` **in process**, per dispatch, without shelling out
    to this script — and, more importantly, so both invokers substitute
    byte-identical text. The log is always **replayed from disk** rather than
    reconstructed from an in-memory list, which is what makes a resumed batch see
    the same context an uninterrupted run would have.

    *phase*, when given, prefers this phase's own entries when trimming to the
    entry cap / ``MAX_CHARS`` (N8): a log accumulates entries from every write
    phase that has ever run against this plan — measured on a real run, 36
    entries were 15 apply-suggestions, 11 apply-task-suggestions and 10
    implement, and an unfiltered tail spent two of implement's eleven visible
    slots on `apply-task-suggestions`' edits, numbered ``**Batch 25**``/``**Batch
    26**`` beside the rest of the log's plain ``T001``…``T006`` implement ids.
    With no entries recorded yet for *phase* (its first dispatch), there is
    nothing to prefer, so this falls back to the unfiltered behaviour rather
    than rendering an empty phase-scoped log while real prior context sits
    unread.

    *tail* and *max_chars* default to the write-batch budget this was extracted
    for — 15 entries, 2 000 chars — and exist as arguments because a *reader*
    of the log has a different one. The code-review prompts summarize a whole
    implement phase, and at the write-batch budget the oldest entries fall off
    the top: the very entry that motivated showing reviewers this log at all
    (``accel tuned 28->32``, recorded against the phase's third task) was the
    third of thirteen and so was trimmed away.

    *quoted* names entries, as ``(id, phase)``, that the prompt this block
    goes into already quotes word for word (:func:`quoted_in`): they are left
    out and counted on one closing line instead of shown twice. The decline
    fixture, 2026-10-07: an apply-code-fixes batch's first prompt showed the
    implement phase's three entries under ``## Implementation record`` and
    again, as "Batch 1-3", under ``## Changes Applied in Prior Batches``.

    *own_run_only* (fix round 22, live run 9 #7) lists *phase*'s own entries
    recorded after *since* (:func:`run_entries`) and nothing else: no other
    phase's entries, no count of them, and no fall-back to the whole log on a
    first batch. An apply-code-fixes batch's context is the earlier batches
    of its own run (implement's record has its own section, and the
    plan-edit batches of the planning phases are not code changes); Codex
    racing 08's first fix batch listed nine of them.

    Each entry is one :func:`entry_line` (fix round 24): named by the id of
    the batch that wrote it, never numbered.
    """
    if own_run_only:
        entries = run_entries(output_dir, phase, since)
    else:
        entries = latest_entries(_load_entries(_jsonl_path(output_dir)))
    if max_chars <= 0:
        return ""
    quoted_keys = {(str(eid), canonical_phase(ph)) for eid, ph in quoted}
    quoted_count = 0
    if quoted_keys:
        kept = [
            e for e in entries
            if (str(e.get("id")), canonical_phase(e.get("phase"))) not in quoted_keys
        ]
        quoted_count = len(entries) - len(kept)
        entries = kept
    quoted_line = (
        f"... and {quoted_count} earlier "
        f"{'entry' if quoted_count == 1 else 'entries'} already quoted in "
        f"this prompt"
        if quoted_count else ""
    )
    if not entries:
        return (quoted_line or DEFAULT_TEXT)[:max_chars]

    phase = canonical_phase(phase)
    same_phase = (
        [e for e in entries if canonical_phase(e.get("phase")) == phase]
        if phase else []
    )
    if same_phase:
        working = same_phase
        other_count = len(entries) - len(same_phase)
    else:
        working = entries
        other_count = 0

    total = len(working)
    tail = min(tail, total)
    output = ""
    while tail > 0:
        skipped = total - tail
        visible = working[total - tail:]

        lines: list[str] = []
        if skipped > 0:
            lines.append(f"... and {skipped} earlier batches applied miscellaneous changes")

        lines.extend(entry_line(entry) for entry in visible)

        if other_count > 0:
            lines.append(f"... and {other_count} earlier batches from other phases")
        if quoted_line:
            lines.append(quoted_line)
        output = "\n".join(lines)
        if len(output) <= max_chars:
            break
        if tail == 1:
            # A single summary can exceed the entire budget. Dropping the
            # final entry used to exit the loop with that oversized text.
            marker = "... [truncated]"
            output = output[:max(0, max_chars - len(marker))] + marker[:max_chars]
            break
        tail -= 1

    return output


def quoted_in(text: str, output_dir: str) -> List[Tuple[str, Optional[str]]]:
    """The entries of *output_dir*'s log that *text* already quotes, as
    ``(id, phase)``: each line ``- (<id>): <summary>`` found in it word for
    word — the shape apply-code-fixes' ``## Implementation record`` quotes
    the implement phase's entries in (``code_fix_batcher``). What
    :func:`render`'s *quoted* takes, so a prompt never shows one entry twice.
    """
    out: List[Tuple[str, Optional[str]]] = []
    for entry in latest_entries(_load_entries(_jsonl_path(output_dir))):
        eid, summary = entry.get("id"), entry.get("summary")
        if eid and summary and (
            record_line(entry) in text or f"- ({eid}): {summary}" in text
        ):
            out.append((str(eid), entry.get("phase")))
    return out


def _task_id_in_task_file(output_dir: str, entry_id: str, phase: Optional[str]) -> str:
    """The ``task_id`` of the batch whose ``prior_changes_id`` is *entry_id*
    in the phase's ``write_tasks.json`` (``<output_dir>/<phase dir>/``), or
    ``""``. Best-effort: a missing or unreadable file names nothing."""
    if not phase or not _PHASE_DIR_WORD.match(phase):
        return ""
    try:
        document = json.loads(
            (Path(output_dir) / phase / WRITE_TASK_FILENAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    if not isinstance(document, dict):
        return ""
    for task in document.get("batches") or document.get("tasks") or []:
        if isinstance(task, dict) and str(task.get("prior_changes_id") or "") == entry_id:
            return plain_task_id(task.get("task_id"))
    return ""


def append(
    output_dir: str, entry_id: str, phase: str, summary: str,
    *, task_id: Optional[str] = None,
) -> bool:
    """Record one entry for ``(id, phase)``. True when a line was written.

    *task_id* is the batch the entry comes from (``apply-fix-batch-0``,
    ``T003``): what every list of earlier batches names it by
    (:func:`entry_line`, fix round 24). The executor passes its own; with
    none given (the native ``append`` command) it is read off the phase's
    ``write_tasks.json``, the file the host dispatched the batch from. It is
    recorded only when it differs from *entry_id* (an implement task's entry
    id is its task id), and only as a plain id (:func:`plain_task_id`).

    The in-process half of ``append``, for the same reason :func:`render` exists.
    Idempotent on ``(id, phase)`` **and summary**: a re-dispatched batch that
    reports what its entry already says writes nothing, so it never doubles
    its own summary into the context every later batch reads — which is why
    the write task carries a stable ``prior_changes_id`` rather than a loop
    index. A batch recorded again with a *different* summary supersedes its
    earlier entry (fix round 14): the line is appended, and every reader
    (:func:`entries`, :func:`render`) sees only the newest line per
    ``(id, phase)`` (:func:`latest_entries`). Until then the first summary
    won for good — a check whose findings were fixed and that passed on
    ``--resume`` kept telling the tasks after it that it failed. The other
    half of the contract is :func:`entry_id`, which is what makes the id
    unique per batch: two batches sharing an id would supersede each other.
    """
    phase = canonical_phase(phase)
    path = _jsonl_path(output_dir)
    latest = _latest_for(_load_entries(path), entry_id, phase)
    if latest is not None and latest.get("summary") == summary:
        return False
    named = plain_task_id(task_id) or _task_id_in_task_file(output_dir, entry_id, phase)
    record = {"id": entry_id}
    if named and named != entry_id:
        record["task_id"] = named
    record.update({
        "phase": phase,
        "summary": summary,
        # Local naive clock, matching `state_manager.py`'s `updated_at` — a
        # UTC stamp here (F13, audited 2026-09-16) read two hours off from
        # `state.json` and `subagent_audit.jsonl` for the same instant, both
        # of which use `datetime.now()`.
        "timestamp": datetime.now().isoformat(),
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    # Append-only, one write per line: concurrent appends (a native host
    # recording same-batch tasks in parallel) never lose each other's line,
    # which a read-modify-write of the file could.
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return True


def entries(output_dir: str) -> list[dict]:
    """The recorded entries, newest per ``(id, phase)``, in order
    (:func:`latest_entries`): what each batch did last."""
    return latest_entries(_load_entries(_jsonl_path(output_dir)))


def history(output_dir: str) -> list[dict]:
    """Every line the log holds, superseded ones included, in file order."""
    return _load_entries(_jsonl_path(output_dir))


def cmd_read(args: argparse.Namespace) -> None:
    # The block a batch's prompt binds, unscoped (fix round 24: one
    # formatter, so this command and the prompts never name a batch two ways).
    print(render(args.output_dir))


#: ``util prior-changes append``'s exit code when it writes nothing because
#: its ``--id`` is empty: the dispatcher's "needs a human" code, which an
#: unknown mode or a stray positional gets too.
EXIT_REFUSED = 3


def _batch_ids_in_task_file(output_dir: str, phase: Optional[str]) -> List[Tuple[str, str]]:
    """``(task_id, prior_changes_id)`` of every batch in the phase's
    ``write_tasks.json`` (``<output_dir>/<phase dir>/``), both plain ids;
    ``[]`` when the file is missing or unreadable."""
    if not phase or not _PHASE_DIR_WORD.match(phase):
        return []
    try:
        document = json.loads(
            (Path(output_dir) / phase / WRITE_TASK_FILENAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    tasks = (document.get("batches") or document.get("tasks") or []) if isinstance(
        document, dict) else []
    out: List[Tuple[str, str]] = []
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        task_id = plain_task_id(task.get("task_id"))
        eid = plain_entry_id(task.get("prior_changes_id"))
        if task_id and eid != "?":
            out.append((task_id, eid))
    return out


#: How many batches the empty-id refusal lists before "and N more".
_IDS_SHOWN = 12


def empty_id_refusal(output_dir: str, phase: Optional[str]) -> str:
    """Why ``util prior-changes append`` wrote nothing for an empty ``--id``,
    and where the id comes from (fix round 28, live run 12 #9: a Claude Code
    host built the id with ``$(python3 …)``, got nothing, and the append wrote
    a row with ``"id": ""``)."""
    task_file = Path(output_dir) / str(phase or "<phase>") / WRITE_TASK_FILENAME
    listed = _batch_ids_in_task_file(output_dir, phase)
    shown = "; ".join(
        task_id if task_id == eid else f"{task_id}: {eid}"
        for task_id, eid in listed[:_IDS_SHOWN]
    ) + (f"; and {len(listed) - _IDS_SHOWN} more" if len(listed) > _IDS_SHOWN else "")
    return (
        f"ERROR: util prior-changes append: --id is empty, so nothing was "
        f"written to {_jsonl_path(output_dir)}. The id is the batch's "
        f"prior_changes_id in {task_file} (for implement, the task id, such "
        f"as T003): copy it from there as it is written and run the append "
        f"again with the same summary."
        + (f" The batches there: {shown}." if shown else "")
    )


def cmd_append(args: argparse.Namespace) -> int:
    # Canonicalize whatever spelling was passed — apply-code-fixes's native
    # leg and its --exec-subagents executor otherwise write this same file
    # under two different `phase` values for the same phase (F6).
    phase = canonical_phase(args.phase)
    if not str(args.id or "").strip():
        print(empty_id_refusal(args.output_dir, phase), file=sys.stderr)
        return EXIT_REFUSED
    summary = args.summary if args.summary is not None else sys.stdin.read().strip()
    earlier = _latest_for(_load_entries(_jsonl_path(args.output_dir)), args.id, phase)
    if not append(args.output_dir, args.id, phase, summary):
        print(
            f"Notice: entry {args.id}/{phase} already says this, skipping",
            file=sys.stderr,
        )
        return 0
    if earlier is not None:
        print(
            f"Replaced entry {args.id}/{phase}: later tasks now read this "
            f"summary instead of the earlier one",
            file=sys.stderr,
        )
        return 0
    print(f"Appended entry {args.id}/{phase}", file=sys.stderr)
    return 0


def cmd_clear(args: argparse.Namespace) -> None:
    path = _jsonl_path(args.output_dir)
    if path.exists():
        path.unlink()


def main(argv=None) -> int:
    bootstrap_streams()
    parser = argparse.ArgumentParser(description="Manage prior batch changes")
    sub = parser.add_subparsers(dest="command", required=True)

    read_p = sub.add_parser("read")
    read_p.add_argument("--output-dir", required=True)

    append_p = sub.add_parser("append")
    append_p.add_argument("--output-dir", required=True)
    append_p.add_argument("--id", required=True)
    append_p.add_argument("--phase", required=True)
    summary_grp = append_p.add_mutually_exclusive_group(required=True)
    summary_grp.add_argument("--summary", default=None)
    summary_grp.add_argument("--summary-stdin", action="store_true")

    clear_p = sub.add_parser("clear")
    clear_p.add_argument("--output-dir", required=True)

    args = parser.parse_args(argv)
    code = {"read": cmd_read, "append": cmd_append, "clear": cmd_clear}[args.command](args)
    return code if isinstance(code, int) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
