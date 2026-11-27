"""Hermes Agent (Nous Research) provider, measured against 0.23.4.

``hermes chat --format stream-json`` prints JSONL on stdout: one
``{"type": "system", "subtype": "init"}`` record, ``{"type": "text"}`` deltas
of everything the model wrote (narration before a tool call included), and one
terminal ``{"type": "result", "exit_code", "text", "tokens", "error"?}``
record whose ``text`` is the final assistant message. stderr is always the two
``Session: …`` / ``session_id: …`` lines, nothing else, on success and failure
alike. Every measurement below is from the offline probe of 2026-11-26: the
v0.23.4 tag (commit ``8fc03744``) in Docker, ``--network none``,
``tests/container/stub_server.py`` and ``failserver.py`` inside the container,
a fake key; the raw captures are ``tests/fixtures/hermes/``.

**Every turn runs in a background daemon, not in the child.** ``hermes chat``
is a thin client of a gateway daemon it auto-starts per ``HERMES_HOME``
(``python -m hermes_cli.main gateway run --idle-exit``) in a session of its
own, so the executor's process-group kill never reaches it. Measured: a client
killed 20 s into a fail-forever 500 left the daemon sending requests (12 → 16
over the next 30 s) until ``hermes gateway stop --yes`` ended it; the stop
takes ~2.3 s and no request follows it. stream-json has no in-process route
(the source says "never AIAgent", no flag or variable turns the daemon off).
So :meth:`HermesProvider.hermetic_dispatch` gives every spawn a private
``HERMES_HOME`` **and** ``HOME`` (two slots sharing one ``HOME`` share the
host-level gateway lock under ``~/.local/state/hermes/gateway-locks``, and the
second slot's stop then reported "No gateway running" while its daemon still
ran), and stops that home's daemon when the dispatch ends, on every exit path.

**The credential is written to disk, inside the private root.** The daemon
rebuilds its environment from the profile, so an exported key never reaches the
turn; it reads ``OPENROUTER_API_KEY`` from ``$HERMES_HOME/.env``. The adapter
writes that file (``0600`` in the ``0700`` root) when a dispatch opens and the
root is removed when the dispatch closes (``private_home``'s rules). Passing
``--api-key`` instead would put the key on argv, visible to ``ps``.

**Toolless, so no file or shell access at all.** ``--toolsets ""`` selects zero
toolsets: the request carries no ``tools``, and a stub forcing ``write_file``
or ``terminal`` calls got ``Tool 'write_file' does not exist`` back while the
workspace stayed clean. Hermes ships no read-only file toolset (``file`` bundles
``write_file`` and ``patch``), so the review lane reads nothing from disk and is
served the plan and diffs inline (``generate_read_scope = "none"``).
"""
import contextlib
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from .base import (
    CATEGORY_INVALID_MODEL,
    CATEGORY_PERMISSION_DENIED,
    CATEGORY_SERVER_ERROR,
    LAUNCH_DIAGNOSTICS_STDERR,
    REASONING_LADDER,
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    USAGE_PARTIAL,
    VERSION_TOO_LOW,
    InternalRetryEnvelope,
    build_child_env,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)
from .parse_kit import answer_from_text, fail
from .private_home import PrivateHomes

