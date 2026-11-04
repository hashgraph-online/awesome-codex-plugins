"""Mistral Vibe provider implementation.

``mistral-vibe`` (Apache-2.0, PyPI, binary ``vibe``). Everything below is
measured against **2.24.1** in the containerized probe of
`plans/harness-expansion.md` §6 — stub-only, ``--network none``, no credential —
and the probe contradicted the plan's researched §4.2 contract on four separate
points. Where it did, the measurement is what shipped and the contradiction is
recorded on the member it affects.

**vibe is not the marginal row §0.1 scored.** It was admitted on exactly one (c)
win, ``--max-price``. Measured, it has three: the spend cap, a **stdin prompt
transport** carrying a multi-KB prompt, and a **permission tier narrower than
all-or-nothing** (``--agent plan``, plus tool allow/deny lists). Two of those are
explicitly enumerated (c) properties in §0, and the transport is the one §6.4
says these adapters need in order to be usable on Windows at all.

**§4.2's central wrinkle does not exist, and it took ``prepare_run`` with it.**
The plan's premise was *"no ``--model`` flag ⇒ the adapter must template a
per-run config"*, which is why §1 grew a ``prepare_run(model, profile, *,
run_dir)`` hook at all. Measured: **``VIBE_ACTIVE_MODEL`` selects the model from
the environment** — the ``VIBE_`` prefix overrides *any* config field — and two
concurrent slots with **different** models both succeeded while sharing one
``VIBE_HOME`` and one read-only ``config.toml`` (the stub saw exactly
``wire-model-ALPHA`` and ``wire-model-BETA``). There is no per-run file to write,
so there is no race, so there is no hook: the catalog is a **static, committed**
``home_seed/vibe/`` tree and the only per-run-varying value is an env var. With
dsh deferred by §0.1, ``prepare_run`` has no consumer left in this plan and does
not ship on vibe's account.

**The permission ladder is inverted at the bottom, and the default is the
dangerous end.** ``--agent NAME`` selects a builtin profile carrying an explicit
safety enum, and ``default_agent`` defaults to **``accept-edits``**, whose
``AgentSafety`` is **DESTRUCTIVE** and whose ``write_file``/``edit`` permission
is ``always``. So the bare ``vibe -p …`` that §6.5's table lists as *tier 1* is
in fact the second-widest rung on the ladder. The real rung 1 is ``--agent plan``
(``AgentSafety.SAFE``, "read-only agent for exploration and planning"), it
completes a realistic review prompt with a clean filesystem canary, and §6.5
rule 1's ascending stop therefore forbids promoting above it. ``--trust`` is
**not** required either — a rung-1 run completed with no trust prompt and no
stall — so it is a permission widener bought for nothing and is not emitted.

**Output.** ``--output json`` is a JSON **array of transcript entries** printed at
exit; ``--output streaming`` is the same entry objects as NDJSON. ``json`` ships:
one parse of one document rather than N line-parses, with an identical schema.
The answer is the **last** entry with ``role == "assistant"`` and
``type == "message"``, concatenating the ``text`` of its ``content[]`` blocks —
last-wins is what the ``multi-assistant`` fixture pins.

**The error channel is stderr, and since 2.26.1 the exit code names the kind.**
Every runtime failure measured — 401, 404, 400 context, 429, 500, stall,
truncated stream, error envelope, zero-byte response — writes to **stderr** with
stdout empty. At 2.24.1 and 2.26.0 every one exits 1, and *config validation*
errors are §6.2's ``stdout-error`` trap: they print on **stdout with stderr
empty**, still exit 1. 2.26.1 (re-measured 2026-10-09) documents four
programmatic exits and uses them: **0** finished; **1** usage or config error —
the 401, and a config validation error, which now prints ``Error: Invalid
configuration …`` on **stderr** with stdout empty; **2** infrastructure failure
— the 404, the 400 context overflow, the stall and every retry-budget
exhaustion; **3** stopped by a limit. The wording on stderr is 2.26.0's byte for
byte except the stall's, which now names its ``ReadTimeout``. So a nonzero
exit's stdout must never be read as an answer, which is exactly the shape
opencode cost this repo a debugging round for.

**Exit 3 leaves a whole transcript on stdout, and it is not an answer.** A run
stopped by ``--max-turns 4``, by ``--max-price 0.25``, by a ``length`` finish or
by a SIGTERM (what the harness's own timeout sends) prints the transcript at
exit — every entry ``generationStatus: completed``, its last assistant message
whatever the run had said: half an array, or all of it — and says only
``Stopped: <outcome>`` on stderr. :meth:`VibeProvider.parse_output` read all
four as success; it now refuses any stdout beside that line
(:func:`stopped_by_a_limit`). The fan-out and ask lanes already fail a nonzero
exit, but the executor lane lets a schema-valid result win over one.

**No exit-0 failures.** Every failure mode measured exits nonzero (1 at 2.24.1
and 2.26.0; 1, 2 or 3 at 2.26.1), so ``exit_zero_failure_markers`` is empty *by
measurement* and §6.2's ``exit-zero-failure`` row is recorded N/A rather than
skipped.

**``VIBE_API_TIMEOUT`` is pinned, and that is load-bearing rather than tidy.**
vibe retries 3 times over ``{408, 409, 425, 429, 500, 502, 503, 504, 529}``, and
a stall costs ``3 × api_timeout``. The default ``api_timeout`` is **720 s**, so
an unpinned worst case is ``3 × 720 + 1.6 ≈ 2162 s`` — about **36 minutes inside
a single slot**. Pinning the knob and declaring the pinned number is the
``claude_code.py`` precedent, and it is what keeps the declared envelope honest.
That is 2.24.1's chain. 2.26.0 retries for a wall-clock budget instead
(``api_retry_max_elapsed_time``, default 300 s), so ``VIBE_API_RETRY_MAX_ELAPSED_TIME``
is pinned beside it (2026-10-08; see ``API_RETRY_BUDGET_S``). 2.26.1 keeps the
budget and changes the chain inside it (2026-10-09; see ``internal_retries``).

**``--max-price`` ships, and its role is narrower than §7.4 assumed.** §4.2 feared
vibe enforces the cap against a priced catalog the stub cannot serve; measured,
vibe issues **no ``GET /models`` at all**, in any run — pricing comes from the
seed's ``input_price``/``output_price`` keys, so the cap is decidable entirely
offline and the flag's "drop it from v1" branch never fires. But the help text is
precise: *"Session will be interrupted if cost exceeds this limit"*. It is a
**between-turns** guard, and a single completion under a ``0.0000001`` cap ran to
completion with the full answer. So it bounds a runaway loop, **not** one
expensive call, and it is not sufficient as §7.4's spend bound on its own —
``--max-turns`` and the key-side credit cap remain load-bearing. 2.26.1 still
lets that one completion run to its end, but then reports the run
``Stopped: price_limit`` and exits 3 with the whole answer on stdout (the
``price-limit`` row, a stub reporting 2,000,000 prompt tokens): the call is paid
for and its answer is a failure.

**Reasoning effort is supported, through the seed rather than argv.** The level
is the ``[[models]]`` config key ``thinking``, whose accepted set was read off
the installed validator itself: ``off, low, medium, high, max``. So
``split_reasoning_effort`` runs in :meth:`VibeProvider.build_command` — a
``:effort`` suffix must never reach the model surface verbatim — but the level is
carried in ``VIBE_THINKING``, not in a flag. That is the same "env, not argv"
split §8 item 8 records for kimi, and it means the §14.1 seven-artifact rule
attaches to the env declaration rather than to ``expected_argv.yaml``.

**Two operational traps, recorded so nobody re-derives them.** A **positional**
prompt with no ``-p`` launches the interactive TUI and hangs forever (ANSI
alt-screen on stderr), so ``-p`` is mandatory and the trailing-positional shape
§8.3 contemplates for dsh must never be copied here. And the wheel also installs
``vibe-acp`` and ``vibe-app-server``; neither is wanted.
"""
import json
import os
import re
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
    split_reasoning_effort,
)

