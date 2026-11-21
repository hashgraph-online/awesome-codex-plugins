"""Where a host's shim can live: scopes, path tokens and locations (D7c).

Every path comes from ``hosts/capabilities.yaml`` through
:mod:`utils.host_capabilities`; nothing here names a host.
:mod:`utils.host_install` re-exports these names, and the rules they serve are
in its docstring and in ``docs/development/hosts.md``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import host_capabilities as caps


class Refused(Exception):
    """An installer-owned refusal: exit 3, message already written for a human."""


# ---------------------------------------------------------------------------
# Scopes and path tokens (D7c)
# ---------------------------------------------------------------------------

SCOPE_PROJECT = "project"
SCOPE_GLOBAL = "global"
SCOPE_LEGACY = "legacy"

#: Writable scopes, in the order ``--check`` reports them: the host's own
#: discovery precedence, recorded rather than assumed (project beats global on
#: every host surveyed).
WRITABLE_SCOPES: Tuple[str, ...] = (SCOPE_PROJECT, SCOPE_GLOBAL)

#: Default scope for a write. ``--global`` is the machine-wide install a user
#: expects from a one-off command; ``--project`` is the opt-in.
DEFAULT_SCOPE = SCOPE_GLOBAL

#: The per-user root tokens, in the order they are honoured. ``$HOME`` is what the
#: data spells; ``%USERPROFILE%`` is the same directory under native Windows and
#: is accepted as a token so a future entry may spell it either way.
_HOME_TOKENS: Tuple[str, ...] = ("$HOME", "${HOME}", "%USERPROFILE%", "~")

_XDG_TOKENS: Tuple[str, ...] = ("$XDG_CONFIG_HOME", "${XDG_CONFIG_HOME}")

#: A native-absolute entry, in either platform's spelling: a leading separator, a
#: drive prefix (``C:\…``) or a UNC root. Rejected for the same reason ``..`` is —
#: an ``install_paths`` entry names a directory *under* the token it starts with
#: or under the project root, and neither form does.
_ABSOLUTE_RE = re.compile(r"^(?:[/\\]|[A-Za-z]:[/\\]?)")


def user_home(env: Optional[Dict[str, str]] = None) -> Path:
    """The per-user root a ``$HOME``/``~``/``%USERPROFILE%`` token expands to.

    ``HOME`` first (POSIX, and what Git Bash sets on Windows), then
    ``USERPROFILE`` (native Windows Python), then the interpreter's own answer.
    One function, so no caller re-derives the platform rule and a test can hand it
    a temp home on either platform.
    """
    env = os.environ if env is None else env
    for name in ("HOME", "USERPROFILE"):
        value = env.get(name)
        if value:
            return Path(value)
    return Path.home()


def expand_path_tokens(
    raw: str,
    *,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> Path:
    """Expand one ``install_paths`` entry into a native absolute directory.

    OS variance is a token expansion, not extra rows in the data: ``$HOME``/``~``
    is ``%USERPROFILE%`` on Windows, and the XDG-style roots honour
    ``$XDG_CONFIG_HOME`` when it is set (falling back to ``<home>/.config``, which
    is what the second global entry of an XDG host spells literally — the two
    collapse to one path and are de-duplicated by :func:`locations`).

    A relative entry is a project-scope path and resolves against *project_root*.
    A token is only a token when the entry *is* it or continues with a separator,
    so ``$XDG_CONFIG_HOMEx`` is not an XDG path, and the entry itself is checked
    (:func:`checked_entry`) before any of it is joined.
    """
    env = os.environ if env is None else env
    text = checked_entry(raw)
    home = user_home(env)
    for token in _XDG_TOKENS:
        if text == token or text.startswith(token + "/"):
            configured = (env.get("XDG_CONFIG_HOME") or "").strip()
            root = Path(configured) if configured else home / ".config"
            return _join(root, text[len(token):])
    for token in _HOME_TOKENS:
        if text == token or text.startswith(token + "/"):
            return _join(home, text[len(token):])
    root = Path(project_root) if project_root is not None else Path.cwd()
    return _join(root, text)


def checked_entry(raw: str) -> str:
    """The stripped ``install_paths`` entry, or :class:`Refused`.

    An entry names a directory *under* the token it starts with, or under the
    project root — nothing else is expressible, and both other shapes are silent
    rather than loud: :func:`_join` normalizes through ``os.path.abspath``, so a
    single ``..`` segment relocates the write outside the root the entry names,
    and a native-absolute entry ignores the root entirely. The schema states the
    same rule (``install_path``), but the schema is CI's guard while this is the
    runtime one — an entry reaching expansion is the last moment a bad path is
    still a message instead of a file in the wrong directory.
    """
    text = raw.strip()
    if not text:
        raise Refused(
            "ERROR: an install_paths entry is empty.\n"
            "       Each entry names one directory, token-rooted ($HOME, "
            "%USERPROFILE%, $XDG_CONFIG_HOME, ~) or relative to the project "
            "root. Fix the entry in hosts/capabilities.yaml."
        )
    remainder, rooted = text, False
    for token in _XDG_TOKENS + _HOME_TOKENS:
        if text == token or text.startswith(token + "/"):
            remainder, rooted = text[len(token):], True
            break
    if any(segment == ".." for segment in re.split(r"[/\\]", remainder)):
        raise Refused(
            f"ERROR: install_paths entry '{text}' contains a '..' segment.\n"
            "       An entry names a directory under the token it starts with "
            "(or under the project root); a parent-directory segment would move "
            "the write outside it. Fix the entry in hosts/capabilities.yaml."
        )
    if not rooted and _ABSOLUTE_RE.match(text):
        raise Refused(
            f"ERROR: install_paths entry '{text}' is an absolute path.\n"
            "       An entry is token-rooted ($HOME, ${HOME}, %USERPROFILE%, ~, "
            "$XDG_CONFIG_HOME, ${XDG_CONFIG_HOME}) or relative to the project "
            "root, so that one entry expands correctly on every OS. Fix the "
            "entry in hosts/capabilities.yaml."
        )
    return text


def _join(root: Path, remainder: str) -> Path:
    remainder = remainder.lstrip("/")
    return Path(os.path.abspath(str(root / remainder) if remainder else str(root)))


# ---------------------------------------------------------------------------
# Where a host's shim can live
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Location:
    """One place a host's shim may sit, with its precedence already decided."""

    host_id: str
    scope: str            # project | global | legacy
    writable: bool        # False for a compatibility location (read-only, D7)
    raw: str              # the unexpanded token form, for messages
    directory: Path
    path: Path

    @property
    def label(self) -> str:
        kind = "preferred" if self.writable else "compat"
        return f"{self.scope}/{kind}"


