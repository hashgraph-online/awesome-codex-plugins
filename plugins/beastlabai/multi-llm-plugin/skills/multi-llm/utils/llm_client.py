"""LLM client wrapper for multi-provider LLM subprocess calls."""

import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Collection, Dict, List, NamedTuple, Optional, Sequence, Tuple, Union

from . import structured_output
from . import process_control
from . import landlock_dispatch as _landlock
from . import readonly_audit as _readonly_audit_mod
from . import result_files as _result_files
from .metrics import describe_usage as _describe_usage
from .provider_registry import parse_model_spec, get_provider, get_provider_timeout
from .json_extractor import _ANSI_ESCAPE, looks_like_ndjson
from .providers.base import (
    JAIL_DENIED_MARKER,
    PROFILE_GENERATE,
    SANDBOX_RUNG_LANDLOCK,
    SANDBOX_RUNG_PLUGIN_LANDLOCK,
    SANDBOX_RUNG_UNSANDBOXED,
    SKIP_RUNG_ENV,
    JailContext,
    JailRequest,
    ReadOnlyInvocationRefused,
    StructuredOutputUnavailable,
    _matches_marker,
    availability_from_failure,
    build_child_env,
    sandbox_rung_id,
    version_tuple,
)
from .providers.result_envelope import is_clean_envelope


class LLMClientError(Exception):
    """Raised when LLM client operations fail."""
    pass


class SubagentTimeoutError(LLMClientError):
    """Raised when subagent execution times out."""
    pass


# Error codes for consistent error reporting
ERROR_TIMEOUT = "TIMEOUT"
ERROR_PARSE_ERROR = "PARSE_ERROR"
ERROR_BINARY_NOT_FOUND = "BINARY_NOT_FOUND"
ERROR_SUBPROCESS_FAILED = "SUBPROCESS_FAILED"
ERROR_FILE_NOT_FOUND = "FILE_NOT_FOUND"
ERROR_PROMPT_TOO_LONG = "PROMPT_TOO_LONG"
ERROR_PROMPT_UNSAFE = "PROMPT_UNSAFE"

#: ``details["sandbox"]`` for a slot that ran under the D6 fallback (2026-09-17)
#: on the **uncontained** rung: the runner's own OS sandbox could not start and
#: ``sandbox_fallback: auto`` (the default) let the read-only dispatch run
#: without any boundary. Absent means "ran as the adapter's default argv renders
#: it". A slot on a **contained** rung (landlock rung, 2026-09-22) carries that
#: rung's id here instead (``landlock``) — never this word, which would claim
#: the opposite of what happened.
SANDBOX_BYPASSED = "bypassed"

#: The per-slot record word for a contained fallback rung — ``models_served``'s
#: ``sandbox: fallback-landlock`` — so a run's provenance greps apart from
#: ``bypassed`` the way ``[SANDBOX_FALLBACK]`` greps apart from
#: ``[SANDBOX_BYPASSED]``. The renderers (``html_report_generator``,
#: ``run_status``) read the recorded word back, never a bool.
SANDBOX_FALLBACK_WORD_PREFIX = "fallback-"

#: The contained rung ids a record word may name. Closed on purpose: a value
#: nobody declared is dropped rather than recorded, exactly as an unknown word
#: always was, so a stray string can never read as a sandbox.
_CONTAINED_RUNG_IDS = frozenset({SANDBOX_RUNG_LANDLOCK})

#: The ``incidental``-grade rung ids a record word may name (plan
#: codex-sandbox-unavailable §7 "Step 2 subtask" item 3, 2026-09-30): the
#: plugin's own Landlock jail. A **separate** closed set beside
#: :data:`_CONTAINED_RUNG_IDS`, which stays ``{landlock}`` so nothing that reads
#: "contained" widens; without this set ``sandbox_record_word`` would drop the
#: rung from every per-slot record, ``models_served`` and reaggregate while the
#: log line said it ran. Recorded as ``fallback-plugin-landlock``; the renderers
#: keep their own closed set of incidental words (they import no provider code).
_INCIDENTAL_RUNG_IDS = frozenset({SANDBOX_RUNG_PLUGIN_LANDLOCK})

#: ``details["failure_reason"]`` for a jailed slot that failed on a
#: codex-internal EACCES the plugin's jail caused (F1 "Where it sits" item 6),
#: or whose required allow entry vanished before the spawn. Non-retryable and
#: never moved to another rung.
FAILURE_JAIL_DENIED = "jail-denied"

#: Where a ``[JAIL_DENIED]`` line sends the reader (F1 item 6, "Next steps").
JAIL_DENIED_ISSUES_URL = "github.com/beastlabai/multi-llm-plugin/issues"


def _attach_sandbox_word(details: Dict[str, Any], sandbox_fallback: Any) -> None:
    """Record the D6 override on ``details["sandbox"]`` for a child that ran.

    ``bypassed`` for the uncontained rung, the rung id for a contained or
    incidental one (``plugin-landlock``, 2026-09-30), and
    nothing when the override did not fire. Called on every path where the
    child actually ran — exit 0, a non-zero exit, and a timeout kill — because
    the slot ran without the runner's sandbox whatever it then returned: a
    record that dropped the word on failure would hide exactly the slots an
    operator most needs to audit (the dogfood run 2026-09-25 lost a bypassed
    codex slot's provenance this way).
    """
    fallback_rung = sandbox_rung_id(sandbox_fallback)
    if fallback_rung:
        details["sandbox"] = (
            SANDBOX_BYPASSED if fallback_rung == SANDBOX_RUNG_UNSANDBOXED
            else fallback_rung
        )


def sandbox_record_word(value: Any) -> Optional[str]:
    """The ``sandbox`` word a per-slot record carries for ``value``, or ``None``.

    ``value`` is either ``details["sandbox"]`` (``bypassed`` or a rung id) or a
    word already recorded (``bypassed``, ``fallback-<rung>``), so the mapping is
    idempotent and every hop — result record, ``models_served``, reaggregate —
    can run it. Only the uncontained rung maps to ``bypassed``; a contained rung
    maps to ``fallback-<rung>``, and so does an incidental one
    (``fallback-plugin-landlock``, 2026-09-30) — each from its own closed set;
    anything else is dropped.
    """
    if value in (SANDBOX_BYPASSED, SANDBOX_RUNG_UNSANDBOXED):
        return SANDBOX_BYPASSED
    if not isinstance(value, str):
        return None
    rung = (
        value[len(SANDBOX_FALLBACK_WORD_PREFIX):]
        if value.startswith(SANDBOX_FALLBACK_WORD_PREFIX) else value
    )
    if rung in _CONTAINED_RUNG_IDS or rung in _INCIDENTAL_RUNG_IDS:
        return SANDBOX_FALLBACK_WORD_PREFIX + rung
    return None


def sandbox_word_is_incidental(word: Any) -> bool:
    """Whether a recorded word (or rung id) names an ``incidental``-grade rung."""
    return sandbox_fallback_rung_of(word) in _INCIDENTAL_RUNG_IDS


def sandbox_fallback_rung_of(word: Any) -> Optional[str]:
    """The fallback rung id a recorded ``fallback-<rung>`` word names — a
    contained rung or an incidental one — or ``None``."""
    recorded = sandbox_record_word(word)
    if recorded and recorded.startswith(SANDBOX_FALLBACK_WORD_PREFIX):
        return recorded[len(SANDBOX_FALLBACK_WORD_PREFIX):]
    return None

# Windows-only concern: POSIX exec passes argv verbatim (no reparsing) and
# has generous per-arg limits, so prompt length is never enforced there.
_IS_WINDOWS = os.name == "nt"

# Hard Windows command-line caps, measured against the FULL rendered command
# line (subprocess renders list argv via ``list2cmdline`` before
# ``CreateProcessW``) in UTF-16 code units — the unit Windows uses, so astral
# characters count twice. cmd.exe — which executes .cmd/.bat npm shims — caps
# the whole command line at 8,191; native CreateProcess caps at 32,767
# (including the terminating NUL).
CMDLINE_CAP_UTF16_BATCH = 8191
CMDLINE_CAP_UTF16_NATIVE = 32767

# Headroom reserved below the caps for overhead that cannot be measured from
# argv alone: the terminating NUL, the implicit `%COMSPEC% /c` wrapper that
# launches batch shims, and expansion the shim itself performs ("%_prog%"
# prefixes, %* re-substitution).
CMDLINE_UTF16_HEADROOM = 256

_BATCH_SUFFIXES = frozenset({".cmd", ".bat"})

# Characters cmd.exe treats specially when it reparses a batch-shim command
# line. Deliberately conservative (interim guard until the explicit `cmd /c`
# escaping path lands — launch-strategy step (c)): `"` breaks argument
# quoting (CreateProcess-style `\"` escapes are NOT honored by cmd.exe),
# `%`/`!` trigger variable expansion even inside quotes, CR/LF split
# commands, and `^&|<>()` become live once quoting is broken or the argument
# is unquoted.
_CMD_UNSAFE_CHARS = frozenset('"%!^&|<>()\r\n')

# npm cmd-shims dispatch to `node <target.js>` via a `%dp0%`-relative (or,
# in older shims, `%~dp0`-relative) quoted path; extract that target so the
# shim can be bypassed entirely.
_NODE_SHIM_TARGET_RE = re.compile(
    r'"%(?:~dp0|dp0%)[\\/]?(?P<rel>[^"%\r\n]+?\.(?:js|cjs|mjs))"',
    re.IGNORECASE,
)


def _resolve_node_shim_target(shim_path: Path) -> Optional[List[str]]:
    """Extract the ``node <cli.js>`` launch an npm batch shim dispatches to.

    npm-installed CLIs on Windows are ``.cmd`` shims whose payload line runs
    ``node`` on a ``%dp0%``-relative script (e.g.
    ``"%_prog%" "%dp0%\\node_modules\\pkg\\bin\\cli.js" %*``). Parsing that
    target lets us launch node directly and skip cmd.exe entirely.

    Returns the ``[node, script]`` argv prefix, or None when the shim does
    not parse as a node dispatcher (missing/unreadable target, or no node
    binary available) — the caller then falls back to the flagged shim.
    """
    try:
        content = shim_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    match = _NODE_SHIM_TARGET_RE.search(content)
    if match is None:
        return None

    # Rebuild the %dp0%-relative path with host separators so the parse also
    # behaves identically under test on POSIX.
    parts = [p for p in re.split(r"[\\/]+", match.group("rel")) if p and p != "."]
    if not parts:
        return None
    script = shim_path.parent.joinpath(*parts)
    try:
        if not script.is_file():
            return None
    except OSError:
        return None

    # Mirror the shim's own dispatch: prefer a node.exe next to the shim
    # (%dp0%\node.exe), else fall back to node from PATH.
    node = shim_path.parent / "node.exe"
    try:
        if node.is_file():
            return [str(node), str(script)]
    except OSError:
        pass
    node_on_path = shutil.which("node")
    if node_on_path is None:
        return None
    return [node_on_path, str(script)]


def _resolve_executable(name: str) -> Tuple[List[str], bool]:
    """Resolve a command name to an argv launch prefix via shutil.which.

    Returns ``(launcher_argv, is_batch_shim)`` where ``launcher_argv``
    replaces ``cmd[0]`` (usually one element; two for ``node <cli.js>``).
    When ``shutil.which`` finds nothing, the bare name is returned unchanged
    so downstream error text stays meaningful. Resolution makes Windows
    ``CreateProcess`` find npm-installed provider CLIs; on POSIX the
    resolved path is exactly what PATH lookup would have executed anyway.

    Batch-shim hazard: npm installs CLIs on Windows as ``.cmd``/``.bat``
    shims, which are executed by cmd.exe. cmd.exe REPARSES the command line
    (metacharacters/newlines in argv corrupt the prompt or can escape into
    executed commands — the BatBadBut / CVE-2024-24576 class) and caps it at
    8,191 chars. To avoid the shim entirely, prefer (a1) a sibling ``.exe``
    with the same stem, then (a2) the ``node <cli.js>`` target the npm shim
    dispatches to; only when neither exists is the shim path returned with
    ``is_batch_shim=True`` so the caller enforces the stricter prompt budget
    and the cmd.exe metacharacter guard.
    """
    resolved = shutil.which(name)
    if resolved is None:
        return [name], False
    path = Path(resolved)
    if path.suffix.lower() in _BATCH_SUFFIXES:
        sibling_exe = path.with_suffix(".exe")
        try:
            if sibling_exe.is_file():
                return [str(sibling_exe)], False
        except OSError:
            pass
        node_target = _resolve_node_shim_target(path)
        if node_target is not None:
            return node_target, False
        return [resolved], True
    return [resolved], False


def expand_env_home(provider_env: Dict[str, str]) -> Dict[str, str]:
    """Shell-expand a leading ``~`` in adapter/config-supplied env values.

    Nothing expands ``~`` on the way to a child: ``CODEX_HOME='~/.codex_work'``
    reaches codex verbatim, and codex 0.146.0 either refuses ("path does not
    exist") or — if a literal ``./~/.codex_work`` happens to exist — resolves it
    CWD-relative and runs **silently against the wrong auth directory**. The
    expansion belongs at the two spawn sites rather than in each adapter, and it
    is applied only to the provider/config **deltas**: ``os.environ`` values
    reached us from a shell that already expanded them, and re-expanding an
    inherited value would change bytes nobody asked us to touch.

    ``os.path.expanduser`` is a no-op on any string that does not start with
    ``~``, and on ``~unknown-user`` where the name does not resolve, so a value
    that is not a home-relative path passes through unchanged.
    """
    return {
        key: (_expand_leading_tilde(value) if isinstance(value, str) else value)
        for key, value in provider_env.items()
    }


def _expand_leading_tilde(value: str) -> str:
    """``os.path.expanduser``, minus Windows' guess at another user's home.

    ``ntpath.expanduser`` never looks ``~name`` up: it answers with a sibling of
    the current profile dir (``%USERPROFILE%\\..\\name``) whether that user exists or
    not, so there only the current user's ``~`` is expanded.
    """
    if os.name == "nt" and value.startswith("~") and value[1:2] not in ("", "/", "\\"):
        return value
    return os.path.expanduser(value)


class DispatchContext:
    """What one spawn learned from the adapter's own run-scoped context.

    ``refusal`` is a human-readable reason the dispatch may not be attempted at
    all — set only by an adapter that can prove the spawn would resolve to
    nothing. ``None`` means "spawn normally", which is every adapter that
    declares no context.
    """

    __slots__ = ("refusal",)

    def __init__(self, refusal: Optional[str] = None) -> None:
        self.refusal = refusal


@contextlib.contextmanager
def provider_dispatch_context(
    provider: Any,
    model: str,
    profile: str,
    *,
    anchor: Optional[str] = None,
    runner_version: Optional[str] = None,
):
    """Enter an adapter's run-scoped dispatch context, if it declares one.

    Lives beside :func:`expand_env_home` for the same reason: it belongs to the
    **two spawn sites**, not to each adapter, so a context that scopes argv and
    env together cannot be entered on one lane and skipped on the other.

    The hook is duck-typed (``hermetic_dispatch``) rather than a base-class
    method so adapters can scope their configuration independently: opencode's
    config root and fx's managed HOME both live until the child has finished.
    Adapters without the hook yield an empty context.

    ``runner_version`` is the CLI version a caller's preflight already read
    (the executor's ``_VERSION_CACHE``), handed through so the adapter can gate
    a version-dependent config key without spawning ``--version`` per dispatch
    (opencode's ``continue_loop_on_deny``, plan T4.2). It is forwarded only when
    the caller has one; ``None`` means "no read on this path".
    """
    # Plan codex-sandbox-unavailable I12 (2026-09-30): an adapter may also ask
    # to be told a dispatch is about to start (codex records its trust state
    # so the run can remove the entries its children add). A separate,
    # side-effect-only hook — never a context, never a refusal, never argv or
    # env — so `hermetic_dispatch` remains the configuration lifecycle hook.
    note = getattr(provider, "note_dispatch", None)
    if callable(note):
        try:
            note(profile, model, anchor=anchor)
        except Exception:  # noqa: BLE001 - bookkeeping may never block a dispatch
            pass
    enter = getattr(provider, "hermetic_dispatch", None)
    if not callable(enter):
        yield DispatchContext()
        return
    extra = {"runner_version": runner_version} if runner_version is not None else {}
    with enter(profile, model, anchor=anchor, **extra) as refusal:
        yield DispatchContext(refusal)


def _utf16_code_units(s: str) -> int:
    """Length of ``s`` in UTF-16 code units (astral characters count as 2).

    Windows command-line caps are defined over the UTF-16 command line handed
    to ``CreateProcessW``, not over Python code points.
    """
    return len(s.encode("utf-16-le")) // 2


def _prompt_length_error(
    cmd: List[str],
    prompt: str,
    provider_name: str,
    model: str,
    is_batch_shim: bool
) -> Optional[Dict[str, Any]]:
    """Return a structured PROMPT_TOO_LONG error dict, or None if within budget.

    Guard for providers whose prompt travels on argv (see
    ``LLMProvider.prompt_transport``): exceeding the cmd.exe/CreateProcess
    command-line caps would otherwise fail with a cryptic
    ``[WinError 206]``/cmd.exe error. Callers gate on ``_IS_WINDOWS``.

    The check measures what Windows actually limits: the FULL command line
    that ``subprocess`` renders from ``cmd`` via ``list2cmdline`` (executable
    path, provider flags, quoting expansion, and the prompt), counted in
    UTF-16 code units, with headroom below the hard cap for overhead that
    cannot be measured from argv alone. Checking ``len(prompt)`` in isolation
    would pass prompts that still blow the cap once argv overhead, quote
    escaping, and astral characters are accounted for.
    """
    cap = CMDLINE_CAP_UTF16_BATCH if is_batch_shim else CMDLINE_CAP_UTF16_NATIVE
    limit = cap - CMDLINE_UTF16_HEADROOM
    cmdline_units = _utf16_code_units(subprocess.list2cmdline(cmd))
    if cmdline_units <= limit:
        return None
    prompt_units = _utf16_code_units(prompt)
    launcher = (
        "a .cmd/.bat shim run via cmd.exe (8,191-unit command-line cap)"
        if is_batch_shim
        else "a native executable (32,767-unit CreateProcess cap)"
    )
    return {
        "success": False,
        "error": (
            f"The fully rendered {provider_name} command line is "
            f"{cmdline_units} UTF-16 code units ({prompt_units} from the "
            f"prompt), but {provider_name} receives the prompt on the "
            f"command line and resolves to {launcher} on Windows; the safe "
            f"limit is {limit} units. Shorten the prompt — e.g. reference "
            f"large files by path instead of embedding their contents "
            f"inline."
        ),
        "error_code": ERROR_PROMPT_TOO_LONG,
        "details": {
            "provider": provider_name,
            "model": model,
            "prompt_chars": len(prompt),
            "prompt_utf16_units": prompt_units,
            "cmdline_utf16_units": cmdline_units,
            "cmdline_utf16_limit": limit,
        }
    }


def _batch_shim_metachar_error(
    prompt: str,
    provider_name: str,
    model: str,
    shim_path: str
) -> Optional[Dict[str, Any]]:
    """Return a structured PROMPT_UNSAFE error dict, or None if the prompt is safe.

    Interim safeguard for launch-strategy step (c): when a provider still
    resolves to a ``.cmd``/``.bat`` shim (no sibling ``.exe``, no parseable
    node target), cmd.exe reparses the command line on launch, so a prompt
    carrying cmd.exe metacharacters can be silently corrupted or escape into
    executed commands (BatBadBut / CVE-2024-24576 class). Until the explicit
    ``cmd /c`` escaping path lands, reject such prompts with a structured
    error rather than launching. Callers gate on ``_IS_WINDOWS``.
    """
    unsafe = sorted(set(prompt) & _CMD_UNSAFE_CHARS)
    if not unsafe:
        return None
    chars = ", ".join(repr(ch) for ch in unsafe)
    return {
        "success": False,
        "error": (
            f"{provider_name} resolves to a cmd.exe batch shim ({shim_path}) "
            f"and the prompt contains cmd.exe metacharacters ({chars}). "
            f"cmd.exe reparses the shim's command line, so these characters "
            f"could corrupt the prompt or escape into executed commands "
            f"(BatBadBut / CVE-2024-24576 class); refusing to launch via the "
            f"shim. Fix: install a native {provider_name} executable, or "
            f"remove these characters from the prompt."
        ),
        "error_code": ERROR_PROMPT_UNSAFE,
        "details": {
            "provider": provider_name,
            "model": model,
            "executable": shim_path,
            "unsafe_characters": unsafe,
        }
    }


MAX_LOGGED_PROMPT_LENGTH = 5000

#: §4.4's storage caps. A *successful* ``review-plan`` against a provider
#: emitting 3 MiB per stream wrote a 6,254,326 B ``log_gemini_*.txt``: this
#: function truncated the prompt and nothing else. Lane B already ``_tail``s its
#: failure captures at 64 KiB, so the log path is the one that was uncapped.
#:
#: Each stream keeps its **last** ``MAX_LOG_TAIL_LINES`` lines with every line
#: cut to ``MAX_LOG_LINE_BYTES``; the per-stream and whole-file byte budgets are
#: the backstops that make the ~100 KB total a property of the written file
#: rather than of the input. Measured against the captured 6 MB artifact,
#: 64 KiB/line + last-20 alone took it to ~17 KB.
MAX_LOG_LINE_BYTES = 64 * 1024
MAX_LOG_TAIL_LINES = 20
MAX_LOG_TOTAL_BYTES = 100 * 1024
#: Two streams plus a ≤5 KB prompt and the header stay inside the total.
MAX_LOG_STREAM_BYTES = 45 * 1024


def _redact(text: str) -> str:
    """§4.5's one redaction boundary, imported late.

    ``write_safety`` reaches this module through ``subagent_tasks``, so a
    module-level import here would close an import cycle. The call is on a
    per-invocation path, not a per-line one.
    """
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from .write_safety import redact_text
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import redact_text
    return redact_text(text)


def _cut_bytes(text: str, limit: int, marker: str) -> str:
    """``text`` cut to ``limit`` UTF-8 bytes, head kept, ``marker`` appended.

    The marker is charged against ``limit`` rather than added on top, so a cap
    stated as a number of bytes really is one — a "~100 KB" file that comes out
    at 100 KB plus a footer is a cap nobody can assert on.
    """
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    keep = max(0, limit - len(marker.encode("utf-8")))
    return encoded[:keep].decode("utf-8", errors="ignore") + marker


