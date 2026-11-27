"""JetBrains Junie CLI provider implementation.

Junie is a proprietary JVM application (a jpackage launcher with a bundled JRE;
use is subject to the JetBrains AI Service terms). Everything below was
measured against **26.11.3 (build 4171.6)** with the real binary pointed at a
localhost OpenAI-compatible stub; the captures are ``tests/fixtures/junie/``.

**Model route: a custom model profile, never a JetBrains account.** Junie reads
custom models from JSON profiles; the file's stem is the profile id, selected
with ``--model custom:<stem>``. :meth:`JunieProvider.get_env` writes one profile
per spawn, :data:`PROFILE_NAME`, into a private root, with the OpenRouter slug
as its ``id`` and ``apiKey: "${OPENROUTER_API_KEY}"``, a reference Junie
resolves from the child's environment, so the file never holds the key.
``JUNIE_MODEL_LOCATIONS`` names the directory and ``--model-default-locations
false`` keeps a repository's own ``.junie/models/<stem>.json`` from shadowing it
(measured: a project profile of the same name is not read). The built-in
OpenRouter provider is not used: it accepts only a fixed alias catalog.

**State isolation needs two variables.** The JVM resolves its home from the
``user.home`` system property, not ``$HOME``, so ``JUNIE_HOME`` alone still
leaves the launcher writing ``~/.junie/logs``. Every spawn sets both
``JUNIE_HOME`` and ``JAVA_TOOL_OPTIONS=-Duser.home=<root>`` (appended to the
user's own options; a later ``-D`` wins). ``_JAVA_OPTIONS`` is applied after
``JAVA_TOOL_OPTIONS`` and could move the home back, so it is stripped. The JVM
announces the option on stderr (``Picked up JAVA_TOOL_OPTIONS: …``); that line
is the runtime's, not Junie's. ``junie --version`` and ``junie --help`` (the
doctor, preflight and flag-gate probes, one shared gate for every adapter) run
with the inherited environment, so each writes one log file into the user's own
``~/.junie/logs`` once per process.

**Repository configuration that can run code is switched off.** Headless Junie
starts a repository's ``.junie/mcp/mcp.json`` stdio servers and loads its
skills, commands, agents and ``config.json`` (measured with Junie's defaults: a
canary MCP server ran and the repository's skill reached the request, although
the vendor docs say an untrusted project is isolated). The argv turns every one
of those default locations off; with them off the same repository left no
canary file, and its skill, command, profile and config were absent from every
request. Hooks in a repository's ``.junie/config.json`` are skipped by Junie
itself (a planted hook never fired; the same hooks passed through
``--config-location`` did). Extensions load only from ``$JUNIE_HOME/extensions``,
which is the private root here and empty. Guidelines stay on: ``AGENTS.md`` and
``.junie/rules/*.md`` reach the model the way they reach codex or claude-code.

**Side effects the adapter does not stop.** The JVM writes
``$HOME/.cache/dconf/user`` (measured under a throwaway ``HOME``), and Junie
contacted ``resources.jetbrains.com`` on a probe run despite
``--skip-update-check`` and ``--share-anonymous-statistics false``.

**Read-only: ``--allowed-tools``.** Unrestricted, headless Junie writes files
and runs shell commands with no approval. Every dispatch passes
``--allowed-tools`` with the read tools and ``submit`` only
(:data:`READ_ONLY_TOOLS`); measured, the request then advertises those seven
tools and a stub-forced ``create``, ``bash``, ``search_replace`` or
``spawn_subagent`` call comes back ``ERROR: Tool "<name>" is not available`` with
the working tree unchanged. Reads outside the working directory are allowed
(a system file opened by absolute path was returned), hence
:attr:`reads_outside_cwd`. An unknown
name in the list is accepted silently, so a misspelt tool narrows the tier
rather than widening it.

**Output: one JSON object on stdout, and the exit code is not a verdict.**
``--output-format json`` prints ``{"sessionId", "taskName", "result",
"changes", "llmUsage"}``; a failure adds ``errors`` (a list of strings). A run
that hit ``--max-steps`` exits **0** with ``errors`` and an empty ``result``, so
:meth:`parse_output` succeeds only on a whole envelope with no ``errors`` and a
non-blank ``result``. The answer is what the model passed to Junie's ``submit``
tool; a model that only replies in text is re-prompted and the run fails with
``Failed to pass user review after 6 attempts``. ``taskName`` is a title Junie
asks the model to write, so it is model text too.

**Retries.** Junie retries a 429 and a 5xx itself, with no flag or variable to
bound it, so :attr:`internal_retries` declares the measured chain with no wall
bound (a ``Retry-After`` is the server's to choose).
"""
import json
import os
import re
import shutil
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .base import (
    CATEGORY_INVALID_MODEL,
    LAUNCH_DIAGNOSTICS_STDERR,
    VERSION_TOO_LOW,
    REASONING_LADDER,
    STDOUT_ENVELOPE,
    STDOUT_PLAIN,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    USAGE_FULL,
    diagnostic_streams,
    envelope_signature,
    read_stdout,
    split_reasoning_effort,
)
from .parse_kit import answer_from_text, fail
from .private_home import PrivateHomes

