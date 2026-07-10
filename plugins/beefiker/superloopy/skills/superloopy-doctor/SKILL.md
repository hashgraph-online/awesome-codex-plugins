---
name: superloopy-doctor
description: Use when diagnosing Superloopy doctor, install, wrapper, plugin cache, hook bootstrap, bundled agents, marketplace, Codex, Claude Code, stale-version, evidence-floor, or host-wiring health problems.
metadata:
  short-description: Diagnose Superloopy install and bootstrap health
---

# superloopy-doctor

SUPERLOOPY DOCTOR ENABLED

Use this skill to prove whether a local Superloopy surface can support the Superloopy loop: repo-local `.superloopy/` state, artifact-backed evidence under `.superloopy/evidence/`, bundled crew agents, hook steering, and the deterministic completion floor. It is read-only by default. Do not mutate plugin config, wrappers, agents, caches, or source files unless the user explicitly asks for repair after seeing the report.

## Native Boundary

This is a Superloopy health check, not a generic plugin drift audit.

- Treat `superloopy doctor --json` as the primary truth surface.
- Treat loop commands as the behavioral truth surface, but keep their limits clear: `superloopy loop status --json`, `superloopy loop check`, `superloopy loop guide --json`, and evidence files under `.superloopy/evidence/` can show current plan and artifact readiness.
- Read the installed plugin cache only to identify which Superloopy code the wrapper runs.
- Do not clone external repos, search issue trackers, or compare unrelated harness layouts unless the user separately asks for research.
- `superloopy doctor` reports the plugin root it checked: by default it uses the current directory when that is a Superloopy checkout, otherwise it checks the installed CLI root. Use `superloopy doctor --root <checkout-or-cache> --json` when you need to pin the target explicitly.

## Diagnostic Spine

1. Identify the target root: `pwd`, `git rev-parse --show-toplevel` when it is a checkout, and the installed plugin cache path when the wrapper points into one.
2. Locate the user-visible command: `command -v superloopy`, `which -a superloopy`, and the wrapper text or symlink target.
3. Inspect Codex registry state with `codex plugin list --json` when Codex is available; use it only to locate `superloopy@beefiker` and its version.
4. Run `superloopy doctor --json` and record the reported `root`. If the wrapper is missing or stale, run `node src/cli.js doctor --root <checkout-or-cache> --json` from the checkout or installed cache being evaluated.
5. Read the named doctor checks, especially `skills`, `fileAudit`, `reviewability`, `dispatchCoherence`, `hostContract`, `modelPolicy`, and `claudeHostWiring`.
6. Probe loop readiness without changing state: use `superloopy loop status --json` if a plan exists, otherwise note "no active plan" instead of creating one. Use `superloopy loop check` only to validate trace/artifact readiness for an existing plan; read-only diagnosis cannot prove completion safety because it does not re-run recorded commands. If the user asks whether completion is actually safe, point at the real gates: `superloopy loop review`, `superloopy loop checkpoint`, or `superloopy loop finish`.
7. Verify crew install shape by name: `franky`, `zoro`, `usopp`, `jinbe`, `robin`, and `nami`; judge by files and doctor checks, not by role labels alone.
8. If managed state is absent, distinguish no fleet from an exact hash-known legacy fleet and an unmanaged/edited conflict. Exact legacy fleets can migrate without `--force`; never infer ownership from names alone.
9. Compare the generated wrapper target with the diagnosed plugin root and report a split-brain warning when they differ.
10. Report configured model routing as `model_unverified` unless the host attests both the resolved role and model.
11. Report PASS, WARN, or FAIL with command output, file path, or JSON check evidence.

## Verdict Rules

- `PASS`: wrapper/cache/checkout, `superloopy doctor --json`, and relevant loop/evidence surfaces agree within read-only limits.
- `WARN`: Superloopy can run, but a wrapper points at an older cache, no active plan exists for loop readiness, read-only mode cannot prove completion safety, host behavior is advisory only, or manual evidence cannot be command-replayed.
- `FAIL`: doctor named checks fail, wrapper is absent or points at the wrong root, required agents are missing, `.superloopy/` state is corrupt, or the deterministic completion floor cannot be evaluated.

## Repair Guidance

Recommend repair commands only after the read-only report explains the failure:

- Marketplace refresh: `codex plugin marketplace upgrade beefiker`.
- Repair reinstall: `codex plugin add superloopy@beefiker`.
- Checkout install: `node src/cli.js install --json`.
- Forced local wrapper/agent overwrite: `node src/cli.js install --force --json`.

Never run `install --force`, plugin remove, marketplace remove, cache deletion, or wrapper deletion without explicit user approval.

## Report Format

```text
Superloopy doctor report
Summary: <healthy/degraded/broken in one sentence>

| Check | Verdict | Evidence |
| --- | --- | --- |
| Command wrapper | PASS/WARN/FAIL | <path, target, cache or checkout root> |
| Doctor checks | PASS/WARN/FAIL | <ok=true or failing check names> |
| Evidence floor | PASS/WARN/FAIL | <.superloopy/evidence/, loop check/status readiness, or "completion safety requires the real gate"> |
| Crew install | PASS/WARN/FAIL | <agent files and dispatchCoherence evidence> |
| Host limits | PASS/WARN/FAIL | <hostContract/claudeHostWiring evidence> |
| Reviewability/native boundary | PASS/WARN/FAIL | <reviewability/fileAudit/designAudit evidence> |

Recommended repair:
- <exact command or "none">
```

## Hard Rules

- Read-only by default.
- Diagnose Superloopy's own contract: package, hooks, skills, CLI, dependency-free boundary, runtime ignore policy, file inventory, design audit, dispatch coherence, model policy, host contract, reviewability, and deterministic completion floor.
- Treat stale wrappers and stale installed plugin caches as separate findings; a marketplace refresh alone is not proof.
- Do not claim a marketplace upgrade fixed anything until the wrapper and `superloopy doctor --json` prove it.
- Do not mark a loop completion-safe from status or `superloopy loop check` alone; those are read-only readiness signals. Completion safety requires the real gate path (`superloopy loop review`, `superloopy loop checkpoint`, or `superloopy loop finish`) because those gates re-derive command-backed criteria.
- If terminal capability noise affects host commands, rerun with a normal terminal environment before recording a failure.
