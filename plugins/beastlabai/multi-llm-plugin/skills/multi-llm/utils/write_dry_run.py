"""``--dry-run-subagents``: a write phase's full preflight, zero dispatch (D3l).

:class:`DryRunReport` walks the phase's batches as the loop would and writes
``subagent_dry_run.json`` (:meth:`DryRunReport.write`): per task, the runner it
resolves to, the exact argv rendered (the prompt replaced by its hash,
``redact.redact_argv``), the prompt transport, the profile, its co-schedule
group under the disjointness admission, the runner preflight under the phase's
grant and the rung it recorded, and the write policy's verdict on its declared
files, then the ceilings. It starts no child and writes nothing else, which is
what makes "would this batch have been refused?" answerable before a model is
handed edit access.

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). It
reads the runner preflight through the run's ``write_grant.WriteGrant`` and the
prompt through its ``batch_prompt_builder.BatchPromptBuilder``, and reaches the
scheduler's batch runners and ceiling, its argv rendering and its ceiling
record through callbacks looked up at each call.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import human_task_plan as _human_task_plan
from . import write_context as _write_context
from .provider_registry import parse_model_spec
from .task_outcome import (
    ExecutorError,
    ResultRejected,
)
from .failure_capture import _atomic_write_json
from .runner_selection import profile_for_kind
from .subagent_tasks import (
    SHARED_ARTIFACT_WRITE_KINDS,
    declared_file_set,
    snapshot_file_set,
    preferred_prompt_transport,
    utf16_units,
)
from .write_safety import (
    DRY_RUN_FILENAME,
    PolicyViolation,
    admit_disjoint_groups,
    redact_argv,
    relative_to_root,
)


class DryRunReport:
    """One phase's dry run.

    Built once per run by the scheduler. *grant* and *prompts* are the run's
    ``WriteGrant`` and ``BatchPromptBuilder``; *host_max* the phase's host
    ceiling; the callables reach the scheduler's ``_batch_runners_and_ceiling``,
    ``_render_argv`` and ``_ceiling_record``.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        host_max: Optional[int],
        grant: Any,
        prompts: Any,
        batch_runners_and_ceiling: Callable[..., Tuple[Dict[str, str], int]],
        render_argv: Callable[[str, str, str], List[str]],
        ceiling_record: Callable[[], Tuple[int, int, Dict[str, Optional[int]]]],
    ) -> None:
        self._ctx = ctx
        self._host_max = host_max
        self._grant = grant
        self._prompts = prompts
        self._batch_runners_and_ceiling = batch_runners_and_ceiling
        self._render_argv = render_argv
        self._ceiling_record = ceiling_record

    def write(
        self,
        ordered: Sequence[Tuple[int, List[Dict[str, Any]]]],
        plan: _human_task_plan.HumanTaskPlan,
    ) -> str:
        """``--dry-run-subagents``: full preflight, zero dispatch (D3l).

        Resolves the runner, renders the exact argv per task, checks the prompt
        transport, applies the profile, the disjointness admission and the write
        policy — then writes the report and starts no child. It is what makes
        "would this batch have been refused?" answerable *before* a model is handed
        edit access.
        """

        entries: List[Dict[str, Any]] = []
        for batch_index, batch_tasks in ordered:
            # As `_run_batch`: one resolution per batch, for its ceiling and
            # each entry's runner.
            runners, ceiling = self._batch_runners_and_ceiling(batch_tasks)
            groups = admit_disjoint_groups(
                batch_tasks, ceiling=ceiling, root=self._ctx.repo_root,
            )
            group_of = {
                str(task.get("task_id", "")): position
                for position, group in enumerate(groups)
                for task in group
            }
            for task in batch_tasks:
                task_id = str(task.get("task_id", ""))
                entry: Dict[str, Any] = {
                    "task_id": task_id,
                    "kind": self._ctx.kind,
                    "batch_index": batch_index,
                    "co_schedule_group": group_of.get(task_id),
                    "profile": profile_for_kind(self._ctx.kind),
                    "cwd": self._ctx.repo_root,
                    "sandbox_root": self._ctx.repo_root,
                    "declared_files": [
                        relative_to_root(p, self._ctx.repo_root)
                        for p in declared_file_set(task)
                    ],
                    "snapshot_files": [
                        relative_to_root(p, self._ctx.repo_root)
                        for p in snapshot_file_set(task)
                    ],
                }
                if plan.is_skipped(task_id) or task.get("executor_role") == "human":
                    entry["would_dispatch"] = False
                    entry["reason"] = plan.skipped.get(
                        task_id, "executor_role: human — never dispatched"
                    )
                    entries.append(entry)
                    continue
                try:
                    prompt = self._prompts.dispatched_prompt(task)
                except ResultRejected as exc:
                    entry["would_dispatch"] = False
                    entry["reason"] = exc.message
                    entries.append(entry)
                    continue
                runner = runners[task_id]
                entry["runner"] = runner
                provider_name, _ = parse_model_spec(runner, anchor=self._ctx.anchor)
                entry["prompt_transport"] = preferred_prompt_transport(provider_name)
                entry["prompt_utf16_units"] = utf16_units(prompt)
                try:
                    info = self._grant.preflight(
                        runner, entry["profile"],
                        # D3l: this flag renders commands and starts no child, so
                        # the nested-exec preflight keeps the declared verdict
                        # (a `denied` host is still refused) and skips its
                        # throwaway dispatch, which is a real turn.
                        probe_nested=False,
                    )
                    entry["runner_version"] = info["version"]
                    rung = self._grant.recorded_rung(runner, entry["profile"])
                    if rung:
                        entry["sandbox_rung"] = rung
                except ExecutorError as exc:
                    entry["would_dispatch"] = False
                    entry["reason"] = exc.message
                    entries.append(entry)
                    continue
                entry["argv"] = redact_argv(
                    self._render_argv(runner, prompt, entry["profile"]), prompt
                )
                try:
                    self._ctx.policy.check(entry["declared_files"], when="pre-dispatch")
                except PolicyViolation as exc:
                    entry["would_dispatch"] = False
                    entry["reason"] = exc.message
                    entries.append(entry)
                    continue
                entry["would_dispatch"] = True
                entries.append(entry)

        path = os.path.join(self._ctx.phase_dir, DRY_RUN_FILENAME)
        effective, configured, provider_limits = self._ceiling_record()
        # Same containment as every other executor write (see ``WriteReports.write_report``).
        _atomic_write_json(path, {
            "dry_run_version": 1,
            "kind": self._ctx.kind,
            "phase": self._ctx.phase,
            "repo_root": self._ctx.repo_root,
            "ceilings": {
                "effective_write_parallelism": effective,
                "driver_max_concurrent_write_subagents": configured,
                "provider_max_concurrent": provider_limits,
                "host_max_concurrent_subagents": self._host_max,
                "shared_artifact_phase": self._ctx.kind in SHARED_ARTIFACT_WRITE_KINDS,
            },
            "write_paths": self._ctx.policy.to_dict(),
            "human_task_strategy": plan.strategy,
            "tasks": entries,
        })
        return path