#: ``--effort <name>`` selects one of the efforts the profile declares, and
#: Junie sends it as ``reasoning_effort`` on the chat request (measured at the
#: stub: ``high`` on every request of the run). A profile that declares no
#: efforts refuses ``--effort`` (``Effort 'high' is not supported``), and one that
#: declares several picks a default of its own on every request, so the profile
#: declares exactly the requested effort. With no effort asked for the profile
#: declares none, and Junie then applies its own catalog's default for a model id
#: it recognises (``openai/gpt-6-luna`` went out with ``reasoning_effort: high``)
#: and sends no reasoning field for one it does not.
EFFORT_LADDER = ReasoningLadder(provider="junie", rungs=REASONING_LADDER)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: The profile's stem, so argv always reads ``--model custom:multi-llm`` and the
#: slug lives in the profile's ``id``.
PROFILE_NAME = "multi-llm"

#: The tools a dispatch may call: Junie's file readers and searches, and
#: ``submit``, which carries the answer. ``bash``, ``create``,
#: ``search_replace``, ``multi_edit``, ``undo_edit``, ``spawn_subagent`` and
#: ``agent_skill_read_doc`` are left out.
READ_ONLY_TOOLS = (
    "open", "open_entire_file", "scroll_down", "scroll_up",
    "glob_search", "grep_search", "submit",
)

#: ``--max-steps``: Junie's default is 150 agent steps; a review reads a few
#: files and submits. Reaching the cap is a failure (``errors``), never a
#: truncated answer.
JUNIE_MAX_STEPS = 60

#: The endpoint the profile names. ``apiType: OpenAICompletion`` posts to this
#: URL verbatim, so it carries the full ``/chat/completions`` path.
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
CREDENTIAL_ENV = "OPENROUTER_API_KEY"

#: The flags the read-only tier and the closed repository configuration rest
#: on. ``--allowed-tools`` is undocumented, so a build whose ``--help`` stops
#: listing any of these is refused rather than run unrestricted.
JUNIE_REQUIRED_FLAGS = (
    "--allowed-tools", "--output-format", "--max-steps", "--model",
    "--mcp-default-locations", "--config-default-locations", "--model-default-locations",
    "--skill-default-locations", "--command-default-location", "--agent-default-location",
)

#: Prefix under ``TMPDIR`` for the per-spawn roots (:class:`PrivateHomes`).
_HOME_PREFIX = "multi-llm-junie-"
_HOMES = PrivateHomes(_HOME_PREFIX)
isolated_home_dirs = _HOMES.isolated_home_dirs
cleanup_home_dirs = _HOMES.cleanup
reset_home_dirs = _HOMES.reset

#: Variables this adapter sets on every spawn; every other ``JUNIE_*`` name in
#: the inherited environment is stripped, because each one is a CLI setting
#: (``JUNIE_MODEL``, ``JUNIE_TASK``, ``JUNIE_TRUST_PROJECT``, a BYOK key that
#: would select a built-in provider) that would change what a dispatch runs.
_INJECTED = frozenset({"JUNIE_HOME", "JUNIE_MODEL_LOCATIONS"})

#: Applied by the JVM after ``JAVA_TOOL_OPTIONS``, so a user's ``-Duser.home``
#: there would undo the private root.
_STRIPPED_JAVA_VARS = ("_JAVA_OPTIONS",)

