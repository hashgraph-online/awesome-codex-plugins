"""Which commit introduced each finding of a commit review.

plans/review-commits.md §2.6, "Attribution is decided by Python, not trusted
from the model". A reviewer is asked for an ``introduced_by`` SHA, but a
model's answer is a reading, not a measurement: it can name a commit outside
the range, a side commit the block never lists, or the commit that wrote the
lines a drifted disk copy put at the cited numbers. So Python decides what it
can measure, and keeps the model's claim only as the checked fallback:

- **Blame, first parent only.** One ``git blame --porcelain --first-parent
  --root -L s,e … <base>..<head> -- <file>`` per file, one ``-L`` per group
  (git merges overlapping ranges). The group goes to the newest blamed
  commit that is in ``commit_range.commits``. ``--first-parent`` makes a line
  a merge brought in blame to that merge, which the block lists; the
  ``<base>..`` side bounds the walk, so an older line blames to the boundary,
  which is not in the list, and the cost follows the range rather than the
  file's age. A root range blames ``<head>`` alone, with ``--root`` keeping
  the root commit's lines attributable.
- **Blame that cannot run never fails the run.** A path absent at ``head``,
  a binary file (a NUL byte in its first 8000 bytes, git's own test), a
  ``line_range`` that starts past the last line (git refuses the whole call
  for one), and a call that fails or passes :data:`BLAME_TIMEOUT_S` each skip
  blame for the groups concerned, which fall back to the model's claim and
  then to ``none``, with one line naming the file and the reason. A range
  that only ends past the last line is clamped, as git does itself.
- **A drifted file's lines are checked first.** A reviewer that read a file
  from disk instead of at ``head`` reports the disk copy's numbers; blamed at
  ``head`` those name whichever commit wrote the lines that sit there, a
  confident wrong answer. So a group on a file in ``commit_range.drifted``,
  or one the shared change test (:func:`git_utils.paths_changed_since`, run
  once per pass) marks now, is blamed only when its ``anchor_text`` occurs at
  ``head`` within the clamped range (whitespace runs collapsed on both sides,
  so it may span lines). Otherwise its source is ``model-drifted``, or
  ``none`` when the claim is refused.
- **The model's claim.** A prefix of 7 or more hex digits matching exactly
  one entry of ``commits``; else a SHA that resolves strictly to a side
  commit of the range (``git rev-list <base>..<head>`` lists it, ``commits``
  does not), mapped to the merge that brought it onto the first-parent chain
  (the oldest entry of ``commits`` that ``git rev-list --ancestry-path
  <sha>..<head>`` lists, over all parents: a side commit that is no parent of
  any first-parent commit, the first of two on a side branch, still maps to
  its merge); anything else is refused.

The outcome is written as two sibling fields of each group,
``introduced_by`` (a full SHA or ``None``) and ``introduced_by_source``
(``blame``, ``model``, ``model-drifted`` or ``none``), never folded into its
title, description or theme, so neither enters the group hash
(``state_manager.generate_group_id``) and two models that disagree about the
commit still group together. Blame output lives in memory for one pass only.

Every git call goes through ``git_utils.git_argv`` (``tests/test_git_utils.py``
fails a runtime git list literal anywhere else).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .commit_range import RangeError, resolve_commit_strict
from .git_utils import _run_git, git_argv, git_path, paths_changed_since, read_at_commit

#: One blame call (one file) may take this long before its groups fall back.
BLAME_TIMEOUT_S = 60

#: git's own binary test reads this many leading bytes for a NUL.
BINARY_SNIFF_BYTES = 8000

#: The shortest hex prefix a model's claim may use.
MIN_CLAIM_HEX = 7

#: The group fields this module writes.
INTRODUCED_BY = "introduced_by"
INTRODUCED_BY_SOURCE = "introduced_by_source"

SOURCE_BLAME = "blame"
SOURCE_MODEL = "model"
SOURCE_MODEL_DRIFTED = "model-drifted"
SOURCE_NONE = "none"
SOURCES: Tuple[str, ...] = (SOURCE_BLAME, SOURCE_MODEL, SOURCE_MODEL_DRIFTED, SOURCE_NONE)

#: The sources a report marks "(model)": the claim, not a measurement.
MODEL_SOURCES: Tuple[str, ...] = (SOURCE_MODEL, SOURCE_MODEL_DRIFTED)

_PORCELAIN_HEADER = re.compile(r"([0-9a-f]{40}|[0-9a-f]{64}) (\d+) (\d+)(?: (\d+))?")
_HEX_CLAIM = re.compile(r"[0-9a-f]{%d,64}" % MIN_CLAIM_HEX)
_FULL_SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


@dataclass
class Outcome:
    """One group's attribution: the commit (full SHA or None) and its source."""

    sha: Optional[str]
    source: str


