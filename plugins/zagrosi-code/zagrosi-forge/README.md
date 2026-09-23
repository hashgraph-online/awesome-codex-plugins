<div align="center">
  <img src="assets/icon.svg" alt="Zagrosi Forge icon" width="96" height="96" />
  <h1>Zagrosi Forge</h1>
  <p><strong>Lean Codex workflows for project decomposition, planning, and test-first implementation.</strong></p>
  <p>
    <a href="https://github.com/zagrosi-code/zagrosi-forge"><img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-0F766E?style=flat-square" /></a>
    <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-334155?style=flat-square" />
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-111827?style=flat-square" />
  </p>
  <img src="assets/readme-hero.svg" alt="Zagrosi Forge workflow hero" width="100%" />
</div>

Forge turns a broad request into bounded specs, an implementation-ready plan,
and tested code. Lean mode is default: fewer files, shorter prompts, one setup,
one final gate.

## Lean By Default

| Mode | Use |
|------|-----|
| `lean` | Default. Minimum sufficient artifacts and focused checks. |
| `standard` | Explicit opt-in for wider research, traceability, or coordination. |
| `deep` | Explicit opt-in for high-risk or architecture-heavy work. |

Depth changes investigation and review rigor. Every mode uses compact, canonical
contracts with stable requirement IDs, exact file ownership, observable acceptance,
and verification. No minimum prose quotas or duplicate research, TDD, decision,
and review files. Extra artifacts serve independent ownership or a material need.

## Install

Requires Codex plugin support and Python 3.11+.

```bash
git clone https://github.com/zagrosi-code/zagrosi-forge.git
cd zagrosi-forge
python3 scripts/zagrosi_skills.py install --pretty
```

Restart Codex after success. Preview with `install --dry-run --pretty`; compare
the installed cache with `update-check --pretty`; refresh it with
`self-update --pretty`.

Codex marketplace install is also supported:

```bash
codex plugin marketplace add zagrosi-code/zagrosi-forge
codex plugin add zagrosi-forge@zagrosi
```

## Use

Invoke the three skills in order, or start at the phase you need:

```text
Use $zagrosi-forge:zagrosi-project on @planning/requirements.md
Use $zagrosi-forge:zagrosi-plan on @planning/01-auth/spec.md
Use $zagrosi-forge:zagrosi-implement on @planning/01-auth/sections/
```

<img src="assets/readme-workflow.svg" alt="Zagrosi Forge artifact workflow" width="100%" />

Output stays small at every depth:

| Workflow | Required output |
|----------|-----------------|
| Project | `project-manifest.md` and child `spec.md` files |
| Single-section plan | `sections/index.md` and one canonical section containing tests, evidence, decisions, risks, and review |
| Multi-section plan | One shared plan and ordered sections that link shared contracts |
| Implement | Tests, code, and compact machine-readable section records |

Each phase runs one setup command, performs the work, then runs one strict
postflight. Example:

```bash
python3 scripts/zagrosi_skills.py plan-setup \
  --file planning/01-auth/spec.md --plugin-root . --depth lean
# Write and review the plan and sections.
python3 scripts/zagrosi_skills.py postflight \
  --phase plan --planning-dir planning/01-auth --depth lean --strict
```

Project uses `project-setup`; implementation uses `implement-setup`. Run
`commands --pretty` for the compact command catalog and
`status --path PATH --pretty` to resume.

Use the explicit [compact-plan format](skills/zagrosi-plan/references/plan-format.md).
Legacy physical plans and reviews remain supported. Detached frozen runs retain
their established physical plan/review contract and separate operational records.

## Context and Performance

Section context preserves the section, selects relevant requirements, and links
omitted sources. `context-brief` and `implementation-packet` use a 2,000-word budget
(`--max-words` adjusts it). Oversized sections fail explicitly. Skills load only
applicable guidance, domain packs, and detached protocol details.

The shared [engineering standard](skills/zagrosi-implement/references/engineering.md)
draws on [Ponytail](https://github.com/DietrichGebert/ponytail): trace callers,
reuse existing code and standard libraries, and prefer meaningful names and
direct flow. Repair encountered duplication, oversized modules, and mixed
responsibilities within the task; update ownership before broader edits.
Characterize weakly covered behavior before refactoring, run targeted regression
checks around changes, and run the full suite once at integration.

On macOS/Linux, known read-only gates avoid repeated process startup; other gates
retain process isolation and timeouts. Compare stable local checkouts:

```bash
python3 tools/benchmark_forge.py \
  --original-root /path/to/main --baseline-root /path/to/earlier-snapshot --runs 5
```

The benchmark checks identical disposable fixtures at every depth, recording
source hashes, median latency, context size, and modeled reference loads.
Archived protocol text is excluded. Model usage requires separate telemetry.

The [recorded comparison](examples/evals/performance.json) found planning
postflight 4.43–4.45× faster across all depths and section context reduced from
381 to 317 words. Added engineering guidance increases some routine reference
loads; detached reading falls from 3,547 to 1,177 words. Results are local to the
recorded environment and fixture.

[Coding trials](examples/evals/coding/README.md) cover features, cleanup, deep
planning, and resume. Separate verdicts check behavior, workflow completion, and
independently reviewed cleanup. Unchanged fixtures cannot pass cleanup. Reviews
and provenance bind the candidate, baseline, plugin runtime, and evaluator.

## Runtime

The CLI imports modules on demand. SHA-256 manifests bind runtime and test
sources. Verification checks every source and compiles those exact bytes without
bytecode caches. Detached admission and completion reverify sources, ownership,
locks, and immutable inputs while preserving process isolation.
Read-only checks reuse unchanged text, ownership parsing, and preceding score
components within one command. Changed inputs force fresh analysis.

## Compatibility

`fast` remains a compatibility alias for `lean`. Existing `zagrosi-*`,
`deep-*`, `DEEP_META`, and migrated `claude-*` workflows remain accepted. New
work should use the names above. Migrate recognized old artifacts with:

```bash
python3 scripts/zagrosi_skills.py migrate --planning-dir planning/01-auth
```

## Package Map

```text
skills/                    three Codex workflows
scripts/zagrosi_skills.py  verified entrypoint and runtime manifest
scripts/forge/             focused CLI, workflow, and security modules
scripts/deep_skills.py     compatibility wrapper
examples/                  valid, invalid, and benchmark fixtures
tests/                     focused CLI, gate, recovery, and coding-trial tests
tools/                     runtime binding, performance comparison, coding trials
assets/                    icon and README visuals
```

## Validate

After editing runtime or test sources, run `python3 tools/update_runtime_manifest.py`;
CI verifies the binding with `--check`. The full suite runs on Linux/Python 3.12;
focused compatibility checks cover Python 3.11, macOS, and Windows. Tests import
only the runtime modules they exercise, with fresh instances for patch isolation.

```bash
python3 tools/update_runtime_manifest.py --check
uv run --with pytest python -m pytest
python3 scripts/zagrosi_skills.py doctor --plugin-root . --strict --pretty
python3 scripts/zagrosi_skills.py release-check --plugin-root . --pretty
plugin-scanner verify .
```

Zagrosi Forge is MIT licensed and includes attribution in [NOTICE.md](NOTICE.md).
