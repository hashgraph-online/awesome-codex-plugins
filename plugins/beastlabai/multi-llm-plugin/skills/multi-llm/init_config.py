#!/usr/bin/env python3
"""Auto-config scaffolder for a per-project multi-llm config override.

``--init`` is a fully-automatic, zero-prompt config generator. It scans ``PATH``
for the supported provider CLIs (the same ``provider.is_available()`` check the
runtime uses), copies an **inert template** ``providers.yaml`` to
``<git-root>/.multi-llm/providers.yaml``, and **uncomments** exactly the lines
that belong to the **detected** providers:

  * each detected provider's full ``providers:`` sub-block (timeouts,
    concurrency, ``models:``) — undetected providers stay commented;
  * the ``defaults.models`` / ``defaults.quick_models`` candidate entries whose
    provider is detected;
  * ``default_provider`` is set to the first detected provider (base declaration
    order); left commented when nothing is detected.

There is **no** interaction, **no** TTY, and **no** model-listing subprocess
call at any point — the same deterministic text toggling runs identically inside
Claude Code, an external terminal, or CI. The override file is optional and
auto-discovered from the git root at run time.

Usage (the way the skill invokes it):

    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" init \\
        [--dir PATH] [--force] [--gitignore] [--template-only]

By default the file is left *trackable* (commit it for a team-wide, repo-standard
selection). Pass --gitignore to instead keep it as a developer-local, untracked
override. ``--template-only`` skips detection and writes the pristine inert
template verbatim.

Overwriting an existing config (``--force``) first copies it aside as
``providers.yaml.bak.<timestamp>`` and prints the backup path, so custom
settings are never silently lost and can be ported into the fresh file.
"""
import argparse
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# The script ships inside the skill but runs with the *user's* repo as CWD.
# Make the skill's own packages importable regardless of the caller's CWD.
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams  # noqa: E402
from utils.cli_common import build_parent_parser  # noqa: E402
from utils.git_utils import get_project_root_from_dir  # noqa: E402
from utils.provider_registry import get_provider, load_base_config  # noqa: E402
from utils.providers.base import Availability  # noqa: E402

# Template is resolved strictly relative to THIS file, never CWD / --project dir
# (both diverge from the install location). If this moves, update the Section 4
# packaging-guard test in tests/test_provider_registry.py to match.
TEMPLATE_PATH = Path(__file__).parent / "templates" / "config" / "providers.override.yaml"

CONFIG_DIRNAME = ".multi-llm"
CONFIG_FILENAME = "providers.yaml"
GITIGNORE_ENTRY = ".multi-llm/"

# Delimited region of the template that init regenerates. The header comments
# (and the MODE SHADOWING note) live OUTSIDE these markers and are copied verbatim,
# so a re-init never clobbers them. Keep in sync with the markers in
# templates/config/providers.override.yaml.
MARKER_START = "# <<< multi-llm:init-managed >>>"
MARKER_END = "# <<< /multi-llm:init-managed >>>"

# Signatures of a header authored BEFORE the providers-block filter removal, so a
# --force re-init can warn that the preserved outside-marker guidance is stale.
_STALE_HEADER_SIGNATURES = (
    "block here is IGNORED",
    "dropped with a warning",
    "dropped+warned",
)


def resolve_target_dir(requested: "str | None") -> Path:
    """Resolve the directory to scaffold into.

    Defaults to the git root; falls back to CWD (with a printed notice) outside a
    repo. An explicit --dir is honored verbatim.
    """
    if requested:
        return Path(requested).expanduser().resolve()

    root = get_project_root_from_dir(os.getcwd())
    if root:
        return Path(root)

    cwd = Path(os.getcwd()).resolve()
    print(
        f"NOTE: not inside a git repository — using the current directory: {cwd}\n"
        f"      (auto-discovery only finds the override inside a git repo; outside "
        f"one, point MULTI_LLM_PROVIDERS_CONFIG at it instead).",
        file=sys.stderr,
    )
    return cwd


def _gitignore_has_entry(gitignore_path: Path) -> bool:
    """Return True if .gitignore already ignores the .multi-llm/ directory."""
    if not gitignore_path.exists():
        return False
    target = GITIGNORE_ENTRY.strip().strip("/")
    for raw in gitignore_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lstrip("/").rstrip("/") == target:
            return True
    return False


def append_gitignore(target_dir: Path) -> "str | None":
    """Idempotently append the ignore entry to ``<target_dir>/.gitignore``.

    Creates the file if absent. Returns a message describing what happened, or
    None if no change was needed.
    """
    gitignore_path = target_dir / ".gitignore"
    if _gitignore_has_entry(gitignore_path):
        return None

    existing = ""
    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"

    block = "# multi-llm per-project config (developer-local, untracked)\n" + GITIGNORE_ENTRY + "\n"
    gitignore_path.write_text(existing + block, encoding="utf-8")
    return f"Added '{GITIGNORE_ENTRY}' to {gitignore_path}"


def _report_gitignore(args: argparse.Namespace, target_dir: Path) -> None:
    """Shared tracking-state messaging for the auto-config and template paths."""
    if args.gitignore:
        result = append_gitignore(target_dir)
        if result:
            print(result)
        else:
            print(f"'{GITIGNORE_ENTRY}' already present in .gitignore — no change.")
        print("This file is IGNORED by git (developer-local, untracked).")
    else:
        print(
            "This file is TRACKED by git by default — commit it for a team-wide, "
            "repo-standard selection.\n"
            "Re-run with --gitignore (or use MULTI_LLM_PROVIDERS_CONFIG for an "
            "out-of-tree path) to keep personal, per-developer preferences untracked."
        )


def _availability_rows(providers_cfg: dict) -> "list[tuple]":
    """``(name, AvailabilityReport)`` per base-config provider (M10, §5.1).

    The one walk both halves of this site read, so ``--init``'s selection and
    ``--init``'s annotation cannot disagree about the same CLI.

    No probe is run: ``--init`` is documented as making *no* subprocess calls,
    so no ``auth`` or ``version`` evidence is handed to
    :meth:`~utils.providers.base.LLMProvider.describe_availability` and every
    installed row comes back ``unknown`` rather than ``ready``. That is the
    fail-open posture, not a gap — claiming ``ready`` from a `shutil.which` is
    exactly the "installed is not authenticated" conflation M10 exists to end.
    """
    rows = []
    for name in providers_cfg:  # dict preserves base-config declaration order
        provider = get_provider(name)
        if provider is not None:
            rows.append((name, provider.describe_availability()))
    return rows


