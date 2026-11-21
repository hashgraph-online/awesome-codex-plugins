# Validation

Use this checklist when refining the plugin in this repository.

## Environment assumptions

- Obsidian desktop installer 1.12.7 or later
- Obsidian CLI enabled in Settings -> General
- Obsidian CLI registered on the system path
- local desktop app available when commands run
- Codex Desktop on macOS may require the sanitized `script + zsh -ilc` launcher

## Repo checks

1. Confirm the plugin manifest lives at `.codex-plugin/plugin.json`.
2. Confirm the skill lives at `skills/obsidian-official-cli/`.
3. Confirm the repo `README.md` describes this repository as a single installable plugin, not as a multi-plugin container.
4. Confirm `.agents/plugins/marketplace.json` exposes this repo root with `source.path` set to `./`.
5. Confirm `SKILL.md` still routes only to the official desktop `obsidian` CLI surface.
6. Confirm `SKILL.md` requires exact `path=` for note-content mutations, except for explicit documented daily-note commands, and forbids mutating ambiguous `file=` targets.
7. Confirm `SKILL.md` explicitly prefers structured output when the command supports it.
8. Confirm `SKILL.md` requires a read-only app/CLI probe before the first mutation in a session.
9. Confirm escalation follows an actual permission/IPC failure or blocked required support step; an external vault alone does not require escalation.
10. Confirm `SKILL.md` documents the Codex Desktop macOS launch wrapper and explains why direct `obsidian` child launches can crash.
11. Confirm `SKILL.md` separates wrapped command form from escalation policy and tells Codex to escalate the wrapped command when needed.
12. Confirm `CODEX_OBSIDIAN_ZSH_PATH` overrides the launcher shell while the unset case still resolves to `/usr/local/bin/zsh`.
13. Confirm the playbook documents missing-parent-folder behavior as a local support step rather than a hard stop.
14. Confirm `agents/openai.yaml` keeps implicit invocation disabled unless deliberately changed.
15. Confirm `assets/eval-prompts.csv` still covers explicit positives, implicit probes, safety cases, and out-of-scope cases.

## Prompt checks

Use the prompts in:

```text
skills/obsidian-official-cli/assets/eval-prompts.csv
```

You want:

- positive prompts to activate the skill
- implicit probes to remain inactive while `allow_implicit_invocation: false`; assess candidate relevance separately from automatic activation
- implicit negative prompts to stay out of scope
- safety prompts to stop before ambiguous mutations
- negative prompts to refuse cleanly

## Behavior checks

Use a disposable vault first. Check:

- note reading
- note search
- note creation
- append or prepend
- task listing
- backlinks
- property set and property read
- history or diff
- write behavior when the vault is outside the current workspace
- write behavior when the parent folder does not already exist
- broader safe vault structure work that supports a CLI note operation
- command-family capability probes for optional or drift-prone commands (for example `obsidian help publish:status`) before claiming support in docs or skill contracts

During manual checks, verify:

- note-content mutations use exact `path=`
- daily-note mutations use the documented `daily:*` commands rather than implicit active-file writes
- a read-only probe happens before the first mutation in a session
- from Codex Desktop on macOS, the probe works with the sanitized `script + zsh -ilc` wrapper
- the wrapper uses `/usr/local/bin/zsh` when `CODEX_OBSIDIAN_ZSH_PATH` is unset and the configured absolute path when it is set
- a direct unwrapped launch is not required if the wrapped launch is the stable path in Codex
- when escalation is needed, the wrapped command is what gets escalated
- external vault mutations try the wrapped CLI path before escalation
- escalation happens only after a write-permission failure or a blocked support step
- parent-folder creation works as a conditional supporting step when the CLI fails specifically because the folder is missing
- the CLI remains the preferred path for note-content mutations even when filesystem support is used
- read-only discovery happens before broad note-name mutations
- structured output is used when the command supports it
- routine responses give concise result, target and verification; detailed target/execution evidence is retained and supplied on request or failure

## When to enable implicit invocation