def shim_filename(host_id: str, base: Optional[str] = None) -> str:
    """The file name a host's shim takes.

    ``shim.installed`` is recorded relative to the host's own config root
    (``commands/multi-llm.md``, ``SKILL.md``) while ``install_paths`` names the
    directory to write into, so the file name is its basename. One rule, both
    hosts, no branch.
    """
    installed = caps.entry(host_id, base)["shim"]["installed"]
    return os.path.basename(installed.replace("\\", "/"))


def locations(
    host_id: str,
    *,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> List[Location]:
    """Every location for *host_id*, in the host's discovery-precedence order.

    Precedence is the host's, not ours, and it is recorded rather than assumed: on
    every host surveyed project scope wins over global and a preferred root wins
    over a legacy one. A legacy entry belongs to the scope its own token implies —
    rooted at the user's home (or XDG) means global, relative means project — so
    the classification stays data-driven too.

    The two kinds of entry compose differently, and that is the one deviation
    worth spelling out: a **preferred** entry names the directory to write into
    and takes its file name from ``shim.installed``, while a **legacy** entry
    names the *file*. A deprecated layout's file name is the host's own old
    convention rather than ours (Codex's ``~/.codex/prompts/multi-llm.md`` is a
    prompt file, not a skill directory), so joining our basename onto it would
    probe a path no install of any vintage ever created — detection that can only
    ever miss.
    """
    entry = caps.entry(host_id, base)
    paths = entry["install_paths"]
    name = shim_filename(host_id, base)
    buckets: Dict[str, List[Tuple[str, bool]]] = {
        SCOPE_PROJECT: [(raw, True) for raw in paths[SCOPE_PROJECT]],
        SCOPE_GLOBAL: [(raw, True) for raw in paths[SCOPE_GLOBAL]],
    }
    for raw in paths[SCOPE_LEGACY]:
        scope = SCOPE_GLOBAL if _is_user_rooted(raw) else SCOPE_PROJECT
        buckets[scope].append((raw, False))

    found: List[Location] = []
    seen: set = set()
    for scope in WRITABLE_SCOPES:
        # Preferred roots first, then this scope's compatibility locations.
        for writable in (True, False):
            for raw, is_writable in buckets[scope]:
                if is_writable is not writable:
                    continue
                expanded = expand_path_tokens(
                    raw, env=env, project_root=project_root
                )
                # Preferred: a directory, plus our own file name. Legacy: the
                # file itself (see the docstring).
                directory = expanded if writable else expanded.parent
                path = expanded / name if writable else expanded
                if str(path) in seen:
                    continue
                seen.add(str(path))
                found.append(
                    Location(
                        host_id=host_id,
                        scope=scope,
                        writable=writable,
                        raw=raw,
                        directory=directory,
                        path=path,
                    )
                )
    return found


def _is_user_rooted(raw: str) -> bool:
    text = raw.strip()
    return any(
        text == token or text.startswith(token + "/")
        for token in _HOME_TOKENS + _XDG_TOKENS
    ) or Path(text).is_absolute()


def target_location(
    host_id: str,
    scope: str = DEFAULT_SCOPE,
    *,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> Location:
    """The one path a write goes to: the **first** preferred path of *scope*.

    Compatibility locations are supported deliberately and read-only: an existing
    install keeps working and ``--check`` finds it, but nothing new is ever created
    there. Migrating is: re-run ``install-host``, then delete the file it names.
    """
    for location in locations(
        host_id, base=base, env=env, project_root=project_root
    ):
        if location.scope == scope and location.writable:
            return location
    raise Refused(
        f"ERROR: host '{host_id}' declares no {scope}-scope install path.\n"
        f"       install_paths.{scope} is empty in hosts/capabilities.yaml, so "
        "there is nowhere to write. Pass the other scope, or add the path to the "
        "data (a host doc change is a data edit, never a code edit)."
    )


def existing_copies(
    host_id: str,
    *,
    base: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> List[Location]:
    """Locations that hold a file today, in precedence order."""
    return [
        location
        for location in locations(
            host_id, base=base, env=env, project_root=project_root
        )
        if location.path.is_file()
    ]
