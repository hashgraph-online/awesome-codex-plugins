# Code-quality lens

Every reviewer applies this lens on top of the rubric. The standard is strict and aims at code that stays cheap to change.

## What to look for

**Restructuring that deletes.** Look for a change, with identical behaviour, that removes a whole branch, helper, mode, or layer by using the existing architecture better. Prefer it over local tidying. Removing complexity is worth more than moving it to another file.

**File size.** Treat a change that pushes a file past roughly 1,000 lines as a serious warning. Recommend splitting unless there is a structural reason to keep it whole and the file stays well organised.

**Special cases.** New ad hoc conditionals inside an unrelated flow are a design problem. The logic belongs in its own helper, module, or state machine where the next reader will find it.

**Plain code.** Prefer boring, direct code over clever mechanisms. Call out thin wrappers and forwarding helpers that add a hop and explain nothing.

**Types.** Question optional fields that are always present in practice, untyped escape hatches, and code that needs many casts to compile. Prefer an explicit typed model. Question silent fallbacks: a default value that hides a missing invariant turns a crash into wrong data.

**Layering and reuse.** Logic belongs in its proper layer. Call out feature-specific code leaking into shared modules, internals exposed through a public API, and reimplementations of a helper that already exists in the repository.

**Work ordering.** Flag independent steps run one after another for no reason, and multi-step updates that can stop halfway and leave the system in a mixed state. Do not chase micro-optimisations.

## Order of concerns

Report in this order: structural regressions and missed simplifications first, then branching complexity, then type, boundary, and file-size problems, then small modularity and readability points.

## Presumed blockers

Treat each of these as blocking unless the author has a stated reason:

- Incidental complexity that a restructuring would remove.
- A file crossing the size threshold.
- An existing flow tangled with ad hoc branches.
- Feature conditionals spread through shared modules.
- A needless wrapper, or a contract that only holds through repeated casts.
- A reimplemented helper, or logic placed in the wrong layer.

Code that appears to work is not enough to approve.

## Tone

Be direct and specific without being rude. Do not shrink a structural problem into a naming suggestion to make it easier to hear.