def _cut_bytes_middle(text: str, limit: int, marker: str) -> str:
    """``text`` cut to ``limit`` UTF-8 bytes, head **and tail** kept, ``marker`` between.

    A stream's end is where its answer is: codex's final ``agent_message`` and
    ``turn.completed`` come last, after a few multi-KB ``aggregated_output`` lines
    (2026-10-01, Claude Code review-code: a head-only cut left a log ending at the
    diff read, and its "0 issues" verdict could not be audited). A quarter of the
    budget keeps the opening, the rest keeps the ending. The marker is charged
    against ``limit``, as in :func:`_cut_bytes`.
    """
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    room = max(0, limit - len(marker.encode("utf-8")))
    head = room // 4
    tail = room - head
    return (
        encoded[:head].decode("utf-8", errors="ignore")
        + marker
        + (encoded[len(encoded) - tail:].decode("utf-8", errors="ignore") if tail else "")
    )


def _bound_stream(text: str) -> str:
    """One captured stream, bounded per §4.4 — **after** it has been redacted.

    Order is normative and is the reason L3 and L4 are one atomic change: every
    cut below slices by construction, and a cut applied first leaves a remnant no
    pattern matches. The last-20-lines rule would decapitate a PEM block's
    ``-----BEGIN`` header and keep its body; the per-line cut would keep a value
    whose key name it had just removed. Neither is recoverable downstream.
    """
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) > MAX_LOG_TAIL_LINES:
        dropped = len(lines) - MAX_LOG_TAIL_LINES
        lines = [
            f"... [{dropped} earlier line(s) truncated; last {MAX_LOG_TAIL_LINES} kept]"
        ] + lines[-MAX_LOG_TAIL_LINES:]
    bounded = [
        _cut_bytes(line, MAX_LOG_LINE_BYTES, f" ... [line truncated at {MAX_LOG_LINE_BYTES} B]")
        for line in lines
    ]
    return _cut_bytes_middle(
        "\n".join(bounded),
        MAX_LOG_STREAM_BYTES,
        f"\n... [stream truncated at {MAX_LOG_STREAM_BYTES} B; middle elided]\n",
    )


def _attach_stdout_excerpt(details: Dict[str, Any], stdout: Optional[str]) -> None:
    """Put the run's stdout on ``details`` as ``stdout_excerpt``, redacted then bounded.

    **Why a helper and not a third copy.** ``invoke_with_provider`` loses a run
    three ways — a non-zero exit, a timeout kill, and a zero exit whose output
    would not parse — and all three are cases where the provider may already have
    said the thing the caller needs. The rule for carrying that text out is not
    one line but four decisions (``_redact`` *before* ``_bound_stream``, per
    §4.5/§4.4; ``.strip()``; set the key only when something survives; never the
    raw stream), and this module argues elsewhere that a rule spelled three times
    is a rule that drifts twice — see ``_bound_stream``'s own note that the
    redact/bound order "is normative", and §2's forward-maintenance case against
    two hand-aligned blocks plus a comment. A cap tightened or a pattern added at
    one copy and not the others would leak from whichever site was forgotten, and
    the leak would be invisible until an artifact was read by a human. So it is
    written once, here, and the three sites call it.

    **Why the key is omitted rather than set empty.** Consumers test
    ``details.get("stdout_excerpt")`` for "did the provider say anything we can
    still use" — salvage gating at ``code_review_orchestrator.py``'s site A reads
    it ahead of ``details["stderr"]`` for exactly that. An always-present key
    holding ``""`` would make every one of those call sites carry a second
    emptiness check, and the first one written without it would treat "the
    provider printed nothing" as "the provider printed something". Absent means
    absent.

    Args:
        details: The result envelope's ``details`` dict, mutated in place.
        stdout: The raw captured stdout, or ``None`` when the path never had it
            (a ``TimeoutExpired`` that carried no partial output).
    """
    excerpt = _bound_stream(_redact(stdout or "")).strip()
    if excerpt:
        details["stdout_excerpt"] = excerpt


#: The key :func:`_attach_salvage_text` writes. Its *presence* is a verdict:
#: ``""`` means "the adapter read its stream and found no answer text", and an
#: absent key means "no reducer applies" (``salvage_source`` then falls back to
#: ``stdout_excerpt`` and stderr).
SALVAGE_TEXT_KEY = "salvage_text"

#: A salvage request's record of *how* the run it came from was lost, and the
#: one value it takes today. Only a run cut by a deadline carries it: a salvaged
#: ``[]`` from such a run is refused (``subagent_executor._salvage_gave_up``),
#: because a reviewer killed mid-review never said "I found nothing", while a
#: ``[]`` from a run that finished and then exited non-zero is still a genuine
#: empty review (plan: review-run-scope-salvage-and-failure-visibility D4.5,
#: decision 11.10). Here because every lane that writes or reads a request
#: already imports this module, and ``ERROR_TIMEOUT`` is what decides it.
SALVAGE_FAILURE_KEY = "failure"
SALVAGE_FAILURE_TIMEOUT = "timeout"


def _answer_window_start(text: str) -> Optional[int]:
    """Where the answer's JSON document opens, by a string-aware bracket walk.

    The depth-0 ``[`` or ``{`` that is **never closed** (the answer was cut
    mid-document) when there is one; otherwise the first depth-0 ``[``/``{``;
    ``None`` when the text has no bracket at all. Quotes toggle string state
    only inside a container, so an apostrophe or a quoted word in the prose
    ahead of the array cannot hide its bracket. Nesting is tracked with a stack
    of openers (the same string-aware walk as ``_unclosed_container`` in
    ``utils/providers/pi_family_stream.py``, over the whole text rather than
    from its first character).
    """
    first: Optional[int] = None
    open_at: Optional[int] = None
    stack: List[str] = []
    in_string = False
    escape_next = False
    pairs = {"]": "[", "}": "{"}
    for index, char in enumerate(text):
        if stack:
            if escape_next:
                escape_next = False
                continue
            if in_string:
                if char == "\\":
                    escape_next = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char in "[{":
                stack.append(char)
            elif char in pairs and stack[-1] == pairs[char]:
                stack.pop()
                if not stack:
                    open_at = None
        elif char in "[{":
            stack.append(char)
            open_at = index
            if first is None:
                first = index
    if stack and open_at is not None:
        return open_at
    return first


def _bound_salvage_text(text: str) -> str:
    """Salvage text capped at ``MAX_LOG_STREAM_BYTES``, **never cut before the answer**.

    ``_bound_stream``'s last-20-lines rule is the wrong bound here: it would cut
    the opening bracket off a pretty-printed array, which is the one part a
    repair pass cannot reconstruct. So text within the cap is kept whole — the
    usual case, since an adapter's reducer returns only the last message's text
    — and longer text is windowed forward from the answer's opening bracket
    (:func:`_answer_window_start`), then cut at the end with a marker charged
    against the cap. Text with no bracket keeps its head.
    """
    if len(text.encode("utf-8", errors="replace")) <= MAX_LOG_STREAM_BYTES:
        return text
    start = _answer_window_start(text)
    window = text[start:] if start is not None else text
    return _cut_bytes(
        window,
        MAX_LOG_STREAM_BYTES,
        f"\n... [salvage text truncated at {MAX_LOG_STREAM_BYTES} B]",
    )


#: Sentinel for "the caller has not read the hook yet": ``None`` is taken, it is
#: the hook's own "no opinion".
_HOOK_UNREAD: Any = object()


def _salvage_hook_text(provider: Any, stdout: Optional[str]) -> Optional[str]:
    """The adapter's :meth:`~utils.providers.base.LLMProvider.salvage_text` reading, once.

    The one place the hook's three-answer contract is read, so
    ``salvage_text`` and ``answer_text`` can never disagree about what the
    hook said, and a losing path that attaches both runs the hook once
    (plans/ask-answer-recovery-and-false-success.md D2.2):

    * the hook's string, as it returned it (``""`` included: "nothing there");
    * ``""`` when the hook raised: by overriding, the adapter declared its
      stdout a transport, so falling back to the raw stream would restore the
      bug the hook removes;
    * ``None`` for "no opinion": the base default, a provider with no callable
      hook, or a return that is not a string.
    """
    hook = getattr(provider, "salvage_text", None)
    if not callable(hook):
        return None
    try:
        text = hook(stdout or "")
    except Exception:  # noqa: BLE001 - a reducer may never break a run
        return ""
    return text if isinstance(text, str) else None


def _attach_salvage_text(
    details: Dict[str, Any],
    provider: Any,
    stdout: Optional[str],
    hook_text: Any = _HOOK_UNREAD,
) -> None:
    """Put the adapter's answer text on ``details['salvage_text']``, redacted then bounded.

    The salvage gate used to judge ``stdout_excerpt`` — the raw stream's last
    20 lines — and on a transport-stream adapter (pi, omp) those lines are
    event data whose ``content`` arrays pass ``has_salvageable_json``: a
    reviewer killed mid-tool-call was sent to salvage over its own
    ``thinking``/``toolCall`` parts (plan:
    review-run-scope-salvage-and-failure-visibility §4). The adapter's
    :meth:`~utils.providers.base.LLMProvider.salvage_text` hook reads the
    **full** stdout, before any bounding, and says which words are the answer.

    Called beside :func:`_attach_stdout_excerpt` at the same three losing
    sites, and — like it — one helper so the redact-then-bound order cannot
    drift between them. What it records:

    * the hook returned a string → that string, redacted, then bounded by
      :func:`_bound_salvage_text`, **even when it is ``""``**: "present and
      empty" is the adapter's verdict that there is nothing to salvage;
    * the hook raised → ``""``: by overriding, the adapter declared its stdout
      a transport, so falling back to the raw stream would restore the bug;
    * the hook returned ``None`` (the base default, "no opinion") or anything
      that is not a string → the key stays **absent**, and the gate keeps its
      old input.

    ``hook_text`` is :func:`_salvage_hook_text`'s reading when the caller has
    already taken it (a losing path that also attaches ``answer_text`` passes
    the one reading to both); left out, this helper reads the hook itself.
    """
    if hook_text is _HOOK_UNREAD:
        hook_text = _salvage_hook_text(provider, stdout)
    if hook_text is None:
        return
    details[SALVAGE_TEXT_KEY] = _bound_salvage_text(_redact(hook_text)).strip()


#: The key :func:`_attach_answer_text` writes, and only when the caller passed
#: ``want_answer_text=True`` to :func:`invoke_with_provider` (the ask lane).
#: Its value is the model's **whole** answer text, reduced from the full stdout,
#: redacted and head-capped. It goes to that caller alone — never into
#: ``.status.json``, a result record or the log
#: (plans/ask-answer-recovery-and-false-success.md D2.2).
ANSWER_TEXT_KEY = "answer_text"

#: ``answer_text``'s cap. An answer is read from the top, so the **head** is
#: kept and a marker appended (:func:`_cut_bytes`), never the tail-bound of the
#: log nor ``_bound_salvage_text``'s bracket window (D2.2).
MAX_ANSWER_TEXT_BYTES = 1024 * 1024


def _clean_envelope_answer(value: Any, text: str) -> str:
    """Rule 2 of :func:`generic_answer_text`: a clean envelope's inner answer, else ``""``.

    Clean means one of the two measured shapes (D2.2):

    * ``{"type": "result", …}`` that
      :func:`~utils.providers.result_envelope.is_clean_envelope` passes
      (claude-code, cursor-agent): its ``result`` string;
    * ``{"response": "<string>"}`` with no ``error`` and a ``status`` that is
      absent or ``"SUCCESS"`` (gemini, agy). Without the ``status`` test an
      agy failure that carries no ``error`` would pass. An ``error`` that is
      present but empty (``null``, ``""``) says no error either: agy's success
      shape is uncaptured (§14), and an answer lost to an empty field is the
      loss this plan fixes.

    Any other JSON value — a refusing envelope, grok's ``{"type":"error",…}``
    body, a record array, a bare number — is transport, never the answer.
    """
    if not isinstance(value, dict):
        return ""
    if value.get("type") == "result":
        if not is_clean_envelope(text):
            return ""
        inner = value.get("result")
        return inner if isinstance(inner, str) else ""
    response = value.get("response")
    if (
        isinstance(response, str)
        and not value.get("error")
        and value.get("status", "SUCCESS") == "SUCCESS"
    ):
        return response
    return ""


def generic_answer_text(
    stdout: Optional[str],
    *,
    framing: str = "auto",
    exit_zero_markers: Collection["re.Pattern[str]"] = (),
) -> str:
    """The answer text of a stdout whose adapter's hook has no opinion (D2.2).

    A conservative default, not a parser. It serves the adapters without a
    :meth:`~utils.providers.base.LLMProvider.salvage_text` hook
    (claude-code, cursor-agent, gemini, agy, kilocode) and any adapter added
    later without one. ``framing`` is the adapter's declared
    ``answer_framing``; the reducer never guesses it.

    Under ``"auto"`` the first rule that applies decides:

    1. an event stream (:func:`~utils.json_extractor.looks_like_ndjson`) → ``""``;
    2. a stdout that parses whole as one JSON value → the inner answer of a
       clean result envelope (:func:`_clean_envelope_answer`), ``""`` for any
       other JSON value: a provider's error body is never an answer;
    3. anything else is plain text: the whole stdout, ANSI escapes removed.

    Under ``"plain"`` (the stdout *is* the reply: kilocode) only rule 3 runs,
    so a direct JSON object, a JSON array or NDJSON the question asked for
    comes back whole.

    **Rule 3's exit-zero check.** Rule 3 cannot tell a prose answer from a
    prose error, and every exit-0 ``PARSE_ERROR`` may reach it (D3.1). So when
    one of the adapter's own ``exit_zero_markers`` matches the lowercased
    stdout (:func:`~utils.providers.base._matches_marker`, as step 6 of
    ``classify_streams`` does), rule 3 gives ``""`` — on every path, success
    included, under both framings. Only the adapter's markers: the shared
    auth, rate-limit and context tables match words an answer *about* auth or
    rate limits uses. The haystack is the stdout both as captured and with its
    ANSI escapes removed, so a painted ``Error:`` still matches a marker.

    Whitespace-only text is ``""``. Text is otherwise returned as is, not
    stripped: the caller redacts and caps it.
    """
    raw = stdout or ""
    text = _ANSI_ESCAPE.sub("", raw)
    if not text.strip():
        return ""
    if framing != "plain":
        if looks_like_ndjson(text):
            return ""
        try:
            value = json.loads(text)
        except ValueError:
            pass
        else:
            answer = _clean_envelope_answer(value, text)
            return answer if answer.strip() else ""
    if exit_zero_markers and (
        _matches_marker(exit_zero_markers, raw.lower())
        or _matches_marker(exit_zero_markers, text.lower())
    ):
        return ""
    return text


def _attach_answer_text(
    details: Dict[str, Any],
    provider: Any,
    stdout: Optional[str],
    hook_text: Any = _HOOK_UNREAD,
) -> None:
    """Put the model's whole answer text on ``details['answer_text']`` (D2.2).

    Set on every :func:`invoke_with_provider` exit that ran the child — the
    success return, the exit-0 parse failure, the non-zero exit and the
    timeout — when the caller asked for it, from the **full** stdout:

    * the hook returned a string → used as is; ``""`` stays ``""``, a final
      "nothing to recover" (so does a hook that raised, and whitespace alone);
    * the hook had no opinion → :func:`generic_answer_text` under the
      adapter's ``answer_framing`` and ``exit_zero_failure_markers``.

    Then :func:`_redact` and the :data:`MAX_ANSWER_TEXT_BYTES` head-kept cap —
    nothing else. Hook text **never** goes through :func:`_bound_salvage_text`:
    its 45 KB window, forward from the first unclosed bracket, is built for a
    findings array and would cut the head off a long prose answer. The two
    keys read one hook result and each cuts its own copy, differently on
    purpose.

    ``hook_text`` is :func:`_salvage_hook_text`'s reading when the caller has
    already taken it for ``salvage_text``; left out, it is read here.
    """
    if hook_text is _HOOK_UNREAD:
        hook_text = _salvage_hook_text(provider, stdout)
    if hook_text is None:
        try:
            text = generic_answer_text(
                stdout,
                framing=getattr(provider, "answer_framing", "auto"),
                exit_zero_markers=tuple(
                    getattr(provider, "exit_zero_failure_markers", ()) or ()
                ),
            )
        except Exception:  # noqa: BLE001 - a reducer may never break a run
            text = ""
    else:
        text = hook_text
    if not text.strip():
        details[ANSWER_TEXT_KEY] = ""
        return
    details[ANSWER_TEXT_KEY] = _cut_bytes(
        _redact(text),
        MAX_ANSWER_TEXT_BYTES,
        f"\n... [answer text truncated at {MAX_ANSWER_TEXT_BYTES} B]",
    )


_READONLY_AUDIT_KEY = _readonly_audit_mod.DETAILS_KEY


def _readonly_audit(
    provider: Any, stdout: Optional[str], sandbox_fallback: Any = None
) -> Optional[Dict[str, Any]]:
    """The adapter's read-only verdict on this attempt's **full** stdout, compact.

    Only for an attempt dispatched on the uncontained rung (``sandbox_fallback``
    names ``unsandboxed``) or on the plugin's own jail (``plugin-landlock``,
    2026-09-30): the first is the one slot the porcelain check brackets, the
    second the one the mode check and the home check bracket, and both read
    this verdict to decide whether a change seen in the window is downgraded to
    a not-attributed warning (plan codex-sandbox-unavailable §6 F1, "What it
    fixes"). A default or contained-rung run adds no key — the same rule the D6
    ``sandbox`` provenance key follows.

    Plan §4.2 option B / 4.2: the audit must see the whole in-memory stream —
    the persisted log and ``stdout_excerpt`` are both cut at
    ``MAX_LOG_STREAM_BYTES``, and a cut stream has no ``turn.completed`` and
    would fail every long slot. So it runs here, at parse time, on every
    outcome that has a stream, before anything is bounded; only the compact
    verdict dict leaves (never the stream). ``None`` when the adapter has no
    opinion or the hook raised — a missing verdict, which
    ``readonly_audit.combine_audits`` treats as not clean.
    """
    if sandbox_rung_id(sandbox_fallback) not in (
        SANDBOX_RUNG_UNSANDBOXED, *_INCIDENTAL_RUNG_IDS,
    ):
        return None
    hook = getattr(provider, "audit_readonly_stream", None)
    if hook is None:
        return None
    try:
        verdict = hook(stdout or "")
    except Exception:  # noqa: BLE001 - an audit may never break a run
        return None
    if verdict is None:
        return None
    to_dict = getattr(verdict, "to_dict", None)
    if callable(to_dict):
        verdict = to_dict()
    return dict(verdict) if isinstance(verdict, dict) else None


def _attach_readonly_audit(
    details: Dict[str, Any], provider: Any, stdout: Optional[str],
    sandbox_fallback: Any = None,
) -> Optional[Dict[str, Any]]:
    """Put :func:`_readonly_audit`'s verdict on ``details['readonly_audit']``."""
    verdict = _readonly_audit(provider, stdout, sandbox_fallback)
    if verdict is not None:
        details[_READONLY_AUDIT_KEY] = verdict
    return verdict


def _attach_usage(
    details: Dict[str, Any], provider: Any, stdout: Optional[str], stderr: Optional[str]
) -> None:
    """Put what the run spent on ``details`` as ``usage``, when the adapter can say.

    The adapter's own :meth:`~utils.providers.base.LLMProvider.parse_usage`,
    under the same never-raise rule ``subagent_executor._safe_parse_usage``
    applies (D3j): metrics must not break a run, and an adapter that reports
    nothing leaves the key **absent** — a ``{}`` would read as "reported,
    free".

    Called on **every** outcome ``invoke_with_provider`` can reach — the
    non-zero exit, the timeout kill, and (Stage U) the exit-0 parse, clean or
    not. It began as a losing-paths-only helper, on the reasoning that a
    completed slot's usage was "a separate question"; it was not a separate
    question, it was the same one asked of the runs an operator is most
    likely to pay for. A successful slot's envelope was parsed for the answer
    and then discarded, so the fan-out could name what a *failed* $25 run
    spent and nothing at all about the run that succeeded beside it. The rule
    is now uniform: whatever the adapter can say about what a run spent
    travels on ``details``, whichever way the run ended.
    """
    try:
        usage = provider.parse_usage(stdout or "", stderr or "")
    except Exception:  # noqa: BLE001 - metrics must not break the run
        return
    if isinstance(usage, dict) and usage:
        details["usage"] = usage


#: What a run cost, as one clause (``$25.05 est., 137,348 output tokens``).
#: Defined in :mod:`utils.metrics` — beside the other number formatters, and
#: importable by the report generator, which cannot import this module at all
#: (it also runs as a bare script, and everything here is a relative import).
#: Re-exported under this name because the failed-slot error line has always
#: reached it here, and because one renderer for every surface that names the
#: number is the whole point of it: the log line, the ``**Models:**`` line and
#: the HTML badge say the same words about the same run.
describe_usage = _describe_usage


