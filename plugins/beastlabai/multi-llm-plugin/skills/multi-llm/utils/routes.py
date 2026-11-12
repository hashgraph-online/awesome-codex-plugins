"""How a printed command is spelled for this process: its route and its plan.

The ``next_command`` route key a host's template is picked by
(:func:`resolve_route`, the only reader of a route signal), the plan argument as
a command shows it (:func:`quote_plan_arg`, and :func:`recorded_plan_spelling`
for a spelling read back from a run's folder), and the template's slot and
resume flag. Every command builder reads them here: ``next_phase``, the
stop-answer builders of the write phases, ``cli_common``'s follow-up commands
and ``detach``'s run record (docs/development/dispatcher.md#import-layers).
``next_phase`` re-exports every name.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple, Union


#: The one slot every ``next_command`` template ends with (schema pattern
#: ``^[^{}]+\{args\}$``). Filled with ``str.replace``, never ``str.format``.
ARGS_SLOT = "{args}"


#: Appended when the phase a command names is recorded ``in_progress``: a bare
#: re-invocation of a write phase starts it over. Never copied from the finished invocation's argv.
RESUME_FLAG = "--resume"


#: The route key of a plain-skill install, told apart from the plugin by the
#: dispatcher's own skill root rather than by any environment variable.
SKILL_ROUTE = "skill"


#: Whitespace-free path components in ``install_paths`` that stand for a
#: variable prefix (``$HOME``, ``%USERPROFILE%``, ``~``); the tail after the
#: last one is what a skill root is compared against.
_PLACEHOLDER_PREFIXES = ("$", "%", "~")


def _skill_module(name: str):
    """Import a top-level skill module (``modes``, ``check_workflow_prerequisites``)."""
    return importlib.import_module(name)


def _host_capabilities():
    # Lazy: host_capabilities imports cli_common, which an emitter living in
    # cli_common may import this module from.
    from . import host_capabilities

    return host_capabilities


def quote_plan_arg(plan_arg: str) -> str:
    """The plan path as it appears in the command: quoted for a model, not a shell.

    * no whitespace and no quote character → bare;
    * contains ``"`` but not ``'`` → wrapped in single quotes;
    * contains both → wrapped in double quotes as it is (no unescaped spelling
      exists, and no route is claimed to round-trip it);
    * otherwise (whitespace and/or ``'``) → wrapped in double quotes.

    Nothing inside is ever escaped (a Windows path keeps every backslash), and a
    quote character already in ``plan_arg`` is part of the value — it only
    decides which wrapping applies.
    """
    has_double = '"' in plan_arg
    has_single = "'" in plan_arg
    if has_double and not has_single:
        return f"'{plan_arg}'"
    if has_double or has_single or any(ch.isspace() for ch in plan_arg):
        return f'"{plan_arg}"'
    return plan_arg


#: What a plan spelling read back from a file may be made of: the characters
#: ``shlex.quote`` leaves bare, plus a plain space — which
#: :func:`quote_plan_arg` wraps in double quotes, inside which none of these is
#: special. No control character, quote, ``$``, backtick, ``\``, ``;``, ``&``,
#: ``|``, redirection, glob or ``~``.
_RECORDED_SPELLING = re.compile(r"[\w@%+=:,./ -]+", re.ASCII)


def recorded_plan_spelling(recorded: Any, plan: str) -> Optional[str]:
    """A typed plan spelling read back from a phase's ``.status.json``, or ``None``.

    The run's output folder is writable by every jailed batch (a standing
    user decision), so a ``plan_arg`` read from it — a continuation hand-off's
    (``multi_llm._remember_plan_spelling``) or a detached run record's — is
    untrusted, and it reaches a printed command verbatim. It is returned only
    when it

    * is a non-empty string, does not start with ``-``, and is made only of
      :data:`_RECORDED_SPELLING`'s characters, so a printed command can
      neither run a substitution nor split into two lines; and
    * resolves, from this process's cwd and with ``strict=True``, to the same
      existing file as *plan*. Non-strict ``realpath`` collapses a component
      that does not exist against a later ``..``, so
      ``plans/$(touch${IFS}pwned)/../foo.md`` "named" ``plans/foo.md``.

    Otherwise the caller prints the plan as it received it.
    """
    if not isinstance(recorded, str) or not recorded or recorded.startswith("-"):
        return None
    if not _RECORDED_SPELLING.fullmatch(recorded):
        return None
    if not _steps_back_only_out_of_dirs(recorded):
        return None
    try:
        same = os.path.realpath(recorded, strict=True) == os.path.realpath(
            plan, strict=True
        )
    except (OSError, ValueError):
        return None
    return recorded if same else None


def _steps_back_only_out_of_dirs(spelling: str) -> bool:
    """Whether every component *spelling* steps back out of with ``..`` is an
    existing directory. POSIX ``realpath(strict=True)`` already refuses one
    that is not; Windows' collapses ``missing/..`` before it looks at the disk."""
    head = spelling
    while True:
        head, tail = os.path.split(head)
        if not tail:
            return True
        if tail == os.pardir and head and not os.path.isdir(head):
            return False


