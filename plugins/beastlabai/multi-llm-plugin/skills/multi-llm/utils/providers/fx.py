"""Vercel fx's terminal JSON envelope, measured against 0.0.14.

Only ``final_output`` is an answer. ``output`` contains narration and provider
diagnostics; stderr also carries shell stdout. Neither is a safe fallback answer
or an unqualified source of provider failure markers.
"""
import atexit
import contextlib
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
import shutil
import threading
import tempfile
import warnings
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from .base import (
    CATEGORY_INVALID_MODEL,
    CATEGORY_PERMISSION_DENIED,
    CATEGORY_SERVER_ERROR,
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    USAGE_PARTIAL,
    VERSION_TOO_LOW,
    PROFILE_GENERATE,
    skill_environment_path,
)
from .pi import parse_answer_text
from ..retry_ladder import STATUS_BUDGET_EXHAUSTED


EFFORT_LADDER = ReasoningLadder(
    provider="fx",
    declined="fx 0.0.14 custom connections send no reasoning option; --effort and --fast are inert",
)
FX_REQUIRED_FLAGS = ("--json", "--no-save", "--auto", "--model")
FX_CREDENTIAL_ENV = "OPENROUTER_API_KEY"
FX_ENV = {
    "FX_PROVIDER": "openrouter", "FX_MAX_AGENT_STEPS": "60",
    "FX_AUTO_UPGRADE": "0", "FX_PERMISSION_MODE": "auto", "NO_COLOR": "1",
}
_ACTIVE_HOME: ContextVar[Optional[str]] = ContextVar("fx_managed_home", default=None)
_HOME_LOCK = threading.RLock()
_CONFIG_HOME: Optional[str] = None
_CONFIG_HOME_USERS = 0
_CONFIG_HOME_PID: Optional[int] = None


def render_settings(base_url: str = "https://openrouter.ai/api/v1") -> dict:
    """The production and container seed profile; contains no credential value.

    The owner accepted automatic shell review and web access on 2026-10-22.
    There is no network sandbox. Unset reviewer_model follows each turn's model
    on this custom connection, so concurrent slots never rewrite shared config.
    """
    return {
        "provider": "openrouter",
        "providers": {"openrouter": {
            "protocol": "openai-chat-completions", "base_url": base_url,
            "auth": {"type": "bearer", "env": FX_CREDENTIAL_ENV},
        }},
        "auto_upgrade": False, "context": False, "permission_mode": "auto",
        "permission": {
            "read": "allow", "glob": "allow", "grep": "allow",
            "edit": "allow", "bash": "allow", "web_fetch": "allow",
            "skill": "deny", "subagent": "deny",
            "mcp_select_tool": "deny", "mcp_features": "deny",
        },
    }


def acquire_config_home() -> str:
    """Share one owned HOME across overlapping dispatches in this process."""
    global _CONFIG_HOME, _CONFIG_HOME_USERS, _CONFIG_HOME_PID
    with _HOME_LOCK:
        if _CONFIG_HOME_PID != os.getpid():
            # A fork must neither reuse nor remove its parent's active HOME.
            _CONFIG_HOME, _CONFIG_HOME_USERS = None, 0
            _CONFIG_HOME_PID = os.getpid()
        if _CONFIG_HOME is None:
            home = Path(tempfile.mkdtemp(prefix="multi-llm-fx-"))
            try:
                home.chmod(0o700)
                settings_dir = home / ".fx"
                settings_dir.mkdir(mode=0o700)
                settings = settings_dir / "settings.json"
                settings.write_text(json.dumps(render_settings()) + "\n", encoding="utf-8")
                settings.chmod(0o600)
                profile = home / ".bash_profile"
                profile.write_text('export PATH="$MULTI_LLM_FX_PATH"\n', encoding="utf-8")
                profile.chmod(0o600)
            except BaseException:
                shutil.rmtree(home, ignore_errors=True)
                raise
            _CONFIG_HOME = str(home)
        _CONFIG_HOME_USERS += 1
        return _CONFIG_HOME


