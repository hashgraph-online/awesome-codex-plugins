"""How a write dispatch's reply is read: its check, its own batch check,
the items it declined, and the labels its outcome is recorded under.

No I/O: every function takes the parsed reply (or a recorded row) and
returns words. A check task's ``check`` object (:func:`read_check_reply`,
:func:`check_findings_from`), a code batch's own check and what it ran
(:func:`batch_check_findings`, :func:`ran_check_outcomes`,
:func:`ran_no_check`), the items a reply declined
(:func:`declined_items`), the ``WRITE_*`` outcome words and their labels
(:func:`write_outcome_label`), and the ``row_*`` readers of a recorded
row (``batch_ledger``, ``apply_report``, the scheduler). The executor,
the scheduler and ``util batch-done`` read the same reply through these,
so the two legs cannot read it differently. It imports none of the
executor's other modules; ``CHECK_FAILED_WITHOUT_FINDINGS`` lives in
``known_checks``, which imports nothing from here.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, NamedTuple, Optional, Sequence

from .text_clip import clip
from . import known_checks as _known_checks


#: The four D3g write outcomes, plus the D3l containment failure. Recorded on the
#: outcome as its own axis rather than being folded into ``status``. "Applied"
#: and "no-op" are dispatches the loop continues past; "clean failure" (nothing
#: moved and the work is not done: a ``failed`` claim, a crash, or — an ``applied``
#: claim no byte backs, after its one re-send) is
#: never ``ok``, and "partial application" and "policy violation" stop it too.
WRITE_APPLIED = "applied"
WRITE_CLEAN_FAILURE = "clean-failure"
#: The runner said ``no-op`` and the byte comparison agrees. Its own outcome
#: rather than a clean failure, because the claim and the verdict AGREE: a
#: clean failure is *success* claimed with nothing moved, and labelling an
#: honest "already present" batch ``(batch failed — …)`` in the prior-changes
#: log and the summary table told the next batch, and the reader, that the
#: work had failed. Measured 2026-09-16 on two verification-only tasks.
WRITE_NO_OP = "no-op"
#: What a verification-only ``implement`` task (one declaring no files) reads as
#: when nothing moved: the check ran and left the repository as it was. A
#: *label*, never a ``write_outcome`` value — the outcome stays ``no-op``, which
#: resume, ``util restore-batch`` and every older reader key on — so it rides
#: beside it as ``outcome_label``. A verification-only task that moved bytes reads
#: ``partial-application`` like any other partial, so the pair is VERIFIED or
#: PARTIAL on every surface.
WRITE_LABEL_VERIFIED = "verified"
#: A verification-only task whose check ran, changed nothing and reported
#: problems in its reply's structured ``check`` object (``passed: false`` or a
#: non-empty ``findings`` list). Never ``verified``: racing re-run 4
#:  recorded T007 VERIFIED while ``npx html-validate`` had reported
#: two problems that lived only in the runner's free-text notes. Not a stop
#: either: what a check finds is a finding, never an exit code (AGENTS.md), and
#: review-code / apply-code-fixes are the phases that fix it — so the tasks
#: that do not depend on the check go on, ``write_outcome`` stays ``no-op``
#: and every surface names the findings. The tasks that DO depend on it are
#: not run: ``WriteBatchScheduler`` records them ``not run —
#: upstream check … reported problems`` and implement ends needing a human.
WRITE_LABEL_CHECK_FINDINGS = "check-findings"
WRITE_PARTIAL = "partial-application"

#: Bounds on what one check reply's ``findings`` may put on the surfaces
#: (summary.md, the reports, state.json, review-code's prompts).
CHECK_FINDINGS_MAX = 20
CHECK_FINDING_MAX_CHARS = 300

#: The finding recorded for a ``check`` that says neither that it passed nor
#: what it found (``{}``, ``{"passed": null, "findings": []}``): an unknown
#: result is never a pass.
CHECK_RESULT_UNKNOWN = (
    "the check's reply did not say whether it passed (its `check` object had "
    "no usable `passed` value and no findings); see the runner notes"
)

#: The words ``check.passed`` (and ``check.could_not_run``) may be spelled
#: in, besides the JSON booleans (a near-miss reply: ``"false"``, ``0``, and
#: since the strings ``"1"``/``"0"``, which read as the numbers
#: do). Anything else is an unknown result.
_CHECK_PASSED_WORDS = frozenset({"true", "yes", "pass", "passed", "1"})
_CHECK_FAILED_WORDS = frozenset({"false", "no", "fail", "failed", "0"})

#: A bare ``findings`` value that says "nothing found" (any case, a trailing
#: ``.``/``!`` ignored), read as ``[]`` only beside a ``passed`` that reads
#: true (``{"passed": true, "findings": "none"}`` was one
#: finding, "none", which held back every task after the check). Kept
#: short on purpose: any other text is a finding.
_EMPTY_FINDINGS_WORDS = frozenset({
    "", "none", "n/a", "na", "no problems", "no problems found", "no findings", "0",
})


def _says_nothing_found(value: Any) -> bool:
    """Whether a bare (non-list) ``findings`` value is an empty-ish marker."""
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        word = " ".join(value.strip().lower().rstrip(".!").split())
        return word in _EMPTY_FINDINGS_WORDS
    return False


def write_outcome_label(
    write_outcome: Optional[str], verification_only: bool = False,
    check_findings: Optional[Sequence[str]] = None,
) -> Optional[str]:
    """The word every report shows for a write outcome (:data:`WRITE_LABEL_VERIFIED`)."""
    if verification_only and write_outcome == WRITE_NO_OP:
        return WRITE_LABEL_CHECK_FINDINGS if check_findings else WRITE_LABEL_VERIFIED
    return write_outcome


def _check_passed(value: Any) -> Optional[bool]:
    """``check.passed`` read leniently: ``True``/``False``, else ``None``.

    The JSON booleans, ``1``/``0`` (numbers or strings) and the words in
    :data:`_CHECK_PASSED_WORDS` / :data:`_CHECK_FAILED_WORDS` (any case);
    anything else (``null``, a missing key, ``"maybe"``) is unknown.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        word = value.strip().lower()
        if word in _CHECK_PASSED_WORDS:
            return True
        if word in _CHECK_FAILED_WORDS:
            return False
    return None


