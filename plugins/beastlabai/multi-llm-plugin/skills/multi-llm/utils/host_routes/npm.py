"""The npm route resolver: a spec declared in the host's JSON config, then one stat.

Config first, cache second (see :func:`_npm_route`). Used by
``host_install.package_route`` through its ``_ROUTE_RESOLVERS`` table.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import PackageRoute

from ..host_paths import (
    SCOPE_GLOBAL,
    SCOPE_PROJECT,
    Refused,
    _is_user_rooted,
    _join,
    checked_entry,
    expand_path_tokens,
    user_home,
)
from ..json_extractor import strip_jsonc as _strip_jsonc


def _package_name(spec: str) -> str:
    """A spec's package name: strip a trailing ``@<range>``, keep a leading scope."""
    if spec.startswith("@"):
        scope, _, rest = spec.partition("/")
        return f"{scope}/{rest.split('@', 1)[0]}" if rest else spec
    return spec.split("@", 1)[0]


def _config_dirs(
    host_id: str,
    entry: Dict[str, Any],
    *,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> List[Path]:
    """The config directories a command directory *implies*, in merge order.

    Derived from ``install_paths`` rather than restated: a command directory's
    *parent* is the config directory, which is the same relation on every host
    that has both. That keeps this probe out of the business of knowing where a
    given host keeps its config, which is exactly the kind of second table this
    project refuses to maintain.

    It is only ever **half** the set, and the half a command directory can reach:
    a host also reads config from places it installs no command into — an
    environment redirect, a per-user ``~/.<host>`` — and those are added by
    :func:`_config_files`, which is what a route probe must iterate.
    """
    dirs: List[Path] = []
    for scope in (SCOPE_PROJECT, SCOPE_GLOBAL):
        for raw in entry["install_paths"].get(scope) or []:
            try:
                expanded = expand_path_tokens(
                    raw, env=env, project_root=project_root
                )
            except Refused:
                continue
            parent = expanded.parent
            if parent not in dirs:
                dirs.append(parent)
    return dirs


def _config_env_names(host_id: str) -> Tuple[str, str]:
    """``($<HOST>_CONFIG, $<HOST>_CONFIG_DIR)`` — the redirect pair, derived.

    A convention rather than a per-host table: the host id upper-cased with
    non-alphanumerics folded to ``_``. Deriving the names is what keeps a second
    "where does this host keep its config" map out of this file, and a wrong
    guess costs nothing — an unset variable contributes no candidate and the
    derived directories still answer. OpenCode's pair is exactly this pair.
    """
    stem = re.sub(r"[^A-Z0-9]+", "_", host_id.upper()).strip("_")
    return f"{stem}_CONFIG", f"{stem}_CONFIG_DIR"


def _project_config_dirs(
    entry: Dict[str, Any],
    *,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> List[Path]:
    """The project config directories, walked upward from *project_root*.

    A host that merges a project ``.opencode`` merges the tree's, not only the
    one sitting in the directory a command happened to run in, so the same name
    is looked for in each ancestor, nearest first. The directory *name* is
    derived and never restated: it is the first segment of each project-scope
    ``install_paths`` entry (``.opencode/commands`` → ``.opencode``).

    **The walk is bounded on purpose.** It stops at the worktree root — the first
    ancestor holding a ``.git`` — or at the user's home, whichever comes first.
    Climbing past either reads a tree the project does not belong to, and
    answering with somebody else's declaration is exactly the false positive this
    whole probe is arranged to avoid.
    """
    start = Path(os.path.abspath(
        str(project_root) if project_root is not None else os.getcwd()
    ))
    names: List[str] = []
    for raw in entry["install_paths"].get(SCOPE_PROJECT) or []:
        if _is_user_rooted(raw):
            continue
        try:
            text = checked_entry(raw)
        except Refused:
            continue
        head = next(
            (segment for segment in re.split(r"[/\\]", text) if segment), ""
        )
        if head and head not in names:
            names.append(head)
    if not names:
        return []
    home = user_home(env)
    dirs: List[Path] = []
    for ancestor in [start, *start.parents]:
        dirs.extend(ancestor / name for name in names)
        if ancestor == home or (ancestor / ".git").exists():
            break
    return dirs


def _config_files(
    host_id: str,
    entry: Dict[str, Any],
    *,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> List[Path]:
    """Every file a declaration could live in, in probe order — environment first.

    The probe has to read the set the host's own installer is driven from, and
    ``install_paths`` cannot express all of it. Three sources have no command
    directory to be derived from, and all three are live:

    * ``$<HOST>_CONFIG`` — an explicit config **file**, read *instead of* the
      per-user one, so a probe ignoring it reads a config the host is not.
    * ``$<HOST>_CONFIG_DIR`` — the same redirect, one level up.
    * ``~/.<host>`` — the per-user directory that holds config but no commands.

    Missing them was not a quiet gap. A user declaring the package in any of them
    got ``route is None``, which makes row 1 fail with the ``install-host``
    repair — telling them to write the duplicate **file** route the shadowing
    note exists to prevent. Environment first, then the project tree, then the
    directories ``install_paths`` implies, then the per-user directory.
    """
    environment = os.environ if env is None else env
    file_var, dir_var = _config_env_names(host_id)
    files: List[Path] = []
    seen: set = set()

    def add(candidate: Path) -> None:
        resolved = Path(os.path.abspath(str(candidate)))
        if resolved not in seen:
            seen.add(resolved)
            files.append(resolved)

    def expanded(value: str) -> Path:
        # ``~`` against the *injected* home, never the interpreter's: this probe
        # is called with a temp ``env`` in tests and under a redirected ``$HOME``
        # in the container, and ``os.path.expanduser`` would answer for neither.
        if value == "~" or value[:2] in ("~/", "~\\"):
            return _join(user_home(environment), value[1:].lstrip("/\\"))
        return Path(os.path.abspath(value))

    explicit = (environment.get(file_var) or "").strip()
    if explicit:
        # A file, named by the user: its basename is theirs, not the host id's.
        add(expanded(explicit))

    dirs: List[Path] = []
    redirected = (environment.get(dir_var) or "").strip()
    if redirected:
        dirs.append(expanded(redirected))
    dirs.extend(_project_config_dirs(entry, env=env, project_root=project_root))
    dirs.extend(_config_dirs(host_id, entry, env=env, project_root=project_root))
    dirs.append(user_home(environment) / f".{host_id}")

    for directory in dirs:
        for suffix in (".json", ".jsonc"):
            add(directory / f"{host_id}{suffix}")
    return files


def _cache_root(
    host_id: str, *, env: Optional[Dict[str, str]] = None
) -> Optional[Path]:
    """Where the host's package installer extracts to.

    ``$XDG_CACHE_HOME/<host>`` when set, else ``~/.cache/<host>``. **This is the
    POSIX formula and it is the only one computed** — whether a host roots its
    cache under ``%LOCALAPPDATA%`` on Windows is unverified, so name the
    consequence rather than discover it: on a Windows machine whose cache lives
    elsewhere, a genuinely installed package route stats as missing and is
    reported as *declared but not resolved*. That is the wrong posture but the
    safe one — the note still warns about a declaration the user really has, and
    it never invents a live route or a repair line.
    """
    environment = os.environ if env is None else env
    xdg = environment.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / host_id
    home = environment.get("HOME") or environment.get("USERPROFILE")
    if not home:
        return None
    return Path(home) / ".cache" / host_id


def _npm_payload_path(
    host_id: str, spec: str, *, env: Optional[Dict[str, str]] = None
) -> Optional[Path]:
    """``<cache>/packages/<normalized spec>/node_modules/<name>``.

    **The innermost component is load-bearing, not decoration.** Measured: the
    spec directory is created *before* resolution is attempted and survives every
    failure as an empty directory — offline, and online against a spec the
    registry 404s. A probe stopping one directory short would report a live route
    for a package that does not exist on the registry at all, which is precisely
    the posture every reader is in before the first publish.

    The directory is the **normalized** spec, not the config string:
    ``"opencode-multi-llm"`` caches at ``…@latest``, and a scoped name nests.
    """
    root = _cache_root(host_id, env=env)
    if root is None:
        return None
    normalized = spec if "@" in spec.lstrip("@") else f"{spec}@latest"
    return root / "packages" / normalized / "node_modules" / _package_name(spec)


#: One probe per registry. Keyed on the ``package.registry`` discriminator so a
#: second host on a second registry adds a row rather than a branch — and
#: :func:`package_route` refuses an unkeyed registry rather than probing ``None``,
#: which is what makes the row mandatory instead of merely conventional.
_PAYLOAD_PROBES: Dict[str, Any] = {"npm": _npm_payload_path}


def _npm_route(
    host_id: str,
    entry: Dict[str, Any],
    package: Dict[str, Any],
    *,
    env: Optional[Dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> Optional[PackageRoute]:
    """Is a package route *declared*, and did it resolve? Config first, cache second.

    **Detection order matters, and a cache glob would get it backwards.** An
    extracted cache tree is not evidence of an install: uninstalling is deleting
    the config line and it leaves that tree behind forever, every version ever
    pinned stays next to the current one, and a package can be extracted for a
    different project's config. A glob would report a live route for all three —
    and since the entire purpose of this probe is to warn about *shadowing*, a
    false shadowing warning is worse than no warning at all.

    So: find the declaration in the merged config first. No entry, no route —
    nothing is stat-ed and the output is byte-unchanged from what it was. Only
    then normalize that entry's spec and stat exactly one computed location.
    """
    probe = _PAYLOAD_PROBES["npm"]
    key = package["config_key"]
    wanted = package["name"]

    for config in _config_files(
        host_id, entry, env=env, project_root=project_root
    ):
        declared = _declared_spec(config, key, wanted)
        if declared is None:
            continue
        payload = probe(host_id, declared, env=env)
        return PackageRoute(
            spec=declared,
            name=_package_name(declared),
            payload=payload,
            resolved=bool(payload and payload.is_dir()),
            declared_in=config,
        )
    return None


def _declared_spec(config: Path, key: str, wanted: str) -> Optional[str]:
    """The spec in *config*'s *key* list whose package name is *wanted*."""
    if not config.is_file():
        return None
    try:
        raw = config.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        document = json.loads(_strip_jsonc(raw))
    except (ValueError, TypeError):
        # A config we cannot parse is not a declaration we can act on, and a
        # --check that died on someone's trailing comma would be worse than one
        # that stays quiet about a route it could not read.
        return None
    if not isinstance(document, dict):
        return None
    declared = document.get(key)
    if not isinstance(declared, list):
        return None
    for item in declared:
        if isinstance(item, str) and _package_name(item) == wanted:
            return item
    return None
