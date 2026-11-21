"""A task's result file: where it may be written, how it is read out of a
reply, and whether it is valid (D3f).

:func:`resolve_output_target` (the containment check on ``output_name``),
:func:`persist_result` (the invoker-persists leg both invokers share),
:func:`extract_result`, :func:`validate_result`, the salvage reads
(:func:`salvage_failure_of`), :func:`normalize_result` and
:func:`task_is_complete`. The size and stream bounds they enforce live
here too.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from . import process_capture
from .json_extractor import (
    extract_json_from_text,
    is_answer_shaped,
)
from .llm_client import (
    SALVAGE_FAILURE_KEY,
    SALVAGE_FAILURE_TIMEOUT,
)
from .providers.base import availability_from_failure
from .retry_ladder import (  # noqa: F401 - re-exported, see below
    STATUS_REJECTED,
    STATUS_RUNNER_ERROR,
    STATUS_SCHEMA_INVALID,
    STATUS_UNPARSEABLE,
)
from .schema_validator import (
    schema_version_supplied,
    supply_schema_version,
    validate_human_decision_verdicts,
    validate_with_schema_file,
    validation_reply_problems,
)
from .subagent_tasks import WRITE_KINDS, content_hash
from . import review_round as _review_round
from .task_decomposer import validate_generated_tasks
from . import failure_capture as _failure_capture
from . import task_outcome as _task_outcome


#: Result size cap (D3f): reject rather than truncate, so a runaway or
#: adversarial runner cannot fill the disk through the executor.
MAX_RESULT_BYTES = 8 * 1024 * 1024

#: Captured-stream cap, per stream (``process_capture`` holds no more than this
#: in memory). A stdout beyond it is refused (rung 5) rather than half-parsed
#: into a plausible-looking result; a stderr beyond it is kept truncated.
MAX_STREAM_BYTES = process_capture.MAX_STREAM_BYTES

#: Per-kind ``output_name`` patterns (D3f), so the reaggregation glob can never be
#: fed a foreign file. ``salvage`` is the one kind whose output IS a model result
#: file (it repairs one), so its pattern is "any plain .json basename" and the
#: reserved-name check below is what bounds it.
OUTPUT_NAME_PATTERN_BY_KIND = {
    "validation": re.compile(r"^validation_batch_\d+\.json$"),
    # Revalidation deliberately reuses the validation batch filenames: it is the
    # same producer (``prepare_batched_revalidation_tasks`` delegates to
    # ``prepare_batched_validation_tasks``) and the same merge reads them back, so
    # the pattern accepts both spellings rather than the kind's own name.
    "revalidation": re.compile(r"^(?:re)?validation_batch_\d+\.json$"),
    "consolidation": re.compile(r"^consolidation_batch_\d+\.json$"),
    # A judge verdict file is keyed by the judged item's stable ``group_id``
    # (``human_decisions.verdict_output_name``), not by a batch index, so that a
    # resumed judging phase — which materializes only the *remaining* items —
    # cannot have one group's task adopt another group's already-written verdict
    # as its own completed output. The token is therefore any basename-safe id;
    # older ``_<n>`` names still match.
    "human_decision_judge": re.compile(
        r"^human_decision_batch_[A-Za-z0-9][A-Za-z0-9._-]*\.json$"
    ),
    "task_generation": re.compile(r"^task_generation_result\.json$"),
    "salvage": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$"),
    # Write kinds (D3g): the batch result JSON. One distinct pattern per kind, so a
    # hand-edited or regenerated task from one phase can never write into another
    # phase's result set even when the phase dirs are siblings.
    "apply_suggestions": re.compile(r"^apply_batch_\d+\.json$"),
    "apply_task_suggestions": re.compile(r"^apply_task_batch_\d+\.json$"),
    "apply_code_fixes": re.compile(r"^apply_fix_batch_\d+\.json$"),
    # An implement result is keyed by the plan task's stable id
    # (``subagent_tasks.implement_output_name``), not by a batch index, for the
    # same reason the judge verdict above is: a resumed implement phase
    # materializes only the *remaining* tasks, so a positional token would let
    # one task adopt a predecessor's already-written result as its own
    # completed output. The token is therefore any basename-safe id; older
    # ``_<n>`` names still match.
    "implement": re.compile(r"^implement_batch_[A-Za-z0-9][A-Za-z0-9._-]*\.json$"),
}

#: Orchestrator-owned artifacts an executor write may never land on (D3f).
RESERVED_OUTPUT_NAMES = frozenset({
    "grouped.json",
    "validation.json",
    "validation_tasks.json",
    "revalidation.json",
    "revalidation_tasks.json",
    "consolidation_tasks.json",
    "consolidated.json",
    "human_decision_tasks.json",
    "report_data.json",
    "state.json",
    ".status.json",
    "orchestrator-run.log",
    _task_outcome.BATCH_REPORT_FILENAME,
    # Write-path artifacts the executor owns (D3g/D3l). A subagent result landing
    # on any of these would overwrite the very evidence the classification, the
    # audit trail and `util restore-batch` depend on.
    "orchestrator_output.json",
    "subagent_audit.jsonl",
    "subagent_dry_run.json",
    "prior_changes.jsonl",
    "write_batch_report.json",
    # The two materialized task files the list above was missing: the write half's
    # (``write_phase_bridge.WRITE_TASK_FILENAME``, spelled out rather than imported
    # only to keep this module's import graph unchanged) and ``generate-tasks``'s
    # single-task envelope. A result landing on either would overwrite the very
    # file the phase is dispatching from, which ``salvage``'s deliberately broad
    # "any plain .json basename" pattern would otherwise permit.
    "write_tasks.json",
    "task_generation_tasks.json",
    # The apply phases' host summary, written beside `orchestrator_output.json`,
    # and the directory of its batch details (an output name is a bare
    # basename, so nothing can land inside it).
    "orchestrator_summary.json",
    "orchestrator_batches",
})

#: Basename prefixes an executor write may never land on (a task file, a salvage
#: request, a rotated log).
RESERVED_OUTPUT_PREFIXES = ("salvage_", "error_", "orchestrator-run.")

#: Basename suffixes an executor write may never land on. Every materialized task
#: file is ``<phase>_tasks.json`` (with its host index ``<phase>_tasks.index.json``
#: beside it), so the suffix — not the enumeration above — is what keeps a later
#: phase's task file safe without a second edit here.
RESERVED_OUTPUT_SUFFIXES = ("_tasks.json", "_tasks.index.json")


# ---------------------------------------------------------------------------
# D3f — containment and the atomic write
# ---------------------------------------------------------------------------

def _is_unsafe_windows_path(name: str) -> bool:
    """Drive-relative (``C:foo``), UNC (``\\\\host\\share``) or an ADS (``a.json:x``)."""
    if name.startswith("\\\\") or name.startswith("//"):
        return True
    if re.match(r"^[A-Za-z]:", name):
        return True
    # An NTFS alternate data stream: a colon anywhere in a *basename*.
    return ":" in name


def resolve_output_target(task: Dict[str, Any], phase_dir: str) -> Path:
    """Resolve and contain a task's ``output_name`` under ``phase_dir`` (D3f).

    ``output_name`` resolved against the dir the task file was actually loaded
    from is authoritative; an absolute ``output_path`` in the JSON is accepted
    only when it resolves to that same file. Task files are persisted in the
    target workspace, survive across runs and (after D2) embed untrusted text, so
    a stale, hand-edited or injected path is an arbitrary-file-overwrite
    primitive.

    Raises:
        ResultRejected: status ``rejected`` (rung 7, no child started), naming the
            task, the offending path and the rule violated.
    """
    task_id = task.get("task_id", "<unnamed>")
    kind = task.get("kind", "")
    name = task.get("output_name")

    def _reject(rule: str, offending: Any) -> "_task_outcome.ResultRejected":
        return _task_outcome.ResultRejected(
            f"Task {task_id}: refusing the output path {offending!r} — {rule}. "
            f"Phase dir: {phase_dir}. Nothing was written and nothing was "
            f"dispatched.",
            STATUS_REJECTED,
        )

    if not isinstance(name, str) or not name:
        raise _reject("output_name must be a non-empty string", name)
    if os.path.basename(name) != name or _is_unsafe_windows_path(name):
        raise _reject(
            "output_name must be a bare basename (no separators, no drive-relative "
            "or UNC prefix, no alternate data stream)",
            name,
        )
    if (
        name in RESERVED_OUTPUT_NAMES
        or any(name.startswith(prefix) for prefix in RESERVED_OUTPUT_PREFIXES)
        or any(name.endswith(suffix) for suffix in RESERVED_OUTPUT_SUFFIXES)
    ):
        raise _reject(
            "it collides with an orchestrator-owned artifact (the task file, "
            "grouped.json, state, the run log or the batch report)",
            name,
        )
    pattern = OUTPUT_NAME_PATTERN_BY_KIND.get(kind)
    if pattern is None:
        raise _reject(f"kind {kind!r} is not one the executor dispatches", name)
    if not pattern.match(name):
        raise _reject(
            f"it does not match the {kind} output pattern {pattern.pattern!r}, so "
            f"the reaggregation glob could be fed a foreign file",
            name,
        )
    # `salvage`'s pattern is necessarily broad — its output IS a model result file
    # — so it must not be allowed to land on another kind's result. Without this a
    # hand-edited or injected salvage task could overwrite validation_batch_0.json
    # with a suggestion array that the merge would then read as validation.
    if kind == "salvage":
        for other_kind, other_pattern in OUTPUT_NAME_PATTERN_BY_KIND.items():
            if other_kind != "salvage" and other_pattern.match(name):
                raise _reject(
                    f"it is the {other_kind} result filename, which a salvage "
                    f"task may never write",
                    name,
                )

    resolved_dir = Path(phase_dir).resolve()
    # Refuse to write *through* a symlink at the final component, before the
    # containment test — otherwise a link pointing outside the phase dir would be
    # reported as an "outside the phase dir" escape and the fix ("stop symlinking
    # the result file") would not be in the message.
    if (resolved_dir / name).is_symlink():
        raise _reject("the target is a symlink", str(resolved_dir / name))
    # Resolve AFTER joining, so a symlinked path component cannot redirect the
    # write, then require containment beneath the resolved phase dir.
    candidate = (resolved_dir / name).resolve()
    try:
        contained = candidate.is_relative_to(resolved_dir)
    except AttributeError:  # pragma: no cover - Python < 3.9
        contained = os.path.commonpath([str(candidate), str(resolved_dir)]) == str(
            resolved_dir
        )
    if not contained or candidate == resolved_dir:
        raise _reject("it resolves outside the phase directory", str(candidate))

    declared = task.get("output_path")
    if isinstance(declared, str) and declared:
        declared_path = Path(declared)
        if not declared_path.is_absolute():
            declared_path = resolved_dir / declared_path
        # Resolve BOTH sides (D1c: asymmetry is the bug). ``make_task`` derives
        # ``output_path`` from the *unresolved* phase-dir string, so whenever that
        # path crosses a symlink — a symlinked repo root, macOS ``/tmp`` →
        # ``/private/tmp``, a CI workspace link — a normpath-only comparison
        # differs from the resolved candidate and every task in the phase is
        # refused before dispatch. D3f accepts an absolute ``output_path`` that
        # RESOLVES to the same file, which is what this compares.
        try:
            declared_resolved = declared_path.resolve()
        except OSError:  # pragma: no cover - unresolvable path is a mismatch
            declared_resolved = Path(os.path.normpath(str(declared_path)))
        if declared_resolved != candidate:
            raise _reject(
                "the task's absolute output_path does not resolve to "
                f"{candidate} (names are authoritative, paths are a "
                "convenience field)",
                declared,
            )

    return resolved_dir / name


def persist_result(task: Dict[str, Any], phase_dir: str, data: Any) -> str:
    """The invoker-persists leg of the D3a contract. Returns the path written.

    **Shared by both invokers.** The executor calls it with the JSON it extracted
    from captured stdout; the equivalence tests' simulated native invoker
    (``tests/harness/native_invoker.py``) calls it with the JSON a driving
    agent's subagent returned. Same containment, same serialization, same
    bytes — which is what makes the result-contract equivalence assertion possible
    rather than aspirational.

    Deliberately does **not** branch on ``result_channel``: ``file`` is the only
    behavior the executor has, so a task carrying ``inline-json`` is refused
    before dispatch instead of selecting a second write path here.
    """
    return persist_result_bytes(task, phase_dir, data)[0]


def persist_result_bytes(
    task: Dict[str, Any], phase_dir: str, data: Any,
) -> Tuple[str, Optional[bytes]]:
    """:func:`persist_result`, with the bytes it wrote: ``None`` when it wrote
    none (a late result of a replaced round)."""
    target = resolve_output_target(task, phase_dir)
    encoded = json.dumps(data, indent=2)
    if len(encoded.encode("utf-8")) > MAX_RESULT_BYTES:
        raise _task_outcome.ResultRejected(
            f"Task {task.get('task_id')}: the extracted result is "
            f"{len(encoded.encode('utf-8'))} bytes, over the {MAX_RESULT_BYTES}-byte "
            f"cap. Rejected rather than truncated — a truncated result file would "
            f"still parse and would reaggregate as a real one.",
            STATUS_SCHEMA_INVALID,
        )
    # Written only while the round that dispatched it is still the round on
    # record; a late result of a replaced round is dropped (utils/review_round.py).
    # Through the module, at each call: tests patch `review_round.persisting_result`.
    persisted: Optional[bytes] = None
    with _review_round.persisting_result(phase_dir, target.name) as current:
        if current:
            # By the phase folder as the run spelled it, not as it resolves
            # now: the write holds that folder from the plan's directory, so a
            # link swapped in for it since the check above is refused
            # (docs/development/write-safety.md#plan-output-containment).
            written = _failure_capture._atomic_write_json(
                os.path.join(os.path.abspath(phase_dir), target.name), data)
            # The bytes written, for the round that dispatched them to read
            # instead of the file (docs/development/review-results.md,
            # "Consuming checked bytes").
            if isinstance(written, bytes):
                persisted = written
                _review_round.record_checked_result(phase_dir, target.name, written, dispatched=True)
    return str(target), persisted


# ---------------------------------------------------------------------------
# Extraction and per-kind result validation
# ---------------------------------------------------------------------------

#: The kinds whose result is one JSON object (their schema's root is an
#: object): the write report, the task list, a consolidation batch and the
#: judge's verdicts. Validation's reply may be a bare array, a salvage's is
#: one.
OBJECT_RESULT_KINDS = frozenset({
    "task_generation", "consolidation", "human_decision_judge", *WRITE_KINDS,
})


def the_reply_object(kind: str, data: Any, extracted: Mapping[str, Any]) -> Any:
    """*data*, or the reply's one JSON object when *kind*'s result is an
    object and the extraction served an array (fix round 28, live run 12 #6).

    Codex decline batch 0 opened its reply with two prose lines, then the
    report object; the adapter's array-preferring extraction served the
    report's own ``declined`` array (an array holding an object ranks as an
    answer), the batch read "<root>: expected type object, got list", and a
    repair re-ask restated the same report. The extractor names the reply's
    one object outside every other document (``only_object``,
    :func:`utils.json_extractor._only_object`); a reply holding two such
    objects names none and keeps its re-ask, as a validation reply holding
    two does. Both invokers read a reply through this."""
    if kind in OBJECT_RESULT_KINDS and isinstance(data, list):
        whole = extracted.get("only_object") if isinstance(extracted, Mapping) else None
        if isinstance(whole, dict):
            return whole
    return data


def extract_result(provider: Any, stdout: str, stderr: str, *, prefer_arrays: bool) -> Any:
    """Recover the subagent's answer: ``parse_output`` first, then extraction.

    :func:`_extract_result_and_syntax` without the syntax diagnosis.
    """
    return _extract_result_and_syntax(
        provider, stdout, stderr, prefer_arrays=prefer_arrays
    )[0]


def _extract_result_and_syntax(
    provider: Any, stdout: str, stderr: str, *, prefer_arrays: bool,
    kind: str = "", capped: bool = False,
) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """Recover the subagent's answer: ``parse_output`` first, then extraction.

    Returns ``(data, enclosing_syntax_error)``: the second is the extractor's
    own report (``json_extractor.extract_json_from_text``) that ``data`` is a
    piece of a larger document which does not parse, else ``None``. It comes
    from whichever extraction served ``data`` — the adapter's, handed back on
    its ``parse_output`` dict, or this function's own for an adapter that
    returns text — so nothing scans the reply a second time to rediscover it.

    The ordering is **mandatory, not an optimization** (D3): provider CLIs emit
    structured event streams, so running ``json_extractor`` over raw stdout would
    match an event envelope or a reasoning item instead of the answer, and
    silently write a garbage result that reaggregation would accept.

    Adapters already run ``extract_json_from_text`` on the text they recover, so
    a dict/list ``data`` is the extracted result; a *string* ``data`` (adapters
    that return raw text) goes through ``utils/json_extractor`` here.

    ``capped`` says the capture already cut stdout at its bound; it is
    refused like any stream over :data:`MAX_STREAM_BYTES`.

    Raises:
        ResultRejected: rung 4 (``runner_error``) when the adapter recovered no
            response text at all, rung 5 (``unparseable_result``) when it recovered
            text but no result object, or the stream is over the bound.
    """
    if capped or len(stdout.encode("utf-8", errors="replace")) > MAX_STREAM_BYTES:
        raise _task_outcome.ResultRejected(
            process_capture.oversized_stream_message("stdout", MAX_STREAM_BYTES),
            STATUS_UNPARSEABLE,
        )

    parsed = provider.parse_output(stdout, stderr)
    if not isinstance(parsed, dict):  # pragma: no cover - adapter contract
        raise _task_outcome.ResultRejected(
            "the adapter's parse_output did not return a result dict",
            STATUS_RUNNER_ERROR,
        )

    if not parsed.get("success"):
        raw = parsed.get("raw")
        error = parsed.get("error") or "parse_output reported failure"
        if isinstance(raw, str) and raw.strip():
            # Text WAS recovered; it just carries no result object (prose, a
            # refusal, a truncated stream) → rung 5.
            raise _task_outcome.ResultRejected(str(error), STATUS_UNPARSEABLE)
        reason = None
        try:
            reason = provider.describe_failure(stdout, stderr)
        except Exception:  # noqa: BLE001 - diagnostics must not raise
            reason = None
        if reason:
            error = f"{error}: {reason}"
        # M10 (§5.1) — the **status**-consumer half of this site, on the same
        # rule as `llm_client`'s twin and through the same shared helper, so a
        # login notice reads the same on both lanes. Diagnostics only: the rung
        # is still `STATUS_RUNNER_ERROR`, decided above and not by this line.
        unavailable = availability_from_failure(provider, stdout, stderr)
        if unavailable is not None:
            error = f"{error} [{unavailable.value}]"
        raise _task_outcome.ResultRejected(str(error), STATUS_RUNNER_ERROR)

    data = parsed.get("data")
    syntax = parsed.get("enclosing_syntax_error")
    served: Mapping[str, Any] = parsed
    if isinstance(data, str):
        extracted = extract_json_from_text(data, prefer_arrays=prefer_arrays)
        if not extracted.get("success"):
            raise _task_outcome.ResultRejected(
                extracted.get("error") or "no JSON found in the recovered text",
                STATUS_UNPARSEABLE,
            )
        data = extracted.get("data")
        syntax = extracted.get("enclosing_syntax_error")
        served = extracted
    whole = the_reply_object(kind, data, served)
    if whole is not data:
        # The object parsed whole: the array's syntax note was about it.
        data, syntax = whole, None
    if data is None or (isinstance(data, dict) and set(data.keys()) == {"raw"}):
        raise _task_outcome.ResultRejected(
            "the adapter recovered no result object from the stream",
            STATUS_UNPARSEABLE,
        )
    if not isinstance(data, (dict, list)):
        raise _task_outcome.ResultRejected(
            f"the recovered result is a {type(data).__name__}, not a JSON object "
            f"or array",
            STATUS_UNPARSEABLE,
        )
    return data, syntax if isinstance(syntax, dict) else None


def _validation_result_errors(data: Any) -> List[str]:
    """Structural check for a ``validation_batch_N.json`` / revalidation result.

    There is no shipped JSON Schema for these (the merge deliberately tolerates
    several index shapes and joins by ``group_hash``), so this pins only what
    the merge cannot recover from, through the check ``util check-reply``
    shares (``schema_validator.validation_reply_problems``). A status outside
    the verdicts is left to the merge, which reads it as ``validation_failed``:
    rung 6 is terminal for this kind.
    """
    return validation_reply_problems(data, recoverable=False)


def _salvage_result_errors(data: Any) -> List[str]:
    """A salvaged model result is the same array shape a model review produces.

    Which is also why the *other* thing a salvage can print — the
    ``{"salvage_failed": true, "reason": ...}`` sentinel — has to fail here. The
    sentinel is not a document any consumer can read; it is this dispatch saying
    it found none. It is recognised **before** validation, by
    :func:`_salvage_gave_up`, and turned into a failed outcome that writes
    nothing. Should one ever reach the disk anyway, keeping it invalid is what
    stops :func:`task_is_complete` from reading the file back and calling the
    task done.

    An empty array stays valid. From here it is indistinguishable from a model
    whose review really was empty, and that ambiguity is precisely why the
    negative was given a shape of its own rather than being refused here.

    The non-array clause below also happens to catch a relayed
    ``{"error": …}`` body or an ``opencode``/``codex`` ``{"type": "error", …}``
    event a salvage subagent "recovered" out of a truncated stream, but that is
    not this function's job and must not be relied on as it: by the time such a
    reply gets here :func:`_salvage_gave_up` has already turned it down with a
    reason that names what actually happened, where "expected a JSON array"
    would have sent the reader back to the repair pass instead of to the
    provider's login. This clause is the floor under that rule, not the rule.
    """
    if not isinstance(data, list):
        return [f"expected a JSON array of suggestions, got {type(data).__name__}"]
    errors = []
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            errors.append(f"[{index}]: expected an object")
    return errors


#: The key ``build_salvage_prompt`` tells a salvage subagent to set when the raw
#: output it was handed holds nothing recoverable. A recovered salvage result is
#: an *array*, so no genuine recovery can carry it.
SALVAGE_FAILED_KEY = "salvage_failed"

#: The reason :func:`_salvage_gave_up` gives for an empty array recovered from a
#: run a deadline ended. The request records ``"failure": "timeout"``
#: (``review_orchestrator_base.salvage_failure_kind``); this is its read side.
SALVAGE_EMPTY_AFTER_TIMEOUT_REASON = (
    "salvage recovered an empty array from a run that timed out: a reviewer "
    "killed at its deadline never reported an empty review, so `[]` is not "
    "written as this model's result"
)


def salvage_failure_of(task: Dict[str, Any], phase_dir: str) -> Optional[str]:
    """How the run behind a salvage task was lost, read from its request file.

    A salvage task's ``output_name`` is ``<stem>.json`` and its request is
    ``salvage_<stem>.json`` beside it — the pairing every writer uses and every
    retire glob relies on. The request is the record that says whether a
    deadline ended the run (``"failure": "timeout"``); the task itself carries no
    such field, and its ``inputs.salvage_request_sha256`` already binds it to
    that request's bytes. ``None`` for any other kind.

    The request is read once, and its text must still hash to the
    ``inputs.salvage_request_sha256`` the task records, the digest the
    dispatch checked it against, before anything in it is believed. A bound
    request that is gone, unreadable, no longer that digest's text, or not a
    JSON object is not the one the task was bound to, so its failure kind is
    unknown and read as ``"timeout"``, which refuses a salvaged ``[]`` and
    nothing else. Only a task that binds no request keeps the old reading,
    ``None`` when the request cannot be read, so its salvaged ``[]`` persists
    (docs/development/review-results.md, "Consuming checked bytes").
    """
    if str(task.get("kind", "")) != "salvage":
        return None
    output_name = str(task.get("output_name") or "")
    if not output_name:
        return None
    inputs = task.get("inputs")
    bound = inputs.get("salvage_request_sha256") if isinstance(inputs, dict) else None
    bound = bound if isinstance(bound, str) and bound else None
    unknown = SALVAGE_FAILURE_TIMEOUT if bound else None
    path = os.path.join(phase_dir, f"salvage_{output_name}")
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, ValueError):
        return unknown
    if bound and content_hash(text) != bound:
        return SALVAGE_FAILURE_TIMEOUT
    try:
        request = json.loads(text)
    except ValueError:
        return unknown
    if not isinstance(request, dict):
        return unknown
    failure = request.get(SALVAGE_FAILURE_KEY)
    return failure if isinstance(failure, str) and failure else None


def _salvage_gave_up(kind: str, data: Any, failure: Optional[str] = None) -> Optional[str]:
    """Why this salvage recovered nothing, or ``None`` if it recovered a result.

    A salvage task's ``output_name`` **is** the model result file it repairs, so
    whatever a salvage dispatch persists *becomes* that model's review. The
    subagent therefore cannot report the negative as an empty array: it would
    validate, be written over the model's own result path, and reaggregation
    would read it as "this model reviewed the input and found nothing". A model
    that never produced a parseable word would join the aggregate as a phantom
    participant — and since finding priority is scored partly by how many models
    flagged something, its silence would count as agreement.

    A salvage arrives here having recovered nothing two ways, read in this order:

    1. **It said so.** ``build_salvage_prompt`` asks for
       ``{"salvage_failed": true, "reason": …}`` and this is the one place that
       shape is read. The reason travels into the outcome because it is the
       diagnostic the empty array threw away — "the raw output was an
       authentication error" is what a reader of ``subagent_batch_report.json``
       needs, and it costs one string to keep. It is checked **first** for
       exactly that: the subagent read the raw output and named what was in it,
       which is a better diagnostic than anything clause 2 can reconstruct from
       the reply alone.
    2. **It did not say so, and what came back is not an answer.** A subagent
       handed a truncated stream that turns out to hold a relayed
       ``{"error": {"code": 401, "message": "User not found"}}`` body, or the
       ``{"type": "error", "message": …}`` envelope an ``opencode``/``codex``
       run prints as an event, can "recover" that object perfectly faithfully
       and never print the sentinel — it believes it found something. Today
       :func:`_salvage_result_errors` stops that object at the door anyway, on
       the narrow ground that it is not an array. What it cannot do is say what
       happened: "does not match the salvage result shape" reads as a botched
       repair pass and invites another one, when what the model actually hit was
       an authentication failure and the fix is the provider's login — the exact
       mis-direction ``has_salvageable_json`` exists to prevent one step
       earlier. So the rule is stated *here*, where the phantom-participant
       argument lives, instead of being left to rest on an array check written
       for the consumer's benefit: were the salvage result shape ever to grow a
       wrapper-object form (the way :func:`_validation_result_errors` tolerates
       ``{"groups": [ … ]}``), an error envelope would sail through that check
       and onto the model's result path with nothing left to stop it. The
       predicate is ``json_extractor.is_answer_shaped``, the one behind
       ``has_salvageable_json``, imported rather than restated: the gate asks
       "is there an answer in this raw output to ask a repair pass for?", this
       asks "is what the repair pass came back with an answer?", and one rule
       spelled once at both ends cannot drift apart from itself.

    Both invokers call this immediately before the point where they would
    validate and persist, and both answer a non-``None`` result the same way:
    ``STATUS_SALVAGE_UNRECOVERABLE``, nothing written, never retried.

    Deliberately **not** folded into :func:`validate_result`: that answers "is
    this a document this kind's consumer can read", and the sentinel must keep
    failing that question for the reason :func:`_salvage_result_errors` gives.

    Scoped to ``kind == "salvage"``; every other kind is judged by its own result
    shape alone. A bare ``[]`` from a salvage still persists — clause 2 lets it
    through because ``is_answer_shaped([])`` is True on purpose: refusing it
    cannot tell "salvage found nothing" from "the model's review was genuinely
    empty", and the sentinel is what carries that distinction. Nor does clause 2
    swallow a *near-miss*: an object naming a field the answer schemas require is
    answer-shaped, so a subagent that returned a single record where an array was
    asked for still falls through to :func:`validate_result` and is reported as
    "does not match the salvage result shape" — the accurate diagnostic for a
    recovery that found an answer and mis-packaged it. Only replies with no
    answer anywhere in them are "recovered nothing".

    The truth test on the sentinel is deliberately loose: a subagent that spelled
    the flag ``"true"`` is still read as the negative, and every reading that
    errs errs towards writing nothing — and clause 2 is the backstop in any case,
    since the sentinel object names no answer field either.

    **The one ``[]`` that is refused** (decision 11.10, timeouts only): when the
    salvage request records ``"failure": "timeout"`` (``failure`` here, read by
    :func:`salvage_failure_of`), an empty array is
    :data:`SALVAGE_EMPTY_AFTER_TIMEOUT_REASON`. A run killed at its deadline
    never said "I found nothing" — a subagent handed only its ``toolcall_delta``
    fragments can return ``[]``, and that would read as a clean review. A ``[]``
    from a run that finished and then exited non-zero still persists: there
    the model did write it.

    Args:
        kind: The task's kind. Anything but ``salvage`` returns ``None``.
        data: The extracted result, before validation.
        failure: The salvage request's ``"failure"`` value, or ``None``.

    Returns:
        The reason for the outcome row, or ``None``.
    """
    if kind != "salvage":
        return None
    if isinstance(data, dict) and data.get(SALVAGE_FAILED_KEY):
        reason = data.get("reason")
        reason = reason.strip() if isinstance(reason, str) else ""
        return (
            f"salvage recovered no result from the raw output: "
            f"{reason or 'the subagent gave no reason'}"
        )
    if failure == SALVAGE_FAILURE_TIMEOUT and isinstance(data, list) and not data:
        return SALVAGE_EMPTY_AFTER_TIMEOUT_REASON
    if is_answer_shaped(data):
        return None
    # Name the shape, never the payload: the keys are what diagnoses this (an
    # `error` or a `type`/`message` pair says "the stream relayed a provider
    # failure" at a glance), while the values are the raw output this dispatch
    # was handed and have no business in a batch report. Bounded, because
    # nothing here promises the object is small.
    if isinstance(data, dict):
        names = sorted(str(key) for key in data)
        listed = ", ".join(names[:5]) + (", …" if len(names) > 5 else "")
        shape = (
            f"an object naming no answer field and holding no array "
            f"({listed or 'no keys at all'}). A relayed provider error or event "
            f"envelope reads as a recovery to the subagent that faithfully "
            f"pulled it out of the stream; it is not this model's review"
        )
    else:
        shape = (
            f"a bare {type(data).__name__} where an array of suggestions was "
            f"the answer; there is nothing in it to write as this model's review"
        )
    return f"salvage recovered no result from the raw output: it returned {shape}"


#: The list-valued keys of a generated task a runner may leave out when the
#: list is empty. ``generated_tasks.schema.json`` requires all three, and a
#: small model reads "no files to create" as "no ``files_to_create`` key" —
#: measured 2026-09-14: ``opencode/nemotron-3-ultra-free`` returned ten
#: well-formed tasks for a single-file plan, every one carrying
#: ``files_to_modify`` and none carrying ``files_to_create``, and the whole
#: reply failed rung 6 (never retried) on that one absent key, twice. An absent
#: list and an empty list mean the same thing to every consumer
#: (``task_decomposer.from_dict`` reads each with a ``[]`` default), so the
#: invoker supplies the key. A key that is *present* with the wrong type is
#: left alone for the schema to name.
TASK_GENERATION_LIST_KEYS: Tuple[str, ...] = (
    "depends_on", "files_to_create", "files_to_modify",
)


def normalize_result(kind: str, data: Any) -> List[str]:
    """Supply what a reply left out that means the same thing absent as empty.

    Mutates ``data`` in place and returns one note per key it supplied, shaped
    ``'files_to_create' on 10 task(s)``; ``[]`` means the reply was already in
    shape. Runs *before* :func:`validate_result` on both parse lanes and on the
    native host's consume path, so the document written to disk is the
    normalized one and :func:`task_is_complete` re-reads what was validated.

    Only ``task_generation`` has such keys. Every other kind returns ``[]``
    with ``data`` untouched: a validation verdict or a write-batch result
    missing a field is a real disagreement, not a spelling of "none".
    """
    if kind != "task_generation":
        return []
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return []
    supplied: Dict[str, int] = {}
    for task in data["tasks"]:
        if not isinstance(task, dict):
            continue
        for key in TASK_GENERATION_LIST_KEYS:
            if key not in task:
                task[key] = []
                supplied[key] = supplied.get(key, 0) + 1
        # Required-but-nullable in the schema (OpenAI's strict subset needs every
        # property required) and absent from the prompt's reply shape, so most
        # replies omit it; "no value" is what null says. Counted like the list
        # keys, not supplied silently: the notes are what makes the native leg
        # write the completed document back before validating, and a silent
        # key left a pre-upgrade `task_generation_result.json` schema-invalid
        # on disk — `task_is_complete` False for a file the phase had consumed
        # (adversarial review, 2026-10-02).
        if "subagent_type" not in task:
            task["subagent_type"] = None
            supplied["subagent_type"] = supplied.get("subagent_type", 0) + 1
    return [f"{key!r} on {count} task(s)" for key, count in supplied.items()]


def _report_normalized(
    kind: str, notes: List[str], version: Optional[str] = None,
) -> None:
    """One stdout line per reply the executor had to complete, or nothing;
    one more when it read an absent ``schema_version`` as *version*."""
    if version:
        print(
            f"[exec-subagents] {kind}: "
            + schema_version_supplied("the reply", version)
            + ", before validating."
        )
    if notes:
        print(
            f"[exec-subagents] {kind}: the reply omitted {', '.join(notes)}; "
            f"supplied the empty value ([] for a list, null for subagent_type) "
            f"before validating (absent and empty mean the same thing to every "
            f"consumer of this document)."
        )


#: The read kinds whose result names a ``schema_version`` its schema pins to
#: one value (fix round 28, live run 12: a host's copy of a task-generation
#: reply left the key out and the first ``--reaggregate`` failed on it). A
#: result without the key is read as that version, on every lane that reads
#: one: the executor's parse, :func:`task_is_complete`, generate-tasks'
#: consume and the judge verdicts' ingest.
VERSIONED_RESULT_SCHEMAS = {
    "task_generation": "generated_tasks.schema.json",
    "human_decision_judge": "human_decision_verdicts.schema.json",
}


def supply_result_version(kind: str, data: Any) -> Optional[str]:
    """Supply a *kind* result's absent ``schema_version`` in place
    (``schema_validator.supply_schema_version``); the version, or ``None``."""
    schema = VERSIONED_RESULT_SCHEMAS.get(kind)
    if schema is None:
        return None
    return supply_schema_version(data, schema)


def validate_result(kind: str, data: Any) -> List[str]:
    """Validate an extracted result against its kind's result shape (D3f).

    Runs *before* anything is written, so a runner that returned prose or the
    wrong object fails the task instead of writing garbage that reaggregation
    accepts. Shipped JSON Schemas are used where they exist; the two kinds with
    no schema get the structural check their consumer actually depends on.

    One kind can also reply with something that is not a document at all:
    ``salvage``'s ``salvage_failed`` sentinel, and the relayed error envelope a
    salvage subagent can "recover" in perfectly good faith. Neither is decided
    here — :func:`_salvage_gave_up` intercepts both a step earlier — and the
    sentinel stays invalid against this function on purpose.
    """
    if kind in ("validation", "revalidation"):
        return _validation_result_errors(data)
    if kind == "consolidation":
        return validate_with_schema_file(data, "consolidation_batch.schema.json")
    if kind == "human_decision_judge":
        return validate_human_decision_verdicts(data)
    if kind == "task_generation":
        # The schema pins the shape; `task_decomposer.validate_generated_tasks`
        # owns the graph rules every later phase depends on (unique T### ids,
        # `depends_on` naming declared ids, acyclic, a dependency-free task).
        # Both are this kind's result shape (fix round 6): a document that only
        # the consumer refused used to be persisted `ok`, get no schema-repair
        # re-ask, and count as done to `task_is_complete` on the next run.
        errors = validate_with_schema_file(data, "generated_tasks.schema.json")
        if errors:
            return errors
        return validate_generated_tasks(data.get("tasks") or [])
    if kind == "salvage":
        return _salvage_result_errors(data)
    if kind in WRITE_KINDS:
        # D3g's "the batch still returns JSON on stdout" made concrete: the same
        # schema gate a validation result gets, so a runner that narrated its work
        # in prose fails the task instead of being counted as applied.
        return validate_with_schema_file(data, "write_batch_result.schema.json")
    return [f"unknown kind {kind!r}"]


def task_is_complete(task: Dict[str, Any], phase_dir: str) -> bool:
    """Whether a task counts as already done, deterministically (D3i).

    Done **iff** its ``output_name`` exists under the phase dir, parses, and
    validates against its kind's result schema. Anything else is re-dispatched
    under its original ``task_id``. Orphans are defined by artifacts, never by
    memory: there is no in-memory queue to recover and no "running" state to
    trust.

    A salvage that recovered nothing writes no file at all, so it is not complete
    here — and a ``salvage_failed`` sentinel that reached the disk by some other
    route is not complete either, because it fails :func:`validate_result` the
    way any other non-document would.
    """
    return complete_result_bytes(task, phase_dir) is not None


def complete_result_bytes(task: Dict[str, Any], phase_dir: str) -> Optional[bytes]:
    """The bytes :func:`task_is_complete` judged complete, or ``None``."""
    try:
        target = resolve_output_target(task, phase_dir)
    except _task_outcome.ResultRejected:
        return None
    if not target.exists() or target.stat().st_size == 0:
        return None
    try:
        raw = target.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    # Read as every lane reads it: an absent schema_version is the one
    # version there is (fix round 28), in memory only.
    supply_result_version(str(task.get("kind", "")), data)
    if validate_result(str(task.get("kind", "")), data):
        return None
    if _result_names_foreign_groups(task, data):
        return None
    # The bytes judged complete, for a review round that dispatched this task
    # to read instead of the file (docs/development/review-results.md,
    # "Consuming checked bytes").
    _review_round.record_checked_result(phase_dir, target.name, raw, dispatched=False)
    return raw


def _result_names_foreign_groups(task: Dict[str, Any], data: Any) -> bool:
    """Whether a batch result echoes a group hash this task was not assigned.

    A task file that lists ``group_ids`` (a validation or revalidation batch)
    says which groups its result may speak about. A file left by an earlier round
    answers a different grouping, so it must not count as done: measured
    2026-10-02 on a Codex ``review-code --force``, a ``validation_batch_0.json``
    from the previous day (judged against an empty repo, hashes of the old
    groups) parsed and schema-validated, was skipped as "already complete", and
    the merge then discarded every row as a foreign ``group_hash`` -- all three
    groups ended ``validation_failed`` and the new code was never validated.
    The same test the merge applies (``merge_batch_validations`` routes by
    ``group_hash``), moved in front of the re-dispatch decision. A result row
    with no hash is not foreign (the merge falls back to its index for those).
    """
    assigned = task.get("group_ids")
    if not isinstance(assigned, list) or not assigned or not isinstance(data, dict):
        return False
    groups = data.get("groups")
    if not isinstance(groups, list):
        return False
    allowed = {str(item) for item in assigned}
    for row in groups:
        if not isinstance(row, dict):
            continue
        echoed = row.get("group_hash") or row.get("group_id")
        if echoed and str(echoed) not in allowed:
            return True
    return False