def _finding_text(item: Any) -> str:
    """One finding as one line: an object is read as its non-empty values."""
    if item is None:
        return ""
    if isinstance(item, dict):
        # An object per finding (`{"command": …, "message": …}`) is read as
        # its values, so a near-miss shape still names the problem.
        item = "; ".join(
            f"{key}: {value}" for key, value in item.items()
            if value not in (None, "", [], {})
        )
    return " ".join(str(item).split())


class CheckReply(NamedTuple):
    """What a check task's reply says in its ``check`` object.

    ``findings`` is :func:`check_findings_from`'s answer. ``listed`` is
    whether the reply listed at least one finding of its own (not one this
    reader supplied: :data:`CHECK_FAILED_WITHOUT_FINDINGS`,
    :data:`CHECK_RESULT_UNKNOWN`). ``could_not_run`` is ``check.could_not_run``
    read as leniently as ``passed`` (``true``, ``1``, ``"1"``,
    ``"true"``/``"yes"``; :func:`_check_passed`): the runner says
    a check could not run.
    """

    findings: Optional[List[str]]
    listed: bool
    could_not_run: bool


def read_check_reply(result: Any) -> CheckReply:
    """The reply's ``check`` object, read (:class:`CheckReply`).

 (a coordinator decision after racing run 3: real runners
    answer ``failed`` for a check that ran and found problems): a check
    that could not run says so with ``check.could_not_run: true``, and only
    that, or a crash, is a check that did not run. ``write_verdict.decide``
    reads a ``failed`` reply whose ``check`` lists findings, and does not
    say it could not run, as findings.
    """
    findings = check_findings_from(result)
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        return CheckReply(findings, False, False)
    could_not_run = _check_passed(check.get("could_not_run")) is True
    listed = bool(findings) and findings[0] not in (
        _known_checks.CHECK_FAILED_WITHOUT_FINDINGS, CHECK_RESULT_UNKNOWN,
    )
    return CheckReply(findings, listed, could_not_run)


