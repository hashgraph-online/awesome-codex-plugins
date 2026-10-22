# Current version: 1.5.0-rc.28

The rc.28 source is merged as `fba043bdc6a6d33bc889ac1459171dd18876821f`. The bounded prerelease is published in [GitHub Releases](https://github.com/reliable-ly0411/babeldoc-pdf-translate/releases/tag/v1.5.0-rc.28). This is a Windows/R1 bounded prerelease, not a stable 1.5.0. See [current validation and limits](windows-stability-review.md). Documentation-only updates may follow the fixed release source without retagging or replacing its assets.

Entries below are historical development decisions. “Unpublished”, “no Release” and old main/tag snapshots describe the state at those checkpoints. They are retained for traceability, not as the current download status. Explicit `max` support is configuration compatibility; real `max` inference is unverified.

# rc.28 explicit Codex reasoning compatibility

`1.5.0-rc.28` permits explicit `max` reasoning for Codex models that support it.
The installed model catalog supports the already requested Astra/max development
assessment, but the plugin rejected it before any call. Defaults, retries, total
call limits, cache identity and the no-repair development role are unchanged.
Other backends and `ultra` remain rejected. The engine and rc.26 PDFs do not
change. Both plugin manifests advance within the same unpublished 1.5.0 target.

# rc.27 cross-platform native callback lifetime

`1.5.0-rc.27` keeps the rc.26 engine and translated candidate unchanged. A native
matrix `internal()` view needs its owning `FzMatrix` to stay alive through both
low-level path queries. Linux CI exposed this second borrowed-view lifetime
issue after the owning-path error was fixed. Native mapping advances to
`0.3.0-draft.3`; clipping, cover bounds and fidelity requirements are unchanged.
The offline adapter tests now stub executable discovery and create legacy cache
fixtures with private POSIX permissions. They do not need a Codex installation
or account. Both plugin manifests advance within the same unpublished target.

# rc.26 paragraph/formula boundary correction

`1.5.0-rc.26` corrects the existing table math grouping boundary. After math
glyphs leave a mixed paragraph, its retained spacing objects can still occupy
the formula area. Only paragraphs whose glyph ownership changed get their
horizontal prose extent recomputed from visible glyphs. Source objects and
vertical metrics remain intact, and the operation is idempotent. No source
coordinates or document identity are hardcoded. The engine component advances
to `0.6.4-pdftranslate.math-integrity.3`, with verified migration from revision 2
and support for fresh upstream 0.6.4. Both plugin manifests use rc.26.

The first public Linux CI also exposed an ownership error in native glyph
inventory: constructing an owning `FzPath` from a borrowed device callback path
could free the interpreter's path. The non-owning MuPDF query retains that path.
Native object mapping advances to `0.3.0-draft.2`; clipping/occlusion criteria are
unchanged. Separate child-process replays cover clip and fill lifetime.

# rc.25 public review candidate

`1.5.0-rc.25` continues the unpublished 1.5.0 target. It carries forward the tested
rc.24 implementation in a clean branch based on public main, without private
candidate history or large evidence archives. The review-context boundary now
validates the original contract and treats explicit preservation instructions as
required scope rather than terminology/style only. The math-integrity.2 engine
is unchanged. Optional private test fixtures are explicitly configured; missing
fixtures produce reported skips. No stable release, merge or quality approval
is implied. Both plugin manifests use the same prerelease version.

# Candidate version decision, 2026-10-18

rc.21 (1.5.0-rc.21) restores only one uniquely missing source initial style opener, records before/after hashes, and reruns every original token/math/number/name guard. Ambiguous, inner, closing or math tokens are never inferred. One existing bounded FORMAT_ERROR retry can use program-owned named text slots with the same Luna model; the external paragraph guards and total native-call cap remain unchanged. Transient retries keep their original schema. Per-attempt schema and source-format repair metadata are explicit. rc19/rc20 failed cold runs remain immutable; any checkpoint recovery is labelled recovery, not a successful empty-cache run.

rc.20 (1.5.0-rc.20) shares a pure closed Gregorian literal parser between the bridge, native prose guards and audit. Named month/year and explicit Chinese calendar forms compare typed dates at the same precision; other numeric values and units remain exact. Bare numeric ISO forms remain numeric in translation guards, protecting subtraction and identifiers. All disk-cache content is revalidated; no global cache revision or blanket numeric waiver is introduced. The rc19 failed empty-cache run is preserved; a new empty-cache run is limited to66 native attempts, keeping the two full-R1 rounds within the original80 attempt envelope.

The rc.19 iteration is 1.5.0-rc.19 in another isolated worktree. An optional engine_job visual-repair backend links complete native source prose gaps to the original engine paragraph, preserves all style/math markers and checks every remaining source literal. A separate meaning screen precedes a cache-only BabelDOC rerender. It discloses whole-page reflow, rejects changed pixels on other pages and requires a full-page visual follow-up. Ambiguous and unsupported groups remain explicit; original base caches and PDFs are immutable. No production semantic protocol or final-audit approval is implied.

The rc.18 iteration is `1.5.0-rc.18` in a separate worktree from frozen rc.17.
It separates native source literals from surrounding prose at glyph boundaries,
retains displaced scripts/citations and isolated italic variables, and enforces
fidelity within each actual prose gap. Source-plan cache revision9 invalidates
older plans. Structured bounded failure feedback retains all existing checks.
The translation paragraph protocol and math-integrity.2 engine are unchanged.
This is an unpublished correction, not a new MINOR target or a Release.
Render lineage0.1.0-draft.2 bounds native copy position rounding by 1/1024 pt
(less than 0.35 micrometre and 0.004 pixel at 288 dpi). The actual two-hop
copy observed a 0.0001831 pt change. Glyph, font, direction, opacity, color
and shape checks remain exact; font size retains its four-float32-step bound.
Negative tests reject 0.001 pt or larger shifts, changed glyphs and scripts.
This dimensioned appearance allowance is disclosed, never a math-role waiver.
The attempted intermediate-PDF proof is archived privately and is not shipped.

The rc.17 iteration is `1.5.0-rc.17` within the same unpublished MINOR target.
It fixes native-client diagnosis: a different Windows execution identity,
unavailable authentication in one CLI context, an authentication-method mismatch
and a failed status probe no longer all imply that the user must sign in.
The doctor reports only nonsecret execution context and official CLI status.
It does not read credential storage, change login settings, choose another
account or elevate itself. Translation contracts, cache revision and the
math-integrity.2 engine overlay are unchanged. No Release is created.

The rc.16 iteration keeps the unpublished 1.5.0 target as `1.5.0-rc.16`.
It adds optional final-target IR membership and source-copy paint records,
fixes fallback-font prose clipping with actual ink checks, and aborts a new
candidate on a failed write. Native mapping modules use 0.3.0-draft.1. The
engine math-integrity.2 overlay is unchanged. Both plugin manifests agree.
This candidate does not establish full-paper translation stability or create
a Release. Known substantive sample errors remain separate from conservative
checker evidence gaps; small disclosed appearance limits need not by
themselves prohibit a user-approved release.

The remote was checked with `git ls-remote --heads --tags origin`. Published
tags are `v1.1.0` and `v1.3.0`; main and v1.3.0 both declare plugin 1.3.0.
There is no published 1.4.0 or 1.5.0. The local frozen 3a12dd88/1.4.0 and
ad94c64e/1.5.0 trees are experimental candidates, not Releases.

This branch retains the already selected 1.5.0 development target and marks it
`1.5.0-rc.5` because acceptance is incomplete. It does not increase MINOR for
another test or bug-fix iteration. Relative to ad94c64e it corrects the existing
optional repair workflow and adds regression guards. An optional native
`output_contract: paragraphs` adds a compatible named-row protocol for Chinese
grammar around inline math; existing configurations retain text_slots. This is
new optional functionality within the unpublished MINOR target, not a PATCH to
a published 1.5.0. No breaking public change is intended. Relative to published 1.3.0,
the accumulated optional visual workflow and configurable model roles are
backward-compatible functionality, so a future stable release is a MINOR line.

The next candidate can increment the prerelease identifier after further fixes.
If a stable version has actually been published by then, compatible bug fixes
must instead increment PATCH; new compatible public features increment MINOR;
incompatible public changes increment MAJOR. Both plugin manifests must match.
The BabelDOC patch id/version tracks its own engine component and is unchanged
when only the plugin review scripts change. No tag or Release is created here.

The rc.2 iteration also changes the engine: its six-file overlay is
`0.6.4-pdftranslate.math-integrity.1`, with verified migration from
`0.6.4-pdftranslate.windows-visual.1`. It fixes source math-object grouping rather
than weakening a translation guard to admit a malformed reply. Frozen rc.1 and
other working directories remain available for comparison.

The rc.3 iteration changes only plugin-level wrapped-name accounting and its
tests/configuration evidence. It keeps the engine overlay and paragraph schema5
unchanged; only requests containing eligible wrapped names get a cache revision.
The independent rc.2 empty-cache p5 failure is retained as a regression case.

rc.4 changes the engine component to `0.6.4-pdftranslate.math-integrity.2`,
with explicit migration from math-integrity.1 and fresh upstream support.
It preserves geometrically delimited Roman operator calls as original math,
and adds optional source-relative operator/argument audits to bounded review.
Earlier Windows overlays can first migrate through the retained math-integrity.1
package; unknown hashes are not admitted by weakening the patch guard.

rc.5 addresses the independent rc.4 prose-completeness and semantic failures.
Its optional Chinese prose screen is not a general semantic equivalence test.
Engine math-integrity.2 remains unchanged while plugin-level checks are developed.

Authority: [Semantic Versioning 2.0.0, Chinese specification](https://semver.org/lang/zh-CN/).

rc.6 added an unvalidated terminal actual-output audit. Independent offline
review found missing math-object proof, sampling/translation scope confusion
and dropped user preferences. rc.7 fixes those invariants and adds real-adapter
counterexamples; it remains an unpublished development prerelease, not a freeze.
The engine math-integrity.2 overlay is unchanged. Both plugin manifests match
1.5.0-rc.7; final audit contract is 1.0.0-draft.2 and remains unvalidated.

rc.8 replaces the terminal character-risk heuristic with a source-derived
typed-token/edit contract, and coordinates same-region program/model findings
without discarding omission warnings. Ordinary long sentences and decimal-unit
prose retain safe automatic repair. Plugin1.5.0-rc.8 / final audit draft.3 /
object-edit contract draft.2 remain unpublished, unvalidated development work.

rc.9 preserves complete continuous-expression boundaries and contextual
unary/binary sign roles in object-edit contract1.0.0-draft.3. Ordinary signed,
scientific and isolated grouped quantities remain supported. Plugin1.5.0-rc.9
and final-audit1.0.0-draft.4 are development prereleases; the engine overlay
stays math-integrity.2. No production validation, tag or Release is implied.

rc.10 unifies prose-boundary classification across lexing, operand parsing and
quantity handling. Explicit operator adjacency cannot be erased by a keyword
collision. Plugin1.5.0-rc.10 / final-audit draft.5 / object-edit draft.4 retain
the unvalidated gate and math-integrity.2 engine; no new dependency is needed.

rc.14 introduced actual native text accounting, source-IR binding and explicit
original-English role context. Independent offline review reproduced 434 passing
tests and two existing skips, but found three false-ready coverage cases and
non-deterministic diagnostic font ordering; it did not validate production.

rc.15 is an unpublished WIP in the same 1.5.0 MINOR target. It corrects those
coverage boundaries, local/page glyph-mask placement, same-source font-program
binding, Roman-prose screening and closed calendar-date normalization. Unknown
native masks, unclassified vector paths and unsupported preservation grants
now fail closed. Text mapping and whole-content coverage are reported separately.
The public manifest pair is 1.5.0-rc.15; native mapping modules are
0.2.0-draft.2. The BabelDOC math-integrity.2 overlay is unchanged. No commit
freeze, tag, merge, Release or production approval is implied.
# rc22 calendar fragment semantics

Plugin `1.5.0-rc.22` uses date-literals `1.1.0-draft.1`: closed calendar
normalization preserves native day/year field identity, calendar punctuation
is distinguished from math within a recognized date, and signs/explicit
omission signals remain protected. The original math-integrity.2 engine,
production validation state and historical scores are unchanged. No Release
or production acceptance is implied by this prerelease identifier.

- 1.5.0-rc.23: distinguish fidelity retries from structural schema recovery;
  supply typed visible calendar hints without inferring opaque fields.
