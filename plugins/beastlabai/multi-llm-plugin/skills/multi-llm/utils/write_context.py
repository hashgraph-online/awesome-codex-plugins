"""The facts one write phase's run is about, shared by the scheduler's collaborators.

``WriteBatchScheduler`` hands a :class:`RunContext` to each collaborator it
composes (``write_verify.VerifyStep`` and ``VerifyCommand``,
``write_sweep.ContainmentSweep``, ``write_eta.EtaLines``,
``write_reports.WriteReports``, ``write_stop.StopAccount``,
``batch_prompt_builder.BatchPromptBuilder``, ``write_commit_leg.CommitGuardLeg``,
``write_check_holds.CheckHolds``, ``write_resume.ResumeEvidence``) instead of
sharing ``self`` with them: what a collaborator may read about the run is the
list of fields below, and nothing it does can reassign one
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).

The objects behind the fields are the scheduler's own, not copies, and the
scheduler never rebinds one after construction. ``state`` is
the run's one ``StateManager``, the only writer of ``state.json`` for the run: a
collaborator writes through it, under the lock the scheduler hands it, and never
reloads it; a run without one holds a :class:`NullState`, never ``None``.
``log`` calls the scheduler's current ``log`` at each line, so a caller that
quiets the scheduler's log for a while (``_dispatch_walk``) quiets its
collaborators with it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from .write_safety import safety_dir

#: Write kinds whose ``output_name`` is keyed by the task id
#: (``subagent_tasks.implement_output_name``) rather than a batch position.
#: ``ResumeEvidence.warn_stale_result_files`` (N6) scopes its stale-file sweep to this set:
#: a positional kind's result filenames have never been renamed, so there is
#: no earlier naming to be stale relative to.
_ID_KEYED_WRITE_KINDS = frozenset({"implement"})


class NullState:
    """The run's state when it has none: ``SchedulerOptions.state`` left
    ``None``, which only a unit test does (a real phase always has a
    ``StateManager``, WRITE-11).

    It keeps nothing and writes nothing. Every write is a no-op and every read
    is what a missing state read as: no ``state.json`` dict (``state``) and no
    file (``state_file``), no task status, no phase started or completed, and
    ``get`` gives the default, so ``check_records``' readers find nothing on
    record. It has none of the metric methods, so ``EtaLines`` prints no
    ``[ETA]`` line for it, as for any state that keeps no metrics. Where a
    missing state means something other than an empty one, the reader asks
    (:func:`has_state`, :func:`manager_or_none`): a reader the native leg
    shares reads ``state.json`` on disk when handed ``None``
    (docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
    """

    #: No ``state.json`` dict and no file behind it.
    state: Any = None
    state_file: Any = None

    def get(self, key: str, default: Any = None) -> Any:
        return default

    def set(self, key: str, value: Any) -> None:
        pass

    def save(self) -> None:
        pass

    def reload(self) -> None:
        pass

    def get_task_status(self, task_id: str) -> Optional[str]:
        return None

    def get_all_task_statuses(self) -> Dict[str, str]:
        return {}

    def update_task_status(
        self, task_id: str, status: str, reason: Optional[str] = None,
    ) -> None:
        pass

    def record_dependency_override(self, task_id: str, overridden_deps: List[str]) -> None:
        pass

    def is_phase_started(self, phase: str) -> bool:
        return False

    def is_phase_completed(self, phase: str) -> bool:
        return False

    def completion_predates(self, apply: str, review: str) -> bool:
        return False

    def mark_phase_started(self, phase: str) -> None:
        pass

    def mark_phase_completed(self, phase: str) -> None:
        pass

    def refresh_plan_hash(self) -> None:
        pass


def has_state(state: Any) -> bool:
    """Whether the run holds a state (anything but :class:`NullState`): for a
    reader to which a missing state means something an empty one does not."""
    return state is not None and not isinstance(state, NullState)


def manager_or_none(state: Any) -> Any:
    """*state* for a reader the native leg shares, which reads ``state.json``
    on disk when it is handed ``None``: the run's own state, or ``None`` for a
    run without one."""
    return state if has_state(state) else None


@dataclass(frozen=True)
class RunContext:
    """One write phase's run, as the scheduler resolved it at construction."""

    kind: str
    phase: str
    phase_dir: str
    output_dir: str
    repo_root: str
    anchor: Optional[str]
    tasks: Sequence[Dict[str, Any]]
    state: Any
    policy: Any
    audit: Any
    log: Callable[..., None]
    summary_file: Optional[str]
    dry_run: bool

    @property
    def safety_dir(self) -> str:
        """Where this phase's pre-batch snapshots, rollback store and audit
        log live (``write_safety.safety_dir``), read at each call: a jailed
        repo-wide run claims an out-of-grant directory part-way through."""
        return safety_dir(self.phase_dir)


@dataclass
class Refusals:
    """The tasks one run refused before any runner started, and why.

    A field of the run's ``SchedulerResult`` (``result.refusals``), written by
    the scheduler where it refuses a task and read by everything that words
    the run's ending: the stop, its answers and resume reason, the ``[ETA]``
    lines, the summary and the write mirror.
    """

    #: Tasks this run refused before any runner started (the write policy,
    #: the grant, the snapshot or the census refused them), so the stop says
    #: nothing was dispatched (fix round 13).
    before_dispatch: Set[str] = field(default_factory=set)
    #: The paths ``driver.write_paths`` refused, per task refused for it
    #: before dispatch: what its way forward names (fix round 20).
    policy_paths: Dict[str, List[str]] = field(default_factory=dict)
    #: Each one's rule (``write_safety.PolicyHit``), which its way forward
    #: is worded from (fix round 21: a deny hit names the deny rule).
    policy_hits: Dict[str, List[Any]] = field(default_factory=dict)


def refusals_of(result: Any) -> Refusals:
    """*result*'s refusals, or none for a caller that has no result."""
    return result.refusals if result is not None else Refusals()
