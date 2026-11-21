# Red flags

Screen every candidate sketch against this list. Any hit is grounds to revise the candidate or drop it. Each flag names the symptom, why it hurts when the next contributor is an agent, and the fix.

## Shallow module

A wide public surface that hides little. Symptoms: one logical operation needs the caller to coordinate several calls in the right order; options expose internal steps or implementation choices; a caller who knows the interface still has to know the implementation. An agent copying a call site will copy half the sequence. Fix by merging the steps behind one call that owns the sequence. A deep module is different from a long call chain: depth means a small surface over a lot of work.

## Leaked decision

One internal choice, such as a data representation, a policy, or a protocol detail, is depended on by several modules, so changing it needs coordinated edits nobody will remember. Re-exporting wire types from a public module is a common case. Fix by parsing external data into domain types inside the boundary and keeping storage layouts, framework types, and wire details private to one module.

## Modules split by time

Code divided by when it runs (load, validate, convert, save) instead of by what knowledge it owns, so the same representation and its rules appear in each stage. An agent editing the validator will not see the converter's copy of the rule. Fix by organising around ownership. Functions that run at different moments can share a module when they guard the same decision.

## Forwarding method

A method whose whole body forwards its arguments unchanged to another method with an identical signature. The extra layer conceals nothing from callers. Delete it or move the responsibility, unless it adds a policy, an adaptation, or a real separate abstraction.

## Multiple writers

Several modules write the same state, or each keeps a private copy. An agent editing one writer cannot see the others, and the rules drift apart. Fix by giving the state one owner. Every other module only reads that state, and requests changes through the owner.

## Duplicate paths

Two supported ways to do the same thing. Agents copy whichever they find first, so both keep spreading. Fix by keeping one, moving every caller, and deleting the other in the same change.

## Reachable internals

Outside code can import a module's private parts. Agents will, and those parts become de facto API. Fix by making such imports fail at build time: package export maps, visibility modifiers, or a lint rule.

## Parallel lists

The same set of items enumerated in several places that must be edited together, such as an enum, a switch, a config table, and a docs list. Fix by keeping one list and generating the others, or by making the build fail when they disagree.

## Scattered trust checks

Authorization, input validation, or output encoding repeated at several call sites instead of enforced once at the boundary. An agent adding the next call site will copy one that lacks the check. Fix by moving the check to the single place every path must pass through, and by making the unchecked form impossible to construct (for example, a handler type that only exists after authorization).

## Privilege mixed with untrusted input

A module that both handles raw untrusted data (request bodies, uploaded files, model output, fetched pages) and holds credentials or performs privileged actions (writes to the database, runs shell commands, calls internal services). A parsing bug in such a module becomes a privilege bug. Fix by splitting parsing from acting, so the privileged module only receives validated domain types.