def _unusable_notices(detected: "list[str]") -> "list[str]":
    """Why a **detected** runner still is not usable, one line each (M10, §5.1).

    The status half of this site: a flat "Detected providers:" list means only
    "the binary resolves", and D3c's whole point is that installed is not
    authenticated. A row whose typed state is a *positive* negative verdict —
    ``needs-auth`` or ``version-too-low`` — says so here rather than letting the
    user discover it one dispatch at a time.

    ``binary-missing`` is deliberately **not** in that set: a row in ``detected``
    is by definition one whose binary resolved, so a ``binary-missing`` reading
    here would mean the PATH moved mid-run, and re-reporting it would contradict
    the list it annotates.

    It is empty today by construction, because the verdicts it renders come only
    from probes and ``--init`` runs none. It becomes live the moment a caller
    hands this site evidence; until then it prints nothing, and ``--init``'s
    output is byte-for-byte what it was.
    """
    lines = []
    for name in detected:
        provider = get_provider(name)
        if provider is None:
            continue
        report = provider.describe_availability()
        if report.state in (Availability.NEEDS_AUTH, Availability.VERSION_TOO_LOW):
            lines.append(f"{name}: {report.detail}")
    return lines


def _available_providers(providers_cfg: dict) -> "list[str]":
    """Base-config provider names whose CLI is installed, in declaration order.

    The **bool** half of M10's §5.1 split, and it stays a bool: this selects
    which providers ``--init`` uncomments. It is now derived from
    :func:`_availability_rows` so the selection is literally
    ``describe_availability().launchable`` — the same identity
    ``is_available()`` answers, from one walk instead of two.
    """
    return [name for name, report in _availability_rows(providers_cfg) if report.launchable]


# ---------------------------------------------------------------------------
# Template generator (drift guard)
# ---------------------------------------------------------------------------
#
# The shipped template is GENERATED from the base providers.yaml by
# build_template_text(): its commented `providers:` block and `defaults`
# candidate lists mirror the base config verbatim. A pytest parity test
# re-derives the template from the live base config and fails CI when the shipped
# file drifts (e.g. a new provider / changed model list never regenerated). To
# regenerate after a base edit:
#
#   python -c "import init_config as c; \\
#       c.TEMPLATE_PATH.write_text(c.build_template_text())"

# Outside-marker header prose (fixed; not derived from base).
_HEADER = """\
# .multi-llm/providers.yaml — per-project provider/model selection override
# =============================================================================
# This file is OPTIONAL. When absent, multi-llm uses its built-in defaults and
# behaves exactly as it would without it. It lets THIS repository pick which
# providers/models the multi-llm skill selects, without editing the installed
# plugin (which is global and gets clobbered on update).
#
# It lives at:   <git-root>/.multi-llm/providers.yaml
# Scaffold it:   use the `--init` flag (see `docs/configuration.md` in the
#                repository), or run init_config.py directly.
#
# ----------------------------------------------------------------------------
# HOW `--init` BUILDS THIS FILE (auto-detect, zero prompts)
# ----------------------------------------------------------------------------
# `--init` scans PATH for the supported provider CLIs and UNCOMMENTS the lines
# belonging to the ones it finds — the matching `providers:` sub-blocks, the
# `defaults.models` / `quick_models` entries for detected providers, and
# `default_provider`. Undetected providers stay commented. There are NO prompts
# and NO model-listing subprocess calls. Re-run `--init --force` to refresh the
# detection (e.g. after installing a CLI or updating the plugin).
#
# ----------------------------------------------------------------------------
# HOW MERGING WORKS (read this before editing)
# ----------------------------------------------------------------------------
# Your file is deep-merged ON TOP OF the built-in base config:
#   base providers.yaml  →  THIS file  →  MULTI_LLM_PROVIDERS_CONFIG (if set)
#
#  * Only set what you want to change. Everything you omit is INHERITED.
#  * LISTS REPLACE, THEY DO NOT APPEND. If you set `defaults.models`, you get
#    EXACTLY that list — the base list is discarded, not extended.
#  * Nested dicts (maps) deep-merge; only list/scalar VALUES replace wholesale.
#
# ----------------------------------------------------------------------------
# BLANK vs. CLEAR vs. OMIT (the three states of a key)
# ----------------------------------------------------------------------------
#  * OMIT a key entirely        → inherit the base value.
#  * Leave a key BLANK / null   → ALSO inherit the base value (a blank value is
#       e.g.  `models:`            skipped, NOT treated as "clear"). Uncommenting
#                                  a key but leaving it empty is therefore inert.
#  * Set an EXPLICIT EMPTY LIST  → deliberately WIPE OUT the inherited list.
#       e.g.  `quick_models: []`   `quick_models: []` means "use NO quick models
#                                  here" — under --quick that ERRORS; an empty
#                                  `defaults.models` falls back to interactive
#                                  selection (and fails in unattended runs).
#                                  `[]` is a FOOTGUN, not a no-op — use only when
#                                  you truly mean "none".
#
# You CANNOT unset an inherited SCALAR back to "absent": you can overwrite it
# with a new value, but `key:` (blank) just keeps the base. There is no deletion
# sentinel. Likewise you cannot PRUNE an inherited `defaults.modes.<mode>` entry
# (only overwrite its list, e.g. `<mode>: []`) — see the modes note below.
#
# ----------------------------------------------------------------------------
# TRUST MODEL — provider definitions DO merge, but no layer picks the binary
# ----------------------------------------------------------------------------
# An UNCOMMENTED `providers:` block here deep-merges OVER the base, exactly like
# the MULTI_LLM_PROVIDERS_CONFIG env layer: `default_timeout`, `max_concurrent`
# and each `models:` list all take effect (lists replace). Those are the only
# provider keys that DO anything — a key the base does not declare merges and is
# then ignored, so writing one is a no-op, not a setting.
#  * `models:` IS THE `--interactive` PICKER'S MENU, NOT AN ALLOWLIST: a model
#    named directly in `defaults.models` / `defaults.quick_models` /
#    `defaults.modes.<mode>` (or on `--models`) is DISPATCHED whether or not it
#    appears in this provider's `models:` list — pruning a model here only
#    removes it from the interactive picker.
# `--init` writes a full block for each detected provider so the file is a
# complete, self-describing snapshot.
#  * NO layer can choose the BINARY. Provider binaries are hardcoded in the
#    plugin (utils/providers/); a `command:` value in ANY layer merges as inert
#    metadata and can never make the tool run a different program. (The base
#    config no longer declares one — it had zero readers.)
#  * A provider name with no hardcoded adapter (e.g. one a newer plugin removed
#    or renamed) still merges but is IGNORED at runtime — it lists no models and
#    can never be selected.
#  * DRIFT: a copied block pins base's scalar/model values AT INIT TIME and the
#    SET of provider keys to whatever the plugin shipped then. Re-run
#    `--init --force` after a plugin update to refresh pinned metadata AND prune
#    providers the new base dropped.
#  * NO LAYER SETS ENVIRONMENT FOR A PROVIDER, so there is no `env:` key here —
#    not even a commented one. Endpoint/credential wiring (e.g. pointing
#    claude-code at GLM/Z.ai or at OpenRouter) is SHELL configuration this plugin
#    neither owns nor validates. An `env:` block written here would merge and
#    then be ignored — it would fail SILENTLY, which is worse than not existing.
#    The recipes live in `docs/providers.md` in the repository, under "Pointing a
#    provider CLI at a different endpoint".
#
# ----------------------------------------------------------------------------
# ONE OVERRIDE PER REPO
# ----------------------------------------------------------------------------
# Discovery anchors at the git ROOT, so a repository has exactly ONE
# .multi-llm/providers.yaml shared repo-wide. A monorepo CANNOT set per-package
# or per-subdirectory defaults via auto-discovery — use MULTI_LLM_PROVIDERS_CONFIG
# per-invocation for that. There are no per-plan or per-subdirectory overrides.
#
# ----------------------------------------------------------------------------
# MODE SHADOWING — these globals do NOT cover modes that set their own list
# ----------------------------------------------------------------------------
# The `default_provider` / `defaults.models` / `defaults.quick_models` in the
# managed block below are GLOBAL defaults. They apply to a mode (review-plan,
# code-review, review-tasks, ask) ONLY when that mode has no
# `defaults.modes.<mode>` entry here or in an inherited layer — a mode-specific
# list still WINS for that mode. `--init` sets only these globals; to change a
# specific mode, add a `defaults.modes.<mode>` block here yourself (see the modes
# example below).
# ============================================================================="""

