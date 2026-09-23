# Relation Authoring — Check the Claim Before the Edge

Runtime procedure for skills and agents that create or review relations.
Load this file before relation work. MCP instructions own the vocabulary,
direction conventions, endpoint validation, and mutation tools. This procedure
owns the evidence for choosing a relation. It adds no manifest fields.

## Find candidates

1. Start with the task's inputs, consumed contracts, and explicit document references.
2. Search for the named subjects and contract owners beyond the current directory.
3. Treat nearby documents, shared tags, and documents created together as candidates only.
4. Read both candidate documents before deciding whether their claims warrant an edge.
5. Retrieve complete bodies when a search result is truncated.

Reuse complete bodies already read during this task unless they changed.

A workflow's relation table supplies candidates and intended roles, not proof
that every available pair has a relation. Preserve required traceability when
the documents establish those roles. Do not use alphabetical neighbours as the
only candidate set. Do not compare every document pair to fill the graph.

## Check one candidate

1. Identify the source statement and the target statement that justify the proposed relation.
2. Choose the type and direction using the connected engine's conventions.
3. State why a reader needs this link for a named task or change review.
4. Check whether the claim describes a current constraint or a historical relationship.
5. Read existing relations for the pair before proposing a mutation.

For `related`, name the joint reading task. A shared topic alone does not
establish that task. An explicit index can link to the documents it indexes:
the index's scope supplies the navigation reason. A body reference is evidence
to inspect, not an instruction to copy every mention into the graph.

For other types, identify the specific requirement, prerequisite, extension,
support, dispute, or replacement. Do not use `related` to hide uncertainty about
the type. Do not infer a direct claim from a path through other documents.

When an exact edge exists, keep it without another write. When a more specific
edge already provides the same reading path, add `related` only for a distinct
claim. Incoming and outgoing reads already expose neighbours at both ends:
do not add a reverse `related` merely for navigation. Stored relations remain
directed; this procedure does not normalize or remove existing reverse edges.

## Choose an outcome

| Outcome | Evidence | Action |
|---|---|---|
| add | Both statements establish the type, direction, and reading purpose | Call `add_relation` within the authorized workflow |
| keep | The supported relation already exists | Make no relation write |
| no_relation | The read establishes no claim beyond topic, location, or shared creation | Leave the pair unlinked |
| review | Missing text, ambiguous direction, or unclear historical scope prevents a decision | Report the unresolved claim; make no speculative relation write |

Use `no_relation` for an unlinked pair. If an existing edge lacks support,
report it for review instead of silently removing it.

Any document type can remain unlinked when no supported relation exists.
Do not add an edge to lower the count of unlinked documents. Do not impose a maximum degree
or a target edge count: several independently justified dependencies can remain.

If a gate requires a specific traceability edge, `no_relation` or `review`
does not satisfy that gate. Resolve the missing input or report the unmet
check under the gate contract. Do not replace the required edge with `related`.

In the workflow's result, explain added edges and unresolved candidates with
the source and target statement locations and one sentence of reasoning.
Do not create a separate document for every candidate. These explanations are
review evidence, not new parameters to `add_relation`.

## Review existing relations

1. After a meaningful content or status change, inspect the changed document's incident relations.
2. Apply the same claim check to retained, missing, and potentially redundant relations.
3. Separate confirmed defects from candidates whose meaning needs review.
4. Report proposed removals or type changes with their statement evidence.
5. Keep audit-only work read-only.

Counts identify candidates, not semantic defects. A document without edges can
be complete. A dense group can contain useful dependencies. Multiple relation
types can express different claims between the same pair.

A rejected target can remain historical context or a superseded record. A
mixed-type cycle can connect a proposal, its decision, and a later living spec.
Inspect that scope before calling either case erroneous. Do not remove edges
solely for status, degree, reverse direction, or acyclicity. Follow the active
workflow's mutation authority; preserve its stricter rules for contradictions.
