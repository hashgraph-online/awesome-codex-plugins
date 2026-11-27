"""DeepSeek Harness (``dsh``) headless provider, measured against 0.2.2-rc.5.

``dsh --profile headless --json`` answers one task and writes newline-delimited
run events to stdout: ``session``, ``status`` (``turn_start``, ``step_start``,
``step_end`` with that step's ``usage``, ``turn_end``), ``text`` (one per
assistant message), ``tool_call``/``tool_result``, an ``error`` record when the
session itself breaks, and a terminal ``final`` record::

    {"type":"final","sessionId":"…","reason":{"kind":"completed"},"text":"…"}
    {"type":"final","sessionId":"…","reason":{"kind":"error",
        "error":{"message":"429: …","code":"RATE_LIMIT"}},"text":""}

``final.text`` is the LAST assistant message only, never earlier narration
(measured with a stub that narrates before a tool call). A failed run also
prints ``dsh: <CODE>: <message>`` on stderr and exits 1; a run killed by a
signal can exit 0 with no ``final`` record at all, so success is
``final.reason.kind == "completed"`` and nothing else.

**Model selection has no flag.** dsh composes its configuration from profile
patches, so every spawn gets a private ``DSH_HOME`` whose
``profiles/headless/cordis.patch.yml`` is :data:`DSH_PROFILE_PATCH`: one
OpenRouter route (``https://openrouter.ai/api/v1``, key from
``OPENROUTER_API_KEY``), the model and reasoning level read from
``DSH_MULTI_LLM_MODEL`` / ``DSH_MULTI_LLM_REASONING``, the retry and stall
bounds pinned, and the hidden session-title request, telemetry and the
DeepSeek session-log uploader disabled. dsh's built-in ``deepseek-official``
route is never selected. A repository's ``.env`` cannot reach any of it: dsh
refuses to start when a project ``.env`` sets a ``DSH_*`` name (measured), and
a ``.env`` value never replaces an inherited one, so the endpoint and the model
stay this adapter's.

**Read-only by dsh's own sandbox.** ``--permission-mode read-only
--approval-policy never``: the file tools refuse writes in-process
(``FS_SANDBOX_DENIED``), shell commands run under bubblewrap or Landlock with
writes denied, and a request to escalate is rejected without a prompt
(``SANDBOX_ESCALATION_REJECTED``). Measured with stub-driven ``write``,
out-of-tree ``write``, ``bash`` and escalation calls: the tree stayed clean in
every row. Where no confinement runner works, dsh fails the shell call closed
(``SANDBOX_UNAVAILABLE``) rather than running it unconfined.
"""
import json
import os
import re
import shutil
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from .base import (
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_INVALID_MODEL,
    CATEGORY_SERVER_ERROR,
    LAUNCH_DIAGNOSTICS_NONE,
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    USAGE_FULL,
    VERSION_TOO_LOW,
    PROFILE_GENERATE,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    split_reasoning_effort,
)
from .parse_kit import answer_from_text, fail
from .private_home import PrivateHomes

