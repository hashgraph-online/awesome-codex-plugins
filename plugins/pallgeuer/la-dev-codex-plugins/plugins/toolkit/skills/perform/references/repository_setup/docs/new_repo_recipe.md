# New repository setup recipe

## For humans: How to use this recipe

With Toolkit installed and enabled, open the empty or essentially empty project directory in a Codex Plan-mode chat with high or xhigh reasoning. Give Codex a brief description of the project's intended purpose, scope, and eventual capabilities, and simply ask for acknowledgement, then run:

```text
$toolkit:perform setup-new-repo
```

The action follows this recipe and asks for missing decisions. After agreeing on the setup plan, switch to Default mode and request implementation in the same chat.

If Toolkit is not installed, give Codex the path or URL to this recipe and your project brief directly in Plan mode with high or xhigh reasoning, and ask it to plan setting up the repository in the current directory. Use the same handoff to Default mode for implementation.

## For Codex: Detailed instructions

The instructions in this file are for Codex to follow, when starting in an empty or essentially empty project directory and wishing to set up a new project. Keep setup orchestration in this file which is intended for Codex agents; the other guides in the same directory as this markdown are concise references intended for consumption by human users.

This recipe orders the complete setup; the linked guides contain its required templates and commands. Follow every applicable requirement rather than treating the templates as inspiration. Make exceptions only for explicit user decisions or stated applicability conditions, and record their reasons. Existing repositories should preserve working files and decisions instead of blindly replacing them.

### 1. Agree on the intended result

Read any supplied notes or reference code first, distinguishing historical ideas from current requirements. Ask the user for a brief covering purpose, users, eventual capabilities/content, immediate setup scope, and work to defer. Interview until consequential uncertainties are resolved.

Settle the project/distribution/import/CLI names, initial version, remote owner/name/visibility, license and attribution, runtime/platform compatibility, installation scope, and release model. Clarify whether the project needs per-file copyright/license/SPDX notices or repository-wide licensing and attribution only; preserve any notices required by the chosen license or third-party material. Licensing and visibility are separate decisions; private repositories may still require a license. Do not invent scientific functionality, a CLI, migration, or publication scope merely to fill a template.

Use the guide's solo direct-main workflow and minimal automation unless the user explicitly chooses otherwise. Explain review/branch-protection, action tags versus reviewed SHAs, and manual versus automated dependency updates when relevant. For a versioned Python/GitHub project, prepare the manual annotated-tag release runbook with validated wheel/sdist/checksum assets; an explicitly chosen alternative needs a concrete runbook too. PyPI and hosted documentation require their own decisions. Writing a runbook is not permission to release.

Ask as many questions as needed. An unanswered, timed-out, skipped, dismissed, or automatically resolved question is not consent; recommended/preselected choices are not answers. Stop dependent work until an explicit answer arrives while continuing independent investigation. Preserve earlier authorization; do not ask again about the same already approved action.

### 2. Inspect and persist the implementation roadmap

Inspect existing/nested Git repositories, identity, instruction files, Codex home/version/settings, installed plugins, required tools, host compatibility, and authentication. Resolve discoverable facts before questioning the user. Preserve existing environments, user settings, and files.

Inventory any existing Codex ding helper, root `notify` command, lifecycle hooks, amplitude, and routing in the active Codex home. Ding setup is optional user-level setup once per machine, not a repository dependency. Preserve and verify an existing working setup and earlier explicit choices; do not ask for its coverage or volume again for each new repository. Ask before proposed repairs or changes, preserving unrelated notification handlers and settings.

At the first authorized implementation step, create `docs/devel/plans/repository_setup.md`. Record checkpoints, completed/pending tasks, decisions/approvals, discoveries, blockers, commands/results, and exact next actions. Maintain a precise deferred-work table: item, reason, and condition for resuming. Update it after checkpoints and before every restart or turn end. Keep scientific/product backlogs separate from this operational journal.

Inventory the actual executable paths/versions before dependent commands. Plugins can use an existing supported system Python; the project's modern Python/dev-tool environment is a separate choice. Check Codex/Python/Bash/Git/jq as required by the selected plugins, GitHub CLI for a GitHub remote, and local uv for a uv-based project. Use maintained [Git](https://git-scm.com/downloads), [jq](https://jqlang.org/download/), [GitHub CLI](https://github.com/cli/cli/blob/trunk/docs/install_linux.md), and [uv](https://docs.astral.sh/uv/getting-started/installation/) instructions when tools are missing. Distinguish OS packages, standalone installers, project dependencies, and plugins. Do not replace system Python, alter unrelated environments, or edit shell profiles without explicit authorization; verify any PATH refresh in the actual session.

For GitHub, check `gh --version`, `gh auth status --hostname github.com`, and `gh api user --jq .login`. If needed, have the user complete `gh auth login --hostname github.com --web` in their own terminal, selecting the agreed Git protocol. Git SSH success does not establish API authentication; preserve working keys rather than uploading new ones automatically. Never ask for passwords/tokens in chat. If administrator authentication is needed, prepare the exact reviewed command, save the journal, end the turn for the user's action, and verify its result after they respond. For older tools, check capabilities and preserve provider signature/fingerprint verification through a compatible isolated procedure; never skip trust checks or modify a personal keyring as a workaround.

