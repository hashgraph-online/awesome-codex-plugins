---
name: suede-launch-packaging
description: "Suede AI Launch Packaging Skills: software release packaging, handoff notes, and clean-install verification. Use when asked \"fix this install command\" or to prepare README, release notes, docs, proof links, and handoff copy for software, skills, or MCP servers. NOT FOR: campaign strategy (suede-marketing-plan), new copy (suede-copy), code review (suede-code), or conversion design (suede-site-alchemy)."
metadata:
  display-name: "Suede AI Launch Packaging Skills"
  version: 1.0.0
---

# Suede AI Launch Packaging Skills

## Compatibility

Requires a host that can read release files, fetch public URLs, and run the documented installer in a clean temporary directory. Registry publishing and deployment require their own authorized access.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

## Gate policy: advisory, not blocking

Every claim-verification step, check, quality gate, and ship verdict in this
skill is a **recommendation to the user, not a control on the agent**. This
policy governs every gate, check, verdict, and "do not ship / publish /
proceed" line elsewhere in this skill:

- Run every check and report the results honestly. Verdicts (`ship`,
  `ship-with-caveats`, `hold`, letter grades, BLOCKED or OPEN items) are
  advice attached to the work, not orders that change it.
- Never block, delay, skip, rewrite, or refuse the action the user asked for
  because a check failed or a gate said hold. Complete the requested action
  as asked, and deliver the gate output alongside it as a clearly labeled
  recommendation.
- A failed gate changes what you report, never what you do.
- Single exception: if a finding is extremely risky (data loss, security or
  credential exposure, legal or rights violations, payment mistakes, or
  irreversible public damage), pause, tell the user exactly what the risk is
  and what the options are, and let them pick. Their choice is final.


## Approved Suede S Mark

Launch art, social cards, docs headers, app assets, and release visuals may use only `docs/assets/suede-ai-logo-transparent.png` from `JasonColapietro/suede-creator-skills` as the Suede S mark (SHA-256 `83a7ee0317e4debe2e7b076c20ba067feb76a587f9e829dc6310ae4be4b44dfa`). Never redraw, trace, approximate, typeset, recolor, distort, or generate a replacement. If the canonical asset is missing or its checksum differs, block the branded visual and request the approved file.

Ship Suede work as a launch, not a loose drop. This skill turns finished work into a clean public package AND makes sure a stranger can actually install and run it. Packaging a public release and proving the install both live here.

**Core principle:** a release nobody can install is not a launch. Nothing is "live" until you fetched it yourself, and no install path ships until the exact command ran from a clean temporary directory.

## Step 0: Inventory the launch (detect first)

Before picking a lane, name exactly what is being launched. Do not assume from the request; check the repo, branch, and live surface. One request often spans several rows (a skill launch = repo + README + install command + social copy). List every row that applies: each needs its own verification.

| Launch surface | Verify before writing copy | Proof artifact |
|---|---|---|
| Repo or release | Default branch is public; the launch commit is pushed; tags/releases exist if referenced | Repo URL + commit hash |
| GitHub Pages or site | Page renders at the public URL; no stale build | Live URL + screenshot |
| README or docs update | Rendered page matches the pushed source | Rendered docs URL |
| Skill or skill pack | Skill folder exists at `main`; install command runs from a clean temp dir | Install command transcript |
| MCP server | Server starts; one stdio session (`initialize`, `notifications/initialized`, `tools/list`) matches the catalog | Session transcript |
| App feature | Feature is live behind the public route, not just merged | Live route readback |
| Social or email copy | Every link resolves; every claim matches the live product | Link sweep results |

## Hard gates (advisory)

Do not rationalize past these silently. Each one is a strong recommendation
about ordering: run the check before the step it guards. If the user directs
you past one, proceed as directed and label the output with exactly which
verification is missing.