#: Junie's own stderr lines when a profile cannot be loaded because the key
#: variable is unset, the one auth failure that never reaches the endpoint.
_MISSING_KEY = re.compile(r"Environment variable '[A-Z_][A-Z0-9_]*' referenced in the model profile is not set")


class JunieFlagsUnconfirmed(RuntimeError):
    """Refuse a Junie build whose help no longer lists a flag the argv relies on."""

    def __init__(self, missing: Tuple[str, ...], binary: str):
        self.missing, self.binary, self.state = missing, binary, VERSION_TOO_LOW
        super().__init__(
            f"junie slot refused ({VERSION_TOO_LOW}): {binary} does not list "
            f"{', '.join(missing)} in junie --help, so the read-only tool tier or "
            "the closed repository configuration cannot be confirmed."
        )


def _java_options(root: str) -> str:
    """The user's ``JAVA_TOOL_OPTIONS`` with ``-Duser.home=<root>`` appended.

    The JVM splits the variable on whitespace and honours no quoting, so a root
    whose path holds whitespace is refused rather than split into two options.
    """
    if any(char.isspace() for char in root):
        raise OSError(f"junie's private root {root!r} contains whitespace; set TMPDIR to a path without it")
    return " ".join(
        part for part in (os.environ.get("JAVA_TOOL_OPTIONS", "").strip(), f"-Duser.home={root}")
        if part
    )


def render_profile(model: str, effort: Optional[str] = None, base_url: str = OPENROUTER_CHAT_URL) -> Dict[str, Any]:
    """The custom model profile for one spawn; it holds no credential value."""
    profile: Dict[str, Any] = {
        "baseUrl": base_url,
        "id": model,
        "apiType": "OpenAICompletion",
        "apiKey": "${" + CREDENTIAL_ENV + "}",
    }
    if effort is not None:
        profile["efforts"] = [effort]
        profile["defaultEffort"] = effort
    return profile


def _envelope(stdout: str) -> Optional[Dict[str, Any]]:
    """stdout as Junie's one JSON object, else ``None``."""
    if not isinstance(stdout, str):
        return None
    try:
        value = json.loads(stdout.strip())
    except ValueError:
        return None
    if isinstance(value, dict) and isinstance(value.get("sessionId"), str):
        return value
    return None


def _errors(envelope: Dict[str, Any]) -> List[str]:
    """The envelope's ``errors``, de-duplicated in order (Junie repeats them)."""
    raw = envelope.get("errors")
    if raw is None:
        return []
    if not isinstance(raw, list):
        return [json.dumps(raw)]
    seen: List[str] = []
    for item in raw:
        text = item if isinstance(item, str) else json.dumps(item)
        if text not in seen:
            seen.append(text)
    return seen


