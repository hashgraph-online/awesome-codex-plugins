# receipts-collector

Every time your coding agent said "done", and whether its own logs back it up.

One Python file, standard library only, runs on your machine. It reads Claude Code transcripts (`~/.claude/projects`, including subagent transcripts) and Codex sessions (`~/.codex/sessions`, including code-mode `exec` tool calls and forked sessions), finds every completion claim in the agent's final message for each turn, and looks back through the same turn for evidence.

```
curl -fsSL https://receipts.nueton.ai/receipts_collect.py -o receipts_collect.py
python3 receipts_collect.py --summary
```

It writes `~/.nueton-receipts/export.json` and prints counts only. These are candidate claims found by keyword; a person (or the paid receipt's claim filter) still has to read them, because goals and plans like "Complete two tasks" also match:

```
sessions=326 claims=1355 confirmed=106 contradicted=122 unverified=1127 stalls=16
```

## Use it inside your agent

Claude Code plugin (Claude Code 2.1.275 or later):

    /plugin install nueton-receipts --marketplace Kloudedge-apex/receipts-collector

Then run `/nueton-receipts:receipts`, or ask "how often was my agent's done actually true?"

Any agent with skills (Claude Code, Codex, Cursor and others):

    npx skills add Kloudedge-apex/receipts-collector --skill receipts

Codex: `$skill-installer install https://github.com/Kloudedge-apex/receipts-collector/tree/main/skills/receipts`

Example prompts: "Show my receipts card for the last 30 days" · "How often was my agent's done actually true this month?" · "Audit my agent's completion claims since 2026-10-01 using local git history"

## Free stop check

The **Receipts stop check**, part of Receipts by Nueton, runs when Claude Code or Codex tries to finish a turn in which it edited files with its edit tools: if no test, build, lint or typecheck ran after the last edit, or (in Claude Code) the last one failed, it asks the agent once to run one or give a `BLOCKED:` reason. It runs locally and stores only event types, check families and results, and hashed session and turn IDs. Install it separately: [setup, privacy and limits](plugins/stop-check/README.md). Installing the receipts skill does not enable this hook.

## Share your card

```
python3 receipts_collect.py --card
```

prints a 40-column receipt of your own counts, made to be screenshotted:

```
RECEIPT               receipts.nueton.ai
period          2026-09-17 .. 2026-10-19
agents                claude code, codex
sessions                             328
"done" candidates                  1,370
----------------------------------------
confirmed                            121
contradicted                         122
unverified                         1,127
silent stalls                         15
----------------------------------------
Counts are keyword matches. Read them
before you quote them.
Check yours, free: receipts.nueton.ai
```

It contains counts and dates only: no sentences, paths, ids or tool names from your logs. `--card-out card.txt` saves it to a file.

## The rules (plain code, no model)

| Status | When |
| --- | --- |
| Confirmed | A test, build, lint or typecheck ran after the last edit and passed; or, with `--repo-check`, your local git shows the claimed commit or push |
| Contradicted | "Committed" or "pushed" with no such command in the session; "tests pass" with no test run; a check passed, then more edits, then "done"; a failing check followed by "passing" |
| Unverified | Nothing in the logs settles it |

A **silent stall** is a turn where the agent started working and then ended without a final message, or hit tool errors and went quiet. Negated or conditional sentences ("still untracked", "should I push") are not counted as claims.

## What the file contains, and what it never contains

**Contains:** session, project and branch ids hashed with SHA-256 and a salt only you hold (`~/.nueton-receipts/salt`); timestamps; tool names; command families such as "test" or "git"; token counts; and claim sentences with paths, URLs, emails, hosts, hashes and long numbers masked. Anything key-shaped is replaced with `<secret>` before the file is written. `--no-sentences` removes claim text entirely.

**Never contains:** prompts, code, file contents, command strings, tool outputs or environment values.

`verify/receipts_verify.py` checks an export without any model: shape, recomputed totals, hashing, and a scan for anything path-, URL-, email- or key-shaped. It refuses a file that leaks.

## Flags

`--since YYYY-MM-DD`, `--until`, `--claude-dir`, `--codex-dir`, `--salt`, `--out`, `--no-sentences`, `--summary`, `--repo-check` (off by default; reads your local git read-only and records only found or absent for commit and push claims).

## Tests

```
python3 -m unittest discover -s tests
```

All fixtures are synthetic.

## A receipt, read by a person

If you'd rather someone read the file and send back a one-page receipt with the evidence and the three hooks that would have caught the misses: [receipts.nueton.ai](https://receipts.nueton.ai). Made by Nueton. Not affiliated with Anthropic, OpenAI or Anysphere.

MIT licensed.
