# Review rubric

Apply the sections that fit the change. Each section lists what to check and what evidence a finding in that section needs.

## Correctness

Check the edge cases: empty collections, null or missing values, the first and last element, values at a limit, and two callers at once. Check how errors move: caught and handled, passed up, or swallowed without a trace. Check for off-by-one errors, implicit type coercion, integer overflow, text encoding, and stale state read after something else changed it.

Read both the success path and the failure path. Ask what happens when the operation runs twice, or when it crashes halfway and runs again. If the result depends on what the crashed run left behind, the change is missing a step that reconciles existing state before acting.

When two writers can touch the same state, check that something structural keeps them apart: a lock, a phase boundary, or exclusive ownership. A comment that says "only call this from X" is a convention, and conventions get broken.

Evidence: a suspected bug needs the call chain that produces it, starting from a real entry point.

## Root cause or symptom

This section requires reading outside the diff: the callers, the callees, the types, and sibling modules. Look for:

- A guard that hides a broken invariant instead of restoring it.
- A retry that papers over a contract the callee does not keep.
- A cast that silences a modelling mistake.
- A workaround with no record of the proper fix.
- A fix in the module where the symptom showed up, when the defect lives elsewhere.
- A rule that lives only in a "never do X" comment or an unwritten team habit, when the compiler, a linter or a check at runtime could enforce it.

Evidence: name where the real defect lives and why the change does not reach it.

## Structure

Input should be validated where it enters the system and trusted afterwards. Flag validation scattered through the interior, and flag interior code that accepts unvalidated input.

Flag high-level coordination mixed into low-level detail, new coupling between modules that did not know about each other, and data structures that do not match how the data is read. Picture the code as it would have been written had this requirement existed on day one. A change that looks attached from outside rather than built in is a warning.

If the change adds a new API and keeps the old one alive, and the old one has no external consumers, the callers should move and the old API should go in the same change.

Do not penalise simple code for lacking abstraction. Two copies of a few lines are cheaper than an abstraction that guesses at a second use.

## Verification

Tests should exist for new behaviour and should check behaviour, not internal calls. A bug fix should ship with a test that fails without the fix. Integration paths should be tested end to end where the project can. Assertions should read the real value, not a proxy such as a timestamp, a cache entry, or a log line. Work done by a subagent or an async job should be checked by reading its actual output, not its summary.

Evidence: name the behaviour that could break while every listed test stays green.

## Complexity budget

Look for complexity the change could drop: an abstraction with a single caller, a parameter for a case that does not exist, dead code, a speculative path, and migration scaffolding that outlived its migration. For user-facing additions, ask whether each option or mode earns its place. A half-built feature costs more than its absence because users and agents find it and depend on it.

## Security

Every security finding traces an input from its source to a sink. Check:

- Untrusted input reaching a query, a shell command, a path, dynamic evaluation, a deserializer, raw HTML, or an outbound URL.
- New endpoints, handlers, or jobs with weaker authentication or authorization than their neighbours.
- Secrets in source, logs, error messages, fixtures, or committed config.
- A check followed by a use, where the checked thing can change in between.
- Agent and tool code: text from issues, web pages, logs, or tool output that flows into a prompt for a model that can take actions. That text may carry instructions an attacker wrote.
- New or upgraded dependencies, and what they execute at install time.
