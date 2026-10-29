"""Cursor-agent CLI provider implementation."""

import atexit
import contextlib
import glob
import json
import os
import re
import shutil
import sys
import tempfile
import threading
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Iterator, List, Optional, Tuple

from .base import (
    PROFILE_GENERATE,
    USAGE_PARTIAL,
    VERSION_TOO_LOW as _VERSION_TOO_LOW,
    LLMProvider,
    ReasoningLadder,
    StructuredSchema,
    matches_any,
    reset_flag_gate_cache,  # noqa: F401 - M14: the one gate's reset, re-exported
)
from .result_envelope import (
    classify_api_error_status,
    describe_refused_envelope,
    parse_result_envelope,
)

#: The most of stderr's last line :meth:`CursorAgentProvider.describe_failure`
#: will quote. The measured reason lines are short (``RetriableError:
#: [resource_exhausted] Error`` is 40 characters); the cap is for the day the
#: last line is a stack frame or a wrapped JSON body, and it matches the
#: quoted-words bound ``result_envelope._MAX_QUOTED_CHARS`` applies to a
#: ``result`` sentence, so the two channels' one-liners are the same length.
_MAX_DESCRIBED_STDERR_CHARS = 400

#: M12 (§6.1): cursor has no rung on the ladder because it has no separate
#: effort *axis* to put one on. Its model list is fully pre-parameterized —
#: effort, thinking and fast are baked into one atomic slug
#: (``gpt-5.5-extra-high``, ``claude-opus-5-thinking-high-fast``) — so the
#: effort a run uses is chosen by picking a model name, and a ``:effort`` suffix
#: would only corrupt that name. Declaring no ``REASONING_EFFORTS`` is what keeps
#: every cursor slug intact through :func:`~.base.split_reasoning_effort`.
EFFORT_LADDER = ReasoningLadder(
    provider="cursor-agent",
    declined=(
        "effort is baked into cursor's own model slugs (gpt-5.5-extra-high, "
        "claude-opus-5-thinking-high-fast), so it is selected by model name and "
        "a `:effort` suffix would only corrupt the slug"
    ),
)

# ---------------------------------------------------------------------------
# §5.4.1 — the per-flag capability gate, in its **load-bearing** form
# ---------------------------------------------------------------------------

#: The two tokens that replace ``-f`` (M1/§3.1, atomic group **A5**). They are
#: inseparable and both are load-bearing:
#:
#: * without ``--trust`` the launch dies on a workspace-trust gate — measured at
#:   exit 1, 0.43 s, zero stdout, ``⚠ Workspace Trust Required … Pass --trust,
#:   --yolo, or -f``;
#: * ``--trust`` alone still **writes files**, because ``--print`` is documented
#:   as having "access to all tools, including write and shell". ``--mode ask``
#:   is the only one of the two that actually refuses ("I'm in Ask mode, so I
#:   can't create or edit files").
#:
#: So there is deliberately **no degraded argv**: dropping ``--trust`` fails the
#: launch, and the only other way to satisfy the trust gate is ``-f``/``--yolo``,
#: which is the write bypass this adapter exists to stop passing. When the gate
#: cannot confirm both tokens the slot is refused before spawn.
#:
#: **M15/§3.5 pins the absence of the token these replaced.** ``-f``/``--force``/
#: ``--yolo`` is in the ``--yolo``-class negative set that
#: ``tests/test_read_only_modes.py`` scans for over *every* adapter's
#: ``build_command``/``get_env``, and cursor-agent declares no
#: ``bypass_exception`` in ``providers.yaml``'s ``read_only_modes:`` table — so
#: the flag cannot return without that guard going red, wherever in this file it
#: is reintroduced. ``--mode ask`` is this adapter's row in that table, one of
#: its three probed positives; ``--trust`` is deliberately **not** part of the
#: recorded mechanism, because it satisfies a launch gate and grants nothing.
CURSOR_REQUIRED_FLAGS: Tuple[str, ...] = ("--trust", "--mode")

#: §5.1's state name for a CLI too old for a flag the dispatch needs — the
#: availability vocabulary's own word, imported rather than re-typed (M14), so
#: this refusal, the executor's preflight refusal and a report all say it the
#: same way.
#:
#: **What is version-gated here and what is not.** cursor declares
#: ``version_cmd`` (M14 measured ``cursor-agent --version`` → exit 0,
#: ``2026.08.11-e8db854`` on stdout), so its build is *read* like every other
#: adapter's. What it still declares no ``min_version`` for is the pair below:
#: no floor has been measured for ``--trust``/``--mode``, and a floor invented
#: from the one build they were probed on would disable installs that work
#: (§5.4.1(a)). So the *help text* remains the gate for these two flags, and the
#: version read remains what names the build in a report.
VERSION_TOO_LOW = _VERSION_TOO_LOW


class CursorFlagsUnconfirmed(RuntimeError):
    """The installed cursor-agent could not be shown to accept both tokens.

    Raised **before** any spawn, from :meth:`CursorAgentProvider.build_command`,
    which is called outside every caller's ``try`` on purpose: the fan-out
    records it as this model's failure (``run_single_model``'s per-model
    ``except``) and the rest of the fan-out is unaffected. That is the named
    refusal §5.4.1 requires — never a silent downgrade to a writable fan-out.
    """

    def __init__(self, missing: Tuple[str, ...], binary: str) -> None:
        self.missing = tuple(missing)
        self.binary = binary
        self.state = VERSION_TOO_LOW
        super().__init__(
            f"cursor-agent slot refused ({VERSION_TOO_LOW}): {binary} does not list "
            f"{', '.join(self.missing)} in its --help, and multi-llm will not run "
            f"cursor without {' + '.join(CURSOR_REQUIRED_FLAGS)} "
            "(--trust satisfies the workspace-trust gate, --mode ask is what refuses "
            "writes; the only other argv that launches is the -f/--yolo write bypass). "
            "Upgrade cursor-agent, or drop cursor from --models."
        )


# The help probe, its memo cache and the runnable-binary resolution that used to
# live here are **gone** — M14 (§5.4.1) absorbed all three into the one shared
# gate in `base.py`, where `LLMProvider.missing_flags` is this refusal's
# load-bearing form and `supports_flag` is the optional-flag one. Nothing about
# the posture moved: whole-word tokens, one help spawn per CLI per process, both
# streams read concatenated, and an unresolvable-or-unspawnable binary reporting
# nothing missing, because an absent CLI is `is_available()`'s refusal to make.


# ---------------------------------------------------------------------------
# Q11 — the residue ``--trust`` and ``--model`` leave in the user's profile
# ---------------------------------------------------------------------------
#
# Measured 2026-08-16. A single `--print --trust --mode ask --model <m>` run
# leaves **two** things behind in the user's own cursor profile, neither of
# which is multi-llm's to keep:
#
#   1. `<data>/projects/<slug>/.workspace-trusted` — 206 B of
#      `{"trustedAt":…,"workspacePath":…,"trustMethod":"cli-flag"}`. Markers
#      accumulate and are never garbage-collected (seven pre-existing ones on the
#      probe machine), and a marker also trusts that workspace for the user's own
#      later *interactive* cursor-agent sessions, which run with full tool
#      permissions.
#   2. `<config>/cli-config.json`'s `model` / `selectedModel` /
#      `modelSelectionHistory` (plus `modelParameters` and
#      `hasChangedDefaultModel`) — `--model` **rewrites the user's global default
#      model**. This is a side effect of `--model`, independent of `--trust`, and
#      a fan-out of several cursor rows would otherwise leave the user's
#      interactive CLI on whichever row finished last.
#
# **The primary mechanism is the per-run profile redirect below**, not this
# snapshot/restore guard. The guard is correct *within* one process (first arm
# wins, so two rows share the earliest clean snapshot) and **broken across two
# overlapping processes**: `_ARMED` is a module-level global, so a second
# orchestrator that arms after the first has already spawned a cursor row
# snapshots the *polluted* value as if it were the user's, and whichever process
# exits last writes that back — measured to move a user from `gpt-5.6-sol` to
# `composer-2.5` permanently. No in-process guard can see another process's
# baseline, so the fix is not to snapshot better but to never touch the user's
# files: see `isolate_profile_env`.
#
# What survives here is the **fallback**, active only when the redirect is off
# (`providers.cursor-agent.isolate_profile: off`) or refused. Its rules are
# deliberately narrow. Nothing outside the exact paths a snapshot recorded is
# ever touched; a marker that already existed is never removed (the user, or an
# earlier run, trusted that workspace on purpose); and a `cli-config.json` key is
# only put back when it actually moved.

_TRUST_MARKER_NAME = ".workspace-trusted"
_CLI_CONFIG_NAME = "cli-config.json"
_TRUST_METHOD_OURS = "cli-flag"

