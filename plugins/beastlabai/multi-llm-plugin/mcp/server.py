#!/usr/bin/env python3
"""multi-llm's codex plugin server: one MCP tool over stdio, stdlib only.

WHAT THIS FILE IS. The whole tool route on codex. It is shipped as
``<plugin_root>/mcp/server.py`` and started by codex from the plugin's
``.mcp.json`` as ``python3 ./mcp/server.py``. It speaks newline-delimited
JSON-RPC 2.0 on stdin/stdout, lists exactly one tool, and on ``tools/call``
composes the dispatcher argv, spawns it through a login shell in the user's
workspace, supervises a detached run to a terminal result, and returns one JSON
envelope. It is a port of the OpenCode plugin's ``execute()``
(``packaging/opencode/src/index.mjs``) state for state, except at the two edges
``plans/codex-native-plugin.md`` D3c re-decides: a claimed run whose budget
expires is handed off **alive** (never aborted), and a pinned ``status`` re-attach
supervises.

RULES EVERY LINE HERE KEEPS (plan D3):

  1. **Stdlib only, one file, parses at Python 3.9.** The server must start when
     ``uv`` is absent so it can *report* that absence (rule 7); a dependency, or a
     second module, is one more thing whose absence empties the tool list.
  2. **No word of its own.** Every mode word, alias, flag, exit code, state word
     and message template is read from ``dist/cli-surface.json`` (schema v6). The
     only words held here are the JSON-RPC/MCP vocabulary, the envelope's key
     names, the anchor_source spellings (``roots``, ``turn-metadata``,
     ``env:<NAME>``), codex's turn-metadata keys and posture words, the
     degraded definition (the tool name and one sentence) and the login
     shell's constant ``-c`` string.
  3. **Fd 1 carries JSON-RPC or nothing.** At start-up fd 1 is duplicated to a
     private descriptor only the locked writer uses, and fd 1 and ``sys.stdout``
     are pointed at stderr. Nothing here prints.
  4. **Never die at start, never throw out of a call.** A missing or mismatched
     surface lists the tool under the degraded definition and refuses every call;
     every failure inside a call is an envelope with ``ok: false``.

THREADING (D3c). The main thread owns stdin and answers everything except the
work of a ``tools/call``, which runs on one worker thread; a second call while
one is in flight is refused ``-32000``. Cancellation (``notifications/cancelled``
for the in-flight id, or stdin EOF) crosses to the worker as a per-call event.
One lock serializes every write to the protocol descriptor.
"""

from __future__ import annotations

import codecs
import collections
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

# ---------------------------------------------------------------------------
# Where we are (D2): resolved from __file__, never from the process cwd, which
# is the plugin's install location rather than the user's project (R11).
# ---------------------------------------------------------------------------

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = PLUGIN_ROOT / "skills" / "multi-llm"
SURFACE_PATH = PLUGIN_ROOT / "dist" / "cli-surface.json"
MCP_JSON_PATH = PLUGIN_ROOT / ".mcp.json"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"

#: Bumped in lockstep with ``packaging/common/surface.py``'s
#: ``SURFACE_SCHEMA_VERSION``; ``test_surface_schema_version_matches`` compares
#: the two constants, never a literal. 6: the commit modes' optional ``revs``.
SUPPORTED_SURFACE_VERSION = 6

#: The longest a cancellation may sit unobserved (D3c). It is met by the
#: worker's cancel-event watch in ``run_child`` (a 20 ms wait on the event, then
#: the process-group kill), NOT by killing poll children at this bound as the
#: plan's D3c first wrote. Changed deliberately: codex declares
#: ``timeout_ceiling_s: 0``, so the dispatcher's ``--wait`` resolves to its 90 s
#: default, and a 10 s kill would discard every poll before it returned —
#: every mid-run ``progress_lines`` relay with it. A poll child's timeout is the
#: remaining budget alone.
CANCEL_LATENCY_BOUND_S = 10

#: A2b's shipped ``tool_timeout_sec``, used only when the sibling ``.mcp.json``
#: is missing, unreadable, not JSON, or carries no cap. Never unbounded.
DEFAULT_TOOL_TIMEOUT_S = 900

#: The login shell's ``-c`` string (D3a), a constant with no interpolation of
#: any kind. The anchor travels as ``$1`` and the dispatcher argv as ``"$@"``,
#: so model text reaches the child as positional parameters bash never re-parses.
LOGIN_SHELL_SCRIPT = 'cd -- "$1" && shift && exec "$@"'

#: The shell D3a names, looked up on the server's own PATH, then the fallback.
SHELL_NAME = "bash"
FALLBACK_SHELL = "/bin/bash"

#: Windows only: the directories a ``bash`` on PATH may sit in without being a
#: POSIX shell. ``%SystemRoot%\System32\bash.exe`` is WSL's launcher, present
#: wherever the feature is enabled and ahead of Git on a stock PATH; it starts a
#: Linux VM that has no ``C:\`` anchor and no ``uv.exe`` to ``exec``. The tool's
#: Windows prerequisite is Git Bash (``host_install.git_bash`` draws the same line).
WSL_LAUNCHER_DIRS = ("system32", "syswow64")

#: SIGTERM → SIGKILL grace for every kill, and the drain-thread join bound.
KILL_GRACE_S = 5
#: The signal-free abort dispatch's own timeout (rule f), never the remainder.
ABORT_DISPATCH_TIMEOUT_S = 30
#: Held back from the cap so the handoff result is written while the host is
#: still listening: result construction, the runbook fetch and one teardown.
RESERVE_MAX_S = 20
RESERVE_FRACTION = 0.1
#: How long a ``roots/list`` round trip may take before that rung is skipped.
ROOTS_TIMEOUT_S = 5
#: Mechanical continuations followed per call (the reference's cap).
DEFAULT_CONTINUATION_CAP = 8

#: Retained output budgets. What is bounded is what is *kept*, never the scan.
STDOUT_TAIL_CHARS = 64 * 1024
STDERR_TAIL_CHARS = 8 * 1024
STDOUT_LINE_BYTES = 4 * STDOUT_TAIL_CHARS

#: MCP protocol versions this server speaks; an unknown request gets the default.
PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25")
DEFAULT_PROTOCOL_VERSION = "2025-06-18"
#: MCP logging's eight level words, lowest first.
LOG_LEVELS = (
    "debug", "info", "notice", "warning", "error", "critical", "alert",
    "emergency",
)

#: D3f rung 2: the per-call turn metadata codex 0.156.1 attaches to every
#: ``tools/call`` as ``params._meta["x-codex-turn-metadata"]`` (Phase 1 row 1b,
#: row 7). An undocumented upstream field, so every read of it tolerates absence
#: and any malformed shape. ``workspaces`` is an object keyed by absolute
#: workspace path — under ``codex exec -C <dir>`` it names ``<dir>``, where the
#: launching shell's ``PWD`` names the wrong checkout — and ``sandbox_mode`` is
#: the session's posture word (D3b). ``model`` is the session's own model id
#: (row 7's tap: ``--model stub-model`` arrived as ``"model": "stub-model"``).
TURN_METADATA_KEY = "x-codex-turn-metadata"
TURN_METADATA_WORKSPACES = "workspaces"
TURN_METADATA_SANDBOX_MODE = "sandbox_mode"
TURN_METADATA_MODEL = "model"

#: A plain model id: the ladder spells it ``<provider>:<id>`` and splits an
#: effort off the last ``:``, so a colon, whitespace or a leading ``-`` is refused.
SESSION_MODEL_PATTERN = re.compile(r"[A-Za-z0-9._/@+~][A-Za-z0-9._/@+~-]{0,199}")

#: D3b: the one posture word under which a write-capable mode is refused, and
#: the posture words under which the session itself may write, so the tool may
#: too. Codex's own vocabulary (``--sandbox``), not a surface word. Anything
#: else — absent, not a string, a word not listed here — is unreadable, and the
#: refusal fails closed exactly as it did before the posture could be read.
POSTURE_READ_ONLY = "read-only"
POSTURES_ALLOWING_WRITES = ("workspace-write", "danger-full-access")

#: D3f rung 3: workspace names read from the environment codex handed us,
#: only when present. Each one must be in A2b's ``env_vars`` (D9) — codex
#: forwards nothing else (R12′) — so ``PWD``, the launching shell's directory,
#: is allowlisted there. Row 7: it arrives only if that shell exported it, and
#: under ``-C`` it names the shell's directory, not the session's workspace.
WORKSPACE_ENV_NAMES = ("PWD",)

#: D9 layer 2: set for the child unless the user's environment already sets it,
#: so the payload's Python writes no ``__pycache__`` into the plugin cache (row 7
#: saw ``init_config.cpython-311.pyc`` appear under ``$CODEX_HOME``).
NO_BYTECODE_ENV = "PYTHONDONTWRITEBYTECODE"

#: What this server exports for the child (D9 layer 2), beside the resolved uv.
SKILL_DIR_ENV = "MULTI_LLM_SKILL_DIR"

#: Plan codex-sandbox-unavailable step 6 (F5, user decision 2026-09-30): the
#: chat's own sandbox posture — the turn metadata's ``sandbox_mode`` — exported
#: to the dispatcher per call, so a write job whose Codex children cannot get
#: a sandbox may run uncontained only when the chat itself runs with
#: ``danger-full-access``, and only after the plugin's Landlock jail could not
#: take it. The same name as ``utils.providers.base.HOST_SANDBOX_POSTURE_ENV``
#: (this server imports nothing from the payload). Set only to a posture word
#: this server knows, and removed on every call that carries none, so a posture
#: is never carried over from one call to the next.
HOST_SANDBOX_POSTURE_ENV = "MULTI_LLM_HOST_SANDBOX_POSTURE"

#: The four argument properties: the shared contract's field names (rule 1).
PROPERTIES = ("mode", "plan", "question", "extra_flags")

#: Schema v6's optional fifth property: the commit modes' range
#: (plans/review-commits.md §2.9). Listed in the schema, never required, and
#: written into a handed-back call only for a mode that takes a range, so every
#: other call keeps its four keys. A left-out one is ``""``, as a left-out
#: ``question`` is.
REVS = "revs"
OPTIONAL_PROPERTIES = (REVS,)

#: The result key the commit run's blocks are relayed in, placed right after
#: ``message`` (plans/review-commits.md §2.3, "Relay"): the commit block and any
#: ``[COMMIT_FIXES]`` block, as the run printed them, moved out of ``output``
#: and out of the parsed result so the model reads each line once.
COMMIT_BLOCKS_KEY = "commit_blocks"

#: The degraded definition (rule 7) — the only words this server authors for a
#: model, used only when there is no surface to read words from. The literal
#: name is also the ``.mcp.json`` server key the cap is read under.
DEGRADED_TOOL_NAME = "multi_llm"
DEGRADED_DESCRIPTION = (
    "The multi-llm plugin's generated surface file could not be read, so every "
    "call to this tool refuses until the plugin is reinstalled."
)
#: The state word a degraded call returns. It cannot come from a surface that
#: could not be read; it is the dispatcher's exit-3 word, held for this case only.
DEGRADED_STATE = "needs-human"

#: The result-line key a finished phase's next command rides in
#: (plans/next-phase-command.md §2.4): an envelope key name, lifted to the top
#: level of an exit-0 or exit-2 result beside ``next``. It is the user's to type,
#: never a call — ``is_mechanical`` reads ``next`` alone, so the continuation
#: loop never follows it, and the tool description (surface data) says so.
USER_NEXT_STEP_KEY = "user_next_step"

#: The keys that tell the user what to type, placed right after ``ok`` and
#: ``state`` in every result. Codex shows the model only part of a large tool
#: result: measured on codex 0.160.0 (racing re-run 3, 06b), the session model
#: read the result through its code-mode ``exec`` cell, which kept the first and
#: the last tokens of a 50 355-character result and dropped the middle ("…7996
#: tokens truncated…"). ``resume_command`` sat just before the 39 722-character
#: runbook, inside the dropped middle, while the trailing ``"user_next_step":
#: null`` survived, and the model told the user there was no resume command.
#: The calls a result hands back lead too, when set (fix round 8): a budget
#: handoff's way forward is its re-attach ``next`` and its ``abort_command``,
#: and a needs-human result's ``options`` trailed ``result``, ``output`` and
#: ``stderr`` into the dropped middle.
WAY_FORWARD_KEYS = (USER_NEXT_STEP_KEY, "resume_command", "resume_why",
                    "resume_answers", "resume_markdown", "no_command_reason",
                    "next", "abort_command", "options")

#: The keys placed last: the long runbook (Open question 20 of
#: plans/codex-native-plugin.md: a cut must lose runbook text, never the
#: envelope).
LAST_KEYS = ("runbook",)

#: Where a redacted ``next`` went, and where any other removed command went.
NEXT_MARKER = "<see the `next` field of this result for the tool call>"
RUNNABLE_MARKER = (
    "<a runnable command was removed; commands come back only as tool calls>"
)

# JSON-RPC error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
SERVER_BUSY = -32000


# ---------------------------------------------------------------------------
# Fd 1 guard and the one writer
# ---------------------------------------------------------------------------

def _guard_protocol_fd() -> int:
    """Move the protocol channel to a private descriptor; aim fd 1 at stderr.

    Run before the first line is read. A stray ``print()``, an unraisable thread
    traceback or anything an import writes then lands on stderr by construction,
    because neither fd 1 nor ``sys.stdout`` reaches the client any more.
    """
    private = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    return private


class Wire:
    """The single locked writer: one ``json.dumps`` plus newline per write."""

    def __init__(self, fd: int):
        self._fd = fd
        self._lock = threading.Lock()
        self.closed = False

    def send(self, message: dict) -> bool:
        # json.dumps escapes control characters, so the line has no embedded
        # newline; os.write on a raw fd needs no flush.
        data = (json.dumps(message) + "\n").encode("utf-8")
        with self._lock:
            if self.closed:
                return False
            try:
                view = memoryview(data)
                while view:
                    written = os.write(self._fd, view)
                    view = view[written:]
                return True
            except OSError:
                self.closed = True
                return False


def _stderr(text: str) -> None:
    try:
        sys.stderr.write("[multi-llm] " + text + "\n")
        sys.stderr.flush()
    except (OSError, ValueError):
        pass


# ---------------------------------------------------------------------------
# Start-up reads: the surface, the sibling .mcp.json, the manifest version
# ---------------------------------------------------------------------------

#: The surface keys this server reads, checked for presence at load so a
#: right-version wrong-shape file degrades rather than raising mid-call.
_REQUIRED_SURFACE_PATHS = (
    ("tool_name",), ("tool_description",), ("argument_descriptions",),
    ("modes",), ("positional_kinds",), ("reserved_flags",), ("baked_flags",),
    ("detach_flag",), ("uv", "env"), ("uv", "run_args_env"),
    ("uv", "default_run_args"), ("uv", "candidates"),
    ("uv", "missing_message_file"), ("dispatcher", "script"),
    ("dispatcher", "result_marker"), ("dispatcher", "exit_codes"),
    ("dispatcher", "states"), ("dispatcher", "poll"), ("dispatcher", "abort"),
    ("dispatcher", "instructions"), ("dispatcher", "host_option"),
    ("dispatcher", "run_id_option"), ("dispatcher", "banner"),
    ("dispatcher", "session_model_env"), ("dispatcher", "route_env"),
    ("dispatcher", "route_env", "name"), ("dispatcher", "route_env", "value"),
    # Schema v6: the commit modes' range.
    ("positional_kinds", "plan"), ("positional_kinds", "question"),
    ("positional_kinds", "revs"), ("revs", "count_word"), ("revs", "brief_suffix"),
    ("revs", "plan_refusal"), ("revs", "pinned", "sha_chars"),
    ("revs", "pinned", "separator"), ("revs", "pinned", "pattern"),
    ("revs", "range_key"), ("revs", "fixes_key"), ("revs", "lines_key"),
    ("needs_human_message",),
    ("needs_human_option",), ("write_posture_refusal",),
    ("anchor_unresolved",), ("shell_missing",), ("runbook",), ("host",),
)