def _path_parts(path: str) -> Tuple[str, ...]:
    """Path components split on either separator, so a Windows path compares too."""
    return tuple(part for part in re.split(r"[\\/]+", path) if part and part != ".")


def _install_tail(entry: str) -> Tuple[str, ...]:
    """An ``install_paths`` entry's components after its last variable prefix."""
    parts = _path_parts(entry)
    for index in range(len(parts) - 1, -1, -1):
        if parts[index].startswith(_PLACEHOLDER_PREFIXES):
            return parts[index + 1:]
    return parts


def _is_skill_install(host_id: str, skill_root: Union[str, Path]) -> bool:
    """Whether *skill_root* ends with one of *host_id*'s ``install_paths`` entries.

    Judged by the root's own path, never its ``realpath``: a copy (or a
    symlink) under ``.claude/skills/multi-llm`` is a plain skill whatever it
    points at, and the plugin cache (or a dev checkout linked into it) is not.
    """
    root = _path_parts(str(skill_root))
    install_paths = _host_capabilities().entry(host_id).get("install_paths") or {}
    for entries in install_paths.values():
        for entry in entries or ():
            tail = _install_tail(str(entry))
            if tail and len(root) >= len(tail) and root[-len(tail):] == tail:
                return True
    return False


def resolve_route(
    host_id: str,
    *,
    environ: Optional[Mapping[str, str]] = None,
    skill_root: Optional[Union[str, Path]] = None,
    stderr=None,
    recorded: Optional[str] = None,
) -> Optional[str]:
    """The ``next_command`` route key for this process, or ``None`` for ``default``.

    The only reader of a route signal; every
    emitter calls it once and passes the result to :func:`next_phase_commands`.

    * A host whose ``next_command`` carries a ``skill`` key (claude-code) is
      told apart by the dispatcher's own skill root (``cli_common._SKILL_DIR``
      unless *skill_root* is given): ``skill`` when that root ends with one of
      the host's ``install_paths`` entries, else ``None`` (the plugin). The
      route variable is ignored there, and saying so costs one stderr line when
      it is set.
    * Any other host reads ``modes.ROUTE_ENV``, which the tool servers set.
      Unset is ``None``, silently. A value is honoured only when it is a member
      of ``modes.TOOL_ROUTES`` **and** a key of the host's ``next_command``
      cell; any other value (empty, a typo, ``skill``, a product name, a tool
      route this host has no cell for) is ``None`` plus one stderr line naming
      the ignored value.
    * *recorded* is the route the run whose commands are printed was started
      on (:func:`recorded_route`): when the environment names
      none, it is honoured under the same test, silently. Live run 10: a
      shell's ``status --host codex`` spelled a run the Codex plugin's tool
      had started in the file shim's words. The environment still wins, and
      a host that reads its route from the skill root ignores it.

    *environ* defaults to ``os.environ`` and *stderr* to ``sys.stderr``.
    """
    modes = _skill_module("modes")
    env = os.environ if environ is None else environ
    stream = sys.stderr if stderr is None else stderr
    capabilities = _host_capabilities()
    routes = capabilities.next_command_routes(host_id)
    value = env.get(modes.ROUTE_ENV)

    if SKILL_ROUTE in routes:
        if value is not None:
            print(
                f"multi-llm: ignoring {modes.ROUTE_ENV}={value!r}: host "
                f"'{host_id}' takes its next-command route from the skill root, "
                "not the environment",
                file=stream,
            )
        if skill_root is None:
            # Imported here to keep next_phase, which loads this module, light.
            from . import cli_common

            skill_root = cli_common._SKILL_DIR
        return SKILL_ROUTE if _is_skill_install(host_id, skill_root) else None

    if value is None:
        if recorded in modes.TOOL_ROUTES and recorded in routes:
            return recorded
        return None
    if value in modes.TOOL_ROUTES and value in routes:
        return value
    honoured = [route for route in modes.TOOL_ROUTES if route in routes]
    print(
        f"multi-llm: ignoring {modes.ROUTE_ENV}={value!r} for host '{host_id}' "
        f"(honoured here: {', '.join(honoured) or 'none'}); using the "
        f"'{capabilities.DEFAULT_ROUTE_KEY}' next-command spelling",
        file=stream,
    )
    return None
