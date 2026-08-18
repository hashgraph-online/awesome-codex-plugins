# Staff Engineer Mode

**Staff-level engineering judgment for coding agents, from design to production.**

Give Staff Engineer Mode a design, diff, rollout, incident, migration, or
maintenance problem. One router selects one of 64 focused specialists. The
agent works through relevant failure modes and verification checks before it
ships code or changes production.

You get concrete decisions, risks, checks, and next steps across
architecture, reliability, security, delivery, data, platform, and operations.

## How It Works

Ask a normal engineering question. You never need to name a specialist.

The router classifies the requested artifact, lifecycle phase, engineering
surface, and risk. It chooses one primary specialist and adds a secondary only
when the request needs a separate artifact.

Supported tools list only the native `staff-engineer-mode` router. The 64
specialist files stay under `specialists/` and load only after routing.

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

## Try It

Start a fresh session inside any open repo and try one of these prompts:

- "Before implementing partner webhooks, design delivery retries, replay, and dead-letter handling."
- "For a new inventory dependency call, decide timeout, retry, and fallback."
- "Review my last commit."

The agent should load the router, choose one specialist, and respond with
concrete decisions, risks, checks, owners, supporting details, and next steps.

For more coverage, see the [sample prompts](evals/prompts/expected-routes.md).

## What's Inside

Staff Engineer Mode ships one native router skill. It keeps 64 specialist files
under `specialists/` and loads them after routing.

The concern groups below help you browse. Runtime routing still follows the
requested artifact, phase, surface, and risk.

| Engineering concern | Specialist files |
| --- | --- |
| Architecture & interfaces | [`architecture-decisions`](specialists/architecture-decisions.md), [`api-design-and-compatibility`](specialists/api-design-and-compatibility.md), [`data-contracts`](specialists/data-contracts.md), [`event-workflows`](specialists/event-workflows.md), [`resilience-requirements`](specialists/resilience-requirements.md), [`persistent-connection-systems`](specialists/persistent-connection-systems.md) |
| Verification & evaluation | [`state-machine-correctness`](specialists/state-machine-correctness.md), [`testing-and-quality-gates`](specialists/testing-and-quality-gates.md), [`test-data-engineering`](specialists/test-data-engineering.md), [`agent-pr-review`](specialists/agent-pr-review.md), [`experimentation-and-metric-guardrails`](specialists/experimentation-and-metric-guardrails.md) |
| Reliability & resilience | [`slo-and-error-budgets`](specialists/slo-and-error-budgets.md), [`high-availability-design`](specialists/high-availability-design.md), [`dependency-resilience`](specialists/dependency-resilience.md), [`backup-and-recovery`](specialists/backup-and-recovery.md), [`resilience-experiments`](specialists/resilience-experiments.md), [`performance-and-capacity`](specialists/performance-and-capacity.md), [`cost-aware-reliability`](specialists/cost-aware-reliability.md), [`multi-region-and-data-residency`](specialists/multi-region-and-data-residency.md), [`scheduled-job-reliability`](specialists/scheduled-job-reliability.md) |
| Data, storage & privacy | [`distributed-data-and-consistency`](specialists/distributed-data-and-consistency.md), [`database-operations`](specialists/database-operations.md), [`data-pipeline-reliability`](specialists/data-pipeline-reliability.md), [`caching-and-derived-data`](specialists/caching-and-derived-data.md), [`privacy-and-data-lifecycle`](specialists/privacy-and-data-lifecycle.md), [`data-lineage-and-provenance`](specialists/data-lineage-and-provenance.md) |
| Delivery & change safety | [`progressive-delivery`](specialists/progressive-delivery.md), [`feature-flag-lifecycle`](specialists/feature-flag-lifecycle.md), [`release-build-reproducibility`](specialists/release-build-reproducibility.md), [`fleet-upgrades`](specialists/fleet-upgrades.md), [`migration-and-deprecation`](specialists/migration-and-deprecation.md), [`configuration-and-automation-safety`](specialists/configuration-and-automation-safety.md), [`dev-environment-parity`](specialists/dev-environment-parity.md), [`service-decommission-and-sunset`](specialists/service-decommission-and-sunset.md) |
| Code quality & maintainability | [`code-readability-for-agents`](specialists/code-readability-for-agents.md), [`dependency-and-code-hygiene`](specialists/dependency-and-code-hygiene.md) |
| Operations & incident response | [`observability-and-alerting`](specialists/observability-and-alerting.md), [`incident-response-and-postmortems`](specialists/incident-response-and-postmortems.md), [`oncall-health`](specialists/oncall-health.md), [`operational-ownership-transfer`](specialists/operational-ownership-transfer.md) |
| Security | [`secure-sdlc-and-threat-modeling`](specialists/secure-sdlc-and-threat-modeling.md), [`identity-and-secrets`](specialists/identity-and-secrets.md), [`cryptography-and-key-lifecycle`](specialists/cryptography-and-key-lifecycle.md), [`software-supply-chain-security`](specialists/software-supply-chain-security.md), [`vulnerability-management`](specialists/vulnerability-management.md), [`tenant-isolation`](specialists/tenant-isolation.md), [`edge-traffic-and-ddos-defense`](specialists/edge-traffic-and-ddos-defense.md), [`llm-application-security`](specialists/llm-application-security.md), [`input-validation-and-injection-defense`](specialists/input-validation-and-injection-defense.md), [`client-application-security`](specialists/client-application-security.md) |
| Platform & infrastructure | [`infrastructure-and-policy-as-code`](specialists/infrastructure-and-policy-as-code.md), [`internal-service-networking`](specialists/internal-service-networking.md), [`platform-golden-paths`](specialists/platform-golden-paths.md), [`container-runtime-and-orchestration`](specialists/container-runtime-and-orchestration.md) |
| Client applications & accessibility | [`web-release-gates`](specialists/web-release-gates.md), [`mobile-release-engineering`](specialists/mobile-release-engineering.md), [`accessibility-gates`](specialists/accessibility-gates.md) |
| AI/ML evaluation & serving | [`llm-evaluation`](specialists/llm-evaluation.md), [`ml-reliability-and-evaluation`](specialists/ml-reliability-and-evaluation.md), [`llm-serving-cost-and-latency`](specialists/llm-serving-cost-and-latency.md) |
| Engineering controls & readiness | [`ai-coding-governance`](specialists/ai-coding-governance.md), [`documentation-lifecycle`](specialists/documentation-lifecycle.md), [`engineering-control-evidence`](specialists/engineering-control-evidence.md), [`production-readiness-review`](specialists/production-readiness-review.md) |

## Sources

The practice library uses first-party engineering publications from Amazon,
Google, Meta, Microsoft, Apple, and Netflix. Standards and guidance come from
NIST, CISA, OWASP, OpenSSF, IETF, and W3C.

The library covers public incident records from AWS, Azure, Google Cloud,
Google Workspace, Meta, and Netflix.

See the [source index](skills/_shared/references/source-index.md) for the full
reference set. Staff Engineer Mode is independent and is not endorsed by or
affiliated with these organizations.

## Contributing

Patches are welcome. New practices should come from authoritative sources:
first-party engineering publications, official documentation, standards
bodies, peer-reviewed papers, or widely cited practitioner references.

Contributors must keep new specialists technology-agnostic. Do not endorse
vendors. Maintain authoritative sources in the shared index and read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. Repository checks
enforce this voice.

## License

MIT
