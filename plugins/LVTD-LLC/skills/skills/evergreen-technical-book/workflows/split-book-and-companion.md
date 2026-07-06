# Split Book And Companion Workflow

Use this workflow to decide what stays in a technical book and what moves to updateable companion resources.

## When To Use

- A technical manuscript feels likely to become outdated.
- A chapter has many tool-specific or UI-specific steps.
- The author wants a book plus website, repo, worksheet, video, or living guide.
- A self-hosting or DevOps book needs concrete examples without becoming stale.

## Prerequisites

- Draft outline or manuscript.
- Target reader and durable book promise.
- Candidate companion resource home, or permission to propose one.

**Reference**: `references/core/rules.md`

---

## Workflow Steps

### Step 1: State The Durable Promise

**Goal**: Know what must remain valuable.

- [ ] Write the reader capability the book should create.
- [ ] Identify which parts should still matter in 3-5 years.
- [ ] Identify whether the book is evergreen or edition-based.

---

### Step 2: Classify Content

**Goal**: Sort material by expected half-life.

- [ ] Mark durable concepts.
- [ ] Mark semi-durable workflows and examples.
- [ ] Mark volatile UI, pricing, policy, version, vendor, and screenshot details.
- [ ] Mark safety warnings that must remain in the book.

---

### Step 3: Decide The Split

**Goal**: Keep the book complete and durable.

- [ ] Keep mental models, decisions, safety boundaries, and core flow in the book.
- [ ] Move volatile walkthroughs or variants to companion resources.
- [ ] Keep enough concrete examples in the book to avoid vague advice.
- [ ] Remove or shorten content that is both volatile and low value.

---

### Step 4: Design Companion Resources

**Goal**: Make updateable material maintainable.

- [ ] Define resource type: repo, website, checklist, script, video, template, or guide.
- [ ] Define owner and update cadence.
- [ ] Define last-reviewed or version markers.
- [ ] Define reader issue/report path.
- [ ] Define how the book links to the resource.

---

### Step 5: Rewrite References

**Goal**: Avoid brittle references and incomplete chapters.

- [ ] Replace fragile deep links with stable resource homes when possible.
- [ ] Explain the purpose of each companion resource.
- [ ] Add current-info caveats where needed.
- [ ] Verify the book still delivers the core promise without extra purchase or hidden access.

## Exit Criteria

Task is complete when:

- [ ] The book vs companion split is explicit.
- [ ] Volatile details have an update plan.
- [ ] The manuscript remains concrete and complete.
- [ ] Reader-facing references are stable enough to survive drift.
