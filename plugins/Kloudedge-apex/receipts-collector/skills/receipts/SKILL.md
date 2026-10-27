---
name: receipts
description: Counts every time a coding agent said work was done, fixed, tested, committed or pushed, and checks each claim against the same session's own commands, marking it Confirmed, Contradicted or Unverified. Runs the open-source Receipts collector locally over Claude Code and Codex session logs and prints the counts as a 40-column card the user can share. Reads local files only and sends nothing anywhere. Use when the user asks how often their agent's "done" was true, wants to audit agent completion claims, or asks for their receipts card.
license: MIT
compatibility: Requires Python 3.9 or newer and local Claude Code (~/.claude/projects) or Codex (~/.codex/sessions) logs. Runs offline; needs no network access, account or API key.
metadata:
  author: Nikxius, Inc.
  homepage: https://receipts.nueton.ai
  source: https://github.com/Kloudedge-apex/receipts-collector
  version: "0.1.0"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/receipts_collect.py *)
---

# Receipts

Your agent said "done". This counts how many of those times its own logs back it up.

The collector is `scripts/receipts_collect.py` next to this file: one Python file, standard library only, MIT licensed. In Claude Code, `${CLAUDE_SKILL_DIR}` expands to this skill's folder. If you see the variable unexpanded (Codex and other agents), use the absolute path of the `scripts/` folder beside this `SKILL.md` instead.

## Steps

1. Tell the user, in one sentence, what is about to happen: the collector reads session logs under `~/.claude/projects` and `~/.codex/sessions`, writes a hashed export to `~/.nueton-receipts/export.json` (and a private salt file at `~/.nueton-receipts/salt` on first run), and sends nothing anywhere.

2. Run the collector:

   ```sh
   python3 ${CLAUDE_SKILL_DIR}/scripts/receipts_collect.py --summary --card
   ```

   The card prints on stdout. The one-line summary and the diagnostic counts print on stderr.

   Add flags only when the user asks for them:
   - `--since YYYY-MM-DD` and `--until YYYY-MM-DD` for a date range (default: the 30 days ending at the newest log record).
   - `--claude-dir PATH` or `--codex-dir PATH` when the logs live somewhere else.
   - `--repo-check` to let commit and push claims use read-only local Git history.
   - `--no-sentences` to keep claim text out of the export entirely.
   - `--card-out PATH` to also save the card as a text file.

   If `python3` is missing, try `python`. Python 3.9 or newer is required.

3. Show the user the card exactly as printed, inside a code block. Do not recompute, round, rephrase or add to any number.

4. Explain the result in a few plain sentences:
   - **Confirmed**: a matching command ran after the last edit and succeeded, for example tests passed after the change.
   - **Contradicted**: the session's own record says otherwise, for example "pushed" with no push in the session, or a failing check after the last edit.
   - **Unverified**: nothing in the session proves it either way. This is usually the largest group.
   - The counts are keyword matches after code and negation filters, as the card says. Some candidates are not real claims. Having a person read every candidate is what the paid receipt at receipts.nueton.ai adds; mention it once, and only if the user asks what to do next.

## Rules

- Never upload, paste, email or otherwise send the export or its contents anywhere, and never open a network connection for this skill.
- Do not print claim sentences from `export.json` unless the user explicitly asks to see them.
- Do not read prompt bodies or file contents from the logs yourself; the collector already extracts only structure and masked claim sentences.
- The card holds counts only and is safe to share as printed. Before the user shares the export itself, tell them to open it in their own editor and read every retained sentence, or to rerun with `--no-sentences`.
- Describe agents neutrally: agents make claims, and claims need receipts.

## When something goes wrong

- `missing_directories=2` with `sessions=0`: no logs were found at the default paths. Ask where the logs are and rerun with `--claude-dir` or `--codex-dir`.
- `ERROR salt: ...`: the salt file has permissions other than `0600` or cannot be created. Report the message as printed. Do not change file permissions unless the user asks you to.
- `ERROR card: value does not fit 40 columns` or any other `ERROR`: report the line as printed and rerun without `--card` to get the summary counts.
