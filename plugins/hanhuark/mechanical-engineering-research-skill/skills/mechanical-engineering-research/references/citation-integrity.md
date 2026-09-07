# Citation Integrity And Claim Verification

Use this reference for citation repair, bibliography audits, numeric-reference ordering, literature claims, permission captions, dataset/software citations, and manuscript restructuring.

## Evidence Rule

Use search results, snippets, AI summaries, and citation-manager records to locate sources. Use the primary paper, standard, dataset record, software release, patent record, or official page to support the claim.

Do not guess a reference identity or silently substitute a nearby source. Mark the citation unresolved when the source cannot be verified.

## Claim Ledger

For consequential quantitative, causal, novelty, safety, limitation, or comparative claims, record:

- claim text and manuscript location;
- intended source and exact locator, such as page, equation, table, figure, or dataset field;
- evidence class and whether the value was measured, simulated, derived, or digitized;
- operating regime, geometry, material/fluid, and applicability limits;
- verification state, caveat, and date checked.

Use [claim-evidence-ledger.csv](../assets/templates/claim-evidence-ledger.csv) when a formal ledger is useful.

## Reference Verification

Verify, as applicable:

1. Title, first author, author order, year, venue, volume, pages or article number, DOI, and URL.
2. Publication state: peer-reviewed article, accepted manuscript, preprint, dataset, software release, report, standard, or web resource.
3. Correction, retraction, withdrawal, version, and current standard status.
4. Whether the source supports the exact sentence rather than only the general topic.
5. Whether the source regime and definitions are transferable to the present system.

Use `FirstAuthor et al.` when naming a study in prose. Group citations when several sources support one synthesis. Place citations adjacent to each named study when their methods or conclusions are contrasted.

## Numeric Citation Audit

After restructuring a numeric-citation manuscript:

1. Compile from the active source entry point.
2. Check unresolved and multiply defined labels or citations in the log.
3. List citation keys in order of first appearance.
4. Confirm that the generated bibliography follows the intended numeric style.
5. Match each high-risk in-text citation to the intended bibliography entry semantically.
6. Recheck figure-permission captions, tables, software, datasets, preprints, data-availability statements, and references moved with text.
7. Flag uncited bibliography entries and cited keys missing from the bibliography.

Do not repair a numeric offset by deleting bibliography entries unless those entries are genuinely unused or erroneous. In normal BibTeX workflows, correct citation keys and regenerate the bibliography.

Run `scripts/audit_latex_project.py` for mechanical checks. Treat its output as a preflight; it cannot determine whether a source truly supports a scientific claim.

## Literature Search Safeguards

- Start from seminal and representative papers, then use backward and forward citation snowballing.
- Search author and laboratory pages when a research group is central, but verify final metadata through primary records.
- Search repositories and archives when software or data are part of the question.
- Record why a search stopped and which source families remain incomplete.
- State whether the review is narrative, scoping, systematic, or taxonomy-driven. Do not imply PRISMA-level completeness without a documented systematic protocol.

## Quantitative Literature Data

For values digitized from plots, record the source figure, axes, units, digitization method, transformations, and extraction uncertainty. Preserve the original and converted values. Do not mix data with different definitions or system boundaries in one comparison without an explicit reconciliation.
