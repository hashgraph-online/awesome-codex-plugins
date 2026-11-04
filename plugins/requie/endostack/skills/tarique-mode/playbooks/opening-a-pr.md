# Opening a PR

Any playbook that produces code finishes with this one. It sets the rules for the worktree, how commits are shaped, what the PR says, which forge to use, how stacks are built, and when a PR counts as ready. Playbooks that only read (Investigation and the forensics playbooks) do not use it.

## 1. Keep the worktree clean

- Do the work in a git worktree created from main. Subagents you spawn work in that same worktree.
- When more than one subagent writes to the same branch, give each its own worktree, or have each one hard-reset to the tip of the remote branch before every turn.
- When the branch already contains unrelated uncommitted changes, save your own change as a patch, make a new worktree, and apply the patch in it.
- When the worktree is too tangled for that, start again from main and make the change with as few edits as possible.
- When the host cannot create worktrees, use a second clone instead and mention it in the reply.

## 2. Shape the commits

- Commit frequently as you go. Before any PR is opened, rebase the history into a short sequence of small commits. Each commit should be able to land as a PR by itself, and reading them in order should explain the change.
- If a fix corrects the commit you just made, amend it. If the fix makes sense alone, give it its own commit.
- Never let a commit body restate the subject line.

## 3. Checks to run before the PR exists

1. Before each commit, run the slop-strip pass on the diff (trigger 11 in [../SKILL.md](../SKILL.md)). That pass includes looking for secrets in the staged changes.
2. Run the `security-review` skill against the diff of the whole branch. Put the fix for each confirmed finding into the commit that caused it. When a finding describes an exploitable flaw that main already has, keep it out of the PR title and body; tell the user and let them choose how to disclose it.
3. Run the `no-comments` skill before asking for review.
4. Draft the PR title, the PR description, and each commit body using the `technical-writing` skill, applying every layer it has apart from the documentation-mode framework. On top of that, follow simplified technical English: use one word for each action, keep articles in, and choose a plain verb over an -ing form. Finish with `unslop`.

## 4. The title

Follow Conventional Commits: `type(scope): subject`. Available types are `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, and also `security` in repositories that use it. The scope is the area of the code. Write the subject as a brief command with no full stop at the end. If a particular symbol is what the change is about, use its actual name in the subject.

## 5. The description

Picture a reviewer who has the diff open and one minute to spare. The description tells that person the reason for the change, what you chose not to include, what might break, and the evidence that it works. Keep sentences short and plain, use identifiers sparingly, and avoid long unbroken paragraphs. Squash merges use the description as the commit body, so stay under roughly forty lines.

Structure it with level-two Markdown headings (never bold text standing in for a heading), using the sections below in the order listed. Leave out a section that would be empty; Scope is the one section that always appears.

`## Why`: one to three sentences on the problem and how you solved it. Do not open with SHAs, a history of rebases, or a note saying which branch it was based on.

`## What changed`: up to three bullets. Mention a file path or symbol only if the change depends on it. For a rename or a retarget, give the old and the new name.

`## Scope`: required. Up to three items saying what this change includes and what it leaves out on purpose, such as planned follow-ups or known gaps. Keep symbols, paths, and file-by-file walkthroughs out of it.

`## Tradeoffs`: list an alternative you turned down only when a reviewer would likely ask why you did not take it. If there was never a real choice, drop the section.

`## Security`: required whenever the change crosses a trust boundary. In one or two sentences, name the boundary, the mitigation, and the test that demonstrates it. Never describe how to exploit a flaw that is still unfixed.

`## Blast radius`: one or two sentences on which users or systems the change reaches and why the risk is low or high. If main is currently failing, say what it costs to leave it failing.

`## Verification`: up to three bullets, each describing an actual run and what it produced. For a performance change, give one key number with its unit before and after, and link the output of the `arena` or `swarm` skill for the details. Do not explain sampling methods, list every lane, or paste metric tables.

Below the sections, add screenshots or a video if they demonstrate something the description claims. Put full SHAs, per-lane accounts, corrections to measurements, per-file checklists, and statements that something came back clean into a separate linked artifact; they do not belong in the description.

## 6. Pick the forge once

Before the first operation on a PR, decide which forge tool you will use, and keep using it for creating, editing, viewing, watching, and merging. An alternate forge CLI wins if it is installed and resolves this repository. Otherwise use the GitHub CLI and record that you fell back to it. A stacking tool is never a requirement.

## 7. When the host has its own PR tool

Some hosts ship a PR tool of their own. When yours does, create, edit, retarget, and mark PRs ready through it, because a PR made through a CLI is invisible to the host's tracking. Do everything else through the forge you picked, and do everything through that forge when the host has no PR tool.

## 8. Size and stacking

- Split work into several focused PRs rather than one big one. Each small PR is quicker to review, and a revert removes only the change that caused the problem.
- A stack is a series of PRs, each based on the branch of the one beneath it. The bottom PR is based on trunk. Every branch above it is rebased onto the precise tip commit of the branch below, and its PR uses that lower branch as its base. Once a lower PR merges, move the PR above it onto trunk using the post-merge step in [shipping.md](shipping.md).
- If the host has no PR tool, open each upper PR with the forge's create command, setting the base to the lower branch and opening it as non-draft. Change a base later with the forge's command for editing the base.
- Start a branch from trunk only when the work does not depend on anything else. Before doing significant work on a stack, rebase it onto trunk.

## 9. Open it ready for review

PRs are never opened as drafts. Some host PR tools default to draft, so state non-draft explicitly each time you create one. On GitHub, simply leave out the draft flag. On an alternate forge, pass whatever flag sets the PR to open. Should a draft slip through anyway, flip it to ready with the forge's ready command or the host tool. Before you tell anyone a PR's status, look it up through the forge.

## 10. Opening does not trigger babysitting

After you open a PR, post its link and carry on with the build. Complete the phase or the stack first, and run [babysit.md](babysit.md) only after the user asks for it and the full stack exists. Babysitting PRs one at a time as they open holds up the build, and the CI runs it starts are thrown away when the next wave of commits restarts them. If reviewers push the change away from what it was meant to do, argue the point instead of complying.

## 11. Subagents that open PRs

A subagent opening a PR runs `interrogate`, the slop-strip pass, `security-review`, and `no-comments`, then posts the link and hands back to its parent. It does not babysit.

Owners under [autopilot-full.md](autopilot-full.md) or [autopilot-stack.md](autopilot-stack.md) are the exception. The owner's brief gives it the babysit loop, and that brief stands in for the user request Babysit normally waits for. Such an owner begins babysitting once it has sent its code-ready report, and finishes by sending merge-ready (autopilot-full) or stack-ready (autopilot-stack). The rules in this playbook and in Babysit that hold babysitting back until the whole stack exists do not bind it.

## Done

The PR exists, it is ready for review, a forge lookup has confirmed its status, and its canonical link has been posted. The reply of whichever playbook called this one includes that link.
