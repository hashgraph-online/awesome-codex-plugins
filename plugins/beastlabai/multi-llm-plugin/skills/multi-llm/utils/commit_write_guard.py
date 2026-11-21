"""The commit write policy's write legs: what a commit review's apply
re-checks before each batch is dispatched.

The apply guard (``utils/commit_apply.py``) decides once and saves what
each fix file must still hold; these helpers read it back, and the
scheduler's ``_dispatch_one``, ``util write-prompt`` and ``util
batch-done`` share them. The lowest of the scheduler's helper modules: it
imports none of the others.

``utils.write_batch_scheduler`` re-exports every name defined here for
reading only: patch one here, never through the scheduler
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import json
import os
import posixpath
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from . import git_utils as _git_utils
from .subagent_tasks import declared_file_set
from .write_safety import file_sha256
from .commit_range import pinned_record
from .code_fix_batcher import fix_member_ids


# ---------------------------------------------------------------------------
# The commit write policy's write legs (plans/review-commits.md §2.7: "Every
# batch is re-checked immediately before it is dispatched" and "The commit
# write policy"). The apply guard (``utils/commit_apply.py``) decides once,
# before human decisions and batching, and saves under the pinned record
# (``commit_range`` or ``head_ref``) the content each fix file must still
# have and the protected set. These helpers are what the executor's
# ``_dispatch_one``, ``util write-prompt`` and ``util batch-done`` share. Every
# one of them is a no-op without a guard, and ``utils.commit_apply`` is only
# imported once one exists, so a run on a plan is untouched by any of this.
# ---------------------------------------------------------------------------

#: The one write kind the apply guard governs: its groups are review fixes.
COMMIT_GUARD_KIND = "apply_code_fixes"

#: The phase output whose batches carry each fix's ``files`` on a commit
#: review's apply (``ApplyCodeFixesOrchestrator.format_item_for_output``:
#: every distinct file the fix's group names, in git's form, primary first).
#: Both legs read a batch's fix files from it: the materialized write task
#: carries only the batch's primary file (``declared_files``).
ORCHESTRATOR_OUTPUT_FILENAME = "orchestrator_output.json"


def commit_guard_of(state: Any, kind: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The live apply guard (``<pinned record>.guard``) of a raw state dict,
    to mutate in place, or ``None``: no dict, no pinned record
    (``commit_range.pinned_record``), no guard in it, or a *kind* the guard
    does not govern."""
    if kind is not None and kind != COMMIT_GUARD_KIND:
        return None
    if not isinstance(state, dict) or not (
        "commit_range" in state or "head_ref" in state
    ):
        return None
    record = pinned_record(state)
    guard = record.get("guard") if isinstance(record, Mapping) else None
    return guard if isinstance(guard, dict) and guard else None


def load_commit_apply() -> Any:
    """``utils.commit_apply``, imported only once a guard exists."""
    # Imported at call time on purpose: tests stand a fake `utils.commit_apply` in `sys.modules` and
    # reach it only through this call.
    from . import commit_apply
    return commit_apply


def commit_head7(guard: Mapping[str, Any]) -> str:
    """The reviewed head's seven-character spelling every commit line uses."""
    return str(guard.get("head") or "")[:7]


def commit_protected_rule(guard: Mapping[str, Any]) -> str:
    """The rule text of the protected set's deny layer: ``changed since
    reviewed commit <head7>``."""
    return f"changed since reviewed commit {commit_head7(guard)}"


