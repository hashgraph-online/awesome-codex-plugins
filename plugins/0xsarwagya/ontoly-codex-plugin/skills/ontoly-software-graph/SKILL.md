---
name: ontoly-software-graph
description: Use Ontoly Software Graph evidence, CLI reports, MCP, and official Ontoly Agent Skills before searching source files when reviewing architecture, dependencies, request flows, configuration, impact, or security-sensitive ownership in JavaScript, TypeScript, Python, or Go repositories.
---

# Ontoly Software Graph

Use this skill when the user asks Codex to understand a JavaScript, TypeScript, Python, or Go repository's architecture, dependency graph, request flow, service ownership, configuration usage, impact radius, package topology, or security-sensitive code paths.

Ontoly is a deterministic Software Graph compiler. It does not answer questions with AI. It builds graph evidence that Codex can query before falling back to source search.

## Workflow

1. Check whether a graph exists: `ontoly-output/SoftwareGraph.json` (written by `ontoly build`) or `.ontoly/SoftwareGraph.json` (written by `ontoly analyze`). Queries read whichever is newer.
2. If the graph is missing or stale, ask before installing dependencies or writing generated graph files. Then run:

   ```bash
   pnpm add -D @0xsarwagya/ontoly-cli
   pnpm ontoly build .
   ```

3. Inspect graph quality before answering:

   ```bash
   pnpm ontoly coverage .
   pnpm ontoly stats .
   ```

4. Prefer Ontoly graph queries before repository-wide source search:

   ```bash
   pnpm ontoly evidence "<question>"
   pnpm ontoly search <concept>
   pnpm ontoly architecture --json
   pnpm ontoly impact <node-id-or-query>
   pnpm ontoly trace <node-id-or-name>
   pnpm ontoly report routes --format markdown
   ```

5. Start Ontoly MCP when the environment supports MCP-backed tools:

   ```bash
   pnpm ontoly mcp
   ```

6. Use source files only when the graph is missing, stale, low confidence, or insufficient for the question.

## Common Questions

- "Explain this repository."
- "Which service owns authentication?"
- "Trace the login flow."
- "What breaks if I remove this repository/service/function?"
- "Which packages depend on this module?"
- "Where is this environment variable read?"
- "Which routes are protected by auth?"

## Evidence Rules

When answering, cite graph evidence:

- graph hash
- node ids
- relationship types
- source spans when available
- diagnostics or confidence warnings
- fallback reason if source files were inspected

Never claim certainty beyond Ontoly evidence. If graph coverage is incomplete, say exactly which part is inferred or unresolved.

## Official Ontoly Skills

Ontoly publishes 14 task-specific Agent Skills in its own repository: architecture-review, codebase-onboarding, configuration-analysis, dead-code-analysis, dependency-analysis, documentation, framework-analysis, impact-analysis, migration-analysis, performance-analysis, refactoring, request-tracing, sdk-generation, and security-review. To inspect or install them with the open `skills` CLI:

```bash
npx skills add 0xsarwagya/ontoly --list
npx skills add 0xsarwagya/ontoly --skill impact-analysis
```

Use those official skills when the task maps directly to one of their workflows.
