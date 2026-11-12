"""What a dispatched write prompt carries beyond the stored one.

:func:`bind_prior_changes` binds ``{prior_changes_context}`` late, per
dispatch, and :func:`with_result_contract` appends the write-batch result
contract. The scheduler and ``util write-prompt`` both call them, so a
batch is sent the same prompt on either leg. Also where a dispatched
prompt is kept (``DISPATCHED_PROMPTS_SUBDIR``) and which write kinds are
code (``CODE_WRITE_KINDS``).

``utils.write_batch_scheduler`` re-exports every name defined here for
reading only: patch one here, never through the scheduler
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from . import check_records as _check_records
from . import known_checks as _known_checks
from . import prompt_files as _prompt_files
from . import prior_changes as _prior_changes
from .retry_ladder import STATUS_REJECTED
from .task_outcome import ResultRejected
from .subagent_tasks import PRIOR_CHANGES_TOKEN, APPLY_WRITE_KINDS, snapshot_file_set
from . import scope_apply


#: Write kinds whose deliverable is **source code**, so the repository's own
#: `driver.verify_command` has something to say about them (F4). The other two
#: write kinds edit the plan and the tasks file — markdown a typecheck cannot
#: read — so they skip verification silently rather than logging a notice about a
#: command that was never going to apply to them.
CODE_WRITE_KINDS = frozenset({"apply_code_fixes", "implement"})


#: The phases whose batch prompts list, under ``## Changes Applied in Prior
#: Batches``, only the earlier batches of their own run (fix round 22, live
#: run 9 #7): apply-code-fixes, whose implement record has its own section
#: and to which the planning phases' plan-edit batches are noise.
OWN_RUN_CONTEXT_PHASES = frozenset({"apply-fixes"})


def last_phase_end(
    state: Any, phase: Optional[str], review_stamp: str = "",
) -> Optional[str]:
    """When *phase* last ended, as ``state.json`` records it: the newer of its
    completion stamp and its skip stamp (under either spelling of the phase,
    :data:`prior_changes.PHASE_ALIASES`), or ``None``. Every prior-changes
    entry of the phase recorded before it belongs to an earlier run.

    Fix round 23 (records #4): a completion does not end the run while the
    phase's ``processed_<phase>`` holds a ``failed`` record of the review
    being applied (*review_stamp*, the batch's ``inputs.grouped_sha256``; a
    record or a batch with no stamp counts as that review). Nothing refuses
    the native ``--mark-completed`` over a failed batch (the runbook forbids
    it), and the ``--resume`` that dispatches that batch again continues the
    same run: its earlier batches stay in the prompt, with no new stop. That
    run is then bounded by the skip stamp and the newest record of another
    review — the run before it, whose batches are not this one's.
    """
    if state is None or not hasattr(state, "get") or not phase:
        return None
    canonical = _prior_changes.canonical_phase(phase)
    names = {phase, canonical} | {
        word for word, alias in _prior_changes.PHASE_ALIASES.items() if alias == canonical
    }
    try:
        completed = dict(state.get("phases_completed") or {})
        skipped = dict(state.get("phases_skipped") or {})
        processed = [
            record for name in sorted(names)
            for record in dict(state.get(f"processed_{name}") or {}).values()
            if isinstance(record, dict)
        ]
    except Exception:  # noqa: BLE001 - a read for a prompt's context
        return None

    def _dated(stamps: Iterable[Any]) -> List[Tuple[Any, str]]:
        return [
            (when, stamp) for stamp in stamps
            if (when := _prior_changes.parse_stamp(stamp)) is not None
        ]

    def _review(record: Dict[str, Any]) -> str:
        details = record.get("details") if isinstance(record.get("details"), dict) else {}
        return str(details.get("grouped_sha256") or "")

    review_stamp = str(review_stamp or "")
    completions = _dated(completed.get(name) for name in names)
    skips = _dated(
        (skipped.get(name) or {}).get("skipped_at")
        for name in names if isinstance(skipped.get(name), dict)
    )
    unfinished = any(
        record.get("status") == "failed"
        and (not review_stamp or not _review(record) or _review(record) == review_stamp)
        for record in processed
    )
    if completions and unfinished:
        earlier = _dated(
            record.get("timestamp") for record in processed
            if review_stamp and _review(record) and _review(record) != review_stamp
        )
        dated = skips + earlier
    else:
        dated = completions + skips
    return max(dated)[1] if dated else None


def _state_on_disk(output_dir: str) -> Optional[Dict[str, Any]]:
    try:
        state = json.loads((Path(output_dir) / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def bind_prior_changes(
    task: Dict[str, Any], *, output_dir: str, phase: Optional[str],
    accepted_checks: Sequence[Tuple[str, str, List[str]]] = (),
    state: Any = None,
) -> str:
    """The prompt that actually goes to the runner, bound *now*.

    ``{prior_changes_context}`` is substituted from the log **on disk**, so a
    resumed batch sees the same context an uninterrupted run would have. The
    task JSON is never rewritten: this produces the dispatched prompt only, and
    the audit record stores its hash and length rather than its bytes.

    A prompt that never contained the token is a contract error, not a
    convenience: every batcher embeds it (``utils/suggestion_batcher.py:359``,
    ``utils/code_fix_batcher.py:307``, ``apply_task_suggestions_orchestrator.py:543``,
    ``prompts/implementation_task.txt``), so its absence means the producer
    changed and every later batch would run without prior-batch context while
    looking fine. ``implement`` used to be the one kind exempted — its prompt
    carried no token and this fell through as a no-op — on the theory that its
    inter-task context is the dependency section
    ``implement_orchestrator._build_dependency_section`` renders instead. That
    section names only the *titles* of preceding tasks (F6, 2026-09-16): a
    verified one-line summary of what each batch actually did already exists in
    ``prior_changes.jsonl``, so implement prompts now carry the token too and
    get the same binding, refusal included, as every other kind.

    The render is scoped to *phase* (N8, 2026-09-16): the log is one file
    shared by every write phase this plan has ever run, and an unscoped tail
    let another phase's older batches crowd out this phase's own recent ones.

    Module-level (2026-10-05) because it has two callers that must produce
    byte-identical text for the same prior-changes log (both legs append a
    summary per finished batch and a failure line per failed one since fix
    round 15; a native host words a failure's reason itself): the scheduler's
    :meth:`WriteBatchScheduler.dispatched_prompt` on the executor leg, and
    ``util write-prompt`` (:mod:`utils.write_prompt`) on the native leg, where
    the host used to substitute the token by hand — and, measured on the
    2026-10-04 Claude Code racing re-run, sometimes did not.

    *accepted_checks* (fix round 14, :func:`accepted_upstream_checks`): the
    checks upstream of an implement task whose findings the user accepted.
    Their note (:func:`accepted_checks_section`) follows the prior-changes
    context, where the check's own ``(check findings — …)`` entry is, so a
    task released by ``--human-task <check>=done`` reads that the problems
    were accepted, not only that they were found.

    A phase in :data:`OWN_RUN_CONTEXT_PHASES` (fix round 22) is shown only the
    earlier batches of its own run: its entries recorded after the phase
    last ended (:func:`last_phase_end`, read from *state* — the executor's,
    else the plan dir's ``state.json``, which ``util write-prompt`` reads),
    never another phase's.
    """
    prompt = str(task.get("prompt") or "")
    if PRIOR_CHANGES_TOKEN not in prompt:
        raise ResultRejected(
            f"Task {task.get('task_id')}: its prompt does not contain the "
            f"{PRIOR_CHANGES_TOKEN} token, so there is nowhere to bind the "
            f"prior-batch context. Every apply/implement prompt must carry it "
            f"(utils/suggestion_batcher.py, utils/code_fix_batcher.py, "
            f"apply_task_suggestions_orchestrator.py, "
            f"prompts/implementation_task.txt). Nothing was dispatched.",
            STATUS_REJECTED,
        )
    # An entry the prompt already quotes word for word (apply-code-fixes'
    # `## Implementation record`) is counted, not shown a second time.
    own_run = _prior_changes.canonical_phase(phase) in OWN_RUN_CONTEXT_PHASES
    context = _prior_changes.render(
        output_dir, phase=phase, quoted=_prior_changes.quoted_in(prompt, output_dir),
        own_run_only=own_run,
        since=last_phase_end(
            state if hasattr(state, "get") else _state_on_disk(output_dir), phase,
            _known_checks.review_stamp(task),
        ) if own_run else None,
    )
    note = _check_records.accepted_checks_section(accepted_checks)
    if note:
        context = f"{context.rstrip()}\n\n{note.rstrip()}"
    return prompt.replace(PRIOR_CHANGES_TOKEN, context)


#: Where a write batch's dispatched prompt is kept, under the phase dir: the
#: layout the native leg's ``util write-prompt`` writes (``write_prompt``
#: imports it), which the executor leg keeps too since fix round 16.
DISPATCHED_PROMPTS_SUBDIR = _prompt_files.FOLDER


def dispatched_prompt_name(task_id: str, attempt: Optional[int] = None) -> str:
    """``{task_id}.prompt.txt``, or ``{task_id}.attempt-{attempt}.prompt.txt``
    (see :func:`dispatched_prompt_path`)."""
    return (
        f"{task_id}.prompt.txt" if attempt is None
        else f"{task_id}.attempt-{attempt}.prompt.txt"
    )


def dispatched_prompt_path(
    phase_dir: str, task_id: str, attempt: Optional[int] = None
) -> str:
    """``{phase_dir}/prompts/{task_id}.prompt.txt``, the batch's prompt.

    With ``attempt``, ``{task_id}.attempt-{attempt}.prompt.txt``: what one
    attempt sent when it was not the batch's prompt (a report re-ask, rule 9's
    re-send). The path to name; the files are written through
    :mod:`utils.prompt_files`, never by this path.
    """
    return os.path.join(
        os.path.abspath(str(phase_dir)), DISPATCHED_PROMPTS_SUBDIR,
        dispatched_prompt_name(task_id, attempt),
    )


def _scope_apply():
    """:mod:`utils.scope_apply`."""
    return scope_apply


def with_result_contract(
    kind: str, task: Dict[str, Any], prompt: str, *, checks_section: str = "",
) -> str:
    """Wrap the batch prompt in the write-batch result contract the
    classification reads.

    Order (PERF-9, docs/development/write-scheduler.md "Prompt order"): the
    blocks that are the same for every batch of a run's phase come first —
    process safety, git, scratch files, the result shape and the check
    contracts — so a provider can reuse them as a cached prefix; the batch
    prompt and its scope block follow, and the ``ids``/``declined`` lines
    naming this batch's ``expected_ids`` close the prompt, so it still ends
    with what the reply must contain.

    The batchers' prompts end in the prose "Return Format" the native
    markdown flow compresses into a one-line summary; the scheduler — on
    both invokers — validates the reply against
    ``write_batch_result.schema.json`` instead, and reads ``ids`` against
    the task's ``expected_ids``. A runner that was never shown that shape
    answers in prose and fails rung 5 with its edits on disk. Measured
    2026-09-15 on ``apply-task-suggestions``: three attempts applied the
    batch to ``tasks.md`` and reported it as asked, every one was recorded
    ``unparseable_result`` / ``schema-rejection``, and a fourth run's
    runner, reading the already-applied file, replied "already addressed"
    in prose and failed the same way.

    The ids are spelled out in the order the items appear in the prompt,
    because the prompt itself never names them; a reply that omits an id
    for an item it found already applied would otherwise read as a partial
    application and stop the loop.

    Module-level for the same reason as :func:`bind_prior_changes`: the
    native leg's ``util write-prompt`` binds the same contract, so a host
    subagent's closing JSON object carries the ``summary`` the prior-changes
    append wants and the ``status``/``files_touched`` the host's verification
    step reads.

    *checks_section* (fix round 20, :func:`known_checks.known_checks_section`):
    an apply-code-fixes batch's list of the repository's known check
    commands, bound at dispatch on both legs, after the code batch's
    ``## Checks you ran``, whose ``check`` object it extends with ``listed``.
    It stays in the leading blocks: its command list is the run's, and only
    an earlier batch's failing check makes it differ between batches.

    A task materialized under ``--scope-policy preserve`` carries a ``scope``
    block, and its writer guidance (``scope_apply.writer_block``) follows the
    batch prompt on both legs; a task without one (``expand``) gets nothing,
    so its text is what it always was (plans/scope-policy-and-report-tags.md §5).
    """
    expected = [str(i) for i in (task.get("expected_ids") or [])]
    scope_block = _scope_apply().writer_block(task)
    if scope_block:
        prompt = f"{prompt.rstrip()}\n\n{scope_block.rstrip()}"
    declining = kind in APPLY_WRITE_KINDS
    if kind == "implement":
        id_lines = (
            f"- `ids`: this task's id, `{expected[0]}`, when you applied it "
            f"or found it already implemented; leave it out on `failed`."
            if expected else
            "- `ids`: the task ids you applied."
        )
    else:
        item = "fix" if kind == "apply_code_fixes" else "suggestion"
        plural = "fixes" if item == "fix" else f"{item}s"
        listed = ", ".join(
            f"{item} {index} = `{member}`"
            for index, member in enumerate(expected, 1)
        )
        # Fix round 18 (Codex racing run 7, apply-code-fixes 08): a batch
        # left a fix out on purpose, said so in `notes`, could not say so in
        # the contract, and stopped as a partial application on every resume.
        # Fix round 26 (live run 11, Codex decline fixture): a fix the plan
        # forbids outright ("Do not add a clamp …") was declined as "requires
        # a plan decision". The reason now names and quotes the decision
        # that already decides it, and says "needs a plan decision" only
        # when nothing does.
        sources = (
            "the plan, its task list or the implementation record"
            if item == "fix" else "the plan or its task list"
        )
        id_lines = (
            f"- `ids`: the ids of the {plural} you applied **or found already "
            f"applied by a prior batch**, from this list (numbered in the "
            f"order they appear above): {listed}.\n"
            f"- `declined`: each {item} from that list you deliberately left "
            f"unapplied, as `{{\"id\": \"<its id>\", \"reason\": "
            f"\"<why, in one sentence>\"}}`; `[]` when you applied every one. "
            f"The reason says what decides it: when {sources} already decides "
            f"against the {item} (a rule it states, a decision it records), "
            f"name which one and quote that decision; when you judge the "
            f"{item} wrong for this code, say why; say it needs a plan "
            f"decision only when nothing there decides it. "
            f"Every {item} goes in exactly one of `ids` and `declined`: one "
            f"left out of both reads as a {item} you meant to apply and did "
            f"not finish, and the run stops for a human to inspect it."
        )
    # Fix round 26 (live run 11): a batch that edits code carries `check` in
    # the shape itself. Asked for in a section of its own below the shape,
    # "required when you ran any", it was left out by replies that ran
    # `npm test` (Claude Code racing T005, OpenCode stop T001).
    own_checks = kind in CODE_WRITE_KINDS and not is_check_task(kind, task)
    shape = (
        '{"status": "applied", "ids": ["<id>", "..."], '
        + (
            '"declined": [{"id": "<id>", "reason": "<why you did not apply '
            'it>"}], ' if declining else ""
        )
        + '"files_touched": ["<repo-relative path>"], '
        '"summary": "<one line, at most 200 characters>", '
        '"notes": "<the per-item summary requested below>"'
        + (
            ', "check": {"passed": true, "findings": [], "ran": '
            '{"<each check command you ran>": "passed"}}' if own_checks else ""
        )
        + '}\n'
    )
    status_line = (
        "- `status`: `applied` if you edited any file; `no-op` if you edited "
        "nothing because every change was already present or you declined "
        "it; `failed` if you could not apply the batch.\n"
        if declining else
        "- `status`: `applied` if you edited any file; `no-op` if every "
        "change was already present and you edited nothing; `failed` if "
        "you could not apply the batch.\n"
    )
    contract = (
        "## Process safety (required)\n\n"
        "Never run `kill`, `pkill`, `killall` or any process-wide signal: "
        "the orchestrator that dispatched you is a sibling process, and a "
        "write subagent's `killall -9 python3` ended a whole phase "
        "(measured 2026-09-16). Do not start background servers, watchers, "
        "browsers or any other background process, and leave no process "
        "running when you finish.\n\n"
        # Fix round 28 (live run 12, OpenCode racing T012): a task that made
        # a vendored file trackable then ran `git add` on it; the implement
        # template forbade commit and push only, the apply batches nothing.
        "## Git (required)\n\n"
        "Do not stage, commit, stash or push anything (no `git add`, `git "
        "commit`, `git stash` or `git push`), even when your task makes a file "
        "trackable: leave the git index and history as you found them. The "
        "user reviews and stages the changes.\n\n"
        "## Scratch files (advisory)\n\n"
        "Keep scratch work (an extracted script to syntax-check, a probe) "
        "out of the repository and out of fixed, shared names such as a "
        "bare `check.mjs` in the system temp directory: create a fresh "
        "directory with `mktemp -d`, work only there and delete it before "
        "you finish. The write gate only sees the repository, so a file "
        "left elsewhere is invisible to it (measured 2026-10-01, OpenCode "
        "runner).\n\n"
        "## Result (required — this is how the batch is verified)\n\n"
        "Do the work below, then end your reply with ONE JSON object (a "
        "fenced ```json block is fine) of exactly this shape:\n\n"
        "```json\n"
        f"{shape}"
        "```\n\n"
        f"{status_line}"
        "- `files_touched`: repo-root-relative paths you edited (empty for "
        "`no-op` and `failed`).\n"
        "- `summary`: one line; it is recorded verbatim as this batch's "
        "entry in the prior-changes log the next batch reads.\n"
        "- `notes`: the per-item summary the return format below asks for.\n"
        + (
            "- `check`: required in every reply, also when you ran no check — "
            "which checks you ran on your edits and how each one ended "
            "(see below).\n"
            if own_checks else ""
        )
        + "\n"
        "A reply without this JSON object is recorded as a FAILED batch even "
        "when the edits landed, so send it in every case — including when "
        "nothing needed changing.\n"
        + (CHECK_RESULT_CONTRACT if is_check_task(kind, task) else "")
        + (WRITE_CHECK_CONTRACT + (checks_section or "") if own_checks else "")
        + (IMPLEMENT_WHICH_CHECKS if own_checks and kind == "implement" else "")
    )
    return (
        f"{contract.rstrip()}\n\n{BATCH_PROMPT_RULE}\n\n{prompt.rstrip()}\n\n"
        f"{RESULT_IDS_HEADING}\n\n{id_lines}\n"
    )


#: Between the leading contract blocks and the batch prompt
#: (:func:`with_result_contract`): a thematic break, so the batch prompt's
#: first line does not read as part of the contract's last section.
BATCH_PROMPT_RULE = "---"

#: The heading of the closing ``ids``/``declined`` lines
#: (:func:`with_result_contract`): they name this batch's ``expected_ids``,
#: so they follow the batch prompt rather than lead the fixed contract.
RESULT_IDS_HEADING = "## Result ids (required in the JSON object above)"


#: Appended to the result contract of a batch that edits code (implement's
#: tasks that declare files, apply-code-fixes' batches): the checks it ran on
#: its edits, in the shape a check task reports (fix round 14). Codex racing
#: run 5 (2026-10-06): an apply-code-fixes batch said in its free-text
#: `notes` that the bundled test failed, the repository's test failed
#: afterwards, and the run reported "All 6 valid fixes were applied". Read by
#: `batch_reply.batch_check_findings`, never from `notes`. Fix round 17:
#: the corrected run that replaces a failing one is pinned to the same check
#: over the same scope, as :data:`CHECK_RESULT_CONTRACT` pins it to the task's
#: own command; a narrower re-run passing never launders the failure.
#: Fix round 26 (live run 11): required in every reply, with ``ran`` naming
#: each command and how it ended, or an empty ``ran`` and a ``not_run``
#: reason. "Required when you ran any" and "leave `check` out when you ran no
#: check" let replies that had run ``npm test`` omit it (Claude Code racing
#: T005, OpenCode stop T001); an empty ``ran`` is read as no check, never as
#: a pass (``batch_reply.batch_check_findings``; ``util batch-done
#: --own-check none`` on the native leg).
WRITE_CHECK_CONTRACT = (
    "\n## Checks you ran (required in every reply)\n\n"
    "Always send the `check` object in the JSON above, also when you ran no "
    "check: it is the only record of what was checked after your edits, and "
    "a reply without it leaves the checks you ran off the record.\n\n"
    "- `ran`: every check you ran on your edits — a test, a build, a type "
    "check, a linter, a syntax check — as its command mapped to how its last "
    "run ended, `\"passed\"` or `\"failed\"`.\n"
    "- `passed`: the JSON boolean `true` only when the last run of every "
    "check you ran passed, else `false`.\n"
    "- `findings`: one string per check whose last run failed: the command "
    "and what it reported, nothing else; `[]` when `passed` is `true`.\n"
    "- `note` (optional): anything you want to say about your checks, such "
    "as why one fails or that a failure is a known one. It is recorded and "
    "shown beside them and never read as a finding, so keep such words out "
    "of `findings`.\n\n"
    "A batch whose check failed answers:\n\n"
    "```json\n"
    '{"check": {"passed": false, "findings": ["<one failing check: the '
    'command and what it reported>"], "ran": {"<that command>": "failed", '
    '"<another command you ran>": "passed"}}}\n'
    "```\n\n"
    "If you ran no check, say so and why: `ran` empty, no `passed`, and the "
    "reason in `not_run`:\n\n"
    "```json\n"
    '{"check": {"ran": {}, "not_run": "<why no check could run on these '
    'edits>"}}\n'
    "```\n\n"
    "Report the last run of each check. A run that failed because of how you "
    "ran it (a wrong flag, mode or path) and that you then ran correctly is "
    "reported by the corrected run, and so is a check you ran again after "
    "fixing what it found: an attempt you corrected is not a finding. The "
    "corrected run is the same check over the same scope: the full command "
    "the task or the repository names, with only what you ran wrongly put "
    "right. It is never a narrower one (fewer files or tests, a filter, or a "
    "flag such as `--passWithNoTests` that lets it pass on less). If the only "
    "run that passed was narrower, the failing run is the last run of that "
    "check: report it. Never describe a passing run as a finding.\n\n"
    "Report a failing check here even when you think your change did not "
    "cause it: the batch is then recorded as applied with a failing check, "
    "and the user is told, instead of the run reporting a clean success.\n"
)


#: Appended after :data:`WRITE_CHECK_CONTRACT` for an implement task that
#: edits files (fix round 28, live run 12 OpenCode accept 01: T001's runner
#: ran T002's release check unprompted, and the failure T002 exists to
#: report was recorded as T001's own): which checks are the task's to run.
#: A run of another task's check that reports only that task's finding is
#: recorded as repeating it (``repeated_findings_for``), never as this
#: task's failure; the paragraph says so, so the task need not argue it in
#: the finding. It never tells a task to skip a check: a code task's run
#: of the repository's tests is its own check's best evidence (live run
#: 12's racing tasks all ran `npm test`).
IMPLEMENT_WHICH_CHECKS = (
    "\nWhich checks to run: the ones this task or its acceptance criteria "
    "name, and the tests that cover the files you edited. When one of them "
    "is also a check another task of the plan exists to run, report it as "
    "asked: a finding that is the same one that task reports is recorded as "
    "that task's finding, not as this task's failure.\n"
)


#: Appended to the result contract of a check task (an ``implement`` task that
#: declares no files): the structured check result the verdict reads
#: (``batch_reply.check_findings_from``). Racing re-run 4 (2026-10-05):
#: T007's ``npx html-validate`` reported two problems, the runner said
#: ``no-op`` and wrote them only in ``notes``, and the task read VERIFIED.
#: Fix round 11: a check that could not run is ``failed`` (it used to be asked
#: for as a finding, so a missing ``npx`` read as findings the run went on
#: past), and the tasks that depend on a check with findings wait for it.
#: Fix round 12: it says so with ``check.could_not_run: true``, because a
#: ``failed`` reply that lists findings is read as findings (runners answer
#: ``failed`` for a check that ran and failed).
CHECK_RESULT_CONTRACT = (
    "\n## Check result (required for this task)\n\n"
    "This task declares no files: it is a check, and it must not change any "
    "file. Run every check it names.\n\n"
    "If every check ran, answer `status: \"no-op\"` and add a `check` object "
    "to the JSON above:\n\n"
    "```json\n"
    '{"check": {"passed": false, "findings": ["<one problem: the command, '
    'what it reported, the file and line>"]}}\n'
    "```\n\n"
    "- `passed`: the JSON boolean `true` only when every check the task names "
    "ran and met its acceptance criteria, else `false`.\n"
    "- `findings`: one string per problem a check reported; `[]` when "
    "`passed` is `true`.\n\n"
    "Report the last run of each check. If you ran a check in a wrong form of "
    "your own (a wrong flag or mode for the command the task names) and then "
    "ran it as the task names it, report that run: the wrong form is not a "
    "finding.\n\n"
    "A problem a check finds is a finding, not a failure: do not fix it and "
    "do not answer `failed` for it. The findings are recorded for the code "
    "review, and the tasks that depend on this check wait until they are "
    "fixed or accepted.\n\n"
    "If a check could not run — its command is missing, it crashed, it timed "
    "out or it printed no result — answer `status: \"failed\"` with "
    "`\"could_not_run\": true` in the `check` object, and say in `summary` "
    "which check could not run and why:\n\n"
    "```json\n"
    '{"status": "failed", "check": {"passed": false, "could_not_run": true, '
    '"findings": []}}\n'
    "```\n\n"
    "Never list a check that did not run as a finding: it says nothing about "
    "the code, and `could_not_run` stops the run so the cause can be fixed. "
    "A `failed` reply whose `check` lists findings and does not say "
    "`could_not_run` is recorded as a check that ran and found them.\n"
)


def is_check_task(kind: str, task: Dict[str, Any]) -> bool:
    """Whether *task* is a verification-only ``implement`` task (no files)."""
    return kind == "implement" and not snapshot_file_set(task)


def dispatch_line(
    batches: int, dispatch: int, *, manual: int = 0, waiting: Sequence[str] = (),
) -> str:
    """``Organized into N execution batches: X task(s) to dispatch …``.

    The one wording both implement legs print: the native emit counts the
    batches it hands the host, the executor what its run will dispatch
    (:meth:`WriteBatchScheduler._dispatch_preview`, fix round 18). *waiting*
    names the tasks that run only if a check dispatched before them passes.
    """
    waiting = sorted(waiting)
    return (
        f"Organized into {batches} execution "
        f"{'batch' if batches == 1 else 'batches'}: {dispatch} "
        f"task(s) to dispatch"
        + (f", {manual} manual task(s) it does not run" if manual else "")
        + (
            f" ({', '.join(waiting)} {'waits' if len(waiting) == 1 else 'wait'} "
            f"on a check's verdict)"
            if waiting else ""
        )
    )
