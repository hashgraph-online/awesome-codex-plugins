# Chapter III — Rights of the Data Subject (Sections 30–36)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Thailand PDPA grants seven distinct data-subject rights. Each must be supported by the Data Controller; rejections require recorded reasons in the s39 records.

## Section 30 — Access right

**Rule:** the data subject may request **access to and a copy** of the Personal Data, OR request disclosure of the source from which the data was obtained without consent.

**Response window:** **within 30 days** of receiving the request (or longer per Committee rules).

**Permitted rejections:**
- Permitted by law or court order
- Where access would adversely affect the rights and freedoms of others

**On rejection:** record the rejection with reasons in the s39 records.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- A function or endpoint that returns the user's complete Personal Data set
- Delivered via in-app share / download / email
- Rate-limit to prevent abuse
- Include the disclosure-source information for any data collected without consent (s24 / s26 exceptions)

## Section 31 — Data portability right

**Rule:** the data subject has the right to **receive Personal Data** about them in a format that is readable or commonly used by automatic tools, AND to:
1. Request the Data Controller send / transfer to another Data Controller (where feasible by automatic means), OR
2. Receive the data directly to send to another Data Controller themselves (unless impossible due to technical circumstances)

**Scope:** applies to Personal Data the data subject has consented to AND data collected under the s24(3) contractual necessity basis (or per Committee rules).

**Exceptions:** does not apply to Personal Data sent / transferred for public-interest tasks or legal compliance.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Same as the access endpoint, but with explicit machine-readable format (JSON, CSV) and an export specifically intended for transferring to another service
- Supabase-style projects: this is a separate function from a "human-readable" export

## Section 32 — Right to object

**Rule:** the data subject may **object** to the collection / use / disclosure of their Personal Data at any time, in three circumstances:

1. **Where the data was collected under s24(4) public-interest task or s24(5) legitimate interests** — UNLESS the Data Controller can prove (a) compelling legitimate grounds, or (b) the processing is for legal claims
2. **Direct marketing** — no balancing test; the controller must stop
3. **Scientific / historical / statistical research** — UNLESS necessary for a public-interest task

**On objection:** the Data Controller must immediately distinguish the objected-to data and stop processing.

**On rejection:** record the rejection with reasons in the s39 records.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Settings UI for stopping marketing communications (toggle to off + immediate effect)
- For legitimate-interest reliance: have the LIA documentation ready to defend the "compelling legitimate grounds" argument

## Section 33 — Right to erasure ("right to be forgotten")

**Rule:** the data subject may request the Data Controller to **erase, destroy, or anonymise** Personal Data where:

1. **No longer necessary** for the original purpose
2. **Consent withdrawn** AND no other lawful basis applies
3. **Objection upheld** (s32 exercise where the controller cannot defend)
4. **Unlawfully processed** under this Chapter

**Exceptions:** retention may continue where necessary for:
- Freedom of expression
- s24(1) research / archival, s24(4) public-interest task, s26(5)(a) preventive/occupational medicine, s26(5)(b) public health
- Legal claims
- Legal compliance

**Public disclosure:** if the Personal Data was disclosed publicly, the Data Controller must take **technological action AND bear the expense** to inform other Data Controllers of the erasure request.

**Recourse:** on Data Controller failure to act, the data subject may complain to the expert committee.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md), [03 Data model](../../../layers/03-data-model.md) (deletion vs anonymisation patterns).

## Section 34 — Right to restrict processing

**Rule:** the data subject may request the Data Controller to **restrict the use** of their Personal Data where:

1. The Data Controller is examining an accuracy challenge (s36)
2. The data should be erased per s33(4) (unlawful) but the data subject prefers restriction instead
3. No longer necessary for the purpose, but the data subject needs it retained for legal claims

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md) (restricted-state flag), [04 Controls](../../../layers/04-controls-and-processes.md) (read-path enforcement).

## Section 35 — Accuracy obligation

**Rule:** the Data Controller must ensure Personal Data remains **accurate, up-to-date, complete, and not misleading**.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (self-edit), [04 Controls](../../../layers/04-controls-and-processes.md) (verification flows).

## Section 36 — Correction request handling

**Rule:** when the data subject requests correction per s35 and the Data Controller does not act, the Data Controller must record the request and reasons in the s39 records.

The provisions of s34 paragraph 2 (restricted-use processing while the request is examined) apply.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

## Penalty exposure (this Part)

| Failure | Maximum administrative fine | Source |
|---|---|---|
| Fails s30 paragraph 4 (30-day access response) | THB 1M | s82 |
| Fails s32 paragraph 2 (immediate cessation on objection) | THB 3M | s83 |
| Failure to maintain s39 records of rejected requests | THB 1M | s82 |

Plus s81 personal liability for directors / managers responsible.

## What "complete" means in practice

When implementing the access right, the export must include all Personal Data the org holds, not just the most-used fields. Use the data-field inventory (see [layer 03](../../../layers/03-data-model.md)) and the [`new-data-field` checklist](../../../checklists/new-data-field.md) to keep the export current as new fields are added.