Initialize Git when needed using the agreed branch and identity. Within the guide-recommended `docs/devel/plans/` directory, track only `.gitkeep`. Add this excerpt to the repository's `.gitignore` alongside its other relevant rules:

```gitignore
/docs/devel/plans/*
!/docs/devel/plans/.gitkeep
```

Create `.gitkeep` and stage it explicitly; use `git add -f docs/devel/plans/.gitkeep` if required by inherited ignores. Keep the temporary plans and feedback reports in that directory local unless the user explicitly chooses otherwise. Never force-add the whole directory.

### 3. Finish Codex setup first

Follow [Marketplace plugin installation](installation.md) and [Recommended Codex setup](recommended_setup.md). Perform installation and CLI state checks now, but defer the installation guide's restart/smoke-test step until all configuration and instruction work below is ready for section 4. Inventory/install only the prerequisites actually required by the selected plugins/project, using maintained provider instructions and approval for system/global changes. Verify executable paths, host compatibility, and any PATH refresh. Do not ask for passwords/tokens in chat; save a resumable handoff if the user must complete authentication or administrator work in their terminal.

Pull repository `.codex/config.toml` and both applicable `AGENTS.md` templates forward from [Language-agnostic project setup](project_setup_agnostic.md) and [Python project setup](project_setup_python.md). Agree on their real commands/conventions before implementation; record not-yet-run command status in the journal, not permanent instructions. Inspect project trust. Show exact sensitive-file diffs and obtain explicit authorization before writing them, preserving unrelated/stronger settings.

Inspect existing user instructions/config/rules before proposing changes. Show exact diffs, preserve stronger instructions, model choices, and unrelated settings, and obtain explicit approval before writing newly proposed user-level changes. Existing approval for the same exact change remains valid. If project trust is missing, show the resolved repository path and exact trust-entry diff; do not infer trust from matching settings or parseable TOML.

For a fresh ding setup, explicitly offer completion plus approval/question sounds, completion-only sounds, or skipping setup. If the user enables either sound option, ask for an explicit choice between 85% (the default) and 100% (full amplitude) before previewing sounds or generating/applying notification or hook configuration. An earlier explicit choice satisfies the corresponding question; unanswered questions authorize neither option. Skipping setup leaves notification settings untouched and does not block repository setup.

Follow [Codex attention sounds](codex_notifications.md) for the selected coverage. Locate the standalone helper in the actual Codex marketplace checkout or a separately obtained checkout, never in the new project or an assumed installed-plugin payload. The bundled guide contains instructions, not the executable helper. Keep the installed helper and notification settings in the active Codex home, preserve existing handlers, and install matching hooks only once. If the selected coverage requires unavailable hooks, an audio player, or another prerequisite, report it and ask before installation, upgrading, or choosing different coverage; do not silently downgrade or report incomplete setup as finished. Record choices, verification, and any intentional skip or deferral in the setup journal. Defer configuration activation and hook trust checks to section 4 so one restart covers all setup changes.

If a normal cache path is missing or read-only in the managed environment, stop and notify the user, then obtain the execution permission needed to initialize/use that normal cache. Do not use UV_CACHE_DIR, a temporary cache, or sandbox weakening to bypass the problem. Declaring a writable root and initializing its directory are separate facts.

**Reuse the AGENTS.md templates verbatim.** Start with the agnostic literal template and merge every applicable language-template point, combining headings without rewriting bullets. Substitute placeholders with agreed values. Do not paraphrase, shorten, combine, summarize, or stylistically rewrite points merely because equivalent wording seems clearer. Keep every applicable point. Make only the smallest targeted edits required by an explicit contradictory user decision; omit a point only when such a decision or a guide applicability condition permits it. Record each deviation and reason. Ask about uncertain conflicts rather than silently resolving them.

Create permanent instructions from the outset: stable purpose, current layout, concrete commands, and ongoing rules. Keep setup status, restart instructions, historical approvals, bootstrap caveats, and deferred setup tasks in the journal. Additional permanent rules must express real ongoing project requirements, not setup commentary. Compare the resulting file item by item with both templates before activation, accounting for each literal point, substitution, and justified deviation.

### 4. End the turn for activation

When applicable plugin/config/instruction setup is complete, save the journal and explain what needs reloading. End the turn and ask the user to restart the Codex host through their normal launch mode and resume the chat. Include the session-specific resume command when available and a fresh-chat handoff from the journal. Do not introduce `--no-daemon` as a generic precaution; inspect supported daemon/app restart controls if the host itself is stale.