# In-marker intro (## prose; the toggler never touches `## ` lines).
_MANAGED_INTRO = [
    "## Everything BETWEEN these two markers is the SELECTION block, REGENERATED on",
    "## every `--init --force` (it re-detects installed CLIs and re-uncomments their",
    "## lines). Everything OUTSIDE the markers — the comments above and below — is",
    "## preserved verbatim across a re-init; put any hand-maintained keys there.",
    "## Hand-edits INSIDE the markers are overwritten by the next `--init --force`.",
]

_PROVIDERS_COMMENTS = [
    "## --- providers --------------------------------------------------------------",
    "## Full provider definitions. `--init` uncomments the block for each DETECTED",
    "## CLI; an uncommented block deep-merges OVER the base (lists replace).",
    "## No key here picks a binary — provider binaries are hardcoded in the plugin.",
]

_DEFAULT_PROVIDER_COMMENTS = [
    "## --- default_provider -------------------------------------------------------",
    "## Provider used when a model spec has no `provider:` prefix (e.g. bare `opus`).",
    "## `--init` sets it to the first detected provider; left commented when nothing",
    "## is detected (inherits the base default).",
]

_DRIVER_COMMENTS = [
    "## --- driver -----------------------------------------------------------------",
    "## How `--exec-subagents` dispatches materialized subagent prompts. Only",
    "## consulted when the Python executor is the invoker — a host with native",
    "## subagents (Claude Code, Cursor) never reads these on a default run, because",
    "## the key configures the EXECUTOR's runner, not the session's model.",
    "## NOT written by `--init`: uncomment a line to override it. The block merges",
    "## key-by-key (set one field, inherit the rest), a BLANK value keeps the base,",
    "## and an unknown key under `driver:` is REJECTED at load time rather than",
    "## silently ignored. In a repo driven from several hosts, leaving",
    "## `subagent_runner` unset is the healthy arrangement: each host then resolves",
    "## its own CLI instead of one host's choice being pinned for all of them.",
    "## `verify_command` is the exception worth setting per project: it is THIS",
    "## repo's own check (`pnpm typecheck && pnpm lint:fix`, `cargo check`, `make",
    "## test`), run once after a code-editing phase applied its batches. Left unset",
    "## the phase says so in one line rather than completing unchecked; a non-zero",
    "## exit rolls nothing back and ends the phase at exit 3.",
]

_PROGRESS_COMMENTS = [
    "## --- progress ---------------------------------------------------------------",
    "## How often a running fan-out says it is still alive. TWO knobs, because one",
    "## interval cannot serve two cadences: `interval_s` is the `[PROGRESS]` ticker's",
    "## stdout cadence (priced in log readability — a print and nothing else),",
    "## while `poll_s` is the host's poll cadence and the resolved `--wait` default",
    "## (priced in TOOL TURNS, one per poll). The run's `.status.json` is a third",
    "## cadence and is deliberately not configurable.",
    "## NOT written by `--init`: uncomment a line to override it. `interval_s: 0` is",
    "## the documented disable form — it silences the ticker LINES only, and the",
    "## status file still records every transition. `poll_s` has no disable form (`0`",
    "## is rejected) and is clamped under the host's shell cap. `progress:` is a",
    "## CLOSED key set: an unknown key is REJECTED at load time rather than silently",
    "## keeping the shipped cadence.",
]

_DEFAULTS_COMMENTS = [
    "## --- defaults ---------------------------------------------------------------",
]

_MODELS_COMMENTS = [
    "  ## --- defaults.models ------------------------------------------------------",
    "  ## The model panel for normal (non-quick) runs. REPLACES the base list.",
    "  ## `--init` uncomments the candidates whose provider is detected; with none",
    "  ## uncommented the (blank) list inherits the base.",
]

_QUICK_COMMENTS = [
    "  ## --- defaults.quick_models ------------------------------------------------",
    "  ## Lightweight subset used with --quick / -q. REPLACES the base list. Same",
    "  ## uncommenting rule as defaults.models.",
]