@dataclass
class AttributionPass:
    """What one pass decided, and what it found on the way.

    ``outcomes`` is per group, in the order the groups were given.
    ``drifted`` holds the (git-form) files of those groups the pass treated
    as drifted: the recorded ``commit_range.drifted`` ones plus those the
    change test marked now; the report's drift badges read it beside the
    record. ``blame_calls`` counts the blame calls made (one per file at most).
    ``skipped`` is ``(file, reason)`` for every file or group whose blame was
    skipped, as the run log names them.
    """

    outcomes: List[Outcome] = field(default_factory=list)
    drifted: Tuple[str, ...] = ()
    blame_calls: int = 0
    skipped: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class _Location:
    file: str
    start: int
    end: int
    anchor: str


# ---------------------------------------------------------------------------
# Reading the groups
# ---------------------------------------------------------------------------


def _members(group: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    members = group.get("suggestions", group.get("issues", []))
    return [m for m in (members or []) if isinstance(m, Mapping)]


def _int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def group_location(group: Mapping[str, Any]) -> Tuple[Optional[str], Optional[Tuple[int, int]], str]:
    """The group's ``(file, (start, end), anchor_text)``, read from its primary
    suggestion as apply-code-fixes reads it (``format_fix_for_output``), or
    from the group itself when it has no suggestions. ``start``/``end`` are
    ``None`` when the ``line_range`` is missing or unusable; a reversed range
    is put in order and a start below 1 is read as 1."""
    members = _members(group)
    source: Mapping[str, Any] = members[0] if members else group
    file = source.get("file")
    file = file.strip() if isinstance(file, str) and file.strip() else None
    anchor = source.get("anchor_text")
    anchor = anchor if isinstance(anchor, str) else ""
    raw = source.get("line_range")
    span: Optional[Tuple[int, int]] = None
    if isinstance(raw, (list, tuple)) and raw:
        start = _int(raw[0])
        end = _int(raw[1]) if len(raw) > 1 else start
        if start is not None and end is not None:
            start, end = max(1, min(start, end)), max(1, max(start, end))
            span = (start, end)
    return file, span, anchor


def _label(group: Mapping[str, Any], index: int) -> str:
    return str(group.get("display_label") or group.get("group_hash") or f"group {index + 1}")


# ---------------------------------------------------------------------------
# Git reads
# ---------------------------------------------------------------------------


def _line_count(data: bytes) -> int:
    """Lines as git counts them: newline-terminated ones plus an unterminated
    last line."""
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def _collapse(text: str) -> str:
    return " ".join(text.split())


def anchor_at_head(anchor: str, lines: Sequence[str], start: int, end: int) -> bool:
    """Whether *anchor* occurs in lines ``start..end`` (1-based, inclusive) of
    the file at ``head``, with runs of whitespace collapsed on both sides; it
    may span lines. An empty anchor never matches."""
    wanted = _collapse(anchor or "")
    if not wanted or start > end or start < 1:
        return False
    window = "\n".join(lines[start - 1:end])
    return wanted in _collapse(window)


def _run_blame(argv: List[str], cwd: Optional[str], timeout: float) -> subprocess.CompletedProcess:
    """The one spawn of a blame call (a seam for tests)."""
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    return subprocess.run(
        argv, capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout, **where,
    )


def parse_porcelain(text: str) -> Dict[int, str]:
    """``{final line number: commit SHA}`` from ``git blame --porcelain``.

    Each blamed line is a header (``<sha> <orig> <final> [<count>]``), then
    key lines on a commit's first appearance, then the line's content behind a
    TAB; only headers are read, and only where a header is expected, so
    content and key text never pass for one."""
    blamed: Dict[int, str] = {}
    expecting_header = True
    for line in text.split("\n"):
        if expecting_header:
            match = _PORCELAIN_HEADER.fullmatch(line)
            if match:
                blamed[int(match.group(3))] = match.group(1)
                expecting_header = False
            continue
        if line.startswith("\t"):
            expecting_header = True
    return blamed


def _blame(file: str, spans: Sequence[Tuple[int, int]], base: Optional[str], head: str,
           cwd: Optional[str]) -> Tuple[Optional[Dict[int, str]], Optional[str]]:
    """Blame *spans* of *file* in one call: ``(lines, None)`` or ``(None, why)``."""
    args: List[str] = ["blame", "--porcelain", "--first-parent", "--root", "--no-textconv"]
    for start, end in spans:
        args += ["-L", f"{start},{end}"]
    args.append(f"{base}..{head}" if base is not None else head)
    args += ["--", file]
    try:
        proc = _run_blame(git_argv(*args, cwd=cwd), cwd, BLAME_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, f"git blame passed {BLAME_TIMEOUT_S}s"
    except (OSError, ValueError) as exc:
        return None, f"git blame could not run ({exc})"
    if proc.returncode != 0:
        stderr = (proc.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        return None, f"git blame failed ({stderr[0] if stderr else f'exit {proc.returncode}'})"
    return parse_porcelain((proc.stdout or b"").decode("utf-8", "replace")), None


class _ClaimResolver:
    """The model's claim, checked against the range (§2.6). The side-commit
    list is read once per pass, and only when a claim needs it."""

    def __init__(self, commits: Sequence[str], base: Optional[str], head: str,
                 cwd: Optional[str]):
        self.commits = list(commits)
        self.commit_set = set(self.commits)
        self.base = base
        self.head = head
        self.cwd = cwd
        self._side: Optional[Set[str]] = None
        self._merges: Dict[str, Optional[str]] = {}

    def _side_commits(self) -> Set[str]:
        if self._side is None:
            spec = f"{self.base}..{self.head}" if self.base is not None else self.head
            stdout, _, rc = _run_git("rev-list", spec, check=False, cwd=self.cwd)
            listed = set(stdout.split()) if rc == 0 else set()
            self._side = listed - self.commit_set
        return self._side

    def _merge_for(self, side: str) -> Optional[str]:
        """The merge that brought *side* onto the first-parent chain: the
        oldest entry of ``commits`` that has *side* as an ancestor.

        ``rev-list --ancestry-path <side>..<head>`` lists every commit that
        descends from *side* and reaches ``head``, over all parents. Along the
        first-parent chain that is a suffix (a commit reaching *side* is
        reached by every later one), so its oldest member in ``commits`` is
        the merge. ``--first-parent`` cannot be added: the walk would then
        leave *side* only through first parents, which reach the merge only
        when *side* is the merge's own second parent, and the older commit of
        a two-commit side branch would be refused. One call per distinct side
        commit a claim names, remembered for the pass."""
        if side not in self._merges:
            stdout, _, rc = _run_git(
                "rev-list", "--ancestry-path", f"{side}..{self.head}",
                check=False, cwd=self.cwd,
            )
            descendants = set(stdout.split()) if rc == 0 else set()
            # `commits` is newest first, so the last one reached is the oldest.
            reached = [sha for sha in self.commits if sha in descendants]
            self._merges[side] = reached[-1] if reached else None
        return self._merges[side]

    def resolve(self, claim: Any) -> Optional[str]:
        """The range commit *claim* names, or None (refused)."""
        if not isinstance(claim, str):
            return None
        tokens = claim.strip().strip("`'\"").split()
        if not tokens:
            return None
        text = tokens[0].strip("`'\".,;:()").lower()
        if not _HEX_CLAIM.fullmatch(text):
            return None
        matches = [sha for sha in self.commits if sha.startswith(text)]
        if len(matches) == 1:
            return matches[0]
        if matches:
            return None  # ambiguous within the range
        try:
            full = resolve_commit_strict(text, cwd=self.cwd or ".")
        except RangeError:
            return None
        if full not in self._side_commits():
            return None  # base, an older commit, or nothing in this range
        return self._merge_for(full)


def _claims(group: Mapping[str, Any]) -> List[Any]:
    """The members' own ``introduced_by`` values, primary first. The group's
    ``introduced_by`` is this module's output, never a claim."""
    return [m.get(INTRODUCED_BY) for m in _members(group) if m.get(INTRODUCED_BY)]


def _log(message: str) -> None:
    print(f"Attribution: {message}")


# ---------------------------------------------------------------------------
# The pass
# ---------------------------------------------------------------------------


def attribute_groups(groups: Sequence[Dict[str, Any]], record: Mapping[str, Any], *,
                     cwd: Optional[str]) -> AttributionPass:
    """Attribute every group to one commit of ``record["commits"]`` or to none,
    writing ``introduced_by`` and ``introduced_by_source`` onto each group.

    *record* is ``state.json``'s ``commit_range``; *cwd* is the repository
    root (the change test needs it). Never raises for a git failure: every
    case that cannot be measured falls back as §2.6 says."""
    commits = [str(entry.get("sha")) for entry in (record.get("commits") or ())
               if isinstance(entry, Mapping) and isinstance(entry.get("sha"), str)
               and _FULL_SHA.fullmatch(str(entry.get("sha")))]
    order = {sha: index for index, sha in enumerate(commits)}   # 0 = newest
    base_value = record.get("base")
    base = str(base_value) if base_value is not None else None
    head = str(record.get("head") or "")
    resolver = _ClaimResolver(commits, base, head, cwd)
    result = AttributionPass()

    locations: Dict[int, _Location] = {}
    by_file: Dict[str, List[int]] = {}
    for index, group in enumerate(groups):
        file, span, anchor = group_location(group)
        if file is None or span is None:
            continue
        name = git_path(file, cwd=cwd)
        locations[index] = _Location(name, span[0], span[1], anchor)
        by_file.setdefault(name, []).append(index)

    recorded = {git_path(path, cwd=cwd) for path in (record.get("drifted") or ())
                if isinstance(path, str) and path}
    files = list(by_file)
    drifted: Set[str] = {name for name in files if name in recorded}
    if files and head:
        drifted |= paths_changed_since(head, files, cwd=cwd)
    result.drifted = tuple(sorted(drifted))

    blamed: Dict[int, str] = {}
    drift_failed: Set[int] = set()
    for name, indexes in by_file.items():
        is_drifted = name in drifted
        data = read_at_commit(head, name, cwd=cwd) if head else None
        if data is None:
            reason = f"absent at {head[:7] or 'head'}"
            _log(f"blame skipped for {name} ({reason}); {len(indexes)} group(s) fall back "
                 f"to the model's claim")
            result.skipped.append((name, reason))
            if is_drifted:
                drift_failed.update(indexes)
            continue
        if b"\0" in data[:BINARY_SNIFF_BYTES]:
            _log(f"blame skipped for {name} (binary file); {len(indexes)} group(s) fall back "
                 f"to the model's claim")
            result.skipped.append((name, "binary file"))
            continue
        total = _line_count(data)
        lines = data.decode("utf-8", "replace").split("\n")
        spans: List[Tuple[int, int, int]] = []
        for index in indexes:
            loc = locations[index]
            end = min(loc.end, total)
            if is_drifted and not anchor_at_head(loc.anchor, lines, loc.start, end):
                why = ("no anchor_text" if not _collapse(loc.anchor)
                       else f"anchor_text not at lines {loc.start}-{loc.end} at {head[:7]}")
                _log(f"{name}: {_label(groups[index], index)} not blamed (file changed on disk "
                     f"since {head[:7]}; {why}); the model's claim is recorded as model-drifted")
                result.skipped.append((name, why))
                drift_failed.add(index)
                continue
            if loc.start > total:
                why = f"line_range starts at {loc.start}, past the last line ({total})"
                _log(f"blame skipped for {name}: {_label(groups[index], index)} ({why}); it "
                     f"falls back to the model's claim")
                result.skipped.append((name, why))
                continue
            spans.append((index, loc.start, end))
        if not spans:
            continue
        result.blame_calls += 1
        blame, why = _blame(name, [(s, e) for _, s, e in spans], base, head, cwd)
        if blame is None:
            _log(f"blame skipped for {name} ({why}); {len(spans)} group(s) fall back to the "
                 f"model's claim")
            result.skipped.append((name, why or "git blame failed"))
            continue
        for index, start, end in spans:
            found = [blame[line] for line in range(start, end + 1)
                     if blame.get(line) in order]
            if found:
                blamed[index] = min(found, key=lambda sha: order[sha])

    for index, group in enumerate(groups):
        if index in blamed:
            outcome = Outcome(blamed[index], SOURCE_BLAME)
        else:
            claim = next((sha for sha in (resolver.resolve(c) for c in _claims(group)) if sha),
                         None)
            if claim is None:
                outcome = Outcome(None, SOURCE_NONE)
            elif index in drift_failed:
                outcome = Outcome(claim, SOURCE_MODEL_DRIFTED)
            else:
                outcome = Outcome(claim, SOURCE_MODEL)
        group[INTRODUCED_BY] = outcome.sha
        group[INTRODUCED_BY_SOURCE] = outcome.source
        result.outcomes.append(outcome)
    return result


def attribute_review_groups(groups: Optional[Sequence[Dict[str, Any]]], state: Any, *,
                            repo_root: Optional[str]) -> Optional[AttributionPass]:
    """The call site's entry: attribute *groups* when the run's state records
    ``commit_range`` (a commit brief's review), else do nothing and return
    None. *state* is a ``StateManager`` or a ``state.json`` mapping."""
    getter = getattr(state, "get", None)
    record = getter("commit_range") if getter is not None else None
    if not isinstance(record, Mapping):
        return None
    group_list = [g for g in (groups or []) if isinstance(g, dict)]
    try:
        result = attribute_groups(group_list, record, cwd=repo_root)
    except Exception as exc:  # noqa: BLE001 - attribution never fails the run (§2.6)
        _log(f"skipped ({type(exc).__name__}: {exc}); every group is left unattributed")
        result = AttributionPass()
        for group in group_list:
            group[INTRODUCED_BY], group[INTRODUCED_BY_SOURCE] = None, SOURCE_NONE
            result.outcomes.append(Outcome(None, SOURCE_NONE))
        return result
    counts: Dict[str, int] = {}
    for outcome in result.outcomes:
        counts[outcome.source] = counts.get(outcome.source, 0) + 1
    if result.outcomes:
        summary = ", ".join(f"{counts[s]} {s}" for s in SOURCES if counts.get(s))
        _log(f"{len(result.outcomes)} group(s) attributed: {summary}")
    return result


def commits_by_sha(record: Optional[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    """``{sha: commits[] entry}`` from a ``commit_range`` record: the subjects a
    report renders come from here, with no git call (§2.6 "Rendering")."""
    table: Dict[str, Mapping[str, Any]] = {}
    for entry in (record or {}).get("commits") or ():
        if isinstance(entry, Mapping) and isinstance(entry.get("sha"), str):
            table[entry["sha"]] = entry
    return table