def _save_log(
    log_file: Union[str, Path],
    model: str,
    prompt: str,
    stdout: str,
    stderr: str,
    returncode: int,
    success: bool,
    error: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    result_source: Optional[str] = None,
    stdout_parse_error: Optional[str] = None,
    readonly_audit: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Save agent output to a log file for debugging.

    Args:
        log_file: Path to save the log
        model: Model identifier, ``"<provider>:<model>"`` where available —
            the header names the provider half, so a bare model string (no
            ``:``) still renders, just without a provider name to show.
        prompt: The prompt sent to the agent
        stdout: Standard output from the process
        stderr: Standard error from the process
        returncode: Process return code
        success: Whether the invocation was successful — the FINAL outcome,
            not necessarily the stdout extractor's verdict (see
            ``stdout_parse_error``/``result_source``).
        error: Error message if failed
        duration_seconds: How long the agent ran
        result_source: Where the caller's data ultimately came from —
            ``"file"``, ``"file_extracted"``, ``"stdout_fallback"``, or
            ``None`` when the caller has no secondary channel to name.
        stdout_parse_error: Set when the stdout extractor itself failed, even
            if a secondary channel (the file) went on to salvage the run —
            the two fields are independent because a failed stdout parse and
            an overall success are not a contradiction. Rendered as
            ``Stdout parse: failed (...)`` only when ``result_source`` is
            NOT one of ``FILE_WRITTEN_SOURCES`` — a file-output provider is
            told not to print JSON on stdout at all, so a failed stdout
            parse beside a file-channel success is expected, not a fault
            (F9.2).
        readonly_audit: The attempt's compact read-only verdict (plan §4.2),
            rendered as one ``Readonly audit:`` header line — the verdict,
            never the stream it was computed on (which the ``STDOUT`` section
            below carries bounded, like any other).

    Returns:
        True if log was saved successfully, False otherwise

    Every rendered field is passed through §4.5's ``redact_text`` **first** and
    bounded by §4.4's caps **second**. This is the sink where all nine planted
    secret shapes landed on a *successful* run, and the sink that wrote a
    6,254,326 B log for one ``review-plan``.
    """
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # §4.5 before §4.4: redact the fully rendered text, then cap it. Reversing
        # these two would slice a secret across a cut and leave a remnant nothing
        # downstream can match.
        prompt = _redact(prompt or "")
        stdout = _bound_stream(_redact(stdout or ""))
        stderr = _bound_stream(_redact(stderr or ""))
        error = _redact(error) if error else error

        # Provider-neutral (§Fix1): every adapter shares this sink, so the
        # header names the provider the model spec actually carries rather
        # than a fixed "CURSOR-AGENT" left over from the original single-CLI
        # implementation. A bare model string (no ``provider:model`` split)
        # falls back to naming itself.
        provider_label = (model or "").split(":", 1)[0].strip().upper() or "PROVIDER"

        lines = [
            "=" * 80,
            f"{provider_label} LOG",
            "=" * 80,
            f"Timestamp: {datetime.now().isoformat()}",
            f"Model: {model or 'default'}",
            f"Success: {success}",
            f"Return Code: {returncode}",
        ]

        if duration_seconds is not None:
            lines.append(f"Duration: {duration_seconds:.1f}s")

        if result_source:
            lines.append(f"Result source: {result_source}")

        if stdout_parse_error:
            # `file (written as <name>)` is the file channel too: a result
            # read from under the wrong name (`invoke_with_file_output` 1b).
            if (result_source or "").split(" ", 1)[0] in FILE_WRITTEN_SOURCES:
                # `render_output_location` told this provider NOT to print
                # JSON on stdout, so a failed stdout parse is the expected
                # shape of a run the file channel already answered for — not
                # a fact worth flagging beside `Success: True` (F9.2, audited
                # 2026-09-16 on review-tasks: two successful file-channel runs
                # logged "Stdout parse: failed (No valid JSON found in
                # text)").
                lines.append("Stdout: not used (file output)")
            else:
                lines.append(f"Stdout parse: failed ({stdout_parse_error})")

        if readonly_audit is not None:
            lines.append(
                f"Readonly audit: {_redact(_readonly_audit_mod.describe(readonly_audit))}"
            )

        if error:
            lines.append(f"Error: {error}")

        truncated_prompt = prompt[:MAX_LOGGED_PROMPT_LENGTH]
        if len(prompt) > MAX_LOGGED_PROMPT_LENGTH:
            truncated_prompt += "..."

        lines.extend([
            "",
            "-" * 40,
            "PROMPT",
            "-" * 40,
            truncated_prompt,
            "",
            "-" * 40,
            "STDOUT",
            "-" * 40,
            stdout if stdout else "(empty)",
            "",
            "-" * 40,
            "STDERR",
            "-" * 40,
            stderr if stderr else "(empty)",
            "",
            "=" * 80,
            "",
        ])

        # The whole-file backstop, so "~100 KB" is a property of the bytes on
        # disk rather than an inference from the per-stream budgets. Safe to cut
        # blind: everything above was redacted before it got here.
        rendered = _cut_bytes(
            "\n".join(lines),
            MAX_LOG_TOTAL_BYTES,
            f"\n... [log truncated at {MAX_LOG_TOTAL_BYTES} B]\n",
        )

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        return True
    except (IOError, OSError) as e:
        print(f"WARNING: Failed to save log to {log_file}: {e}")
        return False


def _served_model_attribution(
    provider: Any, model: str, stdout: str
) -> Optional[Tuple[str, bool, Optional[str]]]:
    """§3.6's ``(served_model, is_fallback, warning)`` for one attempt, or None.

    **Gated on a configured fallback list, which ships empty.** Attribution is
    mandatory *whenever a fallback is configured* — without it a report
    attributes a haiku answer to the sonnet the user asked for. With nothing
    configured there is no substitution to disclose, so nothing is parsed,
    nothing is recorded and nothing is printed: the result dict is byte-for-byte
    what it has always been.

    Only claude-code answers here (its envelope carries ``modelUsage``); §4.6
    stays closed, so every other adapter lacks both methods and returns None.

    **Read, never depended on.** Any failure to answer degrades to None — an
    attribution field never fails an otherwise-successful attempt.
    """
    resolve = getattr(provider, "resolve_served_model", None)
    configured = getattr(provider, "fallback_models", None)
    if resolve is None or configured is None:
        return None
    try:
        fallbacks = configured(model)
        if not fallbacks:
            return None
        return resolve(stdout, model, fallbacks)
    except Exception:  # noqa: BLE001 - attribution never fails a good attempt
        return None


# ---------------------------------------------------------------------------
# The Lane A spawn: `subprocess.run`'s contract, plus the tree sweep (plan:
# review-run-scope-salvage-and-failure-visibility D3.3)
# ---------------------------------------------------------------------------

#: SIGTERM → SIGKILL grace for a stopped Lane A CLI and for each process group
#: its snapshot recorded. SIGTERM first because pi reaps its own detached shells
#: only from its SIGTERM handler; the bare SIGKILL `subprocess.run` sent skipped
#: it.
LANE_A_TERMINATE_GRACE_S = process_control.DEFAULT_TERMINATE_GRACE_S

#: Ceiling on the post-sweep drain. A second ``communicate()`` collects whatever
#: the CLI wrote before it died, but a grandchild the sweep did not reach would
#: keep the inherited pipe open for ever — the reason
#: ``write_batch_scheduler._run_verify_command`` captures to a file — so a
#: drain that outlives this falls back to the output already read.
LANE_A_DRAIN_S = 5.0

#: A CLI that died of one of these was stopped from outside the slot — a
#: terminal Ctrl-C reaches the whole foreground group, an abort SIGTERMs the
#: worker's — and its detached children were not told. Named so a fan-out slot
#: running on a worker thread, where no ``KeyboardInterrupt`` is ever raised,
#: still sweeps what its CLI left behind.
_STOP_SIGNALS = frozenset(
    int(sig) for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None))
    if sig is not None
)

#: The same stops as a CLI that *handled* the signal reports them: ``128 + N``,
#: the shell's convention. pi installs its own SIGTERM handler, reaps its shell
#: and exits 143 — never dying of the signal — while a ``timeout`` inside that
#: shell leads a group of its own and survives it.
_STOP_EXIT_CODES = frozenset(128 + sig for sig in _STOP_SIGNALS)

#: ``STATUS_CONTROL_C_EXIT``: the Windows spelling of "died of Ctrl-C"
#: (2026-10-25). Windows has no signal to die of, so a return code there is
#: never negative and the ``-N`` half of :func:`_stopped_from_outside` never
#: fires. A console process whose Ctrl-C or Ctrl-Break reached the default
#: handler exits with this status instead, and a Python CLI whose
#: ``KeyboardInterrupt`` went unhandled exits with it on purpose (3.8+), so its
#: parent can tell. ``Popen`` reports it unsigned. A CLI that handled the
#: Ctrl-C and exited 130 is :data:`_STOP_EXIT_CODES` on Windows as on POSIX.
#: No POSIX status is ever this value (those are 0-255, or ``-N``).
_WINDOWS_CTRL_C_EXIT = 0xC000013A


def _stopped_from_outside(returncode: Optional[int]) -> bool:
    """Whether a CLI that returned on its own was stopped by a signal from outside.

    Either it died of one of :data:`_STOP_SIGNALS` (``-N``) or its own handler
    exited with ``128 + N`` for it (:data:`_STOP_EXIT_CODES`), or, on Windows,
    the console's Ctrl-C ended it (:data:`_WINDOWS_CTRL_C_EXIT`). There a
    terminal Ctrl-C reaches every process on the console, and what the CLI
    started that ignored it is still in the CLI's job, which this stop ends.
    A CLI killed outright from outside (``taskkill /F``, another
    ``TerminateProcess``) exits with whatever code its killer chose, usually
    1, which no exit code tells from a failure, so it is not one; the
    registry's sweep is what reaches its job when the stop is ours.
    """
    if returncode is None:
        return False
    return (-returncode in _STOP_SIGNALS or returncode in _STOP_EXIT_CODES
            or returncode == _WINDOWS_CTRL_C_EXIT)


def _stop_cli_tree(
    proc: "subprocess.Popen[Any]", job: Optional[process_control.TreeJob] = None,
) -> Optional[process_control.TreeSweep]:
    """Snapshot *proc*'s descendants, then stop it and every snapshotted group.

    The snapshot merges a fresh walk (taken now, while *proc* is un-reaped, so
    its parent links still lead to its children) with the registry's last
    refreshed one (which still holds them when *proc* itself died first). On
    Windows, where there is no snapshot to take, *job* is the CLI's Job Object
    and is terminated right after the CLI (2026-10-25). Never raises: teardown
    must not mask the timeout or the interrupt that asked for it, so a failed
    sweep falls back to a plain kill of the CLI, and then of its job.
    """
    try:
        snapshot = process_control.live_cli_registry.snapshot_for(proc)
        return process_control.terminate_timed_out(
            proc, snapshot, LANE_A_TERMINATE_GRACE_S, job=job
        )
    except Exception:  # noqa: BLE001 - see above
        try:
            proc.kill()
        except OSError:
            pass
        if job is not None:
            try:
                job.terminate()
            except Exception:  # noqa: BLE001 - see above
                pass
        return None


def _drain_after_stop(
    proc: "subprocess.Popen[Any]", expired: subprocess.TimeoutExpired
) -> Tuple[Any, Any]:
    """Everything the stopped CLI wrote, without ever hanging on a survivor.

    The second ``communicate()`` returns the whole capture (what the first call
    had read before the deadline included). If even that blocks, the newest
    partial capture is used and the pipes are let go.
    """
    try:
        return proc.communicate(timeout=LANE_A_DRAIN_S)
    except subprocess.TimeoutExpired as drained:
        return drained.stdout, drained.stderr
    except (OSError, ValueError):
        return expired.stdout, expired.stderr


def _release_pipes(proc: "subprocess.Popen[Any]") -> None:
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        try:
            if stream is not None:
                stream.close()
        except (OSError, ValueError):  # pragma: no cover - best effort
            pass


def _run_provider_cli(
    cmd: List[str],
    *,
    input: Optional[str] = None,
    timeout: Optional[float] = None,
    capture_output: bool = False,
    **popen_kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run one Lane A provider CLI: ``subprocess.run``'s contract, and its tree.

    Same arguments, same ``CompletedProcess``, and the same ``TimeoutExpired``
    carrying the output so far — the ``TimeoutExpired`` handler in
    :func:`invoke_with_provider` and §4's salvage read that partial stdout. What
    changes is what a stop does. ``subprocess.run`` SIGKILLs the direct child
    only, which skips pi's own cleanup and leaves every child in a session of its
    own running (pi's detached shells, and a ``timeout`` inside one, which leads
    a group of its own). Here, on the deadline:

    1. the CLI's descendants are snapshotted while it is still alive;
    2. the CLI is SIGTERMed, given :data:`LANE_A_TERMINATE_GRACE_S`, then
       SIGKILLed; every snapshotted process group is swept through
       ``process_control.terminate_timed_out``;
    3. a bounded second ``communicate()`` collects the rest of the output; and
    4. a ``TimeoutExpired`` is re-raised with it and with the per-group verdicts
       as ``tree_sweep``, which the handler writes into the provider log.

    A ``KeyboardInterrupt`` (or anything else) raised while waiting does the same
    sweep and is re-raised, so the interrupt still ends the run (decision 11.9).
    The CLI is registered in ``process_control.live_cli_registry`` for exactly as
    long as it is waited on, so an aborted detached worker can sweep it too. The
    CLI is **not** moved into a session of its own: a terminal Ctrl-C must still
    reach it.

    Windows has no groups to snapshot, so the CLI is spawned in a Job Object of
    its own instead (``process_control.popen_tree``, 2026-10-25), and each stop
    above, the stop from outside included, ends that job right after the CLI.
    That is what reaches the children a ``TerminateProcess`` of the CLI alone
    left running, holding the pipes until the drain's cap. No new process group
    either: a job does not change who a terminal Ctrl-C reaches, a new group
    would. The job travels with the CLI into the registry, so a sweep ends it
    too, and is closed (never a kill) once the CLI is no longer waited on; a CLI
    that exits on its own leaves whatever it started running, as on POSIX.
    """
    if capture_output:
        popen_kwargs["stdout"] = subprocess.PIPE
        popen_kwargs["stderr"] = subprocess.PIPE
    if input is not None:
        popen_kwargs["stdin"] = subprocess.PIPE
    proc, job = process_control.popen_tree(cmd, **popen_kwargs)
    try:
        with process_control.live_cli_registry.tracking(proc, job):
            try:
                stdout, stderr = proc.communicate(input=input, timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                sweep = _stop_cli_tree(proc, job)
                out, err = _drain_after_stop(proc, exc)
                expired = subprocess.TimeoutExpired(
                    proc.args, exc.timeout, output=out, stderr=err
                )
                expired.tree_sweep = sweep
                raise expired from None
            except BaseException:
                _stop_cli_tree(proc, job)
                raise
            if _stopped_from_outside(proc.returncode):
                # Dead already, and its detached children may not be: only the
                # registry's snapshot still links them to this slot (on Windows,
                # its job).
                _stop_cli_tree(proc, job)
    finally:
        # After `tracking` has unregistered the CLI, so a sweep can no longer
        # be terminating the job through the handle closed here.
        try:
            _release_pipes(proc)
        finally:
            if job is not None:
                job.close()
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


def _describe_tree_sweep(expired: BaseException) -> str:
    """``"; <verdicts>"`` for a timeout's log line, or ``""`` when none ran."""
    sweep = getattr(expired, "tree_sweep", None)
    if sweep is None:
        return ""
    try:
        return f"; {sweep.describe()}"
    except Exception:  # noqa: BLE001 - a log suffix never fails the timeout path
        return ""


# ---------------------------------------------------------------------------
# A fan-out slot on the plugin's Landlock jail (plan
# codex-sandbox-unavailable-findings-and-fixes §6 F1, 2026-09-30)
# ---------------------------------------------------------------------------
#
# `invoke_with_provider` is the fan-out's spawn site, so it owns the attempt's
# half of the grant ("How a dispatch receives its grant"): the read-only
# `JailRequest` built from its own `cwd` (a fan-out slot never carries a write
# scope), the attempt's scratch `TMPDIR` on its `setup_cleanup` stack (released
# by the subprocess `finally`, after `_run_provider_cli` swept the child's
# process groups — never by the lane's coroutine, which `asyncio.to_thread`
# can cancel under a live child), the context completed from the composed
# child env, the one `wrap_argv`, the home snapshots around the child, and
# what is read back afterwards. Only paths, classes and counts travel back on
# `details`; the context and the snapshots die with the attempt.


def _jail_rung(provider: Any, rung_id: Optional[str]) -> Optional[Any]:
    """The adapter's declared wrapping rung ``rung_id`` for ``generate``, or
    ``None`` when ``rung_id`` names no wrapping rung of this adapter."""
    if not rung_id:
        return None
    hook = getattr(provider, "sandbox_fallback_rungs", None)
    if not callable(hook):
        return None
    try:
        rungs = tuple(hook(PROFILE_GENERATE) or ())
    except Exception:  # noqa: BLE001 - a declaration read never ends a slot
        return None
    for rung in rungs:
        if getattr(rung, "name", None) == rung_id and getattr(rung, "wrapper", None):
            return rung
    return None


#: Every live fan-out child in this process: token → (provider name, the
#: tokens of same-provider children whose lifetime overlapped it). What the
#: ``[CODEX_HOME_CHECK]`` line's "how many other Codex children of this run
#: were live in the window" is read from — they share one ``$CODEX_HOME``.
_LIVE_CHILDREN: Dict[int, Tuple[str, set]] = {}
_LIVE_LOCK = threading.Lock()
_LIVE_NEXT = [0]


@contextlib.contextmanager
def _live_child(provider_name: str):
    """Register one child for as long as it runs; yields the (growing) set of
    same-provider children that overlapped it."""
    with _LIVE_LOCK:
        _LIVE_NEXT[0] += 1
        token = _LIVE_NEXT[0]
        overlap: set = set()
        for other, (name, others) in _LIVE_CHILDREN.items():
            if name == provider_name:
                others.add(token)
                overlap.add(other)
        _LIVE_CHILDREN[token] = (provider_name, overlap)
    try:
        yield overlap
    finally:
        with _LIVE_LOCK:
            _LIVE_CHILDREN.pop(token, None)


def _cached_cli_version(provider_name: str) -> str:
    """The CLI version this process already read for ``provider_name`` — the
    executor's version preflight or the sandbox probe's own read — or ``""``.

    Cache-only on purpose: a ``[JAIL_DENIED]`` line must never spawn a
    ``--version`` per slot. The fan-out's probe reads codex's version once per
    process (its ladder declares a ``removed_at`` rung), so on the rung it is
    normally there.
    """
    try:
        from . import subagent_executor as _executor
    except Exception:  # noqa: BLE001 - a diagnostic never ends a slot
        return ""
    for name in ("_VERSION_CACHE", "_PROBE_VERSION_CACHE"):
        cache = getattr(_executor, name, None)
        if isinstance(cache, dict):
            value = cache.get(provider_name)
            if value and value != "unknown":
                return str(value)
    return ""


def _version_newer(installed: str, measured: str) -> bool:
    match = re.search(r"\d+(?:\.\d+)+", installed or "")
    if not match or not measured:
        return False
    return version_tuple(match.group(0)) > version_tuple(measured)


def _render_home_text(text: str) -> str:
    """``text`` with every ``$HOME/`` prefix shown as ``~/`` (a line pasted
    into an issue as it is)."""
    home = os.path.expanduser("~")
    if not text or not home or home in ("~", os.sep):
        return text or ""
    return text.replace(home + os.sep, "~" + os.sep)


def jail_denied_notice(
    provider_name: str,
    model_spec: str,
    rung: Any,
    evidence: Dict[str, Any],
    allow_list: str,
    installed: str,
) -> str:
    """The one ``[JAIL_DENIED]`` line for a slot the plugin's jail failed
    (F1 "Where it sits" item 6, "What prints").

    The runner and spec, the rung, the denied path or "path not named", the
    excerpt, the allow-list, the installed and measured-through versions —
    with "the likely cause" when codex is newer — and the next steps. ``$HOME``
    renders as ``~`` throughout.
    """
    rung_name = getattr(rung, "name", SANDBOX_RUNG_PLUGIN_LANDLOCK)
    measured = (getattr(rung, "measured_through", None) or ("",))[0] or "unknown"
    path = evidence.get("path")
    where = evidence.get("where") or "stderr"
    # The quoted line is codex's raw stderr or error event, and this notice
    # reaches stdout, the detached run log and the closing summary: redacted
    # first, as `describe_failure`'s text is, then `$HOME` rendered as `~`.
    said = _render_home_text(" ".join(_redact(str(evidence.get("line") or "")).split()))
    if path:
        denied = _landlock.render_home(path)
    elif evidence.get("class") == _landlock.JAIL_CLASS_PROBABLE:
        denied = "path not named (Codex did not name the path; a probable jail denial)"
    else:
        denied = "path not named"
    versions = f"{provider_name} installed {installed or 'unknown'}, jail measured through {measured}"
    if _version_newer(installed, measured):
        versions += (
            f"; {provider_name.capitalize()} is newer than the jail was measured "
            f"with, the likely cause"
        )
    return (
        f"{JAIL_DENIED_MARKER} {provider_name} ({model_spec}): the plugin's "
        f"Landlock jail (fallback rung {rung_name!r}) denied a write "
        f"{provider_name} itself needed, so the turn failed: {denied}; "
        f"{where}: \"{said}\"; allow list: {allow_list or '(unavailable)'}; "
        f"{versions}; next steps: (1) compare with `multi_llm.py doctor` (its "
        f"{rung_name} row lists the allow-list, both versions and the switch); "
        f"(2) report it at {JAIL_DENIED_ISSUES_URL} with this line and that row "
        f"(the allow-list is not configurable); (3) to run the job anyway, set "
        f"this key to a runner that is not Codex (for example "
        f"claude-code:<model>) in .multi-llm/providers.yaml, or for one run set "
        f"{SKIP_RUNG_ENV}={rung_name}"
    )


def _toml_tree(text: Optional[str]) -> Optional[Dict[str, Any]]:
    if text is None:
        return None
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover - 3.10 keeps compare_home's names
        return None
    try:
        return tomllib.loads(text)
    except Exception:  # noqa: BLE001 - an unparsable file keeps the coarse names
        return None


def _leaf_tables(value: Any, prefix: str) -> List[str]:
    """The dotted names an added or removed value spans: a table of tables is
    named per sub-table (``mcp_servers.x``), a table holding keys by itself."""
    if isinstance(value, dict) and value and all(isinstance(v, dict) for v in value.values()):
        names: List[str] = []
        for key in sorted(value):
            names.extend(_leaf_tables(value[key], f"{prefix}.{key}"))
        return names
    return [prefix]


def _diff_names(before: Any, after: Any, prefix: str = "") -> List[str]:
    names: List[str] = []
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            dotted = f"{prefix}{key}"
            if key not in before:
                names.extend(_leaf_tables(after[key], dotted))
            elif key not in after:
                names.extend(_leaf_tables(before[key], dotted))
            elif before[key] != after[key]:
                if isinstance(before[key], dict) and isinstance(after[key], dict):
                    names.extend(_diff_names(before[key], after[key], dotted + "."))
                else:
                    names.append(dotted)
    elif before != after:
        names.append(prefix.rstrip(".") or "(file)")
    return names


def _config_key_names(before_text: Optional[str], after_text: Optional[str]) -> List[str]:
    """The table or key names that changed in ``config.toml`` — never a value —
    naming an added table of tables by its sub-tables (``mcp_servers.x``
    rather than just ``mcp_servers``), so the ``[CODEX_HOME_CHECK]`` line says
    which server a slot added. ``[]`` when either side cannot be parsed
    (``compare_home``'s own names are kept then)."""
    before, after = _toml_tree(before_text), _toml_tree(after_text)
    if before is None or after is None:
        return []
    return _diff_names(before, after)


@dataclass
class _JailedAttempt:
    """One attempt on the plugin's jail, alive only inside
    :func:`invoke_with_provider` — never stored anywhere else."""

    rung: Any
    request: JailRequest
    tmpdir: str
    cwd: str
    context: Optional[JailContext] = None
    home_before: Any = None
    live: set = field(default_factory=set)

    def allow_list(self) -> str:
        if self.context is None:
            return ""
        try:
            return _landlock.render_allow_list(_landlock.allow_entries(self.context))
        except Exception:  # noqa: BLE001 - a diagnostic never ends a slot
            return ""


def _jail_refused_result(
    provider_name: str, model: str, rung: Any, message: str,
    *, path: Optional[str], reason: str, failure_reason: str,
) -> Dict[str, Any]:
    """A slot the jail could not be granted for: nothing was spawned."""
    evidence = {
        "where": "spawn", "line": message[:300], "path": path,
        "class": _landlock.JAIL_CLASS_JAIL, "reason": reason,
    }
    details: Dict[str, Any] = {
        "provider": provider_name,
        "model": model,
        "failure_reason": failure_reason,
        "retryable": False,
    }
    if failure_reason == FAILURE_JAIL_DENIED:
        evidence["notice"] = jail_denied_notice(
            provider_name, f"{provider_name}:{model}", rung, evidence, "",
            _cached_cli_version(provider_name),
        )
        evidence["rung"] = getattr(rung, "name", None)
        details["jail_failure"] = evidence
        error = (
            f"{provider_name} was not started: denied by the plugin's jail: "
            f"{_landlock.render_home(path) or 'path not named'} ({message})"
        )
    else:
        error = f"{provider_name} was not started: {message}"
    return {
        "success": False,
        "error": error,
        "error_code": ERROR_SUBPROCESS_FAILED,
        "details": details,
    }


def _turn_failed(stdout: Optional[str]) -> bool:
    """Whether the stream holds a top-level ``turn.failed`` event."""
    for raw in (stdout or "").splitlines():
        raw = raw.strip()
        if not raw.startswith("{") or "turn.failed" not in raw:
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.failed":
            return True
    return False


def _exit0_left_no_answer(hook_text: Optional[str], stdout: Optional[str]) -> bool:
    """Whether a jailed child that exited 0 left no finished answer — the only
    exit 0 a jail failure is read on.

    The parse verdict is not that question: codex's ``parse_output`` succeeds
    only when it finds JSON, so a finished prose ``ask`` answer, or a review
    whose JSON failed to parse for another reason, reads as failed. The answer
    is the adapter's own final answer text (``hook_text``, the
    :func:`_salvage_hook_text` reading — codex's last ``agent_message``), and a
    ``turn.failed`` event means the turn never finished, whatever narration
    came before it.
    """
    answered = isinstance(hook_text, str) and bool(hook_text.strip())
    return not answered or _turn_failed(stdout)


def _jail_after_child(
    details: Dict[str, Any],
    jail: Optional[_JailedAttempt],
    *,
    provider_name: str,
    model: str,
    stdout: str,
    stderr: str,
    returncode: Optional[int],
    failed: bool,
    timed_out: bool = False,
) -> Tuple[Optional[str], str]:
    """What the parent reads back after a jailed child exited or was killed,
    while the context is still alive (F1 order step 8).

    Always: the home check (``details["home_check"]``, only when the home's
    security-relevant set changed or a foreign trust table appeared) and the
    denials inside the model's own commands (``details["jail_denials"]``, for
    the slot's log line — never a failure). On a failed attempt: the jail
    failure. Returns ``(error, suffix)``: ``error`` replaces the failure
    message for a jail or probable jail denial (``failure_reason:
    jail-denied``, non-retryable, ``details["jail_failure"]`` with the
    ``[JAIL_DENIED]`` line under ``notice``); ``suffix`` is the "not a jail
    denial: <reason>" note for an ordinary permission error.

    A child killed at its deadline (``timed_out``) is a timeout and nothing
    else, as on the executor lane: an EACCES it printed before the kill never
    turns it into a never-retried jail denial.
    """
    if jail is None or jail.context is None:
        return None, ""
    context = jail.context
    try:
        after = _landlock.home_snapshot(context.codex_home, [jail.cwd])
        change = _landlock.compare_home(jail.home_before, after)
    except Exception:  # noqa: BLE001 - a check never ends a slot
        change = None
    if change is not None and (change.changed or change.foreign_trust):
        record = change.to_dict()
        if _landlock.HOME_CONFIG in change.changed:
            names = _config_key_names(
                getattr(jail.home_before, "config_text", None),
                getattr(after, "config_text", None),
            )
            if names:
                record["config_keys"] = names
        record["home"] = _landlock.render_home(context.codex_home)
        record["other_live_children"] = len(jail.live)
        details["home_check"] = record
    try:
        denials = _landlock.jail_denied_edits(stdout or "", context, cwd=jail.cwd)
        record = denials.to_dict()
        record["total"] = denials.total
        named: List[str] = []
        for group in denials.failed_file_changes:
            named.extend(group)
        named.extend(denials.out_of_scope_paths)
        record["paths"] = [p for i, p in enumerate(named) if p not in named[:i]][:3]
        details["jail_denials"] = record
    except Exception:  # noqa: BLE001 - a count never ends a slot
        pass
    if not failed or timed_out:
        return None, ""
    # The wrapper's own refusal at dispatch (exit 125/126 with its note) is
    # read first, the same helper the executor lane uses: a jail failure,
    # never a model error, never retried on another rung.
    evidence = _landlock.wrapper_evidence(returncode, stderr or "")
    if evidence is None:
        try:
            evidence = _landlock.is_jail_failure(stderr or "", stdout or "", context)
        except Exception:  # noqa: BLE001 - a diagnostic never ends a slot
            evidence = None
    if evidence is None:
        return None, ""
    if evidence.klass == _landlock.JAIL_CLASS_ORDINARY:
        return None, f"; not a jail denial: {evidence.reason}"
    record = evidence.to_dict()
    installed = _cached_cli_version(provider_name)
    allow = jail.allow_list()
    record.update({
        "rung": getattr(jail.rung, "name", None),
        "installed_version": installed,
        "measured_through": (getattr(jail.rung, "measured_through", None) or ("",))[0],
        "allow_list": allow,
        "notice": jail_denied_notice(
            provider_name, f"{provider_name}:{model}", jail.rung,
            evidence.to_dict(), allow, installed,
        ),
    })
    details["jail_failure"] = record
    details["failure_reason"] = FAILURE_JAIL_DENIED
    details["retryable"] = False
    where = _landlock.render_home(evidence.path) if evidence.path else "path not named"
    return (
        f"denied by the plugin's jail: {where} (fallback rung "
        f"{getattr(jail.rung, 'name', '?')!r}; the jail-denied line in this "
        f"run's log names the allow-list, the versions and the next steps)",
        "",
    )


def invoke_with_provider(
    prompt: str,
    model_spec: str,
    timeout: Optional[int] = None,
    log_file: Optional[Union[str, Path]] = None,
    cwd: Optional[str] = None,
    prompt_transport: Optional[str] = None,
    anchor: Optional[Union[str, Path]] = None,
    schema_phase: Optional[str] = None,
    _defer_parse_failure_log: bool = False,
    sandbox_fallback: Optional[str] = None,
    want_answer_text: bool = False,
) -> Dict[str, Any]:
    """Invoke an LLM using the provider abstraction.

    This is the primary function for invoking LLM providers. It handles
    provider lookup, command building, subprocess execution, and output
    parsing with consistent error reporting.

    Args:
        prompt: The prompt to send to the LLM.
        model_spec: Model specification in "provider:model" or "model" format.
                   If no provider prefix is given, uses the default provider
                   from providers.yaml configuration.
        timeout: Optional timeout override in seconds. Uses provider default
                if not specified.
        log_file: Optional path to save full output log for debugging.
        prompt_transport: Optional non-argv transport override (D2d) —
            ``"stdin"`` writes the prompt to the child's stdin and omits it from
            argv, so no part of it is measured against the Windows
            command-line cap. Defaults to the adapter's ``prompt_transport``
            (``"argv"`` for every adapter today), keeping existing invocations
            byte-identical. Refused with SUBPROCESS_FAILED when the adapter does
            not declare support, rather than silently falling back to argv and
            re-introducing the cap the caller was avoiding.
        anchor: Optional discovery anchor (the run's plan-file path). Threaded
            into BOTH ``parse_model_spec`` and ``get_provider_timeout`` so a bare
            (prefix-less) spec resolves its ``default_provider`` — and its
            timeout — against the plan-derived project config rather than CWD's.
            This is the spawn site: unanchored, a run started from a foreign CWD
            launches a different binary than the project configured (§9.3.c).
        schema_phase: §4.2's phase name (``review-plan``, ``code-review``, …),
            or ``None``. **``None`` is the default and changes nothing**: no
            schema is resolved, no flag is emitted and the returned dict is
            byte-for-byte what it has always been.

            When set, this is §4.2.2's "the caller reads the flag before
            dispatch" leg: the phase's schema file is resolved through
            ``utils.structured_output``, the adapter's
            ``structured_output_support`` decides whether it is passed at all,
            codex's sidecar is written and removed in a ``finally``, and
            §4.2.1's failure policy is applied to the envelope afterwards. The
            verdict lands on ``details['structured_output']`` as ``native`` /
            ``recovered`` / ``unvalidated``; a refusal replaces the result with
            a failure carrying ``details['failure_reason']``.

            **Disposition (W1): DEFER — repository owner, 2026-08-20.** No
            production caller passes ``schema_phase`` today; the only callers
            are in ``tests/test_structured_output.py``, and that is the standing
            check. Lane A's fan-out phases are deliberately *not* wired, because
            Lane A's six shipped documents are array-rooted and claude-code
            cannot natively carry an array-rooted schema at all — wiring the
            callers first buys one WARN per dispatch and no native transport.
            Object-rooting those six files is a contract change for every
            consumer of them and is explicitly not a change a call site may
            take, so it is the repository owner's to make and it has not been
            made.

            **Re-check trigger:** claude-code accepts an array-rooted
            ``--json-schema``. **Re-read date:** 2027-02-20. Until one of those
            fires, wiring a production caller here is a regression, not
            progress. See ``plans/harness-residual-work.md`` §3, W1.
        _defer_parse_failure_log: Internal (§Fix1/F13). When ``log_file`` is
            set and the child exited 0, writing the log here — before
            :func:`invoke_with_file_output` has chosen between the file
            channel and the stdout fallback — would either freeze
            ``Success: False`` on a run the file channel goes on to resolve
            (§Fix1's original bug), or, on a clean parse, write a log with no
            ``Result source:`` line at all because this function does not yet
            know which channel will end up answering (F13). Set by that
            caller only: skips the immediate ``_save_log`` write for every
            exit-0 outcome and hands the raw capture back on
            ``details["_deferred_log"]`` instead, so the one log entry gets
            written once the final outcome — file, stdout fallback, or both
            failed — is known, and always carries `Result source:`. A hard
            failure (binary not found, timeout, non-zero exit) still logs
            immediately, unaffected by this flag — there is no channel choice
            to wait for.
        sandbox_fallback: The fan-out's D6 override (2026-09-17): the rung id
            ``review_orchestrator_base.sandbox_refusal`` selected for this slot
            — the runner's own sandbox probe said ``unavailable``, the
            fallback walk found a rung ``providers.<name>.sandbox_fallback``
            permits, and this is a ``generate`` dispatch (``True`` is the
            pre-rung spelling of the uncontained rung). It is forwarded to the
            adapter's ``build_command_for_transport`` (which every adapter but
            codex ignores) and, whenever the child ran (success, non-zero
            exit or timeout kill), recorded as ``details["sandbox"]``
            — ``"bypassed"`` for the uncontained rung only, the rung id for a
            contained one — so the provenance rides the same dict
            ``served_model`` does. The default renders every argv
            byte-for-byte as before and adds no key.

            **The plugin's own jail** (``plugin-landlock``, plan
            codex-sandbox-unavailable-findings-and-fixes §6 F1, 2026-09-30):
            this function is the fan-out's spawn site, so it builds the
            read-only ``JailRequest`` from ``cwd``, owns the attempt's scratch
            ``TMPDIR`` (``slot_tmpdir`` on ``setup_cleanup``, released by the
            subprocess ``finally`` after the child's groups were swept),
            renders with the ``JailContext``, completes it from the composed
            env and wraps the resolved argv (``landlock_dispatch.wrap_argv``).
            It then reads back, on every outcome that ran a child:
            ``details["home_check"]`` (only when ``$CODEX_HOME``'s
            security-relevant set changed or a foreign trust table appeared:
            ``changed``, ``config_keys``, ``foreign_trust``, ``home``,
            ``other_live_children``), ``details["jail_denials"]`` (the denials
            inside the model's own commands: ``JailDenials.to_dict()`` plus
            ``total`` and the first three ``paths``) and, on a failed attempt
            the jail caused, ``details["jail_failure"]`` (``JailEvidence``'s
            keys plus ``rung``, ``installed_version``, ``measured_through``,
            ``allow_list`` and the ``[JAIL_DENIED]`` line under ``notice``)
            with ``failure_reason: "jail-denied"`` and ``retryable: False``.
            A home it cannot grant is the same jail failure with nothing
            spawned; a scratch directory it cannot make is
            ``failure_reason: "jail-setup-failed"``, also non-retryable.
        want_answer_text: The ask lane's request for the model's **whole**
            answer text (plans/ask-answer-recovery-and-false-success.md D2.2).
            When True, every exit that ran the child — success, exit-0 parse
            failure, non-zero exit, timeout — sets ``details["answer_text"]``
            from the full stdout (:func:`_attach_answer_text`: the adapter's
            ``salvage_text`` hook, else :func:`generic_answer_text`; redacted,
            head-capped at 1 MiB). The returns before the spawn and the launch
            failure carry no key, which a reader treats like ``""``. The
            default adds no key and leaves ``salvage_text`` as it was, so the
            review lanes are unchanged.

    Returns:
        Dict with 'success' key and either:
        - On success: 'data' key with parsed response, plus 'details' dict
        - On failure: 'error' message, 'error_code', and 'details' dict

    Error codes:
        BINARY_NOT_FOUND: Provider CLI tool not found in PATH
        TIMEOUT: Command timed out
        SUBPROCESS_FAILED: Command exited with non-zero code (or failed to launch)
        PARSE_ERROR: Failed to parse output
        PROMPT_TOO_LONG: The fully rendered command line (executable path,
            flags, and prompt) exceeds the Windows command-line length budget
        PROMPT_UNSAFE: Prompt carries cmd.exe metacharacters and the provider
            only resolves to a Windows .cmd/.bat shim
    """
    provider_name, model = parse_model_spec(model_spec, anchor=anchor)
    provider = get_provider(provider_name)

    if provider is None:
        return {
            "success": False,
            "error": f"Unknown provider: {provider_name}",
            "error_code": ERROR_BINARY_NOT_FOUND,
            "details": {
                "provider": provider_name,
                "model": model,
            }
        }

    # M10 (§5.1) — a **bool** consumer, and it stays one. The gate is still
    # `is_available()` verbatim, so this refusal is byte-for-byte the decision it
    # always was; the typed report is read only *inside* the branch, to put the
    # state and its sentence on the error details a caller renders.
    if not provider.is_available():
        availability = provider.describe_availability()
        return {
            "success": False,
            "error": f"{provider_name} CLI not found in PATH",
            "error_code": ERROR_BINARY_NOT_FOUND,
            "details": {
                "provider": provider_name,
                "model": model,
                "availability_state": availability.state.value,
                "availability_detail": availability.detail,
            }
        }

    # Use provided timeout or provider's default
    effective_timeout = timeout or get_provider_timeout(provider_name, anchor=anchor)

    # Build command using provider, resolving cmd[0] to an absolute path
    # (and past any Windows .cmd/.bat npm shim, to a sibling .exe or the
    # shim's `node <cli.js>` target — see _resolve_executable).
    transport = prompt_transport or provider.prompt_transport
    if transport != "argv" and not provider.supports_prompt_transport(transport):
        return {
            "success": False,
            "error": (
                f"{provider_name} does not support the {transport!r} prompt "
                f"transport (supported: "
                f"{', '.join(provider.supported_prompt_transports)})"
            ),
            "error_code": ERROR_SUBPROCESS_FAILED,
            "details": {"provider": provider_name, "model": model},
        }
    # §4.2.2's pre-dispatch read, and M7's one call site. `schema_phase=None`
    # skips all of it, so every existing caller renders the same argv it always
    # did. `schema_for_dispatch` is what consults `structured_output_support`:
    # an adapter that declares `False` — or a schema this CLI provably cannot
    # carry — comes back `None` here and the phase runs its prompt-level JSON
    # path, marked `recovered`/`unvalidated` and never `native`.
    schema = None
    structured_marker = structured_output.MARKER_UNVALIDATED
    # M4/§2.3 — the adapter's run-scoped dispatch context is entered BEFORE argv
    # is built, because argv and env are rendered from the same context state
    # (opencode's `--pure` pairs with its `XDG_CONFIG_HOME` redirect and neither
    # is emitted without the other). It rides the same `ExitStack` as the schema
    # sidecar, so it is left on success, on timeout, on kill-path teardown and on
    # exception alike — the `finally` half of §2.3's lifecycle, with the
    # adapter's own `atexit` sweep as the backstop.
    # Every post-entry setup step — the schema read, the argv build, the
    # executable resolution and the env composition — runs INSIDE this `with`,
    # so a raise anywhere in it unwinds the context here rather than leaving
    # opencode's active context and its config-home reference behind for the
    # `atexit` sweep to find. Only once setup has survived is the live stack
    # handed to `schema_cleanup` (`pop_all`), whose owner from that point on is
    # the subprocess `finally` at the end of this function.
    with contextlib.ExitStack() as setup_cleanup:
        dispatch = setup_cleanup.enter_context(
            provider_dispatch_context(provider, model, PROFILE_GENERATE, anchor=anchor)
        )
        if dispatch.refusal:
            return {
                "success": False,
                "error": dispatch.refusal,
                "error_code": ERROR_SUBPROCESS_FAILED,
                "details": {
                    "provider": provider_name,
                    "model": model,
                    "retryable": False,
                },
            }
        if schema_phase:
            try:
                schema, structured_marker = structured_output.schema_for_dispatch(
                    provider, schema_phase
                )
                if schema is not None and provider.structured_output_transport == "file":
                    # One `mkdtemp` per invocation, written by the CALLER: adapters
                    # are singletons under a concurrent fan-out and cannot hold this.
                    # The stack's `close()` in the `finally` below removes it on
                    # success, on timeout, on kill-path teardown and on exception.
                    schema = setup_cleanup.enter_context(
                        structured_output.schema_sidecar(schema)
                    )
            except structured_output.SchemaConfigError as exc:
                return {
                    "success": False,
                    "error": f"structured output: {exc}",
                    "error_code": ERROR_SUBPROCESS_FAILED,
                    "details": {
                        "provider": provider_name,
                        "model": model,
                        "failure_reason": structured_output.FAILURE_CONFIG_ERROR,
                        "retryable": False,
                    },
                }

        # Plan codex-sandbox-unavailable §6 F1 (2026-09-30): a slot on a
        # wrapping rung (the plugin's own Landlock jail) gets its grant here,
        # at the spawn site, once per attempt — order steps 1-2 of "How a
        # dispatch receives its grant". The read-only request comes from this
        # function's own `cwd` (a fan-out slot never carries a write scope),
        # and the attempt's scratch directory rides `setup_cleanup`, so a
        # return before the spawn removes it here and a spawned child's is
        # removed by the subprocess `finally`, after `_run_provider_cli` swept
        # the child's process groups. A slot on the rung with no declared
        # wrapping rung is refused rather than rendered with the bare atoms.
        jail: Optional[_JailedAttempt] = None
        rung_id = sandbox_rung_id(sandbox_fallback)
        if rung_id in _INCIDENTAL_RUNG_IDS:
            jail_rung = _jail_rung(provider, rung_id)
            if jail_rung is None:
                return _jail_refused_result(
                    provider_name, model, None,
                    f"{provider_name} declares no wrapping rung {rung_id!r} for "
                    f"this phase; the plugin's Landlock jail cannot be applied",
                    path=None, reason="no-rung", failure_reason="jail-setup-failed",
                )
            repo_root = os.path.realpath(cwd or os.getcwd())
            request = JailRequest(repo_root=repo_root, kind=PROFILE_GENERATE)
            try:
                tmpdir = setup_cleanup.enter_context(_landlock.slot_tmpdir(repo_root))
            except _landlock.JailRefused as exc:
                return _jail_refused_result(
                    provider_name, model, jail_rung, exc.message,
                    path=exc.path, reason=exc.reason,
                    failure_reason="jail-setup-failed",
                )
            except OSError as exc:
                return _jail_refused_result(
                    provider_name, model, jail_rung,
                    f"could not make the jailed attempt's scratch directory: {exc}",
                    path=None, reason="tmpdir", failure_reason="jail-setup-failed",
                )
            jail = _JailedAttempt(
                rung=jail_rung, request=request, tmpdir=tmpdir, cwd=repo_root,
            )

        # `timeout_s=effective_timeout` is L5's one call site (§9.6.b): the number is
        # already resolved here, so an adapter with an internal cutoff of its own
        # (agy's `--print-timeout`) can hold it under the deadline this same call
        # passes to `_run_provider_cli` below, instead of hardcoding a value that has to
        # be kept in sync by hand. Twelve of the thirteen adapters ignore it, and
        # dropping the keyword restores every rendered argv byte-for-byte.
        try:
            # `cwd=cwd` on the same terms `resolve_env` already takes it, three
            # lines below: these two hooks are the only ones that see the
            # directory the child is really spawned in, and an adapter whose
            # **argv** carries a workspace-scoped token needs it for the same
            # reason an adapter's env delta does. omp is the one that does — it
            # silently relocates to /tmp when its cwd is the user's home, with
            # nothing on either channel to say so. `None` means "inherit this
            # process's", which is what the adapter falls back to; the base
            # composition ignores the keyword entirely, so seventeen adapters
            # render argv byte-for-byte.
            # `jail_context` only when set: the eight adapters that override
            # this builder without the keyword are called exactly as before.
            cmd, stdin_text = provider.build_command_for_transport(
                prompt, model, transport, timeout_s=effective_timeout, schema=schema,
                sandbox_fallback=sandbox_fallback, cwd=cwd,
                **(
                    {"jail_context": JailContext(jail.request, jail.tmpdir)}
                    if jail is not None else {}
                ),
            )
        except (StructuredOutputUnavailable, ReadOnlyInvocationRefused) as exc:
            # §4.2.1's sixth case: fails BEFORE spawn, so no partial argv reaches
            # the CLI. A configuration error, never retried. The same for an
            # adapter refusing an invocation the user's own config makes unsafe
            # (plans/ask-answer-recovery-and-false-success.md D4.2: aider with
            # yes-always on in an `.aider.conf.yml` or `.env`): re-running
            # reads the same file, and the error names it.
            return {
                "success": False,
                "error": str(exc),
                "error_code": ERROR_SUBPROCESS_FAILED,
                "details": {
                    "provider": provider_name,
                    "model": model,
                    "failure_reason": structured_output.FAILURE_CONFIG_ERROR,
                    "retryable": False,
                },
            }
        launcher, is_batch_shim = _resolve_executable(cmd[0])
        cmd = [*launcher, *cmd[1:]]

        if _IS_WINDOWS and transport == "argv":
            # Interim safeguard until the explicit `cmd /c` escaping path lands
            # (launch-strategy step (c)): a batch shim means cmd.exe reparses
            # the command line, so refuse metacharacter-bearing prompts rather
            # than risk silent corruption or injection. Never enforced on POSIX.
            if is_batch_shim:
                metachar_error = _batch_shim_metachar_error(
                    prompt, provider_name, model, cmd[0]
                )
                if metachar_error is not None:
                    return metachar_error

            # Prompt-on-argv transport hits hard command-line length caps on
            # Windows; fail fast with an actionable error instead of a cryptic
            # CreateProcess/cmd.exe failure. Measured over the full rendered
            # command line (executable path, flags, quoting expansion), not just
            # the prompt. Never enforced on POSIX.
            length_error = _prompt_length_error(cmd, prompt, provider_name, model, is_batch_shim)
            if length_error is not None:
                return length_error

        start_time = time.time()

        # Build subprocess environment: add provider vars, remove blacklisted ones.
        # `resolve_env`, not `get_env`: the Lane A fan-out IS the `generate` profile
        # (§2.2), so it gets the global non-interactive git block plus the scoped
        # `credential.helper=""` wipe. Naming the profile rather than leaning on the
        # default keeps the scoping greppable — `agent-write` must never appear here.
        # `cwd` rides along because an adapter's delta may carry a
        # workspace-scoped side effect (cursor's trust-marker guard): the spawn
        # site is where the child's real directory is known, and `None` here
        # means the child inherits this process's.
        provider_env = expand_env_home(
            provider.resolve_env(model, PROFILE_GENERATE, anchor=anchor, cwd=cwd)
        )
        # M3/M17 (A6): the *composition* is `build_child_env`, the one builder Lane B
        # goes through too, so a slot can never strip on one lane and inherit on the
        # other — and M17's deny-by-default allowlist has exactly one place to live.
        # Lane A passes no host guards: a fan-out slot is a child of this process,
        # not of the host's shell tool, so only the adapter's own list applies.
        env = build_child_env(provider, provider_env=provider_env, anchor=anchor)
        if jail is not None:
            # F1 order steps 5-6: complete the context with `$CODEX_HOME` as
            # the child will see it (read from the env just composed — `None`
            # there means "inherits this process's"), then the one wrap. A
            # missing or in-repo home is a jail failure naming the path, with
            # nothing spawned and no retry on another rung.
            child_view = env if env is not None else dict(os.environ)
            try:
                jail.context = _landlock.complete_context(
                    jail.request, jail.tmpdir, child_view
                )
                cmd, env = _landlock.wrap_argv(cmd, jail.rung, jail.context, child_view)
            except _landlock.JailRefused as exc:
                return _jail_refused_result(
                    provider_name, model, jail.rung, exc.message,
                    path=exc.path, reason=exc.reason,
                    failure_reason=FAILURE_JAIL_DENIED,
                )
            try:
                jail.home_before = _landlock.home_snapshot(
                    jail.context.codex_home, [jail.cwd]
                )
            except Exception:  # noqa: BLE001 - a check never ends a slot
                jail.home_before = None
        # Setup survived: transfer the entered contexts out of the setup
        # stack so leaving this `with` releases nothing, and the subprocess
        # `finally` below owns them for the rest of the dispatch.
        schema_cleanup = setup_cleanup.pop_all()

    try:
        # `subprocess.run`'s contract and arguments, but a `Popen` underneath:
        # on the deadline, a Ctrl-C or an abort the CLI is SIGTERMed first and
        # every process group it spawned is swept, instead of `run`'s bare
        # SIGKILL of the CLI alone (D3.3; see `_run_provider_cli`). On Windows
        # the CLI runs in a Job Object of its own, and the stop ends that job.
        # Registered for exactly as long as the child runs, so a jailed slot's
        # `[CODEX_HOME_CHECK]` line can say how many other children of this
        # provider shared its window (F1 Limits, 2026-09-30).
        with _live_child(provider_name) as live_overlap:
            if jail is not None:
                jail.live = live_overlap
            result = _run_provider_cli(
                cmd,
                capture_output=True,
                text=True,
                # Provider output is not under our control: errors="replace" is
                # lossy for non-UTF-8 bytes but guarantees a total decode — the
                # standard choice for LLM/tool output. surrogateescape rejected
                # (lone surrogates raise on downstream UTF-8 re-encode);
                # backslashreplace rejected (noisier in model-visible output).
                encoding="utf-8",
                errors="replace",
                timeout=effective_timeout,
                env=env,
                cwd=cwd,
                # Under the argv transport the one provider that reads stdin is
                # aider, which reads its decline supply there (D4.2: `s` answers to
                # the "Add file to the chat?" prompts, handed back as `stdin_text`
                # and closed at EOF once written). For every other one, closing it
                # prevents CLIs that poll stdin for piped input (e.g. agy) from
                # blocking forever when the orchestrator's stdin is a non-EOF pipe.
                # Under the stdin transport the prompt IS the child's stdin, and it
                # is closed at EOF once written, which those CLIs treat the same way.
                **(
                    {"input": stdin_text}
                    if stdin_text is not None
                    else {"stdin": subprocess.DEVNULL}
                ),
            )
        duration = time.time() - start_time

        if result.returncode != 0:
            error_message = f"{provider_name} exited with code {result.returncode}"
            # Some CLIs report the actual cause on stdout and leave stderr
            # empty (opencode does this for auth/quota errors), which would
            # otherwise leave the caller with a bare exit code. A provider
            # override must never mask the real failure, so it is best-effort.
            try:
                reason = provider.describe_failure(result.stdout, result.stderr)
            except Exception:  # noqa: BLE001 - diagnostics must not raise
                reason = None
            if reason:
                # §4.5: the reason is the vendor's own sentence quoted off a
                # stream, and it lands in `.status.json`'s `models_failed` and
                # on the fan-out's stdout — neither of which goes through
                # `_save_log`'s redaction. The one boundary applies here too.
                error_message = f"{error_message}: {_redact(reason)}"
            # M10 (§5.1) — the **status**-consumer half of this site. A failure
            # whose own streams carry a login notice is an availability verdict,
            # not a parse, so name it instead of leaving the caller with a
            # generic tail. Only the named negatives speak (see
            # `availability_from_failure`), and nothing is probed here.
            unavailable = availability_from_failure(
                provider, result.stdout, result.stderr, result.returncode
            )
            if unavailable is not None:
                error_message = f"{error_message} [{unavailable.value}]"

            # F1 item 6 (2026-09-30): a jailed child that died on a
            # codex-internal EACCES the jail caused is a jail failure, never a
            # model error; an ordinary permission error keeps today's message
            # plus the reason it is not a jail denial. Read while the context
            # is alive, with the home check and the in-stream denial count.
            jail_details: Dict[str, Any] = {}
            jail_error, jail_note = _jail_after_child(
                jail_details, jail, provider_name=provider_name, model=model,
                stdout=result.stdout, stderr=result.stderr,
                returncode=result.returncode, failed=True,
            )
            if jail_error:
                error_message = (
                    f"{provider_name} exited with code {result.returncode}: {jail_error}"
                )
            elif jail_note:
                error_message = f"{error_message}{jail_note}"

            # Plan §4.2: the read-only audit sees the FULL stream, here, before
            # the excerpt below bounds it — a failed attempt of a bypassed slot
            # could still have written, and 4.3 ANDs every attempt's verdict.
            audit = _readonly_audit(provider, result.stdout, sandbox_fallback)

            # Save log on failure if requested
            if log_file:
                _save_log(
                    log_file=log_file,
                    model=f"{provider_name}:{model}",
                    prompt=prompt,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                    success=False,
                    error=error_message,
                    duration_seconds=duration,
                    readonly_audit=audit,
                )

            details = {
                "exit_code": result.returncode,
                "stderr": result.stderr,
                "provider": provider_name,
                "model": model,
                "duration_seconds": duration
            }
            # THE ANSWER MAY ALREADY BE ON STDOUT, and this return used to drop
            # it. A non-zero exit is not only "the provider never spoke": it is
            # also the provider that wrote a truncated or fenced array and *then*
            # died — a kill after the answer, a crash on teardown — and that array
            # is on stdout, never on stderr. The salvage gate at
            # `code_review_orchestrator.py`'s site A runs under exactly this
            # branch (`if not result["success"]`), so with stderr as its only
            # channel it printed "Provider failed before producing any JSON —
            # nothing to salvage" over a run that *had* produced JSON, and a
            # recoverable review was thrown away silently.
            #
            # The JSON-erroring providers make the same point from the other
            # side: `opencode run --format json` puts its failure shape on stdout
            # with stderr empty, and a relayed `{"error": {"code": 401, ...}}`
            # body looks identical from any HTTP-backed CLI. Those reached the
            # gate as the empty string, so even the verdicts it got *right* were
            # reached for the wrong reason.
            #
            # `provider.describe_failure` and `availability_from_failure` above
            # already read `result.stdout` for their own one-line verdicts; this
            # carries the text itself, under §4.5/§4.4, so a consumer can form a
            # different judgement from the same evidence.
            if audit is not None:
                details[_READONLY_AUDIT_KEY] = audit
            # The child ran, so the D6 provenance rides a failure too.
            _attach_sandbox_word(details, sandbox_fallback)
            details.update(jail_details)
            _attach_stdout_excerpt(details, result.stdout)
            # One hook reading for both keys (D2.2): each cuts its own copy.
            hook_text = _salvage_hook_text(provider, result.stdout)
            _attach_salvage_text(details, provider, result.stdout, hook_text=hook_text)
            if want_answer_text:
                _attach_answer_text(details, provider, result.stdout, hook_text=hook_text)
            # A failed run still spent what its envelope records, and this lane
            # never read it: `parse_usage` was Lane B's (`subagent_executor`)
            # and the audit log's, so the fan-out carried usage for NO slot,
            # failed or not. Measured 2026-09-17: a claude-code review slot ran
            # 491 s, spent $25.05 and 137 348 output tokens, died on a usage cap,
            # and nothing the run wrote — error log, `.status.json`, report —
            # named a number. Best-effort like `describe_failure`, and absent
            # rather than `{}` so "not reported" stays distinguishable.
            _attach_usage(details, provider, result.stdout, result.stderr)

            if schema_phase:
                # §4.2.1 cases 2 and 4 both arrive here as a non-zero exit, and
                # they are NOT the same failure: the CLI exhausting its own
                # structured-output budget is a `schema_violation` our ladder
                # must not re-run, while a malformed schema is a configuration
                # error that made **zero requests** and cost nothing. Classifying
                # here is what keeps the second from being retried as if it were
                # transient.
                verdict = structured_output.classify_attempt(
                    schema,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.returncode,
                    phase=schema_phase,
                    model=f"{provider_name}:{model}",
                )
                if (
                    verdict.failure_reason
                    and details.get("failure_reason") != FAILURE_JAIL_DENIED
                ):
                    details["failure_reason"] = verdict.failure_reason
                    details["retryable"] = verdict.retryable
                if verdict.warning:
                    print(f"[WARN] {verdict.warning}", file=sys.stderr)
            return {
                "success": False,
                "error": error_message,
                "error_code": ERROR_SUBPROCESS_FAILED,
                "details": details,
            }

        # Parse output using provider
        parsed = provider.parse_output(result.stdout, result.stderr)

        # Add details to successful results
        parsed["details"] = {
            "provider": provider_name,
            "model": model,
            "duration_seconds": duration
        }
        # The adapter's completion verdict moves onto `details` straight after
        # the parse (plans/ask-answer-recovery-and-false-success.md D3.1):
        # `incomplete` says the stream's own terminal state shows the answer did
        # not finish (pi's `stopReason: "length"`), whether or not the text
        # parsed. On `details` it survives the schema-verdict rebuild below,
        # which keeps only `details`, and the `PARSE_ERROR` stamp. It is not an
        # `error_code`, so `invoke_with_file_output`'s hard-failure gate — and
        # with it the findings-file channel — is unchanged.
        if parsed.pop("incomplete", False):
            parsed["details"]["incomplete"] = True
        # EXTRACT BEFORE DISCARDING. `parse_output` above has just unwrapped the
        # answer out of the provider's envelope and thrown the envelope away —
        # and the envelope is where the token counts and the catalog cost live.
        # Until Stage U this lane asked for them on the losing paths only, so a
        # run that *worked* reported no numbers anywhere: not on the slot result,
        # not in `.status.json`, not in the report. Asked here, right where
        # `details` is born, every exit-0 outcome carries them — a clean parse, a
        # parse failure, a schema violation, and an adapter whose `parse_output`
        # calls an exit-0 stream a hard failure. There is no second call for the
        # schema-verdict branch below: it replaces `parsed` with a new dict whose
        # `details` spreads `**parsed.get("details", {})`, so the key rides
        # across. An adapter that reports nothing still leaves it absent.
        _attach_usage(parsed["details"], provider, result.stdout, result.stderr)
        # Plan §4.2: the read-only verdict on the full stream, on the same dict
        # (the schema branch below spreads `details`, so it rides across), and
        # always before `_attach_stdout_excerpt` bounds anything.
        audit = _attach_readonly_audit(
            parsed["details"], provider, result.stdout, sandbox_fallback
        )
        # D6 override (2026-09-17): a slot that ran without the runner's own
        # sandbox says so on the same dict, so `served_model_fields` carries it
        # to the result record, `.status.json`'s `models_served` and the report
        # label. Only when the override fired — a default run adds no key —
        # and `bypassed` only for the uncontained rung: a contained rung is a
        # sandbox, and records its own id rather than a word it would contradict.
        _attach_sandbox_word(parsed["details"], sandbox_fallback)

        # §3.6: a fallback that fired rides out on the same details dict the
        # provider/model pair travels on, so every downstream record that names
        # the requested model can name the model that actually served the turn.
        # One WARN per slot — the adapter owns the text; there is no second one.
        attribution = _served_model_attribution(provider, model, result.stdout)
        if attribution is not None:
            served, is_fallback, warning = attribution
            parsed["details"]["served_model"] = served
            parsed["details"]["served_model_is_fallback"] = is_fallback
            if warning:
                print(f"[WARN] {warning}", file=sys.stderr)

        # §4.2.1's rule, stated as a rule and not only as a case: **no**
        # combination of exit 0, `subtype: success` and `is_error: false` is by
        # itself a success for a schema-carrying phase. The only success is
        # `structured_output` present (→ `native`) or a recovered document that
        # validates against the SAME schema file (→ `recovered`, one WARN).
        # Anything else is `schema_violation`, handed to the retry ladder like
        # any other parse failure. Applied here, on the parsed envelope, so no
        # adapter can silently upgrade prose to validated output.
        if schema_phase:
            verdict = structured_output.classify_attempt(
                schema,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                phase=schema_phase,
                model=f"{provider_name}:{model}",
                native_document=structured_output.native_document_for(
                    provider, result.stdout
                ),
            )
            if verdict.warning:
                print(f"[WARN] {verdict.warning}", file=sys.stderr)
            if verdict.failure_reason:
                parsed = {
                    "success": False,
                    "error": (
                        f"{provider_name} returned no schema-conformant document "
                        f"for {schema_phase} ({verdict.failure_reason})"
                    ),
                    "error_code": ERROR_PARSE_ERROR,
                    "data": None,
                    "details": {
                        **parsed.get("details", {}),
                        "failure_reason": verdict.failure_reason,
                        "retryable": verdict.retryable,
                        "structured_output": None,
                    },
                }
            else:
                parsed["details"]["structured_output"] = (
                    verdict.marker or structured_marker
                )
                if verdict.data is not None:
                    parsed["success"] = True
                    parsed["data"] = verdict.data

        # If parse_output indicates failure, add error_code
        if not parsed.get("success", False) and "error_code" not in parsed:
            parsed["error_code"] = ERROR_PARSE_ERROR

        # F1 (2026-09-30): the jailed slot's read-back on an exit 0 too — the
        # home check and the in-stream denial count always; a jail failure
        # only when the run produced no answer (a `turn.failed` on a
        # codex-internal EACCES can still exit 0). Such a failure is a hard
        # one (`SUBPROCESS_FAILED`), so `invoke_with_file_output` returns it as
        # it is instead of re-labelling it a parse failure of both channels.
        # "No answer" is `_exit0_left_no_answer`'s reading, not the parse
        # verdict: codex's `parse_output` succeeds only on JSON, so a finished
        # prose answer would otherwise be rewritten as jail-denied by any
        # EACCES-looking line on codex's stderr or in an `error` event.
        hook_text: Any = _HOOK_UNREAD
        if jail is not None:
            parsed_details = parsed.setdefault("details", {})
            jail_failed = not parsed.get("success", False)
            if jail_failed:
                hook_text = _salvage_hook_text(provider, result.stdout)
                jail_failed = _exit0_left_no_answer(hook_text, result.stdout)
            jail_error, jail_note = _jail_after_child(
                parsed_details, jail, provider_name=provider_name, model=model,
                stdout=result.stdout, stderr=result.stderr,
                returncode=result.returncode,
                failed=jail_failed,
            )
            if jail_error:
                parsed["success"] = False
                parsed["error"] = f"{provider_name}: {jail_error}"
                parsed["error_code"] = ERROR_SUBPROCESS_FAILED
            elif jail_note and parsed.get("error"):
                parsed["error"] = f"{parsed['error']}{jail_note}"

        # WHAT THE MODEL ACTUALLY SAID, kept on the failure. A parse failure is
        # the one class where the error message describes our disappointment
        # rather than the event: "JSON parsing failed from both file and stdout"
        # is what a cursor `--mode ask` write refusal looked like from the
        # outside, and reading the sentence that caused it ("I can't write the
        # requested file while Ask mode is active") cost three 450 s runs and a
        # hand-driven CLI invocation, because nothing downstream carried the
        # text. Redacted and bounded by the same §4.5/§4.4 boundary the log
        # writer uses — never the raw stream. This is the *original* of the three
        # `stdout_excerpt` sites; `_attach_stdout_excerpt` now spells the rule for
        # all of them, and the two hard-failure returns above and below join it,
        # so `details.get("stdout_excerpt")` means the same thing whichever way
        # the run was lost. The jail read-back above may already have taken the
        # hook's one reading; it is reused, never taken twice.
        if not parsed.get("success", False):
            _attach_stdout_excerpt(parsed.setdefault("details", {}), result.stdout)
            if hook_text is _HOOK_UNREAD:
                hook_text = _salvage_hook_text(provider, result.stdout)
            _attach_salvage_text(
                parsed["details"], provider, result.stdout, hook_text=hook_text
            )

        # Save log if requested. §Fix1/F13: a deferring caller (invoke_with_file_output)
        # gets the raw capture on `details` instead of an immediate write, on
        # EVERY exit-0 outcome — not only a failed stdout parse — because this
        # function does not yet know which channel (file, stdout fallback, or
        # neither) will end up answering for the run, and that is exactly what
        # `Result source:` in the log is supposed to name. Writing here
        # unconditionally on a clean parse used to freeze a log with no
        # `Result source:` line at all: the caller's file-vs-stdout decision
        # came later and had nothing left to add to. Only the deferring caller
        # actually reads `_deferred_log`, so a plain `invoke_with_provider`
        # call (no defer requested) still gets one immediate write.
        if log_file:
            if _defer_parse_failure_log:
                parsed.setdefault("details", {})["_deferred_log"] = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "duration_seconds": duration,
                }
            else:
                _save_log(
                    log_file=log_file,
                    model=f"{provider_name}:{model}",
                    prompt=prompt,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                    success=parsed.get("success", False),
                    error=parsed.get("error"),
                    duration_seconds=duration,
                    readonly_audit=audit,
                )

        # D2.2: the whole answer on the success return too — the path
        # nemotron's 124-line answer was lost on, since `data` was a dict and
        # the full stdout existed only here. A failed parse reuses the hook
        # reading `salvage_text` took above; a success reads it now, once.
        if want_answer_text:
            _attach_answer_text(
                parsed.setdefault("details", {}), provider, result.stdout,
                hook_text=hook_text,
            )

        return parsed

    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        # TimeoutExpired may carry partial output as str or bytes; decode
        # bytes with the same utf-8/replace policy as the run() call above.
        if e.stdout is None:
            stdout = ""
        elif isinstance(e.stdout, str):
            stdout = e.stdout
        else:
            stdout = e.stdout.decode("utf-8", errors="replace")
        if e.stderr is None:
            stderr = ""
        elif isinstance(e.stderr, str):
            stderr = e.stderr
        else:
            stderr = e.stderr.decode("utf-8", errors="replace")

        # Plan §4.2: a killed attempt is audited too — on whatever it streamed
        # before the kill, which has no `turn.completed`, so it can only come
        # out not clean (an incomplete stream is "could have written").
        audit = _readonly_audit(provider, stdout, sandbox_fallback)

        # F1 (2026-09-30): a jailed child killed at the deadline is read back
        # like any other — the home check and the in-stream denials — but it
        # stays a timeout, as on the executor lane: an EACCES on codex's own
        # channels before the kill never makes it a never-retried jail denial.
        jail_details: Dict[str, Any] = {}
        jail_error, jail_note = _jail_after_child(
            jail_details, jail, provider_name=provider_name, model=model,
            stdout=stdout, stderr=stderr, returncode=None, failed=True,
            timed_out=True,
        )
        timeout_error = f"{provider_name} timed out after {effective_timeout}s"
        if jail_error:
            timeout_error = f"{timeout_error}: {jail_error}"
        elif jail_note:
            timeout_error = f"{timeout_error}{jail_note}"

        # Save log on timeout if requested
        if log_file:
            _save_log(
                log_file=log_file,
                model=f"{provider_name}:{model}",
                prompt=prompt,
                stdout=stdout,
                stderr=stderr,
                returncode=-1,
                success=False,
                # Plus what the sweep did to the CLI and to each process group
                # it had spawned, so a `survived` group is named where the
                # timeout is (D3.3).
                error=f"{timeout_error}{_describe_tree_sweep(e)}",
                duration_seconds=duration,
                readonly_audit=audit,
            )

        details = {
            "provider": provider_name,
            "model": model,
            "timeout": effective_timeout,
            "duration_seconds": duration
        }
        # A TIMEOUT KILL DOES RECOVER PARTIAL STDOUT, so this return no longer
        # throws it away — checked rather than assumed, because attaching a key
        # that is empty by construction would be worse than attaching nothing.
        # `_run_provider_cli` re-raises a `TimeoutExpired` carrying what the CLI
        # wrote: the bytes read before the deadline plus whatever a bounded
        # second `communicate()` collected after the sweep stopped it. That is
        # the `e.stdout` the decode a few lines above has just
        # turned into the `stdout` local — the same local `_save_log` is handed,
        # so the log file has always kept this text and only the returned envelope
        # did not. The envelope is the half a caller can act on.
        #
        # This is the archetype §2 of the plan names for salvage site A: a
        # provider that streamed a review array and was killed mid-emission
        # leaves a *truncated* array on stdout and nothing at all on stderr. It is
        # the most salvageable failure this skill has, and the stderr-only gate
        # was structurally unable to see it. Bounding matters more here than at
        # either sibling site, because the run killed at the deadline is the run
        # most likely to have emitted megabytes — the 6,254,326 B log `_save_log`
        # was written to survive came off a path like this one.
        #
        # When the kill caught the child before its first write, `stdout` is the
        # empty string rather than absent; the helper omits the key rather than
        # attaching `""`, so this path and the non-zero-exit path answer
        # `details.get("stdout_excerpt")` the same way.
        if audit is not None:
            details[_READONLY_AUDIT_KEY] = audit
        # A killed child ran too, and ran under whatever rung it was given.
        _attach_sandbox_word(details, sandbox_fallback)
        details.update(jail_details)
        _attach_stdout_excerpt(details, stdout)
        # One hook reading for both keys (D2.2): each cuts its own copy.
        hook_text = _salvage_hook_text(provider, stdout)
        _attach_salvage_text(details, provider, stdout, hook_text=hook_text)
        if want_answer_text:
            _attach_answer_text(details, provider, stdout, hook_text=hook_text)
        # AND THE SAME PARTIAL STDOUT IS WHAT USAGE IS PARSED OUT OF. This is
        # the third of the three outcomes `_attach_usage` is documented to
        # cover, and it was the one that never called it — so the run killed at
        # the deadline, the expensive failure class Stage U exists to report,
        # reported no numbers at all while the excerpt beside it carried the
        # very bytes an adapter reads them from. A provider that streamed a
        # terminal usage event before the kill, or that reports cumulatively per
        # step, has already said what it spent; best-effort like every other
        # call, and absent rather than `{}` when the adapter can say nothing.
        _attach_usage(details, provider, stdout, stderr)

        return {
            "success": False,
            "error": timeout_error,
            "error_code": ERROR_TIMEOUT,
            "details": details,
        }

    except OSError as e:
        # Process creation failed (executable removed after detection, an
        # invalid resolved shim, or any other CreateProcess/exec failure):
        # return a structured error through the same result-dict path as
        # other provider errors instead of aborting the orchestrator.
        duration = time.time() - start_time
        if isinstance(e, FileNotFoundError):
            error_code = ERROR_BINARY_NOT_FOUND
            error_msg = f"{provider_name} CLI not found when launching: {e}"
        else:
            error_code = ERROR_SUBPROCESS_FAILED
            error_msg = f"Failed to launch {provider_name} CLI: {e}"

        # Save log on launch failure if requested
        if log_file:
            _save_log(
                log_file=log_file,
                model=f"{provider_name}:{model}",
                prompt=prompt,
                stdout="",
                stderr=str(e),
                returncode=-1,
                success=False,
                error=error_msg,
                duration_seconds=duration
            )

        return {
            "success": False,
            "error": error_msg,
            "error_code": error_code,
            "details": {
                "provider": provider_name,
                "model": model,
                "duration_seconds": duration
            }
        }

    finally:
        # §4.2.1: codex's per-invocation schema directory is removed in a
        # `finally` so it is cleaned up on success, on timeout, on kill-path
        # teardown and on exception alike. A no-op when `schema_phase` is unset
        # or the adapter's transport is inline.
        schema_cleanup.close()