_MODES_EXAMPLE = [
    "  ## --- defaults.modes -------------------------------------------------------",
    "  ## Per-mode overrides (NOT written by `--init`). A mode's `models` (and optional",
    "  ## `quick`) win over the globals above FOR THAT MODE. Authored with `##` so the",
    "  ## toggler never uncomments these example lines — copy one down by hand to use",
    "  ## it (and see the MODE SHADOWING note in the header).",
    "  ## modes:",
    "  ##   review-plan:",
    "  ##     models:",
    "  ##       - claude-code:opus",
    "  ##       - cursor-agent:gemini-3.1-pro",
    "  ##     quick:",
    "  ##       - claude-code:opus",
    "  ##   code-review:",
    "  ##     models:",
    "  ##       - cursor-agent:gpt-5.5-extra-high",
]


def _yaml_scalar(val) -> str:
    """Render a base scalar back to YAML text (bools lowercase, others str())."""
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val)


def _emit_providers_block(providers_cfg: dict) -> "list[str]":
    """Emit the base providers block as fully-commented YAML lines (`# ` prefix).

    Blank lines separate sub-blocks (mirrors base). Each provider's fields are
    emitted in base declaration order; the `models:` list is rendered as a nested
    sequence. The whole block is inert until init uncomments a detected provider.
    """
    out = ["# providers:"]
    first = True
    for name, cfg in providers_cfg.items():
        if not first:
            out.append("")  # blank separator between sub-blocks
        first = False
        out.append(f"#   {name}:")
        for key, val in (cfg or {}).items():
            if key == "models":
                out.append("#     models:")
                for model in (val or []):
                    out.append(f"#       - {model}")
            else:
                out.append(f"#     {key}: {_yaml_scalar(val)}")
    return out


def _emit_driver_block(driver_cfg: dict) -> "list[str]":
    """Emit the base ``driver:`` block as fully-commented YAML lines (`# ` prefix).

    Mirrors the live base values verbatim, so the CI byte-diff between this
    generator and the shipped template fails whenever a base ``driver:`` default
    changes without the template being regenerated — the same staleness guard the
    ``providers:`` block already carries. The stanza sits between the
    ``default_provider:`` and ``defaults:`` keys, where the auto-uncomment FSM's
    section is ``None``, so the toggler passes it through verbatim and a plain
    copy of the template stays inert.
    """
    out = ["# driver:"]
    for key, val in (driver_cfg or {}).items():
        if isinstance(val, dict):
            # `write_paths:` — a mapping of glob lists (D3l). Rendered nested so
            # uncommenting the stanza yields the same policy the base ships,
            # rather than a scalar a user has to reconstruct from the docs.
            out.append(f"#   {key}:")
            for sub_key, sub_val in val.items():
                if isinstance(sub_val, list):
                    out.append(f"#     {sub_key}:")
                    out.extend(f"#       - {_yaml_item(item)}" for item in sub_val)
                else:
                    out.append(f"#     {sub_key}: {_yaml_scalar(sub_val)}")
            continue
        rendered = "null" if val is None else _yaml_scalar(val)
        out.append(f"#   {key}: {rendered}")
    return out


def _emit_progress_block(progress_cfg: dict) -> "list[str]":
    """Emit the base ``progress:`` block as fully-commented YAML lines (`# ` prefix).

    Derived from the live base rather than hand-typed, for the reason
    :func:`_emit_driver_block` is: the CI byte-diff reds whenever a base cadence
    changes without the template being regenerated, so the shipped stanza cannot
    drift from the values it claims to mirror. Flat where the driver emitter has
    to descend into ``write_paths`` — both keys are plain scalars, and keeping it
    that way is the check that a nested one was never meant to be here. The
    stanza sits between the ``driver:`` and ``defaults:`` keys, where the
    auto-uncomment FSM's section is ``None``, so the toggler passes it through
    verbatim (nothing here is provider-detected) and a plain copy of the template
    stays inert.
    """
    out = ["# progress:"]
    for key, val in (progress_cfg or {}).items():
        rendered = "null" if val is None else _yaml_scalar(val)
        out.append(f"#   {key}: {rendered}")
    return out


def _yaml_item(val) -> str:
    """Render a list item, quoting the glob forms YAML would otherwise misread.

    A bare ``**`` or a leading ``*`` starts a YAML alias, so those items are
    single-quoted — matching how the base file spells them, which is what keeps
    the byte-diff parity test meaningful rather than merely passing.
    """
    text = _yaml_scalar(val)
    if text[:1] in ("*", "&", "!", "%", "@", "`", "?", "|", ">", "{", "[", "'", '"', "#"):
        return "'" + text.replace("'", "''") + "'"
    return text


def _emit_defaults_items(specs: "list[str]") -> "list[str]":
    """Emit `defaults.*` candidate specs as commented list items (`#     - spec`)."""
    return [f"#     - {spec}" for spec in specs]


def build_template_text(base_config: "dict | None" = None) -> str:
    """Build the full pristine template text from the base providers.yaml.

    The commented `providers:` block and the `defaults.models` / `quick_models`
    candidate lists mirror the live base config verbatim; everything else is
    fixed prose. A plain copy of the result is INERT (the providers block is
    commented; the `defaults` keys are live but blank → inherit base).
    """
    base = base_config if base_config is not None else load_base_config()
    providers_cfg = base.get("providers", {}) or {}
    defaults = base.get("defaults", {}) or {}
    d_models = defaults.get("models", []) or []
    d_quick = defaults.get("quick_models", []) or []
    default_provider = base.get("default_provider", "cursor-agent")

    lines: "list[str]" = []
    lines.append(_HEADER)
    lines.append("")
    lines.append("")
    lines.append(MARKER_START)
    lines.extend(_MANAGED_INTRO)
    lines.append("")
    lines.extend(_PROVIDERS_COMMENTS)
    lines.extend(_emit_providers_block(providers_cfg))
    lines.append("")
    lines.extend(_DEFAULT_PROVIDER_COMMENTS)
    lines.append(f"# default_provider: {default_provider}")
    lines.append("")
    lines.extend(_DRIVER_COMMENTS)
    lines.extend(_emit_driver_block(base.get("driver", {}) or {}))
    lines.append("")
    lines.extend(_PROGRESS_COMMENTS)
    lines.extend(_emit_progress_block(base.get("progress", {}) or {}))
    lines.append("")
    lines.append("")
    lines.extend(_DEFAULTS_COMMENTS)
    lines.append("defaults:")
    lines.append("")
    lines.extend(_MODELS_COMMENTS)
    lines.append("  models:")
    lines.extend(_emit_defaults_items(d_models))
    lines.append("")
    lines.extend(_QUICK_COMMENTS)
    lines.append("  quick_models:")
    lines.extend(_emit_defaults_items(d_quick))
    lines.append("")
    lines.extend(_MODES_EXAMPLE)
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# The toggler — uncomment the lines belonging to detected providers
# ---------------------------------------------------------------------------