#: Levels accepted by the ``[[models]]`` key ``thinking`` at 2.24.1, read off the
#: installed pydantic validator rather than from documentation: a bogus value
#: exits 1 with ``models.<alias>.thinking: Input should be 'off', 'low',
#: 'medium', 'high' or 'max'``.
#:
#: Note this is a *config* key, not a flag. The suffix is split off the model
#: string here so it never reaches ``VIBE_ACTIVE_MODEL`` verbatim — an alias with
#: a stray ``:high`` glued on selects no configured model at all — and the level
#: is emitted through :meth:`VibeProvider.get_env`.
#:
#: The narrowest ladder that still has a top: four rungs, no ``minimal`` and no
#: ``xhigh``, with ``off`` as vibe's spelling of ``none``. The validator's own
#: message above is the whole accepted set, in vibe's own words.
EFFORT_LADDER = ReasoningLadder(
    provider="vibe",
    rungs=("low", "medium", "high", "max"),
    spellings=(("off", "none"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

#: §4.2's decision, taken here rather than left to taste: emitted on **every**
#: ``build_command``, never lane- or kwarg-conditional. A config-conditional flag
#: would break the argv contract — the provider lane's call log is graded against
#: ``expected_argv.yaml``, whose reference shapes are built from this adapter
#: under the *host's* config, so a flag present in one and absent in the other
#: leaves an unmatched record and a stale entry at once. It is a **policy value**
#: and is kept verbatim in the pinned argv table; reducing it to a placeholder
#: would make the assertion vacuous.
MAX_PRICE_USD = "0.25"

#: The per-run turn ceiling. A module constant, so §7 step 6 classifies it as
#: **policy, verbatim** — nothing derives it from the slot, and it does not join
#: ``normalize_argv.py``'s ``_ROW_DERIVED``.
#:
#: This is the bound that actually stops a runaway on §7.4's credentialed lane.
#: ``--max-price`` is checked *between* turns, so it cannot interrupt a single
#: expensive completion; a turn cap can.
MAX_TURNS = "4"

#: The pinned per-request timeout, in seconds, and the number the declared
#: envelope is computed from. The vendor default is 720 s and vibe retries three
#: times, so leaving it alone would put a ~36-minute worst case inside one slot.
#:
#: 90 s × 3 + margin sits comfortably under the 1200 s block timeout with room
#: for the harness's own shutdown, which is the invariant §3.3 states for any
#: inner bound.
API_TIMEOUT_S = 90

#: The pinned retry budget, in seconds: 2.26.0's ``api_retry_max_elapsed_time``.
#: 2.26.0 (the Unified Harness) retries a retryable failure while less than this
#: much time has passed since the first request, with a 0.5 s backoff doubling
#: to a 30 s cap and ``Retry-After`` honoured up to that cap. The vendor default
#: is 300 s, which measured 16 requests over ~305 s on a fail-forever row and
#: 367 s on a stall, past 2.24.1's declared 272 s. 150 s keeps the worst case at
#: that same 272 s (below). 2.24.1 has no such setting and ignores the variable.
#:
#: 2.26.1 reads the same variable and spends it differently
#: (``mistralai_vibe_local_harness/vibe/adapters/_retry.py``, measured
#: 2026-10-09): a retry is made only when its *wait* ends inside the budget (the
#: provider's ``Retry-After`` uncapped, else the backoff), the backoff is 0.5 s ×
#: 1.5ⁿ plus up to 1 s of jitter, still capped at 30 s, and a stall is retried
#: once. At 150 s that is 13 requests over 124.5 s on every fail-forever row, a
#: stall 2 requests over 185 s, and five ``Retry-After: 29`` 429s then a stall 6
#: requests over 239 s.
API_RETRY_BUDGET_S = 150

#: 2.26.0's backoff cap, read off the harness source (``_MAX_RETRY_DELAY_S``),
#: and 2.26.1's (``_MAX_RETRY_DELAY_S = 30.0`` in ``_retry.py``).
_MAX_RETRY_DELAY_S = 30

#: ``max_wall_s`` for the declaration below, the largest of the supported
#: releases' bounds: 2.24.1's three attempts at the pinned timeout plus its
#: measured ~1.6 s of backoff, and 2.26.0's last retry granted just inside the
#: budget, one capped delay, then one attempt at the pinned timeout. Both are
#: 272 s at these pins. 2.26.1's is smaller — its last attempt starts inside the
#: budget, so budget + one attempt, 240 s, measured 239 s — and the 272 s stands.
_MAX_WALL_S = max(
    3 * API_TIMEOUT_S + 2,
    API_RETRY_BUDGET_S + _MAX_RETRY_DELAY_S + API_TIMEOUT_S + 2,
)

#: Prefix under ``TMPDIR``, so a directory leaked by a SIGKILL is sweepable by
#: name — the rule ``cursor_agent``, ``kimi``, ``qwen-code`` and ``copilot`` all
#: follow.
_HOME_PREFIX = "multi-llm-vibe-"

_HOME_LOCK = threading.Lock()
#: Every config root **this process created**. Nothing outside this list is ever
#: removed: a user-pinned ``VIBE_HOME`` is respected, never deleted.
_HOME_DIRS: List[str] = []
_HOME_ATEXIT_REGISTERED = False

#: B3 and ambient names (§2.2 rule 3: adapter wins, ambient loses, no fallback).
#:
#: **This list holds only names :meth:`VibeProvider.get_env` never sets, and that
#: is a correctness constraint rather than a stylistic one.** Both spawn sites
#: compose the child env as ``{**os.environ, **provider_env}`` and *then* pop
#: every name ``get_remove_env`` returns — the strip runs **after** the merge. So
#: a name that appears in both lists is not belt-and-braces; it is the adapter
#: deleting its own value. Listing ``VIBE_ACTIVE_MODEL`` here would leave vibe
#: with no model selected at all, and nothing in the argv would show why.
#:
#: The injected ``VIBE_*`` names need no strip anyway: ``get_env`` merges last
#: and therefore already wins over anything the user's shell exported. Only the
#: names this adapter leaves alone can be shadowed, so only they appear below.
#: ``test_nothing_the_adapter_injects_is_also_stripped`` pins the invariant.
_STRIPPED_VENDOR_VARS: Tuple[str, ...] = (
    # The vendor backend. §2.2's vibe row says a seed missing `backend =
    # "generic"` selects Mistral's own path; measured, that is FALSE --
    # `ProviderConfig.backend` DEFAULTS to `Backend.GENERIC`. The real trap is
    # narrower: a provider *named* `mistral` with no explicit backend is
    # special-cased onto the legacy Mistral path. The committed seed names its
    # provider `openrouter`, which avoids it by construction -- and this strip
    # stays anyway, because a stale vendor key has no business being reachable
    # from a run this adapter points at OpenRouter.
    "MISTRAL_API_KEY",
    # OpenTelemetry export. `get_env` turns `enable_telemetry` off, which is the
    # load-bearing half (otel needs it), but this one is a separate switch and
    # the adapter does not set it -- so an ambient value is the only way it could
    # come on, and stripping it costs nothing.
    "VIBE_ENABLE_OTEL",
    # vibe reads the BARE name, so a user's unrelated LOG_LEVEL=DEBUG changes
    # this CLI's output shape and can put diagnostics where the parser expects
    # an answer.
    "LOG_LEVEL",
)


#: 2.26.1's line for a run that ended without finishing and without an error
#: (``vibe/cli/cli.py``: ``print(f"Stopped: {result.outcome}", file=sys.stderr)``
#: when the outcome is not ``finished`` and carries no error message; a run that
#: does carry one prints ``Error: …`` instead and leaves stdout empty). These are
#: the exit-3 outcomes (``RunOutcome`` in ``vibe/app_server/run_export.py``):
#: ``turn_limit``, ``token_limit``, ``price_limit``, ``deadline``,
#: ``terminated``, ``length``. Measured 2026-10-09: ``turn_limit``,
#: ``price_limit``, ``length``, ``terminated`` and ``deadline``, each exit 3
#: beside a whole transcript on stdout.
_STOPPED_LINE = re.compile(r"^Stopped: ([a-z_]+)[ \t]*$", re.MULTILINE)


def stopped_by_a_limit(stderr: str) -> Optional[str]:
    """The outcome on 2.26.1's ``Stopped: <outcome>`` stderr line, else ``None``.

    The stopped run's transcript is byte-for-byte a finished one's shape, so this
    line is the one place the stop can be read without the exit code.
    """
    match = _STOPPED_LINE.search(stderr or "")
    return match.group(1) if match else None


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

    Containment must never be the thing that fails a run, so a directory that
    cannot be removed is left behind under a known prefix rather than
    propagating an exception out of interpreter shutdown.
    """
    with _HOME_LOCK:
        paths, _HOME_DIRS[:] = list(_HOME_DIRS), []
    for path in paths:
        shutil.rmtree(path, ignore_errors=True)


def reset_home_dirs() -> None:
    """Drop this process's tracking list without removing anything (tests)."""
    with _HOME_LOCK:
        _HOME_DIRS[:] = []


class VibeProvider(LLMProvider):
    """Provider for Mistral's Vibe CLI, driven against a generic OpenAI backend.

    ``vibe --output json --max-price 0.25 --max-turns 4 --agent plan
    -p <prompt>`` — flags first, the ``-p`` pair trailing.

    Declares a stdin transport and the ``:effort`` suffix, both measured; stays
    at ``usage_support = "none"``, also measured. See the module docstring.
    """

    #: §8.3: flags first, the ``-p <prompt>`` **pair** trailing. Confirmed legal
    #: at 2.24.1 — ``-p`` takes exactly one value and the flags are
    #: order-independent, so the grok-shape reorder changes no dispatched
    #: behaviour. Note the pair: the stdin transport drops ``-p`` **and** the
    #: prompt, not ``cmd[:-1]``.
    #:
    #: ``-1`` is *required* rather than preferred here, because
    #: ``test_last_element_assumption_holds_wherever_it_is_relied_on`` forces it
    #: on any adapter declaring a non-argv transport, which this one does.
    prompt_argv_index = -1

    #: Measured on the wire: the prompt travels as one argv element **or** on
    #: stdin. vibe's stdin form is unusual and worth naming — ``-p`` is passed
    #: **with no value** and the prompt is piped; an 8,427-byte prompt arrived
    #: intact as the user message, with ``-p`` still trailing.
    supported_prompt_transports = ("argv", "stdin")

    #: ``--agent plan`` — §6.5's rung 1, emitted unconditionally and pinned again
    #: through ``VIBE_DEFAULT_AGENT`` — is upstream's read-only profile, so this
    #: adapter cannot write the ``{output_json_path}`` file the Lane A prompts
    #: used to demand. The plan profile *advertises* ``write_file`` and ``edit``
    #: to the model and then denies them: both carry ``permission: "never"`` with
    #: an allowlist of ``$VIBE_HOME/plans/*`` alone (confirmed in a real run's own
    #: ``logs/session/**/meta.json`` under
    #: ``plans/harness-expansion/probe-out/vibe/``). That is the cursor failure
    #: shape exactly — the model tries, is denied, and narrates the denial — and
    #: the one writable path is a per-slot temp home this adapter mints and
    #: deletes, never the review's output directory.
    #:
    #: The declaration deliberately does not lean on the ``bash`` tool the plan
    #: profile leaves un-overridden: a harness must not depend on a model
    #: shelling around its own sandbox. Stdout is the channel ``--output json``
    #: gives, within ``--max-turns 4``.
    supports_file_output = False

    version_cmd = ("vibe", "--version")
    #: 2.24.1 is where the fixtures in ``tests/fixtures/vibe/`` were first
    #: captured and the floor this parser is known to handle; it stays the floor.
    #:
    #: 2026-10-08: every row re-captured on 2.26.0 (the image's pin) except
    #: ``empty``, whose zero bytes no 2.26.0 run produces. 2.26.0 runs the new
    #: Unified Harness by default; the parser needed no change (new
    #: ``inputEntryId`` key, renamed ids, httpx-worded HTTP errors, vendor text
    #: forwarded). Its retry chain did change: a 300 s budget
    #: (``api_retry_max_elapsed_time``) instead of 3 tries, 16 requests on a
    #: fail-forever row, ``Retry-After`` honoured to 30 s, and cut or
    #: finish-less streams retried. :meth:`get_env` now pins that budget
    #: (:data:`API_RETRY_BUDGET_S`) and ``internal_retries`` below covers both
    #: releases.
    #:
    #: 2026-10-09: re-captured on 2.26.1 the same way, the argv unchanged. The
    #: stderr wording is 2.26.0's byte for byte except the stall's; what moved is
    #: the exit code (1 config, 2 infrastructure, 3 stopped by a limit), the
    #: config error's channel (stderr now, so ``stdout-error`` keeps its 2.26.0
    #: bytes beside a new ``config-error`` row) and the retry chain inside the
    #: pinned budget. One parser change: a ``Stopped: <outcome>`` line on stderr
    #: refuses the transcript beside it (:func:`stopped_by_a_limit`).
    min_version = "2.24.1"
    verified_version = "2.26.1"

    #: Measured at 2.24.1 (§6.1.1), every field, including the one experiment the
    #: other adapters do not run, and re-measured at 2.26.0 on 2026-10-08 with
    #: the retry budget pinned (2.26.0 retries for a budget, not three times),
    #: and at 2.26.1 on 2026-10-09.
    #:
    #: ``max_requests`` is **14**, 2.26.1's. At the pinned 150 s budget six
    #: fail-forever rows (500, 429, a cut stream, a finish-less stream, a 200
    #: error body, a zero-byte response) each logged 13 requests over 124.5 s
    #: (0, ~0.9, ~1.8, … ~90.4, ~120.4 s); the 13th request starts at 115.5 s
    #: plus the summed jitter of the eleven delays before it, and when that sum
    #: is under ~4.5 s (about one run in eight) a 14th fits inside the budget.
    #: 2.26.0's was 11 (0, 0.5, 1.5, … 121.5, 151.5 s) and 2.24.1's 3 —
    #: ``async_retry(tries=3, delay_seconds=0.5, backoff_factor=2.0)`` in the
    #: installed source, confirmed against the stub's request log for 5xx and
    #: 429 alike. **The count is the server's whenever it sends a ``Retry-After``
    #: shorter than the backoff**: 2.26.0 and 2.26.1 take that wait as given, so
    #: ``Retry-After: 1`` measured 150 requests over 153 s at 2.26.1 (one per
    #: second until the budget). The wall bound below holds either way.
    #:
    #: ``retries_rate_limit`` is **True** (429 is in the retryable set), so §7.5
    #: rule 6(b) suppresses an identical harness-side re-dispatch. ``Retry-After``
    #: was **not** honoured at 2.24.1 (a 30 s header produced no sleep at all);
    #: 2.26.0 honours it up to a 30 s cap, so a server-chosen delay is still
    #: bounded, which is what lets this adapter state a real ``max_wall_s`` where
    #: copilot and qwen-code cannot. 2.26.1 sleeps the same capped delay and
    #: makes no retry whose uncapped wait would end past the budget
    #: (``Retry-After: 30`` measured 5 requests 30 s apart, 124 s).
    #:
    #: ``max_wall_s`` is computed from the **pinned** ``VIBE_API_TIMEOUT`` and
    #: retry budget, not from the vendor defaults, which is the whole reason the
    #: pins exist (see :data:`_MAX_WALL_S`). Measured at 2.26.0: six 429s with
    #: ``Retry-After: 29`` then a stalled request ended at 267 s, 7 requests,
    #: under the declared 272 s; a plain stall ended at 184 s, 2 requests.
    #: Measured at 2.26.1: five such 429s then a stall ended at 239 s, 6
    #: requests (the last started at 145 s); a plain stall at 185 s, 2 requests,
    #: because 2.26.1 retries a stall once whatever the budget has left.
    #:
    #: **Experiment 6 is why this row is trustworthy.** §4.2 predicted that a 200
    #: whose stream carries no ``finish_reason`` makes vibe "treat the stream as
    #: incomplete and retry", and warned that a 5xx-only measurement would report
    #: zero retries and be wrong. Measured, the opposite is true: that case is
    #: **one POST, exit 1, immediate hard error** — a fail-fast, not a retry loop.
    #: The "un-pinnable stream-retry loop spends the slot's budget invisibly"
    #: hazard behind §4.2's abort criterion 1 is empirically void. The experiment
    #: still earns its place: it is what proves the absence, and it is what
    #: showed ``emits_finish_reason = false`` in the seed turns that hard error
    #: into a clean exit 0 against an endpoint that omits the field.
    internal_retries = InternalRetryEnvelope(
        max_requests=14,
        max_wall_s=_MAX_WALL_S,
        retries_rate_limit=True,
        configurable_by=("VIBE_API_TIMEOUT", "VIBE_API_RETRY_MAX_ELAPSED_TIME"),
    )

    #: vibe's own wording, added to the base set. The measured 401 message is
    #: *"Invalid API key. Please check your API key and try again."*, which
    #: contains none of "unauthorized", "not logged in" or "authentication
    #: required". Multi-word, so it stands alone without the bare-token context
    #: window.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "invalid api key",
    )

    #: The measured 429 message is *"Rate limits exceeded. Please wait a moment
    #: before trying again."* — note the plural "limits", which the base set's
    #: "rate limit" pattern already covers as a prefix match, but which is worth
    #: naming so a wording change is a visible test edit.
    rate_limit_patterns = LLMProvider.rate_limit_patterns + (
        "rate limits exceeded",
    )

    #: **Empty by measurement, not by omission.** Every failure mode the probe
    #: exercised — 401, 404, 400 context-overflow, 429, 500, stall, truncated
    #: stream, error envelope and a bad config — exits **1** at 2.24.1 and
    #: 2.26.0, and nonzero at 2.26.1 (1, or 2 for infrastructure; a run stopped
    #: by a limit exits 3). §6.2's ``exit-zero-failure`` row is therefore
    #: recorded N/A for this CLI rather than left untested.
    exit_zero_failure_markers: Tuple[Any, ...] = ()

    @property
    def name(self) -> str:
        return "vibe"

    @property
    def default_timeout(self) -> int:
        # 1200 s, matching the providers.yaml block. It has to clear vibe's own
        # declared inner bound (3 x 90 s + backoff) with room for the harness's
        # shutdown margin, which is the invariant §3.3 states for any inner cap.
        return 1200

    def is_available(self) -> bool:
        return shutil.which("vibe") is not None

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """``vibe <flags> -p <prompt>`` — flags first, the prompt pair last.

        Args:
            prompt: The prompt text, rendered as the value of a trailing ``-p``.
                ``-p`` is **mandatory**: a bare positional prompt launches the
                interactive TUI and hangs forever.
            model: The seed alias to activate. It never reaches argv — vibe has
                no ``--model`` flag — and is carried in ``VIBE_ACTIVE_MODEL``
                instead. An optional trailing ``:effort`` suffix is split off
                here so it cannot be glued onto the alias, and the level rides
                ``VIBE_THINKING``.
            timeout_s: Accepted and **ignored** — vibe exposes no wall-clock flag
                at 2.24.1. Its inner bound is ``VIBE_API_TIMEOUT``, which
                :meth:`get_env` pins to a constant, so there is nothing to
                render. §1's guard is satisfied trivially: the argv is
                byte-identical with and without the keyword.
            schema: Accepted and ignored; vibe declares no structured-output
                support, so ``structured_output_support`` stays ``False`` and the
                caller never materializes a sidecar for it.
        """
        return [
            "vibe",
            "--output",
            "json",
            # The roster's only USD spend cap. Policy value, verbatim in the
            # pinned argv table -- never a placeholder (§4.2).
            "--max-price",
            MAX_PRICE_USD,
            # The bound that actually stops a runaway loop: --max-price is only
            # checked BETWEEN turns.
            "--max-turns",
            MAX_TURNS,
            # §6.5 RUNG 1, AND THE BARE FORM IS NOT IT. `default_agent` is
            # `accept-edits`, whose AgentSafety is DESTRUCTIVE and whose
            # write_file/edit permission is `always`. `plan` is SAFE and
            # read-only, it completes a realistic review prompt with a clean
            # canary, and rule 1's ascending stop forbids promoting above it.
            # Never `--auto-approve`/`--yolo`, and `--trust` is not needed
            # either -- a rung-1 run showed no trust prompt and no stall.
            "--agent",
            "plan",
            "-p",
            prompt,
        ]

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
        """Deliver the prompt on argv, or on stdin with a valueless ``-p``.

        vibe's stdin form is not the usual one and the difference matters: the
        ``-p`` flag **stays** and simply loses its value, rather than the pair
        being dropped. Measured at 2.24.1 with an 8,427-byte prompt, which
        arrived intact as the user message.

        Dropping ``-p`` entirely would not be a degraded run — it would launch
        the interactive TUI and hang until the slot's timeout killed it.
        """
        if transport != "stdin":
            return super().build_command_for_transport(
                prompt, model, transport, prompt_file,
                timeout_s=timeout_s, schema=schema,
                sandbox_fallback=sandbox_fallback,
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        # Drop the prompt VALUE only; `-p` itself is what keeps vibe headless.
        return cmd[:-1], prompt

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """The transcript minus the ``role: "user"`` entries, which are ours.

        vibe's ``--output json`` transcript opens with a ``{"type": "message",
        "role": "user"}`` entry whose ``content[].text`` is our prompt verbatim,
        so ``classify_failure`` was classifying the plan under review: the
        committed ``success-json.json`` classified **``rate_limited``** because
        the reviewed plan says "unify auth errors, rate limits, …". Like
        copilot's, this half of the defect was pinned by nothing — vibe shipped
        with no manifest.

        Two committed shapes, one rule. The ``--output json`` capture is a JSON
        array, filtered structurally and re-rendered at the same 2-space indent
        the CLI writes; the streamed capture is one entry per line, filtered as
        lines so every other byte survives. In both cases the filter key is
        ``role``, the same field :meth:`_last_assistant_text` already uses to
        stop a user entry being served back as the model's answer.

        Nothing vibe's own diagnosis needs is on this side of the filter: on
        every measured failure vibe writes to **stderr** (``Error: API error
        from …``, ``Rate limits exceeded``, ``The conversation context exceeds
        …``) and stderr is returned unchanged, while a config-validation error
        lands on stdout (stderr at 2.26.1) as bare prose that never parses as
        JSON and is therefore passed straight through.
        """
        try:
            text = stdout.strip() if stdout else ""
            if not text or '"user"' not in text:
                return stdout, stderr
            if text.startswith("["):
                entries = json.loads(text)
                if not isinstance(entries, list):
                    return stdout, stderr
                kept = [
                    entry for entry in entries
                    if not (isinstance(entry, dict) and entry.get("role") == "user")
                ]
                if len(kept) == len(entries):
                    return stdout, stderr
                return json.dumps(kept, indent=2, ensure_ascii=False), stderr
            lines: List[str] = []
            dropped = False
            for line in stdout.split("\n"):
                stripped = line.strip()
                if stripped:
                    try:
                        entry = json.loads(stripped)
                    except ValueError:
                        entry = None
                    if isinstance(entry, dict) and entry.get("role") == "user":
                        dropped = True
                        continue
                lines.append(line)
            if not dropped:
                return stdout, stderr
            return "\n".join(lines), stderr
        except (AttributeError, TypeError, ValueError):
            return stdout, stderr

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """§3.4's two-step unwrap over a JSON array of transcript entries.

        **Step 1** parses stdout as a JSON array and takes the **last** entry
        with ``role == "assistant"`` and ``type == "message"``, concatenating the
        ``text`` of its ``content[]`` blocks whose ``type == "text"``. Last-wins
        is what the ``multi-assistant`` fixture pins — the muse trap — and the
        ``role`` filter is what stops a user or tool entry being served back as
        the model's answer.

        A transcript with **no** assistant entry is a failure, not an
        empty-string success; that is what the ``ephemeral-only`` fixture pins.
        So is any transcript beside a ``Stopped: <outcome>`` line on stderr
        (:func:`stopped_by_a_limit`): 2.26.1 prints the whole transcript and
        exits 3 when ``--max-turns``, ``--max-price``, a ``length`` finish or a
        SIGTERM stops the run, and nothing on stdout says so (the
        ``turn-limit``, ``price-limit``, ``length`` and ``terminated`` rows).

        **Step 2** runs :func:`extract_json_from_text` over that text with
        ``prefer_arrays=True``, so ``data`` carries the model's own document
        rather than vibe's envelope.

        The stdout-carrying failure case is handled first and deliberately: a
        *config validation* error prints on stdout with **stderr empty** and
        still exits 1 (2.24.1 and 2.26.0; 2.26.1 moved it to stderr, and the
        floor is still 2.24.1), so unparseable stdout must be reported as a failure
        carrying that text rather than passed to the extractor, which would
        happily find nothing and report an empty answer instead of the reason.
        """
        text = (stdout or "").strip()
        if not text:
            return {
                "success": False,
                "error": self._empty_stdout_reason(stderr),
                "raw": stdout,
                "data": None,
            }

        stopped = stopped_by_a_limit(stderr)
        if stopped is not None:
            # 2.26.1's exit 3: the whole transcript is on stdout, every entry
            # `completed`, and its last assistant message is whatever the run
            # had said when the limit fell -- half an array, or a whole one
            # that cost more than --max-price. stderr's one line is the only
            # sign; read without it, all four limit rows parsed as success.
            return {
                "success": False,
                "error": (
                    f"vibe stopped before finishing (Stopped: {stopped}); the "
                    "transcript on stdout is a stopped run's, not an answer"
                ),
                "raw": stdout,
                "data": None,
            }

        try:
            entries = json.loads(text)
        except ValueError:
            # THE stdout-error shape: vibe's config-validation diagnostics land
            # here, on stdout, with stderr empty. Quoting them is the whole
            # point -- this is the only place the reason exists.
            return {
                "success": False,
                "error": f"vibe produced non-JSON output on stdout: {text[:300]}",
                "raw": stdout,
                "data": None,
            }

        if not isinstance(entries, list):
            return {
                "success": False,
                "error": (
                    "vibe --output json returned "
                    f"{type(entries).__name__}, expected a transcript array"
                ),
                "raw": stdout,
                "data": None,
            }

        answer = self._last_assistant_text(entries)
        if answer is None:
            return {
                "success": False,
                "error": (
                    "no assistant message in vibe's transcript "
                    "(the run produced no answer)"
                ),
                "raw": stdout,
                "data": None,
            }
        if not answer.strip():
            return {
                "success": False,
                "error": "vibe returned an empty assistant message",
                "raw": stdout,
                "data": None,
            }

        return extract_json_from_text(answer, prefer_arrays=True)

    @staticmethod
    def _last_assistant_text(entries: List[Any]) -> Optional[str]:
        """The last assistant message's text, or ``None`` if there is none.

        Kept separate from :meth:`parse_output` because it is the one part of the
        unwrap that is a claim about vibe's schema: entries carry ``type`` and
        ``role`` alongside a ``content[]`` list of typed blocks, and only
        ``type == "text"`` blocks are answer text.
        """
        answer: Optional[str] = None
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("role") != "assistant" or entry.get("type") != "message":
                continue
            blocks = entry.get("content")
            if not isinstance(blocks, list):
                continue
            parts = [
                block.get("text", "")
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            answer = "".join(parts)
        return answer

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last assistant message's text, never the transcript (D2.5).

        The text :meth:`parse_output` reads: :meth:`_last_assistant_text` over
        the ``--output json`` array. So the ask lane's answer text and the
        review lanes' salvage read what the parser treats as the answer
        (plans/ask-answer-recovery-and-false-success.md D2.5).

        ``""`` — a final verdict — for everything else: no assistant entry, a
        blank one, and any stdout that is not one JSON array. That last case is
        load-bearing: vibe prints its config-validation diagnostics on stdout
        as plain prose (the ``stdout-error`` fixture), which the generic
        plain-text rule would save as the answer. ``generate`` always renders
        ``--output json``, so a streamed or text-mode stdout is not an answer
        this adapter asked for either.
        """
        try:
            if not isinstance(stdout, str):
                return ""
            try:
                entries = json.loads(stdout.strip())
            except ValueError:
                return ""
            if not isinstance(entries, list):
                return ""
            answer = self._last_assistant_text(entries)
            return answer if answer is not None and answer.strip() else ""
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""

    @staticmethod
    def _empty_stdout_reason(stderr: str) -> str:
        """Name the cause of a zero-byte stdout rather than restating the symptom."""
        raw = (stderr or "").strip()
        if raw:
            return f"vibe produced no output on stdout; stderr said: {raw[:300]}"
        return "Empty output from vibe (no transcript on stdout)"

    def get_env(self, model: str) -> Dict[str, str]:
        """The model surface, the pinned inner bound, and the opt-outs.

        vibe has **no ``--model`` flag**, so this is where the model is selected:
        ``VIBE_ACTIVE_MODEL`` names an alias defined in the committed seed, and
        the ``VIBE_`` prefix overrides any value the config file carries. That is
        also what makes two concurrent slots with different models safe while
        sharing one read-only ``config.toml`` — measured, and the reason this
        adapter needs no per-run file and therefore no ``prepare_run``.

        ``VIBE_API_TIMEOUT`` is pinned because the vendor default is 720 s and
        vibe retries three times: an unpinned stall is ~36 minutes inside one
        slot. ``VIBE_API_RETRY_MAX_ELAPSED_TIME`` is pinned because 2.26.0+
        retries for that budget (default 300 s) rather than three times. The
        declared :attr:`internal_retries` envelope is computed from the pinned
        values, so they cannot drift.

        Note the endpoint and the key **variable name** are not here: they live
        in the committed ``home_seed/vibe/`` tree, because
        ``[[providers]]``/``[[models]]`` are sub-tables that no flat ``VIBE_*``
        variable can express (``emits_finish_reason`` especially — verified). The
        seed names the variable; the key's *value* reaches vibe through the
        process environment and never enters a file.

        Nothing here mutates ``os.environ``; this dict is the entire surface.
        """
        alias, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        env = {
            # THE MODEL SURFACE -- there is no flag for this.
            "VIBE_ACTIVE_MODEL": alias,
            # The pinned inner bound the declared envelope is computed from.
            "VIBE_API_TIMEOUT": str(API_TIMEOUT_S),
            # 2.26.0+'s retry budget (vendor default 300 s), the envelope's other
            # input; 2.24.1 has no such setting and ignores it.
            "VIBE_API_RETRY_MAX_ELAPSED_TIME": str(API_RETRY_BUDGET_S),
            # Both default TRUE, and the dependency tree carries sentry-sdk and
            # opentelemetry-*. `enable_otel` needs `enable_telemetry` too, so
            # turning the latter off is the load-bearing one; the third is
            # belt-and-braces against a default flip.
            "VIBE_ENABLE_TELEMETRY": "false",
            "VIBE_ENABLE_UPDATE_CHECKS": "false",
            "VIBE_ENABLE_NOTIFICATIONS": "false",
            # The argv already passes `--agent plan`; pinning the default too
            # means a future argv change cannot silently fall back to
            # `accept-edits`, which is DESTRUCTIVE.
            "VIBE_DEFAULT_AGENT": "plan",
            # Effort is a CONFIG key, not a flag (see REASONING_EFFORTS), and it
            # is emitted UNCONDITIONALLY rather than only when a suffix is
            # present. The reason is the strip-after-merge ordering documented on
            # _STRIPPED_VENDOR_VARS: a conditional injection cannot be made safe
            # by adding the name to get_remove_env (that would delete the value
            # on the suffixed path too), and get_remove_env takes no model, so it
            # cannot strip conditionally either. Emitting always is what stops an
            # ambient VIBE_THINKING from silently applying a reasoning level to
            # an unsuffixed spec -- the same determinism copilot buys by
            # stripping COPILOT_MODEL because it passes --model.
            #
            # `off` is the measured literal for "no reasoning requested", which
            # is exactly what a model spec with no :effort suffix means.
            "VIBE_THINKING": effort if effort is not None else "off",
        }
        home = self._home_dir_for_spawn()
        if home is not None:
            env["VIBE_HOME"] = home
        return env

    def _home_dir_for_spawn(self) -> Optional[str]:
        """A fresh config root for this spawn, or ``None`` to leave it alone.

        Per **slot**, so two concurrent fan-out slots never share one writable
        config root — the corruption ``cursor-agent`` actually hit and the
        assertion §8.2's test 2 makes. vibe writes on every run: session logs,
        ``vibehistory`` and ``trusted_folders.toml``.

        ``None`` when the user (or a lane) pinned ``VIBE_HOME`` themselves —
        their directory is respected and never removed — or when a temp directory
        cannot be created, because refusing a slot over a containment mechanism
        would be a worse trade than running without it.

        **Respecting a pinned root is not merely polite here, it is what makes
        the seeded catalog reachable.** vibe reads ``$VIBE_HOME/config.toml``,
        and both container lanes seed that file into a root they choose: the
        provider lane through the wrapper's ``config_roots``, the credentialed
        lane by rendering the same ``home_seed/vibe/`` tree. An adapter that
        always minted a fresh empty directory would hand vibe a config root with
        no providers and no models in it.
        """
        if os.environ.get("VIBE_HOME"):
            return None
        with _HOME_LOCK:
            try:
                return _create_home_dir()
            except OSError:  # noqa: BLE001 - containment must never fail a run
                return None

    def get_remove_env(self) -> List[str]:
        """Strip the vendor key and every ``VIBE_*`` knob this adapter does not set.

        §2.2 rule 3: adapter wins, ambient loses, no fallback. The ``VIBE_``
        prefix overrides *any* config field, so an ambient one outranks the
        committed seed — which makes this list the thing that keeps the seed
        authoritative. ``LOG_LEVEL`` is in it because vibe reads the **bare**
        name, so an unrelated ``LOG_LEVEL=DEBUG`` in the user's shell changes
        this CLI's output shape.

        Note the division of labour the strip does **not** cover: it removes
        stale values, while :meth:`get_env` and the committed seed select the
        model and the endpoint. Neither substitutes for the other.
        """
        return list(_STRIPPED_VENDOR_VARS)
