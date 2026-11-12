"""LLM client wrapper for multi-provider LLM subprocess calls."""

import contextlib
import contextvars
import functools
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
from typing import Any, Dict, FrozenSet, Iterator, List, Optional, Sequence, Tuple, Union

from . import structured_output
from . import process_control
from . import process_capture
from . import prompt_channels
from .providers import private_home
from . import landlock_dispatch as _landlock
from . import readonly_audit as _readonly_audit_mod
from . import result_files as _result_files
from .metrics import describe_usage as _describe_usage
from .retry_ladder import STATUS_UNPARSEABLE
from .provider_registry import parse_model_spec, get_provider, get_provider_timeout
from .providers.base import (
    INCIDENTAL_LANE_FANOUT,
    PROFILE_GENERATE,
    SANDBOX_RUNG_UNSANDBOXED,
    JailContext,
    JailRequest,
    ReadOnlyInvocationRefused,
    StructuredOutputUnavailable,
    build_child_env,
    sandbox_rung_id,
)
# What a run means — the result dict, its error codes and every `details` key
# a child that ran carries — is read in `provider_outcome`. The names callers
# have always read off this module are re-exported from it.
from .provider_outcome import (  # noqa: F401 - re-exported, see above
    ANSWER_TEXT_KEY,
    ERROR_BINARY_NOT_FOUND,
    ERROR_FILE_NOT_FOUND,
    ERROR_PARSE_ERROR,
    ERROR_PROMPT_TOO_LONG,
    ERROR_PROMPT_UNSAFE,
    ERROR_SUBPROCESS_FAILED,
    ERROR_TIMEOUT,
    FAILURE_CATEGORY_KEY,
    FAILURE_JAIL_DENIED,
    MAX_ANSWER_TEXT_BYTES,
    MAX_LOG_LINE_BYTES,
    MAX_LOG_STREAM_BYTES,
    MAX_LOG_TAIL_LINES,
    MAX_LOG_TOTAL_BYTES,
    SALVAGE_TEXT_KEY,
    SANDBOX_BYPASSED,
    SANDBOX_FALLBACK_WORD_PREFIX,
    _CONTAINED_RUNG_IDS,
    _INCIDENTAL_RUNG_IDS,
    _READONLY_AUDIT_KEY,
    Capture,
    JailReadBack,
    _attach_answer_text,
    _attach_salvage_text,
    _attach_stdout_excerpt,
    _attach_usage,
    _bound_salvage_text,
    _bound_stream,
    _cut_bytes,
    _readonly_audit,
    _redact,
    _salvage_hook_text,
    generic_answer_text,
    outcome_from_capture,
    rejected_answer_category,
)
from . import probe_state as _probe_state
from . import json_extractor
from .json_extractor import generate_output_path, parse_file_content


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

    The whole context is also the dispatch's private-home scope
    (``private_home.dispatch_homes``): a per-slot config root an adapter's
    ``get_env`` makes while it is open is removed when it closes, after the
    adapter's own context (docs/development/providers.md#private-config-roots).
    """
    with private_home.dispatch_homes():
        # Unavailable I12: an adapter may also ask
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




#: A salvage request's record of *how* the run it came from was lost, and the
#: one value it takes today. Only a run cut by a deadline carries it: a salvaged
#: ``[]`` from such a run is refused (``task_result._salvage_gave_up``),
#: because a reviewer killed mid-review never said "I found nothing", while a
#: ``[]`` from a run that finished and then exited non-zero is still a genuine
#: empty review. Here because every lane that writes or reads a request
#: already imports this module, and ``ERROR_TIMEOUT`` is what decides it.
SALVAGE_FAILURE_KEY = "failure"
SALVAGE_FAILURE_TIMEOUT = "timeout"






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
        readonly_audit: The attempt's compact read-only verdict,
            rendered as one ``Readonly audit:`` header line — the verdict,
            never the stream it was computed on (which the ``STDOUT`` section
            below carries bounded, like any other).

    Returns:
        True if log was saved successfully, False otherwise

    Every rendered field is passed through the ``redact_text`` **first** and
    bounded by the caps **second**. This is the sink where all nine planted
    secret shapes landed on a *successful* run, and the sink that wrote a
    6,254,326 B log for one ``review-plan``.
    """
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Redact the fully rendered text, then cap it. Reversing
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




# ---------------------------------------------------------------------------
# The Lane A spawn: `subprocess.run`'s contract, plus the tree sweep
# ---------------------------------------------------------------------------

#: SIGTERM → SIGKILL grace for a stopped Lane A CLI and for each process group
#: its snapshot recorded. SIGTERM first because pi reaps its own detached shells
#: only from its SIGTERM handler; the bare SIGKILL `subprocess.run` sent skipped
#: it.
LANE_A_TERMINATE_GRACE_S = process_control.DEFAULT_TERMINATE_GRACE_S

#: Ceiling on the post-sweep drain, and the grace a CLI's pipes get to reach end
#: of file once it has exited: the shared ``process_capture.DRAIN_S``. A
#: grandchild the sweep did not reach can keep an inherited pipe open for ever,
#: so a drain that outlives this returns the output already read.
LANE_A_DRAIN_S = process_capture.DRAIN_S

#: Per-stream capture bound, the executor's figure. A stdout past it is never
#: parsed (``process_capture.oversized_stream_message``); a stderr past it is
#: kept truncated.
LANE_A_MAX_STREAM_BYTES = process_capture.MAX_STREAM_BYTES

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

#: ``STATUS_CONTROL_C_EXIT``: the Windows spelling of "died of Ctrl-C". Windows has no
#: signal to die of, so a return code there is
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
    and is terminated right after the CLI. Never raises: teardown
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


#: :attr:`process_control.TreeSweep.cli` verdicts that saw the CLI exit.
_CLI_SEEN_TO_EXIT = ("exited", "terminated", "killed")


