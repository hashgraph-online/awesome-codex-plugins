"""Kimi Code (Moonshot) CLI provider implementation.

`@moonshot-ai/kimi-code` (MIT, npm, binary ``kimi``; distinct from the legacy
Python ``kimi-cli``). Everything below is measured against **0.36.1** in the
containerized probe of `plans/harness-expansion.md` §6 — stub-only,
``--network none``, no credential — and several measurements contradict the
plan's researched contract. Where they do, the measurement is what shipped and
the contradiction is recorded on the member it affects. The parser fixtures, the
retry chains, the effort inertness and the ``KIMI_MODEL_*`` family were
re-measured at **2.1.1** on 2026-10-08 (see ``verified_version``); the telemetry
DNS finding below was not.

**Output.** ``--output-format stream-json`` (valid only with ``-p``) emits JSONL
on stdout, one object per line. Assistant text is on **stdout**; thinking, tool
progress and notices are on **stderr**, which is *exactly 0 bytes* on a clean
run and carries one classified ``error: failed to run prompt: <class>: <detail>``
line on every failure. That clean split is the §0.1 (c) win kimi was admitted
on, and it is what makes :meth:`parse_output` short.

**Model selection — the slug travels in env, never in argv.** The
``KIMI_MODEL_*`` family synthesizes one provider and one model under the *fixed
literal ids* ``__kimi_env__`` / ``__kimi_env_model__``, and
``KIMI_MODEL_NAME`` is the upstream **wire slug**, not an alias. Passing the
slug to ``-m`` is a hard failure::

    $ kimi -m moonshotai/kimi-k2-thinking -p …      # KIMI_MODEL_NAME set to the same
    error: failed to run prompt: Model "moonshotai/kimi-k2-thinking" is not
    configured in config.toml.

The synthesized model is the CLI's default, so **omitting ``-m`` entirely is
correct** — verified byte-identical output to passing the literal alias. The
slug therefore appears exactly once, in ``get_env``, and there is no second
place for it to drift from. (This corrects the plan's §8 item 3 rule, which
required the slug in both places.)

**Prompt transport: argv only.** Measured on the wire, not inferred from an exit
code — ``-p -`` delivers the literal one-character prompt ``-`` rather than
reading stdin, ``-p @file`` delivers the literal path, ``--prompt-file`` does not
exist, and a bare ``kimi`` with piped stdin opens the TUI and hangs. So this
adapter is **argv-only — a large prompt exceeds the Windows command-line cap and
is refused before spawn** (``llm_client._prompt_length_error``). It serves every
fan-out mode on POSIX; on Windows a multi-KB prompt is refused with a structured
``PROMPT_TOO_LONG`` rather than truncated.

**Reasoning effort: declined.** ``KIMI_MODEL_THINKING_EFFORT`` exists as a name
but is **inert on the wire** at 0.36.1 — the request body is byte-identical with
and without it, and no ``reasoning_effort``/``thinking`` field is emitted. So no
``:effort`` suffix is parsed here: a third ``:``-segment is part of the model id
and passes through verbatim.

**Telemetry: the documented opt-out does not stop the connection attempt.**
``get_env`` sets ``KIMI_DISABLE_TELEMETRY=1`` — the CLI's own documented control,
and ``"1"`` really is in its true-value set — yet 0.36.1 resolves
``telemetry-logs.kimi.com`` twice on every run regardless. Reproduced offline
three ways (opt-out set, opt-out unset, and with ``KIMI_DISABLE_CRON=1``):
identical two queries each time, so the variable is not the problem and no other
``KIMI_*`` name reaches it (``KIMI_CODE_ALLOWED_HOSTS`` is an *inbound* host
allowlist for its daemon, not an egress control). The §7.4 lane's DNS allowlist
refuses the query, so nothing leaves the container — but on a host install there
is no such allowlist and the request goes out. Recorded here, in the
``providers.yaml`` block and in the README rather than worked around, and worth
re-checking on the next version bump.

**Tool permissions: rung 1, and rung 1 is the only rung that exists.** Every
permission-bearing flag is rejected outright in prompt mode (``Cannot combine
--prompt with --yolo|--auto|--plan``), so no flag can lower ``-p`` below its
``auto`` policy and none is emitted. The ship gate is therefore the §6.5 rule-6
filesystem canary, which measured **clean** across ask, review-plan, code-review,
a 12.9 KB prompt and a read-only bind mount whose prompt explicitly invited
edits: the working directory was never touched in any run, and every write landed
under the config root that :meth:`get_env` relocates per slot.
"""
import json
import os
import shutil
import tempfile
import threading
from typing import Any, Dict, List, Optional, Tuple

