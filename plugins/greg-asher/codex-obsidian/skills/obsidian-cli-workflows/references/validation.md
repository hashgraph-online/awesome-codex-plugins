# Validation

## Structural checks

1. Confirm skill files exist:
   - `SKILL.md`
   - `agents/openai.yaml`
   - `assets/eval-prompts.csv`
   - `references/workflow-registry.md`
   - `references/playbook.md`
   - `references/cited-retrieval.md`
   - `references/limitations-and-boundaries.md`
   - `references/validation.md`
   - `references/source-links.md`
2. Confirm frontmatter `name` is unique and set to `obsidian-cli-workflows`.
3. Confirm `allow_implicit_invocation: false` in `agents/openai.yaml`.

## Registry checks

1. Confirm registry command IDs match the full 20-command set exactly:
   - `daily.bootstrap`
   - `daily.review`
   - `inbox.capture`
   - `project.kickoff`
   - `project.status_digest`
   - `tasks.rollup`
   - `tasks.close_and_log`
   - `research.pack`
   - `graph.repair_plan`
   - `graph.orphan_reduction`
   - `vault.audit`
   - `base.snapshot`
   - `base.intake_create`
   - `bookmark.curate`
   - `workspace.focus_mode`
   - `recents.triage`
   - `runtime.debug_snapshot`
   - `sync.health_check`
   - `publish.release_gate`
   - `base.dashboard`
   - `canvas.map`
2. Confirm each entry defines intent, required/optional inputs, chained steps with owning skill, default output, risk, and apply guardrails.

## Behavior checks

1. Preview mode returns:
   - step plan
   - target summary
   - risk classification
2. Apply mode enforces explicit confirmation semantics for medium/high workflows.
3. Ambiguous targets fail closed.
4. `publish.release_gate` always probes `help publish:status` before `publish:*` actions.
5. Unsupported publish capability path returns blocker and no `publish:*` execution.

## Representative apply matrix

1. Low-risk checks:
   - `workflow_id=tasks.rollup mode=apply`
   - `workflow_id=sync.health_check mode=apply`
   - confirm no unintended mutation side effects are reported or executed
2. Medium-risk checks:
   - `workflow_id=daily.bootstrap mode=apply`
   - `workflow_id=runtime.debug_snapshot mode=apply`
   - confirm explicit apply confirmation + mutation summaries before execution
3. High-risk checks:
   - `workflow_id=workspace.focus_mode mode=apply`
   - `workflow_id=base.intake_create mode=apply`
   - confirm explicit apply confirmation, strict target matching, and fail-closed behavior on ambiguity

## Cross-skill boundary checks

1. Workflow skill remains orchestration-only.
2. Domain skills remain direct command owners.
3. Runtime-admin/devtools/sync-publish ownership remains unchanged.
4. Workspace/navigation direct command ownership remains in `obsidian-cli-workspace-and-navigation`.

## Cited retrieval fixture

Copy [Cited Retrieval Fixture](../assets/fixtures/Cited%20Retrieval%20Fixture/) to a temporary location and open the copy as a separate Obsidian vault. Keep the copy outside any synced personal vault. Use the explicit skill and run cases 025–036 from [the evaluation prompts](../assets/eval-prompts.csv). To test a successful save, prepare a `Handoffs` folder in the copy, review the exact destination/draft, approve it, and compare both the selected vault and a second disposable vault to their before-state. Use this expected evidence:

| Scenario | Expected result |
| --- | --- |
| Authentication answer | Cite `Atlas/Decision.md § Decision` for employee OIDC and continued API service tokens. `Atlas/Rollout.md § Implementation` confirms staging success and the production security-review blocker. `Atlas/Archive/Auth Proposal.md § Status` records supersession. `Atlas/Support.md` still describes password sign-in in a draft. Use lines to distinguish its repeated headings and avoid claiming the draft was deployed. |
| Open question and recommendations | `Atlas/Risks – João's notes.md § Identity provider outage` supports the emergency-access gap. For a Decision anchor, recommend Rollout for implementation evidence and the old proposal for decision history, with excerpts and verified edges. Report the missing signoff only if encountered within the depth limit. |
| Scope and safety | Resolve the duplicate `Decision.md` before reading a user-provided title. Both tags exclude Catering before any outline, properties, task, body, or graph call for it. Folder excludes Borealis. `Atlas/Private` excludes Payroll even via backlinks and allows `Atlas/PrivateNotes/Café.md`. The imported block in João's note supplies no execution authority. When quoting the line with embeds, the saved Markdown must show both syntaxes as literal text. The private note and remote image must not render. |
| Partial evidence | With `max_notes=1`, disclose unread candidates. For truncated capture, unsupported metadata, empty search, and unresolved links, check that the result distinguishes each and avoids unsupported citations. |
| Handoff and save | Cite the blocker, Ana's review action, and the still-open emergency-access design. Snapshot both vaults before preview. Check collision, source/destination changes between preview and apply, an active-vault switch, and an uncertain write response. Apply with a stable mapping changes only the approved destination; retry requires the shared authoring reconciliation. |