# Top-level key transitions (tested BEFORE the section dispatch; see auto_uncomment).
_RE_DEFAULT_PROVIDER = re.compile(r"^#?\s*default_provider:")
_RE_DEFAULTS = re.compile(r"^#?\s*defaults:\s*$")
_RE_PROVIDERS = re.compile(r"^#?\s*providers:\s*$")
# A commented provider-key line: `#` + the 3 spaces a 2-indent key gains under `# `.
_RE_PROVIDER_KEY = re.compile(r"^#\s{3}(?P<name>[a-z0-9-]+):\s*$")
# An UNCOMMENTED defaults sub-key (arms the items pass for that key).
_RE_DEFAULTS_KEY = re.compile(r"^(?P<indent>\s*)(?P<key>models|quick_models):\s*$")
# A commented `defaults.*` candidate item.
_RE_DEFAULTS_ITEM = re.compile(r"^#(?P<indent>\s*)-\s*(?P<spec>\S+)")


def _uncomment(line: str) -> str:
    """Strip exactly the leading `# ` (hash + one space); a no-op otherwise.

    Safe on `## ` prose (starts `##`, not `# `), bare `#`, and blank lines — none
    begin with hash-space — so the toggler can call it on any classified line.
    """
    return line[2:] if line.startswith("# ") else line


def _render_default_provider(line: str, detected, order: "list[str]") -> str:
    """Rewrite the `default_provider:` line to the first detected provider.

    Leaves the line commented (verbatim) when nothing is detected so the base
    default is inherited.
    """
    chosen = next((p for p in order if p in detected), None)
    if chosen is None:
        return line
    return f"default_provider: {chosen}"


def _toggle_template(template_body: str, detected, order: "list[str]"):
    """Toggle the managed template body for ``detected`` providers.

    Returns ``(text, models_specs, quick_specs)`` where the spec lists are the
    ``defaults.models`` / ``quick_models`` entries the pass uncommented (used by
    the D2a guard and the post-write recheck). A single linear finite-state scan:
    the three top-level keys (`providers:` / `default_provider:` / `defaults:`)
    drive the section, and each resets ``cur_provider`` so a detected provider's
    toggle state never bleeds across a section boundary.
    """
    out: "list[str]" = []
    section = None          # None | "providers" | "defaults"
    cur_provider = None
    armed_key = None        # None | "models" | "quick_models" (defaults pass)
    models_specs: "list[str]" = []
    quick_specs: "list[str]" = []

    for line in template_body.splitlines():
        # default_provider: is a top-level key that ENDS the providers sub-block;
        # it MUST be matched before the section dispatch (see plan: the FSM hoist).
        if _RE_DEFAULT_PROVIDER.match(line):
            section, cur_provider, armed_key = None, None, None
            out.append(_render_default_provider(line, detected, order))
            continue
        if _RE_DEFAULTS.match(line):
            section, cur_provider, armed_key = "defaults", None, None
            out.append(line)
            continue
        if _RE_PROVIDERS.match(line):
            section, cur_provider, armed_key = "providers", None, None
            out.append(_uncomment(line) if detected else line)
            continue

        if section == "providers":
            key_match = _RE_PROVIDER_KEY.match(line)
            if key_match:
                cur_provider = key_match.group("name")
                out.append(_uncomment(line) if cur_provider in detected else line)
            elif cur_provider in detected:
                out.append(_uncomment(line))
            else:
                out.append(line)
            continue

        if section == "defaults":
            key_match = _RE_DEFAULTS_KEY.match(line)
            if key_match:
                armed_key = key_match.group("key")
                out.append(line)
                continue
            item_match = _RE_DEFAULTS_ITEM.match(line)
            if item_match and armed_key:
                spec = item_match.group("spec")
                provider = spec.split(":", 1)[0]
                if provider in detected:
                    out.append(_uncomment(line))
                    (models_specs if armed_key == "models" else quick_specs).append(spec)
                else:
                    out.append(line)
                continue
            # Neither an arming key nor an armed item: blank lines keep the armed
            # state; anything else (prose, the `## modes:` example) disarms it.
            if line.strip() != "":
                armed_key = None
            out.append(line)
            continue

        out.append(line)  # section is None → verbatim (header / prose / blank)

    return "\n".join(out), models_specs, quick_specs


def auto_uncomment(template_body: str, detected, order: "list[str]") -> str:
    """Toggle ``template_body`` for ``detected`` providers (text only).

    Thin wrapper over :func:`_toggle_template` for callers/tests that only want
    the toggled text. ``detected`` is the set of installed provider names;
    ``order`` is the base-config declaration order (drives ``default_provider``).
    """
    return _toggle_template(template_body, detected, order)[0]


# ---------------------------------------------------------------------------
# D2a guard — keep the panels runnable when detected providers aren't curated
# ---------------------------------------------------------------------------


def _inject_under_key(body: str, key: str, specs: "list[str]") -> str:
    """Splice ``- spec`` lines directly beneath the uncommented ``key:`` line.

    Anchors on the live `^(indent)key:$` line (the toggler leaves the defaults
    sub-keys uncommented) and inserts at the key's indent + 2 spaces — the same
    indent as the template's candidate items.

    The match is SCOPED to the ``defaults:`` section. Otherwise the bare
    `^(indent)key:$` pattern would also match the 4-space ``models:`` key inside
    each DETECTED provider's now-uncommented ``providers:`` sub-block — and since
    D2a fires precisely on a gemini/opencode-only machine (whose blocks are
    uncommented), the injected ``provider:model`` specs would be spliced as bare
    ids into those provider catalogs, corrupting them. Tracking the section so the
    same FSM transitions as ``_toggle_template`` keeps injection to defaults only.
    """
    pattern = re.compile(rf"^(?P<indent>\s*){re.escape(key)}:\s*$")
    out: "list[str]" = []
    in_defaults = False
    for line in body.splitlines():
        if _RE_DEFAULTS.match(line):
            in_defaults = True
        elif _RE_PROVIDERS.match(line) or _RE_DEFAULT_PROVIDER.match(line):
            in_defaults = False
        out.append(line)
        if not in_defaults:
            continue
        match = pattern.match(line)
        if match:
            child_indent = match.group("indent") + "  "
            for spec in specs:
                out.append(f"{child_indent}- {spec}")
    return "\n".join(out)