def load_surface():
    """``(surface, None)`` or ``(None, problem)``. Never raises."""
    try:
        raw = SURFACE_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return None, "cannot read {}: {}".format(SURFACE_PATH, error)
    try:
        data = json.loads(raw)
    except ValueError as error:
        return None, "{} is not valid JSON: {}".format(SURFACE_PATH, error)
    if not isinstance(data, dict):
        return None, "{} is not a JSON object".format(SURFACE_PATH)
    found = data.get("schema_version")
    if found != SUPPORTED_SURFACE_VERSION:
        return None, (
            "{} declares schema_version {}, but this server supports {}; the "
            "plugin is inconsistent and must be reinstalled".format(
                SURFACE_PATH, json.dumps(found), SUPPORTED_SURFACE_VERSION)
        )
    for keys in _REQUIRED_SURFACE_PATHS:
        node = data
        for key in keys:
            node = node.get(key) if isinstance(node, dict) else None
        if node is None:
            return None, "{} lacks the key {}".format(SURFACE_PATH, ".".join(keys))
    described = data["argument_descriptions"]
    if not isinstance(data["tool_name"], str) or not data["tool_name"]:
        return None, "{}: tool_name is not a non-empty string".format(SURFACE_PATH)
    if not isinstance(data["tool_description"], str) or not isinstance(
        described, dict
    ) or not all(isinstance(described.get(name), str)
                 for name in PROPERTIES + OPTIONAL_PROPERTIES):
        return None, "{}: the tool definition's text is malformed".format(
            SURFACE_PATH)
    # Schema v5's route signal, set on every child. A surface without a usable
    # one is refused whole, never half-used: spawning without it would print a
    # finished phase's next command in another route's spelling.
    route_env = data["dispatcher"]["route_env"]
    if not all(isinstance(route_env.get(key), str) and route_env.get(key)
               for key in ("name", "value")):
        return None, "{}: dispatcher.route_env is not a non-empty name and value".format(
            SURFACE_PATH)
    return data, None


def _server_entry(data):
    """This server's entry in ``.mcp.json``, under either spelling of the table."""
    if not isinstance(data, dict):
        return None
    for table in ("mcpServers", "mcp_servers"):
        servers = data.get(table)
        if isinstance(servers, dict):
            entry = servers.get(DEGRADED_TOOL_NAME)
            if entry is None and len(servers) == 1:
                entry = next(iter(servers.values()))
            if isinstance(entry, dict):
                return entry
    return None


def load_mcp_config():
    """``(cap_s, allowlist, problems)`` from the sibling ``.mcp.json``.

    The cap is read once at start-up and cached (D3c); a file that is missing,
    unreadable, not JSON or keyless leaves ``DEFAULT_TOOL_TIMEOUT_S``, with the
    reason reported on stderr and never on fd 1.
    """
    problems = []
    try:
        entry = _server_entry(json.loads(MCP_JSON_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError, UnicodeDecodeError) as error:
        entry = None
        problems.append("cannot read {}: {}".format(MCP_JSON_PATH, error))
    if entry is None and not problems:
        problems.append("{} names no server entry".format(MCP_JSON_PATH))
    entry = entry or {}
    cap = entry.get("tool_timeout_sec")
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) or cap <= 0:
        if not problems:
            problems.append("{} carries no usable tool_timeout_sec".format(
                MCP_JSON_PATH))
        cap = DEFAULT_TOOL_TIMEOUT_S
    if problems:
        problems[-1] += "; the call budget falls back to {} s".format(
            DEFAULT_TOOL_TIMEOUT_S)
    allowlist = []
    for item in entry.get("env_vars") or []:
        name = item.get("name") if isinstance(item, dict) else item
        if isinstance(name, str) and name:
            allowlist.append(name)
    return float(cap), allowlist, problems


def _plugin_version() -> str:
    try:
        version = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
        version = version.get("version")
        return version if isinstance(version, str) and version else "0.0.0"
    except (OSError, ValueError, AttributeError, UnicodeDecodeError):
        return "0.0.0"


def fill(template: str, values: dict) -> str:
    """Substitute ``{token}`` once, in one pass. Never ``str.format``."""
    if not values:
        return template
    pattern = "\\{(" + "|".join(re.escape(key) for key in values) + ")\\}"
    return re.sub(pattern, lambda match: values[match.group(1)], template)


def _positive_int(raw, fallback):
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    return value if value > 0 else fallback


# ---------------------------------------------------------------------------
# Reserved-flag matching — argparse's rule, not a literal-token scan
# ---------------------------------------------------------------------------

def flag_matches(head: str, name: str, exact_options) -> bool:
    """Whether option token *head* would bind to option *name* (abbreviations).

    A transliteration of ``cli_common._flag_matches``: no parser in the skill
    passes ``allow_abbrev=False``, so ``--ho`` binds to ``--host``.
    """
    if head == name:
        return True
    if not name.startswith("--"):
        return False  # short options never abbreviate
    if not head.startswith("--") or len(head) <= 2:
        return False
    if head in exact_options:
        return False  # a real option spelled in full is not an abbreviation
    return name.startswith(head)


def reserved_hit(token: str, surface: dict):
    """The reserved name *token* would bind to, or None."""
    head = token.split("=", 1)[0]
    reserved = surface["reserved_flags"]
    for prefix in reserved.get("prefixes", []):
        if head.startswith(prefix):
            return prefix + "*"
    for name in list(reserved.get("exact", [])) + list(
            reserved.get("named_exception", [])):
        if flag_matches(head, name, reserved.get("exact_options", [])):
            return name
    return None


def resolve_mode(word, surface):
    for mode in surface["modes"]:
        if mode["name"] == word:
            return mode
    for mode in surface["modes"]:
        if word in mode.get("aliases", []):
            return mode
    return None


