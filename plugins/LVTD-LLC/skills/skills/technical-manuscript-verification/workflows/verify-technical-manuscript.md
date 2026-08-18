# Verify Technical Manuscript Workflow

Use this workflow to run a technical verification pass on a manuscript, chapter, or tutorial.

## When To Use

- A technical chapter is ready for beta readers.
- A self-hosting or infrastructure guide contains commands or config.
- A final manuscript needs accuracy checks before production.
- A draft may contain stale platform, UI, pricing, or version details.

## Prerequisites

- Manuscript section or artifact set.
- Target reader and supported environment.
- Safe test environment, or a clear list of untestable items.

**Reference**: `references/core/rules.md`

---

## Workflow Steps

### Step 1: Define Scope And Environment

**Goal**: Know what is being verified and under what conditions.

- [ ] Select chapter, section, or artifact type.
- [ ] Name supported OS, versions, tools, provider, and hardware.
- [ ] Identify unsafe or unavailable checks.
- [ ] Create an evidence table.

---

### Step 2: Inventory Technical Items

**Goal**: Find everything that can fail.

- [ ] Extract commands, code, config, links, screenshots, diagrams, file paths, ports, and claims.
- [ ] Mark safety-critical items.
- [ ] Mark current-info dependencies.
- [ ] Mark expected-output gaps.

---

### Step 3: Verify Items

**Goal**: Check artifacts with the strongest practical evidence.

- [ ] Run safe commands or code in the named environment.
- [ ] Parse, lint, or dry-run config files where possible.
- [ ] Check links and primary documentation for volatile details.
- [ ] Compare screenshots and diagrams to current text.
- [ ] Record pass, fail, partial, untested, or unsafe status.

---

### Step 4: Classify Findings

**Goal**: Prioritize by reader harm and manuscript promise.

- [ ] Flag critical and high-risk safety issues first.
- [ ] Flag blockers to the core reader outcome.
- [ ] Flag missing prerequisites and unsupported variants.
- [ ] Flag stale current-info dependencies.
- [ ] Flag unclear expected outputs.

---

### Step 5: Recommend Fixes

**Goal**: Give the author changes they can apply.

- [ ] Write exact manuscript edits.
- [ ] Add expected outputs or verification steps.
- [ ] Add warnings, rollback, cleanup, or troubleshooting.
- [ ] Recommend companion-resource moves for volatile detail.
- [ ] List items for expert review or beta-reader testing.

## Exit Criteria

Task is complete when:

- [ ] Technical findings are evidence-backed.
- [ ] Untested items are clearly labeled.
- [ ] High-risk reader failures have fixes.
- [ ] The author knows what must be verified again after edits.