def _is_valid_parsed_data(data: Any) -> bool:
    """Check if parsed data is valid JSON (not just a raw wrapper).

    Args:
        data: Parsed data from provider output

    Returns:
        True if data is a valid list or dict (not just a raw error wrapper)
    """
    if data is None or data == "" or data == {"raw": ""}:
        return False
    if not isinstance(data, (list, dict)):
        return False
    # Check if it's just a raw wrapper (single key "raw")
    if isinstance(data, dict) and set(data.keys()) == {"raw"}:
        return False
    return True


# ---------------------------------------------------------------------------
# The ``{output_location}`` block the three review prompts end with
# ---------------------------------------------------------------------------

#: What a file-capable adapter is asked for. Byte-identical to the text
#: ``prompts/{code,plan,task}_review.txt`` carried inline before the placeholder
#: existed, so the rendered prompt of every adapter that declares
#: ``supports_file_output`` is unchanged to the character — the golden container
#: turns under ``tests/golden/container_turns/`` are captured from those bytes.
FILE_OUTPUT_LOCATION = (
    "CRITICAL: Write your JSON output to this file: {path}\n"
    "Do NOT print JSON to stdout. Write ONLY the JSON array to the specified "
    "file path.\n"
    'After writing, confirm by printing: "JSON written to {path}"\n'
    "\n"
    "The file must contain ONLY valid JSON - no markdown, no code blocks, no "
    "explanation. Just the raw JSON array."
)

