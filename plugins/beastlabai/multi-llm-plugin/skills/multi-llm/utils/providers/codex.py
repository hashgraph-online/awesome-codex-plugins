"""OpenAI Codex CLI provider implementation with NDJSON event stream parsing."""
import json
import os
import shutil
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from ..json_extractor import _loads_reply, extract_json_from_text
from .base import (
    PROFILE_AGENT_READONLY,
    PROFILE_AGENT_WRITE,
    PROFILE_GENERATE,
    SANDBOX_FALLBACK_AUTO,
    SANDBOX_FALLBACK_OFF,
    SANDBOX_FALLBACK_POLICIES,
    SANDBOX_CANARY_DENIED,
    SANDBOX_CANARY_NOT_DENIED,
    SANDBOX_FALLBACK_PROFILES,
    SANDBOX_WRITE_FALLBACK_PROFILES,
    SANDBOX_CONTAINMENT_INCIDENTAL,
    SANDBOX_RUNG_LANDLOCK,
    SANDBOX_RUNG_PLUGIN_LANDLOCK,
    SANDBOX_RUNG_UNSANDBOXED,
    WRITE_SCOPE_PLAN_FILE,
    WRITE_SCOPE_REPO_WIDE,
    WRITE_SCOPE_TASKS,
    WRITE_SCOPES_BY_CONSENT,
    WRITE_SCOPES_ON_RUNG,
    HOST_POSTURE_FULL_ACCESS,
    JailContext,
    WritePostureConsent,
    USAGE_FULL,
    REASONING_LADDER,
    InternalRetryEnvelope,
    LLMProvider,
    ReasoningLadder,
    SandboxRung,
    StructuredOutputUnavailable,
    StructuredSchema,
    _provider_block,
    _resolve_policy,
    canary_marker_shell_words,
    sandbox_rung_id,
    split_reasoning_effort,
)

# Reasoning effort values this adapter EMITS as `model_reasoning_effort`
# (verified live against codex-cli 0.144.0/0.146.0).
#
# `max` was missing until L11, and its absence was not inert: `gpt-5.6-sol:max`
# is a combination codex's own catalog advertises (`codex debug models` →
# `supported_reasoning_levels` lists `max` for gpt-5.6-sol/-terra/-luna), so a
# whitelist stopping at `xhigh` made `split_reasoning_effort` find no known
# suffix and pass `gpt-5.6-sol:max` through as the MODEL NAME — a model id that
# does not exist, with no effort set at all.
#
# `none`/`minimal` stay in the set because the CLI takes them on the wire, but
# no catalog entry advertises them: they may be passed through when a user asks
# for one, never chosen by a default or a rung-down.
#
# codex is the one adapter that takes the ladder whole — all seven rungs, under
# their canonical names — plus one inbound-only alias below.
EFFORT_LADDER = ReasoningLadder(
    provider="codex",
    rungs=REASONING_LADDER,
    # Inbound-only alias: accepted on a model spec, rewritten before argv is
    # built, and never emitted. codex takes `ultra` as an input alias and
    # normalizes it down to `max` client-side; the harness does that rewrite
    # itself so the emitted value is always a name this adapter states, and
    # codex's own normalization becomes an unused backstop rather than a
    # dependency. (Muse is the mirror case: it has no `max` and renders the same
    # pair in the opposite direction.)
    inbound_aliases=(("ultra", "max"),),
)
REASONING_EFFORTS = EFFORT_LADDER.accepted
EFFORT_ALIASES = EFFORT_LADDER.aliases

#: What a model spec may CARRY, as opposed to what argv may show.
_ACCEPTED_EFFORTS = EFFORT_LADDER.accepted_inbound

#: The codex sandbox policy each invocation profile runs under — the one place
#: in this adapter a `--sandbox` value is spelled (M5).
#:
#: Before this table the same three policies were stated three unconnected ways:
#: a literal inside `_BASE_ARGV` for `generate`, an *implicit* re-use of that
#: literal by `build_agent_command`'s `agent-write` leg (which simply returned
#: `build_command`), and a second literal in its `agent-readonly` leg's
#: positional rewrite. Nothing tied them together, so editing the `generate`
#: default silently edited BOTH agent profiles: agent-write inherits it and the
#: readonly rewrite degenerates into a no-op, which makes agent-write and
#: agent-readonly byte-identical while `supports_file_edits` stays `True` —
#: nothing refuses the dispatch, so every write batch would run, move zero bytes
#: and be recorded as a D3g "clean failure". Each profile now names its own
#: policy here, so a change to one row cannot travel to another.
#:
#: The values are codex's own documented sandbox policies (`codex exec --help`,
#: verified against codex-cli 0.146.0) rather than anything this repo enforces
#: after the fact, which is what makes `agent-readonly` a real denial mechanism
#: and `agent-write` a real (cwd-rooted) boundary rather than a bypass.
_SANDBOX_BY_PROFILE = {
    PROFILE_GENERATE: "workspace-write",
    PROFILE_AGENT_WRITE: "workspace-write",
    PROFILE_AGENT_READONLY: "read-only",
}

#: The one `--sandbox` value this adapter renders that is NOT a row of the table
#: above, and the only way it is ever rendered is `_apply_sandbox(...,
#: rung="unsandboxed")` — the last rung of the fallback ladder, a dispatch-time
#: override no default argv carries (D6, 2026-09-17; ladder 2026-09-22).
#:
#: The ladder, walked only after the D6 probe said `unavailable` (never
#: `unknown`) and only for the two read-only profiles in
#: `SANDBOX_FALLBACK_PROFILES`: rung 1 `landlock` (`LANDLOCK_RUNG` below —
#: `--sandbox read-only` + a per-dispatch `-c features.use_legacy_landlock=true`,
#: a real kernel boundary, taken only when its canary write is denied, reported
#: `[SANDBOX_FALLBACK]` / `sandbox: fallback-landlock`), then rung 2
#: `unsandboxed` (this value, no boundary, reported `[SANDBOX_BYPASSED]`).
#: `providers.codex.sandbox_fallback` gates every rung: `auto` (default) walks
#: both, `contained` takes rung 1 and refuses rather than reach rung 2, `off`
#: takes none and refuses — unchanged by the ladder. ⚠ Never enable landlock
#: globally (`codex features enable use_legacy_landlock`): every
#: `workspace-write` dispatch then panics, `agent-write` included — see
#: `LANDLOCK_FEATURE_FLAG`. Rung 1 is read-only only and deprecated upstream
#: (measured at 0.155.1; owner: whoever bumps the pinned codex version), so the
#: AppArmor repair `doctor` prints is still the real fix for `agent-write`,
#: which no rung serves.
#:
#: `danger-full-access` is codex's own third documented policy
#: (`codex exec --help`: `-s, --sandbox {read-only, workspace-write,
#: danger-full-access}`), chosen over `--dangerously-bypass-approvals-and-sandbox`
#: because approvals are already `never` in exec mode (see `build_command`) and
#: because it lands in the slot the positional rewrite already owns, so the
#: fallback is a value change and not a new flag. Measured on codex-cli 0.154.0
#: with the adapter's own probe shape: `codex sandbox -c 'sandbox_mode=
#: "read-only"' -- sh -c 'exit 0'` dies on `bwrap: loopback: Failed
#: RTM_NEWADDR: Operation not permitted` (rc 1); under `danger-full-access` the
#: same command runs (rc 0) with no bwrap started at all. `verified_version`
#: stays 0.146.0: 0.154.0 is where this one value was measured, and one
#: flag's measurement is not a re-verification of the whole adapter.
#:
#: What it costs, stated once here and again in every artifact of a slot that
#: ran under it: no OS boundary of any kind between the model's shell and this
#: machine — reads and writes anywhere the user can, and network from model
#: commands (workspace-write unshares it). `agent-readonly`'s "real denial
#: mechanism" does not exist under it; a prompt-injected validator could write.
#: That is exactly the footing cursor-agent, pi, claude-code and muse (always
#: `--disable-sandbox`) run the same read-only phases on, which is why `auto`
#: keeps it as the last rung rather than holding codex back until a machine
#: installs the AppArmor repair — codex is the one reviewer that insists on its
#: own sandbox, and a fan-out that dropped it for that reason alone was
#: measured (2026-09-17) to miss 2 unique validated-high issues. Still: only
#: when rung 1 is unusable, only under `auto`; `contained` and `off` never
#: render it.
SANDBOX_FALLBACK_VALUE = "danger-full-access"

#: Every codex slot starts without the user's installed plugins (2026-10-02,
#: codex 0.160.0, offline against a stub, throwaway CODEX_HOME holding a copy of
#: the multi-llm plugin install). A nested `codex exec` loads `$CODEX_HOME/plugins`
#: like the interactive session does, so each review slot booted multi-llm's own
#: `multi_llm` MCP server (a probe wrapper in the copied `.mcp.json` logged the
#: start) whose venv Python wrote `__pycache__/*.pyc` under the watched
#: `plugins/` tree: a `[CODEX_HOME_CHECK]` warning on every slot, on every host.
#: `-c features.plugins=false` stops it (0 starts, against 1 without it);
#: `-c plugins."<name>@<marketplace>".enabled=false` did not (still 1 start) and
#: would name the user's plugins anyway, and `--ignore-user-config` also drops
#: their model provider. A provider slot reads and reviews text; it needs none of
#: the user's plugins, skills or apps. Their user-defined `[mcp_servers.*]` are not
#: plugins and are untouched. A codex too old to know the key ignores an unknown
#: `features.*` key (see the legacy-landlock probe note below).
PLUGINS_OFF_PAIR = ("-c", "features.plugins=false")

#: The one `-c` key the landlock rung adds (2026-09-22). codex-cli 0.155.1 still
#: ships a second Linux sandbox backend, `[features] use_legacy_landlock`, which
#: needs no user namespace — so on a machine where bubblewrap cannot start it
#: starts, and it really contains: under `sandbox_mode="read-only"` every write
#: is denied by the kernel (inside and outside cwd, `/tmp` included) and the
#: model's shell has no network, while reads are unrestricted.
#:
#: ⚠ Only ever a **per-dispatch** `-c`, paired with `--sandbox read-only`.
#: Enabled globally (`codex features enable use_legacy_landlock`, i.e. written
#: into `~/.codex/config.toml`) it makes every `workspace-write` dispatch panic —
#: `permission profiles requiring direct runtime enforcement are incompatible
#: with --use-legacy-landlock`, exit 101 — `agent-write` included. Nothing here
#: ever writes a config file or runs `codex features`; the `-c` lives and dies
#: with the one process it is on.
#:
#: Deliberately **not** in `flags_verified_at_floor`: it was measured on 0.155.1
#: alone, not at `min_version`. The rung is gated by its probe at run time
#: instead, so a build that lacks (or has dropped) the feature falls through to
#: the next rung by probe failure.
LANDLOCK_FEATURE_FLAG = "features.use_legacy_landlock"
LANDLOCK_FEATURE_PAIR = ("-c", f"{LANDLOCK_FEATURE_FLAG}=true")

