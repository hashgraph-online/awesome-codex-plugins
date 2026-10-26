# Resume, handoff and exact intent

Plan loads this only when discovery resumes after interruption or
replacement, when a slice may go to another context, when the caller asks for
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

Change context at a step boundary, not midway; midway, keep going, or, where
the caller has authorized delegation, hand a tightly scoped remainder on under
Orchestrate. At a boundary, stay in this context when
the next step needs its reasoning as it happened (shaping a slice right after
the interview that settled it, say) and room remains: a summary, handoff or
new session replaces that record with a lossy copy, worth paying for only when
staying costs more. Before any change, make sure the intent source holds the
settled choices the next step needs (Resume discovery's update, under the
authority of Plan's Output write) and name what it must keep; check a
consequential decision against that source, not a summary. A dispatched
implementer still starts fresh under
[Orchestrate](../../orchestrate/SKILL.md).

Give it exact intent references and the evidence it needs to act, its write
scope, and who owns integration and final review. Keep approach notes separate
from frozen acceptance. Pass the next decision and relevant source references,
not the entire research history. A new goal does not clear an existing
conversation, and a fresh context can still carry large startup instructions,
tool catalogs and retrieved inputs.

## Code plus a retrospective

When the caller requests both, keep code acceptance and the later analysis
separate in the same intent: code judgment uses acceptance and checks, the
retrospective uses the known outcome, and both stay required.

## Exact intent identity

Use runtime-derived source identity and digest. If conversation intent needs
an exact snapshot, the `ao` CLI (not shipped with the plugin) writes it to
caller-selected protected external non-Git storage:
`ao provenance snapshot-intent --source - --evidence-root <explicit-root>`.
Without `ao` or a routed root, say that no exact snapshot was taken and keep
the intent in the conversation or tracker; never write a workspace copy or a
second planning artifact. Preserve legacy proof.

## Sources

Decision pointers and coarse future work adapt ideas from Matt Pocock's
[Wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md);
complete slices and compatibility migrations adapt
[To Tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md).
AgentOps keeps the caller's existing intent and native work authority.