#: What an adapter that declares ``supports_file_output = False`` is asked for
#: instead. Two adapters run their CLI in a read-only chat mode on purpose
#: (cursor ``--mode ask``, aider ``/ask``), and the file instruction is one they
#: can only answer with a refusal sentence. Stdout is the channel they *do*
#: have, it is the one ``invoke_with_file_output`` already falls back to, and
#: the parsed array lands in exactly the same per-model result file either way —
#: ``save_model_result`` writes it from the returned data, not from the model's
#: own file.
#:
#: "Refused by the sandbox where one runs", not "will be refused": until D6's
#: fallback (2026-09-17) every adapter on this roster really did refuse the
#: write — a chat mode, a zero tool budget, a missing tool, or codex's own
#: bubblewrap. A codex slot dispatched under the fallback (``sandbox_fallback:
#: auto``, the default) runs with no sandbox at all, so a write there would
#: *succeed*, and a prompt
#: that promised otherwise would be lying to the model about the one thing it
#: is being asked not to do. The instruction is the same either way (return the
#: array on stdout); only the claim about what happens on disobedience moved.
STDOUT_OUTPUT_LOCATION = (
    "CRITICAL: Return your JSON output on stdout as your final message. Do NOT "
    "write it to a file — this is a read-only task, and a file write is "
    "refused by the sandbox where one runs.\n"
    "Your final message must be ONLY the raw JSON array - no markdown, no code "
    "blocks, no explanation, no preamble and no closing remarks."
)