def check_findings_from(result: Any) -> Optional[List[str]]:
    """The structured check result of a write reply, as a findings list.

    ``None`` when the reply carries no ``check`` key at all (an older reply,
    a task that is not a check); ``[]`` when it says the check passed and
    lists nothing; otherwise the findings, one line each
    and bounded (:data:`CHECK_FINDINGS_MAX`, :data:`CHECK_FINDING_MAX_CHARS`).
    Read from the reply's own field, never from its notes.

    Lenient on shape, strict on meaning. The schema admits
    any ``check``, because a near-miss shape (``passed: "false"``,
    ``findings: "one problem"``, a number as a finding) used to be a
    ``schema_invalid`` reply, and implement had no report re-ask then, so the
    run stopped for good on a check that had answered (it has one; the lenient reading
    stays, so a near-miss costs no re-ask).
    Each shape is read here
    instead, and only a clear pass with nothing listed is a pass: a finding
    beside ``passed: true`` still counts, ``passed: false`` with none listed
    gets :data:`CHECK_FAILED_WITHOUT_FINDINGS`, and a ``check`` that says
    neither (``{}``, ``passed: null``, ``check: null``, a ``check`` that is
    not an object) gets :data:`CHECK_RESULT_UNKNOWN` — never a pass. ``check: null``
    read as no result, so a check task's reply
    carrying it was VERIFIED; only a missing key is no result now. A bare
    ``findings`` that says "nothing found" (``"none"``, ``"N/A"``, ``"No
    problems found."``, ``0``) beside a ``passed`` that reads true is
    ``[]`` (:data:`_EMPTY_FINDINGS_WORDS`).
    """
    if not isinstance(result, dict) or "check" not in result:
        return None
    check = result.get("check")
    if check is None:
        return [f"{CHECK_RESULT_UNKNOWN} (its `check` was null)"]
    if not isinstance(check, dict):
        shown = clip(check, 80)
        return [
            f"{CHECK_RESULT_UNKNOWN} (its `check` was "
            f"{type(check).__name__} {shown!r}, not an object)"
        ]
    raw = check.get("findings")
    passed = _check_passed(check.get("passed"))
    if isinstance(raw, list):
        items = raw
    elif raw is None:
        items = []
    elif passed is True and _says_nothing_found(raw):
        # "findings": "none" beside a pass says there is none.
        items = []
    else:
        # One finding given bare (a string, an object, a number).
        items = [raw]
    findings = []
    for item in items:
        text = _finding_text(item)
        if text:
            findings.append(clip(text, CHECK_FINDING_MAX_CHARS))
    if len(findings) > CHECK_FINDINGS_MAX:
        extra = len(findings) - (CHECK_FINDINGS_MAX - 1)
        findings = findings[:CHECK_FINDINGS_MAX - 1] + [
            f"(+{extra} more finding(s) in the batch result file)"
        ]
    if findings:
        return findings
    if passed is True:
        return []
    if passed is False:
        return [_known_checks.CHECK_FAILED_WITHOUT_FINDINGS]
    return [CHECK_RESULT_UNKNOWN]


#: The finding a code batch's own check carries when its reply said
#: ``check.could_not_run``: every surface then says "its check
#: could not run", never that it fails.
BATCH_CHECK_COULD_NOT_RUN = "its check could not run"


def batch_check_could_not_run(findings: Optional[Sequence[str]]) -> bool:
    """Whether a code batch's own-check findings say the check could not run."""
    return bool(findings) and str(findings[0]).startswith(BATCH_CHECK_COULD_NOT_RUN)