from ..json_extractor import extract_json_from_text
from .base import (
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
)

#: M12 (§6.1): kimi's position on the ladder is *declined*, and the module
#: docstring above is the measurement behind it. ``KIMI_MODEL_THINKING_EFFORT``
#: exists as a name but is inert on the wire at 0.36.1 — byte-identical request
#: body with and without it — so a ``:effort`` suffix would be a control that
#: reports success and changes nothing. No ``REASONING_EFFORTS`` is declared
#: here, which is what keeps a third ``:``-segment part of the model id.
#: Re-confirmed at 2.1.1 (2026-10-08): with and without
#: ``KIMI_MODEL_THINKING_EFFORT=high`` the request body differs only in the
#: session id and the working-directory listing kimi puts in its system prompt.
EFFORT_LADDER = ReasoningLadder(
    provider="kimi",
    declined=(
        "KIMI_MODEL_THINKING_EFFORT is inert on the wire at 0.36.1 (byte-identical "
        "request body with and without it), so no `:effort` suffix is parsed and a "
        "third `:`-segment stays part of the model id"
    ),
)

#: The retry knob this adapter pins, and the number it therefore declares.
#:
#: Measured at 0.36.1 against a fail-forever stub: **10** attempts with
#: exponential backoff capped near 38 s (0.55, 1.05, 2.38, 4.35, 8.63, 17.56,
#: 33.47, 38.02, 35.61 s), 145 s for one whole dispatch, and a 429 chain that
#: behaves identically. Re-measured at 2.1.1 (2026-10-08): the same 10
#: attempts, 145.4 s for the 5xx dispatch, 134.7 s for the 429 one.
#: `claude_code.py` is the committed precedent for pinning the knob and
#: declaring the pinned number rather than the out-of-the-box one:
#: budgeting for 10 requests would reserve a slot's whole deadline for a
#: configuration this harness never runs.
#:
#: `1` — not a smaller-but-nonzero number — because the shared ``RetryLadder``
#: is the one retry authority in this codebase (adapters never loop), and a CLI
#: retrying underneath it spends the slot's budget invisibly.
KIMI_LOOP_MAX_ATTEMPTS_PER_STEP = 1

#: The output ceiling this adapter pins, and it is load-bearing rather than
#: hygiene.
#:
#: Measured 2026-08-17: kimi derives the request's ``max_tokens`` from its
#: synthesized model's context size and sends **131072** on every call. Several
#: OpenRouter upstreams cap output well below that and reject the request
#: outright rather than clamping it — the live smoke died on
#: ``400 Provider returned error`` whose raw body read *"Requested maximum tokens
#: of 131072 exceeds the maximum output tokens limit: 102400"*. So an unpinned
#: kimi does not answer at all on those providers, and the failure arrives from
#: the upstream with the vendor's own wording rather than from anything this
#: repo can classify.
#:
#: The asymmetry §3.1 states for copilot decides the value: a ceiling that is too
#: large fails late and mid-flight, a bound that is too small fails early and
#: legibly. 8192 output tokens is several times what any fan-out mode's JSON
#: document needs (a suggestion list is a few KB), and it is far under every
#: published cap. It is also §7.4's required per-CLI output ceiling for the
#: credentialed lane's spend bound.
#:
#: ``KIMI_MODEL_MAX_TOKENS`` is the name that carries it. Three others move the
#: same field (``MAX_OUTPUT_SIZE``, ``MAX_COMPLETION_TOKENS``, and
#: ``MAX_CONTEXT_SIZE`` as a side effect); this is the one that names the wire
#: field it sets, and the other three stay in the strip list so a user's stale
#: export cannot quietly raise the ceiling back.
KIMI_MODEL_MAX_TOKENS = 8192