def sweep_config_home() -> None:
    """Delete only the HOME this process created, never another process's."""
    global _CONFIG_HOME, _CONFIG_HOME_USERS
    with _HOME_LOCK:
        home, _CONFIG_HOME = _CONFIG_HOME, None
        _CONFIG_HOME_USERS = 0
        if home and _CONFIG_HOME_PID == os.getpid():
            shutil.rmtree(home, ignore_errors=True)


def release_config_home() -> None:
    global _CONFIG_HOME_USERS
    with _HOME_LOCK:
        _CONFIG_HOME_USERS = max(0, _CONFIG_HOME_USERS - 1)
        if not _CONFIG_HOME_USERS:
            sweep_config_home()


atexit.register(sweep_config_home)


class FxFlagsUnconfirmed(RuntimeError):
    """Refuse an incompatible binary before constructing a runnable command."""

    def __init__(self, missing: Tuple[str, ...], binary: str):
        self.missing, self.binary, self.state = missing, binary, VERSION_TOO_LOW
        super().__init__(
            f"fx slot refused ({VERSION_TOO_LOW}): {binary} does not list "
            f"{', '.join(missing)} in fx ask --help. The npm/brew fx JSON viewer "
            "is unrelated; use vercel-labs/fx from https://github.com/vercel-labs/fx/releases."
        )


class FxPromptInvalid(ValueError):
    """A prompt fx cannot accept, refused before any child is spawned."""
_ENVELOPE_KEYS = frozenset({
    "output", "final_output", "exit_code", "model", "resolved_provider",
    "session_id", "steps", "tool_calls", "usage", "error", "auth_failure", "recovery",
})
_WARNED_KEYS: set = set()
_WARN_LOCK = threading.Lock()
_HTTP = re.compile(
    r"^(?:API request failed|API access denied|configured provider authentication failed)"
    r" · HTTP (?P<status>\d{3})(?: · (?P<body>[^\n]*))?\s*$", re.MULTILINE
)
_STDERR = re.compile(r"^(?:\[notice\] ⚠ |fx ask: |fx: [A-Z]\w*$|Agent step limit reached)")
_BUDGET = re.compile(
    r"insufficient (?:credits?|quota)|(?:credit|budget|quota).{0,32}(?:exhausted|exceeded|limit)|"
    r"(?:exhausted|exceeded).{0,32}(?:credit|budget|quota)", re.I
)
_INVALID_MODEL = re.compile(r"not a valid model ID|No endpoints found", re.I)
_CONTEXT = re.compile(r"maximum context length|context[_ -]length[_ -]exceeded|too many tokens", re.I)


def _object(stdout: str) -> Optional[dict]:
    try:
        value = json.loads(stdout)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _tool_failure(envelope: dict) -> Optional[str]:
    calls = envelope.get("tool_calls", [])
    if not isinstance(calls, list):
        return "fx returned malformed tool_calls"
    for call in calls:
        if not isinstance(call, dict):
            return "fx returned a malformed tool record"
        if not isinstance(call.get("name"), str) or not isinstance(call.get("status"), str):
            return "fx returned a malformed tool record"
        error = call.get("error")
        if "error" in call and (
            not isinstance(error, dict) or not error
            or any(not isinstance(value, str) or not value for value in error.values())
        ):
            return "fx returned a malformed tool error"
        if call.get("status") in ("rejected", "denied", "held") or (
            isinstance(error, dict)
            and (error.get("category") == "rejected" or error.get("code") == "rejected")
        ):
            return f"fx refused tool {call.get('name', 'unknown')}; its requested result was not obtained"
    return None