Only switch `allow_implicit_invocation` to `true` after:

- the explicit behavior feels correct
- the skill boundaries stay clean
- the prompt checks and manual checks route consistently

## Issue #10 reproducible checks

From plugin root:

```bash
python3 -B -m unittest discover -s skills/obsidian-official-cli/tests -v
```

The tests execute pure section-splice/state/containment mechanics, actual shell argument recording, and mocked process failure paths. They assert preservation of unrelated frontmatter/body/links, duplicate/missing/overlapping-match rejection, final-newline/CRLF/Unicode preview preservation, stale/partial/collision comparisons, applied-effect detection, symlink/traversal containment, no preview parent creation, macOS default/override construction, shell metacharacters as argv data, malformed requests, and uncertain timeout classification. Pure `ready` comparison alone never authorizes retry of an in-flight operation. Test assertions do **not** establish live CLI capabilities, runtime metadata serialization, vault identity enforcement by Obsidian, exactly-once app execution, or Markdown rendering.

Fixtures: `tests/fixtures/Atlas.md` models a project with properties, risks/mitigation, links, a callout, and hostile-looking quoted data; `Rollout.md` supplies a decision block and embed example. For a disposable vault, place them at `Projects/Atlas.md` and `Decisions/Rollout.md`, add `People/Sam.md` as the link destination, and keep an unrelated duplicate-title Atlas note in another folder for ambiguity checks.

### Evidence recorded 2026-11-05

- Initial sanitized default launcher failed because `/usr/local/bin/zsh` is absent. Supported `/bin/zsh` override reached the installed `obsidian` command.
- Sanitized `version`, `help append`, `help prepend`, `help create`, `help vault`, `help vaults`, `help property:set`, and `help template:read` all returned “Command line interface is not enabled” (overall process exit 0). Shell startup also reported blocked fnm/pyenv writes. The disabled message is the capability blocker; no personal vault mutation/settings changes were attempted.
- Official current documentation was inspected for CLI operations and Obsidian format/template semantics. Competitor sources were read as research only.
- An independent instruction forward review covered duplicate headings/titles + active-vault switch, uncertain append completion, CRLF/literal escape revision, missing parent outside repository CWD, and a saved report collision. Its timeout finding led to requiring original-operation completion/quiescence before any retry; an unchanged target alone is insufficient. A generic harmless delayed-child experiment confirmed why wrapper timeout cannot prove quiescence; it was not an Obsidian test.

### Completed independent checks

- Initial implementation: 19 deterministic helper/fixture tests passed, including actual shell argv recording; all 19 also passed from a copied skill package in a path containing spaces, launched from an unrelated CWD. The review repair below extends this suite.
- Plugin/marketplace JSON and asset paths, all seven skill frontmatter and agent YAML files, explicit invocation policies, eval CSV shape/unique IDs, local Markdown links, and all 18 retained workflow IDs checked successfully. Six pre-existing unquoted-comma notes fields were repaired without changing evaluation semantics.
- Skill-creator `quick_validate.py` passed for the core skill (its PyYAML tooling dependency was supplied in an isolated temporary uv environment; bundled helpers remain standard-library only). Whitespace/diff checks passed.
- New launcher executed a real sanitized `version` probe with `/bin/zsh` and correctly reported only `process-completed` plus raw disabled-CLI diagnostics, rather than claiming verified capability/success.

### Required live follow-up (not verified here)

With CLI enabled/registered and a disposable vault explicitly selected:

