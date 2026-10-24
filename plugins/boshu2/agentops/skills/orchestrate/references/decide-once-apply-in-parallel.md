# Decide once, apply in parallel

Orchestrate loads this when several workers will apply one set of decisions: a
batch of review findings to repair, or one rewrite that must read the same in
many files. Parallel workers apply a decision well but rarely make the same
decision the same way. Splitting the decision across them yields one variant per
worker and leaves no context that saw the whole set.

## The shared shape

- One context decides. It reads the inputs whole, makes each decision, and
  writes it so a worker can apply it without judging it again.
- Workers apply decisions inside their declared scope. They do not reopen
  whether a decision is warranted, and they do not invent a variant for a case
  the decision does not cover.
- A worker returns an item unapplied only with something the decider could not
  see: an occurrence the decision does not fit, a caller or check the change
  would break, or code that differs from what the decision assumed.
- The decider settles each returned item with that evidence: correct the
  decision and dispatch it again, answer it without a change, or return it to
  the caller. A returned item is never dropped.
- The decisions travel in the worker packets and the existing native handoff;
  they need no separate ledger or persisted artifact.

## A batch of findings

Decide which findings become repairs in the one context that holds all of them.
Read each affected file once and judge its findings together, not one at a
time. A source that is wrong about one finding is suspect for its others, so
weigh the rest with that in mind. When the batch is too large for one context,
split it into groups clustered by file and judge each group whole; never assign
one judge per finding. Repair workers receive decided repairs only.

## One rewrite across many files

Find the occurrences in parallel, then decide in one place. One author writes
the exact old text, the exact new text, and the cases the change excludes.
Workers apply that mapping verbatim within their own scopes and report any
occurrence it does not fit. The author settles each gap and updates the mapping
for any worker still running. After integration, search the whole tree for the
old text, including files no worker owned and generated companions; each hit is
either an excluded case or unfinished work.