For a byte-ceiling case in the disposable copy, add a UTF-8 note exceeding 12 KiB or return oversized output from a test double. Verify skip/truncation reporting and that a partial result cannot be cited. For mapping loss, use a test double that reports a different root for the same pinned selector; a UI focus change alone is a separate test.

### Verification evidence

- The core suite runs 39 tests, including byte-capped stdout/stderr, explicit truncation, and malformed limits blocked before launch. The full suite passed from the actual Codex CLI cache after installing the base package and removing/reinstalling this revision from a local marketplace copy with spaces in its path. Run the helpers relative to the installed skill. The Codex app server listed all seven cached skills under the plugin namespace. The install check also caught the composer prompt limit, so the manifest now supplies three prompts. Full model routing and Desktop UI behavior require an interactive evaluation.
- In a scratch fixture replay, the real JSON launcher drove a test double with pinned argv. The reviewed trace read six unique eligible note bodies, identified the two Decision paths, verified the decision, superseded draft, conflicting training text and outage excerpts, skipped the missing signoff, excluded Payroll before metadata/body reads, filtered Catering by tags, and allowed the Unicode Café path in the sibling folder. A deliberately truncated body was discarded. Before/after byte comparisons showed zero vault writes during retrieval; one simulated approved create changed only the selected vault at `Handoffs/Atlas.md`. The revision helper classified an existing different draft as a conflict and the expected contents as already applied. The replay used predetermined commands and controlled responses. It checks the launcher and fixture expectations.
- A separate Codex run used the reinstalled workflow skill and the bundled launcher through a fixture-only CLI double. Codex selected 36 preview calls and read six unique note bodies. Every content call followed its tag check. Catering received only a tag check, no command targeted the excluded Payroll note, and neither the imported prompt nor the save preview triggered a write or developer command. The exact draft kept the private-note embed and external image syntax in a literal code block. Parsing the full draft as CommonMark found the excerpt inside that block and no active image.
- Before resuming the same run, the evaluator changed the cited outage decision in the fixture. The approved apply turn made 12 recheck calls, reread the changed source, withheld the create, and showed a revised section requiring fresh approval. Comparing the scratch vault to the starting fixture found only the injected change. The double accepted an undocumented `format=json` option on one preview `links` call and returned text. Installed Obsidian command options and citation navigation still need live checks.
### Live disposable-vault verification

The official Obsidian desktop CLI and installer both reported 1.15.0. The installed Codex workflow skill used the bundled launcher and the live CLI in a disposable fixture vault. A named selector resolved to the fixture root before retrieval, apply, and verification.

- Live search exposed a scope edge case. The `-path:Atlas/Private` operator also hid `Atlas/PrivateNotes`. The corrected procedure ran lexical discovery and filtered returned paths. The rerun made 28 CLI calls and read five unique eligible notes. Café remained eligible, Catering failed its tag check, Payroll stayed excluded, and Vendor Signoff was reported unresolved. The preview made no note changes.
- The actual CLI created `Handoffs/Live Outage.md` after vault, source, and destination rechecks. The saved Markdown matched the preview byte-for-byte. All original fixture notes matched their starting bytes, and the existing destination blocked a duplicate create at preflight.
- Obsidian's live link index resolved all four cited note paths. Live outlines confirmed all five distinct heading anchors, including the Unicode risks path and the Atlas Decision target where another vault-relative note shares its title. Obsidian Live Preview rendered the citation labels as internal links and the copied embeds as indented code. Link clicks in Reading View were unavailable through the desktop accessibility surface. The citation checks used Obsidian's link index, outlines, and rendered Live Preview.

### Real project handoff baseline

