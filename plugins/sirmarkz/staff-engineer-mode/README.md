# Staff Engineer Mode

Staff Engineer Mode bakes decades of major-outage lessons into a set of
specialists. Each carries thousands of engineer-years of judgment from the
engineers who built and ran systems at the largest scale. You get
availability, reliability, resilience, security, operability, compatibility,
and rollout-safety checks before your code ships.

## Sources

Every outage case study here is built on a primary incident record: AWS
post-event summaries, Azure post-incident reviews, Google Cloud and Google
Workspace incident reports, Meta's outage writeups, and Netflix's AWS-outage
analysis.

The broader practices rest on first-party engineering sources: AWS Builders'
Library, Google's SRE books and Software Engineering at Google, Meta
Engineering, Microsoft's SDL and DevOps guidance, Apple's security and privacy
documentation, and Netflix's resilience work. Standards and guidance come from
NIST, CISA, OWASP, OpenSSF, IETF, and W3C.

See the [source index](skills/_shared/references/source-index.md) for the full
reference set. Staff Engineer Mode is independent and is not endorsed by or
affiliated with these organizations.

## How It Works

Ask a normal engineering question. Hand the agent a task, design, diff,
incident, rollout, or maintenance problem. The router picks one specialist
(occasionally one secondary), reads that file, and returns concrete decisions,
risks, checks, owners, supporting details, and next steps. You never name a
specialist.

Supported tools should list only the native `staff-engineer-mode` router.
Specialist files live under `specialists/` and load only after routing. The
router picks one primary specialist by default.

For commits and amends, Staff Engineer Mode calls `agent-pr-review` against
the exact staged diff. For releases, tags, version bumps, packages, artifacts,
and promotions, it calls `release-build-reproducibility` and
`production-readiness-review` together.

## Installation

Commands labeled "terminal" are run in your shell. Commands labeled "agent
chat" are typed inside that tool's interactive agent session.

### Claude Code

Terminal:

```bash
claude plugin marketplace add https://github.com/sirmarkz/staff-engineer-mode.git
claude plugin install staff-engineer-mode@staff-engineer-mode
```

Agent chat:

```text
/plugin marketplace add https://github.com/sirmarkz/staff-engineer-mode.git
```

```text
/plugin install staff-engineer-mode@staff-engineer-mode
```

### Codex

Terminal:

```bash
codex plugin marketplace add https://github.com/sirmarkz/staff-engineer-mode.git
codex plugin add staff-engineer-mode@staff-engineer-mode
```

### Cursor

Terminal:

```bash
git clone https://github.com/sirmarkz/staff-engineer-mode.git ~/.cursor/staff-engineer-mode-src
mkdir -p ~/.cursor/plugins
ln -s ~/.cursor/staff-engineer-mode-src ~/.cursor/plugins/staff-engineer-mode
```

### OpenCode

Terminal:

```bash
opencode plugin 'staff-engineer-mode@git+https://github.com/sirmarkz/staff-engineer-mode.git'
```

### GitHub Copilot CLI

Terminal:

```bash
copilot plugin marketplace add https://github.com/sirmarkz/staff-engineer-mode.git
```

Install the plugin:

```bash
copilot plugin install staff-engineer-mode@staff-engineer-mode
```

### Gemini CLI

Terminal:

```bash
gemini extensions install https://github.com/sirmarkz/staff-engineer-mode
```

## Verify

Start a fresh session inside any open repo and ask one of:

- "Before implementing partner webhooks, design delivery retries, replay, and dead-letter handling."
- "For a new inventory dependency call, decide timeout, retry, and fallback."
- "Review my last commit."

The agent should load the router, choose one specialist, and respond with concrete decisions, risks, checks, owners, supporting details, and next steps.

For more coverage, see the [sample prompts](evals/prompts/expected-routes.md).

## What's Inside

One native router skill: `staff-engineer-mode`. It routes to 54 specialist
files under `specialists/`; those files are not installed or listed as separate
native skills.

All specialist files by surface:

