"""Read-only audit of one ``codex exec --json`` stream (plan §4.2, option B).

Given the **full** in-memory stdout of one codex attempt, answer: could this
attempt have written to the working tree? The answer turns a porcelain delta
into a pass, so the classifier **fails closed**: it accepts only what it fully
recognises and rejects everything else, including anything it cannot parse.

Every fact below was captured from codex-cli 0.156.1 (offline, against a
localhost Responses stub), from the persisted log of run ``0c477c4d``, or from
the live web-search capture of 2026-09-25; see
``tests/fixtures/codex/0.156.1/SCHEMA.md``.

Code mode (``gpt-6-astra``): the model's ``exec`` JavaScript cell itself emits
**no** item, but every nested tool it calls does: ``tools.apply_patch`` →
``file_change``, ``tools.exec_command`` → ``command_execution``,
``tools.web__run`` → ``web_search``, an MCP tool → ``mcp_tool_call`` (live
capture ``code_mode_writes.jsonl``, ``web_search_code_mode.jsonl``,
``code_mode_mcp.jsonl``). The cell's V8 isolate has no file system or
network of its own, so the nested items are the whole action record.

Stream rules (step 5):

- The stream must contain ``turn.completed``. A ``turn.failed``, a top-level
  event type outside the known set, or a line that is not a JSON object fails.
- Every ``item.started`` / ``item.updated`` must be matched by an
  ``item.completed`` with the same id. An unmatched one is an unfinished action
  and fails: that is exactly how a long-running exec session looks when codex
  ends the turn with it still open, and a session's ``write_stdin`` input never
  appears on the stream at all.
- Completed items are classified by type:

  - ``agent_message``, ``reasoning``, ``error`` (codex's non-fatal notices such
    as "Model metadata … not found"): inert.
  - ``command_execution``: its ``command`` (a string, ``/bin/bash -lc '<cmd>'``)
    must pass :func:`classify_command`.
  - ``file_change`` (apply_patch, whether called as the freeform tool or as
    ``apply_patch <<EOF`` through the shell): always a write.
  - ``mcp_tool_call``: fails unless ``(server, tool)`` is on
    :data:`READONLY_MCP_TOOLS`, which starts empty. This plugin's own MCP tool
    on the codex host is deliberately not on it.
  - ``collab_tool_call`` (``spawn_agent`` and friends): fails. The capture shows
    a spawned sub-agent's own tool items never reach the parent's stream, so a
    sub-agent that wrote is invisible here.
  - ``web_search``: a web search run over the network, never locally. The live
    §6.2 capture (2026-09-25) shows two producers, and neither has a local
    execution path: the hosted ``web_search`` Responses tool (the server runs
    it and sends a ``web_search_call`` output item) and, in code mode, the
    nested ``tools.web__run`` call (a codex extension item ``web.search``).
    Inert when ``action.type`` is on :data:`WEB_SEARCH_INERT_ACTIONS` and
    ``results`` is absent (the hosted route never sends it) or a list whose
    every ``type`` is on :data:`WEB_SEARCH_INERT_RESULT_TYPES`. An action or
    result type outside those lists still fails closed.
  - ``todo_list`` and every other type: "could have written" until a fixture
    shows otherwise.

- A known tool item whose expected fields are missing or of the wrong type
  fails; it is never skipped.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from typing import Dict, List, Optional, Sequence, Tuple

from ..readonly_audit import AuditVerdict

#: Top-level event types codex 0.156.1 emits (binary tag table + captures).
KNOWN_EVENTS = frozenset({
    "thread.started", "turn.started", "turn.completed", "turn.failed",
    "item.started", "item.updated", "item.completed", "error",
})

#: Item types that carry no tool action. ``error`` is codex's nested notice item
#: (``item.completed`` with ``type: error``), seen on every stub capture.
INERT_ITEM_TYPES = frozenset({"agent_message", "reasoning", "error"})

#: ``(server, tool)`` pairs of MCP tools known to be read-only. Starts empty
#: (plan §4.2 step 5): an MCP tool is the runner's business, not ours.
READONLY_MCP_TOOLS: frozenset = frozenset()

#: ``web_search.action.type`` values classified inert, each seen in the live
#: §6.2 capture (``tests/fixtures/codex/0.156.1/web_search_*.jsonl``):
#: ``search`` (``query``/``queries``), ``open_page`` (``url``) and
#: ``find_in_page`` (``url``, ``pattern``) name a query or a public URL, never a
#: local path. ``other`` is codex's own placeholder: every ``item.started``
#: carries it, and on a completed item it is codex's catch-all for a server
#: action it cannot name (the stub probe sent ``not_a_known_action`` and codex
#: emitted ``other`` with the fields dropped). None of the four runs anything
#: locally. A value outside this set means codex grew a new action variant,
#: and fails closed until a capture shows it.
WEB_SEARCH_INERT_ACTIONS = frozenset({"search", "open_page", "find_in_page", "other"})

#: ``web_search.results[].type`` values classified inert. ``text_result``
#: (``domain``, ``ref_id``, ``snippet``, ``title``, ``url``, optional
#: ``thumbnail_url``) is page text the code-mode ``web__run`` search returned
#: from the network, relayed to the model; codex passes it through without
#: acting on it. Any other result type fails closed.
WEB_SEARCH_INERT_RESULT_TYPES = frozenset({"text_result"})

#: The one shell wrapper codex puts in front of every exec_command, exactly as
#: rendered (``shell`` param absent → ``/bin/bash``; ``login: false`` → ``-c``;
#: ``shell: /bin/sh`` → ``/usr/bin/sh``). A wrapper naming any other binary,
#: even one called ``bash`` in another directory, is not unwrapped.
SHELL_WRAPPERS = frozenset({
    "bash", "sh", "/bin/bash", "/usr/bin/bash", "/bin/sh", "/usr/bin/sh",
})
WRAPPER_FLAGS = frozenset({"-lc", "-c"})

#: Substrings that fail the inner command before it is tokenised, including
#: inside double quotes (and, conservatively, inside single quotes too).
FORBIDDEN_SUBSTRINGS = ("$(", "`", "${", "<(", ">(", "\n", "\r")

#: A ``$`` the shell would still expand, checked per token after tokenising
#: (quotes are gone by then, so a quoted ``'$X'`` is refused too). A bare
#: ``$NAME`` / ``$1`` / ``$@`` survives shlex as a literal token and would
#: otherwise pass as a ``find`` leading path or a ``git`` positional while the
#: shell expands it at run time (``-delete``, ``--output=x``). ``-`` and ``\``
#: cover ANSI-C / locale quoting (``$'\x2ddelete'``, ``$"--output=x"``), which
#: shlex flattens to ``$`` + the quoted text. A ``$`` at the end of a token or
#: before a regex metacharacter (``'line$'``, ``'a$|b'``) is left alone.
_EXPANDING_DOLLAR = re.compile(r"\$[A-Za-z0-9_@*#?!$\\-]")

SEPARATORS = frozenset({"|", "&&", "||", ";"})

#: The redirection suffixes allowed at the end of a segment. shlex splits
#: ``2>/dev/null`` into ``2``, ``>``, ``/dev/null``; either reading of those
#: tokens only ever writes to ``/dev/null`` or duplicates a descriptor.
ALLOWED_REDIRECT_SUFFIXES = (("2", ">", "/dev/null"), ("2", ">&", "1"))

_OPERATOR_CHARS = set("();<>|&")


class _Reject(Exception):
    """A classification failure; ``str()`` is the short reason."""


# --------------------------------------------------------------------------- #
# Per-verb argument grammar (step 4)
# --------------------------------------------------------------------------- #

class _FlagSpec:
    """A getopt-style flag grammar: which flags exist and which take a value."""

    def __init__(self, short_noarg: str = "", short_arg: str = "",
                 long_noarg: Sequence[str] = (), long_arg: Sequence[str] = (),
                 numeric_short: bool = False,
                 hyphen_values: Sequence[str] = ()):
        self.short_noarg = set(short_noarg)
        self.short_arg = set(short_arg)
        self.long_noarg = set(long_noarg)
        self.long_arg = set(long_arg)
        self.numeric_short = numeric_short
        # Flags whose SEPARATE value may start with `-` (`rg -e '-i'`): the
        # tool always consumes the next token for them. Every other flag's
        # separate value is refused when it starts with `-`, because a flag
        # the real tool parses as taking an optional or attached-only value
        # (`git diff -U --output=x`, `git log --pretty --output=x`) would
        # otherwise hide a write flag in what this grammar took for a value.
        self.hyphen_values = set(hyphen_values)

    def _take_value(self, verb: str, flag: str, args: Sequence[str], i: int) -> int:
        if i >= len(args):
            raise _Reject(f"{verb}: {flag} needs a value")
        if args[i].startswith("-") and flag not in self.hyphen_values:
            raise _Reject(f"{verb}: {flag} followed by the flag-like value {args[i][:40]!r}")
        return i + 1

    def positionals(self, verb: str, args: Sequence[str]) -> List[str]:
        """Validate every flag; return the positional arguments. Raises _Reject."""
        positionals: List[str] = []
        i = 0
        only_positionals = False
        while i < len(args):
            token = args[i]
            i += 1
            if only_positionals or token == "-" or not token.startswith("-"):
                positionals.append(token)
                continue
            if token == "--":
                only_positionals = True
                continue
            if token.startswith("--"):
                name, eq, _value = token.partition("=")
                if name in self.long_noarg and not eq:
                    continue
                if name in self.long_arg:
                    if not eq:
                        i = self._take_value(verb, name, args, i)
                    continue
                raise _Reject(f"{verb}: flag {name} is not on the read-only grammar")
            # A cluster of short flags: -niC3, -e PATTERN, -5.
            body = token[1:]
            if self.numeric_short and body.isdigit():
                continue
            j = 0
            while j < len(body):
                ch = body[j]
                if ch in self.short_noarg:
                    j += 1
                    continue
                if ch in self.short_arg:
                    if j + 1 == len(body):
                        i = self._take_value(verb, f"-{ch}", args, i)
                    break
                raise _Reject(f"{verb}: flag -{ch} is not on the read-only grammar")
        return positionals


_RG = _FlagSpec(
    short_noarg="nNiSswxvlcoFHIuUPLq0h",
    short_arg="egtTmABCMdj",
    long_noarg=(
        "--line-number", "--no-line-number", "--ignore-case", "--smart-case",
        "--case-sensitive", "--word-regexp", "--line-regexp", "--invert-match",
        "--files-with-matches", "--files-without-match", "--count",
        "--count-matches", "--only-matching", "--fixed-strings",
        "--with-filename", "--no-filename", "--hidden", "--no-ignore",
        "--no-ignore-vcs", "--no-ignore-dot", "--no-ignore-parent",
        "--no-ignore-global", "--no-ignore-exclude", "--multiline",
        "--multiline-dotall", "--pcre2", "--follow", "--files", "--json",
        "--no-heading", "--heading", "--column", "--no-column", "--vimgrep",
        "--trim", "--stats", "--null", "--quiet", "--no-messages", "--text",
        "--binary", "--no-binary", "--unrestricted", "--no-config",
        "--byte-offset", "--passthru", "--crlf", "--debug", "--type-list",
        "--no-unicode", "--line-buffered", "--block-buffered",
    ),
    long_arg=(
        "--regexp", "--glob", "--iglob", "--type", "--type-not", "--max-count",
        "--after-context", "--before-context", "--context", "--max-columns",
        "--max-depth", "--max-filesize", "--threads", "--sort", "--sortr",
        "--color", "--colors", "--encoding", "--engine", "--context-separator",
        "--field-match-separator", "--field-context-separator", "--path-separator",
    ),
    hyphen_values=("-e", "--regexp"),
)

_GREP = _FlagSpec(
    short_noarg="nirRlLcovwxEFPGHhsqIaUZbz",
    short_arg="eABCmd",
    long_noarg=(
        "--line-number", "--ignore-case", "--no-ignore-case", "--recursive",
        "--dereference-recursive", "--files-with-matches",
        "--files-without-match", "--count", "--only-matching", "--invert-match",
        "--word-regexp", "--line-regexp", "--extended-regexp", "--fixed-strings",
        "--perl-regexp", "--basic-regexp", "--with-filename", "--no-filename",
        "--no-messages", "--quiet", "--silent", "--text", "--null",
        "--null-data", "--byte-offset",
    ),
    long_arg=(
        "--regexp", "--include", "--exclude", "--exclude-dir", "--color",
        "--colour", "--max-count", "--after-context", "--before-context",
        "--context", "--binary-files", "--directories", "--devices",
    ),
    numeric_short=True,
    hyphen_values=("-e", "--regexp"),
)

#: ``git log|show|diff|status`` flags that only select or format output; ``git
#: grep`` shares the long ones. ``--output*``, ``--ext-diff``, ``--textconv``,
#: ``-O``/``--open-files-in-pager`` and ``--no-index`` are absent on purpose
#: (the grammar rejects any unlisted flag). ``-L`` takes a value (``git log -L
#: 1,5:f``): read as a bare flag it let ``git log -L -- --output=x`` through,
#: and git takes that ``--`` as the line range, then writes ``x``.
_GIT = _FlagSpec(
    short_noarg="psbzwMlicvEFPhqu",
    short_arg="nSGUL",
    long_noarg=(
        "--oneline", "--stat", "--name-only", "--name-status", "--patch",
        "--no-patch", "--graph", "--decorate", "--no-decorate", "--all",
        "--cached", "--staged", "--porcelain", "--short", "--branch", "--long",
        "--numstat", "--shortstat", "--summary", "--follow", "--reverse",
        "--first-parent", "--merges", "--no-merges", "--abbrev-commit",
        "--no-abbrev", "--no-color", "--word-diff", "--ignore-space-change",
        "--ignore-all-space", "--raw", "--full-index", "--no-renames",
        "--find-renames", "--relative", "--minimal", "--patience", "--histogram",
        "--no-ext-diff", "--no-textconv", "--check", "--ignored", "--line-number",
        "--ignore-case", "--full-name", "--untracked", "--no-untracked",
        "--show-signature", "--parents", "--children", "--left-right",
        "--topo-order", "--date-order", "--no-walk", "--source", "--pretty",
        "--compact-summary", "--dirstat", "--cherry", "--boundary", "--quiet",
    ),
    long_arg=(
        "--format", "--pretty", "--since", "--until", "--after", "--before",
        "--author", "--committer", "--grep", "--max-count", "--skip",
        "--diff-filter", "--date", "--unified", "--color", "--abbrev",
        "--untracked-files", "--word-diff", "--stat", "--dirstat",
        "--find-renames", "--relative", "--decorate", "--ignore-submodules",
        "--submodule", "--inter-hunk-context", "--max-parents", "--min-parents",
    ),
    numeric_short=True,
)

#: ``git grep``. Here ``-n`` (line numbers), ``-G`` (basic regexp) and ``-L``
#: (files without a match) are booleans, not ``git log``'s value flags. Read
#: as value-taking, ``-n`` swallowed the rest of a cluster, and git runs
#: ``git grep -nO<cmd> x`` as ``-n -O<cmd>``: ``<cmd>`` on every matching
#: file. ``-O``/``--open-files-in-pager`` stays absent, so a cluster holding
#: it fails at the ``O``.
_GIT_GREP = _FlagSpec(
    short_noarg="nGLpzwlicvEFPhq",
    short_arg="e",
    long_noarg=_GIT.long_noarg,
    long_arg=_GIT.long_arg,
    numeric_short=True,
)

#: ``git ls-tree`` lists tree objects: no flag of it (git 2.43 ``ls-tree -h``)
#: writes, runs a command or reads the working tree, and ``--format`` only
#: picks entry fields.
_GIT_LS_TREE = _FlagSpec(
    short_noarg="drtzl",
    long_noarg=("--long", "--name-only", "--name-status", "--object-only",
                "--full-name", "--full-tree", "--abbrev"),
    long_arg=("--format", "--abbrev"),
)

#: The read-only git subcommands and their grammars. ``ls-tree`` joined on
#: 2026-10-27: the commit modes' pinned-head read rule
#: (``commit_range.pinned_head_read_rule``) prescribes ``git ls-tree -r
#: --name-only <head> -- <dir>``, and a codex reviewer that obeyed it was
#: marked not clean, which on the plugin-landlock rung discards its result
#: whenever the user's tree changes during the slot.
GIT_SUBCOMMANDS: Dict[str, _FlagSpec] = {
    "log": _GIT, "show": _GIT, "diff": _GIT, "status": _GIT,
    "grep": _GIT_GREP, "ls-tree": _GIT_LS_TREE,
}

#: Verbs whose flags cannot write, whatever they are (step 4, first bullet).
#: ``pwd`` joined on 2026-09-28: its only flags (``-L``/``-P``) choose how the
#: directory is spelled, and a real read-only review opened with ``pwd && rg
#: --files …`` and was marked not clean for it, which costs the slot its
#: unattributed-change exemption (plan: review-run-scope-salvage-and-failure-
#: visibility §7.3).
ANY_FLAG_VERBS = frozenset({"cat", "nl", "head", "tail", "wc", "ls", "pwd"})

_SED_ADDR = r"(?:\d+|\$|/(?:[^/\\]|\\.)*/)"
_SED_SCRIPT_PART = re.compile(rf"^\s*{_SED_ADDR}(?:\s*,\s*{_SED_ADDR})?\s*p\s*$")

_FIND_TESTS_WITH_ARG = frozenset({
    "-name", "-iname", "-path", "-type", "-maxdepth", "-mindepth", "-newer",
    "-size",
})
_FIND_NOARG = frozenset({"-print", "-print0"})
_FIND_OPERATORS = frozenset({"-o", "-or", "-a", "-and", "-not", "!"})


def _sed(args: Sequence[str]) -> None:
    has_n = False
    script: Optional[str] = None
    rest: List[str] = []
    for token in args:
        if script is None and token.startswith("-") and token != "-":
            if token in ("--quiet", "--silent"):
                has_n = True
                continue
            if token.startswith("--"):
                raise _Reject(f"sed: flag {token[:40]} is not on the read-only grammar")
            for ch in token[1:]:
                if ch == "n":
                    has_n = True
                elif ch in "Er":
                    continue
                else:
                    raise _Reject(f"sed: flag -{ch} is not on the read-only grammar")
            continue
        if script is None:
            script = token
        else:
            rest.append(token)
    if not has_n:
        raise _Reject("sed: only `sed -n` is read-only")
    if script is None:
        raise _Reject("sed: no script")
    parts = script.split(";")
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    if not parts:
        raise _Reject("sed: empty script")
    for part in parts:
        if not _SED_SCRIPT_PART.match(part):
            raise _Reject("sed: script is not only address/range + `p` commands")
    for path in rest:
        if path.startswith("-") and path != "-":
            raise _Reject("sed: flag after the script")


def _find(args: Sequence[str]) -> None:
    i = 0
    # Leading paths, up to the first expression token.
    while i < len(args) and not args[i].startswith("-") and args[i] != "!":
        i += 1
    while i < len(args):
        token = args[i]
        i += 1
        if token in _FIND_TESTS_WITH_ARG:
            if i >= len(args):
                raise _Reject(f"find: {token} needs a value")
            i += 1
        elif token in _FIND_NOARG or token in _FIND_OPERATORS:
            continue
        else:
            raise _Reject(f"find: primary {token[:40]} is not on the read-only grammar")


def _git(args: Sequence[str]) -> None:
    args = list(args)
    # `--no-pager` / `-P` is the one global option allowed: it only removes the
    # pager (codex already exports GIT_PAGER=cat for every exec).
    while args and args[0] in ("--no-pager", "-P"):
        args.pop(0)
    if not args:
        raise _Reject("git: no subcommand")
    sub = args[0]
    if sub.startswith("-"):
        raise _Reject(f"git: global option {sub[:40]} is not allowed")
    spec = GIT_SUBCOMMANDS.get(sub)
    if spec is None:
        raise _Reject(f"git: subcommand {sub[:40]!r} is not read-only")
    spec.positionals(f"git {sub}", args[1:])


def _classify_segment(argv: Sequence[str]) -> None:
    if not argv:
        raise _Reject("empty command segment")
    verb, args = argv[0], list(argv[1:])
    if verb in ANY_FLAG_VERBS:
        return
    if verb == "rg":
        _RG.positionals("rg", args)
        return
    if verb == "grep":
        _GREP.positionals("grep", args)
        return
    if verb == "sed":
        _sed(args)
        return
    if verb == "find":
        _find(args)
        return
    if verb == "git":
        _git(args)
        return
    raise _Reject(f"verb {verb[:40]!r} is not on the read-only allow-list")


def _tokenise(inner: str) -> List[str]:
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in inner:
            shown = {"\n": "newline", "\r": "carriage return"}.get(bad, bad)
            raise _Reject(f"shell construct {shown!r} is not allowed")
    lexer = shlex.shlex(inner, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    # shlex treats '#' anywhere as a comment start and drops the rest of the
    # line; bash only does so at the start of a word. Clearing it (as
    # shlex.split does) keeps ``cat x#; touch y`` from hiding the write.
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError as exc:
        raise _Reject(f"unparseable shell text ({exc})") from None
    for token in tokens:
        if _EXPANDING_DOLLAR.search(token):
            raise _Reject("shell parameter expansion `$…` is not allowed")
    return tokens


def _is_operator(token: str) -> bool:
    return bool(token) and all(ch in _OPERATOR_CHARS for ch in token)


def _strip_redirect_suffix(segment: List[str]) -> List[str]:
    changed = True
    while changed:
        changed = False
        for suffix in ALLOWED_REDIRECT_SUFFIXES:
            n = len(suffix)
            if len(segment) > n and tuple(segment[-n:]) == suffix:
                segment = segment[:-n]
                changed = True
    return segment


def classify_shell_text(inner: str) -> None:
    """Steps 3-4 on one shell string. Raises :class:`_Reject` on any doubt."""
    tokens = _tokenise(inner)
    if not tokens:
        raise _Reject("empty command")
    segments: List[List[str]] = [[]]
    for token in tokens:
        if token in SEPARATORS:
            segments.append([])
            continue
        segments[-1].append(token)
    for segment in segments:
        segment = _strip_redirect_suffix(segment)
        for token in segment:
            if _is_operator(token):
                raise _Reject(f"shell operator {token!r} is not allowed")
        _classify_segment(segment)


def classify_command(command: object) -> Optional[str]:
    """``None`` when a ``command_execution`` command is read-only, else a reason.

    Step 1: the wire shape. A list is an exact argv; a string is parsed with
    POSIX shlex (codex renders the argv with POSIX quoting — captured round-trip
    in ``quoting_render.jsonl``). Anything else fails.
    Step 2: unwrap exactly one leading ``bash|sh -lc|-c '<string>'``; the inner
    string then goes through steps 3-4. An argv without a wrapper is one
    segment, classified as is.
    """
    try:
        if isinstance(command, list):
            if not command or not all(isinstance(t, str) for t in command):
                raise _Reject("command argv is not a list of strings")
            argv = list(command)
        elif isinstance(command, str):
            try:
                argv = shlex.split(command, posix=True)
            except ValueError as exc:
                raise _Reject(f"unparseable command ({exc})") from None
            if not argv:
                raise _Reject("empty command")
        else:
            raise _Reject("command is neither a string nor an argv list")

        if argv[0] in SHELL_WRAPPERS:
            if len(argv) != 3 or argv[1] not in WRAPPER_FLAGS:
                raise _Reject("shell invoked other than as one `-lc`/`-c` wrapper")
            classify_shell_text(argv[2])
        elif isinstance(command, str):
            # No wrapper on a string: how it was executed is unknown, so it gets
            # the strictest reading — the same shell grammar.
            classify_shell_text(command)
        else:
            _classify_segment(argv)
    except _Reject as exc:
        return str(exc)
    return None


#: The rendered command in a rejection reason is cut to this many characters
#: (plus an ellipsis), after redaction.
MAX_RENDERED_COMMAND_CHARS = 200

_HOME_PATH = re.compile(r"/(?:home|Users)/[^/\s'\"]+")


def _redact_command_text(text: str) -> str:
    """Secret-shaped values and per-user home paths masked.

    ``write_safety`` is imported late: it reaches the provider registry, so a
    module-level import here would close an import cycle.
    """
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from ..write_safety import redact_text
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import redact_text
    out = redact_text(text)
    home = os.path.expanduser("~")
    if home and home not in ("~", "/") and len(home) > 1:
        out = out.replace(home.rstrip("/"), "~")
    return _HOME_PATH.sub("~", out)


def render_command(command: object) -> str:
    """A bounded, redacted rendering of what codex ran, for a rejection reason.

    The single ``bash|sh -lc|-c`` wrapper is stripped so the reason shows the
    inner shell text; newlines are shown as ``\\n``. The text is redacted
    **before** it is cut to :data:`MAX_RENDERED_COMMAND_CHARS`, so a cut can
    never leave half a secret unmasked. Only the command is rendered — never
    the item's ``aggregated_output``.
    """
    text: str
    if isinstance(command, list) and all(isinstance(t, str) for t in command):
        argv = list(command)
        if len(argv) == 3 and argv[0] in SHELL_WRAPPERS and argv[1] in WRAPPER_FLAGS:
            text = argv[2]
        else:
            text = shlex.join(argv)
    elif isinstance(command, str):
        text = command
        try:
            argv = shlex.split(command, posix=True)
        except ValueError:
            argv = []
        if len(argv) == 3 and argv[0] in SHELL_WRAPPERS and argv[1] in WRAPPER_FLAGS:
            text = argv[2]
    else:
        return "<unrenderable command>"
    text = text.replace("\r", "\\r").replace("\n", "\\n").strip()
    text = _redact_command_text(text)
    if len(text) > MAX_RENDERED_COMMAND_CHARS:
        text = text[:MAX_RENDERED_COMMAND_CHARS] + "\u2026"
    return text


# --------------------------------------------------------------------------- #
# Stream walk (step 5)
# --------------------------------------------------------------------------- #

def _classify_item(item: Dict[str, object]) -> Optional[str]:
    """``None`` when a completed item is read-only, else a reason."""
    item_type = item.get("type")
    if item_type in INERT_ITEM_TYPES:
        return None
    if item_type == "command_execution":
        command = item.get("command")
        if not isinstance(command, (str, list)):
            return "command_execution without a string `command` field"
        if "status" in item and not isinstance(item.get("status"), str):
            return "command_execution with a malformed `status` field"
        why = classify_command(command)
        if why is None:
            return None
        return f"command_execution: {why}; ran: {render_command(command)}"
    if item_type == "file_change":
        return "file_change (apply_patch) is a write"
    if item_type == "mcp_tool_call":
        server, tool = item.get("server"), item.get("tool")
        if not isinstance(server, str) or not isinstance(tool, str):
            return "mcp_tool_call without string `server`/`tool` fields"
        if (server, tool) in READONLY_MCP_TOOLS:
            return None
        return f"mcp_tool_call {server[:40]}/{tool[:40]} is not on the read-only MCP list"
    if item_type == "collab_tool_call":
        return ("collab_tool_call: a spawned sub-agent's actions never reach this "
                "stream")
    if item_type == "web_search":
        action = item.get("action")
        if not isinstance(action, dict) or not isinstance(action.get("type"), str):
            return "web_search without an `action.type` field"
        if action["type"] not in WEB_SEARCH_INERT_ACTIONS:
            return (f"web_search action {action['type'][:40]!r} is not classified "
                    f"(could have written)")
        # The hosted route never carries `results` (codex drops the field even
        # when the server sends it); the code-mode route always does. Absent
        # is fine, present must be a list of classified results.
        if "results" not in item:
            return None
        results = item.get("results")
        if not isinstance(results, list):
            return "web_search with a non-list `results` field"
        for result in results:
            rtype = result.get("type") if isinstance(result, dict) else None
            if not isinstance(rtype, str) or rtype not in WEB_SEARCH_INERT_RESULT_TYPES:
                return (f"web_search result type {str(rtype)[:40]!r} is not "
                        f"classified (could have written)")
        return None
    return f"item type {str(item_type)[:40]!r} is not classified (could have written)"


def audit_codex_stream(stdout: Optional[str]) -> AuditVerdict:
    """The read-only verdict for one attempt's full ``codex exec --json`` stdout."""
    open_items: Dict[str, str] = {}
    turn_completed = False
    actions = 0
    for number, raw in enumerate((stdout or "").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return AuditVerdict(False, f"line {number}: not a JSON event", actions)
        if not isinstance(event, dict):
            return AuditVerdict(False, f"line {number}: not a JSON object", actions)
        etype = event.get("type")
        if etype not in KNOWN_EVENTS:
            return AuditVerdict(
                False, f"line {number}: unknown event type {str(etype)[:40]!r}",
                actions)
        if etype == "turn.completed":
            turn_completed = True
            continue
        if etype == "turn.failed":
            return AuditVerdict(False, "turn.failed: the stream did not complete",
                                actions)
        if not etype.startswith("item."):
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            return AuditVerdict(False, f"line {number}: {etype} without an item", actions)
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            return AuditVerdict(False, f"line {number}: item without an id", actions)
        if etype in ("item.started", "item.updated"):
            open_items[item_id] = str(item.get("type"))
            continue
        open_items.pop(item_id, None)
        if item.get("type") not in INERT_ITEM_TYPES:
            actions += 1
        why = _classify_item(item)
        if why is not None:
            return AuditVerdict(False, f"{item_id[:48]}: {why}", actions)
    if open_items:
        first = sorted(open_items)[0]
        return AuditVerdict(
            False,
            f"{first[:48]}: {open_items[first][:40]} started but never completed "
            f"(unfinished action)", actions)
    if not turn_completed:
        return AuditVerdict(False, "no turn.completed: the stream is incomplete",
                            actions)
    return AuditVerdict(True, "", actions)
