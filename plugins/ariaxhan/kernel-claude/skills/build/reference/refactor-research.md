# Refactor & Code Cleanup Reference: Research & Best Practices

Reference document for refactoring, optimization, and cleaning up AI-generated
code. Read when deeper context is needed. Not auto-loaded; read on demand.

## Sources

Compiled from: CodeRabbit's State of AI vs Human Code Generation Report (2025),
GitClear's analysis of 153M+ lines of code, Qodo's State of AI Code Quality
(2025), University of Naples large-scale study (arxiv 2508.21634), Veracode
AI security research, CodeScene's agentic AI best practice patterns, Cortex
Engineering Benchmark Report (2026), Martin Fowler ("Refactoring"), IBM's AI
code refactoring analysis, The Register/Futurism industry reporting, Borg &
Tornhill peer-reviewed study (Jan 2026, arXiv 2601.02200), Martin Fowler Feb
2026 fragments, SonarSource 2026 State of Code Survey, and "Vibe Coding"
Technical Debt Crisis analysis.

---

## The State of AI-Generated Code (2025-2026)

The data is now unambiguous. AI increases output AND increases defects.

CodeRabbit (470 GitHub PRs analyzed): AI-generated pull requests contain
1.7x more issues than human-written ones. 1.4x more critical issues. 1.75x
more logic and correctness errors. Every quality dimension is worse.

Cortex Engineering Benchmark (2026): PRs per author up 20% YoY. Incidents
per PR up 23.5%. Change failure rates up 30%. More code, more problems.

GitClear (211M lines, 2026): AI-assisted coding linked to 4x more code
cloning. Code churn up 41% in AI-heavy teams. Code duplication up 48% as
models fail to modularize. 60% decline in refactored code - developers favor
velocity over health. For the first time, developers paste code more often
than they reuse or refactor it. Copy-paste has overtaken abstraction.

Veracode: 45% of AI-generated code contains known security flaws.

Qodo: 65% of developers cite missing context as the top issue. Only 3.8%
report both low hallucination rates AND high confidence shipping AI code
without human review. 66% spend more time fixing "almost-right" AI code.

University of Naples (500K+ code samples, arxiv 2508.21634): AI code is
"simpler and more repetitive, yet more prone to unused constructs and
hardcoded debugging." Human code has "greater structural complexity and
higher concentration of maintainability issues." Both have problems;
different problems.

The implication: every AI-generated codebase needs systematic cleanup.
Not as a one-time event, but as continuous practice.

---

## AI-Friendliness Quantified (Jan 2026 - Peer-Reviewed)

Borg & Tornhill (arXiv 2601.02200): Tested 5,000 Python files across 6 LLMs.

Key findings:
- **30% minimum defect risk increase** when AI applied to unhealthy code.
- CodeHealth is the **strongest predictor** of AI refactoring success.
- One standard deviation increase in CodeHealth improves odds by **20-40%**.
- GPT break rates: 35.87% (healthy) vs 47.02% (unhealthy code).

Threshold for AI-ready code: **CodeHealth >= 9.5** (ideally 10.0).

loveholidays case study: Scaled from 0 to 50% agent-assisted code in 5 months
while maintaining quality by implementing CodeScene safeguards. Quote: "AI has
an amplifying effect. If your engineering practices are strong, AI helps you
move faster. If they're weak, it will destroy you."

---

## The Verification Bottleneck (SonarSource 2026)

SonarSource survey of 1,100+ developers:
- **96% don't fully trust** AI-generated code
- **72% use AI for refactoring**, but only 43% find it highly effective
- The #1 skill for the AI era: "Reviewing and validating AI-generated code" (47%)

This creates "engineering productivity paradox" - more code, more review burden.

---

## The "Vibe Coding" Technical Debt Crisis

New concept not previously documented:
- **$1.5 trillion projected cost** by 2027 from AI-generated technical debt
- **"Spaghetti Point"** occurs around month 3 of vibe-coded projects
- **"6-Month Wall"** - when accumulated debt makes app unmaintainable
- Forrester: 75% of tech decision-makers face moderate-severe debt by 2026
- **"Rescue engineering"** predicted as hottest discipline in 2026

---

## The 12 Most Common AI Code Defects

Ranked by frequency from aggregated research (CodeRabbit, Qodo, University
of Naples, Veracode, CodeScene):

### 1. Code Duplication / Cloning
AI generates similar solutions in multiple places rather than reusing
existing functions. GitClear: 4x increase in code cloning with AI tools.
Fix: grep for duplicate logic, extract shared functions. But apply Rule
of Three; don't abstract prematurely.