def _sweep_confirmed(sweep: Optional[process_control.TreeSweep]) -> bool:
    """Did *sweep* confirm the CLI and everything it reached stopped?

    The CLI was seen to exit, its Windows job (if any) ended, and every process
    group the sweep met has a kill verdict that confirms a stop under the
    executor's rule (``process_control.unconfirmed_kill``). A sweep that
    raised (``None``), or a rule that cannot be read, confirms nothing.
    """
    if sweep is None or sweep.cli not in _CLI_SEEN_TO_EXIT:
        return False
    if sweep.job == process_control.JOB_FAILED:
        return False
    if not sweep.groups:
        return True
    try:
        return all(process_control.unconfirmed_kill(verdict) is None
                   for verdict in sweep.groups.values())
    except Exception:  # noqa: BLE001 - unknown is unconfirmed
        return False


def _stop_and_note(
    proc: "subprocess.Popen[Any]", job: Optional[process_control.TreeJob] = None,
) -> Optional[process_control.TreeSweep]:
    """:func:`_stop_cli_tree`, and its verdict recorded for the dispatch
    (``process_control.note_stop``): a private home the CLI was lent outlives
    a stop that is not confirmed (docs/development/providers.md#private-config-roots).
    Never raises, like the stop."""
    sweep = _stop_cli_tree(proc, job)
    try:
        confirmed = _sweep_confirmed(sweep)
    except Exception:  # noqa: BLE001 - see above
        confirmed = False
    process_control.note_stop(proc, confirmed)
    return sweep


def _drain_after_stop(
    proc: Any, expired: subprocess.TimeoutExpired
) -> Tuple[Any, Any]:
    """Everything the stopped CLI wrote, without ever hanging on a survivor.

    *proc* is the CLI's :class:`process_capture.PipeCapture`. The second
    ``communicate()`` returns the whole capture (what the first call had read
    before the deadline included). If even that blocks, the newest partial
    capture is used and the pipes are let go.
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
    stream_watch: Optional[process_capture.StreamWatch] = None,
    **popen_kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run one Lane A provider CLI: ``subprocess.run``'s contract, and its tree.

    Same arguments, same ``CompletedProcess``, and the same ``TimeoutExpired``
    carrying the output so far — the ``TimeoutExpired`` handler in
    :func:`invoke_with_provider` and the salvage read that partial stdout. What
    changes is what a stop does. ``subprocess.run`` SIGKILLs the direct child
    only, which skips pi's own cleanup and leaves every child in a session of its
    own running (pi's detached shells, and a ``timeout`` inside one, which leads
    a group of its own). Here, on the deadline:

    1. the CLI's descendants are snapshotted while it is still alive;
    2. the CLI is SIGTERMed, given :data:`LANE_A_TERMINATE_GRACE_S`, then
       SIGKILLed; every snapshotted process group is swept through
       ``process_control.terminate_timed_out``, and whether that confirmed the
       stop is recorded for the dispatch (:func:`_stop_and_note`);
    3. a bounded second ``communicate()`` collects the rest of the output; and
    4. a ``TimeoutExpired`` is re-raised with it and with the per-group verdicts
       as ``tree_sweep``, which the handler writes into the provider log.

    The pipes are read by ``process_capture.PipeCapture``: at most
    :data:`LANE_A_MAX_STREAM_BYTES` per stream, and the wait ends when the CLI
    exits (plus a drain of :data:`LANE_A_DRAIN_S` at most), not when the last
    process holding an inherited pipe closes it. The streams that passed the
    bound ride out as ``capped_streams`` on the ``CompletedProcess`` and on the
    ``TimeoutExpired``. A pipe still held once the CLI exited is held by what
    it left running: before this call returns, that is swept exactly as on
    the deadline (:func:`_stop_and_note`). A sweep that is confirmed and lets
    go of the pipes leaves the CLI's answer standing, and what it did rides
    out as ``pipe_held`` (:func:`_held_pipe_record`; ``""`` when no pipe was
    held); otherwise a process the sweep did not reach still holds the
    output, or may, and the call ends as the deadline's ``TimeoutExpired``,
    as it did when that process held the pipe until the deadline, with the
    words saying so as ``held_pipe``.

    *stream_watch* (the adapter's ``stream_watch()``, passed only when it
    declares one) watches stdout as it arrives; when it asks for a stop, the
    CLI is stopped exactly as on the deadline and the ``TimeoutExpired``
    carries the watch's reason as ``stream_stop`` (``None`` on a deadline).

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
    that exits on its own leaves whatever it started running, as on POSIX,
    unless it still holds the CLI's pipes (above).
    """
    if capture_output:
        popen_kwargs["stdout"] = subprocess.PIPE
        popen_kwargs["stderr"] = subprocess.PIPE
    if input is not None:
        popen_kwargs["stdin"] = subprocess.PIPE
    proc, job = process_control.popen_tree(cmd, **popen_kwargs)
    streams: Optional[process_capture.PipeCapture] = None
    held_sweep = ""
    try:
        with process_control.live_cli_registry.tracking(proc, job):
            try:
                # A pipe still held once the CLI exited is what it left
                # running: swept as on the deadline before this call returns,
                # so the slot's write check after it sees every write it made
                # (docs/development/runtime.md#process-primitives).
                streams = process_capture.PipeCapture(
                    proc, max_bytes=LANE_A_MAX_STREAM_BYTES, grace_s=LANE_A_DRAIN_S,
                    watch=stream_watch,
                    on_held=lambda _held: _stop_and_note(proc, job),
                )
                stdout, stderr = streams.communicate(input=input, timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                sweep = _stop_and_note(proc, job)
                out, err = _drain_after_stop(streams, exc)
                expired = subprocess.TimeoutExpired(
                    proc.args, exc.timeout, output=out, stderr=err
                )
                expired.tree_sweep = sweep
                expired.capped_streams = streams.capped
                expired.stream_stop = streams.stream_stop
                raise expired from None
            except BaseException:
                _stop_and_note(proc, job)
                raise
            if streams.held_stopped:
                held_sweep, confirmed = _held_pipe_record(proc, streams)
                if not confirmed:
                    expired = subprocess.TimeoutExpired(
                        proc.args, timeout, output=stdout, stderr=stderr
                    )
                    expired.tree_sweep = streams.held_stop
                    expired.capped_streams = streams.capped
                    expired.stream_stop = None
                    expired.held_pipe = held_sweep
                    raise expired
            elif _stopped_from_outside(proc.returncode):
                # Dead already, and its detached children may not be: only the
                # registry's snapshot still links them to this slot (on Windows,
                # its job).
                _stop_and_note(proc, job)
    finally:
        # After `tracking` has unregistered the CLI, so a sweep can no longer
        # be terminating the job through the handle closed here.
        try:
            if streams is not None:
                streams.close()
            _release_pipes(proc)
        finally:
            if job is not None:
                job.close()
    completed = subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)
    completed.capped_streams = streams.capped
    completed.pipe_held = held_sweep
    return completed


