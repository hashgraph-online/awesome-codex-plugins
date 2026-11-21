#!/usr/bin/env python3
"""``install-host`` / ``uninstall-host`` — the D7 install contract.

One file is written per invocation, and the rules for that write are the whole
design; every lifecycle question (upgrade, relocate, repair, uninstall) is a
consequence of them.

* **Always a rendered copy — never a symlink, junction or hardlink.** The
  installed artifact is *output*: ``hosts/<host>/shim.md.tmpl`` still carries an
  unexpanded ``{SKILL_DIR}`` and unfilled slots, so a link would install a
  template no host can run. It also takes symlink privileges out of the Windows
  story entirely (D7c) — nothing here needs elevation or Developer Mode.
* **The baked absolute prefix is the one staleness we can *check*.** The Claude
  plugin cache is keyed by commit hash, so the skill dir moves on every plugin
  update (D1c). An env var, a stable symlink or a shim-relative path each trade a
  checkable staleness for an unchecked one; a literal absolute path in a known
  slot can be compared against the running skill dir, which is what turns a moved
  skill dir into ``--check`` row 2 — a named failure with a one-line repair —
  instead of a ``No such file or directory`` surfacing from inside ``uv``.
* **The write is atomic and reversible.** Render into a temp file *in the target
  directory*, ``fsync``, ``os.replace``. An existing shim's bytes are read into
  memory first; a failure after the replace restores them exactly, and a
  first-time install rolls back by deleting what it wrote. Nothing is left behind
  on success — no ``.bak`` litter, no temp file.
* **An install ends with verification, not with the write.** After the replace the
  same ``--check`` runs inline. A shim whose *bytes* do not verify (rows 1-4) is a
  failed install and is rolled back; a byte-correct shim whose *environment* is
  not ready (row 5: uv, the runner CLI) is reported with exit 3 and **kept**,
  because deleting a correct file cannot make a missing CLI appear and the user's
  next step is to install that CLI, not to re-render.
* **Local edits are detected, never silently overwritten.** Every rendered shim
  carries a ``multi_llm_shim`` header (host id, ``shim_version``, template hash,
  hash of the body as written) in the file's own comment syntax. On re-install the
  body is re-hashed: an unchanged hash is a routine re-render, a changed one means
  the user edited the installed shim and the install stops with exit 3 naming the
  path and the two ways forward.

**No per-host branch exists in this module.** Paths, scopes, precedence, the
reload requirement, the shim's format and the verb sentences are all read from
``hosts/capabilities.yaml``; if a host needs something this code cannot express,
the missing information belongs in that data file.

``link-skill.sh``/``sync-skill.sh`` are Claude-Code-only dev tooling and
deliberately **not** an install backend: neither writes a shim, neither knows about
``--host``, and one of them collides with the installed plugin. ``install-host
claude-code`` is ``--check``-only (D5c): that host's shim is the plugin's own
``SKILL.md``, which the host itself resolves.
"""

from __future__ import annotations

if __name__ == "__main__" and not __package__:
    # Run by path: put the skill root on sys.path, found from this file's real
    # location as Python finds sys.path[0], then call the package module's entry
    # point with sys.argv untouched, so the program name stays the one typed
    # (docs/development/dispatcher.md#import-safety).
    import os
    import sys

    _UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path[:] = [os.path.dirname(_UTILS_DIR)] + [
        p for p in sys.path if os.path.realpath(p) != _UTILS_DIR]
    from utils.host_install import main

    raise SystemExit(main(sys.argv[1:]))

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import host_capabilities as caps
from .atomic_io import atomic_write_bytes as _atomic_write_bytes
from .cli_common import (
    EXIT_NEEDS_HUMAN,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    dispatcher_prefix,
    record_artifact,
    skill_dir,
)
from .stream_bootstrap import bootstrap_streams
from .unattended import find_uv, uv_missing_text


# The shim's paths, text and package routes live in their own modules; every
# name stays importable from here, the installer's public surface.
from .host_paths import (  # noqa: F401
    Refused,
    SCOPE_PROJECT,
    SCOPE_GLOBAL,
    SCOPE_LEGACY,
    WRITABLE_SCOPES,
    DEFAULT_SCOPE,
    _HOME_TOKENS,
    _XDG_TOKENS,
    _ABSOLUTE_RE,
    user_home,
    expand_path_tokens,
    checked_entry,
    _join,
    Location,
    shim_filename,
    locations,
    _is_user_rooted,
    target_location,
    existing_copies,
)
from .host_shim import (  # noqa: F401
    SHIM_VERSION,
    HEADER_KEY,
    _HEADER_SYNTAX,
    _HEADER_RE,
    SLOT_UV_MISSING_TEXT,
    SLOT_UV_MISSING_FILE,
    _SLOT_RE,
    _UV_RUN_FLAGS_RE,
    _BAKED_PREFIX_QUOTED_RE,
    _BAKED_PREFIX_BARE_RE,
    FORBIDDEN_IN_INSTALLED,
    _HOST_EXPANDED_PLACEHOLDER,
    UV_MISSING_RELATIVE,
    SNIPPET_DIR,
    _MAX_SNIPPET_DEPTH,
    PLUGIN_SKILL_DESCRIPTION_MAX,
    template_path,
    snippets,
    render,
    baked_prefix,
    _sha256,
    body_of,
    parse_header,
    _header_line,
    with_header,
    _template_sha,
    render_installed,
    local_edit,
    _is_pristine_shim,
)
from .host_routes import (  # noqa: F401
    PackageRoute,
    _NOTE_FORMS,
)
from .host_routes.npm import (  # noqa: F401
    _package_name,
    _config_dirs,
    _config_env_names,
    _project_config_dirs,
    _config_files,
    _cache_root,
    _npm_payload_path,
    _PAYLOAD_PROBES,
    _npm_route,
    _declared_spec,
)
from .host_routes.codex import (  # noqa: F401
    CODEX_SERVER_MIN_PYTHON,
    CODEX_LIST_TIMEOUT_S,
    _CODEX_PAYLOAD_MARKERS,
    codex_home,
    _codex_payload_dir,
    _codex_payload_answers,
    _codex_plugin_list,
    _strip_toml_comment,
    _TOML_ENABLED_KEY_RE,
    _TOML_ENABLED_RE,
    _TOML_TOP_LEVEL_PLUGINS_RE,
    _is_plugins_family_header,
    _Abstain,
    _scan_codex_config,
    _codex_route,
    _with_enabled,
    _with_siblings,
    _python3_problem,
    _codex_note,
)


# ---------------------------------------------------------------------------
# Package routes: which resolver answers for a host, and what --check says
# ---------------------------------------------------------------------------

