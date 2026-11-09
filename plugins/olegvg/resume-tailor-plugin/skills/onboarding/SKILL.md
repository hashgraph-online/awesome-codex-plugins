---
name: onboarding
description: Use when creating or updating a candidate master profile from resumes, career notes or supplied facts, organizing career-source provenance, or resolving profile identity, conflicts and disclosure preferences.
---

# Candidate Profile Onboarding

Build or update the requested career data store from supplied evidence. Preserve factual uncertainty and user preferences so later applications can select truthful, permitted claims. This skill stands alone; it does not require resume-tailor, a particular runtime, or export tooling. Tailoring or formatting alone does not trigger profile creation.

Read [profile-contract.md](references/profile-contract.md) before extracting or updating. It defines location, identity, sources, career facts, optional sections, visibility, durable preferences, scoped decisions and unresolved facts. Accept an existing schema rather than migrating it for compliance.

## Extract before asking

1. **Resolve the target and scope.** Use the explicitly supplied profile path first. Otherwise use an unambiguous established profile in the chosen workspace. New profiles default to `resume/<candidate-label>/master-profile.md` there; honor a different requested path. A neutral collision-free file label is not a person's name. Keep candidate data out of installed plugin assets and caches. For an update, read the relevant existing profile before editing.
2. **Read the supplied evidence.** Extract supported identity, contacts, career chronology, employment capacity, contribution and outcomes into source-linked facts. Available read-only tools may read supplied files or URLs; if extraction fails, state what is missing and continue with readable material. Preserve source dates separately from employment/implementation dates. Do not search unrelated candidate records or private session history.
3. **Bind identity and qualify claims.** Keep distinct candidates' extracts separate. If records may describe different people, ask which record/person is intended before merging or persisting; recency and an explicit filename do not resolve identity. Preserve measured versus estimated/target/test values, personal versus team/advisory/agent-assisted contribution, title, skills recency and approved public wording. Do not fill a missing name, month, metric, certificate or outcome by inference.
4. **Ask only consequential follow-ups.** Review what extraction already answered. Clarify material identity, conflicts, missing truth, public-name/NDA permission or target-path ambiguity. Do not require a biography questionnaire, quantified achievements or a language/market pair. Sparse records can yield a useful profile with unknowns. A direct human correction becomes the current fact with its source; retain superseded context and any separate uncertainty it leaves unresolved.
5. **Preserve preference scope.** Separate durable disclosure restrictions and established preferences from one-output/application decisions. Retain existing visibility/variant definitions. A one-PDF B2 description may narrow supported C1 but does not change the canonical level; no override establishes unsupported expertise. Do not treat role inclusion as platform publication visibility.
6. **Complete the requested artifact.** For an authorized profile creation/update, write only supported facts, provenance and relevant restrictions/uncertainties. Preserve unrelated existing content and schema. A chat-only request stays in chat with no files or profile mutation. Neither task implies a resume, cover letter, export, application submission or platform update.

## Review and return

Check candidate/source binding, date precision, evidence qualifications, public versus private wording, and durable versus scoped decisions. Ensure unrelated existing content remains intact. Do not mark a self-reported fact independently verified. Summarize the profile changes, material unresolved questions and the saved absolute path when applicable; for chat-only work return the requested content directly. Keep internal aliases and confidential details out of the public-facing summary. No ATS score or mandatory numerical evidence is part of onboarding.
