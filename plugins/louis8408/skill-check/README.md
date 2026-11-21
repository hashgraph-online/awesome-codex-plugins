# skill-check

Know when a skill you're using is out of date.

Agent skills (`SKILL.md` folders) change often, but once a skill is copied into your skills folder nothing tracks it. Claude keeps running the old copy, and a stale skill doesn't fail; it just quietly does worse work.

skill-check warns at the moment a skill is used, when a newer version exists:

```
[skill-check] The skill "speckit-plan" is out of date: installed 0.12.0, latest v0.13.1.
Run `specify self upgrade`, then `specify integration upgrade claude` in this project.
```

Claude sees the warning too, mentions it to you, and carries on. Nothing is blocked, and no tool call is approved, changed or denied.

## Install

In Claude Code:

```
/plugin marketplace add louis8408/skill-check
/plugin install skill-check@skill-check
```

## Requirements

[Node.js](https://nodejs.org) 20 or later on your `PATH`. The plugin is one readable JavaScript file with no dependencies, so nothing is installed. Without Node.js, Claude Code shows a `hook error` notice when a skill is used.

## How it knows a skill is out of date

1. **`metadata.source` in SKILL.md.** The local copy is compared with the upstream copy at that URL: by `metadata.version` when upstream's is higher, otherwise by content and, for GitHub sources, the file's commit history.
2. **Spec Kit.** Core `speckit-*` project skills are compared with the latest [github/spec-kit](https://github.com/github/spec-kit) release, using the `metadata.version` each skill records (Spec Kit 1.4.2 and later), or for older projects the version in `.specify/`. Extension and preset skills record their own version and aren't compared yet.
3. **`npx skills`.** Skills installed with [`npx skills add`](https://github.com/vercel-labs/skills) are compared with what its lock file recorded at install time. Personal (`-g`) installs use the GitHub folder hash in the global lock file. Project installs (the default) use the content hash in the project's `skills-lock.json`, computed the way `npx skills` documents it.

## A skill shows as "unknown"?

skill-check can only check a skill if it knows where the original lives. If you copied a skill by hand and its author didn't add a source, add one to **your copy's** frontmatter:

```yaml
metadata:
  source: https://github.com/anthropics/skills/tree/main/skills/pdf
```

Use the URL of the skill's **folder** on GitHub (the page you copied it from). No version is needed: skill-check compares your copy with upstream by content and commit history, so it can tell which commit your copy came from and warn when upstream has moved on. The `source` line (and a `metadata:` key added just to hold it) is ignored in that comparison, so adding it doesn't make your copy look edited. If you did edit your copy, it stays "unknown" rather than being reported as out of date.

## What it runs, reads, fetches and sends

skill-check has no server, account or telemetry. Its hooks run `node dist/cli.js hook` at session start (in the background), when the Skill tool is used, and when you type a `/skill`. Each hook prints at most one warning. It only:

- **Reads** your personal skills (`~/.claude/skills`), the project's `.claude/skills`, `.specify/` in your project (Spec Kit), and the `npx skills` lock files (the global one and the project's `skills-lock.json`).
- **Fetches** the upstream copy of a skill from the `https://` URL in its `metadata.source`, and for GitHub sources the file's recent commits from `api.github.com`. For Spec Kit skills it fetches the latest release of `github/spec-kit`, and for `npx skills` installs the folder hashes of the skill's GitHub repository (for project installs, the skill's files from `raw.githubusercontent.com`, to hash them).
- **Writes** its cache (`status.json`) to the plugin's data folder.

Requests carry a `skill-check/<version>` user agent and nothing about you or your project beyond the URLs above.

## GitHub token (optional)

Without a token, GitHub allows 60 API requests an hour, which is plenty unless you have many skills. To raise the limit, create a GitHub token with no scopes, run `/plugin configure skill-check@skill-check`, and paste it into **GitHub token**. Claude Code keeps it in your system's secure credential store, and skill-check sends it only to `api.github.com` and `raw.githubusercontent.com`.

## More

Source, settings, Codex support and the `metadata.version` / `metadata.source` convention: [github.com/louis8408/skill-check](https://github.com/louis8408/skill-check). Licensed under [Apache-2.0](LICENSE).
