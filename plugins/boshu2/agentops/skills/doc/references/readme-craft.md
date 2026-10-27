# README Craft — Gold-Standard README Generation

> Generate a README that converts skimmers into users and satisfies deep readers, then run deterministic documentation checks and return factual evidence to the caller.

Use this reference when the caller asks to create, update, rewrite or check a README.

## Request shapes

- **New:** no README exists, or the caller asks for one from scratch. Gather
  context, fill each section, generate, then run the checks.
- **Update:** bring one section or fact of an existing README current (for
  example, install steps that no longer match the code). Edit that part in
  place under [Grounded writing step 3](../SKILL.md#grounded-writing): keep the
  file's shape, skip Steps 2-4 and the template, then run Step 5.
- **Rewrite:** regenerate an existing README with these patterns, using the
  current file as context.
- **Check only:** inspect an existing README against these patterns without
  rewriting it, and report the evidence.

---

## The Patterns

Every README this mode generates or rewrites follows these patterns; an update
applies them only to the part it edits.

### 1. Lead with the problem, not the framework

Bad: "A DevOps layer implementing the Three Ways for agent workflows."
Good: "Coding agents forget everything between sessions. This fixes that."

The reader should understand what pain you solve in one sentence. No jargon, no framework names, no theory. The problem is the hook. (Note: framework references like Three Ways and Meadows belong in the body as design rationale — just don't lead with them.)

### 2. Acknowledge prior art

If your approach resembles established practices (agile, SCRUM, spec-driven development, CI/CD), say so explicitly:

> "If you've done X, you already know the fix. What's new is Y."

This disarms experienced practitioners who would otherwise dismiss you as reinventing the wheel. Claim only what's genuinely novel.

### 3. Show, don't claim

Bad: "This is what makes X different. The system compounds."
Good: A terminal transcript showing the system working.

Assertions without evidence trigger hostility. Concrete examples > adjectives. If you can't show it in a code block, it's not ready for the README.

### 4. State your differentiator once

One clear explanation. One demonstration. That's the max. Repeating your core value proposition in every section crosses from reinforcement into marketing copy. Trust the reader to absorb it the first time.

### 5. Trust block near install

Before a user installs anything that runs code, hooks, or modifies config, they need to see:

| Concern | Answer it |
|---------|-----------|
| What does it touch? | Files created/modified, hooks registered |
| Does it exfiltrate? | Telemetry, network calls, data leaving the machine |
| Permission surface | Shell commands, config changes, git behavior modifications |
| Reversibility | How to disable instantly, how to uninstall completely |

This goes near the install command, not buried in an FAQ.

### 6. Collapse depth, don't delete it

Detailed workflow steps, architecture deep-dives, theory, and reference material belong in `<details>` blocks. Skimmers get the fast path. Deep readers click to expand. Never delete depth to achieve brevity — collapse it.

### 7. Strip guru tone

No "What N months taught me." No "I come from X, so I applied Y." No "This is what makes us different." Let the tool speak for itself. Humility disarms. Condescension repels.

### 8. Section order serves adoption

```
Problem → Install → See It Work → Getting Started Path → How It Works (collapsed) → Reference
```

Theory and architecture come AFTER the user has seen examples and knows how to start. Never put "why this is important" before "how to try it."

---

## Execution Steps

For the request shape detected in Step 1:

### Step 1: Pre-flight

```bash
ls README.md 2>/dev/null
```

**Request detection:** take the shape from the request.
- Check only + README exists → skip to Step 5 (deterministic review only)
- Update + README exists → edit the named part in place, then Step 5
- Rewrite + README exists → read existing, use as context for rewrite
- No README exists → proceed to Step 2 (generate from scratch)
- README exists and the request names no shape → ask once which the caller
  wants

### Step 2: Gather Context

Read available project files silently (no output to user):

```bash
ls README.md PRODUCT.md package.json pyproject.toml go.mod Cargo.toml Makefile 2>/dev/null
ls -d src/ lib/ cmd/ app/ 2>/dev/null
ls -d docs/ 2>/dev/null
ls LICENSE CHANGELOG.md 2>/dev/null
```

Extract:
- **Project name** from manifest files
- **Language/runtime** from build files
- **Existing description** from README or PRODUCT.md
- **License** from LICENSE file
- **Install method** from manifest (npm, pip, brew, go install, cargo, etc.)

### Step 3: Fill each section

Ask only for facts the repository cannot supply. Each prompt below names the
fact a section needs; fill it from Step 2 where possible and keep any question
short.

#### 3a: The Problem

Ask: "What problem does this solve? One sentence — what pain does your user have?"

Options (derived from existing README/PRODUCT.md if available):
- Suggested problem statement
- A punchier variant
- "Let me type my own"

#### 3b: The Fix

Ask: "How does it fix that problem? One sentence — what does your tool actually do?"

#### 3c: Who Is It For

Ask: "Who is this for? Name the runtime, framework, or role."

Example: "Python developers using FastAPI" or "Anyone running Claude Code or Cursor"

#### 3d: Install

Ask: "What's the install command? (We'll put this front and center)"

Options:
- Detected from manifest (e.g., `npm install <pkg>`, `pip install <pkg>`)
- "Let me type my own"

#### 3e: Quick Demo

Ask: "What's the simplest thing a user can do after installing to see it work? (A command, a code snippet, or a terminal session)"

#### 3f: Trust Concerns

Ask: "Does your tool do any of these? Check all that apply."
- Runs shell commands or hooks
- Modifies config files outside the project
- Makes network calls
- Creates files in the user's repo
- None of the above

#### 3g: Prior Art (optional)

Ask: "Are there similar tools? If so, how is yours different? (Be honest — readers who know the space will check)"

Options:
- "Yes, let me describe" → follow up
- "Not really / I'll skip this"

### Step 4: Generate README

Using the section facts from Steps 2-3 and the 8 patterns above, generate the README with this structure:

```markdown
<div align="center">

# {Project Name}

### {Problem statement — one line}

{Badges}

{Nav links}

</div>

---

> [!IMPORTANT]
> {Trust block — local-only, what it touches, how to disable, how to uninstall}
> (Skip if no trust concerns from 3f)

{Install command}

## The Problem

{2-3 sentences expanding the problem. Acknowledge prior art if applicable.
State what's genuinely new about your approach — once.}

## See It Work

{Terminal transcript or code example from 3e. Show, don't describe.}

## Install

{Full install details, alternative methods in <details> blocks.
"What it touches" table if trust concerns exist.}

## Getting Started

{Adoption path — Day 1, Week 1, etc. Or just "Run X, then Y."}

## How It Works

{One paragraph summary + diagram if applicable.}

<details>
<summary><b>Details</b> — {phases, architecture, etc.}</summary>

{Deep content here}

</details>

## {Reference sections as needed}

{Skills, API, CLI, etc. — collapsed where appropriate}

## FAQ, Contributing, License (only when the project has them)

{Top 3 questions inline, a link to CONTRIBUTING.md, the license name}
```

**Generation rules:**
- Every `<details>` block must have a blank line after `<summary>` (enables markdown rendering)
- Use markdown inside details blocks, not inline HTML (`<code>`, `<a href>`, `<br>`)
- Trailing blank line before `</details>`
- No emoji unless the user's existing content uses them
- Flywheel/differentiator concept: state ONCE in "The Problem", demonstrate ONCE in "See It Work"
- Never use phrases: "What N months taught me", "This is what makes X different", "I come from X so I applied Y"

For a New or Rewrite request, write the generated README to `README.md`.

### Step 4b: Docs prose pass (optional)

For a substantial generated or rewritten README, the full docs-prose prompt in
[de-slopify.md](de-slopify.md) can help: run it on the exact `README.md` you
wrote and recast line by line, not with a regex pass.

For a check-only request: inspect for residual prefab/slop tells and record
them as evidence; do not rewrite unless the caller asked for a rewrite.

### Step 5: Deterministic checks

Run the repository's own link or docs checks where they exist and inspect the
anti-pattern table below against the exact README. Record concrete matches,
checked scope, and anything the local environment could not check. These
results are evidence, not a semantic verdict.

Do not start Council, rewrite the README again, or decide what happens after a
finding. The caller may supply the README and these results to Validate as part
of an exact candidate.

### Step 6: Report

```
## README Evidence

**File:** README.md
**Checks:** {commands and factual results}
**Unchecked:** {scope not examined}

{List concrete findings without approval or next-action language}
```

---

## Anti-Patterns to Detect

When rewriting or validating, flag these:

| Anti-Pattern | Detection | Fix |
|-------------|-----------|-----|
| **Flywheel echo** | Core value prop stated 3+ times | State once, demonstrate once |
| **Framework-first** | Opens with methodology name, not problem | Rewrite lead as problem statement |
| **Guru tone** | "What I learned", "This is what makes X different" | Strip, let the tool speak |
| **Jargon before definition** | Domain terms used before they're explained | Define on first use or use plain language |
| **Buried trust info** | Security/permissions info below the fold | Move near install |
| **No visible uninstall** | Uninstall not findable within 10 seconds | Add near install block |
| **Install scatter** | Same install command in 3+ locations | One hero install, one canonical reference |
| **Theory before try** | Architecture/philosophy before examples | Reorder: examples first, theory in details |
| **Claim without evidence** | "Best", "different", "unique" without demo | Replace with concrete example or remove |
| **AI slop prose** | Prefab phrases, "not X, it's Y" on the lead, "here's why," metronomic cadence | Run [de-slopify.md](de-slopify.md); recast manually |

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| A repository docs or link check cannot run | A required local tool or path is unavailable | Record the command failure and unchecked scope; do not claim the check passed |
| Generated README has no trust block | Step 3f recorded no trust concerns ("None of the above") | Report the mismatch when the tool does run hooks, modify config, or make network calls |
| `<details>` blocks render as raw HTML on GitHub | Missing blank line after `<summary>` tag or before `</details>` | This mode enforces the formatting rule, but manual edits may break it. Ensure a blank line after every `<summary>...</summary>` line and before every `</details>` |
| Questions ask for facts the project manifest already answers | The manifest file format is not recognized by the context-gathering step | Ensure your project has a standard manifest (`package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`) in the repo root |
| Anti-pattern detection flags false positives on rewrite | Some content patterns trigger heuristic detection even when intentional | Report the exact match as heuristic evidence and let the caller judge it |
