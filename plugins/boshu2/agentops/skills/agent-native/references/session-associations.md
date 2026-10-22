# Session associations

AgentOps work and runtime identity guidance.

## Work-to-session associations

The caller passes work identity at dispatch/start before execution can fail,
and records the dispatch reference in native work comments/metadata or existing
runtime facts. At startup, record observed identity in that caller-owned channel
before substantive work, independently of final handoff. These are versioned
facts under their source owners, not a new AO association database, lifecycle,
packet schema or permanent writer. Core skills return facts; tracker mutation
requires the caller's authority. No memory/evidence file belongs in a consumer
checkout by default; requested CDLC evidence uses owner-selected protected
external non-Git storage.

Keep these facts distinct in the native record or its permitted evidence:

| Fact | Required distinction |
|---|---|
| Source work | Backend/store identity, database/project identity where available, native work ID and permitted source revision/intent locator; a bead ID alone or workspace basename is not globally unique. |
| Execution | Selected runtime and requested model/ID separately from actual observed model/session/context IDs; absent observations are explicit unknowns, never synthetic UUIDs. |
| Relations | Native parent, dispatch controller and resume predecessor are separate links, each with its observation source. Record the selected runtime's actual resume identity even when it reuses a session ID. Unknown is distinct from an observed absence of parent. |
| Provenance | Who or which runtime observed the fact, when, through which native operation/record, and its permitted locator. Caller-supplied facts remain labeled as supplied; do not upgrade inference to observation. |
| Discovery | Exact query/filters/limits, index freshness, observed cutoff and missing/unavailable/restricted sources. CASS results discover candidates, not every episode member. |
| Source extent | Permitted native locator plus available frozen byte length/bounds and digest, with the cutoff and digest scope. Unknown or unreadable extent/digest remains unknown, never zero or a hash of an excerpt represented as the full source. |
| Work span | Only the source interval supported by explicit work/start/switch observations. Where frozen byte offsets are available use half-open `[start, end)` ranges tied to that source identity/digest. A search line is a locator, not an inferred byte boundary. |

For a child, pass its work identity before launch, then record the child's
observed ID and independently supported parent link at startup. For resume,
retain the predecessor reference and add the observed resume relation; a
requested resume ID does not prove a resumed execution. Workspace adjacency,
matching task titles, filenames and guessed line numbers establish neither
identity nor parentage. A native session can cover multiple work items: record
only supported spans for each, preserve unrelated and unassigned spans, and
leave an unknown end unknown until an observation supports it. Never assign a
whole session to a work item because one hit names that work.

If launch, startup observation or native recording fails, retain the caller's
pre-execution record, available bounded failure facts and explicit unknowns;
report any recording gap. Recovery reopens permitted startup/native sources
without depending on a final handoff, preserving earlier failures/unknowns as
history when later observations resolve them. Do not fill gaps with invented
IDs, inferred edges or unrelated source spans.

All metadata follows source-owner and recipient/model/destination authorization,
including locators, native comments, filenames and diagnostics. BD/Dolt is
versioned and is not a secret store. Use permitted opaque locators rather than
restricted paths/excerpts or credentials; opacity grants no clearance. Check
access before resolving a locator, never retrieve denied bytes and redact later.

Association is not coverage: CASS discovery, `view`/`expand` windows and tool-call
mining do not prove full prose/outcome reading. Preserve missing sources and
unknown lengths. Frozen bounds/digests identify available evidence; they do not
prove bytes were emitted, delivered to the host or semantically processed.
Head/tail excerpts leave the middle unread; new tails or children belong to a
later observation, not a rewritten completed denominator. T09 owns the later
coverage verifier; no coverage command or acceptance claim is introduced here.

For byte-preserving reads of explicitly authorized sources, follow
[bounded raw source reads](RAW_SOURCE_READS.md). The source reader checks native
policy before opening bytes and reports frozen prefix/span digests, reversible
content and delivery limits; emitted stdout does not establish full reading.

