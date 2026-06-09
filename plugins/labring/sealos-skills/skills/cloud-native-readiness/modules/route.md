# Module: Decision Routing

## Purpose

Based on the assessment score and artifact detection results, determine the next action.

## Decision Matrix

```
┌─────────────────┬──────────────────┬─────────────────────────────────────┐
│ Readiness Score │ Artifacts Status │ Action                              │
├─────────────────┼──────────────────┼─────────────────────────────────────┤
│ ≥ 7 (Good+)    │ Complete         │ REPORT: Return existing setup info  │
│ ≥ 7 (Good+)    │ Partial          │ REPORT: Show gaps + improvements    │
│ ≥ 7 (Good+)    │ None             │ HANDOFF: Invoke dockerfile-skill    │
│ 4-6 (Fair)     │ Complete         │ REPORT: Show artifacts + concerns   │
│ 4-6 (Fair)     │ Partial/None     │ ASK: Confirm with user, then optionally handoff │
│ 0-3 (Poor)     │ Any              │ STOP: Report blockers, do NOT containerize │
└─────────────────┴──────────────────┴─────────────────────────────────────┘
```

## Execution Steps

### Step 1: Evaluate Decision

Read the assessment result and artifact inventory from previous modules.

```yaml
input:
  assessment_score: {0-12}
  assessment_rating: "{Excellent | Good | Fair | Poor}"
  artifacts_status: "{complete | partial | none}"
```

### Step 2: Route — REPORT (Artifacts Exist)

When artifacts are found and readiness is Good+:

1. **Summarize existing setup**:
   - List all found Dockerfiles and their quality
   - List docker-compose configuration
   - List K8s manifests if any
   - Note any CI/CD integration

2. **Assess completeness**:
   - Can the user `docker-compose up` right now?
   - Are all dependent services covered?
   - Is the Dockerfile production-quality?

3. **Suggest improvements** (if partial):
   - Missing health checks
   - Missing .dockerignore
   - Using :latest instead of fixed versions
   - Missing multi-stage build
   - No non-root user
   - Missing restart policy in compose

4. **Output the readiness report** (format from SKILL.md)

### Step 3: Route — HANDOFF (Need to Generate)

When score ≥ 7 and no artifacts exist:

1. **Output the readiness report** first

2. **Inform the user**:
   ```
   This project is ready for containerization but has no Docker configuration yet.
   Invoking dockerfile-skill to generate production-ready Docker setup...
   ```

3. **Invoke dockerfile-skill** with context:
   - Pass the detected language, framework, package manager
   - Pass external service dependencies
   - Pass any specific concerns from the assessment
   - Use: `/dockerfile` on the current project path

4. **The dockerfile-skill will handle**:
   - Deep project analysis (its own Phase 1)
   - Dockerfile generation (Phase 2)
   - Build validation (Phase 3)
   - Runtime validation (Phase 4)

### Step 4: Route — ASK (Fair Score)

When score is 4-6:

1. **Output the readiness report** with concerns highlighted

2. **Present options to user**:
   - Option A: Proceed with containerization anyway (with caveats)
   - Option B: Address the concerns first, then re-run assessment
   - Option C: Containerize with documented limitations

3. **If user chooses to proceed**:
   - Add assessment concerns as comments in generated Dockerfile
   - Include warnings in DOCKER.md
   - Invoke `dockerfile-skill`

4. **If user chooses to address concerns**:
   - Provide specific, actionable remediation steps:
     - Which files to modify
     - What patterns to add (e.g., SIGTERM handler, health endpoint)
     - What dependencies to externalize

### Step 5: Route — STOP (Poor Score)

When score is 0-3:

1. **Output the readiness report** with blockers

2. **Provide remediation roadmap**:
   ```markdown
   ## Remediation Steps (Priority Order)

   ### 1. [Highest impact blocker]
   - What: {describe the issue}
   - Why: {why it blocks containerization}
   - How: {specific code changes needed}
   - Effort: {low | medium | high}

   ### 2. [Next blocker]
   ...
   ```

3. **Do NOT invoke dockerfile-skill**
   - Generating a Dockerfile for a project that isn't ready leads to:
     - Broken containers
     - Silent runtime failures
     - False sense of deployment readiness

4. **Offer to re-assess** after the user makes changes

## Final Output

Regardless of route taken, always end with a clear summary:

```markdown
## Next Steps

{One of:}
- ✅ Your project is already containerized. See the artifacts listed above.
- 🔧 Minor improvements suggested for your existing Docker setup (see above).
- 🐳 Generating Docker configuration now via dockerfile-skill...
- ⚠️ Some concerns noted. Would you like to proceed anyway or address them first?
- 🚫 Not recommended for containerization yet. See remediation steps above.
```