def batch_check_words(findings: Optional[Sequence[str]]) -> str:
    """How a surface names a code batch's own check that did not pass:
    "its check could not run", else "a check it ran fails"."""
    return (
        BATCH_CHECK_COULD_NOT_RUN if batch_check_could_not_run(findings)
        else "a check it ran fails"
    )


def batch_check_findings(result: Any) -> Optional[List[str]]:
    """What a code-writing batch's own ``check`` object says about the checks
    it ran on its edits.

    ``None`` when the reply reports no usable check — no ``check`` key, one
    that says neither whether it passed nor what failed (``{}``, ``null``), or
     one whose ``ran`` is empty, the contract's way of saying no
    check ran (:func:`ran_no_check`), and that names no finding and does not
    say it failed: saying nothing is not a finding here, as
    it is for a check task, whose whole answer it is. A command ``ran`` maps
    to ``failed`` is a failing check whatever ``passed`` says
    (:func:`ran_check_outcomes`). ``[]`` for a clear pass; else the failing checks, bounded. Codex
    racing run 5: an apply-code-fixes batch wrote "the bundled
    test fails" in its free-text ``notes``, the repository's test failed
    afterwards, and the run reported every fix applied. Never read from
    ``notes``.

    Not the check task's fail-closed reading: a check task's ``check`` is its whole
    verdict, so a finding beside
    ``passed: true`` counts there; here ``passed: true`` is the batch's own
    word that its checks passed, and what it lists beside it ("npm test: 12
    passed") is informational, never a failing check. ``could_not_run``
    (read as leniently as ``passed``) is one finding,
    :data:`BATCH_CHECK_COULD_NOT_RUN` with whatever the reply listed after
    it, so it reads "its check could not run", never "fails".

    One rule on both legs, the one
    ``references/own-check.md`` states for the native host's ``util
    batch-done --own-check``, first match wins: no ``check`` object is no
    check; ``could_not_run`` is that; a reply that ran nothing
    (:func:`ran_no_check`) is failing when it names a finding, whatever
    ``passed`` says (a pass of nothing is no verdict), or says ``passed:
    false`` (:data:`CHECK_FAILED_WITHOUT_FINDINGS` kept), and no check
    otherwise (a ``not_run`` reason with no ``ran`` ran nothing too); any other reply is
    a pass on ``passed: true``, failing on ``passed:
    false`` or a finding, a pass when only ``ran`` says what passed, and no
    check when it says nothing at all.
    """
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        # No `check` key, `null`, or not an object: no usable report.
        return None
    stated = _stated_findings(check)
    if _check_passed(check.get("could_not_run")) is True:
        text = BATCH_CHECK_COULD_NOT_RUN + (
            f": {'; '.join(stated)}" if stated else ""
        )
        return [clip(text, CHECK_FINDING_MAX_CHARS)]
    passed = _check_passed(check.get("passed"))
    if ran_no_check(result):
        # It ran nothing (an empty `ran`, every entry "not run", or only the
        # result shape's placeholder): its `passed: true` is a pass of
        # nothing, so a failure it names counts and nothing else is a pass;
        # a `passed: false` is a failing check (round 26 made
        # it "no check", where it had been CHECK_FAILED_WITHOUT_FINDINGS).
        if stated:
            return stated
        return [_known_checks.CHECK_FAILED_WITHOUT_FINDINGS] if passed is False else None
    ran = ran_check_outcomes(result)
    if passed is True:
        # What it lists beside a pass is informational.
        return _with_ran_failures([], ran)
    if passed is False:
        return _with_ran_failures(stated or [_known_checks.CHECK_FAILED_WITHOUT_FINDINGS], ran)
    if stated:
        return _with_ran_failures(stated, ran)
    # It says neither: `ran` alone says how its checks ended, if anything.
    if any(word == _ran_word("failed") for word in ran.values()):
        return _with_ran_failures([], ran)
    if any(word == _ran_word("passed") for word in ran.values()):
        return []
    return None