#: The containment canary the landlock rung's probe runs. Exit 0 proves only
#: that a process started — a deprecated flag that is accepted and then fails
#: open passes `sh -c 'exit 0'` while reporting a boundary that is not there —
#: so the canary attempts the same `.multi-llm/tmp` write the profile probe
#: uses and inverts the convention: a **denied** write (no file afterwards) is
#: its exit 0, **and** it prints `SANDBOX_CANARY_DENIED` on stdout — the walk
#: takes the rung only on exit 0 *with* that marker, so a CLI that prints usage
#: and exits 0 without running the canary is not read as containment. The
#: marker is spelled split in the script's source
#: (`canary_marker_shell_words`), so a CLI echoing its argv cannot forge it. A
#: write that lands is removed again and reported as exit 3 with
#: `SANDBOX_CANARY_NOT_DENIED` on stderr, which the walk reads as a rejected
#: rung. The write runs in a subshell because a redirection failure on a
#: special builtin (`:`) exits a POSIX `sh` outright — measured: dash died on
#: the denied redirect with exit 2 before the verdict line ran.
#:
#: Only the **write** may count as the denial. A failed `mkdir` (the sandbox
#: refusing to create the directory, or a non-directory already at
#: `.multi-llm/tmp`) is a setup failure, not containment: the canary then exits
#: `LANDLOCK_CANARY_SETUP_EXIT` with `LANDLOCK_CANARY_SETUP_FAILED` on stderr
#: and no marker, which the walk never takes. The directory is created — and
#: proven writable — *outside* the sandbox by the walk before the probe runs
#: (`LANDLOCK_RUNG.probe_workdir`), so under a working boundary the `mkdir -p`
#: here is a no-op on an existing directory and a denied write can only be the
#: boundary's, never ordinary filesystem permissions. The canary removes only
#: the directories its own `mkdir -p` created (checked before it runs), so a
#: fail-open probe never deletes a pre-existing — e.g. the walk's — `.multi-llm`
#: or `.multi-llm/tmp`; what the walk created, the walk removes.
LANDLOCK_CANARY_WORKDIR = ".multi-llm/tmp"
LANDLOCK_CANARY_SETUP_EXIT = 4
LANDLOCK_CANARY_SETUP_FAILED = (
    "multi-llm sandbox canary: setup failed (no writable .multi-llm/tmp directory)"
)
LANDLOCK_CANARY_SCRIPT = (
    f'd={LANDLOCK_CANARY_WORKDIR}; f="$d/sandbox-canary-$$"; m=; t=; '
    '[ -e .multi-llm ] || [ -L .multi-llm ] || m=1; '
    '[ -e "$d" ] || [ -L "$d" ] || t=1; '
    'mkdir -p "$d" 2>/dev/null; '
    'if [ ! -d "$d" ]; then [ -n "$m" ] && rmdir .multi-llm 2>/dev/null; '
    f'echo "{LANDLOCK_CANARY_SETUP_FAILED}" >&2; '
    f'exit {LANDLOCK_CANARY_SETUP_EXIT}; fi; '
    'if (: > "$f") 2>/dev/null; '
    'then rm -f "$f"; rc=3; else rc=0; fi; '
    '[ -n "$t" ] && rmdir "$d" 2>/dev/null; '
    '[ -n "$m" ] && rmdir .multi-llm 2>/dev/null; '
    '[ -e "$f" ] && rc=3; '
    f'if [ "$rc" -eq 0 ]; then echo {canary_marker_shell_words(SANDBOX_CANARY_DENIED)}; '
    f'else echo "{SANDBOX_CANARY_NOT_DENIED}" >&2; fi; exit $rc'
)

#: The landlock rung's probe, pinned verbatim — never rebuilt from the
#: profile's probe (whose `generate` form *writes* a byte, so under read-only
#: landlock it would exit non-zero exactly when the rung works) nor from the
#: dispatch argv. It carries the feature in the **dispatch's own spelling**
#: (`-c features.use_legacy_landlock=true`, not `codex sandbox --enable
#: use_legacy_landlock`), so probe and dispatch exercise one mechanism.
#: Measured 2026-09-23, codex-cli 0.155.1, this repo's host (bwrap broken by
#: `apparmor_restrict_unprivileged_userns=1`): exit 0 in 0.03 s, canary write
#: denied, nothing left behind — with and without a pre-existing
#: `.multi-llm/tmp`; the `--enable` spelling gives the same answer; without the
#: flag the same argv dies on `bwrap: loopback: …` (exit 1); an unknown
#: `features.*` key is silently ignored and also dies on bwrap (so a build
#: without the feature reads `unavailable`, not a false pass); and under
#: `sandbox_mode="danger-full-access"` — the fail-open shape — the canary
#: reports the write not denied, exit 3.
LANDLOCK_PROBE_ARGV: Tuple[str, ...] = (
    "codex", "sandbox", *LANDLOCK_FEATURE_PAIR, "-c", 'sandbox_mode="read-only"',
    "--", "sh", "-c", LANDLOCK_CANARY_SCRIPT,
)

#: What codex 0.156.1 prints when rung 1's probe runs (measured 2026-09-24,
#: this repo's host, bwrap broken as above): exit 101, a panic at
#: `linux-sandbox/src/linux_run_main.rs:410` with this sentence. The legacy
#: landlock path now needs bubblewrap itself, so the rung is **measured
#: unavailable** from that build on a bwrap-less machine — which is the only
#: machine it ever served. Matched by text (whitespace-insensitive), never by
#: exit code: exit 101 is also constraint 2's panic below, a different cause.
LANDLOCK_NEEDS_BWRAP_PANIC = (
    "filesystem-restricted execution requires bubblewrap to isolate "
    "app-server sockets"
)

#: `removed_at`'s evidence sentence: a measurement on this configuration, not an
#: upstream changelog entry (none says "removed" yet).
LANDLOCK_REMOVED_EVIDENCE = (
    f"measured 2026-09-24: rung probe exits 101, {LANDLOCK_NEEDS_BWRAP_PANIC!r}"
)

#: What :meth:`CodexProvider.describe_failure` reports for that panic — its own
#: outcome, never the global-landlock mapping below nor a generic failure.
LANDLOCK_NEEDS_BWRAP_REASON = (
    "landlock rung requires bubblewrap in this codex build (measured from "
    "codex 0.156.1: the legacy landlock path panics with exit 101, "
    f"{LANDLOCK_NEEDS_BWRAP_PANIC!r}); the contained fallback rung is "
    "unavailable here, and `sandbox_fallback: auto` falls to "
    "--sandbox danger-full-access"
)


def is_landlock_needs_bwrap_panic(text: str) -> bool:
    """Whether ``text`` carries codex 0.156.1's rung-1 panic sentence."""
    return LANDLOCK_NEEDS_BWRAP_PANIC in " ".join((text or "").split())


#: Rung 1 — a real OS boundary on a bwrap-less machine. Serves the two
#: read-only profiles only, and always renders `--sandbox read-only` whatever
#: the profile's own row says (`generate` defaults to `workspace-write`, and
#: `workspace-write` + landlock is the exit-101 panic).
LANDLOCK_RUNG = SandboxRung(
    name=SANDBOX_RUNG_LANDLOCK,
    probe_argv=LANDLOCK_PROBE_ARGV,
    argv_rewrite=("--sandbox", "read-only", *LANDLOCK_FEATURE_PAIR),
    contained=True,
    deprecated_at=(
        "0.155.1",
        "`[features].use_legacy_landlock` is deprecated and will be removed soon.",
    ),
    removed_at=("0.156.1", LANDLOCK_REMOVED_EVIDENCE),
    probe_workdir=LANDLOCK_CANARY_WORKDIR,
    removed_signature=LANDLOCK_NEEDS_BWRAP_PANIC,
)

#: Rung 2 — today's D6 bypass, now the last rung rather than the first. No
#: probe: there is no boundary to ask about.
UNSANDBOXED_RUNG = SandboxRung(
    name=SANDBOX_RUNG_UNSANDBOXED,
    probe_argv=None,
    argv_rewrite=("--sandbox", SANDBOX_FALLBACK_VALUE),
    contained=False,
)

# ─────────────────────────────────────────────────────────────────────────────
# The plugin-landlock rung (plan codex-sandbox-unavailable-findings-and-fixes
# §6 F1, steps 2 and 3; 2026-09-30).
#
# When codex's own sandbox cannot start (bwrap blocked by
# `apparmor_restrict_unprivileged_userns=1`) and only then, the plugin launches
# codex through `utils/landlock_exec.py`: the wrapper applies a Landlock ruleset
# to itself and `exec`s codex under `--sandbox danger-full-access`. Codex runs
# none of its own sandbox code, and the kernel still refuses every write
# outside the allow-list, for codex and every process it spawns. Measured
# 2026-09-29 (preflight step 1, codex 0.158.0): codex starts and finishes a turn
# inside the jail, writes only beneath $CODEX_HOME (+ /dev/null, /dev/ptmx,
# /dev/pts), and `apply_patch` rewrites a file in place.
#
# Grade `incidental`, never `contained`: `systemd-run --user` wrote through the
# jail (Landlock does not mediate `connect()` to pathname Unix sockets), writes
# to $CODEX_HOME are allowed, `chmod`/`utimes` pass, and the network is not
# confined. So `sandbox_fallback: contained` never reaches it, and every
# artifact says it stops stray writes, not the model.
# ─────────────────────────────────────────────────────────────────────────────

#: The wrapper id the rung names (`SandboxRung.wrapper`); the path is resolved by
#: `utils/landlock_dispatch.WRAPPER_PATHS`, never from PATH or the cwd.
PLUGIN_LANDLOCK_WRAPPER = "landlock_exec"

#: The newest codex the rung's allow-list was measured against. Render-only:
#: `doctor` shows it beside the installed version, and a `[JAIL_DENIED]` line
#: names a newer installed codex as the likely cause. Raising it needs the
#: allow-list re-measurement (plan §8.2) to pass on the newer build.
PLUGIN_LANDLOCK_MEASURED_THROUGH: Tuple[str, str] = (
    "0.163.0",
    "measured 2026-09-29 on 0.158.0 (preflight step 1), re-measured "
    "2026-09-30 on 0.159.0 and 0.159.1 (step 1c), on 0.159.2 and on "
    "2026-10-08 on 0.161.0 (tests/test_codex_jail_rig.py, the promoted rig, "
    "all 12 rows): a read-only turn, a code-mode turn and a plan-file edit "
    "completed inside the jail; every write outside the allow-list denied; "
    "codex writes nothing new outside $CODEX_HOME. Re-measured 2026-10-22 "
    "on 0.163.0: all 12 promoted rig rows passed, including strace allow-list "
    "and positive controls, denied repo writes, in-place plan editing, "
    "repo-wide toolchain execution and seeded-home integrity; no grants widened",
)

#: The env names the rung's canary reads. The targets reach the script through
#: the env so the probe tail stays pinned text (plan F1 "Where it sits" item 3).
CANARY_ENV_SEEDED = "MULTI_LLM_CANARY_SEEDED"
CANARY_ENV_PYTHON = "MULTI_LLM_CANARY_PYTHON"
CANARY_ENV_WRITE_FILE = "MULTI_LLM_CANARY_WRITE_FILE"
CANARY_ENV_WRITE_DIR = "MULTI_LLM_CANARY_WRITE_DIR"
#: The canary's workdir — its negative targets' directory — when it is not
#: the cwd-relative `LANDLOCK_CANARY_WORKDIR` (root grant, 2026-10-05): a
#: `repo-wide` probe's root rule makes `.multi-llm/tmp` writable, so
#: `landlock_dispatch.rung_probe` prepares a directory OUTSIDE the repository
#: (under the parent's temp base, beside the slot `TMPDIR`) and hands it over
#: here; the script reads it ahead of the default. Unset for every other
#: probe, whose workdir the walk prepared inside the repository.
CANARY_ENV_WORKDIR = "MULTI_LLM_CANARY_WORKDIR"

#: What the rung's canary prints (stderr, exit 5) when a write it must be able
#: to make — in its own $TMPDIR, or a write profile's own target — failed: a
#: jail that denies everything is not a usable rung.
SANDBOX_CANARY_POSITIVE_FAILED = (
    "multi-llm sandbox canary: an allowed write failed"
)
PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT = 5

#: The truncation control's interpreter snippet: the path-based `truncate(2)`
#: (a shell `: >` redirect opens for writing, which WRITE_FILE refuses on every
#: ABI, so it cannot tell a jail that stops truncation from one that does not —
#: Appendix A). Exit 7 is a denial, 8 any other error (a setup failure, never a
#: pass), 0 a truncation that landed.
_TRUNCATE_SNIPPET = (
    "import os, sys\n"
    "try:\n"
    "    os.truncate(sys.argv[1], 0)\n"
    "except PermissionError:\n"
    "    sys.exit(7)\n"
    "except OSError:\n"
    "    sys.exit(8)\n"
)

