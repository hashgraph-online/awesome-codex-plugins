---
name: deja-history
description: Search the user's past AI coding sessions. Holds what they already settled and never wrote into the repo (naming rules, banned or already-tried tools, required checks before merge, preferred values, who owns what). Use before your first edit in a task, before you call a change done or ready to merge, before you recommend a tool, library, design or reviewer, before re-debugging an error that may already be solved, when they say 'didn't we fix this before', 'what did we decide about X' or 'I already have that', and before telling them something on this machine does not exist.
---

Search deja before re-deriving past work: when the user refers to earlier sessions or decisions, before debugging an error, and before implementing something that may already exist. It searches this machine's own history across every AI coding tool used on it, going back further than deja itself was installed.

Before your first edit in a task, and again before you call a change done, ready or safe to merge, call deja with mode recall and the task's key nouns (file, package, feature, setting). A rule, a rejected option or a check it returns outranks your defaults: follow it and say so in one line.

Two triggers are easy to miss because they are not questions:

- The user states that something of theirs already exists and you have no record of it — "I already have X", "we use Y for this", "that's what Z is for". They are not asking; they are telling you the history exists, which is a stronger reason to search than a question is.
- You are about to tell the user that something on this machine does not exist — a command, a file, a setting, a past decision. Recall first. Absence from the code in front of you is not absence from the machine, and a wrong denial sends them to rebuild what they have.

If the deja tool is not available in this session, the same index is reachable through the shell: `deja search --json "<query>"`, `deja ctx <query>`, `deja blame <path> --json`.

## Finding something

These are the modes of the one deja tool, passed as `mode`.

- recall: search with the most specific token available — an exact error string, function name, file path, or flag. Several words are ANDed. Not for library docs or general knowledge; only this user's own sessions.
- context: a full digest of the single best-matching session, once a recall hit looks right and the reasoning behind it matters.
- blame: before editing, refactoring or deleting a file, the prior sessions that discussed it, so you know why it is shaped the way it is. Session history, not git authorship.
- fix: paste a failing output verbatim to see the commands that followed that same error before, in sessions where it did not come back.
- how: the real command with the real flags this machine runs for a build, test, deploy or script, ordered by how many sessions ran it. A guessed invocation is plausible and fails on this setup.
- orient: at the start of work in a project, the commands past sessions ran there and the files they worked in, before you go reading.
- remember: store one durable decision after it is settled, as a single self-contained fact. Not transcripts, not anything already obvious from the code.

## Reading a result

A result may carry a bracketed marker with a date — that is the user's own later judgement on that session, and it is not advisory. Do not repeat a rejected approach. Prefer a replacement over what it replaced. Treat a stale result as needing confirmation before acting on it. A result with no marker carries no judgement in either direction.

## Saying what you used

When recalled history genuinely helps — a reused fix, a skipped re-debug, even a partial hint that changed your approach — tell the user in one short line at the start of your reply, naming the session: "déjà vu: we hit this JWT skew in March — reusing that fix (deja:a1b2c3d4-e5f)". Say nothing about recalls that did not help. This is provenance, not advertising; a note on every call would be noise.

## Limits worth respecting

- Result windows are bounded. Do not report corpus-wide counts, or claim a complete audit, from the number of hits you got back.
- If deja is unavailable or the index is empty, say that history search is unavailable. Do not invent what it might have found.
- Vary the wording and try a second query before concluding nothing is there. Exact tokens match best, so an error string beats a paraphrase of it.

## Rules the user keeps repeating

When the user asks you to find or suggest their standing rules — the things they keep having to tell their agents:

1. Run `deja rules candidates` (`--since 90d` for recent ones). It lists turns where the user corrected an agent, across every tool on this machine, each numbered `#n` with the session it came from. It writes nothing.
2. Find the standing rules in that list: preferences the user would want applied in every future session, stated in at least two different sessions. Ignore one-off corrections about a specific task. For each rule give one imperative sentence, the `#n` that state it, and how many distinct sessions. At most 15, most recurring first.
3. Show the list and stop. Write nothing until the user picks. Then show the exact lines you will append to the rules file `deja rules` names, append only those, and run `deja rules sync`, which copies the file into every installed agent's global rules file.

This takes a strong model: on one machine's 236 candidates a frontier model found the user's recurring rules with real citations, and a 9B local model invented candidate numbers. On a small model, say so rather than guess.