| Surface | Specialist files |
| --- | --- |
| Architecture, contracts, and correctness | [`architecture-decisions`](specialists/architecture-decisions.md), [`api-design-and-compatibility`](specialists/api-design-and-compatibility.md), [`data-contracts`](specialists/data-contracts.md), [`state-machine-correctness`](specialists/state-machine-correctness.md) |
| Reliability and resilience | [`slo-and-error-budgets`](specialists/slo-and-error-budgets.md), [`high-availability-design`](specialists/high-availability-design.md), [`dependency-resilience`](specialists/dependency-resilience.md), [`backup-and-recovery`](specialists/backup-and-recovery.md), [`resilience-experiments`](specialists/resilience-experiments.md), [`performance-and-capacity`](specialists/performance-and-capacity.md) |
| Change review, delivery, and rollout safety | [`agent-pr-review`](specialists/agent-pr-review.md), [`progressive-delivery`](specialists/progressive-delivery.md), [`feature-flag-lifecycle`](specialists/feature-flag-lifecycle.md), [`release-build-reproducibility`](specialists/release-build-reproducibility.md), [`production-readiness-review`](specialists/production-readiness-review.md), [`migration-and-deprecation`](specialists/migration-and-deprecation.md), [`configuration-and-automation-safety`](specialists/configuration-and-automation-safety.md), [`fleet-upgrades`](specialists/fleet-upgrades.md) |
| Testing, quality, and environment parity | [`testing-and-quality-gates`](specialists/testing-and-quality-gates.md), [`test-data-engineering`](specialists/test-data-engineering.md), [`dev-environment-parity`](specialists/dev-environment-parity.md) |
| Maintenance and code hygiene | [`dependency-and-code-hygiene`](specialists/dependency-and-code-hygiene.md) |
| Operations and observability | [`observability-and-alerting`](specialists/observability-and-alerting.md), [`incident-response-and-postmortems`](specialists/incident-response-and-postmortems.md), [`oncall-health`](specialists/oncall-health.md) |
| Security and privacy | [`secure-sdlc-and-threat-modeling`](specialists/secure-sdlc-and-threat-modeling.md), [`identity-and-secrets`](specialists/identity-and-secrets.md), [`cryptography-and-key-lifecycle`](specialists/cryptography-and-key-lifecycle.md), [`software-supply-chain-security`](specialists/software-supply-chain-security.md), [`vulnerability-management`](specialists/vulnerability-management.md), [`tenant-isolation`](specialists/tenant-isolation.md), [`privacy-and-data-lifecycle`](specialists/privacy-and-data-lifecycle.md), [`llm-application-security`](specialists/llm-application-security.md) |
| Data and workflow systems | [`distributed-data-and-consistency`](specialists/distributed-data-and-consistency.md), [`database-operations`](specialists/database-operations.md), [`event-workflows`](specialists/event-workflows.md), [`data-pipeline-reliability`](specialists/data-pipeline-reliability.md), [`caching-and-derived-data`](specialists/caching-and-derived-data.md) |
| Platform, edge, and cost | [`platform-golden-paths`](specialists/platform-golden-paths.md), [`infrastructure-and-policy-as-code`](specialists/infrastructure-and-policy-as-code.md), [`internal-service-networking`](specialists/internal-service-networking.md), [`edge-traffic-and-ddos-defense`](specialists/edge-traffic-and-ddos-defense.md), [`cost-aware-reliability`](specialists/cost-aware-reliability.md) |
| Client release gates | [`web-release-gates`](specialists/web-release-gates.md), [`mobile-release-engineering`](specialists/mobile-release-engineering.md), [`accessibility-gates`](specialists/accessibility-gates.md) |
| LLM and ML systems | [`llm-evaluation`](specialists/llm-evaluation.md), [`llm-serving-cost-and-latency`](specialists/llm-serving-cost-and-latency.md), [`ml-reliability-and-evaluation`](specialists/ml-reliability-and-evaluation.md) |
| Experimentation and metric guardrails | [`experimentation-and-metric-guardrails`](specialists/experimentation-and-metric-guardrails.md) |
| AI-agent workflow | [`ai-coding-governance`](specialists/ai-coding-governance.md), [`code-readability-for-agents`](specialists/code-readability-for-agents.md) |
| Engineering control records | [`engineering-control-evidence`](specialists/engineering-control-evidence.md) |
| Engineering documentation lifecycle | [`documentation-lifecycle`](specialists/documentation-lifecycle.md) |

## Contributing

Patches welcome, especially practices from authoritative sources: first-party engineering publications, official documentation, standards bodies, peer-reviewed papers, or widely cited practitioner references.

New specialist files must be technology-agnostic, cite source-index references, and avoid vendor endorsement. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. The voice is enforced.

## License

MIT
