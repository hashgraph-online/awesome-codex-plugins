# Stacked PRs

An open agent skill for splitting large changes into focused PRs, carrying review fixes through the stack, and landing changes in order.

Works with GitHub, GitLab, Bitbucket, and skills-compatible coding agents such as Codex, Claude Code, and Cursor.

## Install

**Claude Code plugin**

```sh
claude plugin marketplace add Qabbout/stacked-prs-skill
claude plugin install stacked-prs@qabbout-stacked-prs
```

**Codex plugin**

```sh
codex plugin marketplace add Qabbout/stacked-prs-skill
codex plugin add stacked-prs@qabbout-stacked-prs
```

**Standalone skill (skills.sh)**

```sh
npx skills add https://github.com/Qabbout/stacked-prs-skill --skill stacked-prs
```

Choose your agent in the installer. Also available on [skills.sh](https://skills.sh/qabbout/stacked-prs-skill/stacked-prs).

The command leaves the installer version unpinned and installs from this repository's default branch. npm is used only for installation. For a versioned manual installation without npm, download the [v1.1.2 source](https://github.com/Qabbout/stacked-prs-skill/archive/refs/tags/v1.1.2.zip), review it, and copy `SKILL.md`, `references/`, and `scripts/` into your agent's skills directory under `stacked-prs/`, preserving executable permissions on the shell scripts.

## Use

Ask your agent:

- “Use stacked-prs to split this branch into reviewable PRs.”
- “Fix this review comment and carry the fix up the stack.”
- “Help land this PR stack in dependency order.”

Requires Git, Bash 3.2+, Python 3.9+, and authenticated access to your Git host. See [SKILL.md](SKILL.md) for the workflow and bundled helpers.

Native plugins namespace the skill: use `/stacked-prs:stacked-prs` in Claude Code, or select it from `/skills` in Codex.

## Updates

```sh
claude plugin update stacked-prs@qabbout-stacked-prs
codex plugin marketplace upgrade qabbout-stacked-prs
```

Claude Code uses the plugin manifest version; automatic updates are opt-in in `/plugin`. The Codex command refreshes the marketplace catalog. Both marketplaces and the skills.sh install command track the default branch. To update an older standalone installation, rerun the install command above.

## Test locally

```sh
python3 -m unittest discover -s tests -v
```

Tests use disposable local Git repositories. GitHub Actions is disabled.

## License

[MIT](LICENSE) © 2026 Abdulrahman Qabbout.