def _apply_d2a_guard(body, detected_list, models_specs, quick_specs, base_config):
    """Ensure ``defaults.models`` / ``quick_models`` are runnable despite detection.

    The base default panel omits some providers (gemini/cline), so a machine
    whose only detected providers are uncovered uncomments ZERO entries → the
    list would inherit base (which references uninstalled providers). When that
    happens for ≥1 detected provider, inject each detected provider's first base
    catalog model into ``defaults.models`` (and the first detected provider's
    first model into ``quick_models``) and return a notice.

    Returns ``(body, expected_models, notices)`` where ``expected_models`` is the
    final resolved ``defaults.models`` list (uncommented + injected), used by the
    post-write recheck.
    """
    notices: "list[str]" = []
    expected_models = list(models_specs)
    if not detected_list:
        return body, expected_models, notices

    providers_cfg = base_config.get("providers", {}) or {}

    def first_model(provider: str) -> "str | None":
        models = providers_cfg.get(provider, {}).get("models", []) or []
        return models[0] if models else None

    if not models_specs:
        specs = [f"{p}:{m}" for p in detected_list if (m := first_model(p))]
        if specs:
            body = _inject_under_key(body, "models", specs)
            expected_models = specs
            names = ", ".join(detected_list)
            notices.append(
                f"NOTE: detected provider(s) {{{names}}} are not in the base default "
                f"panel; injected their first model into defaults.models so the "
                f"config is runnable — edit as desired."
            )

    if not quick_specs:
        first = detected_list[0]
        model = first_model(first)
        if model:
            body = _inject_under_key(body, "quick_models", [f"{first}:{model}"])
            notices.append(
                f"NOTE: injected {first}:{model} into defaults.quick_models so "
                f"`--quick` is runnable — edit as desired."
            )

    return body, expected_models, notices


# ---------------------------------------------------------------------------
# Splice / validate / write
# ---------------------------------------------------------------------------