#: How much of a code batch's ``check.note`` the records carry.
CHECK_NOTE_MAX_CHARS = 300


def batch_check_note(result: Any) -> Optional[str]:
    """A code batch's ``check.note``: its own words about the checks it ran,
    one plain line bounded at :data:`CHECK_NOTE_MAX_CHARS`, or ``None``.

    T007 re-ran the check the user accepted and wrote its comment into the
    finding ("… (known problem the user accepted in T002)", "… — the
    accepted T002 problem (…), not caused by this note"), and the strict
    match read the finding as T007's own failure. The contract asks for
    each finding as the check reported it and for any comment here instead
    (:data:`batch_prompt.WRITE_CHECK_CONTRACT`). Recorded and shown
    beside the check on both legs (``util batch-done --note``); never read
    as a finding and never matched on."""
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        return None
    note = check.get("note")
    if not isinstance(note, str):
        return None
    return clip(note, CHECK_NOTE_MAX_CHARS) or None


def _ran_word(which: str) -> str:
    """``known_checks``' ``passed`` / ``failed`` outcome word."""
    return _known_checks.LISTED_FAILED if which == "failed" else _known_checks.LISTED_PASSED


def _stated_findings(check: Dict[str, Any]) -> List[str]:
    """The findings a ``check`` object names itself, bounded, without the
    placeholders :func:`check_findings_from` puts in for none. Beside a
    ``passed`` that reads true, an entry that only says nothing was found
    (``"none"``, ``"n/a"``, ``0``) is no finding either; beside any other ``passed`` it
    stays one, as before."""
    raw = check.get("findings")
    if _check_passed(check.get("passed")) is True:
        if isinstance(raw, list):
            raw = [item for item in raw if not _says_nothing_found(item)]
        elif _says_nothing_found(raw):
            raw = None
    return [
        text for text in (check_findings_from(
            {"check": {"passed": False, "findings": raw}}
        ) or [])
        if text not in (_known_checks.CHECK_FAILED_WITHOUT_FINDINGS, CHECK_RESULT_UNKNOWN)
    ]


def ran_check_outcomes(result: Any) -> Dict[str, str]:
    """``{command: passed|failed|not run}`` from a code batch's ``check.ran``
    The commands it says it ran, read as leniently as an
    apply-code-fixes batch's ``listed`` (``known_checks.listed_check_outcomes``).

    The contract asks for a map; a list of ``"<command>: <outcome>"`` strings
    is read too. An entry that cannot be read is left out, never guessed.
    """
    check = result.get("check") if isinstance(result, dict) else None
    ran = check.get("ran") if isinstance(check, dict) else None
    if isinstance(ran, list):
        pairs: Dict[str, Any] = {}
        for item in ran:
            if isinstance(item, str):
                command, sep, word = item.rpartition(":")
                if sep and command.strip():
                    pairs[command] = word
            elif isinstance(item, dict):
                # `{"command": …, "outcome": …}` per check, a near miss.
                command = next((item[k] for k in _RAN_COMMAND_KEYS if k in item), None)
                word = next((item[k] for k in _RAN_OUTCOME_KEYS if k in item), None)
                if isinstance(command, str) and command.strip():
                    pairs[command] = word
        ran = pairs
    if not isinstance(ran, dict) or not ran:
        return {}
    return {
        command: word for command, word in _known_checks.listed_check_outcomes(ran).items()
        if not _is_placeholder(command)
    }


#: The keys a ``ran`` entry written as an object names its command and its
#: outcome under, first found wins.
_RAN_COMMAND_KEYS = ("command", "cmd", "check", "name")
_RAN_OUTCOME_KEYS = ("outcome", "result", "status", "passed")


def _is_placeholder(command: str) -> bool:
    """Whether a ``ran`` key is the contract's own placeholder copied as it
    is (``<each check command you ran>``): it names no command."""
    text = command.strip()
    return len(text) > 1 and text[0] == "<" and text[-1] == ">"