def _terminal_failure(envelope: Optional[dict]) -> Optional[str]:
    if envelope is None:
        return "fx did not return one complete JSON object"
    if (
        type(envelope.get("exit_code")) is not int
        or not isinstance(envelope.get("output"), str)
        or not isinstance(envelope.get("final_output"), str)
    ):
        return "fx returned a malformed terminal envelope"
    # The pinned writer omits these fields on success. Even a falsey or
    # malformed error marker must never turn a failed run into an answer.
    if "error" in envelope or "auth_failure" in envelope:
        return f"fx failed: {envelope.get('error') or 'authentication failure'}"
    if envelope["exit_code"] != 0:
        return f"fx exited with status {envelope['exit_code']}"
    denied = _tool_failure(envelope)
    if denied:
        return denied
    if not envelope["final_output"].strip():
        return "fx returned no final answer"
    if envelope["output"] == "" and envelope["final_output"] == "Done.":
        return "fx fabricated Done. after an empty completion"
    return None


class FxProvider(LLMProvider):
    """OpenRouter custom connection, managed HOME, automatic tool review."""

    version_cmd = ("fx", "--version")
    help_argv = ("ask", "--help")
    verified_version = "0.0.14"
    auth_check: Tuple[str, ...] = ()
    install_hint = "Use the checksummed vercel-labs/fx release archive; npm/brew fx is an unrelated JSON viewer."
    auth_hint = "Export OPENROUTER_API_KEY; the adapter creates an isolated fx configuration automatically."
    prompt_transport = "stdin"
    supported_prompt_transports = ("stdin", "argv")
    usage_support = USAGE_PARTIAL
    # Measured with this --auto policy: shell-reviewed fixture; a reviewer
    # can still reject an individual command (shell-held fixture).
    runs_shell_in_generate = True
    internal_retries = InternalRetryEnvelope(max_requests=None, retries_rate_limit=True)

    @property
    def name(self) -> str:
        return "fx"

    @property
    def default_timeout(self) -> int:
        return 1200

    def is_available(self) -> bool:
        return shutil.which("fx") is not None

    def build_command(
        self, prompt: str, model: str, *, timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        if not isinstance(prompt, str) or not prompt.strip() or "\0" in prompt:
            raise FxPromptInvalid("fx requires a nonempty UTF-8 prompt without NUL bytes")
        try:
            prompt.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise FxPromptInvalid("fx requires a valid UTF-8 prompt") from exc
        missing = self.missing_flags(FX_REQUIRED_FLAGS)
        if missing:
            raise FxFlagsUnconfirmed(missing, self.gate_binary(runnable=True) or "fx")
        return ["fx", "ask", "--json", "--no-save", "--auto", "--model", model, "--", prompt]

    def build_command_for_transport(
        self, prompt: str, model: str, transport: str = "argv",
        prompt_file: Optional[str] = None, *, timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None, sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        if transport not in self.supported_prompt_transports:
            raise ValueError(f"fx does not support the {transport!r} prompt transport")
        argv = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        if transport == "stdin" or prompt in ("-h", "--help"):
            return argv[:-2], prompt
        return argv, None

    def build_agent_command(
        self, prompt: str, model: str, profile: str = "agent-readonly", *,
        timeout_s: Optional[int] = None, schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        if profile != PROFILE_GENERATE:
            return super().build_agent_command(prompt, model, profile, timeout_s=timeout_s, schema=schema)
        return self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)

    def build_agent_command_for_transport(
        self, prompt: str, model: str, profile: str = "agent-readonly",
        transport: str = "argv", prompt_file: Optional[str] = None, *,
        timeout_s: Optional[int] = None, schema: Optional[StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None, **options: Any,
    ) -> Tuple[List[str], Optional[str]]:
        if profile != PROFILE_GENERATE:
            return super().build_agent_command_for_transport(
                prompt, model, profile, transport, prompt_file,
                timeout_s=timeout_s, schema=schema, sandbox_fallback=sandbox_fallback, **options,
            )
        return self.build_command_for_transport(prompt, model, transport, timeout_s=timeout_s, schema=schema)

    @contextlib.contextmanager
    def hermetic_dispatch(
        self, profile: str, model: str = "", *, anchor: Optional[str] = None,
        runner_version: Optional[str] = None,
    ) -> Iterator[Optional[str]]:
        home = acquire_config_home()
        token = _ACTIVE_HOME.set(home)
        try:
            yield None
        finally:
            _ACTIVE_HOME.reset(token)
            release_config_home()

    def _env(self, source: Mapping[str, str]) -> Dict[str, str]:
        env = dict(FX_ENV)
        credential = source.get(FX_CREDENTIAL_ENV)
        if credential:
            env[FX_CREDENTIAL_ENV] = credential
        active = _ACTIVE_HOME.get()
        if active:
            env["HOME"] = active
            real_home = source.get("HOME") or os.path.expanduser("~")
            for key, suffix in (
                ("XDG_CONFIG_HOME", ".config"), ("XDG_CACHE_HOME", ".cache"),
                ("XDG_DATA_HOME", ".local/share"),
            ):
                env[key] = source.get(key) or str(Path(real_home) / suffix)
            gitconfig = source.get("GIT_CONFIG_GLOBAL")
            if gitconfig:
                env["GIT_CONFIG_GLOBAL"] = gitconfig
            else:
                try:
                    if (Path(real_home) / ".gitconfig").is_file():
                        env["GIT_CONFIG_GLOBAL"] = str(Path(real_home) / ".gitconfig")
                except OSError:
                    # Optional identity repair must not prevent dispatch when
                    # the inherited user's home is inaccessible (UID switches).
                    pass
            env["MULTI_LLM_FX_PATH"] = skill_environment_path(source.get("PATH", os.defpath))
        return env

    def get_env(self, model: str) -> Dict[str, str]:
        return self._env(os.environ)

    def resolve_env(self, model: str, profile: str = PROFILE_GENERATE, **options: Any) -> Dict[str, str]:
        env = super().resolve_env(model, profile, **options)
        source = options.get("base_env")
        if source is not None:
            # Remove get_env's ambient HOME repairs and credentials before
            # composing against the actual caller-supplied environment.
            for key in (FX_CREDENTIAL_ENV, "HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "GIT_CONFIG_GLOBAL", "MULTI_LLM_FX_PATH"):
                env.pop(key, None)
            env.update(self._env(source))
        return env

    def get_remove_env(
        self, anchor: Optional[str] = None, base_env: Optional[Mapping[str, str]] = None,
    ) -> List[str]:
        source = os.environ if base_env is None else base_env
        # Removals run AFTER the explicit delta; retain pinned FX_ENV names.
        return sorted({
            "AI_GATEWAY_API_KEY", "VERCEL_OIDC_TOKEN", "TYPESAFE_API_KEY", "TYPESAFE_BASE_URL",
            *(key for key in source if key.startswith("FX_") and key not in FX_ENV),
        })

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        envelope = _object(stdout)
        if envelope is not None:
            unknown = set(envelope) - _ENVELOPE_KEYS
            with _WARN_LOCK:
                fresh = unknown - _WARNED_KEYS
                _WARNED_KEYS.update(unknown)
            if fresh:
                warnings.warn("fx version drift: unknown JSON keys: " + ", ".join(sorted(fresh)), stacklevel=2)
        failure = _terminal_failure(envelope)
        if failure:
            return {
                "success": False, "data": None, "raw": stdout,
                "error": self.describe_failure(stdout, stderr) or failure,
                "error_code": "SUBPROCESS_FAILED",
            }
        return parse_answer_text(envelope["final_output"])

    def salvage_text(self, stdout: str) -> Optional[str]:
        envelope = _object(stdout)
        return "" if _terminal_failure(envelope) else envelope["final_output"].strip()

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Main-agent tokens only: fx excludes shell-reviewer usage and cost."""
        envelope = _object(stdout)
        usage = envelope.get("usage") if envelope else None
        if not isinstance(usage, dict):
            return None
        tokens = {
            key: usage[key] for key in ("input_tokens", "output_tokens")
            if type(usage.get(key)) is int and usage[key] >= 0
        }
        return tokens or None

    @staticmethod
    def _diagnostics(stdout: str, stderr: str) -> Tuple[str, str]:
        envelope = _object(stdout)
        diagnostic = ""
        if envelope and type(envelope.get("exit_code")) is int and envelope["exit_code"] == 1 and envelope.get("final_output") == "":
            output = envelope.get("output")
            if isinstance(output, str):
                diagnostic = "\n".join(match.group(0) for match in _HTTP.finditer(output))
        anchored = "\n".join(line for line in stderr.splitlines() if _STDERR.match(line))
        return diagnostic, anchored

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        return self._diagnostics(stdout, stderr)

    def classify_failure(self, stdout: str, stderr: str, exit_code: int = 0) -> Optional[str]:
        envelope = _object(stdout)
        error = envelope.get("error") if envelope else None
        if error == "MissingCredentials":
            return STATUS_AUTH_FAILED
        if error in ("InvalidChunk", "IncompleteStream", "InvalidToolName"):
            return CATEGORY_SERVER_ERROR
        if error == "NonInteractivePermissionRequired":
            return STATUS_RUNNER_ERROR
        if error in ("InvalidAskArgs", "InvalidProfileConfiguration", "UnknownConfiguredProvider"):
            return STATUS_RUNNER_ERROR
        if envelope and envelope.get("auth_failure"):
            return STATUS_AUTH_FAILED
        # A successful final turn cannot become a provider failure because a
        # shell printed a diagnostic-looking line or a transient retry recovered.
        if envelope and _terminal_failure(envelope) is None:
            return None
        output, anchored = self._diagnostics(stdout, stderr)
        evidence = output or "\n".join(line.removeprefix("fx ask: ") for line in anchored.splitlines())
        for match in _HTTP.finditer(evidence):
            status = int(match["status"])
            body = match["body"] or ""
            if status == 401:
                return STATUS_AUTH_FAILED
            if _BUDGET.search(body):
                return STATUS_RATE_LIMITED
            if status in (400, 502) and _INVALID_MODEL.search(body):
                return CATEGORY_INVALID_MODEL
            if status == 400 and _CONTEXT.search(body):
                return STATUS_CONTEXT_LENGTH_EXCEEDED
            if status == 403:
                return CATEGORY_PERMISSION_DENIED
            if status == 429:
                return STATUS_RATE_LIMITED
            if status >= 500:
                return CATEGORY_SERVER_ERROR
        if any(line.startswith("Agent step limit reached") for line in anchored.splitlines()):
            return STATUS_BUDGET_EXHAUSTED
        if re.search(r"^\[notice\] ⚠ .*HTTP 429\b", anchored, re.MULTILINE):
            return STATUS_RATE_LIMITED
        return None

    def classify_structural(self, stdout: str, stderr: str, exit_code: int = 0) -> Optional[Tuple[str, str]]:
        envelope = _object(stdout)
        if envelope:
            failure = _tool_failure(envelope)
            if failure or envelope.get("error") == "NonInteractivePermissionRequired":
                return STATUS_RUNNER_ERROR, failure or "fx requires interactive permission for the requested action"
        return None

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        envelope = _object(stdout)
        failure = _terminal_failure(envelope)
        if failure is None:
            return None
        if envelope and envelope.get("error") in ("InvalidProfileConfiguration", "UnknownConfiguredProvider"):
            return f"{failure}; check the managed HOME/.fx/settings.json"
        if envelope and envelope.get("error") == "InvalidAskArgs":
            return f"{failure}; check fx ask --json --no-save --auto --model"
        diagnostic, anchored = self._diagnostics(stdout, stderr)
        return diagnostic or failure + ("; " + anchored if anchored else "")
