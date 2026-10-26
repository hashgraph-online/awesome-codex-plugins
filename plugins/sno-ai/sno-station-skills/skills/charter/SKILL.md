---
name: charter
description: "Write, revise or review a charter: the one document that tells an executor what to deliver, what is out of bounds, what the owner already decided, and how each success check will be proven. Use when work needs a written brief before someone else does it, or when asked to write, change or check a charter."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# charter

A charter is one markdown file that says what to deliver and how everyone will know it was
delivered. A task is named by its charter
filename. `charter` writes it; `deliver` carries a released charter out. Any kind of project
uses it: software, documents, campaigns, research, operations. The owner is whoever owns the
work (often the user); speak to them in the language they use.

Prerequisites: none to use it; its selftest needs bash and python3.

Read `references/template.md` for the file layout and `references/questions.md` before asking
the owner anything.

## Rules that keep a charter useful

- Preserve the owner's words and decisions. Never invent a decision, a fact or a requirement.
  A missing choice that would change the outcome is asked once, one question at a time, at the
  end of a message; independent work continues while it waits, and silence is not approval.
- Read the existing work first (files, documents, data, earlier decisions). Ask nothing they
  already answer.
- Every success check names what will be observed, where, and how, and can be answered pass or
  fail by a real run or inspection. The expected result comes from the requirement or from
  independent data, never from pasting the program's own output. For a defect, the check
  reproduces the defect first.
- Before adding a precondition, check, section or approval step, name the failure it detects
  and what would change if it failed. If nothing changes, leave it out. By default no checksums,
  sign-off records, warm-up runs, baselines, fixed snapshots or report formats are entry
  conditions.
- By default a security check, a full test suite or a full evaluation enters a charter only if
  the owner names it. Propose it as a question that says what it would check and what it would
  block; do not write it in as a requirement on your own judgment. A project may choose
  otherwise.
- Say what happens on failure: which operation is logged with its error, what continues. A
  record or report failure never disables the main result; a real failure stays a failure.
- Time is finite. A check that takes long states its expected duration from existing timings;
  by default no full suites unless the owner asks.
- State what the executor may not do without the owner: publish, send to other people, spend,
  delete, overturn a recorded decision.

## Write

1. Read the request, adjacent notes and the existing work. Cite settled decisions without
   copying or locking their source. When the work depends on a third-party product, service or
   version, read its current official documentation and record the facts that constrain the
   work with the page and version.
2. Draft Owner decisions, Outcome, Scope and non-goals, and Success checks from the template.
   Length follows the work: a few lines for a small task, a sliced charter (named slices, each
   with its own checks) for a big one. There is one kind of charter, not sizes.
3. Read it as the executor: for each check, could someone tell pass from fail without asking?
   Walk one real example through it. Fix the gaps that would make the result fail. Do not run
   the future work to plan it.
4. One independent review for the owner's intent and concrete defects (`peer-review` when it
   is installed, otherwise a second agent). Fix material findings; no second round unless the
   owner asks.
5. Tell the owner what the charter will deliver and any genuine open decision, in plain
   words, ending with the one question. After the owner approves, set `status: released` and
   hand the path to the executor, or to whoever supervises the work.

By default an agent alone never releases a charter: it records the owner's decisions. When the
owner is away, leave the charter as a `draft` for them to release; a project may choose
otherwise.

## Revise

A scope change updates the affected decisions and checks in the same edit, sets `updated`, and
leaves the rest alone. A replaced charter gets `status: superseded` and a pointer to its
successor. Delivery records `delivered` only through `deliver`; never infer it from the header.

## Review only

Read the charter and the affected work. Report concrete mismatches, their consequences and the
smallest corrections in one local file; do not edit the reviewed charter. Questions go in the
conversation. Applying accepted corrections is Revise.
