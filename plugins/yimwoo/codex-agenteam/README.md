<p align="center">
  <img src="assets/agenteam-banner.png" alt="AgenTeam — Role-based AI team for Codex" width="100%">
</p>

<p align="center">
  <a href="https://github.com/yimwoo/codex-agenteam/releases"><img src="https://img.shields.io/github/v/release/yimwoo/codex-agenteam?color=2563EB&label=version&style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/yimwoo/codex-agenteam/stargazers"><img src="https://img.shields.io/github/stars/yimwoo/codex-agenteam?color=2563EB&style=flat-square" alt="Stars"></a>
  <a href="https://github.com/yimwoo/codex-agenteam/issues"><img src="https://img.shields.io/github/issues/yimwoo/codex-agenteam?color=2563EB&style=flat-square" alt="Issues"></a>
</p>

<p align="center">
  <strong>A full AI development team — researcher, PM, architect, dev, QA, and reviewer — as native Codex agents, orchestrated through a configurable pipeline.</strong>
</p>

---

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/yimwoo/codex-agenteam/main/install.sh | bash
```

Restart Codex, go to **Plugins > Local Plugins**, install AgenTeam, then:

```
@ATeam build my team
```

If the role picker does not show `@Architect`, `@Dev`, and the others right
away, confirm the project has `.codex/agents/*.toml`, then open a new thread
or restart Codex so it reloads workspace agents.

---

## Your Team

| Role | Mention | Job |
|------|---------|-----|
| Researcher | `@Researcher` | Investigates docs, trends, prior art |
| PM | `@Pm` | Prioritizes work, writes specs |
| Architect | `@Architect` | Designs systems, identifies risks |
| Dev | `@Dev` | Writes production code |
| Qa | `@Qa` | Writes tests, catches regressions |
| Reviewer | `@Reviewer` | Reviews for correctness and security |

```
@Architect review this API design
@Dev fix the race condition in src/queue.py
@ATeam add user authentication
```

---

## Documentation

- [**Setup & Installation**](docs/setup.md) — prerequisites, install, update
- [**Configuration**](docs/configuration.md) — roles, profiles, model routing, two-layer config
- [**Pipeline & Profiles**](docs/pipeline.md) — stages, gates, verification, resume, CI repair
- [**CLI Reference**](docs/cli.md) — all skills and runtime commands
- [**HOTL Integration**](docs/hotl.md) — structured execution with the HOTL plugin
- [**Benchmarking**](benchmarks/README.md) — reproducible strategy comparisons from run evidence

## Current Capabilities

- **Run control:** configurable stages, role routing, isolation, verification,
  retries, rework, gates, and resume.
- **Compatibility and observability:** `doctor`, `status`, `trace`, standups,
  reports, and portable evidence bundles.
- **Portable planning:** deterministic workspace-agent export plus
  evidence-backed benchmark conversion and reporting.
- **Structured handoffs:** opt-in schema-validated role results with SHA-256
  provenance, downstream prompt reuse, and trace/evidence metrics.
- **Governed delivery:** optional decision logs, tripwires, scope audits, and
  approval evidence for larger or longer-lived work.

These capabilities are additive. Quick fixes and standard pipelines remain
lightweight unless you enable structured handoffs or governed delivery.

---

## Contributing

Found a bug or have a role idea? [Open an issue](https://github.com/yimwoo/codex-agenteam/issues) or submit a PR.

## License

MIT © [Yiming Wu](https://github.com/yimwoo)
