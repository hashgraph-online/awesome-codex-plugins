#!/usr/bin/env python3
"""The single owner of the multi-llm mode table.

Every surface that enumerates modes is *rendered* from ``MODES`` rather than
hand-maintained: ``multi_llm.py --help``, ``SKILL.md``'s ``argument-hint`` line,
``check_workflow_prerequisites.py``'s ``--mode``/``--phase`` vocabulary and (with
a later change) each host shim's flag list. Adding a mode is a row here, never an
edit in twelve places, and ``tests/test_instruction_portability.py`` fails if the
dispatcher and ``argument-hint`` disagree.

Three vocabularies meet in this table and are deliberately kept distinct:

* **mode word** — what ``multi_llm.py`` takes as ``argv[1]`` (``review-code``).
* **user flag** — what a user types at the skill (``--review-code``). The mapping
  is mechanical: strip the leading ``--``, verify membership. No shim invents it.
* **phase** — the ``state.json`` / phase-dir name (``code-review``). It differs
  from the mode word for exactly one mode, which is why ``code-review`` is also a
  dispatcher alias.

Nothing here imports an orchestrator: ``target_module`` is a dotted path the
dispatcher resolves lazily, so ``import modes`` never drags in the ~9k lines of
orchestrator code just to list mode names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Positional kinds a mode can declare, in the order they must appear.
POS_PLAN = "<plan>"
POS_QUESTION = "<question>"
POS_HOST = "<host>"
#: The commit modes' range (plans/review-commits.md §2.2). Spelled in square
#: brackets because, unlike the three kinds above, it is optional: no words
#: means ``HEAD``. It is also the only kind that spans several bare words, so
#: ``--review-commits last 2 commits`` needs no quotes: the dispatcher joins
#: every leading bare word into the one value (a ``-N`` word included) and
#: hands it on as ``--revs``, or as ``--plan-file`` when it is one commit
#: brief's path (``multi_llm._normalize_positionals``). ``--help`` and the
#: package surfaces render the spelling as it is written here.
POS_REVS = "[<range>]"


@dataclass(frozen=True)
class Mode:
    """One row of the dispatch table.

    Attributes:
        name: The mode word (``argv[1]``).
        positionals: Positional kinds, in order. Normalized by the dispatcher
            into the flags the target's own argparse parser already accepts.
            :data:`POS_REVS` is the one kind that is optional and joins every
            leading bare word into its one value.
        summary: One-line ``--help`` text.
        target_module: Dotted module path, imported lazily. ``None`` for modes
            whose implementation has not landed yet.
        target_attr: Callable attribute on that module, called as
            ``main(argv) -> int``.
        phase: ``state.json`` / phase-dir name, or ``None`` for modes that own no
            phase (``status``, ``init``, the install modes). A composite's
            (``full``) names its run dir only, for ``--detach``'s lock, log and
            ``run`` record; it records no phase of its own.
        instruction_file: Core instruction file under ``instructions/``, served
            token-free by ``multi_llm.py util instructions <mode>``.
        user_facing: True for the modes that appear in ``SKILL.md``'s
            ``argument-hint`` as ``--<name>``.
        is_workflow_phase: True for the eight phases
            ``check_workflow_prerequisites.py`` gates on.
        supports_detach: True for the modes ``--detach`` covers: the fan-out modes
            plus, since the write executor landed, every executor-backed mode
            (``implement``, the three apply phases, ``generate-tasks``, ``full``) —
            a write phase that schedules N batches through real agent CLIs outlives
            a host's shell cap exactly as a fan-out does. A mode with ``False``
            **rejects** ``--detach`` with exit 3 rather than accepting a flag that
            silently does nothing. ``generate-tasks`` and ``full`` carried the
            column before their orchestrators existed, so the gate a shim saw was
            already the final one; now that both are Python, the detach path they
            registered for is the one that actually runs.
        injected_flags: Flags the dispatcher prepends before the user's, because
            the mode is a thin view over a more general script.
        requires_uv: Whether the dispatcher runs D6c's layer-3 ``uv`` backstop
            before dispatching. True for every mode that *does* work, because a
            missing ``uv`` means nothing can run. False for exactly the two
            install modes: ``install-host --check`` **is** layer 1 of the same
            bootstrap and reports a missing ``uv`` as one of its five assertions,
            so failing at the backstop would replace a five-row prerequisite
            report with a one-line refusal — and ``uninstall-host`` has to work on
            a machine whose ``uv`` is already gone.
        unavailable: When set, the mode is dispatchable but exits 3 with this
            reason instead of running. Keeps the boundary a shim sees stable
            while the implementation is still a markdown sequence.
        runs_workflow: True for the mode that runs the whole workflow
            (``full``). Narrower than :attr:`is_composite`: a composite that
            runs two phases runs other modes but not the workflow. Read only
            where "the whole workflow" is the point, the next step a finished
            ``full`` falls back to (``suggested_next``), since it has no single
            next phase of its own. A reader that means "a mode that runs other
            modes" reads :attr:`is_composite`.
        sequence: The mode words a composite runs, in order, each through its
            own ``main(argv)``; empty on every other row. Mode words, and no
            reader uses them raw: :attr:`sequence_phases` gives the
            ``state.json`` phase words (``review-code`` → ``code-review``),
            :attr:`last_phase` the one it ends on, and ``utils/detach.py`` maps
            each phase through ``output_handler.PHASE_DIRECTORIES`` for the
            on-disk dir (``apply-code-fixes`` → ``apply-fixes``), which stays out
            of this module because ``output_handler`` imports it. Data rather
            than a name check, so a package's generated surface derives a
            composite's ``writes_worktree`` from the phases it runs, and a
            stopped composite retires the maps of exactly the phases it drove,
            without a list in a host layer or a mode word in ``detach``.
        optional_why: The generic reason an *optional* phase is offered before
            the next required one, shown beside its command in a finished
            phase's next-step block (``user_next_step.optional_before[].why``,
            plans/next-phase-command.md §2.1 "Each ``why`` has one owner").
            Set on exactly the rows whose phase is in
            ``check_workflow_prerequisites.OPTIONAL_PHASES`` and ``None`` on
            every other row; ``utils/next_phase.py`` holds no prose of its own.
            A sentence that reads after the host's own "Optional, before
            that:" label, saying what the step does and what skipping it
            means, never one that starts "optional" itself (fix round 22: a
            host printed "Optional, before that: optional: have the models
            review…").
        commit_view_of: The phase mode a commit front door fronts
            (plans/review-commits.md §2.1): ``review-code`` on
            ``review-commits``, ``apply-code-fixes`` on ``apply-commit-fixes``.
            Such a front door resolves its range to a commit brief, then
            re-records the invocation as that mode and calls its ``main``, so
            every run record, resume line and next step of the review names
            the fronted mode. This column is the one owner of the mapping
            back: wherever a command is rendered for a brief whose
            ``state.json`` holds ``commit_range``, the fronted word is spelled
            as the row that names it here (§2.8). ``None`` on every other row,
            ``improve-commits`` included: that composite is recorded as
            itself (its own run dir, ``--mode improve-commits``) and never as
            ``improve-code``, so nothing maps back for it, and its steps come
            from its own ``sequence``.
    """

    name: str
    positionals: Tuple[str, ...]
    summary: str
    target_module: Optional[str] = None
    target_attr: str = "main"
    phase: Optional[str] = None
    instruction_file: Optional[str] = None
    user_facing: bool = True
    is_workflow_phase: bool = False
    supports_detach: bool = False
    injected_flags: Tuple[str, ...] = ()
    requires_uv: bool = True
    unavailable: Optional[str] = None
    runs_workflow: bool = False
    sequence: Tuple[str, ...] = ()
    optional_why: Optional[str] = None
    commit_view_of: Optional[str] = None

    @property
    def is_composite(self) -> bool:
        """True for a mode that runs other modes (``sequence`` is set)."""
        return bool(self.sequence)

    @property
    def sequence_phases(self) -> Tuple[str, ...]:
        """``sequence`` as ``state.json`` phase words, in order.

        Resolved at call time, never stored: a row is a frozen dataclass built
        inside ``MODES``, so it cannot read the table it sits in. A word that
        resolves to no phase is a table bug, and raises rather than hand a
        reader ``None`` to use as a phase or a directory name.
        """
        phases = []
        for word in self.sequence:
            phase = phase_for(word)
            if phase is None:
                raise ValueError(
                    f"modes.py row {self.name!r}: sequence word {word!r} "
                    "resolves to no phase"
                )
            phases.append(phase)
        return tuple(phases)

    @property
    def last_phase(self) -> Optional[str]:
        """The phase a composite ends on; ``None`` for a mode that runs no other."""
        phases = self.sequence_phases
        return phases[-1] if phases else None


# Reason strings for the modes that are dispatchable but not yet implemented.
# Kept as constants so the dispatcher's exit-3 text and the tests agree.
#
# Why they are in the table at all: **every mode word is invocable through
# multi_llm.py on every host from day one**, even where the implementation behind
# it is still a markdown sequence. "Instruction-only" describes an
# implementation, never the dispatcher boundary a shim sees — otherwise every
# non-Claude shim has to special-case the remainder and re-derive a
# Claude-authored instruction sequence, which is the coupling the dispatcher
# exists to delete. The dispatcher makes the "not yet here" call, so no shim
# carries a host-specific fallback.
#
# `generate-tasks` and `full` used to sit here: both are now Python
# (`generate_tasks_orchestrator.py`, `full_workflow_orchestrator.py`), so the two
# instruction-only rows are gone and their markdown is narrative only. So did
# `install-host`/`uninstall-host`, until `utils/host_install.py` landed the D7
# install contract; **no mode is unavailable today**, and the constant survives as
# the documented shape of an honest gap rather than as a live reason string.
NOT_YET_AVAILABLE = "not yet available"


# Order is the workflow order, and it is also the order rendered into
# SKILL.md's `argument-hint` line — keep them in sync by rendering, never by
# copying (see render_argument_hint).
MODES: Tuple[Mode, ...] = (
    Mode(
        name="review-plan",
        positionals=(POS_PLAN,),
        summary="Review a plan with every configured model, then group + validate.",
        target_module="review_plan_orchestrator",
        phase="review-plan",
        instruction_file="review-plan.md",
        is_workflow_phase=True,
        supports_detach=True,
    ),
    Mode(
        name="apply-suggestions",
        positionals=(POS_PLAN,),
        summary="Prepare the validated plan-review suggestions for application.",
        target_module="apply_suggestions_orchestrator",
        phase="apply-suggestions",
        instruction_file="apply-suggestions.md",
        is_workflow_phase=True,
        supports_detach=True,
    ),
    Mode(
        name="improve-plan",
        positionals=(POS_PLAN,),
        summary="Review the plan with every model, then apply the validated "
                "suggestions to it (unattended).",
        target_module="improve_plan_orchestrator",
        phase="improve-plan",          # run dir only, as `full`
        instruction_file="improve-plan.md",
        supports_detach=True,
        sequence=("review-plan", "apply-suggestions"),
    ),
    Mode(
        name="generate-tasks",
        positionals=(POS_PLAN,),
        summary="Decompose the plan into an implementable task list.",
        target_module="generate_tasks_orchestrator",
        phase="generate-tasks",
        instruction_file="generate-tasks.md",
        is_workflow_phase=True,
        supports_detach=True,
    ),
    Mode(
        name="review-tasks",
        positionals=(POS_PLAN,),
        summary="Review the generated task list with every configured model.",
        target_module="review_tasks_orchestrator",
        phase="review-tasks",
        instruction_file="review-tasks.md",
        is_workflow_phase=True,
        supports_detach=True,
        optional_why=(
            "Have the models review the task list before implementing it; "
            "skipping this implements the tasks as they were generated."
        ),
    ),
    Mode(
        name="apply-task-suggestions",
        positionals=(POS_PLAN,),
        summary="Prepare the validated task-review suggestions for application.",
        target_module="apply_task_suggestions_orchestrator",
        phase="apply-task-suggestions",
        instruction_file="apply-task-suggestions.md",
        is_workflow_phase=True,
        supports_detach=True,
        optional_why=(
            "Apply the task-review suggestions to the task list before "
            "implementing it; skipping this implements the task list as it stands."
        ),
    ),
    Mode(
        name="implement",
        positionals=(POS_PLAN,),
        summary="Batch the tasks for implementation and track progress.",
        target_module="implement_orchestrator",
        phase="implement",
        instruction_file="implement.md",
        is_workflow_phase=True,
        supports_detach=True,
    ),
    Mode(
        name="review-code",
        positionals=(POS_PLAN,),
        summary="Review the working diff against the plan with every model.",
        target_module="code_review_orchestrator",
        phase="code-review",
        instruction_file="review-code.md",
        is_workflow_phase=True,
        supports_detach=True,
    ),
    Mode(
        name="apply-code-fixes",
        positionals=(POS_PLAN,),
        summary="Prepare the validated code-review fixes for application.",
        target_module="apply_code_fixes_orchestrator",
        phase="apply-code-fixes",
        instruction_file="apply-code-fixes.md",
        is_workflow_phase=True,
        supports_detach=True,
    ),
    Mode(
        name="improve-code",
        positionals=(POS_PLAN,),
        summary="Review the code changes with every model, then apply the "
                "validated fixes (unattended).",
        target_module="improve_code_orchestrator",
        phase="improve-code",
        instruction_file="improve-code.md",
        supports_detach=True,
        sequence=("review-code", "apply-code-fixes"),
    ),
    # The three commit modes (plans/review-commits.md §2.1): front doors that
    # resolve a commit range to a commit brief and run the code phases on it.
    # None is a workflow phase, so `full` never runs them and `full.sequence`
    # stays the workflow rows. Each core runs its front door (or, natively on
    # improve-commits, `util commit-brief`) and then loads the code phase cores
    # it fronts with `util instructions <phase>`, so validation, reaggregate and
    # the report stay single-sourced (plans/review-commits.md §2.9).
    Mode(
        name="review-commits",
        positionals=(POS_REVS,),
        summary="Review a commit range (HEAD by default) with every model, "
                "then group + validate.",
        target_module="review_commits_orchestrator",
        # The fronted phase: the run is review-code's on the commit brief.
        phase="code-review",
        instruction_file="review-commits.md",
        supports_detach=True,
        commit_view_of="review-code",
    ),
    Mode(
        name="apply-commit-fixes",
        positionals=(POS_REVS,),
        summary="Apply a commit review's validated fixes as uncommitted edits.",
        target_module="apply_commit_fixes_orchestrator",
        phase="apply-code-fixes",
        instruction_file="apply-commit-fixes.md",
        supports_detach=True,
        commit_view_of="apply-code-fixes",
    ),
    Mode(
        name="improve-commits",
        positionals=(POS_REVS,),
        summary="Review a commit range with every model, then apply the "
                "validated fixes (unattended).",
        target_module="improve_commits_orchestrator",
        phase="improve-commits",       # run dir only, as `improve-code`
        instruction_file="improve-commits.md",
        supports_detach=True,
        # The code words: every sequence word is a workflow-phase row.
        sequence=("review-code", "apply-code-fixes"),
    ),
    Mode(
        name="full",
        positionals=(POS_PLAN,),
        summary="Run the whole plan-to-code workflow as one resumable sequence.",
        target_module="full_workflow_orchestrator",
        # `full` owns no *workflow* phase (every phase it runs records its own
        # completion), but it does own a run dir: `--detach` needs somewhere for
        # `.status.json`, the log and the lock, and `status --phase full` has to
        # resolve through this same table rather than through a second vocabulary.
        phase="full",
        instruction_file="full-workflow.md",
        supports_detach=True,
        runs_workflow=True,
        # The eight workflow mode words, in `PREREQUISITE_PHASES` order, as a
        # literal: the row cannot derive them from the table it sits in.
        # `tests/test_mode_sequence.py` holds it to the `is_workflow_phase`
        # rows and to `FullWorkflow.steps()`.
        sequence=(
            "review-plan", "apply-suggestions", "generate-tasks", "review-tasks",
            "apply-task-suggestions", "implement", "review-code",
            "apply-code-fixes",
        ),
    ),
    Mode(
        name="ask",
        positionals=(POS_PLAN, POS_QUESTION),
        summary="Ask every configured model one free-text question about a plan.",
        target_module="ask_orchestrator",
        phase="ask",
        instruction_file="ask.md",
        supports_detach=True,
    ),
    Mode(
        name="status",
        positionals=(POS_PLAN,),
        summary="Report workflow phases (state.json) and detached runs "
                "({phase}/.status.json).",
        # Two views over two files behind one command word. The predecessor was
        # an instruction-only mode word whose markdown wrapper shelled out to
        # `check_workflow_prerequisites.py --status`; that function survives as
        # the workflow view's implementation (still directly callable, still
        # byte-identical under `--view workflow --json`), but the mode itself is
        # Python now, because a detached run with no command to poll it is
        # unusable.
        target_module="utils.run_status",
        instruction_file=None,
    ),
    Mode(
        name="doctor",
        positionals=(),
        summary="Check every configured provider CLI on this machine: present, "
                "version, auth, sandbox. No model calls; exit 0 or 3.",
        # D6 step 5. The one mode allowed to spawn provider CLIs outside a
        # phase — and only their model-free probes (`--version`, the declared
        # `auth_check`, the sandbox self-test). No lock, no phase dir, no
        # instruction file: like `status`, its flags are the whole interface.
        # Not user-facing: it is what the Claude Code plugin's SessionStart
        # hook runs (`hooks/hooks.json`, `--warn-only`) and what a user runs
        # by hand after a refusal names it — not a workflow flag.
        target_module="utils.doctor",
        instruction_file=None,
        user_facing=False,
    ),
    Mode(
        name="init",
        positionals=(),
        summary="Scaffold a per-project .multi-llm/providers.yaml override.",
        target_module="init_config",
        instruction_file="init-config.md",
    ),
    # Not user-facing: neither is part of the skill's own argument surface, so
    # neither gets a `--flag` in `argument-hint`.
    Mode(
        name="install-host",
        positionals=(POS_HOST,),
        summary="Install this skill's entry shim into another coding harness.",
        target_module="utils.host_install",
        target_attr="main",
        user_facing=False,
        requires_uv=False,
    ),
    Mode(
        name="uninstall-host",
        positionals=(POS_HOST,),
        summary="Remove a previously installed host shim.",
        target_module="utils.host_install",
        target_attr="uninstall_main",
        user_facing=False,
        requires_uv=False,
    ),
)


# A closed alias table, shown in `--help`. No prefix or fuzzy matching: an
# unrecognized word is an error, not a guess.
ALIASES: Dict[str, str] = {
    "review": "review-plan",
    "code-review": "review-code",
    "tasks": "generate-tasks",
    # Stopping a detached run has to be discoverable, so the verb is an alias
    # like any other — the only one that expands to a mode word *plus a flag*
    # (see ALIAS_FLAGS). Aliases are a human convenience: generated shims always
    # emit the `status … --abort` spelling so their text stays on one surface.
    "abort": "status",
    "cancel": "status",
    "stop": "status",
}


# The flags an alias contributes on top of its target mode, prepended before the
# user's own. Carried here so `--help` renders the expansion and nothing else
# re-derives it.
ALIAS_FLAGS: Dict[str, Tuple[str, ...]] = {
    "abort": ("--abort",),
    "cancel": ("--abort",),
    "stop": ("--abort",),
}


def alias_flags(word: str) -> Tuple[str, ...]:
    """Flags the dispatcher must inject for *word*, if it is a flag-bearing alias."""
    return ALIAS_FLAGS.get(word, ())


def alias_expansion(word: str) -> str:
    """How `--help` spells an alias: ``abort -> status --abort``."""
    target = ALIASES[word]
    extra = " ".join(ALIAS_FLAGS.get(word, ()))
    return f"{target} {extra}".rstrip()


#: The mode a bare argument text resolves to when it carries no mode flag.
#: **The single owner of "no mode flag means review-plan".** That sentence used
#: to be prose in two hand-written places (``SKILL.md`` and
#: ``hosts/opencode/shim.md.tmpl``) with no constant behind either, held together
#: only by ``tests/test_shim_correctness.py``. The npm plugin route would have
#: made a third copy inside a tool description, so the rule became a constant and
#: every surface now renders from it: ``dist/cli-surface.json`` (what the
#: model-facing tool definition is assembled from), and both places every shim
#: template states it — its step-2 prose and its worked example — through
#: ``cli_common.DEFAULT_MODE_PLACEHOLDER``.
#:
#: One surface cannot render, and is pinned instead: Claude Code's ``SKILL.md`` is
#: ``installable: false`` and is read by the host verbatim (it expands
#: ``${CLAUDE_SKILL_DIR}`` itself at load time), so nothing substitutes a token
#: there. Its two sentences are literals held to this constant by
#: ``test_default_mode_has_one_owner``, which asserts all three surfaces together
#: — the guard is what makes the claim above a property rather than an intention.
DEFAULT_MODE = "review-plan"


#: The model-callable tool's registration name on every package route — the
#: OpenCode plugin's ``tool`` hook key and the codex MCP server's ``tools/list``
#: entry. One owner, because it is also what every re-attach and abort
#: ``{tool, args}`` object the plugin hands back names, and two hosts spelling
#: it twice is two chances for a continuation to point at a tool that does not
#: exist. Emitted as the surface's ``tool_name``.
TOOL_NAME = "multi_llm"

#: The two literal values the tool description's worked examples fill in. The
#: examples themselves are *selected by shape* from the table (rule f) — the
#: default mode, a mode with no positional, a mode taking a question, an alias
#: carrying a flag — so these are the only written words in them.
EXAMPLE_PLAN_PATH = "plans/x.md"
EXAMPLE_QUESTION = "Why is the ceiling 120 s?"

#: The one authored sentence in the OpenCode plugin's model-facing tool
#: definition. It lives here rather than in JavaScript for the same reason the uv
#: preflight message lives in ``hosts/uv-missing.txt``: the plugin holds no prose
#: of its own, so everything it shows a model is generated from this tree
#: (D7.2). Everything *else* in that definition — the mode lines, the argument
#: descriptions, the reserved-flag rules — is derived from the table above, so
#: this is the only string a human writes.
#:
#: It carries the one thing no generated line can: that the tool is the *only*
#: way to run multi-llm on that host, and that its dispatcher must not be reached
#: through ``bash``.
TOOL_DESCRIPTION_LEDE = (
    "Run a multi-LLM workflow over a plan file. This tool is the only supported "
    "way to run multi-llm on this host: never invoke multi_llm.py, uv run or any "
    "dispatcher command through bash, because the flags this host requires are "
    "appended here and a shell invocation reaches none of them."
)

#: The lede's sibling: one line that names the four exit codes and the decision
#: exit 3 carries. A sibling rather than a clause folded into the lede, so the
#: two strings with two jobs stay separately assertable (the lede is pinned by
#: identity and by ``startswith``; this one by ``contains``). It is rendered
#: into the tool description after the mode block, so a model meets it in the
#: same glance as the modes. The four numbers are ``cli_common.EXIT_*``, held
#: to this line by a test rather than by an import: this module imports nothing
#: by design. Fix round 18 (live run 7, Codex racing 08): "report" is the
#: result's ``error`` line whole — the stop's what, reported and not-run text
#: and whether anything ran the tests — beside the commands the result names.
TOOL_OUTCOMES_LINE = (
    "Exit codes: 0 done · 1 error · 2 nothing to do · 3 needs a human: stop, "
    "report its `error` line whole, do not do the phase's work."
)

#: How a host prints a ready section (``user_next_step.markdown``, a stop's
#: ``resume_markdown``, Claude Code's ``[NEXT_STEP_MARKDOWN]`` section), said
#: once here and word for word on every route (fix round 26, live run 11:
#: hosts wrote its sentences above it a second time, wrapped it in a fence of
#: their own and reworded its manual note). The relay surfaces carry it as a
#: literal, held to this constant by ``tests/test_relay_says_it_once.py``.
READY_SECTION_RULE = (
    "Copy it word for word, never wrapped in a fenced block of your own (its "
    "commands are fenced already), and say none of it twice: its whys, notes, "
    "manual tasks and \"Workflow complete.\" appear only in it, never above it."
)

#: The outcomes line's second sibling (plans/next-phase-command.md §2.4): what
#: ``user_next_step`` in a result is, said in the tool description a model reads
#: before any result. Lifting that key to a tool result's top level puts it next
#: to ``next``, which the same model is taught to treat as a call — so the
#: description says, once, that this one is the user's to type and never a call.
#: Rendered after :data:`TOOL_OUTCOMES_LINE` on both package hosts; neither
#: server authors the string. "Only then" / "never otherwise" since fix round
#: 11: on OpenCode racing run 4, phase 06, the host ended an implement result
#: whose `command` named review-code, and whose notice listed the manual tasks
#: left, with "Workflow complete. Manual tasks left …". Fix round 16 (Codex
#: racing 06r/07): a command answer carries `manual_tasks` and its note too,
#: and the line says to relay them on any result — the hosts named T009 from
#: the notice but never the command that records it done. Fix round 17: it
#: said "which no phase will run" of every entry, while a task skipped with a
#: manual one (`waits_on`) runs on the resume the note names. Fix round 18
#: (live run 7): the `command` first and each optional entry after it with its
#: `why` (plans/next-phase-command.md §2.1, "Primary first"; Codex had put the
#: optional step first, OpenCode had dropped its `why`), and the note as prose
#: (Codex racing 06 put it in a ```text fence). Fix round 22 (live run 9:
#: Codex 04 printed both commands as bare paragraphs, and the manual-task
#: close command, which the note carried at its end, reached the user as
#: prose): the key carries the section already written, each command fenced
#: (`next_phase.render_next_step_markdown`), and the line says to copy it.
#: Fix round 24 (live run 10: OpenCode 03 reordered the step under captions
#: of its own, 08 wrote "Workflow complete." beside the markdown that says
#: it): its words and order, no caption, and the words never the host's own;
#: a stop's `resume_markdown` is copied the same way.
#: Fix round 26 (live run 11): Codex 04/06/08 and OpenCode 03-08 wrote the
#: notice or the manual note above the copied section, OpenCode 08 opened a
#: fence of its own around it, the OpenCode decline run printed "Workflow
#: complete." twice (plain, then fenced), Codex 06 reworded the manual
#: note and OpenCode's stops added a recap and their own list of options
#: before `resume_markdown`: :data:`READY_SECTION_RULE`, and the stop's
#: section stands in place of any list of the host's own.
TOOL_USER_NEXT_STEP_LINE = (
    "`user_next_step` in a result is a command for the user to type, never a "
    "call to make: end your report with its `markdown`, copied as it is (its "
    "words and order, each command alone in its fenced block, each why and "
    "note plain text, the manual tasks it lists included, no caption of your "
    "own), then stop. " + READY_SECTION_RULE + " It says \"Workflow complete.\" only "
    "when it is `complete`: never write those words yourself, even when a "
    "notice lists manual tasks left for the user. Only `next` is a call. At a "
    "stop, `resume_markdown` is the same kind of thing: copy it the same way, "
    "in place of any list, recap or summary of the options or ways forward of "
    "your own, its commands (`resume_command` among them) the user's to type, "
    "never a call."
)

#: Where a finished run's notice goes (fix round 26, live run 11: the hosts
#: wrote it above the ready section, which said the same sentences again).
#: The notice no longer carries what that section says (``run_status``); the
#: relay surfaces say so too, word for word.
NOTICE_PLACEMENT = (
    "Put it above the closing section, and repeat nothing that section says."
)

#: The finished run's relay (live run 8, OpenCode racing 08): a completed
#: apply-code-fixes result carried, in `result.notice`, that nothing ran the
#: repository's tests and that two invalid fixes were not applied, and the host
#: relayed neither: no route's text named the key. The stop's own line is the
#: result's `error` (:data:`TOOL_OUTCOMES_LINE`); this is the other half.
#: Rendered after :data:`TOOL_NO_COMPOSED_COMMAND_LINE` on both package hosts.
TOOL_NOTICE_LINE = (
    "A finished run's `result` can carry a `notice`: what the run left out or "
    "could not check, such as items it did not apply or that nothing ran this "
    "repository's tests. Report what it says, every part of it, as plain text "
    "outside any fenced block. " + NOTICE_PLACEMENT
)

#: What a host does with a commit mode's blocks on a tool route
#: (plans/review-commits.md §2.3, "Relay"). The CLI prints the commit block
#: (and ``[COMMIT_FIXES]`` on an apply) before any model runs, and the cores
#: relay them verbatim and once; both servers lift those lines out of the
#: output into one ``commit_blocks`` string, so the tool description has to say
#: the same thing the cores say.
TOOL_COMMIT_BLOCKS_LINE = (
    "A commit mode's result (review-commits, apply-commit-fixes, "
    "improve-commits) can carry `commit_blocks`: the commits the run acts on, "
    "and on an apply the fixes it will apply and skip. Relay it verbatim and "
    "once, as soon as you read it, before anything else from the result."
)

#: What every host does with the write policy at a stop (fix round 20, live
#: run 8 #4; a user decision, 2026-10-07: permissive). Round 18 told hosts
#: never to suggest loosening ``driver.write_paths`` after a Claude Code host
#: offered "remove the deny rule" on its own, while the plugin's own stop line
#: offered allowing the file, which hosts are told to relay whole. The plugin
#: keeps offering it, worded as the user's own call
#: (``write_safety.policy_allow_clause``), since it is theirs to decide and it
#: lets the run complete; a host relays it as given, adds no policy advice of
#: its own and never edits the setting itself. Fix round 21: the change is
#: worded per rule (a deny hit names the deny rule to narrow, since the deny
#: list wins over ``allow``), so the rule names both kinds. Rendered into
#: :data:`NEEDS_HUMAN_RULE` (every file route, both plugin instructions and
#: Claude Code's ``SKILL.md``), :data:`TOOL_NO_COMPOSED_COMMAND_LINE` (both
#: tool descriptions) and :data:`NEEDS_HUMAN_MESSAGE` (the tool routes'
#: exit-3 message), and held word for word in implement's stop rule.
STOP_POLICY_RULE = (
    "Never edit `driver.write_paths`, or any other multi-llm setting in "
    "`.multi-llm/providers.yaml`, yourself. At a stop, offer only the ways "
    "forward the stop itself names, as it words them: when it names a change "
    "to `driver.write_paths` that lets a refused file be written (adding it to "
    "`allow`, or removing or narrowing a deny rule that covers it), that is "
    "one of them and the user's call; add no advice about the write policy of "
    "your own."
)

#: The user-next-step line's sibling (racing re-run 2026-10-04): after a failed
#: generate-tasks whose result carried no command at all, an OpenCode host model
#: printed a "next phase" it composed itself, in the tool-call spelling
#: (``multi_llm --mode review-tasks --plan …``) and for a phase a failed run
#: does not lead to. The line above says what the two command keys are; this
#: one says they are the only commands, and what a result carrying neither
#: means — every failed or needs-human result now says so explicitly, with
#: ``user_next_step: null`` and :data:`NO_COMMAND_REASON`. Rendered directly
#: after :data:`TOOL_USER_NEXT_STEP_LINE` on both package hosts. Fix round 18
#: (live run 7, the Claude Code stop path): a host offered "remove the deny
#: rule" as a way past a task the write policy refused. Fix round 20: it ends
#: with :data:`STOP_POLICY_RULE` instead of "never suggest loosening".
TOOL_NO_COMPOSED_COMMAND_LINE = (
    "Never compose a command for the user yourself, and never spell one from "
    "this tool's arguments: the only commands you may give them are the ones "
    "in `user_next_step`, `resume_command` and each `resume_answers` "
    "command, each copied verbatim. "
    "A result whose `user_next_step` is "
    "null and that carries no `resume_command` has no command to give "
    "(`no_command_reason` says why): name no command and no next phase. "
    + STOP_POLICY_RULE
)

#: The value of ``no_command_reason``, the key both package servers set beside
#: ``user_next_step: null`` on a failed or needs-human result that carries no
#: ``resume_command`` (the explicit "there is nothing to type" the line above
#: refers to). Read off the surface; a server whose surface lacks it still
#: sets ``user_next_step: null`` and simply omits the sentence.
NO_COMMAND_REASON = (
    "There is no command for the user to type: this phase did not finish, so no "
    "next phase follows it, and nothing names a re-run that would get past this "
    "stop as it stands. Report what happened and what its error names; do not "
    "compose a command."
)

#: The title the OpenCode package puts on its tool part when a call ends at a
#: stop (``tool.execute.after``; fix round 16). ``opencode run`` prints a
#: plugin tool's title on the tool's own line (the TUI's header reads it too,
#: not measured) as soon as the call returns and whether or not the session's model ever
#: writes its reply: OpenCode racing run 6's free model never did (28 min
#: idle), and the stop and its resume command were only in the tool output.
#: ``{line}`` is the run's own last error line (``result.error``, the line
#: the exit-3 ``message`` quotes) or ``no_line``; ``resume`` is appended,
#: ``{command}`` filled with ``resume_command``, when the result carries one.
#: Fix round 17: ``{line}`` is shown without control characters and cut at
#: ``max_line`` characters, ending in ``cut``; the command is never cut.
#: Fix round 22: by ``utils.text_clip.clip``'s rule (a word boundary, no
#: separator before ``cut``, a bracket the kept part opened closed after it).
STOP_TITLE = {
    "template": "stopped and needs you: {line}",
    "no_line": "the run did not finish; the tool output says why.",
    "resume": " Resume with: {command}",
    "max_line": 300,
    "cut": "…",
}

#: The route signal's one owner (plans/next-phase-command.md §2.1, "Knowing the
#: route"). The package routes' tool servers set ``ROUTE_ENV`` in every child
#: env they spawn (polls included) to their surface's
#: ``dispatcher.route_env.value``, which the surface generator picks from
#: ``TOOL_ROUTES`` — so neither server spells the name or the value. It picks
#: only the spelling a printed next-phase command uses, never which phases run
#: (D6b). ``utils.next_phase.resolve_route`` is the one reader, and it honours
#: a value only when it is a member of ``TOOL_ROUTES`` **and** the resolved host
#: carries a ``next_command`` cell for it. It is owned by the tool servers, not
#: a user setting. ``package`` is the route key ``hosts/capabilities.yaml``
#: already gives each host's distribution route, whatever the host calls it.
ROUTE_ENV = "MULTI_LLM_ROUTE"
TOOL_ROUTES: Tuple[str, ...] = ("package",)

#: The one sentence every needs-human surface shares, and the one the incident
#: turned on: an agent whose tool has just told it the run is blocked has no
#: sentence anywhere telling it not to do the work by hand. Composed into
#: :data:`NEEDS_HUMAN_RULE` (the file routes and the plugin's command body) and
#: into :data:`NEEDS_HUMAN_MESSAGE` (the plugin's exit-3 result), so the two
#: cannot say it differently.
NEEDS_HUMAN_WORK_SENTENCE = (
    "Do not perform the work this run was going to review, plan, or implement: "
    "doing it yourself is never a substitute for a failed run."
)

#: The decision rule for exit 3, authored once. Every instruction surface a
#: supported route loads renders it: both ``hosts/*/shim.md.tmpl``, the
#: opencode plugin's ``hosts/opencode/plugin-command.md.tmpl`` and the codex
#: plugin's ``hosts/codex/plugin-skill.md.tmpl`` through
#: ``cli_common.NEEDS_HUMAN_RULE_PLACEHOLDER``, and Claude Code's ``SKILL.md`` — read
#: verbatim by its host, so nothing substitutes a token there — as a literal
#: held to this constant by ``test_needs_human_rule_has_one_owner``, the same
#: shape :data:`DEFAULT_MODE` uses. It also owns the ``next`` clause, because
#: ``next`` and the plugin's ``options`` are one object under two names: on
#: ``0`` and ``2`` it runs verbatim, on ``3`` it is reported and waits for the
#: user. "Run verbatim" is the command-string wording the file routes and
#: Claude Code need; on the codex plugin route ``next`` is re-spelled as the
#: tool's arguments object (D3c) and is never a shell command, so that
#: template follows this token with its own line saying "run" means calling
#: the tool again with ``next`` as its arguments. The gloss lives in the
#: template, not here, so this constant — and the ``SKILL.md`` literal held
#: to it — keep one wording. Four hand-typed paraphrases of this rule are
#: exactly how two hosts come to contradict each other on the behaviour an
#: incident hinges on. Fix round 19: it asked for "what was being run", which
#: on a file route is the dispatcher command with the flags the shim composed
#: (the needs-human message's `argv`, run-7 #13); it asks for the phase and
#: the plan. Fix round 22: "which phase was running" came back as "Phase
#: running: implement" for a phase that had stopped (OpenCode, live run 9).
#: "Or commit range" (commit modes' live run, 2026-10-26): a commit mode's
#: refusal before any phase (`[RANGE_DIVERGED]`) has a range and no plan, and
#: OpenCode reported "on which plan" all the same.
NEEDS_HUMAN_RULE = (
    "Run `next` verbatim when it is not `null` on `0` and `2`. On `3` stop: "
    "report to the user which phase stopped, on which plan or commit range, "
    "the last error line it printed, "
    "whole (on a stop it says what stopped, what it reported, what did not "
    "run and whether anything ran the repository's tests), "
    "and the options its output names (`next` included); do not run a "
    "different mode. " + NEEDS_HUMAN_WORK_SENTENCE + " Run an option only "
    "after the user has picked it. " + STOP_POLICY_RULE
)

#: The plugin's exit-3 ``message``, as a **template**: the JS selects a clause
#: for each token and substitutes, and authors no wording of its own — not even
#: a fallback. ``{phase}`` and ``{error}`` are literal tokens here (nothing in
#: Python ``%``- or ``.format``-expands them); the clause alternatives below are
#: what the plugin fills them with, chosen by what the child actually left:
#:
#: * ``phase_incomplete`` — the phase is named from the *launch* (the call's
#:   validated mode word, through the table above) and the result line's
#:   ``state`` is the needs-human state, so "did not complete" is true of it;
#: * ``phase_known`` — the phase is named but the result line does not say it
#:   failed to complete;
#: * ``review_completed`` — ``review-code --fail-on-high``: the review finished,
#:   found what it was told to stop on, and wants a decision. Never "did not
#:   complete";
#: * ``phase_unnamed`` — a result line is present but nothing names a phase;
#: * ``phase_unknown`` — no result line at all (a child that died before it
#:   emitted one, or a line that was not JSON), so nothing names the phase;
#: * ``error_known`` — the last error line, quoted: the result's own ``error``
#:   when it carries one, else the last non-blank line of the *redacted*
#:   output, else of the redacted stderr;
#: * ``error_unknown`` — the child left no line to quote; ``log`` is what to
#:   report.
#:
#: The ``options`` sentence is kept word for word from the message it replaces:
#: it is what tells the model where the redacted commands went.
#:
#: Fix round 18 (Codex racing run 7, phase 08): the message named `argv` as
#: what was being run, and the host told the user the tool's own
#: `--exec-subagents --detach`; it now says to report the phase and the plan,
#: and never to quote `argv` or its flags. Fix round 19: the round's merge had
#: kept "what was being run (`argv`)" as the opening instruction beside the
#: later prohibition, telling the host both; the opening asks for the phase
#: and the plan, and a test fails any host-facing text that asks for `argv`.
NEEDS_HUMAN_MESSAGE = {
    "template": (
        "Stop here: this run is blocked and needs a human. {phase} {error} "
        "Report to the user which phase stopped, on which plan or commit range, "
        "that line whole, word for word (on a stop it says what stopped, what the "
        "task reported, what did not run and whether anything ran the "
        "repository's tests), and the "
        "`options`; an `options` entry is a tool call for you, never a command "
        "for the user to type, so do not print one as a command. The "
        "dispatcher's output is included as it was rendered, except that every "
        "runnable dispatcher command in it was re-spelled the way this host's "
        "user would type it (or replaced by a pointer where it could not be) "
        "and also comes back as a tool call in `options`, in the order it "
        "appeared, and its result line is in `result` instead; do not "
        "paraphrase the output, and do not lift a command out of it for the "
        "user: only `resume_command` (and each `resume_answers` command) is "
        "theirs to type. Do "
        "not run a different mode. Never quote `argv` or its flags to the user, "
        "which are this tool's own (`--host`, `--yes`, `--exec-subagents`, "
        "`--detach`) and nothing the user ran or types. "
        + NEEDS_HUMAN_WORK_SENTENCE + " " + STOP_POLICY_RULE + " Send back "
        "an `options` entry only after the user has picked one."
    ),
    "phase_incomplete": "The `{phase}` phase did not complete.",
    "phase_known": "The `{phase}` phase was running.",
    "review_completed": (
        "The `{phase}` review finished, found what it was told to stop on, and "
        "needs your decision."
    ),
    # Appended (never substituted) when the result carries `resume_command`: the
    # one command here that IS for the user to type. 2026-10-02: the run's
    # options were all the user was shown, as tool-call JSON on Codex and as
    # `call multi_llm with …` plus the agent-facing `human` sentence on OpenCode,
    # with "Pick an option and I'll run it" in a headless run.
    "resume": (
        "`resume_command` is what the user types to resume this phase once the "
        "cause above is fixed. Give it to the user verbatim in its own fenced "
        "block, as the way forward. It is never a tool call and never a shell "
        "command: do not run it, and do not offer to run it for them."
    ),
    # Appended instead of `resume` when the lookup says what the plain resume
    # does (`user_resume.why`, the result's `resume_why`; fix round 22, live
    # run 9: with no why the hosts wrote one — "re-runs the T002 check",
    # false on unchanged files, or "after addressing the write policy").
    # `{why}` is substituted as it comes.
    "resume_why": (
        "`resume_command` is what the user types to resume this phase; it "
        "{why}. Give it to the user verbatim in its own fenced block, with "
        "what it does as plain text above it. It is never a tool call and "
        "never a shell command: do not run it, and do not offer to run it for "
        "them."
    ),
    # Appended after `resume` when the stop offers answers as well (fix round
    # 14, live run 5: the `--human-task` answers lived only in `error`, and
    # hosts relayed them in two of four first stops). `{answers}` is the
    # dispatcher's `user_resume.answers_text` — each command in backticks and
    # what it does, one sentence apiece and ending its own (the merge of fix
    # round 28: a bracketed why read "(T006))") — substituted as it comes; the
    # server authors none of it. Each is also in `resume_answers` and an `options` entry.
    # Fix round 22 (live run 9, OpenCode accept 01): the host headed each
    # answer "Optional, before that:" and added a paraphrased "Ways forward"
    # list beside them; the clause says what they are and where the why goes.
    "answers": (
        "Instead of `resume_command` the user can type any of these, each "
        "with what it does (each is in `resume_answers` and is also an "
        "`options` entry, in the same order): {answers} After "
        "`resume_command`, give the user every one of them verbatim in its own "
        "fenced block, its why as plain text above it, and no list or summary "
        "of them of your own: they are the stop's ways forward. Like "
        "`resume_command`, none is a tool call or a shell command for you to run."
    ),
    # Appended instead of `resume`/`resume_why` and `answers` when the lookup
    # wrote the stop's ways forward as one section (`user_resume.markdown`,
    # the result's `resume_markdown`; fix round 24, live run 10: the hosts
    # composed their own blocks, reworded the whys, added "what ran" lists
    # and printed `options` entries as "Call multi_llm with …").
    # Fix round 26 (live run 11, OpenCode stop 01): the host added a recap
    # and an "Options named in output (resume choices)" list before the
    # section, following the template's "report … the `options`": the
    # section IS that report.
    "resume_markdown": (
        "`resume_markdown` is the stop's ways forward, already written for "
        "the user: `resume_command` with what it does and, when the stop "
        "offers them, the answers they can type instead (each also in "
        "`resume_answers` and an `options` entry). It is the report of the "
        "`options` asked above: end your report with it, copied as it is, in "
        "place of any list of options or ways forward of your own, and write "
        "no list, recap or summary of the options or answers anywhere else. "
        + READY_SECTION_RULE + " Each command stays alone in its fenced "
        "block, each why stays plain text. None of its commands is a tool "
        "call or a shell command for you to run, and do not offer to run one."
    ),
    # Appended instead of `resume` when the result carries no
    # `resume_command` (racing re-run 2026-10-04: a result with neither command
    # key, and the host model composed a "next phase" of its own).
    "no_command": (
        "`user_next_step` is null and there is no `resume_command`: give the "
        "user no command to type and name no next phase; `no_command_reason` "
        "says why."
    ),
    "phase_unnamed": "Nothing in the result line names the phase that was running.",
    "phase_unknown": (
        "The dispatcher exited without a result line, so nothing here names the "
        "phase that was running; `log` says what ran."
    ),
    "error_known": "The last line it left is: {error}",
    "error_unknown": (
        "Its result line names no error, and what it printed is in `output` and "
        "`stderr`; `log` is what to report."
    ),
}

#: The one ``options`` entry that is not a retry: a legal exit. Appended by the
#: plugin after the scraped tool calls, as ``{human: <this sentence>}``, so an
#: agent reading the options finds "ask the user" beside "run this again".
NEEDS_HUMAN_OPTION = (
    "(a note to you, not a command and not for the user) stop here and report; "
    "send back one of the options above only after the user has picked one"
)

#: The one exit 3 that is not an unfinished run. ``review-code --fail-on-high``
#: completes the review and *then* exits 3 to hold a standalone gate for a
#: decision, and its result line carries the same needs-human state every other
#: exit 3 does. The plugin combines the launch flag with the result's positive
#: ``high_priority_groups.count`` before claiming completion: the flag alone
#: also appears on preflight failures where no review ever ran.
#: The flag is declared by ``code_review_orchestrator``'s parser; a test holds
#: the two spellings together.
REVIEW_GATE = {"mode": "review-code", "flag": "--fail-on-high"}


# ---------------------------------------------------------------------------
# The package routes' pre-spawn refusals — authored here, read off the surface
# ---------------------------------------------------------------------------
#
# Every message a package route's server returns *instead of* spawning the
# dispatcher is a template here, emitted into ``dist/cli-surface.json`` and
# returned by the server verbatim after token substitution — the same rule
# that keeps the exit-3 message in :data:`NEEDS_HUMAN_MESSAGE` and the uv
# preflight text in ``hosts/uv-missing.txt``. Tokens are literal ``{name}``
# spans replaced by plain string substitution (never ``str.format``), so a
# brace a user typed into a value can never be read as another token.

#: The environment name that lifts the codex tool's write-posture refusal, and
#: the one value that means "on" (the ``MULTI_LLM_ALLOW_DIRTY`` spelling:
#: ``=1`` and nothing else, so ``=0`` does not enable it). An environment name
#: and **not** a tool argument, because every tool argument is model-supplied
#: and a model must never be able to authorize its own escalation (D3b).
WRITE_POSTURE_LEVER_ENV = "MULTI_LLM_CODEX_UNSANDBOXED_WRITES"
WRITE_POSTURE_LEVER_VALUE = "1"

#: The refusal a write-capable mode gets under a read-only (or unreadable)
#: session posture. The codex server reads the posture per call from the
#: ``sandbox_mode`` in its turn metadata: ``read-only`` refuses,
#: ``workspace-write`` and ``danger-full-access`` allow. ``{mode}`` is the mode
#: word as sent; ``{posture}`` is the posture word the server read, or
#: :data:`WRITE_POSTURE_UNREADABLE` when it could not read one — absent, or a
#: word it does not know — and then the refusal fails closed.
WRITE_POSTURE_REFUSAL = (
    "Refused before anything ran: `{mode}` edits the working tree, and this "
    "session's sandbox posture is {posture}. This tool runs outside the "
    "session's exec sandbox, so it will not make edits the session was not "
    "granted. The single way to proceed is the user's, never yours: they set "
    + WRITE_POSTURE_LEVER_ENV + "=" + WRITE_POSTURE_LEVER_VALUE
    + " in the environment codex is launched from and restart it. Report this "
    "to the user. " + NEEDS_HUMAN_WORK_SENTENCE
)

#: What ``{posture}`` reads when the server could not observe the session's
#: sandbox posture at all.
WRITE_POSTURE_UNREADABLE = (
    "unreadable from this tool, so it is treated as read-only"
)

#: The refusal when no workspace-anchor candidate answered (D3f). ``{probed}``
#: is the list of candidates the server tried, in its own order. The process's
#: own working directory is never a fallback: on a plugin route it is the
#: install location, and a run anchored there scaffolds configuration into a
#: directory the next install deletes.
ANCHOR_UNRESOLVED = (
    "Refused before anything ran: this tool could not determine which "
    "workspace to run in. It probed {probed}, and none answered. It does not "
    "fall back to its own working directory, which is the plugin's install "
    "location, not your project. Report this to the user; do not retry with a "
    "different mode. " + NEEDS_HUMAN_WORK_SENTENCE
)

#: The refusal when the login shell the dispatcher is started through does not
#: resolve (D3a) — the Windows-without-Git-Bash case, and any ``PATH`` with no
#: POSIX shell on it. ``{shell}`` is the program searched for, ``{platform}``
#: the platform word, ``{path}`` the ``PATH`` that was searched. A shell-less
#: spawn is not offered: it would start the provider CLIs without the
#: credentials a login profile exports, and fail one layer down as an opaque
#: provider error.
SHELL_MISSING = (
    "Refused before anything ran: this tool starts the dispatcher through a "
    "login `{shell}`, and no `{shell}` was found on {platform} along this "
    "PATH: {path}. A POSIX bash on PATH is a prerequisite of this tool "
    "(on Windows, Git Bash). Install one, put it on PATH, and restart the "
    "host. Report this to the user; running without a login shell is not "
    "offered, because the provider CLIs would start without the credentials "
    "your profile sets."
)

#: The codex-only clause of the tool description (D3b: the tool says what it
#: is). ``{modes}`` is the comma-joined list of modes whose surface row carries
#: ``writes_worktree``. Emitted for the codex host alone; the OpenCode plugin
#: runs inside its host's own permission model and says nothing of the kind.
TOOL_WRITE_CAPABLE_NOTE = (
    "This tool runs outside the session's exec sandbox. {modes} edit the "
    "working tree through agent CLIs; under a read-only posture, or one this "
    "tool cannot read, they are refused unless the user has set "
    + WRITE_POSTURE_LEVER_ENV + "=" + WRITE_POSTURE_LEVER_VALUE + "."
)

#: The codex host's rule for waiting on a call (fix round 16, Codex racing run
#: 6). Under codex's code mode the model calls this tool from a JavaScript
#: ``exec`` cell that hands control back after ``yield_time_ms`` (30 s by
#: default) while the call is still running, and a model that then ends its
#: turn ends ``codex exec``, whose teardown aborts the run. Measured offline on
#: codex 0.160.1: a cell whose first line is the pragma below waited for a
#: 75 s call and returned only with its result. ``{BUDGET_MIN}`` and
#: ``{YIELD_MS}`` are filled from the plugin's ``tool_timeout_sec``
#: (``packaging/codex/mcp.json``) by ``packaging/common/surface.py``, so the
#: wait and the budget cannot drift. Rendered into the codex tool description
#: and the codex plugin's skill; no other host has the cell.
TOOL_LONG_CALL_RULE = (
    "A call can run for up to its {BUDGET_MIN}-minute budget. When you call this "
    "tool from an `exec` cell, start the cell with "
    '`// @exec: {"yield_time_ms": {YIELD_MS}}`, so the cell waits for the '
    'result. If a cell hands back "Script running" anyway, call `wait` until '
    "this call returns, and never end your turn while it is running."
)


# The `util` namespace is a mode word for routing purposes but is deliberately
# *not* a mode: it is excluded from `--help`'s mode list and from
# `argument-hint`, and is never rendered into a MULTI_LLM_RESULT.next value.
UTIL_NAMESPACE = "util"


# Legacy direct-invocation script name -> mode word. Used when a printed
# follow-up command has to be built from an orchestrator script name (the
# orchestrators pass their own filename around as `orchestrator_script`).
SCRIPT_TO_MODE: Dict[str, str] = {
    m.target_module + ".py": m.name
    for m in MODES
    if m.target_module and m.target_module.endswith("_orchestrator")
}


_BY_NAME: Dict[str, Mode] = {m.name: m for m in MODES}


def mode_names() -> Tuple[str, ...]:
    """Every mode word, in table order."""
    return tuple(m.name for m in MODES)


def user_facing_modes() -> Tuple[Mode, ...]:
    """The modes that have a ``--<name>`` user flag."""
    return tuple(m for m in MODES if m.user_facing)


def resolve(word: str) -> Optional[Mode]:
    """Resolve a mode word or alias to its :class:`Mode`, else ``None``."""
    return _BY_NAME.get(ALIASES.get(word, word))


def phase_for(word: str) -> Optional[str]:
    """The ``state.json`` phase name for a mode word or alias."""
    mode = resolve(word)
    return mode.phase if mode else None


def mode_for_script(script: str) -> Optional[str]:
    """The mode word that replaces a direct ``*_orchestrator.py`` invocation."""
    return SCRIPT_TO_MODE.get(script.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])


def instruction_path(word: str) -> Optional[str]:
    """Repo-relative path of a mode's core instruction file, if it has one."""
    mode = resolve(word)
    if mode is None or mode.instruction_file is None:
        return None
    return "instructions/" + mode.instruction_file


#: The phase vocabulary ``check_workflow_prerequisites.py`` gates on, in
#: workflow order. Imported there so one table owns it.
PREREQUISITE_PHASES: Tuple[str, ...] = tuple(
    m.phase for m in MODES if m.is_workflow_phase and m.phase
)


#: The modes ``--detach`` covers, in table order. One owner: the dispatcher's
#: rejection, ``utils/detach.py``'s guard and every error message read this.
DETACH_MODES: Tuple[str, ...] = tuple(m.name for m in MODES if m.supports_detach)


def phase_names() -> Tuple[str, ...]:
    """Every phase name any mode owns, in table order (includes ``ask``)."""
    seen: Dict[str, None] = {}
    for mode in MODES:
        if mode.phase:
            seen.setdefault(mode.phase, None)
    return tuple(seen)


def phase_from_selector(word: str) -> Optional[str]:
    """Resolve a ``--phase``/``--mode`` value to a phase name, or ``None``.

    Accepts either vocabulary, because the two differ for exactly one mode
    (``review-code`` → phase ``code-review``) and a caller should not have to know
    which one a given flag wanted. The resolution lives here so ``status``'s
    ``--phase`` selector and ``check_workflow_prerequisites.py``'s ``--mode``
    choices cannot drift apart.
    """
    if word in phase_names():
        return word
    return phase_for(word)


# The non-mode part of `argument-hint` — everything after the mode alternation.
# A literal because it describes flags, not modes; the mode list itself is
# rendered so a new row cannot be forgotten here. The commit modes take an
# optional range where the others take a plan (`POS_REVS`), and add two flags
# of their own.
ARGUMENT_HINT_TRAILER = (
    f' <plan_path>|{POS_REVS} (<range>: --*-commits only) '
    '["<question>" (required for --ask)] '
    "[--models provider:model ...] [--interactive] [--quick] [--yes] [--force] "
    '[--focus "<text>"|--context-plan PATH (--*-commits only)] '
    "[--dir PATH|--gitignore|--template-only (--init only)]"
)


def render_argument_hint() -> str:
    """Render SKILL.md's ``argument-hint`` value from the table."""
    flags = "|".join(f"--{m.name}" for m in user_facing_modes())
    return f"[{flags}]{ARGUMENT_HINT_TRAILER}"