def load_orchestrator_batches(phase_dir: Union[str, Path]) -> Optional[List[Any]]:
    """The ``batches`` of ``<phase_dir>/orchestrator_output.json``, or
    ``None`` when the file is absent or cannot be read."""
    try:
        document = json.loads(
            (Path(phase_dir) / ORCHESTRATOR_OUTPUT_FILENAME).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None
    batches = document.get("batches") if isinstance(document, dict) else None
    return batches if isinstance(batches, list) else None


def batch_fixes_for(
    task: Mapping[str, Any], batches: Optional[Sequence[Any]],
) -> Optional[List[Dict[str, Any]]]:
    """The fixes of *task*'s batch in *batches* (``orchestrator_output.json``'s):
    the batch at the task's ``batch_index`` when its member ids
    (``code_fix_batcher.fix_member_ids``) are the task's ``expected_ids``,
    else the first batch whose are; ``None`` when none matches (an output
    from another run is never read as this one's)."""
    if not batches:
        return None
    expected = [str(item) for item in task.get("expected_ids") or []]
    index = task.get("batch_index")
    ordered = list(batches)
    if isinstance(index, int) and 0 <= index < len(ordered):
        ordered.insert(0, ordered[index])
    for batch in ordered:
        fixes = batch.get("fixes") if isinstance(batch, Mapping) else None
        if not isinstance(fixes, list) or not all(isinstance(f, dict) for f in fixes):
            continue
        if expected and fix_member_ids(fixes) == expected:
            return fixes
    return None


def commit_group_files(
    task: Mapping[str, Any], *, repo_root: Optional[str] = None,
    fixes: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, List[str]]:
    """``{group id: [fix files]}`` for one apply-code-fixes write task, each
    file repo-relative in git's form (``git_utils.git_path``): the batch's
    declared (primary) file, then every file the group's fix names in
    *fixes* (:func:`batch_fixes_for`: its ``files``, else its ``file``).
    Without *fixes* a group's fix files are the declared ones."""
    def form(path: Any) -> str:
        try:
            name = _git_utils.git_path(str(path), repo_root)
        except Exception:  # noqa: BLE001 - a name is still a name
            name = str(path).replace(os.sep, "/")
        # `..` resolved lexically, as the guard's own names are
        # (`commit_apply._git_name`), so `docs/../a.py` meets its `a.py` key.
        if name and not os.path.isabs(name) and ".." in name.split("/"):
            name = posixpath.normpath(name)
        return name

    declared: List[str] = []
    for path in declared_file_set(dict(task)):
        name = form(path)
        if name and name not in declared:
            declared.append(name)
    named: Dict[str, List[str]] = {}
    if fixes:
        for member_id, fix in zip(fix_member_ids([dict(f) for f in fixes]), fixes):
            listed = fix.get("files")
            if not isinstance(listed, (list, tuple)):
                listed = [fix.get("file")]
            named[str(member_id)] = [
                str(path) for path in listed if isinstance(path, str) and path.strip()
            ]
    groups: Dict[str, List[str]] = {}
    for group_id in task.get("expected_ids") or []:
        group_id = str(group_id)
        if not group_id:
            continue
        files = list(declared)
        for path in named.get(group_id, ()):
            name = form(path)
            if name and name not in files:
                files.append(name)
        groups[group_id] = files
    return groups


def commit_recheck_failing(
    guard: Mapping[str, Any], groups: Mapping[str, Sequence[str]], *,
    repo_root: str, commit_apply: Any = None,
) -> List[str]:
    """The fix files of *groups* the pre-dispatch re-check fails, in the
    batch's order: ``commit_apply.recheck_files``' answer over every fix
    file the batch declares (each against its saved ``head`` or ``batch``
    identity), plus each one in the saved protected set (§2.7, "Every
    target, before dispatch": a fix that names a protected path is skipped
    like a guard skip)."""
    commit_apply = commit_apply or load_commit_apply()
    files: List[str] = []
    for group_files in groups.values():
        for path in group_files:
            if path not in files:
                files.append(path)
    if not files:
        return []

    def sha256_of(path: str) -> Optional[str]:
        return file_sha256(path if os.path.isabs(path) else os.path.join(repo_root, path))

    failing = {
        str(path) for path in commit_apply.recheck_files(
            guard, files, cwd=repo_root, file_sha256=sha256_of,
        ) or ()
    }
    protected = guard.get("protected")
    if isinstance(protected, Mapping):
        failing |= {path for path in files if path in protected}
    return [path for path in files if path in failing] + sorted(failing - set(files))


def commit_stale_split(
    groups: Mapping[str, Sequence[str]], failing: Sequence[str],
) -> Tuple[List[str], List[str]]:
    """``(skipped, held back)``: the groups that name a failing file, and
    the batch's other groups, which are held back rather than lost."""
    bad = set(failing)
    skipped = [gid for gid, files in groups.items() if bad.intersection(files)]
    return skipped, [gid for gid in groups if gid not in skipped]


def commit_stale_line(
    task_id: str, failing: Sequence[str], guard: Mapping[str, Any], *,
    marker: str = "[COMMIT_FIXES_STALE]",
) -> str:
    """``[COMMIT_FIXES_STALE] <task id>: <files> changed since reviewed
    commit <head7>``, both legs' line for a batch the re-check stops."""
    return (
        f"{marker} {task_id}: {', '.join(failing)} changed since reviewed "
        f"commit {commit_head7(guard)}"
    )


def commit_stale_reason(
    failing: Sequence[str], guard: Mapping[str, Any], *, held: bool,
) -> str:
    """The reason a stopped batch is recorded ``failed`` with: ``held back:
    batched with <files>`` when some of its groups passed (a ``--resume``
    re-batches them without the skipped ones), else the skip itself."""
    if held:
        return f"held back: batched with {', '.join(failing)}"
    return f"skipped: {', '.join(failing)} {commit_protected_rule(guard)}"
