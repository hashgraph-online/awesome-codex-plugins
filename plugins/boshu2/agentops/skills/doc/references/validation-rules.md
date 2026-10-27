# Documentation validation techniques

Choose checks for the accepted document and audience. These techniques do not
expand the [Doc contract](../SKILL.md) into a repository-wide audit, fixed
coverage target, required section list or separate report.

## State what was examined

| Question | Evidence | Limit |
|---|---|---|
| Are selected entities documented? | Inspect each enumerated entity and its associated documentation against a declared criterion. | A ratio needs numerator and denominator from that same checked set; unknown or unexamined status precludes a percentage. |
| Do code references exist? | Resolve the named symbols or commands in current source. | Existence alone does not verify the prose's behavior claims. |
| Do links resolve? | Check links in the selected documents with the repository's validator or direct inspection. After moving a document, also re-resolve the relative links inside it; their base moved with it. | A scoped link check says nothing about unread documents. |
| Do cited commits survive? | Resolve each cited hash and confirm a long-lived upstream branch or a release tag contains it. | In a document meant to outlive the branch, a hash that exists only locally or on a branch that a squash merge will discard does not survive; cite the pull request instead. A handoff keeps the exact commit and marks it unpushed or machine-local. |
| Do cited paths exist? | Check each path in the revision the document states. | A path the documented change removed is historical, not broken; give the revision where it existed. |
| Is drafting scaffold gone? | Search for unfilled template tokens, placeholder headings and draft-only labels or numbering. | A placeholder shown on purpose, as in a template example, is not scaffold. |
| Is required metadata present? | Check the fields required by the document's actual consumer. | No universal frontmatter target applies. |
| Are configuration keys explained? | Compare the selected keys with source and the requested reference. | File presence is not key or entity coverage. |

Use caller-supplied acceptance thresholds when they exist. Otherwise report
observed checks and gaps without inventing a percentage target. For entity
discovery and status handling, see [code/API guidance](default-mode.md).

## Informational documents

Use an existing validator where available, or inspect the selected files
directly. This skill's `scripts/audit-oss-docs.sh`, run with the audited
repository as the working directory (see [OSS pack](oss-pack.md#audit-and-project-type)),
checks doc-file presence for an OSS pack; its counts do not measure API
entities, link validity or semantic accuracy. No standalone link/orphan validator ships with this skill.

For a requested broader audit, define its file set and check relevant items:

- Broken links in that set.
- Documents absent from an index that is intended to enumerate them.
- Missing index entries required by the navigation contract.
- Machine-specific paths that would mislead the intended reader.

An unlinked page is not automatically obsolete. Report the finding and source;
do not delete it or create a new validator without authorization. For a scoped
edit, check its affected links and state what was not checked.

## Coding documents

Use sections appropriate to the document's purpose. A code-map may need an
overview, component entry points, inputs/outputs, data flow and dependencies.
An API page may need parameters, returns, errors and usage. Configuration,
metrics, tests, state diagrams, deployment status and lessons belong only when
they answer the requested question or an existing template requires them.

### Code references

- Resolve function, class, type and command names in the stated source revision.
- Use semantic names, such as `authenticate()` or `UserService`, with paths when
  needed to disambiguate them.
- Prefer stable symbol references for maintained navigation. Exact line
  references are useful for revision-bound findings; state the revision so they
  do not imply permanence.

## Operational documents

An installation or chart guide may need an overview, quick start, selected
configuration values, dependencies, environment overrides and troubleshooting.
Use only the sections the requested guide needs. For a full values reference,
enumerate the selected keys and verify descriptions, types and defaults against
the same source. Do not infer full coverage from a few documented keys.

Commands and deployment claims require current evidence from the appropriate
source. Repository access alone does not authorize querying a cluster or using
credentials. If the authorized source is unavailable, label the status unknown
or stated but unverified and name the missing check.

## Semantic validation

Formatting checks establish structure; semantic checks establish whether the
document's claims follow its sources. Resolve each material claim to its
existing authority rather than creating a new ground-truth file or duplicating
another owner's state.

| Claim | Check |
|---|---|
| An API accepts or returns a value | Inspect its implementation, callers or executable checks. |
| A feature is deployed or running | Read authorized native deployment state; a declaration or template alone is insufficient. |
| A configuration value is the default | Compare with the versioned configuration source. |
| A status observation is current | State when and against which source it was observed; use an existing freshness requirement if one applies. |
| A change landed, merged or is fixed | Read through an authorized interface whether the pull request merged with the default branch as its base, or check that the upstream default branch reaches the fix; where squash or rebase broke ancestry, compare content (see [Research's claimed-state audit](../../research/SKILL.md#claimed-state-audit)). A local checkout may predate the merge. When neither is possible, date the claim and say it was not verified. |

For status prose, distinguish observed, planned and unverified facts. A date
records an observation, not a universal validity period. There is no generic
`--verify-claims` command or cluster check added by this reference.

## Reporting, when requested

Return scoped check results and gaps with the changed paths. A separate coverage
report is optional and follows the caller's selected destination and the Doc
contract's evidence rules. A useful requested report can state:

```text
Scope: <selected documents/entities and source revision>
Criterion: <what counted as documented or valid>
Checked: <source/document references and observed results>
Gaps: <verified missing or inaccurate documentation>
Unknown or unexamined: <items and reasons>
Coverage: <checked documented entities / same enumerated entity set, if established>
```

Do not populate counts or results from an example. Sampling supports findings
about the sample; an exhaustive claim requires examining the declared whole
set. Preserve the distinction between not checked and a verified defect.
