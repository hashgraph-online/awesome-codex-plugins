---
name: reflexion
description: "Use for self-correcting implementation. Implements the reflexion loop: implement, validate, self-critique, retry (max 3 iterations)."
metadata:
  instruction_budget: "52"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Reflexion Skill

Self-correcting implementation loop from the n-trax pattern.

## Workflow

### Iteration Loop (max 3)

**Step 1: Implement**
- Create the deliverable according to the specification/acceptance criteria.
  - Software: write code. Content: write/produce content. AI tool: write prompts/configs. Service: document workflow.
- Follow ${CLAUDE_PLUGIN_ROOT}/harness/engineering-principles.md (principles apply to all product types).
- Apply patterns from patterns.md.
- Check corrections.md for relevant past mistakes.

**Step 2: Validate**
- Software: Run tests, linter, type checker, security scan, accessibility checks (if UI).
  - **Security validation (OWASP)**: Check input validation, output encoding, parameterized queries, no hardcoded secrets, authentication/authorization patterns, dependency vulnerabilities. Reference OWASP Top 10:2025 categories for each check.
- Content: Review against learning objectives/editorial standards, check accessibility (captions, alt text), fact-check claims.
- AI tool: Run eval test cases, red-team testing, bias assessment.
- Service: Walk through the service blueprint end-to-end, verify documentation completeness.
- All: Verify acceptance criteria.

**Step 3: Self-Critique**
Review the implementation against (select items relevant to product_type):
- [ ] Engineering principles: DRY, KISS, YAGNI, SoC (apply to all product types)
- [ ] Security: Input validation, output encoding, no secrets, parameterized queries (software, ai_tool)
- [ ] Accessibility: Semantic HTML, keyboard nav, contrast, screen reader (software); captions, transcripts, alt text (content)
- [ ] Edge cases: What happens with unexpected input? Empty? Adversarial? (software, ai_tool)
- [ ] Error handling / user recovery: Are errors handled gracefully? Can users recover? (software, service)
- [ ] Quality: Factual accuracy, style consistency, source attribution (content); eval scores, safety scores (ai_tool)
- [ ] Naming / clarity: Do names reveal intent? Would a new reader understand this? (all)
- [ ] Completeness: Is anything missing that the user would expect? (all)

**Step 4: Decide**
- If all validations pass AND self-critique finds no issues: **DONE**
- If issues found AND iteration < 3: **FIX and return to Step 1**
- If iteration = 3 AND issues remain: **ESCALATE** with documented issues

### Escalation Protocol
When max iterations reached without full resolution:
1. Document what was attempted in each iteration.
2. Document remaining issues with severity assessment.
3. Recommend: fix now (blocking) vs. fix later (non-blocking) vs. accept risk.
4. Update corrections.md with learnings.

## Verification Modes

The validate step in the reflexion loop should use the appropriate verification mode:

### Rules-Based (deterministic)
- Linters, formatters, schema validators, type checkers
- Pass/fail is unambiguous — no judgment needed
- Always run first — fastest and cheapest
- Examples: `eslint`, `mypy`, `yamllint`, YAML schema validation against ${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml

### Computational (deterministic)
- Test runners, build systems, security scanners
- Requires executing code — slower than rules-based
- Results are objective but may need interpretation (flaky tests)
- Examples: `pytest`, `npm test`, `cargo clippy`, OWASP dependency check

### Inferential (probabilistic)
- LLM-as-judge, peer review, heuristic evaluation
- Used when rules-based and computational verification are insufficient
- Results require confidence scoring — never treat as definitive
- Examples: `/mycelium:devils-advocate`, `/mycelium:usability-check`, auto-dogfood evaluation, design review
- The auto-dogfood system is an inferential verification loop

**Order**: Always attempt rules-based → computational → inferential. Only escalate to the next mode when the previous mode cannot verify the property in question.

*Source: Trivedy (Anatomy of an Agent Harness, LangChain blog). Three-mode taxonomy adapted from Böckeler (Harness Engineering, martinfowler.com — computational vs inferential distinction). Note: harnesses continue to matter even as models improve — they engineer systems around model intelligence, not just patch deficiencies.*

## Rules
- Each iteration must show measurable improvement over the previous.
- If the same issue recurs across iterations, investigate root cause rather than patching symptoms.
- Never skip the self-critique step, even if tests pass.
- Log the reflexion loop outcome in delivery-journal.md.
- **NUDGE-AT-FAILURE** (4-layer JIT composition): if the failure being reflexed on is a class a standard tool (linter, SAST, secrets scanner, dep audit) would have caught automatically, append a single-line nudge to the reflexion output: *"This class of failure is what `{tool}` catches automatically — want help wiring it up now?"* Never auto-install. Per `feedback-jit-nudge-not-push` (founder principle, 2026-05-26).

## Theory Citations
- Reflexion pattern (Shinn et al.)
- Clean Code (Martin)
- OWASP secure coding
- WCAG 2.1 AA
