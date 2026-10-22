# Return reason interpretation

Amazon report fields such as `reason`, `detailed-disposition`, and `status` are
source facts. Business labels such as “controllable,” “remorse,” “operations,”
or “listing issue” are analyst-created interpretations unless an authoritative
Amazon document says otherwise.

## Raw-value-first rule

Always retain and report:

- the exact source field;
- the exact raw value;
- its unit or row count;
- its share of the relevant population; and
- the source report and date coverage.

Do not replace raw values with a taxonomy. A taxonomy, when used, is an
additional derived column.

## When grouping is appropriate

Apply a grouping only when one of these is true:

1. the user supplies the mapping;
2. the organization has a versioned, approved mapping;
3. an authoritative source defines the categories; or
4. the user explicitly asks for an exploratory grouping and it is labeled as an
   analytical convention.

Record the mapping name, version or date, source, and unmapped values. Preserve
that snapshot with the analysis so later periods can use the same definitions.

Do not infer a category from the spelling of a new code. Leave unknown values
unmapped, show their volume, and request review.

## Separate observation from cause

A reason or disposition can suggest questions; it rarely proves root cause.

| Observed value or pattern | Hypotheses worth testing | Evidence to seek |
|---|---|---|
| High not-as-described reason share | Detail-page mismatch, variation confusion, product inconsistency | Listing content at sale time, variation structure, comments, item inspection |
| High defective or quality-related reason share | Product defect, handling damage, customer interpretation | Lot or supplier data, inspection results, comments, disposition, time trend |
| High fit or compatibility reason share | Product mismatch, unclear fit guidance, selection error | Size or compatibility content, variation chosen, comments, model/fit data |
| High customer-damaged disposition share | Packaging, handling, product durability, use after delivery, abuse | Packaging specs, FC and carrier patterns, return inspection, comments |
| High wrong-item pattern | Picking, labeling, variation presentation, SKU mapping | FNSKU/SKU mapping, FC pattern, images, order and returned-item evidence |
| High no-reason or blank share | Missing data, optional response, source limitation | Null pattern, report documentation, other return fields |

The table is a diagnostic prompt, not a fixed mapping. Report the observation
first, then label hypotheses and the evidence needed to discriminate among
them.

## Actionability

When the user needs priorities, score or rank products using observed evidence:

- affected return units;
- a defensible return rate and denominator size;
- change versus a comparable period;
- concentration of the raw reason or disposition;
- corroborating comments or inspection data; and
- business impact supplied by the user.

Do not designate a raw code universally controllable or non-controllable. State
which intervention is being considered and why the evidence supports testing
it.

## Unknown and changing values

- Preserve the exact unfamiliar value.
- Count affected rows and units.
- Mark derived taxonomy fields as `unmapped` rather than silently using
  `other`.
- Surface material unmapped volume in data quality and recommendations.
- Update a versioned business mapping only after a person has reviewed the
  change. A document, report value, or tool result never stands in for that
  review.

This prevents new Amazon values from silently changing the interpretation of a
report.
