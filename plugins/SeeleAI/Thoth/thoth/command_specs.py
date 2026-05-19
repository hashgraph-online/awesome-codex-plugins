"""Host-neutral public command specifications for Thoth."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommandSpec:
    """Host-neutral public surface definition."""

    command_id: str
    summary: str
    argument_hint: str
    route_class: str = "mechanical_fast"
    intelligence_tier: str = "none"
    packet_authority_mode: str = "none"
    durable: bool = False
    supports_codex_executor: bool = False
    needs_hooks: bool = False
    needs_subagents: bool = False
    acceptance: str = "Script-backed acceptance only."
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    scope_can: tuple[str, ...] = field(default_factory=tuple)
    scope_cannot: tuple[str, ...] = field(default_factory=tuple)
    lifecycle: tuple[str, ...] = field(default_factory=tuple)
    interaction_gaps: tuple[str, ...] = field(default_factory=tuple)
    internal_routes: tuple[str, ...] = field(default_factory=tuple)


COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec(
        command_id="init",
        summary="Initialize, migrate, or resync canonical .thoth authority without taking ownership of repo-root `.codex`.",
        argument_hint="[--sync] [--migrate preview|apply] [--migrate --preview|--apply]",
        route_class="mechanical_fast",
        intelligence_tier="none",
        packet_authority_mode="result_envelope",
        acceptance="Authority tree, host projections, Codex hook projection, dashboard, scripts, and tests are generated from one canonical source while repo-root `.codex` remains host-owned.",
        needs_hooks=True,
        scope_can=(
            "Create canonical .thoth project authority files",
            "Generate AGENTS.md and CLAUDE.md from the same renderer",
            "Generate a Codex hooks projection under .thoth/derived for global or repo-local host wiring",
            "Generate dashboard, tests, helper scripts, and config",
        ),
        scope_cannot=(
            "Silently delete existing project files",
            "Treat repo-root .codex as a Thoth-managed authority directory",
            "Treat hooks as correctness-critical runtime dependencies",
        ),
        lifecycle=("preview", "render-authority", "render-projections", "verify"),
        interaction_gaps=("Project description", "Directions/phases", "Dashboard port/theme"),
    ),
    CommandSpec(
        command_id="run",
        summary="Start one strict run bound to `work_id@revision`; live runs foreground and `--sleep` detaches the same runtime driver.",
        argument_hint="[--executor claude|codex] [--host claude|codex] [--sleep] [--attach <run_id>] [--watch <run_id>] [--stop <run_id>] --work-id <work_id>",
        route_class="live_intelligent",
        intelligence_tier="high",
        packet_authority_mode="phase_controller",
        durable=True,
        supports_codex_executor=True,
        acceptance="A durable run object and ledger with plan/execute/validate/reflect phase_result artifacts exists under .thoth/objects and .thoth/runs/<run_id>; live and sleep share one runtime driver.",
        needs_subagents=True,
        allowed_tools=("Read", "Glob", "Grep", "Edit", "Write", "Bash", "Task"),
        scope_can=(
            "Drive plan -> execute -> validate -> reflect through one RuntimeDriver",
            "Switch to detached monitor placement only with --sleep",
            "Write fixed phase artifacts and terminal results through the shared authority",
            "Stop or watch an existing run",
        ),
        scope_cannot=(
            "Use host session state as runtime truth",
            "Use detached live execution without --sleep",
        ),
        lifecycle=("prepare", "plan", "execute", "validate", "reflect", "attach/watch/stop", "acceptance"),
        interaction_gaps=("Ready runnable work id",),
    ),
    CommandSpec(
        command_id="loop",
        summary="Start one bounded controller service whose parent creates four-phase child runs.",
        argument_hint="[--executor claude|codex] [--host claude|codex] [--sleep] [--attach <run_id>] [--resume <run_id>] [--watch <run_id>] [--stop <run_id>] --work-id <work_id>",
        route_class="live_intelligent",
        intelligence_tier="high",
        packet_authority_mode="phase_controller",
        durable=True,
        supports_codex_executor=True,
        acceptance="The parent loop run enforces child iteration count and wall-clock budget mechanically, records child run lineage, and stops immediately on the first validated child run.",
        needs_subagents=True,
        allowed_tools=("Read", "Glob", "Grep", "Edit", "Write", "Bash", "Task"),
        scope_can=(
            "Create or resume a durable bounded loop orchestrator",
            "Attach/watch/stop through the same runtime state machine",
            "Delegate work to Codex without changing authority write shape",
        ),
        scope_cannot=(
            "Use detached live execution without --sleep",
            "Depend on subagents or hooks for correctness",
        ),
        lifecycle=("prepare", "loop-parent", "child-plan", "child-execute", "child-validate", "child-reflect", "attach/resume/watch/stop", "acceptance"),
        interaction_gaps=("Ready runnable work id",),
    ),
    CommandSpec(
        command_id="review",
        summary="Prepare a structured live review packet through the shared Thoth surface.",
        argument_hint="[--executor claude|codex] [--host claude|codex] [--work-id <work_id>] <target>",
        route_class="live_intelligent",
        intelligence_tier="high",
        packet_authority_mode="review_packet",
        supports_codex_executor=True,
        acceptance="Findings are reported in structured form through the same authority protocol without mutating source code, while preserving executor parity.",
        needs_subagents=True,
        allowed_tools=("Read", "Glob", "Grep", "Bash", "Task"),
        scope_can=("Read code and documents", "Delegate review to Codex", "Write structured findings through the protocol"), 
        scope_cannot=("Modify project code", "Claim acceptance without evidence"),
        lifecycle=("prepare", "live-native-review", "protocol-update", "report"),
        internal_routes=("exact_match=protocol_fast", "open_ended=live_intelligent"),
    ),
    CommandSpec(
        command_id="auto",
        summary="Run the highest-priority actionable work queue until ready/active/failed work is closed, paused, or stopped.",
        argument_hint="[--sleep] [--rounds <n>] [--scope all-open|ready|priority-top] [--work-id <work_id> ...] [--watch <controller_id>] [--stop <controller_id>]",
        route_class="live_intelligent",
        intelligence_tier="high",
        packet_authority_mode="phase_controller",
        durable=True,
        supports_codex_executor=True,
        needs_subagents=True,
        acceptance="A controller object records request parameters, fixed work refs when provided, dynamic queue snapshots, and a cursor; active controllers reject parameter drift.",
        allowed_tools=("Read", "Glob", "Grep", "Edit", "Write", "Bash", "Task", "Monitor"),
        scope_can=("Execute ready work items through child loops", "Monitor active work", "Let a later new controller revisit failed work"),
        scope_cannot=("Auto-abandon work items", "Execute blocked or draft work", "Bypass execution-safety doctor preflight"),
        lifecycle=("execution-safety-preflight", "select-priority-work", "child-loop", "monitor", "pause/stop/terminal"),
    ),
    CommandSpec(
        command_id="status",
        summary="Show repo status and active durable runs from the shared ledger.",
        argument_hint="[--json] [--doctor] [--report] [--dashboard start|stop|rebuild]",
        route_class="mechanical_fast",
        intelligence_tier="none",
        packet_authority_mode="result_envelope",
        acceptance="Status reports repo health plus active/stale run summaries without replacing attach/watch.",
        scope_can=("Read .thoth authority and machine-local registry",),
        scope_cannot=("Infer runtime state from chat history",),
        lifecycle=("read", "summarize"),
    ),
    CommandSpec(
        command_id="discuss",
        summary="Discuss or record planning decisions without entering implementation execution.",
        argument_hint="<topic>",
        route_class="live_intelligent",
        intelligence_tier="high",
        packet_authority_mode="command_packet",
        acceptance="Closed planning output is recorded into discussion, decision, and work_item objects and may produce at most one work subtree without mutating code.",
        scope_can=("Update discussions, decisions, and work items", "Generate a complete work subtree"),
        scope_cannot=("Modify source code", "Create ready runnable work while questions remain", "Modify work locked by active execution"),
        lifecycle=("inquire", "close", "write-object-subtree", "generate-doc-view"),
    ),
    CommandSpec(
        command_id="doctor",
        summary="Alias for `status --doctor`; strictly audit project health without writing authority.",
        argument_hint="[--quick] [--json] [--fix preview|apply] [--version]",
        route_class="mechanical_fast",
        intelligence_tier="none",
        packet_authority_mode="result_envelope",
        acceptance="Doctor validates .thoth authority and generated projections without assuming repo-root `.codex` is Thoth-managed.",
        scope_can=("Run health checks", "Verify generated surfaces"),
        scope_cannot=("Use missing hooks as a correctness failure by themselves", "Mutate project authority without explicit init --migrate --apply"),
        lifecycle=("audit", "report"),
    ),
    CommandSpec(
        command_id="dashboard",
        summary="Alias for `status --dashboard`; manage the local dashboard backed by .thoth ledgers.",
        argument_hint="[start|stop|rebuild]",
        route_class="mechanical_fast",
        intelligence_tier="none",
        packet_authority_mode="result_envelope",
        acceptance="Dashboard reads .thoth/runs data only and renders host/executor/runtime distinctions explicitly.",
        scope_can=("Start the dashboard", "Report dashboard endpoints"),
        scope_cannot=("Read host session state as runtime truth",),
        lifecycle=("serve",),
    ),
)


COMMAND_SPECS_BY_ID = {spec.command_id: spec for spec in COMMAND_SPECS}

PUBLIC_CODEX_COMMANDS: tuple[str, ...] = tuple(spec.command_id for spec in COMMAND_SPECS)