1. Record installed version/help and unique vault ID/root mapping. Verify ordinary exact-path read/create/append/property set/read with before/after raw bytes. Include quotes, apostrophes, backticks, dollars, multiline/tab, backslashes and Unicode. Check final newline/BOM behavior before whole-file transport. Record unsupported literal-escape/CRLF cases as blocked unless a lossless mechanism is proved.
2. Test a single Risks revision, duplicate headings/titles, active-vault switch between preview/apply, concurrent local edit, collision, missing parents under the intended vault, lost response/post-read, in-flight original operation, and safe resume. Verify no unrelated note/configuration changes. Do not intentionally cause uncertain mutations in a personal vault.
3. Inspect links/alias labels, heading/block navigation, embed, callout folding and typed properties in Reading view/Live Preview. Record correctness and manual corrections; fixture syntax is not visual proof.
4. Run a representative project decision capture/saved briefing/revision and record usefulness/omissions. Cross-capability Bases/Canvas dashboard validation remains with #11/#12; this issue does not implement those formats.
5. Refresh/reinstall the cached plugin via the established marketplace flow, explicitly invoke the core skill, and verify the bundled helper resolves relative to that installed skill from an unrelated CWD. Static copied-package tests cover path portability only, not Codex UI installation or routing.

Never label these live items passed from static tests, mocks, documentation, or a successful shell exit.

### PR #14 review regression repairs

All four findings from the deep review are addressed:

- Both helpers read UTF-8 JSON bytes rather than inheriting stdin's locale codec, and emit ASCII-safe JSON escapes. Subprocess regressions run under `PYTHONIOENCODING=cp1252` and `ascii`, asserting exact Unicode paths/content, revision fingerprints, and Unicode CLI output. Invalid UTF-8 blocks before launch.
- CLI validation/process creation are separated from communication and reporting. Launch failures, post-dispatch uncertainty, and completed-process evidence stay distinct. A real scratch child writes a marker before a simulated broken stdout; completion evidence reaches stderr with `report_error`, and exit 2 prevents treating the report failure as permission to repeat the effect. No child in these tests accesses a vault.
- Windows explicitly resolves `Obsidian.com` on PATH without a shell or GUI fallback. Platform construction tests cover spaces/Unicode arguments and missing redirector guidance; this is not a native Windows runtime test. Official behavior: [Obsidian CLI Windows redirector](https://obsidian.md/help/cli) and [CreateProcess extension selection](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
- Unified diffs split on LF rather than all `str.splitlines` separators. Regressions preserve Unicode line/paragraph separators, NEL, control characters, CRLF and final-newline variants. An optional system `patch` test applies generated diffs in scratch files and checks exact candidate bytes; it skips explicitly when `patch` is unavailable. No runtime dependency on `patch` is added.

After the first review repair, the suite had 29 tests. All 29 also pass from a copied package path containing spaces with an unrelated CWD. Targeted locale/report/diff regressions fail against the pre-fix helpers, confirming they detect the original defects. The live follow-up requirements above remain unchanged; these repairs do not establish live CLI capability, native Windows execution, lossless Obsidian overwrite, rendering, or actual Codex installation/routing success.

### Second-review transport and Unicode repairs

- Replaced pipe capture with private delete-on-close temporary files. Descendants retaining stdout/stderr no longer hold up pipe-reader teardown. Cleanup waits at most one second for the launcher after the 30-second communication timeout; cleanup/capture failures preserve dispatch evidence and exit 2. Capture reads use independent offsets and Windows delete-sharing, return at most 1 MiB per stream, and flag truncation explicitly. This bounds returned diagnostics, not descendant lifetime or total scratch-file growth.
- Every final CLI argument is checked for strict UTF-8 encodability before process creation. Tests cover escaped unpaired high/low surrogates in vault, path, property, inline content and separate content fields. Valid emoji, musical symbols, Japanese text, and JSON surrogate pairs round-trip to a real harmless child.
- Added eight regression tests, bringing the suite to 37. The inherited-output test waits for a real descendant to hold the output open, then requires an uncertain result before releasing that descendant. On POSIX it models the Windows blocking-reader behavior if a regressed implementation uses pipes; native Windows uses the actual backend. Additional checks cover independent writer offsets, capture truncation/failure, and cleanup failure/timeout. All subprocess selections are guarded so regressions cannot invoke Obsidian or access a vault.

All 37 tests pass locally and from a copied package path containing spaces with an unrelated CWD. Both finding-specific regressions fail against the previous helper, confirming they detect the original defects. Metadata, YAML, skill validation, links, CSV shapes, and diff whitespace checks pass. Native Windows execution, live Obsidian capabilities/writes, rendering, and Codex reinstall/routing acceptance remain unverified. The live follow-up checklist above still applies.

## Obsidian 1.15 compatibility review and live test (2026-11-05)

- Official CLI Help lists `heading=` and `inline` for the four append/prepend commands. The 1.15 release notes establish the heading feature's version. See [source links](source-links.md).
- Before updating, macOS Obsidian 1.13.7 returned the disabled-CLI message despite exit 0. After installing the official 1.15.0 bundle and enabling the CLI in Settings, the bundled macOS launcher returned `1.15.0 (installer 1.15.0)` and live help confirmed both options on all four verbs.
- In a disposable vault, all eight combinations of `append`, `prepend`, `daily:append`, and `daily:prepend` with default spacing or `inline` inserted the supplied Unicode marker exactly once. Byte comparisons confirmed preservation of the surrounding text, including frontmatter, a child heading, and the next peer section. Append landed after the child section's body and prepend landed before the first body line. The `inline` flag joined the neighboring body line.
- A missing heading returned an error with exit 0 and left the fixture bytes intact. A duplicate heading selected the first match, confirming the need to block ambiguous selectors before dispatch.
- Installed `codex-obsidian` from the repository's local marketplace. The Codex app server listed the enabled `codex-obsidian:obsidian-official-cli` skill at its installed cache path. From an unrelated working directory, followed the installed skill and ran its cached launcher against the disposable vault. The launcher appended one test line under the unique target heading after its child section. CLI readback and a byte comparison confirmed the intended insertion and preservation of all other content.
- Remaining live checks include an enabled older build, a delayed daily-note apply after date rollover, and the 1.15.1 async `eval` case.


## Controlled note revision follow-up

The original authoring work shipped in PR #14. The following results supersede its disabled-CLI and live-validation blockers. This follow-up used Obsidian desktop and installer 1.15.0 on macOS with the bundled sanitized launcher and two disposable vaults.

- Exact-path create made the missing nested parents under the pinned vault. A deliberately dispatched collision created a numbered sibling and left the original unchanged. The production preflight blocks known collisions and reconciles unexpected siblings.
- The Atlas Risks splice preserved frontmatter, the child section, subsequent headings, links, and literal data byte for byte outside the selected edit. A second active vault contained the same relative path. Only the pinned vault was modified. Duplicate titles and headings were discovered and left untouched. Exact snapshots also verified no-final-newline, multiple trailing newlines, leading blank lines and a UTF-8 BOM through create and overwrite.
- A changed snapshot blocked a stale edit, and a fresh splice kept the intervening task. An ordinary append preserved apostrophes, dollars, backticks, shell-like text, Japanese and a non-BMP character. Discarding its successful response exercised the already-applied branch without replaying it. Tests still cover launcher failure and uncertain completion. The live run did not induce a still-in-flight mutation.
- The property probe showed that a different explicit type changed the vault type map and reserialized frontmatter, including removing an unrelated comment. Omitting the type wrote a string even when the property had a number assignment. Reusing the matching explicit type preserved the type map in the probe. The exact metadata splice preserved unrelated bytes and the type map and verified the selected property with the CLI.
- The alternate vault’s configured template resolved its title and date. Exact-path create using that template matched the resolved content and the expected frontmatter value.
- Obsidian’s rendered DOM showed the revised warning callout, collapsed background callout, property values and the rollout link’s display label and exact block target. The heading embed was marked loaded for the correct section. The embed body and click-through navigation were not verified.
- A refreshed local marketplace install exposed all nine skills through the Codex app server. The cached core revision and launcher entrypoints generated a diff and applied and verified a live Risks edit from an unrelated working directory.

The optimistic recheck still leaves a race before write. The helper blocks CRLF and literal `\n` or `\t` sequences whose transport has not been established. This run did not verify native Windows execution or an enabled older Obsidian build.