#: The plugin-landlock rung's canary (run by `codex sandbox` under
#: `sandbox_mode="danger-full-access"`, inside the jail). Controls, in order:
#: negative — creating a file in the workdir (`.multi-llm/tmp`, prepared and
#: proven writable *outside* the jail by the walk, or the out-of-repository
#: directory `$MULTI_LLM_CANARY_WORKDIR` names for a repo-wide probe, whose
#: root rule makes the in-repo one writable — root grant, 2026-10-05) must be
#: denied; truncation — the seeded file (`$MULTI_LLM_CANARY_SEEDED`, in the
#: same negative target) must not be truncatable, and the parent compares its
#: bytes afterwards too; positive — a file created and removed in `$TMPDIR`,
#: and for the `plan-file` and `tasks` scopes the dispatch's own declared
#: target (`: >> <file>` opens the plan or tasks file for writing without
#: changing it; a tasks dir gets a file created and removed). A repo-wide
#: grant hands over no positive target: its `$TMPDIR` write is the control,
#: and nothing is created in the user's source tree
#: (`landlock_dispatch.canary_env` has the reasoning, 2026-10-02). Only when
#: every control holds does it print SANDBOX_CANARY_DENIED (split, so an
#: echoing CLI cannot forge it) and exit 0.
PLUGIN_LANDLOCK_CANARY_SCRIPT = (
    f'd="${{{CANARY_ENV_WORKDIR}:-{LANDLOCK_CANARY_WORKDIR}}}"; f="$d/sandbox-canary-$$"; '
    f'if [ ! -d "$d" ] || [ -z "${CANARY_ENV_SEEDED}" ] '
    f'|| [ -z "${CANARY_ENV_PYTHON}" ] || [ -z "$TMPDIR" ]; then '
    f'echo "{LANDLOCK_CANARY_SETUP_FAILED}" >&2; exit {LANDLOCK_CANARY_SETUP_EXIT}; fi; '
    'rc=0; '
    'if (: > "$f") 2>/dev/null; then rm -f "$f"; rc=3; fi; '
    '[ -e "$f" ] && rc=3; '
    f'"${CANARY_ENV_PYTHON}" -I -S -c \'{_TRUNCATE_SNIPPET}\' "${CANARY_ENV_SEEDED}" '
    '2>/dev/null; t=$?; '
    'if [ "$t" -eq 0 ]; then rc=3; '
    'elif [ "$t" -ne 7 ]; then '
    f'echo "{LANDLOCK_CANARY_SETUP_FAILED}" >&2; exit {LANDLOCK_CANARY_SETUP_EXIT}; fi; '
    f'if [ "$rc" -ne 0 ]; then echo "{SANDBOX_CANARY_NOT_DENIED}" >&2; exit 3; fi; '
    'p="$TMPDIR/sandbox-canary-ok-$$"; '
    f'if ! (: > "$p") 2>/dev/null || ! rm -f "$p"; then '
    f'echo "{SANDBOX_CANARY_POSITIVE_FAILED}" >&2; exit {PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT}; fi; '
    f'if [ -n "${CANARY_ENV_WRITE_FILE}" ] && ! (: >> "${CANARY_ENV_WRITE_FILE}") 2>/dev/null; then '
    f'echo "{SANDBOX_CANARY_POSITIVE_FAILED}" >&2; exit {PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT}; fi; '
    f'if [ -n "${CANARY_ENV_WRITE_DIR}" ]; then q="${CANARY_ENV_WRITE_DIR}/.multi-llm-canary-$$"; '
    f'if ! (: > "$q") 2>/dev/null || ! rm -f "$q"; then '
    f'echo "{SANDBOX_CANARY_POSITIVE_FAILED}" >&2; exit {PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT}; fi; fi; '
    f'echo {canary_marker_shell_words(SANDBOX_CANARY_DENIED)}; exit 0'
)

#: The rung's probe tail, pinned verbatim: codex itself, under the dispatch's own
#: `danger-full-access` value, running the canary. The wrapper prefix and the
#: allow-list belong to `landlock_dispatch.wrap_argv`, never to this tuple, so
#: the "pinned verbatim" rule still holds. Exercising codex (config load,
#: state-db init) rather than a bare `sh` is the point: a codex build that
#: writes a new path outside the allow-list at start-up fails the probe instead
#: of every dispatch. This shape ran on 0.158.0 as preflight step 0's fail-open
#: control (outside a jail: exit 3, "the write was not denied").
PLUGIN_LANDLOCK_PROBE_ARGV: Tuple[str, ...] = (
    "codex", "sandbox", "-c", f'sandbox_mode="{SANDBOX_FALLBACK_VALUE}"',
    "--", "sh", "-c", PLUGIN_LANDLOCK_CANARY_SCRIPT,
)

#: The plugin-landlock rung. `argv_rewrite` holds only the in-codex atoms; the
#: wrapper prefix is `landlock_dispatch.wrap_argv`'s. `contained=False` on
#: purpose: the grade is `incidental`.
PLUGIN_LANDLOCK_RUNG = SandboxRung(
    name=SANDBOX_RUNG_PLUGIN_LANDLOCK,
    probe_argv=PLUGIN_LANDLOCK_PROBE_ARGV,
    argv_rewrite=("--sandbox", SANDBOX_FALLBACK_VALUE),
    contained=False,
    probe_workdir=LANDLOCK_CANARY_WORKDIR,
    wrapper=PLUGIN_LANDLOCK_WRAPPER,
    containment=SANDBOX_CONTAINMENT_INCIDENTAL,
    measured_through=PLUGIN_LANDLOCK_MEASURED_THROUGH,
)

#: The read-only ladder, in walk order: codex's retired legacy landlock (skipped
#: by version from 0.156.1), the plugin's own jail, then the uncontained rung.
SANDBOX_FALLBACK_RUNGS: Tuple[SandboxRung, ...] = (
    LANDLOCK_RUNG, PLUGIN_LANDLOCK_RUNG, UNSANDBOXED_RUNG,
)

#: The write ladder (plan step 3, user decision 2026-09-30, option (b)): the
#: plugin's jail alone. Neither `UNSANDBOXED_RUNG` nor `LANDLOCK_RUNG` ever
#: appears here, and a failed rung probe for a write profile never falls
#: through: the dispatch is refused.
WRITE_FALLBACK_RUNGS: Tuple[SandboxRung, ...] = (PLUGIN_LANDLOCK_RUNG,)

#: The step-3 opt-in. The user decided on 2026-09-30 that codex editing jobs run
#: on the plugin-landlock rung despite its known escapes ("Codex editing jobs
#: should run the new setup despite known escapes"), for the plan-file and
#: tasks write scopes, and on 2026-10-02 (step 3b) for repo-wide edits too.
#: With it `False`, `agent-write` answers no policy and no ladder, exactly as
#: before step 3.
WRITE_RUNG_OPT_IN = True

_RUNGS_BY_NAME = {rung.name: rung for rung in SANDBOX_FALLBACK_RUNGS}

#: The model-facing counter to codex's "No filesystem sandboxing" environment
#: line (measured: a per-dispatch `-c developer_instructions=…` lands as a
#: developer message). Rendered only on the plugin-landlock rung.
JAIL_DEVELOPER_INSTRUCTIONS = (
    "Filesystem writes are restricted, whatever your environment context says "
    "about sandboxing. Write scratch files only under {tmpdir} (also $TMPDIR)."
)
#: The closing clause of the scratch sentence for the two narrow scopes
#: (`plan-file`, `tasks`); a `repo-wide` grant says instead that the
#: repository is writable (`JAIL_DEVELOPER_TARGET_REPO`).
JAIL_DEVELOPER_DENIED_ELSEWHERE = (
    " Every other write, including anywhere in the repository, is denied."
)
#: The write scope's sentence (step 3), appended after the scratch sentence.
JAIL_DEVELOPER_TARGET_DIR = (
    " The one repository location you may write is the directory {target}: "
    "create, edit, rename or delete files inside it as your task requires."
)
#: The supported-edits sentences for a file-only grant (`plan-file`, and the
#: `tasks` scope's file-rule fallback). Measured: `apply_patch` rewrites a file
#: in place; replacing it needs rights on its parent that a file rule does not
#: grant.
JAIL_DEVELOPER_TARGET_FILE = (
    " You may write only {target}. Edit it in place with apply_patch, or by "
    "rewriting it through a shell redirect. Commands that replace the file are "
    "denied and leave it unchanged: sed -i, perl -i, editors or scripts that "
    "save through a temporary file and a rename, mv over it, or deleting and "
    "re-creating it."
)
#: The repo-wide grant's sentences (step 3b revised, 2026-10-05, a user
#: decision): the whole repository is writable — one dir rule on its root —
#: and the hands-off set (`landlock_dispatch.REPO_WIDE_HANDS_OFF_NAMES`, the
#: run's output folder, the policy's denied paths) is an instruction, not a
#: rule: nothing is backed up around a batch, and a write there is what the
#: post-run sweep, `driver.write_paths` and the `[GIT_CONFIG_CHANGED]` line
#: report afterwards.
JAIL_DEVELOPER_TARGET_REPO = (
    " The whole repository {root} is writable: create, edit, rename or delete "
    "files anywhere under it as your task requires, including directly in its "
    "root; every write outside it is denied. Do NOT modify .git/ (no git add, "
    "commit, stash, checkout, restore, reset or fetch; no edits to .git/config "
    "or .git/hooks/), .codex/, .multi-llm/, this run's output folder "
    "{output_dir}, or any path driver.write_paths denies: the jail does not "
    "enforce this, and a change there fails the batch or is flagged afterwards."
)
#: Step 1b's decision (measured 2026-10-02 on codex 0.160.0), for `repo-wide`
#: only: the toolchain paths that stay denied, so the runner reads such an
#: EACCES as the jail's. uv's cache, pytest's cache, npm's cache and Python's
#: bytecode are redirected under $TMPDIR instead
#: (`landlock_dispatch.repo_wide_env_redirects`).
JAIL_DEVELOPER_DENIED_TOOLCHAIN = (
    " /tmp and /dev/shm are denied: put temporary files under $TMPDIR "
    "(tempfile already does). uv, pytest, npm and Python bytecode already use "
    "caches under $TMPDIR; any other tool's cache outside the repository is "
    "denied unless you point it under $TMPDIR."
)
#: Step 1c's decision (measured 2026-09-30 on codex 0.159.0/0.159.1): what stays
#: denied on the rung, named so the model reads such an EACCES as the jail's and
#: not the code's. `git status`'s index refresh, Python's `__pycache__` and
#: npm's cache are redirected instead (`landlock_dispatch.child_env_redirects`);
#: git commands that write `.git/` stay denied, and npm's own EACCES advice
#: ("sudo chown -R … ~/.npm") is wrong under the jail, hence the last sentence.
JAIL_DEVELOPER_DENIED_GIT = (
    " Git commands that write .git/ (add, commit, stash, checkout, restore, "
    "fetch) are denied."
)
JAIL_DEVELOPER_DENIED_PATHS = (
    " npm and npx use a per-dispatch cache under $TMPDIR. A "
    "Permission denied error here comes from this restriction, not from file "
    "ownership: never try sudo or chown to work around it."
)

#: The `-c` key the rung's developer message rides on.
DEVELOPER_INSTRUCTIONS_KEY = "developer_instructions"


def jail_developer_instructions(context: JailContext) -> str:
    """The rendered developer message for one jailed dispatch.

    The scratch sentence names this attempt's ``tmpdir``; a write scope adds its
    target: the dir sentence naming ``target_dir`` when the grant is a dir rule
    (the ``tasks`` scope in its default directory), else the supported-edits
    sentences naming the file (``plan-file``, and the ``tasks`` file-rule
    fallback). The lane decided ``target_dir``; nothing is guessed here.
    """
    text = JAIL_DEVELOPER_INSTRUCTIONS.format(tmpdir=context.tmpdir)
    repo_wide = context.write_scope == WRITE_SCOPE_REPO_WIDE
    if repo_wide:
        text += repo_wide_developer_sentences(context)
    else:
        text += JAIL_DEVELOPER_DENIED_ELSEWHERE
        if context.write_scope and context.target:
            if context.target_dir:
                text += JAIL_DEVELOPER_TARGET_DIR.format(target=context.target_dir)
            else:
                text += JAIL_DEVELOPER_TARGET_FILE.format(target=context.target)
        text += JAIL_DEVELOPER_DENIED_GIT
    text += JAIL_DEVELOPER_DENIED_PATHS
    if repo_wide:
        text += JAIL_DEVELOPER_DENIED_TOOLCHAIN
    return text


def repo_wide_developer_sentences(context: JailContext) -> str:
    """The ``repo-wide`` grant's sentences, naming the root the dir rule sits
    on and this run's output folder (root grant, 2026-10-05)."""
    try:
        from ..landlock_dispatch import repo_wide_root
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.landlock_dispatch import repo_wide_root  # type: ignore[no-redef]
    output_dir = context.output_dir or "(none)"
    return JAIL_DEVELOPER_TARGET_REPO.format(
        root=repo_wide_root(context.request), output_dir=output_dir,
    )


