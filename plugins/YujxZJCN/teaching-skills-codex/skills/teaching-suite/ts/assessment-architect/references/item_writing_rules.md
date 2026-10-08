# Item Writing Rules

Working rulebook for `item_writer_agent` and the professor reviewing its drafts.
Distilled from classical test-construction practice (Pedagogy Foundations §10). These are
defaults: a professor's discipline convention overrules any rule here — record the
override and move on.

## Universal stem & option rules

| # | Rule | Bad | Fixed |
|---|------|-----|-------|
| 1 | One construct per item — never two capabilities behind one answer | "Define a binary search tree and state its worst-case search complexity. (2 pts)" | Two items: definition (1 pt); complexity with justification (1 pt) |
| 2 | Stem asks a complete question before options are read | "Binary search trees: a) are always balanced b) …" | "What is the worst-case search complexity of an unbalanced binary search tree?" |
| 3 | No double negatives; avoid negative stems, and bold NOT when unavoidable | "Which of the following is not a non-stable sort?" | "Which of the following sorting algorithms is stable?" |
| 4 | Options homogeneous in form, length, and grammar — the longest, most-qualified option is a known answer giveaway | Correct option twice as long with two qualifying clauses | Trim or lengthen distractors until parallel |
| 5 | Each distractor encodes a real misconception (log which, instructor-side) | Filler distractor "the algorithm crashes" | Distractor = answer a student gets by forgetting the rebalance step |
| 6 | No "all of the above" / "none of the above" by default — AOTA is answerable from any two options; NOTA leaves the construct unmeasured | "d) all of the above" | Replace with a fourth misconception-based distractor, or use multiple-select with stated select-count |
| 7 | No absolute or hedge cues ("always", "never" in distractors; "usually", "may" in the key) | Key is the only option containing "may" | Match hedging across all options |
| 8 | No trick wording: difficulty comes from the construct, not from parsing | "…assuming the array is sorted (descending)" buried mid-sentence | State the non-default condition prominently, or test it deliberately as the construct |
| 9 | Items independent: one item must not reveal or require another's answer | Item 7's stem states the fact item 3 asks for | Reorder, rewrite, or merge into one multi-part problem with explicit carry-forward |
| 10 | No untaught content — every item traces to taught material and a tagged outcome | Item on a topic the schedule shows was cut | Cut the item or flag the alignment break (Pedagogy Foundations §2); never "they should know it anyway" |
| 11 | Numeric distractors are computed wrong paths, not random offsets | Correct 42; distractors 41, 43, 44 | Distractors = sign error result, off-by-one result, formula-confusion result |
| 12 | Options in a logical order (numeric ascending, chronological) — randomness reads as a pattern puzzle | Options 17, 3, 42, 8 | 3, 8, 17, 42 |

## Per-format guidance

**Multiple choice.** 3–5 options; four is the default; a sharp three-option item beats a
four-option item with one dead distractor. Best for remember/understand/apply, and for
analyze+ only with a scenario stem (below).

**Multiple-select.** State the count ("select TWO") or warn that count is unstated —
and pick one convention per instrument. Score all-or-nothing or per-option-with-no-
negative; declare which in the grading notes.

**Short answer.** Specify expected length and form ("one sentence", "an expression in
terms of n"). The key lists required elements + acceptable phrasings — a short-answer
item without an element list is ungradeable consistently.

**Numeric / problem.** State units, precision, and what work must be shown. Multi-step
problems get per-step points and a carry-forward policy in the grading notes so an early
slip doesn't zero the attempt. Specify tool conditions (calculator, formula sheet) on
the item, not just the cover page, if they vary.

**Essay.** The prompt names the construct and the criteria hooks ("graded on thesis,
use of course evidence, counter-argument handling"). One broad essay is usually worse
measurement than two focused ones (one construct per item, scaled up). Key = exemplar
sketch + rubric mapping, never a model "answer."

**Oral.** A protocol, not a conversation: fixed core questions per outcome, defined
probe ladder ("if stuck, prompt with X — costs one level"), and a scoring sheet filled
during, not after. Time-box per student and state it.

## Writing higher-order items

Recall phrasing cannot carry an analyze cell. Patterns that can:

- **Scenario stems** — a situation, case, or system the student hasn't seen; the
  question requires applying course concepts to it, not recognizing them.
- **Data interpretation** — a table, plot, output, or trace; the item asks what it
  shows, what's wrong with it, or what follows from it.
- **Error-finding** — a worked solution, proof, code, or argument with a planted flaw;
  the student locates and names it. (The flaw is a known misconception, naturally.)
- **Justify-your-choice two-tier items** — tier 1: an MC choice; tier 2: a short
  justification, separately pointed. Catches right-answer-wrong-reason, the failure
  mode plain MC cannot see.
- **Best-answer items** — all options defensible, one superior by a stated criterion;
  this is the honest MC form of *evaluate*, and the stem must name the criterion.

## Bank & variant discipline

For `question-bank` mode and parallel exam forms — what may vary across variants of one
item family, and what must not:

| May vary | Must not vary |
|----------|---------------|
| Surface numbers (within the same difficulty band — no variant where the arithmetic happens to be trivial) | The construct: outcome, Bloom level, blueprint cell |
| Names, contexts, cover stories | The solution path's structure and step count |
| Option order | The misconceptions the distractors encode |
| Dataset instance (same shape and noise character) | Units/conventions mid-family (invites transcription errors across forms) |

Every variant carries a family id; randomized delivery serves at most one member per
family per student. Each variant gets its own independently worked key — variants are
where silent key errors breed, because nobody re-solves "the same" item.
