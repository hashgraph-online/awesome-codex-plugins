# Caller vocabulary examples

Use these examples when a naming question hides a behavioral distinction.
They illustrate the skill; they are not definitions to import into a caller's
domain. Keep actual decisions in that caller's existing source owner.

## Distinguish the thing from its use

A library catalog calls a particular printed volume a **copy**. Circulation
calls one reader's temporary possession of that copy a **loan**. A proposed
`CloseCopy` operation obscures whether a return ends the loan or removes the
volume from circulation. Inspect the existing definitions and return behavior
before proposing `ReturnLoan`; the useful distinction is the preserved copy,
not a preference for one verb.

```gherkin
Scenario: A return ends a loan while retaining the copy
  Given copy C has an active loan to reader R
  When R returns C
  Then that loan is completed
  And C remains in the catalog and becomes available to borrow
```

If accepted, this example supplies both the operation's meaning and the later
behavioral check. A passing test that merely deletes the loan does not establish
the copy's continued availability. Changing an exported operation name still
requires the repository's compatibility checks.

## Keep context-specific meanings explicit

An identity service uses **workspace** for an organization-controlled resource
with membership. An editor uses **workspace** for a local set of open files.
Do not merge them into one entity or rename both across the repository. Qualify
the meanings where the contexts meet and state whether an editor workspace
belongs to an identity workspace; do not infer identical lifetimes.

```gherkin
Scenario: Closing the editor does not remove membership
  Given a person belongs to an identity workspace
  And an editor workspace is open for that person's files
  When the person closes the editor workspace
  Then their identity workspace membership remains unchanged
```

A lookup cites the relevant definition and changes no files. An authorized
refinement updates the existing definition where one exists. If code or tests
contradict the accepted example, report the specific disagreement and preserve
the intended behavior for implementation and validation; do not redefine the
term to make the current code appear correct.