def _names_a_command(entry: Any) -> bool:
    """Whether one entry of a ``ran`` list may name a command it ran: not the
    contract's placeholder, whether written as a ``"<command>: <outcome>"``
    string or (it read as a clean pass) as
    an object whose command is the placeholder. An entry that cannot be read
    counts, so what ran stays unknown rather than nothing."""
    if isinstance(entry, str):
        return not _is_placeholder(entry.rpartition(":")[0] or entry)
    if isinstance(entry, dict):
        command = next((entry[k] for k in _RAN_COMMAND_KEYS if k in entry), None)
        return not (isinstance(command, str) and _is_placeholder(command))
    return True


def ran_no_check(result: Any) -> bool:
    """Whether a code batch's ``check`` says it ran no check:
    its ``ran`` is present and empty, holds only the contract's placeholder,
    or every entry in it reads ``not run`` — or it has no
    ``ran`` at all but gives a ``not_run`` reason, the contract's other half
    of "I ran no check", so ``{"passed": true, "not_run": "…"}`` is never a
    pass of nothing.

    A missing ``ran`` with no ``not_run`` reason is not this (an older reply,
    read as before), and neither is a ``ran`` holding an entry that cannot be
    read: what it ran is then unknown, and ``passed``/``findings`` decide.
    """
    check = result.get("check") if isinstance(result, dict) else None
    ran = check.get("ran") if isinstance(check, dict) else None
    if ran is None and isinstance(check, dict):
        reason = check.get("not_run")
        return isinstance(reason, str) and bool(reason.strip())
    if not isinstance(ran, (dict, list)):
        return False
    # The contract's placeholder copied as it is names no command (a reply
    # that pasted the shape without running anything).
    named = [
        entry for entry in ran if _names_a_command(entry)
    ] if isinstance(ran, list) else [key for key in ran if not _is_placeholder(str(key))]
    if not named:
        return True
    outcomes = ran_check_outcomes(result)
    return len(outcomes) == len(named) and all(
        word == _known_checks.LISTED_NOT_RUN for word in outcomes.values()
    )


def _with_ran_failures(
    findings: Optional[List[str]], ran: Dict[str, str],
) -> Optional[List[str]]:
    """*findings* with one added for each command ``ran`` says failed that no
    finding names (``known_checks.with_listed_failures``): a reply whose
    ``passed`` says true beside a failed command is never a clean pass.

    It only adds. A ``ran`` naming no failure leaves a
    ``passed: false`` that named nothing a failing check
    (:data:`CHECK_FAILED_WITHOUT_FINDINGS`), as the native leg records it;
    round 26 read it as a pass through ``with_listed_failures``' rule for an
    apply-code-fixes batch's ``listed``, which stays
    ``listed``'s alone. A failed command added stands in for that bare
    placeholder, as the native host names the command instead."""
    failed = {
        command: word for command, word in ran.items() if word == _ran_word("failed")
    }
    if not failed:
        return findings
    current = _known_checks.with_listed_failures(findings, failed) or []
    if len(current) > 1 and current[0] == _known_checks.CHECK_FAILED_WITHOUT_FINDINGS:
        current = current[1:]
    return current


def _report_check_evidence(result: Any) -> Optional[Dict[str, Any]]:
    """A readable check object to retain across a report-only re-ask.

    A restatement runs no check, so it cannot retract the original turn's
    evidence. Keep the whole object, including ``listed`` and any extra
    detail, when the existing lenient readers can use it. A missing or
    unreadable check remains repairable rather than pinning an unknown
    result over a useful correction.
    """
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        return None
    if (
        batch_check_findings(result) is not None
        or _known_checks.listed_check_outcomes(check.get("listed"))
        # "I ran no check" is an answer too; a restatement
        # cannot turn it into a pass.
        or ran_no_check(result)
    ):
        return copy.deepcopy(check)
    return None


#: How much of one declined item's reason a row, a stamp or a notice carries.
DECLINED_REASON_MAX_CHARS = 300