#: Every key a ``--model`` run rewrites. Everything else in ``cli-config.json``
#: is cursor's own bookkeeping (statsig, privacy and server-config caches) and is
#: left exactly as the run left it — reverting the whole file would also revert
#: those, and would clobber a concurrent interactive session's writes.
#:
#: ``modelParameters`` is keyed **per model id**, so a run adds its own model's
#: entry rather than replacing the user's: restoring it therefore means putting
#: the *whole mapping* back to its pre-run value, which is what the generic
#: per-key restore below already does (merging would leave the run's entry
#: behind). ``hasChangedDefaultModel`` is a bare flag cursor flips the first time
#: ``--model`` moves the default; a run that flips it tells the user's next
#: interactive session that *they* changed it. Both were leaking.
_MODEL_KEYS: Tuple[str, ...] = (
    "model",
    "selectedModel",
    "modelSelectionHistory",
    "modelParameters",
    "hasChangedDefaultModel",
)


def _cursor_config_dir() -> str:
    """Where ``cli-config.json`` lives, resolved exactly as cursor-agent does."""
    explicit = (os.environ.get("CURSOR_CONFIG_DIR") or "").strip()
    if explicit:
        return explicit
    xdg = (os.environ.get("XDG_CONFIG_HOME") or "").strip()
    if xdg:
        return os.path.join(xdg, "cursor")
    return os.path.join(os.path.expanduser("~"), ".cursor")


def _cursor_data_dir() -> str:
    """Where ``projects/<slug>/`` lives, resolved exactly as cursor-agent does.

    Note this is a **different** env var from :func:`_cursor_config_dir`'s.
    """
    explicit = (os.environ.get("CURSOR_DATA_DIR") or "").strip()
    if explicit:
        return explicit
    return os.path.join(os.path.expanduser("~"), ".cursor")


def _read_bytes(path: str) -> Optional[bytes]:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def _detect_indent(payload: bytes) -> int:
    """The indent width the file already uses, so a rewrite keeps its shape."""
    for line in payload.decode("utf-8", errors="replace").splitlines():
        stripped = line.lstrip(" ")
        if stripped and stripped != line and not stripped.startswith("\t"):
            return len(line) - len(stripped)
    return 2