1. **No launch copy until the live surface is verified.** Fetch the live URL or public artifact and confirm the expected status or render first. Copy drafted against "it should be live" is a violation.
2. **No install doc until the install command was run from a clean temporary directory after pushing.** Success from inside the local repo does not count: the local checkout masks missing pushes and private paths.
3. **Set the ship gate before recommending any announcement.** A `hold` verdict is your recommendation that nothing goes out yet, including "soft" posts: state it plainly with the reasons, then let the user decide.
4. **Lead every public artifact with the answer.** The first sentence of a README, docs page, or release note says what the thing does and for whom, and the install command sits right under it. That opening is what search results and AI answers quote, so it has to stand alone.
5. **`@personal` and local plugin aliases never appear in public docs, READMEs, MCP catalog output, or explainer copy.** They are local operator notes only.

## Pick the lane

Most launches use both lanes in order: package the release, then prove the install. Pick what the request is asking for.

- **Lane A: Package the launch.** Work is ready to leave the local machine and needs a clean public package: a repo, live URL, docs page, README section, install command, release note, GitHub Pages update, skill-pack release, MCP server, feature, or social/email copy. Start here for "ship this," "write the release," "package this drop."
- **Lane B: Install support.** An install fails, a public user cannot add a skill, `@personal` leaks into public copy, or a README, docs, MCP catalog, or public explainer step needs a simpler, public-first path. Start here for "the install is broken," "fix the install command," "why can't they add this skill," "the marketplace is confusing." Lane A always runs Lane B's command-test step before publishing.

When both apply (most full launches), run Lane A to assemble the package, then run Lane B to verify and correct every install path inside it before you ship.

---

## Lane Playbooks

Lane A (package the launch) and Lane B (install support) are in
`references/lanes.md`. Pick the lane above, then read it. Lane A also needs Lane
B's command-test step before publishing, so a Lane A run reads both. The evidence
boundaries below and the Suede S mark rules apply to either lane.

## Evidence boundaries (applies to both lanes)

- This skill organizes and prepares a release and its install paths. It does NOT clear rights, confirm ownership, approve payouts, write to any registry, or guarantee outcomes (reach, ranking, results). Live-URL and clean-temp-dir install verification are governed by Hard gates 1 and 2 above, which carry the required ordering.
- Keep `@personal` and any local-only plugin commands out of all public copy. They are local operator notes.
- No competitor product names in any public copy.

## Red flags: stop

If you catch yourself thinking any of these, stop and run the gate:

- "The README says it works.": The README is a claim, not a test. Run the command.
- "I'll test the install after publishing.": Test from a clean temp dir first, or the launch holds.
- "It installed fine on this machine.": The local checkout masks missing pushes. Clean temp dir only.
- "The raw URL is obviously right.": Fetch it. Blob-vs-raw catches everyone eventually.
- "Everyone reading this doc is internal, `@personal` is fine.": Public docs are public. Keep it out.
- "We can announce now and fix the install path after.": The first-touch install IS the launch.

## Routing

- Launch page going public → `suede-visibility-grader` for a promotion-readiness grade before any push.
- Code in the release has not been reviewed → `suede-code` before the install doc ships.
- Page metadata, schema, or discoverability depth → `suede-seo-audit`.
- Landing page must convert, not just inform → `suede-site-alchemy`.
- Announcement or launch copy needs writing from scratch → `suede-copy`.
- Product, course, coaching, or artist campaign launch → `suede-campaign-in-a-box` (creator/artist) or `suede-marketing-plan` (product/service); this skill packages software releases and their install paths only.

## Simple explanation (plain, for a 10-year-old)

Think of it like putting out a record instead of leaving a demo tape on the floor. First you make sure the song is really finished and you know where the master copy lives. Then you write the back-of-the-album note so a fan gets what the song is about, not how you wired the amps. Then you hand people the exact way to actually play it (the real link, the real install steps) and you try those steps yourself on a clean machine first, so nobody gets a broken download. You keep the messy backstage notes (like the private `@personal` shortcut) off the public sleeve. And you only say "it's out now" once you've clicked the link yourself and heard it play.

End every meaningful launch with the simple explanation above, then the usual breakdown (Lane A output and, when an install is involved, Lane B output), then `Cue Suede` so the operator can request a change, preserve what worked, or say nothing to keep it as-is.