def _toml_basic_string(value: str) -> str:
    """``value`` as a TOML basic string for a ``-c key=<value>`` override, so a
    path with a space, a quote or a backslash survives codex's TOML parse."""
    escaped = (
        value.replace("\\", "\\\\").replace('"', '\\"')
        .replace("\n", "\\n").replace("\t", "\\t")
    )
    return f'"{escaped}"'

#: Constraint 2 of the landlock rung, as codex 0.155.1 reports it: a
#: `workspace-write` dispatch on a machine whose **own** codex config enables
#: `[features] use_legacy_landlock` panics (exit 101,
#: `linux-sandbox/src/linux_run_main.rs:392`) with this sentence. Matched
#: whitespace-insensitively because the panic message may wrap.
LANDLOCK_GLOBAL_PANIC = (
    "permission profiles requiring direct runtime enforcement are "
    "incompatible with --use-legacy-landlock"
)

#: What :meth:`CodexProvider.describe_failure` reports for that panic: the
#: cause named, instead of a Rust backtrace that names no config file.
LANDLOCK_GLOBAL_PANIC_REASON = (
    "codex panicked because `[features] use_legacy_landlock` is enabled in "
    "your own codex config ($CODEX_HOME/config.toml, else "
    "~/.codex/config.toml — e.g. by `codex features enable "
    "use_legacy_landlock`). multi-llm never sets it globally and cannot unset "
    "it per dispatch; every workspace-write dispatch (agent-write included) "
    "will keep panicking until that line is removed. `multi_llm.py doctor` "
    "names the file"
)


def is_landlock_global_panic(stderr: str) -> bool:
    """Whether a failed run's stderr carries constraint 2's panic sentence.

    stderr only: a Rust panic is written there, never into the ``--json``
    event stream on stdout, and :meth:`CodexProvider.describe_failure` reads
    the one channel it declares (``tests/test_providers.py``'s channel table).
    """
    return LANDLOCK_GLOBAL_PANIC in " ".join((stderr or "").split())


def sandbox_fallback_policy(anchor: Optional[str] = None) -> str:
    """Resolve ``providers.codex.sandbox_fallback`` (default ``auto``).

    Same shape as ``opencode.hermetic_policy``: read through the normal layering
    (base → ``<git-root>/.multi-llm/providers.yaml`` → ``MULTI_LLM_PROVIDERS_CONFIG``)
    via the shared ``_provider_block``, an unrecognised value warns once naming
    the key and falls back to the default. YAML 1.1 resolves a bare ``off`` /
    ``on`` (``no``/``yes``, ``false``/``true``) to a boolean, so a user who
    wrote either word gets what the word says — ``False`` is ``off``, ``True``
    is ``auto`` — rather than a warning about their YAML loader. Only ``off``
    narrows anything, so no spelling of "on" needs guarding: the key's whole
    job is to let a machine turn the default fallback *off*.
    """
    value = _provider_block("codex", anchor).get("sandbox_fallback")
    if isinstance(value, bool):
        return SANDBOX_FALLBACK_AUTO if value else SANDBOX_FALLBACK_OFF
    return _resolve_policy(
        value,
        SANDBOX_FALLBACK_POLICIES,
        SANDBOX_FALLBACK_AUTO,
        "providers.codex.sandbox_fallback",
    )


def _has_pair(cmd: List[str], pair: Tuple[str, str]) -> bool:
    """Whether ``cmd`` already carries ``pair`` as adjacent flag/value elements.

    The final element is the prompt (arbitrary text) and is never read as a
    value, so a prompt that happens to spell the value cannot suppress the
    insert.
    """
    flag, value = pair
    return any(
        cmd[i] == flag and cmd[i + 1] == value for i in range(len(cmd) - 2)
    )


def _sandbox_for(profile: str) -> str:
    """The `--sandbox` value codex runs ``profile`` under (M5).

    Unknown profiles do not reach here: :meth:`CodexProvider.build_agent_command`
    hands anything outside :attr:`~CodexProvider.agent_profiles` to the base
    class, which raises ``ProfileUnsupported`` naming the adapter and the
    declared set. The raise below is a structural backstop for a *future* call
    site rather than a reachable path — what it rules out is this function ever
    answering an unrecognised profile with a default sandbox.
    """
    try:
        return _SANDBOX_BY_PROFILE[profile]
    except (KeyError, TypeError):
        raise ValueError(
            f"codex has no sandbox policy for profile {profile!r} "
            f"(declared: {', '.join(_SANDBOX_BY_PROFILE)})"
        ) from None


#: The invariant head of every `codex exec` this adapter builds.
#:
#: `--ephemeral` and `--skip-git-repo-check` are emitted **unconditionally** —
#: no version gate, no floor raise (M2). Both were re-verified functionally, not
#: merely in help text, at the declared `min_version` 0.144.0 as well as at
#: 0.146.0, so there is no release in the supported range that would need gating
#: and a runtime probe would only add a failure mode. That claim is no longer
#: only prose: M14 turned it into the declaration
#: `CodexProvider.flags_verified_at_floor`, which the shared gate reads, so
#: "exempt" is a *checked* statement about these flags rather than a paragraph
#: beside them.
#:
#: * `--ephemeral` suppresses the rollout file every call otherwise writes into
#:   `$CODEX_HOME/sessions`. multi-llm never resumes one, and a four-model,
#:   ten-phase run leaves forty of them behind. Measured: three stub-backed runs
#:   in one git dir take the session count 1 → 2 (without) → 2 (with), with
#:   identical `agent_message` output — persistence is suppressed, the work is
#:   not.
#: * `--skip-git-repo-check` is misnamed by its own error text: the gate it
#:   opens announces itself as "Not inside a trusted directory and
#:   --skip-git-repo-check was not specified", i.e. it is codex's *trust* gate.
#:   Without it, codex outside a git repo exits 1 having made ZERO requests —
#:   while `--ask` is perfectly usable there. That contrast is the measured
#:   discriminator for this flag.
#:
#: Both are boolean, so neither may be the last element before the prompt: a
#: valueless flag in final position would take the prompt as its value, and
#: `build_command_for_transport`'s stdin leg (which drops `cmd[-1]`) would then
#: drop the wrong element. Keeping them inside this head makes that structural.
#:
#: The plugins-off pair sits before them for the same reason: a `-c` pair is never
#: the last element before the prompt either, and `--skip-git-repo-check` stays the
#: splice site the landlock rung's `-c` pair is measured against.
#:
#: The sandbox value is `_sandbox_for(PROFILE_GENERATE)` rather than a literal:
#: this head is what `build_command` — the `generate` path — renders, so this is
#: that profile's call site into `_SANDBOX_BY_PROFILE` (M5). `--sandbox` keeps
#: its fixed offset either way, which is what the agent legs' positional rewrite
#: relies on.
_BASE_ARGV = (
    "codex", "exec", "--sandbox", _sandbox_for(PROFILE_GENERATE), "--json",
    *PLUGINS_OFF_PAIR,
    "--ephemeral", "--skip-git-repo-check",
)

#: §4.2's contract asymmetry, encoded from day one: claude takes the schema
#: **inline**, codex takes a **file path**. No §5.4.1 probe — this is the
#: exemption, not an omission: `--output-schema <FILE>` is documented by
#: `codex exec --help` at the declared floor 0.144.0 and was re-verified
#: functionally, which is exactly §5.4.1's "verified at the adapter's declared
#: min_version" clause (the same reason `--ephemeral` carries none). It is
#: declared as such in `flags_verified_at_floor` below.
OUTPUT_SCHEMA_FLAG = "--output-schema"

# ─────────────────────────────────────────────────────────────────────────────
# §7.6(b) — the retry envelope, measured 2026-08-16.
#
# codex's two internal retry knobs are **config keys, not env vars**, and they
# compose multiplicatively: requests = (stream_max_retries + 1) ×
# (request_max_retries + 1) = 5 × 6 = 30. Both are **unreachable for the
# provider multi-llm uses** (§7.3): `-c request_max_retries=…` is an `unknown
# configuration field`, and `-c model_providers.openai.…` is refused with
# "model_providers contains reserved built-in provider IDs: `openai`. Built-in
# providers cannot be overridden." The env names both donor plans proposed
# (`OPENAI_MAX_RETRIES`, `OPENAI_TIMEOUT`) are absent from the binary and
# measurably inert — 30 requests in every configuration, with or without them.
#
# So this row is a declaration the harness cannot change, which is exactly why
# it has to be *declared*: codex stays on the harness-side ladder, and §7.5's
# arithmetic needs the number it cannot configure away.
# ─────────────────────────────────────────────────────────────────────────────

#: Defaults, verified against codex-cli 0.146.0. Named rather than inlined so
#: the 30 below is visibly the product and not a magic constant.
CODEX_STREAM_MAX_RETRIES = 4
CODEX_REQUEST_MAX_RETRIES = 5

# ─────────────────────────────────────────────────────────────────────────────
# Plan T3.1 — the classifier's haystack is what *codex* wrote.
#
# A codex subagent's stdout carries the repository back to us: every
# `command_execution` item holds the `aggregated_output` of the `rg`/`cat`/`sed`
# it ran over the plan and the tree, and `agent_message`/`reasoning` hold the
# model's prose about them. A plan that discusses rate limits or model names is
# then one grep away from a `rate_limited` or `invalid_model` verdict (the
# opencode run b38de8bb is the measured case of the same class). codex's own
# verdicts are never inside those items: the 401 and the 429 terminal arrive as
# top-level `error` / `turn.failed` events and on stderr (see
# `auth_error_patterns` / `rate_limit_patterns` below).
#
# Vocabulary: `tests/fixtures/codex/0.156.1/SCHEMA.md`. This is deliberately
# separate from `codex_stream_audit`, which audits the *commands* and must keep
# seeing every item; this reduction only narrows what `classify_failure` reads.
# ─────────────────────────────────────────────────────────────────────────────

#: `item.*` payload types whose text is the model's or the repository's, never
#: codex's own verdict. Everything else is kept: the nested `error` item (codex's
#: "Model metadata … not found" notice), `todo_list` (never captured — 0.156.1
#: does not advertise the plan tool, and an uncaptured shape is kept, the
#: conservative direction), and any item type a later codex adds.
_NON_VENDOR_ITEM_TYPES = frozenset({
    "command_execution",
    "agent_message",
    "reasoning",
    "file_change",
    "mcp_tool_call",
    "web_search",
    "collab_tool_call",
})

#: How far into a cut final line the end-cut rule looks for the two `type`
#: keys. A codex item line opens `{"type":"item.completed","item":{"id":"item_N",
#: "type":"command_execution"` — about 75 bytes; the window leaves room for a
#: long item id without reaching into `aggregated_output`.
_CUT_LINE_WINDOW = 128


def _is_non_vendor_item(event: Dict[str, Any]) -> bool:
    """Whether a parsed event is an ``item.*`` event of a dropped type."""
    if not str(event.get("type", "")).startswith("item."):
        return False
    item = event.get("item")
    return isinstance(item, dict) and item.get("type") in _NON_VENDOR_ITEM_TYPES


def _is_cut_non_vendor_item(line: str) -> bool:
    """A final line cut mid-event that opened as a dropped ``item.*`` event.

    A stream killed mid-write (the slot timeout) ends on a line that cannot be
    parsed, so this rule is textual by necessity. It is order-tolerant — it does
    not assume ``type`` is the first key — and needs both the ``item.`` event
    type and a dropped item type inside the window, so a cut ``error`` or
    ``turn.failed`` line is never dropped.
    """
    head = line[:_CUT_LINE_WINDOW].replace(" ", "")
    if '"type":"item.' not in head:
        return False
    return any(f'"type":"{kind}"' in head for kind in _NON_VENDOR_ITEM_TYPES)


def _vendor_stdout(stdout: str) -> str:
    """``stdout`` with the model's and the repository's items taken out.

    Whole lines are removed and nothing is re-rendered, so the result is always
    a subsequence of the input. A stream in which no line parses as JSON is not
    a codex event stream at all (a banner, a bare stderr-style sentence), so it
    comes back unchanged — the end-cut rule included.
    """
    lines = stdout.splitlines(keepends=True)
    kept: List[str] = []
    parsed_any = False
    last = len(lines) - 1
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            try:
                event = json.loads(stripped)
            except ValueError:
                if index == last and parsed_any \
                        and _is_cut_non_vendor_item(stripped):
                    continue
            else:
                parsed_any = True
                if isinstance(event, dict) and _is_non_vendor_item(event):
                    continue
        kept.append(line)
    return "".join(kept) if parsed_any else stdout