class CursorResidueSnapshot:
    """What the user's cursor profile looked like before this process spawned cursor.

    Recorded **before** the spawn (that is the whole point: pre-existence is not
    recoverable afterwards) and put back by :meth:`restore`, which is idempotent
    and never raises — a cleanup that can fail a run is worse than the residue.
    """

    def __init__(
        self,
        *,
        projects_dir: str,
        markers: FrozenSet[str],
        config_path: str,
        config_bytes: Optional[bytes],
        config_mode: Optional[int],
        workspaces: Tuple[str, ...],
    ) -> None:
        self.projects_dir = projects_dir
        self.markers = markers
        self.config_path = config_path
        self.config_bytes = config_bytes
        self.config_mode = config_mode
        self._workspaces: List[str] = list(workspaces)
        self._lock = threading.Lock()

    @property
    def workspaces(self) -> Tuple[str, ...]:
        with self._lock:
            return tuple(self._workspaces)

    def add_workspace(self, workspace: str) -> None:
        """Also clean markers for ``workspace`` (a second row, another cwd)."""
        resolved = os.path.realpath(workspace)
        with self._lock:
            if resolved not in self._workspaces:
                self._workspaces.append(resolved)

    # -- restore ---------------------------------------------------------

    def restore(self) -> List[str]:
        """Undo what this process's cursor runs changed. Never raises."""
        actions: List[str] = []
        for step in (self._restore_markers, self._restore_config):
            try:
                actions.extend(step())
            except Exception:  # noqa: BLE001 - cleanup must never fail a run
                continue
        return actions

    def _restore_markers(self) -> List[str]:
        removed: List[str] = []
        pattern = os.path.join(self.projects_dir, "*", _TRUST_MARKER_NAME)
        for path in glob.glob(pattern):
            if not self._marker_is_ours(path):
                continue
            try:
                os.remove(path)
            except OSError:
                continue
            removed.append(path)
        return removed

    def _marker_is_ours(self, path: str) -> bool:
        """Three conditions, all required, none of them inferred after the fact.

        The marker must have been **absent** when this process armed (a marker
        the user already had is theirs), must carry cursor's own
        ``trustMethod: cli-flag``, and must name a workspace this process
        actually ran in — its own cwd, or a directory containing it, which is the
        repo root a pinned dispatch uses.

        ``trustMethod`` is the sharpest of the three, and it was verified against
        real markers rather than assumed: a marker written by ``--trust`` carries
        ``"trustMethod": "cli-flag"``, while one the user acquired another way
        omits the field entirely (observed on a 2026-08-04 marker). So a build
        that stops writing the field makes this cleanup a no-op — residue stays,
        nothing of the user's is ever removed, which is the safe direction.
        """
        if path in self.markers:
            return False
        payload = _read_bytes(path)
        if payload is None:
            return False
        try:
            document = json.loads(payload.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return False
        if not isinstance(document, dict):
            return False
        if document.get("trustMethod") != _TRUST_METHOD_OURS:
            return False
        declared = document.get("workspacePath")
        if not isinstance(declared, str) or not declared:
            return False
        # realpath on BOTH sides of the comparison (D1c): asymmetry is the bug.
        marked = os.path.realpath(declared)
        for workspace in self.workspaces:
            if workspace == marked or workspace.startswith(marked + os.sep):
                return True
        return False

    def _restore_config(self) -> List[str]:
        current = _read_bytes(self.config_path)
        if current is None:
            return []
        if self.config_bytes is not None and current == self.config_bytes:
            return []
        try:
            current_document = json.loads(current.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            # Not ours to repair, and rewriting it would destroy whatever the
            # CLI is mid-write on.
            return []
        if not isinstance(current_document, dict):
            return []
        if self.config_bytes is None:
            original_document: Dict[str, Any] = {}
        else:
            try:
                loaded = json.loads(self.config_bytes.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                return []
            if not isinstance(loaded, dict):
                return []
            original_document = loaded

        restored = dict(current_document)
        moved: List[str] = []
        for key in _MODEL_KEYS:
            if key in original_document:
                if restored.get(key) != original_document[key]:
                    restored[key] = original_document[key]
                    moved.append(key)
            elif key in restored:
                del restored[key]
                moved.append(key)
        if not moved:
            return []

        if self.config_bytes is not None and restored == original_document:
            payload = self.config_bytes  # byte-for-byte, formatting included
        else:
            indent = _detect_indent(self.config_bytes or current)
            trailing = "\n" if (self.config_bytes or current).endswith(b"\n") else ""
            payload = (
                json.dumps(restored, indent=indent, ensure_ascii=False) + trailing
            ).encode("utf-8")
        self._write_atomically(payload)
        return [f"{self.config_path}:{key}" for key in moved]

    def _write_atomically(self, payload: bytes) -> None:
        directory = os.path.dirname(self.config_path) or "."
        handle = tempfile.NamedTemporaryFile(
            mode="wb", dir=directory, prefix=".cli-config.", suffix=".tmp", delete=False
        )
        try:
            with handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if self.config_mode is not None:
                os.chmod(handle.name, self.config_mode)
            os.replace(handle.name, self.config_path)
        except OSError:
            try:
                os.unlink(handle.name)
            except OSError:
                pass
            raise


def snapshot_side_effects(workspace: Optional[str] = None) -> CursorResidueSnapshot:
    """Record the pre-spawn state of the two paths a cursor run rewrites."""
    projects_dir = os.path.join(_cursor_data_dir(), "projects")
    config_path = os.path.join(_cursor_config_dir(), _CLI_CONFIG_NAME)
    markers = frozenset(glob.glob(os.path.join(projects_dir, "*", _TRUST_MARKER_NAME)))
    config_bytes = _read_bytes(config_path)
    config_mode: Optional[int] = None
    try:
        config_mode = os.stat(config_path).st_mode & 0o777
    except OSError:
        config_mode = None
    return CursorResidueSnapshot(
        projects_dir=projects_dir,
        markers=markers,
        config_path=config_path,
        config_bytes=config_bytes,
        config_mode=config_mode,
        workspaces=(os.path.realpath(workspace or os.getcwd()),),
    )


_GUARD_LOCK = threading.Lock()
_ARMED: Optional[CursorResidueSnapshot] = None
_ATEXIT_REGISTERED = False


def arm_side_effect_guard(workspace: Optional[str] = None) -> CursorResidueSnapshot:
    """Snapshot once per process, at the first cursor spawn, and restore at exit.

    **First arm wins.** Under a concurrent fan-out a later row's reading is
    already polluted by an earlier row, so taking the earliest snapshot is what
    makes the restore converge on the user's real state rather than on another
    row's model. Later arms only widen the set of workspaces whose markers are
    ours to clean.

    ``atexit`` is the process-level ``finally``: it covers a normal exit and an
    unhandled exception, which is as far as an in-process guard reaches. A
    ``SIGKILL``'d run leaves the residue behind — the next run's restore does not
    pick it up either, because by then the marker is *pre-existing* and therefore
    out of bounds by the rule above. That is the safe direction to fail.
    """
    global _ARMED, _ATEXIT_REGISTERED
    with _GUARD_LOCK:
        if _ARMED is not None:
            armed = _ARMED
        else:
            armed = snapshot_side_effects(workspace=workspace)
            _ARMED = armed
            if not _ATEXIT_REGISTERED:
                atexit.register(restore_side_effects)
                _ATEXIT_REGISTERED = True
    armed.add_workspace(workspace or os.getcwd())
    return armed


def armed_snapshot() -> Optional[CursorResidueSnapshot]:
    """The snapshot this process is holding, if any."""
    with _GUARD_LOCK:
        return _ARMED


def restore_side_effects() -> List[str]:
    """Put the user's cursor profile back. Idempotent; safe to call at any time."""
    global _ARMED
    with _GUARD_LOCK:
        armed = _ARMED
        _ARMED = None
    return armed.restore() if armed is not None else []


def reset_side_effect_guard() -> None:
    """Drop the armed snapshot without restoring (tests only)."""
    global _ARMED
    with _GUARD_LOCK:
        _ARMED = None


# ---------------------------------------------------------------------------
# The per-run profile redirect — the primary mechanism (§2.3's shape)
# ---------------------------------------------------------------------------
#
# Give the run its own cursor profile and the residue problem stops existing:
# cursor never opens the user's `cli-config.json`, so there is nothing to
# snapshot, nothing for a second overlapping process to race on, and nothing to
# restore. The cross-process defect described above is not mitigated by this, it
# is **unreachable**.
#
# **Why this is safe, and why the earlier "logged-out CLI" worry was wrong.**
# cursor-agent 2026.08.11 resolves three things by three different rules:
#
#   * `cli-config.json` ← `CURSOR_CONFIG_DIR` → `$XDG_CONFIG_HOME/cursor` → `~/.cursor`
#   * `projects/<slug>/` ← `CURSOR_DATA_DIR`   → `~/.cursor`
#   * `auth.json`       ← a **third** rule that consults *neither* variable:
#     `$XDG_CONFIG_HOME/cursor/auth.json` on Linux (verified 0600 on the probe
#     machine), `~/.cursor` on macOS, `%APPDATA%\Cursor` on Windows.
#
# So redirecting the first two leaves credentials exactly where the CLI looks for
# them. `XDG_CONFIG_HOME` itself is therefore **never** redirected here — doing
# that *would* move `auth.json` on Linux and disable the provider outright. The
# only two variables this code writes are the two named above, and a test asserts
# that the env delta contains no third key.

#: ``providers.cursor-agent.isolate_profile``. Mirrors §2.3's
#: ``providers.opencode.hermetic``.
ISOLATE_AUTO = "auto"
ISOLATE_ON = "on"
ISOLATE_OFF = "off"
ISOLATE_VALUES: Tuple[str, ...] = (ISOLATE_AUTO, ISOLATE_ON, ISOLATE_OFF)
#: ``auto``, not ``on``, and the asymmetry of the two failure modes is why.
#: Only Linux's auth rule was *measured*; macOS and Windows are read off the
#: bundle. If that reading is wrong on either, ``on`` presents every cursor slot
#: as logged out — a disabled provider — whereas ``auto`` falls back to the
#: snapshot/restore guard, which is exactly the behaviour that shipped before
#: this change: correct within a run, broken across overlapping runs. Strictly
#: no worse, on the platforms nobody could test. This follows the same rule
#: §2.4 applies to the env allowlist ("opt-in per platform until that platform's
#: column is green") and §3.5 applies to unprobed rows. Set ``isolate_profile:
#: on`` to opt a non-Linux host in, or widen ``_AUTH_UNAFFECTED_PLATFORMS``
#: once that platform is measured.
ISOLATE_DEFAULT = ISOLATE_AUTO

#: Platforms where cursor's *auth* rule is **verified** not to follow either
#: redirected variable. ``auto`` redirects only here; ``on`` redirects
#: everywhere. Widening this set is a measurement, not an opinion.
_AUTH_UNAFFECTED_PLATFORMS: Tuple[str, ...] = ("linux",)

#: ------------------------------------------------------------------------
#: THE decision point. Flipping this one line is the whole per-run/per-spawn
#: switch; :func:`_profile_dir_for_spawn` is the only reader, and the tests in
#: ``tests/test_cursor_profile_isolation.py::TestScopeIsParameterized`` cover
#: both values. The parameterization stays; the **default is now measured**.
#:
#: * ``per-run`` (default, §2.3's shape) — one process-scoped directory shared by
#:   every cursor row.
#: * ``per-spawn`` — one directory per child.
#:
#: **The live probe ran, and the answer is that parameters do not bleed: argv
#: wins completely.** cursor's model list is fully pre-parameterized — effort,
#: thinking and fast are baked into one atomic slug (``gpt-5.5-extra-high``,
#: ``claude-opus-5-thinking-high-fast``) and the rest ride on argv
#: (``'claude-opus-4-8[context=1m,effort=high,fast=false]'``). A deliberately
#: hostile seeded config (``selectedModel = claude-opus-5-thinking-max``,
#: ``maxMode: true``, and ``modelParameters`` for the argv slug set to
#: ``context:1m, reasoning:xhigh, effort:max, thinking:true``) produced a run
#: **equivalent** to one from an empty config: same
#: ``providerOptions.cursor.modelName``, an empty reasoning block, and a scan
#: for ``opus``/``xhigh``/``effort``/``1m``/``thinking``/``maxMode`` found none
#: in either. The run even *reset* the seeded ``maxMode: true`` to ``false``.
#: **The config file is where the resolved argv lands — it is output, never
#: input**, so concurrent rows racing on one shared file cannot alter each
#: other's model, effort, thinking, fast or max-mode.
#:
#: Per-spawn is therefore not merely unnecessary, it is now actively **worse**,
#: for two measured reasons:
#:
#: 1. **Cost.** A cold profile dir costs ~3.35 s (8.85 s vs 5.50 s warm),
#:    mostly re-fetching the 703 KB statsig cache. Per-run pays that once;
#:    per-spawn charges every child, so a 4-row fan-out burns ~13 s
#:    re-downloading the same cache four times.
#: 2. **The leaked ``worker-server``.** cursor-agent spawns a detached
#:    ``worker-server`` daemon that outlives the CLI, reparents to init and
#:    **inherits the redirect env** (verified: its ``CURSOR_CONFIG_DIR``
#:    pointed into the scratch dir). A per-spawn directory would be torn down
#:    at *row* end — while that row's worker is still live and holding it.
#:    Per-run keeps removal at process exit, which is after every row; see
#:    :func:`cleanup_isolated_profiles` for the residual that still leaves.
#: ------------------------------------------------------------------------
SCOPE_PER_RUN = "per-run"
SCOPE_PER_SPAWN = "per-spawn"
PROFILE_DIR_SCOPE: str = SCOPE_PER_RUN

#: Prefix under ``TMPDIR``, so a leaked directory is sweepable by name.
_PROFILE_PREFIX = "multi-llm-cursor-"

_PROFILE_LOCK = threading.Lock()
#: Every directory **this process created**. Nothing outside this list is ever
#: removed — a user-supplied profile is respected, never deleted.
_PROFILE_DIRS: List[str] = []
_RUN_PROFILE_DIR: Optional[str] = None
_PROFILE_ATEXIT_REGISTERED = False

#: The two variables the redirect writes, and the only two it reads to decide
#: whether the user has already pinned a profile of their own.
_PROFILE_ENV_VARS: Tuple[str, ...] = ("CURSOR_CONFIG_DIR", "CURSOR_DATA_DIR")


def _provider_config(anchor: Optional[str] = None) -> Dict[str, Any]:
    """This adapter's own block from the layered config.

    Read through the normal layering (base → auto-discovered
    ``<git-root>/.multi-llm/providers.yaml`` → ``MULTI_LLM_PROVIDERS_CONFIG``),
    so the switch lives exactly where every other provider setting does.
    ``resolve_env`` forwards the run's anchor when it has one; otherwise this
    falls back to the pinned run anchor, §9.3.b's documented backstop.
    """
    from ..provider_registry import get_run_anchor, load_config  # import cycle

    try:
        config = load_config(anchor=anchor if anchor is not None else get_run_anchor())
    except Exception:  # noqa: BLE001 - a config failure must not decide this
        return {}
    block = (config.get("providers") or {}).get("cursor-agent")
    return block if isinstance(block, dict) else {}


def isolate_profile_setting(anchor: Optional[str] = None) -> str:
    """``auto`` | ``on`` | ``off``, defaulting to :data:`ISOLATE_DEFAULT`.

    YAML 1.1 turns a bare ``on``/``off`` into a bool, so both spellings —
    ``isolate_profile: off`` and ``isolate_profile: "off"`` — resolve to the same
    enum value. Anything unrecognised falls back to the default rather than
    failing the run: this switch decides *how well* a run is contained, and an
    unreadable value must never be the reason a fan-out does not start.
    """
    raw = _provider_config(anchor).get("isolate_profile", ISOLATE_DEFAULT)
    if isinstance(raw, bool):
        return ISOLATE_ON if raw else ISOLATE_OFF
    value = str(raw).strip().lower()
    return value if value in ISOLATE_VALUES else ISOLATE_DEFAULT


def user_pinned_profile_dirs() -> Tuple[str, ...]:
    """Which of the two variables the *user* already set, if any.

    A user who exports ``CURSOR_CONFIG_DIR`` or ``CURSOR_DATA_DIR`` is pinning
    their own cursor profile on purpose. That is respected verbatim: the run
    does **not** redirect (the fallback guard takes over instead), and the
    directory they named is never seeded, never written and never removed.
    """
    return tuple(name for name in _PROFILE_ENV_VARS if (os.environ.get(name) or "").strip())


def _seed_profile_dir(path: str) -> None:
    """Put whatever a fresh cursor profile *needs* into ``path``. One function.

    **A no-op, and the live probe is why — no seed is required.** Measured with
    both ``CURSOR_CONFIG_DIR`` and ``CURSOR_DATA_DIR`` pointed at one **empty**
    directory: a real cursor-agent run exited **0**, authenticated normally and
    wrote **0 bytes to stderr** — no login prompt, no first-run setup, no
    complaint about the missing ``cli-config.json``. ``auth.json`` was
    byte-identical before and after (it follows neither variable, as above) and
    the user's ``~/.cursor/projects`` trust markers were untouched. The CLI
    built what it needed on its own: ``cli-config.json``,
    ``statsig-cache.json`` (703 KB), ``chats/<hash>/<session>/{meta.json,
    store.db}`` and ``projects/<slug>/{.workspace-trusted, mcp-auth.json,
    agent-transcripts/…}``. So the empty 0700 directory *is* the seed, and this
    function stays empty. The one measured cost is time, not correctness: a
    cold directory ran in **8.85 s against 5.50 s warm**, a ~3.35 s penalty
    spent mostly re-fetching the statsig cache — which is an argument about
    *how many* directories a run creates (see :data:`PROFILE_DIR_SCOPE`), not
    about seeding one.

    It remains the single hook, so if a future cursor build does need something
    the minimum goes **here** and nowhere else. One rule binds whatever lands
    here: **never copy the user's
    ``cli-config.json`` in**. That would reintroduce the leak in reverse — the
    run would inherit (and then diverge from) the user's model, parameters and
    history, and a per-spawn scope would hand every row the same stale copy.
    Seed only literals this module owns.
    """
    return None


def _create_profile_dir() -> str:
    """A fresh 0700 profile directory, owned and tracked by this process."""
    global _PROFILE_ATEXIT_REGISTERED

    path = tempfile.mkdtemp(prefix=_PROFILE_PREFIX)
    try:
        os.chmod(path, 0o700)  # mkdtemp already does this; asserted, not assumed
        os.makedirs(os.path.join(path, "projects"), mode=0o700, exist_ok=True)
        _seed_profile_dir(path)
    except Exception:
        # A half-built profile is worse than none: unwind it and let the caller
        # fall back to the guard rather than pointing cursor at a broken dir.
        shutil.rmtree(path, ignore_errors=True)
        raise
    _PROFILE_DIRS.append(path)
    if not _PROFILE_ATEXIT_REGISTERED:
        atexit.register(cleanup_isolated_profiles)
        _PROFILE_ATEXIT_REGISTERED = True
    return path


def _profile_dir_for_spawn() -> str:
    """The directory this spawn gets — the **only** reader of the scope switch."""
    global _RUN_PROFILE_DIR

    if PROFILE_DIR_SCOPE == SCOPE_PER_SPAWN:
        return _create_profile_dir()
    # per-run: created lazily at the first cursor spawn and shared by every row.
    if _RUN_PROFILE_DIR is None:
        _RUN_PROFILE_DIR = _create_profile_dir()
    return _RUN_PROFILE_DIR


def isolate_profile_env(anchor: Optional[str] = None) -> Optional[Dict[str, str]]:
    """The env delta that gives this spawn its own cursor profile, or ``None``.

    ``None`` means "not redirected, use the fallback guard" and has exactly three
    causes, all deliberate:

    * ``isolate_profile: off`` — the user chose today's behaviour;
    * ``isolate_profile: auto`` on a platform where cursor's auth rule has not
      been verified against the redirect (see
      :data:`_AUTH_UNAFFECTED_PLATFORMS`);
    * the user pinned ``CURSOR_CONFIG_DIR``/``CURSOR_DATA_DIR`` themselves, or
      the directory could not be created.

    Never returns a third key. Redirecting ``XDG_CONFIG_HOME`` would move
    ``auth.json`` on Linux and present as a logged-out CLI, which is the one
    outcome this must not produce.
    """
    setting = isolate_profile_setting(anchor)
    if setting == ISOLATE_OFF:
        return None
    if setting == ISOLATE_AUTO and not sys.platform.startswith(_AUTH_UNAFFECTED_PLATFORMS):
        return None
    if user_pinned_profile_dirs():
        return None
    with _PROFILE_LOCK:
        try:
            path = _profile_dir_for_spawn()
        except Exception:  # noqa: BLE001 - containment must never fail a run
            # No temp dir, no redirect — and the guard is what the caller arms
            # instead. Refusing the slot over a cleanup mechanism would be a
            # worse trade than running with the mitigation that already shipped.
            return None
    return {"CURSOR_CONFIG_DIR": path, "CURSOR_DATA_DIR": path}


def isolated_profile_dirs() -> Tuple[str, ...]:
    """Every profile directory this process created and has not yet removed."""
    with _PROFILE_LOCK:
        return tuple(_PROFILE_DIRS)


#: Bounded, **unslept** re-walks of one profile tree. ``rmtree`` lists a
#: directory once and then unlinks what it listed, so a file the live
#: ``worker-server`` creates *after* that listing survives the pass and keeps its
#: parent non-empty; a second walk sees it and removes it. Three passes because
#: this must never become a wait: a worker writing continuously would otherwise
#: spin here, and blocking is the one outcome worse than the residue.
_REMOVE_PASSES = 3


def _remove_profile_tree(path: str) -> bool:
    """Best-effort removal of one profile tree. **Never raises, never waits.**

    Returns whether ``path`` is gone. The contract, in the order it matters:

    1. **Never raise and never block.** This runs from ``atexit`` and from a
       ``finally``; a cleanup that raised would turn a completed fan-out into a
       failed one, and a cleanup that waited on a daemon would delay every run
       for a directory nobody is reading. So: ``ignore_errors=True``, a
       ``try``/``except`` around the whole body rather than trust in
       ``rmtree``'s internals, no sleep, no retry loop with a clock.
    2. **Still remove it.** "Leak it and let ``TMPDIR`` sort it out" is not the
       cheap option here — one profile holds a 703 KB ``statsig-cache.json``
       plus a ``chats/<hash>/<session>/store.db`` *per run*. Hence the bounded
       re-walk above rather than a single pass.
    3. **Never kill anything.** cursor-agent leaks a detached ``worker-server``
       that reparents to init and inherits this directory through the redirect
       env. Reaping it is ``plans/timeout-orphans-and-reaggregate-determinism``'s
       job, not this module's; this code only has to stay correct next to it.

    **The residual, stated plainly:** a worker that outlives *this process*
    loses its config dir out from under it. That is the safe direction to fail.
    The CLI has already exited with the result the run consumed, so nothing a
    caller is waiting on depends on that directory; it holds only a telemetry
    cache and this run's own chat store; and — decisively — cursor's credentials
    are **not** in it (``auth.json`` follows neither redirected variable), so a
    worker losing it cannot log the user out or damage anything the user owns.
    The opposite direction — keeping the tree alive for an unbounded daemon —
    leaks per-run megabytes for a process nobody tracks.
    """
    try:
        for _ in range(_REMOVE_PASSES):
            shutil.rmtree(path, ignore_errors=True)
            if not os.path.exists(path):
                return True
        return False
    except Exception:  # noqa: BLE001 - see rule 1: cleanup may never raise
        return False


def remove_profile_dir(path: str) -> bool:
    """Remove ``path`` **iff this process created it**. Never raises.

    The containment rule §2.3 states outright: a directory this process did not
    create is not this process's to delete, whatever it is named and wherever it
    sits. The return value answers *ownership* — removal itself is the
    best-effort contract in :func:`_remove_profile_tree`, so ``True`` means "this
    was ours and it was removed as far as removal can be guaranteed".
    """
    with _PROFILE_LOCK:
        if path not in _PROFILE_DIRS:
            return False
        _PROFILE_DIRS.remove(path)
        global _RUN_PROFILE_DIR
        if _RUN_PROFILE_DIR == path:
            _RUN_PROFILE_DIR = None
    _remove_profile_tree(path)
    return True


def cleanup_isolated_profiles() -> List[str]:
    """Remove every profile directory this process created. Idempotent; never raises.

    Registered with ``atexit`` the moment the first directory is created — the
    process-level ``finally``, covering a normal exit and an unhandled exception
    — and called directly by :func:`isolated_profile_session`'s ``finally`` for
    callers that own a bounded scope. Under the default per-run scope that
    ``atexit`` pass is already after *every* row, which is why the leaked
    ``worker-server`` (see :data:`PROFILE_DIR_SCOPE`) is only ever racing the
    **last** row's daemon rather than each row's in turn.

    Returns the directories that are actually gone. A tree a live holder kept
    non-empty across :data:`_REMOVE_PASSES` walks is *not* reported as removed
    and is put back on the tracking list, so a bounded caller's ``finally`` that
    could not win the race hands it to the ``atexit`` pass instead of silently
    dropping it. Nothing here waits for, signals or kills that holder. A leak
    that survives both costs one directory under ``TMPDIR``, sweepable by the
    ``multi-llm-cursor-`` prefix.
    """
    with _PROFILE_LOCK:
        paths = list(_PROFILE_DIRS)
        _PROFILE_DIRS.clear()
        global _RUN_PROFILE_DIR
        _RUN_PROFILE_DIR = None
    removed: List[str] = []
    residue: List[str] = []
    for path in paths:
        (removed if _remove_profile_tree(path) else residue).append(path)
    if residue:
        with _PROFILE_LOCK:
            _PROFILE_DIRS.extend(p for p in residue if p not in _PROFILE_DIRS)
    return removed


@contextlib.contextmanager
def isolated_profile_session() -> Iterator[None]:
    """Scope the redirected profiles to a block, with the ``finally`` §2.3 asks for.

    ``atexit`` alone would hold the directories for the life of the interpreter;
    this is the explicit boundary a caller (or a test) uses when the run is
    shorter than the process.
    """
    try:
        yield
    finally:
        cleanup_isolated_profiles()


def reset_run_profile_dir() -> None:
    """Forget the per-run directory without removing it (tests only).

    A faithful stand-in for a *second process*: the new interpreter shares
    nothing, so it builds its own profile.
    """
    global _RUN_PROFILE_DIR
    with _PROFILE_LOCK:
        _RUN_PROFILE_DIR = None


def reset_profile_state() -> None:
    """Remove every created directory and drop the registration (tests only).

    The trailing ``clear()`` matters: :func:`cleanup_isolated_profiles`
    deliberately *re-tracks* a tree a live holder kept, and one test's simulated
    holder must not become the next test's inherited state.
    """
    global _PROFILE_ATEXIT_REGISTERED
    cleanup_isolated_profiles()
    with _PROFILE_LOCK:
        _PROFILE_DIRS.clear()
        _PROFILE_ATEXIT_REGISTERED = False


# ---------------------------------------------------------------------------
# M13 (§5.2, §5.3) — two probes, not one, and only one of them is about auth
# ---------------------------------------------------------------------------
#
# The donor plans proposed `cursor-agent about --format json` as a single call
# doing four jobs. Measured 2026-08-16 it does two of them:
#
# * **auth is `status --format json`.** It reads *local* token state
#   (`{"isAuthenticated":true,…}` vs `{"status":"unauthenticated",…}`), which is
#   the only thing that separates **offline-logged-in** from **logged-out**.
# * **`about` is demoted to a version / plan-tier readout.** Its `userEmail` and
#   `subscriptionTier` round-trip the network, so a logged-in HOME pointed at an
#   unreachable endpoint returns `userEmail:null, subscriptionTier:null` —
#   *byte-identical* to a logged-out scratch HOME, in all six states at exit 0.
#   Keying auth on `userEmail == null` reports a flight-mode laptop as logged
#   out. `about` is therefore never consulted for a verdict here, and
#   :class:`CursorAbout` has no field that could carry one.
# * **No default-model readback.** `about`'s `model` is a *display label*
#   ("GPT-5.6 Sol 272K Extra High"), not a `--model` slug, and it reflects the
#   **last-used** model — this skill's own fan-out mutates it. It must not be
#   read back as configuration, so it does not survive the boundary either.
# * **Verdicts come from JSON fields, never exit codes.** cursor-agent exited 0
#   in all six auth states measured (§5.3/§7.2), which is why
#   :meth:`CursorAgentProvider.classify_auth_probe` overrides the base rule that
#   reads a clean exit as authenticated.

#: The auth probe (§5.2). Declared as ``auth_check`` below, so the shared D3c
#: preflight runs it — this adapter spawns nothing of its own.
CURSOR_STATUS_ARGS: Tuple[str, ...] = ("cursor-agent", "status", "--format", "json")

#: The version / plan-tier readout, and nothing else (§5.2).
CURSOR_ABOUT_ARGS: Tuple[str, ...] = ("cursor-agent", "about", "--format", "json")

#: The **nine** keys `about --format json` really returns (measured 2026-08-16;
#: the donor plans said five). Written down because three of them are P13
#: identity fields and the count is what a redaction test asserts against.
CURSOR_ABOUT_KEYS: Tuple[str, ...] = (
    "cliVersion",
    "model",
    "subscriptionTier",
    "osPlatform",
    "osArch",
    "userEmail",
    "terminalProgram",
    "shell",
    "lastRequestId",
)

#: The three of those nine that are §4.5.1 P13 identity fields. They are
#: redacted at the **probe boundary** — before the envelope reaches a log, a
#: report or an artifact — rather than at each rendering site, because a
#: boundary is one place to get right and a rendering site is many.
CURSOR_ABOUT_IDENTITY_KEYS: FrozenSet[str] = frozenset(
    {"userEmail", "terminalProgram", "shell"}
)

#: Whatever the CLI calls being logged in / out in ``status``'s ``status``
#: field. ``isAuthenticated`` is the measured shape and is read first; these are
#: the spellings a sibling build might use for the same fact.
_STATUS_AUTHENTICATED: FrozenSet[str] = frozenset(
    {"authenticated", "logged_in", "logged-in", "loggedin", "ok"}
)
_STATUS_UNAUTHENTICATED: FrozenSet[str] = frozenset(
    {"unauthenticated", "logged_out", "logged-out", "loggedout",
     "not_logged_in", "not-logged-in"}
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _strip_ansi(text: str) -> str:
    """``text`` without SGR/CSI sequences — the text fallback's precondition."""
    return _ANSI_ESCAPE.sub("", text or "")


def _probe_object(text: str) -> Optional[Dict[str, Any]]:
    """The first JSON **object** in ``text``, or ``None``.

    ``None`` is half of §5.2's feature-sniff: errors from this CLI land on
    stderr with empty stdout and a non-zero exit (``error: unknown option
    '--format'``), and ``unexpected argument`` never occurs — it is
    commander.js, not clap — so the sniff is *exit ≠ 0 plus a decode failure*,
    never a match on vendor wording.
    """
    body = _strip_ansi(text)
    start = body.find("{")
    if start < 0:
        return None
    try:
        data, _end = json.JSONDecoder().raw_decode(body[start:])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def redact_probe_output(text: str) -> str:
    """§4.5's redaction, applied at the probe boundary (§5.2).

    Imported late for the same reason ``subagent_executor._redact`` does it: the
    redaction module must never become an import-time dependency of an adapter.
    A redactor that cannot be imported must not silently return the raw
    envelope, so the fallback drops the text rather than leaking it.
    """
    if not text:
        return ""
    try:
        try:
            from ..write_safety import redact_text
        except ImportError:  # pragma: no cover - direct-script import shim
            from utils.write_safety import redact_text  # type: ignore
    except Exception:  # pragma: no cover - a diagnostic never leaks on failure
        return "<redacted:probe-output>"
    return redact_text(text)


def status_auth_verdict(
    stdout: str, stderr: str, exit_code: int = 0
) -> Optional[bool]:
    """Read ``status --format json`` as authenticated / not / unknown.

    **The state this exists to separate is offline-logged-in from logged-out**,
    which `about` cannot do and an exit code cannot do either:

    * ``{"isAuthenticated":true,…,"message":"Logged in (unable to fetch user
      details)"}`` — logged in, network unreachable → ``True``;
    * ``{"status":"unauthenticated",…,"message":"Not logged in"}`` — logged out
      → ``False``.

    Both exit **0**, and both carry a null-ish user detail, so only the local
    token field tells them apart.

    ``None`` where no verdict field is present: an older build without the
    subcommand, a ``--format`` this CLI does not know, a decode failure. Silence
    is never read as a verdict in either direction — the fail-open posture
    M10's ``UNKNOWN`` exists for.
    """
    for stream in (stdout, stderr):
        data = _probe_object(stream)
        if data is None:
            continue
        flag = data.get("isAuthenticated")
        if isinstance(flag, bool):
            return flag
        state = str(data.get("status") or "").strip().lower()
        if state in _STATUS_AUTHENTICATED:
            return True
        if state in _STATUS_UNAUTHENTICATED:
            return False
    return None


@dataclass(frozen=True)
class CursorAbout:
    """What `about --format json` is allowed to tell this skill (§5.2).

    Four fields, and the *absence* of two others is the point:

    * **no auth field** — `about` cannot tell offline-logged-in from logged-out,
      so nothing here may be read as a login verdict;
    * **no model field** — `about`'s ``model`` is a last-used display label, not
      a ``--model`` slug, so reading it back as configuration would hand a
      fan-out a name no ``--model`` accepts.

    :attr:`redacted` is the envelope as it is safe to log: the three P13
    identity keys are already replaced, at this boundary, once.
    """

    #: ``cliVersion``, as the CLI printed it (``2026.08.11-e8db854``).
    version: str = ""
    #: ``subscriptionTier`` — **online only**; empty offline, which is a network
    #: fact and not an auth fact.
    plan_tier: str = ""
    #: Whether a JSON object was actually decoded (the feature-sniff's answer).
    parsed_json: bool = False
    #: The probe's own output, redacted. Never the raw envelope.
    redacted: str = ""


def _about_text_pairs(text: str) -> Dict[str, str]:
    """The ANSI-stripped ``Key  Value`` fallback shape, as a mapping.

    §5.2's fallback for a build whose ``--format`` flag is not recognised. The
    labels are normalized (case and separators dropped) because this shape is
    **unmeasured** — it is what the CLI prints without ``--format``, and keying
    it on an exact label this repo has never captured would be a guess dressed
    as a parser.
    """
    pairs: Dict[str, str] = {}
    for line in _strip_ansi(text).splitlines():
        parts = re.split(r"\s{2,}|\t|:\s", line.strip(), maxsplit=1)
        if len(parts) != 2:
            continue
        key = re.sub(r"[^a-z0-9]", "", parts[0].lower())
        value = parts[1].strip()
        if key and value:
            pairs.setdefault(key, value)
    return pairs


def read_about(stdout: str, stderr: str, exit_code: int = 0) -> CursorAbout:
    """The two jobs `about` really does, with the identity fields left behind.

    Version ✅ and plan tier ✅ (online). Auth ❌ and default-model readback ❌ —
    see :class:`CursorAbout` for why neither has a field to land in.
    """
    data = _probe_object(stdout) or _probe_object(stderr)
    redacted = redact_probe_output(f"{stdout or ''}{stderr or ''}")
    if data is not None:
        version = data.get("cliVersion")
        tier = data.get("subscriptionTier")
        return CursorAbout(
            version=str(version).strip() if isinstance(version, str) else "",
            plan_tier=str(tier).strip() if isinstance(tier, str) else "",
            parsed_json=True,
            redacted=redacted,
        )

    # Feature-sniff (§5.2): a decode failure alone is not enough — a build that
    # answers `--format json` and happens to print nothing is not a build that
    # lacks the flag. The text fallback is read only when the run also failed.
    if exit_code == 0:
        return CursorAbout(redacted=redacted)
    pairs = _about_text_pairs(f"{stdout or ''}\n{stderr or ''}")
    return CursorAbout(
        version=pairs.get("cliversion") or pairs.get("version") or "",
        plan_tier=(
            pairs.get("subscriptiontier")
            or pairs.get("subscription")
            or pairs.get("plan")
            or ""
        ),
        parsed_json=False,
        redacted=redacted,
    )


class CursorAgentProvider(LLMProvider):
    """Provider for cursor-agent CLI tool.

    This provider wraps the cursor-agent CLI, which returns responses in a JSON
    wrapper format: {"type":"result","result":"..."}. The provider handles
    extraction of the actual response content and JSON parsing with fallback
    strategies for code blocks and raw JSON.
    """

    # D3j: the `--output-format json` envelope really does carry a `usage`
    # block, so this adapter is not duration-only. `partial` rather than `full`
    # because the envelope has **no cost field at all** — the nine keys are
    # `type`, `subtype`, `is_error`, `duration_ms`, `duration_api_ms`, `result`,
    # `session_id`, `request_id`, `usage`, and `usage` itself is exactly
    # `{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens}`. Nothing
    # in it prices a run, and `cost_usd` is never derived from token counts
    # (that would need a per-model price table this repo does not own), so the
    # honest declaration is `partial`.
    usage_support = USAGE_PARTIAL

    #: ``--mode ask`` refuses every write, so this adapter can never produce the
    #: ``{output_json_path}`` file the review prompts used to demand. Measured
    #: 2026-08-18 on ``cursor-agent:gpt-5.6-sol-xhigh``, reproduced three times:
    #: the run *succeeds* (``{"type":"result","subtype":"success",
    #: "is_error":false,…}``) and its whole ``result`` is
    #: ``"I can't write the requested file while Ask mode is active. Switch to
    #: Agent mode and resend the request."`` — no JSON, no file, and the slot
    #: fails on ``JSON parsing failed from both file and stdout``. (A sibling
    #: model that ignores its own mode restriction and writes the file anyway is
    #: not a counterexample; it is the same argv producing undeclared behaviour.)
    #:
    #: The fix is the prompt, **not** the argv: the write refusal is the point of
    #: :data:`CURSOR_REQUIRED_FLAGS`, so this adapter asks for the JSON array on
    #: stdout — the channel ``--output-format json`` already gives it, and the
    #: one :meth:`parse_output` already unwraps.
    supports_file_output = False

    #: MEASURED FALSE, 2026-09-25: ``--mode ask`` refuses a shell. Both cursor
    #: lanes of that day's ``review-code`` run said so in their own logs — kimi:
    #: "Shell access is refused in this environment, so I'll review by reading
    #: the plan fully and inspecting the current file contents directly" (it
    #: returned ``[]``); grok: "Shell diffs are blocked in this mode". So this
    #: lane cannot run ``git diff`` and reviews from the diff files the
    #: orchestrator writes to the phase dir (``render_diff_access``'s ``False``
    #: text). Whether another cursor mode grants a read-only shell is
    #: unverified (plan: review-run-scope-salvage-and-failure-visibility T2.7).
    #: ``read_only_modes.cursor-agent.probed`` cites this attribute rather than
    #: restating it.
    runs_shell_in_generate = False

    #: MEASURED ``"cwd"`` (the default, declared because it is measured): ask
    #: mode keeps ``Read`` and ``Grep`` — the same 2026-09-25 kimi and grok logs
    #: read files under the repo root, and Q12 (2026-08-16) found ``Read``/
    #: ``Grep`` ``tool_use`` entries under this exact argv. Whether it reads
    #: OUTSIDE its working directory is **unverified**, so a phase dir outside
    #: the repo sends this lane down the inline branch rather than betting on it.
    generate_read_scope = "cwd"

    #: §7.2/§5.3 — cursor-agent exited **0 in all six auth states measured**, so
    #: for this CLI the exit code carries no verdict whatsoever and only a
    #: stream field does. Two shapes, both measured on 2026-08-16:
    #:
    #: * the ``--output-format json`` envelope's ``is_error`` flag (the nine-key
    #:   result object ``parse_output`` unwraps), and
    #: * a plain-text ``Error: Authentication required. Please run 'agent login'
    #:   first, …`` printed *instead of* the envelope when auth fails before the
    #:   session starts. That one already matches the base auth set
    #:   ("authentication required"); it is the ``is_error`` envelope that
    #:   nothing else would have caught.
    #:
    #: Reading the auth *state* off ``status --format json`` is a different job
    #: and now a separate one — :attr:`auth_check` declares that probe and
    #: :meth:`classify_auth_probe` reads it (M13). This attribute is only about
    #: a dispatch that produced no usable result.
    exit_zero_failure_markers = (
        re.compile(r'"is_error"\s*:\s*true'),
    )

    #: The build ``tests/fixtures/cursor-agent/``'s two rows were captured from,
    #: and the one lane that can capture them: `success` is HARVESTED from a
    #: credentialed live run against api2.cursor.sh
    #: (``tests/container/runs/20260819T145322Z/live-cursor-agent``), because
    #: cursor-agent reaches no surface any stub in this repo can serve — after
    #: its JSON handshake every call is `POST /aiserver.v1.<Service>/<Method>`
    #: in binary protobuf over Connect-RPC (``tests/container/redirect.yaml``).
    #: There is therefore no free re-capture, which is exactly why the version
    #: this parser was last confirmed against is worth writing down.
    #:
    #: **M14 opened the version read that M13 deliberately did not.** Measured
    #: 2026-08-21: ``cursor-agent --version`` exits 0 and prints
    #: ``2026.08.11-e8db854`` on **stdout**, so the build below is now *read*
    #: rather than only written down, and the shared gate resolves this
    #: adapter's binary from a declaration (``version_cmd[0]``) instead of a
    #: literal spelled a second time inside the gate. It is emphatically **not**
    #: wired to ``about``: the version comes from the CLI's own ``--version``,
    #: which is the boundary M13's demotion drew and this keeps.
    #:
    #: ``min_version`` stays empty ON PURPOSE, and independently: no floor has
    #: been *measured* for anything this adapter needs. The two flags that are
    #: load-bearing (:data:`CURSOR_REQUIRED_FLAGS`) are gated on the *help text*
    #: through :class:`CursorFlagsUnconfirmed`, because a floor invented from the
    #: single build they were probed on would disable installs that work
    #: (§5.4.1(a)). ``max_version_exclusive`` is empty for the same reason: no
    #: cursor build has been measured to break this parser, and a guessed
    #: ceiling refuses runs nobody showed to be broken.
    version_cmd = ("cursor-agent", "--version")
    verified_version = "2026.08.11-e8db854"

    #: M13 (§5.2) — the real auth probe, at last. It is a *local* token read:
    #: it reports `isAuthenticated` with the network down, which is exactly the
    #: state `about` cannot distinguish from a logged-out HOME. Declaring it
    #: here is the whole wiring — the shared D3c preflight runs it once per
    #: distinct runner per run and hands the verdict to
    #: :meth:`~.base.LLMProvider.describe_availability`, so this adapter spawns
    #: nothing itself and the probe cannot fan out from inside a picker loop.
    #:
    #: Until this row existed cursor-agent could only ever report ``UNKNOWN``:
    #: M10's rule is that ``READY`` requires a **positive** verdict and is never
    #: inferred from silence, and an adapter declaring no probe is silence.
    auth_check: Tuple[str, ...] = CURSOR_STATUS_ARGS

    #: What fixes a ``False`` verdict, named verbatim in the exit-3 refusal.
    #: Mirrors ``runners.cursor-agent.login_cmd`` in ``hosts/capabilities.yaml``.
    login_cmd = "cursor-agent login"

    #: M13 (§5.3) — printed, never run (no auto-install).
    install_hint = "curl https://cursor.com/install -fsS | bash"

    #: M13 (§5.2) — the version / plan-tier readout, declared so something
    #: actually runs it. ``about`` was demoted out of the auth path and left
    #: with exactly one job this repo has a use for: the **plan tier**, which no
    #: other probe reports. Declaring it here is the whole wiring — the spawn
    #: belongs to the human-invoked status path
    #: (:func:`utils.subagent_executor.probe_setup_metadata`, reached from
    #: ``install-host --check`` row 5), so this adapter still spawns nothing and
    #: no dispatch preflight pays for it.
    #:
    #: It is **not** the auth probe and cannot become one: :attr:`auth_check`
    #: names ``status`` (the local token read), and the tier below goes nowhere
    #: near a verdict — offline it is simply absent, which is a network fact.
    setup_probe: Tuple[str, ...] = CURSOR_ABOUT_ARGS

    #: M13 (§5.3) — the credential is a *file on disk*, but not one the per-run
    #: ``CURSOR_CONFIG_DIR``/``CURSOR_DATA_DIR`` redirect
    #: (:func:`isolate_profile_env`) can move. Measured on 2026.08.11 and
    #: recorded in ``providers.yaml``: ``auth.json`` follows a third rule that
    #: consults *neither* variable — ``$XDG_CONFIG_HOME/cursor/auth.json`` on
    #: Linux, ``~/.cursor`` on macOS, ``%APPDATA%\Cursor`` on Windows. So the
    #: redirect is a concurrency/residue mitigation only: a run pointed at a
    #: scratch profile keeps whatever credential the user already has, and
    #: anyone troubleshooting auth belongs at the path above, not in the
    #: redirected profile dir.
    auth_hint = (
        "cursor-agent keeps its credential in auth.json, not in an "
        "environment variable: $XDG_CONFIG_HOME/cursor/auth.json on Linux, "
        "~/.cursor on macOS, %APPDATA%\\Cursor on Windows. The per-run "
        "CURSOR_CONFIG_DIR/CURSOR_DATA_DIR profile redirect does not move it, "
        "so it never changes login state; `cursor-agent status --format json` "
        "reads that local token without touching the network."
    )

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "cursor-agent"

    @property
    def default_timeout(self) -> int:
        """Return the default timeout in seconds."""
        return 600

    def is_available(self) -> bool:
        """Check if cursor-agent CLI is available in PATH."""
        return shutil.which("cursor-agent") is not None

    def resolve_env(
        self, model: str, profile: str = PROFILE_GENERATE, **options: Any
    ) -> Dict[str, str]:
        """The shared env delta, plus this run's own cursor profile (Q11).

        ``resolve_env`` is the composition point *both* spawn sites call
        (``llm_client`` for the Lane A fan-out and ``subagent_executor._spawn``
        for a dispatch), and it runs immediately before the child starts — which
        makes it the only hook an adapter owns that is guaranteed to see every
        real spawn and no argv-only caller. :meth:`build_command` deliberately
        does **not** redirect or arm: it is called by ``detach._spec_binary``
        purely to read a binary name, and by every argv fixture.

        **Exactly one of the two mitigations is active per spawn.** The redirect
        is primary: with ``CURSOR_CONFIG_DIR``/``CURSOR_DATA_DIR`` pointing at
        this run's own directory, cursor never opens the user's profile, so
        there is nothing to snapshot and the cross-process corruption the guard
        cannot see is unreachable. Only when the redirect declines — the config
        switch is ``off``, ``auto`` on an unverified platform, the user pinned
        their own profile, or the directory could not be created — is the
        snapshot/restore guard armed as the fallback.

        **The fallback is armed with the dispatch's own ``cwd``.** A marker is
        only cleaned up when its ``workspacePath`` names a workspace this process
        ran in (:meth:`CursorResidueSnapshot._marker_is_ours`), so arming without
        one would record the *orchestrator's* directory while the child runs
        somewhere else — Lane B spawns with an explicit ``cwd`` — and the durable
        ``.workspace-trusted`` marker the run really wrote would be left behind
        as if it were the user's. ``None`` (Lane A's usual case) still means
        ``os.getcwd()``, which is exactly the directory such a child inherits.

        The keyword-only options the base declares are forwarded untouched
        rather than re-listed: this override adds a side effect and decides
        nothing about the env itself, so naming them here would only create a
        second place to keep in sync with ``LLMProvider.resolve_env``.
        """
        env = super().resolve_env(model, profile, **options)
        redirect = isolate_profile_env(anchor=options.get("anchor"))
        if redirect is None:
            arm_side_effect_guard(workspace=options.get("cwd"))
            return env
        env.update(redirect)
        return env

    def build_command(
        self,
        prompt: str,
        model: str,
        *,
        timeout_s: Optional[int] = None,
        schema: Optional[StructuredSchema] = None,
    ) -> List[str]:
        """Build the cursor-agent command with JSON output format.

        The argv is ``--print --trust --mode ask --output-format json --model
        <model> <prompt>`` (M1/§3.1). ``-f`` — ``--force``, alias ``--yolo``,
        "Run Everything" — is gone: it was a write bypass on a read-only fan-out,
        and it measurably let the CLI create files. See
        :data:`CURSOR_REQUIRED_FLAGS` for why the two replacements are one
        change and not two.

        ``--mode ask`` applies to **every** cursor Lane A phase, not just the
        text-only ones. Q12 was answered at tool level on 2026-08-16: under this
        exact argv cursor's own agent transcript carries ``tool_use`` entries for
        ``Grep`` and ``Read``, and the run found a file by an unguessable token
        it was never given. Ask mode keeps its read tools but **refuses a
        shell** — measured 2026-09-25 in the kimi and grok ``review-code`` logs
        ("Shell access is refused in this environment", "Shell diffs are blocked
        in this mode") and recorded as :attr:`runs_shell_in_generate`. So
        ``review-plan`` and ``review-tasks``, which read documents, are not
        degraded by it, but ``review-code`` is: this lane cannot run ``git
        diff``, and it depends on the scope manifest and per-file diffs the
        orchestrator writes to the phase dir before dispatch
        (``code-review/review-scope.md`` and ``code-review/diff/``), which the
        prompt's ``{diff_access}`` block points it at. The argv does not change
        for it: no ``--mode plan`` fallback is adopted, because whether any
        cursor mode grants a shell without granting writes is unverified.

        Args:
            prompt: The prompt text to send to the LLM.
            model: The model identifier to use.

        Returns:
            Command arguments for cursor-agent CLI invocation.

        Raises:
            CursorFlagsUnconfirmed: when cursor-agent is installed but its help
                does not list both gated tokens — the slot is refused as
                ``version-too-low`` rather than degraded.
        """
        # The gate (§5.4.1), through the shared machinery (M14). Its precondition
        # is that there is a binary to gate: a *missing* (or unexecutable)
        # cursor-agent is not the gate's refusal to make. `is_available()`
        # already reports that, `llm_client` checks it before building anything,
        # `detach._spec_binary` asks this method for the binary name precisely so
        # it can say "cursor-agent is not installed", and nothing that cannot be
        # spawned can reject a flag. Refusing here would replace a precise
        # message with silence — which is why `missing_flags` answers "nothing
        # missing" when the binary does not resolve, rather than "everything".
        missing = self.missing_flags(CURSOR_REQUIRED_FLAGS)
        if missing:
            raise CursorFlagsUnconfirmed(missing, self.gate_binary(runnable=True) or "")

        return [
            "cursor-agent",
            "--print",
            "--trust",
            "--mode",
            "ask",
            "--output-format",
            "json",
            "--model",
            model,
            prompt,
        ]

    def parse_usage(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """Recover usage from the ``--output-format json`` result envelope (D3j).

        ``parse_output`` unwraps ``result`` and **discards the envelope**, which
        is where ``usage`` lives, so this captures it before it is dropped. The
        block is camelCase (``inputTokens``/``outputTokens``/``cacheReadTokens``/
        ``cacheWriteTokens``), unlike claude-code's snake_case one, and fields
        are selected by name and omitted when absent — a zero would read as a
        free run. Only the cache **read** half is "cached input";
        ``cacheWriteTokens`` is deliberately dropped rather than folded into any
        total, because the normalized structure has no cache-write slot and
        claude-code's ``cache_creation_input_tokens`` is dropped for the same
        reason. No ``cost_usd``: the envelope carries no price (hence
        ``USAGE_PARTIAL``).
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

        _put("input_tokens", usage.get("inputTokens"))
        _put("output_tokens", usage.get("outputTokens"))
        _put("cached_input_tokens", usage.get("cacheReadTokens"))
        if "input_tokens" in out and "output_tokens" in out:
            out["total_tokens"] = out["input_tokens"] + out["output_tokens"]
        return out or None

    def classify_failure(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[str]:
        """The envelope's ``api_error_status``, then the shared text ladder.

        The same rung claude-code declares, over the same nine-key envelope and
        the same shared map (:func:`result_envelope.classify_api_error_status`);
        the narrowing shape is aider's ``classify_failure``.

        **On every committed cursor-agent capture this delegates.** Neither
        ``success`` nor ``exit-zero-failure`` carries an ``api_error_status``
        field at all — the live envelope has nine keys and that is not one of
        them — so both rows go to ``super()`` and reach
        :attr:`exit_zero_failure_markers` exactly as before. That is the point
        of pinning them: a status rung that swallowed the text ladder on an
        adapter which never emits the field would take this CLI's only failure
        signal with it. The map's coverage comes entirely from claude-code's
        rows, and this override exists so the field is not silently dropped if
        Cursor starts printing it.
        """
        category = classify_api_error_status(stdout)
        if category is not None:
            return category
        return super().classify_failure(stdout, stderr, exit_code)

    def describe_failure(self, stdout: str, stderr: str) -> Optional[str]:
        """The envelope's own line when there is one, else stderr's last line.

        Two channels, in the base hook's order — **stderr is the diagnosis,
        stdout is the answer** — read the way this CLI really writes them:

        * A run that reached the backend answers with the nine-key
          ``--output-format json`` envelope on stdout, and a failure is that
          envelope with ``is_error: true``; its ``result`` is the sentence.
          :func:`result_envelope.describe_refused_envelope` is the one renderer
          for it, shared with claude-code.
        * A run that never got an envelope leaves the reason on stderr, as its
          **last** line. Measured 2026-09-17 on ``cursor-agent:kimi-k3-high``:
          zero bytes on stdout, exit 1 after 23.7 s, and on stderr three
          ``Connection lost, reconnecting to https://agentn.global.api5.cursor.sh
          (attempt N)...`` / ``Retry attempt N...`` pairs followed by
          ``RetriableError: [resource_exhausted] Error`` — the one line that
          says what happened, and the one the bare ``exited with code 1`` in
          ``error_<model>.log`` and ``.status.json`` dropped. The progress
          lines above it are not the reason and are not returned; the line is
          capped so a stack trace's last frame cannot become a paragraph.

        Diagnostics, never classification: the same bytes reach
        :meth:`classify_failure` for the verdict, and returning ``None`` stays
        safe.
        """
        line = describe_refused_envelope(stdout)
        if line:
            return line
        for raw in reversed((stderr or "").splitlines()):
            candidate = " ".join(raw.split())
            if candidate:
                return candidate[:_MAX_DESCRIBED_STDERR_CHARS]
        return None

    def classify_auth_probe(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Optional[bool]:
        """The verdict is a JSON field or nothing — never the exit code (M13).

        The base rule reads a clean exit with no login notice as ``True``. For
        this CLI that rule manufactures a verdict: cursor-agent exited **0 in
        all six auth states measured** (§5.3/§7.2), so a clean exit says nothing
        whatsoever about credentials, and the offline-logged-in and logged-out
        envelopes are separated only by :func:`status_auth_verdict`'s local
        token field.

        Order, and it is load-bearing:

        1. the ``status --format json`` field — the whole point of the probe;
        2. failing that, the shared ``auth_error_patterns`` over the text,
           which is what catches a plain ``Error: Authentication required…``
           printed by a build with no ``--format`` flag;
        3. otherwise ``None``. Never ``True`` from silence — an unrecognised
           shape means the probe could not tell, and M10 renders that as
           ``UNKNOWN`` rather than as a runner that is ready.

        Nothing from ``stdout``/``stderr`` is returned or stored: the caller
        gets a tri-state, so the nine-key envelope's identity fields have no
        path out of this method. Where the *text* is needed, it crosses
        :func:`redact_probe_output` first.
        """
        verdict = status_auth_verdict(stdout, stderr, exit_code)
        if verdict is not None:
            return verdict
        haystack = f"{stdout or ''}\n{stderr or ''}".lower()
        if matches_any(self.auth_error_patterns, haystack):
            return False
        return None

    def read_setup_probe(
        self, stdout: str, stderr: str, exit_code: int = 0
    ) -> Dict[str, str]:
        """The one fact `about` is kept for: the plan tier (M13, §5.2).

        :func:`read_about` already does the reading — the version, the tier, the
        feature-sniff and the probe-boundary redaction — and this is the
        production caller that was missing: without it the readout was parsed by
        nothing and the status row had no way to say which plan a run is
        spending.

        **Only the tier crosses.** ``about``'s ``cliVersion`` is deliberately
        dropped: the version the status row prints comes from this adapter's own
        ``version_cmd`` (``cursor-agent --version``, M14), and reporting a second
        copy from a second probe would give one fact two owners that can
        disagree — the same rule :meth:`describe_setup` follows by deriving its
        rows instead of re-declaring them. The remaining seven keys never had a
        path out of :class:`CursorAbout` at all, and the three identity fields
        among them were already replaced at the probe boundary.

        **An absent tier is silence, never a verdict.** ``subscriptionTier``
        round-trips the network, so it is empty offline, empty on a build without
        ``--format``, and empty when the probe could not run. Each of those is a
        row with one less fact on it — never a claim about login state, which is
        exactly the conflation `about`'s demotion exists to prevent.

        The value is length-bounded and reduced to a printable character set
        before it is returned: it is CLI output bound for a terminal and a log,
        and a status row is not the place to discover what a surprising envelope
        prints.
        """
        tier = read_about(stdout, stderr, exit_code).plan_tier
        tier = re.sub(r"[^A-Za-z0-9 ._+-]", "", tier).strip()[:32].strip()
        return {"plan-tier": tier} if tier else {}

    def parse_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse cursor-agent output and extract structured data.

        The cursor-agent with --output-format json returns responses wrapped in:
        {"type":"result","result":"..."}

        This method unwraps that format and attempts to parse the inner result
        as JSON, with fallback strategies for various response formats.

        **It reads ``is_error``**, and the row that used to record it not doing
        so is what pins the fix: ``tests/fixtures/cursor-agent/``'s
        ``exit-zero-failure`` row is the harvested live envelope with that one
        field flipped to ``true``, and this method used to return
        ``{"success": True, "data": ["ok"]}`` for it, because
        :func:`parse_result_envelope` branched only on the presence of a
        ``result`` key. It now refuses that envelope with the flag named in the
        error (C5) — so an envelope cursor flagged as an error is a failure on
        **both** sides of the division of labour: the parser refuses to serve
        the document, and :meth:`classify_failure` still answers
        ``runner_error`` through :attr:`exit_zero_failure_markers`, which stays
        the only thing that says *why* on a CLI whose exit code carries no
        verdict.

        Args:
            stdout: The standard output from cursor-agent.
            stderr: The standard error (unused but required by interface).

        Returns:
            A dictionary with 'success' and 'data' (or 'error') keys.
        """
        # One shared implementation (§9.5): claude-code emits the same envelope
        # and used to carry a byte-identical copy of the unwrapping.
        return parse_result_envelope(stdout)