### 2. Missing Error Handling
AI generates happy-path code. Error paths are omitted or generic.
Catch blocks that do nothing. Missing try/catch entirely.
Fix: for every function, ask "what happens when this fails?" Add specific
error handling with actionable messages.

### 3. Unused Constructs / Dead Code
Variables declared but never used. Imports that nothing references.
Functions defined but never called. AI "prepares" for things that
never happen.
Fix: run linter with unused-variable rules. Delete anything unreferenced.

### 4. Hardcoded Values
Debug strings left in production code. API URLs hardcoded instead of
config. Magic numbers without constants. Credentials in source.
Fix: grep for localhost, hardcoded ports, API keys, console.log/print
statements. Move to environment variables or constants.

### 5. Logic and Correctness Errors
75% more frequent in AI code (CodeRabbit). Off-by-one errors, wrong
comparison operators, incorrect boolean logic, missed edge cases.
Fix: write tests for boundary conditions. Review every conditional.

### 6. Excessive Verbosity
AI generates more code than needed. Redundant null checks, unnecessary
type assertions, over-commented obvious code, wrapper functions that
add no value.
Fix: for each function, ask "can this be shorter?" Remove anything
that doesn't change behavior.

### 7. Poor Naming
AI picks generic names: data, result, temp, handler, process, item.
Or overly verbose names that duplicate the type information.
Fix: rename to describe WHAT, not HOW. "userEmail" not "data".
"fetchActiveOrders" not "processItems".

### 8. Missing Input Validation
AI trusts its inputs. No validation at API boundaries. No sanitization
of user input. No type checking at runtime for dynamic languages.
Fix: validate at every system boundary (API endpoints, function
signatures that accept external data, form handlers).

### 9. Security Vulnerabilities
Veracode: 45% of AI code has known security flaws. Common: SQL injection
via string concatenation, XSS through unescaped output, insecure
deserialization, missing auth checks, exposed internal endpoints.
Fix: run security scanner (Snyk, npm audit, safety). Parameterize all
queries. Escape all output. Auth-gate all endpoints.

### 10. Inconsistent Patterns
AI doesn't maintain consistency across a codebase. Different error
handling in different files. Mixed async patterns (callbacks + promises
+ async/await). Inconsistent naming conventions.
Fix: establish patterns in CLAUDE.md or conventions doc. Lint for
consistency. Review for pattern adherence, not just correctness.

### 11. Missing Tests
AI generates implementation without tests. When it does generate tests,
they often test the happy path only, use mocks that don't reflect real
behavior, or assert implementation details rather than outcomes.
Fix: require tests for every feature. Test behavior, not implementation.
Include edge cases and error paths.

### 12. Dependency Bloat
AI adds packages for trivial functionality. A full lodash import for
one function. A date library for simple formatting. Multiple packages
that do the same thing.
Fix: audit package.json / requirements.txt. For each dependency: is it
used? Could the functionality be 10 lines of native code instead?

---

## The Refactoring Checklist for AI Code

Run this checklist after ANY AI-generated code session. Order matters;
earlier items catch problems that compound into later ones.

### Pass 1: Dead Code Removal (fastest, highest signal)
- Remove unused imports
- Remove unused variables and functions
- Remove commented-out code (git has history; comments are not archives)
- Remove console.log / print / debug statements
- Remove TODO comments without ticket references

### Pass 2: Hardcoded Values
- Extract magic numbers to named constants
- Move API URLs, ports, credentials to environment variables
- Replace hardcoded paths with config-driven values
- Remove any secrets (grep for key=, token=, password=, secret=)

### Pass 3: Error Handling
- Every async operation has error handling
- Catch blocks do something (log, rethrow, recover; never empty)
- Error messages are specific and actionable
- API endpoints return proper error responses (not 500 + stack trace)
- External calls have timeout and retry logic

### Pass 4: Logic Review
- Every conditional: is the operator correct? (>, >=, ==, ===)
- Every loop: does it terminate? Off-by-one at boundaries?
- Every null check: is it in the right place (before use, not after)?
- Boolean logic: De Morgan's traps? Double negatives?