#: pi-ai's thinking levels, which dsh's ``llm-pi-ai`` route takes as its
#: ``reasoning`` field: ``off minimal low medium high xhigh max``. Measured on
#: the wire through the OpenRouter route: ``high`` and ``max`` reach the
#: request as ``reasoning: {effort: …}``, ``off`` (and no level at all) as
#: ``effort: "none"``. dsh validates the level against the model's catalog entry
#: before any request: ``xhigh`` on deepseek-v4.1-flash, or any level on a model
#: its catalog does not describe, exits 1 with ``UNSUPPORTED_REASONING_EFFORT``.
EFFORT_LADDER = ReasoningLadder(
    provider="dsh",
    rungs=("minimal", "low", "medium", "high", "xhigh", "max"),
    spellings=(("off", "none"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: The binary's npm package, for the install hint (the Debian ``dsh`` package
#: is an unrelated distributed shell).
DSH_PACKAGE = "@deepseek-ai/dsh"

#: Retries after the first request of one model call (dsh's default is 5).
#: dsh retries ``RATE_LIMIT``, ``SERVER``, ``TIMEOUT``, ``TRANSPORT`` and
#: ``EMPTY_RESPONSE`` with 0.5 s exponential backoff capped at 10 s. Measured
#: with this value against a stub: a 429, a 500 and an empty answer each made
#: three requests and failed in 2.8-3.8 s.
DSH_MAX_RETRIES = 2

#: The longest one stream read may stay silent before dsh abandons that request
#: (``streamIdleTimeoutMs``; dsh's default is 300 s). A stall is retried like
#: any timeout, so a fail-forever stall is ``(DSH_MAX_RETRIES + 1)`` idle
#: windows plus backoff: measured 62.85 s at a 20 s window.
DSH_STREAM_IDLE_TIMEOUT_S = 120

#: The output cap every request asks for (``max_completion_tokens``). Unset,
#: dsh asks for the catalog maximum, 393,216 on deepseek-v4.1-flash (measured on
#: the wire), and a spend-capped OpenRouter key refuses a request it could not
#: pay for at that size rather than clamping it. Reasoning tokens count toward
#: it, so it is generous for a JSON review.
DSH_MAX_OUTPUT_TOKENS = 65536

#: Variables the profile patch reads (``!!js process.env.…``). The ``DSH_``
#: prefix is load-bearing: dsh refuses to start when a project ``.env`` sets
#: any ``DSH_*`` name, so a cloned repository can never supply them.
MODEL_ENV = "DSH_MULTI_LLM_MODEL"
REASONING_ENV = "DSH_MULTI_LLM_REASONING"
DSH_CREDENTIAL_ENV = "OPENROUTER_API_KEY"
HOME_ENV = "DSH_HOME"

#: The profile patch every private ``DSH_HOME`` carries. No credential value:
#: ``apiKeyEnv`` names the variable dsh resolves per request. ``api`` is set so
#: a slug newer than dsh's bundled catalog still dispatches; a catalogued slug
#: keeps its catalog entry's reasoning levels and limits.
DSH_PROFILE_PATCH = f"""\
# Written by multi-llm for one dispatch; removed with this directory.
- id: session-title-llm
  disabled: true
- id: session-log-deepseek
  disabled: true
- id: session-telemetry-otel
  disabled: true
- id: agent-default-model
  config:
    provider: openrouter
    model: !!js process.env.{MODEL_ENV}
- id: llm-pi-ai
  config:
    providers:
      openrouter:
        apiKeyEnv: {DSH_CREDENTIAL_ENV}
        api: openai-completions
        baseURL: https://openrouter.ai/api/v1
        reasoning: !!js process.env.{REASONING_ENV} || undefined
        streamIdleTimeoutMs: {DSH_STREAM_IDLE_TIMEOUT_S * 1000}
        retryPolicy:
          mode: normal
          maxRetries: {DSH_MAX_RETRIES}
        models:
          - id: !!js process.env.{MODEL_ENV}
            maxTokens: {DSH_MAX_OUTPUT_TOKENS}
"""

_PATCH_RELPATH = ("profiles", "headless", "cordis.patch.yml")

#: ``DSH_HOME`` when no private root could be made: a path under the null
#: device, which no process can create, so dsh fails at boot instead of
#: answering from the user's own ``~/.dsh`` on its default route (which the
#: patch is the only thing that replaces).
UNUSABLE_HOME = os.path.join(os.devnull, "multi-llm-dsh-no-private-home")

#: Prefix under ``TMPDIR`` (:class:`PrivateHomes`), one root per spawn.
_HOME_PREFIX = "multi-llm-dsh-"
_HOMES = PrivateHomes(_HOME_PREFIX)
isolated_home_dirs = _HOMES.isolated_home_dirs
cleanup_home_dirs = _HOMES.cleanup
reset_home_dirs = _HOMES.reset

#: Variables every dispatch pins. ``DSH_TELEMETRY_MODE`` is the documented
#: switch; the patch also unmounts the exporter.
DSH_ENV = {"DSH_TELEMETRY_MODE": "DISABLED", "NO_COLOR": "1"}

#: The launcher's own flags, read from top-level ``dsh --help`` (which, unlike
#: ``dsh --profile headless --help``, writes nothing into ``DSH_HOME``). They
#: tell DeepSeek Harness from Debian's unrelated ``dsh`` distributed shell.
DSH_LAUNCHER_FLAGS = ("--profile", "--patch")
#: The headless app's flags, measured on the floor build
#: (:attr:`DshProvider.flags_verified_at_floor`) rather than read from its help.
DSH_HEADLESS_FLAGS = ("--json", "--permission-mode", "--approval-policy")
DSH_REQUIRED_FLAGS = DSH_LAUNCHER_FLAGS + DSH_HEADLESS_FLAGS

#: dsh's own stderr verdict line, ``dsh: RATE_LIMIT: 429: {…}``.
_STDERR_CODE = re.compile(r"^dsh: (?P<code>[A-Z][A-Z0-9_]+): (?P<message>.*)$", re.MULTILINE)
#: The boot refusal a project ``.env`` setting a launch-only name produces.
_ENV_REFUSAL = re.compile(
    r"^(?:Error: )?dsh: .*, which only the launching environment may set", re.MULTILINE
)
_INVALID_MODEL_TEXT = re.compile(
    r"model_not_found|does not exist|not a valid model|No endpoints found", re.I
)

_AUTH_CODES = frozenset({
    "AUTH", "MISSING_CREDENTIAL", "INVALID_CREDENTIAL",
})
_RATE_CODES = frozenset({"RATE_LIMIT", "QUOTA"})
_MODEL_CODES = frozenset({
    "UNKNOWN_MODEL", "MODEL_UNSUPPORTED", "UNSUPPORTED_REASONING_EFFORT",
    "INVALID_MODEL_CONTEXT", "INVALID_MODEL_INFO", "INVALID_MODEL_MAX_TOKENS",
    "INVALID_MODEL_REASONING",
})
_SERVER_CODES = frozenset({
    "SERVER", "TIMEOUT", "STREAM_CLOSED", "EMPTY_RESPONSE", "MALFORMED_RESPONSE",
    "INVALID_RESPONSE",
})
_RUNNER_CODES = frozenset({
    "INVALID_CONFIG", "NO_ADAPTER", "INVALID_ADAPTER", "INVALID_CATALOG",
    "UNSUPPORTED_OPTION", "INVALID_PREPARED_CALL",
})


class DshFlagsUnconfirmed(RuntimeError):
    """The ``dsh`` on PATH does not document the headless flags this argv needs."""

    def __init__(self, missing: Tuple[str, ...], binary: str):
        self.missing, self.binary, self.state = missing, binary, VERSION_TOO_LOW
        super().__init__(
            f"dsh slot refused ({VERSION_TOO_LOW}): {binary} does not list {', '.join(missing)} in "
            f"`dsh --help`. Install DeepSeek Harness with "
            f"`npm install -g {DSH_PACKAGE}`; the Debian `dsh` package is an "
            "unrelated distributed shell."
        )


def _events(stdout: str) -> Iterator[Dict[str, Any]]:
    # "\n" only: str.splitlines() also splits on U+2028/U+2029/U+0085, which
    # JSON.stringify leaves raw inside a string, and would cut a record in two.
    for line in (stdout or "").split("\n"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and isinstance(event.get("type"), str):
            yield event


def _final(stdout: str) -> Optional[Dict[str, Any]]:
    """The last ``final`` record, or ``None``."""
    final = None
    for event in _events(stdout):
        if event["type"] == "final":
            final = event
    return final


def _reason(final: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    reason = final.get("reason") if final else None
    return reason if isinstance(reason, dict) else {}


def _final_error(final: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """``(code, message)`` of a failed ``final`` record, else ``("", "")``."""
    error = _reason(final).get("error")
    if not isinstance(error, dict):
        return "", ""
    code = error.get("code") if isinstance(error.get("code"), str) else ""
    message = error.get("message") if isinstance(error.get("message"), str) else ""
    return code, message


def _completed_text(final: Optional[Dict[str, Any]]) -> Optional[str]:
    """``final.text`` of a completed run, else ``None``."""
    if _reason(final).get("kind") != "completed":
        return None
    text = final.get("text") if final else None
    return text if isinstance(text, str) else None


class DshProvider(LLMProvider):
    """DeepSeek Harness headless mode over an OpenRouter route.

    Model ids are OpenRouter slugs (``deepseek/deepseek-v4.1-flash-1017``) with
    an optional ``:effort`` suffix from :data:`REASONING_EFFORTS`.
    """

    version_cmd = ("dsh", "--version")
    #: The build every argv, patch and failure shape here was measured on.
    verified_version = "0.2.2-rc.5"
    #: The floor the headless flags were verified at. ``0.2.2`` and not the
    #: measured ``0.2.2-rc.5`` on purpose: :func:`version_tuple` reads the rc as
    #: ``(0, 2, 2, 5)``, which would put the final 0.2.2 below its own rc.
    min_version = "0.2.2"
    flags_verified_at_floor = DSH_HEADLESS_FLAGS
    install_hint = f"npm install -g {DSH_PACKAGE} (needs Node.js; the Debian dsh package is unrelated)"
    auth_hint = (
        "Export OPENROUTER_API_KEY; the adapter writes its own dsh profile into a "
        "private DSH_HOME for every dispatch."
    )
    prompt_transport = "stdin"
    supported_prompt_transports: Tuple[str, ...] = ("stdin", "argv")
    prompt_argv_index = -1
    usage_support = USAGE_FULL
    #: Read-only is dsh's own sandbox (module docstring), so the answer comes
    #: back on stdout: the file tools refuse every write under this argv.
    supports_file_output = False
    #: Measured: a stub-driven ``bash`` call ran (``id`` printed) with its writes
    #: denied (``Permission denied``) under Landlock on the host.
    runs_shell_in_generate = True
    internal_retries = InternalRetryEnvelope(
        max_requests=DSH_MAX_RETRIES + 1,
        max_wall_s=float((DSH_MAX_RETRIES + 1) * DSH_STREAM_IDLE_TIMEOUT_S + 2 * 10 + 5),
        retries_rate_limit=True,
        configurable_by=("profile patch llm-pi-ai.providers.openrouter.retryPolicy",
                         "profile patch llm-pi-ai.providers.openrouter.streamIdleTimeoutMs"),
    )

    #: :attr:`~.base.LLMProvider.EXIT0_CLASSIFIABLE`, reviewed: :meth:`vendor_text`
    #: keeps only dsh's own failure records (a failed ``final``, ``turn_end`` or
    #: ``error`` record, code and message); the model's ``text`` and every
    #: tool record stay out.
    EXIT0_CLASSIFIABLE = True

    #: :attr:`~.base.LLMProvider.LAUNCH_DIAGNOSTICS`, from the captures: besides
    #: dsh's ``dsh: CODE: …`` line, stderr carries pi-ai's dump of a chunk it
    #: could not parse (``Could not parse message into JSON:`` / ``From chunk:``,
    #: fixture row ``truncated``) and a malformed tool call's arguments
    #: (``Received arguments:``), both the model's bytes. So no line there is
    #: read for a launch verdict, and :meth:`vendor_text` keeps only dsh's own.
    LAUNCH_DIAGNOSTICS = LAUNCH_DIAGNOSTICS_NONE

    @property
    def name(self) -> str:
        return "dsh"

    def is_available(self) -> bool:
        return shutil.which("dsh") is not None

    def parse_version(self, stdout: str, stderr: str) -> Optional[str]:
        """``0.2.2-rc.5``, prerelease tag kept: dsh ships only prereleases."""
        for text in (stdout or "", stderr or ""):
            match = re.search(r"\b(\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?)\b", text)
            if match:
                return match.group(1)
        return super().parse_version(stdout, stderr)

    # -- argv ------------------------------------------------------------

    def build_command(
        self, prompt: str, model: str, *, timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # dsh --profile headless --json --permission-mode read-only
        #     --approval-policy never -- <prompt>
        # The model and effort travel in get_env (no --model flag exists).
        missing = self.missing_flags(DSH_REQUIRED_FLAGS)
        if missing:
            raise DshFlagsUnconfirmed(missing, self.gate_binary(runnable=True) or "dsh")
        return [
            "dsh", "--profile", "headless", "--json",
            "--permission-mode", "read-only", "--approval-policy", "never",
            "--", prompt,
        ]

    def build_command_for_transport(
        self, prompt: str, model: str, transport: str = "argv",
        prompt_file: Optional[str] = None, *, timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None, sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """stdin by default: ``-`` reads the task from stdin (223 KB measured).

        The argv form keeps ``--`` ahead of the prompt, so a prompt that opens
        with ``-`` is task text, not an option (measured).
        """
        if transport not in self.supported_prompt_transports:
            raise ValueError(
                f"dsh does not support the {transport!r} prompt transport "
                f"(supported: {', '.join(self.supported_prompt_transports)})"
            )
        argv = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        if transport == "stdin":
            return argv[:-2] + ["-"], prompt
        return argv, None

    # -- environment -------------------------------------------------------

    def _private_home(self) -> Optional[str]:
        """A fresh ``DSH_HOME`` holding :data:`DSH_PROFILE_PATCH`, or ``None``."""
        try:
            home = _HOMES.create()
        except OSError:
            return None
        try:
            patch = os.path.join(home, *_PATCH_RELPATH)
            os.makedirs(os.path.dirname(patch), mode=0o700, exist_ok=True)
            with open(patch, "w", encoding="utf-8") as handle:
                handle.write(DSH_PROFILE_PATCH)
        except OSError:
            _HOMES.release(home)
            return None
        return home

    def _env(self, model: str, source: Mapping[str, str]) -> Dict[str, str]:
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        env = dict(DSH_ENV)
        env[MODEL_ENV] = base_model
        env[REASONING_ENV] = effort or ""
        # Carried explicitly so the `env_allowlist` filter (which admits only
        # this adapter's DSH_* family) cannot strip the one key the route reads.
        credential = source.get(DSH_CREDENTIAL_ENV)
        if credential:
            env[DSH_CREDENTIAL_ENV] = credential
        return env

    def get_env(self, model: str) -> Dict[str, str]:
        """The model, its reasoning level, the key and a private ``DSH_HOME``.

        Always a private home, even when the user exported ``DSH_HOME``: the
        model is selected by the patch in it, so without it dsh would answer on
        whatever its own default route is. When none can be made the home is
        :data:`UNUSABLE_HOME` and the slot fails, never the user's.
        """
        env = self._env(model, os.environ)
        env[HOME_ENV] = self._private_home() or UNUSABLE_HOME
        return env

    def resolve_env(self, model: str, profile: str = PROFILE_GENERATE, **options: Any) -> Dict[str, str]:
        env = super().resolve_env(model, profile, **options)
        source = options.get("base_env")
        if source is not None:
            # The key comes from the environment the child really inherits.
            env.pop(DSH_CREDENTIAL_ENV, None)
            credential = source.get(DSH_CREDENTIAL_ENV)
            if credential:
                env[DSH_CREDENTIAL_ENV] = credential
        return env

    def get_remove_env(
        self, anchor: Optional[str] = None, base_env: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Every other ``DSH_*`` name: ``DSH_PERMISSION_MODE`` alone would
        change the sandbox preset dsh boots with."""
        source = os.environ if base_env is None else base_env
        keep = {HOME_ENV, MODEL_ENV, REASONING_ENV, *DSH_ENV}
        return sorted(key for key in source if key.startswith("DSH_") and key not in keep)

    # -- reading the stream --------------------------------------------------

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        final = _final(stdout)
        text = _completed_text(final)
        if text is None:
            # ``raw`` picks the executor's rung (parse_kit): the closing
            # message a cut run left is answer text (unparseable_result),
            # a failed call's stream holds none (runner_error).
            return fail(self.describe_failure(stdout, stderr) or "dsh failed",
                        self.salvage_text(stdout) or "")
        if not text.strip():
            return fail("dsh completed with no final message", "")
        return answer_from_text(text, raw=stdout)

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The closing assistant message: ``final.text`` of a completed run,
        else the last ``text`` record whose step ended without a tool call (a
        run cut before ``final``). Narration ahead of a tool call, and a
        message whose step never ended, are never returned."""
        try:
            last: Optional[str] = None
            pending: Optional[str] = None
            tool_in_step = False
            saw_stream = False
            for event in _events(stdout):
                saw_stream = True
                kind = event["type"]
                if kind == "status" and event.get("phase") == "step_start":
                    pending, tool_in_step = None, False
                elif kind == "text" and isinstance(event.get("text"), str):
                    pending = event["text"]
                elif kind in ("tool_call", "tool_result"):
                    tool_in_step = True
                    pending = None
                elif kind == "status" and event.get("phase") == "step_end":
                    # A message counts once its step ended with no tool call:
                    # text cut before that may be narration ahead of a call.
                    if pending is not None and not tool_in_step:
                        last = pending
                    pending = None
                elif kind == "final":
                    completed = _completed_text(event)
                    if completed is not None:
                        return completed.strip()
            if not saw_stream:
                return None
            return (last or "").strip()
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """The sum of every ``step_end`` record's ``usage`` (one per model call).

        ``inputTokens`` excludes the cached prefix, which dsh reports apart as
        ``cacheReadTokens`` (measured live: 134 input beside 5,888 cached on a
        second step), so that is ``cached_input_tokens``.
        """
        totals = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
        seen = False
        tool_uses = 0
        for event in _events(stdout):
            if event["type"] == "tool_call":
                tool_uses += 1
                continue
            if event["type"] != "status" or event.get("phase") != "step_end":
                continue
            usage = event.get("usage")
            if not isinstance(usage, dict):
                continue
            for key, field in (("input_tokens", "inputTokens"), ("output_tokens", "outputTokens"),
                               ("cached_input_tokens", "cacheReadTokens")):
                value = usage.get(field)
                if type(value) is int and value >= 0:
                    totals[key] += value
                    seen = seen or value > 0
        # A failed call's step_end carries zeros: usage is reported or absent.
        if not seen:
            return None
        result: Dict[str, Any] = {k: v for k, v in totals.items() if v or k != "cached_input_tokens"}
        result["tool_uses"] = tool_uses
        return result

    @staticmethod
    def _failure_records(stdout: str) -> List[Dict[str, Any]]:
        """dsh's own failure records, reduced to code and message."""
        records: List[Dict[str, Any]] = []
        for event in _events(stdout):
            kind = event["type"]
            if kind == "error" and isinstance(event.get("message"), str):
                records.append({"type": "error", "message": event["message"]})
            elif kind == "final" or (kind == "status" and event.get("phase") == "turn_end"):
                code, message = _final_error(event)
                if code or message:
                    records.append({"type": kind, "code": code, "message": message})
        return records

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """dsh's own words only: its failure records on stdout, and on stderr
        its ``dsh: CODE: …`` lines and the ``.env`` boot refusal, never the
        chunk or tool arguments pi-ai dumps beside them."""
        lines = [json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                 for record in self._failure_records(stdout)]
        own = [line for line in (stderr or "").split("\n")
               if _STDERR_CODE.match(line) or _ENV_REFUSAL.search(line)]
        return "\n".join(lines), "\n".join(own)

    def _codes(self, stdout: str, stderr: str) -> List[Tuple[str, str]]:
        """``(code, message)`` pairs from the final record, then dsh's stderr line."""
        pairs: List[Tuple[str, str]] = []
        code, message = _final_error(_final(stdout))
        if code:
            pairs.append((code, message))
        for match in _STDERR_CODE.finditer(stderr or ""):
            pairs.append((match["code"], match["message"]))
        return pairs

    def classify_failure(self, stdout: str, stderr: str, exit_code: int = 0) -> Optional[str]:
        if _completed_text(_final(stdout)) is not None:
            return None
        if _ENV_REFUSAL.search(stderr or ""):
            return STATUS_RUNNER_ERROR
        for code, message in self._codes(stdout, stderr):
            if code in _AUTH_CODES:
                return STATUS_AUTH_FAILED
            if code in _RATE_CODES:
                return STATUS_RATE_LIMITED
            if code == "CONTEXT_WINDOW_EXCEEDED":
                return STATUS_CONTEXT_LENGTH_EXCEEDED
            if code in _MODEL_CODES:
                return CATEGORY_INVALID_MODEL
            if code == "INVALID_REQUEST" and _INVALID_MODEL_TEXT.search(message):
                return CATEGORY_INVALID_MODEL
            if code in _SERVER_CODES:
                return CATEGORY_SERVER_ERROR
            if code == "TRANSPORT":
                return CATEGORY_CONNECTION_ERROR
            # pi-ai's residual code; a stream it could not read is the
            # server's (fixture row `truncated`: a cut SSE frame).
            if code == "PI_AI_ERROR" and message.startswith("Error reading response"):
                return CATEGORY_SERVER_ERROR
            if code in _RUNNER_CODES:
                return STATUS_RUNNER_ERROR
        # The shared rows: exit 127, a sandbox's own refusal on stderr, and the
        # marker tables over :meth:`vendor_text`'s reduction.
        return super().classify_failure(stdout, stderr, exit_code)

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        final = _final(stdout)
        if _completed_text(final) is not None:
            return None
        refusal = _ENV_REFUSAL.search(stderr or "")
        if refusal:
            line = next((line for line in stderr.splitlines() if _ENV_REFUSAL.search(line)), "")
            return line.removeprefix("Error: ").strip() or "dsh refused this repository's .env"
        code, message = _final_error(final)
        if code or message:
            return f"dsh {code or 'error'}: {message}".rstrip(": ")
        match = _STDERR_CODE.search(stderr or "")
        if match:
            return f"dsh {match['code']}: {match['message']}"
        for record in self._failure_records(stdout):
            if record["type"] == "error":
                return f"dsh error: {record['message']}"
        if final is None:
            # Only a dsh stream is evidence; nothing at all says nothing.
            return "dsh ended without a final event" if any(_events(stdout)) else None
        return f"dsh ended with reason {_reason(final).get('kind')!r}"
