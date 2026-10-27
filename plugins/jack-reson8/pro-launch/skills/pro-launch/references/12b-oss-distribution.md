# 12b Open-source distribution: be seen, not just shipped

Read this when a repo is public (skills, MCP servers, libraries) or Jack asks "why no stars / exposure". Output: `docs/distribution.md` with the four sections below. Distilled from 2026-10-24: six repos with 0 stars, 13 PRs open on lists that hadn't merged anything in months, and zero external referrers.

## D1 · Diagnose with numbers, not guesses
```bash
python3 scripts/gh_exposure.py repos            # stars · views · clones · referrers
python3 scripts/gh_exposure.py prs              # every open PR of mine, tagged ALIVE / DEAD by its list
```
- Views ≈ 0 with 40–100 clones means bots and indexers, not people. Never report clones as exposure.
- Referrers show only `github.com`, which means no post anywhere links to the repo. A post is the missing step, not another PR.
- Write the table plus a 3–5 line "why" into `docs/distribution.md` § Diagnosis.

## D2 · Liveness before any PR (gate)
```bash
python3 scripts/gh_exposure.py lists owner/a owner/b ...
```
- A list with fewer than 3 merges in the last 14 days is **DEAD**: a PR there is never read. The biggest-star lists are often dead (77k-star Composio last merged in May, with 1.7k PRs open).
- Read each ALIVE list's CONTRIBUTING / AGENTS.md for star floors, age rules ("≥14 days old"), "issue form only, no gh CLI" or "humans must submit". Record the rule; a list you're blocked from today goes in manual-tasks with its trigger condition, e.g. "repo reaches 14 days or 100 stars".
- Find candidates with a subagent (gh search repos for awesome lists, marketplaces and MCP registries in each language). Only lists that pass D2 go in § Targets.

## D3 · Two kinds of PR, both legitimate, many of them
1. **Listing PRs**: one per project per list, written in that list's exact entry format, section, sort order and validation script (`npm run validate`, `build.py`, `lint`). Insert text and never reformat a JSON/MD file; check `git diff --stat` before pushing. The PR body states what the plugin runs and downloads; security-minded reviewers close vague ones. Pin plugin entries to a commit SHA.
2. **Fix PRs**: lint other people's skill repos (`skill-skill`'s audit) for objective spec violations (name ≠ folder, description > 1024 chars, missing frontmatter, dangling paths). Only repos that merged an outside PR in the last 30 days. Use an issue instead when a rename could break installs or CONTRIBUTING says "issue first". Each one is a real contribution and carries one link to the tool that found it. This kind scales to dozens; copy-paste listing spam does not.
- **Pace it**: GitHub answers `HTTP 403: was submitted too quickly` after about 8 fork calls in a burst, and the limit is account-wide. Reuse existing forks, run at most ~6 new forks per batch, and queue the rest with the ready branch noted. Spammy bursts can get the account restricted, which would sink every repo at once.

## D4 · The storefront and the human channels
- **Share image (1280×640)** per repo: logo-only previews fail a stranger's 3-second test (12 of 17 top repos used logo-only, and that works only for famous brands). Use one sentence of what it does plus real output, or before → after (06b, `style_frame.py`, spec `assets/style-frame-spec.example.json`). Uploading it is web-only, so it goes in manual-tasks.
- README top: one sentence, real output (GIF / before-after), install line. Profile README lists every project; pins are web-only, so they go in manual-tasks.
- Check plugin.json `homepage` and `repository` links resolve (two pointed at renamed repos and returned 404).
- Human channels (X, Reddit, HN, 小红书, V2EX/LINUX DO): write ready-to-paste posts (Chinese via `renhua`), leading with the most data-rich story, e.g. "audited 899 skills". Jack posts them himself.

## `docs/distribution.md` sections
`Diagnosis` (D1 table + why) · `Targets` (list | ALIVE evidence | rule | project | PR/issue URL | status) · `Blocked until` (trigger condition, not a date range) · `Manual tasks` (posts with copy, uploads, pins, form submissions).
