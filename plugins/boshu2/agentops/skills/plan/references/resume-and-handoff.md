# Resume, handoff and exact intent

Plan loads this only when discovery resumes after interruption or
replacement, when a slice goes to another context, when the caller asks for
code plus a retrospective, or when conversation intent needs an exact
snapshot.

## Resume discovery

Recover the current outcome, accepted examples and source identity from the
existing plan or native handoff. Reuse settled domain terms and caller choices
with their source pointers; do not repeat an interview or load the full
transcript. Read details on demand only if a missing fact or new contradiction
can change the next decision. Before reusing inherited prototype evidence,
follow [reuse after source drift](ground-truth-routing.md#reuse-after-source-drift).

Check active assignments, write scopes and integration or review ownership
against the native tracker or runtime before suggesting more work. Handoff
facts are recovery pointers, not a second authoritative assignment or status
ledger. If the native source is unavailable or contradicts the handoff, report
that gap and resolve it before dependent dispatch or overlapping writes;
independently safe discovery can continue.

Leave a compact update in that same source when interruption or replacement
would otherwise lose a decision: accepted outcome and reference; settled
choices and evidence; active assignment references and scopes; the one open
question and next discriminator; deferred decisions and their revisit
triggers; known failed assumptions and relevant contrary evidence. An
unchanged recovery needs no duplicate artifact. Preserve native ownership and
original evidence; new observations amend the approach within scope, while
changed acceptance still needs the caller.

## Hand a slice to another context

Give it exact intent references and the evidence it needs to act, its write
scope, and who owns integration and final review. Keep approach notes separate
from frozen acceptance. Pass the next decision and relevant source references,
not the entire research history. A new goal does not clear an existing
conversation, and a fresh context can still carry large startup instructions,
tool catalogs and retrieved inputs.

## Code plus a retrospective

When the caller requests both, distinguish code acceptance, delivery facts and
the later analysis in the same intent. Code judgment consumes acceptance and
checks; the retrospective consumes the known outcome and judgment. Keep both
deliverables required for the overall goal without making either depend on
its own conclusion.

## Exact intent identity

Use runtime-derived source identity and digest. If conversation intent needs
an exact snapshot, the existing command
`ao provenance snapshot-intent --source - --evidence-root <explicit-root>`
writes it to caller-selected protected external non-Git storage. Missing
routing permits neither a workspace fallback nor a second planning artifact.
Preserve legacy proof.

## Sources

Decision pointers and coarse future work adapt ideas from Matt Pocock's
[Wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md);
complete slices and compatibility migrations adapt
[To Tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md).
AgentOps keeps the caller's existing intent and native work authority.
