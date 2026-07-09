---
name: scaffold
description: Stamp project/component/CI scaffolds — but
---
# Scaffold Skill

> **Quick Ref:** Domain-slice manifests (the repo binding) + generic project/component/CI scaffolds. `$scaffold domain <name>` for a scoped operating-loop slice; `$scaffold <language> <name>`, `$scaffold component <type> <name>`, `$scaffold ci <platform>` for the generic modes.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.** Generate real files, run real commands, verify real output.

## Modes

| Mode | Invocation | Output | Where |
|------|-----------|--------|-------|
| **Domain-Slice** | `$scaffold domain <name>` | Domain-slice manifest for a scoped operating-loop run | **this file** (repo binding) |
| **Project** | `$scaffold <language> <name>` | Full project directory with build, test, lint | [references/generic-templates.md](references/generic-templates.md) |
| **Component** | `$scaffold component <type> <name>` | New module/package added to existing project | [references/generic-templates.md](references/generic-templates.md) |
| **CI** | `$scaffold ci <platform>` | CI/CD pipeline configuration | [references/generic-templates.md](references/generic-templates.md) |

Parse the invocation: `domain` first-positional → Domain-Slice; `component` → Component; `ci` → CI; otherwise Project. If ambiguous, ask ONE clarifying question, then proceed.

## Generic scaffolding (project / component / CI)

**A frontier model needs no template for standard project trees, best-practice config, or GitHub-Actions / GitLab-CI YAML — ask it directly.** State the language, type, and name; it produces an idiomatic go/python/node/rust/react tree with real (not placeholder) files, a passing test, and CI, then verifies build/test/lint and makes the `bootstrap(<name>): …` commit. The four-step spine is **gather → generate → verify → commit** (do not push).

The canonical tree shapes, `.editorconfig`/pre-commit/CI YAML skeletons, verification-command table, per-mode component layouts, and the error-recovery + output-summary blocks the skill historically stamped are preserved verbatim in **[references/generic-templates.md](references/generic-templates.md)** — consult it only when you want those exact shapes. For installer scripts, agent-facing tool servers, MCP surfaces, or Rust CLI storage scaffolds, apply [references/agent-facing-tool-scaffolds.md](references/agent-facing-tool-scaffolds.md) before writing files.

## Domain-Slice Mode

When invoked as `$scaffold domain <name>`, scaffold a **domain-slice manifest** — the bounded-context declaration used to scope an operating-loop run.

> There is **no `scaffold` subcommand on the `ao` CLI**. Domain-slice scaffolding is this skill's responsibility; the old phased-engine flags are superseded by ADR-0009.

### Workflow

1. **Generate the manifest.** Run the write-and-exit flag — it creates the template and returns without starting an RPI run:

   Run `$scaffold domain <name>`.

   This writes `docs/domains/<name>/manifest.yaml` from a template that already validates against `schemas/domain-slice-manifest.v1.schema.json`. An existing manifest is **not** overwritten unless `--force` is passed.

2. **Fill in the placeholders.** Edit the generated manifest:
   - `bounded_context` — one sentence: what this slice owns and explicitly does NOT own.
   - `directive_ids` — stable GOALS.md directive IDs (pattern `d-<slug>`) this slice owns.
   - `scenario_ids` — promoted spec scenario IDs from `spec/scenarios/` (may stay `[]` initially).
   - `context_roots` — repo-relative implementation surface (at least one entry).
   - `allowed_read_globs` / `denied_read_globs` — the read fence (gitignore syntax; deny wins).
   - `validation_commands` — ordered build/test/lint steps.

3. **Verify it loads.** The scaffolded manifest already passes the F3.1 schema/loader. After editing, confirm it still validates:

   Dry-run the operating-loop plan against `docs/domains/<name>/manifest.yaml` before execution.

   A dry run loads the manifest, prints the scoped phase prompts, and exits — proving the slice attaches.

4. **Run scoped RPI.** Once the manifest is real:

   Run the operating loop with `docs/domains/<name>/manifest.yaml` as the explicit scope contract.

   Phase prompts carry the slice's boundaries; each run also writes a domain-scope audit artifact reporting any out-of-domain references visible in evidence.

### Next commands the scaffold names

After writing the manifest, lint executable-spec links with `ao goals scenarios --lint`, preview the scoped operating-loop plan, then execute with the manifest as the scope contract. Run them in that order.

Error-recovery and output-summary conventions (shared with the generic modes) live in [references/generic-templates.md](references/generic-templates.md).

## References

- [references/agent-facing-tool-scaffolds.md](references/agent-facing-tool-scaffolds.md)
- [references/recommended-reading.md](references/recommended-reading.md) — forward-looking index of external skills (e.g., `mcp-server-design`) worth absorbing into scaffold when their trigger conditions arrive. Consult before designing a new scaffold mode that targets agent-facing tool surfaces.
- [references/scaffold.feature](references/scaffold.feature) — Executable spec: project/component/CI scaffolding entry points + domain-slice manifest routing (soc-qk4b)