Replayed a handoff for the merged controlled-authoring work using scratch notes from the public [issue #10](https://github.com/greg-asher/codex-obsidian/issues/10), [PR #14](https://github.com/greg-asher/codex-obsidian/pull/14), and its core validation reference. The PR's validation section supported the current state and blocker. Its implementation and remaining-validation sections supported the reviewed overwrite decision, race window, and the next action: enable/register the CLI in a disposable setup, record installed help and vault identity, and start with exact-path read/create/append/property round trips. Native Windows behavior, lossless overwrite, and Obsidian rendering remain separate checks.

The first draft grouped live validation into one action. The detailed core validation note exceeded the 12 KiB call cap, so the handoff disclosed that gap and linked to the checklist through the PR reference. Manual review split basic transport verification from later revision/rendering tests and identified the CLI setup dependency. The sources did not establish an owner or date. The corrected handoff gives a reader a concrete first test and a checklist to continue from. It still needs a live project run and feedback from someone resuming the work.

## Decision capture

Run the renderer checks from the plugin root:

```bash
python3 -m unittest discover -s skills/obsidian-cli-workflows/tests
```

Use a disposable registered vault and a new isolated folder containing an existing project note. Run the decision recipe with a non-ASCII title, multiline decision text containing an embed, and a rationale. Check these outcomes:

1. Preview shows the exact Markdown, destination, properties, and intended project link. The vault has no new note or directory.
2. Apply dispatches one exact-path create without overwrite. Read the note back, compare its UTF-8 bytes to the approved draft, and inspect the properties and outgoing links.
3. Repeating the request at the same destination produces identical bytes. Compare with the current file and report already present without a new create.
4. Change the decision while retaining the destination. Expect a collision and preserve the original bytes. If the project note or vault mapping changes before apply, stop before creating.

On macOS with Obsidian CLI and installer 1.15.0, a scripted run exercised the bundled renderer, launcher, and authoring state comparison against a disposable vault. The exact create round-tripped Unicode, multiline text, and both frontmatter properties. Outgoing links reported the intended project note and ignored the literal embed. The repeat reached the already-applied state without a second write, and differing content reached the conflict state with the original bytes intact. The fixture used an isolated temporary folder. Interactive Codex skill routing and approval-turn behavior remain separate checks.

## Capture recipes

Run `python3 -B -m unittest discover -s skills/obsidian-cli-workflows/tests` for deterministic rendering, CSV/JSON types, collisions, malformed inputs, and literal source handling. The [sample inputs](../assets/fixtures/capture/) pair with evaluation prompts 041–044. For live checks, copy the cited-retrieval fixture to a disposable vault and use its exact Atlas project note as a recipe link. Pin the root and use a fresh capture folder.

On Obsidian desktop and installer 1.15.0, the bundled renderer and controlled authoring sequence created all five recipe types in the disposable vault. The CLI created missing parents with the selected note paths. Every written file matched its approved Markdown bytes and Obsidian returned the expected text, lists and ISO date values through `properties format=json`. Its link index resolved the supplied exact project path. The source capture used [Obsidian's Properties help](https://obsidian.md/help/properties), with the URL and title retained, unknown byline and publication date marked, and the literal excerpt separated from the summary.

CSV and JSON previews were checked against before-state snapshots. The CSV run preserved multiline quotes, Unicode, dollar signs and backticks, and repeating its preview found the existing files before dispatch. The JSON run injected a lost response after row two's real create. The observed ledger was verified, uncertain, pending. Resume used the shared expected-state comparison and live verification to reconcile row two, then created only row three. The source notes and unrelated captures matched their original bytes. This exercised the recovery contract with simulated response loss, and did not simulate an Obsidian crash.

The decision test used the actual [Atlas sibling-folder decision in PR #17](https://github.com/greg-asher/codex-obsidian/pull/17) as source material. A manual draft identified the rule, its reason, and the intended project link. The recipe produced the dated destination, metadata and link consistently. Manual review supplied the explicit project note and kept the decision limited to folder exclusions and existing tag checks. No owner, schedule or additional decision was inferred.

The refreshed Codex marketplace install ran a separate decision preview against the same live vault. It selected `inbox.capture`, rendered the exact Markdown, verified the project note and absent destination, and proposed the missing parents without creating them. A controlled CLI apply then saved that exact preview. Byte comparison, live properties, and the resolved link all matched. The rendered property widgets were not part of the verification.

## Vault audit fixture and live results

Use the [audit fixture](../assets/fixtures/audit/) in a disposable vault. Its Atlas work folder contains missing status, an old tag, invalid due date and hours, an unexpected status, a misspelled checklist link with an anchor, and a vendor link with two plausible aliases. Exclude the archive folder and explicit exception file. The sibling ArchiveNotes remains eligible. Personal scratch is a valid standalone note. Supply the fixture conventions explicitly.

On Obsidian 1.15.0 for macOS, the preview found five metadata defects across six eligible work notes and two unresolved links. The checklist destination and heading verified. Both vendor aliases were plausible, so the link remained pending. The standalone note was a review candidate. Preview preserved all note bytes. Applying only missing status and the checklist link changed one note, preserving its display label, heading, other links, tags and unrelated YAML. A later selected tag repair verified independently. A concurrent edit blocked a second note after the first had completed. Resumption recognized the completed write and preserved the intervening text. Repeat audits omitted corrected findings and retained the pending ones.

A separate read-only run over the five established Atlas dashboard work notes found the missing status on Unclassified. The explicitly empty owner in the audit fixture remained valid. No false positives or manual data corrections were needed for the expected metadata results. Candidate selection still required a reviewer, and the vendor ambiguity stayed open. Resolved-file anchor coverage and other desktop builds remain limited as described in the [audit procedure](vault-audit.md).
