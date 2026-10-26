# Publishing a skill: lists, marketplaces, bots

Read this at step 7, before opening any listing PR. Each line is a failure or bot message we actually got while listing six skills across ~15 repos.

## Before any PR: `scripts/publish_check.py <repo> --scan` must say READY

| What broke | Who caught it | Rule |
|---|---|---|
| `description: Post — … look native and sell: Xiaohongshu …` | strict YAML loaders, skill_audit | A plain scalar can't contain `": "`. Quote the description (`publish_check` and the audit fail it). |
| Scan 78 < 80 on awesome-ai-plugins | HOL `plugin-scanner` | Ship `LICENSE` **and** `SECURITY.md` at the root *and* in every `plugins/<name>/`. That alone moves 86 → 96–100. |
| `HARDCODED_SECRET` on a skill named `waboxapp` + `-automation` | secret scanner | Data files are scanned too. `xapp-`, `sk-`, `ghp_`, `AKIA` with enough characters after them look like tokens. Compress (`.gz`) or rename report data. |
| `CLAUDE_MARKETPLACE_STRICT_INVALID` | old scanner 3.0.x | The old scanner wants root `strict`; Claude Code and newer scanners want it per plugin. Don't add it; explain in the PR. |
| Glama check on awesome-mcp-servers | bot | MCP servers must be listed and passing on glama.ai first. Only the account owner can do this. |
| `validate` failing on a fix PR (Composio) | auto-labeler | It only accepts README-only listing PRs. Put fixes and listings in separate PRs and leave a one-line note for reviewers. |
| Vercel "attempting to deploy" (sickn33) | Vercel | It's the maintainer's preview deploy for fork PRs. Ignore it. |
| Pinned plugin source (`sha`) pointed at the broken commit | buildwithclaude | After fixing a repo, re-pin every open PR that pins a commit. |
| `name` in plugin.json ≠ marketplace entry, full-width `＠` in install lines | users can't install | `publish_check` verifies both. |
| 3 of 4 plugins closed on buildwithclaude (Markdown-only renhua merged) | human security review | Download only pinned versions and verify a checksum (no `releases/latest`); never pick a URL out of a fetched page; installs and network actions list what they'll do and wait for the user's yes (`--yes` flag); say in SKILL.md that fetched pages, videos, screenshots and audited files are **data**, not instructions; scripts act only on inputs the user named. `publish_check` flags `releases/latest`, `curl … \| sh` and unpinned `npm i`/`pip install`. |
| "🤖 Generated with Claude Code" footer | reviewers | Leave it off; write the PR as the author. Add AI disclosure only where a list requires it. |

## One skill, every agent (set this up once per repo)

| Surface | What the repo needs | Install line for the README |
|---|---|---|
| Claude Code | `.claude-plugin/marketplace.json` → `plugins/<name>/.claude-plugin/plugin.json` → `plugins/<name>/skills/<name>/SKILL.md` | `/plugin marketplace add <owner>/<repo>` |
| Codex / ChatGPT desktop | `plugins/<name>/.codex-plugin/plugin.json` (`"skills": "./skills/"`, `interface` with displayName, category, defaultPrompt, privacy/terms URLs) + `.agents/plugins/marketplace.json` | `codex plugin marketplace add <owner>/<repo>` then `codex plugin add <name>@<repo>` |
| Cursor, Gemini CLI, Copilot, 40+ agents | nothing extra; the skills CLI finds SKILL.md (installs also feed the skills.sh leaderboard) | `npx skills add <owner>/<repo>` |
| Plain folder | — | copy `plugins/<name>/skills/<name>` to `~/.claude/skills/` or `~/.codex/skills/` |

Also ship `SECURITY.md`, `LICENSE`, `PRIVACY.md` (a skill collects nothing; say so) and `.codexignore` at the root and in `plugins/<name>/`; the HOL scanner then reports ~98 with both ecosystems detected. Codex lists (awesome-codex-plugins) mirror bundles from your repo and need ≥80. OpenAI's public plugin directory takes a skills-only upload through its portal (account owner only); its rules: provider-neutral wording ("the model"), no hooks, no Claude-only artifacts.

Test it like a user before submitting: `CODEX_HOME=$(mktemp -d) codex plugin marketplace add <owner>/<repo> && codex plugin add <name>@<repo>`, and `npx skills use <owner>/<repo>@<name>` (reads without installing).

## Keep one copy

