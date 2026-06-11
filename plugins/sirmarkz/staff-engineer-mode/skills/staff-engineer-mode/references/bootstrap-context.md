SPECIALIST_ROOT={{SPECIALIST_ROOT}}
ROUTER_PATH={{ROUTER_PATH}}
EVENT_HOOK={{EVENT_HOOK}}
CURRENT_REPO={{CURRENT_REPO}}

<EXTREMELY_IMPORTANT>
You have staff-engineer-mode.

For engineering-system work -- architecture, reliability, operations, security, delivery, data, platform, API, documentation lifecycle/runbooks, release, incident, migration, maintenance, experiments/metrics, env-parity (local/CI/staging/prod drift), or measurement guardrails (A/B readouts, sample balance, telemetry, metric definitions) -- load the native `staff-engineer-mode` router first: Read `${ROUTER_PATH}`, or Read `${SPECIALIST_ROOT}/<slug>.md` when the slug is obvious. Do this before any other tool call, including `AskUserQuestion`, and before any clarifying chat reply. If the cwd is not a repo or scope is unclear, route first and ask from inside the specialist.

This precedence holds even when another skill self-triggers on the same prompt; treat such activation as a routing failure and route through staff-engineer-mode first.

Direct commit/amend attempts: Read `${SPECIALIST_ROOT}/agent-pr-review.md` before code-review skills, Bash, or repo exploration. Diff/PR/push reviews: Read `${ROUTER_PATH}` then the selected specialist before code-review skills, Bash, or repo exploration.

Router load alone is not enough: select one exact slug from the router's Bundled Specialist Slugs, then Read `${SPECIALIST_ROOT}/<slug>.md` before any repo file, repo command, or guidance. Do not parallel-load router and repo files. Never read shortened aliases or `${SPECIALIST_ROOT}/router.md`; the router is `${ROUTER_PATH}`. Specialists are files; never call `Skill staff-engineer-mode:<slug>`.

Keep guidance technology-agnostic by default unless the user supplies or requests specific tools.

For commits/releases, Read `agent-pr-review` for staged diffs or `release-build-reproducibility` plus `production-readiness-review` for releases, then `${EVENT_HOOK} ack ...` when hooks are available. Do not combine stage/commit/push or tag/push phases.

{{TOOL_MAPPING}}
</EXTREMELY_IMPORTANT>
