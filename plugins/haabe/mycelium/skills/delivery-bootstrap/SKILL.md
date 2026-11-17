---
name: delivery-bootstrap
description: "Use when starting implementation on a new or unfamiliar codebase. Auto-detects tech stack and sets up development context."
metadata:
  instruction_budget: "54"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Delivery Bootstrap Skill

Just-in-Time tech stack detection and setup.

## Workflow

1. **Check product_type** from `.claude/diamonds/active.yml`:
   - If `product_type` is set (from `/mycelium:interview`), use it to determine the delivery profile.
   - If not set, scan for indicators per `${CLAUDE_PLUGIN_ROOT}/jit-tooling/detector.md` Step 1b:
     - Curriculum/lesson plans, LMS config -> `content_course`
     - Manuscript/chapters, editorial calendar -> `content_publication`
     - Video scripts, subtitle files, podcast RSS -> `content_media`
     - Prompt templates, model configs, agent definitions -> `ai_tool`
     - Service blueprints, pricing docs -> `service_offering`
   - If non-software product_type detected: skip software tooling detection (Steps 2-3 below), configure product-type-appropriate validation instead, and proceed to Step 4.

1b. **Scan project root** for technology indicators (software and ai_tool with code):
   - Package files: package.json, Cargo.toml, go.mod, requirements.txt, pyproject.toml, Gemfile, pom.xml, build.gradle
   - Config files: tsconfig.json, .eslintrc, .prettierrc, rustfmt.toml, .editorconfig
   - CI/CD: .github/workflows, .gitlab-ci.yml, Jenkinsfile, Dockerfile
   - Framework indicators: next.config.js, nuxt.config.ts, angular.json, etc.

2. **Identify stack components** (software/ai_tool with code):
   - Language(s) and version(s)
   - Framework(s)
   - Package manager
   - Test runner and framework
   - Linter and formatter
   - Build tool
   - CI/CD platform
   - Database (if detectable)
   - Deployment target

3. **Verify tooling works**:
   - Run build command
   - Run test command
   - Run lint command
   - Note any failures or warnings

3a. **Offer the feedback-loop tooling menu** (OFFER-MENU layer):
   - For the detected stack, present the best-practice menu from `${CLAUDE_PLUGIN_ROOT}/jit-tooling/security-scanning.md` (SAST, dep audit, secrets, test runner, linter), **ordered smallest-friction first** (typically: secrets scan → linter → SAST → dep audit → container scan).
   - Frame as: *"Best practice is to have tools help you shorten the feedback loop. For your detected stack ({lang}), the menu is: {list}. Want help finding and configuring any of these?"*
   - **Never auto-install. Never pick rulesets on the user's behalf.** Adoption is per-tool, per-consent. The user owns the choice. See `feedback-jit-nudge-not-push` (founder principle, 2026-05-26).
   - If user declines or defers, record the offer in `active-stack.yml` under `tooling_offers_declined` with timestamp — later shape-triggers (Step 3b) can re-surface the relevant subset.

3b. **Risk-shape re-offer** (RISK-TRIGGERED layer):
   - Scan code for risk-shape patterns. If any fires AND the corresponding tool was declined in 3a, re-offer the relevant subset with the risk as citation. Patterns:
     - **AUTH shape**: `/login`, `/auth`, `/register`, `password`, `session`, `token`, `jwt`, `oauth`, `x-user-id` and similar trust-bearing headers → re-offer SAST + suggest `/mycelium:threat-model` and `/mycelium:security-review`. **SAST blind spot**: identity-trust design (e.g., `x-user-id` header trusted as auth) is NOT catchable by SAST tools — they don't model intent. Route to `/mycelium:security-review` regardless of whether SAST consent was given.
     - **AI shape**: imports from `ai_components` categories per detector.md Step 1c → suggest `/mycelium:xai-check`
     - **PII / data shape**: `email`, `ssn`, `phone`, `address`, `payment`, `card`, schema fields matching PII patterns → suggest `/mycelium:privacy-check` + secrets scanner
     - **Public endpoint shape**: routes without auth middleware → suggest SAST + DAST. **SAST blind spot**: "no authorization check" is design-level; SAST can flag suspicious patterns but cannot confirm absence-of-intent. Route to `/mycelium:security-review`.
     - **File-upload shape**: `upload`, `multipart`, `FormFile`, `ServeFile`, `ServeContent`, `Content-Disposition`, file-system write from request → re-offer SAST + suggest `/mycelium:threat-model` with explicit MIME-allowlist + filename-sanitization + size-cap + overwrite-policy review. **SAST partial coverage**: gosec/semgrep catch path-traversal (`filepath.Join` without `Base`), but cannot catch design flaws (MIME confusion via stored files, public-list disclosure, missing auth).
   - Cite the trigger explicitly per the operating contract's attribution rule (Communication Rule 4): `(per: AUTH shape detected at app.py:42 → SAST recommended)`.
   - The 4-layer composition (OFFER-MENU + RISK-TRIGGERED + NUDGE-AT-FAILURE + PR-TIME) is derived from a deep-study comparison of 10 adoption approaches (2026-05-26). Strongest single-finding: contextual nudges at decision moments produce ~8× higher detection vs no-nudge baseline (Less is More, arxiv 2202.04586; *consistency_only* — single experimental study). Other layers live in `/mycelium:security-review`, `/mycelium:threat-model`, `/mycelium:reflexion` (NUDGE-AT-FAILURE) and `/mycelium:definition-of-done` (PR-TIME).

