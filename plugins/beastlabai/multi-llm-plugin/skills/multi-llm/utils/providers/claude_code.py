"""Claude Code CLI provider implementation."""

import json
import os
import re
import shutil
import subprocess
from typing import Any, Collection, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import (
    PROFILE_AGENT_READONLY,
    PROFILE_AGENT_WRITE,
    PROFILE_GENERATE,
    STRIP_VENDOR_KEYS_ALWAYS,
    STRIP_VENDOR_KEYS_NEVER,
    USAGE_FULL,
    VENDOR_BACKEND_KEEP,
    VENDOR_BACKEND_STRIP,
    MAX_STRUCTURED_OUTPUT_RETRIES,
    STRUCTURED_OUTPUT_RETRY_ENV,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    _warn_policy_once,
    declared_env_names,
    git_env,
    reset_flag_gate_cache,  # noqa: F401 - M14: re-exported for the gate's tests
    split_reasoning_effort,
    strip_vendor_keys_policy,
    vendor_backend_policy,
    warn_gate_once,
)
from .result_envelope import (
    classify_api_error_status,
    describe_refused_envelope,
    is_clean_envelope,
    parse_result_envelope,
)

# Reasoning effort values accepted by `claude --effort`
# (verified live against claude 2.1.205). Byte-identical to the CLI's own valid
# list, which it prints when it warns about an unknown value: the top five rungs
# of the ladder, with no `none` and no `minimal`.
EFFORT_LADDER = ReasoningLadder(
    provider="claude-code",
    rungs=("low", "medium", "high", "xhigh", "max"),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted

# The `agent-readonly` tool policy (D3e). Both flags are documented in
# `claude --help` (verified against 2.1.224) and take a comma- or
# space-separated list; a single comma-joined argv element is used so no part of
# the policy can be re-split by a shell.
#
# The allow-list is the positive half — only these tools may run — and the
# deny-list is belt-and-braces for the edit-capable ones plus Bash, which would
# otherwise be an unrestricted write primitive. Both are passed because an
# allow-list alone is a *permission* statement, while the deny-list survives a
# future default that widens the allowed set.
#
# The web tools are denied on this profile, not merely left out of the allow-list.
# Every read/analyze prompt this profile ever runs is `context_mode: inline` or
# `workspace-read` — its inputs travel inside the prompt or come off the pinned
# repo root — so nothing here needs the network, while the text it is fed
# (plans, diffs, review comments) is exactly the untrusted material a prompt
# injection arrives in. With egress available, a `WebFetch` to an
# attacker-named URL carrying repository content in the query string is an
# exfiltration channel that needs no write tool at all. Denying it also puts
# this runner on the same egress footing as the codex read-only profile, whose
# `--sandbox read-only` denies network by default: one task class, one policy,
# whichever runner `driver.subagent_runner` happens to name.
READONLY_ALLOWED_TOOLS = ("Read", "Grep", "Glob", "TodoWrite")
READONLY_DENIED_TOOLS = (
    "Edit",
    "MultiEdit",
    "Write",
    "NotebookEdit",
    "Bash",
    "Task",
    "WebFetch",
    "WebSearch",
)

# The `agent-write` tool policy (D3g/D3l). `--permission-mode acceptEdits` is
# Claude Code's own pre-approval for edits (documented in `claude --help`,
# verified against 2.1.224); it is NOT a sandbox, which is exactly why the
# executor layers the `driver.write_paths` policy and the pre-batch snapshot on
# top of it (D3l: the runner's mechanism is the preventive control, the policy is
# the detective second layer).
#
# `Task` stays denied on this profile too: a nested subagent would run outside
# every ceiling the executor computed (D3c `nested_exec`) and its writes would
# not appear in this dispatch's audit record. `Bash` IS allowed — an implement
# batch legitimately runs a formatter or a test — and that is precisely the hole
# the post-run policy recomputation exists to catch.
WRITE_ALLOWED_TOOLS = (
    "Read",
    "Grep",
    "Glob",
    "Edit",
    "MultiEdit",
    "Write",
    "NotebookEdit",
    "Bash",
    "TodoWrite",
    "WebFetch",
    "WebSearch",
)
WRITE_DENIED_TOOLS = ("Task",)

# The permission grant itself, named once. Two callers emit it and they must
# never both emit it into the SAME argv: `--permission-mode` is not repeatable,
# and a doubled pair normalizes to `acceptEdits+` in
# `tests/golden/normalize_argv.py`'s flag view — i.e. it fails
# `tests/container/expected_argv.yaml`'s agent-write row rather than passing
# silently. `_render_argv`'s `permission_mode` parameter is what makes that
# structurally impossible: the flag is emitted from exactly one place, and each
# profile says once whether it wants it.
PERMISSION_MODE_FLAG = "--permission-mode"
PERMISSION_MODE_ACCEPT_EDITS = "acceptEdits"

# §9.8. `--allowed-tools` / `--disallowed-tools` take `<tools...>`, so every
# token after one of them — up to a separator — is part of its VALUE. The agent
# profiles used to emit the prompt immediately after `--disallowed-tools`, and
# the variadic swallowed it: the adapter's own rendered argv, run verbatim at
# 2.1.233, exits 1 with `Error: Input must be provided either through stdin or
# as a prompt argument when using --print` and makes **zero requests**. Latent
# only because `preferred_prompt_transport('claude-code') == 'stdin'` drops the
# prompt from argv, but `build_agent_command` is a public, unit-tested surface.
#
# `--` before the prompt is one of the two fixes verified working (1 request,
# exit 0); it is the one chosen here because it keeps the prompt at `argv[-1]`,
# which every `cmd[:-1]` override, `build_agent_command_for_transport` and the
# cross-adapter `agent-write` invariant in `tests/test_providers.py` rely on.
PROMPT_SEPARATOR = "--"

# ─────────────────────────────────────────────────────────────────────────────
# M3 / §2.1 — strip vendor API keys so subscription auth wins (the "money bug").
#
# Measured on the wire at claude-code 2.1.233: with a subscription token present,
# adding `ANTHROPIC_API_KEY` swaps the request's `authorization: Bearer …` for
# `x-api-key: …` and **drops the `anthropic-beta: oauth-2025-04-20` header
# entirely** — the subscription is not used at all. The resolver checks the API
# key *before* OAuth, and Anthropic's own shipped string says so: "Your
# ANTHROPIC_API_KEY belongs to a disabled organization · Unset the environment
# variable to use your subscription instead".
#
# The strip list is longer than one name. `ANTHROPIC_AUTH_TOKEN` overrides the
# subscription the same way; `ANTHROPIC_CUSTOM_HEADERS` is a **third** `x-api-key`
# injection path (the CLI matches header names case-insensitively, so the whole
# variable goes, not a filtered subset); and an inherited `CLAUDE_CODE_USE_BEDROCK`
# is worse than a billing bug — it hung for **137 s with zero requests and zero
# output** before SIGTERM, blocking on AWS credential resolution.
#
# The bundle *does* group these families, and a one-time human read of its
# minified symbols is how the enumeration below was made exhaustive rather than
# from memory. **"Read the list from the bundle" is not a mechanism and must not
# be implemented as one:** those identifiers are minifier output, re-assigned on
# every release, so nothing here addresses them at run time or at build time.
# What ships is the pinned literal list below. Nothing in the dispatch path ever
# reads the bundle, so a CLI upgrade can never change what a run strips until a
# human bumps these tuples.
# ─────────────────────────────────────────────────────────────────────────────

# transcribed from claude-code 2.1.233 — evidence: plans/evidence-harness-
#   invocation-2026-08-16/A2-claude-code-findings.md ("Surrounding vars
#   measured", rows 3–4). Nothing at run time reads the bundle.
_CREDENTIAL_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_CUSTOM_HEADERS")
_VENDOR_BACKEND_ENV = (
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS", "CLAUDE_CODE_USE_GOOGLE_CLOUD",
    "CLAUDE_CODE_USE_MANTLE", "CLAUDE_CODE_USE_GATEWAY",
)

#: Never stripped, by name, and each for its own measured reason:
#: `OPENAI_API_KEY` is not consulted on any claude-code path and stripping it
#: breaks configs declaring `env_key = "OPENAI_API_KEY"`; `ANTHROPIC_BASE_URL`
#: is a corporate gateway's only route to a model; `CLAUDE_CONFIG_DIR` is where
#: the subscription credential lives.
NEVER_STRIPPED = ("OPENAI_API_KEY", "ANTHROPIC_BASE_URL", "CLAUDE_CONFIG_DIR")

#: `ANTHROPIC_BASE_URL` is not merely left alone — its **presence declines the
#: credential strips** (this is the donor's Q9, answered). When the org pays
#: through a gateway the subscription-vs-API-key billing question does not apply
#: either way, and stripping would produce a run that authenticates against the
#: public API with credentials meant for the gateway. `always` still strips;
#: that is what the escape hatch is for.
GATEWAY_ENV = ("ANTHROPIC_BASE_URL",)

#: The sanitized preflight (§2.1 rule 1). `claude auth status` **is** a real
#: non-interactive subcommand: it emits JSON on stdout with **zero network** in
#: ~0.3 s. Run with the full candidate strip set already removed — i.e. the env
#: the post-strip spawn would actually get — because run with those variables
#: still inherited it reports only *which credential currently wins* and says
#: nothing about whether a usable subscription survives the strip.
AUTH_STATUS_ARGV = ("auth", "status")
AUTH_PROBE_TIMEOUT_S = 5.0

#: The `authMethod` values that mean "a subscription won". Gating on
#: `apiKeySource` instead is the trap §2.1 calls out and supersedes: it names the
#: current winner and cannot separate *subscription overridden by env* (the money
#: bug — strip is correct) from *API-key-only* (strip yields "Not logged in" in
#: 0.35 s), because both report the same `apiKeySource`.
#:
#: **Two spellings, and the second one is a correction measured here.** §2.1 was
#: written against `authMethod: "oauth_token"` at 2.1.233. Re-measured at
#: **2.1.237** (four zero-network `claude auth status` runs, no paid tokens),
#: that is *not* what a subscription reports:
#:
#: | env | loggedIn | authMethod | apiKeySource | subscriptionType |
#: |---|---|---|---|---|
#: | sanitized (nothing set) | true | `claude.ai` | *absent* | `max` |
#: | `ANTHROPIC_API_KEY` set | true | `claude.ai` | `ANTHROPIC_API_KEY` | `null` |
#: | `ANTHROPIC_AUTH_TOKEN` set | true | `oauth_token` | *absent* | *absent* |
#: | `ANTHROPIC_BASE_URL` set | true | `claude.ai` | *absent* | `max` |
#:
#: So at 2.1.237 `oauth_token` is the **env-token** spelling and `claude.ai` is
#: the subscription one — the donor's reading was almost certainly taken in row
#: 3's state. `claude.ai` is added because without it the gate never fires on a
#: current CLI (it fails open, so it is a silent no-op rather than a breakage);
#: `oauth_token` is kept because dropping it would silently disable the strip on
#: the version §2.1 measured. The sanitized probe removes
#: :data:`_CREDENTIAL_ENV` before it runs, so row 3 cannot be produced by the
#: probe itself — which is exactly what makes accepting both spellings safe, and
#: exactly why the probe must be sanitized rather than merely run.
#:
#: Rows 1 and 2 are also the ambiguity §2.1's "Normative gate" describes,
#: reproduced on the wire: adding the key makes `apiKeySource` appear and
#: `subscriptionType` go `null`, while `loggedIn` stays `true` — so an
#: *unsanitized* `loggedIn: true` describes an API-key run.
OAUTH_AUTH_METHODS = frozenset({"claude.ai", "oauth_token"})

#: Positive corroboration, checked only when the CLI emits it. At 2.1.237 a real
#: subscription reports `subscriptionType: "max"`; the API-key row reports
#: `null` (already declined on `apiKeySource`) and the env-token row omits the
#: key entirely. Absent ⇒ no constraint, so a version that never emits it is
#: judged on the table alone rather than declined for a field it does not have.
SUBSCRIPTION_TYPE_KEY = "subscriptionType"

STRIP_VERDICT_STRIP = "strip"
STRIP_VERDICT_DECLINE = "decline"

#: Memoised for the **process lifetime, no TTL**, keyed on the resolved binary
#: path + `CLAUDE_CONFIG_DIR` + the candidate strip set — the strip set belongs
#: in the key because the verdict is only meaningful for the env it was
#: sanitized against. Nothing invalidates it mid-process: a credential that
#: changes under a running orchestrator keeps the run's first verdict, which is
#: precisely what makes the two lanes agree for the whole run.
_VERDICT_CACHE: Dict[Tuple[str, ...], Tuple[str, str]] = {}
#: Counts probe **spawns**, so the "one probe per process, never per slot" rule
#: is observable rather than asserted. Read by tests only.
_PROBE_SPAWNS = 0


def reset_subscription_verdict_cache() -> None:
    """Forget the memoised verdict and the spawn counter (tests only)."""
    global _PROBE_SPAWNS
    _VERDICT_CACHE.clear()
    _PROBE_SPAWNS = 0


def probe_spawn_count() -> int:
    """How many times the sanitized preflight has actually spawned."""
    return _PROBE_SPAWNS


def _decode_auth_status(stdout: str) -> Optional[Dict[str, Any]]:
    """The probe's JSON object, or ``None`` when it cannot be read.

    Undecodable output is not a verdict — it takes the decision table's last
    row (decline) like every other unknown.
    """
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        decoded = json.loads(text)
    except (ValueError, TypeError):
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            decoded = json.loads(text[start : end + 1])
        except (ValueError, TypeError):
            return None
    return decoded if isinstance(decoded, dict) else None


def _subscription_verdict(
    candidates: Sequence[str],
    *,
    base_env: Optional[Mapping[str, str]] = None,
) -> Tuple[str, str]:
    """``(verdict, reason)`` from the sanitized preflight — §2.1's decision table.

    | sanitized `claude auth status` (env already stripped) | strip? |
    |---|---|
    | exit 0, `loggedIn:true`, `authMethod:oauth_token`, no `apiKeySource` | **strip** |
    | exit 0, `loggedIn:false` — the env key was the only credential | decline |
    | exit 0, `loggedIn:true`, `apiKeySource` still present | decline |
    | exit 0, `loggedIn:true`, `authMethod` not an OAuth method | decline |
    | `ANTHROPIC_BASE_URL` present | decline |
    | non-zero exit, undecodable JSON, missing binary, probe timeout | decline |

    **Every failure declines — the gate fails *open*.** Failing closed on a probe
    hiccup would break every claude-code slot for API-key-only users, a strictly
    worse trade than an occasional per-token bill. On a decline the API-key path
    is preserved byte-for-byte.

    Scope, stated so it cannot be read wider: this is **claude-code's alone and
    gates claude-code's three credential names only**. It does not gate
    `CLAUDE_CODE_USE_*` (those follow `vendor_backend` and read configuration,
    not the probe) and it does not gate codex, which has no zero-network verdict
    at all — a codex-only run must never spawn `claude auth status`.
    """
    global _PROBE_SPAWNS
    source = dict(os.environ if base_env is None else base_env)
    for name in GATEWAY_ENV:
        if source.get(name):
            return (
                STRIP_VERDICT_DECLINE,
                f"{name} is set — the org pays through the gateway either way",
            )
    binary = shutil.which("claude")
    if binary is None:
        return STRIP_VERDICT_DECLINE, "the claude binary is not on PATH"

    strip_set = tuple(sorted(candidates))
    key = (binary, source.get("CLAUDE_CONFIG_DIR", ""), *strip_set)
    cached = _VERDICT_CACHE.get(key)
    if cached is not None:
        return cached

    # Sanitized: the candidate strip set is already gone, plus the nested-session
    # marker (a probe run from inside a Claude Code session would otherwise be
    # refused by the same guard a dispatch is), plus §2.2's global git env so it
    # cannot prompt and cannot hang on a credential helper.
    env = {k: v for k, v in source.items() if k not in set(strip_set) | {"CLAUDECODE"}}
    env.update(git_env(PROFILE_GENERATE))
    _PROBE_SPAWNS += 1
    try:
        completed = subprocess.run(
            [binary, *AUTH_STATUS_ARGV],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=AUTH_PROBE_TIMEOUT_S,
            env=env,
        )
    except subprocess.TimeoutExpired:
        verdict = (STRIP_VERDICT_DECLINE, "the auth-status probe timed out")
    except (OSError, ValueError) as exc:
        verdict = (STRIP_VERDICT_DECLINE, f"the auth-status probe failed: {exc}")
    else:
        verdict = _verdict_from_probe(completed.returncode, completed.stdout)
    _VERDICT_CACHE[key] = verdict
    return verdict


def _verdict_from_probe(returncode: int, stdout: str) -> Tuple[str, str]:
    """The decision table applied to one probe result (no I/O)."""
    if returncode != 0:
        return STRIP_VERDICT_DECLINE, f"auth status exited {returncode}"
    payload = _decode_auth_status(stdout)
    if payload is None:
        return STRIP_VERDICT_DECLINE, "auth status printed no decodable JSON"
    if payload.get("loggedIn") is not True:
        return (
            STRIP_VERDICT_DECLINE,
            "no credential survives the strip (API-key-only login)",
        )
    if payload.get("apiKeySource"):
        return (
            STRIP_VERDICT_DECLINE,
            f"a key still reaches the CLI from {payload['apiKeySource']!r}, "
            f"which stripping the environment cannot remove",
        )
    method = payload.get("authMethod")
    if method not in OAUTH_AUTH_METHODS:
        return STRIP_VERDICT_DECLINE, f"authMethod is {method!r}, not a subscription"
    if SUBSCRIPTION_TYPE_KEY in payload and not payload[SUBSCRIPTION_TYPE_KEY]:
        return (
            STRIP_VERDICT_DECLINE,
            f"{SUBSCRIPTION_TYPE_KEY} is {payload[SUBSCRIPTION_TYPE_KEY]!r} — no "
            f"subscription behind the login",
        )
    return STRIP_VERDICT_STRIP, "a subscription survives the strip"


def _stripped_vendor_backends(
    present: Sequence[str], policy: str, declared: Collection[str]
) -> List[str]:
    """The `CLAUDE_CODE_USE_*` half of the strip — §2.1's second table.

    | origin | action |
    |---|---|
    | in the ambient env, no backend in `providers.claude-code.env` | **strip** |
    | named in `providers.claude-code.env`, or `vendor_backend: keep` | never |
    | `vendor_backend: strip` | strip regardless of declaration |

    A declared backend is the user's configured auth path; stripping it
    unconditionally trades a 137 s hang for "the user's only route to a model is
    gone". Its hang risk is bounded by the per-slot timeout and the §8
    process-group kill, and that is the user's own choice.
    """
    if policy == VENDOR_BACKEND_KEEP:
        return []
    if policy == VENDOR_BACKEND_STRIP:
        return list(present)
    return [name for name in present if name not in set(declared)]


# ─────────────────────────────────────────────────────────────────────────────
# §7.3 — the retry budget is delegated to the vendor CLI, in ITS OWN env names.
#
# The CLI ships a default of **10 retries**. Measured 2026-08-16 against a stub
# that 429s forever: 11 requests and **182 s** in a single rate-limited slot
# before the harness saw anything at all — a meaningful fraction of a 600 s
# provider slot spent inside one subprocess nobody could observe. Setting these
# is closer to a bug fix than a feature.
#
# The two names both donor plans proposed are FICTIONAL and provably inert: they
# occur zero times in the shipped binary (control: the API-key variable occurs
# 185 times), and a request-timeout value expressed in seconds is ignored while
# the millisecond one aborts an 8 s request at 2.37 s. `get_env` must therefore
# never emit them; `tests/test_providers.py` asserts their absence in both
# directions (not in the env, not as a key anywhere in this module).
# ─────────────────────────────────────────────────────────────────────────────

#: §3.6's floor exactly — not one more. Below 3, `--fallback-model`'s overload
#: path is silently dead (it needs three consecutive 529s), which is why L6 and
#: L7 are atomic group A3. Above 3 buys no additional fallback capability and
#: multiplies the worst-case wall by one more API_TIMEOUT_MS each. Values above
#: 15 are silently clamped by the CLI, with a warning.
CLAUDE_CODE_MAX_RETRIES = 3

#: §9.6.c's margin rule applied one level in: the CLI must reach its own cutoff
#: and exit *before* the harness's outer deadline, or the parent kills a live
#: child and reports a bare timeout instead of the CLI's own reason. Named, never
#: a literal inside get_env.
INNER_REQUEST_MARGIN_MS = 30_000

#: The hang ceiling, and the one judgement in §7.3 — flagged as one. It is above
#: every measured single request and below the point at which a request that has
#: produced nothing is anything but hung. FALSIFIER: an attempt aborting at
#: 300 s ± jitter *with a partial answer* is a legitimate generation being
#: truncated (API_TIMEOUT_MS bounds the whole request, not time-to-first-byte),
#: and the ceiling is raised — that is not evidence of a hang.
API_TIMEOUT_CEILING_MS = 300_000


def derive_api_timeout_ms(resolved_timeout_s: int) -> Optional[int]:
    """The CLI's own per-request timeout, in **milliseconds** (§7.3).

    Derived rather than constant, because "sized to sit under the outer
    per-provider slot timeout" is a relation, not a number:

        min(300_000, (slot_s * 1000) // (MAX_RETRIES + 1) - 30_000)

    Both configured ends are safe by construction — 1800 s ⇒ 300 000 ms (worst
    case 4 × 300 s inside a 1800 s slot), 600 s ⇒ 120 000 ms (worst case 4 ×
    120 s inside a 600 s slot).

    Returns ``None`` when the slot is too short to carry a whole retry budget
    (below ~120 s the derivation goes non-positive). Emitting a zero or negative
    value would abort every request instantly, so the variable is omitted and the
    CLI's own request default applies; the retry cap still ships, since it is the
    half that is a bug fix on its own.
    """
    value = min(
        API_TIMEOUT_CEILING_MS,
        (int(resolved_timeout_s) * 1000) // (CLAUDE_CODE_MAX_RETRIES + 1)
        - INNER_REQUEST_MARGIN_MS,
    )
    return value if value > 0 else None


# ─────────────────────────────────────────────────────────────────────────────
# §3.6 — `--fallback-model`, and §5.4.1's per-flag capability gate for it.
# ─────────────────────────────────────────────────────────────────────────────

#: Verified functionally at claude **2.1.233** while this adapter's declared
#: floor is `min_version = "2.0.0"`. A measured-at version is an upper bound on
#: the true floor, never the floor itself, so raising `min_version` to it would
#: disable installs that work (§5.4.1(a) — rejected). Hence the gate below.
FALLBACK_MODEL_FLAG = "--fallback-model"
FALLBACK_MODEL_VERIFIED_AT = "2.1.233"

# ─────────────────────────────────────────────────────────────────────────────
# §4.2 — `--json-schema`, and the SAME §5.4.1 gate (M14 absorbs both, later).
# ─────────────────────────────────────────────────────────────────────────────

#: Verified at claude **2.1.227** (§4.2) and re-verified functionally here at
#: 2.1.233 against a localhost Anthropic stub, while this adapter's declared
#: floor is `min_version = "2.0.0"`. Same §5.4.1(a) rejection as
#: `--fallback-model`: a measured-at version is an upper bound on the true floor,
#: so raising the floor to it would disable installs that work. Hence the gate —
#: and it is the same one help read, not a second one.
JSON_SCHEMA_FLAG = "--json-schema"
JSON_SCHEMA_VERIFIED_AT = "2.1.227"

# ─────────────────────────────────────────────────────────────────────────────
# The account usage cap, told apart from a transient 429 by its own sentence.
# ─────────────────────────────────────────────────────────────────────────────

#: The tag :meth:`ClaudeCodeProvider.describe_failure` puts in front of a 429
#: whose sentence says the *account* is out of budget rather than the endpoint
#: momentarily busy. Both arrive as ``api_error_status: 429`` and both classify
#: ``rate_limited`` — the status is the same integer and the ladder's rate-limit
#: rung already refuses an identical re-dispatch to this adapter (rule 6(b),
#: :meth:`~ClaudeCodeProvider.internal_retries`) — so no category moves. What
#: moves is the sentence a human reads: "Rate limited (429)" says wait a
#: minute; this says the fix is another model or more credits, and the wait is
#: however long the cap takes to reset.
USAGE_LIMIT_TAG = "[USAGE_LIMIT]"

#: The measured shape (2026-09-17, ``claude-fable-5-1``, ``claude 2.1.x``):
#: ``You've reached your Fable limit. Switch to another model, or manage usage
#: credits at claude.ai/settings/usage?from=cc_cli_limit_message, to
#: continue.`` No ``API Error:`` prefix, no number, no "rate limit" — the text
#: ladder reads nothing in it, which is why it is matched here against the
#: vendor sentence and not added to a classifier table. ``usage limit`` is the
#: wording the shared rate-limit table already carries for the same condition
#: at other vendors. Lowercased before matching, like every marker table. A
#: "resets at HH:MM" clause has not been measured on this CLI and is not
#: parsed: an invented time would be worse than none.
USAGE_LIMIT_MARKERS = (
    re.compile(r"\breached your\b.{0,40}\blimit\b"),
    re.compile(r"\busage limit\b"),
    re.compile(r"\bmanage usage credits\b"),
)

# The help read, its per-process cache, the flag-token regex and the warn-once
# set that used to live here are **gone** — M14 (§5.4) absorbed them into the one
# shared gate in `base.py`. What is left below is what is genuinely this
# adapter's: which flags it gates, and what the one WARN says about the
# capability a declined flag costs. `base.reset_flag_gate_cache` is the reset,
# for the whole gate rather than for one adapter's copy of it.


#: ``modelUsage``'s camelCase counters and the normalized key each one feeds.
#: Only the cache **read** half is "cached input" (the same rule the top-level
#: block follows); ``cacheCreationInputTokens`` has no slot and is dropped.
_MODEL_USAGE_KEYS = (
    ("inputTokens", "input_tokens"),
    ("outputTokens", "output_tokens"),
    ("cacheReadInputTokens", "cached_input_tokens"),
)


def _sum_model_usage(model_usage: Any) -> Dict[str, Any]:
    """The per-model ``modelUsage`` totals summed over every model.

    Selected by name and omitted when no model reports the counter, so the
    "reported or absent, never zero" contract holds here too: a key is present
    only when at least one model carried a number for it. Every model is
    summed rather than the served one alone because the session-title call is
    a real request this invocation made and paid for.
    """
    if not isinstance(model_usage, dict):
        return {}
    totals: Dict[str, Any] = {}
    for entry in model_usage.values():
        if not isinstance(entry, dict):
            continue
        for source, target in _MODEL_USAGE_KEYS:
            value = entry.get(source)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[target] = totals.get(target, 0) + value
    return totals


def _base_name(model: str) -> str:
    """A model id with any ``:effort`` suffix removed."""
    base, _effort = split_reasoning_effort(str(model), REASONING_EFFORTS)
    return base


def validate_fallback_models(provider_config: Dict[str, Any]) -> None:
    """Validate ``providers.claude-code.fallback_models`` (§3.6).

    Run over the **whole** block, not just the key about to be dispatched: the
    contract is "fails the run at load, naming the offending key", so a bad list
    for one primary must not wait for that primary to be selected.

    The CLI **accepts a primary that is also its own fallback silently**
    (measured), so this validation is ours or nobody's — otherwise the argv
    carries a fallback that is a guaranteed no-op and only surfaces as an
    unexplained failure under load.

    Raises:
        ConfigError: naming the offending key, its value and the reason.
    """
    from ..provider_registry import ConfigError  # local: avoids an import cycle

    def fail(message: str) -> None:
        raise ConfigError(f"providers.claude-code.{message}")

    declared = {
        _base_name(entry)
        for entry in (provider_config.get("models") or [])
        if isinstance(entry, str) and entry.strip()
    }

    def check_list(where: str, primary: Optional[str], value: Any) -> None:
        if not isinstance(value, list) or not value:
            fail(
                f"{where}: expected a non-empty list of model ids, got "
                f"{value!r}. Remove the key rather than leaving it empty — the "
                f"shipped value is an empty map and emits no flag at all."
            )
        seen: List[str] = []
        for entry in value:
            if not isinstance(entry, str) or not entry.strip():
                fail(f"{where}: {entry!r} is not a model id")
            name = _base_name(entry.strip())
            if primary is not None and name == primary:
                fail(
                    f"{where}: {entry!r} is its own primary. The CLI accepts "
                    f"this silently and the fallback is then a guaranteed no-op."
                )
            if name in seen:
                fail(f"{where}: {entry!r} is repeated")
            seen.append(name)
            if declared and name not in declared:
                fail(
                    f"{where}: {entry!r} is not one of the models this provider "
                    f"declares ({', '.join(sorted(declared))})"
                )

    mapping = provider_config.get("fallback_models")
    if mapping:
        if not isinstance(mapping, dict):
            fail(
                f"fallback_models: expected a map of "
                f"{{<primary-model>: [<fallback>, …]}}, got {mapping!r}"
            )
        for primary, value in mapping.items():
            if not isinstance(primary, str) or not primary.strip():
                fail(f"fallback_models: {primary!r} is not a model id")
            check_list(
                f"fallback_models.{primary}", _base_name(primary.strip()), value
            )

    default = provider_config.get("fallback_models_default")
    if default is not None:
        check_list("fallback_models_default", None, default)


class ClaudeCodeProvider(LLMProvider):
    """Provider for Claude Code CLI tool.

    This provider wraps the Claude Code CLI (claude), which returns responses in a JSON
    wrapper format: {"type":"result","result":"..."}. The provider handles
    extraction of the actual response content and JSON parsing with fallback
    strategies for code blocks and raw JSON.

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``opus:high``), translated to ``--effort <effort>``. Valid efforts are
    listed in REASONING_EFFORTS; anything else passes through verbatim as
    the model name.

    When invoked from within a Claude Code session, the CLAUDECODE env var is
    stripped to avoid the nested-session guard.

    Everything below was **measured** by the §6 step-5 probe on 2026-08-19
    against ``claude 2.1.232`` driven offline at a localhost Anthropic stub
    (``--network none``, no credential), and re-measured by the same rig on
    2026-10-08 against ``claude 2.1.293`` (one API call per exec now, no
    session-title call; every verdict below unchanged); the raw captures are
    ``tests/fixtures/claude-code/`` and its README carries the full record.

    **The whole diagnosis rides stdout and stderr is 0 bytes** — on all eleven
    measured outcomes, success and failure alike. Every failure the envelope
    reports is prefixed ``API Error:``.

    **The exit code is authoritative at this version.** Eight injected failure
    modes (401, 429, 404, 400 context-length, 5xx-forever, a truncated stream, a
    zero-byte response, a 200 carrying an error object) all exit **1**; both
    answering runs exit **0**. That is what makes this adapter's empty
    :attr:`exit_zero_failure_markers` correct today — measured, not assumed.

    **Two requests per exec, not one.** The first is claude-code's own
    session-title generator: tool-free, *same model*, same surface, so only the
    presence of ``tools`` separates the two on the wire. A failure-injection run
    therefore hits the injected error on the title call first, and the measured
    request counts are 4 per API call × 2 calls at the pinned
    ``CLAUDE_CODE_MAX_RETRIES=3``.

    **The envelope's own verdict is read, and that is what fixed three of the
    four classification defects this set was captured to record.**
    :meth:`parse_output` no longer serves the ``result`` of an envelope the CLI
    flagged: ``is_error`` and a non-``completed`` ``terminal_reason`` are
    enforced by :func:`result_envelope.parse_result_envelope`, whose value table
    is measured off these eleven captures. :meth:`classify_failure` reads
    ``api_error_status`` as a rung ahead of the text ladder, so a 401 answers
    ``auth_failed`` (its own :attr:`auth_error_patterns` entry answers the same
    from the text) and a 404 answers ``invalid_model`` where the ladder had no
    route at all — the CLI replaces the vendor sentence with *"There's an issue
    with the selected model (X). It may not exist…"*, which no
    ``INVALID_MODEL_MARKERS`` entry matches at any ladder order. Two JSON
    documents in one ``result`` are resolved **last**-wins by
    ``extract_json_from_text``.

    **What is still imprecise, and is pinned rather than hidden:** both
    connection-shaped failures (``truncated``, ``zero-byte-response``) answer
    ``server_error``. Their ``api_error_status`` is ``null`` — no HTTP response
    ever arrived — so the status rung defers, and the text falls to
    ``\\bapi error\\b`` in ``SERVER_ERROR_MARKERS`` via this CLI's universal
    ``API Error:`` prefix. Both categories are retryable, so the verdict costs
    nothing here; the manifest rows say so.
    """

    # `claude -p` reads the prompt from stdin when no prompt argument is given,
    # so this adapter has a real non-argv transport (D2d). Materialized prompts
    # are dispatched over stdin, which removes the Windows command-line cap from
    # the prompt budget entirely; the fan-out path's default stays "argv" so
    # existing invocations are byte-identical.
    supported_prompt_transports = ("argv", "stdin")

    # Subagent-runner declarations (D3e/D3j/D3m). `agent-write` is the
    # `--permission-mode acceptEdits` invocation below; `supports_file_edits`
    # tracks it so `tests/test_providers.py` can cross-check the declaration
    # against the implemented branch in both directions.
    agent_profiles = (PROFILE_GENERATE, PROFILE_AGENT_READONLY, PROFILE_AGENT_WRITE)
    supports_file_edits = True
    supports_workspace_reads = True
    # Claude Code denies `Read` outside its working directory unless the
    # directory is added: a validation batch naming a snapshot in a phase dir
    # outside the repo gets `--add-dir <dir>` (validation-context-by-path §2.2).
    read_scope_flag = "--add-dir"
    # MEASURED FALSE, and by design: `generate` renders `--permission-mode
    # acceptEdits`, which "auto-accepts FILE EDITS only; Bash and the rest still
    # hit the headless prompt and are denied" (the argv comment in
    # `_render_argv`). The 2026-09-25 `review-code` envelope carries three
    # `Bash` `permission_denials` and the run still returned 27 findings, so any
    # `git diff` it tried was denied. `generate_read_scope` keeps the "cwd"
    # default: only the executor widens reads with `--add-dir` (above), and
    # `generate` never renders it.
    runs_shell_in_generate = False
    usage_support = USAGE_FULL
    # §4.2.2: this adapter really emits `--json-schema` when handed a schema (see
    # `build_command`), so the caller may mark an accepted result `native`.
    structured_output_support = True
    # No `auth_check`: the CLI ships no non-interactive login-status subcommand
    # (`/status` is an in-session slash command, and `claude setup-token` starts a
    # login flow), and inventing one out of a throwaway generating dispatch would
    # cost a model call per run. The auth state is therefore recorded `unknown`
    # (D3c) and a login notice is still caught reactively by auth_error_patterns.
    login_cmd = "claude login"
    version_cmd = ("claude", "--version")
    #: M14/§5.4 — the floor names the FEATURE it protects: 2.0.0 is where
    #: ``claude -p --output-format json`` settled into the ``result`` envelope
    #: this adapter's :meth:`parse_output` and :meth:`parse_usage` read. It stays
    #: 2.0.0 — §5.4.1(a): a measured-at version is an upper bound on the true
    #: floor, never the floor itself, and raising it to the build
    #: ``--fallback-model`` or ``--json-schema`` happened to be probed on would
    #: disable installs that work. Those two are gated per flag instead
    #: (:meth:`~.base.LLMProvider.supports_flag`), which is the whole reason
    #: §5.4.1(b) exists.
    min_version = "2.0.0"
    #: No ceiling. ``max_version_exclusive`` would be a *refusal*, and no claude
    #: release has been measured to break this parser; ``verified_version`` below
    #: carries the "newer than the capture" warning, which is what an unmeasured
    #: future build honestly deserves.
    #: 2.1.232 is where every fixture under ``tests/fixtures/claude-code/`` was
    #: captured (``manifest.yaml``'s ``cli_version``), and it is what the image
    #: really installs — ``tests/container/cli-versions.lock`` pins it and
    #: ``verify_versions.py`` fails the build if the layer resolved anything
    #: else. Re-confirmed 2026-08-20 by running the pinned binary directly:
    #: ``docker run --rm --network none --entrypoint /opt/mllm/real/claude
    #: mllm-e2e:local --version`` prints ``2.1.232 (Claude Code)`` on stdout,
    #: which the base :meth:`parse_version` reads without an override.
    #:
    #: It was left at 2.1.224 through the fixture capture only because this
    #: string is pinned in a second place — ``tests/mocks/mock_llm.py``'s
    #: ``VERSION_STRINGS``, which ``test_subagent_executor.py::
    #: test_the_mock_version_matches_each_verified_version`` asserts this value
    #: is a substring of. Both are moved together; that test names no version
    #: itself, so it is the pair that has to stay coherent, not a third
    #: expectation.
    #:
    #: 2.1.293 since 2026-10-08 (run 10, #10): every row re-captured on it by the
    #: same rig in the pinned image (cli-versions.lock moved to 2.1.293 the same
    #: day); the parser's verdict on every row is unchanged, and the envelope
    #: only gained keys (``queued_turn_count``, ``result_index``,
    #: ``safety_stops``, ``subagent_stats``, ``first_content_frame_ms``).
    verified_version = "2.1.293"

    #: §7.2 — the base auth set, EXTENDED by this CLI's own measured 401 gloss
    #: (C3). ``tests/fixtures/claude-code/auth-error.stdout.txt`` is failserver
    #: `--mode 401` captured at 2.1.232, and the sentence claude-code prints is
    #: ``Failed to authenticate. API Error: 401 Incorrect API key provided: …``.
    #: Not one of :data:`base.LLMProvider.auth_error_patterns`' ten entries
    #: matches it, while ``\bapi error\b`` in ``SERVER_ERROR_MARKERS`` matches
    #: the universal ``API Error:`` prefix — so a 401 classified ``server_error``
    #: and was retried **eight times** against a condition no retry can fix.
    #:
    #: The added phrase is claude-code's **own** wording, not the upstream
    #: provider's: everything after ``API Error:`` is whatever server answered,
    #: while ``Failed to authenticate.`` is what this CLI writes in front of any
    #: of them. Measured against every capture in ``tests/fixtures/claude-code/``
    #: — it occurs in `auth-error` and nowhere else, so no success row moves.
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "failed to authenticate",
    )

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "claude-code"

    @property
    def default_timeout(self) -> int:
        """Return the default timeout in seconds."""
        return 600

    def is_available(self) -> bool:
        """Check if Claude Code CLI is available in PATH."""
        return shutil.which("claude") is not None

    # ── §3.6: the fallback list is configuration, and it ships empty ─────────

    def _provider_config(self) -> Dict[str, Any]:
        """This provider's own block from the layered config (§3.6).

        Read through the normal layering (base → auto-discovered
        ``<git-root>/.multi-llm/providers.yaml`` → ``MULTI_LLM_PROVIDERS_CONFIG``),
        so a fallback list is configured exactly where every other provider
        setting is.

        ``build_command`` has no anchor to thread (the signature is the base
        class's, shared by every adapter and every caller), so this is §9.3.b's
        backstop used deliberately and explicitly: the run's pinned plan path,
        or CWD when no pre-flight set one.
        """
        from ..provider_registry import get_run_anchor, load_config  # import cycle

        config = load_config(anchor=get_run_anchor())
        block = (config.get("providers") or {}).get(self.name)
        return block if isinstance(block, dict) else {}

    def fallback_models(self, model: str) -> List[str]:
        """The configured fallback list for ``model``, or ``[]`` (§3.6).

        **Default off, explicit per model, never silently substituted.** The
        probe proves the *flag* works; it says nothing about which model should
        stand in for which. There is no built-in haiku stand-in and no
        `sonnet → haiku` degrade ladder: the configured list *is* the whole
        source, joined verbatim in the user's own order, and an unconfigured
        primary emits no flag at all.

        The whole block is validated here rather than just the selected key, so a
        malformed entry fails the run before any child is spawned.
        """
        block = self._provider_config()
        validate_fallback_models(block)
        mapping = block.get("fallback_models") or {}
        primary = _base_name(model)
        configured = None
        if isinstance(mapping, dict):
            configured = mapping.get(primary) or mapping.get(model)
        if configured is None:
            configured = block.get("fallback_models_default")
        if not configured:
            return []
        return [str(entry).strip() for entry in configured]

    # `supports_flag` is **not** overridden here any more. It was L7's one-off —
    # shipped inside that task because §3.6 is in the severable live-defect set
    # and may not depend on §11.2 — and M14 absorbed it into
    # `LLMProvider.supports_flag`, which answers both flags below from one
    # memoised help read of the binary `version_cmd` names. The optional-flag
    # posture it holds is unchanged: unsupported *or undecidable* ⇒ False, whole
    # word only, because `--fallback-model` is a prefix of
    # `--fallback-model-chain` and a substring probe would confirm a flag that
    # does not exist.

    def _fallback_flag_supported(self) -> bool:
        supported = self.supports_flag(FALLBACK_MODEL_FLAG)
        if not supported:
            warn_gate_once(
                ("claude", FALLBACK_MODEL_FLAG),
                f"[WARN] claude-code: {FALLBACK_MODEL_FLAG} is not documented by "
                f"the installed CLI's own help (verified at "
                f"{FALLBACK_MODEL_VERIFIED_AT}); the configured fallback models "
                f"are not passed and this run has no overload/404 fallback. "
                f"Everything else is unchanged.",
            )
        return supported

    def _json_schema_flag_supported(self) -> bool:
        """§5.4.1's gate for ``--json-schema``, answered from the SAME help read.

        One help read per CLI per process, memoised on the resolved binary — not
        one per flag — so adding this capability adds no spawn. Optional-flag
        posture: unsupported or undecidable ⇒ the flag is omitted with one WARN
        and the phase falls back to prompt-level JSON plus §4.2.1's recovery
        branch. The degraded run is a documented degraded mode, and it is marked
        ``recovered`` (or fails as ``schema_violation``), **never** ``native``.
        """
        supported = self.supports_flag(JSON_SCHEMA_FLAG)
        if not supported:
            warn_gate_once(
                ("claude", JSON_SCHEMA_FLAG),
                f"[WARN] claude-code: {JSON_SCHEMA_FLAG} is not documented by "
                f"the installed CLI's own help (verified at "
                f"{JSON_SCHEMA_VERIFIED_AT}); the schema is not passed and this "
                f"phase falls back to prompt-level JSON with schema-validated "
                f"recovery. The result is marked 'recovered', never 'native'.",
            )
        return supported

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build the claude command with JSON output format.

        Args:
            prompt: The prompt text to send to the LLM.
            model: The model identifier to use (e.g., 'sonnet', 'opus', 'haiku').
            timeout_s: Accepted and ignored — claude has no internal print-mode
                cutoff to keep under the parent's deadline (§9.6.a).
            schema: §4.2.2's optional structured-output schema. claude's
                transport is **inline** (`--json-schema <json>`), so only
                ``schema.document`` is read and ``schema.path`` is irrelevant
                here — the asymmetry with codex's file is encoded in the two
                adapters, not in the caller.

        This is the **fan-out** invocation, and it carries
        ``--permission-mode acceptEdits`` because its own prompt asks the model
        to write the answer to a file (``supports_file_output = True``). See the
        splice comment in :meth:`_render_argv` for the measurement that made the
        grant necessary, and that method's docstring for why `agent-readonly`
        does not get it.

        Returns:
            Command arguments for Claude Code CLI invocation.
        """
        return self._render_argv(
            prompt,
            model,
            timeout_s=timeout_s,
            schema=schema,
            permission_mode=PERMISSION_MODE_ACCEPT_EDITS,
        )

    def _render_argv(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        permission_mode: Optional[str],
    ) -> List[str]:
        """The one argv renderer every profile goes through.

        ``permission_mode`` is the single knob the three profiles disagree on,
        and it is a **parameter rather than a post-hoc splice or strip** so the
        flag has exactly one emission site:

        * ``generate`` (:meth:`build_command`) passes ``acceptEdits`` — the write
          grant its own prompt asks for, see the comment at the splice below;
        * ``agent-write`` passes ``acceptEdits`` too, and no longer appends a
          second copy of its own. `--permission-mode` is not repeatable, and the
          duplicate this parameter replaced was a real defect: it rendered
          ``--permission-mode acceptEdits --permission-mode acceptEdits``, which
          `normalize_argv` collapses to ``acceptEdits+`` and
          `tests/container/expected_argv.yaml`'s agent-write row then rejects;
        * ``agent-readonly`` passes ``None`` and emits the flag **not at all**.
          That profile's whole contract is that Claude Code's own permission
          mechanism refuses edits, and its dispatches never need a write: the
          executor captures stdout and writes ``output_path`` itself, so the
          model only prints. Handing it an edit-accepting permission mode would
          contradict the profile in words even though `READONLY_DENIED_TOOLS`
          still refuses `Write` in fact.
        """
        # claude -p --output-format json [--json-schema <json>]
        #        --model <model> [--effort <effort>]
        #        [--permission-mode acceptEdits] [--fallback-model <m1,m2>]
        #        <prompt>
        base_model, effort = split_reasoning_effort(model, REASONING_EFFORTS)
        cmd = [
            "claude",
            "-p",
            "--output-format",
            "json",
        ]
        # §4.2.2's normative splice point, at a FIXED INDEX immediately after
        # `--output-format json` — never an append before `cmd[-1]`. That one
        # position makes all six rows right at once (generate on argv and on
        # stdin, both agent profiles on both transports):
        #
        # * it is inside the policy region, ahead of `--model`, so the prompt is
        #   never the token after the schema and the schema is never the token
        #   after the prompt;
        # * it precedes the variadic `--allowed-tools` / `--disallowed-tools`
        #   the agent profiles splice in later, so §9.8's swallowing trap cannot
        #   reach it;
        # * `cmd[-1] is the prompt` still holds, which every `cmd[:-1]` override
        #   and `build_agent_command_for_transport` relies on.
        #
        # The value is rendered with sorted keys and compact separators so one
        # schema file always produces one argv byte string — a golden fixture
        # cannot churn on dict ordering.
        if schema is not None and self._json_schema_flag_supported():
            cmd += [
                JSON_SCHEMA_FLAG,
                json.dumps(
                    dict(schema.document), sort_keys=True, separators=(",", ":")
                ),
            ]
        cmd += [
            "--model",
            base_model,
        ]
        if effort is not None:
            cmd += ["--effort", effort]
        # §3.6's splice point: in the policy region beside --model/--effort,
        # INSIDE build_command and ahead of the prompt append. That one position
        # makes all four rows right at once — generate on argv and on stdin, and
        # both agent profiles, each carrying the flag *before* the variadic
        # --allowed-tools / --disallowed-tools and never adjacent to the prompt.
        # Appending it after the prompt would break `cmd[-1] is the prompt` in
        # two directions: build_command_for_transport's stdin branch returns
        # cmd[:-1] and would ship a valueless --fallback-model, and the agent
        # profiles splice their tool policy in after cmd[-1].
        # THE WRITE GRANT THE FAN-OUT ALWAYS NEEDED, and whose absence was a
        # measured defect (harness-expansion.md §17). `supports_file_output` is
        # True here, so `render_output_location` ends the review prompt with
        # "write your JSON output to this file: <path>" — and this argv granted
        # nothing, so headless `claude -p` DENIED the model's own Write. Measured
        # 2026-08-20 on the credentialed live lane: exit 0, `is_error: false`,
        # `subtype: "success"`, `permission_denials: [{"tool_name": "Write"}]`,
        # the answer "Permission is required to write to the file", and the slot
        # then dying in `parse_output`. Every other file-output adapter already
        # grants this on the SAME fan-out path -- codex `--sandbox
        # workspace-write`, opencode's write-capable `run` agent, kilocode
        # `--auto` -- so claude-code was the outlier, not the exception.
        #
        # `--permission-mode acceptEdits` and NOT `--allowed-tools Write`: it is
        # non-variadic, so it cannot swallow the trailing positional (§9.8) and
        # `cmd[-1] is the prompt` still holds for the stdin transport's
        # `cmd[:-1]`. It auto-accepts FILE EDITS only; Bash and the rest still hit
        # the headless prompt and are denied, which is the narrow grant this path
        # wants. It is deliberately NOT `--yolo`/`-f`: that is the write bypass
        # §3.1 removed, and this is not it.
        #
        # Emitted here for `generate` and `agent-write` and OMITTED for
        # `agent-readonly` — see `_render_argv`'s own docstring for why the knob
        # is a parameter and not a splice the agent branches undo.
        if permission_mode is not None:
            cmd += [PERMISSION_MODE_FLAG, permission_mode]
        fallbacks = self.fallback_models(model)
        if fallbacks and self._fallback_flag_supported():
            cmd += [FALLBACK_MODEL_FLAG, ",".join(fallbacks)]
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
        command-line cap. The fixed-index schema splice is what makes the two
        transports differ by **exactly** the prompt element and nothing else.
        """
        if transport != "stdin":
            return super().build_command_for_transport(
                prompt, model, transport, prompt_file, timeout_s=timeout_s,
                schema=schema,
                sandbox_fallback=sandbox_fallback,
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        return cmd[:-1], prompt

    def build_agent_command(
        self,
        prompt: str,
        model: str,
        profile: str = PROFILE_AGENT_READONLY,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build an agentic ``claude -p`` invocation for ``profile`` (D3e).

        ``agent-readonly`` is ``build_command`` plus an explicit tool policy:
        an allow-list of read-only tools and a deny-list of every edit-capable
        one. Writes are refused by Claude Code's own permission mechanism, not by
        anything this repo enforces after the fact, which is what makes it safe
        to hand an untrusted (plan/diff/review) prompt to.

        ``agent-write`` swaps that policy for the edit-capable one and keeps
        ``--permission-mode acceptEdits``, which is what makes a headless apply /
        implement batch possible at all. It is deliberately **not** a
        ``--dangerously-skip-permissions``-class bypass: the executor pins ``cwd``
        to the resolved repo root (D3h), enforces ``driver.write_paths`` on both
        sides of the run and snapshots every file the batch may touch (D3l).

        Both branches render through :meth:`_render_argv` rather than through
        :meth:`build_command`, so the permission grant `generate` needs is
        **asked for once per profile** instead of being inherited and then
        patched: `agent-write` requests it (one pair, never two) and
        `agent-readonly` declines it.
        """
        if profile == PROFILE_AGENT_WRITE:
            cmd = self._render_argv(
                prompt,
                model,
                timeout_s=timeout_s,
                schema=schema,
                permission_mode=PERMISSION_MODE_ACCEPT_EDITS,
            )
            return [
                *cmd[:-1],
                "--allowed-tools",
                ",".join(WRITE_ALLOWED_TOOLS),
                "--disallowed-tools",
                ",".join(WRITE_DENIED_TOOLS),
                PROMPT_SEPARATOR,
                cmd[-1],
            ]
        if profile != PROFILE_AGENT_READONLY:
            return super().build_agent_command(
                prompt, model, profile, timeout_s=timeout_s, schema=schema
            )
        cmd = self._render_argv(
            prompt, model, timeout_s=timeout_s, schema=schema,
            permission_mode=None,
        )
        # _render_argv appends the prompt last; splice the policy in before it.
        return [
            *cmd[:-1],
            "--allowed-tools",
            ",".join(READONLY_ALLOWED_TOOLS),
            "--disallowed-tools",
            ",".join(READONLY_DENIED_TOOLS),
            PROMPT_SEPARATOR,
            cmd[-1],
        ]

    def build_agent_command_for_transport(
        self,
        prompt: str,
        model: str,
        profile: str = PROFILE_AGENT_READONLY,
        transport: str = "argv",
        prompt_file: Optional[str] = None,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
        sandbox_fallback: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """Drop the ``--`` separator along with the prompt it shields (§9.8).

        The separator exists for exactly one reason: to end option parsing so the
        variadic ``--disallowed-tools`` cannot swallow the trailing positional.
        Under the ``stdin`` transport there is no positional left, so a surviving
        bare ``--`` would be a token with nothing to separate — and it would move
        the two claude-code agent rows in ``tests/container/expected_argv.yaml``
        (both ``transport: stdin``) for no behavioural reason. Dropping it keeps
        the stdin argv byte-identical to what this adapter has always emitted.
        """
        argv, stdin_text = super().build_agent_command_for_transport(
            prompt, model, profile, transport, prompt_file, timeout_s=timeout_s,
            schema=schema, sandbox_fallback=sandbox_fallback,
        )
        if transport == "stdin" and argv and argv[-1] == PROMPT_SEPARATOR:
            return argv[:-1], stdin_text
        return argv, stdin_text

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Recover usage from the ``--output-format json`` result envelope (D3j).

        ``parse_output`` unwraps ``result`` and **discards the envelope**, which
        is where ``usage`` and ``total_cost_usd`` live, so this captures it before
        it is dropped. Fields are selected by name and omitted when absent — a
        zero would read as a free run.
        """
        text = (stdout or "").strip()
        if not text.startswith("{"):
            return None
        try:
            envelope = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(envelope, dict) or envelope.get("type") != "result":
            return None

        usage = envelope.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        out: Dict[str, Any] = {}

        def _put(key: str, value: Any) -> None:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[key] = value

        _put("input_tokens", usage.get("input_tokens"))
        _put("output_tokens", usage.get("output_tokens"))
        # Claude Code reports cache reads and cache writes separately; only the
        # read half is "cached input".
        _put("cached_input_tokens", usage.get("cache_read_input_tokens"))

        # The top-level ``usage`` block is the FINAL TURN's, not the run's:
        # ``modelUsage`` is the per-model total for the whole invocation, and on
        # every committed success capture it exceeds the block above by exactly
        # the session-title call (1/1 beside 2/2). When the final turn is the
        # API call that failed, the block above is all zeros while the run has
        # already spent what ``modelUsage`` records. Measured 2026-09-17 on
        # ``claude-fable-5-1``: ``usage.output_tokens: 0`` beside
        # ``modelUsage[...].outputTokens: 137348`` and ``total_cost_usd: 25.05``
        # — a report of "0 tokens, $25.05" is the exact "zero would read as a
        # free run" this extractor exists to avoid. So a turn that reports no
        # tokens at all defers to the per-model totals; a turn that reports any
        # keeps the block the tests pin, because the two disagree by a known
        # amount on a good run and this is not the place to re-attribute it.
        if not any(out.get(k) for k in ("input_tokens", "output_tokens", "cached_input_tokens")):
            totals = _sum_model_usage(envelope.get("modelUsage"))
            if totals:
                out.update(totals)

        _put("cost_usd", envelope.get("total_cost_usd"))
        if "input_tokens" in out and "output_tokens" in out:
            out["total_tokens"] = out["input_tokens"] + out["output_tokens"]

        # §3.6: cost follows the served model. This extractor already holds the
        # one envelope that carries `modelUsage`, so the attribution rides the
        # same channel as the tokens it belongs to rather than being re-parsed.
        # It is a string among numbers on purpose — the numeric accumulator
        # ignores it, and nothing about "absent means not reported" changes.
        served = self._served_model_from_envelope(envelope)
        if served:
            out["served_model"] = served
        return out or None

    @staticmethod
    def _served_model_from_envelope(envelope: Dict[str, Any]) -> Optional[str]:
        """The model that actually served the turn, from ``modelUsage``.

        Keyed by model id. With more than one key (a turn that changed models
        mid-flight), the one that produced the most output is the one the answer
        came from; ties keep insertion order.
        """
        usage = envelope.get("modelUsage")
        if not isinstance(usage, dict) or not usage:
            return None
        names = [name for name in usage if isinstance(name, str) and name]
        if not names:
            return None

        def produced(name: str) -> float:
            entry = usage.get(name)
            if not isinstance(entry, dict):
                return 0.0
            value = entry.get("outputTokens", entry.get("output_tokens", 0))
            return float(value) if isinstance(value, (int, float)) else 0.0

        return max(names, key=produced)

    def parse_served_model(self, stdout: str, stderr: str = "") -> Optional[str]:
        """``served_model`` from the ``--output-format json`` envelope (§3.6).

        claude's envelope carries ``modelUsage`` keyed by the model that actually
        served the turn — measured: a 529 run's fourth request and its
        ``modelUsage`` both name ``claude-haiku-4-5-20251001``. Returns ``None``
        for anything unparseable; this is attribution, never a failure path.
        """
        text = (stdout or "").strip()
        if not text.startswith("{"):
            return None
        try:
            envelope = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(envelope, dict):
            return None
        return self._served_model_from_envelope(envelope)

    def resolve_served_model(
        self,
        stdout: str,
        requested_model: str,
        fallback_models: Optional[Sequence[str]] = None,
    ) -> Tuple[str, bool, Optional[str]]:
        """``(served_model, is_fallback, warning)`` for one attempt (§3.6).

        Attribution is mandatory whenever a fallback is configured: without it a
        report attributes a haiku answer to the sonnet the user asked for, and
        the quality and cost delta is invisible at exactly the moment it matters.
        When the two differ the caller emits one WARN naming phase / requested /
        served, and every report that names a model labels that row with the
        **served** model and marks it ``fallback``.

        **Read, never depended on.** If ``modelUsage`` is absent, or names a
        model outside {primary} ∪ configured fallbacks, the *requested* model is
        recorded and a warning is returned — an attribution field never fails an
        otherwise-successful attempt.

        Alias matching is deliberately loose in one direction only: config names
        aliases (``sonnet``, ``haiku``) while the envelope names resolved ids
        (``claude-haiku-4-5-20251001``), so an alias matches an id that contains
        it. A miss costs a WARN and the requested model, never the run.
        """
        requested = _base_name(requested_model)
        served = self.parse_served_model(stdout, "")
        if not served:
            return (
                requested_model,
                False,
                f"claude-code: the result envelope carried no `modelUsage`, so "
                f"the answer is attributed to the requested model "
                f"({requested_model}) — it may have been served by a fallback.",
            )

        def matches(alias: str) -> bool:
            alias = _base_name(str(alias)).strip().lower()
            low = served.lower()
            return bool(alias) and (alias == low or alias in low)

        if matches(requested):
            return served, False, None
        for candidate in fallback_models or ():
            if matches(candidate):
                return (
                    served,
                    True,
                    f"claude-code: `--fallback-model` fired — requested "
                    f"{requested_model}, served {served}. The result is "
                    f"attributed to the served model.",
                )
        return (
            requested_model,
            False,
            f"claude-code: `modelUsage` names {served}, which is neither the "
            f"requested model ({requested_model}) nor a configured fallback "
            f"({', '.join(fallback_models or ()) or 'none'}); recording the "
            f"requested model.",
        )

    def resolved_timeout_s(self) -> int:
        """The outer per-provider slot timeout `get_env` derives from (§7.3).

        The same value §7.5 rule 1 takes its deadline from: ``providers.yaml``'s
        ``default_timeout`` (**1800** for claude-code) or the configured
        override, falling back to this adapter's own ``default_timeout`` (600)
        when the provider is absent from config or the read fails.

        ``get_env`` has no anchor to thread either, so it reads the same §9.3.b
        run anchor ``_provider_config`` does — the alternative is a slot timeout
        resolved against CWD while the fan-out resolves its own against the
        plan, i.e. an inner budget sized for the wrong outer deadline.
        """
        try:
            from ..provider_registry import (  # import cycle
                get_provider_timeout,
                get_run_anchor,
            )

            value = int(get_provider_timeout(self.name, anchor=get_run_anchor()))
        except Exception:  # noqa: BLE001 - env shaping must never fail a run
            return self.default_timeout
        return value if value > 0 else self.default_timeout

    @property
    def internal_retries(self) -> InternalRetryEnvelope:
        """What `claude -p` does inside one awaited subprocess (§7.6(b)).

        Measured 2026-08-16 against a stub that 429s forever: **11 requests and
        182 s** at the CLI's own default of 10 retries. The number declared here
        is **4**, the post-L6 one, because L6 has landed and every dispatch this
        harness makes carries ``CLAUDE_CODE_MAX_RETRIES=3``; declaring 11 would
        budget for a configuration nothing here runs.

        A **property**, not a constant, because ``max_wall_s`` is 4 ×
        ``API_TIMEOUT_MS`` and ``API_TIMEOUT_MS`` is itself *derived from the
        resolved slot timeout* (§7.3) — 1200 s at a 1800 s slot, 480 s at a 600 s
        one. Both halves therefore come from the same
        :func:`derive_api_timeout_ms` call ``get_env`` makes, so the bound §7.5
        rule 4 subtracts can never disagree with the env the child was handed.
        A slot too short to carry a whole retry budget emits no ``API_TIMEOUT_MS``
        at all, and the wall is then honestly ``None`` rather than a guess.

        ``retries_rate_limit`` is ``True`` — the 182 s measurement *is* a
        rate-limit chain — which is what makes §7.5 rule 6(b) forbid an identical
        rate-limit re-dispatch to this adapter: ≤ 3 harness backoffs would turn 4
        requests into 20 against the same upstream for the same verdict.
        """
        requests = CLAUDE_CODE_MAX_RETRIES + 1
        api_timeout_ms = derive_api_timeout_ms(self.resolved_timeout_s())
        return InternalRetryEnvelope(
            max_requests=requests,
            max_wall_s=(
                None if api_timeout_ms is None else requests * api_timeout_ms / 1000.0
            ),
            retries_rate_limit=True,
            configurable_by=("CLAUDE_CODE_MAX_RETRIES", "API_TIMEOUT_MS"),
        )

    def get_env(self, model: str) -> Dict[str, str]:
        """Delegate retry to the vendor CLI's own engine (§7.3, task L6).

        Absorbs transient 429s inside the one subprocess already awaited, instead
        of wrapping it in a harness-side retry loop. Two variables, both in the
        CLI's real names (see the module comment for the two fictional ones this
        must never emit), and both chosen together with §3.6's
        ``--fallback-model``: below three retries its overload path is silently
        dead, which is why they are atomic group A3.
        """
        env = {"CLAUDE_CODE_MAX_RETRIES": str(CLAUDE_CODE_MAX_RETRIES)}
        api_timeout_ms = derive_api_timeout_ms(self.resolved_timeout_s())
        if api_timeout_ms is not None:
            env["API_TIMEOUT_MS"] = str(api_timeout_ms)
        # §4.2.1's pinned structured-output budget. Emitted UNCONDITIONALLY, not
        # only when a schema is attached: the variable is inert without
        # `--json-schema`, and making it conditional would mean a dispatch that
        # acquired a schema by some other route (a future caller, a config
        # default) silently ran at the CLI's default of FIVE paid model calls.
        # Setting it here also keeps it in the one env builder both lanes share,
        # so Lane A and Lane B can never disagree about the budget.
        env[STRUCTURED_OUTPUT_RETRY_ENV] = str(MAX_STRUCTURED_OUTPUT_RETRIES)
        return env

    def get_remove_env(
        self,
        anchor: Optional[str] = None,
        base_env: Optional[Mapping[str, str]] = None,
    ) -> List[str]:
        """`CLAUDECODE`, plus M3's two independently gated vendor-key strips.

        **`CLAUDECODE` is in every outcome, including `strip_vendor_keys:
        never`.** When this provider is invoked from within a Claude Code
        session the parent sets `CLAUDECODE=1`, the child `claude -p` detects it
        and refuses to start, so that strip is not a policy — it is what makes
        the dispatch work at all.

        The two vendor gates on top of it are independent of each other (§2.1):

        * the **credential** names (:data:`_CREDENTIAL_ENV`) follow
          `providers.claude-code.strip_vendor_keys` — `auto` (default) consults
          the sanitized `claude auth status` preflight and its decision table,
          `always` strips regardless, `never` declines regardless;
        * the **vendor-backend** names (:data:`_VENDOR_BACKEND_ENV`) follow
          `providers.claude-code.vendor_backend` and the *declaration* table, not
          the probe.

        Only names **present in the ambient environment** are returned. Removing
        a name that is not there is a no-op on both lanes, so this changes no
        behaviour — but it keeps the list an honest statement of what this
        dispatch is actually taking away, and it means the probe never spawns for
        a run that has no vendor credential to decide about.

        This is called by :func:`base.build_child_env`, the one builder both
        lanes go through, so Lane A and Lane B consume the same verdict and a
        decline re-admits the same names on both — and it is called with **that
        dispatch's** context. Both parameters are load-bearing here, which is why
        this override declares them:

        * ``anchor`` is what the two policy reads resolve against. Without it a
          dispatch anchored on one project evaluates
          `providers.claude-code.strip_vendor_keys` / `vendor_backend` against
          the process-wide run anchor or the CWD — a different
          `.multi-llm/providers.yaml`, and therefore a credential decision the
          requested project never made.
        * ``base_env`` is the environment the child will actually inherit, so
          "present" means present *there*. It also scopes the probe: the
          sanitized preflight is run against the same env, so its verdict is
          about the credential this dispatch would really hand over.

        ``None`` for either keeps the process defaults (the run anchor's config,
        ``os.environ``), which is what a context-free call means.
        """
        names: List[str] = ["CLAUDECODE"]
        source: Mapping[str, str] = os.environ if base_env is None else base_env

        backend_present = [n for n in _VENDOR_BACKEND_ENV if n in source]
        if backend_present:
            names.extend(
                _stripped_vendor_backends(
                    backend_present,
                    vendor_backend_policy(self.name, anchor),
                    declared_env_names(self.name, _VENDOR_BACKEND_ENV, anchor),
                )
            )

        credentials = [n for n in _CREDENTIAL_ENV if n in source]
        if not credentials:
            # Nothing to decide, so nothing is probed. A run with no vendor
            # credential in its environment spawns no `claude auth status` at
            # all — the tighter half of "never at import, never per slot".
            return names

        policy = strip_vendor_keys_policy(self.name, anchor)
        if policy == STRIP_VENDOR_KEYS_ALWAYS:
            names.extend(credentials)
            return names
        if policy == STRIP_VENDOR_KEYS_NEVER:
            self._warn_credential_decline(
                credentials, "providers.claude-code.strip_vendor_keys is 'never'"
            )
            return names

        verdict, reason = _subscription_verdict(_CREDENTIAL_ENV, base_env=base_env)
        if verdict == STRIP_VERDICT_STRIP:
            names.extend(credentials)
            return names
        self._warn_credential_decline(credentials, reason)
        return names

    def _warn_credential_decline(self, present: Sequence[str], reason: str) -> None:
        """One line per process naming the billing consequence of a decline.

        The gate fails **open** — the API-key path is preserved byte-for-byte —
        and this is the only trace that says so, so it names the variable, the
        reason and the cost. Emitted once per distinct reason per process, and
        only when a vendor credential is really present: with none set there is
        no billing consequence to warn about.
        """
        _warn_policy_once(
            f"claude-code:strip-declined:{reason}",
            f"multi-llm: keeping {', '.join(present)} for claude-code "
            f"({reason}). This run may be billed per token instead of using a "
            f"subscription; set providers.claude-code.strip_vendor_keys: always "
            f"to strip it anyway.",
        )

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """The envelope's ``api_error_status``, then the shared text ladder.

        A rung **ahead of** the ladder rather than a replacement for it, and the
        narrowing shape is aider's (``aider.py``'s ``classify_failure``): the
        adapter supplies what only it can read and ``classify_streams`` keeps
        the rule. The map is
        :func:`result_envelope.category_for_api_error_status`, one copy for the
        two adapters that emit this envelope, and its table is measured off the
        rows in ``tests/fixtures/claude-code/manifest.yaml``.

        **Absent, ``null``, or a status the map declines to name (400) delegates
        to ``super()``**, which is every route the ladder had before: the
        launch-failure tuple, context overflow, this adapter's own widened auth
        set, rate limits, and the marker tables. A run that never launched
        prints no envelope at all, so this rung cannot mask the exit-127 verdict
        or a spawn failure — it fires only where the CLI itself answered.

        What it buys is independence from wording. The ladder reads sentences a
        vendor may reword at any release; ``api_error_status`` is the same
        integer the HTTP response carried. On the committed rows the two routes
        agree wherever both speak (pinned by
        ``tests/test_result_envelope_verdicts.py``), and on ``invalid-model``
        the status is the *only* route: claude-code replaces the vendor's
        ``The model `X` does not exist`` with its own *"There's an issue with the
        selected model (X). It may not exist…"*, which no
        ``INVALID_MODEL_MARKERS`` entry matches at any ladder order.

        **A clean envelope's ``result`` is never scanned** (plan
        ``opencode-validator-false-rate-limit-and-denied-turn`` T3.2). When the
        CLI reports the run clean — ``is_error`` false, ``terminal_reason``
        completed, no ``api_error_status`` (:func:`result_envelope.
        is_clean_envelope`) — ``result`` is the model's own prose, and a
        validator that read a plan discussing rate limits or model names says
        so there. Handed to the ladder whole, that prose classified a green
        run ``rate_limited`` (a backoff for the batch) or ``invalid_model``
        (fatal to it). So the ladder runs over stderr and the exit code alone;
        the envelope's other fields are bookkeeping and ``permission_denials``,
        which quotes tool input, so none of stdout is kept. The audit that set
        this rule found no committed failure capture that needs the prose: all
        eight refusing rows carry ``is_error: true`` and the real 429
        (``rate-limit``) carries ``api_error_status: 429``, so every one of
        them still reaches the ladder or the status rung exactly as before.

        The exclusion itself lives in :meth:`vendor_text`, so the failure
        reason's quote (``subagent_executor._classify_failed_run``) is cut from
        the same reduced capture the verdict was decided on; the status rung
        above still reads the raw stdout.
        """
        category = classify_api_error_status(stdout)
        if category is not None:
            return category
        return super().classify_failure(stdout, stderr, exit_code)

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """``("", stderr)`` for a clean envelope; the capture unchanged otherwise.

        A clean envelope's ``result`` is the model's own prose (see
        :meth:`classify_failure`), and the rest of stdout is bookkeeping and
        ``permission_denials`` quoting tool input, so none of it is the
        vendor's verdict. Living here rather than inline in
        :meth:`classify_failure` is what keeps the verdict and its quote on one
        haystack: ``_classify_failed_run`` re-reduces through this hook to cut
        the quote, and an identity hook let it quote the prose the verdict
        excluded (plan T2.5). Any other stdout, including one that fails to
        parse, is returned unchanged, per the base contract; stderr is never
        reduced.
        """
        try:
            if is_clean_envelope(stdout):
                return "", stderr
        except Exception:  # noqa: BLE001 - a failed reduction returns its input
            pass
        return stdout, stderr

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """The refusing envelope's own line, tagged when it names a usage cap.

        This CLI puts the whole diagnosis on stdout (the class docstring: eleven
        measured outcomes, stderr 0 bytes on every one), and the envelope carries
        both the status and the vendor's sentence — yet with no override here a
        failed slot was recorded as the bare ``claude-code exited with code 1``.
        Measured 2026-09-17: ``claude-code:claude-fable-5-1:high`` ran 491 s,
        spent $25.05, hit the account's usage cap, and every artifact a human
        reads (``error_<model>.log``, ``.status.json``'s ``models_failed``, the
        ``Agent failed`` line) said only the exit code; the session model had to
        open the provider log to learn why.

        :func:`result_envelope.describe_refused_envelope` renders ``HTTP 429:
        <sentence>``; this method prepends :data:`USAGE_LIMIT_TAG` when the
        sentence matches :data:`USAGE_LIMIT_MARKERS`, because a usage cap and a
        busy endpoint share the status code and differ in every remedy.

        Diagnostics, never classification (the base hook's rule):
        :meth:`classify_failure` reads the same envelope for its own verdict and
        nothing here changes it. ``stderr`` is accepted for the signature and
        deliberately unread: it has been empty on every capture.
        """
        line = describe_refused_envelope(stdout)
        if line is None:
            return None
        lowered = line.lower()
        if any(marker.search(lowered) for marker in USAGE_LIMIT_MARKERS):
            return f"{USAGE_LIMIT_TAG} {line}"
        return line

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse Claude Code output and extract structured data.

        Claude Code with --output-format json returns responses wrapped in:
        {"type":"result","result":"...","session_id":"...","total_cost_usd":...}

        This method unwraps that format and attempts to parse the inner result
        as JSON, with fallback strategies for various response formats.

        **It reads the envelope's verdict too**, in the one shared place: an
        envelope carrying ``is_error: true`` or a non-``completed``
        ``terminal_reason`` is refused by :func:`parse_result_envelope` with the
        CLI's own sentence as the error, rather than having its ``result``
        served as the answer. See that function for the measured value table.

        Args:
            stdout: The standard output from Claude Code CLI.
            stderr: The standard error (unused but required by interface).

        Returns:
            A dictionary with 'success' and 'data' (or 'error') keys.
        """
        # One shared implementation (§9.5): cursor-agent emits the same envelope
        # and used to carry a byte-identical copy of the unwrapping.
        return parse_result_envelope(stdout)