def package_route(
    host_id: str,
    *,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> Optional[PackageRoute]:
    """Is a package route installed? Dispatched on ``package.registry``.

    Each registry has its own resolver in :data:`_ROUTE_RESOLVERS`, because
    what counts as *evidence of an install* is registry-shaped: a spec listed in
    a JSON config on npm, a ``codex plugin list`` entry or a ``config.toml``
    table on the codex marketplace. Neither resolver bends the other's helpers.
    """
    entry = caps.entry(host_id, base)
    package = entry.get("package")
    if not package:
        return None
    registry = package["registry"]
    resolver = _ROUTE_RESOLVERS.get(registry)
    if resolver is None:
        # **Refuse rather than probe nothing.** A missing resolver used to mean
        # `payload=None` and `resolved=False` — which reads out as row 1 FAILing
        # with "no payload resolved at None" and a repair line telling the user
        # to reconnect to a network or delete an entry that is, in fact, exactly
        # right. A correctly installed route mislabelled as broken is the one
        # answer this probe must never give, so the gap is reported as ours.
        # `render_capabilities._package_section` refuses the same way.
        raise Refused(
            f"ERROR: host '{host_id}' declares package registry '{registry}', "
            "which this route probe has no resolver for.\n"
            "       Add a row to _ROUTE_RESOLVERS in host_install.py rather than "
            "letting `--check` report an installed route as unresolved."
        )
    return resolver(host_id, entry, package, env=env, project_root=project_root)


#: One resolver per registry. Keyed on the ``package.registry`` discriminator,
#: so a second host on a known registry needs no code and a new registry is one
#: row — and :func:`package_route` refuses an unkeyed registry rather than
#: reporting an installed route as unresolved.
_ROUTE_RESOLVERS: Dict[str, Any] = {
    "npm": _npm_route,
    "codex-marketplace": _codex_route,
}

#: Whether a detected route answers row 1 ("is a route present and
#: loadable?") on its own. On npm the package's command *replaces* the file
#: shim's, so a resolved package is the route and `install-host` would be the
#: wrong repair. On the codex marketplace **both** skills are advertised under
#: different names, the check keeps its five rows as they were, and the route is
#: reported in a note that never moves an exit status (D5).
_ROUTE_ANSWERS_ROW_ONE: Dict[str, bool] = {
    "npm": True,
    "codex-marketplace": False,
}


def package_route_note(
    host_id: str,
    route: PackageRoute,
    *,
    file_present: bool,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> str:
    """What ``--check`` says about a detected package route.

    Sentences come from the route's registry row in :data:`_NOTE_FORMS`. A
    note is never a row: it cannot fail the check or move an exit status.

    **npm — flat rather than hedged, because the winner is a decision and not
    a discovery.** The host merges every command file into one map first, then
    hands that same object *by reference* to each plugin's config hook — hooks
    run in load order, return nothing, and nothing is validated or checked for
    collisions. Since the plugin is ours and it assigns unconditionally, the
    package route wins by construction and the file shim becomes inert: still on
    disk, never invoked, with no warning of any kind from the host.

    **codex — both skills are advertised**, under different names, so the note
    exists to warn about the double advertisement, and only an installed *and
    enabled* plugin earns that warning (plus a second line when the plugin's
    server cannot start on this ``PATH``).
    """
    if route.registry == "codex-marketplace":
        return _codex_note(route, file_present=file_present,
                           uninstall=uninstall_line(host_id, base), env=env)
    forms = _NOTE_FORMS["npm"]
    words = {
        "declared_in": route.declared_in,
        "spec": route.spec,
        "payload": route.payload,
        "where": f" at {route.payload}" if route.payload else "",
        "uninstall": uninstall_line(host_id, base),
    }
    if not route.resolved:
        return forms["unresolved"].format(**words)
    if not file_present:
        return forms["package_only"].format(**words)
    return forms["both"].format(**words)


# ---------------------------------------------------------------------------
# --check: exactly five assertions, in order
# ---------------------------------------------------------------------------

ROW_PRESENT = 1
ROW_PREFIX = 2
ROW_SHAPE = 3
ROW_GENERATION = 4
ROW_ENVIRONMENT = 5

ROW_NAMES: Dict[int, str] = {
    ROW_PRESENT: "present",
    ROW_PREFIX: "baked prefix current",
    ROW_SHAPE: "rendered shape valid",
    ROW_GENERATION: "generation current",
    ROW_ENVIRONMENT: "environment",
}

#: Windows needs Git Bash: every shim we write is a POSIX-shell command block, so
#: a Windows host without it would get a shim it cannot run. Same prerequisite the
#: the README and ``references/uv-check.md`` state; no second detector.
GIT_BASH_MISSING = (
    "Git for Windows (Git Bash) is required on Windows: every command in a "
    "rendered shim is POSIX shell, and there is no PowerShell instruction path. "
    "Install it from https://git-scm.com/download/win and re-run."
)

#: The directories a Windows ``bash`` on ``PATH`` may resolve to *without* being a
#: POSIX shell: ``%SystemRoot%\\System32\\bash.exe`` is WSL's launcher, installed
#: by enabling the feature, and it starts a Linux VM whose filesystem is not the
#: one the baked ``C:\\…`` prefix names. A bare ``which("bash")`` accepts it and
#: reports the prerequisite as met on exactly the PowerShell-only machine
#: ``references/uv-check.md`` tells the agent to stop on.
_NOT_GIT_BASH_DIRS: Tuple[str, ...] = ("system32", "syswow64")

#: Where Git for Windows keeps its shell, relative to the install root, and where
#: that root sits relative to a ``git`` found on ``PATH``
#: (``<root>\\cmd\\git.exe``, ``<root>\\bin\\git.exe``, ``<root>\\mingw64\\bin\\git.exe``).
_GIT_BASH_RELATIVE: Tuple[Tuple[str, ...], ...] = (
    ("bin", "bash.exe"), ("usr", "bin", "bash.exe"),
)
_GIT_ROOT_PARENTS: Tuple[int, ...] = (1, 2)

#: The default install roots, for a Git that is installed but not on ``PATH``.
_GIT_ROOT_ENV: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("ProgramFiles", ("Git",)),
    ("ProgramW6432", ("Git",)),
    ("ProgramFiles(x86)", ("Git",)),
    ("LOCALAPPDATA", ("Programs", "Git")),
)


def git_bash(env: Optional[Dict[str, str]] = None) -> Optional[str]:
    """The POSIX shell a rendered shim runs under, or ``None``.

    Same probe ``references/uv-check.md`` (D6c) describes — look for ``bash`` on
    ``PATH`` — with the one correction that document's own "Supported shells"
    section already states in prose: on Windows the answer must be *Git Bash*.
    With WSL enabled, ``bash`` on ``PATH`` is ``%SystemRoot%\\System32\\bash.exe``,
    so a bare ``which`` reports the prerequisite as met on precisely the machine
    that has no POSIX shell for the shim. When ``PATH``'s answer is that launcher
    (or there is none), Git's own installation is asked instead — Git for Windows
    ships ``bash.exe`` inside its root — which is what the row claims to assert.
    """
    env = os.environ if env is None else env
    found = shutil.which("bash")
    if found and not _is_wsl_launcher(found):
        return os.path.abspath(found)
    for candidate in _git_bash_candidates(env):
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
    return None


def _is_wsl_launcher(path: str) -> bool:
    # Split on both separators rather than through ``os.path``: the Windows seam
    # is asserted on POSIX too, and there ``dirname`` treats a backslash as an
    # ordinary character, which would hide the very path this rejects.
    parts = [part for part in re.split(r"[/\\]", path) if part]
    return len(parts) > 1 and parts[-2].lower() in _NOT_GIT_BASH_DIRS


def _git_bash_candidates(env: Dict[str, str]) -> List[str]:
    """Every place Git for Windows' own ``bash.exe`` may sit, PATH's git first."""
    roots: List[Path] = []
    git = shutil.which("git")
    if git:
        parents = Path(os.path.abspath(git)).parents
        roots.extend(
            parents[index] for index in _GIT_ROOT_PARENTS if index < len(parents)
        )
    for name, tail in _GIT_ROOT_ENV:
        value = (env.get(name) or "").strip()
        if value:
            roots.append(Path(value).joinpath(*tail))
    seen: set = set()
    candidates: List[str] = []
    for root in roots:
        for relative in _GIT_BASH_RELATIVE:
            candidate = str(root.joinpath(*relative))
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    return candidates


@dataclass
class Row:
    number: int
    ok: bool
    detail: str
    fix: str = ""

    @property
    def name(self) -> str:
        return ROW_NAMES[self.number]


@dataclass
class CheckResult:
    host_id: str
    rows: List[Row] = field(default_factory=list)
    copies: List[Location] = field(default_factory=list)
    loaded: Optional[Location] = None
    notes: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(row.ok for row in self.rows)

    @property
    def failures(self) -> List[Row]:
        return [row for row in self.rows if not row.ok]

    def row(self, number: int) -> Optional[Row]:
        for row in self.rows:
            if row.number == number:
                return row
        return None


def uninstall_line(host_id: str, base: Optional[str] = None) -> str:
    """The command that removes a file shim, spelled once.

    ``uninstall-host``, never ``install-host --uninstall``: there is no such
    flag, and a note that printed one would hand a user a command the dispatcher
    answers with exit 3.
    """
    prefix = dispatcher_prefix(Path(str(base)) if base else None)
    return f"{prefix} uninstall-host {host_id}"


def repair_line(host_id: str, base: Optional[str] = None) -> str:
    """The one string a stale shim is repaired with, everywhere it is printed.

    The same string D1c's moved-skill-dir message and the `docs/hosts.md`
    quickstart print: the instruction a user sees and the command that repairs
    are never two different things.
    """
    prefix = dispatcher_prefix(Path(str(base)) if base else None)
    return f"{prefix} install-host {host_id}"


def check(
    host_id: str,
    *,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
    path: Optional[Path] = None,
    windows: Optional[bool] = None,
) -> CheckResult:
    """Verify an install: five assertions, in order, each failing on its own.

    *path* pins the file to check (an install verifying what it just wrote);
    otherwise every location is searched and the copy the host would actually load
    is the one rows 2-4 are asserted against. A host whose shim is not ours to
    install (``installable: false``) runs rows 3-5 only: there is no file of ours
    to find (row 1) and no prefix we baked (row 2).
    """
    entry = caps.entry(host_id, base)
    result = CheckResult(host_id=host_id)
    installable = bool(entry["installable"])
    root = str(base) if base else str(skill_dir())

    # A host fact, not a file fact, so it is reported before anything is read —
    # a check that cannot find a shim at all still names the knob (below).
    knob = timeout_note(host_id, base)
    if knob:
        result.notes.append(knob)

    # The route note fires **ungated by `path`**, which is the gate easiest to
    # get backwards and the one that matters most: `install()` runs `check()`
    # and prints its result, so `install-host --all` — the command the docs
    # prescribe after every plugin update — is exactly the moment a shadowed
    # duplicate gets created, and it is exactly the moment a user can act on
    # being told. Only the *row* carve-out below is gated on `path is None`, so
    # an install still grades the file it just wrote.
    route = package_route(host_id, base=base, env=env, project_root=project_root)

    subject: Optional[Path]
    if not installable:
        subject = Path(root) / entry["shim"]["installed"]
        result.notes.append(
            f"host '{host_id}' is not installable: its shim is the plugin's own "
            f"{entry['shim']['installed']}, which the host resolves itself. "
            "Rows 1-2 do not apply."
        )
    elif path is not None:
        subject = Path(path)
        result.copies = existing_copies(
            host_id, base=base, env=env, project_root=project_root
        )
        result.loaded = result.copies[0] if result.copies else None
        if subject.is_file():
            result.rows.append(Row(ROW_PRESENT, True, str(subject)))
        else:
            result.rows.append(
                Row(
                    ROW_PRESENT, False, f"{subject} is missing",
                    f"run `{repair_line(host_id, base)}`",
                )
            )
    else:
        result.copies = existing_copies(
            host_id, base=base, env=env, project_root=project_root
        )
        result.loaded = result.copies[0] if result.copies else None
        subject = result.loaded.path if result.loaded else None
        if (
            subject is None and route is not None
            and _ROUTE_ANSWERS_ROW_ONE.get(route.registry, True)
        ):
            # Row 1's question is "is a route to this skill present and
            # loadable?", not "is there a file?". Answering it with the file
            # question would tell a package user to run `install-host` — which
            # writes the second, shadowed route this probe exists to detect —
            # and then they would be running two.
            #
            # Keeping it a *row* rather than skipping it is what keeps
            # `result.ok` meaningful: "rows 1-4 N/A" would return success on a
            # machine whose declared route never resolved.
            if route.resolved:
                result.rows.append(
                    Row(
                        ROW_PRESENT, True,
                        f"installed as a package: '{route.spec}' at "
                        f"{route.payload}",
                    )
                )
            else:
                result.rows.append(
                    Row(
                        ROW_PRESENT, False,
                        f"'{route.spec}' is declared in {route.declared_in} but "
                        f"no payload resolved at {route.payload}",
                        # The package route's own repair, never `install-host`.
                        f"restart {host_id} with a network connection, or "
                        f"remove the '{route.spec}' entry",
                    )
                )
        elif subject is None:
            target = target_location(
                host_id, DEFAULT_SCOPE, base=base, env=env,
                project_root=project_root,
            )
            result.rows.append(
                Row(
                    ROW_PRESENT, False,
                    f"no shim found in any of {host_id}'s install paths",
                    f"run `{repair_line(host_id, base)}` (writes {target.path})",
                )
            )
        else:
            detail = f"{len(result.copies)} copy(ies); loads {subject}"
            result.rows.append(Row(ROW_PRESENT, True, detail))

    if subject is None or not subject.is_file():
        # Rows 2-4 read the file; without one they are unanswerable rather than
        # failed, and row 5 is still worth reporting.
        result.rows.append(
            _environment_row(
                host_id, base=base, project_root=project_root, windows=windows
            )
        )
        if route is not None:
            result.notes.append(
                package_route_note(
                    host_id, route, file_present=False, base=base, env=env
                )
            )
        return result

    text = subject.read_text(encoding="utf-8")

    if installable:
        result.rows.append(_prefix_row(host_id, text, root, base))
    result.rows.append(_shape_row(host_id, text, base))
    result.rows.append(_generation_row(host_id, text, base, installable))
    result.rows.append(
        _environment_row(
            host_id, base=base, project_root=project_root, windows=windows
        )
    )

    if installable and local_edit(text):
        result.notes.append(
            f"{subject} has local edits (its body no longer matches the hash it "
            "records). Re-installing needs --force, which preserves the edited "
            "file as <shim>.local.bak."
        )
    if route is not None:
        result.notes.append(
            package_route_note(
                host_id, route,
                file_present=subject is not None and subject.is_file(),
                base=base, env=env,
            )
        )
    if installable and str(entry["reload"]) != "none" and path is None:
        # An install prints this line itself, on success and once (see `install`);
        # a standalone check carries it as a note, because "installed but not yet
        # loaded" is a state a reader has to be told about either way.
        result.notes.append(reload_note(host_id, base))
    return result


def reload_note(host_id: str, base: Optional[str] = None) -> str:
    """The host's own reload requirement — a state, never a failure.

    "Installed but not yet loaded" is a distinct, non-failing condition: a
    file-scanning command host picks a new shim up on the next invocation, a host
    that enumerates skills at session start needs a fresh session, and the
    reference host takes a plugin update rather than an install.
    """
    entry = caps.entry(host_id, base)
    value = str(entry["reload"])
    if value == "none":
        return (
            f"host '{host_id}' needs no reload: its shim ships with the plugin, so "
            "a plugin update is the only refresh."
        )
    if value == "restart":
        return (
            f"[NOT_YET_LOADED] restart {host_id} before invoking the command; it "
            "reads its configuration once at startup."
        )
    return (
        f"[NOT_YET_LOADED] start a new {host_id} session before invoking the "
        "command; this host enumerates its commands/skills at session start."
    )


#: The three surfaces a host's command-timeout ceiling can move through (D5b
#: ``timeout_override``), in the order they are reported.
TIMEOUT_CHANNELS: Tuple[str, ...] = ("frontmatter", "env", "config")


def timeout_note(host_id: str, base: Optional[str] = None) -> str:
    """The host's own timeout-raise knob, reported — empty when it has none.

    ``timeout_ceiling_s`` is how long one *foreground* command may run before the
    host kills it; ``timeout_override`` records the channels that ceiling moves
    through — ``none`` where the host has no such surface at all (OpenCode's V2
    frontmatter has no ``timeout`` field, so rendering one would be ignored
    rather than honored) and ``unknown`` until a smoke confirms the key.

    Only a *named* channel is actionable, so only a named channel is reported,
    and where the channel is an environment variable the line to export is
    printed rather than described. An ``unknown`` channel stays silent: an
    install that told the user to export ``unknown`` would be worse than saying
    nothing. Both shipped hosts are ``unknown`` on every raisable channel today,
    so this returns ``""`` for them until one is confirmed.
    """
    entry = caps.entry(host_id, base)
    declared = entry.get("timeout_override") or {}
    named: List[str] = []
    for channel in TIMEOUT_CHANNELS:
        value = str(declared.get(channel) or "none").strip()
        if value in ("", "none", "unknown"):
            continue
        if channel == "env":
            named.append(
                f"export {value}=<seconds> in the shell that starts {host_id}"
            )
        elif channel == "config":
            named.append(f"set `{value}` in {host_id}'s own config")
        else:
            named.append(f"the shim's `{value}:` frontmatter key")
    if not named:
        return ""
    try:
        ceiling = int(entry.get("timeout_ceiling_s") or 0)
    except (TypeError, ValueError):  # pragma: no cover - schema keeps this an int
        ceiling = 0
    cap = (
        f"caps one foreground command at {ceiling}s"
        if ceiling
        else "documents no command-timeout cap"
    )
    return (
        f"host '{host_id}' {cap}; the entry names how that ceiling is raised — "
        + "; ".join(named)
        + ". install-host reports the knob and never writes it for you."
    )


def _prefix_row(
    host_id: str, text: str, root: str, base: Optional[str]
) -> Row:
    prefix = baked_prefix(text)
    if not prefix:
        return Row(
            ROW_PREFIX, False,
            "the file carries no `uv run [flags…] --project \"<abs>\"` prefix, so "
            "nothing binds it to a skill dir",
            f"run `{repair_line(host_id, base)}`",
        )
    if not Path(prefix).is_dir():
        return Row(
            ROW_PREFIX, False,
            f"the baked skill dir no longer exists: {prefix} (the plugin was "
            "updated or removed — the cache is keyed by commit hash)",
            f"run `{repair_line(host_id, base)}`",
        )
    if os.path.normcase(os.path.abspath(prefix)) != os.path.normcase(
        os.path.abspath(root)
    ):
        return Row(
            ROW_PREFIX, False,
            f"the baked skill dir moved: shim says {prefix}, running skill dir is "
            f"{root}",
            f"run `{repair_line(host_id, base)}`",
        )
    return Row(ROW_PREFIX, True, prefix)


#: The one dispatcher command a shim renders: ``… multi_llm.py" <mode> …``.
_DISPATCHER_RE = re.compile(r'multi_llm\.py"?\s+<mode>')


def dispatcher_commands(text: str) -> List[str]:
    """Every dispatcher command in *text*, one logical command per entry.

    Row 3's assertions about the command a host actually *runs* have to read that
    command, not the file: the same shim bakes in verb sentences that discuss the
    unattended default in prose ("… which implies ``--yes``"), so a whole-file
    substring test still passes on a shim whose dispatcher lost the flag. A
    trailing backslash continues a command onto the next line.
    """
    lines = text.splitlines()
    commands: List[str] = []
    for index, line in enumerate(lines):
        if not _DISPATCHER_RE.search(line):
            continue
        command = [line]
        cursor = index
        while command[-1].rstrip().endswith("\\") and cursor + 1 < len(lines):
            cursor += 1
            command.append(lines[cursor])
        commands.append("\n".join(command))
    return commands


#: The substitution words that make ``--interactive`` a replacement, not an extra.
_SUBSTITUTES_RE = re.compile(r"replac\w*|in place of|instead of|substitut\w*", re.I)


def substitution_rule(text: str) -> bool:
    """Does *text* tell the agent to swap ``--interactive`` **for** ``--yes`` (D6b)?

    Every non-reference shim bakes ``--yes``; the user's ``--interactive`` is the
    one flag that may not simply pass through alongside it, because the dispatcher
    rejects the pair with exit 3 and interactive mode would be unreachable on a
    ``ask: free-text`` host. The rule has to be *stated* in the shim — one sentence
    naming both flags and the substitution — so this reads sentences rather than
    the whole file: naming the two flags paragraphs apart is not a rule.
    """
    flat = " ".join(text.split())
    for sentence in re.split(r"(?<=[.;:])\s", flat):
        if (
            "--interactive" in sentence
            and "--yes" in sentence
            and _SUBSTITUTES_RE.search(sentence)
        ):
            return True
    return False


def shape_problems(
    host_id: str, text: str, base: Optional[str] = None
) -> List[str]:
    """Row 3's list: does the file parse the way the shipped-shim guard parses it?

    Frontmatter where the host requires one, exactly one dispatcher command block,
    the uv preflight ahead of the first ``uv run``, no surviving placeholder or
    unfilled slot, the three verb sentences filled once each, and a baked
    ``--host`` id that is a key in the capability data.
    """
    entry = caps.entry(host_id, base)
    problems: List[str] = []
    fmt = str(entry["shim"]["format"])
    if fmt.endswith("+frontmatter"):
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---" or "---" not in lines[1:]:
            problems.append(
                f"this host's shim format is {fmt}, but the file opens with no "
                "`---` frontmatter block"
            )
    forbidden = FORBIDDEN_IN_INSTALLED if entry["installable"] else tuple(
        token for token in FORBIDDEN_IN_INSTALLED
        if token != _HOST_EXPANDED_PLACEHOLDER
    )
    for token in forbidden:
        if token in text:
            problems.append(f"the placeholder {token} survived rendering")
    for slot in sorted(set(_SLOT_RE.findall(text))):
        problems.append(f"the slot {slot} was never filled")

    dispatchers = _DISPATCHER_RE.findall(text)
    if len(dispatchers) != 1:
        problems.append(
            f"expected exactly one dispatcher command block, found "
            f"{len(dispatchers)}"
        )
    probe = text.find("command -v uv")
    # Searched as a pattern, not as the literal `uv run --project`: the rendered
    # dispatcher carries the uv flag list between the two.
    dispatch = _BAKED_PREFIX_BARE_RE.search(text)
    first_run = dispatch.start() if dispatch else -1
    if probe < 0:
        problems.append("no `command -v uv` preflight")
    elif 0 <= first_run < probe:
        problems.append(
            "the uv preflight comes after the first `uv run`, so a missing uv "
            "surfaces as a bare `command not found`"
        )
    baked = set(re.findall(r"--host\s+([a-z][a-z0-9-]*)", text))
    if not baked:
        problems.append("no `--host <id>` is baked into the dispatcher command")
    elif baked != {host_id}:
        problems.append(
            f"the file bakes --host {sorted(baked)} but is the shim for "
            f"'{host_id}'"
        )
    else:
        known = caps.host_ids(base)
        for candidate in baked:
            if candidate not in known:
                problems.append(
                    f"the baked --host '{candidate}' is not a key in the "
                    "capability data"
                )
    for verb, sentence in zip(caps.VERBS, caps.verb_sentences(host_id, base)):
        if text.count(sentence) != 1:
            problems.append(
                f"the *{caps.VERB_WORDING[verb]}* resolution appears "
                f"{text.count(sentence)} times; exactly one per verb, byte-"
                "identical to the capability data's own render"
            )
    if bool(entry["installable"]):
        commands = "\n".join(dispatcher_commands(text))
        if "--yes" not in commands:
            problems.append(
                "the dispatcher command never passes --yes; unattended is the "
                "default on every host that is not the interactive reference host. "
                "(A verb sentence mentioning --yes is prose about the flag, not the "
                "command the host runs, so the assertion reads the command itself.)"
            )
        if "--interactive" in commands:
            problems.append(
                "the dispatcher command bakes --interactive alongside --yes; the "
                "two together are exit 3, so --interactive is only ever a "
                "substitution the agent makes for the user-typed flag"
            )
        elif not substitution_rule(text):
            problems.append(
                "no rule tells the agent to substitute --interactive for the baked "
                "--yes (D6b): without it a user who types --interactive gets "
                "`--yes --interactive`, which the dispatcher rejects with exit 3, "
                "and interactive mode is unreachable on this host"
            )
    return problems


def _shape_row(host_id: str, text: str, base: Optional[str]) -> Row:
    problems = shape_problems(host_id, text, base)
    if problems:
        return Row(
            ROW_SHAPE, False, "; ".join(problems),
            f"run `{repair_line(host_id, base)}` to re-render from the template",
        )
    return Row(ROW_SHAPE, True, "frontmatter, one dispatcher block, uv preflight, "
                                "no unfilled slot")


def _generation_row(
    host_id: str, text: str, base: Optional[str], installable: bool
) -> Row:
    """Row 4 — is this file what the *running* skill would render today?

    Two signals, coarse first, because they answer the same question at different
    resolutions. ``shim_version`` is the hand-maintained shape counter, and its
    unique reach is everything the renderer contributes that no digest of a
    template can see — a changed snippet, a changed verb sentence, a changed
    :func:`render`. ``template_sha256`` is the digest of the
    ``hosts/<host>/shim.md.tmpl`` this file was actually rendered from, recorded
    in the header since D7 and — until this row read it — never compared against
    anything. That gap had a concrete consequence: a template body edited without
    the counter being bumped left every shim already installed from it reporting
    "generation current" while missing whatever the edit added, which is exactly
    how an installed OpenCode shim kept a dispatcher line with no
    ``--exec-subagents`` in it and still passed row 4.

    They are one row rather than a fifth plus a sixth: "generated by an older
    multi-llm" and "rendered from a superseded template" are the same fact to a
    reader ("this shim predates the skill that is running") with the same repair,
    and five is a count `docs/hosts.md`, `references/host-capabilities.md` and the
    tests all state.
    """
    if not installable:
        return Row(
            ROW_GENERATION, True,
            "n/a — this shim is not rendered, so it carries no generation",
        )
    header = parse_header(text)
    if header is None:
        return Row(
            ROW_GENERATION, False,
            f"no {HEADER_KEY} block: this file was not written by install-host "
            "(hand-authored, or from a copy of an older layout)",
            f"run `{repair_line(host_id, base)}`",
        )
    recorded = header.get("shim_version")
    if recorded != SHIM_VERSION:
        return Row(
            ROW_GENERATION, False,
            f"shim generated by an older multi-llm (shim_version {recorded!r}, "
            f"current {SHIM_VERSION})",
            f"run `{repair_line(host_id, base)}`",
        )
    template_problem = _template_problem(host_id, header, base)
    if template_problem:
        return Row(
            ROW_GENERATION, False, template_problem,
            f"run `{repair_line(host_id, base)}` to re-render from the template",
        )
    return Row(
        ROW_GENERATION, True,
        f"shim_version {SHIM_VERSION}, rendered from the current template",
    )


def _template_problem(
    host_id: str, header: Dict[str, object], base: Optional[str]
) -> str:
    """Why this shim's recorded template digest is not the current one, or ``""``.

    Two non-failures are deliberate. A host whose entry sets ``shim.template:
    null`` has no template to have moved — ``_template_sha`` returns ``""`` for
    it — and reporting that as a stale render would fail the one host (the
    reference host, `installable: false`) whose shim is a file nobody renders.
    Everything else is a failure, **including a header carrying no
    ``template_sha256`` key at all**: that field has been written by every
    ``install-host`` that has ever shipped, so its absence means the header was
    hand-assembled or truncated rather than that the file is merely old, and it
    is not something ``shim_version`` can catch — the counter has never left 1,
    so a "this predates the field" reading would pass the file silently.
    """
    expected = _template_sha(host_id, base)
    if not expected:
        return ""
    template = str(caps.entry(host_id, base)["shim"]["template"])
    if "template_sha256" not in header:
        return (
            f"header records no template_sha256, so the {template} this file was "
            "rendered from cannot be identified: every install-host that has "
            "shipped writes that field, which makes this header hand-assembled "
            "or truncated rather than simply older"
        )
    recorded = header.get("template_sha256")
    if recorded != expected:
        return (
            f"rendered from a superseded {template}: the template body has "
            f"changed since this shim was written (records template_sha256 "
            f"{_abbreviate(recorded)}, current {_abbreviate(expected)}), so the "
            "file is missing whatever that change added"
        )
    return ""


def _abbreviate(digest: object) -> str:
    """A digest short enough to read in a one-line row, or what was there instead."""
    if isinstance(digest, str) and len(digest) > 12:
        return digest[:12] + "…"
    return repr(digest)


def _environment_row(
    host_id: str,
    *,
    base: Optional[str] = None,
    project_root: Optional[Path] = None,
    windows: Optional[bool] = None,
) -> Row:
    """Row 5 — the install-time half of the uv bootstrap (D6c layer 1).

    Layer 1 exists because layer 3 cannot run: every invocation goes through
    ``uv run``, so on a machine with no uv the shell fails with exit 127 before any
    Python could print the message. What this row certifies is narrower than it
    looks: on a host where it runs and passes, :func:`find_uv` found uv at
    install time. It says nothing about a host that never runs it (Claude Code is
    ``installable: false``, so no install route evaluates this row), nothing about
    an install kept after this row failed (:func:`install` excludes
    ``ROW_ENVIRONMENT`` from the failures that roll a write back), and nothing
    about whether a bare ``uv`` resolves in the shell the shim later dispatches
    in — the row can pass on ``$MULTI_LLM_UV`` or on an absolute candidate.
    Layers 2 and 3 are what cover the rest.

    The runner leg is :func:`_runner_facts`, which resolves the runner this
    project would really dispatch — never the capability entry's default read on
    its own — and reports the four facts that decide whether it can serve a phase.
    """
    problems: List[str] = []
    details: List[str] = []
    uv = find_uv()
    if uv is None:
        problems.append(uv_missing_text(base))
    else:
        details.append(f"uv={uv}")

    runner_problems, runner_details = _runner_facts(
        host_id, base=base, project_root=project_root
    )
    problems.extend(runner_problems)
    details.extend(runner_details)

    is_windows = os.name == "nt" if windows is None else bool(windows)
    if is_windows:
        shell = git_bash()
        if shell is None:
            problems.append(GIT_BASH_MISSING)
        else:
            details.append(f"bash={shell}")

    if problems:
        return Row(
            ROW_ENVIRONMENT, False, "; ".join(problems),
            "install the missing prerequisite named above, then re-run "
            f"`{repair_line(host_id, base)} --check`",
        )
    return Row(ROW_ENVIRONMENT, True, ", ".join(details))


#: The config key row 5 reports on, spelled the way the executor's own rejections
#: spell it, so the string a user greps for is the same in both places.
RUNNER_KEY = "driver.subagent_runner"

#: The three independent ways a host can stop a dispatched runner (D3c), each
#: declared per host in ``nested_exec``.
NESTED_EXEC_LEGS: Tuple[str, ...] = ("spawn", "network", "credentials")


def configured_runner(
    host_id: str,
    *,
    base: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> Tuple[str, str]:
    """The runner this project would really dispatch, and the layer that set it.

    Row 5 has to ask the question the **executor** asks — ``get_subagent_runner``
    with this host id and this project as the discovery anchor (D3o) — never the
    capability entry's ``default_subagent_runner`` read on its own. That entry
    value is only the middle rung of the ladder: an explicit
    ``driver.subagent_runner`` in ``<git-root>/.multi-llm/providers.yaml`` or in
    ``MULTI_LLM_PROVIDERS_CONFIG`` outranks it, and the host default is itself
    skipped when its own CLI is not detected. Checking the entry default alone
    therefore reports green on a project whose configured runner is absent,
    logged out or too old, and red on a project over a default that nothing
    running there would ever dispatch.

    The layer is reported alongside the spec because "I set it and nothing
    changed" is otherwise a support question (D3o).
    """
    # Imported here to keep host_install light.
    from .provider_registry import resolve_subagent_runner
    anchor = str(project_root) if project_root is not None else None
    # The resolver reports the layer it actually took, so the middle rung is named
    # as itself: re-deriving the provenance here would let the check and the
    # dispatch disagree, and reporting the host default as `base` would point a
    # reader at a file that did not supply the value.
    spec, layer = resolve_subagent_runner("full", anchor=anchor, host_id=host_id)
    return str(spec).strip(), layer


def probe_runner(spec: str, *, anchor: Optional[str] = None) -> Dict[str, str]:
    """Auth and version for one runner spec, through the executor's own preflight.

    The very call the executor makes once per phase (``preflight_runner``:
    profile support, ``version_cmd`` against ``min_version``, the adapter's
    ``auth_check``), so a green ``--check`` and the first dispatch cannot
    disagree about the same CLI. **Installed is not authenticated** (D3c): every
    ``is_available()`` is a bare ``shutil.which``, so a logged-out runner passes
    detection here and is otherwise discovered one spawned child at a time, once
    per task in the batch.

    Nothing a probe cannot answer blocks — an adapter declaring no ``auth_check``,
    a CLI that dropped ``--version``, a probe that fails to run all report
    ``unknown`` — but a recognized refusal (no read-only profile, a build below
    the minimum this release parses, a login notice) is exactly what row 5 exists
    to surface before a batch discovers it.

    One thing this runs that a dispatch preflight does not: the adapter's
    optional ``setup_probe`` readout (M13, §5.2) — cursor-agent's
    ``about --format json`` plan tier is the only one declared today. It is a
    *metadata* probe and never a verdict: it cannot make this function report
    ``problem``, it never touches ``auth``, and a readout that will not run is
    simply one less fact on the row. It is spawned here rather than in
    ``preflight_runner`` because ``--check`` is invoked by a human, once, while a
    preflight runs every phase and would pay a subprocess for a sentence no
    dispatch decision reads.

    Returns:
        ``{"auth", "version", "problem", "metadata"}``; ``problem`` is empty when
        the preflight passed, and ``metadata`` is the rendered ``label=value``
        readout — empty for every adapter that declares none.
    """
    unknown = {
        "auth": "unknown", "version": "unknown", "problem": "", "metadata": "",
    }
    try:
        # Imported here to keep host_install light.
        from .providers.base import PROFILE_AGENT_READONLY
        from .task_outcome import RunnerRejected
        from .runner_preflight import (
            preflight_runner,
            probe_setup_metadata,
        )
    except Exception:  # pragma: no cover - a partial install never fails a check
        return dict(unknown)
    try:
        info = preflight_runner(
            spec, profile=PROFILE_AGENT_READONLY, key=RUNNER_KEY, anchor=anchor
        )
    except RunnerRejected as exc:
        if getattr(exc, "reason_code", "") == "binary_absent":
            # Presence is `runner_available`'s verdict — the two ask the same
            # question of the same adapter, and row 5 reports it once.
            return dict(unknown)
        return {
            "auth": "unknown", "version": "unknown", "problem": str(exc),
            "metadata": "",
        }
    except Exception:  # pragma: no cover - a probe reports; it never blocks
        return dict(unknown)
    try:
        readout = probe_setup_metadata(spec.split(":", 1)[0].strip())
    except Exception:  # pragma: no cover - a readout never fails a check
        readout = {}
    return {
        "auth": str(info.get("auth") or "unknown"),
        "version": str(info.get("version") or "unknown"),
        "problem": "",
        "metadata": ", ".join(f"{k}={v}" for k, v in sorted(readout.items())),
    }


def _runner_state(provider: str, facts: Dict[str, str]) -> str:
    """The typed availability state for a runner row 5 already probed (M10, §5.1).

    Row 5 runs the two probes anyway (``preflight_runner`` → ``probe_runner``),
    so this costs nothing extra and turns three separate facts into the one word
    a reader acts on. It reads the probe *results* — never re-running them.

    ``probe_runner`` never reports a negative auth verdict in its ``auth`` field:
    a recognised login notice is raised by the preflight and arrives here as
    ``problem`` instead, so that is where the ``needs-auth`` reading comes from.
    Anything unresolvable is ``""`` — a diagnostic never fails a ``--check``.
    """
    try:
        # Imported here to keep host_install light.
        from .provider_registry import get_provider
        adapter = get_provider(provider)
        if adapter is None:
            return ""
        if "not_authenticated" in str(facts.get("problem") or ""):
            auth: Optional[bool] = False
        elif str(facts.get("auth") or "") in ("ok", "config"):
            # `config` (plan §8 T8.4): the model-aware preflight found the
            # runner's provider declared in the config its dispatch resolves.
            auth = True
        else:
            auth = None
        report = adapter.describe_availability(
            auth=auth, version=str(facts.get("version") or "")
        )
        return report.state.value
    except Exception:  # pragma: no cover - a diagnostic never fails a check
        return ""


def _runner_facts(
    host_id: str,
    *,
    base: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> Tuple[List[str], List[str]]:
    """Row 5's runner leg: four facts about the runner this project resolves.

    Present, authenticated, version and nested-exec — because "on PATH" answers
    none of the other three, and each of them fails *quietly* at dispatch: a
    logged-out CLI prints a login notice and exits, a CLI below ``min_version``
    emits an event stream the adapter was not written against, and a host whose
    ``nested_exec`` says ``denied`` cannot exec a runner at all.
    """
    entry = caps.entry(host_id, base)
    try:
        spec, layer = configured_runner(
            host_id, base=base, project_root=project_root
        )
    except Exception as exc:  # a broken override layer is an environment miss
        return (
            [
                f"the configured subagent runner could not be resolved: {exc}. "
                f"Fix `{RUNNER_KEY}` in providers.yaml (or in the file "
                "MULTI_LLM_PROVIDERS_CONFIG points at) and re-check."
            ],
            [],
        )

    problems: List[str] = []
    details: List[str] = []
    native = str(entry["subagents"]) == "native"
    scope = (
        " (this host dispatches subagents natively, so the runner is consulted "
        "only under --exec-subagents)"
        if native else ""
    )
    provider = spec.split(":", 1)[0]
    version = "unknown"
    # M10 (§5.1) — `runner_available` stays the **bool**: present or absent is
    # the whole question this branch asks, and it is the same `is_available()`
    # `--init` asks. The typed state rides along in the message and in the facts
    # row below, which is where "installed but not usable" finally has a word.
    if not runner_available(provider):
        state = _runner_state(provider, {}) or "binary-missing"
        problems.append(
            f"the CLI for the configured subagent runner '{spec}' (supplied by "
            f"{layer}) is not installed [{state}], so every phase that dispatches "
            f"a subagent would fail{scope}. Install the '{provider}' CLI (or point "
            f"`{RUNNER_KEY}` in providers.yaml at one you have) and re-check."
        )
    else:
        facts = probe_runner(
            spec, anchor=str(project_root) if project_root is not None else None
        )
        problem = str(facts.get("problem") or "")
        if problem:
            problems.append(problem)
        version = str(facts.get("version") or "unknown")
        details.append(f"runner={spec} (supplied by {layer}){scope}")
        details.append(f"auth={facts.get('auth') or 'unknown'}")
        details.append(f"version={version}")
        state = _runner_state(provider, facts)
        if state:
            details.append(f"state={state}")
        # The adapter's own metadata readout (M13, §5.2), if it declares one.
        # It sits *after* `state` on purpose: it is context for a verdict this
        # row has already reached, never an input to one — `_runner_state` reads
        # `auth`, `version` and `problem`, and this key reaches none of them.
        readout = str(facts.get("metadata") or "").strip()
        if readout:
            details.append(readout)

    nested = entry.get("nested_exec") or {}
    states = {leg: str(nested.get(leg) or "unknown") for leg in NESTED_EXEC_LEGS}
    denied = [leg for leg in NESTED_EXEC_LEGS if states[leg] == "denied"]
    if denied:
        notes = str(nested.get("notes") or "").strip()
        line = (
            f"this host's nested_exec declares {', '.join(denied)} denied, so a "
            f"runner dispatched from inside it cannot run at all — the executor "
            f"refuses the run naming the field rather than dispatching into a "
            f"sandbox that eats the failure. {notes}"
        ).strip()
        # A `denied` leg is fatal only where the executor *is* the dispatch path:
        # a native host resolves the verb to its own subagents, and `denied` there
        # says only that its opt-in `--exec-subagents` fallback is unavailable.
        (details if native else problems).append(line)
    details.append(
        "nested_exec=" + "/".join(f"{leg}:{states[leg]}" for leg in NESTED_EXEC_LEGS)
    )
    if version != "unknown" and states["spawn"] == "unknown":
        # The version probe *is* a spawn probe: the runner CLI started as a child
        # of this host's own shell, which is the one nested_exec leg a check can
        # observe without dispatching a real, billed turn.
        details.append("spawn probed here: the runner CLI started under this host")
    return problems, details


def runner_available(provider: str) -> bool:
    """Is this provider's CLI installed?

    Reuses ``init_config``'s detection path — ``provider_registry.get_provider``
    plus the adapter's own ``is_available()`` — rather than re-implementing a
    second probe that could disagree with ``--init``.
    """
    try:
        # Imported here to keep host_install light.
        from .provider_registry import get_provider
        adapter = get_provider(provider)
    except Exception:  # pragma: no cover - a config error is not a check failure
        return False
    if adapter is None:
        return False
    try:
        return bool(adapter.is_available())
    except Exception:  # pragma: no cover - a probe that raises is a miss
        return False


# ---------------------------------------------------------------------------
# The write
# ---------------------------------------------------------------------------

def atomic_write(target: Path, text: str) -> None:
    """Render into the target directory, ``fsync``, then ``os.replace``
    (:func:`atomic_write_bytes`).

    The text is encoded here rather than handed to a newline-translating stream,
    which is the same guarantee ``newline="\\n"`` used to give: the bytes are
    identical on every platform (idempotency and the body hash both depend on
    that).
    """
    atomic_write_bytes(target, text.encode("utf-8"))


def atomic_write_bytes(target: Path, data: bytes) -> None:
    """The same write, for bytes that must land exactly as they were read.

    Same volume by construction, which is what makes ``os.replace`` atomic on
    Windows too. Directories come from ``mkdir(parents=True, exist_ok=True)`` —
    no symlink, no junction, no elevation.

    A backup and a rollback cannot go through the text path: reading a file with
    ``read_text`` translates CRLF/CR to LF, so round-tripping a user's edited
    shim through it would rewrite the line endings of the very bytes D7a
    promises to preserve.

    The written file is owner-only (0600), as every shim, backup and rollback
    this installer has written is.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_bytes(target, data, mode=0o600, temp_prefix=".multi-llm-shim-")


def _as_text(data: bytes) -> str:
    """Decode an existing file the way every other reader in this module does.

    ``read_text`` — which ``check``'s row 3 and the header parser both go
    through — translates CRLF/CR to LF, so hashing and comparison must see the
    same translation or an install would disagree with the ``--check`` that
    follows it. Undecodable bytes are replaced rather than raised on: a file
    that is not UTF-8 is certainly not a pristine shim of ours, and it belongs
    in ``_guard_existing``'s refusal, not in a traceback.
    """
    return (
        data.decode("utf-8", errors="replace")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


class _VerifyFailed(Exception):
    """A post-replace verification failure, on its way to one rollback site.

    Both a failed ``--check`` row and a probe that raised have to restore the
    previous bytes before they surface (D7a); routing them through one exception
    keeps that from being two rollback calls that can drift apart.
    """


def install(
    host_id: str,
    *,
    scope: str = DEFAULT_SCOPE,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
    force: bool = False,
    windows: Optional[bool] = None,
) -> int:
    """Render, write atomically, verify — or roll back. Returns an exit code."""
    entry = caps.entry(host_id, base)
    if not entry["installable"]:
        raise Refused(
            f"ERROR: `install-host {host_id}` is --check-only.\n"
            f"       This host's entry is installable: false — its shim is the "
            f"plugin's own {entry['shim']['installed']}, which the host resolves "
            "itself, so there is nothing for an installer to write. Run "
            f"`install-host {host_id} --check` to verify the shipped shim and this "
            "machine's prerequisites."
        )
    location = target_location(
        host_id, scope, base=base, env=env, project_root=project_root
    )
    target = location.path
    if target.exists() and not target.is_file():
        raise Refused(
            f"ERROR: {target} exists and is not a regular file, so the shim "
            "cannot be written there.\n"
            "       install-host writes one file per host and never replaces a "
            "directory or anything else it did not write. Move whatever is at "
            "that path aside, or fix the install_paths entry for "
            f"'{host_id}' in hosts/capabilities.yaml."
        )
    previous_bytes: Optional[bytes] = None
    previous: Optional[str] = None
    if target.is_file():
        # The bytes are what the backup and the rollback restore; the decoded
        # text is only ever hashed or compared.
        previous_bytes = target.read_bytes()
        previous = _as_text(previous_bytes)
        _guard_existing(host_id, target, previous, force)

    rendered = render_installed(host_id, base=base)
    if previous is not None and previous == rendered:
        # Idempotency is a property, not a coincidence: nothing is written, no
        # rollback is possible, and the verification below still runs.
        print(f"[SHIM_UNCHANGED] {target}")
    else:
        if previous_bytes is not None and force and not _is_pristine_shim(previous):
            # Anything --force had to override — a hand-edited shim or a file that
            # was never ours — is preserved rather than destroyed, byte for byte.
            # A pristine shim of ours needs no backup: re-rendering it reproduces
            # it exactly.
            backup = Path(str(target) + ".local.bak")
            atomic_write_bytes(backup, previous_bytes)
            print(f"[SHIM_EDIT_PRESERVED] {backup}")
        atomic_write(target, rendered)
        print(f"[SHIM_INSTALLED] {target}")

    # Everything from here to the reload note runs against bytes already on disk,
    # so every way out of it — a failed row, an unreadable file, a probe that
    # raised — is one failed install with one rollback (D7a).
    try:
        record_artifact(target)
        result = check(
            host_id, base=base, env=env, project_root=project_root, path=target,
            windows=windows,
        )
        print_check(result)
        byte_failures = [
            row for row in result.failures if row.number != ROW_ENVIRONMENT
        ]
        if byte_failures:
            raise _VerifyFailed(
                "did not verify:\n"
                + "\n".join(
                    f"       row {row.number} ({row.name}): {row.detail}"
                    for row in byte_failures
                )
            )
        _report_neighbours(result, location)
    except Exception as error:
        expected = isinstance(error, _VerifyFailed)
        detail = str(error) if expected else (
            f"could not be verified — {type(error).__name__}: {error}"
        )
        outcome = _rollback(target, previous_bytes)
        raise Refused(
            f"ERROR: the shim written to {target} {detail}\n"
            f"       The install failed and was rolled back ({outcome})."
        ) from (None if expected else error)
    print(reload_note(host_id, base))
    if result.failures:
        raise Refused(
            f"ERROR: {target} is installed and correct, but this machine is not "
            "ready to run it:\n"
            + "\n".join(
                f"       row {row.number} ({row.name}): {row.detail}"
                for row in result.failures
            )
            + "\n       The shim was kept: installing the missing prerequisite is "
            "the fix, not re-rendering."
        )
    return EXIT_OK


def _guard_existing(
    host_id: str, target: Path, previous: str, force: bool
) -> None:
    """Refuse to overwrite a foreign or hand-edited file (D7a/D7b)."""
    header = parse_header(previous)
    if header is None:
        if force:
            return
        raise Refused(
            f"ERROR: {target} exists and carries no {HEADER_KEY} block, so it was "
            "not written by install-host.\n"
            "       Overwriting it could destroy a file that is not ours. Move it "
            "aside, or pass --force to overwrite (the existing file is preserved "
            "as <shim>.local.bak)."
        )
    owner = header.get("host")
    if owner != host_id:
        raise Refused(
            f"ERROR: {target} already carries a {HEADER_KEY} block for host "
            f"'{owner}', not '{host_id}'.\n"
            "       Two hosts resolving to one path is a conflict, and it is "
            "reported rather than resolved: overwriting would swap the baked "
            "--host, and with it the whole capability profile, out from under "
            f"'{owner}'. Fix the install_paths collision in "
            "hosts/capabilities.yaml, or uninstall the other host first."
        )
    if local_edit(previous) and not force:
        raise Refused(
            f"ERROR: {target} has local edits — its body no longer matches the "
            "hash it records.\n"
            "       A shim that needs repair and a shim you deliberately "
            "customized are different situations, and the installer refuses to "
            "guess between them. Either re-run with --force (overwrites, keeping "
            "your file as <shim>.local.bak) or migrate the edit into the template "
            "by hand."
        )


def _rollback(target: Path, previous: Optional[bytes]) -> str:
    """Undo the write, and report what actually happened.

    The refusal quotes this clause verbatim, so it only ever claims the cleanup
    that succeeded: telling a user nothing was left behind when the unlink
    failed sends them looking in the wrong place for a file that is still there.
    """
    if previous is not None:
        atomic_write_bytes(target, previous)
        return "the previous file was restored"
    try:
        target.unlink()
    except FileNotFoundError:  # pragma: no cover - nothing to remove
        pass
    except OSError as error:
        return (
            f"except that {target} could not be removed and must be deleted by "
            f"hand: {error}"
        )
    return "nothing was left behind"


def _report_neighbours(result: CheckResult, written: Location) -> None:
    """Name the copy that will actually load, and every one that will not.

    A stale global shim shadowing nothing is harmless; a stale project shim
    shadowing a fresh global install is exactly the failure this reporting exists
    to surface, and it is caught here at install time rather than at the first
    confusing run.
    """
    for copy in result.copies:
        if copy.path == written.path:
            continue
        if _precedes(result.copies, copy, written):
            print(
                f"[SHIM_SHADOWED] {copy.path} ({copy.label}) takes precedence "
                f"over the shim just written to {written.path} "
                f"({written.label}), so that copy is what this host will actually "
                f"load. Install into {copy.scope} scope instead, or remove the "
                "older copy."
            )
        else:
            print(
                f"[SHIM_ALSO_FOUND] {copy.path} ({copy.label}) — lower precedence "
                "than what was just written"
                + ("; a compatibility location is never written by install-host, "
                   "so removing it is safe once the new shim loads."
                   if not copy.writable else ".")
            )


def _precedes(order: Sequence[Location], one: Location, other: Location) -> bool:
    paths = [location.path for location in order]
    if one.path not in paths or other.path not in paths:
        return False
    return paths.index(one.path) < paths.index(other.path)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_check(result: CheckResult) -> None:
    print(f"[INSTALL_CHECK] host={result.host_id}")
    for copy in result.copies:
        marker = " <- loads" if result.loaded and copy.path == result.loaded.path else ""
        print(f"  found: {copy.path} ({copy.label}){marker}")
    for row in result.rows:
        status = "OK  " if row.ok else "FAIL"
        print(f"  {row.number}. {row.name:<22} {status} {row.detail}")
        if not row.ok and row.fix:
            print(f"     FIX: {row.fix}")
    for note in result.notes:
        first, *rest = note.split("\n")
        print(f"  note: {first}")
        for line in rest:
            print(f"        {line}")


# ---------------------------------------------------------------------------
# uninstall-host
# ---------------------------------------------------------------------------

def uninstall(
    host_id: str,
    *,
    scopes: Sequence[str] = WRITABLE_SCOPES,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """The missing inverse: remove only files carrying our header block.

    Identified by the ``multi_llm_shim`` block, never by filename. Compatibility
    locations (never ours to begin with) and locally edited shims are **reported,
    not deleted** — an edited shim needs ``--force`` exactly as a re-install does.
    Nothing outside the host's own ``install_paths`` is ever a candidate.
    """
    removed: List[Path] = []
    kept: List[str] = []
    for location in existing_copies(
        host_id, base=base, env=env, project_root=project_root
    ):
        if location.scope not in scopes:
            continue
        text = location.path.read_text(encoding="utf-8")
        header = parse_header(text)
        if header is None:
            kept.append(
                f"{location.path} ({location.label}) carries no {HEADER_KEY} "
                "block, so it is not ours to remove"
            )
            continue
        if header.get("host") != host_id:
            kept.append(
                f"{location.path} ({location.label}) belongs to host "
                f"'{header.get('host')}', not '{host_id}'"
            )
            continue
        if not location.writable:
            kept.append(
                f"{location.path} ({location.label}) is a compatibility location; "
                "install-host never creates one, so uninstall-host never deletes "
                "one"
            )
            continue
        if local_edit(text) and not force:
            kept.append(
                f"{location.path} ({location.label}) has local edits; pass --force "
                "to remove it anyway"
            )
            continue
        if dry_run:
            print(f"[SHIM_WOULD_REMOVE] {location.path}")
            removed.append(location.path)
            continue
        location.path.unlink()
        print(f"[SHIM_REMOVED] {location.path}")
        removed.append(location.path)
        _prune_empty_dir(location)

    for line in kept:
        print(f"[SHIM_KEPT] {line}")
    if not removed:
        print(
            f"[SHIM_NOT_FOUND] no removable multi-llm shim for host '{host_id}' in "
            f"scope(s) {', '.join(scopes)}."
        )
        return EXIT_NOTHING_TO_DO
    if dry_run:
        print("[DRY_RUN] nothing was changed.")
    return EXIT_OK


def _prune_empty_dir(location: Location) -> None:
    """Remove a skill directory we created and left empty — and only that.

    The directory is pruned only when its own name is the last segment of the
    install path (``…/skills/multi-llm``), so a shared command directory
    (``…/opencode/commands``) is never removed even when it ends up empty.
    """
    directory = location.directory
    if directory.name != "multi-llm":
        return
    try:
        next(directory.iterdir())
    except StopIteration:
        try:
            directory.rmdir()
            print(f"[SHIM_DIR_REMOVED] {directory}")
        except OSError:  # pragma: no cover - a racing writer keeps it
            pass
    except OSError:  # pragma: no cover - unreadable dir
        pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _installed_hosts(
    *,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> List[Location]:
    """Every writable location holding a shim, for every installable host.

    **Every** scope, not just the one that loads: a host installed in both scopes
    has two copies with the same baked prefix, and a plugin update staled both. If
    ``--all`` stopped at the highest-precedence copy, the global one would keep its
    dead prefix forever and load stale in every *other* project — the exact repair
    ``--all`` exists to perform, silently skipped. One entry per scope, because a
    scope's write target is its first preferred path however many of that scope's
    locations happen to hold a file.
    """
    found: List[Location] = []
    for host_id in sorted(caps.host_ids(base)):
        if not caps.entry(host_id, base)["installable"]:
            continue
        seen: set = set()
        for location in existing_copies(
            host_id, base=base, env=env, project_root=project_root
        ):
            if location.writable and location.scope not in seen:
                seen.add(location.scope)
                found.append(location)
    return found


def _scope_from(args: argparse.Namespace) -> str:
    if getattr(args, "scope_project", False):
        return SCOPE_PROJECT
    return SCOPE_GLOBAL


def _project_root(args: argparse.Namespace) -> Optional[Path]:
    value = getattr(args, "project_root", None)
    return Path(os.path.abspath(value)) if value else None


def main(argv: Optional[Sequence[str]] = None) -> int:
    """``multi_llm.py install-host <host> [--global|--project] [--check] [--all]``."""
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        prog="multi_llm.py install-host",
        description=(
            "Render this skill's entry shim into another coding harness, or "
            "verify an existing install. Paths, precedence and the reload "
            "requirement all come from hosts/capabilities.yaml."
        ),
    )
    parser.add_argument(
        "host", nargs="?",
        help="Host id from hosts/capabilities.yaml (omit with --all).",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--global", dest="scope_global", action="store_true",
        help="Write the machine-wide copy (the default).",
    )
    scope.add_argument(
        "--project", dest="scope_project", action="store_true",
        help="Write the copy scoped to this project.",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Verify instead of writing: the five assertions, exit 3 on any "
             "failure.",
    )
    parser.add_argument(
        "--all", dest="every", action="store_true",
        help="Every installable host that already has a shim on disk, in every "
             "scope that holds one. This is the one command to run after a "
             "plugin update.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite a locally edited or unrecognized shim, preserving it as "
             "<shim>.local.bak.",
    )
    parser.add_argument(
        "--project-root", dest="project_root", default=None,
        help="Where a project-scope path is resolved (default: the current "
             "directory).",
    )
    args = parser.parse_args(list(argv) if argv is not None else [])

    try:
        return _run_install(args)
    except Refused as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_NEEDS_HUMAN
    except caps.UnknownHost as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code


def _run_install(args: argparse.Namespace) -> int:
    project_root = _project_root(args)
    if args.every and args.host:
        raise Refused(
            "ERROR: pass either a host id or --all, not both. --all covers every "
            "installable host that already has a shim on disk."
        )
    if not args.every and not args.host:
        raise Refused(
            "ERROR: install-host needs a host id (or --all).\n"
            f"       Known hosts: {', '.join(sorted(caps.host_ids()))}"
        )

    if args.every:
        installed = _installed_hosts(project_root=project_root)
        if not installed:
            print(
                "[SHIM_NOT_FOUND] no installed shim to re-render. Install one "
                "first: `install-host <host>`."
            )
            return EXIT_NOTHING_TO_DO
        worst = EXIT_OK
        for location in installed:
            # `path` pins the check to *this* copy: the default search asserts
            # rows 2-4 against the copy that loads, which would pass a stale
            # global shim off as verified whenever a fresh project one shadows it.
            code = _one_install(
                location.host_id, scope=location.scope, check_only=args.check,
                force=args.force, project_root=project_root,
                path=location.path,
            )
            worst = code if code != EXIT_OK else worst
        return worst

    scope = _scope_from(args)
    return _one_install(
        args.host, scope=scope, check_only=args.check, force=args.force,
        project_root=project_root,
    )


def _one_install(
    host_id: str,
    *,
    scope: str,
    check_only: bool,
    force: bool,
    project_root: Optional[Path],
    path: Optional[Path] = None,
) -> int:
    caps.entry(host_id)  # exit 3 on an unknown id, before anything is touched
    if check_only:
        result = check(host_id, project_root=project_root, path=path)
        print_check(result)
        if result.ok:
            return EXIT_OK
        print(
            "[INSTALL_CHECK_FAILED] "
            + "; ".join(f"row {row.number} ({row.name})" for row in result.failures),
            file=sys.stderr,
        )
        return EXIT_NEEDS_HUMAN
    try:
        return install(
            host_id, scope=scope, force=force, project_root=project_root
        )
    except Refused as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_NEEDS_HUMAN


def uninstall_main(argv: Optional[Sequence[str]] = None) -> int:
    """``multi_llm.py uninstall-host <host> [--global|--project|--all] [--dry-run]``."""
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        prog="multi_llm.py uninstall-host",
        description=(
            "Remove a previously installed host shim. Only files carrying our "
            "multi_llm_shim block are candidates, and only inside that host's own "
            "install_paths."
        ),
    )
    parser.add_argument("host", help="Host id from hosts/capabilities.yaml.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--global", dest="scope_global", action="store_true",
        help="Only the machine-wide copy.",
    )
    scope.add_argument(
        "--project", dest="scope_project", action="store_true",
        help="Only this project's copy.",
    )
    scope.add_argument(
        "--all", dest="every_scope", action="store_true",
        help="Both scopes (the default).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List what would be removed and change nothing.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Remove a locally edited shim too.",
    )
    parser.add_argument(
        "--project-root", dest="project_root", default=None,
        help="Where a project-scope path is resolved (default: the current "
             "directory).",
    )
    args = parser.parse_args(list(argv) if argv is not None else [])

    scopes: Tuple[str, ...] = WRITABLE_SCOPES
    if args.scope_global:
        scopes = (SCOPE_GLOBAL,)
    elif args.scope_project:
        scopes = (SCOPE_PROJECT,)
    try:
        caps.entry(args.host)
        return uninstall(
            args.host, scopes=scopes, dry_run=args.dry_run, force=args.force,
            project_root=_project_root(args),
        )
    except Refused as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_NEEDS_HUMAN
    except caps.UnknownHost as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":  # pragma: no cover - direct invocation is unadvertised
    raise SystemExit(main(sys.argv[1:]))