# ─────────────────────────────────────────────────────────────────────────────
# The answer walk, shared by `parse_output` and `salvage_text` (plan:
# review-run-scope-salvage-and-failure-visibility §4, D4.4). One walk so the
# text salvage recovers is, by construction, the text the parser reads as the
# answer — never the `command_execution` output or `reasoning` text around it.
# ─────────────────────────────────────────────────────────────────────────────

#: codex's top-level event types — the serde tag table of the 0.14x/0.156.1
#: binaries (`tests/fixtures/codex/0.156.1/SCHEMA.md`). A line carrying one of
#: them is what makes stdout a codex event stream rather than a bare answer.
_CODEX_EVENT_TYPES = frozenset({
    "thread.started",
    "turn.started",
    "turn.completed",
    "turn.failed",
    "item.started",
    "item.updated",
    "item.completed",
    "error",
})


class _CodexStream(NamedTuple):
    """What one pass over a ``codex exec --json`` stream collected."""

    #: ``agent_message`` texts from ``item.completed`` events, in stream order.
    messages: List[str]
    #: Text from the pre-0.14x ``text``/``message``/``content`` event shapes.
    legacy_parts: List[str]
    #: Top-level ``error`` and ``turn.failed`` messages (the fatal pair).
    fatal_errors: List[str]
    #: Nested ``item.type == "error"`` messages (often benign notices).
    item_errors: List[str]
    #: Whether any line was one of :data:`_CODEX_EVENT_TYPES`.
    saw_event: bool


def _scan_codex_stream(stdout: str) -> _CodexStream:
    """Walk the NDJSON once and collect the answer text and the error reports.

    The rules are ``parse_output``'s (see its docstring): only ``item.completed``
    counts, and only an ``agent_message`` item's ``text`` is the model's reply —
    a ``reasoning`` item carries a ``text`` field too.
    """
    messages: List[str] = []
    legacy_parts: List[str] = []
    fatal_errors: List[str] = []
    item_errors: List[str] = []
    saw_event = False

    for line in stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(event, dict):
            continue

        event_type = event.get("type", "")
        # `isinstance` first: an unhashable `type` would make the set lookup
        # raise, and this walk also serves `parse_output`, which never did.
        if isinstance(event_type, str) and event_type in _CODEX_EVENT_TYPES:
            saw_event = True

        if event_type == "item.completed":
            item = event.get("item")
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    messages.append(text)
            elif item_type == "error":
                # Not fatal on its own: codex emits these for benign
                # conditions such as unrecognised model metadata, on runs
                # that go on to succeed.
                message = item.get("message")
                if isinstance(message, str) and message:
                    item_errors.append(message)
        elif event_type == "error":
            message = event.get("message")
            if isinstance(message, str) and message:
                fatal_errors.append(message)
        elif event_type == "turn.failed":
            error = event.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str) and message:
                    fatal_errors.append(message)
        # Legacy event shapes, kept as a fallback for Codex builds that
        # predate the dotted-namespace stream. No 0.14x release emits these.
        elif event_type == "text":
            if isinstance(event.get("text"), str):
                legacy_parts.append(event["text"])
            part = event.get("part")
            if isinstance(part, dict) and part.get("type") == "text" \
                    and isinstance(part.get("text"), str):
                legacy_parts.append(part["text"])
        elif event_type == "message":
            if isinstance(event.get("content"), str):
                legacy_parts.append(event["content"])
        elif event_type == "content":
            if isinstance(event.get("text"), str):
                legacy_parts.append(event["text"])

    return _CodexStream(messages, legacy_parts, fatal_errors, item_errors, saw_event)


def _require_write_context(profile: str, context: Optional[JailContext]) -> None:
    """Raise unless ``context`` carries a write scope the rung serves and its
    target (plan step 3). A write dispatch with no grant is refused, never
    narrowed to the base entries or widened."""
    scope = getattr(context, "write_scope", None) if context is not None else None
    if context is None or not scope:
        raise ValueError(
            f"codex never runs the {profile!r} profile on "
            f"{SANDBOX_RUNG_PLUGIN_LANDLOCK!r} without a jail context carrying a "
            f"write scope (the grant is missing)"
        )
    if scope not in WRITE_SCOPES_ON_RUNG:
        raise ValueError(
            f"codex's {SANDBOX_RUNG_PLUGIN_LANDLOCK!r} rung does not serve the "
            f"{scope!r} write scope (served: {', '.join(WRITE_SCOPES_ON_RUNG)})"
        )
    if scope == WRITE_SCOPE_REPO_WIDE:
        # The grant is one dir rule on the repository root (step 3b, revised
        # 2026-10-05); it names no single target.
        return
    if not getattr(context, "target", None):
        raise ValueError(
            f"codex's {SANDBOX_RUNG_PLUGIN_LANDLOCK!r} rung needs the {scope!r} "
            f"scope's target (the grant names no path)"
        )


def _splice_developer_instructions(cmd: List[str], context: JailContext) -> None:
    """Splice ``-c developer_instructions=…`` right after
    ``--skip-git-repo-check`` (the landlock pair's measured site), once: an
    agent leg passes through ``_apply_sandbox`` twice, and the pair must not be
    rendered twice. ``--sandbox`` stays at index 2 and the prompt last."""
    value = (
        f"{DEVELOPER_INSTRUCTIONS_KEY}="
        f"{_toml_basic_string(jail_developer_instructions(context))}"
    )
    for i in range(len(cmd) - 2):
        if cmd[i] == "-c" and cmd[i + 1].startswith(f"{DEVELOPER_INSTRUCTIONS_KEY}="):
            cmd[i + 1] = value
            return
    splice = cmd.index("--skip-git-repo-check") + 1
    cmd[splice:splice] = ["-c", value]



#: The write probe's steps for Windows (`sandbox_probe_command`): the POSIX
#: script's mkdir, touch, remove and best-effort rmdir, run by python because
#: `sh` is not on a Windows PATH. Exit 0 when the file could be created, which
#: is the question; the remove is retried, because a scanner that opens a new
#: file for a moment makes an immediate remove a sharing violation, and a
#: write the sandbox allowed must not read as one it denied.
_WINDOWS_WRITE_PROBE = (
    "import os, sys, time\n"
    "d = '.multi-llm/tmp'\n"
    "f = d + '/sandbox-probe-%d' % os.getpid()\n"
    "try:\n"
    "    os.makedirs(d, exist_ok=True)\n"
    "    open(f, 'w').close()\n"
    "    rc = 0\n"
    "except OSError:\n"
    "    rc = 1\n"
    "for _ in range(20 if rc == 0 else 0):\n"
    "    try:\n"
    "        os.remove(f)\n"
    "        break\n"
    "    except FileNotFoundError:\n"
    "        break\n"
    "    except OSError:\n"
    "        time.sleep(0.05)\n"
    "for p in (d, '.multi-llm'):\n"
    "    try:\n"
    "        os.rmdir(p)\n"
    "    except OSError:\n"
    "        pass\n"
    "sys.exit(rc)\n"
)