### Pass 5: Consistency
- Same error handling pattern throughout
- Same async pattern throughout (don't mix callbacks and promises)
- Same naming convention throughout
- Same file structure and organization

### Pass 6: Duplication
- Grep for similar code blocks (3+ similar lines = candidate)
- Apply Rule of Three: only abstract at 3+ occurrences
- Prefer duplication over wrong abstraction

### Pass 7: Security
- All user input validated and sanitized
- All database queries parameterized (no string concatenation)
- All output escaped for context (HTML, SQL, shell)
- Auth checks on every endpoint that needs them
- Dependencies scanned for known vulnerabilities

### Pass 8: Tests
- Every function has at least one test
- Edge cases tested (empty, null, boundary, error)
- Tests assert behavior, not implementation
- Tests can run independently (no order dependence)

---

## CodeScene's Key Insight: Code Health Predicts AI Success

CodeScene's research (2025-2026) links code health to AI effectiveness:

"Unhealthy" code produces 15x more defects, 2x slower development,
and 10x more delivery uncertainty compared to healthy code.

Critical finding for AI-agent workflows: "Code that is not-yet
AI-friendly needs to be refactored and uplifted BEFORE attempting to
implement features via agents."

In other words: refactoring isn't just cleanup. It's preparation.
Clean code produces better AI output. Messy code produces messier AI
output. The feedback loop is vicious or virtuous; you choose.

Their recommendation: "Even a minor amount of Code Health issues will
soon contribute to a major decline in subsequent iterations." Due to
AI speed, small quality issues accumulate quickly. What takes humans
months to degrade takes AI-assisted development weeks.

---

## The "Almost Right" Problem

Qodo's research: 66% of developers spend more time fixing "almost-right"
AI code than they save by generating it.

Why "almost right" is worse than "clearly wrong":
- Clearly wrong code fails tests and gets caught.
- Almost-right code passes tests and ships.
- The subtle error surfaces in production under specific conditions.
- Debugging "almost right" is harder because the code LOOKS correct.

The CodeRabbit report's recommendation: AI-aware PR checklists with
explicit questions about error-path coverage, concurrency correctness,
configuration validation, and security helpers. Generic code review
isn't sufficient; reviewers need to know WHERE AI fails.

---

## Refactoring Principles for AI Codebases

### 1. Refactor Incrementally, Not In Sprints
The mythical "tech debt sprint" rarely happens. Instead: every PR
improves one thing. Leave every file cleaner than you found it.
Boy Scout Rule (Robert C. Martin): "Always leave the campground
cleaner than you found it."

### 2. Test Before Refactoring
Never refactor without test coverage. If tests don't exist, write them
FIRST. The tests verify that your refactoring preserves behavior.
Refactoring without tests is rewriting, and rewriting introduces bugs.

### 3. Measure Before and After
Track: cyclomatic complexity, function length, duplication ratio,
dependency count, test coverage. If these don't improve, the refactoring
didn't help. Subjective "feels cleaner" is not evidence.

### 4. Refactor High-Churn Files First
Files that change frequently are where defects accumulate fastest.
Use git log to find hotspots: files with high change frequency AND
high complexity are the highest-value refactoring targets.
git log --format='%H' -- {file} | wc -l for change frequency.

### 5. Don't Refactor and Add Features Simultaneously
Fowler's "preparatory refactoring": "Make the change easy, then make
the easy change." Two separate commits. Two separate reviews. Mixing
refactoring with feature work makes it impossible to tell which
caused a regression.

### 6. Preserve Behavior, Not Structure
The goal of refactoring is to change structure while preserving
behavior. If the external API, return values, or side effects change,
it's not refactoring; it's rewriting. Different risk profile.

---

## Anti-Patterns in Refactoring

### Big Bang Rewrite
"Let's rewrite the whole thing." Almost always fails. Joel Spolsky
called it "the single worst strategic mistake that any software
company can make." Incremental improvement beats rewrite.

### Refactoring Without Tests
Changing code structure without a safety net. You will introduce
bugs. You won't know until production. Write tests first.

### Cosmetic Refactoring
Renaming variables and reformatting code without addressing structural
issues. Feels productive, changes nothing meaningful. Automate with
linters; don't spend human time on it.

### Refactoring Someone Else's Code Without Context
You see "bad" code. You refactor it. It was intentional; the "ugly"
code handled an edge case you didn't know about. Always understand
WHY code exists before changing it. Git blame is your friend.

### Scope Creep Refactoring
"While I'm here, I'll also fix..." leads to PRs that touch 40 files
and are impossible to review. One concern per PR. One concern per
commit. This is especially important in KERNEL: separate contract
for refactoring. Never mix with feature work.

### Trusting AI Refactoring Without Verification
AI suggests a "cleaner" version. You accept it. It looks better.
It also subtly changed the behavior in an edge case the AI didn't
test. Always run the full test suite after AI-suggested refactors.
CodeScene: "Agents cannot verify their own improvements. After a
refactoring attempt, is the code objectively better or just a
different arrangement of accidental complexity?"

---

## Integration with KERNEL System

Refactoring in KERNEL follows the standard flow with specific rules:

- Classification: refactor signal terms (refactor, clean, improve,
  optimize, restructure, simplify, extract) route through /kernel:ingest.

- Tier matters: 1-2 files = do it directly. 3+ files = contract.
  Never "refactor while you're there." Separate contract.

- tearitapart before large refactors: if tier 2+, review the
  refactoring plan before executing. What are we changing? Why?
  What's the risk?

- Tests first: validator agent runs BEFORE and AFTER refactoring.
  No test coverage = write tests as a separate contract FIRST.

- Atomic commits: "refactor: extract auth middleware" not
  "refactor: various improvements." Each commit is one structural
  change. Each is independently revertible.

- Evidence: the surgeon must show metrics before and after
  (function length, complexity, duplication). Not "it's cleaner"
  but "complexity reduced from 15 to 7."

- The "almost right" defense: after any AI-assisted refactoring,
  run the full 8-pass checklist above. AI refactoring introduces
  the same defect categories as AI generation.

---

## Moved from SKILL.md (2026-05-28)

### Core Principles (background)

Refactoring changes structure, not behavior. If behavior changes, it's not refactoring.
The goal is clarity, not cleverness. Three similar lines beats a premature abstraction.

### Vibe Coding Crisis (stats)

From research (2026): developers accept AI output without understanding.
60% decline in refactored code — velocity over health.
Copy-paste has overtaken abstraction for first time.

Refactoring is the antidote: systematically improve what AI generates.
But it requires understanding the code. No understanding = no safe refactor.

### AI Code Cleanup Patterns (GitClear 2026)

AI-generated code has specific patterns that need cleanup:
- Code cloning: 4x more duplication. Extract shared logic.
- Unused constructs: Imports, variables, functions never called. Delete.
- Hardcoded debugging: console.log, print statements left behind. Remove.
- Missing modularization: Long functions doing multiple things. Extract.
- Copy-paste over abstraction: Duplicate blocks that should be functions.

The verification bottleneck: AI generates faster than humans can review.
Refactoring must be reviewable — small, atomic, tested.

### Agentic Refactor Safety (background context)

**Phantom abstraction**: AI frequently creates abstractions used in only one place.
Rule: if an abstraction has exactly one call site, inline it. Wait for a second use
case before abstracting. (Executable rule retained in SKILL.md step 8.)

**Comment drift**: AI comments often describe what the code WAS doing before an edit.
Audit every comment for accuracy during refactor — stale comments are worse than none.
(Executable rule retained in SKILL.md step 8.)

**Parallel agent conflicts**: If multiple agents touched the same file, check git log
for overlapping changes. The "final" file may be a merge artifact, not intentional code.
(Executable rule retained in SKILL.md step 8.)

**Scope creep detection**: Before starting, write down EXACTLY what you're changing.
After finishing, diff changes against that list. Any extras are scope creep — revert
and open a separate task. (Executable rule retained in SKILL.md step 8.)

**Explicit scope for refactor agents (Opus 4.7)**: Opus 4.7 follows instructions literally.
- Wrong: "Rename `getUserData` to `fetchUser`"
- Right: "Rename `getUserData` to `fetchUser` in ALL files across the codebase, including imports, tests, and docs"
When spawning a surgeon for a refactor, enumerate the specific files in the contract.
Ambiguous scope = partial refactor. (Executable rule retained in SKILL.md step 7.)

### JiT Refactor Verification (background)

From Meta's JiT research: generating tests at the point of change catches regressions
that pre-existing suites miss — 4x bug-detection improvement. Tests generated JiT are
disposable; they exist only to verify behavior preservation during this refactor.
Delete them after if they're not worth keeping. Source: infoq.com/news/2026/04/meta-jit-testing-ai-detection/

### Strategic Refactoring (stats and context)

**Target high-impact components**: Teams targeting critical high-ROI components see 4x
better results than comprehensive refactoring sweeps. Identify by: change frequency, bug
density, review time.

**Atomic transformations under 200 lines**: Keeping each change under 200 lines reduces
code review time by 60% and lowers regression risk. Anything larger is a separate task.

**Document before refactoring**: Before starting, create an architectural diagram and
document any complex business logic the AI is unlikely to understand. AI frequently
mishandles domain-specific constraints. Organizations that prepare context see 3x faster
modernization cycles.

**Success metrics**: A successful refactor measurably reduces cyclomatic complexity by
15-25%. Organizations with systematic pre/post testing see 70% fewer post-deployment
issues.

**Embed into regular development**: Refactoring as a periodic "cleanup project" fails
from adoption friction. Integrate into normal PR workflow: every merge includes a small
cleanup.

**Rollback procedure required**: Establish a clear rollback path (git SHA or stash)
before every refactor. Never merge without the ability to undo.

Sources: getdx.com/blog/enterprise-ai-refactoring-best-practices/,
augmentcode.com/tools/ai-code-refactoring-tools-tactics-and-best-practices (2026-05-06)