class JunieProvider(LLMProvider):
    """Provider for JetBrains' Junie CLI, headless, through a custom profile."""

    #: The prompt travels on stdin by default. The argv transport renders it as
    #: the trailing ``--task <prompt>`` pair, so a non-argv transport drops the
    #: pair, not only ``argv[-1]``. A positional or ``--task`` prompt of about
    #: 65 KB or more crashes the launcher (exit 139), while stdin carried 1 MB.
    prompt_argv_index = -1
    prompt_transport = "stdin"
    supported_prompt_transports: Tuple[str, ...] = ("stdin", "argv")

    #: The read-only tier has no write tool, so the answer comes back on stdout.
    supports_file_output = False
    supports_workspace_reads = True
    reads_outside_cwd = True
    #: ``bash`` is outside :data:`READ_ONLY_TOOLS`; a forced call is refused.
    runs_shell_in_generate = False

    usage_support = USAGE_FULL

    version_cmd = ("junie", "--version")
    #: ``junie --version`` prints ``Junie version: 26.11.3 (4171.6)``; the base
    #: parser reads the marketing version. The envelope keys the parser reads
    #: are vendor-internal, so the pin only warns above it.
    min_version = "26.11.3"
    verified_version = "26.11.3"

    install_hint = (
        "Install Junie CLI: curl -fsSL https://junie.jetbrains.com/install.sh | bash "
        "(or a checksummed release zip from github.com/JetBrains/junie/releases)."
    )
    auth_hint = (
        "Export OPENROUTER_API_KEY; the adapter writes a custom model profile per run, "
        "so no JetBrains account or Junie login is used."
    )

    #: Measured in the pinned image (tests/fixtures/junie/captures.json): a
    #: 429-forever endpoint drew 34 requests over 336 s before Junie gave up, a
    #: 500-forever one 47 over 155 s and a zero-byte response 48 over 157 s. No
    #: Junie setting changes any of these chains. Each of up to
    #: :data:`JUNIE_MAX_STEPS` agent steps (plus Junie's helper requests) can run
    #: such a chain, so no finite request bound holds (``max_requests=None``; the
    #: ``exit-zero-failure`` row made 62 requests without one retry).
    internal_retries = InternalRetryEnvelope(
        max_requests=None,
        max_wall_s=None,
        retries_rate_limit=True,
    )

    #: Junie relays the endpoint's 401 text after an ``OpenAI:`` prefix:
    #: OpenAI's wording, which the stub serves (tests/fixtures/junie/auth-error),
    #: and OpenRouter's answer to an unknown key (``OpenAI: User not found.``,
    #: measured against openrouter.ai). The last is Junie's own refusal when the
    #: profile's key variable is unset (``missing-key``).
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "incorrect api key provided",
        "user not found",
        "referenced in the model profile is not set",
    )

    #: :attr:`~.base.LLMProvider.EXIT0_CLASSIFIABLE`, reviewed: :meth:`vendor_text`
    #: reads the envelope without ``result``, ``taskName`` and ``changes`` (the
    #: model's words and file bodies), so what an exit-0 verdict reads is
    #: Junie's ``errors`` list and its stderr lines.
    EXIT0_CLASSIFIABLE = True

    #: stderr is the JVM's ``Picked up JAVA_TOOL_OPTIONS`` line, Junie's
    #: ``log file:`` line and its ``Junie failed with the message:`` verdict;
    #: the turn itself never reaches stderr.
    LAUNCH_DIAGNOSTICS = LAUNCH_DIAGNOSTICS_STDERR

    ENVELOPE_SIGNATURE = envelope_signature("sessionId")
    ENVELOPE_ANSWER_FIELDS = ("result", "taskName", "changes")

    @property
    def name(self) -> str:
        return "junie"

    def is_available(self) -> bool:
        return shutil.which("junie") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """The headless read-only argv; the slug itself travels in the profile.

        ``timeout_s`` and ``schema`` are ignored: Junie has no wall-clock flag
        and no structured-output mode.
        """
        missing = self.missing_flags(JUNIE_REQUIRED_FLAGS)
        if missing:
            raise JunieFlagsUnconfirmed(missing, self.gate_binary(runnable=True) or "junie")
        _, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = [
            "junie",
            "--skip-update-check",
            "--share-anonymous-statistics", "false",
            "--mcp-default-locations", "false",
            "--skill-default-locations", "false",
            "--command-default-location", "false",
            "--agent-default-location", "false",
            "--config-default-locations", "false",
            "--model-default-locations", "false",
            "--model", f"custom:{PROFILE_NAME}",
            "--allowed-tools", ",".join(READ_ONLY_TOOLS),
            "--output-format", "json",
            "--max-steps", str(JUNIE_MAX_STEPS),
        ]
        if effort is not None:
            cmd += ["--effort", effort]
        cmd += ["--task", prompt]
        return cmd

    def build_command_for_transport(
        self,
        prompt: str,
        model: str,
        transport: str = "argv",
        prompt_file: Optional[str] = None,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
        cwd: Optional[str] = None,
        **options: Any,
    ) -> Tuple[List[str], Optional[str]]:
        if transport not in self.supported_prompt_transports:
            raise ValueError(
                f"junie does not support the {transport!r} prompt transport "
                f"(supported: {', '.join(self.supported_prompt_transports)})"
            )
        argv = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        if transport == "stdin":
            return argv[:-2], prompt
        return argv, None

    def get_env(self, model: str) -> Dict[str, str]:
        """A private root holding Junie's home and this spawn's model profile.

        The root is per spawn, so concurrent slots never share Junie's session
        and log state, and it is removed with its dispatch
        (docs/development/providers.md#private-config-roots).
        """
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        root = _HOMES.create()
        models_dir = os.path.join(root, "models")
        os.mkdir(models_dir, 0o700)
        profile_path = os.path.join(models_dir, f"{PROFILE_NAME}.json")
        with open(profile_path, "w", encoding="utf-8") as handle:
            json.dump(render_profile(base_model, effort), handle)
            handle.write("\n")
        os.chmod(profile_path, 0o600)
        java_options = _java_options(root)
        return {
            "JUNIE_HOME": os.path.join(root, ".junie"),
            "JUNIE_MODEL_LOCATIONS": models_dir,
            "JAVA_TOOL_OPTIONS": java_options,
        }

    def get_remove_env(
        self,
        anchor: Optional[str] = None,
        base_env: Optional[Mapping[str, str]] = None,
    ) -> List[str]:
        """Every inherited ``JUNIE_*`` name this adapter does not set, and ``_JAVA_OPTIONS``."""
        source = os.environ if base_env is None else base_env
        return sorted(
            key for key in source
            if key.startswith("JUNIE_") and key not in _INJECTED
        ) + list(_STRIPPED_JAVA_VARS)

    #: OpenRouter's answer to an unknown slug, relayed in ``errors`` as
    #: ``OpenAI: <slug> is not a valid model ID`` (measured against
    #: openrouter.ai); the shared invalid-model markers do not cover it.
    _INVALID_SLUG = re.compile(r"\bis not a valid model ID\b")

    def classify_failure(self, stdout: str, stderr: str, exit_code: int = 0) -> Optional[str]:
        """The shared rule, then OpenRouter's unknown-slug wording in ``errors``."""
        verdict = super().classify_failure(stdout, stderr, exit_code)
        if verdict is not None:
            return verdict
        envelope = _envelope(stdout)
        if envelope and any(self._INVALID_SLUG.search(error) for error in _errors(envelope)):
            return CATEGORY_INVALID_MODEL
        return None

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """:func:`stdout_shape.diagnostic_streams`: the envelope without the model's words."""
        return diagnostic_streams(stdout, stderr, self)

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """The answer Junie's ``submit`` carried, or a failure naming ``errors``."""
        text = stdout.strip() if isinstance(stdout, str) else ""
        shape = read_stdout(text, self.ENVELOPE_SIGNATURE)
        if not text:
            missing = _MISSING_KEY.search(stderr or "")
            return fail(missing.group(0) if missing else "junie printed nothing on stdout", text)
        if shape.kind == STDOUT_PLAIN:
            return fail("junie did not print its JSON envelope", text)
        if shape.kind != STDOUT_ENVELOPE:
            return shape.failure("junie", text)
        envelope = shape.value
        if not isinstance(envelope, dict):
            return fail("junie printed a malformed envelope", text)
        errors = _errors(envelope)
        if errors:
            return fail("; ".join(errors), text)
        result = envelope.get("result")
        if not isinstance(result, str):
            return fail("junie's envelope carries no result", text)
        return answer_from_text(result, raw=text, empty_error="junie returned an empty result")

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The envelope's ``result`` when it has no ``errors``, else ``""``."""
        try:
            envelope = _envelope(stdout)
            if envelope is None or _errors(envelope):
                return ""
            result = envelope.get("result")
            return result.strip() if isinstance(result, str) else ""
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Token totals summed over ``llmUsage``; ``cost`` is never read.

        Junie reports ``cost: 0.0`` for a custom profile even on a billed
        OpenRouter call, so a cost here would read as a free run.
        """
        envelope = _envelope(stdout)
        rows = envelope.get("llmUsage") if envelope else None
        if not isinstance(rows, list) or not rows:
            return None
        totals = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            for out_key, in_key in (
                ("input_tokens", "inputTokens"),
                ("output_tokens", "outputTokens"),
                ("cached_input_tokens", "cacheInputTokens"),
            ):
                value = row.get(in_key)
                if type(value) is int and value >= 0:
                    totals[out_key] += value
                    seen.add(out_key)
        usage: Dict[str, Any] = {key: totals[key] for key in totals if key in seen}
        if "input_tokens" in usage and "output_tokens" in usage:
            usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
        return usage or None