#: Prefix under ``TMPDIR``, so a directory leaked by a SIGKILL is sweepable by
#: name — the same rule ``cursor_agent``'s profile isolation follows.
_HOME_PREFIX = "multi-llm-kimi-"

_HOME_LOCK = threading.Lock()
#: Every config root **this process created**. Nothing outside this list is ever
#: removed: a user-pinned ``KIMI_CODE_HOME`` is respected, never deleted.
_HOME_DIRS: List[str] = []
_HOME_ATEXIT_REGISTERED = False

#: The variable that relocates kimi's entire writable state — ``device_id``,
#: ``config.toml``, ``logs/``, ``workspaces.json``, ``session_index.jsonl``,
#: ``sessions/<ws>/<session>/``, and a 16-shard ``cache/query-store/``. Verified:
#: with it set, the canary is clean; without it, all of the above lands in the
#: user's real ``$HOME/.kimi-code/``. Unlike copilot there is no second cache
#: path to chase, so this one name is the whole isolation story.
_HOME_ENV_VAR = "KIMI_CODE_HOME"

#: The complete ``KIMI_MODEL_*`` family as read out of the 0.36.1 bundle —
#: **18 names, not the 6 the vendor documents.** §8.2 defines the strip list as
#: "every name the adapter does not set", so this is the list that rule is
#: applied to; the four this adapter *does* set are excluded in
#: :meth:`get_remove_env`. A user-exported ``KIMI_MODEL_BASE_URL`` that survived
#: would silently re-point the synthesized model at somebody else's endpoint.
_KIMI_MODEL_VARS: Tuple[str, ...] = (
    "KIMI_MODEL_ADAPTIVE_THINKING",
    "KIMI_MODEL_API_KEY",
    "KIMI_MODEL_BASE_URL",
    "KIMI_MODEL_CAPABILITIES",
    "KIMI_MODEL_DISPLAY_NAME",
    "KIMI_MODEL_FIELDS",
    "KIMI_MODEL_MAX_COMPLETION_TOKENS",
    "KIMI_MODEL_MAX_CONTEXT_SIZE",
    "KIMI_MODEL_MAX_OUTPUT_SIZE",
    "KIMI_MODEL_MAX_TOKENS",
    "KIMI_MODEL_NAME",
    "KIMI_MODEL_OUTPUT_FORMAT",
    "KIMI_MODEL_PROVIDER_TYPE",
    "KIMI_MODEL_REASONING_KEY",
    "KIMI_MODEL_TEMPERATURE",
    "KIMI_MODEL_THINKING_EFFORT",
    "KIMI_MODEL_THINKING_KEEP",
    "KIMI_MODEL_TOP_P",
)

#: The four the B1 selector set owns (§2.2 rule 2: emitted as one indivisible
#: set, never partially). ``KIMI_MODEL_NAME`` is the *enable switch* — verified:
#: with none of the family set, ``kimi provider list --json`` returns
#: ``{"providers":{},"models":{}}`` and the CLI silently reverts to its
#: config-file route.
_INJECTED_MODEL_VARS: Tuple[str, ...] = (
    "KIMI_MODEL_NAME",
    "KIMI_MODEL_API_KEY",
    "KIMI_MODEL_BASE_URL",
    "KIMI_MODEL_PROVIDER_TYPE",
    # Not a selector, but injected all the same, so it belongs here rather than
    # in the strip list -- see KIMI_MODEL_MAX_TOKENS for why an unpinned kimi
    # cannot answer at all on a capped upstream.
    "KIMI_MODEL_MAX_TOKENS",
)

