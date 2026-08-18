---
name: clean-room-loop
description: Front door for running the clean-room unattended loop as a Claude Code dynamic WORKFLOW using in-session subagents, so it never spends `claude -p` API tokens. Use when the user wants to run a clean-room / reverse-engineering / source-to-clean-implementation task hands-off but without paying per-token for `clean-room-skill run`, or says "clean-room as a workflow", "unattended clean-room without API cost", "/clean-room-loop". Runs a short discussion (authorization, end goal, target stack, policies, source roots, output roots, iterations) then launches the `clean-room-loop` workflow with the answers. NOT the enforced OS-level wall - that is `clean-room-skill run --agent-runtime claude`.
argument-hint: [end goal, authorized source roots, target stack, output roots, optional max iterations]
---

# Clean-room loop (discussion -> clean-room-loop workflow launch)

Conversational front door to the `clean-room-loop` dynamic workflow (`.claude/workflows/clean-room-loop.js`).
The workflow runs in the background with no way to ask anything mid-run, so the discussion happens
HERE; answers pass as `args`.

**Claude Code only.** Dynamic workflows are a Claude Code feature. In Pi/Codex/OpenCode the
`Workflow()` call will not exist - see the Fallback step. Only this workflow shortcut is Claude
Code specific; the underlying clean-room skills (`/clean-room:unattended`, `clean-room-skill run`)
work on every supported runtime.

**Installed project-local.** The workflow script ships to project-local `.claude/workflows/`
(not global). `Workflow({ name })` discovers it from the current project's `.claude/workflows/`
(or `~/.claude/workflows/` if a personal copy exists). If the current project does not have it,
initialize a project-local install before launching - see Step 3.

## What this is (and is NOT)

- It drives the six clean-room roles with the workflow's OWN `agent()` subagents (in-session,
  subscription, **no `claude -p`**), gating every wall crossing with the real
  `clean-room-skill artifact validate --role` leakage + schema hooks.
- It is a **cost-free path with context-level separation**, NOT the OS-enforced wall. A workflow
  cannot set `CLEAN_ROOM_*` env or install hooks, so nothing stops a clean subagent from reading
  source off disk except the neutral-artifact discipline + the leakage gate. If the user needs the
  enforced boundary, use `clean-room-skill run --agent-runtime claude` instead (that path costs API
  tokens by design).
- The workflow READS the authorized source and WRITES clean specs, plans, code, and reports under the
  external artifact roots. Confirm authorization and paths before launching.

## Steps

1. **Get the brief.** Take the end goal from the invocation if present. If missing, ask what they are
   reimplementing and why they are authorized to.

2. **Run the discussion.** Collect the fields below with `AskUserQuestion` (batch - max 4 per call,
   ~3 calls); ask free-text ones plainly. Offer defaults so a terse brief is still runnable. Do NOT
   infer the end goal or target stack from source - clean-room forbids it; if unknown, ask.

   Batch A (goal + stack):
   - **endGoal** (free-text): what the clean implementation must do; its success definition.
   - **targetStack**: language / runtime / framework / packageManager / testFramework. Pass as a nested object.
   - **compatibilityPolicy**: public-behavior-and-API-names only (default) or public-behavior-only.
     Private structure/comments/internal names are NEVER mirrored.
   - **featurePolicy** (skippable): features to preserve / remove / add / non-goals.

   Batch B (policy):
   - **licensePolicy**: destination license + any blocked dep licenses.
   - **dependencyPolicy**: allow new deps? prefer stdlib? require approval for native deps.
   - **codeHygienePolicy** (skippable): max lines per code/test file, max files per iteration.
   - **schemaProfile**: speckit-feature-folder (default) / openspec-delta / gsd-planning-package / kiro-spec-folder.

   Batch C (roots + bounds - all safety-relevant):
   - **sourceRoots** (REQUIRED): absolute path(s) to the authorized source. No source = cannot run.
   - **artifactBase**: where run artifacts live (default `~/Documents/CleanRoom`). Must be OUTSIDE the
     source tree and neutral-named.
   - **project / taskId** (skippable): neutral names; the CLI generates neutral ones if omitted.
   - **maxIterations**: finite inner-loop cap (default 3).

3. **Ensure the workflow is installed project-local, preview, STOP for confirmation, then launch.**
   First confirm this project has the workflow. Dynamic workflows load from project-local
   `.claude/workflows/`. If `.claude/workflows/clean-room-loop.js` is absent in the current project
   (and no `~/.claude/workflows/clean-room-loop.js` personal copy exists), initialize a project-local
   install before launching:

   ```bash
   clean-room-skill --claude --local --yes
   # or, without a global CLI:
   npx clean-room-skill@latest --claude --local --yes
   ```

   That writes `clean-room-loop.js` into the current project's `.claude/workflows/` so
   `Workflow({ name })` can discover it. Then show a compact preview of the `args`
   (at least `endGoal`, `sourceRoots`, `artifactBase`, `targetStack`, `maxIterations`) so a wrong
   source path or output root is caught BEFORE a filesystem-writing, source-reading run starts. STOP
   and wait for an explicit "yes". Do NOT call `Workflow` in the same turn as the preview. Only after
   the user confirms:

   ```
   Workflow({ name: "clean-room-loop", args: {
     endGoal,
     targetStack,                 // { language, runtime, framework, packageManager, testFramework }
     compatibilityPolicy, featurePolicy,
     licensePolicy, dependencyPolicy, codeHygienePolicy,
     sourceRoots,                 // array of absolute paths (REQUIRED)
     artifactBase, project, taskId,
     schemaProfile, maxIterations,
     specSliceRef,                // optional
   }})
   ```

   Pass only what was gathered; omit the rest (the workflow defaults them).

4. **Fallback.** If `Workflow()` errors or is unavailable (non-Claude host, or dynamic workflows
   disabled), do NOT hand-run the roles here. Route the user to `/clean-room:unattended`, which
   prefers fresh-context in-harness roles on that harness and drops to the durable runner only as a
   last resort: `clean-room-skill run --agent-commands <adapter>` on Codex/Pi/other runtimes (spawns
   the harness CLI, `shell: false`), or `--agent-runtime claude` (spawns `claude -p`, Claude only,
   per-token) last. Use the runner only once a runner-ready manifest with `loop_context` exists.

5. **Hand back** the workflow's result (the terminal `clean-room-result.json` result string, task
   root, and clean/implementation roots).
