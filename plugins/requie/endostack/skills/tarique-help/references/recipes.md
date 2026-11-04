# Recipes

Short, casual prompts to adapt. Replace the parts in angle brackets. Each recipe says what it teaches. Give the user at most one per answer.

## Understanding

**Restate a thread.** "Read <issue link> and tell me in plain words what the actual problem is. Don't propose fixes yet." The agent commits to an interpretation you can correct before any code moves.

**Untangle a messy request.** "/in-your-own-words <long request>". Surfaces a misreading while it is cheap.

**Sharpen before sending.** "/sharpen <the prompt you were about to send>". Returns a deeper version of the same task.

**Investigate without editing.** "/tarique-mode The <service> returns 502s under load. Find out why. Don't change any code. Report what's known, what data you used, and what's still a guess." The constraint keeps it read-only, and the report separates evidence from hypothesis.

**Understand a broken subsystem.** "/how <subsystem>, then /why it's built that way." Mechanics first, then the reasons that constrain any fix.

**Recall before reading.** "/recall what I did on <topic> in the last two weeks, then read <issue>." Brings your own earlier context into a new chat.

**Make it argue.** "/teach me why you chose <approach> over <alternative>, and what we give up." A defended choice gives you concrete reasoning to test, which a summary does not.

**Resume a branch.** "/tarique-mode Pick up <branch> from its decision log. Don't redo anything already verified." Triggers session-pickup, which verifies inherited claims instead of trusting them.

## Building

**Bug fix.** "/tarique-mode <symptom>. Reproduce it first, then fix it and show me it's gone." Reproduction before the fix proves the fix addressed the real fault.

**App bug with proof.** "/tarique-mode Reproduce <bug> with the project's verification skill, fix it, and attach a recording of the fixed flow."

**Test-first.** "/tdd <bug>". Use it when a quick failing test is possible. Otherwise the skill falls back to the nearest runnable check.

**Feature with a fixed output.** "/tarique-mode Add <flag> to <command>. Output without the flag must stay byte-for-byte identical. Show both."

**Refactor.** "/tarique-mode Refactor <module>. Record its output on <fixtures> before you start and prove it's unchanged after."

**Performance.** "/tarique-mode <endpoint> takes <n> ms at p95. Find the measured cause and show before and after numbers."

## Designing and planning

**Prototype first.** "/tarique-mode Prototype three options for <UI or behaviour> behind one switch, with screenshots, so I can pick."

**Architect with a stop.** "/architect <change>. Use prototypes for anything open, and stop for my review before implementing."

**Tutorial first.** "Write the README for <new package> before any code, then /teach me why it beats <existing package>."

**Second opinion.** "/arena <design question>. Treat my current design at <path> as one of the candidates."

**Plan into PRs.** "/tarique-mode Turn <design doc> into a plan of small PRs, each with its own check. Don't implement."

**Exact migration.** "/tarique-mode Plan the move from <old library> to <new library>. The new version must match the old behaviour exactly, bugs included."

## Reviewing and shipping

**Skeptical review.** "/interrogate this branch. Don't edit anything. Only report real problems." Then read the Dismissed section, since a wrong dismissal costs the most.

**Security pass.** "/security-review this branch. Evidence for every finding, no theoretical issues."

**Prove a property.** "Use the formal verification skill to show <property> holds under retries and interleaving." After merges: "/maintain-formal-verification-skill".

**Coverage swarm.** "/swarm one worker per package, each running that package's check script on <commit>. One table back."

**Open a PR.** "/tarique-mode Open a PR with small ordered commits and the evidence in the description."

**Babysit.** "/tarique-mode Babysit PR <number> until it's green." Or, status only: "/tarique-mode Check on PR <number>."

**Land a stack.** "/tarique-mode Land this stack."

## Leaving and returning

**Overnight.** "/tarique-mode I'm going to bed. Work in a fresh worktree from <branch>. Done means <checks> all pass. You can commit. Keep a decision log with /show-me-your-work. Loop until done. If you're stuck for three hours, stop and write up the blocker." Combines every element of the leaving checklist in [prompting.md](prompting.md).

**Morning review.** "/show-me-your-work review last night's run." Read the section that flags what needs you first.

**Quick status.** "/catch-up". Read-only, with pending decisions listed.

**Queue on autopilot.** "/tarique-mode Full autopilot on <queue>." Or, to review before anything ships: "/tarique-mode Stack these up but don't ship."

**Capture lessons.** "/reflect". Approve only the edits that would change a future decision.

**Plain words.** "/bro".
