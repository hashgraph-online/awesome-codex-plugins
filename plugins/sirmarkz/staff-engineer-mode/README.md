# Staff Engineer Mode

[![Release](https://img.shields.io/github/v/release/sirmarkz/staff-engineer-mode?label=release)](./RELEASE-NOTES.md)

**Your AI coding agent ships fast. This makes it ship with judgment.**

Best software engineering practices from FAANG, packaged as
decision guidance for AI coding agents. As agents write material amounts of
production code, the bottleneck is no longer how fast they write; it is whether
they reason about what happens when the code runs at 3am. Staff Engineer Mode closes that
gap before an agent ships code without the reliability, security, operability,
compatibility, and rollout judgment production systems need.

## Sources

Staff Engineer Mode distills public engineering practices from AWS Builders' Library,
Google SRE and Software Engineering at Google, Meta Engineering, Microsoft SDL
and DevOps guidance, Apple security and privacy docs, Netflix resilience work,
and standards from NIST, CISA, OWASP, OpenSSF, IETF, and W3C into practical
guidance for AI coding agents. See the
[source index](skills/_shared/references/source-index.md) for references and
stable source IDs. Staff Engineer Mode is independent and is not endorsed by or
affiliated with those organizations.

## How It Works

Ask a normal engineering question. Hand the agent a task, design, diff, incident, rollout, or maintenance problem. The router reads the work, picks one specialist (occasionally one secondary), reads that specialist file, and returns concrete decisions, risks, checks, owners, supporting details, and next steps. You never name a specialist.

Supported tools should list only the native `staff-engineer-mode` router. Specialist files live under `specialists/` and load only after routing.

The router refuses to load every plausible specialist. One primary specialist at a time, by default.

See [SAMPLE-PROMPTS.md](SAMPLE-PROMPTS.md) for prompts across every specialist.

## Installation

### Claude Code

Register the marketplace:

```text
/plugin marketplace add https://github.com/sirmarkz/staff-engineer-mode.git
```

Install the plugin:

```text
/plugin install staff-engineer-mode@staff-engineer-mode
```

### Codex

Works with Codex CLI and Codex App. Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/sirmarkz/staff-engineer-mode/main/.codex/INSTALL.md
```

### Cursor

```text
/add-plugin staff-engineer-mode
```

### OpenCode

Works with OpenCode. Tell OpenCode:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/sirmarkz/staff-engineer-mode/main/.opencode/INSTALL.md
```

### GitHub Copilot CLI

Register the marketplace:

```bash
copilot plugin marketplace add https://github.com/sirmarkz/staff-engineer-mode.git
```

Install the plugin:

```bash
copilot plugin install staff-engineer-mode@staff-engineer-mode
```

### Gemini CLI

```bash
gemini extensions install https://github.com/sirmarkz/staff-engineer-mode
```

## Verify

Start a fresh session inside any open repo and ask one of:

- "Before implementing partner webhooks, design the event contract, delivery retries, replay path, and dead-letter handling."
- "During development of the checkout inventory call, decide timeout, retry, fallback, and duplicate-work safeguards."
- "Review my last commit and tell me what you would catch in PR review."

The agent should load the router, choose one specialist, and respond with concrete decisions, risks, checks, owners, supporting details, and next steps — not vibes.

## What's Inside

One native router skill: `staff-engineer-mode`. It routes to 54 specialist
files under `specialists/`; those files are not installed or listed as separate
native skills.

Examples by surface:

| Surface | Example specialist files |
| --- | --- |
| Architecture and interfaces | [`architecture-decisions`](specialists/architecture-decisions.md), [`api-design-and-compatibility`](specialists/api-design-and-compatibility.md), [`data-contracts`](specialists/data-contracts.md), [`state-machine-correctness`](specialists/state-machine-correctness.md) |
| Reliability and resilience | [`slo-and-error-budgets`](specialists/slo-and-error-budgets.md), [`high-availability-design`](specialists/high-availability-design.md), [`dependency-resilience`](specialists/dependency-resilience.md), [`backup-and-recovery`](specialists/backup-and-recovery.md), [`resilience-experiments`](specialists/resilience-experiments.md), [`performance-and-capacity`](specialists/performance-and-capacity.md) |
| Delivery and change safety | [`progressive-delivery`](specialists/progressive-delivery.md), [`feature-flag-lifecycle`](specialists/feature-flag-lifecycle.md), [`release-build-reproducibility`](specialists/release-build-reproducibility.md), [`testing-and-quality-gates`](specialists/testing-and-quality-gates.md), [`test-data-engineering`](specialists/test-data-engineering.md), [`dev-environment-parity`](specialists/dev-environment-parity.md), [`migration-and-deprecation`](specialists/migration-and-deprecation.md), [`code-readability-for-agents`](specialists/code-readability-for-agents.md), [`dependency-and-code-hygiene`](specialists/dependency-and-code-hygiene.md), [`configuration-and-automation-safety`](specialists/configuration-and-automation-safety.md), [`fleet-upgrades`](specialists/fleet-upgrades.md) |
| Operations and observability | [`observability-and-alerting`](specialists/observability-and-alerting.md) |
| Security and privacy | [`secure-sdlc-and-threat-modeling`](specialists/secure-sdlc-and-threat-modeling.md), [`identity-and-secrets`](specialists/identity-and-secrets.md), [`cryptography-and-key-lifecycle`](specialists/cryptography-and-key-lifecycle.md), [`software-supply-chain-security`](specialists/software-supply-chain-security.md), [`vulnerability-management`](specialists/vulnerability-management.md), [`tenant-isolation`](specialists/tenant-isolation.md), [`privacy-and-data-lifecycle`](specialists/privacy-and-data-lifecycle.md) |
| Data and workflow systems | [`distributed-data-and-consistency`](specialists/distributed-data-and-consistency.md), [`database-operations`](specialists/database-operations.md), [`event-workflows`](specialists/event-workflows.md), [`data-pipeline-reliability`](specialists/data-pipeline-reliability.md), [`caching-and-derived-data`](specialists/caching-and-derived-data.md) |
| Platform and edge | [`infrastructure-and-policy-as-code`](specialists/infrastructure-and-policy-as-code.md), [`internal-service-networking`](specialists/internal-service-networking.md), [`edge-traffic-and-ddos-defense`](specialists/edge-traffic-and-ddos-defense.md), [`cost-aware-reliability`](specialists/cost-aware-reliability.md) |
| Client, ML/AI, and experimentation | [`web-release-gates`](specialists/web-release-gates.md), [`mobile-release-engineering`](specialists/mobile-release-engineering.md), [`accessibility-gates`](specialists/accessibility-gates.md), [`llm-application-security`](specialists/llm-application-security.md), [`llm-evaluation`](specialists/llm-evaluation.md), [`llm-serving-cost-and-latency`](specialists/llm-serving-cost-and-latency.md), [`ml-reliability-and-evaluation`](specialists/ml-reliability-and-evaluation.md), [`experimentation-and-metric-guardrails`](specialists/experimentation-and-metric-guardrails.md) |
| Engineering workflow, readiness, and controls | [`agent-pr-review`](specialists/agent-pr-review.md), [`ai-coding-governance`](specialists/ai-coding-governance.md), [`documentation-lifecycle`](specialists/documentation-lifecycle.md), [`engineering-control-evidence`](specialists/engineering-control-evidence.md), [`production-readiness-review`](specialists/production-readiness-review.md), [`incident-response-and-postmortems`](specialists/incident-response-and-postmortems.md), [`oncall-health`](specialists/oncall-health.md), [`platform-golden-paths`](specialists/platform-golden-paths.md) |

## Contributing

Patches welcome — especially additional practices from authoritative sources: first-party engineering publications, official documentation, standards bodies, peer-reviewed papers, or widely cited practitioner references.

New specialist files must be technology-agnostic, cite stable source IDs, and avoid vendor endorsement. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. The voice is enforced.

## License

MIT — see [LICENSE](LICENSE). The project notice is included there.