def _held_pipe_record(
    proc: "subprocess.Popen[Any]", streams: process_capture.PipeCapture,
) -> Tuple[str, bool]:
    """What the deadline's sweep did once the CLI exited while a process it
    started still held its output (the capture's ``on_held``,
    :func:`_stop_and_note`), and whether it confirmed the stop: the sweep
    confirmed every group it met (:func:`_sweep_confirmed`) and the pipes
    were let go. Confirmed, the text is the slot's record
    (``Capture.pipe_held``). Not confirmed, it is the words the call's
    timeout carries: a pipe still held is held by a process the sweep did not
    reach, which may still run (the private home it was lent is kept,
    ``process_control.note_stop``), and how to look for it; a ``WARNING``
    says so too. Never raises."""
    sweep = streams.held_stop
    try:
        line = sweep.describe() if sweep is not None else "the sweep failed"
        confirmed = _sweep_confirmed(sweep)
    except Exception:  # noqa: BLE001 - a record never fails the slot
        line, confirmed = "the sweep could not be read", False
    held = " and ".join(sorted(streams.still_held))
    if not held and confirmed:
        return ("the CLI exited while a process it started still held its output; "
                f"swept before the slot's checks: {line}"), True
    process_control.note_stop(proc, False)
    text = (
        f"the CLI exited (code {proc.returncode}) while a process it started held "
        f"its output, so what it started was swept as at a timeout ({line})"
        + (f", but its {held} was still held after that: a process the sweep did "
           f"not reach holds it and may still be running" if held
           else ", which could not be confirmed")
        + "; the call was ended as a timeout. Look for it with: ps -eo "
        "pid,ppid,pgid,sid,lstart,args (one in a session of its own has init or the "
        "user's service manager as its parent and started during this run)"
    )
    print(f"WARNING: pid {getattr(proc, 'pid', None)}: {text}.", file=sys.stderr,
          flush=True)
    return text, False


