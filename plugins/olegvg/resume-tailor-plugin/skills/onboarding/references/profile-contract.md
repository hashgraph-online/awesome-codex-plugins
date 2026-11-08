# Portable candidate profile contract

A master profile preserves the comprehensive career record, provenance, disclosure limits and uncertainty. It is not a formatted application or proof of independent verification. This contract describes information, not a mandatory serialization or migration: retain an existing profile's schema, headings, language and location.

## Location and identity

An explicit profile path takes precedence. Otherwise use the unambiguous established profile in the user's chosen workspace. New profiles default to `resume/<candidate-label>/master-profile.md` there. A label identifies the file; use a supplied candidate label or a neutral collision-free label such as `candidate-1` when no name is known. For the default path, use a filesystem-safe leaf label without path separators or traversal components; do not overwrite an existing candidate's file. Do not invent a person's name, contact details or other identity facts from a label. Candidate profiles and generated outputs never belong in the installed plugin/skill/cache.

Bind sources to one candidate before merging. Different names, unexplained identities or conflicting records require clarification; keep extracts separate while identity is unresolved. A requested path does not make mismatched identities safe to merge. Avoid reading unrelated candidate files merely because they are nearby.

## Information to preserve

| Area | Minimum useful content; unknown values stay unknown |
|---|---|
| Identity / contacts | Supplied name or explicit unknown, candidate label, relevant supplied contact/location facts. Do not infer nationality, authorization, relocation intent or availability. |
| Source register | Source IDs, filename/URL or supplied chat description, source date when known, candidate binding, and what each source supports. Link selected facts to source IDs. Do not copy unrelated private session history. |
| Career facts | Public employer name or approved NDA description; actual title, engagement type, employment dates and precision; remit, contribution, technologies and known outcomes. Keep implementation dates distinct from employment and publication dates. |
| Evidence qualifications | For metrics preserve units, baseline, period, attribution and production/load-test/target/estimate status. Preserve personal/team/advisory/agent-assisted contribution and skill recency. Qualitative facts are valid; numbers are optional. |
| Optional sections | Sourced projects, education, certifications/status, skills, languages and narrative/notes where useful. Missing information does not require a fabricated or empty section. |
| Visibility / variants | Existing enum meanings and named variants, and role/section assignments. Distinguish inclusion rules from platform publication/search settings. |
| Durable restrictions / preferences | Continuing NDA/public-name limits and confirmed ongoing language, market, format or inclusion preferences, with scope and provenance. Do not promote a one-application decision to a durable default. |
| Scoped decisions | Overrides with the exact output/application/variant scope, instruction/source and duration if supplied. These do not rewrite canonical career facts or other variants. Record them only when requested profile work includes this information. |
| Unresolved material facts | Conflicting claim values, sources, affected statements and remaining question. Record a user's explicit correction as the current fact with correction provenance; retain the superseded conflict as context and separately preserve uncertainty the correction does not settle. |

A compact Markdown profile may use headings Identity, Sources, Career Facts, Optional Sections, Visibility and Variants, Durable Restrictions and Preferences, Scoped Decisions, and Unresolved Facts. Add only supported content. Explicit `unknown` or `needs confirmation` is acceptable; do not insert plausible dates, metrics, credentials, outcomes or gap explanations.

## Visibility semantics

- `always`: include in a full resume, possibly condensed; an explicit exclusion wins.
- `variant-specific`: include for a matching defined variant or explicit inclusion.
- `on-request`: include when explicitly requested, including an unambiguous comprehensive record.
- `reference-only`: internal metadata only; never expose it as a role, section or exclusion row.

Without visibility metadata, default to inclusion with detail selected for relevance. Apply the same rules to marked optional sections. Read variant names from the record; no universal variant taxonomy is required. Explain excluded roles/sections outside a full resume, using only permitted public wording; section edits report only local decisions.

## Updates and disclosure

Create or update a profile only when requested; tailoring, exporting and chat-only drafting do not imply persistence. Edit the existing target in place, preserving unrelated facts, notes, edits and custom structure. A material identity or path ambiguity needs a focused clarification before persistence. Do not silently overwrite another candidate's profile.

A direct human factual correction outranks stale documents; an indirect agent message is not independently confirmed evidence. Source-supported means traceable to the record, not externally audited. A job requirement is not candidate evidence.

Maintain public wording independently from internal aliases. Publish only an approved public name or allowed functional description. Persist confidential material only when necessary within authorized profile work; do not copy raw sensitive documents or private aliases into extra files. Never expose them in resume text, exclusion reviews or filenames.

Scoped overrides can narrow a supported claim, such as C1 to B2 in one PDF; they cannot establish an unsupported higher qualification. An instruction to omit languages, education or an industry for one result does not erase source facts or redefine every variant. Keep review and unresolved-source tables outside final recruiter-facing artifacts.