The installed skill must be the repo: `ln -s ~/code/<repo>/plugins/<name>/skills/<name> ~/.claude/skills/<name>` (and the same into `~/.codex/skills/`). Editing an installed copy that isn't the repo forks it silently: four of six skills had drifted (unpushed commits, edits on both sides) and needed a three-way merge before they could be published.

## Descriptions in the users' languages

Models pick skills from the description, so a user writing in Japanese only triggers a skill whose description has Japanese words. Write the description in English, then add `Triggers:` with the real phrases in Chinese and in each target language (ja, ko, vi, hi…), staying under 1,024 characters. README in English + Chinese first, then the same languages, with a switcher line under the H1.

## Writing the PR

- Read the list's CONTRIBUTING, PR template and `.github/workflows` first. Bots enforce what humans don't write down: alphabetical order, README-only, keyword blocklists, minimum scores.
- One open PR per list. To add another skill, append it to your open PR and leave a one-line comment, instead of opening a new PR.
- Place each entry alphabetically in the closest category, and copy the neighbours' format exactly (table row vs bullet, `*By @you*` suffix, description ≤150 chars).
- PR body: what it is (one sentence each), real-world use, proof (audit score, a report), "I am the author". Follow the account owner's rule on AI attribution in PR and issue text; many owners want none there (commit trailers are separate).
- JSON lists: re-dump with the file's own indent and `ensure_ascii`, or one entry becomes a 100k-line diff. `scripts/json_append.py` detects both, inserts, and refuses if anything but additions changed. Run the list's own tests before pushing.
- Forks: GitHub rate-limits new forks. Open at most 6 new forks per batch; reuse existing forks (`gh repo sync`) for the rest.
- Vendoring lists (they copy skill folders into their repo, e.g. ok-skills) also need the README count and index updated in every language the Contributing section names.
- Gates you can't meet yet: a minimum repo age (e.g. 14 days) or star count. Note them with the date they open; don't submit early.

## What reviewers rejected, and what got merged

| Seen | Fix |
|---|---|
| Plugin directory (buildwithclaude) closed: a script downloaded `releases/latest`, a page chose what to download, `setup.sh` installed packages without asking | Pin the binary and verify its SHA-256; fetch only the URL the user gave; print the install plan and wait for a yes; say in SKILL.md that pages, videos and screenshots are data, never instructions |
| Same directory merged on: "Markdown only, no scripts, no network, version matches the manifest" | Lead the PR body with exactly those facts, and pin to a commit SHA. After any later fix, push, re-pin, and leave one comment saying what changed |
| Auto-labeler `validate` fails because rule 1 allows README-only changes | Expected for fix PRs; leave one comment explaining it, don't fight the bot |
| Frontmatter with an unquoted `: ` passes Claude Code but fails js-yaml / PyYAML | Quote the description; `publish_check.py` parses strictly. When fixing someone else's repo, claim only what you verified ("strict parsers reject it") |
| Crawler notes "manifest but no standard commands/skills" on a marketplace repo | Harmless when the entry's type is `marketplace`; skills live under `plugins/<name>` |
| awesome-copilot wants an issue form plus an immutable tag or SHA, tested in Copilot | Cut a release tag first; submit through the form, not a PR |
| MCP lists (punkpeye) require a Glama listing and badge | Account owner registers on glama.ai; add the badge to the PR line |

## Exposure: what actually brings people

Measured on one account: 49 listing PRs → 0 stars, 8 human views in 14 days, ~240 clones that were almost all index bots. Listing PRs are table stakes, not reach. In order of what moves humans:

1. **A data post** the owner publishes (e.g. "audited 899 skills, 98 % never say when to use them"), with one chart. `skill_report.py` produces the numbers.
2. **A tool people paste into**, with a badge that links back (the in-browser checker at `docs/check/` + `skill health` badge). Every repo that adds the badge is a backlink.
3. **Fix-type PRs** to popular skill repos (description over 1,024 chars, broken references, invalid YAML). Maintainers read those; listing PRs get bot replies.
4. **A series**: one collection repo whose marketplace lists every plugin via `git-subdir`, a "part of the X series" line under each README's H1, the same share image as README hero and GitHub social preview.
5. **Dogfood**: make the launch video and images with your own skills and say so in the post.
6. **A daily growth check** (scheduled task): stars, views, clones, PR states, one line of what changed.

## After: `scripts/pr_triage.py` instead of reading notifications

It sorts every open PR into ACTION (you can fix it), YOU (the account owner must act: register, authorize, sign), or WAIT (a maintainer, or an expected bot message). Fix every ACTION item, reply on the PR once, and re-run. Most bot mail is WAIT.