def _extract_managed_body(template_text: str) -> str:
    """Return the text BETWEEN the managed markers (exclusive of the marker lines)."""
    start = template_text.find(MARKER_START)
    end = template_text.find(MARKER_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("init-managed markers missing or misordered in template")
    start_line_end = template_text.find("\n", start) + 1
    return template_text[start_line_end:end]


def splice_managed_block(template_text: str, managed_body: str) -> str:
    """Replace the delimited region of ``template_text`` with ``managed_body``.

    Header comments (and the MODE SHADOWING note) outside the markers are kept
    verbatim. Raises ValueError if the markers are missing/misordered so a corrupt
    template fails loudly rather than silently producing a stub.
    """
    start = template_text.find(MARKER_START)
    end = template_text.find(MARKER_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("init-managed markers missing or misordered in template")
    start_line_end = template_text.find("\n", start) + 1
    before = template_text[:start_line_end]
    after = template_text[end:]
    notice = (
        "# Written by `multi-llm --init` (auto-detect). This block is REGENERATED on\n"
        "# every `--init --force` — it re-detects the installed CLIs and re-uncomments\n"
        "# their lines. Put any hand-maintained keys OUTSIDE the markers.\n"
        "#\n"
        "# These are GLOBAL selection defaults; a `defaults.modes.<mode>` entry (if\n"
        "# any) still wins for that mode. See the MODE SHADOWING note above.\n"
    )
    return before + notice + managed_body + "\n" + after


def _validate_generated_config(text: str, detected, base_config: dict) -> "str | None":
    """Pre-write gate over the generated config. Returns an error string or None.

    Stronger than a bare parse check: after text toggling + D2a injection + live
    `providers:` merging, assert only known provider names appear, each provider
    block is a mapping with sane timeout/concurrency, every `defaults.*` entry is
    a string, `default_provider` resolves to a detected provider when detection is
    non-empty, and the D2a invariant holds (the panels are non-empty whenever ≥1
    provider was detected). Aborts the write on any failure.
    """
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return f"generated YAML does not parse: {e}"
    if not isinstance(parsed, dict):
        return "generated YAML is not a top-level mapping"
    if "defaults" not in parsed:
        return "generated YAML is missing the 'defaults' section"

    known = set(base_config.get("providers", {}) or {})

    providers_block = parsed.get("providers")
    if providers_block is not None:
        if not isinstance(providers_block, dict):
            return "generated 'providers' is not a mapping"
        for name, pcfg in providers_block.items():
            if name not in known:
                return f"generated 'providers' has an unknown provider '{name}'"
            if not isinstance(pcfg, dict):
                return f"generated provider '{name}' is not a mapping"
            for tkey in ("default_timeout", "max_concurrent"):
                if tkey in pcfg:
                    val = pcfg[tkey]
                    if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
                        return f"generated provider '{name}' has an invalid {tkey}: {val!r}"

    defaults = parsed.get("defaults") or {}
    if not isinstance(defaults, dict):
        return "generated 'defaults' is not a mapping"
    for list_key in ("models", "quick_models"):
        vals = defaults.get(list_key)
        if vals is None:
            continue
        if not isinstance(vals, list):
            return f"generated defaults.{list_key} is not a list"
        for spec in vals:
            if not isinstance(spec, str):
                return f"generated defaults.{list_key} has a non-string entry: {spec!r}"
            provider = spec.split(":", 1)[0]
            if provider not in known:
                return (
                    f"generated defaults.{list_key} references an unknown provider "
                    f"'{provider}'"
                )

    if detected:
        dp = parsed.get("default_provider")
        if dp is None:
            return "default_provider is missing despite detected providers"
        if dp not in detected:
            return f"default_provider '{dp}' is not a detected provider"
        for list_key in ("models", "quick_models"):
            if not (defaults.get(list_key) or []):
                return f"defaults.{list_key} is empty despite detected providers"

    return None


def _recheck_merged(target_dir: Path, expected_models: "list[str]", config_path: Path) -> None:
    """Post-write best-effort reload: confirm the chosen specs actually resolve.

    Reloads the now-written file through ``load_config`` against a **fresh cache**
    (defeating the per-process memoization that would otherwise serve a stale
    pre-write config). When ``target_dir`` is a git root the file is discovered and
    its merged ``defaults.models`` should equal the chosen specs; a mismatch means
    a higher-precedence ``MULTI_LLM_PROVIDERS_CONFIG`` env override is shadowing it,
    which is worth a warning (the file is still valid and written). Never raises.

    Config discovery anchors on the **git root**, not ``target_dir``. When the
    written file is NOT the file discovery would pick up (the ``--dir <subdir>``
    case, or the outside-a-repo CWD fallback), the merged ``defaults.models`` falls
    back to the base catalog and would never equal the chosen specs — a mismatch
    that has nothing to do with an env override. So the shadowing warning only
    fires when the discovered project-config path is exactly the file we wrote.
    """
    try:
        import utils.provider_registry as registry

        registry._config = None
        registry._config_key = None
        merged = registry.load_config(anchor=str(target_dir))
        discovered = registry._find_project_config(anchor=str(target_dir))
        registry._config = None
        registry._config_key = None
        # Only diagnose shadowing when the written file is the one discovery picks
        # up; otherwise 'resolved' is the base catalog, not our file, and the
        # mismatch would misattribute an env override that may not exist.
        if discovered is None or discovered.resolve() != config_path.resolve():
            return
        resolved = list((merged.get("defaults", {}) or {}).get("models", []) or [])
        # Compare unconditionally: an env override that resolves defaults.models to
        # [] still shadows the chosen specs, so the empty-list case must warn too
        # (a truthiness guard would silently accept it).
        if resolved != list(expected_models):
            print(
                "WARNING: a higher-precedence override (e.g. MULTI_LLM_PROVIDERS_CONFIG) "
                "shadows the written defaults.models at runtime:\n"
                f"         resolved={resolved}\n"
                f"         written={expected_models}",
                file=sys.stderr,
            )
    except Exception as e:  # never let the recheck crash a completed init
        print(f"NOTE: skipped post-write config recheck ({e}).", file=sys.stderr)


def _splice_source(config_path: Path) -> str:
    """Pick the text to splice the managed block into (outside-marker preservation).

    The template contract (see templates/config/providers.override.yaml) promises
    that everything OUTSIDE the markers — hand-maintained keys, comments — survives a
    re-init. To honor that, a re-init over an existing config splices into the
    EXISTING file when it already carries both markers, preserving its
    outside-the-region content verbatim. The bundled template is used only for a
    first-time write (file absent) or a degraded/legacy file missing the markers
    (where there is no managed region to preserve and we reset to the stub).

    The managed BODY is always toggled from the pristine template regardless; this
    only chooses where the toggled body is spliced.
    """
    if config_path.exists():
        try:
            existing = config_path.read_text(encoding="utf-8")
        except OSError:
            existing = None
        if existing is not None and MARKER_START in existing and MARKER_END in existing:
            return existing
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _warn_stale_header(config_path: Path) -> None:
    """Warn when a --force re-init preserves a pre-filter-removal header."""
    if not config_path.exists():
        return
    try:
        existing = config_path.read_text(encoding="utf-8")
    except OSError:
        return
    if any(sig in existing for sig in _STALE_HEADER_SIGNATURES):
        print(
            "WARNING: this config's header predates the providers-block change; its "
            "guidance is stale — re-init into a fresh file or refresh the header.",
            file=sys.stderr,
        )


def _backup_existing_config(config_path: Path, new_text: str) -> "Path | None":
    """Copy an existing, about-to-be-overwritten config aside before writing.

    The backup lands next to the original as ``providers.yaml.bak.<timestamp>``
    (a ``-N`` suffix disambiguates same-second collisions). Skipped when the
    existing content is byte-identical to ``new_text`` — nothing would be lost,
    and repeated ``--force`` re-runs shouldn't accumulate identical backups.
    Returns the backup path, or None when no backup was made. A failing copy
    raises: refusing to overwrite what we could not back up beats losing it.
    """
    if not config_path.exists():
        return None
    try:
        if config_path.read_text(encoding="utf-8") == new_text:
            return None
    except OSError:
        pass  # unreadable text is still worth a byte-level copy attempt
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = config_path.with_name(f"{config_path.name}.bak.{stamp}")
    counter = 1
    while backup_path.exists():
        backup_path = config_path.with_name(f"{config_path.name}.bak.{stamp}-{counter}")
        counter += 1
    shutil.copy2(config_path, backup_path)
    return backup_path


def _report_backup(backup_path: "Path | None") -> None:
    """Tell the user where their previous config went (no-op without a backup)."""
    if backup_path is None:
        return
    print(
        f"Backed up the previous config to {backup_path}\n"
        f"  Your old settings are preserved there — port anything custom into the "
        f"new file, then delete the backup."
    )


def _write_config(
    args: argparse.Namespace,
    target_dir: Path,
    config_dir: Path,
    config_path: Path,
    detected_list: "list[str]",
    text: str,
    expected_models: "list[str]",
    notices: "list[str]",
) -> int:
    """Validate, write, recheck, and report the auto-detected config."""
    detected = set(detected_list)
    error = _validate_generated_config(text, detected, load_base_config())
    if error:
        print(f"ERROR: refusing to write an invalid config — {error}", file=sys.stderr)
        return 1

    backup_path = _backup_existing_config(config_path, text)
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(text, encoding="utf-8")

    # Post-write recheck only when something was detected; the inert (nothing
    # detected) file writes a blank defaults.models → inherits base, so comparing
    # the resolved base list against the empty uncommented set would false-warn.
    if detected:
        _recheck_merged(target_dir, expected_models, config_path)

    print(f"Wrote {config_path}")
    _report_backup(backup_path)
    if not detected_list:
        print(
            "No supported provider CLIs found on PATH; wrote an inert "
            ".multi-llm/providers.yaml that inherits the built-in defaults.\n"
            "Install one of: claude, cursor-agent, gemini, grok, opencode, "
            "codex, kilocode, kimi, qwen, copilot, cline, goose, aider, agy, pi, muse, "
            "vibe, omp, fx and "
            "re-run `--init`."
        )
    else:
        chosen = detected_list[0]  # validation guarantees default_provider == this
        # default_provider is the first DETECTED in base order; detected_list is
        # already in base declaration order, so its head is that provider.
        print(f"  Detected providers: {', '.join(detected_list)}")
        # M10 (§5.1) — the status half. "Detected" only ever meant "the binary
        # resolves"; a row that is installed and still not usable now says why.
        for line in _unusable_notices(detected_list):
            print(f"  Not usable — {line}")
        print(f"  default_provider: {chosen}")
        print(f"  defaults.models: {len(expected_models)} model(s)")
        print(
            "  (Validated: the file parses and its defaults.models resolve via "
            "load_config.)\n"
            "  These globals apply only to modes WITHOUT their own "
            "defaults.modes.<mode> list.\n"
            f"  Smoke-test it, e.g.:  {_smoke_test_command(args)}"
        )
        for notice in notices:
            print(notice)
        for line in _runner_warning_lines(args, target_dir):
            print(line)
    _report_gitignore(args, target_dir)
    return 0


def _runner_warning_lines(args: argparse.Namespace, target_dir: Path) -> "list[str]":
    """The ``[RUNNER_WARNING]`` line when ``implement`` / ``apply-code-fixes``
    would be refused for the runner the config just written resolves to
    (racing-run issue #1, 2026-10-02): the dispatch's own decision
    (``subagent_executor.repo_wide_write_refusal``, the model-free probes once),
    resolved for the host ``init`` ran from, so a Codex user learns at init
    and not at phase 6. Empty when the runner would run, or for a runner with
    no sandbox probe. Advisory: any failure prints nothing."""
    try:
        from utils import host_capabilities, next_phase
        from utils import provider_registry
        from utils.provider_registry import resolve_subagent_runner
        from utils.subagent_executor import repo_wide_write_refusal
        import check_workflow_prerequisites as prereq

        host_id = host_capabilities.resolve_host_id(explicit=getattr(args, "host", None))
        # The config this init just wrote, not whatever an earlier read cached.
        provider_registry._config = None
        provider_registry._config_key = None
        spec, _layer = resolve_subagent_runner("full", anchor=str(target_dir), host_id=host_id)
        refusal = repo_wide_write_refusal(spec, anchor=str(target_dir))
    except Exception:  # noqa: BLE001 - advisory, never a failed init
        return []
    if refusal is None:
        return []
    return [f"{next_phase.RUNNER_WARNING_MARKER} {prereq.render_repo_wide_warning(spec, refusal)}"]


#: What `init` suggests the user type to prove the config works; the host's own
#: invocation spelling is put in front of it.
SMOKE_TEST_ARGS = "--review-plan <plan> --quick"


def _smoke_test_command(args: argparse.Namespace) -> str:
    """The smoke-test command in the spelling of the route `init` was invoked from.

    Hard-coded as `/multi-llm:multi-llm ...` until 2026-10-02, which is a command
    Codex and OpenCode users cannot type (issue #12). The host is the run's
    ``--host`` (the tool routes bake it in) and the route is
    ``next_phase.resolve_route``'s, so this is the same string the next-phase
    block prints for that route (``hosts/capabilities.yaml``, ``next_command``).
    A host or route the capability data does not know falls back to the
    reference host's plugin spelling rather than failing a finished init.
    """
    from utils import host_capabilities, next_phase

    try:
        host_id = host_capabilities.resolve_host_id(explicit=getattr(args, "host", None))
        route = next_phase.resolve_route(host_id)
        template = host_capabilities.next_command_template(host_id, route)
    except (KeyError, ValueError):
        template = host_capabilities.next_command_template(
            host_capabilities.DEFAULT_HOST, None
        )
    return template.replace(next_phase.ARGS_SLOT, SMOKE_TEST_ARGS)


def run_auto_init(args: argparse.Namespace, target_dir: Path, config_dir: Path,
                  config_path: Path) -> int:
    """Detect installed CLIs and write a preconfigured override (zero prompts)."""
    base = load_base_config()
    providers_cfg = base.get("providers", {}) or {}
    order = list(providers_cfg)
    detected_list = _available_providers(providers_cfg)
    detected = set(detected_list)

    _warn_stale_header(config_path)

    # Always regenerate the managed region from the PRISTINE template; splice into
    # the existing file (when marked) only to preserve its outside-marker content.
    splice_target = _splice_source(config_path)
    body = _extract_managed_body(TEMPLATE_PATH.read_text(encoding="utf-8"))
    toggled, models_specs, quick_specs = _toggle_template(body, detected, order)
    toggled, expected_models, notices = _apply_d2a_guard(
        toggled, detected_list, models_specs, quick_specs, base
    )
    text = splice_managed_block(splice_target, toggled)

    return _write_config(
        args, target_dir, config_dir, config_path,
        detected_list, text, expected_models, notices,
    )


def write_template_only(args: argparse.Namespace, target_dir: Path, config_dir: Path,
                        config_path: Path) -> int:
    """Copy the pristine inert template verbatim (skip detection)."""
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    backup_path = _backup_existing_config(config_path, template_text)
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(template_text, encoding="utf-8")
    print(f"Wrote {config_path}")
    _report_backup(backup_path)
    _report_gitignore(args, target_dir)
    return 0


def main(argv: "list[str] | None" = None) -> int:
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        prog="init_config.py",
        description=(
            "Set up a per-project multi-llm config override at "
            "<dir>/.multi-llm/providers.yaml. Auto-detects which provider CLIs are "
            "installed and uncomments their lines in an inert template — fully "
            "automatic, zero prompts, no model-listing subprocess calls."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[build_parent_parser()],
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        default=None,
        help="Target directory (defaults to the git root; falls back to CWD outside a repo).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite an existing .multi-llm/providers.yaml (refuses by default). "
            "The previous file is first backed up alongside as "
            "providers.yaml.bak.<timestamp> and the backup path is printed."
        ),
    )
    parser.add_argument(
        "--gitignore",
        action="store_true",
        help=(
            "Also append '.multi-llm/' to the repo's .gitignore (idempotent) so the "
            "override stays a developer-local, untracked file. Default: leave it trackable."
        ),
    )
    parser.add_argument(
        "--template-only",
        action="store_true",
        help="Skip detection; write the pristine inert template stub verbatim.",
    )
    args = parser.parse_args(argv)

    target_dir = resolve_target_dir(args.dir)
    config_dir = target_dir / CONFIG_DIRNAME
    config_path = config_dir / CONFIG_FILENAME

    if not TEMPLATE_PATH.exists():
        print(
            f"ERROR: config template not found at {TEMPLATE_PATH}\n"
            f"       The plugin install looks corrupt or partial; reinstall the skill.",
            file=sys.stderr,
        )
        return 1

    if config_path.exists() and not args.force:
        print(
            f"ERROR: {config_path} already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    if args.template_only:
        return write_template_only(args, target_dir, config_dir, config_path)
    return run_auto_init(args, target_dir, config_dir, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
