# Curate / qualify / retire

Maintain caller-selected reviewed Markdown topic pages in project `.context/`
or an external bundle. BD remains
the work/status/handoff owner, Git the content-history owner, and native/CASS
systems the episode owner. Existing docs, ADRs and code retain their declared
authority. Link those owners; do not duplicate policy, build a second tracker
or copy raw history. A small authored `README.md` topic map is a navigation aid,
not a work/status index; keep it only as useful to the selected pages.
This lean operation accepts public or already-cleared inputs only; it supplies
no native isolation for restricted sources.

1. Find the existing topic page and inspect its current claims and review
   evidence before editing. Reuse/update it instead of a lesson-per-session
   file. If no relevant page exists and the caller selected a destination,
   create one topic page only for a concrete reusable claim and consumer.
   Do not scaffold empty directories, import private material or create a store
   automatically. Ordinary filesystem reads of cleared project pages need
   neither BD nor AO; native source operations retain their own requirements.
2. Draft the smallest change in protected external non-Git staging. Each entry
   gives applicability, action, support, limits and invalidation. Cite exact
   source identities sufficient to inspect evidence without copying private
   material. Keep unrelated claims and useful rare constraints.
3. Qualify a single incident narrowly. General methods require stronger support
   and later reapplication evidence; contradiction may narrow or remove a rule.
   Retire when invalidated or unsupported after examination, not merely old.
   Preserve withdrawal reason, provenance and unique evidence in the existing
   page/history under owner policy. No blind TTL or deletion sweep.
4. Have a fresh authorized author-distinct context review exact factual support
   and exact destination disclosure before any Git object, index, stash or
   import. Include intended paths and metadata in the reviewed payload. A
   changed claim or destination requires matching review; the author cannot
   approve their own knowledge. Public input does not waive factual review.
5. Apply only the approved content to the caller-selected destination under
   existing Git authority. Read back exact bytes and confirm that citations
   and withdrawal facts remain available. Do not commit/push unless authorized.
   If review, routing or permission is missing, return the supported gap with
   the protected draft; do not invent an alternate memory destination. Project
   placement does not move drafts or review proof into the checkout. The optional
   `ao config context` route supports an explicitly bound canonical direct
   `<consumer>/.context` or an external bundle; it requires native BD and retains
   policy and identity bindings. A resolved route does not approve page admission.

Ordinary Markdown is sufficient. If the caller selects the existing OKF profile,
use [its profile](learn/okf-page-profile.md) and
`ao provenance check-okf --file <topic.md>` for structure. This checks no factual
support, disclosure, isolation, review or usefulness; the profile is optional.

Return the changed claim and why, its limits and exact review evidence, or
no-change. Curation can remove rules. It cannot alter earlier product verdicts
or claim benefit until later task evidence shows helpful reuse. A page admitted
for one owner/destination is not authorized for another.
