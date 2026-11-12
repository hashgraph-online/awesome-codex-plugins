"""The prompt one write dispatch is sent, on the executor leg (D2g, fix round 17).

:class:`BatchPromptBuilder` turns one materialized write task into the text its
runner receives: the task's prompt with the prior changes bound
(:meth:`BatchPromptBuilder.dispatched_prompt`), the result contract and the
known checks it is told to run (:meth:`BatchPromptBuilder.with_result_contract`,
:meth:`BatchPromptBuilder.known_checks_section`), the scope policy's refusal
(:meth:`BatchPromptBuilder.scope_refusal`), and the copy of what was sent kept
in the pinned phase folder (:meth:`BatchPromptBuilder.keep_dispatched_prompt`).
The texts are ``batch_prompt``'s, shared with the native leg's ``util
write-prompt`` (docs/development/write-scheduler.md#prompt-order).

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). It
writes the known checks it told each task into the scheduler's
``told_checks``, which the reply's classification reads; its own state is the
pinned phase folder and the warnings already given.
"""

from __future__ import annotations

import os
import threading
from typing import Any, Dict, List, Optional, Set, Tuple

from . import batch_prompt as _batch_prompt
from . import check_records as _check_records
from . import known_checks as _known_checks
from . import prompt_files as _prompt_files
from . import write_context as _write_context
from .subagent_tasks import APPLY_WRITE_KINDS