#: B3 and legacy names confirmed present in the 0.36.1 bundle. Stripped so a
#: stale export cannot re-select the Moonshot subscription route underneath BYOK
#: (§2.2 rule 3: adapter wins, ambient loses, no fallback). ``KIMI_API_KEY`` is
#: the documented gotcha — verified inert **on its own**, but stripped anyway
#: because a value we strip must never also be a value anything branches on.
#: ``KIMI_LOOP_MAX_RETRIES_PER_STEP`` is the deprecated alias of the knob pinned
#: above: left in place it still works, and prints a deprecation warning onto the
#: stderr channel this adapter's failure classification reads.
_STRIPPED_VENDOR_VARS: Tuple[str, ...] = (
    "KIMI_API_KEY",
    "KIMI_BASE_URL",
    "KIMI_API_KEY_ENV",
    "KIMI_BASE_URL_ENV",
    "KIMI_DEFAULT_BASE_URL",
    "KIMI_CODE_BASE_URL",
    "KIMI_CODE_BASE_URL_ENV",
    "KIMI_CODE_CUSTOM_HEADERS",
    "KIMI_CODE_CUSTOM_HEADERS_ENV",
    "KIMI_CODE_OAUTH_HOST",
    "KIMI_CODE_OAUTH_KEY",
    "KIMI_CODE_CACHE_DIR",
    "KIMI_CODE_PASSWORD",
    "KIMI_LOOP_MAX_RETRIES_PER_STEP",
    # Read by the 2.1.1 bundle (2026-10-08): when true, EVERY failed request is
    # retried without end, past the pinned KIMI_LOOP_MAX_ATTEMPTS_PER_STEP.
    # Measured against a 401 stub: one request and exit 1 in 0.9 s without it,
    # seven requests, no stderr and no exit after 40 s with it exported.
    "KIMI_CODE_INFINITE_RETRY",
)


def _create_home_dir() -> str:
    """A fresh 0700 config root, owned and tracked by this process."""
    global _HOME_ATEXIT_REGISTERED

    path = tempfile.mkdtemp(prefix=_HOME_PREFIX)
    os.chmod(path, 0o700)  # mkdtemp already does this; asserted, not assumed
    _HOME_DIRS.append(path)
    if not _HOME_ATEXIT_REGISTERED:
        import atexit

        atexit.register(cleanup_home_dirs)
        _HOME_ATEXIT_REGISTERED = True
    return path


def isolated_home_dirs() -> Tuple[str, ...]:
    """Every config root this process created and has not yet removed."""
    with _HOME_LOCK:
        return tuple(_HOME_DIRS)


def cleanup_home_dirs() -> None:
    """Remove every config root this process created. Never raises.

    Registered with ``atexit`` at the first creation. Containment must never be
    the thing that fails a run, so a directory that cannot be removed is left
    behind under a known prefix rather than propagating an exception out of
    interpreter shutdown.
    """
    with _HOME_LOCK:
        paths, _HOME_DIRS[:] = list(_HOME_DIRS), []
    for path in paths:
        shutil.rmtree(path, ignore_errors=True)


def last_assistant_content(stdout: str) -> Optional[str]:
    """Step 1 of :meth:`KimiProvider.parse_output`: the answer text, or ``None``.

    The **last** ``role: "assistant"`` record's string ``content``, and
    ``None`` when the stream has no such record (meta records only). Filtering
    on ``role`` is the point: the trailing ``session.resume_hint`` meta record
    also carries ``content``. Shared by the parser and :meth:`salvage_text`, so
    the ask lane's answer text is the text the parser reads
    (plans/ask-answer-recovery-and-false-success.md D2.5). Never raises; a
    non-string is read as an empty stream.
    """
    answer: Optional[str] = None
    # Split on "\n" only: `str.splitlines` also breaks on U+2028/U+2029 and
    # U+0085, which JSON leaves unescaped inside a string, so an answer holding
    # one would tear its own record in two and read as no answer at all.
    lines = stdout.split("\n") if isinstance(stdout, str) else []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            # A truncated final line is expected when a stream is cut
            # mid-record; earlier complete records still count.
            continue
        if isinstance(record, dict) and record.get("role") == "assistant":
            content = record.get("content")
            if isinstance(content, str):
                answer = content
    return answer


def reset_home_dirs() -> None:
    """Drop this process's tracking list without removing anything (tests)."""
    with _HOME_LOCK:
        _HOME_DIRS[:] = []