If plugin content appears stale, verify the tracked marketplace ref and actual loaded files. Main-tracking installations can pick up changes after they merge into main; a pushed PR branch is insufficient, and pinned refs remain pinned. Restarting may refresh installed plugins but does not guarantee it. Use `codex plugin marketplace upgrade la-dev-codex-plugins` to refresh explicitly, then restart and verify. If still stale, follow the installation guide's reinstall steps for the selected plugins. Do not change versions, refs, or the user's launch mode merely as a precaution.

After resume, Codex should read the repository instructions and journal, inspect the trust entry and configuration files, and run `codex plugin list --marketplace la-dev-codex-plugins` to verify the installed/enabled plugin state. These file/CLI checks alone do not prove what the running host loaded. Ask the user to run `/debug-config` and `/status` in the Codex UI, confirm that the repository config is loaded with the expected settings, and perform the installation guide's non-destructive in-session skill checks. Autocomplete and slash commands require the user's UI action; Codex cannot run them as shell commands. Explicit-only skills may be absent from implicit discovery, so ask for the documented autocomplete or explicit invocation check. Do not launch a Loupe review just to verify autocomplete. Wait for the user's confirmation before dependent implementation. If resuming still shows stale state, ask the user to start a new chat with the journal handoff and repeat the checks.

If ding configuration was added or changed, have the user review and trust new or changed approval/question hooks through `/hooks` when applicable. Verify the selected completion and attention sounds using the sound guide's checks, including stable per-chat pitch and independent repeated events. Do not manufacture approvals using destructive commands or permission changes. For an unchanged working installation, verify its helper/configuration without reinstalling it or repeating volume selection. Keep any unfinished sound checks in the journal's deferred-work table and final summary.

### 5. Complete the repository and verify it

Complete the remaining agnostic and applicable language guide requirements. For Python, lock and actually sync the environment on the host, keep the pytest extra and xdist configured from the start, and use serial runs manually when useful. Configure runtime-package branch coverage by default, missing-code reporting, no percentage gate, and HTML/XML on demand; installing pytest-cov alone is incomplete. Enable guarded-CWD behavior only when tests warrant it.

Verify the actual locked environment installs on the host, not only that its dependencies resolve. Diagnose interpreter/architecture/glibc wheel compatibility and native transitive builds. A Rust-backed dependency such as LibCST can require a compiler on an older host; use [Rustup's instructions](https://rust-lang.github.io/rustup/installation/) only when needed and obtain approval before installation. Do not downgrade outside a parent's declared constraints to avoid a build. Keep approved PATH changes command-local unless profile edits were authorized, and record the concrete dependency chain, error, and resolution.

Keep the documented bare `--cov` followed by another option so it cannot consume a positional test path. If considering `--cov=` instead, verify that the installed pytest-cov preserves the configured source scope without warnings. Do not suppress warnings or silently change the package scope/gate.

Create CHANGELOG.md with Release diffs before the first commit. In an untagged repository, keep the explicit TODO and fenced non-live v0.1.0/v0.2.0 examples; first-release preparation replaces them with real links. For a versioned Python/GitHub project, create root RELEASE.md during setup using the [Python/GitHub release template](templates/release_python_github.md). Follow its adoption instructions, fill every project placeholder, validate the concrete archive-check command and other commands against this repository, and verify the separate exact-version/publication approval handoffs. Check that no setup placeholders remain. For other release models, adapt the runbook to the explicitly agreed model. Do not execute release commands as setup tests.

For distributable packages, build and inspect both archive formats and independently install/smoke-test each outside the checkout. Exclude local/agent state, including the plans directory and its placeholder. Verify mechanical formatter changes preserve structured metadata; locked dependencies do not alone guarantee host compatibility or byte-identical artifacts.

Verify the authenticated GitHub API identity and remote-name availability separately from Git transport credentials. Create the agreed remote empty: no generated competing README/license commit. Preserve an unexpected existing repository and ask before changing its setup. Push only the checked source, require CI success for its exact commit, run the applicable Perform setup audit, and resolve findings. Recheck permanent-template fidelity after any later instruction changes.

### 6. Finish and summarize deferred work

Update the journal with final commit/CI/remote evidence, guide deviations, and every remaining task. **Summarize all deferred work in the final response**, with each item's reason and concrete resumption condition; do not hide it only in a file. Distinguish intentionally deferred product/migration/publication work from blockers to the requested setup. Explicitly state when no deferred work remains.

Include remaining `docs/devel/plans/` cleanup as a deferred item. Codex may automatically remove clearly obsolete, self-created temporary artifacts such as an applied patch preview, one-off bootstrap helper, or redundant path pointer after verifying it is no longer needed. Preserve `.gitkeep`, useful plans/journals/handoffs, user-created material, reports awaiting extraction, and anything explicitly protected or uncertain. Record the files removed; for retained cleanup, state what must happen first, such as the user extracting a feedback report. If cleanup is already complete, report it as complete rather than inventing a pending task.

Keep the journal and other useful state resumable until their purposes are finished. Summarize outcomes, checks, remaining deferrals/cleanup, and relevant links. In the final response, recommend that the user read and follow [AI-supported repository development](ai_supported_development.md) when prompting Codex during continued development.
