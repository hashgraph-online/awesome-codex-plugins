"""Qwen Code CLI provider implementation.

`@qwen-code/qwen-code` (npm, binary ``qwen``, provider key ``qwen-code``).
Originally a Gemini-CLI fork, independent since v0.1. Everything below is
measured against **0.21.13** in the containerized probe of
`plans/harness-expansion.md` §6 — stub-only, ``--network none``, no credential —
and several measurements contradict the plan's researched contract. Where they
do, the measurement is what shipped and the contradiction is recorded on the
member it affects.

**The defect that shapes this whole adapter: qwen exits 0 on total backend
failure.** Measured against a 500-forever stub, 28 requests over 93 s::

    rc              = 0
    result.subtype  = "success"
    result.is_error  = false
    result.result   = "[API Error: 500 internal server error]"
    stderr          = "" (0 bytes)

The process exit code says success, the envelope's own ``is_error`` flag says
success, ``subtype`` says success, and the model's "answer" is the error string.
So §6 step 3's two named traps — *errors on stdout with an empty stderr* (the
opencode trap) and *exit-0 failures* — **coincide in one shape**, which is the
worst case for a parser that checks either one alone. And it is not a 5xx quirk:
401, 404, 400-overflow and 500 all produce byte-identically shaped envelopes, so
one marker covers the whole class.

That is why :attr:`QwenCodeProvider.exit_zero_failure_markers` is mandatory here
rather than optional, and why :meth:`QwenCodeProvider.parse_output` classifies
*before* it unwraps.

**0.25.0 fixed the defect upstream** (re-captured 2026-10-08): the same
500-forever run now exits **1**, its ``result`` record is ``subtype:
"error_during_execution"``, ``is_error: true`` with the ``[API Error: …]`` text
under ``error.message`` and no ``result`` key, and stderr carries the same text
in an ``AlreadyReportedError`` JSON envelope — 401, 404, 400 and the truncated
streams alike. Rule 1 catches that shape; the marker stays for the 0.21.13 floor,
whose exit-0 bytes remain committed as ``*.0.21.13.stdout.json``.

**Output mode: ``-o json``, not ``stream-json``.** Both were captured.
``-o json`` emits **one JSON array** of records terminating in a ``result``
record that carries everything classification needs in a single object —
``result`` (the answer), ``is_error``, ``num_turns``, ``usage``, and a ``stats``
block. ``-o stream-json`` is JSONL with additional ``stream_event`` noise records
and its ``result`` record **drops the ``stats`` block**, which is the
corroborating failure signal. (This corrects §3.3's provisional ``stream-json``.)

**Prompt: a bare positional, because ``-p`` is deprecated.** At 0.21.13 the help
marks the flag ``[deprecated: Use the positional prompt instead. This flag will
be removed in a future version.]`` and declares a default positional
``qwen [query..]``. Both forms were measured working; the positional is the
non-deprecated one, and it puts the prompt at ``argv[-1]`` for free.

**Prompt transport: argv and stdin.** Measured on the wire with a 15,663-byte
prompt: argv, a bare redirect with **no prompt argument at all**, ``-p ""`` plus
a redirect, and a pipe with a short argv prompt all returned rc=0 and
byte-identical output. The help states the contract directly —
``-p, --prompt  Prompt. Appended to input on stdin (if any).`` So a multi-KB
prompt never has to be measured against the Windows command-line cap.

**Reasoning effort: declined.** There is no ``--effort``, thinking-level or
reasoning option anywhere in the full (hidden) help; the ``/effort`` slash
command is interactive-only. And the decline has to be *documented* rather than
left implicit, because the failure is silent: ``-m qwen3-coder-plus:high`` was
measured going to the backend **verbatim**, suffix included, where it becomes a
"model not found" with nothing pointing at the suffix.

**Tool permissions: tier 1, plus a rung narrower than tier 1.** The §6.5 ladder
was walked in ascending order and the bare invocation answered, so rule 1 forbids
promoting — no ``--approval-mode``, no ``--yolo``, no ``--add-dir``. The
filesystem canary was **clean at every rung** (nothing under the workspace
created, modified, deleted or renamed; the only writes were under the config root
:attr:`QWEN_HOME_ENV_VAR` relocates).

``--max-tool-calls 0`` is then shipped *below* tier 1, and it is the most
valuable thing this probe found: it means "no tool calls allowed (first call
aborts)", it fires **before** the call executes, and a backend that demanded an
``edit`` got exit 55 with the workspace untouched. That makes ``(generate,)`` a
real permission boundary rather than only a parsing decision — precisely what
§1's ship gate asks for — and it costs nothing on a well-behaved answer run.
Contrast the rungs above it: ``--approval-mode plan`` still advertises ``edit``,
``run_shell_command`` and ``notebook_edit`` in the session's tool list, and
``--yolo`` was blocked in the probe only by a read-before-edit precondition, not
by permission.

One consequence, stated so it is not mistaken for a defect later: with
``--max-tool-calls 0`` and no schema, a backend that insists on calling a tool
aborts the slot with exit 55 and zero bytes on stdout. That is the intended
trade — a loud, classifiable failure instead of a quiet workspace write.

**And it is not hypothetical: the §7.4 live smoke hit it.** The probe could not
see this, because the committed stub never emits tool calls; a *real* model does,
non-deterministically. On one trivial prompt against
``qwen/qwen3.8-max``, **4 of 14 live runs (~29%)** aborted with
``FatalBudgetExceededError: tool-call budget of 0 exceeded; observed 1`` while
the other ten answered normally. So the cost of this rung is real, measured, and
priced in rather than discovered later:

* the workspace stayed untouched, which is the whole point;
* the abort is **transport-shaped** to ``classify_failure`` (an unrecognized
  shape returns ``None``), so it takes the executor's bounded-retry path and a
  blocked tool call is normally recovered by the next attempt rather than
  failing the slot outright;
* :meth:`QwenCodeProvider._empty_stdout_reason` lifts qwen's own structured
  stderr envelope into the reported error, so the failure names the tool cap
  instead of saying "empty output" about a run whose cause was machine-readable
  all along.

**And that same 29% is the argument for keeping the rung, not against it.** It
is direct evidence that a real model *wants* to call a tool on a fraction of
ordinary prompts — so at bare tier 1 those calls would not be refused, they
would EXECUTE, in the user's own checkout, from a provider this adapter declares
``(generate,)``. The probe's clean canary was measured against a stub that never
emits a tool call and therefore never licensed the bare rung for a real backend;
this measurement is what settles it. Dropping the flag to make a smoke greener
would be §11's "yolo-flag creep" with the evidence pointing the other way.

The trade this leaves is a noisier provider: a ~29% first-attempt abort that the
retry ladder normally absorbs, at the price of a second call. ``--json-schema``
reduces it structurally — the synthetic ``structured_output`` tool is exempt from
the cap (measured), so a schema-carrying dispatch gives the model a sanctioned
way to finish.

**Structured output: supported, inline** (OQ2, closed at the probe). The flag is
spelled ``--json-schema`` and takes a JSON literal — the **same name and the same
shape as claude-code's** — so the inline branch needs no new machinery and no
``schema_sidecar`` is materialized. It really constrains the output (the wire log
shows a synthetic ``structured_output`` tool added to the request and the run
ending on its call, with the schema-conforming document in ``result``), and it
**fails closed**: a backend answering plain text instead exits 1 with
``Model produced plain text instead of calling the structured_output tool as
required by --json-schema``. A flag that appeared in help but did not constrain
would have been a ``False``.

*Known coverage gap, recorded rather than worked around*: ``--json-schema`` ends
the session on a **tool call**, and the committed ``stub_server.py`` never emits
tool calls — a deliberate, documented non-goal of the rig. So the container
provider lane cannot exercise this flag as the rig stands; its coverage is unit
tests plus the §7.4 live smoke. Growing the stub to emit a tool call is rig
growth, which §6 step 1 forbids at a probe.

**``--max-wall-time`` is load-bearing, not a nicety.** §6.1.1 measured that only
the 5xx path self-terminates: a 429-forever backend was still retrying past 180 s
with a growing-then-resetting backoff, and a stalled backend cost ~120 s per
request with no self-imposed ceiling. Wiring the flag from ``timeout_s=`` turns
"the slot hangs until the harness's outer timeout kills it" into a clean,
classifiable exit 55 *inside* the CLI, strictly below the outer bound.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import threading
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
)
from .result_envelope import envelope_verdict, parse_result_envelope

#: M12 (§6.1): qwen-code's position on the ladder is *declined*, carrying the
#: module docstring's measurement. There is no ``--effort``, thinking-level or
#: reasoning option anywhere in the full (hidden) help, and ``/effort`` is
#: interactive-only. The decline is written down rather than left implicit
#: because the failure is silent: ``-m qwen3-coder-plus:high`` was measured going
#: to the backend **verbatim**, suffix included, where it becomes a "model not
#: found" with nothing pointing at the suffix.
EFFORT_LADDER = ReasoningLadder(
    provider="qwen-code",
    declined=(
        "no --effort, thinking-level or reasoning option exists in the full "
        "(hidden) help and /effort is interactive-only; a `:effort` suffix would "
        "reach the backend verbatim as part of the model id"
    ),
)

#: Seconds by which qwen's own wall-clock cutoff is held UNDER the parent's
#: ``subprocess.run(timeout=…)`` deadline — agy's ``INNER_SHUTDOWN_MARGIN_S``
#: precedent, and the invariant §3.3 requires this adapter to encode.
#:
#: The margin is the point: qwen must reach its own bound, write its structured
#: ``FatalBudgetExceededError`` envelope to stderr and exit *before* the parent
#: fires, so the harness reports qwen's own reason instead of killing a live
#: child and reporting a bare TIMEOUT. 30 s matches agy's measured envelope-write
#: plus process-exit budget.
INNER_SHUTDOWN_MARGIN_S = 30

#: Floor for the derived cutoff, and a misconfiguration guard. qwen itself
#: **rejects** values below 1 s (``0``, ``0.5`` and ``500ms`` all exit 1 with
#: "below the 1s minimum"), so an unclamped derivation could render argv the
#: binary refuses outright. A sub-90 s qwen run is a mistake rather than an
#: intent, so the clamp is announced with exactly one WARNING naming both
#: numbers rather than applied silently.
MIN_INNER_TIMEOUT_S = 60

#: Turn cap, a **module constant on every invocation** — policy, not row-derived
#: (§7 step 6), so ``expected_argv.yaml`` keeps it verbatim. A fan-out slot asks
#: one question and reads one answer; 25 turns is far above anything a
#: `generate` dispatch legitimately needs and is a backstop against a model that
#: loops rather than a tuning knob.
MAX_SESSION_TURNS = 25

#: The §6.5 tool tier, expressed as argv. ``0`` means "no tool calls allowed;
#: the first one aborts the run" — see the module docstring for why this is a
#: rung *below* tier 1 and why it ships. Policy, verbatim in the pinned table.
MAX_TOOL_CALLS = 0

#: Prefix under ``TMPDIR``, so a directory leaked by a SIGKILL is sweepable by
#: name — the rule ``cursor_agent``'s profile isolation and ``kimi``'s config
#: root both follow.
_HOME_PREFIX = "multi-llm-qwen-"

_HOME_LOCK = threading.Lock()
#: Every config root **this process created**. Nothing outside this list is ever
#: removed: a user-pinned ``QWEN_HOME`` is respected, never deleted.
_HOME_DIRS: List[str] = []
_HOME_ATEXIT_REGISTERED = False

#: §8.2's "sharp open item", **answered by measurement — branch (a)**.
#:
#: §3.3 recorded that qwen "writes ``$HOME/.qwen/settings.json`` and exposes no
#: config-dir env var", and ranked a per-spawn ``HOME`` redirect as the likely
#: resolution. That is wrong at 0.21.13: ``QWEN_HOME`` exists and is exact — with
#: it set, ``installation_id``, ``usage/token-usage-YYYY-MM.jsonl``,
#: ``usage_record.jsonl`` and ``tmp/<sha>/scheduled_tasks.lock`` all land
#: **directly under** that directory, and ``$HOME/.qwen`` is **not created at
#: all** (verified from both a warm and a freshly wiped ``$HOME``). So it
#: replaces ``$HOME/.qwen`` itself rather than replacing ``$HOME``, and none of
#: the redirect's cost (re-injecting ``GIT_CONFIG_GLOBAL`` and friends) is
#: incurred.
#:
#: ``XDG_CONFIG_HOME``, ``QWEN_CODE_HOME`` and ``QWEN_CONFIG_DIR`` were measured
#: and are **not** honoured.
QWEN_HOME_ENV_VAR = "QWEN_HOME"

#: The B1 selector set (§2.2 rule 2). Emitted as one indivisible set for every
#: ``(model, profile)`` — see :meth:`QwenCodeProvider.get_env` for why a partial
#: set is the dangerous shape rather than a degraded one.
_OPENAI_TRIO: Tuple[str, ...] = ("OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL")

#: B3 and legacy names, all confirmed present in the 0.21.13 bundle. Stripped so
#: a stale export cannot re-select the vendor route underneath BYOK (§2.2 rule 3:
#: adapter wins, ambient loses, no fallback).
#:
#: ``OPENAI_API_BASE`` is the legacy alias and it is stripped for the reason
#: §3.3 rule 3 gives — *a strip is not a substitute for injecting the base URL*.
#: Measured: with ``OPENAI_API_BASE`` set and ``OPENAI_BASE_URL`` unset qwen made
#: **no request at all** (rc=1, "No auth type is selected"), so the alias is not
#: a live fallback; but it is in the bundle, and a value we strip must never also
#: be a value anything branches on.
_STRIPPED_VENDOR_VARS: Tuple[str, ...] = (
    "OPENAI_API_BASE",
    "QWEN_API_KEY",
    "QWEN_BASE_URL",
    "QWEN_CODE_MODEL",
    "QWEN_DEFAULT_AUTH_TYPE",
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_BASE_URL",
    "MODELSCOPE_API_KEY",
)

#: §A's marker, and the only reliable detector of a failed run.
#:
#: A **search**, never a prefix test: the truncated-stream shape concatenates
#: partial text across retry attempts and the marker arrives as a *suffix* —
#: ``"OKOKOKOKOK[API Error: Model stream ended without a finish reason.]"`` — so
#: ``startswith`` would miss it and serve ten characters of plausible-looking
#: content as the model's answer. ``matches_any`` already searches, which is why
#: this is a constraint on how the marker is written rather than new machinery.
_API_ERROR_MARKER = re.compile(r"\[API Error:")

#: qwen's startup ripgrep check, printed to stderr on EVERY run when the
#: bundled ``rg`` cannot be executed — an advisory, never a diagnosis.
#: Measured at 0.25.0 (2026-10-08): qwen restores a missing exec bit on its
#: vendored ``rg`` itself, so a user-owned install never prints it, but a
#: root-owned one (``sudo npm i -g``, a distro package, an image layer) cannot
#: and prints ``Ripgrep not available: spawn …/rg EACCES. Falling back to
#: built-in grep.``. That ``EACCES`` classified every run ``permission_denied``
#: — a 401, a 404 and a successful run alike — so :meth:`QwenCodeProvider.vendor_text`
#: drops exactly this line, both of its upstream wordings, and nothing else.
_RIPGREP_ADVISORY = re.compile(
    r"^Ripgrep not available: .*Falling back to built-in grep\.[ \t]*\r?\n?",
    re.MULTILINE,
)


def max_wall_time_value(timeout_s: Optional[int]) -> Optional[str]:
    """Render ``--max-wall-time`` for an outer deadline of ``timeout_s``.

    ``None`` in, ``None`` out — and that is §1's guard, not a convenience: a
    caller that passes no timeout must get argv **byte-identical** to omitting
    the keyword, so the flag is absent entirely rather than carrying a default.
    That is also what keeps ``expected_argv.yaml`` free of a "sometimes present"
    case.

    Bare integer seconds. Measured at 0.21.13: the flag accepts both bare
    seconds (``90``) and duration strings (``30s``, ``5m``, ``1h``, ``1.5h``) and
    **rejects** ``0``, ``0.5`` and ``500ms`` with exit 1 and "below the 1s
    minimum" — hence :data:`MIN_INNER_TIMEOUT_S`. The bare form is chosen because
    it removes a rounding rule instead of specifying one.
    """
    if timeout_s is None:
        return None
    outer = int(timeout_s)
    inner = max(MIN_INNER_TIMEOUT_S, outer - INNER_SHUTDOWN_MARGIN_S)
    if inner + INNER_SHUTDOWN_MARGIN_S > outer:
        print(
            f"WARNING: qwen timeout of {outer}s leaves nothing above the "
            f"{INNER_SHUTDOWN_MARGIN_S}s shutdown margin; --max-wall-time is "
            f"clamped to {MIN_INNER_TIMEOUT_S}s, so qwen will still be running "
            f"when the {outer}s deadline fires. Raise the configured timeout "
            f"to at least {MIN_INNER_TIMEOUT_S + INNER_SHUTDOWN_MARGIN_S}s.",
            file=sys.stderr,
        )
    return str(inner)


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


def reset_home_dirs() -> None:
    """Drop this process's tracking list without removing anything (tests)."""
    with _HOME_LOCK:
        _HOME_DIRS[:] = []