def declined_reason(text: Any) -> str:
    """One declined item's reason as every record carries it: the batch's
    own words, whitespace collapsed and bounded; ``""`` for no text.

    Both legs read a reason through here: the executor's
    :func:`declined_items` and ``util batch-done --declined``, and
    :func:`row_declined` reads a record back through it.

    The closing full stop is kept.
    ``processed_<phase>``, the write mirror, the verdict stamp and the report
    dropped it while the reply, the log and the host's summary.md kept it.
    A line that puts its own punctuation right after a reason drops the
    reason's one there (``text_clip.without_closing_mark``: the
    ``[BATCH_DECLINED]`` line, the stop and log text, the notes, ``status``),
    so a reason is still printed with one full stop (the decline fixture,
    2026-10-07: "… MAX_SPEED.."); a reason of ``...`` or ``.`` stays a
    reason.
    """
    if not isinstance(text, str):
        return ""
    reason = " ".join(text.split())
    # Cut at a word and marked, never mid-word.
    return clip(reason, DECLINED_REASON_MAX_CHARS)


@dataclass
class DeclinedItems:
    """What a write reply's ``declined`` says, read against its batch.

    ``items`` maps each expected id the batch declined — not also in ``ids``,
    with a non-empty reason — to that reason, in the batch's own order.
    ``conflicting`` holds the ids the reply put in both ``ids`` and
    ``declined``: neither claim stands, so such an id is not attested at all.
    ``problems`` names every other entry that could not be read as a decline
    (an id the batch does not hold, an entry without an id or a reason, a
    value that is not a list of objects), in plain words for the stop.
    """

    items: Dict[str, str] = field(default_factory=dict)
    conflicting: List[str] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)


def declined_items(
    result: Any, expected_ids: Sequence[str],
) -> DeclinedItems:
    """Read a write reply's ``declined`` leniently against *expected_ids*.

    Codex racing run 7: a batch applied
    one fix and left the other on purpose ("Not applied; T011 records the
    clamp removal as deliberate"), said so only in ``notes``, and stopped as
    a partial application on the run and on its resume; the contract had no
    place for a decline. A reason is what makes a decline: an entry without
    one is a problem, and its id reads as not having come back, as an id
    missing from ``ids`` always has. Never read from ``notes``.
    """
    out = DeclinedItems()
    raw = result.get("declined") if isinstance(result, dict) else None
    if raw is None:
        return out
    expected = [str(item) for item in expected_ids]
    reported = result.get("ids") if isinstance(result, dict) else None
    applied = {str(item) for item in reported} if isinstance(reported, list) else set()
    if not isinstance(raw, list):
        out.problems.append("`declined` is not a list")
        return out
    found: Dict[str, str] = {}
    for index, entry in enumerate(raw, 1):
        if not isinstance(entry, dict):
            out.problems.append(f"`declined` entry {index} is not an object")
            continue
        item = entry.get("id")
        item = str(item).strip() if isinstance(item, (str, int)) else ""
        if not item:
            out.problems.append(f"`declined` entry {index} names no id")
            continue
        if item not in expected:
            out.problems.append(
                f"`declined` names {item!r}, which this batch does not hold"
            )
            continue
        if item in applied:
            if item not in out.conflicting:
                out.conflicting.append(item)
                out.problems.append(f"{item} is in both `ids` and `declined`")
            continue
        reason = declined_reason(entry.get("reason"))
        if not reason:
            out.problems.append(f"`declined` gives no reason for {item}")
            continue
        found.setdefault(item, reason)
    out.items = {item: found[item] for item in expected if item in found}
    return out


def row_declined(row: Any) -> Dict[str, str]:
    """A serialized row's (or verdict stamp's) declined items, ``{id: reason}``."""
    raw = row.get("declined") if isinstance(row, dict) else None
    out: Dict[str, str] = {}
    for entry in raw if isinstance(raw, list) else []:
        if isinstance(entry, dict) and entry.get("id") and entry.get("reason"):
            # As recorded (a record from has no closing
            # stop; one from before `declined_reason` reads the same way).
            reason = declined_reason(str(entry["reason"])) or str(entry["reason"])
            out.setdefault(str(entry["id"]), reason)
    return out


