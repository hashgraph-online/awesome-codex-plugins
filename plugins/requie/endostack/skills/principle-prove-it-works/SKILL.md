---
name: principle-prove-it-works
description: Use at the end of every task, before you say it succeeded. Check the actual output yourself, for example by exercising the feature, reading back what got stored, or opening the diff. A proxy signal, a subagent's self-report, or a successful compile does not count.
disable-model-invocation: true
---

# Prove it works

Look at the real artifact before calling a task finished: exercise the feature, read the value that was stored, examine the diff. Proxies, self-reports, and a successful compile do not count as evidence.

## When it applies

The end of every task, before you report success.

## What to do

1. Expect indirect checks to tempt you. File timestamps, a subagent's summary, and a cached screenshot feel cheaper than looking, but acting on a wrong inference costs more.
2. Check whether a process is alive by querying the process, not by reading a status file it last wrote.
3. Read the value at its source rather than a cached copy or something computed from it. After changing a firewall rule, send a request that should be blocked and confirm it is blocked. Do not stop at "the config file contains the rule."
4. When a verification fails, suspect the observation method first.
5. Prefer a deterministic script that reruns the comparison over a one-time visual check. Run that script and keep what it prints as an artifact the reviewer can execute again ([principle-build-the-lever](../principle-build-the-lever/SKILL.md)).
6. Show that artifact to the user in the reply. Reserve committing it for big or complicated work that needs an audit trail, such as a big port or migration, using the [show-me-your-work](../show-me-your-work/SKILL.md) skill.

A delegate reporting "all tests pass" may have run a subset. Rerun the command or read its captured output before repeating the claim.

## The failure it prevents

False "done" claims, trust in subagent summaries, and the belief that a green build means working software.

## Done when

Evidence from the real artifact accompanies the claim of completion.

Compare [principle-explain-the-number](../principle-explain-the-number/SKILL.md): that one asks whether a measurement means what it claims, and this one asks whether the output exists and behaves correctly.

Related: [principle-build-the-lever](../principle-build-the-lever/SKILL.md), [principle-sequence-verifiable-units](../principle-sequence-verifiable-units/SKILL.md), [principle-explain-the-number](../principle-explain-the-number/SKILL.md), [create-verification-skill](../create-verification-skill/SKILL.md).