def _capped_streams(outcome: Any) -> FrozenSet[str]:
    """The streams :func:`_run_provider_cli` cut at its bound; none for a
    stand-in that returns a plain ``CompletedProcess``."""
    capped = getattr(outcome, "capped_streams", None)
    return frozenset(capped) if capped else frozenset()




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
# A fan-out slot on the plugin's Landlock jail
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
    for name in ("_VERSION_CACHE", "_PROBE_VERSION_CACHE"):
        cache = getattr(_probe_state, name, None)
        if isinstance(cache, dict):
            value = cache.get(provider_name)
            if value and value != "unknown":
                return str(value)
    return ""


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
        "where": "spawn", "line": _landlock.redacted_excerpt(message),
        "path": _landlock.redacted_excerpt(path) or None,
        "class": _landlock.JAIL_CLASS_JAIL, "reason": reason,
    }
    details: Dict[str, Any] = {
        "provider": provider_name,
        "model": model,
        "failure_reason": failure_reason,
        "retryable": False,
    }
    if failure_reason == FAILURE_JAIL_DENIED:
        evidence["notice"] = _landlock.jail_denied_text(
            spec=f"{provider_name}:{model}", rung=rung, evidence=evidence,
            allow_list="", installed=_cached_cli_version(provider_name),
            lane=INCIDENTAL_LANE_FANOUT,
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




def _home_check_record(
    change: Any, before: Any, after: Any, *, codex_home: str, live: set,
) -> Optional[Dict[str, Any]]:
    """One jailed child's ``details["home_check"]``: only when the home's
    security-relevant set changed or a foreign trust table appeared, else
    ``None``. Shared by the invoker's own read-back and
    :func:`raised_attempt_home_checks`, so both name a change the same way."""
    if change is None or not (change.changed or change.foreign_trust):
        return None
    record = change.to_dict()
    if _landlock.HOME_CONFIG in change.changed:
        names = _config_key_names(
            getattr(before, "config_text", None),
            getattr(after, "config_text", None),
        )
        if names:
            record["config_keys"] = names
    record["home"] = _landlock.render_home(codex_home)
    record["other_live_children"] = len(live)
    return record


@dataclass
class _ArmedHome:
    """What one jailed child's home check needs once its attempt has raised:
    the home as the child saw it, the run cwd its trust table is expected
    for, the invoker's before-snapshot, and the set of same-provider children
    live beside it (``_live_child``'s, frozen once the child is gone)."""

    codex_home: str
    cwd: str
    before: Any
    live: set


#: The jailed children the current fan-out attempt armed, or ``None`` outside
#: :func:`armed_homes_window`. ``asyncio.to_thread`` copies the context into
#: the dispatch's worker thread, so the invoker appends to the lane's list.
_ARMED_HOMES: "contextvars.ContextVar[Optional[List[_ArmedHome]]]" = (
    contextvars.ContextVar("multi_llm_armed_homes", default=None)
)


@contextlib.contextmanager
def armed_homes_window() -> Iterator[List[_ArmedHome]]:
    """Collect every jailed child one review fan-out attempt arms.

    An attempt that raises returns no ``details``, so its ``home_check`` is
    lost with it; the lane wraps each attempt in this window and, only on a
    raise, hands the list to :func:`raised_attempt_home_checks`. Nothing is
    read or written on the normal path."""
    armed: List[_ArmedHome] = []
    token = _ARMED_HOMES.set(armed)
    try:
        yield armed
    finally:
        _ARMED_HOMES.reset(token)


def _note_armed_home(jail: "_JailedAttempt") -> None:
    """Record a jailed child about to spawn in the lane's window, if any."""
    armed = _ARMED_HOMES.get()
    if armed is not None and jail.context is not None:
        armed.append(_ArmedHome(
            codex_home=jail.context.codex_home, cwd=jail.cwd,
            before=jail.home_before, live=jail.live,
        ))


def raised_attempt_home_checks(armed: Sequence[_ArmedHome]) -> List[Dict[str, Any]]:
    """The home check of every jailed child an attempt that raised had armed.

    The comparison the invoker makes after a child exits, against its own
    before-snapshot, so the record is the one the attempt would have returned
    (only when something changed). A home that cannot be compared (no
    before-snapshot, or none after: unreadable or gone) is recorded as
    ``unaudited``: the attempt's own check never ran, so the lane fails it
    closed (F1 Limits; see the home-check block in
    ``review_orchestrator_base``). Blocking; the lane hands it to a thread.
    """
    records: List[Dict[str, Any]] = []
    for entry in armed:
        after = None
        if entry.before is not None:
            try:
                after = _landlock.home_snapshot(entry.codex_home, [entry.cwd])
            except Exception:  # noqa: BLE001 - recorded as unaudited below
                after = None
        change = _landlock.compare_home(entry.before, after)
        if change is None:
            records.append({
                "home": _landlock.render_home(entry.codex_home),
                "changed": [], "config_keys": [], "foreign_trust": [],
                "other_live_children": len(entry.live), "unaudited": True,
            })
            continue
        record = _home_check_record(
            change, entry.before, after,
            codex_home=entry.codex_home, live=entry.live,
        )
        if record is not None:
            records.append(record)
    return records


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
    after = None
    try:
        after = _landlock.home_snapshot(context.codex_home, [jail.cwd])
        change = _landlock.compare_home(jail.home_before, after)
    except Exception:  # noqa: BLE001 - a check never ends a slot
        change = None
    record = _home_check_record(
        change, jail.home_before, after,
        codex_home=context.codex_home, live=jail.live,
    )
    if record is not None:
        details["home_check"] = record
    try:
        denials = _landlock.jail_denied_edits(stdout or "", context, cwd=jail.cwd)
        record = denials.to_dict()
        record["total"] = denials.total
        record["paths"] = denials.named_paths()
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
        "notice": _landlock.jail_denied_text(
            spec=f"{provider_name}:{model}", rung=jail.rung,
            evidence=evidence.to_dict(), allow_list=allow, installed=installed,
            lane=INCIDENTAL_LANE_FANOUT,
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


@dataclass
class PreparedDispatch:
    """One fan-out dispatch ready to spawn (:func:`prepare_dispatch`).

    ``cleanup`` holds what setup entered (the adapter's dispatch context, a
    schema sidecar, a jailed attempt's scratch directory); the caller closes it
    once the child is done, on every outcome. ``start_time`` is when setup
    began composing the child's environment: a run's ``duration_seconds`` is
    measured from it.
    """

    provider: Any
    provider_name: str
    model: str
    timeout: Any
    cmd: List[str]
    stdin_text: Optional[str]
    env: Optional[Dict[str, str]]
    cwd: Optional[str]
    schema: Any
    structured_marker: str
    jail: Optional[_JailedAttempt]
    start_time: float
    cleanup: contextlib.ExitStack

    def jail_read_back(self) -> Optional[JailReadBack]:
        """The jail's read-back for this attempt, or ``None`` off the jail."""
        if self.jail is None:
            return None
        return functools.partial(
            _jail_after_child, jail=self.jail,
            provider_name=self.provider_name, model=self.model,
        )


def _phase_schema(
    provider: Any, schema_phase: str, stack: contextlib.ExitStack
) -> Tuple[Any, str]:
    """The pre-dispatch read of ``schema_phase``'s schema, as ``(schema,
    marker)``; raises ``structured_output.SchemaConfigError``.

    Lane A only, and no production caller passes ``schema_phase`` (W1, deferred
    by the repository owner; see :func:`invoke_with_provider`'s docstring).
    ``schema_for_dispatch`` consults ``structured_output_support``: an adapter
    that declares ``False``, or a schema this CLI provably cannot carry, comes
    back ``None`` and the phase runs its prompt-level JSON path.
    """
    schema, structured_marker = structured_output.schema_for_dispatch(
        provider, schema_phase
    )
    if schema is not None and provider.structured_output_transport == "file":
        # One `mkdtemp` per invocation, written by the CALLER: adapters are
        # singletons under a concurrent fan-out and cannot hold this. The
        # stack's `close()` removes it on success, on timeout, on kill-path
        # teardown and on exception.
        schema = stack.enter_context(structured_output.schema_sidecar(schema))
    return schema, structured_marker


def prepare_dispatch(
    prompt: str,
    model_spec: str,
    *,
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    prompt_transport: Optional[str] = None,
    anchor: Optional[Union[str, Path]] = None,
    schema_phase: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
) -> Union[PreparedDispatch, Dict[str, Any]]:
    """Everything :func:`invoke_with_provider` does before the spawn.

    Resolves the provider, the timeout, the transport, the phase schema, the
    plugin's jail grant, the argv and the child's environment, with the
    arguments :func:`invoke_with_provider` documents. Returns the prepared
    dispatch, or the refusal result when it cannot start (an unknown or
    unavailable provider, an unsupported transport, a refused dispatch
    context, a schema or read-only refusal, a Windows command line it will not
    risk, a jail it cannot grant), with nothing spawned and every context
    entered so far released.
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

    # M10 — a **bool** consumer, and it stays one. The gate is still
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
    # The pre-dispatch read, and M7's one call site. `schema_phase=None`
    # skips all of it, so every existing caller renders the same argv it always
    # did. `schema_for_dispatch` is what consults `structured_output_support`:
    # an adapter that declares `False` — or a schema this CLI provably cannot
    # carry — comes back `None` here and the phase runs its prompt-level JSON
    # path, marked `recovered`/`unvalidated` and never `native`.
    schema = None
    structured_marker = structured_output.MARKER_UNVALIDATED
    # The adapter's run-scoped dispatch context is entered BEFORE argv
    # is built, because argv and env are rendered from the same context state
    # (opencode's `--pure` pairs with its `XDG_CONFIG_HOME` redirect and neither
    # is emitted without the other). It rides the same `ExitStack` as the schema
    # sidecar, so it is left on success, on timeout, on kill-path teardown and on
    # exception alike — the `finally` half of the lifecycle, with the
    # adapter's own `atexit` sweep as the backstop.
    # Every post-entry setup step — the schema read, the argv build, the
    # executable resolution and the env composition — runs INSIDE this `with`,
    # so a raise anywhere in it unwinds the context here rather than leaving
    # opencode's active context and its config-home reference behind for the
    # `atexit` sweep to find. Only once setup has survived is the live stack
    # handed to the prepared dispatch (`pop_all`), whose owner from that point
    # on is `invoke_with_provider`'s `finally`.
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
                schema, structured_marker = _phase_schema(
                    provider, schema_phase, setup_cleanup
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

        # Unavailable F1: a slot on a
        # wrapping rung (the plugin's own Landlock jail) gets its grant here,
        # at the spawn site, once per attempt — order steps 1-2 of "How a
        # dispatch receives its grant". The read-only request comes from this
        # function's own `cwd` (a fan-out slot never carries a write scope),
        # and the attempt's scratch directory rides `setup_cleanup`, so a
        # return before the spawn removes it here and a spawned child's is
        # removed by `invoke_with_provider`'s `finally`, after `_run_provider_cli` swept
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

        # `timeout_s=effective_timeout` is L5's one call site: the number is
        # already resolved here, so an adapter with an internal cutoff of its own
        # (agy's `--print-timeout`) can hold it under the deadline this same call
        # passes to `_run_provider_cli`, instead of hardcoding a value that has to
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
            # The sixth case: fails BEFORE spawn, so no partial argv reaches
            # the CLI. A configuration error, never retried. The same for an
            # adapter refusing an invocation the user's own config makes unsafe
            # (aider with
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
        # `resolve_env`, not `get_env`: the Lane A fan-out IS the `generate` profile, so
        # it gets the global non-interactive git block plus the scoped
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
        # stack so leaving this `with` releases nothing, and the caller's
        # `finally` owns them for the rest of the dispatch.
        return PreparedDispatch(
            provider=provider, provider_name=provider_name, model=model,
            timeout=effective_timeout, cmd=cmd, stdin_text=stdin_text, env=env,
            cwd=cwd, schema=schema, structured_marker=structured_marker,
            jail=jail, start_time=start_time, cleanup=setup_cleanup.pop_all(),
        )


def _run_dispatch(prepared: PreparedDispatch) -> Capture:
    """Spawn the prepared CLI and capture what it wrote.

    ``_run_provider_cli``'s contract: a deadline raises ``TimeoutExpired``
    carrying the output so far, a failed start ``OSError``.
    """
    jail = prepared.jail
    # `subprocess.run`'s contract and arguments, but a `Popen` underneath: on
    # the deadline, a Ctrl-C or an abort the CLI is SIGTERMed first and every
    # process group it spawned is swept, instead of `run`'s bare SIGKILL of the
    # CLI alone (D3.3; see `_run_provider_cli`). On Windows the CLI runs in a
    # Job Object of its own, and the stop ends that job. Registered for exactly
    # as long as the child runs, so a jailed slot's `[CODEX_HOME_CHECK]` line
    # can say how many other children of this provider shared its window (F1
    # Limits, 2026-09-30).
    with _live_child(prepared.provider_name) as live_overlap:
        if jail is not None:
            jail.live = live_overlap
            # For the lane, in case this attempt raises before its
            # `details["home_check"]` is returned (armed_homes_window).
            _note_armed_home(jail)
        # Passed only when the adapter declares a watch, so every other
        # adapter's spawn call (and a test's `subprocess.run` stand-in) is
        # unchanged (docs/development/providers.md#a-cli-that-loops).
        watch = process_capture.provider_watch(prepared.provider)
        completed = _run_provider_cli(
            prepared.cmd,
            capture_output=True,
            text=True,
            # Provider output is not under our control: errors="replace" is
            # lossy for non-UTF-8 bytes but guarantees a total decode — the
            # standard choice for LLM/tool output. surrogateescape rejected
            # (lone surrogates raise on downstream UTF-8 re-encode);
            # backslashreplace rejected (noisier in model-visible output).
            encoding="utf-8",
            errors="replace",
            timeout=prepared.timeout,
            env=prepared.env,
            cwd=prepared.cwd,
            # Under the argv transport the one provider that reads stdin is
            # aider, which reads its decline supply there (D4.2: `s` answers to
            # the "Add file to the chat?" prompts, handed back as `stdin_text`
            # and closed at EOF once written). For every other one, closing it
            # prevents CLIs that poll stdin for piped input (e.g. agy) from
            # blocking forever when the orchestrator's stdin is a non-EOF pipe.
            # Under the stdin transport the prompt IS the child's stdin, and it
            # is closed at EOF once written, which those CLIs treat the same way.
            **(
                {"input": prepared.stdin_text}
                if prepared.stdin_text is not None
                else {"stdin": subprocess.DEVNULL}
            ),
            **({"stream_watch": watch} if watch is not None else {}),
        )
    held = getattr(completed, "pipe_held", "")
    return Capture(
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
        duration=time.time() - prepared.start_time,
        capped_streams=_capped_streams(completed),
        stream_bound=LANE_A_MAX_STREAM_BYTES,
        pipe_held=held if isinstance(held, str) else "",
    )


def _decoded_partial(stream: Any) -> str:
    """A ``TimeoutExpired``'s partial stream as text: it may carry ``str`` or
    ``bytes``, decoded with the run's own utf-8/replace policy."""
    if stream is None:
        return ""
    if isinstance(stream, str):
        return stream
    return stream.decode("utf-8", errors="replace")


def _timed_out_capture(expired: subprocess.TimeoutExpired, start_time: float) -> Capture:
    """A deadline kill's capture: what ``_run_provider_cli`` re-raised with, the
    bytes read before the deadline plus what the bounded post-sweep drain
    collected, what the sweep did, and the stdout watch's reason when it, not
    the deadline, asked for the stop."""
    duration = time.time() - start_time
    stop = getattr(expired, "stream_stop", None)
    held = getattr(expired, "held_pipe", "")
    return Capture(
        stdout=_decoded_partial(expired.stdout),
        stderr=_decoded_partial(expired.stderr),
        timed_out=True,
        duration=duration,
        capped_streams=_capped_streams(expired),
        stream_bound=LANE_A_MAX_STREAM_BYTES,
        tree_sweep=_describe_tree_sweep(expired),
        stream_stop=stop if isinstance(stop, str) and stop else None,
        pipe_held=held if isinstance(held, str) else "",
    )


def _log_outcome(
    log_file: Union[str, Path],
    prompt: str,
    prepared: PreparedDispatch,
    capture: Capture,
    result: Dict[str, Any],
) -> None:
    """The provider log for ``result``: ``outcome_from_capture``'s ``log``
    writer, called where each path logs. It is never called for an exit 0 the
    caller defers, which gets ``details["_deferred_log"]`` and writes the one
    entry once it knows which channel answered."""
    model = f"{prepared.provider_name}:{prepared.model}"
    if capture.launch_error is not None:
        _save_log(
            log_file=log_file, model=model, prompt=prompt, stdout="",
            stderr=capture.launch_error, returncode=-1, success=False,
            error=result["error"], duration_seconds=capture.duration,
        )
        return
    if capture.timed_out:
        # Plus what the sweep did to the CLI and to each process group it had
        # spawned, so a `survived` group is named where the timeout is (D3.3).
        returncode, error = -1, f"{result['error']}{capture.tree_sweep}"
    elif capture.exit_code != 0:
        returncode, error = capture.exit_code, result["error"]
    else:
        returncode, error = capture.exit_code, result.get("error")
    if capture.pipe_held and not capture.timed_out:
        # What the sweep of the CLI's pipe holders did, beside how it ended
        # (a timeout's error line names it already).
        error = f"{error}; {capture.pipe_held}" if error else capture.pipe_held
    _save_log(
        log_file=log_file, model=model, prompt=prompt, stdout=capture.stdout,
        stderr=capture.stderr, returncode=returncode,
        success=result.get("success", False), error=error,
        duration_seconds=capture.duration,
        readonly_audit=result["details"].get(_READONLY_AUDIT_KEY),
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
    parsing with consistent error reporting, in three steps:
    :func:`prepare_dispatch` (setup, and every refusal before a spawn), the
    spawn, and :func:`utils.provider_outcome.outcome_from_capture` (the result,
    read from what the spawn captured), which writes the provider log through
    :func:`_log_outcome` at the point each path logs
    (docs/development/providers.md#reading-a-capture).

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
            launches a different binary than the project configured.
        schema_phase: the phase name (``review-plan``, ``code-review``, …),
            or ``None``. **``None`` is the default and changes nothing**: no
            schema is resolved, no flag is emitted and the returned dict is
            byte-for-byte what it has always been.

            When set, this is the "the caller reads the flag before
            dispatch" leg: the phase's schema file is resolved through
            ``utils.structured_output``, the adapter's
            ``structured_output_support`` decides whether it is passed at all,
            codex's sidecar is written and removed in a ``finally``, and
            The failure policy is applied to the envelope afterwards. The
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
            progress. Where the verdict sits:
            docs/development/providers.md#reading-a-capture (the schema verdict).
        _defer_parse_failure_log: Internal (§Fix1/F13). When the child
            exited 0, writing the log here (if ``log_file`` is set) — before
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
            failed — is known, and always carries `Result source:`. The
            capture rides back with no ``log_file`` too: the caller reads a
            rejected stdout answer's verdict off it
            (``provider_outcome.rejected_answer_category``). A hard
            failure (binary not found, timeout, non-zero exit) still logs
            immediately, unaffected by this flag — there is no channel choice
            to wait for.
        sandbox_fallback: The fan-out's D6 override: the rung id
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

            **The plugin's own jail** (``plugin-landlock`` F1, 2026-09-30):
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
            answer text.
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
    prepared = prepare_dispatch(
        prompt, model_spec, timeout=timeout, cwd=cwd,
        prompt_transport=prompt_transport, anchor=anchor,
        schema_phase=schema_phase, sandbox_fallback=sandbox_fallback,
    )
    if not isinstance(prepared, PreparedDispatch):
        return prepared
    read = functools.partial(
        outcome_from_capture, prepared.provider,
        provider_name=prepared.provider_name, model=prepared.model,
        timeout=prepared.timeout, sandbox_fallback=sandbox_fallback,
        want_answer_text=want_answer_text, schema=prepared.schema,
        schema_phase=schema_phase, structured_marker=prepared.structured_marker,
        jail=prepared.jail_read_back(),
        defer_log=_defer_parse_failure_log,
        log=(
            functools.partial(_log_outcome, log_file, prompt, prepared)
            if log_file else None
        ),
    )
    try:
        # The reading of an exit shares the spawn's `try`: whatever raises out
        # of either is handled the same way.
        try:
            return read(_run_dispatch(prepared))
        except subprocess.TimeoutExpired as expired:
            return read(_timed_out_capture(expired, prepared.start_time))
        except OSError as exc:
            return read(Capture(
                launch_error=str(exc),
                launch_not_found=isinstance(exc, FileNotFoundError),
                duration=time.time() - prepared.start_time,
            ))
    finally:
        # Codex's per-invocation schema directory is removed in a
        # `finally` so it is cleaned up on success, on timeout, on kill-path
        # teardown and on exception alike, and so are the adapter's dispatch
        # context and a jailed attempt's scratch directory. A no-op for what
        # was never entered.
        prepared.cleanup.close()


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
# The names that moved to utils/prompt_channels.py
# ---------------------------------------------------------------------------

#: Every top-level name of :mod:`utils.prompt_channels`, the prompt text and
#: diff-access rendering split out of this module. They are read-only
#: re-exports: reading one here returns that module's current binding, and
#: ``dir()`` lists them. Nothing is copied into this module, so a patch of the
#: owner shows through here; a write here only shadows the name in this module
#: and reaches no code, which ``tests/test_llm_client_moved_names.py`` refuses.
_MOVED: Dict[str, Tuple[str, ...]] = {
    "prompt_channels": (
        "DIFF_ACCESS_NO_SHELL_PARTIAL",
        "DIFF_ACCESS_NO_SHELL_TEXT",
        "DIFF_ACCESS_PINNED_NO_SHELL_NOTE",
        "DIFF_ACCESS_PINNED_SHELL_PARTIAL",
        "DIFF_ACCESS_PINNED_SHELL_TEXT",
        "DIFF_ACCESS_SHELL_PARTIAL",
        "DIFF_ACCESS_SHELL_TEXT",
        "DIFF_ACCESS_UNMEASURED_PARTIAL",
        "DIFF_ACCESS_UNMEASURED_TEXT",
        "DiffAccess",
        "FILE_OUTPUT_LOCATION",
        "GENERATE_READ_SCOPES",
        "INLINE_CONTEXT_PLAN_LABEL",
        "INLINE_DIFF_CAP_BYTES",
        "INLINE_MANIFEST_LABEL",
        "INLINE_PROMPT_CAP_BYTES",
        "STDOUT_OUTPUT_LOCATION",
        "WORKING_LIMITS_BLOCK",
        "_INLINE_HEAD_BY_SCOPE",
        "_INLINE_HEAD_TAIL",
        "_INLINE_HEAD_TAIL_CONTEXT_PLAN",
        "_INLINE_HEAD_TAIL_REST",
        "_INLINE_SHELL_BY_STATE",
        "_MANIFEST_DIFF_REF_RE",
        "_MANIFEST_SENTENCE",
        "_PINNED_DRIFT_NAMED",
        "_inline_block",
        "_is_root_base",
        "_lies_within",
        "_pinned_opening",
        "_pinned_rule",
        "_read_inline_text",
        "_render_inline_diff_access",
        "_render_pinned_diff_access",
        "render_diff_access",
        "render_output_location",
        "render_working_limits",
    ),
}
_MOVED_TO: Dict[str, str] = {
    name: module for module, names in _MOVED.items() for name in names
}


def __getattr__(name: str) -> Any:
    """A moved name, read from the module that defines it now."""
    owner = _MOVED_TO.get(name)
    if owner is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return getattr(globals()[owner], name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> List[str]:
    """This module's own names and the moved ones it re-exports."""
    return sorted({*globals(), *_MOVED_TO})


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
        "output_location": prompt_channels.render_output_location(
            output_json_path, model_spec, anchor=anchor
        ),
        # The minutes this call will really be allowed: a missing `timeout` is
        # resolved exactly as `invoke_with_provider` resolves it below, so the
        # deadline the prompt states is the one the kill honours. A template
        # without the placeholder ignores the key (`str.format` drops extras).
        "working_limits": prompt_channels.render_working_limits(
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
    ceiling (:data:`~utils.prompt_channels.INLINE_PROMPT_CAP_BYTES`) before
    anything is spawned.
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
    attempt's baseline, and the slot was recorded failed beside its own answer.
    """

    phase_dir = generate_output_path(Path(output_dir), "output", phase, model_spec).parent
    return _result_files.snapshot_candidates(phase_dir)


#: ``(st_dev, st_ino, st_size, st_mtime_ns)`` of a slot's requested result file
#: when the slot started, or ``()`` when there was none. Where one is
#: ``Optional``, ``None`` is a stamp that could not be read.
ResultFileStamp = Tuple[int, ...]


def _result_file_stamp(path: Union[str, Path]) -> Optional[ResultFileStamp]:
    """What moves when anything writes *path*: its identity, size and mtime.

    ``()`` only when the file is shown absent; ``None`` when its metadata
    cannot be read, which says nothing about whether it is there, nor whether
    it moved: every comparison of stamps keeps that open, and so never takes
    an earlier answer for gone or for this call's (docs/development/
    review-results.md, "Withheld slot answers"). Followed through a link, as
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
    except FileNotFoundError:
        return ()
    except OSError:
        return None
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def requested_result_baseline(
    output_dir: Union[str, Path],
    phase: str,
    model_spec: str,
) -> Optional[ResultFileStamp]:
    """The stamp of the file :func:`invoke_with_file_output` asks *model_spec* for, now.

    ``()`` only when the file is shown absent; ``None`` when its metadata
    cannot be read, which says nothing about whether it is there
    (:func:`_result_file_stamp`). A slot that compares two of these to decide
    an earlier answer is gone keeps it withheld on ``None``
    (docs/development/review-results.md, "Withheld slot answers"); handed to
    :func:`invoke_with_file_output` as ``requested_baseline``, ``None`` makes
    each attempt take its own, and one it cannot take reads no file at the
    requested name.

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

    return _result_file_stamp(
        generate_output_path(Path(output_dir), "output", phase, model_spec)
    )


#: :func:`_set_aside_unchanged_result`: the file is the earlier round's, unchanged.
_RESULT_FILE_STALE = "stale"

#: :func:`_set_aside_unchanged_result`: a stamp could not be read, so nothing
#: shows the file was written after the slot started.
_RESULT_FILE_UNVERIFIED = "unverified"


def _set_aside_unchanged_result(
    path: Path, baseline: Optional[ResultFileStamp],
) -> Optional[str]:
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

    Returns why *path* is not to be read, or ``None`` when it is this call's to
    read: it was absent when the slot started, is absent now (the read then
    reports it missing), or has changed since. :data:`_RESULT_FILE_STALE` when
    it is that earlier round's file, even when the rename failed (which warns
    on stderr), because the caller's question is whether to read it, and the
    answer is no either way. :data:`_RESULT_FILE_UNVERIFIED` when either stamp
    could not be read (*baseline* ``None``, or this one): nothing shows the
    file was written since the slot started, so it may still be an earlier
    answer, one whose safety checks failed among them; it is left in place,
    neither read nor renamed (docs/development/review-results.md, "Withheld
    slot answers").
    """
    if baseline == ():
        return None
    now = _result_file_stamp(path)
    if now == ():
        return None
    if baseline is None or now is None:
        return _RESULT_FILE_UNVERIFIED
    if now != baseline:
        return None
    _result_files.set_aside_stale_result(path)
    return _RESULT_FILE_STALE


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
    after the directory scan, or before the rename, is never adopted.
    """

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
    :func:`~utils.prompt_channels.render_output_location`). Both channels are
    read below either way.

    Fallback strategy:
    1. Primary: Read from output file (with extraction fallback for code blocks)
       — only a file that appeared or changed since the slot started
       (``requested_baseline``). One that was there before and is unchanged is
       a previous round's answer, not this call's: it is not read, it is
       renamed ``<name>.stale-earlier-run`` so nothing after this call reads
       it either (:func:`_set_aside_unchanged_result`), and the steps below
       run as if it were missing. One that a stamp which could not be read
       leaves unproven (the baseline's or the one after the call) is not read
       either, and is left in place (``source: unverified``): it may be an
       earlier answer, one whose safety checks failed among them
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
            verbatim to :func:`invoke_with_provider`
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
            takes it here, at the start of this call (a slot of one attempt);
            when that stamp cannot be read either, no file at the requested
            name is read on this call.

    Returns:
        Dict with keys:
        - 'success': bool indicating overall success
        - 'data': Parsed JSON data (if successful)
        - 'source': Where JSON came from ('file', 'file_extracted', 'stdout_fallback')
        - 'output_file': Path to the output file (if generated)
        - 'error': Error message (if failed)
        - 'file_error': File-specific error (if file read failed, or the file
          was left unread as older than the slot, or as not shown newer)
        - 'details': Provider execution details, forwarded verbatim on every
          return path — including the ``served_model`` /
          ``served_model_is_fallback``, so the JSON's origin travels with it
          whichever channel (file, extracted file, stdout) supplied it
    """

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
    # stdout answer is then saved to the requested name as before. One no
    # readable stamp shows to be newer than the slot is not read either, but
    # stays where it is: it may be the earlier answer, or this call's.
    refused_file = _set_aside_unchanged_result(output_json_path, requested_baseline)
    stale_file = refused_file is not None
    if refused_file == _RESULT_FILE_STALE:
        file_result = {
            "success": False,
            "error": (
                f"{output_json_path.name} is older than this slot and unchanged: "
                f"an earlier run's answer, not read"
            ),
            "source": "stale",
            "data": None,
        }
    elif refused_file == _RESULT_FILE_UNVERIFIED:
        file_result = {
            "success": False,
            "error": (
                f"{output_json_path.name} could not be shown to have been written "
                f"since this slot started (its metadata could not be read): it "
                f"may be an earlier answer, not read"
            ),
            "source": "unverified",
            "data": None,
        }
    else:
        file_result = json_extractor.read_json_from_file(output_json_path, prefer_arrays=prefer_arrays)

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
    # scrape. Never over an unverified one, which the rename would overwrite.
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
    details = result.get("details", {})
    if result.get("success") and FAILURE_CATEGORY_KEY not in details:
        # The child exited 0 and its stdout parsed, but not into an answer
        # (`_is_valid_parsed_data`): the executor's verdict for the same
        # rejection, read off the capture the exit 0 handed back, so both
        # lanes' ladders agree
        # (docs/development/delegation.md#read-and-analyze-executor).
        held = deferred_log or {}
        try:
            provider = get_provider(parse_model_spec(model_spec, anchor=anchor)[0])
            category = rejected_answer_category(
                provider, held.get("stdout"), held.get("stderr")
            )
        except Exception:  # noqa: BLE001 - classification must not break a failure path
            category = STATUS_UNPARSEABLE
        details = {**details, FAILURE_CATEGORY_KEY: category}
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
        "details": details,
        "data": None,
    }
