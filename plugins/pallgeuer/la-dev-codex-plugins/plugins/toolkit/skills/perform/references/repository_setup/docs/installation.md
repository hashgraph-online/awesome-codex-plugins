# Marketplace plugin installation

Install the marketplace once, then select either or both plugins. Each plugin is installed independently, and marketplace installation is separate from installing the repository's [Python package](../PYPI.md).

For a new empty or essentially empty repository, follow the [New repository setup recipe](new_repo_recipe.md). With Toolkit installed and enabled, start it in a Plan-mode chat with `$toolkit:perform setup-new-repo`.

## Prerequisites

Use the requirements table below for the selected plugin. An existing supported system Python (3.6+) is sufficient for the plugins and the base Python package; no custom interpreter or environment is needed. The optional pytest integration has its own dependency. Installing the Python package is not required to use the marketplace plugins.

For missing plugin tools, see [Codex CLI](https://learn.chatgpt.com/docs/cli/overview), [Git](https://git-scm.com/downloads), and [jq](https://jqlang.org/download/).

## Install and verify

These workflows require a stable Codex CLI release at version `0.137.0` or newer. Check the active executable before installation:

```bash
codex --version
codex plugin --help
```

See [Plugin compatibility and stability](compatibility.md#codex-cli-compatibility) for the stable-release and prerelease support policy.

### 1. Add the marketplace

Use the `main` branch for the canonical first installation:

```bash
codex plugin marketplace add pallgeuer/la-dev-codex-plugins --ref main
```

This configures the user-level `la-dev-codex-plugins` marketplace. See [Pin a stable release](#pin-a-stable-release) after completing the basic installation if you prefer a fixed repository snapshot.

### 2. Install the plugins you want

Install **[Loupe Code Review](loupe.md)** with the `la-review` plugin:

```bash
codex plugin add la-review@la-dev-codex-plugins
```

Install the **[Perform Action Toolkit](codex_perform.md)** with the `toolkit` plugin:

```bash
codex plugin add toolkit@la-dev-codex-plugins
```

Each command installs only the named plugin into the active Codex home. Neither plugin requires the other, and installing either marketplace plugin does not install the Python package.

### 3. Verify the installed state

List this marketplace's plugins:

```bash
codex plugin list --marketplace la-dev-codex-plugins
```

Every plugin you selected should report `installed, enabled`. Run this command under the same `CODEX_HOME` environment that you use to launch Codex.

### 4. Restart Codex and smoke-test the skills

Start or restart Codex after installation:

```bash
codex
```

Perform the applicable non-destructive check inside the new session:

- For `la-review`, type `$la-review:loupe` and confirm that skill autocomplete recognizes it, but do not submit the invocation merely as an installation check because that would launch external reviewers.
- For `toolkit`, submit `$toolkit:perform` with no arguments. It should list the effective actions and stop without executing one.

The plugin is ready when both the command-line listing and its applicable in-session check succeed. Both skills disable implicit invocation: for example, use `$la-review:loupe` explicitly rather than expecting a request such as "review my changes" to select Loupe automatically. Absence from an implicit skill list is therefore normal.

## Requirements by plugin

| Plugin              | Required                                                                                                               | Optional or conditional                                                                                                      |
|---------------------|------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `la-review` / Loupe | Stable Codex CLI 0.137.0+; Python 3.6+; Bash; Git; `jq`; and at least one authenticated `codex` or `claude` executable | Install and authenticate both reviewer CLIs for provider diversity; Loupe still runs when only one is available              |
| `toolkit` / Perform | Stable Codex CLI 0.137.0+ and Python 3.6+ with the standard library                                                    | Git improves repository-root discovery but has a marker-walk fallback; individual actions can require project-specific tools |

The in-chat Perform skill does not require the `la-dev-codex-plugins` Python package. Install that package only when you want the standalone `codex-perform` launcher or the repository's reusable Python tools.

Codex CLI prerelease builds are supported only on a best-effort basis. If the active `codex` executable is older than `0.137.0` or does not expose the `plugin` subcommand, update or switch the Codex installation before following this guide.

## Pin a stable release

Marketplace refs are Git refs. The canonical `main` path follows current repository development; a release tag selects one fixed marketplace snapshot. For a first installation that must be pinned, replace the first command's ref with a published tag:

```bash
codex plugin marketplace add pallgeuer/la-dev-codex-plugins --ref vX.Y.Z
```

A `vX.Y.Z` tag identifies version `X.Y.Z` of the repository. Each plugin has an independent version in its manifest, so plugins from one repository release can have different versions from each other and from the repository. Published repository tags are listed on the [GitHub tags page](https://github.com/pallgeuer/la-dev-codex-plugins/tags).

The plugin homepage links intentionally continue to open the latest product guides on `main`, even for a pinned marketplace. To read the guide matching a pinned repository release, replace `blob/main` in the homepage URL with `blob/vX.Y.Z` using that marketplace tag. See [Product documentation links](compatibility.md#product-documentation-links) for the complete policy.

## Optional: Auto-allow the Loupe review script

The Loupe skill calls a bundled Python script that launches external `codex` and/or `claude` subprocesses. Those processes need their normal user-level state, so Codex asks for escalated sandbox permission before launching them.

To avoid approving that exact script on every review, add the following line to `~/.codex/rules/default.rules`, replacing `YOUR_USER` with your user name and `X.Y.Z` with the installed `la-review` plugin version:

```text
prefix_rule(pattern=["/home/YOUR_USER/.codex/plugins/cache/la-dev-codex-plugins/la-review/X.Y.Z/skills/loupe/scripts/run_reviewers.py"], decision="allow")
```

See [Loupe's data and trust boundary](loupe.md#data-and-trust-boundary) before deciding whether this persistent permission is suitable for your environment.

## Troubleshooting

| Symptom                                                   | Check and resolution                                                                                                                                                                                                                                    |
|-----------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `codex plugin` is not recognized or the CLI is too old    | Run `codex --version` and `codex plugin --help`. The active executable must be stable Codex CLI 0.137.0+ and expose plugin management; update or switch the Codex installation otherwise.                                                               |
| The marketplace is missing                                | Run `codex plugin marketplace list`. If `la-dev-codex-plugins` is absent, add it with the canonical `main` command above.                                                                                                                               |
| A plugin cannot be found or appears stale                 | Run `codex plugin marketplace upgrade la-dev-codex-plugins`, then list the marketplace and retry the exact `PLUGIN@MARKETPLACE` selector. A pinned marketplace remains on its configured ref until you replace that ref.                                |
| A selected plugin is not `installed, enabled`             | Run `codex plugin list --marketplace la-dev-codex-plugins`, reinstall the exact plugin selector, and restart Codex. Confirm that installation and launch use the same `CODEX_HOME`.                                                                     |
| The CLI lists the plugin but the skill is absent in Codex | Fully restart Codex and check `/plugins` plus skill autocomplete. If multiple Codex homes or executables exist, compare the environment used for installation and launch.                                                                               |
| Loupe reports no launchable reviewer                      | Check `python3 --version`, `bash --version`, `git --version`, `jq --version`, `codex --version`, and optionally `claude --version`. At least one reviewer CLI must be installed and authenticated through its normal provider flow.                     |
| Perform cannot list actions                               | Check `python3 --version`, then retry `$toolkit:perform`. Follow the surfaced catalog diagnostic and the [Perform action-file troubleshooting](../plugins/toolkit/skills/perform/references/action_files.md#troubleshooting).                           |
| `codex-perform` cannot find Toolkit                       | Confirm that `toolkit@la-dev-codex-plugins` is `installed, enabled` in the same Codex home. See [Standalone Perform troubleshooting](../plugins/toolkit/skills/perform/references/standalone_cli.md#troubleshooting) for launcher-specific diagnostics. |

## Update plugins

### Update a marketplace following `main`

Restarting Codex can refresh plugins that follow `main`. To force a refresh and reinstall the selected plugin versions explicitly:

```bash
codex plugin remove la-review@la-dev-codex-plugins
codex plugin remove toolkit@la-dev-codex-plugins
codex plugin marketplace upgrade la-dev-codex-plugins
codex plugin add la-review@la-dev-codex-plugins
codex plugin add toolkit@la-dev-codex-plugins
```

The example shows both plugins. Remove and reinstall only the selectors you use, then repeat the [verification steps](#3-verify-the-installed-state).

### Move a pinned marketplace to another release

Upgrading a marketplace configured with `--ref vX.Y.Z` refreshes that same fixed ref. To move to a different release, remove every installed plugin from this marketplace, replace the marketplace, and reinstall the selected plugins:

```bash
codex plugin remove la-review@la-dev-codex-plugins
codex plugin remove toolkit@la-dev-codex-plugins
codex plugin marketplace remove la-dev-codex-plugins
codex plugin marketplace add pallgeuer/la-dev-codex-plugins --ref vX.Y.Z
codex plugin add la-review@la-dev-codex-plugins
codex plugin add toolkit@la-dev-codex-plugins
```

After updating `la-review`, also update any version-specific Loupe allow rule you chose to maintain.

## Uninstall

Remove either plugin independently:

```bash
codex plugin remove la-review@la-dev-codex-plugins
codex plugin remove toolkit@la-dev-codex-plugins
```

Keep the marketplace when another installed plugin still uses it. After removing every plugin from this marketplace, remove the marketplace itself if it is no longer wanted:

```bash
codex plugin marketplace remove la-dev-codex-plugins
```

Run `codex plugin list` and `codex plugin marketplace list` to verify the resulting state. Plugin removal does not delete user-maintained Toolkit action catalogs or a Loupe allow rule manually added to `~/.codex/rules/default.rules`.

The separately installed Python package has an independent lifecycle. Remove it from the environment where it was installed with:

```bash
python -m pip uninstall la-dev-codex-plugins
```

This removes `codex-perform` and the other installed Python tools together. Source activation through `activate.sh` installs nothing; its shell function disappears when that shell session ends.

After installation or an update, see [Recommended Codex setup](recommended_setup.md) for optional user-level configuration that complements the plugins.