class BatchPromptBuilder:
    """The text one write dispatch is sent, and where it is kept.

    Built once per run by the scheduler. *told_checks* is the scheduler's
    ``_told_checks`` (``task id -> the known check commands its prompt
    listed``), filled here and read by the reply's classification.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        plan_file: Optional[str],
        scope_policy: Optional[str],
        scope_baseline_id: Optional[str],
        told_checks: Dict[str, List[str]],
    ) -> None:
        self._ctx = ctx
        self._plan_file = plan_file
        self._scope_policy = scope_policy
        self._scope_baseline_id = scope_baseline_id
        self._told_checks = told_checks
        #: Fix round 17: the phase dir the dispatched prompts are kept in,
        #: pinned (``prompt_files.pin_phase_dir``) before any batch of this
        #: run can replace it — a jailed repo-wide batch can write the phase
        #: dir, and this process is not jailed. ``None`` until it exists.
        self.pin: Optional[_prompt_files.PhasePin] = None
        self._pin_lock = threading.Lock()
        #: The ``(task id, leftover entry)`` pairs already warned about
        #: (:meth:`warn_prompt_keep`).
        self._keep_warnings: Set[Tuple[str, Optional[str]]] = set()

    def dispatched_prompt(self, task: Dict[str, Any]) -> str:
        """The prompt that actually goes to the runner, bound *now*.

        :func:`bind_prior_changes` over this phase's log; see it for the
        contract. Kept as a method so the dispatch site reads as before.
        An implement task gets the note about the checks upstream of it
        whose findings the user accepted (fix round 14), read from the
        state as it is at dispatch, as ``util write-prompt`` reads it.
        """
        accepted: List[Tuple[str, str, List[str]]] = []
        if self._ctx.kind == "implement":
            accepted = _check_records.accepted_upstream_checks(
                self._ctx.tasks, str(task.get("task_id") or ""), self._ctx.state,
            )
        return _batch_prompt.bind_prior_changes(
            task, output_dir=self._ctx.output_dir, phase=self._ctx.phase,
            accepted_checks=accepted,
            state=_write_context.manager_or_none(self._ctx.state),
        )

    def scope_refusal(self, task: Dict[str, Any]) -> Optional[str]:
        """Why an apply task must not dispatch under the effective scope
        policy (``scope_apply.stale_task_refusal``), else ``None``."""
        if self._ctx.kind not in APPLY_WRITE_KINDS:
            return None
        scope = _batch_prompt._scope_apply()
        if self._scope_policy is not None:
            policy, baseline = self._scope_policy, self._scope_baseline_id
        else:
            state = getattr(self._ctx.state, "state", None)
            if not isinstance(state, dict):
                state = _batch_prompt._state_on_disk(self._ctx.output_dir)
            policy, baseline = scope.effective_from_state(
                state if isinstance(state, dict) else {}, self._ctx.phase)
        return scope.stale_task_refusal(task, policy, baseline)

    def with_result_contract(self, task: Dict[str, Any], prompt: str) -> str:
        """Append the write-batch result contract (:func:`with_result_contract`),
        with an apply-code-fixes batch's known checks (fix round 20)."""
        return _batch_prompt.with_result_contract(
            self._ctx.kind, task, prompt, checks_section=self.known_checks_section(task),
        )

    def known_checks(self) -> List[Tuple[str, str]]:
        """The repository's known check commands
        (:func:`known_checks.known_check_commands`), read now from the state
        this run holds (else the plan dir's ``state.json``), as ``util
        write-prompt`` reads them on the native leg. Never run here."""
        return _known_checks.known_check_commands(
            self._ctx.output_dir, plan_file=self._plan_file,
            repo_root=self._ctx.repo_root,
            state=_write_context.manager_or_none(self._ctx.state),
        )

    def known_checks_section(self, task: Dict[str, Any]) -> str:
        """Fix round 20 (live run 8, Codex racing 08): an apply-code-fixes
        batch is told the repository's known check commands, to run after its
        edits, and which earlier batch of the run reported a failing check.
        ``""`` for every other kind. The commands told to each batch are kept
        (``_told_checks``), so its reply's ``listed`` is read against them."""
        if self._ctx.kind != "apply_code_fixes":
            return ""
        task_id = str(task.get("task_id") or "")
        try:
            checks = self.known_checks()
            state = _write_context.manager_or_none(self._ctx.state)
            earlier = _known_checks.earlier_batch_check_failures(
                state if state is not None else _known_checks.read_state(self._ctx.output_dir),
                self._ctx.tasks, task_id,
            )
        except Exception:  # noqa: BLE001 - advisory: the batch is still dispatched
            checks, earlier = [], []
        self._told_checks[task_id] = [command for command, _where in checks]
        return _known_checks.known_checks_section(checks, earlier)

    def pinned_phase_dir(self) -> "_prompt_files.PhasePin":
        """The phase dir as pinned for the prompt files (fix round 17): its
        ``realpath`` inside the repository root and its identity, taken once
        — at construction, or on the first prompt kept when the phase dir did
        not exist yet. Raises ``OSError`` naming why it cannot be pinned."""
        with self._pin_lock:
            pin = self.pin
            if pin is None:
                pin = _prompt_files.pin_phase_dir(self._ctx.phase_dir, self._ctx.repo_root)
                self.pin = pin
            return pin

    def keep_dispatched_prompt(
        self, task_id: str, attempt: int, sent: str, batch_prompt: str
    ) -> None:
        """Keep the prompt this attempt sends, beside the native leg's.

        Run 6 (#10b): on the executor leg the prompt a task was dispatched
        with was in no plan artifact — the audit line keeps its sha256 and
        length only — so T007's prompt with "## Check findings the user
        accepted" could not be audited on Codex at all, and on OpenCode only
        from the host's session database. The native leg's ``util
        write-prompt`` always wrote ``{phase}/prompts/<id>.prompt.txt``; this
        writes the same file, the same bytes, just before the child starts.

        * The batch's prompt **overwrites** the file on every dispatch, as a
          ``--resume`` rebinds the native one: it is what the task was last
          told, and the audit log's ``prompt_sha256`` on that ``dispatched``
          line verifies it.
        * An attempt that sends something else (a report re-ask, rule 9's
          re-send) goes to ``<id>.attempt-<n>.prompt.txt`` instead, so the
          batch's file is never replaced by a re-ask; the task's next first
          attempt clears those, so none outlives the dispatch it belongs to.
        * Never for a task refused before dispatch: the policy check and the
          snapshot run first, so a task declaring a denied path leaves no
          file. The text is the native file's, unredacted — plan and task
          text, the prior-changes summaries, accepted check findings, all
          already on disk in the phase and plan dirs — and it lies inside the
          phase dir, which the containment sweep never attributes to a runner.

        A jailed repo-wide batch can write the phase dir and this process is
        not jailed, so nothing here follows a link (fix round 17: round 16
        checked ``prompts`` once by path, which a phase dir replaced by a link
        or a ``prompts`` swapped after the check still redirected outside the
        repository): the phase dir is the one pinned before any batch ran,
        reached from the repository root without following a link, and every
        file is created, renamed and unlinked relative to the folder's own
        descriptor (:mod:`utils.prompt_files`).

        Best-effort: a write that fails never fails the dispatch, and warns
        once for that task, naming it (fix round 17: one warning for the
        whole run let a directory planted under one task's file name silence
        every later task's failure). An earlier re-ask file that cannot be
        removed is named and left; the batch's own prompt is still kept.
        """
        where = os.path.join(self._ctx.phase_dir, _batch_prompt.DISPATCHED_PROMPTS_SUBDIR)
        try:
            if not task_id or os.path.basename(task_id) != task_id or task_id in (
                    ".", ".."):
                raise OSError(f"{task_id!r} is not a file name")
            with _prompt_files.PromptFolder.open(self.pinned_phase_dir()) as folder:
                if sent == batch_prompt:
                    name = _batch_prompt.dispatched_prompt_name(task_id)
                    if attempt <= 1:
                        head, tail = f"{task_id}.attempt-", ".prompt.txt"
                        for entry in folder.names():
                            if not (entry.startswith(head) and entry.endswith(tail)
                                    and entry[len(head):-len(tail)].isdigit()):
                                continue
                            try:
                                folder.remove(entry)
                            except OSError as exc:
                                self.warn_prompt_keep(
                                    task_id, entry,
                                    f"[write-subagents] could not remove "
                                    f"{task_id}'s earlier re-ask prompt {entry} "
                                    f"under {where}: {exc}. It is not this "
                                    f"dispatch's prompt; {task_id}'s own prompt "
                                    f"is kept beside it.",
                                )
                else:
                    name = _batch_prompt.dispatched_prompt_name(task_id, attempt)
                folder.write(name, sent)
        except (OSError, ValueError) as exc:
            self.warn_prompt_keep(
                task_id, None,
                f"[write-subagents] could not keep {task_id}'s dispatched "
                f"prompt under {where}: {exc}. The dispatch goes ahead; the "
                f"audit log keeps its sha256.",
            )

    def warn_prompt_keep(
        self, task_id: str, entry: Optional[str], line: str
    ) -> None:
        """Log ``line`` once per task (and per leftover ``entry`` it names):
        a retried dispatch that meets the same problem says nothing new,
        another task always does."""
        if (task_id, entry) in self._keep_warnings:
            return
        self._keep_warnings.add((task_id, entry))
        self._ctx.log(line)
