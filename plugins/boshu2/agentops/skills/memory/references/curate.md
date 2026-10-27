# Curate / qualify / retire

Maintain caller-selected reviewed Markdown topic pages in project `.context/`
or an external bundle under Memory's
[one authority per fact](../SKILL.md#one-authority-per-fact) and
[access rules](../SKILL.md#access-storage-and-honest-limits): link owners, do
not duplicate policy, build a second tracker or copy raw history. A small
authored `README.md` topic map is a navigation aid, not a work/status index;
keep it only as useful to the selected pages.

1. Find the existing topic page and inspect its current claims before editing,
   with any review verdict for them in a store the caller named; if there is
   none, treat those claims as unreviewed. Reuse/update it instead of a
   lesson-per-session file. If no relevant page exists and the caller selected
   a destination, create one topic page only for a concrete reusable claim and
   consumer.
   Do not scaffold empty directories, import private material or create a store
   automatically. Ordinary filesystem reads of cleared project pages need
   neither BD nor AO; native source operations retain their own requirements.
2. Draft the smallest change inline in your reply, or in storage outside Git
   that the caller named; never in the repository before review. Each entry
   gives applicability, action, support, limits and invalidation. Cite exact
   source identities sufficient to inspect evidence without copying private
   material. Keep unrelated claims and useful rare constraints.
3. Qualify a single incident narrowly. General methods require stronger support
   and later reapplication evidence; contradiction may narrow or remove a rule.
   For consolidation, test each claim against the proposed surviving source:
   cite the exact passage that preserves its reasoning, not just a related path
   or topic. Keep investigation results, rejected alternatives and rare constraints
   that source does not explain; shorten duplicated explanation to a pointer.
   Accurate but duplicated content is not invalidated. If the survivor cannot
   be checked, retain the claim and name the gap. Retire when invalidated or
   unsupported after examination, not merely old. Preserve withdrawal reason,
   provenance and unique evidence in the existing page/history under owner
   policy. No blind TTL or deletion sweep.
4. Before rewriting or retiring an entry that current code contradicts,
   classify the difference. Fix a renamed path, symbol or link directly. A
   changed action needs evidence that the new action governs; otherwise qualify
   the entry and name the gap. A supported entry the code stopped honoring
   stays, reported as a possible regression. A deleted cited file shows the code
   moved, not that the problem left; while the problem remains, rewrite the
   entry for the current path. Report a conflict with an instruction file or
   runbook the page names by quoting both passages and the side current code
   follows, if either; do not edit that file here. Check an invalidation that
   lives outside the repository, such as an upstream issue or a tool version,
   through its own source and report the result and date. If it is met while
   the code still carries the workaround, keep the entry and recommend verifying
   the removal; an unmet or uncheckable condition decides nothing alone.
5. A change can make other entries wrong. Check its neighbours, not the whole
   store: entries it contradicts or supersedes, and pages, the `README.md` map
   or instruction files that cite the changed, merged, moved or retired entry.
   Resolve first any two entries in scope that give opposite actions for the
   same conditions; a newer entry that fully covers an older narrow one is a
   consolidation candidate. In the same draft, repoint plain pointers in pages
   and the map to the survivor, keep one map row per live topic, and make the
   corrections the evidence in hand supports. A page or entry that relies on a
   retired claim for support is narrowed to what remains, or the retirement
   stays a proposal that names it; such a dependency found late stops the
   retirement. For an instruction file that cites or relies on the entry,
   propose the repoint or narrowing and edit only with the caller's consent.
   Name a neighbour that needs new investigation as the narrowest follow-up,
   the page and then its topic; it never delays the new claim.
6. Have a fresh authorized author-distinct context review exact factual support
   and exact destination disclosure before any Git object, index, stash or
   import. Include intended paths and metadata in the reviewed payload. A
   changed claim or destination requires matching review; the author cannot
   approve their own knowledge. Public input does not waive factual review.
7. Apply only the approved content to the caller-selected destination under
   existing Git authority. Read back exact bytes and confirm that citations
   and withdrawal facts remain available. Do not commit/push unless authorized.
   If review, routing or permission is missing, return the supported gap with
   the draft inline; do not invent an alternate memory destination. Project
   placement does not move drafts or review proof into the checkout. A resolved
   `ao config context` route ([Find / recall](recall.md)) does not approve page
   admission.

Ordinary Markdown is sufficient. If the caller selects the existing OKF profile,
use [its profile](learn/okf-page-profile.md) and
`ao provenance check-okf --file <topic.md>` for structure. This checks no factual
support, disclosure, isolation, review or usefulness; the profile is optional.

After curating a project `.context/`, read the root instruction file or the
file such a stub only includes. If a fresh reader would not learn that the
store exists, where it is and when it helps, propose one informational line with
the concrete path in its closest section; an order to read it first makes agents
reread what they already search. Edit only with the caller's consent; never
create the file or point a checked-in file at an external bundle.

Return the changed claim and why, its limits and exact review evidence, any
reported regression, conflict or follow-up, or no-change. Curation can remove
rules; it cannot alter earlier verdicts or claim benefit (Memory rule 5). A page
admitted for one owner/destination is not authorized for another.
