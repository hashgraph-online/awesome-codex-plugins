# Audit Engagement Workflow

Use this workflow to find value-pacing and reader-dropoff risks in a nonfiction manuscript.

## When To Use

- A manuscript feels boring, bloated, or slow.
- A draft is being prepared for beta readers.
- Beta readers stop commenting or abandon at similar points.
- The author wants a word-count map by section.

## Prerequisites

- Manuscript in Markdown, outline form, or another readable structure.
- Target reader and book promise.
- Optional beta-reader comment or progress data.

**Reference**: `references/core/rules.md`

---

## Workflow Steps

### Step 1: Anchor On Reader Value

**Goal**: Know what engagement means for this book.

- [ ] Identify target reader.
- [ ] State the book promise.
- [ ] Define the first meaningful payoff.
- [ ] Define value events for this manuscript.

---

### Step 2: Generate The Structure Map

**Goal**: Measure value over reading time.

- [ ] Run `scripts/analyze_manuscript.py` for Markdown when possible.
- [ ] Capture section word counts and cumulative words.
- [ ] Mark long sections and weak headings.
- [ ] Estimate reading time where useful.

---

### Step 3: Mark Value And Risk

**Goal**: Identify slow starts and slogs.

- [ ] Mark first payoff distance.
- [ ] Mark value events.
- [ ] Mark setup-only runs.
- [ ] Mark vague topic headings.
- [ ] Mark sections whose word count exceeds their payoff.

---

### Step 4: Incorporate Beta Data

**Goal**: Use reader behavior as a heatmap.

- [ ] Map comment clusters and dropoffs by section.
- [ ] Compare patterns across readers.
- [ ] Inspect the section before each dropoff.
- [ ] List follow-up questions for ambiguous reader silence.

---

### Step 5: Recommend Revisions

**Goal**: Improve engagement structurally.

- [ ] Move useful material earlier.
- [ ] Cut or compress low-value setup.
- [ ] Rename headings as takeaways.
- [ ] Split long sections with multiple takeaways.
- [ ] Add examples, checklists, labs, or decisions where payoff is missing.

## Exit Criteria

Task is complete when:

- [ ] The main engagement risks are named.
- [ ] The evidence table is available.
- [ ] The author has an ordered structural revision plan.
- [ ] Follow-up checks after revision are clear.