class CodexProvider(LLMProvider):
    """Provider for OpenAI Codex CLI tool.

    Codex outputs NDJSON (newline-delimited JSON) events when using --json flag.
    Uses 'codex exec --sandbox workspace-write --json' for non-interactive
    execution. The sandbox mode must be passed explicitly: codex's no-flag
    default is trust-dependent (read-only in a repo the user has not marked
    trusted), and this skill runs codex in arbitrary repositories.

    Model strings support an optional ``model[:effort]`` suffix (e.g.
    ``gpt-5.5:high``), translated to ``-c model_reasoning_effort=<effort>``.
    Valid efforts are listed in REASONING_EFFORTS, plus the inbound-only
    aliases in EFFORT_ALIASES; anything else passes through verbatim as the
    model name.

    Every invocation also carries ``--ephemeral`` and ``--skip-git-repo-check``
    unconditionally — see ``_BASE_ARGV`` for what each one buys and why neither
    is version-gated.
    """

    # `codex exec` reads the prompt from stdin when no prompt argument is given
    # (`codex exec < prompt.txt`), so this adapter has a real non-argv transport
    # (D2d). The fan-out default stays "argv"; materialized prompts use stdin.
    supported_prompt_transports = ("argv", "stdin")

    # Subagent-runner declarations (D3e/D3j/D3m). `-s read-only` is one of the
    # three documented sandbox policies (`codex exec --help`, verified against
    # codex-cli 0.146.0), so the read-only profile is the CLI's own sandbox
    # rather than anything this repo enforces afterwards.
    agent_profiles = (PROFILE_GENERATE, PROFILE_AGENT_READONLY, PROFILE_AGENT_WRITE)
    supports_file_edits = True
    # D6 — the review fan-out asks codex for the array on stdout, never for a
    # file. `codex exec` writes through its own bubblewrap sandbox (`--sandbox
    # workspace-write`), and on a stock Ubuntu 24.04 with
    # `kernel.apparmor_restrict_unprivileged_userns=1` bwrap cannot start at
    # all (`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`).
    # Measured twice on `codex:gpt-6-astra:xhigh`, 2026-09-10: seven minutes of
    # review work each time, three `Failed to write file` attempts through the
    # file tool, and a final message carrying no JSON — with `--ephemeral`
    # keeping no rollout to salvage it from. The review only ever needed the
    # array as the final `agent_message`, which `parse_output` already returns
    # and `invoke_with_file_output` already reads (`source: stdout_fallback`);
    # `save_model_result` writes the same per-model file from it either way.
    # `supports_file_edits` stays True — the agent-write profile really edits,
    # and D6 step 3's sandbox probe is what gates it — and
    # `structured_output_transport` stays "file": that is the `--output-schema`
    # sidecar the CLI reads, not a file the model writes.
    #
    # None of this makes the fan-out sandbox-free. The child still READS the
    # plan through the same bwrap, so a sandbox that cannot start ends the slot
    # before the model has an input — which is why `sandbox_probe_command`
    # answers for the `generate` profile too.
    supports_file_output = False
    supports_workspace_reads = True
    # `--sandbox read-only` restricts writes, not reads: a snapshot outside the
    # repo root is readable with no extra flag (validation-context-by-path §2.2).
    reads_outside_cwd = True
    # MEASURED TRUE: an audited review stream of the 2026-09-25 run ran the
    # `command_execution` `pwd && rg --files …`, under `generate`'s
    # `--sandbox workspace-write` (`_SANDBOX_BY_PROFILE`) — the stream that
    # moved `pwd` into `codex_stream_audit.ANY_FLAG_VERBS` (plan:
    # review-run-scope-salvage-and-failure-visibility §7.3). Where bubblewrap
    # cannot start, the D6 fallback runs the same profile unsandboxed, which
    # keeps the shell. `generate_read_scope` stays the "cwd" default:
    # `reads_outside_cwd` above describes `agent-readonly`, not this profile.
    runs_shell_in_generate = True
    usage_support = USAGE_FULL
    # §4.2.2: this adapter really emits `--output-schema` when handed a
    # materialized schema (see `build_command`), so the caller may mark an
    # accepted result `native`.
    structured_output_support = True
    # …and it takes a PATH, not inline JSON — §4.2's contract asymmetry, stated
    # as data so the caller materializes the sidecar without knowing the name
    # "codex".
    structured_output_transport = "file"
    # `codex login status` prints the account it is logged in as, or "Not logged
    # in"; it generates nothing and contacts no model, which is what makes it
    # cheap enough for the once-per-run preflight probe (D3c). The credential
    # store it reads is ~/.codex/auth.json (or CODEX_API_KEY / OPENAI_API_KEY).
    auth_check = ("codex", "login", "status")
    login_cmd = "codex login"
    version_cmd = ("codex", "--version")
    # D6 — `codex exec --sandbox workspace-write` writes through bubblewrap, and
    # bubblewrap needs a user namespace a stock Ubuntu 24.04 denies it. Read by
    # `multi_llm.py doctor` to pick the bwrap self-test; the dispatch-time gate
    # is `sandbox_probe_command` below, which asks codex's own runner instead.
    sandbox_mechanism = "bubblewrap"
    # M14/§5.4 — the floor names the FEATURE, not a bare number: 0.144.0 is the
    # oldest build measured to emit the `item.completed`/`agent_message` JSONL
    # shape `parse_output` reads AND to accept the three flags below at the same
    # time. Both halves matter — a build that answers prompts but streams the
    # older event names produces a clean run this adapter cannot parse.
    min_version = "0.144.0"
    # No ceiling: no codex release has been measured to break this parser, and a
    # guessed `max_version_exclusive` would refuse runs nobody showed to be
    # broken. `verified_version` carries the "newer than the capture" *warning*,
    # which is the honest posture for an unmeasured future build. 0.156.1 since
    # the §6.2 recapture (2026-09-24): `tests/fixtures/codex/0.156.1/`, driven
    # offline against a localhost Responses stub, parsed by this adapter in
    # `tests/test_codex_stream_audit.py::TestTheCapturedFixtures`. 0.160.0 since
    # 2026-10-02: the same capture rig (`0.156.1/capture/`, offline, throwaway
    # CODEX_HOME) re-run on the installed 0.160.0 gave the same event kinds and
    # key shapes for the five scripted cases (`tests/fixtures/codex/0.160.0/`
    # keeps three), so the version-lag WARN every run printed was this pin
    # lagging the install. The `web_search_*` / `code_mode_*` fixtures are live
    # captures no stub can redo; they stay at 0.156.1. 0.160.1 since 2026-10-06
    # (run 6, #11b, the same WARN on every phase): the rig re-run on the
    # installed 0.160.1 gave byte-identical streams for the three kept cases
    # (thread ids aside) and the same event kinds and keys for
    # `writes_patches_sessions` and `exec_session` (`tests/fixtures/codex/0.160.1/`).
    # 0.161.0 since 2026-10-08 (run 10, #10, the same WARN): the same rig on the
    # installed 0.161.0 gave byte-identical streams for the three kept cases
    # (thread ids and the commit hash aside) and the same event kinds and keys
    # for all five scripted cases (`tests/fixtures/codex/0.161.0/`).
    # 0.163.0 since 2026-10-22: four offline recaptures (read_only_clean,
    # quoting_render, writes_patches_sessions, exec_session) retain the event
    # kinds and keys of 0.156.1. See tests/fixtures/codex/0.163.0/README.md;
    # collaboration, hosted tools and code mode were not re-measured.
    verified_version = "0.163.0"

    # M14/§5.4.1(a) — the exemption, as data. Each of these was re-verified
    # FUNCTIONALLY (not merely found in help text) at the declared floor above
    # as well as at 0.146.0, which is the one clause that lets a flag ship with
    # no runtime gate: there is no release in the supported range that would
    # need one, and a probe would only add a failure mode. See `_BASE_ARGV` for
    # what each one buys and how it was measured.
    flags_verified_at_floor = (
        "--ephemeral",
        "--skip-git-repo-check",
        OUTPUT_SCHEMA_FLAG,
    )

    # §7.2 — the per-adapter pattern overrides. Before this, *zero* adapters
    # extended the base English lists, including the four with structured error
    # events; codex's own failure text is one of the ones the base list misses.
    #
    # Both tuples EXTEND the base set rather than replacing it: the base entries
    # are audited-clean and shared, and dropping them here would quietly make
    # this adapter blinder than the default it started from.
    #
    # Measured against codex-cli 0.146.0 on 2026-08-16 with an invalid
    # OPENAI_API_KEY: the run ends on a `turn.failed` record whose
    # `error.message` reads `unexpected status 401 Unauthorized: Missing …
    # authentication in header, url: https://api.openai.com/v1/responses`.
    # "unauthorized" alone would have matched, but only because that same
    # sentence happens to carry "status" inside the context window — these two
    # phrases pin the shape itself. (The message's middle names the two HTTP
    # auth schemes; it is quoted only in prose here, because spelling it in
    # source trips `write_safety`'s own credential-shaped-token diagnostic.)
    auth_error_patterns = LLMProvider.auth_error_patterns + (
        "unexpected status 401",
        "authentication in header",
    )

    # §7.2's measured note: codex never retries a 429 internally — one request,
    # then this exact terminal. It carries no word the base list recognises
    # ("429" is there, but this is the sentence a user sees and the one §7.5
    # rule 6(b) reasons about), so the adapter declares it.
    rate_limit_patterns = LLMProvider.rate_limit_patterns + (
        "exceeded retry limit, last status: 429",
    )

    # A stderr line that is deliberately NOT a verdict, recorded rather than
    # fixed (plans/ask-answer-recovery-and-false-success.md T5.2):
    #   ERROR codex_core::tools::router: error=collab spawn failed: no thread with id: <uuid>
    # A `spawn_agent` (collab) sub-agent spawn failed inside the slot. Seen once
    # on the 2026-09-26 ask run whose 734 s codex answer was discarded, and
    # twice on the 2026-09-28 re-run of that question, where the slot still
    # ended `done`. Observed, non-fatal, and not the cause of the discard (the
    # `pwd` audit false alarm and aider's tag cache were: T5.1, T4.3). It
    # matches none of the patterns above, so `classify_failure` gives it no
    # verdict. Watch for recurrence; if it recurs, open a task.

    # §7.6(b). A constant, not a property: nothing about this envelope moves with
    # the resolved slot timeout — codex takes no timeout flag and this adapter
    # sets no env at all, so `configurable_by` is empty *from the harness's side*
    # (see the module comment for the two config keys and why they are
    # unreachable). `retries_rate_limit=False` is the measured negative: one
    # request, then `exceeded retry limit, last status: 429 Too Many Requests` —
    # so the harness's own backoff is the only one a 429 gets here, and §7.5 rule
    # 6(b) must NOT suppress it for this adapter. The ~25 s wall is what 30
    # requests really cost on 5xx/stream failures inside the one awaited
    # subprocess.
    internal_retries = InternalRetryEnvelope(
        max_requests=(CODEX_STREAM_MAX_RETRIES + 1) * (CODEX_REQUEST_MAX_RETRIES + 1),
        max_wall_s=25.0,
        retries_rate_limit=False,
        configurable_by=(),
    )

    @property
    def name(self) -> str:
        return "codex"

    @property
    def default_timeout(self) -> int:
        return 600

    def is_available(self) -> bool:
        return shutil.which("codex") is not None

    @staticmethod
    def _schema_argv(schema: Optional[StructuredSchema]) -> List[str]:
        """``[--output-schema, <path>]`` for a materialized schema, or ``[]``.

        **The file is the caller's, and its absence fails before spawn** (§4.2.1,
        sixth acceptance case). Adapters are module-level singletons shared
        across a concurrent fan-out, so this one cannot write a per-run temp file
        without becoming a data race — ``utils.structured_output.schema_sidecar``
        is the writer, and it removes the directory in a ``finally``.

        Raising here rather than dropping the flag is deliberate and is the
        opposite posture from §5.4.1's *optional-flag* gate, for the reason that
        gate states: a gate declines toward the status quo when the **CLI** may
        not understand a flag, whereas this is our own caller failing to produce
        a file it said it would. Silently dropping it would run the phase
        unvalidated while the caller recorded `native`.
        """
        if schema is None:
            return []
        if not schema.path:
            raise StructuredOutputUnavailable(
                f"codex takes {OUTPUT_SCHEMA_FLAG} as a FILE, but {schema.name} "
                f"was handed over with no materialized path. Wrap the dispatch "
                f"in utils.structured_output.schema_sidecar(). Nothing was "
                f"dispatched.",
                provider="codex",
                schema=schema.name,
            )
        if not os.path.isfile(schema.path):
            raise StructuredOutputUnavailable(
                f"codex's {OUTPUT_SCHEMA_FLAG} file for {schema.name} is not "
                f"readable at {schema.path}. Nothing was dispatched.",
                provider="codex",
                schema=schema.name,
            )
        return [OUTPUT_SCHEMA_FLAG, schema.path]

    def sandbox_probe_command(self, profile: str) -> Optional[List[str]]:
        """codex's own runner, asked to start where a dispatch would (D6).

        ``codex sandbox -c 'sandbox_mode="<policy>"' -- <cmd>`` runs ``<cmd>``
        under exactly the bubblewrap policy ``codex exec --sandbox <policy>``
        would use, with no model and no prompt — ~30 ms measured, and on a
        stock Ubuntu 24.04 it dies on ``bwrap: loopback: Failed RTM_NEWADDR:
        Operation not permitted`` before the shell starts.

        **Every** profile this adapter declares answers, because every one of
        them is bubblewrap. The two ``workspace-write`` profiles —
        ``agent-write`` and ``generate``, the review fan-out's — write and
        delete one byte under ``.multi-llm/tmp`` of the current directory (the
        executor and the fan-out both run this with ``cwd`` at the repo root),
        and the shell leaves nothing behind it created. ``generate`` used to
        return ``None`` on the premise that "the review fan-out stopped needing
        the sandbox when ``supports_file_output`` went ``False``". That premise
        is wrong: the fan-out stopped needing the sandbox to *write*, and a
        bwrap that cannot start denies the child every file operation —
        including the READ of the plan file, which is the whole input to the
        phase. Measured 2026-09-16, `codex:gpt-5.6-terra` on a review-plan
        fan-out: 27.9 s, 61k input tokens, and a one-item "review" whose only
        suggestion was that the plan file could not be read — scored a success,
        because nothing had asked the sandbox whether it could start.

        ``agent-readonly`` runs the same probe with **no** write in it: an
        empty command under ``sandbox_mode="read-only"``, which is enough,
        because what fails on this machine is bwrap *starting* and nothing
        inside the sandbox gets to run at all. It used to answer ``None`` on
        the premise that "this probe writes a byte, and a read-only dispatch is
        never asked to" — true of the byte, irrelevant to the failure: every
        read kind (validation, revalidation, consolidation, salvage, task
        generation, the human-decision judge) dispatched codex unprobed, and
        the bwrap failure then surfaces inside the model's own tool results
        rather than on the stream, so the D3k classifier never sees ``bwrap:``
        and the JSON the model still returns is scored a valid batch — the same
        "the file could not be read" shape the ``generate`` row above fixed.

        The policy comes from ``_SANDBOX_BY_PROFILE`` so the probe cannot answer
        for a policy the dispatch does not use (M5).
        """
        try:
            policy = _sandbox_for(profile)
        except ValueError:
            return None
        readonly = profile == PROFILE_AGENT_READONLY
        if os.name == "nt":
            # Windows has no `sh` on PATH as a rule (Git for Windows puts only
            # Git\cmd there), and a probe whose command cannot start reads as a
            # sandbox that cannot: every codex dispatch refused before codex was
            # asked. So the command is the plugin's own interpreter taking the
            # same steps. Unmeasured on Windows: whether `codex sandbox` starts
            # there is the question the probe asks, not one this answers.
            return [
                "codex", "sandbox", "-c", f'sandbox_mode="{policy}"',
                "--", sys.executable, "-I", "-c",
                "pass" if readonly else _WINDOWS_WRITE_PROBE,
            ]
        if readonly:
            # Nothing to clean up, so nothing to clean up *as*: the question is
            # only whether the sandbox comes up.
            script = "exit 0"
        else:
            script = (
                'd=.multi-llm/tmp; f="$d/sandbox-probe-$$"; '
                'mkdir -p "$d" && : > "$f" && rm -f "$f"; rc=$?; '
                'rmdir "$d" .multi-llm 2>/dev/null; exit $rc'
            )
        return [
            "codex", "sandbox", "-c", f'sandbox_mode="{policy}"',
            "--", "sh", "-c", script,
        ]

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        # --sandbox workspace-write, not the older --full-auto: 0.146.0 keeps
        # --full-auto only as a hidden compatibility trap (internally
        # `removed_full_auto`) and warns on every run. The two produce an
        # identical effective policy — approval_policy is forced to "never"
        # in exec mode regardless — so this is a rename, not a permission
        # change.
        #
        # §4.2.2's splice point: the schema pair goes in the same policy region
        # as claude's, immediately after `_BASE_ARGV` and ahead of `--model`, so
        # it is never the last pair before the prompt and
        # `build_command_for_transport`'s stdin leg (which drops `cmd[-1]`) can
        # never drop half of it. `--sandbox` keeps its fixed offset inside
        # `_BASE_ARGV`, which is what `build_agent_command`'s positional rewrite
        # relies on.
        schema_argv = self._schema_argv(schema)
        base_model, effort = split_reasoning_effort(model, _ACCEPTED_EFFORTS)
        if effort is not None:
            return [
                *_BASE_ARGV,
                *schema_argv,
                "--model", base_model,
                "-c", f"model_reasoning_effort={EFFORT_ALIASES.get(effort, effort)}",
                prompt,
            ]
        return [*_BASE_ARGV, *schema_argv, "--model", model, prompt]

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
        jail_context: Optional[JailContext] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """Deliver the prompt on argv or on stdin (prompt omitted from argv).

        ``sandbox_fallback`` — the selected rung id — is applied on the stdin leg
        here and on the argv leg by the base class — both through
        :meth:`apply_sandbox_fallback` with that rung, and both **before** the
        prompt is dropped, so the positional rewrite (and the landlock rung's
        insert) sees the argv exactly as :meth:`build_command` laid it out.
        """
        if transport != "stdin":
            return super().build_command_for_transport(
                prompt, model, transport, prompt_file, timeout_s=timeout_s,
                schema=schema, sandbox_fallback=sandbox_fallback,
                jail_context=jail_context,
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        rung = sandbox_rung_id(sandbox_fallback)
        if rung:
            cmd = self.apply_sandbox_fallback(
                cmd, PROFILE_GENERATE, rung, context=jail_context,
            )
        return cmd[:-1], prompt

    def sandbox_fallback_policy(
        self, profile: str, anchor: Optional[str] = None
    ) -> Optional[str]:
        """``providers.codex.sandbox_fallback`` for a profile that has a ladder; else ``None``.

        The profile gate is answered *here*, in the adapter, and not only at
        the call sites. The two read-only profiles return the resolved policy
        (``auto`` by default), which the gates then match against the rung the
        walk selected. ``agent-write`` (plan step 3, user decision 2026-09-30)
        returns the resolved policy only while :data:`WRITE_RUNG_OPT_IN` is in
        force, and the gates read it through ``write_rung_allowed``: the
        plugin-landlock rung under ``auto`` alone — never ``contained``, never
        ``off``, never another rung. Without the opt-in it is ``None`` whatever
        the config says.
        """
        if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
            return sandbox_fallback_policy(anchor) if WRITE_RUNG_OPT_IN else None
        if profile not in SANDBOX_FALLBACK_PROFILES:
            return None
        return sandbox_fallback_policy(anchor)

    def sandbox_fallback_rungs(self, profile: str) -> Tuple[SandboxRung, ...]:
        """The read-only ladder ``(landlock, plugin-landlock, unsandboxed)``,
        the write ladder ``(plugin-landlock,)`` while the step-3 opt-in is in
        force, and ``()`` otherwise.

        The write ladder never holds the uncontained rung or the legacy landlock
        rung (which panics under ``workspace-write`` anyway), and a failed
        plugin-landlock probe for a write profile never falls through.
        """
        if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
            return WRITE_FALLBACK_RUNGS if WRITE_RUNG_OPT_IN else ()
        if profile not in SANDBOX_FALLBACK_PROFILES:
            return ()
        return SANDBOX_FALLBACK_RUNGS

    def apply_sandbox_fallback(
        self,
        argv: List[str],
        profile: str,
        rung: Optional[str] = None,
        context: Optional[JailContext] = None,
        consent: Optional[WritePostureConsent] = None,
    ) -> List[str]:
        """Render fallback ``rung`` onto ``argv`` (D6 override, landlock rung,
        plugin-landlock rung).

        ``landlock`` writes ``read-only`` into the ``--sandbox`` slot and adds
        ``-c features.use_legacy_landlock=true`` once; ``unsandboxed`` writes
        ``danger-full-access``; ``plugin-landlock`` writes
        ``danger-full-access`` and splices ``-c developer_instructions=…`` for
        this attempt's ``context`` — the wrapper prefix that makes it a jail is
        added after executable resolution by ``landlock_dispatch.wrap_argv``,
        never here. Structural, not policy:

        * a read-only profile takes any declared rung; ``plugin-landlock``
          needs a ``context`` (raises without one, never renders the bare
          atoms);
        * ``agent-write`` takes ``plugin-landlock`` alone, and only with a
          ``context`` whose ``write_scope`` the rung serves and which names its
          target — every other rung (``None``, ``landlock``, ``unsandboxed``,
          an unknown id) raises the same ``ValueError`` as before step 3;
        * any other profile, a missing or an unknown rung raises.

        F5 (plan step 6, user decision 2026-09-30) adds one route: ``agent-write``
        on ``unsandboxed`` renders only with a ``consent`` whose posture is
        ``danger-full-access`` — the chat's own full-access mode, exported per
        call — and whose ``write_scope`` is a step-3 scope
        (:data:`WRITE_SCOPES_BY_CONSENT`: ``repo-wide``, or no scope at all,
        raises here whatever the gates decided — step 3b put repo-wide edits
        on the jail, never on the uncontained rung), and the gates hand it
        over only after the plugin-landlock rung could not take the dispatch.
        """
        if (
            profile in SANDBOX_WRITE_FALLBACK_PROFILES
            and rung == SANDBOX_RUNG_UNSANDBOXED
            and consent is not None
        ):
            if consent.posture != HOST_POSTURE_FULL_ACCESS:
                raise ValueError(
                    f"codex runs the {profile!r} profile unsandboxed only with "
                    f"the chat's {HOST_POSTURE_FULL_ACCESS!r} posture (got "
                    f"{consent.posture!r})"
                )
            scope = getattr(consent, "write_scope", None)
            if scope not in WRITE_SCOPES_BY_CONSENT:
                raise ValueError(
                    f"codex runs the {profile!r} profile unsandboxed under the "
                    f"chat's {HOST_POSTURE_FULL_ACCESS!r} posture only for the "
                    f"write scopes F5 covers "
                    f"({', '.join(WRITE_SCOPES_BY_CONSENT)}; repo-wide edits "
                    f"run on the {SANDBOX_RUNG_PLUGIN_LANDLOCK!r} rung alone); "
                    f"got {scope!r}"
                )
            cmd = argv
            cmd[cmd.index("--sandbox") + 1] = SANDBOX_FALLBACK_VALUE
            return cmd
        if profile in SANDBOX_WRITE_FALLBACK_PROFILES and WRITE_RUNG_OPT_IN:
            if rung != SANDBOX_RUNG_PLUGIN_LANDLOCK:
                raise ValueError(
                    f"codex never runs the {profile!r} profile on sandbox "
                    f"fallback rung {rung!r}: the only rung a write profile may "
                    f"take is {SANDBOX_RUNG_PLUGIN_LANDLOCK!r} (the plugin's "
                    f"Landlock jail)"
                )
            _require_write_context(profile, context)
            return self._apply_sandbox(argv, profile, rung=rung, context=context)
        if profile not in SANDBOX_FALLBACK_PROFILES:
            raise ValueError(
                f"codex never runs the {profile!r} profile on a sandbox "
                f"fallback (the fallback covers: "
                f"{', '.join(SANDBOX_FALLBACK_PROFILES)})"
            )
        if rung not in _RUNGS_BY_NAME:
            raise ValueError(
                f"codex has no sandbox fallback rung {rung!r} (declared: "
                f"{', '.join(_RUNGS_BY_NAME)})"
            )
        return self._apply_sandbox(argv, profile, rung=rung, context=context)

    def build_agent_command(
        self,
        prompt: str,
        model: str,
        profile: str = PROFILE_AGENT_READONLY,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build ``codex exec`` under an explicit sandbox policy (D3e).

        Both profiles start from :meth:`build_command` and then point the
        ``--sandbox`` slot at their **own** row of ``_SANDBOX_BY_PROFILE`` (M5).
        Neither leg inherits the other's policy by accident, and neither restates
        a policy string of its own — which is what makes the two profiles argv-
        distinguishable by construction rather than by the coincidence that they
        happen to have been written with different literals.

        ``agent-readonly`` renders ``--sandbox read-only``: codex refuses
        model-generated writes itself, so a prompt-injected validator cannot edit
        the repository while pretending to score suggestions.

        ``agent-write`` renders ``--sandbox workspace-write`` — codex's own
        documented write policy, rooted at the process ``cwd``, which the executor
        pins to the resolved repo root (D3h). It is deliberately **not**
        ``--dangerously-bypass-approvals-and-sandbox`` (nor the older
        ``--yolo``): a runner with no honored write sandbox is refused for
        ``agent-write``, so fabricating a bypass here would delete the very
        boundary that makes the profile eligible. Network access is left at
        codex's own workspace-write default rather than being widened here.

        **The one override** (D6, 2026-09-17): nothing this method renders is
        ever a bypass, and the default argv of every profile stays that way —
        but a *dispatch-time* rewrite exists, :meth:`apply_sandbox_fallback`,
        which points the same ``--sandbox`` slot at ``danger-full-access`` for
        ``generate`` and ``agent-readonly`` only. It is reachable through
        exactly one gate, applied by ``sandbox_refusal`` (fan-out) and
        ``_detect_sandbox`` (executor): the D6 probe verdict is ``unavailable``
        (bubblewrap cannot start here; never ``unknown``), the profile is one
        of the two read-only ones, and ``providers.codex.sandbox_fallback`` is
        ``auto`` — which it is unless a config layer wrote ``off``. So on a
        stock Ubuntu 24.04 this is what a read-only codex dispatch runs as by
        default: the read-only profile's own denial mechanism is gone — the
        model's shell has the operator's rights, as it does for every reviewer
        with no OS sandbox of its own — and every artifact of such a slot says
        so in so many words. ``agent-write`` is refused under a broken sandbox
        exactly as before, whatever the key says; the override raises on it
        rather than rendering.
        """
        if profile not in (PROFILE_AGENT_READONLY, PROFILE_AGENT_WRITE):
            return super().build_agent_command(
                prompt, model, profile, timeout_s=timeout_s, schema=schema
            )
        cmd = self.build_command(prompt, model, timeout_s=timeout_s, schema=schema)
        return self._apply_sandbox(cmd, profile)

    @staticmethod
    def _apply_sandbox(
        cmd: List[str],
        profile: str,
        *,
        rung: Optional[str] = None,
        context: Optional[JailContext] = None,
    ) -> List[str]:
        """Point ``cmd``'s ``--sandbox`` value at ``profile``'s policy (M5).

        The rewrite is *positional* — the element right after the first
        ``--sandbox`` — never a sweep of argv for the outgoing value. The prompt
        is the final element and a model string is arbitrary text, so a value
        sweep would silently rewrite either one if it happened to equal
        ``workspace-write``, leaving a stray ``read-only`` positional that codex
        would take as the prompt (and that
        ``base.build_agent_command_for_transport`` could no longer recognise at
        ``argv[-1]``). ``cmd`` is mutated in place and returned; every caller
        hands over a list :meth:`build_command` just built, so nothing shared is
        touched.

        ``rung=`` renders a fallback rung instead of the profile's row (D6
        override 2026-09-17, landlock rung 2026-09-22) — keyword-only, default
        ``None``, so every existing caller renders the row it always did.
        ``unsandboxed`` writes :data:`SANDBOX_FALLBACK_VALUE` into the slot.
        ``landlock`` writes ``read-only`` — whatever the profile's row, because
        ``workspace-write`` plus the feature is the exit-101 panic — and
        **inserts** :data:`LANDLOCK_FEATURE_PAIR` at the measured splice site:
        immediately after ``--skip-git-repo-check`` (the end of ``_BASE_ARGV``)
        and so ahead of ``--output-schema`` and ``--model``, which keeps
        ``--sandbox`` at index 2 and the prompt last. The insert is idempotent:
        an agent leg passes through here twice (``build_agent_command``, then
        ``apply_sandbox_fallback`` at dispatch), and a slot rewrite survives
        that by construction where an insert would render the pair twice.
        ``_sandbox_for`` still runs first: an unknown profile raises the same
        way on every path, and a profile outside ``SANDBOX_FALLBACK_PROFILES``
        is refused here too, one level below :meth:`apply_sandbox_fallback`,
        because two callers rendering a rung is one too many places for a
        write profile to slip through.
        """
        sandbox_at = cmd.index("--sandbox")
        policy = _sandbox_for(profile)
        if rung is not None:
            write_on_rung = (
                profile in SANDBOX_WRITE_FALLBACK_PROFILES
                and WRITE_RUNG_OPT_IN
                and rung == SANDBOX_RUNG_PLUGIN_LANDLOCK
            )
            if profile not in SANDBOX_FALLBACK_PROFILES and not write_on_rung:
                raise ValueError(
                    f"codex never runs the {profile!r} profile on a sandbox "
                    f"fallback (a write profile takes only "
                    f"{SANDBOX_RUNG_PLUGIN_LANDLOCK!r})"
                )
            if write_on_rung:
                _require_write_context(profile, context)
            if rung == SANDBOX_RUNG_UNSANDBOXED:
                policy = SANDBOX_FALLBACK_VALUE
            elif rung == SANDBOX_RUNG_LANDLOCK:
                policy = "read-only"
                if not _has_pair(cmd, LANDLOCK_FEATURE_PAIR):
                    splice = cmd.index("--skip-git-repo-check") + 1
                    cmd[splice:splice] = list(LANDLOCK_FEATURE_PAIR)
            elif rung == SANDBOX_RUNG_PLUGIN_LANDLOCK:
                if context is None:
                    raise ValueError(
                        "codex's plugin-landlock rung needs the attempt's jail "
                        "context (its scratch directory and write scope); it is "
                        "never rendered without one"
                    )
                policy = SANDBOX_FALLBACK_VALUE
                _splice_developer_instructions(cmd, context)
            else:
                raise ValueError(f"codex has no sandbox fallback rung {rung!r}")
        cmd[sandbox_at + 1] = policy
        return cmd

    def note_dispatch(
        self,
        profile: str,
        model: str = "",
        *,
        anchor: Optional[str] = None,
    ) -> None:
        """Record codex's trust state before a child starts (plan I12, option B).

        Both spawn sites call this through ``llm_client.provider_dispatch_context``
        before any codex child runs. It arms ``utils.codex_trust`` for the home the
        child will see (``CODEX_HOME`` from this adapter's env delta, else the
        inherited one, else ``~/.codex``) and the repository the dispatch is
        anchored in, so ``multi_llm.main``'s ``finally`` can remove only the
        ``[projects."<repo>"] trust_level = "trusted"`` tables this run's
        children added. It never refuses and never changes the argv or env:
        option A's override was measured to narrow what the child loads (the
        repo's ``AGENTS.md``), so it is not used.
        """
        try:
            from .. import codex_trust
            env = dict(os.environ)
            try:
                delta = self.resolve_env(model, profile, anchor=anchor)
            except Exception:  # noqa: BLE001 - bookkeeping may never block a dispatch
                delta = {}
            for key, value in (delta or {}).items():
                if isinstance(value, str):
                    env[key] = os.path.expanduser(value)
            home = (env.get("CODEX_HOME") or "").strip() or os.path.join(
                env.get("HOME") or os.path.expanduser("~"), ".codex"
            )
            codex_trust.arm(home, [anchor, os.getcwd()])
        except Exception:  # noqa: BLE001 - bookkeeping may never block a dispatch
            pass

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """Name constraint 2's panic by its cause; nothing to add otherwise.

        A user who once ran ``codex features enable use_legacy_landlock`` sees
        every ``workspace-write`` dispatch die with exit 101 and a Rust
        backtrace that names no config file. The one sentence that identifies
        it is mapped back to :data:`LANDLOCK_GLOBAL_PANIC_REASON`. Reads stderr,
        the channel a panic is printed on. Diagnostics only, as the base
        contract requires: the classification is untouched.
        """
        if is_landlock_global_panic(stderr):
            return LANDLOCK_GLOBAL_PANIC_REASON
        # codex 0.156.1's rung-1 panic (2026-09-24): a different sentence from
        # constraint 2's, with the same exit 101 — told apart by text alone.
        if is_landlock_needs_bwrap_panic(stderr):
            return LANDLOCK_NEEDS_BWRAP_REASON
        return super().describe_failure(stdout, stderr)

    def vendor_text(self, stdout: str, stderr: str) -> Tuple[str, str]:
        """codex's own events, without the model's or the repository's text.

        codex does not echo our prompt, but it echoes the **repository**: a
        ``command_execution`` item's ``aggregated_output`` is the output of the
        ``rg``/``cat`` the model ran over the plan, and ``agent_message`` /
        ``reasoning`` are the model's prose about it. Classified whole, a plan
        that discusses rate limits reads as ``rate_limited`` and one that
        discusses model names as the batch-fatal ``invalid_model``.

        Dropped: ``item.*`` events whose item is one of
        :data:`_NON_VENDOR_ITEM_TYPES`, plus a **final** line cut mid-event
        that opened as one (:func:`_is_cut_non_vendor_item`). Kept whole:
        ``error``, ``turn.failed`` (where the 401 and the 429 terminal live),
        ``thread.started``, ``turn.started``, ``turn.completed``, the nested
        ``error`` item, unknown event and item types, and non-JSON lines (the
        bare ``stream error: exceeded retry limit…`` sentence).

        The base contract holds in all three parts: whole lines are removed and
        nothing is added; a stream with no parseable line, or any exception in
        the walk, returns the input unchanged; stderr is never reduced.

        Separate from :meth:`audit_readonly_stream` on purpose: that audit
        judges the *commands* and must keep seeing every item. This hook is
        applied inside :meth:`classify_failure` only, so the raw stream every
        human-facing excerpt is cut from is untouched.
        """
        try:
            return _vendor_stdout(stdout), stderr
        except Exception:
            return stdout, stderr

    def audit_readonly_stream(self, raw_stream: str) -> Optional[Any]:
        """Plan §4.2 option B: classify every tool item on the full stream.

        The walk (and every fail-closed rule) is
        ``codex_stream_audit.audit_codex_stream``, written against the 0.156.1
        capture in ``tests/fixtures/codex/0.156.1/``. ``parse_output`` below
        never looks at ``command_execution``/``file_change`` items, so the
        audit parses them itself.
        """
        from .codex_stream_audit import audit_codex_stream

        return audit_codex_stream(raw_stream)

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Read usage off the terminal turn event of ``codex exec --json`` (D3j).

        Selected by event identity (``turn.completed`` carrying a ``usage``
        object), never by position, and the **last** such event wins — the item
        stream the answer is recovered from carries no usage at all, so the two
        never interfere.
        """
        usage: Optional[Dict[str, Any]] = None
        for line in (stdout or "").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") not in ("turn.completed", "token_count"):
                continue
            candidate = event.get("usage")
            if isinstance(candidate, dict):
                usage = candidate

        if not usage:
            return None

        def _num(key: str) -> Optional[Any]:
            value = usage.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
            return None

        out: Dict[str, Any] = {}
        input_tokens = _num("input_tokens")
        cached = _num("cached_input_tokens")
        output_tokens = _num("output_tokens")
        reasoning = _num("reasoning_output_tokens")
        if input_tokens is not None:
            out["input_tokens"] = input_tokens
        if cached is not None:
            out["cached_input_tokens"] = cached
        if output_tokens is not None:
            # Reasoning output is billed output; codex reports it separately.
            out["output_tokens"] = output_tokens + (reasoning or 0)
        if "input_tokens" in out and "output_tokens" in out:
            out["total_tokens"] = out["input_tokens"] + out["output_tokens"]
        return out or None

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """Parse ``text`` as JSON, falling back to embedded-JSON extraction.

        Read the way the extractor reads a reply (``_loads_reply``: a raw
        control character inside a string is kept, not fatal). The strict
        parse failed a whole document over one typed line break, and the
        array-preferring fallback then served the document's own ``tasks``
        array where an object was expected (fix round 8).
        """
        if text.startswith(('[', '{')):
            try:
                return {"success": True, "data": _loads_reply(text)}
            except json.JSONDecodeError:
                pass

        return extract_json_from_text(text, prefer_arrays=True)

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse the NDJSON event stream emitted by ``codex exec --json``.

        The assistant's reply arrives as ``item.completed`` events whose nested
        item has ``type == "agent_message"``. Three details matter, all verified
        against live codex-cli 0.144.0 output:

        - ``reasoning`` items are also ``item.completed`` and also carry a
          ``text`` field, so the item type must be checked or chain-of-thought
          leaks into the payload.
        - ``item.started``/``item.updated`` carry streaming deltas; ignoring
          them keeps text from being counted twice.
        - A turn may contain several agent messages (prose, then the answer),
          so the last is preferred over concatenating standalone JSON documents.

        The walk itself is :func:`_scan_codex_stream`, shared with
        :meth:`salvage_text`.
        """
        scan = _scan_codex_stream(stdout)
        messages = scan.messages
        legacy_parts = scan.legacy_parts
        fatal_errors = scan.fatal_errors
        item_errors = scan.item_errors

        candidates: List[str] = []
        if messages:
            candidates.append(messages[-1])
            if len(messages) > 1:
                candidates.append("\n".join(messages))
        elif legacy_parts:
            candidates.append("".join(legacy_parts))

        if not candidates:
            error = "No text events found in output"
            reported = fatal_errors or item_errors
            if reported:
                error = "Codex reported an error: " + "; ".join(reported)
            return {"success": False, "error": error, "raw": stdout, "data": None}

        if not any(candidate.strip() for candidate in candidates):
            return {"success": False, "error": "Empty text response", "raw": stdout, "data": None}

        result: Dict[str, Any] = {}
        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate:
                continue
            result = self._extract_json(candidate)
            if result.get("success"):
                return result

        if fatal_errors:
            result = dict(result)
            result["error"] = "{} (codex reported: {})".format(
                result.get("error", "Failed to parse response"), "; ".join(fatal_errors)
            )
        return result

    def native_structured_output(self, stdout: str) -> Any:
        """The ``--output-schema`` document: the last ``agent_message``, whole.

        codex never emits a ``structured_output`` key. Measured 2026-10-05 on
        codex-cli 0.160.0 against a localhost Responses stub (zero spend): with
        ``--output-schema`` the request carries ``text.format = {type:
        json_schema, strict: true, name: codex_output_schema}`` — the API's
        strict structured output — and the document comes back as the final
        ``item.completed`` ``agent_message``'s ``text``, a JSON string and
        nothing else. So that text is the native answer when, and only when,
        the whole of it parses; a message with prose around a document is not
        what strict output produces, and stays on the recovery path. The caller
        validates the value against the schema before marking it ``native``.
        It parses as the rest of the lane does (``_loads_reply``), so a raw
        control character inside a string does not lose the native answer
        (fix round 8).
        """
        try:
            scan = _scan_codex_stream(stdout or "")
            if not scan.messages:
                return None
            return _loads_reply(scan.messages[-1].strip())
        except Exception:  # noqa: BLE001 - the hook must never raise
            return None

    def salvage_text(self, stdout: str) -> Optional[str]:
        """The last ``agent_message``'s text, for the salvage gate (D4.1/D4.4).

        A failed codex stream is mostly transport: ``command_execution`` items
        whose ``aggregated_output`` is whatever the model ``cat``-ed, ``reasoning``
        text, ``turn.completed`` usage. Handed to ``has_salvageable_json`` whole,
        the arrays inside those items (an MCP result's ``content``, a
        ``web_search`` item's action) pass it as if they were findings — 14 of the
        18 committed ``.jsonl`` captures did, ``run_0c477c4d_partial`` (a run that
        never wrote an answer) among them — while a real answer array, being a
        JSON-escaped string inside ``item.text``, did not.

        The answer is the text :meth:`parse_output` reads first: the **last**
        ``agent_message`` (same walk, :func:`_scan_codex_stream`). Earlier ones
        are narration between tool calls and are dropped, not joined — joining
        could hand the gate an example array quoted in passing (plan D4.2).
        codex emits an ``agent_message`` only on ``item.completed``, never as a
        streamed delta, so there is no half-written message to recover: a run
        killed mid-answer holds none of it.

        * ``None`` when no line is a codex event (not this adapter's stream);
        * ``""`` when the stream holds no ``agent_message`` — a verdict, final;
        * the legacy ``text``/``message``/``content`` parts joined, for the
          pre-0.14x shape ``parse_output`` still falls back to.

        Never raises: a failed walk is ``""``, the reading the caller would give
        a raise anyway.
        """
        try:
            scan = _scan_codex_stream(stdout or "")
            if scan.messages:
                return scan.messages[-1]
            if scan.legacy_parts:
                return "".join(scan.legacy_parts)
            return "" if scan.saw_event else None
        except Exception:  # noqa: BLE001 - the hook must never raise
            return ""
