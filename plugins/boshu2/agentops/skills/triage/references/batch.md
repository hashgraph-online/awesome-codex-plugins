# Batch triage

Conditional detail for [Triage](../SKILL.md): read it when asked what needs
triage, or when more than one input arrives at once. Each item still follows
the rules and output in the skill body.

Asked what needs triage, query for items never triaged (the tracker's own
triage state, or else no maintainer comment and no label, named as the proxy
in the limit) and for needs-info items with a reply from anyone after the
last triage note; include PRs only from outside contributors unless one is
named. List each by ID and one line, oldest first, with the query and its
limit; the maintainer picks.

List every input with a stable ID first: tracker ID, URL, or for an untracked
message its channel, sender and timestamp. A reply in a message-channel thread
that is itself a batch input gets its own ID and carries its parent's ID and a
one-line summary of the parent; classify it against that report. A comment on
a tracker item belongs to that item. Work one item at a time to its own
outcome. Reconcile at the end: every input ID appears once in the output, as an
outcome, its split items, a link to its in-batch duplicate, or "not reached:
<why>". When the budget runs short, stop at an item boundary rather than thin
every item.