4. **Document existing patterns**:
   - Code organization (monorepo, src layout, etc.)
   - Naming conventions
   - Test patterns
   - Error handling patterns
   - API patterns

5. **Scaffold Architecture Decision Records** (if applicable):
   - Check: Does the project have significant architecture decisions ahead? Indicators:
     - Multiple competing implementation approaches (e.g., REST vs GraphQL, monolith vs microservices)
     - New infrastructure choices (database, hosting, auth provider)
     - Framework selection or migration
     - Integration with external systems
   - If yes: create `docs/adr/` directory and a template file `docs/adr/0000-template.md`:
     ```
     # [NUMBER]. [TITLE]

     Date: [DATE]

     ## Status
     Proposed | Accepted | Deprecated | Superseded by [ADR-XXXX]

     ## Context
     What is the issue that we're seeing that is motivating this decision?

     ## Decision
     What is the change that we're proposing and/or doing?

     ## Consequences
     What becomes easier or more difficult to do because of this change?
     ```
   - If no significant architecture decisions are foreseeable: skip. Don't scaffold ceremony for a weekend project.
   - ADR format: Nygard (Context/Decision/Consequences). Lightweight by design — each ADR should be readable in under 2 minutes.

6. **Output**:
   ```
   ## Stack Profile
   - Language: [x] v[y]
   - Framework: [x]
   - Package manager: [x]
   - Test: [command] ([framework])
   - Lint: [command]
   - Build: [command]
   - CI/CD: [platform]

   ## Commands
   - Install: [command]
   - Dev server: [command]
   - Test: [command]
   - Build: [command]
   - Lint: [command]

   ## Observed Patterns
   - [list of patterns detected]

   ## Issues Found
   - [any broken tooling or warnings]

   ## Architecture Decision Records
   - Scaffolded: yes/no
   - Location: docs/adr/
   - Pending decisions: [list if any identified during bootstrap]

   ## Risk Shapes Detected
   - [list of risk shapes fired in Step 3b, with citations]

   ## Recommended Next Skills
   - [if AUTH / public-endpoint / file-upload / PII shape fired] → run `/mycelium:security-review` before merging (per: SAST blind spot — identity/authorization/business-logic flaws aren't tool-catchable)
   - [if AI shape fired] → run `/mycelium:xai-check`
   - [if PII shape fired] → run `/mycelium:privacy-check`
   ```

## Rules
- Use the project's established patterns. Don't impose external preferences.
- Be language-agnostic in principles, language-specific in implementation.
- If tooling is broken, flag it rather than silently working around it.

## Canvas Output
Create/update `.claude/jit-tooling/active-stack.yml` with detected stack configuration — **project state, in the consumer's `.claude/`**, never the shared plugin cache (which is read-only in practice and wiped on `/plugin update`).
See `${CLAUDE_PLUGIN_ROOT}/jit-tooling/active-stack.example.yml` for the expected format.

This file is the trigger for the whole XAI/AI-Act gate family: `ai_components.detected` gates Theory Gate 13 and `/mycelium:xai-check`, plus the AI arms of `/mycelium:threat-model`, `/mycelium:launch-tier`, `/mycelium:regulatory-review`, and `/mycelium:definition-of-done`. If it is not written here, every one of those silently reports N/A.

## Theory Citations
- Forsgren: Accelerate (tooling and automation)
- Smart: Sooner Safer Happier (remove friction)
- Nygard: Architecture Decision Records (lightweight decision documentation)
