#!/usr/bin/env python3
"""``util report-check``: does this turn's final message carry the next command?

The Claude Code plugin's ``Stop`` hook (``hooks/report-check.sh``) runs this
after every turn whose transcript mentions the block at all
(plans/next-phase-command.md T11). A phase result, or ``util next-command``,
prints the next step as a block of marker lines above its result line::

    [NEXT_COMMAND] <command>
    [NEXT_COMMAND_OPTIONAL_WHY] <why>
    [NEXT_COMMAND_OPTIONAL] <command>
    [NEXT_COMMAND_ANSWERS_WHY] <why>
    [NEXT_COMMAND_ANSWERS] <command>

(the answers pairs only from ``util next-command`` on a stopped implement,
fix round 14: the combined answer first when more than one task waits, then
each answer alone since fix round 20; the check holds the report to the
commands printed, in any order, so one waiting task means no combined
command to carry), or ``[WORKFLOW_COMPLETE]``. Either kind is followed by one
``[MANUAL_TASK] <id> <title>`` line per implement task the run deferred to the
user, while any is owed, and one ``[MANUAL_TASK_NOTE]`` line saying how to
record them done (after the commands of a command block since fix round 16),
then the ``[MANUAL_TASK_COMMAND]`` line that does it, a command the report
fences like the others (fix round 22).
The model is told to end its report with each command in a fenced block,
copied character for character, or with "Workflow complete.", and then those
tasks listed. This checks the copy, and only the copy:

* It reads the transcript entries since the last prompt the user **typed**: a
  user entry whose content is a string or carries a text block. A user entry
  that only carries ``tool_result`` blocks is part of the run, and so is an
  ``isMeta`` entry (a loaded skill body, a local-command caveat, a scheduled
  wakeup's prompt), a compaction summary and, since fix round 26, an entry
  the harness sent (``origin.kind`` other than ``human``: a background task's
  ``task-notification``). Claude Code runs a phase's subagents in the
  background, so one headless phase spans several turns, and live run 11's
  Claude Code 04 printed the ready section in one and ended on another.
  ``isSidechain`` entries belong to a subagent, not the run.
* Among that run's tool results it takes the **last** block. A block printed
  only before the user's last typed prompt is not this run's to copy, so it
  is never checked. Nor is a block a subagent's report quotes (an ``Agent``,
  ``Task`` or ``SendMessage`` result, :data:`SUBAGENT_TOOLS`, fix round 27):
  those are the subagent's words, not a phase's output, while a ``Read``, a
  ``tail`` or a ``grep`` of the phase's own output still counts.
* A block's ready section (``util next-command``'s ``[NEXT_STEP_MARKDOWN]``
  … ``[NEXT_STEP_MARKDOWN_END]``, a success's or a stop's) holds the report
  to every command it fences too, beside the marker lines' (fix round 26),
  and a block reason asks for the section printed as given.
* **A native ``--improve-plan`` / ``--improve-code`` / ``--improve-commits``
  run is held to its own continuation, never to an inner phase's next step**
  (Fable review 2026-10-09; improve-commits' core runs the same planner on
  the commit brief, plans/review-commits.md §2.8). Its core first runs
  ``util improve-steps``, which ends with
  ``[IMPROVE_RERUN] <command>``, the composite's continuation in the host's
  spelling; each phase it then runs still prints its own standalone block
  (review-plan's ``--reaggregate`` names ``--apply-suggestions <plan>``), and
  only the core's closing ``util next-command`` gives the run a next step.
  Read as the last block, review-plan's would block every correct report of
  a run whose apply stopped (the core gives ``[IMPROVE_RERUN]`` and the
  stopped phase's own answer there, and makes no lookup), and the forced
  turn would hand the user a bare ``--apply-suggestions``, which re-emits
  every batch on this leg. So an ``[IMPROVE_RERUN]`` line printed by a call
  that ran ``util improve-steps`` (:func:`planner_call_ids`: a plan or a core
  quoting the line is not the run's planner) is a block too
  (:attr:`Block.continuation`), and once it is the block held, a later block
  with no ready section, an inner phase's, does not replace it. A block with
  one does: every ``util next-command`` lookup prints a section and no phase
  result does, so a finished run is held to section 4's lookup as before. A
  run that never ran the planner (every other mode, and a composite refused
  or ``[ALREADY_COMPLETE]``, which prints no continuation) is read exactly
  as before. The one cost: a finished run whose closing lookup failed (exit
  3, no block) is held to the continuation, which on that plan prints
  ``[ALREADY_COMPLETE]`` and the next step.
* A marker counts only at the start of a line, which is where the emitter puts
  it. An indented example of the block (a plan or a doc quoting it, read by a
  tool) is not a phase result.
* It passes when every command of that block (the ``[NEXT_COMMAND]`` one,
  each ``[NEXT_COMMAND_OPTIONAL]`` one and each ``[NEXT_COMMAND_ANSWERS]`` one)
  is, byte for byte, a line inside a
  fenced code block of the final assistant message. Only the whitespace around
  a line is ignored, so a fence nested in a list item still counts. For
  ``[WORKFLOW_COMPLETE]`` it passes when the message says "Workflow complete."
  A block of either kind with ``[MANUAL_TASK]`` lines also needs each of their
  ids named as a word of its own, anywhere in the message (fix round 17: after
  a command block too, which SKILL.md and summary-format.md have asked for
  since fix round 16). Only the ids: a report that lists the tasks as the
  rule says always names them, while a check of the note's wording would
  block a report that put its command in backticks. A why line is never a
  command.
* The final message is the text of the run's trailing assistant entries, the
  ones after its last user entry of any kind (fix round 26: a wakeup's
  ``isMeta`` prompt ends the reply before it too). The
  ``Stop`` hook input's ``last_assistant_message`` is read too, when present,
  and the turn passes when either carries the copy: a stale transcript must
  never produce a block. The input (2.1.289 and 2.1.293, headless
  ``claude -p``) carries ``session_id``, ``transcript_path``, ``cwd``,
  ``prompt_id``, ``permission_mode``, ``effort``, ``hook_event_name``,
  ``stop_hook_active``, ``last_assistant_message``, ``background_tasks`` and
  ``session_crons``.
* **The hook waits for the transcript to settle before reading it** (fix
  round 27). Claude Code writes the transcript in batches, so the entries of
  the last moments before ``Stop`` are not on file when the hook starts.
  Measured on 2.1.293 against a localhost stub (2026-10-08): the reply was
  never on file at ``Stop`` and appeared 0.1-0.2 s later; with a reply sent
  2.5 s after the last tool result, that result was on file at ``Stop``; with
  a reply sent at once, it was not (the whole file was missing at ``Stop``
  in a session that young), so a block printed by the turn's last call was
  not seen and the turn passed (``hooks/report-check.sh`` exited at its
  marker grep in 3 ms). So the check reads the transcript only once the reply
  ``last_assistant_message`` names is on file after the run's last user
  entry, with no ``stop_hook_summary`` after it (that reply is an earlier
  ``Stop``'s), or, with no such field, once the file stopped growing for one
  step: :func:`settled_turn`, every :data:`SETTLE_STEP_S`, at most
  :data:`SETTLE_BUDGET_S`. Everything before the reply is on file once the
  reply is. Past the budget it decides on what is on file, a last line still
  being written left out. A transcript already settled costs one read.
* ``last_assistant_message`` is the text of the **last** assistant message
  Claude Code holds in memory, not the whole reply (hooks review of fix round
  10, read from the harness, not measured live). A reply split into several
  text blocks hands the hook only the last one, so a command copied into an
  earlier block reads as missing. Once the transcript has settled, its own
  trailing assistant entries carry the earlier blocks and are checked beside
  the field; a block that still happens (the budget ran out first) costs at
  most one needless turn: the model's extra turn ends with
  ``stop_hook_active`` set, and the hook passes at once then.
* A turn that ends on an API error fires Claude Code's ``StopFailure`` event,
  not ``Stop``, so this check never runs on it (``hooks/hooks.json`` runs it
  on ``Stop`` alone). :func:`ended_on_api_error` still passes such a turn, for
  a transcript checked by hand or read later: the model wrote no report there.
* On a miss it prints exactly one line, ``{"decision": "block", "reason": …}``,
  the one form Claude Code reads as a ``Stop`` decision. The reason names each
  missing command in its own fenced block and asks for it copied exactly (and
  repeats the block's other commands), and it asks for the whole report again
  (:data:`WHOLE_REPORT`), since the reply becomes the final message: racing
  run 5's block got back the `### Next Steps` section alone, and the run's
  result lost its report. The model gets one more turn: the hook script exits
  at once when ``stop_hook_active`` is true, and so does this. A block with a
  ready section says once how the report ends: with that section, in
  SKILL.md's words (:data:`SECTION_REQUEST`); the commands it holds are not
  listed again, and no reason asks for a ``### Next Steps`` section (fix round
  28, live run 12, Claude Code 03: it asked for both, and the resent report
  added a heading of its own above the section).
* The interactive UI labels a block "Stop hook error occurred" (a
  ``stop-hook-error`` notification in a ``stream-json`` stream). Measured on
  racing run 5 (Claude Code 2.1.289): it fired only in the round this hook
  blocked, while the hook's own record read exit 0, empty stderr, the one
  JSON line on stdout and ``outcome: success`` — so the label is Claude
  Code's word for a block, not a fault in this hook, and no documented
  output field turns it off.

**Advisory, so every error passes silently.** An unreadable or malformed
transcript (a malformed line before the one still being written), a bad
argument, a missing file: exit 0 and no output. A check that
could break a session, or block on data it could not read, is worse than the
miss it exists to catch.

**Stdout is the hook's decision channel.** Called through the dispatcher, the
decision line is followed by the dispatcher's own ``MULTI_LLM_RESULT`` line,
and Claude Code parses hook stdout as JSON only when the whole of it is JSON.
So the decision is printed on a line of its own that starts with
:data:`DECISION_PREFIX`, and ``hooks/report-check.sh`` passes that line alone
through (``grep '^{"decision"'``). Nothing else here prints to stdout.

Import is side-effect free: argparse and all I/O live inside :func:`main`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set

try:
    from .stream_bootstrap import bootstrap_streams
except ImportError:  # direct script invocation
    from stream_bootstrap import bootstrap_streams  # type: ignore

#: The block's four line kinds (plans/next-phase-command.md §2.2(2)). The
#: trailing space is part of each command prefix: ``[NEXT_COMMAND] `` must never
#: match ``[NEXT_COMMAND_OPTIONAL] ``.
NEXT_COMMAND = "[NEXT_COMMAND] "
NEXT_COMMAND_OPTIONAL = "[NEXT_COMMAND_OPTIONAL] "
NEXT_COMMAND_OPTIONAL_WHY = "[NEXT_COMMAND_OPTIONAL_WHY] "
#: A stopped implement's answers (``util next-command``, fix round 14; each
#: alone after the combined one since fix round 20), after the primary and
#: any optional entries, each below its why line.
NEXT_COMMAND_ANSWERS = "[NEXT_COMMAND_ANSWERS] "
NEXT_COMMAND_ANSWERS_WHY = "[NEXT_COMMAND_ANSWERS_WHY] "
WORKFLOW_COMPLETE = "[WORKFLOW_COMPLETE]"
#: One per implement task the run deferred, under ``[WORKFLOW_COMPLETE]`` or
#: after a command block's commands: ``<id> <title>``
#: (``next_phase.MANUAL_TASK_MARKER``).
MANUAL_TASK = "[MANUAL_TASK] "
#: After those lines: how the user records them done
#: (``next_phase.MANUAL_TASK_NOTE_MARKER``). Quoted in a block's reason.
MANUAL_TASK_NOTE = "[MANUAL_TASK_NOTE] "
#: After the note: the command that records them done, alone
#: (``next_phase.MANUAL_TASK_COMMAND_MARKER``, fix round 22). A command the
#: report carries in a fenced block like the block's others.
MANUAL_TASK_COMMAND = "[MANUAL_TASK_COMMAND] "

#: The lines around the section ``util next-command`` prints below the block
#: (``next_phase.NEXT_STEP_MARKDOWN_MARKER``, fix round 24). Every line
#: between them is the section's, never a marker line of the block.
NEXT_STEP_MARKDOWN = "[NEXT_STEP_MARKDOWN]"
NEXT_STEP_MARKDOWN_END = "[NEXT_STEP_MARKDOWN_END]"

#: The composite's continuation, the last line ``util improve-steps`` prints
#: (``improve_steps.RERUN_MARKER``; plans/improve-plan-and-improve-code.md
#: §2.4). Read as a block only in a planner call's result (:func:`last_block`).
IMPROVE_RERUN = "[IMPROVE_RERUN] "

#: A Bash command that ran the planner: ``multi_llm.py util improve-steps``,
#: either word quoted or not. A ``grep`` or a ``Read`` of a file quoting the
#: line, and ``util instructions improve-plan`` printing the core, are not.
_PLANNER_RE = re.compile(
    r"multi_llm\.py[\"']?\s+[\"']?util[\"']?\s+[\"']?improve-steps\b")

#: What the report says when the block is ``[WORKFLOW_COMPLETE]`` (§2.3).
COMPLETE_SENTENCE = "Workflow complete."

#: Every decision line starts with this, so the hook script can select it from
#: a stdout that also carries the dispatcher's result line.
DECISION_PREFIX = '{"decision"'

#: A fence opener: three or more backticks or tildes. Any indentation, so a
#: fence nested in a list item counts; the info string (```bash) is ignored.
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")

#: How long a hook waits for Claude Code to write a turn's last entries to the
#: transcript, and how often it looks (fix round 27, :func:`settled_turn`).
#: Claude Code 2.1.293 wrote them 0.1-0.2 s after the hook started, measured
#: against a localhost stub; the hook scripts' own timeout is 30 s.
SETTLE_BUDGET_S = 2.0
SETTLE_STEP_S = 0.1

#: The ``system`` entry Claude Code writes after a ``Stop`` hook ran: a reply
#: it follows was an earlier ``Stop``'s, never the one being checked.
STOP_HOOK_SUMMARY = "stop_hook_summary"

#: The tools whose result is a subagent's own words, never a phase's output
#: (fix round 27): a block quoted in one is not a block the report owes, nor
#: does it end ``util wakeup-check``'s hold.
SUBAGENT_TOOLS = ("Agent", "Task", "SendMessage")


class _Unreadable(Exception):
    """The transcript or hook input could not be read as what it claims to be."""


class _ArgumentError(Exception):
    """argparse refused the command line; the caller passes silently."""


class _QuietParser(argparse.ArgumentParser):
    """An ``ArgumentParser`` whose usage error raises instead of exiting 2.

    A hook must never print a usage error into the session or exit non-zero,
    so a bad command line becomes a silent pass. ``--help`` still prints and
    exits 0, as it does for every other util command.
    """

    def error(self, message: str):  # type: ignore[override]
        raise _ArgumentError(message)


# ---------------------------------------------------------------------------
# The block
# ---------------------------------------------------------------------------

class Block:
    """One ``[NEXT_COMMAND]`` block, or one ``[WORKFLOW_COMPLETE]`` line."""

    def __init__(self, complete: bool, command: Optional[str] = None,
                 continuation: bool = False):
        self.complete = complete
        self.command = command
        #: An ``[IMPROVE_RERUN]`` line: a native composite's own continuation
        #: (Fable review 2026-10-09), held over a later inner phase's block.
        self.continuation = continuation
        #: ``(why, command)`` pairs, in the order the block printed them.
        self.optional: List[tuple] = []
        #: ``(why, command)`` pairs: the answers lines, in the order printed.
        self.answers: List[tuple] = []
        #: ``(id, title)`` pairs the block names: the manual tasks the user
        #: still owes (``title`` may be ``""``), on either kind of block.
        self.manual: List[tuple] = []
        #: The ``[MANUAL_TASK_NOTE]`` text after them, when printed.
        self.note: Optional[str] = None
        #: The ``[MANUAL_TASK_COMMAND]`` after the note, when printed.
        self.manual_command: Optional[str] = None
        #: The ready section ``util next-command`` printed below the block,
        #: between ``[NEXT_STEP_MARKDOWN]`` and ``[NEXT_STEP_MARKDOWN_END]``
        #: (fix round 26), when it printed one.
        self.section: Optional[str] = None

    def section_commands(self) -> List[str]:
        """Every command the ready section fences, in its order: each
        non-blank line inside one of its fenced blocks (``fenced_command``
        puts each command alone in its own)."""
        if not self.section:
            return []
        return [line for line in _fenced_line_list(self.section) if line]

    def commands(self) -> List[str]:
        """Every command the report has to carry: the primary one first, the
        manual tasks' close command after the block's others, then any
        command the ready section fences that no marker line printed (fix
        round 26: the section is what the report copies, so every command it
        fences is held to the report). A complete block's marker command is
        the manual one alone (its primary is the sentence)."""
        manual = [self.manual_command] if self.manual_command else []
        if self.complete or self.command is None:
            listed = manual
        else:
            listed = (
                [self.command]
                + [command for _why, command in self.optional]
                + [command for _why, command in self.answers]
                + manual
            )
        extra: List[str] = []
        for command in self.section_commands():
            if command not in listed and command not in extra:
                extra.append(command)
        return listed + extra


def find_blocks(text: str, continuations: bool = False) -> List[Block]:
    """Every block in one tool result's text, in the order printed.

    A ``[NEXT_COMMAND]`` line or a ``[WORKFLOW_COMPLETE]`` line starts a block;
    each ``[NEXT_COMMAND_OPTIONAL]`` line joins the block started before it in
    the same text, with the why line printed directly above it. An optional
    line with no primary above it is ignored: it is not a block the emitter
    prints. A ready section (``[NEXT_STEP_MARKDOWN]`` …
    ``[NEXT_STEP_MARKDOWN_END]``) belongs to the block printed above it, as
    :attr:`Block.section`; one that never closes is not kept.

    With *continuations* (:func:`last_block`, for a planner call's result) an
    ``[IMPROVE_RERUN]`` line is a block too, a :attr:`Block.continuation` that
    no later line joins. Without it, the default, the line is not read:
    ``util wakeup-check`` reads a phase as over once a block is printed, and
    the planner's line, printed before any phase runs, says nothing of that.
    """
    blocks: List[Block] = []
    current: Optional[Block] = None
    pending_why: Optional[str] = None
    in_section = False
    section_lines: List[str] = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        # The section printed below the block (fix round 24) is the
        # block's own rendering: none of its lines is a marker line.
        if line.rstrip() == NEXT_STEP_MARKDOWN:
            in_section = True
            section_lines = []
            continue
        if line.rstrip() == NEXT_STEP_MARKDOWN_END:
            if in_section and current is not None:
                current.section = "\n".join(section_lines).strip("\n") or None
            in_section = False
            continue
        if in_section:
            section_lines.append(line)
            continue
        if line.startswith(NEXT_COMMAND):
            command = line[len(NEXT_COMMAND):].strip()
            current = Block(complete=False, command=command) if command else None
            if current is not None:
                blocks.append(current)
            pending_why = None
        elif line.rstrip() == WORKFLOW_COMPLETE:
            current = Block(complete=True)
            blocks.append(current)
            pending_why = None
        elif continuations and line.startswith(IMPROVE_RERUN):
            # The planner prints it last and alone: nothing joins it.
            command = line[len(IMPROVE_RERUN):].strip()
            if command:
                blocks.append(Block(complete=False, command=command,
                                    continuation=True))
            current = None
            pending_why = None
        elif line.startswith(NEXT_COMMAND_OPTIONAL_WHY):
            pending_why = line[len(NEXT_COMMAND_OPTIONAL_WHY):].strip()
        elif line.startswith(NEXT_COMMAND_ANSWERS_WHY):
            pending_why = line[len(NEXT_COMMAND_ANSWERS_WHY):].strip()
        elif line.startswith(NEXT_COMMAND_ANSWERS):
            command = line[len(NEXT_COMMAND_ANSWERS):].strip()
            if current is not None and not current.complete and command:
                current.answers.append((pending_why, command))
            pending_why = None
        elif line.startswith(NEXT_COMMAND_OPTIONAL):
            command = line[len(NEXT_COMMAND_OPTIONAL):].strip()
            if current is not None and not current.complete and command:
                current.optional.append((pending_why, command))
            pending_why = None
        elif line.startswith(MANUAL_TASK_NOTE):
            note = line[len(MANUAL_TASK_NOTE):].strip()
            if current is not None and current.manual and note:
                current.note = note
        elif line.startswith(MANUAL_TASK_COMMAND):
            command = line[len(MANUAL_TASK_COMMAND):].strip()
            if current is not None and current.manual and command:
                current.manual_command = command
        elif line.startswith(MANUAL_TASK):
            task_id, _, title = line[len(MANUAL_TASK):].strip().partition(" ")
            if current is not None and task_id:
                current.manual.append((task_id, title.strip()))
    return blocks


# ---------------------------------------------------------------------------
# The message
# ---------------------------------------------------------------------------

def fenced_lines(text: str) -> Set[str]:
    """Every line inside a fenced code block of *text*, whitespace-stripped.

    CommonMark's closing rule: the same fence character, at least as many of
    it, and nothing else on the line. An unclosed fence runs to the end of the
    message, as it renders. A backtick fence whose info string holds a
    backtick is not a fence (CommonMark again), which keeps an inline
    ```` ```code``` ```` span from opening one.
    """
    return set(_fenced_line_list(text))


def _fenced_line_list(text: str) -> List[str]:
    """:func:`fenced_lines` in the order the lines appear, repeats kept."""
    lines: List[str] = []
    fence: Optional[str] = None
    for raw in text.splitlines():
        if fence is None:
            match = _FENCE_RE.match(raw)
            if match is None:
                continue
            marker, info = match.group(1), match.group(2)
            if marker[0] == "`" and "`" in info:
                continue
            fence = marker
            continue
        stripped = raw.strip()
        if (
            stripped
            and set(stripped) == {fence[0]}
            and len(stripped) >= len(fence)
        ):
            fence = None
            continue
        lines.append(stripped)
    return lines


def missing_commands(block: Block, message: str) -> List[str]:
    """The block's commands that *message* does not carry, in block order.

    For a ``[WORKFLOW_COMPLETE]`` block the "commands" are the sentence, missing
    when the message does not contain it. On either kind of block, the id of
    each manual task it names follows, missing when the message does not name
    it as a word of its own (``T011``, not ``T0110``): a final message that
    lists them passes, and one that drops them does not.
    """
    missing = (
        [] if not block.complete or COMPLETE_SENTENCE in message
        else [COMPLETE_SENTENCE]
    )
    carried = fenced_lines(message)
    for command in block.commands():
        if command not in carried and command not in missing:
            missing.append(command)
    for task_id in missing_manual_tasks(block, message):
        if task_id not in missing:
            missing.append(task_id)
    return missing


def missing_manual_tasks(block: Block, message: str) -> List[str]:
    """The ids of *block*'s manual tasks that *message* does not name."""
    return [
        task_id for task_id, _title in block.manual
        if re.search(rf"(?<![\w]){re.escape(task_id)}(?![\w])", message) is None
    ]


#: What every block reason asks for (fix round 14, racing run 5 Claude Code
#: 08): the reply after a block is what the run's final message becomes, and
#: a reason that asked for "your report's `### Next Steps` section" got back
#: that section alone, so the run's result lost the report it had written
#: (what was fixed, skipped and left out). The whole report is asked for again.
WHOLE_REPORT = (
    "Your next reply replaces your last message as the run's final message, "
    "so send your whole report again — everything your last message said "
    "(what ran, what changed, what was skipped, failed or left out, the files "
    "and the counts), unchanged — and end it with"
)


def _manual_list(block: Block) -> str:
    """The block's manual tasks as a list, then its note when it printed one,
    and on a complete block the command after it, fenced (a command block
    lists it among its commands)."""
    listed = "\n".join(
        f"- {task_id} {title}".rstrip() for task_id, title in block.manual
    )
    if block.note:
        listed += (
            "\n\nThen this note, verbatim, and the command after it alone in its "
            "own fenced block (the user's to type, never yours to run):\n\n"
            + block.note
        )
        if block.complete and block.manual_command:
            listed += f"\n\n```\n{block.manual_command}\n```"
    return listed


def _tasks_noun(ids: Sequence[str]) -> str:
    return ("task " if len(ids) == 1 else "tasks ") + ", ".join(ids)


#: How a ready section is printed (``modes.READY_SECTION_RULE``, word for
#: word: the rule every route and SKILL.md carry, held to that constant by
#: ``tests/test_block_reason_says_one_thing.py``; this module imports nothing
#: of the skill's own).
READY_SECTION_RULE = (
    "Copy it word for word, never wrapped in a fenced block of your own (its "
    "commands are fenced already), and say none of it twice: its whys, notes, "
    "manual tasks and \"Workflow complete.\" appear only in it, never above it."
)

#: How a block reason asks for the section the lookup printed (fix round 26,
#: live run 11, Claude Code 04: the reply the run ended on carried none of
#: the section's commands). It finishes :data:`WHOLE_REPORT`'s sentence and
#: the section follows it verbatim. Fix round 28 (live run 12, Claude Code
#: 03): the reason asked for "its `### Next Steps` section, with each
#: command in its own fenced code block …" and then for the section "printed
#: as given …, no caption of your own", and the resent report put a
#: `### Next Steps` heading of its own above the section. A reason with a
#: section now says how the report ends once, in SKILL.md's words.
SECTION_REQUEST = (
    "the ready section the lookup printed between its "
    f"{NEXT_STEP_MARKDOWN} and {NEXT_STEP_MARKDOWN_END} lines, copied as it is "
    "(its words and order, each command alone in its fenced block, each why "
    "and note plain text, the manual tasks it lists included, no caption of "
    "your own), in place of any next step your last message gave. "
    f"{READY_SECTION_RULE} Do not rebuild, shorten, re-quote or "
    "rephrase a command, and do not run one: each is for the user to type. "
    "The section is:"
)


def block_reason(block: Block, missing: Sequence[str]) -> str:
    """The text the model reads when the hook blocks its stop."""
    if block.continuation:
        return _continuation_reason(block)
    if block.section:
        return _section_reason(block, missing)
    return _block_reason(block, missing)


def _continuation_reason(block: Block) -> str:
    """A native composite's continuation the report lacks (Fable review
    2026-10-09). The command is the only thing held; the reason also says
    why an inner phase's block is no substitute, since the turn that ends a
    stopped run holds review-plan's (or review-code's, or review-commits')
    bare apply command, which is the wrong one to give."""
    marker = IMPROVE_RERUN.strip()
    return "\n\n".join([
        "multi-llm report check: this --improve-plan, --improve-code or "
        "--improve-commits run's "
        f"next step is the {marker} command its `util improve-steps` call "
        "printed, and your final message does not carry it exactly. No "
        "closing lookup came after it (a stopped run makes none), and the "
        "[NEXT_COMMAND] blocks its phases printed are each phase's own "
        "standalone next step, never this run's: do not give one in its place.",
        f"{WHOLE_REPORT} the way to continue: any answer the stopped phase "
        "named (its own command, as the stop gave it), then the command below "
        "alone in its own fenced code block, copied character for character "
        f"from the {marker} line. Do not rebuild, shorten, re-quote or "
        "rephrase it, and do not run it: it is for the user to type.",
        "Missing command:",
        f"```\n{block.command}\n```",
    ])


def _section_reason(block: Block, missing: Sequence[str]) -> str:
    """A block with a ready section: what the report lacks, then the section
    to end the whole report with (:data:`SECTION_REQUEST`), and no other
    description of the report's end. The section already holds every command,
    why, manual task and note in their order, so nothing of it is said twice."""
    commands = block.commands()
    lost = [item for item in missing if item in commands]
    manual_ids = {task_id for task_id, _title in block.manual}
    dropped = [item for item in missing if item in manual_ids]
    noun = "command" if len(lost) == 1 else "commands"
    if block.complete:
        printed = WORKFLOW_COMPLETE
    else:
        printed = "the next step"
    if block.manual:
        printed += (
            " with the tasks implement deferred to the user" if block.complete
            else " and, after it, the tasks implement deferred to the user")
    lacks = []
    if block.complete and COMPLETE_SENTENCE in missing:
        lacks.append(f'does not say "{COMPLETE_SENTENCE}"')
    if lost:
        lacks.append(f"does not carry the {noun} below exactly")
    if dropped:
        lacks.append(f"does not name the {_tasks_noun(dropped)}")
    if not lacks:  # pragma: no cover - every missing item is one of the three
        lacks.append("does not carry it")
    parts = [
        "multi-llm report check: the last phase result in this run printed "
        f"{printed}, and your final message "
        + (", ".join(lacks[:-1]) + " and " if len(lacks) > 1 else "")
        + f"{lacks[-1]}."
    ]
    if lost:
        parts.append(f"Missing {noun}:")
        parts.extend(f"```\n{command}\n```" for command in lost)
    parts.append(f"{WHOLE_REPORT} {SECTION_REQUEST}")
    parts.append(block.section or "")
    return "\n\n".join(parts)


def _block_reason(block: Block, missing: Sequence[str]) -> str:
    if block.complete:
        if not block.manual:
            return (
                "multi-llm report check: the last phase result in this run printed "
                f"{WORKFLOW_COMPLETE}, and your final message does not say "
                f'"{COMPLETE_SENTENCE}". {WHOLE_REPORT} the words '
                f'"{COMPLETE_SENTENCE}" and no multi-llm command.'
            )
        # The reply replaces the final message, so it is told the whole
        # section again, the tasks it already named included.
        lacks = []
        if COMPLETE_SENTENCE in missing:
            lacks.append(f'does not say "{COMPLETE_SENTENCE}"')
        manual_ids = {task_id for task_id, _title in block.manual}
        dropped = [item for item in missing if item in manual_ids]
        if dropped:
            lacks.append(f"does not name the {_tasks_noun(dropped)}")
        if any(item in block.commands() for item in missing):
            lacks.append(
                "does not carry the command that records them done alone in a "
                "fenced block")
        return (
            "multi-llm report check: the last phase result in this run printed "
            f"{WORKFLOW_COMPLETE} with the tasks implement deferred to the "
            f"user, and your final message {' and '.join(lacks)}. {WHOLE_REPORT} "
            f'the words "{COMPLETE_SENTENCE}" and then each of these '
            "tasks, its id and title, as the user's to do, with no "
            + ("other " if block.note else "")
            + "multi-llm command:\n\n" + _manual_list(block)
        )
    commands = block.commands()
    lost = [item for item in missing if item in commands]
    dropped = [item for item in missing if item not in commands]
    tasks_after = (
        "After the commands, list each of these tasks implement deferred to "
        "the user, its id and title, as the user's to do; never write "
        f'"{COMPLETE_SENTENCE}" for them: while a command is next, the '
        "workflow goes on."
    )
    if not lost:
        # Fix round 17: every command is there and the tasks after them are
        # not. The reply replaces the final message, so it carries the
        # commands again too.
        parts = [
            "multi-llm report check: the last phase result in this run printed "
            "the next step and, after it, the tasks implement deferred to the "
            f"user, and your final message does not name the {_tasks_noun(dropped)}. "
            f"{WHOLE_REPORT} the next step: each command "
            "below in its own fenced code block, copied character for character "
            "as before. " + tasks_after,
        ]
        for command in commands:
            parts.append(f"```\n{command}\n```")
        parts.append(_manual_list(block))
        return "\n\n".join(parts)
    noun = "command" if len(lost) == 1 else "commands"
    parts = [
        "multi-llm report check: the last phase result in this run printed "
        f"the next step, and your final message does not carry the {noun} "
        f"below exactly. {WHOLE_REPORT} the next step: "
        "each command in its own fenced code block, "
        "copied character for character from its [NEXT_COMMAND], "
        "[NEXT_COMMAND_OPTIONAL], [NEXT_COMMAND_ANSWERS] or "
        "[MANUAL_TASK_COMMAND] line (optional "
        "commands after the main one, under the line \"Optional, before "
        "that:\", each with its why; the answers commands last, each with its why). "
        "Do not "
        "rebuild, shorten, re-quote or rephrase a command, and do not run it: "
        "it is for the user to type.",
        f"Missing {noun}:",
    ]
    for command in lost:
        parts.append(f"```\n{command}\n```")
    # The reply replaces the final message, so it has to carry the commands
    # the report already had right as well.
    others = [command for command in commands if command not in lost]
    if others:
        parts.append(
            "Carry the block's other "
            + ("command" if len(others) == 1 else "commands")
            + " in the reply too, unchanged:"
        )
        for command in others:
            parts.append(f"```\n{command}\n```")
    if block.manual:
        parts.append(tasks_after)
        parts.append(_manual_list(block))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# The transcript
# ---------------------------------------------------------------------------

def _content(entry: Dict[str, Any]) -> Any:
    message = entry.get("message")
    if not isinstance(message, dict):
        return None
    return message.get("content")


#: The ``origin.kind`` of a prompt the user typed in an interactive session
#: (a headless ``claude -p`` prompt carries no ``origin`` at all). Every other
#: kind is the harness speaking: ``task-notification`` (a background task's
#: completion, a plain string entry that is not ``isMeta``), ``peer``,
#: ``coordinator``, ``auto-continuation`` (those three ``isMeta``). Read off
#: Claude Code 2.1.293 transcripts, 2026-10-08.
TYPED_ORIGIN_KIND = "human"


def _is_real_prompt(entry: Dict[str, Any]) -> bool:
    """A user entry the user typed: it starts a run of the conversation.

    Not a tool-result carrier, not an ``isMeta`` entry (a loaded skill body, a
    hook's feedback, a scheduled wakeup's prompt), and not one the harness
    sent: an entry whose ``origin.kind`` is anything but
    :data:`TYPED_ORIGIN_KIND` (fix round 26, live run 11: Claude Code runs a
    phase's subagents in the background, so one phase spans several turns,
    each opened by a ``task-notification`` entry, and the ready section is
    printed in one of them while the run ends on another).
    """
    if entry.get("type") != "user":
        return False
    if entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    origin = entry.get("origin")
    if isinstance(origin, dict) and origin.get("kind") not in (None, TYPED_ORIGIN_KIND):
        return False
    content = _content(entry)
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(
            isinstance(block, dict) and block.get("type") == "text"
            for block in content
        )
    return False


def _tool_result_texts(
    entry: Dict[str, Any], skip: Iterable[str] = (),
) -> Iterable[str]:
    """The text of every ``tool_result`` block a user entry carries, in order,
    but those answering a call whose id is in *skip*."""
    for _call_id, text in _tool_results(entry, skip):
        yield text


def _tool_results(
    entry: Dict[str, Any], skip: Iterable[str] = (),
) -> Iterable[tuple]:
    """``(tool_use_id, text)`` for :func:`_tool_result_texts`' results."""
    content = _content(entry)
    if not isinstance(content, list):
        return
    skipped = set(skip)
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            continue
        call_id = str(block.get("tool_use_id") or "")
        if call_id in skipped:
            continue
        inner = block.get("content")
        if isinstance(inner, str):
            yield call_id, inner
        elif isinstance(inner, list):
            texts = [
                part.get("text", "")
                for part in inner
                if isinstance(part, dict) and part.get("type") == "text"
                and isinstance(part.get("text"), str)
            ]
            if texts:
                yield call_id, "\n".join(texts)


def _assistant_text(entry: Dict[str, Any]) -> List[str]:
    content = _content(entry)
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    return [
        block["text"]
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]


def read_turn(path: Path, partial_tail: bool = False) -> List[Dict[str, Any]]:
    """The transcript entries since the last prompt the user typed, in file
    order (:func:`_is_real_prompt`): the whole of a headless ``claude -p``
    session, task-notification turns and wakeup turns included.

    Read from the end, so a long session parses only its last run. A line
    inside that stretch that is not a JSON object makes the whole transcript
    unreadable (:class:`_Unreadable`): the check does not guess at a turn it
    cannot see in full. With *partial_tail* (:func:`settled_turn` once its
    wait ran out: both hooks read the transcript while the session is writing
    it), a last line with no newline after it is a write in progress and is
    left out.
    """
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise _Unreadable(str(exc)) from exc
    lines = data.splitlines()
    if partial_tail and lines and not data.endswith((b"\n", b"\r")):
        lines.pop()
    turn: List[Dict[str, Any]] = []
    for raw in reversed(lines):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise _Unreadable(f"not JSON: {exc}") from exc
        if not isinstance(entry, dict):
            raise _Unreadable("a transcript line is not a JSON object")
        if entry.get("isSidechain"):
            continue
        if _is_real_prompt(entry):
            break
        turn.append(entry)
    turn.reverse()
    return turn


def settled_turn(
    path: Path,
    settled: Optional[Callable[[List[Dict[str, Any]]], bool]],
    budget: Optional[float] = None,
    step: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """:func:`read_turn` once Claude Code has written what the hook waits for
    (fix round 27).

    *settled* says whether a turn read off the file holds it; ``None`` means
    the hook input names nothing to wait for, and the file then counts as
    settled once its size held for one *step* with its last line complete.
    The file is read every *step* seconds (:data:`SETTLE_STEP_S`) for at most
    *budget* seconds (:data:`SETTLE_BUDGET_S`), a missing file and a last
    line still being written included; the first read that is settled
    returns at once. Past the budget the turn is read as it stands, a last
    line with no newline after it left out. A malformed line before that one
    still raises :class:`_Unreadable`: the caller passes.
    """
    budget = SETTLE_BUDGET_S if budget is None else budget
    step = SETTLE_STEP_S if step is None else step
    deadline = time.monotonic() + max(budget, 0.0)
    last_size: Optional[int] = None
    while True:
        try:
            size: Optional[int] = path.stat().st_size
        except OSError:
            size = None
        # A file that has not grown since the last look cannot have become
        # settled; it is parsed again only once it changed.
        if size is not None and (settled is None or size != last_size):
            try:
                turn = read_turn(path)
            except _Unreadable:
                size = None
            else:
                if settled is not None:
                    if settled(turn):
                        return turn
                elif size == last_size:
                    return turn
        last_size = size
        if time.monotonic() >= deadline:
            break
        time.sleep(step)
    return read_turn(path, partial_tail=True)


def reply_on_file(last_assistant_message: str) -> Callable[[List[Dict[str, Any]]], bool]:
    """A :func:`settled_turn` test: the reply the ``Stop`` hook input names
    is the transcript's newest one.

    True when the newest assistant entry with text after the run's last user
    entry ends on that text (whitespace around it aside), with no
    ``stop_hook_summary`` after it: Claude Code writes one after every
    ``Stop`` hook, so a reply it follows is an earlier ``Stop``'s, even one
    worded the same.
    """
    wanted = last_assistant_message.strip()

    def settled(turn: List[Dict[str, Any]]) -> bool:
        for entry in reversed(turn):
            kind = entry.get("type")
            if kind == "system" and entry.get("subtype") == STOP_HOOK_SUMMARY:
                return False
            if kind == "user":
                return False
            if kind == "assistant":
                texts = _assistant_text(entry)
                if texts:
                    return texts[-1].strip() == wanted
        return False

    return settled


def subagent_call_ids(turn: Sequence[Dict[str, Any]]) -> Set[str]:
    """The ids of the turn's calls whose result is a subagent's own words
    (:data:`SUBAGENT_TOOLS`)."""
    found: Set[str] = set()
    for entry in turn:
        if entry.get("type") != "assistant":
            continue
        content = _content(entry)
        if not isinstance(content, list):
            continue
        for block in content:
            if (isinstance(block, dict) and block.get("type") == "tool_use"
                    and block.get("name") in SUBAGENT_TOOLS):
                found.add(str(block.get("id") or ""))
    return found


def planner_call_ids(turn: Sequence[Dict[str, Any]]) -> Set[str]:
    """The ids of the turn's Bash calls that ran ``util improve-steps``
    (:data:`_PLANNER_RE`): the only results whose ``[IMPROVE_RERUN]`` line is
    the run's continuation (Fable review 2026-10-09)."""
    found: Set[str] = set()
    for entry in turn:
        if entry.get("type") != "assistant":
            continue
        content = _content(entry)
        if not isinstance(content, list):
            continue
        for block in content:
            if not (isinstance(block, dict) and block.get("type") == "tool_use"
                    and block.get("name") == "Bash"):
                continue
            tool_input = block.get("input")
            command = (tool_input.get("command")
                       if isinstance(tool_input, dict) else None)
            if isinstance(command, str) and _PLANNER_RE.search(command):
                found.add(str(block.get("id") or ""))
    return found


def last_block(turn: Sequence[Dict[str, Any]]) -> Optional[Block]:
    """The last block printed in the turn's tool results, if any, a block a
    subagent's report quotes left out.

    A native composite's continuation (an ``[IMPROVE_RERUN]`` line in a
    planner call's result, :func:`planner_call_ids`) is a block, and while it
    is the one held, a later block with no ready section does not replace it:
    that is an inner phase's standalone next step, which the composite's core
    never gives (Fable review 2026-10-09). A block with a section, which
    only a ``util next-command`` lookup prints, and a later continuation
    still do. With no planner call in the turn this is the last block, as
    it always was.
    """
    found: Optional[Block] = None
    quoted = subagent_call_ids(turn)
    planners = planner_call_ids(turn)
    for entry in turn:
        if entry.get("type") != "user":
            continue
        for call_id, text in _tool_results(entry, skip=quoted):
            for block in find_blocks(text, continuations=call_id in planners):
                if (found is not None and found.continuation
                        and not block.continuation and block.section is None):
                    continue
                found = block
    return found


def _trailing_assistant(turn: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The assistant entries after the turn's last user entry, newest first:
    the reply the run ends on.

    Every user entry ends the stretch, an ``isMeta`` one included (fix round
    26). A scheduled wakeup's prompt is ``isMeta``, and live run 11's Claude
    Code 04 ended on the reply to one, which carried none of the ready
    section's commands: read together with the report before the wakeup, the
    two passed as one message. The other ``isMeta`` entries end nothing a
    reply spans: a loaded skill body comes before the reply, and the reply
    after a hook's feedback is the message that replaces the one it blocked.
    """
    trailing: List[Dict[str, Any]] = []
    for entry in reversed(turn):
        kind = entry.get("type")
        if kind == "user":
            break
        if kind == "assistant":
            trailing.append(entry)
    return trailing


def ended_on_api_error(turn: Sequence[Dict[str, Any]]) -> bool:
    """Whether the turn ended on an API error the harness synthesized.

    True when the newest trailing assistant entry that carries text, or is an
    API error, is the API error: the model wrote no report there to check.
    """
    for entry in _trailing_assistant(turn):
        if entry.get("isApiErrorMessage"):
            return True
        if _assistant_text(entry):
            return False
    return False


def final_message(turn: Sequence[Dict[str, Any]]) -> Optional[str]:
    """The text of the turn's trailing assistant entries.

    Claude Code writes one transcript entry per content block, so one reply
    can span several entries (thinking, then text). The final message is every
    assistant entry after the turn's last user entry. ``None`` when those
    entries carry no text: the transcript has not written the reply yet, which
    is how it stands when the ``Stop`` hook starts (it is written 0.1-0.2 s
    later on 2.1.293, which is why the hook waits for it, :func:`settled_turn`)
    and how it can still stand once that wait ran out.
    """
    texts: List[str] = []
    for entry in reversed(_trailing_assistant(turn)):
        texts.extend(_assistant_text(entry))
    if not texts:
        return None
    return "\n".join(texts)


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------

def check(
    transcript: Path,
    last_assistant_message: Optional[str] = None,
    settle: bool = False,
) -> Optional[Dict[str, str]]:
    """The hook decision for one turn: ``None`` to pass, else the block object.

    The turn passes when either the transcript's trailing assistant text or
    *last_assistant_message* carries the copy. The second is only the last
    text block of the reply (see the module docstring), so a copy made in an
    earlier block of a split reply is a miss here, once: the hook's next run
    sees ``stop_hook_active`` and passes.

    With *settle* (the hook, reading a live session's transcript), the
    transcript is read once the reply *last_assistant_message* names is on
    file (:func:`settled_turn`); without it, as it stands.

    Raises :class:`_Unreadable` for a transcript it cannot read; the caller
    turns that into a silent pass.
    """
    if settle:
        wanted = (last_assistant_message
                  if isinstance(last_assistant_message, str)
                  and last_assistant_message.strip() else None)
        turn = settled_turn(
            transcript, reply_on_file(wanted) if wanted is not None else None)
    else:
        turn = read_turn(transcript)
    block = last_block(turn)
    if block is None or ended_on_api_error(turn):
        return None
    # A reply this check cannot see is never a miss: with the transcript not
    # yet holding it and no hook-input copy of it, the turn passes.
    messages = [
        message
        for message in (final_message(turn), last_assistant_message)
        if message is not None
    ]
    if not messages:
        return None
    misses = [missing_commands(block, message) for message in messages]
    if any(not missing for missing in misses):
        return None
    # Name what the freshest message lacks: the hook input's, when it has one.
    missing = misses[-1]
    return {"decision": "block", "reason": block_reason(block, missing)}


def _read_hook_input(source: str) -> Dict[str, Any]:
    try:
        if source == "-":
            raw = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else (
                sys.stdin.read().encode("utf-8")
            )
        else:
            raw = Path(source).read_bytes()
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except (OSError, ValueError) as exc:
        raise _Unreadable(f"hook input: {exc}") from exc
    if not isinstance(data, dict):
        raise _Unreadable("hook input is not a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = _QuietParser(
        prog="multi_llm.py util report-check",
        description=(
            "Check that a Claude Code turn's final message carries the next "
            "command a phase result printed ([NEXT_COMMAND] lines), each in a "
            "fenced code block and copied exactly, or says \"Workflow "
            "complete.\" for [WORKFLOW_COMPLETE]. Run by the Claude Code "
            "plugin's Stop hook. Prints nothing on a pass, and one "
            '{"decision": "block", "reason": ...} line on a miss. Always '
            "exits 0: every error is a silent pass."
        ),
    )
    parser.add_argument(
        "--hook-input",
        metavar="PATH",
        help="The Stop hook's input JSON, as a file or - for stdin. Supplies "
             "transcript_path, stop_hook_active and last_assistant_message.",
    )
    parser.add_argument(
        "--transcript",
        metavar="PATH",
        help="The session transcript (JSONL). Takes precedence over the hook "
             "input's transcript_path.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    parser = build_parser()
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except _ArgumentError:
        return 0
    try:
        hook: Dict[str, Any] = {}
        if args.hook_input:
            hook = _read_hook_input(args.hook_input)
            if hook.get("stop_hook_active") is True:
                return 0
        transcript = args.transcript or hook.get("transcript_path")
        if not isinstance(transcript, str) or not transcript:
            return 0
        path = Path(transcript)
        if not path.is_file():
            return 0
        last_message = hook.get("last_assistant_message")
        decision = check(
            path, last_message if isinstance(last_message, str) else None,
            # The hook reads a live session's transcript; a transcript named
            # on the command line alone is read as it stands.
            settle=bool(args.hook_input) and not args.transcript,
        )
    except Exception:  # noqa: BLE001 - advisory: every failure passes silently
        return 0
    if decision is not None:
        sys.stdout.write(json.dumps(decision) + "\n")
        try:
            sys.stdout.flush()
        except (AttributeError, ValueError):  # pragma: no cover - closed stream
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