#: summary.md's sections for an apply phase's items that were not applied, written by
#: the executor's summary and named by the native
#: runbooks' template and `util batch-done`'s `[BATCH_DECLINED]` /
#: `[BATCH_SKIPPED]` lines.
DECLINED_SECTION_HEADING = "Declined by their batch (not applied)"
SKIPPED_SECTION_HEADING = "Skipped at your request (not applied)"


def declined_record(items: Dict[str, str]) -> List[Dict[str, str]]:
    """The ``declined`` list a row, a verdict stamp and a mirror row carry."""
    return [{"id": item, "reason": reason} for item, reason in items.items()]


def row_batch_check_findings(row: Dict[str, Any]) -> List[str]:
    """A serialized row's own-check findings (its ``batch_check``), else ``[]``."""
    check = row.get("batch_check") if isinstance(row, dict) else None
    if not isinstance(check, dict):
        return []
    return [str(item) for item in (check.get("findings") or []) if str(item)]


def _row_findings_by_check(row: Dict[str, Any], key: str) -> Dict[str, List[str]]:
    """A serialized row's ``{check id: [finding, ...]}`` map under *key*,
    empty findings and empty lists dropped, else ``{}``."""
    found = row.get(key) if isinstance(row, dict) else None
    if not isinstance(found, dict):
        return {}
    return {
        str(check_id): [str(item) for item in items if str(item)]
        for check_id, items in found.items()
        if isinstance(items, list) and any(str(item) for item in items)
    }


def row_batch_check_accepted(row: Dict[str, Any]) -> Dict[str, List[str]]:
    """A serialized row's own-check findings that only repeat what the user
    accepted, by check id (its ``batch_check_accepted``)."""
    return _row_findings_by_check(row, "batch_check_accepted")


def row_batch_check_repeats(row: Dict[str, Any]) -> Dict[str, List[str]]:
    """A serialized row's own-check findings that are the same findings a
    check task of the run reported, by that check's id (its
    ``batch_check_repeats``)."""
    return _row_findings_by_check(row, "batch_check_repeats")


def row_batch_check_note(row: Dict[str, Any]) -> Optional[str]:
    """A serialized row's own-check note (its ``batch_check_note``), else ``None``."""
    note = row.get("batch_check_note") if isinstance(row, dict) else None
    if not isinstance(note, str):
        return None
    return clip(note, CHECK_NOTE_MAX_CHARS) or None


def row_outcome_label(row: Dict[str, Any]) -> Optional[str]:
    """A serialized row's label: ``outcome_label`` when present, else ``write_outcome``.

    Only a verification-only row carries ``outcome_label`` (every other row
    is byte-identical to before), so a reader asks this rather than either key.
    """
    return row.get("outcome_label") or row.get("write_outcome")


def check_record(findings: Sequence[str]) -> Dict[str, Any]:
    """The ``check`` object a row, a verdict stamp and a mirror row carry."""
    return {"passed": not findings, "findings": list(findings)}


def row_check_findings(row: Dict[str, Any]) -> List[str]:
    """A serialized row's check findings (its ``check`` object), else ``[]``."""
    check = row.get("check") if isinstance(row, dict) else None
    if not isinstance(check, dict):
        return []
    return [str(item) for item in (check.get("findings") or []) if str(item)]


WRITE_SCHEMA_REJECTED = "schema-rejection"
WRITE_POLICY_VIOLATION = "policy-violation"

#: Write outcomes that stop the batch loop at its boundary (D3g/D3n): the phase is
#: not completed, snapshots stay in place, and the run exits 3 naming the restore
#: command — under ``--yes`` too, since an unattended run may not decide that a
#: half-applied plan file is acceptable.
WRITE_STOP_OUTCOMES = frozenset({WRITE_PARTIAL, WRITE_POLICY_VIOLATION})