class KimiProvider(LLMProvider):
    """Provider for Moonshot's Kimi Code CLI.

    ``kimi --output-format stream-json -p <prompt>`` — no ``-m``, because the
    model is selected entirely through ``KIMI_MODEL_NAME`` (see the module
    docstring). Declares no ``:effort`` suffix and no non-argv transport, both
    measured rather than assumed.
    """

    #: §8.3: flags first, the ``-p <prompt>`` pair trailing. Confirmed legal at
    #: 0.36.1 — ``-p`` takes exactly one value, the flags are order-independent,
    #: and ``--output-format stream-json`` still applies with ``-p`` last (which
    #: is the shape every successful probe run used). Note the pair: a future
    #: non-argv transport would have to drop ``-p`` **and** the prompt, not
    #: ``cmd[:-1]`` — but kimi has no such transport (module docstring).
    prompt_argv_index = -1

    version_cmd = ("kimi", "--version")
    #: 0.36.1 is where every fixture in ``tests/fixtures/kimi/`` was first
    #: captured and the floor this parser is known to handle. kimi moved 0.33.0 →
    #: 0.36.1 in three days, so this is a pin to re-confirm rather than a range
    #: to trust.
    #:
    #: 2026-10-08: every captured row re-run on 2.1.1 (the image's pin) by the
    #: same probe servers through the container wrapper. The stream-json grammar
    #: and every stderr line are unchanged apart from the ``system.version``
    #: value, the session ids and the ``See log:`` path; the one measured move is
    #: a 400 context overflow costing 4 POSTs instead of 3. ``min_version`` stays
    #: at 0.36.1: nothing the parser reads changed, so the older capture is
    #: still the floor it is known to handle.
    min_version = "0.36.1"
    verified_version = "2.1.1"

    #: Measured at 0.36.1, every field (§6.1.1), and re-measured at 2.1.1 on
    #: 2026-10-08. ``max_wall_s`` is ``None`` because no bound here is one this
    #: adapter can set: a honoured ``Retry-After`` is server-chosen (a 20 s
    #: header produced gaps of exactly 20.02 s at 0.36.1, 20.01-20.03 s at
    #: 2.1.1), and no ``KIMI_*`` request-timeout knob exists (the
    #: ``KIMI_*TIMEOUT*`` names are MCP and subagent only). CORRECTION, 2026-10-08:
    #: an earlier note here said a stalled request has **no** client-side
    #: timeout. It has one, fixed at ~300 s: at 2.1.1 a stall ends the request
    #: with ``APITimeoutError`` / ``provider.connection_error: Request timed
    #: out.`` after 301.6 s (exit 1 at 302 s with the pinned single attempt), and
    #: the probe's own 0.36.1 evidence shows the same ~301 s per attempt (ten of
    #: them, 3,155 s). The "no output within 420 s" reading was the probe
    #: buffering stdout until exit. The value is kimi's, not a knob, so this
    #: declaration stays ``None`` and the plugin's outer timeout stays the
    #: bound rule 4 relies on.
    #:
    #: ``retries_rate_limit`` is ``True``: a 429-forever stub produced the same
    #: 10-attempt chain (0.36.1 and 2.1.1 alike), so §7.5 rule 6(b) must
    #: suppress an identical harness-side rate-limit re-dispatch.
    internal_retries = InternalRetryEnvelope(
        max_requests=KIMI_LOOP_MAX_ATTEMPTS_PER_STEP,
        max_wall_s=None,
        retries_rate_limit=True,
        configurable_by=("KIMI_LOOP_MAX_ATTEMPTS_PER_STEP",),
    )

    #: kimi's own classified stderr vocabulary, added to the base sets. The
    #: prefixes are what make these specific: ``provider.auth_error:`` and
    #: ``provider.rate_limit:`` are emitted verbatim ahead of the upstream text.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "provider.auth_error",
    )
    rate_limit_patterns = LLMProvider.rate_limit_patterns + (
        "provider.rate_limit",
    )

    # exit_zero_failure_markers is deliberately EMPTY and that is a measurement,
    # not an omission: across 27 probe runs the exit code was authoritative in
    # every shape — 0 on success, 1 on auth failure, rate limit, invalid model,
    # context overflow, a truncated stream, a masked error envelope and a
    # refused connection alike. Adding a marker here would be guessing at a
    # failure mode this CLI does not have.

    @property
    def name(self) -> str:
        return "kimi"

    @property
    def default_timeout(self) -> int:
        # 1200 s, matching the providers.yaml block. Generous on purpose: with
        # the retry knob pinned to a single attempt a dispatch is one request,
        # and a *stalled* upstream ends inside the child only at kimi's own
        # ~300 s request timeout (measured at 2.1.1, see internal_retries) --
        # a value no knob sets, so this outer timeout is the bound the plugin
        # owns.
        return 1200

    def is_available(self) -> bool:
        return shutil.which("kimi") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """``kimi --output-format stream-json -p <prompt>``.

        ``model`` is deliberately **not** rendered into argv: it travels in
        ``KIMI_MODEL_NAME`` (module docstring), and passing it to ``-m`` is a
        hard failure. It is still a parameter because the base class's contract
        and every caller pass it, and because :meth:`get_env` — which receives
        the same value from the same dispatch — is where it lands.

        ``timeout_s`` and ``schema`` are both ignored: kimi has no wall-clock
        flag and declares no structured-output support, so both keywords render
        argv byte-identical to omitting them (§1's guard).
        """
        return ["kimi", "--output-format", "stream-json", "-p", prompt]

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """§3.4's two-step unwrap: JSONL envelope → answer text → JSON document.

        **Step 1** parses stdout as JSONL, keeps records whose ``role`` is
        ``"assistant"``, and takes the **last** one's ``content``.

        Filtering on ``role`` is mandatory rather than stylistic, and this is the
        trap the probe found that the plan did not know about: the trailing
        ``session.resume_hint`` meta record **also carries a ``content`` key**
        (``"To resume this session: kimi -r …"``). The obvious implementation —
        "the last record with a content field" — therefore returns the resume
        hint as the model's answer, on every single successful run.

        A run with no assistant record at all is a **failure**, not an empty
        answer. That is what makes an all-noise stream classify correctly: a
        5xx-forever run emits ``system.version`` plus nine
        ``turn.step.retrying`` meta records and nothing else, and reporting that
        as an empty success would hand reaggregation a run that never happened.

        **Step 2** is the shared ``extract_json_from_text``, which handles fenced
        blocks and prose-wrapped JSON. It is step 2, never a fallback: handing it
        an un-unwrapped stream would let it find the *envelope's* braces and
        serve kimi's bookkeeping to reaggregation as the model's answer.
        """
        answer = last_assistant_content(stdout)

        if answer is None:
            return {
                "success": False,
                "error": (
                    "no assistant record in kimi stream-json output "
                    "(the run produced only meta records)"
                ),
                "raw": stdout,
                "data": None,
            }
        if not answer.strip():
            return {
                "success": False,
                "error": "Empty assistant content",
                "raw": stdout,
                "data": None,
            }
        return extract_json_from_text(answer, prefer_arrays=True)

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last assistant record's ``content``, never the JSONL stream.

        Step 1 of :meth:`parse_output` (:func:`last_assistant_content`), so the
        ask lane's answer text and the review lanes' salvage read what the
        parser treats as the answer (plans/ask-answer-recovery-and-false-
        success.md D2.5). ``""`` when there is no assistant record or its
        content is blank: a stream of meta records only, the resume hint whose
        ``content`` is not an answer, a text-mode stdout the adapter never asks
        for. ``generate`` always renders ``--output-format stream-json``, so the
        verdict is final and stderr's diagnostics never stand in for it.
        """
        try:
            answer = last_assistant_content(stdout)
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""
        return answer if answer is not None and answer.strip() else ""

    # describe_failure is deliberately NOT overridden. That hook exists for a CLI
    # that reports its errors on *stdout*, where a non-zero exit would otherwise
    # discard them (opencode and muse are the two). kimi is the opposite case by
    # measurement: every failure shape prints one classified
    # `error: failed to run prompt: <class>: <detail>` line on **stderr**, which
    # the caller already surfaces verbatim. An override here would re-print what
    # the user can already read, and `test_stdout_error_providers_are_the_only_
    # overrides` pins that roster at exactly the two CLIs that need it.

    def get_env(self, model: str) -> Dict[str, str]:
        """The B1 selector set, the pinned retry knob, and a per-slot config root.

        §2.2 rule 2 — **selection is total, never partial**. All four selector
        variables are emitted together for every ``(model, profile)``, including
        the base URL when the key is empty: a half-set is the bug that rule
        exists to prevent, because ``KIMI_MODEL_NAME`` is the enable switch and
        omitting any member makes the whole family inert, at which point the CLI
        silently reverts to its config-file route and answers on somebody else's
        credential.

        The endpoint is OpenRouter and the key is the single
        ``OPENROUTER_API_KEY`` (§2.1). The base URL **must carry ``/v1``**:
        measured, kimi appends ``/chat/completions`` to it verbatim and inserts
        no version segment of its own.
        """
        env = {
            "KIMI_MODEL_NAME": model,
            "KIMI_MODEL_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),
            "KIMI_MODEL_BASE_URL": "https://openrouter.ai/api/v1",
            "KIMI_MODEL_PROVIDER_TYPE": "openai",
            # The pinned output ceiling. Without it kimi asks for 131072 output
            # tokens on every call and a capped upstream rejects the request
            # rather than clamping it -- measured against the real endpoint.
            "KIMI_MODEL_MAX_TOKENS": str(KIMI_MODEL_MAX_TOKENS),
            # The pinned retry knob — see internal_retries for why 1, and why
            # the declared number is this one rather than the measured 10.
            "KIMI_LOOP_MAX_ATTEMPTS_PER_STEP": str(KIMI_LOOP_MAX_ATTEMPTS_PER_STEP),
            # Both confirmed present in the 0.36.1 bundle. The auto-updater
            # would otherwise move the binary underneath a pinned parser, and
            # telemetry is not something a fan-out slot should emit on the
            # user's behalf.
            "KIMI_CODE_NO_AUTO_UPDATE": "1",
            "KIMI_DISABLE_TELEMETRY": "1",
        }
        home = self._home_dir_for_spawn()
        if home is not None:
            env[_HOME_ENV_VAR] = home
        return env

    def _home_dir_for_spawn(self) -> Optional[str]:
        """A fresh config root for this spawn, or ``None`` to leave it alone.

        Per **slot**, not per run: two fan-out slots on kimi write
        ``session_index.jsonl``, ``workspaces.json`` and a 16-shard query-store
        cache under this root, and sharing one root between concurrent slots is
        the corruption ``test_cursor_profile_isolation.py`` exists to prevent.

        ``None`` when the user pinned ``KIMI_CODE_HOME`` themselves — their
        directory is respected and never removed — or when a temp directory
        cannot be created, because refusing a slot over a containment mechanism
        would be a worse trade than running without it.
        """
        if os.environ.get(_HOME_ENV_VAR):
            return None
        with _HOME_LOCK:
            try:
                return _create_home_dir()
            except OSError:  # noqa: BLE001 - containment must never fail a run
                return None

    def get_remove_env(self) -> List[str]:
        """Every ``KIMI_MODEL_*`` name this adapter does not set, plus the B3 set.

        §8.2's rule verbatim: an unset member of the family that survives from
        the user's shell re-points the synthesized model. ``KIMI_MODEL_BASE_URL``
        is the sharp one — it is *in* the injected set, so it is overwritten
        rather than stripped, but ``KIMI_MODEL_MAX_CONTEXT_SIZE`` or
        ``KIMI_MODEL_TEMPERATURE`` left over from a user's own kimi session would
        silently reshape a fan-out request nobody configured.
        """
        return [
            name for name in _KIMI_MODEL_VARS if name not in _INJECTED_MODEL_VARS
        ] + list(_STRIPPED_VENDOR_VARS)
