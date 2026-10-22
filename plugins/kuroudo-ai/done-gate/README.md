# done_gate — stop your AI agent from saying "Fixed!" without checking (free edition)

![done_gate demo](docs/demo_done_gate.gif)

A real run, replayed: the agent says "I fixed the login bug." without testing, done_gate stops it once, and it rewrites honestly. With a test run first, it goes straight through.

## The problem, in plain words

AI coding agents (Claude Code, OpenAI Codex, and others) often say **"Fixed!" or "Done!" without running a single test.**
You believe them, move on, and the bug is still there.

Writing "please test before saying it's fixed" in your instructions does not reliably help.
The agent reads the rule and breaks it anyway, because it believes it has already checked.

done_gate catches that moment automatically. If the agent claims something is fixed or done, but nothing in **this turn**
shows a test result, an exit code, or command output, the reply is stopped **once** with a short note:
"check it now, or say it is unverified." Then the agent carries on.

## Install as a plugin (Claude Code or Codex)

You need Python 3.8 or newer, available as `python3` (type `python3 --version` to check).

**Claude Code**, from your shell:

```
claude plugin marketplace add kuroudo-ai/done-gate
claude plugin install done-gate@done-gate
```

Or in one command from inside a session (Claude Code v2.1.275 or later):
`/plugin install done-gate --marketplace kuroudo-ai/done-gate`

**OpenAI Codex CLI**, from your shell:

```
codex plugin marketplace add kuroudo-ai/done-gate
codex plugin add done-gate@done-gate
```

Codex asks you to trust the new hook the first time it runs; say yes.

It takes effect from the **next** session. Update with `claude plugin update done-gate@done-gate`
(or `codex plugin marketplace upgrade`). Remove with `claude plugin uninstall done-gate@done-gate` / `codex plugin remove done-gate@done-gate`.

Use **either** the plugin **or** `install.py` below, not both, or the check runs twice.
If your system only has `python` (not `python3`), use `install.py` instead: it records the exact Python it was run with.

## Or install with the script

Put this folder anywhere you like, open a terminal in it, and run:

```
python3 install.py            # for Claude Code
python3 install.py --codex    # for OpenAI Codex CLI
```

That is all. It takes effect from the **next** session you open.

- Your existing settings are backed up first, and only this tool's line is added. Running it twice does not add it twice.
- **Codex only:** the first time Codex sees a new hook, it asks you to trust it. Say yes.
  (For unattended runs, Codex has `codex exec --dangerously-bypass-hook-trust`. Only use that if you understand what it skips.)
- Check: `python3 install.py --check` / Remove: `python3 install.py --uninstall` (add `--codex` for Codex)
- The installer remembers where this folder is. **To move the folder, run `python3 install.py --uninstall` first, then run `python3 install.py` again in the new place.** (If you forgot, the installer points out the old line to the missing file; remove that line by hand.)
- "This tool's lines" means lines that run a file inside this folder. The same check installed from another folder (another package from us, or your own copy) is never removed. If it is already there, it is not added twice and the installer tells you; `--allow-duplicates` registers both.

## Good to know

- **Works with Claude Code and OpenAI Codex CLI.**
- **Understands agent replies in 8 languages:** Japanese, English, Korean, Chinese, German, Spanish, Portuguese, French.
- Plans ("I will fix"), conditions ("once it's fixed") and quoted text do not count as claims.
- Evidence from an **earlier** turn does not count. An old green test cannot cover for today's change.
- **Python standard library only.** Nothing extra to install, no API key, no network access.
- **Stops once, then lets go.** The same message is blocked at most once per session, so the agent never gets stuck.
- **Messages are in English by default.** For Japanese, put `{"message_language": "ja"}` in `~/.claude/guardrails/config.json`;
  the installer switches with `python3 install.py --lang ja` or `GUARDRAILS_LANG=ja`.
- **Fails open.** If done_gate itself breaks, your work is never stopped; one line is written to `~/.claude/guardrails/guardrails.log`.

## Modes

Set `done_gate_mode` in `~/.claude/guardrails/config.json`:

- `"block"` (default): stops the reply once, as described above, and sends the note to the agent.
- `"warn"`: never stops. The same note is shown as a warning (`systemMessage` in the hook output, and on stderr),
  and the reply goes through as written. The agent is not asked to continue, so it is up to you to act on the warning.
- Any other value (a typo included) is treated as `"block"`, and one line is written to the log. A bad setting never turns the check off.
  (If done_gate crashes, it still lets your work through, as described under "Fails open". That rule is for bugs, not for settings.)

## How we use them at our company

At our company (Human Supply Co., Ltd., Japan), we run our own internal versions of these checks, and the owner chose these settings:

- `done_gate`: warn style (it does not stop the agent).
- The secret check: log only, and we ask the destination to delete what was sent afterwards.
- `pipe_guard`, `no_excuse_gate` and `unknown_gate`: block. In the 7 days from September 20 to 27, 2026, they stopped our agent 76, 6 and 3 times.

## Honest limits

- **It uses pattern matching (regular expressions).** An agent that phrases things differently can slip past it.
  The goal is to catch the everyday slips cheaply, not to be an unbreakable wall.
- **It checks that evidence exists, not that the evidence supports the claim.** If the agent ran an unrelated test that passed,
  "fixed" will go through.
- The second time the same message appears, it always goes through ("remind once" rather than "block forever").
- The `"warn"` mode uses `systemMessage`, which both Claude Code and Codex document as a warning shown to the user;
  it is tested by its output only and has not been run in a real session yet.

## Make sure it works

```
python3 tests/run_tests.py     # acceptance tests
python3 tests/mutate.py        # breaks the code on purpose and confirms the tests notice
python3 tests/test_install.py  # installer tests (temporary folder, never your real settings)
```

When everything is fine, each exits with code 0 and its last line shows `0 FAIL` (for `mutate.py`: `0 survived`).
Tests for the paid checks are skipped in this edition, and the summary line says how many were skipped. That is expected.

## Get the full set

The full edition adds four more checks:

| Check | What it stops |
|---|---|
| `unknown_gate` | Saying "I don't know / where is it?" when the answer is in your own notes |
| `secret_guard` | Sending a secret value from your `.env` files to the web, another AI, or `curl` (stopped before sending) |
| `pipe_guard` | Cutting a tool's output with `\| tail -3` and throwing away warnings that only appear when something is wrong |
| `no_excuse_gate` | Saying "I can't / I'll do it later" without having tried |

Get the full set ($12) or any single guard ($4): https://kuroudo3.gumroad.com/l/mslhcd

## License

MIT. See `LICENSE`.