def render_output_location(
    output_json_path: Union[str, Path],
    model_spec: str,
    anchor: Optional[Union[str, Path]] = None,
) -> str:
    """The ``{output_location}`` block for ``model_spec``'s rendered prompt.

    One decision, taken from the adapter's declared
    :attr:`~utils.providers.base.LLMProvider.supports_file_output` rather than
    from a provider name spelled out in an orchestrator: the caller that renders
    a prompt does not need to know *which* CLIs refuse to write, only that this
    one does. An unknown provider (a config naming an adapter this build no
    longer ships) renders the file block, which is what every caller did before
    this function existed.

    ``anchor`` is the run's plan path (§9.3.c): a bare, prefix-less spec resolves
    its ``default_provider`` against the plan-derived project config, so the
    block matches the binary that will actually be spawned.
    """
    provider_name, _ = parse_model_spec(model_spec, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is not None and not provider.supports_file_output:
        return STDOUT_OUTPUT_LOCATION
    return FILE_OUTPUT_LOCATION.format(path=output_json_path)


# ---------------------------------------------------------------------------
# The ``{diff_access}`` block of the code-review prompt
# ---------------------------------------------------------------------------
#
# Measured on the 2026-09-25 review run (plan: review-run-scope-salvage-and-
# failure-visibility §2.1): the code-review prompt only told reviewers to run
# `git diff`, and the two cursor-agent lanes run `--mode ask`, which has no
# shell — kimi returned `[]` having never seen a diff, and grok reported a test
# failure it could not have run. The orchestrator now writes the scope manifest
# and one diff per file into the phase dir before dispatch, and this block tells
# each lane how to reach them, rendered from the adapter's two `generate`
# declarations (`generate_read_scope`, `runs_shell_in_generate`) so the
# orchestrator never names a provider. It is the ONLY block of the prompt that
# may grant a shell command, and only its `True` text does.

#: The one size cap decision 11.4 keeps. It bounds only the INLINE branch — a
#: lane that cannot open the phase dir gets the plan, the manifest and every
#: diff in the prompt itself — and it is physical, not a guess at a context
#: window: an argv lane's whole prompt is one argument, Linux caps one argument
#: at ``MAX_ARG_STRLEN`` (131072 bytes), and 96 KB leaves room for the template.
INLINE_DIFF_CAP_BYTES = 96 * 1024

#: The same physical limit applied to the WHOLE rendered prompt of an inline
#: slot, not only its ``{diff_access}`` block: the template around that block
#: also carries the implementation record (up to 20 000 chars, UTF-8 widens it),
#: the file list and the working limits, so a block under
#: :data:`INLINE_DIFF_CAP_BYTES` can still sit in a prompt past
#: ``MAX_ARG_STRLEN`` and die as an ``E2BIG`` spawn failure. 4 KB under the
#: kernel's number, for its NUL and an adapter's own wrapping of the prompt
#: argument (aider's ``/ask `` prefix) — the ceiling ``ask_orchestrator``'s
#: ``MAX_PROMPT_BYTES`` uses for the same reason. Measured with
#: :func:`argv_prompt_bytes`.
INLINE_PROMPT_CAP_BYTES = 124 * 1024

#: The values ``LLMProvider.generate_read_scope`` may take.
GENERATE_READ_SCOPES = ("none", "cwd", "any")

#: What the inline branch calls the manifest block. A lane on that branch
#: cannot open the file, so this is the name a truncated file-list notice can
#: point it at ("the ``review-scope.md`` block below") instead of a path.
INLINE_MANIFEST_LABEL = "review-scope.md"

#: What the inline branch calls a commit review's frozen context plan
#: (``commit_range.plan_snapshot``, plans/review-commits.md §2.4): the
#: snapshot's own file name (``commit_brief.CONTEXT_PLAN_SNAPSHOT``), so the
#: commit template's ``{plan_block}`` can point an inline lane at the block.
INLINE_CONTEXT_PLAN_LABEL = "context-plan.md"

#: Shared by the three path texts. Deliberately names no command: only the
#: ``True`` text may.
_MANIFEST_SENTENCE = (
    "The scope manifest at {scope_file} lists every in-scope file with its "
    "status, and names each file's diff file (relative to the manifest) and "
    "its size."
)

#: ``runs_shell_in_generate is True`` — a shell runs, measured. Carries the
#: guidance ``prompts/code_review.txt`` used to hold in its static text, now an
#: optional cross-check rather than the only way to see the change.
DIFF_ACCESS_SHELL_TEXT = (
    "The diff files in {diff_dir} are the authoritative record of the change. "
    + _MANIFEST_SENTENCE
    + " Read the manifest first, then each entry's diff file, with your file "
    "tools.\n"
    "\n"
    "You can also run shell commands. `git diff {base_ref}`, `git show` and "
    "`git log` are an optional cross-check of the diff files, never a "
    "replacement for reading them:\n"
    "1. **All changes at once:** `git diff {base_ref} -- <file1> <file2> ...`\n"
    "2. **One file's changes:** `git diff {base_ref} -- path/to/file`\n"
    "3. **A file's current content:** `cat path/to/file`, or your file-read "
    "tool\n"
    "\n"
    "`git diff {base_ref} -- <path>` is required for any file the manifest "
    "marks `omitted`: it has no diff file, so that command's output is the only "
    "record of its change you can review."
)

#: ``runs_shell_in_generate is False`` — no shell, measured. The first
#: paragraph is plan D2.3's text, word for word.
DIFF_ACCESS_NO_SHELL_TEXT = (
    "You cannot run shell commands. The diff is at {diff_dir}; read it with "
    "your file tools. Do not claim a test passes or fails, because you cannot "
    "run it.\n"
    "\n"
    + _MANIFEST_SENTENCE
    + " The diff files are the authoritative record of the change: read the "
    "manifest first, then each entry's diff file."
)

#: ``runs_shell_in_generate is None`` — not measured. It neither grants nor
#: denies a shell; the first paragraph is plan D2.3's text, word for word.
DIFF_ACCESS_UNMEASURED_TEXT = (
    "The diff files at {diff_dir} are the authoritative record of the change; "
    "read them with your file tools. Do not claim a test passes or fails unless "
    "you actually ran it and saw the result.\n"
    "\n"
    + _MANIFEST_SENTENCE
    + " Read the manifest first, then each entry's diff file."
)

#: What each state adds when ``write_review_diff``'s coverage is ``partial``
#: (git produced no diff for some in-scope path). ``False`` and ``None`` are
#: plan D2.3's text, word for word. ``None``'s names ``git diff`` only as the
#: command the MANIFEST gives, conditionally — it grants nothing.
DIFF_ACCESS_SHELL_PARTIAL = (
    "Diff coverage for this change is partial: git produced no diff file for "
    "the files the manifest marks `omitted`. Run `git diff {base_ref} -- "
    "<path>` for each of them and review it from that output; if the command "
    "fails, list the file as not reviewed. Do not review their current "
    "contents as if they were the change."
)
DIFF_ACCESS_NO_SHELL_PARTIAL = (
    "Files the manifest marks `omitted` have no diff you can read. List them as "
    "not reviewed. Do not review their current contents as if they were the "
    "change."
)
DIFF_ACCESS_UNMEASURED_PARTIAL = (
    "Files the manifest marks `omitted` have no diff file. If you can run the "
    "`git diff` command the manifest gives for one, review it from that output; "
    "otherwise list it as not reviewed. Do not review their current contents as "
    "if they were the change."
)

# A review pinned to a commit (``--head-ref``: a direct two-commit run, or a
# commit brief; plans/review-commits.md §2.5). The change is `git diff <base>
# <head>`, so the working tree is never the reviewed content, for any file, and
# nothing below says it is: the shell text's third command reads a file at the
# head commit (`git show`), never with `cat`. The block opens by naming the
# change as `<base7>..<head7>`, says it ends at the head commit and not at the
# working tree, names the files that changed on disk since that commit, and
# closes with the pinned-head read rule (with the §2.6 trust sentence), so
# `code_review.txt`'s fixed "everything since it" is corrected on a direct run.
# `{sides}` is `<base> <head>` as git takes them, `{head}` the head commit's
# 12-character prefix.

#: ``runs_shell_in_generate is True`` on a pinned review.
DIFF_ACCESS_PINNED_SHELL_TEXT = (
    "The diff files in {diff_dir} are the authoritative record of the change. "
    + _MANIFEST_SENTENCE
    + " Read the manifest first, then each entry's diff file, with your file "
    "tools.\n"
    "\n"
    "You can also run shell commands. `git diff {sides}`, `git show` and "
    "`git log` are an optional cross-check of the diff files, never a "
    "replacement for reading them:\n"
    "1. **All changes at once:** `git diff {sides} -- <file1> <file2> ...`\n"
    "2. **One file's changes:** `git diff {sides} -- path/to/file`\n"
    "3. **A file as the head commit holds it:** `git show {head}:path/to/file`\n"
    "\n"
    "`git diff {sides} -- <path>` is required for any file the manifest "
    "marks `omitted`: it has no diff file, so that command's output is the only "
    "record of its change you can review."
)

#: The shell state's partial-coverage sentence on a pinned review.
DIFF_ACCESS_PINNED_SHELL_PARTIAL = (
    "Diff coverage for this change is partial: git produced no diff file for "
    "the files the manifest marks `omitted`. Run `git diff {sides} -- "
    "<path>` for each of them and review it from that output; if the command "
    "fails, list the file as not reviewed. Do not review their working-tree "
    "contents as if they were the change."
)

#: What a lane with no shell (or an unmeasured one) is told on a pinned review:
#: the read rule's commands need a shell, and its alternative is never the disk.
DIFF_ACCESS_PINNED_NO_SHELL_NOTE = (
    "Without a shell you cannot run the commands below: review from the diff "
    "files and the manifest alone, and read no other file from the working "
    "tree, which may not hold the reviewed code."
)

#: How many changed-on-disk files the opening names before "… and <k> more"
#: (the `[SCOPE_DRIFT]` line names the same ten).
_PINNED_DRIFT_NAMED = 10


def _pinned_opening(
    base_ref: str, head: str, *, root: bool, drifted: Sequence[str],
) -> str:
    """The pinned block's first paragraph: which change, where it ends, what
    drifted. Built by concatenation, never ``str.format``: a drifted path may
    hold braces."""
    h7, h12 = head[:7], head[:12]
    if root:
        text = (
            f"The change under review is `root..{h7}`: every commit up to and "
            f"including `{h7}`, as `git diff {base_ref} {h12}` (the empty tree "
            f"against that commit). It ends at commit `{h7}`, not at the working "
            f"tree. The range starts at the repository's first commit, so the "
            f"diff shows each whole file as new."
        )
    else:
        text = (
            f"The change under review is `{base_ref[:7]}..{h7}`: the net diff "
            f"`git diff {base_ref[:12]} {h12}`, ending at commit `{h7}`, not at "
            f"the working tree."
        )
    names = [str(path) for path in drifted if path]
    if names:
        shown = ", ".join(f"`{name}`" for name in names[:_PINNED_DRIFT_NAMED])
        if len(names) > _PINNED_DRIFT_NAMED:
            shown += f" … and {len(names) - _PINNED_DRIFT_NAMED} more"
        text += (
            f" {len(names)} reviewed file(s) have changed since `{h7}` and "
            f"differ on disk from it, so their working-tree copies are not the "
            f"reviewed code: {shown}."
        )
    return text


def _pinned_rule(base_ref: str, head: str, *, root: bool) -> str:
    """``commit_range.pinned_head_read_rule`` for this pair (imported here, not
    at module load: ``commit_range`` reaches ``cli_common``)."""
    from .commit_range import pinned_head_read_rule

    return pinned_head_read_rule(None if root else base_ref, head)


def _is_root_base(base_ref: str, cwd: Union[str, Path]) -> bool:
    """Whether *base_ref* is the repository's empty-tree id (a root range)."""
    from .git_utils import is_empty_tree_id

    return bool(base_ref) and is_empty_tree_id(base_ref, str(cwd))

#: The inline branch's opening, by read scope. It names no path: the lane
#: cannot open the phase dir, so every block below is labelled with the name
#: the manifest uses for it, never an address.
_INLINE_HEAD_BY_SCOPE = {
    "none": "You cannot open files in this review, so everything you need is "
    "inline below:",
    "cwd": "The review's artifacts sit outside the directory you can read, so "
    "everything you need is inline below:",
}
_INLINE_HEAD_TAIL_REST = (
    " the scope manifest (`" + INLINE_MANIFEST_LABEL + "`) and one "
    "diff per in-scope source and test file. The diffs are the authoritative "
    "record of the change. Each block is labelled with the name the manifest "
    "uses for it; the labels are names, not files you can open."
)
_INLINE_HEAD_TAIL = " the plan," + _INLINE_HEAD_TAIL_REST
#: The same tail when a commit review has a context plan: its frozen snapshot
#: is one more block, right after the plan's.
_INLINE_HEAD_TAIL_CONTEXT_PLAN = (
    " the plan, the context plan's frozen snapshot (`"
    + INLINE_CONTEXT_PLAN_LABEL + "`)," + _INLINE_HEAD_TAIL_REST
)

#: The inline branch's shell sentence, by ``runs_shell_in_generate``. Only the
#: ``True`` one names a command, as on the path branch.
_INLINE_SHELL_BY_STATE = {
    True: (
        "You can also run shell commands. `git diff {base_ref}`, `git show` and "
        "`git log` are an optional cross-check of the inline diffs, never a "
        "replacement for reading them."
    ),
    False: (
        "You cannot run shell commands. Do not claim a test passes or fails, "
        "because you cannot run it."
    ),
    None: (
        "Do not claim a test passes or fails unless you actually ran it and saw "
        "the result."
    ),
}

#: A diff file name as ``write_review_diff`` writes it (``<n>-<slug>.diff``),
#: as the manifest cites it (relative to itself, under ``diff/``).
_MANIFEST_DIFF_REF_RE = re.compile(r"\bdiff/(\d+-[A-Za-z0-9._-]+\.diff)")


class DiffAccess(NamedTuple):
    """What :func:`render_diff_access` decided for one code-review slot."""

    #: ``"paths"`` (the lane reads the artifacts by absolute path),
    #: ``"inline"`` (they are in :attr:`text`) or ``"unsupported"`` (the slot
    #: must not be dispatched; :attr:`reason` says why).
    mode: str
    #: The rendered ``{diff_access}`` block; ``""`` when unsupported.
    text: str
    #: The adapter's ``generate_read_scope`` (``"cwd"`` for an unknown adapter).
    read_scope: str
    #: The adapter's ``runs_shell_in_generate`` (``None`` for an unknown one).
    #: Not spelled ``shell``: a ``shell: <value>`` line is the identity-text
    #: shape ``write_safety.redact_text`` redacts (``tests/test_redaction.py``'s
    #: source-tree tripwire).
    runs_shell: Optional[bool]
    #: UTF-8 size of the inline block measured against
    #: :data:`INLINE_DIFF_CAP_BYTES`; ``0`` on the path branch.
    inline_bytes: int
    #: Why the slot is unsupported; ``""`` otherwise.
    reason: str


def _lies_within(path: Union[str, Path], root: Union[str, Path]) -> bool:
    """True when ``path`` resolves to ``root`` or somewhere beneath it."""
    try:
        resolved = os.path.realpath(str(path))
        base = os.path.realpath(str(root))
        return os.path.commonpath([resolved, base]) == base
    except (OSError, ValueError):  # ValueError: different drives on Windows
        return False


def _read_inline_text(path: Union[str, Path]) -> Optional[str]:
    """``path``'s text, or ``None`` when it cannot be read. Never raises."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None


def _inline_block(label: str, body: str) -> str:
    """One labelled block of the inline payload.

    Delimited rather than fenced: a plan or a diff routinely carries its own
    triple-backtick fences, which would close a fence early.
    """
    content = body.rstrip("\n")
    return f"===== BEGIN {label} =====\n{content}\n===== END {label} ====="


def _render_inline_diff_access(
    *,
    read_scope: str,
    runs_shell: Optional[bool],
    scope_file: str,
    diff_dir: str,
    plan_path: str,
    base_ref: str,
    partial: bool,
    head_ref: Optional[str] = None,
    pinned_opening: str = "",
    pinned_rule: str = "",
    context_plan_path: Optional[str] = None,
) -> DiffAccess:
    """The bounded inline branch, or an explicit unsupported outcome.

    The payload is the plan, the whole manifest and every file in ``diff_dir``
    except ``.gitignore``, in name order (``<n>`` is zero-padded, so name order
    is review order). It is offered only when ALL of it fits
    :data:`INLINE_DIFF_CAP_BYTES` and the coverage is complete: a partial
    inline review would read as a review of the whole change. A missing
    manifest, plan or cited diff file is a reason, never an exception.

    With *context_plan_path* (a commit review's frozen context plan,
    plans/review-commits.md §2.4) the snapshot's text is one more block, the
    :data:`INLINE_CONTEXT_PLAN_LABEL` one right after the plan, and it counts
    against the cap like the rest: a lane that cannot open the snapshot is
    shown it, or is not dispatched at all, never left to judge the range
    without it. An unreadable snapshot is a reason too.

    On a pinned review (*head_ref*) the block opens with *pinned_opening*, its
    shell sentence names ``git diff <base> <head>``, and *pinned_rule* follows
    the shell sentence, ahead of the payload; all of it counts against the cap.
    """
    reasons: List[str] = []
    blocks: List[str] = []

    plan_text = _read_inline_text(plan_path)
    if plan_text is None:
        reasons.append(f"plan file not readable: {plan_path}")
    else:
        blocks.append(_inline_block("plan", plan_text))

    if context_plan_path is not None:
        context_text = _read_inline_text(context_plan_path)
        if context_text is None:
            reasons.append(f"context plan snapshot not readable: {context_plan_path}")
        else:
            blocks.append(_inline_block(INLINE_CONTEXT_PLAN_LABEL, context_text))

    manifest = _read_inline_text(scope_file)
    if manifest is None:
        reasons.append(f"scope manifest not readable: {scope_file}")
    else:
        blocks.append(_inline_block(INLINE_MANIFEST_LABEL, manifest))

    try:
        names = sorted(
            entry.name
            for entry in os.scandir(diff_dir)
            if entry.is_file() and entry.name != ".gitignore"
        )
    except OSError:
        names = []
    unreadable: List[str] = []
    for name in names:
        body = _read_inline_text(os.path.join(diff_dir, name))
        if body is None:
            unreadable.append(name)
            continue
        blocks.append(_inline_block(f"diff/{name}", body))
    if unreadable:
        reasons.append(f"diff files not readable: {', '.join(unreadable)}")
    if manifest is not None:
        cited = set(_MANIFEST_DIFF_REF_RE.findall(manifest))
        absent = sorted(cited - set(names))
        if absent:
            reasons.append(
                f"the manifest names {len(absent)} diff file(s) that do not "
                f"exist: {', '.join(absent[:3])}"
                + (f" (+{len(absent) - 3} more)" if len(absent) > 3 else "")
            )

    if partial:
        reasons.append("diff coverage is partial")

    head = _INLINE_HEAD_BY_SCOPE.get(read_scope, _INLINE_HEAD_BY_SCOPE["none"])
    head += (
        _INLINE_HEAD_TAIL if context_plan_path is None else _INLINE_HEAD_TAIL_CONTEXT_PLAN
    )
    shell_sentence = _INLINE_SHELL_BY_STATE.get(runs_shell, _INLINE_SHELL_BY_STATE[None])
    if head_ref is None:
        text = "\n\n".join(
            [head, shell_sentence.format(base_ref=base_ref)] + blocks
        )
    else:
        sentence = shell_sentence.format(base_ref=f"{base_ref} {head_ref}")
        if runs_shell is not True:
            sentence += " " + DIFF_ACCESS_PINNED_NO_SHELL_NOTE
        text = "\n\n".join(
            [pinned_opening, head, sentence, pinned_rule] + blocks
        )
    size = len(text.encode("utf-8"))
    if size > INLINE_DIFF_CAP_BYTES:
        reasons.append(
            f"inline context {size} B exceeds the {INLINE_DIFF_CAP_BYTES} B cap"
        )

    if reasons:
        return DiffAccess("unsupported", "", read_scope, runs_shell, size, "; ".join(reasons))
    return DiffAccess("inline", text, read_scope, runs_shell, size, "")


def render_diff_access(
    model_spec: str,
    scope_file: Union[str, Path],
    diff_dir: Union[str, Path],
    phase_dir: Union[str, Path],
    cwd: Union[str, Path],
    *,
    base_ref: str,
    coverage: str,
    plan_path: Union[str, Path],
    anchor: Optional[Union[str, Path]] = None,
    head_ref: Optional[str] = None,
    drifted: Sequence[str] = (),
    context_plan_path: Optional[Union[str, Path]] = None,
) -> DiffAccess:
    """Decide how ``model_spec``'s lane reaches the change, and render the block.

    ``scope_file`` is ``code-review/review-scope.md``, ``diff_dir`` is
    ``code-review/diff/``, ``phase_dir`` is the code-review phase dir and
    ``cwd`` is the directory the lane runs in (the repo root), all absolute.
    ``coverage`` is ``write_review_diff``'s ``"complete"`` or ``"partial"``;
    anything but ``"complete"`` is treated as partial, the conservative reading.

    The adapter is resolved exactly as :func:`render_output_location` resolves
    it (``anchor`` is the run's plan path). An unknown adapter reads as
    ``generate_read_scope="cwd"``, ``runs_shell_in_generate=None`` — the base
    defaults, which assert nothing about a shell.

    * **Usable file reads** — ``"any"``, or ``"cwd"`` with ``phase_dir``
      resolving inside ``cwd`` — give ``mode="paths"``: one of three texts
      chosen by ``runs_shell_in_generate``, each naming both absolute paths and
      calling the diff files the authoritative record, plus that state's
      partial-coverage sentence when coverage is partial.
    * **No usable reads** — ``"none"``, or ``"cwd"`` with the phase dir outside
      the repo — give the bounded inline branch, whatever the shell state:
      ``mode="inline"`` when coverage is complete and the whole block fits
      :data:`INLINE_DIFF_CAP_BYTES`, otherwise ``mode="unsupported"`` with an
      empty ``text`` and the reason, so the caller dispatches nothing.

    ``head_ref`` pins the review to a commit (``review-code --head-ref``, a
    commit brief; plans/review-commits.md §2.5): ``base_ref`` is then the base
    commit, or the empty-tree id on a root range. The block opens by naming
    the change as ``<base7>..<head7>`` ending at the head commit, not at the
    working tree, and names *drifted* (the reviewed files that differ on disk
    from it) as changed since that commit; every command reads ``git diff
    <base> <head>`` and a file's content through ``git show <head>:<path>``;
    nothing says the disk is the reviewed content; and the pinned-head read
    rule closes it. ``None`` renders today's text byte for byte.

    ``context_plan_path`` is a commit review's frozen context-plan snapshot
    (``commit_range.plan_snapshot``, plans/review-commits.md §2.4), absolute.
    The paths branch leaves it to the prompt's ``{plan_block}``, which names
    it; the inline branch carries its text as one more block, counted against
    the cap, so an inline lane checks the range against the same plan every
    other reviewer reads, or is not dispatched (too large, or unreadable).

    Never raises for a missing manifest, diff, plan or snapshot file.
    """
    provider_name, _ = parse_model_spec(model_spec, anchor=anchor)
    provider = get_provider(provider_name)
    read_scope = (
        getattr(provider, "generate_read_scope", "cwd") if provider is not None else "cwd"
    )
    shell = (
        getattr(provider, "runs_shell_in_generate", None)
        if provider is not None
        else None
    )
    partial = coverage != "complete"
    scope_file = os.path.abspath(str(scope_file))
    diff_dir = os.path.abspath(str(diff_dir))
    # An empty base ref (no resolvable ref, e.g. an initial commit) fails the
    # whole diff set, so coverage is partial; the command text still has to
    # read as a command with a slot in it rather than `git diff  -- <path>`.
    ref = base_ref or "<base_ref>"
    context_plan = (
        os.path.abspath(str(context_plan_path)) if context_plan_path is not None else None
    )

    reads = read_scope == "any" or (
        read_scope == "cwd" and _lies_within(phase_dir, cwd)
    )
    if head_ref is not None:
        return _render_pinned_diff_access(
            reads=reads,
            read_scope=read_scope,
            runs_shell=shell,
            partial=partial,
            scope_file=scope_file,
            diff_dir=diff_dir,
            plan_path=str(plan_path),
            base_ref=ref,
            head_ref=head_ref,
            drifted=drifted,
            root=_is_root_base(base_ref, cwd),
            context_plan_path=context_plan,
        )
    if not reads:
        return _render_inline_diff_access(
            read_scope=read_scope,
            runs_shell=shell,
            scope_file=scope_file,
            diff_dir=diff_dir,
            plan_path=str(plan_path),
            base_ref=ref,
            partial=partial,
            context_plan_path=context_plan,
        )

    if shell is True:
        text, extra = DIFF_ACCESS_SHELL_TEXT, DIFF_ACCESS_SHELL_PARTIAL
    elif shell is False:
        text, extra = DIFF_ACCESS_NO_SHELL_TEXT, DIFF_ACCESS_NO_SHELL_PARTIAL
    else:
        text, extra = DIFF_ACCESS_UNMEASURED_TEXT, DIFF_ACCESS_UNMEASURED_PARTIAL
    if partial:
        text = text + "\n\n" + extra
    rendered = text.format(scope_file=scope_file, diff_dir=diff_dir, base_ref=ref)
    return DiffAccess("paths", rendered, read_scope, shell, 0, "")


def _render_pinned_diff_access(
    *,
    reads: bool,
    read_scope: str,
    runs_shell: Optional[bool],
    partial: bool,
    scope_file: str,
    diff_dir: str,
    plan_path: str,
    base_ref: str,
    head_ref: str,
    drifted: Sequence[str],
    root: bool,
    context_plan_path: Optional[str] = None,
) -> DiffAccess:
    """:func:`render_diff_access` for a review pinned to *head_ref*.

    The same branch decision (paths, inline or unsupported) and the same
    per-state texts, with the head commit as the new side: the opening names
    the change and the drifted files, the body's commands take ``<base>
    <head>``, and the pinned-head read rule follows. Only the template parts
    go through ``str.format``; the opening and the rule are concatenated, as
    paths and commit text may hold braces.
    """
    opening = _pinned_opening(base_ref, head_ref, root=root, drifted=drifted)
    rule = _pinned_rule(base_ref, head_ref, root=root)
    if not reads:
        return _render_inline_diff_access(
            read_scope=read_scope,
            runs_shell=runs_shell,
            scope_file=scope_file,
            diff_dir=diff_dir,
            plan_path=plan_path,
            base_ref=base_ref,
            partial=partial,
            head_ref=head_ref,
            pinned_opening=opening,
            pinned_rule=rule,
            context_plan_path=context_plan_path,
        )
    if runs_shell is True:
        text, extra = DIFF_ACCESS_PINNED_SHELL_TEXT, DIFF_ACCESS_PINNED_SHELL_PARTIAL
    elif runs_shell is False:
        text, extra = DIFF_ACCESS_NO_SHELL_TEXT, DIFF_ACCESS_NO_SHELL_PARTIAL
    else:
        text, extra = DIFF_ACCESS_UNMEASURED_TEXT, DIFF_ACCESS_UNMEASURED_PARTIAL
    if partial:
        text = text + "\n\n" + extra
    body = text.format(
        scope_file=scope_file, diff_dir=diff_dir, base_ref=base_ref,
        sides=f"{base_ref} {head_ref}", head=head_ref[:12],
    )
    parts = [opening, body]
    if runs_shell is not True:
        parts.append(DIFF_ACCESS_PINNED_NO_SHELL_NOTE)
    parts.append(rule)
    return DiffAccess("paths", "\n\n".join(parts), read_scope, runs_shell, 0, "")


#: The ``{working_limits}`` block the review templates carry just above their
#: output sections (plan: review-run-scope-salvage-and-failure-visibility D3.2).
#: Measured on the 2026-09-25 review run: a pi code-review slot with a 1200 s
#: budget started ``timeout 1700 python -m pytest tests`` and was killed
#: mid-suite, having written nothing — nothing in the prompt told it how long it
#: had or that the suite was off limits. So the block states the real number of minutes and
#: forbids long commands, while still allowing ONE narrowly scoped test file
#: (decision 11.7, the same allowance ``prompts/implementation_task.txt`` makes).
#:
#: It deliberately names no shell command: it reaches every Lane A lane,
#: cursor-agent and claude-code included, which have no shell, so a "use
#: ``git diff``" line here would grant what ``{diff_access}`` denies in the same
#: prompt. The test-claim line is here rather than only in ``{diff_access}``
#: because the false HIGH finding in that run's evidence was a model asserting
#: a test result it had not run, and every lane can make that claim. Advisory
#: text only — what bounds a model that ignores it is the slot's kill.
WORKING_LIMITS_BLOCK = (
    "## Working limits\n"
    "- This review is stopped after about {minutes}. Anything unfinished at "
    "that point is lost, so write your answer well before then.\n"
    "- Do NOT run the project's test suite, builds, linters, installers, or any "
    "other long-running command. This is a read-only review. If a finding "
    "depends on a test's result, you may run that ONE narrowly scoped test "
    "file, and only if you can run commands at all.\n"
    "- Do NOT modify, create or delete any file except the output file named "
    "below.\n"
    "- Do NOT claim that a test passes or fails unless you ran it during this "
    "review and saw its result. Say what a test covers, not what it would "
    "report."
)


def render_working_limits(timeout_s: Union[int, float]) -> str:
    """The ``{working_limits}`` block for an attempt with ``timeout_s`` seconds.

    ``timeout_s`` must be the budget THIS attempt is really spawned with — the
    ``timeout`` handed to :func:`invoke_with_file_output`, or the ladder's slice
    on the review-plan/review-tasks fan-out — because the number is the point:
    the incident's model chose ``timeout 1700`` inside a 1200 s slot. Minutes are
    floored (never promise time the kill will not honour) and never below 1, so
    a sub-minute slot still reads as a deadline rather than "about 0 minutes".
    """
    minutes = max(1, int(timeout_s // 60))
    unit = "minute" if minutes == 1 else "minutes"
    return WORKING_LIMITS_BLOCK.format(minutes=f"{minutes} {unit}")


#: `result["source"]` values where the file on disk is what the model itself
#: produced. Anything else (chiefly `stdout_fallback`) means the answer came
#: over stdout and `output_file` is only where THIS PROCESS intends to persist
#: it later (`save_model_result`, run after the whole fan-out finishes) — see
#: `describe_output_file` (F14).
FILE_WRITTEN_SOURCES = frozenset({"file", "file_extracted"})


def describe_output_file(output_file: Union[str, Path], source: str) -> str:
    """The one line a fan-out prints about where a slot's answer lives (F14).

    ``[model] Output file: <path> (source: stdout_fallback)`` reads as "the
    model wrote this" — and for a provider with ``supports_file_output =
    False`` (or one that simply didn't write this time), it did not: the path
    is a promise this process is making to itself, not a fact about the
    child. Wording is picked from the *observed* ``source`` rather than the
    provider's declared capability, so a file-capable provider that happened
    to fall back to stdout this attempt still gets the accurate line.
    """
    verb = "Output file" if source in FILE_WRITTEN_SOURCES else "Result will be saved to"
    return f"{verb}: {output_file} (source: {source})"


def _finalize_file_output_log(
    log_file: Optional[Union[str, Path]],
    deferred_log: Optional[Dict[str, Any]],
    result: Dict[str, Any],
    model_spec: str,
    prompt: str,
    *,
    success: bool,
    error: Optional[str],
    result_source: Optional[str],
) -> None:
    """Write the one log entry :func:`invoke_with_file_output` owes (§Fix1/F13).

    A no-op when no log was requested, or when the run hard-failed before
    reaching the exit-0 branch that defers (there is no channel choice to
    report on those). Every exit-0 outcome defers now — a clean stdout parse
    included — so this is the single place that settles what the log
    ultimately says: the FINAL outcome — after the file channel and the
    stdout fallback both had their turn — never the stdout extractor's own
    opinion of a run it did not get the last word on, and always carrying
    ``Result source:`` (``file`` / ``file_extracted`` / ``stdout_fallback`` /
    absent on a double failure), which a clean-parse run used to lack
    entirely (F13): the immediate write inside ``invoke_with_provider`` ran
    before the file-vs-stdout choice existed to name.
    """
    if not log_file or deferred_log is None:
        return
    details = result.get("details", {})
    provider = details.get("provider")
    model = details.get("model")
    resolved_model = f"{provider}:{model}" if provider or model else model_spec
    # The stdout extractor's own verdict travels alongside the final one
    # rather than being overwritten by it — "Success: True" by itself would
    # hide that the file channel is what actually salvaged this run.
    stdout_parse_error = result.get("error") if not result.get("success") else None
    _save_log(
        log_file=log_file,
        model=resolved_model,
        prompt=prompt,
        stdout=deferred_log.get("stdout", ""),
        stderr=deferred_log.get("stderr", ""),
        returncode=deferred_log.get("returncode", -1),
        success=success,
        error=error,
        duration_seconds=deferred_log.get("duration_seconds"),
        result_source=result_source,
        stdout_parse_error=stdout_parse_error,
        readonly_audit=details.get(_READONLY_AUDIT_KEY),
    )


def _file_output_context(
    model_spec: str,
    prompt_context: Dict[str, Any],
    output_dir: Union[str, Path],
    phase: str,
    timeout: Optional[int],
    anchor: Optional[Union[str, Path]],
) -> Tuple[Dict[str, Any], Path]:
    """The context :func:`invoke_with_file_output` formats its template with.

    Returns ``(full_context, output_json_path)``. One owner, so the prompt
    :func:`argv_prompt_bytes` measures is the prompt that is dispatched.
    """
    from .json_extractor import generate_output_path

    # Generate output file path
    prefix = prompt_context.get("prefix", "output")
    output_json_path = generate_output_path(Path(output_dir), prefix, phase, model_spec)

    # Inject output path into prompt context, plus the channel instruction that
    # path belongs to: an adapter whose CLI cannot write files is asked for the
    # array on stdout instead of being asked for a file it will refuse. The path
    # itself is still handed over (a template may name it outside the block, and
    # every caller-supplied template in the test suite does), and the file is
    # still read first below, so a provider that writes one anyway is unaffected.
    full_context = {
        **prompt_context,
        "output_json_path": str(output_json_path),
        "output_location": render_output_location(
            output_json_path, model_spec, anchor=anchor
        ),
        # The minutes this call will really be allowed: a missing `timeout` is
        # resolved exactly as `invoke_with_provider` resolves it below, so the
        # deadline the prompt states is the one the kill honours. A template
        # without the placeholder ignores the key (`str.format` drops extras).
        "working_limits": render_working_limits(
            timeout or get_provider_timeout(
                parse_model_spec(model_spec, anchor=anchor)[0], anchor=anchor
            )
        ),
    }
    return full_context, output_json_path


def argv_prompt_bytes(
    prompt_template: str,
    model_spec: str,
    prompt_context: Dict[str, Any],
    output_dir: Union[str, Path],
    phase: str,
    timeout: Optional[int] = None,
    anchor: Optional[Union[str, Path]] = None,
) -> Optional[int]:
    """UTF-8 size of the prompt :func:`invoke_with_file_output` would put on argv.

    Takes that function's own arguments and renders the same prompt, so a
    caller can refuse a slot whose prompt would exceed the single-argument
    ceiling (:data:`INLINE_PROMPT_CAP_BYTES`) before anything is spawned.
    ``None`` when the prompt would not travel on argv at all — an adapter
    whose default ``prompt_transport`` is not ``argv``, an unknown adapter
    (nothing is spawned for it) — or when the template does not format, which
    the dispatch itself reports as ``PROMPT_FORMAT_ERROR``. Never raises.
    """
    try:
        provider = get_provider(parse_model_spec(model_spec, anchor=anchor)[0])
        if provider is None or getattr(provider, "prompt_transport", "argv") != "argv":
            return None
        full_context, _ = _file_output_context(
            model_spec, prompt_context, output_dir, phase, timeout, anchor
        )
        prompt = prompt_template.format(**full_context)
    except Exception:  # noqa: BLE001 - a measurement never fails the slot
        return None
    return len(prompt.encode("utf-8"))


def misnamed_result_baseline(
    output_dir: Union[str, Path],
    phase: str,
    model_spec: str,
) -> Dict[str, Tuple[int, int]]:
    """The candidate files of the phase dir :func:`invoke_with_file_output` writes into, now.

    A review slot takes this once, before its first attempt, and hands it to
    every attempt as ``misnamed_baseline``: a misnamed file is this slot's only
    when it appeared (or changed) after the slot started. Taken per attempt, an
    attempt killed after writing it under the wrong name left it in the next
    attempt's baseline, and the slot was recorded failed beside its own answer
    (review of fix round 24).
    """
    from .json_extractor import generate_output_path

    phase_dir = generate_output_path(Path(output_dir), "output", phase, model_spec).parent
    return _result_files.snapshot_candidates(phase_dir)


#: ``(st_dev, st_ino, st_size, st_mtime_ns)`` of a slot's requested result file
#: when the slot started, or ``()`` when there was none.
ResultFileStamp = Tuple[int, ...]


def _result_file_stamp(path: Union[str, Path]) -> ResultFileStamp:
    """What moves when anything writes *path*: its identity, size and mtime.

    ``()`` when there is no file. Followed through a link, as
    :func:`read_json_from_file` follows one when it reads the file. The inode is
    in it so a file renamed over the old one is a change whatever its size and
    mtime say. No content hash, on purpose: a model that writes the same bytes
    again has answered this call, and identical bytes would hide it. The mtime
    is safe at any filesystem's granularity here, because the file it is
    compared with is a previous round's, written well before the stamp was
    taken, so any write after the stamp lands on a later tick.
    """
    try:
        st = os.stat(path)
    except OSError:
        return ()
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def requested_result_baseline(
    output_dir: Union[str, Path],
    phase: str,
    model_spec: str,
) -> ResultFileStamp:
    """The stamp of the file :func:`invoke_with_file_output` asks *model_spec* for, now.

    A slot takes this once, before its first attempt, and hands it to every
    attempt as ``requested_baseline``, for the reason
    :func:`misnamed_result_baseline` is the slot's: the file an attempt killed
    after writing it left behind is still this slot's answer when the retry
    writes nothing. Taken per attempt, that file is in the retry's baseline,
    the retry skips it, and the slot is recorded failed beside its own answer,
    while the same file written under the wrong name is adopted (step 1b): the
    better-named answer would be the one refused. The file that was there
    before the slot started (the previous round's) is never this slot's, on
    any attempt, and is not left for anything after the slot to read either:
    the attempt that finds it unchanged renames it
    ``<stem>.json.stale-earlier-run`` (:func:`_set_aside_unchanged_result`).
    Refused but left in place, the salvage recovery loop and ``--reaggregate``
    both read it back as this round's answer at exit 0 (Fable review
    2026-10-09).
    """
    from .json_extractor import generate_output_path

    return _result_file_stamp(
        generate_output_path(Path(output_dir), "output", phase, model_spec)
    )


def _set_aside_unchanged_result(path: Path, baseline: ResultFileStamp) -> bool:
    """Set *path* aside when it is still exactly the file the slot started beside.

    The one place every file-output lane reaches (review-plan and review-tasks
    through ``run_single_model``, review-code's slot; ``ask`` writes markdown
    through ``invoke_with_provider`` and has no such file), so the rule holds
    on every lane: once an attempt has found the previous round's file
    unchanged, it is renamed out of every result glob before the attempt
    returns (:func:`utils.result_files.set_aside_stale_result`), whatever the
    slot then makes of it. Before (Fable review 2026-10-09), the refused file
    stayed on disk and two readers took it back as this round's answer: the
    ``--exec-subagents`` salvage recovery loop, and ``--reaggregate``. Doing it
    at the attempt rather than at the slot's failure also covers a slot failed
    after this function returned success — the porcelain, mode and home checks,
    or ``save_model_result`` refusing a stdout answer — and costs a slot that
    answered on stdout nothing: ``save_model_result`` writes its answer to the
    requested name, where the old file would have been overwritten. ``()`` (no
    file when the slot started) and a file that moved since are never touched.

    Returns whether *path* was that earlier round's file — ``True`` even when
    the rename failed (which warns on stderr), because the caller's question is
    whether to read it, and the answer is no either way.
    """
    if not baseline or _result_file_stamp(path) != baseline:
        return False
    _result_files.set_aside_stale_result(path)
    return True


def _adopt_misnamed_result(
    output_json_path: Path,
    before: Dict[str, Tuple[int, int]],
    model_spec: str,
    run_model_specs: Sequence[str],
    *,
    prefer_arrays: bool,
) -> Optional[Tuple[Any, str]]:
    """Read and rename the one misnamed result this slot wrote (step 1b).

    ``(data, the name it was written under)``, or ``None`` — no unambiguous
    candidate, one that does not parse as a JSON array (the shape every review
    asks for), or a rename that failed. The rename puts the file at the
    requested name, so it is this model's file from here on and no glob can
    read it a second time as somebody else's.

    The candidate is read through one descriptor that never follows a link
    (:func:`utils.result_files.read_regular_text`), and what the rename left
    at the requested name must be that same regular file: a link swapped in
    after the directory scan, or before the rename, is never adopted (review
    of fix round 24).
    """
    from .json_extractor import parse_file_content

    found = _result_files.find_misnamed_result(
        output_json_path.parent, before, model_spec, run_model_specs
    )
    if found is None:
        return None
    opened = _result_files.read_regular_text(found)
    if opened is None:
        return None
    content, identity = opened
    read = parse_file_content(content, prefer_arrays=prefer_arrays)
    if not read.get("success") or not isinstance(read.get("data"), list):
        return None
    try:
        os.replace(found, output_json_path)
    except OSError:
        return None
    if not _result_files.is_same_regular_file(output_json_path, identity):
        return None
    return read["data"], found.name


def invoke_with_file_output(
    prompt_template: str,
    model_spec: str,
    prompt_context: Dict[str, Any],
    output_dir: Union[str, Path],
    phase: str,
    timeout: Optional[int] = None,
    log_file: Optional[Union[str, Path]] = None,
    prefer_arrays: bool = True,
    cwd: Optional[str] = None,
    anchor: Optional[Union[str, Path]] = None,
    sandbox_fallback: Optional[str] = None,
    run_model_specs: Optional[Sequence[str]] = None,
    misnamed_baseline: Optional[Dict[str, Tuple[int, int]]] = None,
    requested_baseline: Optional[ResultFileStamp] = None,
) -> Dict[str, Any]:
    """Invoke LLM with file-based JSON output.

    This function instructs the LLM to write JSON output to a specified file
    instead of relying on stdout parsing. The prompt is formatted with an
    {output_json_path} variable that the LLM should use, and an
    {output_location} block rendered from the adapter's declared
    ``supports_file_output`` — a CLI running in a read-only mode is asked for
    the array on stdout rather than for a file it is going to refuse (see
    :func:`render_output_location`). Both channels are read below either way.

    Fallback strategy:
    1. Primary: Read from output file (with extraction fallback for code blocks)
       — only a file that appeared or changed since the slot started
       (``requested_baseline``). One that was there before and is unchanged is
       a previous round's answer, not this call's: it is not read, it is
       renamed ``<name>.stale-earlier-run`` so nothing after this call reads
       it either (:func:`_set_aside_unchanged_result`), and the steps below
       run as if it were missing
    1b. With ``run_model_specs``, when the output file is missing: the one JSON
        array this model's provider prefix wrote elsewhere in the phase dir
        during the call (``utils/result_files.find_misnamed_result``), renamed
        to the requested name and reported as ``misnamed_from``
    2. Secondary: Parse stdout (current behavior)
    3. Tertiary: Return error for salvage request

    Args:
        prompt_template: Prompt template with {output_json_path} placeholder
        model_spec: Model specification (e.g., 'cursor-agent:auto')
        prompt_context: Dict of variables to substitute in the prompt template
        output_dir: Directory for output files
        phase: Operation phase for filename (e.g., 'code_review', 'plan_review')
        timeout: Optional timeout override in seconds
        log_file: Optional path to save full output log
        prefer_arrays: If True, prefer array candidates when extracting JSON
        anchor: Optional discovery anchor (the run's plan-file path), forwarded
            verbatim to :func:`invoke_with_provider` (§9.3.c)
        sandbox_fallback: The D6 override, forwarded verbatim to
            :func:`invoke_with_provider`; the prompt's ``{output_location}``
            block is unchanged by it (a bypassed codex still answers on
            stdout, measured 2026-09-17 — its final ``agent_message`` was the
            array, exactly the ``stdout_fallback`` shape this reads).
        run_model_specs: Every model of the fan-out this slot belongs to,
            itself included. Given, a missing output file is looked for under a
            wrong name (step 1b): live run 10, pi wrote
            ``…deepseek-v4-flash.json`` for ``…deepseek-v4_1-flash.json`` and
            its three findings were recorded as a failed model. ``None`` (the
            default) never looks, which is every caller that does not know
            which other models write into the same dir.
        misnamed_baseline: Step 1b's baseline, from
            :func:`misnamed_result_baseline` taken once at the slot's start, so
            a file an earlier attempt of the same slot wrote under the wrong
            name is still this slot's on a retry. ``None`` takes it here, at the
            start of this call (a slot of one attempt).
        requested_baseline: Step 1's baseline, from
            :func:`requested_result_baseline` taken once at the slot's start
            (``()`` when the file was not there), for the same reason. ``None``
            takes it here, at the start of this call (a slot of one attempt).

    Returns:
        Dict with keys:
        - 'success': bool indicating overall success
        - 'data': Parsed JSON data (if successful)
        - 'source': Where JSON came from ('file', 'file_extracted', 'stdout_fallback')
        - 'output_file': Path to the output file (if generated)
        - 'error': Error message (if failed)
        - 'file_error': File-specific error (if file read failed, or the file
          was left unread as older than the slot)
        - 'details': Provider execution details, forwarded verbatim on every
          return path — including §3.6's ``served_model`` /
          ``served_model_is_fallback``, so the JSON's origin travels with it
          whichever channel (file, extracted file, stdout) supplied it
    """
    from .json_extractor import read_json_from_file

    full_context, output_json_path = _file_output_context(
        model_spec, prompt_context, output_dir, phase, timeout, anchor
    )
    # Step 1b's baseline, taken before the child can write anything: a file
    # this call adopts must have appeared (or changed) since the slot started —
    # the caller's baseline when it took one before its first attempt, else now.
    if run_model_specs is None:
        phase_files_before = None
    elif misnamed_baseline is not None:
        phase_files_before = misnamed_baseline
    else:
        phase_files_before = _result_files.snapshot_candidates(output_json_path.parent)
    # Step 1's baseline, by the same rule and at the same moment: the requested
    # file is this call's answer only if it appeared (or changed) since the
    # slot started. Read unconditionally, a re-run over a phase dir that still
    # holds the previous round's `{model}.json` (`--force --rerun-all`) handed
    # that round's findings back as the new answer of every model that answered
    # on stdout or did not write the file this time, logged `source: file`
    # (measured 2026-10-09 with the suite's mock providers).
    if requested_baseline is None:
        requested_baseline = _result_file_stamp(output_json_path)

    # Format prompt
    try:
        prompt = prompt_template.format(**full_context)
    except KeyError as e:
        # A failed slot leaves no earlier round's file behind for the salvage
        # recovery loop or `--reaggregate` to read (Fable review 2026-10-09).
        _set_aside_unchanged_result(output_json_path, requested_baseline)
        return {
            "success": False,
            "error": f"Missing prompt variable: {e}",
            "error_code": "PROMPT_FORMAT_ERROR",
            "data": None,
        }

    # Invoke provider. §Fix1: defer the log write for an exit-0 stdout parse
    # failure — this function may still salvage the run through the file
    # channel below, and the immediate write inside invoke_with_provider
    # cannot know that yet.
    result = invoke_with_provider(prompt, model_spec, timeout, log_file, cwd=cwd,
                                  anchor=anchor, _defer_parse_failure_log=True,
                                  sandbox_fallback=sandbox_fallback)
    deferred_log = result.get("details", {}).pop("_deferred_log", None)

    # Check for hard failures that mean the command didn't run properly
    # (as opposed to parse errors which may still have written to file)
    error_code = result.get("error_code", "")
    is_hard_failure = error_code in (
        ERROR_BINARY_NOT_FOUND,
        ERROR_TIMEOUT,
        ERROR_SUBPROCESS_FAILED,
        ERROR_PROMPT_TOO_LONG,
        ERROR_PROMPT_UNSAFE,
    )

    if not result.get("success") and is_hard_failure:
        # `deferred_log` is USUALLY None here: the three classic hard failures
        # (binary missing, timeout kill, non-zero exit) all return before
        # `invoke_with_provider` reaches the exit-0 branch that defers, so
        # nothing was deferred and there is nothing to settle.
        #
        # It is not always None. An adapter whose `parse_output` reads an exit-0
        # stream and calls it a hard failure — a terminal in-stream verdict, the
        # shape a JSON-streaming CLI uses to report an auth or context error it
        # exited 0 on — lands here *with* a deferred log, because the run did
        # reach the deferring branch. Returning without this call would silently
        # drop that run's only log entry: the whole log for the slot, not a line
        # of it. `success=False` and `result["error"]` because that is the
        # outcome, and `result_source=None` because no channel answered — the
        # same triple the "both failed" return below uses, which is the other
        # way a run ends with nothing to show for it.
        _finalize_file_output_log(
            log_file, deferred_log, result, model_spec, prompt,
            success=False, error=result.get("error"), result_source=None,
        )
        # The file channel is never read on this path, so an earlier round's
        # file is set aside here or not at all: left on disk, the slot's
        # failure is undone by the salvage recovery loop or a `--reaggregate`
        # reading it back (Fable review 2026-10-09). A file this attempt wrote
        # before it died has moved, and stays: it is this slot's.
        _set_aside_unchanged_result(output_json_path, requested_baseline)
        return {
            **result,
            "output_file": str(output_json_path),
        }

    # Try to read JSON from file first (even if stdout parsing failed) — a file
    # this slot wrote. One that was there when the slot started and has not
    # moved since is the previous round's answer: it is set aside now
    # (`<name>.stale-earlier-run`, never deleted), so neither this call nor
    # anything after it — the salvage recovery loop, `--reaggregate`, a slot
    # failed after this returns — can take it for this round's (Fable review
    # 2026-10-09), and every step below runs exactly as if it were missing. A
    # stdout answer is then saved to the requested name as before.
    stale_file = _set_aside_unchanged_result(output_json_path, requested_baseline)
    if stale_file:
        file_result = {
            "success": False,
            "error": (
                f"{output_json_path.name} is older than this slot and unchanged: "
                f"an earlier run's answer, not read"
            ),
            "source": "stale",
            "data": None,
        }
    else:
        file_result = read_json_from_file(output_json_path, prefer_arrays=prefer_arrays)

    if file_result.get("success"):
        _finalize_file_output_log(
            log_file, deferred_log, result, model_spec, prompt,
            success=True, error=None,
            result_source=file_result.get("source", "file"),
        )
        return {
            "success": True,
            "data": file_result["data"],
            "source": file_result.get("source", "file"),
            "output_file": str(output_json_path),
            "details": result.get("details", {}),
        }

    # Step 1b: the requested file is missing (or only the previous round's), but
    # the model may have written its answer under another name. Before stdout,
    # because a file the model wrote is its deliberate answer and stdout is a
    # scrape.
    if phase_files_before is not None and file_result.get("source") in ("missing", "stale"):
        adopted = _adopt_misnamed_result(
            output_json_path, phase_files_before, model_spec, run_model_specs,
            prefer_arrays=prefer_arrays,
        )
        if adopted is not None:
            data, wrote = adopted
            _finalize_file_output_log(
                log_file, deferred_log, result, model_spec, prompt,
                success=True, error=None, result_source=f"file (written as {wrote})",
            )
            return {
                "success": True,
                "data": data,
                "source": "file",
                "output_file": str(output_json_path),
                "misnamed_from": wrote,
                "details": result.get("details", {}),
            }

    # Fall back to stdout parsing (the data parsed by the provider)
    stdout_data = result.get("data")
    if _is_valid_parsed_data(stdout_data):
        # The log names the file it passed over: without it, a reader holding
        # the old `{model}.json` and this log cannot tell why it did not count.
        _finalize_file_output_log(
            log_file, deferred_log, result, model_spec, prompt,
            success=True, error=None,
            result_source=(
                f"stdout_fallback ({file_result['error']})"
                if stale_file else "stdout_fallback"
            ),
        )
        return {
            "success": True,
            "data": stdout_data,
            "source": "stdout_fallback",
            "output_file": str(output_json_path),
            "file_error": file_result.get("error"),
            "details": result.get("details", {}),
        }

    # Both failed. The returned `error` is the one string callers match; the
    # log also says when the file channel was the previous round's file, which
    # was never parsed at all.
    _finalize_file_output_log(
        log_file, deferred_log, result, model_spec, prompt,
        success=False,
        error=(
            f"JSON parsing failed from both file and stdout ({file_result['error']})"
            if stale_file else "JSON parsing failed from both file and stdout"
        ),
        result_source=None,
    )
    return {
        "success": False,
        "error": "JSON parsing failed from both file and stdout",
        "error_code": ERROR_PARSE_ERROR,
        "file_error": file_result.get("error"),
        "stdout_error": result.get("error", "No valid JSON in stdout"),
        "output_file": str(output_json_path),
        "details": result.get("details", {}),
        "data": None,
    }


def invoke_subagent(
    prompt: str,
    model: Optional[str] = None,
    context_files: Optional[List[str]] = None,
    allowed_tools: Optional[List[str]] = None,
    timeout: int = 1200,
    max_retries: int = 2,
    retry_backoff: Optional[List[int]] = None,
    log_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Invoke a cursor-agent subagent with the given prompt.

    This is a backward-compatible wrapper that delegates to invoke_with_provider()
    while maintaining the original interface and retry logic.

    Args:
        prompt: The prompt/task for the subagent
        model: Optional model to use (e.g., "sonnet", "opus")
        context_files: List of file paths to provide as context (included in prompt)
        allowed_tools: List of allowed tools for the subagent (included in prompt)
        timeout: Timeout in seconds (default 1200 = 20 minutes)
        max_retries: Maximum number of retry attempts
        retry_backoff: List of backoff delays in seconds (default [5, 15])
        log_file: Optional path to save full output log for debugging

    Returns:
        Dict with 'success', 'output', 'stderr', and optionally 'error' keys
    """
    if retry_backoff is None:
        retry_backoff = [5, 15]

    # Build model spec for provider abstraction
    # cursor-agent is the default provider when model doesn't have a prefix
    model_spec = f"cursor-agent:{model}" if model else "cursor-agent:auto"

    last_result = None
    last_error = None

    for attempt in range(max_retries + 1):
        # Delegate to invoke_with_provider()
        result = invoke_with_provider(
            prompt=prompt,
            model_spec=model_spec,
            timeout=timeout,
            log_file=log_file if attempt == max_retries else None  # Only log final attempt
        )

        if result["success"]:
            # Convert to legacy format for backward compatibility
            # The invoke_with_provider returns 'data', but invoke_subagent returns 'output'
            details = result.get("details", {})
            # Return raw JSON output string to match legacy behavior
            data = result.get("data", "")
            output = json.dumps(data) if data and not isinstance(data, str) else str(data) if data else ""
            return {
                "success": True,
                "output": output,
                "stderr": details.get("stderr", "")
            }

        last_result = result
        last_error = result.get("error", "Unknown error")

        # Check if it's a binary not found error (no point retrying)
        if result.get("error_code") == ERROR_BINARY_NOT_FOUND:
            raise LLMClientError("cursor-agent CLI not found. Please ensure it is installed and in PATH.")

        # Retry if we haven't exhausted attempts
        if attempt < max_retries:
            backoff_delay = retry_backoff[min(attempt, len(retry_backoff) - 1)]
            time.sleep(backoff_delay)

    # Check for timeout error
    if last_result and last_result.get("error_code") == ERROR_TIMEOUT:
        raise SubagentTimeoutError(f"Subagent timed out after {max_retries + 1} attempts: {last_error}")

    # Return error in legacy format
    details = last_result.get("details", {}) if last_result else {}
    return {
        "success": False,
        "output": "",
        "stderr": details.get("stderr", ""),
        "error": last_error
    }


def parse_subagent_response(output: str) -> Dict[str, Any]:
    """
    Parse structured output from a subagent response.

    Args:
        output: Raw output string from subagent

    Returns:
        Parsed JSON as dict/list, or {"raw": output} if no JSON found
    """
    output = output.strip()

    # First, try to parse as cursor-agent JSON wrapper format
    # cursor-agent --output-format json returns: {"type":"result","result":"...","..."}
    if output.startswith('{'):
        try:
            wrapper = json.loads(output)
            if isinstance(wrapper, dict) and "result" in wrapper:
                # Extract the inner result and parse it
                inner_result = wrapper["result"]
                if isinstance(inner_result, str):
                    inner_result = inner_result.strip()
                    if inner_result.startswith(('[', '{')):
                        try:
                            return json.loads(inner_result)
                        except json.JSONDecodeError:
                            pass
                    # Try to find JSON in the inner result
                    return _extract_json_from_text(inner_result)
                return inner_result if inner_result else {"raw": output}
            # Not a wrapper format, might be direct JSON
            return wrapper
        except json.JSONDecodeError:
            pass

    # Try direct JSON parsing for arrays
    if output.startswith('['):
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass

    return _extract_json_from_text(output)


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON from text that may contain other content."""
    # Try code block extraction
    code_block_match = re.search(r'```(?:json)?\s*([\[\{][\s\S]*?[\]\}])\s*```', text)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON arrays or objects
    for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    return {"raw": text}

def invoke_for_json(
    prompt: str,
    model: Optional[str] = None,
    context_files: Optional[List[str]] = None,
    timeout: int = 1200
) -> Dict[str, Any]:
    """
    Invoke subagent expecting JSON output.

    Args:
        prompt: The prompt (should request JSON output)
        model: Optional model to use
        context_files: Optional list of context files
        timeout: Timeout in seconds

    Returns:
        Parsed JSON response or error dict
    """
    result = invoke_subagent(
        prompt=prompt,
        model=model,
        context_files=context_files,
        timeout=timeout
    )

    if not result["success"]:
        return result

    parsed = parse_subagent_response(result["output"])
    return {
        "success": True,
        "data": parsed,
        "raw_output": result["output"]
    }