def _type_name(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _legal_words(surface) -> str:
    words = []
    for mode in surface["modes"]:
        words.append(mode["name"])
        words.extend(mode.get("aliases", []))
    return ", ".join(words)


def with_absent_question(args):
    """*args* with a left-out ``question`` read as ``""``, its empty value.

    Only ``ask`` takes a question, and the property's own description says it
    is ``""`` for every other mode; a host model that left it out of an
    ``apply-suggestions`` call got ``"question" must be a string, got
    undefined`` and had to retry (racing re-run 3, opencode 02b). A question left out of an ``ask`` call is still refused by
    the arity rule, which names what to send. The port of ``withAbsentQuestion``.
    """
    if isinstance(args, dict) and "question" not in args:
        return dict(args, question="")
    return args


def takes_revs(row, surface) -> bool:
    """Whether *row* declares the commit modes' range (schema v6)."""
    return surface["positional_kinds"]["revs"] in row["positionals"]


def revs_words(revs, surface) -> list:
    """The argv words a ``revs`` value travels as, right after the mode word.

    The dispatcher joins every leading bare word of a range mode into its one
    range, a ``-N`` count word included (``multi_llm._split_positionals``), so
    ``last 2 commits`` goes as three words and arrives as the range the user
    typed, and ``-2 main..HEAD`` as two, which the grammar refuses whole rather
    than reading the second as a flag. One exception keeps a value whole: a
    commit brief's path (it ends in the surface's ``brief_suffix``), which the
    dispatcher turns into ``--plan-file`` only as one word, so a path holding a
    space reaches it unsplit. Nothing here is resolved as a file: ``A..B`` is
    not a path.
    """
    text = (revs or "").strip()
    if not text:
        return []
    if text.endswith(surface["revs"]["brief_suffix"]) and not text.startswith("-"):
        return [text]
    return text.split()


def is_pinned_range(plan, surface) -> bool:
    """Whether *plan* is a pinned range (``<base12>..<head12>``, the surface's
    ``revs.pinned.pattern``), which ``status`` maps to its brief by name: a
    re-attach or abort call names a commit run that way, and it is never a
    path to resolve against the workspace."""
    pattern = ((surface or {}).get("revs") or {}).get("pinned", {}).get("pattern")
    return bool(isinstance(plan, str) and pattern and re.fullmatch(pattern, plan))


def flag_like_revs_word(revs, surface):
    """The first ``revs`` word the dispatcher would read as a flag, or None.

    Only a word starting with ``-`` that is not the surface's ``count_word``
    (``-2``): any other one ends the leading bare-word run, so it would arrive
    as a flag the call never put in ``extra_flags``, a reserved one included.

    A value kept whole as a brief path (:func:`revs_words`) is one argv word
    and carries no flag, but a ``--`` word spelled inside it is refused too:
    ``HEAD~3..HEAD --context-plan docs/x.md``, the shape the plan refusal
    invites, would otherwise reach the range grammar as one bare
    ``[RANGE_UNRECOGNIZED]`` and never hear "send it in extra_flags". Only
    the long-option spelling counts there, as a brief path may hold a word
    that starts with one ``-`` (``reviews -old/x.md``).
    """
    count = re.compile(surface["revs"]["count_word"])
    for token in revs_words(revs, surface):
        if token.startswith("-") and not count.fullmatch(token):
            return token
    for token in (revs or "").split():
        if token.startswith("--"):
            return token
    return None


def validate_args(args, surface):
    """``(mode_row, None)`` or ``(None, message)``. Every rule, before any spawn."""
    if not isinstance(args, dict):
        return None, "arguments must be an object, got {}.".format(_type_name(args))
    mode = args.get("mode")
    plan, question, extra = args.get("plan"), args.get("question"), args.get(
        "extra_flags")
    revs = args.get(REVS, "")
    if not isinstance(mode, str) or not mode:
        return None, '"mode" must be a non-empty string, got {}. Legal words: {}'.format(
            _type_name(mode), _legal_words(surface))
    row = resolve_mode(mode, surface)
    if row is None:
        return None, (
            'unknown mode "{}". Legal words: {}. Nothing is prefix-matched or '
            "guessed.".format(mode, _legal_words(surface)))
    if not isinstance(plan, str):
        return None, '"plan" must be a string, got {}.'.format(_type_name(plan))
    if not isinstance(question, str):
        asking = [mode["name"] for mode in surface["modes"]
                  if surface["positional_kinds"]["question"] in mode["positionals"]]
        return None, (
            '"question" must be a string: the question for {}, "" (or the key left '
            "out) for every other mode. Got {}.".format(
                " or ".join(asking) or "no mode", _type_name(question)))
    if not isinstance(extra, list) or not all(isinstance(t, str) for t in extra):
        return None, (
            '"extra_flags" must be an array of strings (use [] for none), got '
            "{}.".format(_type_name(extra)))
    if not isinstance(revs, str):
        return None, (
            '"revs" must be a string: the commit range for a mode that takes one, '
            '"" (or the key left out) otherwise. Got {}.'.format(_type_name(revs)))
    kinds = surface["positional_kinds"]
    unknown = [kind for kind in row["positionals"] if kind not in kinds.values()]
    if unknown:
        # Never dropped: a positional this server cannot compose would reach
        # the dispatcher missing, or as the wrong kind.
        return None, (
            'mode "{}" declares a positional this server cannot compose ({}); the '
            "plugin is inconsistent and must be reinstalled.".format(
                row["name"], ", ".join(unknown)))
    takes_plan = kinds["plan"] in row["positionals"]
    takes_question = kinds["question"] in row["positionals"]
    ranging = takes_revs(row, surface)
    if ranging and plan != "":
        # `plan` keeps one meaning: a range mode declares no plan positional,
        # and its message names the range's argument and the context flag.
        return None, fill(surface["revs"]["plan_refusal"], {"mode": row["name"]})
    if not ranging and revs != "":
        return None, (
            'mode "{}" declares no range positional, so "revs" must be "" (or the '
            "key left out).".format(row["name"]))
    if ranging:
        flag = flag_like_revs_word(revs, surface)
        if flag is not None:
            return None, (
                '"revs" holds "{}", which the dispatcher would read as a flag and '
                "not as part of the range. Send flags in extra_flags; the only "
                'range word that may begin with "-" is a commit count.'.format(flag))
    if takes_plan and not plan.strip():
        return None, 'mode "{}" takes a plan path and "plan" was empty.'.format(
            row["name"])
    if not takes_plan and plan != "":
        return None, (
            'mode "{}" declares no plan positional, so "plan" must be "".'.format(
                row["name"]))
    if takes_question and not question.strip():
        return None, ('mode "{}" takes a question and "question" was empty: send '
                      "the user's question as \"question\".".format(row["name"]))
    if not takes_question and question != "":
        return None, (
            'mode "{}" declares no question positional, so "question" must be '
            '"".'.format(row["name"]))
    if takes_plan and plan.startswith("-"):
        return None, (
            '"plan" looks like a flag ("{}"). The dispatcher takes leading bare '
            "words as positionals and forwards everything from the first flag "
            "on, so this would arrive with one positional missing.".format(plan))
    if takes_question and question.startswith("-"):
        return None, (
            '"question" may not begin with "-": the dispatcher would read it as '
            "a flag and the mode would arrive one positional short. A question "
            "that merely contains a flag is fine; only the first character "
            "matters.")
    reserved = surface["reserved_flags"]
    _kept, _dropped, refused = split_extra_flags(extra, surface)
    if refused is not None:
        token, hit = refused
        if hit in reserved.get("named_exception", []):
            # Requirement #5: refused before the spawn, never substituted.
            return None, (
                '"{}" is refused: interactive model selection is unsupported on '
                "this route. The tool spawns the dispatcher with no terminal on "
                "its stdin, so {} would force a model picker that cannot prompt. "
                "Choose models non-interactively instead, in extra_flags or in "
                "providers.yaml, or use the file route from a real terminal."
                .format(token, hit))
        return None, (
            '"{}" is reserved: this tool composes {} itself, so a call may not '
            "duplicate, contradict or restate it. Remove it from extra_flags."
            .format(token, hit))
    return row, None


def split_extra_flags(extra, surface):
    """``(kept, dropped, refused)``: what is forwarded, dropped, or refused first.

    A token naming a flag this tool composes is a no-op when the surface lists
    it as ``reserved_flags.redundant`` — a valueless one (``--yes`` in every
    spelling, ``--exec-subagents``) always, a valued one (``--host``) only with
    the value this tool composes, from the ``=`` form or the next element.
    ``refused`` is ``(token, hit)`` for the first other reserved token, else
    ``None``. A surface without ``redundant`` drops nothing, so every reserved
    token is refused exactly as before. The port of ``splitExtraFlags``.
    """
    redundant = surface["reserved_flags"].get("redundant") or {}
    flags = redundant.get("flags") or []
    valued = redundant.get("valued") or {}
    kept, dropped, index = [], [], 0
    while index < len(extra):
        token = extra[index]
        hit = reserved_hit(token, surface)
        if hit is None:
            kept.append(token)
            index += 1
            continue
        if hit in flags and "=" not in token:
            dropped.append(token)
            index += 1
            continue
        value = valued.get(hit)
        if isinstance(value, str):
            inline = "=" in token
            given = token.split("=", 1)[1] if inline else (
                extra[index + 1] if index + 1 < len(extra) else None)
            if given == value:
                dropped.append(token if inline else "{} {}".format(token, given))
                index += 1 if inline else 2
                continue
        return kept, dropped, (token, hit)
    return kept, dropped, None


# ---------------------------------------------------------------------------
# uv preflight — unattended.find_uv(), branch for branch
# ---------------------------------------------------------------------------

def _is_file(target) -> bool:
    try:
        return os.path.isfile(target)
    except (OSError, ValueError):
        return False


def windows_bash(path: str):
    """Git for Windows' ``bash`` along *path*, never WSL's launcher, or None.

    ``bash`` on PATH minus its System32 entries; failing that the one installed
    beside a ``git`` on PATH, because Git's default install puts only
    ``<root>\\cmd`` there (``<root>\\bin`` is a separate installer option).
    """
    kept = os.pathsep.join(
        entry for entry in path.split(os.pathsep)
        if re.split(r"[/\\]", entry.rstrip("/\\"))[-1].lower() not in WSL_LAUNCHER_DIRS)
    found = shutil.which(SHELL_NAME, path=kept)
    if found:
        return found
    git = shutil.which("git", path=path)
    if git:
        # <root>\cmd\git.exe, <root>\bin\git.exe or <root>\mingw64\bin\git.exe
        parents = Path(os.path.abspath(git)).parents
        for root in [parents[index] for index in (1, 2) if index < len(parents)]:
            for relative in (("bin", "bash.exe"), ("usr", "bin", "bash.exe")):
                candidate = root.joinpath(*relative)
                if _is_file(candidate):
                    return str(candidate)
    return None


def file_uri_path(parsed) -> str:
    """The local path of a parsed ``file://`` URI.

    A Windows URI carries its drive behind the path's leading slash
    (``file:///C:/src/x`` parses to ``/C:/src/x``), which ``ntpath``
    resolves under the current drive into no directory at all; so every root a
    Windows client offered was "not a directory" and the anchor fell through to
    the next rung.
    """
    path = unquote(parsed.path)
    if os.name == "nt" and re.match(r"/[A-Za-z]:", path):
        path = path[1:]
    return path


def expand_home(target: str, env) -> str:
    home = env.get("HOME") or env.get("USERPROFILE") or os.path.expanduser("~")
    if target == "~":
        return home
    if target.startswith("~/") or target.startswith("~\\"):
        return os.path.join(home, target[2:])
    return target


def find_uv(surface, env):
    """``$<uv.env>`` → PATH → the surface's candidates. Absolute path or None."""
    override = env.get(surface["uv"]["env"])
    if override and _is_file(override):
        return os.path.abspath(override)
    names = ("uv.exe", "uv") if sys.platform == "win32" else ("uv",)
    for directory in (env.get("PATH") or "").split(os.pathsep):
        if not directory:
            continue
        for name in names:
            candidate = os.path.join(directory, name)
            if _is_file(candidate) and os.access(candidate, os.X_OK):
                return os.path.abspath(candidate)
    for candidate in surface["uv"]["candidates"]:
        expanded = expand_home(candidate, env)
        if _is_file(expanded):
            # Normalized like the two rungs above: on Windows the candidate's
            # `/`s would otherwise follow the home's `\`s into the child's env.
            return os.path.abspath(expanded)
    return None


#: D5's health contract, row 2: the payload files every spawn needs, beside the
#: surface's dispatcher script. Checked at call time, never at start (rule 7).
PAYLOAD_INVENTORY = ("pyproject.toml", "uv.lock")


def missing_payload(surface):
    """The absolute path of the first required payload file absent, or None."""
    for name in (surface["dispatcher"]["script"],) + PAYLOAD_INVENTORY:
        target = SKILL_DIR.joinpath(*name.split("/"))
        if not _is_file(target):
            return os.path.abspath(str(target))
    return None


def payload_missing_text(target: str) -> str:
    """A partial install, named by its absolute path (D3 rule 7)."""
    return ("This plugin install is incomplete: {} is missing, so nothing was "
            "started. Reinstall the plugin, then call the tool again.".format(target))


def uv_missing_text(surface) -> str:
    """``hosts/uv-missing.txt`` from the payload, verbatim (its single owner)."""
    target = SKILL_DIR.joinpath(*surface["uv"]["missing_message_file"].split("/"))
    try:
        return target.read_text(encoding="utf-8").rstrip("\n")
    except (OSError, UnicodeDecodeError):
        # A partial install is the only way here; name the file, author nothing.
        return "uv could not be found, and this install is missing {}.".format(
            target)


# ---------------------------------------------------------------------------
# Redaction — the port of redactCommand / commandForms / scrubValue /
# runnablePattern (D3c). Applied to next, the parsed result and the tails.
# ---------------------------------------------------------------------------

def command_forms(command):
    """Every spelling of one command a captured string may hold, escaped first."""
    if not isinstance(command, str) or not command:
        return []
    escaped = json.dumps(command, ensure_ascii=False)[1:-1]
    return [command] if escaped == command else [escaped, command]


#: A command's body: anything but a newline, a double quote or a backtick —
#: except ``"'"``, the middle of ``cli_common._quote``'s ``'"'"'``, its only
#: spelling of an apostrophe (an ``ask`` question holding one was cut there,
#: 2026-10-05).
_COMMAND_BODY = r"""(?:[^\n"`]|"'")*"""


def runnable_pattern(surface):
    """``uv … run … <script> …``, bounded at a newline, a double quote or backtick."""
    script = re.escape(surface["dispatcher"]["script"])
    return re.compile(
        r'[^\s"`]*\buv(?:\.exe)?\b\s+run\b' + _COMMAND_BODY + script + _COMMAND_BODY)


def cut_mid_token(match) -> bool:
    """Whether a ``"`` cut this match where its last token may go on.

    Every command the dispatcher prints is POSIX-quoted (``cli_common._quote``),
    so a stop right after a closing quote (or an escaping backslash) can sit
    inside one shell word: the parse then succeeds on the part before the cut,
    and the re-spelled command — and the option — carry a truncated value (an
    ``ask`` question with a ``"`` in it, 2026-10-05). Such a match keeps the
    pointer and comes back unparseable; a cut inside an open quote already
    fails to parse. The port of ``cutMidToken``.
    """
    end = match.end()
    return match.string[end:end + 1] == '"' and match.group(0)[-1:] in ("'", "\\")


def scrub_value(value, commands, pattern, respell=None):
    if isinstance(value, str):
        for form in commands:
            value = value.replace(form, NEXT_MARKER)
        if not pattern:
            return value
        return pattern.sub(
            lambda match: (respell(match.group(0))
                           if respell and not cut_mid_token(match) else None)
            or RUNNABLE_MARKER, value)
    if isinstance(value, list):
        return [scrub_value(item, commands, pattern, respell) for item in value]
    if isinstance(value, dict):
        return {key: scrub_value(item, commands, pattern, respell)
                for key, item in value.items()}
    return value


_UV_RUN = re.compile(r'[^\s"`]*\buv(?:\.exe)?\b\s+run\b')


def scrub_runbook(text: str, surface) -> str:
    """Remove every runnable dispatcher line from the runbook, whole.

    The core files quote their paths (``--project "<dir>"``), which the shape
    pattern stops at, and continue long commands with a trailing backslash. So
    the runbook is scrubbed by *logical* line: one whose ``uv run`` reaches the
    dispatcher script keeps its prefix (a list number, an env assignment) and
    loses the command and every continuation line, replaced by the pointer.
    """
    script = surface["dispatcher"]["script"]
    lines, out, index = text.split("\n"), [], 0
    while index < len(lines):
        start = index
        while lines[index].rstrip().endswith("\\") and index + 1 < len(lines):
            index += 1
        logical = "\n".join(lines[start:index + 1])
        found = _UV_RUN.search(logical)
        if found and script in logical[found.start():]:
            out.append(logical[:found.start()] + RUNNABLE_MARKER)
        else:
            out.extend(lines[start:index + 1])
        index += 1
    return "\n".join(out)


def redact(value, command, surface, respell=None):
    return scrub_value(value, command_forms(command),
                       runnable_pattern(surface) if surface else None, respell)


def split_posix(text: str):
    """POSIX word splitting, quotes only. Reads; never executes. None if unbalanced."""
    out, current, quote, any_char, index = [], [], None, False, 0
    while index < len(text):
        char = text[index]
        if quote:
            if char == quote:
                quote = None
            elif quote == '"' and char == "\\" and index + 1 < len(text):
                index += 1
                current.append(text[index])
            else:
                current.append(char)
            any_char = True
        elif char in ("'", '"'):
            quote, any_char = char, True
        elif char == "\\" and index + 1 < len(text):
            index += 1
            current.append(text[index])
            any_char = True
        elif char.isspace():
            if any_char:
                out.append("".join(current))
            current, any_char = [], False
        else:
            current.append(char)
            any_char = True
        index += 1
    if quote:
        return None
    if any_char:
        out.append("".join(current))
    return out


def parse_dispatcher_command(command, surface):
    """``uv run … <script> <mode> <positionals> <flags>`` back into tool args.

    On a mode that takes a range, the leading bare words (a ``-N`` count word
    included, as the dispatcher splits them) are the range: they are joined
    into ``revs``, ``plan`` stays empty, and every flag from the first one on
    (``--focus``, ``--context-plan`` and their values among them) stays in
    ``extra_flags`` as printed.
    """
    tokens = split_posix(command)
    if not tokens:
        return None
    script = surface["dispatcher"]["script"]
    at = next((i for i, t in enumerate(tokens) if t.endswith(script)), -1)
    if at < 0 or at + 1 >= len(tokens):
        return None
    rest = tokens[at + 1:]
    row = resolve_mode(rest[0], surface)
    if row is None:
        return None
    ranging = takes_revs(row, surface)
    count = re.compile(surface["revs"]["count_word"]) if ranging else None
    positionals, flags, seen_flag = [], [], False
    for token in rest[1:]:
        if token.startswith("-") and not (
                not seen_flag and count is not None and count.fullmatch(token)):
            seen_flag = True
        (flags if seen_flag else positionals).append(token)
    kinds = surface["positional_kinds"]
    takes_plan = kinds["plan"] in row["positionals"]
    takes_question = kinds["question"] in row["positionals"]
    # Drop the flags this tool composes itself, and each one's value.
    kept, index = [], 0
    while index < len(flags):
        token = flags[index]
        if reserved_hit(token, surface) is None:
            kept.append(token)
        elif "=" not in token and index + 1 < len(flags) and not flags[
                index + 1].startswith("-"):
            index += 1
        index += 1
    if ranging:
        return {"mode": row["name"], REVS: " ".join(positionals), "plan": "",
                "question": "", "extra_flags": kept}
    args = {
        "mode": row["name"],
        "plan": (positionals[0] if positionals else "") if takes_plan else "",
        "question": (positionals[1] if len(positionals) > 1 else "")
        if takes_question else "",
        "extra_flags": kept,
    }
    if takes_plan and not args["plan"]:
        return None
    return args


def unparseable_call() -> dict:
    """What a follow-up this tool cannot parse into a tool call comes back as."""
    return {
        "unparseable": True,
        "note": "The dispatcher returned a follow-up this tool could not "
                "parse into a tool call. It is reported rather than "
                "executed. Do not run it in a shell.",
    }


def next_as_tool_call(raw, surface):
    """A ``next`` string re-spelled as tool-call args, or an unparseable note."""
    if not isinstance(raw, str) or not raw:
        return None
    parsed = parse_dispatcher_command(raw, surface)
    if parsed is None:
        return unparseable_call()
    return parsed


def quote_for_reader(value: str) -> str:
    """A value quoted for the model reading a user-spelled command, never a shell.

    ``next_phase.quote_plan_arg``'s rule, held to it by a shared case table:
    bare without whitespace or a quote, single quotes around a value holding
    ``"`` but not ``'``, double quotes otherwise, nothing escaped.
    """
    has_double, has_single = '"' in value, "'" in value
    if has_double and not has_single:
        return "'{}'".format(value)
    if has_double or has_single or any(ch.isspace() for ch in value):
        return '"{}"'.format(value)
    return value


def typed_plan(plan, values):
    """*plan* as this call typed it, when it names the call's own plan file."""
    values = values or {}
    if plan and values.get("plan_arg") and same_plan_file(plan, values.get("plan")):
        return values["plan_arg"]
    return plan


#: The result keys that hand the model a tool call to send back.
HANDED_BACK_CALLS = ("next", "abort_command")


def hand_back_typed(outcome, values) -> None:
    """Every tool call *outcome* hands back names the plan as this call typed it.

    The server names the plan absolutely inside its own loop (the polls, the
    abort dispatch, a mechanical continuation), and those spellings used to
    leave in the re-attach ``next`` and the ``abort_command``. The call the
    model sent back then *typed* the absolute path, so its resume command and
    its re-spelled output lines carried it too (racing re-run 3, 2026-10-05:
    ``--implement <absolute path>/plans/racing-game.md --resume`` for a plan
    the user typed ``plans/racing-game.md``). The call runs in the
    same anchor, so the typed spelling names the same file. The port of
    ``handBackTyped``.
    """
    for key in HANDED_BACK_CALLS:
        call_args = outcome.get(key)
        if (isinstance(call_args, dict) and not call_args.get("unparseable")
                and isinstance(call_args.get("plan"), str)):
            outcome[key] = dict(call_args, plan=typed_plan(call_args["plan"], values))


def plan_from_root(result, values, anchor, key) -> None:
    """Name a plan typed from the repository root by the root's file, when the
    dispatcher's result line says it ran from there.

    The dispatcher runs a command whose relative paths name nothing from its
    cwd (the anchor, here) from the root of the repository that cwd is in
    (fix round 26, live run 11: ``multi_llm._run_from_repository_root``), and
    its result line names that root (*key*, the surface's
    ``dispatcher.ran_from_root_key``). So the polls, the abort and the
    options this server composes name the file that run reads, never a path
    under the anchor that does not exist. Fix round 27 (the Fable review of
    round 26): this server walked to the nearest ``.git`` itself, which named
    the root's plan where the dispatcher refused to move (``GIT_DIR`` set, a
    planted ``core.worktree``, a planted nested ``.git``); it now takes the
    dispatcher's own answer, off a line it reads anyway, and nothing else. A
    root that is not absolute or that the anchor is not inside is ignored, as
    is a plan typed absolute. The port of ``planFromRoot``.
    """
    root = result.get(key) if key and isinstance(result, dict) else None
    typed = values.get("plan_arg")
    if (not isinstance(root, str) or not os.path.isabs(root)
            or not isinstance(typed, str) or not typed or os.path.isabs(typed)
            or values.get("pinned_plan")):
        return
    try:
        here = os.path.realpath(anchor)
    except (OSError, ValueError, TypeError):
        return
    root = os.path.normpath(root)
    if here != root and not here.startswith(root.rstrip(os.sep) + os.sep):
        return
    values["plan"] = os.path.normpath(os.path.join(root, typed))


def dispatcher_cwd(result, anchor, key):
    """The directory the dispatcher ran from: the repository root its result
    line names (*key*, the surface's ``dispatcher.ran_from_root_key``) when it
    is absolute and holds the anchor, as :func:`plan_from_root` accepts it,
    else the anchor. A relative path the dispatcher printed is relative to it.
    """
    root = result.get(key) if key and isinstance(result, dict) else None
    if not isinstance(root, str) or not os.path.isabs(root):
        return anchor
    try:
        here = os.path.realpath(anchor)
    except (OSError, ValueError, TypeError):
        return anchor
    root = os.path.normpath(root)
    if here == root or here.startswith(root.rstrip(os.sep) + os.sep):
        return root
    return anchor


def watched_plan(watched) -> str:
    """What a re-attach or abort call names the watched run by: a range
    mode's pinned range when its launch pinned one (``Server.pin_commit_range``),
    else the plan."""
    watched = watched or {}
    return watched.get("pinned") or watched.get("plan", "")


def same_plan_file(left, right) -> bool:
    """Whether two plan paths name one file, symlinks followed on both sides.

    The call's plan is joined to the anchor without following symlinks
    (``normalize_plan``) and the dispatcher prints some paths through
    ``Path.resolve()``, so under a symlinked plan directory the same file came
    back spelled two ways and the re-spelled commands and options carried the
    absolute real path instead of the plan as typed (2026-10-05). Two absolute
    paths are compared by ``realpath``; anything else only by equality. The
    port of ``samePlanFile``.
    """
    if left == right:
        return True
    if not left or not right or not os.path.isabs(left) or not os.path.isabs(right):
        return False
    return os.path.realpath(left) == os.path.realpath(right)


def user_spelling(args, surface):
    """Tool-call args spelled the way this route's user types them, or ``None``.

    The template and slot are ``dispatcher.user_command``, the mode word the
    row's ``user_flag``, every value quoted by :func:`quote_for_reader` — the
    pieces ``next_phase.resume_command`` builds the same string from.
    """
    spell = (surface or {}).get("dispatcher", {}).get("user_command")
    row = resolve_mode(args.get("mode"), surface) if surface else None
    if not isinstance(spell, dict) or not isinstance(spell.get("template"), str) \
            or not row or not row.get("user_flag"):
        return None
    words = [row["user_flag"]]
    words.extend(quote_for_reader(word) for word in revs_words(args.get(REVS), surface))
    for key in ("plan", "question"):
        if args.get(key):
            words.append(quote_for_reader(args[key]))
    words.extend(quote_for_reader(flag) for flag in args.get("extra_flags") or [])
    return spell["template"].replace(spell["args_slot"], " ".join(words))


def respeller_for(surface, values):
    """Re-spell one redacted dispatcher command for the user, or ``None`` (D3c).

    Parsed into tool-call args first (the composed flags already gone), the
    plan put back as this call typed it, spelled through the route's template.
    ``None`` when the surface carries no ``dispatcher.user_command``; the
    returned function answers ``None`` for a command that does not parse, and
    the caller keeps the pointer.
    """
    if not (surface or {}).get("dispatcher", {}).get("user_command"):
        return None

    def respell(command):
        args = parse_dispatcher_command(command, surface)
        if args is None:
            return None
        return user_spelling(dict(args, plan=typed_plan(args["plan"], values)), surface)
    return respell


def blocked_word(values, outcome, surface):
    """The mode ``util next-command --blocked`` is asked about, or ``None``.

    The call's own when it is a phase, else the phase of the run the call
    reported on: a ``status`` or ``abort`` call on a failed run re-spells
    status's ``resume with:`` line into the host's command, and asking
    ``--blocked status`` — no phase, so no answer — then put "give the user no
    command" beside it (2026-10-05). The run is named by the result line (a
    poll pinned to one run carries its ``mode`` and ``phase``), else by the one
    phase the output re-invokes; several, or none, name nothing. The port of
    ``blockedWord``.
    """
    def is_phase(word):
        row = resolve_mode(word, surface) if isinstance(word, str) and word else None
        return bool(row and row.get("phase"))

    word = (values or {}).get("word")
    if is_phase(word):
        return word
    result = (outcome or {}).get("result")
    result = result if isinstance(result, dict) else {}
    for candidate in (result.get("mode"), result.get("phase")):
        if is_phase(candidate):
            return candidate
    named = {resolve_mode(option["mode"], surface)["name"]
             for option in (outcome or {}).get("options") or []
             if isinstance(option, dict) and is_phase(option.get("mode"))}
    return named.pop() if len(named) == 1 else None


def shows_a_phase_command(outcome, surface) -> bool:
    """Whether the result's own text shows a re-spelled phase command.

    An ``options`` call on a phase mode, spelled for the user
    (:func:`user_spelling`), found in ``output`` or ``stderr`` as rendered.
    The port of ``showsAPhaseCommand``.
    """
    text = "\n".join(part for part in (outcome.get("output"), outcome.get("stderr"))
                     if isinstance(part, str))
    if not text:
        return False
    for option in outcome.get("options") or []:
        if not isinstance(option, dict) or "mode" not in option:
            continue
        row = resolve_mode(option.get("mode"), surface)
        if not row or not row.get("phase"):
            continue
        spelled = user_spelling(option, surface)
        if spelled and spelled in text:
            return True
    return False


def pinned_run_id(tokens, surface):
    """The value bound to the run-id option in *tokens* (abbreviations too)."""
    name = surface["dispatcher"]["run_id_option"]
    exacts = surface["reserved_flags"].get("exact_options", [])
    for index, token in enumerate(tokens):
        head, sep, value = token.partition("=")
        if not flag_matches(head, name, exacts):
            continue
        if sep:
            return value or None
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        return following if following is not None and not following.startswith(
            "-") else None
    return None


def lift_user_next_step(outcome: dict) -> None:
    """Move the redacted payload's ``user_next_step`` to the result's top level.

    Exit 0 and exit 2 only (plans/next-phase-command.md §2.4): a finished phase
    or a terminal poll, and a phase already complete. The value is taken from
    ``result`` after ``redact``, byte for byte, the completed form
    (``command: null``, ``complete: true``) included, under the same key name.
    A payload without the key lifts nothing, so an absent top-level key keeps
    meaning "no answer", never "workflow complete". A still-running poll's
    exit 2 carries no key (the dispatcher never sets one there), so nothing is
    lifted mid-run.

    Moved, not copied (fix round 26, live run 11): the section the host
    copies was in the result twice, and the hosts wrote its sentences twice
    ("Workflow complete." plain and then fenced on OpenCode's decline run).
    One copy, in the field that owns it, as the result line itself is
    dropped from ``output`` once it parsed. ``result`` is ``redact``'s own
    copy, so the child's parsed payload is untouched.
    """
    payload = outcome.get("result")
    if isinstance(payload, dict) and payload.get(USER_NEXT_STEP_KEY) is not None:
        outcome[USER_NEXT_STEP_KEY] = payload.pop(USER_NEXT_STEP_KEY)


def carries_next_step(child) -> bool:
    """Whether :func:`lift_user_next_step` lifts a step off this child's
    result: its parsed payload holds a non-null ``user_next_step``."""
    payload = getattr(child, "result", None)
    return isinstance(payload, dict) and payload.get(USER_NEXT_STEP_KEY) is not None


def is_mechanical(next_args, surface) -> bool:
    if not isinstance(next_args, dict) or next_args.get("unparseable"):
        return False
    markers = surface["dispatcher"].get("mechanical_continuations") or []
    return any(token.split("=", 1)[0] in markers
               for token in next_args.get("extra_flags", []))


# ---------------------------------------------------------------------------
# One child: login shell, own process group, drained pipes, bounded
# ---------------------------------------------------------------------------

class _Tail:
    """The newest *keep* characters of a stream, without quadratic copying."""

    def __init__(self, keep: int):
        self.keep, self.parts, self.size, self.truncated = keep, collections.deque(), 0, False

    def add(self, text: str) -> None:
        self.parts.append(text)
        self.size += len(text)
        while self.size > self.keep and len(self.parts) > 1:
            self.size -= len(self.parts.popleft())
            self.truncated = True

    def text(self) -> str:
        joined = "".join(self.parts)
        if len(joined) > self.keep:
            self.truncated = True
            joined = joined[-self.keep:]
        return joined


def _signal_name(number: int) -> str:
    """`` (SIGKILL)`` for a known signal number, else empty."""
    try:
        return " ({})".format(signal.Signals(number).name)
    except ValueError:
        return ""


class ChildRun:
    """What one child left behind. Never raises; a failure is a field."""

    def __init__(self, argv):
        self.argv = argv
        self.code = None
        self.signal = None  # the signal number when the child was killed by one
        self.spawn_error = None
        self.result = None
        self.result_raw = None
        self.stdout = ""
        self.stderr = ""
        self.truncated = False
        self.banner = {}
        self.cancelled = False
        self.timed_out = False


def _drain_stdout(pipe, run: ChildRun, marker: str, banner_re, tail: _Tail):
    """Scan every line: the *last* result line wins, the first banner field wins."""
    overflow = False
    try:
        for raw in iter(lambda: pipe.readline(STDOUT_LINE_BYTES), b""):
            if overflow:
                overflow = not raw.endswith(b"\n")
                continue
            if not raw.endswith(b"\n") and len(raw) >= STDOUT_LINE_BYTES:
                overflow = True  # keep the head, where the marker is
                run.truncated = True
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            trimmed = line.strip()
            if trimmed.startswith(marker):
                run.result_raw = trimmed[len(marker):].strip()
                try:
                    parsed = json.loads(run.result_raw)
                except ValueError:
                    parsed = None
                run.result = parsed if isinstance(parsed, dict) else None
            field = banner_re.match(line)
            if field and field.group(1) not in run.banner:
                run.banner[field.group(1)] = field.group(2)
            tail.add(line + "\n")
    except (OSError, ValueError):
        pass
    finally:
        _close_quietly(pipe)


def _close_quietly(pipe) -> None:
    """The drain owns its pipe: closing it from the supervisor could block on the
    buffered reader's lock while an abandoned drain sits in readline()/read1()."""
    try:
        pipe.close()
    except (OSError, ValueError):
        pass


def _drain_stderr(pipe, tail: _Tail):
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    try:
        for chunk in iter(lambda: pipe.read1(65536), b""):
            tail.add(decoder.decode(chunk))
    except (OSError, ValueError):
        pass
    finally:
        _close_quietly(pipe)


def _signal_group(proc, which) -> None:
    # POSIX process groups; tolerate a missing killpg in embedded runtimes too.
    killpg = getattr(os, "killpg", None)
    if killpg is not None:
        try:
            killpg(proc.pid, which)
            return
        except (ProcessLookupError, PermissionError, OSError):
            pass
    try:
        proc.send_signal(which)
    except (ProcessLookupError, OSError):
        pass


#: ``CreateProcess`` flag: the child's first thread starts suspended (Windows).
CREATE_SUSPENDED = 0x00000004


class WindowsJob:
    """A Job Object holding one child and every process it starts (Windows).

    ``taskkill /T`` finds a tree by parent pid, and Windows keeps a dead
    parent's pid on its orphans, so an unrelated orphan whose dead parent's
    pid was recycled to our child died with it. The child is created
    suspended, put in a job of its own (:meth:`adopt`) and only then resumed,
    so all it starts lands in the job: the venv launcher's and libuv's own
    jobs let their children break away only up to the first job that does not
    permit it, and this one permits nothing. :meth:`terminate` then ends
    exactly that tree in one call. No limit is set, so :meth:`close` kills
    nothing. Stdlib ``ctypes``, typed for 64-bit handles (rule 1).
    """

    #: ``PROCESS_TERMINATE | PROCESS_SET_QUOTA | PROCESS_SUSPEND_RESUME``.
    PROCESS_RIGHTS = 0x0001 | 0x0100 | 0x0800

    def __init__(self, api, handle):
        self.api, self.handle = api, handle

    @classmethod
    def load_api(cls):  # pragma: no cover - Windows
        import ctypes
        import types
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll")
        handle, boolean, dword = wintypes.HANDLE, wintypes.BOOL, wintypes.DWORD
        for name, argtypes, restype in (
                ("CreateJobObjectW", [ctypes.c_void_p, wintypes.LPCWSTR], handle),
                ("AssignProcessToJobObject", [handle, handle], boolean),
                ("TerminateJobObject", [handle, wintypes.UINT], boolean),
                ("OpenProcess", [dword, boolean, dword], handle),
                ("CloseHandle", [handle], boolean)):
            function = getattr(kernel32, name)
            function.argtypes, function.restype = argtypes, restype
        # Popen keeps no handle of the child's first thread, so the whole
        # process is resumed (undocumented, stable since XP; psutil's resume).
        ntdll.NtResumeProcess.argtypes = [handle]
        ntdll.NtResumeProcess.restype = ctypes.c_long
        return types.SimpleNamespace(
            create=lambda: kernel32.CreateJobObjectW(None, None) or None,
            open_process=lambda pid: kernel32.OpenProcess(
                cls.PROCESS_RIGHTS, False, pid) or None,
            assign=lambda job, process: bool(
                kernel32.AssignProcessToJobObject(job, process)),
            resume=lambda process: ntdll.NtResumeProcess(process) == 0,
            terminate=lambda job: bool(kernel32.TerminateJobObject(job, 1)),
            close=kernel32.CloseHandle)

    @classmethod
    def create(cls):
        """A new empty job, or ``None`` (not Windows, or no job to be had)."""
        if sys.platform != "win32":
            return None
        try:
            api = cls.load_api()
            handle = api.create()
        except Exception:  # noqa: BLE001 - no job: taskkill is the kill
            return None
        return cls(api, handle) if handle else None

    def adopt(self, proc) -> bool:
        """Put the suspended *proc* in the job and resume it.

        ``False`` only when it could not be resumed. One that could not join
        the job runs anyway and the job is closed, so taskkill is its kill.
        Popen's own handle has every right CreateProcess grants; another is
        opened only for a Popen that keeps none.
        """
        process = getattr(proc, "_handle", None)
        opened = process is None
        resumed = False
        try:
            if opened:
                process = self.api.open_process(proc.pid)
            if process:
                if not self.api.assign(self.handle, process):
                    self.close()
                resumed = bool(self.api.resume(process))
        except Exception:  # noqa: BLE001 - settled by the caller: killed
            pass
        finally:
            if opened and process:
                try:
                    self.api.close(process)
                except Exception:  # noqa: BLE001
                    pass
        return resumed

    def terminate(self) -> bool:
        if not self.handle:
            return False
        try:
            return bool(self.api.terminate(self.handle))
        except Exception:  # noqa: BLE001 - the caller falls back to taskkill
            return False

    def close(self) -> None:
        handle, self.handle = self.handle, None
        if handle:
            try:
                self.api.close(handle)
            except Exception:  # noqa: BLE001 - a leaked handle is all it costs
                pass


def kill_tree(proc, drains, job=None) -> None:
    """Stop the tree, bounded: the child's job (else taskkill) on Windows, TERM
    then KILL on POSIX."""
    if sys.platform == "win32":
        # Kill the tree while its leader still exists. Terminating bash/uv
        # first loses taskkill's root and leaves the dispatcher running.
        if job is None or not job.terminate():
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=KILL_GRACE_S,
                )
            except (OSError, subprocess.SubprocessError):
                pass
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
        try:
            proc.wait(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            pass
        return
    _signal_group(proc, signal.SIGTERM)
    try:
        proc.wait(timeout=KILL_GRACE_S)
    except subprocess.TimeoutExpired:
        pass
    if proc.poll() is None or any(t.is_alive() for t in drains):
        # The leader outlived the grace, or a grandchild still holds a pipe.
        _signal_group(proc, getattr(signal, "SIGKILL", signal.SIGTERM))
        try:
            proc.wait(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            pass


# ---------------------------------------------------------------------------
# One tools/call
# ---------------------------------------------------------------------------

class Call:
    """Per-request state: the cancel event and everything the envelope echoes."""

    def __init__(self, request_id, args, token, meta=None):
        self.id = request_id
        self.args = args
        self.token = token
        self.meta = meta if isinstance(meta, dict) else {}
        self.cancel = threading.Event()
        self.anchor = None
        self.anchor_source = None
        self.shell_argv = None
        self.progress_n = 0
        self.progress_lines = None
        self.shown = set()
        self.relays = {"attempted": 0, "delivered": 0, "rejected": 0,
                       "unavailable": 0, "logged": 0}
        # The run in view, and whether this call claimed it (D3c).
        self.claimed = False
        self.run_id = None
        self.log = None
        self.watched = None
        self.polls = 0
        self.deadline = time.monotonic()
        self.hard_deadline = self.deadline

    def remaining(self) -> float:
        return self.deadline - time.monotonic()


class Server:
    def __init__(self, wire: Wire, environ=None):
        self.wire = wire
        # D9 layer 1: what codex handed us, snapshotted before anything is
        # written into os.environ, so `missing` and every override read reports
        # what was forwarded rather than what this server exported itself.
        self.layer1 = dict(os.environ if environ is None else environ)
        self.surface, self.surface_problem = load_surface()
        self.cap_s, self.allowlist, cap_problems = load_mcp_config()
        self.version = _plugin_version()
        self.initialized = False
        self.log_floor = LOG_LEVELS.index("info")
        self.client_roots = False
        self.roots_cache = None
        self._call_lock = threading.Lock()
        self._inflight = None
        self._pending_lock = threading.Lock()
        self._pending = {}
        self._next_request = 0
        self._deferred = []
        self.shell = None
        self.uv = None
        for problem in ([self.surface_problem] if self.surface_problem else []) + cap_problems:
            self.warn(problem)

    # -- diagnostics ---------------------------------------------------------

    def tool_name(self) -> str:
        return self.surface["tool_name"] if self.surface else DEGRADED_TOOL_NAME

    def notify_log(self, level: str, text: str) -> bool:
        """A ``notifications/message`` above the floor, once initialized."""
        if not self.initialized or LOG_LEVELS.index(level) < self.log_floor:
            return False
        return self.wire.send({
            "jsonrpc": "2.0", "method": "notifications/message",
            "params": {"level": level, "logger": self.tool_name(), "data": text},
        })

    def record_choice(self, text: str) -> None:
        """A decision the server made on the user's behalf: fd 2 and an info log."""
        _stderr(text)
        self.notify_log("info", text)

    def warn(self, text: str) -> None:
        _stderr(text)
        if self.initialized:
            self.notify_log("warning", text)
        else:
            self._deferred.append(text)

    # -- the read loop (main thread) -----------------------------------------

    def serve(self, stream) -> None:
        for raw in iter(stream.readline, b""):
            line = raw.strip()
            if line:
                self.handle_line(line)
        self.shutdown()

    def shutdown(self) -> None:
        """Stdin EOF: cancel whatever is in flight, wait for it, then exit."""
        with self._call_lock:
            call = self._inflight
        if call is not None:
            call.cancel.set()
            thread = getattr(call, "thread", None)
            if thread is not None:
                thread.join(ABORT_DISPATCH_TIMEOUT_S + 4 * KILL_GRACE_S + 10)
        with self._pending_lock:
            for slot in self._pending.values():
                slot["event"].set()

    def error(self, request_id, code: int, message: str) -> None:
        self.wire.send({"jsonrpc": "2.0", "id": request_id,
                        "error": {"code": code, "message": message}})

    def reply(self, request_id, result) -> None:
        self.wire.send({"jsonrpc": "2.0", "id": request_id, "result": result})

    def handle_line(self, line: bytes) -> None:
        try:
            message = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.error(None, PARSE_ERROR, "Parse error")
            return
        if not isinstance(message, dict):
            self.error(None, INVALID_REQUEST, "Invalid Request")
            return
        request_id = message.get("id")
        if "method" not in message:
            if "id" in message and ("result" in message or "error" in message):
                self.route_response(message)  # a reply to our own request
                return
            self.error(request_id, INVALID_REQUEST, "Invalid Request")
            return
        method = message.get("method")
        if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
            self.error(request_id, INVALID_REQUEST, "Invalid Request")
            return
        params = message.get("params")
        if "id" not in message:
            self.handle_notification(method, params)
            return
        try:
            self.handle_request(request_id, method, params, message)
        except Exception as error:  # noqa: BLE001 — rule 7: the loop survives
            _stderr("internal error handling {}: {!r}".format(method, error))
            self.error(request_id, -32603, "Internal error")

    def handle_notification(self, method, params) -> None:
        params = params if isinstance(params, dict) else {}
        if method == "notifications/initialized":
            self.initialized = True
            deferred, self._deferred = self._deferred, []
            for text in deferred:
                self.notify_log("warning", text)
        elif method == "notifications/cancelled":
            target = params.get("requestId")
            with self._call_lock:
                call = self._inflight
            # Per-request state: only the in-flight id cancels; anything else,
            # including a cancel landing after the return, is a no-op.
            if call is not None and _same_id(call.id, target):
                call.cancel.set()
        elif method == "notifications/roots/list_changed":
            self.roots_cache = None

    def handle_request(self, request_id, method, params, message) -> None:
        if method == "initialize":
            params = params if isinstance(params, dict) else {}
            requested = params.get("protocolVersion")
            capabilities = params.get("capabilities")
            self.client_roots = isinstance(capabilities, dict) and isinstance(
                capabilities.get("roots"), dict)
            self.roots_cache = None
            self.reply(request_id, {
                "protocolVersion": requested if requested in PROTOCOL_VERSIONS
                else DEFAULT_PROTOCOL_VERSION,
                "capabilities": {"tools": {}, "logging": {}},
                "serverInfo": {"name": self.tool_name(), "version": self.version},
            })
        elif method == "ping":
            self.reply(request_id, {})
        elif method == "tools/list":
            # One tool is the whole list: no nextCursor, and a cursor this server
            # never issued gets the same single-tool page.
            self.reply(request_id, {"tools": [self.tool_definition()]})
        elif method == "logging/setLevel":
            level = params.get("level") if isinstance(params, dict) else None
            if level not in LOG_LEVELS:
                self.error(request_id, INVALID_PARAMS, "Invalid params")
                return
            self.log_floor = LOG_LEVELS.index(level)
            self.reply(request_id, {})
        elif method == "tools/call":
            self.start_call(request_id, params)
        else:
            self.error(request_id, METHOD_NOT_FOUND, "Method not found")

    def tool_definition(self) -> dict:
        if self.surface is None:
            properties = {name: {"type": "string"}
                          for name in PROPERTIES + OPTIONAL_PROPERTIES}
            properties["extra_flags"] = {"type": "array", "items": {"type": "string"}}
            return {"name": DEGRADED_TOOL_NAME, "description": DEGRADED_DESCRIPTION,
                    "inputSchema": {"type": "object", "properties": properties,
                                    "required": list(PROPERTIES)}}
        described = self.surface["argument_descriptions"]
        properties = {name: {"type": "string", "description": described[name]}
                      for name in PROPERTIES + OPTIONAL_PROPERTIES}
        properties["extra_flags"] = {"type": "array", "items": {"type": "string"},
                                     "description": described["extra_flags"]}
        return {
            "name": self.surface["tool_name"],
            "description": self.surface["tool_description"],
            "inputSchema": {"type": "object", "properties": properties,
                            "required": list(PROPERTIES)},
        }

    # -- server → client requests (roots/list) --------------------------------

    def route_response(self, message) -> None:
        with self._pending_lock:
            slot = self._pending.get(message.get("id")) if isinstance(
                message.get("id"), str) else None
        if slot is None:
            return  # a response to nothing we asked: dropped in silence
        slot["response"] = message
        slot["event"].set()

    def ask_client(self, method: str, params, timeout: float):
        with self._pending_lock:
            self._next_request += 1
            request_id = "mllm-{}".format(self._next_request)
            slot = {"event": threading.Event(), "response": None}
            self._pending[request_id] = slot
        try:
            if not self.wire.send({"jsonrpc": "2.0", "id": request_id,
                                   "method": method, "params": params}):
                return None
            slot["event"].wait(max(0.0, timeout))
            return slot["response"]
        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    # -- tools/call: accept on the main thread, run on the worker -------------

    def start_call(self, request_id, params) -> None:
        if not isinstance(params, dict):
            self.error(request_id, INVALID_PARAMS, "Invalid params")
            return
        if params.get("name") != self.tool_name():
            self.error(request_id, INVALID_PARAMS,
                       "Unknown tool: {}".format(json.dumps(params.get("name"))))
            return
        args = params.get("arguments")
        meta = params.get("_meta")
        token = meta.get("progressToken") if isinstance(meta, dict) else None
        with self._call_lock:
            busy = self._inflight
            if busy is None:
                call = Call(request_id, args, token, meta)
                self._inflight = call
        if busy is not None:
            # Refused, never queued: a queued call spends its own budget waiting
            # and two dispatchers over one plan race on its result files.
            self.error(request_id, SERVER_BUSY,
                       "Server busy: tools/call {} is still in flight; one call "
                       "runs at a time.".format(json.dumps(busy.id)))
            return
        thread = threading.Thread(target=self.run_call, args=(call,), daemon=True)
        call.thread = thread
        thread.start()

    def run_call(self, call: Call) -> None:
        try:
            envelope = self.execute(call)
        except Exception as error:  # noqa: BLE001 — never throw out of a call
            _stderr("tools/call failed unexpectedly: {!r}".format(error))
            envelope = self.envelope(call, {
                "ok": False, "state": self.state_word("error"),
                "message": "the tool failed unexpectedly: {!r}".format(error),
            })
        # Cancellation handling is released *before* the return, so a cancel
        # landing on the teardown edge kills nothing and dispatches nothing.
        with self._call_lock:
            self._inflight = None
        text = json.dumps(envelope, ensure_ascii=False)
        self.reply(call.id, {"content": [{"type": "text", "text": text}],
                             "isError": not envelope.get("ok")})

    def state_word(self, key: str) -> str:
        if self.surface is None:
            return DEGRADED_STATE
        return self.surface["dispatcher"]["states"][key]

    def environment(self, call: Call) -> dict:
        """D3a's six keys, never partial. ``missing`` is a forwarding report."""
        return {
            "platform": sys.platform,
            "shell": list(call.shell_argv) if call.shell_argv else None,
            "login_shell": call.shell_argv is not None,
            "profile_shell": self.layer1.get("SHELL") or None,
            "interpreter": "{} ({})".format(
                sys.executable, ".".join(str(part) for part in sys.version_info[:3])),
            "missing": sorted(name for name in set(self.allowlist)
                              if name not in self.layer1),
        }

    def envelope(self, call: Call, fields: dict) -> dict:
        """Rule 5's one shape: the fields every branch carries, then the rest.

        Ordered for a reader that sees only part of it (:data:`WAY_FORWARD_KEYS`,
        :data:`LAST_KEYS`): ``ok`` and ``state``, then the way forward, then
        ``message`` and the other fields, and the runbook last.
        """
        def kept(key, value):
            # A null `user_next_step` is the answer "no next phase", set on
            # purpose by `finish`; every other null is an absent key.
            return value is not None or key == USER_NEXT_STEP_KEY

        out = {"ok": bool(fields.get("ok")), "state": fields.get("state")}
        for key in WAY_FORWARD_KEYS:
            if key in fields and kept(key, fields[key]):
                out[key] = fields[key]
        out["message"] = fields.get("message")
        if fields.get(COMMIT_BLOCKS_KEY) is not None:
            # A commit run's blocks, right under the message they belong to.
            out[COMMIT_BLOCKS_KEY] = fields[COMMIT_BLOCKS_KEY]
        out.update({"exit": fields.get("exit"),
                    "anchor": call.anchor, "anchor_source": call.anchor_source,
                    "environment": self.environment(call),
                    "relays": dict(call.relays), "progress_lines": call.progress_lines})
        for key, value in fields.items():
            if key not in out and key not in LAST_KEYS and kept(key, value):
                out[key] = value
        for key in LAST_KEYS:
            if fields.get(key) is not None:
                out[key] = fields[key]
        return out

    def refusal(self, call: Call, state_key: str, message: str) -> dict:
        """A pre-spawn refusal: the ordinary envelope, ``exit`` null, relays zeroed.

        An argument error (``state_key`` ``error``) is the model's own call to
        fix and goes out as it is; a needs-human refusal is finished like any
        other failed outcome (:meth:`finish`).
        """
        fields = {"ok": False, "state": self.state_word(state_key),
                  "message": message, "exit": None}
        if state_key != "error":
            self.finish(call, fields)
        return self.envelope(call, fields)

    def finish(self, call: Call, outcome: dict) -> dict:
        """What every outcome past argument validation owes the model (D3c).

        A failed or needs-human result says explicitly what the user can run
        (racing re-run 2026-10-04: a result with no command key at all, and the
        host model composed a next command of its own): ``user_next_step`` is
        null and, unless the result carries a ``resume_command``, the surface's
        ``no_command_reason`` says there is none, with its ``no_command`` clause
        on a dispatcher exit 3. A restated composed flag ``split_extra_flags``
        dropped is never named back (run 6, #10a/#14: the note was relayed to
        the user as "`--yes` was dropped from your flags"): it means what the
        call already does. Every sentence is the surface's; with no surface, or
        a key it lacks, only that sentence is lost. The port of
        ``finishOutcome``.
        """
        surface = self.surface
        if surface is None:
            return outcome
        if outcome.get("ok") is not False:
            return outcome
        outcome[USER_NEXT_STEP_KEY] = None
        if outcome.get("resume_command"):
            return outcome
        # No reason (2026-10-05) for a result that names a run and no `exit`
        # (`stop_report`: the run outlived the call, so "did not finish" is not
        # yet true), nor for a `status`/`abort` call whose output shows a
        # re-spelled command re-invoking a phase, which it would contradict.
        row = resolve_mode(call.args.get("mode"), surface) if call.args else None
        report = row is not None and not row.get("phase")
        if ((outcome.get("run_id") and outcome.get("exit") is None)
                or (report and shows_a_phase_command(outcome, surface))):
            return outcome
        reason = surface.get("no_command_reason")
        if isinstance(reason, str):
            outcome["no_command_reason"] = reason
        clause = (surface.get("needs_human_message") or {}).get("no_command")
        dispatcher = surface["dispatcher"]
        if (isinstance(clause, str)
                and outcome.get("state") == dispatcher["states"]["needs_human"]
                and outcome.get("exit") == dispatcher["exit_codes"]["needs_human"]):
            outcome["message"] = "{} {}".format(outcome.get("message") or "", clause)
        return outcome

    # -- the budget ------------------------------------------------------------

    def budget_s(self) -> float:
        cap = self.cap_s
        override = _positive_int(self.layer1.get("MLLM_TEST_POLL_BUDGET_MS"), None)
        if override is not None:
            cap = min(cap, override / 1000.0)  # a test override only shortens
        return cap

    # -- the anchor ladder (D3f) -------------------------------------------------

    def _usable_dir(self, value):
        if not isinstance(value, str) or not value:
            return None, "unset"
        expanded = os.path.expanduser(value)
        if not os.path.isabs(expanded):
            return None, "not an absolute path"
        resolved = os.path.realpath(expanded)
        if not os.path.isdir(resolved):
            return None, "not a directory"
        root = os.path.realpath(str(PLUGIN_ROOT))
        if resolved == root or resolved.startswith(root.rstrip(os.sep) + os.sep):
            return None, "the plugin's own install location"
        return resolved.rstrip(os.sep) or os.sep, None

    def _roots(self, call: Call):
        if self.roots_cache is None:
            timeout = min(ROOTS_TIMEOUT_S, max(0.0, call.remaining()))
            response = self.ask_client("roots/list", {}, timeout)
            result = response.get("result") if isinstance(response, dict) else None
            roots = result.get("roots") if isinstance(result, dict) else None
            if not isinstance(roots, list):
                return None
            self.roots_cache = roots
        return self.roots_cache

    def _workspace_candidates(self, call: Call):
        """Rung 2's paths, preferred first, and a note on the choice (D3f).

        One key is the workspace. Several: the one equal to or containing the
        ``PWD`` codex handed us (the most specific when more than one does) goes
        first, else codex's own first; the rest follow in codex's order.
        """
        workspaces = turn_metadata(call.meta).get(TURN_METADATA_WORKSPACES)
        if not isinstance(workspaces, dict):
            return [], "absent" if workspaces is None else "not an object"
        # A NUL cannot be in a path and makes os.path raise, so such a key is
        # malformed metadata and dropped with the non-strings.
        keys = [key for key in workspaces
                if isinstance(key, str) and key and "\x00" not in key]
        if not keys:
            return [], "no workspaces"
        if len(keys) == 1:
            return keys, None
        pwd = self.layer1.get("PWD")
        pwd = os.path.realpath(pwd) if isinstance(pwd, str) and os.path.isabs(pwd) else None
        best = None
        for key in keys:
            if not os.path.isabs(key) or pwd is None:
                continue
            real = os.path.realpath(key).rstrip(os.sep) or os.sep
            if pwd == real or pwd.startswith(real.rstrip(os.sep) + os.sep):
                if best is None or len(real) > len(os.path.realpath(best)):
                    best = key
        chosen = best if best is not None else keys[0]
        ordered = [chosen] + [key for key in keys if key != chosen]
        note = "{} workspaces; chose {} ({})".format(
            len(keys), json.dumps(chosen),
            "it holds PWD" if best is not None else "the first; none holds PWD")
        return ordered, note

    def resolve_anchor(self, call: Call):
        """``(anchor, source, probed)``; the first green rung wins, never the process cwd."""
        probed = []
        if self.client_roots:
            roots = self._roots(call)
            note = "no answer to roots/list" if roots is None else "no roots"
            for root in roots or []:
                uri = root.get("uri") if isinstance(root, dict) else None
                parsed = urlparse(uri) if isinstance(uri, str) else None
                if parsed is None or parsed.scheme != "file":
                    note = "the first root is not a file:// URI"
                else:
                    path, note = self._usable_dir(file_uri_path(parsed))
                    if path:
                        return path, "roots", probed
                break  # the first root is the anchor, or nothing is
            probed.append("roots ({})".format(note))
        else:
            probed.append("roots (not offered by the client)")
        candidates, note = self._workspace_candidates(call)
        skipped = []
        for candidate in candidates:
            path, problem = self._usable_dir(candidate)
            if path:
                if note or skipped:
                    # Several workspaces, or the preferred one unusable: the
                    # choice is recorded where the user and the host can see it.
                    parts = ([note] if note else []) + skipped
                    if skipped:
                        parts.append("took {}".format(json.dumps(candidate)))
                    self.record_choice(
                        "anchor from turn-metadata: {}".format("; ".join(parts)))
                return path, "turn-metadata", probed
            skipped.append("skipped {} ({})".format(json.dumps(candidate), problem))
        if candidates:
            probed.append("turn-metadata ({})".format("; ".join(skipped)))
        else:
            probed.append("turn-metadata ({})".format(note))
        for name in WORKSPACE_ENV_NAMES:
            path, note = self._usable_dir(self.layer1.get(name))
            if path:
                return path, "env:" + name, probed
            probed.append("env:{} ({})".format(name, note))
        return None, None, probed

    # -- execute: validate → anchor → refusals → preflight → the loop ----------

    def execute(self, call: Call) -> dict:
        start = time.monotonic()
        budget = self.budget_s()
        call.hard_deadline = start + budget
        call.deadline = call.hard_deadline - min(RESERVE_MAX_S, budget * RESERVE_FRACTION)
        call.anchor, call.anchor_source, probed = self.resolve_anchor(call)
        if self.surface is None:
            return self.refusal(call, "needs_human", "{} {}".format(
                DEGRADED_DESCRIPTION, self.surface_problem or ""))
        surface = self.surface
        call.args = with_absent_question(call.args)
        row, problem = validate_args(call.args, surface)
        if problem:
            return self.refusal(call, "error", problem)
        kept_flags, _dropped, _refused = split_extra_flags(
            call.args["extra_flags"], surface)
        if call.anchor is None:
            return self.refusal(call, "needs_human", fill(
                surface["anchor_unresolved"], {"probed": ", ".join(probed)}))
        args = call.args
        posture = surface["write_posture_refusal"]
        session = session_posture(call.meta)
        if row.get("writes_worktree") and session not in POSTURES_ALLOWING_WRITES \
                and self.layer1.get(posture["lever_env"]) != posture["lever_value"]:
            # D3b: the posture is read per call from codex's turn metadata. A
            # read-only session refuses; a posture that is absent or not a word
            # this server knows is treated as read-only (fail closed). Only a
            # session that may itself write lets the tool write. The lever is
            # read from layer 1 (what codex forwarded), never a login profile:
            # it must be in codex's own environment, not ~/.profile.
            return self.refusal(call, "needs_human", fill(posture["template"], {
                "mode": args["mode"],
                "posture": session or posture["posture_unreadable"]}))
        self.shell = self.find_shell()
        if self.shell is None:
            return self.refusal(call, "needs_human", fill(surface["shell_missing"], {
                "shell": SHELL_NAME, "platform": sys.platform,
                "path": self.layer1.get("PATH", "")}))
        uv = find_uv(surface, self.layer1)
        if uv is None:
            return self.refusal(call, "needs_human", uv_missing_text(surface))
        # D5 row 2 / rule 7: a partial payload is refused by name before any
        # spawn, so a missing lockfile never reaches uv (or a --no-sync override).
        missing = missing_payload(surface)
        if missing is not None:
            return self.refusal(call, "needs_human", payload_missing_text(missing))
        self.uv = uv
        # D9 layer 2: the resolved uv (the detached worker reuses it), the
        # skill dir, and the route signal (both strings from the surface, so
        # a finished phase's next command is spelled for this route). The
        # child inherits os.environ whole; no env= is passed, so every child
        # this call spawns — launch, polls, abort, runbook — carries all three.
        os.environ[surface["uv"]["env"]] = uv
        os.environ[SKILL_DIR_ENV] = str(SKILL_DIR)
        route_env = surface["dispatcher"]["route_env"]
        os.environ[route_env["name"]] = route_env["value"]
        if NO_BYTECODE_ENV not in os.environ:
            os.environ[NO_BYTECODE_ENV] = "1"
        model = self.export_session_model(call)
        self.export_host_posture(call)
        values = {"word": args["mode"], "plan": self.normalize_plan(args["plan"], call),
                  "plan_arg": self.plan_spelling(args["plan"]),
                  "pinned_plan": is_pinned_range(args["plan"], surface),
                  # The range as typed, never resolved here: the dispatcher
                  # resolves it, and the launch's result line pins it.
                  REVS: args.get(REVS) or "",
                  # What validation forwards: a restated composed flag is
                  # dropped quietly (`split_extra_flags`).
                  "question": args["question"], "extra": list(kept_flags)}
        outcome = self.run_workflow(call, row, values)
        hand_back_typed(outcome, values)
        self.attach_commit_blocks(call, values, outcome)
        if not call.cancel.is_set():
            self.attach_resume(call, values, outcome)
        if not call.cancel.is_set() and self.unfinished(row, outcome):
            self.attach_runbook(call, row, outcome)
        if model is not None:
            outcome["session_model"] = model
        return self.envelope(call, self.finish(call, outcome))

    def export_session_model(self, call: Call):
        """D9 layer 2: this turn's model for the ladder's ``session`` rung, or ``None``.

        Per call, because ``os.environ`` outlives the call: a turn naming no
        usable model gets back exactly what codex forwarded. A model the turn
        did name but ``SESSION_MODEL_PATTERN`` refused (``gpt-oss:20b`` under
        ``codex --oss``) is logged by value, so the fallback is never silent.
        """
        name = self.surface["dispatcher"]["session_model_env"]
        model = session_model(call.meta)
        if model is not None:
            os.environ[name] = model
            return model
        if name in self.layer1:
            os.environ[name] = self.layer1[name]
        else:
            os.environ.pop(name, None)
        refused = turn_metadata(call.meta).get(TURN_METADATA_MODEL)
        if refused is not None:
            shown = json.dumps(refused)
            if len(shown) > 80:
                shown = shown[:77] + "..."
            self.record_choice(
                "turn-metadata model {} refused (not a plain model id); {}".format(
                    shown, "the session rung keeps the forwarded " + name
                    if name in self.layer1
                    else "the subagent runner falls back past the session rung"))
        return model

    def export_host_posture(self, call: Call):
        """F5 (plan step 6): this turn's sandbox posture for the dispatcher, or ``None``.

        Per call, because ``os.environ`` outlives the call: the value is the
        turn metadata's ``sandbox_mode`` when it is one of codex's own posture
        words (``session_posture`` validates it), and otherwise the variable is
        removed — never inherited from an earlier call or from what codex
        forwarded, since only the chat's own posture is consent.
        """
        posture = session_posture(call.meta)
        if posture is not None:
            os.environ[HOST_SANDBOX_POSTURE_ENV] = posture
        else:
            os.environ.pop(HOST_SANDBOX_POSTURE_ENV, None)
        return posture

    def find_shell(self):
        path = self.layer1.get("PATH") or os.defpath
        if sys.platform == "win32":
            found = windows_bash(path)
        else:
            found = shutil.which(SHELL_NAME, path=path)
        if found:
            return os.path.abspath(found)
        fallback = self.layer1.get("MLLM_TEST_FALLBACK_SHELL") or FALLBACK_SHELL
        return fallback if _is_file(fallback) and os.access(fallback, os.X_OK) else None

    def plan_spelling(self, plan: str) -> str:
        """The plan as the user spelled it: ``~`` expanded, **nothing resolved**.

        ``normalize_plan``'s absolute path is what this server names the file
        by, and it used to be the string the dispatcher received, recorded as
        ``plan_arg`` and printed in every next command (2026-10-02, issue #15: a
        user who typed ``plans/racing-game.md`` was told to type ``$multi-llm:
        multi-llm --implement <absolute path>/plans/racing-game.md``). The child runs in
        the anchor, so a relative spelling names the same file there, and the
        launch passes this one; the polls and the abort keep the absolute path
        inside this server, and the tool calls it hands back carry this one
        (:func:`hand_back_typed`).
        """
        return expand_home(plan, self.layer1) if plan else ""

    def normalize_plan(self, plan: str, call: Call) -> str:
        """A relative plan resolved against the anchor, ``~`` expanded. One the
        dispatcher runs from the repository root is renamed by the root's file
        once its result line says so (:func:`plan_from_root`). A pinned range
        (a commit run's re-attach or abort) is passed on as it is: it names a
        brief by name, and joined to the anchor it would name nothing."""
        if not plan:
            return ""
        if is_pinned_range(plan, self.surface):
            return plan
        expanded = self.plan_spelling(plan)
        if os.path.isabs(expanded):
            return expanded
        return os.path.normpath(os.path.join(call.anchor, expanded))

    # -- argv composition (D3 rule 3) ---------------------------------------------

    def dispatcher_argv(self, row, values) -> list:
        surface = self.surface
        kinds = surface["positional_kinds"]
        argv = [values.get("word") or row["name"]]  # aliases travel unexpanded
        for kind in row["positionals"]:
            if kind == kinds["plan"]:
                if values.get("plan"):
                    # The user's own spelling when the caller kept one, else the
                    # resolved path (see `plan_spelling`).
                    argv.append(values.get("plan_arg") or values["plan"])
            elif kind == kinds["question"]:
                if values.get("question"):
                    argv.append(values["question"])
            elif kind == kinds["revs"]:
                # The range as typed, its words right after the mode and never
                # resolved as a file; none means HEAD (`revs_words`).
                argv.extend(revs_words(values.get(REVS), surface))
            else:
                # `validate_args` refuses such a row first; a kind this server
                # cannot compose is never dropped from the argv in silence.
                raise ValueError("mode {!r} declares a positional this server cannot "
                                 "compose: {!r}".format(row["name"], kind))
        argv.extend(surface["baked_flags"])
        if row.get("supports_detach"):
            argv.append(surface["detach_flag"])
        argv.extend(values.get("extra") or [])
        return argv

    def uv_run_args(self) -> list:
        """``MULTI_LLM_UV_RUN_ARGS`` replaces the surface's list; ASCII-whitespace split."""
        uv = self.surface["uv"]
        override = (self.layer1.get(uv["run_args_env"]) or "").strip(" \t\n\r\f\v")
        if override:
            return re.split(r"[ \t\n\r\f\v]+", override)
        return list(uv["default_run_args"])

    def spawn_argv(self, dispatcher_argv) -> list:
        script = str(SKILL_DIR / self.surface["dispatcher"]["script"])
        return ([self.uv, "run"] + self.uv_run_args()
                + ["--project", str(SKILL_DIR), "--", "python", script]
                + list(dispatcher_argv))

    def status_argv(self, extra, plan) -> list:
        poll_word = self.surface["dispatcher"]["poll"][0]
        row = resolve_mode(poll_word, self.surface)
        return self.dispatcher_argv(row, {"word": row["name"], "plan": plan,
                                          "question": "", "extra": extra})

    # -- one child ------------------------------------------------------------------

    def run_child(self, call: Call, dispatcher_argv, timeout_s: float,
                  cancellable: bool = True) -> ChildRun:
        """Spawn ``[bash, -lc, CONST, bash, anchor, *argv]`` and supervise it.

        One shell at this one site, an argv list, ``shell=False``, its own
        session (so the kill reaches uv's python grandchild; on Windows, its
        own Job Object, :class:`WindowsJob`), stdin from /dev/null (fd 0 is
        the protocol's read half), both pipes drained by their own threads so
        a chatty child can never fill one.
        """
        argv = self.spawn_argv(dispatcher_argv)
        run = ChildRun(argv)
        prefix = [self.shell, "-lc", LOGIN_SHELL_SCRIPT, SHELL_NAME]
        job = WindowsJob.create()
        try:
            proc = subprocess.Popen(
                prefix + [call.anchor] + argv, shell=False, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True, close_fds=True,
                creationflags=CREATE_SUSPENDED if job is not None else 0)
        except (OSError, ValueError) as error:
            if job is not None:
                job.close()
            run.spawn_error = str(error)
            return run
        if job is not None and not job.adopt(proc):
            # Created suspended and never resumed: nothing ran, and nothing may
            # be left waiting suspended.
            job.close()
            proc.kill()
            for pipe in (proc.stdout, proc.stderr):
                _close_quietly(pipe)
            try:
                proc.wait(timeout=KILL_GRACE_S)
            except subprocess.TimeoutExpired:
                pass
            run.spawn_error = ("the shell was created suspended to enter its Job "
                               "Object, and could not be resumed")
            return run
        call.shell_argv = prefix
        try:
            return self.supervise_child(call, run, proc, job, timeout_s, cancellable)
        finally:
            if job is not None:
                job.close()

    def supervise_child(self, call: Call, run: ChildRun, proc, job, timeout_s: float,
                        cancellable: bool) -> ChildRun:
        """:meth:`run_child` from the spawn on: drain, wait, kill, collect."""
        dispatcher = self.surface["dispatcher"]
        fields = dispatcher["banner"].get("fields") or [dispatcher["banner"]["run_id_field"]]
        banner_re = re.compile(
            r"^\s*(" + "|".join(re.escape(f) for f in fields) + r"):\s*(.+?)\s*$")
        out_tail, err_tail = _Tail(STDOUT_TAIL_CHARS), _Tail(STDERR_TAIL_CHARS)
        drains = [
            threading.Thread(target=_drain_stdout, daemon=True, args=(
                proc.stdout, run, dispatcher["result_marker"], banner_re, out_tail)),
            threading.Thread(target=_drain_stderr, daemon=True,
                             args=(proc.stderr, err_tail)),
        ]
        for thread in drains:
            thread.start()
        until = time.monotonic() + max(0.0, timeout_s)
        while True:
            if proc.poll() is not None and not any(t.is_alive() for t in drains):
                break
            if cancellable and call.cancel.is_set():
                run.cancelled = True
                break
            if time.monotonic() >= until:
                run.timed_out = True
                break
            if cancellable:
                call.cancel.wait(0.02)
            else:
                time.sleep(0.02)
        if run.cancelled or run.timed_out:
            kill_tree(proc, drains, job)
        for thread in drains:
            # A drain still blocked after the grace is abandoned, never waited on.
            # Each drain closes its own pipe on exit; closing it here would block
            # on the reader's lock while an abandoned drain is still inside a read.
            thread.join(KILL_GRACE_S if (run.cancelled or run.timed_out) else None)
        code = proc.poll()
        run.code = code if (code is not None and code >= 0 and not (
            run.cancelled or run.timed_out)) else None
        if code is not None and code < 0 and not (run.cancelled or run.timed_out):
            run.signal = -code  # e.g. an OOM kill: `code` stays None, the cause is kept
        run.stdout, run.stderr = out_tail.text(), err_tail.text()
        run.truncated = run.truncated or out_tail.truncated
        return run

    # -- progress (D3d) ----------------------------------------------------------------

    def relay(self, call: Call, child: ChildRun) -> None:
        """One relay point: progress notification, log notification, counters."""
        result = child.result or {}
        update = redact({"progress": result.get("progress"),
                         "lines": result.get("progress_lines"),
                         "run_id": call.run_id, "log": call.log, "polls": call.polls},
                        None, self.surface)
        supplied = update["lines"] if isinstance(update["lines"], list) else []
        fresh = []
        for line in supplied:
            if isinstance(line, str) and line and line not in call.shown:
                call.shown.add(line)
                fresh.append(line)
        if supplied:
            call.progress_lines = [line for line in supplied if isinstance(line, str)]
        text = "\n".join(fresh) if fresh else json.dumps(update)
        call.relays["attempted"] += 1
        if call.token is not None:
            call.progress_n += 1
            sent = self.wire.send({
                "jsonrpc": "2.0", "method": "notifications/progress",
                "params": {"progressToken": call.token, "progress": call.progress_n,
                           "message": text}})
            call.relays["delivered" if sent else "rejected"] += 1
        else:
            call.relays["unavailable"] += 1
        if self.notify_log("info", text):
            call.relays["logged"] += 1

    # -- S1–S6 -------------------------------------------------------------------------

    def run_workflow(self, call: Call, row, values) -> dict:
        surface = self.surface
        dispatcher = surface["dispatcher"]
        codes = dispatcher["exit_codes"]
        banner = dispatcher["banner"]
        call.watched = values

        def cycle(cycle_row, cycle_values):
            # A pinned re-attach names its run before the blocking wait, so a
            # wait that eats the whole budget still hands that run off.
            pinned = (None if cycle_row.get("supports_detach")
                      else self.pinned_reattach_id(cycle_values))
            # S1 — the launch child. Its result line is a handshake, not the answer.
            launch = self.run_child(call, self.dispatcher_argv(cycle_row, cycle_values),
                                    call.remaining())
            if launch.spawn_error:
                return "spawn-error", self.error_result(
                    call, launch, "could not start the dispatcher: {}".format(
                        launch.spawn_error))
            # Fix round 27: the plan the dispatcher read, before any poll,
            # abort or option names it.
            plan_from_root(launch.result, cycle_values, call.anchor,
                           dispatcher.get("ran_from_root_key"))
            if takes_revs(cycle_row, surface):
                # A range mode's run is named by the range the launch pinned,
                # never by the phrase the call typed.
                self.pin_commit_range(launch.result, cycle_values, call.anchor)
            if cycle_row.get("supports_detach"):
                # S2 — the run id, off the banner and nothing else (rule f).
                launched = launch.banner.get(banner["run_id_field"])
                if launched:
                    call.run_id, call.claimed = launched, True
                    call.log = launch.banner.get(banner["log_field"])
                    call.watched = cycle_values
                    if not call.cancel.is_set():
                        self.relay(call, launch)
                if launch.cancelled or launch.timed_out or launch.code != codes["ok"]:
                    if launched and launch.cancelled:
                        return "return", self.stop_report(
                            call, "the call was cancelled while the launch was "
                                  "still running")
                    if launched and launch.timed_out:
                        return "return", self.handoff(call)
                    if launched:
                        return "return", self.stop_report(
                            call, "the launch exited {} after reporting a run".format(
                                launch.code))
                    return "return", self.terminal_result(call, launch, cycle_values)
                if not launched:
                    return "return", self.error_result(
                        call, launch, "the launch reported no run id on its banner, "
                        "so the run cannot be polled or aborted safely. Refusing to "
                        "adopt whatever run is newest.")
            else:
                # S0's foreground child; a pinned view of a live run re-attaches.
                if pinned is not None and launch.timed_out:
                    call.run_id, call.claimed = pinned, False
                    call.log = launch.banner.get(banner["log_field"])
                    call.watched = cycle_values
                    return "return", self.handoff(call)
                adopted = self.reattached_run_id(launch, cycle_values)
                if adopted is None:
                    return "return", self.terminal_result(call, launch, cycle_values)
                call.run_id, call.claimed = adopted, False
                call.log = launch.banner.get(banner["log_field"])
                call.watched = cycle_values
            # S3 — the poll, pinned to the run id, one blocking child per turn.
            poll_argv = self.status_argv(
                list(dispatcher["poll"][1:]) + [dispatcher["run_id_option"], call.run_id],
                call.watched.get("plan"))
            while True:
                if call.cancel.is_set():
                    return "return", self.stop_report(call, "the call was cancelled")
                remaining = call.remaining()
                if remaining <= 0:
                    return "return", self.handoff(call)
                # The remaining budget only: see CANCEL_LATENCY_BOUND_S for why
                # a poll is never cut at the cancellation bound.
                poll = self.run_child(call, poll_argv, remaining)
                call.polls += 1
                if poll.spawn_error:
                    return "return", self.error_result(
                        call, poll, "could not poll: {}".format(poll.spawn_error),
                        with_run=True)
                if poll.cancelled:
                    return "return", self.stop_report(call, "the call was cancelled")
                if poll.timed_out:
                    continue  # the budget ran out mid-poll: the loop hands off
                # S4 — the exit map is the loop condition.
                if poll.code != codes["nothing_to_do"]:
                    break
                self.relay(call, poll)  # never the terminal poll
            terminal = self.terminal_result(call, poll, call.watched)
            # `argv` names what this call ran: the launch, never the internal
            # `status … --wait --run-id` poll whose answer this is. The model
            # was told to report `argv` as "what was being run" (it is told the
            # phase and the plan since fix round 19), and on Codex racing
            # re-run 5 it told the user the poll was "the dispatcher's final
            # argv" (fix round 14). The poll is not the user's business.
            terminal["argv"] = launch.argv
            terminal["launch_state"] = (launch.result or {}).get("state")
            return "terminal", terminal

        kind, outcome = cycle(row, values)
        if kind != "terminal":
            return outcome
        # S5 — a mechanical continuation is re-composed and driven here; every
        # other next is returned as tool-call args, never run.
        cap = _positive_int(self.layer1.get("MLLM_TEST_NEXT_CAP"), DEFAULT_CONTINUATION_CAP)
        followed = 0
        while (outcome.get("ok") and followed < cap and not call.cancel.is_set()
               and is_mechanical(outcome.get("next"), surface)):
            args = outcome["next"]
            checked, problem = validate_args(args, surface)
            if problem:
                outcome["next"] = {
                    "unparseable": True,
                    "note": "The dispatcher returned a follow-up this tool refused "
                            "to run: {} It is reported rather than executed. Do not "
                            "run it in a shell.".format(problem)}
                break
            followed += 1
            planned = self.normalize_plan(args["plan"], call)
            kind, following = cycle(checked, {
                "word": args["mode"], "plan": planned,
                # The dispatcher's `next` names the plan absolutely; when that is
                # the plan this call was typed with, the continuation keeps the
                # user's spelling so its own next-phase command does too.
                "plan_arg": (values.get("plan_arg")
                             if same_plan_file(planned, values.get("plan")) else ""),
                REVS: args.get(REVS) or "",
                "question": args["question"], "extra": list(args["extra_flags"])})
            if kind == "spawn-error":
                break
            if kind == "return":
                return following
            outcome = following
            outcome["continuations"] = followed
        if followed >= cap and is_mechanical(outcome.get("next"), surface):
            return self.stop_report(call, "the continuation cap of {} was reached".format(cap))
        return outcome

    def pinned_reattach_id(self, values):
        """The run a pinned poll-mode view names, known before its child runs.

        Only the poll mode's own word counts (its aliases are abort spellings),
        and never alongside the abort flag: an abort that times out is not a
        watch to hand off.
        """
        surface = self.surface
        dispatcher = surface["dispatcher"]
        if values.get("word") != dispatcher["poll"][0]:
            return None
        extra = values.get("extra") or []
        exacts = surface["reserved_flags"].get("exact_options", [])
        abort_flags = list(dispatcher["abort"][1:])
        if any(flag_matches(token.partition("=")[0], flag, exacts)
               for token in extra for flag in abort_flags):
            return None
        return pinned_run_id(extra, surface)

    def reattached_run_id(self, child: ChildRun, values):
        """The run a pinned ``status`` view re-attached to, while it is live."""
        surface = self.surface
        if child.code != surface["dispatcher"]["exit_codes"]["nothing_to_do"]:
            return None
        if pinned_run_id(values.get("extra") or [], surface) is None:
            return None
        raw = (child.result or {}).get("next")
        if not isinstance(raw, str) or not raw:
            return None
        parsed = parse_dispatcher_command(raw, surface)
        poll_mode = resolve_mode(surface["dispatcher"]["poll"][0], surface)
        if parsed is None or poll_mode is None or parsed["mode"] != poll_mode["name"]:
            return None
        return pinned_run_id(parsed["extra_flags"], surface)

    def abort_args(self, call: Call) -> dict:
        """The explicit abort spelling, as tool-call args (never the alias).

        A range mode's run is named by its pinned range (`pin_commit_range`),
        which ``status`` maps to the brief by name: never the phrase typed.
        """
        dispatcher = self.surface["dispatcher"]
        word, flags = dispatcher["abort"][0], list(dispatcher["abort"][1:])
        return {"mode": word, "plan": watched_plan(call.watched),
                "question": "", "extra_flags": flags + [dispatcher["run_id_option"],
                                                        call.run_id]}

    def reattach_args(self, call: Call) -> dict:
        dispatcher = self.surface["dispatcher"]
        return {"mode": dispatcher["poll"][0], "plan": watched_plan(call.watched),
                "question": "", "extra_flags": list(dispatcher["poll"][1:]) + [
                    dispatcher["run_id_option"], call.run_id]}

    def pin_commit_range(self, result, values, anchor) -> None:
        """Name a range mode's run by the range its launch resolved.

        The launch's result line carries ``commit_range`` (the surface's
        ``revs.range_key``): the full ``base`` and ``head``, and the ``brief``
        path as the dispatcher printed it, relative to the directory it ran
        from. From it, *values* gains ``pinned``, the spelling every tool call
        handed back names the run by (``<base12>..<head12>``, shaped by the
        surface's ``revs.pinned``; the brief path for a root range, which has no
        base), and the brief as the plan the polls and the abort dispatch name
        absolutely (``plan``) and as printed (``plan_arg``, which the
        ``--blocked`` lookup takes: ``util next-command`` reads a file). The
        typed phrase names none of them, so a re-attach never resolves
        ``last 2 commits`` again against a moved ``HEAD``
        (plans/review-commits.md §2.8, §2.9). The record itself is kept for the
        block (:meth:`attach_commit_blocks`). A launch without the key pins
        nothing.
        """
        shape = self.surface["revs"]
        record = result.get(shape["range_key"]) if isinstance(result, dict) else None
        if not isinstance(record, dict):
            return
        values["commit_range"] = record
        brief = record.get("brief")
        brief = brief if isinstance(brief, str) and brief else None
        base, head = record.get("base"), record.get("head")
        chars, separator = shape["pinned"]["sha_chars"], shape["pinned"]["separator"]
        if isinstance(base, str) and base and isinstance(head, str) and head:
            values["pinned"] = base[:chars] + separator + head[:chars]
        elif brief:
            values["pinned"] = brief
        if brief:
            ran_from = dispatcher_cwd(result, anchor,
                                      self.surface["dispatcher"].get("ran_from_root_key"))
            values["plan"] = (brief if os.path.isabs(brief)
                              else os.path.normpath(os.path.join(ran_from, brief)))
            values["plan_arg"] = brief

    def attach_commit_blocks(self, call: Call, values, outcome) -> None:
        """The commit run's blocks, relayed once in ``commit_blocks``.

        A tool route renders the commit block and the ``[COMMIT_FIXES]`` block
        from the result line (plans/review-commits.md §2.3, "Relay"): the
        launch printed the first before it detached and the terminal poll
        answers for the run, so the block is in no ``output`` this call keeps.
        Each record (the surface's ``revs.range_key`` and ``revs.fixes_key``)
        carries its block as the run printed it (``revs.lines_key``), which is
        what is relayed: this file composes none of it. The commit block comes
        from the terminal payload when it has one (a launch that stopped after
        printing it), else from the launch this call watched; ``[COMMIT_FIXES]``
        from the terminal payload (``status`` reads it off the saved guard).
        Moved, not copied: the lines leave the parsed result, and a block the
        terminal child also printed leaves ``output``.
        """
        shape = self.surface["revs"]
        lines_key = shape["lines_key"]
        payload = outcome.get("result") if isinstance(outcome.get("result"), dict) else {}
        launched = (call.watched or values or {}).get("commit_range")
        blocks = []
        for key, fallback in ((shape["range_key"], launched), (shape["fixes_key"], None)):
            record = payload.get(key)
            lines = record.get(lines_key) if isinstance(record, dict) else None
            if isinstance(record, dict):
                record.pop(lines_key, None)
            if not isinstance(lines, list) and isinstance(fallback, dict):
                lines = fallback.get(lines_key)
            if (isinstance(lines, list) and lines
                    and all(isinstance(line, str) for line in lines)):
                blocks.append(redact(list(lines), None, self.surface))
        if not blocks:
            return
        output = outcome.get("output")
        if isinstance(output, str):
            kept = output.split("\n")
            for block in blocks:
                for index in range(len(kept) - len(block) + 1):
                    if kept[index:index + len(block)] == block:
                        del kept[index:index + len(block)]
                        break
            outcome["output"] = "\n".join(kept).strip("\n")
        outcome[COMMIT_BLOCKS_KEY] = "\n".join(line for block in blocks for line in block)

    def handoff(self, call: Call) -> dict:
        """The budget expired: the run is left ALIVE and named (D3c's re-decided edge).

        No abort dispatch, claimed or not. The claim was already released by
        reaching here; the re-attach ``next`` is how the run is picked up, and a
        chain of re-attaches hands off again rather than ever aborting.
        """
        return {
            # ok: the run is alive and re-attachable; an error flag would invite
            # the model to give up on it or to retry the launch.
            "ok": True, "state": self.surface["dispatcher"]["states"]["running"], "exit": None,
            "run_id": call.run_id, "log": call.log, "polls": call.polls,
            "next": self.reattach_args(call), "abort_dispatched": False,
            "abort_command": self.abort_args(call),
            "message": "This call's time budget ran out while the detached run "
                       "{} was still going, so it was left running, untouched. Send "
                       "the `next` tool call exactly as given to keep watching it; "
                       "stop it only with the `abort_command` tool call.{}".format(
                           call.run_id,
                           " Log: {}.".format(call.log) if call.log else ""),
        }

    def stop_report(self, call: Call, reason: str) -> dict:
        """Cancellation or the continuation cap: abort a claimed run, else leave it."""
        if not call.claimed:
            # A re-attach claims nothing: supervision stops, the run keeps going.
            return {
                "ok": False, "state": self.state_word("needs_human"), "exit": None,
                "reason": reason, "run_id": call.run_id, "log": call.log,
                "abort_dispatched": False, "abort_command": self.abort_args(call),
                "message": "{}. The run {} was not started by this call, so it was "
                           "left running rather than stopped.{} Watch it again by "
                           "sending this call again, or stop it with the "
                           "`abort_command` tool call in this result.".format(
                               reason, call.run_id,
                               " Log: {}.".format(call.log) if call.log else ""),
            }
        codes = self.surface["dispatcher"]["exit_codes"]
        stopped = (codes["ok"], codes["nothing_to_do"])
        # Sent after the kill ladder returned, signal-free, under its own timeout.
        out = self.run_child(call, self.status_argv(
            list(self.surface["dispatcher"]["abort"][1:])
            + [self.surface["dispatcher"]["run_id_option"], call.run_id],
            (call.watched or {}).get("plan")), ABORT_DISPATCH_TIMEOUT_S, cancellable=False)
        dispatched = (not out.spawn_error and out.code in stopped and out.result is not None
                      and out.result.get("exit") in stopped)
        return {
            "ok": False, "state": self.state_word("needs_human"), "exit": None,
            "reason": reason, "run_id": call.run_id, "log": call.log,
            "abort_dispatched": dispatched, "abort_command": self.abort_args(call),
            "message": "{}. The detached run {} was {}. {}{}If it is still alive, "
                       "stop it with the `abort_command` tool call in this result."
                       .format(reason, call.run_id,
                               "confirmed aborted" if dispatched
                               else "NOT confirmed aborted",
                               "The abort dispatch timed out and was killed. "
                               if out.timed_out else "",
                               "Log: {}. ".format(call.log) if call.log else ""),
        }

    # -- S4/S5: results -------------------------------------------------------------------

    def human_output(self, child: ChildRun, command, respell=None, carried=False):
        """Redacted stdout, the result line dropped only when it parsed.

        With *carried* (the result carries the lifted ``user_next_step``), the
        block's lines that step says itself are dropped too (fix round 27, the
        Fable review of round 26: the manual note and the optional whys
        reached the model twice, in ``output`` and in the step's
        ``markdown``): a line that is one of the surface's
        ``dispatcher.next_step_markers``, or starts with one and a space. A
        ``[RUNNER_WARNING]`` line, which the step does not carry, stays.
        """
        text = redact(child.stdout, command, self.surface, respell)
        if not text or child.result is None:
            return text.rstrip() if text else text
        dispatcher = self.surface["dispatcher"]
        marker = dispatcher["result_marker"]
        said = tuple(dispatcher.get("next_step_markers") or ()) if carried else ()
        return "\n".join(
            line for line in text.split("\n")
            if not line.strip().startswith(marker)
            and not any(line == block or line.startswith(block + " ") for block in said)
        ).rstrip()

    def tool_calls_for(self, child: ChildRun, values=None) -> list:
        """Every runnable command the child printed, as tool-call args, once each.

        The plan is put back the way this call typed it when it is the call's
        own plan file (the dispatcher prints it absolute), and two lines that
        name the same call — a failed run's retry hint and ``status``'s
        ``resume with:`` differ only in flags this tool composes — are one
        option (racing re-run 2026-10-04).
        """
        raw = (child.result or {}).get("next")
        commands = [raw] if isinstance(raw, str) and raw else []
        # A command a quote cut short is reported, never offered: its parse
        # would carry the truncated value (`cut_mid_token`).
        commands.extend(
            None if cut_mid_token(found) else found.group(0)
            for found in runnable_pattern(self.surface).finditer(
                "{}\n{}".format(child.stdout or "", child.stderr or "")))
        seen, calls = set(), []
        for command in commands:
            call_args = (unparseable_call() if command is None
                         else next_as_tool_call(command, self.surface))
            if call_args is None:
                continue
            if not call_args.get("unparseable"):
                call_args["plan"] = typed_plan(call_args["plan"], values)
            key = json.dumps(call_args, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            calls.append(call_args)
        return calls

    def nested_exec(self, child: ChildRun, call: Call):
        haystack = "{}\n{}".format(child.stdout or "", child.stderr or "")
        for code, field in (self.surface.get("nested_exec_reasons") or {}).items():
            if code in haystack:
                return {"reason": code, "capability_field": field, "log": call.log}
        return None

    def needs_human_message(self, payload, output, stderr, values) -> str:
        text = self.surface["needs_human_message"]
        states = self.surface["dispatcher"]["states"]
        row = resolve_mode(values.get("word"), self.surface) if values and values.get(
            "word") else None
        launched = row.get("phase") if row else None
        gate = self.surface["dispatcher"].get("review_gate") or {}
        high = (payload or {}).get("high_priority_groups")
        count = high.get("count") if isinstance(high, dict) else None
        held = (row is not None and row["name"] == gate.get("mode")
                and gate.get("flag") in (values.get("extra") or [])
                and isinstance(count, int) and not isinstance(count, bool) and count > 0)
        if payload is None:
            phase = text["phase_unknown"]
        elif launched and held:
            phase = fill(text["review_completed"], {"phase": launched})
        elif launched:
            incomplete = payload.get("state") == states["needs_human"]
            phase = fill(text["phase_incomplete"] if incomplete else text["phase_known"],
                         {"phase": launched})
        else:
            phase = text["phase_unnamed"]
        if payload is not None:
            error = payload.get("error")
            line = error.strip() if isinstance(error, str) and error.strip() else None
        else:
            line = _last_line(output) or _last_line(stderr)
        error_clause = fill(text["error_known"], {"error": '"{}"'.format(line)}) \
            if line else text["error_unknown"]
        return fill(text["template"], {"phase": phase, "error": error_clause})

    def settle_progress_lines(self, call: Call, child: ChildRun) -> None:
        """The terminal child's own ``progress_lines``, in place of the last
        relayed ones, or none (fix round 28, live run 12 #10: a finished Codex
        result showed "3/8 batches ok … in flight", the last mid-run poll's
        lines, beside its ``done`` state). Redacted as a relay is."""
        lines = redact((child.result or {}).get("progress_lines"), None, self.surface)
        kept = ([line for line in lines if isinstance(line, str) and line]
                if isinstance(lines, list) else [])
        call.progress_lines = kept or None

    def terminal_result(self, call: Call, child: ChildRun, values) -> dict:
        surface = self.surface
        codes = surface["dispatcher"]["exit_codes"]
        self.settle_progress_lines(call, child)
        states = surface["dispatcher"]["states"]
        base = {"exit": child.code, "argv": child.argv, "run_id": call.run_id,
                "log": call.log, "polls": call.polls,
                "stdout_truncated": True if child.truncated else None}
        if child.code is not None and child.code == codes["needs_human"]:
            # Each redacted dispatcher command is re-spelled the way this
            # route's user types it, plan as typed, instead of a removal note;
            # a surface without `dispatcher.user_command` keeps the note.
            respell = respeller_for(surface, values)
            payload = redact(child.result, None, surface, respell)
            output = self.human_output(child, None, respell)
            stderr = redact(child.stderr, None, surface, respell)
            base.update({
                "ok": False, "state": states["needs_human"], "result": payload,
                "error": (payload or {}).get("error"), "output": output,
                "stderr": stderr or None, "next": None,
                "options": self.tool_calls_for(child, values) + [
                    {"human": surface["needs_human_option"]}],
                "nested_exec": self.nested_exec(child, call),
                "message": self.needs_human_message(payload, output, stderr, values),
            })
            return base
        if child.code is not None and child.code == codes["nothing_to_do"] and child.result:
            raw = child.result.get("next")
            base.update({
                "ok": True, "state": child.result.get("state") or states["nothing_to_do"],
                "result": redact(child.result, raw, surface),
                "artifacts": redact(child.result.get("artifacts") or [], raw, surface),
                "next": next_as_tool_call(raw, surface),
                "output": self.human_output(child, raw, carried=carries_next_step(child)),
                "stderr": redact(child.stderr, raw, surface) or None})
            lift_user_next_step(base)
            return base
        if child.code != codes["ok"] or child.result is None:
            marker = surface["dispatcher"]["result_marker"]
            if child.cancelled:
                why = "the call was cancelled before the dispatcher finished"
            elif child.timed_out:
                why = "the call's time budget ran out before the dispatcher finished"
            elif child.signal is not None:
                why = "the dispatcher was killed by signal {}{}".format(
                    child.signal, _signal_name(child.signal))
            elif child.result is not None:
                why = "the dispatcher exited {}".format(child.code)
            elif child.result_raw is not None:
                why = "the dispatcher's {} line was not valid JSON: {}".format(
                    marker, child.result_raw)
            elif child.code is None:
                why = "the dispatcher ended without an exit code and with no {} line".format(
                    marker)
            else:
                why = "the dispatcher exited {} with no {} line".format(child.code, marker)
            return self.error_result(call, child, why, with_run=True)
        raw = child.result.get("next")
        base.update({
            "ok": True, "state": child.result.get("state") or states["ok"],
            "result": redact(child.result, raw, surface),
            "artifacts": redact(child.result.get("artifacts") or [], raw, surface),
            "next": next_as_tool_call(raw, surface),
            "output": self.human_output(child, raw, carried=carries_next_step(child)),
            "stderr": redact(child.stderr, raw, surface) or None})
        lift_user_next_step(base)
        return base

    def error_result(self, call: Call, child: ChildRun, message: str,
                     with_run: bool = False) -> dict:
        """A failed child is a result. With a live run, it names how to stop it."""
        options = self.tool_calls_for(child, call.watched)
        out = {
            "ok": False, "state": self.state_word("error"), "exit": child.code,
            "argv": child.argv, "message": redact(message, None, self.surface),
            "stderr": redact(child.stderr, None, self.surface) or None,
            "output": self.human_output(child, None) or None,
            "options": options or None, "nested_exec": self.nested_exec(child, call),
        }
        if with_run and call.run_id:
            # `status` itself failing is never a statement about the run.
            out.update({"run_id": call.run_id, "log": call.log,
                        "abort_command": self.abort_args(call)})
        return out

    # -- the runbook (rule 5, D3's runbook paragraph) -----------------------------------

    def unfinished(self, row, outcome) -> bool:
        """Positively enumerated: running, needs-human exit, status failed, unfollowed next."""
        if not row.get("supports_detach"):
            return False
        states = self.surface["dispatcher"]["states"]
        codes = self.surface["dispatcher"]["exit_codes"]
        state = outcome.get("state")
        if state == states["running"]:
            return True
        if state == states["needs_human"] and outcome.get("exit") == codes["needs_human"]:
            return True
        if state == states["error"] and outcome.get("run_id") and outcome.get("exit") is not None:
            return True
        return outcome.get("ok") is True and outcome.get("next") is not None

    def attach_resume(self, call: Call, values, outcome) -> None:
        """``util next-command <plan> --blocked <mode>`` after an exit 3.

        A blocked run owes the user a command they can type: the same phase,
        resumed, in this route's own spelling. The dispatcher's output names the
        retry as a raw ``uv run`` argv (redacted here) and the options as tool
        calls, and neither is something a person types. The string is built in
        Python from the host's ``next_command`` template, so this file spells
        none of it, and it is the user's to type: nothing here (or in
        ``is_mechanical``) runs it. A surface without the ``resume`` entry, a
        spawn failure, a non-zero exit or an empty answer all leave the result
        as it was: an advisory lookup never changes what it decorates. The mode
        asked about is :func:`blocked_word`'s: a ``status``/``abort`` call
        reports on a run and is no phase. A range mode's run is asked about by
        the brief its launch pinned (:meth:`pin_commit_range`), never by the
        phrase the call typed; one that pinned nothing is asked nothing.
        """
        dispatcher = self.surface["dispatcher"]
        resume = dispatcher.get("resume")
        plan = values.get("plan_arg") or values.get("plan")
        word = blocked_word(values, outcome, self.surface)
        if (not resume or not plan or not word
                or outcome.get("state") != dispatcher["states"]["needs_human"]
                or outcome.get("exit") != dispatcher["exit_codes"]["needs_human"]):
            return
        argv = list(resume["argv"]) + [
            plan, resume["option"], word,
            dispatcher["host_option"], self.surface["host"]]
        spare = max(1.0, call.hard_deadline - time.monotonic() - 0.5)
        child = self.run_child(call, argv, spare)
        if child.spawn_error or child.code != dispatcher["exit_codes"]["ok"]:
            return
        step = (child.result or {}).get(resume["result_key"])
        command = step.get("command") if isinstance(step, dict) else None
        if isinstance(command, str) and command.strip():
            outcome["resume_command"] = command
            text = self.surface["needs_human_message"]
            why = step.get("why")
            clause = text["resume"]
            if isinstance(why, str) and why.strip() and isinstance(
                    text.get("resume_why"), str):
                # Fix round 22: what the plain resume does, from the stop.
                outcome["resume_why"] = why.strip()
                clause = fill(text["resume_why"], {"why": why.strip()})
            markdown = step.get("markdown")
            if (isinstance(markdown, str) and markdown.strip()
                    and isinstance(text.get("resume_markdown"), str)):
                # Fix round 24: the ways forward as one written section,
                # whose clause stands for the resume's and the answers'.
                outcome["resume_markdown"] = markdown
                clause = text["resume_markdown"]
                self.relay_stop_beside_section(values, outcome, step)
            outcome["message"] = "{} {}".format(outcome.get("message") or "", clause)
            self.attach_answers(step, word, plan, outcome,
                                revs=values.get("pinned") or plan)

    def relay_stop_beside_section(self, values, outcome: dict, step: dict) -> None:
        """The stop's line without the ways forward its section carries, in
        the ``error``'s place (fix round 28, live run 12 #5: the host relayed
        the whole ``error`` line, whose "To go on (your call): … add
        --human-task …" restated every answer the section gave as commands).

        ``util next-command --blocked`` hands back the line it read off the
        stop's record (``error_line``) and that line without the section's
        ways forward (``error_beside_section``). Swapped only while the
        result's ``error`` is the recorded line word for word, so a stop the
        record does not describe keeps its own line; ``result.error`` follows
        and ``message`` is composed again around it."""
        line, beside = step.get("error_line"), step.get("error_beside_section")
        payload = outcome.get("result")
        if (not isinstance(line, str) or not isinstance(beside, str)
                or not beside.strip() or not isinstance(payload, dict)):
            return
        respell = respeller_for(self.surface, values)
        current = outcome.get("error")
        if (not isinstance(current, str) or current.strip()
                != (redact(line, None, self.surface, respell) or "").strip()):
            return
        shown = redact(beside, None, self.surface, respell)
        outcome["error"] = shown
        payload["error"] = shown
        outcome["message"] = self.needs_human_message(
            payload, outcome.get("output"), outcome.get("stderr"), values)

    def attach_answers(self, step: dict, word: str, plan: str, outcome: dict,
                       revs: str = "") -> None:
        """Lead ``options`` with the resume and every answer the stop offers.

        Fix round 14 (live run 5): ``resume_command`` was a plain ``--resume``
        while the first option replayed ``--human-task`` answers, and on a
        first stop ``message`` and ``options`` offered only the bare resume, the
        answers sitting in ``error``. ``util next-command --blocked`` now hands
        back the resume's own ``flags`` and the stop's ``answers`` (each a
        command the user types, its flags, and what it does); here the resume
        becomes the first option — the same command as ``resume_command`` by
        construction — each answer the next ones, in order, and the scraped
        options follow minus any repeat, the human note still last. The answers
        go to ``resume_answers`` and, through the surface's ``answers`` clause
        filled with the dispatcher's ``answers_text``, into ``message``. This
        file spells none of it. The port of ``attachAnswers``.

        The option calls name ``user_resume.mode``, the mode the resume runs,
        and the word asked about only when the lookup names none: a composite
        asked about answers with an inner phase's resume and answers
        (plans/improve-plan-and-improve-code.md §2.6), and a call built from
        the composite's word would carry ``--human-task`` to a parser that
        rejects it. A call on a range mode names the run by *revs*, its pinned
        range, with ``plan`` empty.
        """
        named = step.get("mode")
        row = resolve_mode(named if isinstance(named, str) and named else word,
                           self.surface)
        if not row:
            return

        def flags_of(value):
            return (list(value) if isinstance(value, list)
                    and all(isinstance(flag, str) and flag for flag in value) else None)

        def call_for(flags):
            if takes_revs(row, self.surface):
                return {"mode": row["name"], REVS: revs, "plan": "", "question": "",
                        "extra_flags": flags}
            return {"mode": row["name"], "plan": plan, "question": "",
                    "extra_flags": flags}

        lead = []
        flags = flags_of(step.get("flags"))
        if flags is not None:
            lead.append(call_for(flags))
        answers = []
        for entry in step.get("answers") if isinstance(step.get("answers"), list) else []:
            entry_flags = flags_of((entry or {}).get("flags")) if isinstance(entry, dict) else None
            spelled, why = (entry.get("command"), entry.get("why")) if isinstance(
                entry, dict) else (None, None)
            if (entry_flags is None or not isinstance(spelled, str) or not spelled.strip()
                    or not isinstance(why, str)):
                continue
            answers.append({"command": spelled, "why": why})
            lead.append(call_for(entry_flags))
        if answers:
            outcome["resume_answers"] = answers
            clause = (self.surface.get("needs_human_message") or {}).get("answers")
            text = step.get("answers_text")
            if (isinstance(clause, str) and isinstance(text, str) and text.strip()
                    and "resume_markdown" not in outcome):
                outcome["message"] = "{} {}".format(
                    outcome.get("message") or "", fill(clause, {"answers": text}))
        if not lead:
            return
        seen = {json.dumps(call, sort_keys=True) for call in lead}
        rest = [option for option in outcome.get("options") or []
                if json.dumps(option, sort_keys=True) not in seen]
        outcome["options"] = lead + rest

    def attach_runbook(self, call: Call, row, outcome) -> None:
        """``util instructions <mode> --host <id>``: integrity-checked, banner dropped."""
        dispatcher = self.surface["dispatcher"]
        runbook = self.surface["runbook"]
        argv = list(dispatcher["instructions"]) + [
            row["name"], dispatcher["host_option"], self.surface["host"]]
        # Cut from the reserve the loop held back, not from the loop's deadline:
        # on the handoff edge that deadline has already passed.
        spare = max(1.0, call.hard_deadline - time.monotonic() - 0.5)
        child = self.run_child(call, argv, spare)
        problem = None
        if child.spawn_error or child.code != dispatcher["exit_codes"]["ok"]:
            problem = "the runbook fetch did not complete (exit {})".format(child.code)
        lines = (child.stdout or "").split("\n")
        # Drop the head banner: its character count describes the unscrubbed core.
        opening = runbook.get("banner_opening") or ""
        fence = opening.split()[0] if opening.split() else None
        kept, index = [], 0
        while index < len(lines):
            line = lines[index]
            if opening and fence and line.startswith(opening):
                index += 1
                while index < len(lines) and not lines[index].startswith(fence):
                    index += 1
                index += 1
                continue
            if not line.strip().startswith(dispatcher["result_marker"]):
                kept.append(line)
            index += 1
        sentinel = runbook["core_end_marker"] + " " + row["name"]
        if problem is None and not any(line.rstrip() == sentinel for line in kept):
            problem = ("the runbook arrived without its closing line ({}), so it is a "
                       "partial payload and was not attached".format(sentinel))
        if problem:
            # A documentation fetch never restates the run: ok/state/isError stay
            # as the run produced them (a live handoff or an exit-0 with an
            # unfollowed next is not a failure because its runbook was not fetched).
            outcome["runbook_error"] = problem
            return
        outcome["runbook"] = redact(scrub_runbook("\n".join(kept).strip("\n"), self.surface),
                                    None, self.surface)


def turn_metadata(meta) -> dict:
    """``_meta["x-codex-turn-metadata"]`` as a dict, or ``{}``; never raises.

    Seen as a JSON object on 0.156.1; a JSON-encoded string is accepted too,
    since the field is undocumented and its encoding is not a contract.
    """
    value = meta.get(TURN_METADATA_KEY) if isinstance(meta, dict) else None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def session_posture(meta):
    """D3b: the session's sandbox posture word, or ``None`` when unreadable."""
    value = turn_metadata(meta).get(TURN_METADATA_SANDBOX_MODE)
    if value == POSTURE_READ_ONLY or value in POSTURES_ALLOWING_WRITES:
        return value
    return None


def session_model(meta):
    """The session's model id, or ``None`` when absent or not a plain id."""
    value = turn_metadata(meta).get(TURN_METADATA_MODEL)
    if isinstance(value, str) and SESSION_MODEL_PATTERN.fullmatch(value):
        return value
    return None


def _last_line(text):
    if not isinstance(text, str):
        return None
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return lines[-1] if lines else None


def _same_id(left, right) -> bool:
    """JSON-RPC ids compare with their JSON type preserved (1 is not "1")."""
    return type(left) is type(right) and left == right


def main() -> int:
    fd = _guard_protocol_fd()
    server = Server(Wire(fd))

    def _terminate(_number, _frame):
        # Measured (Phase 1 row 10, codex 0.156.1): on an interrupted session
        # codex closes this server's stdin and sends SIGTERM in the same
        # millisecond, and sends no `notifications/cancelled`. Python's default
        # SIGTERM exit beat the EOF branch every time, so the in-flight child —
        # its own session, by design — was orphaned. SIGTERM (and SIGHUP) now
        # take the EOF branch: cancel, reap the group, then exit.
        raise KeyboardInterrupt

    for name in ("SIGTERM", "SIGHUP"):
        number = getattr(signal, name, None)
        if number is not None:
            try:
                signal.signal(number, _terminate)
            except (OSError, ValueError):
                pass
    try:
        server.serve(sys.stdin.buffer)
    except KeyboardInterrupt:
        # Ctrl-C reaches this process too when it shares the terminal's process
        # group, so SIGINT and codex's SIGTERM arrive together: the second one
        # must not cut the reap short.
        for name in ("SIGINT", "SIGTERM", "SIGHUP"):
            number = getattr(signal, name, None)
            if number is not None:
                try:
                    signal.signal(number, signal.SIG_IGN)
                except (OSError, ValueError):
                    pass
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