class QwenCodeProvider(LLMProvider):
    """Provider for Alibaba's Qwen Code CLI.

    ``qwen --bare --chat-recording false -o json --max-tool-calls 0
    --max-session-turns 25 [--max-wall-time <n>] [--json-schema <json>]
    [-m <model>] <prompt>`` — flags first, bare positional prompt last.

    Declares a stdin transport and inline structured output, both measured;
    declines the ``:effort`` suffix, also measured. See the module docstring.
    """

    #: §8.3: flags first, the prompt a **bare trailing positional**. Not a
    #: ``-p <prompt>`` pair — ``-p`` is deprecated at 0.21.13 — so this is dsh's
    #: shape rather than grok's, and a non-argv transport drops exactly one
    #: element. ``-1`` is *required* rather than preferred here, because
    #: ``test_last_element_assumption_holds_wherever_it_is_relied_on`` forces it
    #: on any adapter declaring a non-argv transport, which this one does.
    prompt_argv_index = -1

    #: Measured: the prompt travels as one argv element **or** on stdin with no
    #: prompt argument at all. ``prompt_transport`` (the fan-out default) stays
    #: ``"argv"``, as it does for claude-code, codex and opencode, which declare
    #: the same pair.
    supported_prompt_transports = ("argv", "stdin")

    #: ``--max-tool-calls 0`` (:data:`MAX_TOOL_CALLS`) is a **zero** budget, not
    #: an unlimited one, and it aborts *before* the first call executes — so this
    #: adapter can never write the ``{output_json_path}`` file the Lane A prompts
    #: used to demand, and the failure is harsher than a refusal sentence:
    #: ``FatalBudgetExceededError: tool-call budget of 0 exceeded`` on stderr,
    #: **exit 55 with zero bytes on stdout** (captured under
    #: ``plans/harness-expansion/probe-out/qwen-code/captures/block/``), which
    #: leaves ``invoke_with_file_output`` nothing to fall back to at all. It was
    #: measured live too: 4 of 14 runs (~29%) aborted this way against a backend
    #: that reached for a tool.
    #:
    #: The one exemption does not rescue the review path — only the synthetic
    #: ``structured_output`` tool is exempt from the budget, and the fan-out
    #: dispatches without a schema. So the prompt asks for stdout, which is the
    #: channel ``-o json`` gives and the one this adapter's parser already reads.
    supports_file_output = False

    #: MEASURED, from the same zero budget (:data:`MAX_TOOL_CALLS`, rendered as
    #: ``--max-tool-calls 0``): the abort fires *before* the first tool call
    #: executes (``FatalBudgetExceededError``, exit 55, zero bytes on stdout,
    #: ``plans/harness-expansion/probe-out/qwen-code/captures/block/``). A shell
    #: is a tool call, so none runs in ``generate``…
    runs_shell_in_generate = False

    #: …and neither does a file read: this lane cannot open even the plan, let
    #: alone the phase dir's diff files. ``"none"`` sends it down
    #: ``render_diff_access``'s inline branch (plan, manifest and diffs in the
    #: prompt, under the 96 KB argv-safe cap) or, over the cap or on partial
    #: diff coverage, to an explicit ``[REVIEW_UNSUPPORTED]`` that costs nothing.
    generate_read_scope = "none"

    version_cmd = ("qwen", "--version")
    #: 0.21.13 is where the fixtures were first captured and the floor this
    #: parser is known to handle (its exit-0 API-error shape stays graded by
    #: ``tests/fixtures/qwen-code/*.0.21.13.stdout.json``). qwen publishes fast
    #: (592 versions, with 0.21.12 → 0.21.13 plus a nightly inside the probe
    #: window), so this is a pin to re-confirm rather than a range to trust.
    #:
    #: 2026-10-08: every fixture re-captured on 0.25.0 in the pinned image. An
    #: API error is now an error record (exit 1, ``is_error: true``, the
    #: ``[API Error: …]`` text under ``error.message``, an
    #: ``AlreadyReportedError`` envelope on stderr) instead of an exit-0 success;
    #: retries no longer concatenate partial text; stderr gained retry lines.
    #: Retry counts (28 on 5xx, 44 in 180 s on 429) are unchanged. The floor
    #: stays: nothing here stopped handling 0.21.13.
    min_version = "0.21.13"
    verified_version = "0.25.0"

    #: OQ2, measured (see the module docstring). ``"inline"`` because the flag
    #: takes a JSON literal, exactly as claude-code's does — so the caller
    #: correctly skips ``structured_output.schema_sidecar``.
    structured_output_support = True
    structured_output_transport = "inline"

    #: Measured at 0.21.13 from the stub's request log (§6.1.1), **not** from the
    #: envelope: qwen's own ``stats.totalRequests`` reported 7 for a run the stub
    #: logged 28 completion POSTs for — a 4× understatement, because the retry
    #: structure is 4 wire requests per logical attempt (three fast inner retries
    #: at ~0.5/1/2 s) with a growing outer backoff between attempts. Re-measured
    #: at 0.25.0 (2026-10-08): 28 POSTs on 5xx again (88-107 s, now exit 1), and
    #: 429-forever still running at 180 s after 44 POSTs (12 with
    #: ``Retry-After: 60``). 0.25.0's error envelope carries no ``stats`` block.
    #:
    #: ``max_wall_s`` is ``None`` and that is the **honest** declaration rather
    #: than an unmeasured one. Only the 5xx path self-terminates (93 s); the 429
    #: path was still going at 180 s with a backoff that ramps to 60 s then
    #: *resets* rather than exhausting, and the stall path retries a ~120 s
    #: client timeout indefinitely. Declaring 93 would describe one path out of
    #: three and would misbudget every rate-limited slot. ``base.py`` defines
    #: ``None`` as "no bound this adapter can state", and rule 4 then performs no
    #: admission test — which §6.1.1 blesses explicitly.
    #:
    #: ``retries_rate_limit`` is ``True`` and emphatically so, which is what
    #: makes §7.5 rule 6(b) suppress an identical harness-side re-dispatch.
    #:
    #: ``configurable_by`` names only ``QWEN_CODE_API_TIMEOUT_MS``, the knob that
    #: sets the ~120 s stall timeout. It deliberately does **not** name
    #: ``QWEN_CODE_UNATTENDED_RETRY``: §3.3 flagged that variable as retry-shaped
    #: env, but it was measured **inert in both states** (28 requests either way,
    #: within noise of the bare CLI), so this adapter does not set it and does not
    #: advertise it. Listing a knob shown to move nothing is the same category of
    #: error as guessing a retry count.
    internal_retries = InternalRetryEnvelope(
        max_requests=28,
        max_wall_s=None,
        retries_rate_limit=True,
        configurable_by=("QWEN_CODE_API_TIMEOUT_MS",),
    )

    #: §A — mandatory, and measured across every upstream error class. The
    #: upstream message is preserved verbatim inside the brackets, so the base
    #: class's ``auth_error_patterns`` / ``rate_limit_patterns`` / context-overflow
    #: matching still works **provided the classifier is given
    #: ``result.result``** rather than raw stdout.
    exit_zero_failure_markers = (_API_ERROR_MARKER,)

    #: qwen prefixes every upstream failure with the HTTP status:
    #: ``[API Error: 401 <upstream text>]``. The base patterns match none of the
    #: 401 sentences measured or documented for this lane (the stub's OpenAI
    #: "Incorrect API key provided", OpenRouter's "No auth credentials found" /
    #: "User not found."), so until 2026-10-08 a 401 classified ``server_error``
    #: off the ``api error`` rung and entered the retry ladder as retryable, on
    #: 0.21.13 and 0.25.0 alike. qwen's own status prefix names it whatever the
    #: backend wrote.
    auth_error_patterns = LLMProvider.auth_error_patterns + ("[api error: 401",)

    @property
    def name(self) -> str:
        return "qwen-code"

    @property
    def default_timeout(self) -> int:
        # 1200 s, matching the providers.yaml block. `--max-wall-time` is derived
        # from the caller's resolved timeout and held 30 s under it, so this
        # value is also what bounds qwen's own unbounded 429/stall paths on a
        # default run.
        return 1200

    def is_available(self) -> bool:
        return shutil.which("qwen") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """``qwen <flags> <prompt>`` — flags first, bare positional prompt last.

        Args:
            prompt: The prompt text. Rendered as a trailing **positional**;
                ``-p`` is deprecated at 0.21.13.
            model: Passed to ``-m``. Measured: the flag wins over
                ``OPENAI_MODEL`` when both are set, OpenRouter-shaped slugs pass
                through verbatim (slash preserved), and — because there is no
                effort surface — a stray ``:effort`` suffix would also pass
                through verbatim, which is why the decline is documented rather
                than implicit.
            timeout_s: Rendered as ``--max-wall-time`` minus the shutdown margin.
                ``None`` emits **no flag at all**, byte-identical to omitting the
                keyword (§1's guard).
            schema: Rendered inline as ``--json-schema <json>``, claude-code's
                shape. ``None`` emits nothing.
        """
        cmd = [
            "qwen",
            # Non-interactive output with no TUI chrome, and no per-project
            # `projects/<slug>/chats/*.jsonl` write (measured: 5 files -> 4).
            "--bare",
            "--chat-recording",
            "false",
            "-o",
            "json",
            # The §6.5 tier. Policy constants, both of them -- see the module
            # docstring for why the tool cap is a rung BELOW tier 1.
            "--max-tool-calls",
            str(MAX_TOOL_CALLS),
            "--max-session-turns",
            str(MAX_SESSION_TURNS),
        ]
        # Row-derived, and the only such value this adapter renders (§7 step 6).
        wall_time = max_wall_time_value(timeout_s)
        if wall_time is not None:
            cmd += ["--max-wall-time", wall_time]
        # Inline transport, rendered with sorted keys and compact separators so
        # one schema always produces one argv byte string -- claude_code.py's
        # rule, for the same reason: a golden fixture cannot churn on dict
        # ordering.
        if schema is not None:
            cmd += [
                "--json-schema",
                json.dumps(
                    dict(schema.document), sort_keys=True, separators=(",", ":")
                ),
            ]
        cmd += ["-m", model]
        # The prompt is LAST and it is a bare positional, so a non-argv transport
        # drops exactly `cmd[-1]`.
        cmd.append(prompt)
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
    ) -> Tuple[List[str], Optional[str]]:
        """Deliver the prompt on argv or on stdin.

        Under ``stdin`` the prompt is omitted from argv entirely and returned as
        the text to write to the child, so no part of it is measured against a
        command-line cap. Measured at 0.21.13: qwen with **no prompt argument at
        all** reads the prompt from stdin and returns byte-identical output to
        the argv form. Because the prompt is a bare trailing positional, the two
        transports differ by exactly one element and nothing else.
        """
        if transport != "stdin":
            return super().build_command_for_transport(
                prompt, model, transport, prompt_file, timeout_s=timeout_s,
                schema=schema,
                sandbox_fallback=sandbox_fallback,
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        return cmd[:-1], prompt

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """§3.4's two-step unwrap, with classification **before** delegation.

        **Step 1** parses stdout as a JSON *array* of records and takes the last
        ``type == "result"`` record. It then classifies, and this ordering is the
        whole point rather than a stylistic choice:

        * ``is_error`` true, or ``subtype`` other than ``"success"``, or no
          ``result`` key at all ⇒ failure. That last condition is load-bearing:
          the error-shaped ``result`` record carries ``error`` *instead of*
          ``result``, so ``parse_result_envelope``'s ``if "result" in wrapper``
          guard misses it and serves the record's own bookkeeping to
          reaggregation as the model's answer. Verified against the committed
          helper on the ``stdout-error`` fixture.
        * an ``[API Error: …]`` marker anywhere in the answer text ⇒ failure,
          **even though the exit code, ``subtype`` and ``is_error`` all say
          success** (see the module docstring). Searched, never prefix-matched,
          because the truncated-stream shape puts the marker after ten characters
          of concatenated partial text.

        **Step 2** hands a record that passed both checks to the committed
        :func:`parse_result_envelope` — the same envelope claude-code and
        cursor-agent already use — rather than growing a fourth copy of the
        unwrap. That helper runs ``extract_json_from_text`` internally, which is
        §3.4's step 2.
        """
        text = (stdout or "").strip()
        if not text:
            return {
                "success": False,
                "error": self._empty_stdout_reason(stderr),
                "raw": stdout,
                "data": None,
            }

        try:
            records = json.loads(text)
        except ValueError as exc:
            return {
                "success": False,
                "error": f"JSON parse error: {exc}",
                "raw": stdout,
                "data": None,
            }

        if not isinstance(records, list):
            return {
                "success": False,
                "error": "qwen -o json did not emit a JSON array of records",
                "raw": stdout,
                "data": None,
            }

        result_records = [
            record
            for record in records
            if isinstance(record, dict) and record.get("type") == "result"
        ]
        if not result_records:
            return {
                "success": False,
                "error": (
                    "no result record in qwen output "
                    "(the run produced no terminal envelope)"
                ),
                "raw": stdout,
                "data": None,
            }
        record = result_records[-1]

        # Rule 1 -- the envelope's own verdict, where it has one. Since 0.25.0
        # this is where EVERY API error lands (`is_error: true`, the
        # `[API Error: …]` text under `error.message`), so the message is
        # read out of the object rather than reported as its Python repr.
        subtype = record.get("subtype")
        if record.get("is_error") or (subtype is not None and subtype != "success"):
            return {
                "success": False,
                "error": self._record_error_text(record),
                "raw": stdout,
                "data": None,
            }

        answer = record.get("result")
        if not isinstance(answer, str):
            return {
                "success": False,
                "error": (
                    "qwen result record carries no result string "
                    "(an error-shaped envelope reported success)"
                ),
                "raw": stdout,
                "data": None,
            }

        # Rule 2 -- the marker, which is the ONLY signal on seven of the eight
        # failure shapes measured at 0.21.13 (the floor). 0.25.0 sends those
        # shapes through rule 1 instead.
        if _API_ERROR_MARKER.search(answer):
            return {
                "success": False,
                "error": answer.strip(),
                "raw": stdout,
                "data": None,
            }

        if not answer.strip():
            return {
                "success": False,
                "error": "Empty result",
                "raw": stdout,
                "data": None,
            }

        return parse_result_envelope(json.dumps(record))

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last ``result`` record's answer, when the record is clean (D2.5).

        The text :meth:`parse_output` serves: the last ``type == "result"``
        record's ``result`` string, and only when every check the parser makes
        before delegating passes — rule 1 (``is_error`` not true, ``subtype``
        absent or ``"success"``), a string ``result``, no ``[API Error:``
        marker (:data:`_API_ERROR_MARKER`), not blank — plus the verdict
        :func:`parse_result_envelope` reads (``envelope_verdict``). So the ask
        lane's answer text and the review lanes' salvage read what the parser
        treats as the answer (plans/ask-answer-recovery-and-false-success.md
        D2.5).

        The marker test is the one that matters: qwen reports its API failures
        **inside a record marked clean** (``is_error: false``,
        ``subtype: "success"``, ``result: "[API Error: 401 …]"``), so without it
        seven of the eight committed error captures would be saved as answers,
        two of them with partial text in front (``OKOKOKOKOK[API Error: …]``).
        ``""`` — a final verdict — for those, for an error-shaped record, and
        for any stdout that is not one JSON array of records (a wall-clock or
        tool-budget abort prints nothing).
        """
        try:
            if not isinstance(stdout, str):
                return ""
            try:
                records = json.loads(stdout.strip())
            except ValueError:
                return ""
            if not isinstance(records, list):
                return ""
            results = [
                record for record in records
                if isinstance(record, dict) and record.get("type") == "result"
            ]
            if not results:
                return ""
            record = results[-1]
            subtype = record.get("subtype")
            if record.get("is_error") or (subtype is not None and subtype != "success"):
                return ""
            if envelope_verdict(record):
                return ""
            answer = record.get("result")
            if not isinstance(answer, str) or not answer.strip():
                return ""
            if _API_ERROR_MARKER.search(answer):
                return ""
            return answer
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""

    @staticmethod
    def _record_error_text(record: Dict[str, Any]) -> str:
        """The failure text of an error-shaped ``result`` record.

        qwen writes ``"error": {"message": "…"}``; the message is what a user
        should read, not the object's repr. Any other shape keeps the old
        rendering.
        """
        error = record.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        return str(error or record.get("subtype") or "qwen reported a failure")

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """Drop qwen's ripgrep advisory line from stderr; nothing else.

        The one stderr reduction a shipped adapter makes, and the narrowest one
        possible: :data:`_RIPGREP_ADVISORY` matches only the startup line qwen
        prints when its bundled ``rg`` cannot run, whose ``EACCES`` otherwise
        decides the class of every run on a root-owned install. Removal-only,
        and any failure returns the capture unchanged.
        """
        try:
            return stdout, _RIPGREP_ADVISORY.sub("", stderr or "")
        except Exception:  # noqa: BLE001 - the hook must never raise
            return stdout, stderr

    @staticmethod
    def _stderr_error_envelope(raw: str) -> Optional[Dict[str, Any]]:
        """qwen's ``{"error": {...}}`` envelope, wherever stderr's last block is.

        At 0.21.13 the envelope was the whole of stderr. At 0.25.0 it follows
        whatever qwen printed first — one ``Retrying provider attempt …`` line
        per retry, the ripgrep advisory — so the parse starts at each line that
        opens with ``{`` instead of at byte 0.
        """
        starts = [0] + [i + 1 for i, ch in enumerate(raw) if ch == "\n"]
        for start in starts:
            if not raw.startswith("{", start):
                continue
            try:
                envelope = json.loads(raw[start:])
            except ValueError:
                continue
            error = envelope.get("error") if isinstance(envelope, dict) else None
            if isinstance(error, dict) and error.get("message"):
                return error
        return None

    @staticmethod
    def _empty_stdout_reason(stderr: str) -> str:
        """Name the cause of a zero-byte stdout, rather than restating the symptom.

        qwen aborts a run with **exit 55 and no stdout at all** in two measured
        cases, and in both it writes a structured envelope to stderr:

        * the wall-clock bound (``--max-wall-time``) —
          ``FatalBudgetExceededError``, "wall-clock budget of Ns exceeded";
        * the tool-call cap (``--max-tool-calls 0``) — the same error type,
          "tool-call budget of 0 exceeded; observed 1". This one is **not**
          hypothetical: it was hit against the real backend on the §7.4 live
          smoke, because a real model sometimes chooses to call a tool where the
          stub never does.

        There is also ``FatalCancellationError`` (code 130) on SIGTERM.

        `parse_output` receives both streams, so reporting "empty output" while
        the reason sits in stderr would hide a cause the CLI took the trouble to
        make machine-readable. The classification ladder is unaffected — an
        unrecognized shape stays transport-shaped and keeps the bounded-retry
        path, which is what recovers the occasional blocked tool call.
        """
        raw = (stderr or "").strip()
        if raw:
            error = QwenCodeProvider._stderr_error_envelope(raw)
            if error is not None:
                kind = error.get("type") or "error"
                return f"qwen aborted with no output — {kind}: {error['message']}"
            return f"qwen produced no output on stdout; stderr said: {raw[:300]}"
        return "Empty output from qwen (no JSON records on stdout)"

    def get_env(self, model: str) -> Dict[str, str]:
        """The complete B1 selector set, plus a per-slot config root.

        §2.2 rule 2 — **selection is total, never partial**. All three
        ``OPENAI_*`` variables are emitted together for every ``(model,
        profile)``, including the base URL when the key is empty.

        Two measurements decide the shape, and they pull in opposite directions:

        * an *incomplete* trio **fails closed** — with ``OPENAI_BASE_URL`` unset
          qwen made no request at all and printed "No auth type is selected",
          so it does not silently resolve to ``api.openai.com``;
        * but a *stale inherited* ``OPENAI_BASE_URL=https://api.openai.com/v1``
          **completes** the trio and would be used, pairing the user's real
          OpenAI credit with an OpenRouter slug. That is §3.3's "money bug" in
          its exact original shape.

        So the rule stands unchanged: emit all three, always. And this dict is
        the entire surface — nothing here mutates ``os.environ``, because a
        process-wide write would put qwen's base URL under **codex's** next spawn
        in the same fan-out, which is the one thing ``resolve_env``'s child-only
        composition cannot defend against.
        """
        env = {
            # Measured (§7 step 4): qwen appends `/chat/completions` to this
            # verbatim and adds no version segment of its own, so the `/v1` is
            # load-bearing.
            "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
            "OPENAI_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),
            "OPENAI_MODEL": model,
            # Confirmed in the 0.21.13 bundle. The updater would otherwise move
            # the binary underneath a pinned parser, and telemetry is not
            # something a fan-out slot should emit on the user's behalf.
            "QWEN_TELEMETRY_ENABLED": "false",
            "QWEN_USAGE_STATISTICS_ENABLED": "false",
            "QWEN_CODE_SKIP_UPDATE_CHECK_ONCE": "1",
        }
        home = self._home_dir_for_spawn()
        if home is not None:
            env[QWEN_HOME_ENV_VAR] = home
        return env

    def _home_dir_for_spawn(self) -> Optional[str]:
        """A fresh config root for this spawn, or ``None`` to leave it alone.

        Per **slot**, not per run. The probe could not reproduce the corruption
        §8.2 feared — two simultaneous slots with different models completed rc=0
        and each got its own model on the wire, with a separate ``QWEN_HOME``, a
        *shared* one, and a shared real ``$HOME`` alike, because qwen never
        writes ``settings.json`` on this path and its per-run writes are
        append-only JSONL. The per-slot root is set anyway: it is free, it
        satisfies §8.2's test 2 by construction, and it keeps a fan-out's
        ``usage_record.jsonl`` out of the user's own qwen state.

        ``None`` when the user pinned ``QWEN_HOME`` themselves — their directory
        is respected and never removed — or when a temp directory cannot be
        created, because refusing a slot over a containment mechanism would be a
        worse trade than running without it.
        """
        if os.environ.get(QWEN_HOME_ENV_VAR):
            return None
        with _HOME_LOCK:
            try:
                return _create_home_dir()
            except OSError:  # noqa: BLE001 - containment must never fail a run
                return None

    def get_remove_env(self) -> List[str]:
        """The B3 and legacy names, so ambient config cannot re-select a vendor.

        §2.2 rule 3: adapter wins, ambient loses, no fallback. Note the division
        of labour — the strip covers names this adapter does **not** set, and the
        *injection* covers the endpoint. Neither substitutes for the other:
        stripping ``OPENAI_API_BASE`` removes a stale value but would leave the
        CLI on its compiled-in default if the base URL were not also injected.
        """
        return list(_STRIPPED_VENDOR_VARS)