#: ``--reasoning <level>``, measured on the wire (2026-11-26) against a TLS stub
#: answering as ``openrouter.ai``: Hermes sends OpenRouter's ``reasoning`` body
#: field only when the base URL's host is openrouter.ai, so a localhost stub
#: sees nothing. ``none`` sends ``{"enabled": false}``; ``minimal`` through
#: ``max`` send ``{"enabled": true, "effort": <rung>}`` verbatim; ``ultra`` is
#: clamped to ``max`` by Hermes itself, so it is accepted here only as an inbound
#: alias and rewritten before argv, the way codex's is. Without the flag the
#: request carries ``"effort": "medium"``.
EFFORT_LADDER = ReasoningLadder(
    provider="hermes",
    rungs=REASONING_LADDER,
    inbound_aliases=(("ultra", "max"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted
EFFORT_ALIASES = EFFORT_LADDER.aliases
_ACCEPTED_EFFORTS = EFFORT_LADDER.accepted_inbound

#: Every flag :meth:`HermesProvider.build_command` renders, checked against
#: ``hermes chat --help`` before a command is built. The stale PyPI 0.19.0 and
#: the unrelated Hermes JavaScript engine (React Native's ``hermes`` binary)
#: both fail it.
HERMES_REQUIRED_FLAGS = (
    "--format", "--query-file", "--toolsets", "--ignore-rules", "--source",
    "--provider", "--max-turns", "--reasoning",
)

#: Tool-calling iterations per turn. The lane has no tools, so a turn that
#: loops is a model inventing tool calls that each come back "does not exist";
#: hitting the cap ends the turn with ``exit_code`` 1.
MAX_TURNS = 4

CREDENTIAL_ENV = "OPENROUTER_API_KEY"

#: Written into ``.env`` on every dispatch, so neither a user's
#: ``OPENROUTER_BASE_URL`` nor a ``CUSTOM_BASE_URL`` can re-point the slot. The
#: capture rig (``tests/fixtures/hermes/capture_probe.py``) replaces it with a
#: localhost stub.
BASE_URL = "https://openrouter.ai/api/v1"

#: ``config.yaml`` in each private home. JSON, which YAML reads as-is.
#:
#: * ``agent.api_max_retries: 1`` and ``agent.auto_recovery_cycles: 0`` bound the
#:   retry ladder (:data:`INTERNAL_RETRIES`). Unpinned, a fail-forever 500 took
#:   26 chat requests over 322 s; pinned, 2.
#: * ``auxiliary.title_generation.enabled: false`` removes the session-title
#:   call, a second billed chat request on every answered turn.
#: * ``gateway.unmanaged_idle_exit_seconds: 5`` makes a daemon nobody stopped
#:   (this process SIGKILLed) exit 5 s after its last turn ends, not 600 s.
#:   Measured: a client killed 14 s into a fail-forever 500, with no stop, left
#:   the daemon to finish its pinned ladder; it had exited on its own 45 s later
#:   and sent nothing more.
#: * ``updates.check: false`` stops the passive update check.
#: * ``security.allow_lazy_installs: false``: otherwise every fresh home's
#:   first start (each dispatch, and the ``chat --help`` gate) spawns a
#:   detached child that fetches the plugin catalog and installs the default
#:   plugins, outliving the command and writing into a root already removed.
#:   Measured in the container lane: a help probe's root came back after the
#:   wrapper removed it. With it off the boot step skips the spawn
#:   (``hermes_cli.default_plugins``), and nothing runs or writes after exit.
HERMES_CONFIG: Dict[str, Any] = {
    "agent": {"api_max_retries": 1, "auto_recovery_cycles": 0},
    "auxiliary": {"title_generation": {"enabled": False}},
    "gateway": {"unmanaged_idle_exit_seconds": 5},
    "security": {"allow_lazy_installs": False},
    "updates": {"check": False},
}

#: Measured with :data:`HERMES_CONFIG` in force, request counts from the stub
#: log. Each dispatch makes five catalog GETs and one ``/api/show`` probe before
#: its first chat request; on top of those a 401, 404 or 429 costs one chat
#: request, a 500 or a zero-byte response two, a cut stream or an error object
#: on a 200 three, and an empty answer four (Hermes's empty-response guard,
#: 55 s; nothing in the config lowers it): ten requests in all, the worst
#: case. A 429 is not retried, so ``retries_rate_limit`` is ``False``. A stalled
#: request had no client-side timeout within 400 s, so no wall bound is
#: stated: the slot's own timeout and :meth:`HermesProvider.hermetic_dispatch`'s
#: gateway stop end it.
INTERNAL_RETRIES = InternalRetryEnvelope(
    max_requests=10,
    max_wall_s=None,
    retries_rate_limit=False,
    configurable_by=("HERMES_HOME/config.yaml agent.api_max_retries",),
)

_HOME_PREFIX = "multi-llm-hermes-"
_HOMES = PrivateHomes(_HOME_PREFIX)
isolated_home_dirs = _HOMES.isolated_home_dirs
cleanup_home_dirs = _HOMES.cleanup
reset_home_dirs = _HOMES.reset

_ACTIVE_HOME: ContextVar[Optional[str]] = ContextVar("hermes_active_home", default=None)
_PROBE_LOCK = threading.Lock()
_PROBE: Dict[str, Any] = {"root": None, "pid": None}


def _probe_root() -> str:
    """One credential-free private root per process, remade if it went away
    (a root first made inside a dispatch is removed when that dispatch ends)."""
    with _PROBE_LOCK:
        root = _PROBE["root"]
        if _PROBE["pid"] != os.getpid() or not root or not os.path.isdir(root):
            root = _HOMES.create()
            seed_home(root, "")
            _PROBE.update(root=root, pid=os.getpid())
        return root

#: A key with any other character is not written (``.env`` quoting is
#: Hermes's dotenv's, not ours); the slot then fails as unauthenticated.
_SAFE_CREDENTIAL = re.compile(r"[A-Za-z0-9_.:+/=-]+")

_NO_CREDENTIAL = "no API keys or providers found"
_HTTP_STATUS = re.compile(r"\bHTTP (\d{3})\b")
_CONTEXT = re.compile(r"context[_ -]length|maximum context|context window|too many tokens", re.I)
_BUDGET = re.compile(r"insufficient (?:credits?|quota)|credits?.{0,32}(?:exhausted|exceeded)", re.I)
#: Hermes refusing its own compression model (context below 64K) is a
#: configuration fault, not this request's context overflowing.
_COMPRESSION_FLOOR = re.compile(r"compression model .* below the minimum", re.I)
_CUT_MODEL_RECORD = re.compile(r'"type"\s*:\s*"(?:text|tool_use|tool_result)"')
_CUT_RESULT_RECORD = re.compile(r'"type"\s*:\s*"result"')
_CUT_STREAM = re.compile(r"empty stream with no finish_reason|malformed SSE", re.I)


class HermesFlagsUnconfirmed(RuntimeError):
    """Refuse an incompatible binary before constructing a runnable command."""

    def __init__(self, missing: Tuple[str, ...], binary: str):
        self.missing, self.binary, self.state = missing, binary, VERSION_TOO_LOW
        super().__init__(
            f"hermes slot refused ({VERSION_TOO_LOW}): {binary} does not list "
            f"{', '.join(missing)} in `hermes chat --help`. Install Hermes Agent "
            "from https://github.com/NousResearch/hermes-agent (the PyPI package "
            "is stale, and React Native's Hermes JavaScript engine is unrelated)."
        )


def _home_env(root: str) -> Dict[str, str]:
    """``HERMES_HOME`` and a private ``HOME`` (with its XDG roots) under ``root``."""
    home = os.path.join(root, "home")
    return {
        "HERMES_HOME": root,
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "XDG_CACHE_HOME": os.path.join(home, ".cache"),
        "XDG_DATA_HOME": os.path.join(home, ".local", "share"),
        "XDG_STATE_HOME": os.path.join(home, ".local", "state"),
        "NO_COLOR": "1",
    }


def seed_home(root: str, credential: str, base_url: Optional[str] = None) -> None:
    """Write ``.env`` (``0600``) and ``config.yaml`` into a fresh private root."""
    Path(root, "home").mkdir(mode=0o700, exist_ok=True)
    lines = [f"OPENROUTER_BASE_URL={base_url or BASE_URL}"]
    if credential and _SAFE_CREDENTIAL.fullmatch(credential):
        lines.insert(0, f"{CREDENTIAL_ENV}={credential}")
    env_file = Path(root, ".env")
    descriptor = os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    Path(root, "config.yaml").write_text(json.dumps(HERMES_CONFIG, indent=1) + "\n", encoding="utf-8")


def stop_gateway(
    root: str, binary: Optional[str] = None, env: Optional[Mapping[str, str]] = None,
) -> None:
    """``hermes gateway stop --yes`` for this root's daemon; never raises.

    Run on every dispatch, never skipped on what the root holds: a client
    stopped early can leave a daemon still starting that has written nothing
    yet. ``env`` is the spawn's own composition when the caller has one, so the
    stop finds the daemon wherever the client looked for it; measured, the
    daemon's socket does not follow ``XDG_RUNTIME_DIR`` (a run with it set
    stopped cleanly), but the two must never be able to disagree.
    """
    try:
        binary = binary or shutil.which("hermes")
        if not binary:
            return
        if env is None:
            env = {"PATH": os.environ.get("PATH", os.defpath)}
            for name in ("SYSTEMROOT", "TMPDIR", "TEMP", "TMP", "LANG", "XDG_RUNTIME_DIR"):
                if os.environ.get(name):
                    env[name] = os.environ[name]
        env = {**env, **_home_env(root)}
        subprocess.run(
            [binary, "gateway", "stop", "--yes"], env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
        )
    except Exception:  # noqa: BLE001 - teardown never fails a dispatch
        pass


def _records(stdout: Any) -> List[Dict[str, Any]]:
    """Every whole JSON object line of a stream-json capture."""
    if not isinstance(stdout, str):
        return []
    records = []
    # "\n" only: str.splitlines also splits on U+2028, which JSON leaves raw.
    for line in stdout.split("\n"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _result(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    results = [r for r in records if r.get("type") == "result"]
    return results[-1] if results else None


def _streamed(records: List[Dict[str, Any]]) -> bool:
    return any(r.get("type") == "text" and isinstance(r.get("text"), str) and r["text"] for r in records)


def verdict(stdout: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """``(result record, None)`` for an answered turn, else ``(record, reason)``.

    An answered turn has a ``result`` record with ``exit_code`` 0, no ``error``
    and a nonblank ``text``, **and** streamed at least one ``text`` record. The
    last test is what separates a reply from Hermes's own exit-0 sentence after
    an empty completion (``⚠️ No reply: … didn't produce a reply this time``),
    which carries no ``error`` and streams nothing.
    """
    records = _records(stdout)
    record = _result(records)
    if record is None:
        return None, "hermes printed no result record (the stream was cut or the client was stopped)"
    code, text = record.get("exit_code"), record.get("text")
    if type(code) is not int or not isinstance(text, str):
        return record, "hermes printed a malformed result record"
    if "error" in record:
        return record, f"hermes failed: {record.get('error') or text.strip()}"
    if code != 0:
        return record, f"hermes ended the turn with exit_code {code}: {text.strip()[:300]}"
    if not _streamed(records):
        return record, f"hermes produced no reply: {text.strip()[:300]}"
    if not text.strip():
        return record, "Empty text response"
    return record, None


class HermesProvider(LLMProvider):
    """``hermes chat`` with zero toolsets, one private home and daemon per spawn."""

    #: ``-q <prompt>`` trails, so a non-argv transport drops the pair and adds
    #: ``--query-file -``.
    prompt_argv_index = -1
    #: Measured: ``--query-file -`` carried a 200 KB prompt on stdin. argv stays
    #: available, but a prompt that opens with ``-`` always goes on stdin
    #: (argparse would read it as a flag).
    prompt_transport = "stdin"
    supported_prompt_transports = ("stdin", "argv")

    #: Zero toolsets (module docstring): no write tool exists in the run, so the
    #: lane answers on stdout…
    supports_file_output = False
    #: …runs no shell (a forced ``terminal`` call came back "does not exist")…
    runs_shell_in_generate = False
    #: …and reads no file, so the plan and diffs go into the prompt.
    generate_read_scope = "none"

    usage_support = USAGE_PARTIAL
    internal_retries = INTERNAL_RETRIES

    #: No ``version_cmd``: ``hermes --version`` writes ``SOUL.md`` and
    #: ``cache/scratch/.last_prune`` into ``$HERMES_HOME`` (``~/.hermes`` unless
    #: set), and the version probes run with the caller's environment, so
    #: declaring it would write into the user's own Hermes home on every
    #: preflight. Compatibility is gated on :data:`HERMES_REQUIRED_FLAGS` instead,
    #: under a private home (:meth:`gate_probe_env`). An unstamped install prints
    #: ``vunknown`` anyway.
    verified_version = "0.23.4"
    help_argv = ("chat", "--help")

    def gate_binary_name(self) -> str:
        """``hermes``: the gate reads the name from ``version_cmd`` or
        ``auth_check``, and this adapter declares neither, so without this the
        flag gate would find no binary and confirm every flag unprobed."""
        return "hermes"
    install_hint = (
        "Install Hermes Agent with its own installer "
        "(https://github.com/NousResearch/hermes-agent); the PyPI package is stale."
    )
    auth_hint = "Export OPENROUTER_API_KEY; the adapter writes it into a private HERMES_HOME per run."

    #: :attr:`~.base.LLMProvider.EXIT0_CLASSIFIABLE`, reviewed: :meth:`vendor_text`
    #: drops every ``text`` record and, on a turn that streamed any, the result
    #: record's ``text`` (the model's answer), so an exit 0 is classified only on
    #: Hermes's own fields.
    EXIT0_CLASSIFIABLE = True
    #: stderr is only Hermes's two session-id lines (tests/fixtures/hermes).
    LAUNCH_DIAGNOSTICS = LAUNCH_DIAGNOSTICS_STDERR

    @property
    def name(self) -> str:
        return "hermes"

    def is_available(self) -> bool:
        return shutil.which("hermes") is not None

    def build_command(
        self, prompt: str, model: str, *, timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        missing = self.missing_flags(HERMES_REQUIRED_FLAGS)
        if missing:
            raise HermesFlagsUnconfirmed(missing, self.gate_binary(runnable=True) or "hermes")
        base_model, effort = split_reasoning_effort(model, _ACCEPTED_EFFORTS)
        cmd = [
            "hermes", "chat", "--format", "stream-json", "--toolsets", "",
            "--ignore-rules", "--source", "tool", "--provider", "openrouter",
            "--max-turns", str(MAX_TURNS), "-m", base_model,
        ]
        if effort is not None:
            cmd += ["--reasoning", EFFORT_ALIASES.get(effort, effort)]
        return cmd + ["-q", prompt]

    def build_command_for_transport(
        self, prompt: str, model: str, transport: str = "argv",
        prompt_file: Optional[str] = None, *, timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None, sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None, **options: Any,
    ) -> Tuple[List[str], Optional[str]]:
        if transport not in self.supported_prompt_transports:
            raise ValueError(f"hermes does not support the {transport!r} prompt transport")
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        if transport == "stdin" or prompt.startswith("-"):
            return cmd[:-2] + ["--query-file", "-"], prompt
        return cmd, None

    @contextlib.contextmanager
    def hermetic_dispatch(
        self, profile: str, model: str = "", *, anchor: Optional[str] = None,
        runner_version: Optional[str] = None,
    ) -> Iterator[Optional[str]]:
        """One private root per spawn, its daemon stopped on the way out.

        Entered by both spawn sites (``llm_client.provider_dispatch_context``)
        once per spawn. The root is a :class:`PrivateHomes` root, so the
        dispatch scope removes it after this context closes, and only once the
        client is confirmed stopped. The gateway stop runs first, on success,
        failure, timeout and exception alike: the daemon is not a child of the
        client and outlives it otherwise (module docstring). A root that cannot
        be made refuses the slot, since Hermes would fall back to ``~/.hermes``.
        """
        try:
            root = _HOMES.create()
            seed_home(root, os.environ.get(CREDENTIAL_ENV, ""))
        except OSError as exc:
            yield f"hermes slot refused: could not create its private HERMES_HOME ({exc})"
            return
        token = _ACTIVE_HOME.set(root)
        try:
            yield None
        finally:
            _ACTIVE_HOME.reset(token)
            stop_gateway(root, env=self._stop_env(root))

    def _stop_env(self, root: str) -> Optional[Dict[str, str]]:
        """The spawn's environment composition for ``root``, or ``None``."""
        try:
            return build_child_env(self, provider_env=_home_env(root))
        except Exception:  # noqa: BLE001 - the stop falls back to a minimal env
            return None

    def get_env(self, model: str) -> Dict[str, str]:
        """The dispatch's private root; outside one, the process's probe root.

        Outside a dispatch nothing generates (a help probe, a dry-run render),
        so one seeded, credential-free root per process serves every call.
        """
        return _home_env(_ACTIVE_HOME.get() or _probe_root())

    def help_probe_env(self) -> Dict[str, str]:
        """``hermes chat --help`` writes state, so it runs in the probe root."""
        try:
            return _home_env(_probe_root())
        except OSError:
            return {}

    def get_remove_env(
        self, anchor: Optional[str] = None, base_env: Optional[Mapping[str, str]] = None,
    ) -> List[str]:
        """Every ambient ``HERMES_*`` name, the base-URL overrides and the key.

        Removals run after the adapter's delta, so ``HERMES_HOME`` is kept.
        ``HERMES_TUI_GATEWAY_URL`` would point the client at somebody else's
        gateway; the key reaches the turn through ``.env``, never the child's
        environment.
        """
        source = os.environ if base_env is None else base_env
        return sorted({
            "CUSTOM_BASE_URL", "OPENROUTER_BASE_URL", CREDENTIAL_ENV,
            "HERMES_TUI_GATEWAY_URL", "HERMES_IGNORE_RULES", "HERMES_ENABLE_PROJECT_PLUGINS",
            *(key for key in source if key.startswith("HERMES_") and key != "HERMES_HOME"),
        })

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        record, failure = verdict(stdout)
        if failure:
            return fail(failure, stdout)
        return answer_from_text(record["text"], raw=stdout)

    def salvage_text(self, stdout: str) -> Optional[str]:
        try:
            record, failure = verdict(stdout)
            return "" if failure else record["text"].strip()
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """``result.tokens``: Hermes reports no cost on this route."""
        record = _result(_records(stdout))
        tokens = record.get("tokens") if record else None
        if not isinstance(tokens, dict):
            return None
        usage = {}
        for source, target in (
            ("input", "input_tokens"), ("output", "output_tokens"),
            ("total", "total_tokens"), ("cache_read", "cached_input_tokens"),
        ):
            value = tokens.get(source)
            if type(value) is int and value >= 0:
                usage[target] = value
        return usage or None

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The stream without what the model wrote.

        ``text``, ``tool_use`` and ``tool_result`` records go, and so does the
        result record's ``text`` on a turn that streamed text (it is then the
        model's answer; on every failure it is Hermes's own sentence and stays).
        Lines that are not JSON stay. A reduction that raises returns its input;
        stderr is never reduced.
        """
        try:
            if not isinstance(stdout, str) or not stdout:
                return stdout, stderr
            records = _records(stdout)
            answered = _streamed(records)
            lines = stdout.split("\n")
            last = max((i for i, line in enumerate(lines) if line.strip()), default=-1)
            kept = []
            for index, line in enumerate(lines):
                try:
                    record = json.loads(line) if line.strip().startswith("{") else None
                except ValueError:
                    record = None
                    # A stream cut inside a record the model wrote: its tail
                    # is the model's prose, never Hermes's verdict.
                    if index == last and (
                        _CUT_MODEL_RECORD.search(line)
                        or (answered and _CUT_RESULT_RECORD.search(line))
                    ):
                        continue
                if not isinstance(record, dict):
                    kept.append(line)
                    continue
                kind = record.get("type")
                if kind in ("text", "tool_use", "tool_result"):
                    continue
                if kind == "result" and answered:
                    record = {k: v for k, v in record.items() if k != "text"}
                    line = json.dumps(record)
                kept.append(line)
            return "\n".join(kept), stderr
        except Exception:  # noqa: BLE001 - a failed reduction returns its input
            return stdout, stderr

    def classify_failure(self, stdout: str, stderr: str, exit_code: int = 0) -> Optional[str]:
        """Read the result record's ``error``; the shared tables otherwise."""
        record, failure = verdict(stdout)
        if record is not None and failure is None and exit_code == 0:
            return None
        error = record.get("error") if record else None
        if error == "credentials or agent init failed" or _NO_CREDENTIAL in (stderr or ""):
            # Hermes's first-run guard, before any request: no key in .env
            # (tests/fixtures/hermes/no-key). Nothing a retry can fix.
            return STATUS_AUTH_FAILED
        if isinstance(error, str):
            match = _HTTP_STATUS.search(error)
            status = int(match.group(1)) if match else None
            if status == 401:
                return STATUS_AUTH_FAILED
            if _BUDGET.search(error) or status in (402, 429):
                return STATUS_RATE_LIMITED
            if status == 403:
                return CATEGORY_PERMISSION_DENIED
            if status == 404:
                return CATEGORY_INVALID_MODEL
            if _CONTEXT.search(error) and not _COMPRESSION_FLOOR.search(error):
                return STATUS_CONTEXT_LENGTH_EXCEEDED
            if (status is not None and status >= 500) or _CUT_STREAM.search(error):
                return CATEGORY_SERVER_ERROR
        return super().classify_failure(stdout, stderr, exit_code)

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """The parser's reason, read from stdout only; ``None`` without a record."""
        if not _records(stdout):
            return None
        return verdict(stdout)[1]
