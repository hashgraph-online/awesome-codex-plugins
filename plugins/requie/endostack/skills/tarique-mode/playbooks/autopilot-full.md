# Autopilot, full

You are the root of a fully autonomous program: a queue of independent changes goes in, and each one comes out as a merged PR. Your job is verdicts. You never own a PR yourself. Every PR gets exactly one owner, who builds it and later merges it, and the merge waits until a verification swarm made of agents that did not write the code has checked the exact commit that will land.

Pick [autopilot-stack.md](autopilot-stack.md) instead in three cases: the operator wants to look at the work before it lands, the items depend on each other or must land in order, or you were not given merge authority.

Keep two scopes apart throughout. A verdict is about a patch, meaning the change itself. A green CI run is about a head, meaning one specific commit. You pay for a full swarm once (step 4) and repeat it only after a major change. When a later head carries the same patch, the patch-identity rule in [shipping.md](shipping.md) lets a lane's earlier result still count, but CI has to pass again on that head before anything merges.

## 1. Respect what the operator kept

Your autonomy extends to the queue and stops there. If the operator says an item is theirs, or a PR is not in the queue, take it as far as merge-ready and leave the merge to them. Being asked to explain how you would run the queue does not mean you may start running it.

## 2. Give each PR an owner whose work survives a crash

- **Forge.** Decide once, for the whole program, which tool talks to the code host. The GitHub CLI is the default. Use a different forge CLI only when it is installed and actually resolves this repository, and write down which fallback you chose when it does not. Stacking tools are optional and never a requirement.
- **What an owner does.** Run each owner as a remote or cloud agent when the host offers them, or as a local subagent when it does not. The owner writes the change, opens the PR following [opening-a-pr.md](opening-a-pr.md), demonstrates the change working on the real artifact, drives CI and review to green following [babysit.md](babysit.md), and lands the PR after you clear it in steps 4 and 5.
- **Open the PR early, declare readiness late.** An early PR lets CI and review bots run while the owner is still working. The code is not ready until the owner has done the slop-strip pass and run the `security-review` and `no-comments` skills, because the swarm should judge finished code. At that point the owner rebases onto the latest trunk and reports that commit as the code-ready head, before doing its own proof. Verifiers then test against the same trunk the change will merge onto.
- **Keep reporting.** Every head pushed after code-ready gets reported too. The owner sends a merge-ready report once its own proof, CI, and the babysit loop are all done. During fix rounds, the owner keeps its existing base and rebases only when trunk causes a conflict or a CI failure, since every rebase makes CI start from zero. Before pushing the code-ready head, and before any later push that a verifier will look at, the owner runs the repository's checks for the paths it changed against the committed tree.
- **Plan for the machine dying.** The owner pushes within minutes of starting, and opens a decision trail in your store using the `show-me-your-work` skill. It pushes again after each piece of work worth keeping. Any agent that spawns a subagent writes three things about it into the store: its id, its state, and how long it may run before it counts as stuck (judged from earlier runs of the same kind of task). With that row in place you can check on the child even after its parent is gone.
- **Pushing.** An owner force-pushes nothing but its own branch, and every force-push carries a lease pinned to the SHA it last pushed or inherited. A commit on its branch that it did not author means it stops and tells you. On an unattended branch, that commit could come from another agent, a person, or someone using a stolen token, and the owner has no way to know which.
- **Permissions.** An owner can write to its own branch and to nothing else. Keep credentials for deployment, package publishing, and production data out of owner environments entirely.

## 3. Work in parallel, all from trunk

Every owner branches from trunk. No owner builds on another owner's branch, which means any PR can merge without waiting on a sibling.

## 4. Run the swarm once per change

- **Timing.** The full swarm starts when the owner reports the code-ready head. It runs again in full only if the change gains new behavior, gets redesigned, or grows by a large new diff. For a rebase, a conflict fix, or a small correction, one verifier checks the new head.
- **What the lanes do.** Following the `swarm` skill, spawn independent verifiers against the code-ready SHA using the `swarm-workers` model role (`fast` unless configured otherwise). Between them they rerun the repository's gates, exercise the behavior the change exists for on the real running surface (through that surface's control skill or a driver you name), and read the diff for defects. When the change crosses a trust boundary, one audit lane runs the `security-review` skill and confirms each mitigation in the threat model with a test.
- **When the verdict counts as clean.** Two conditions both hold: the live lane passed, and you have personally checked the evidence attached to the owner's merge-ready report. Lanes treat every unproven statement as unproven, the PR description included.
- **Fixing.** Send all proven findings back to the owner together, in a single round, regardless of how a lane labelled their severity. Each finding comes with a failing test, and that test covers every place in the code where the same defect appears.
- **Defects trunk already had.** If trunk shows the defect without this PR, log it against trunk and let the PR proceed. If the PR copies the defect or makes it reachable from somewhere new, the PR owns it.
- **Single writer.** You never push a fix yourself. If an owner is stuck, replace the owner.

## 5. Merge only code whose tests ran against its destination trunk

A passing CI run is never enough to merge on. Once the swarm lanes are running, the owner prepares for merge: it rebases onto the latest trunk, reports the resulting head, and waits for CI on it to pass.

Right before the merge, fetch trunk again and ask whether what changed there could affect this patch. Trunk keeps moving, so rebasing every time it moves would never finish. Decide with these rules:

- **The commit that would land was never tested.** This covers conflicts, files that both trunk and the PR changed, and trunk changes that alter which checks run on this PR. Rebase and wait for CI.
- **Both sides edited the lockfile.** Do a frozen install on the merged tree. If it succeeds and every package this PR touched resolves to the version it had on the PR head, no rebase is needed. If the install fails, rebase and repair it. If one of those packages now resolves to a version the swarm never saw, treat it as a supply-chain change: rebase and verify again.
- **Trunk changed code the patch calls or relies on, a dependency version for example.** Run the checks belonging to this patch on the merged tree, and merge when they pass.
- **Anything else.** Merge.
- **A third rebase.** If trunk would push the PR into a third rebase after merge prep began, the owner holds the PR and reports to you, and you decide the order in which the colliding work lands.

## 6. Your layer as root

**Loosening a gate needs your countersign.** Raising a budget, adding an allowlist entry, or suppressing a finding all make a gate weaker. Each needs a verifier's proof plus a new countersign from you, since the owner is the one who gains when the gate turns green. When the operator's grant includes approvals, your countersign serves as the approval, and the owner links to it from its trail so a lane can check it. A check that is disabled or that fails softly guards nothing, so delete it rather than leaving it in place. A forge-enforced approval is outside anything you can countersign: never grant it and never route around it.

**Hourly audit.** Once the operator says go, schedule an audit every hour using the host's scheduled-task feature, and keep it running until no delegated work is left. Over a long run, instructions drift and agents stop making progress without reporting it. If the host has no scheduler, run the audit at the end of each of your own turns and mention that you are doing so. On each audit:

1. Read this playbook again from trunk and correct anything that has drifted from it. A head nobody reported, or an agent with no row in the store, is missing bookkeeping and not evidence of a stall; tell the responsible owner to record it.
2. Check every agent, all the way down to individual lanes, by what it has actually done: pushes, trail rows, comments. A parent's status message can look fine while a child under it has stopped.
3. An agent is stuck when it is erroring, cannot begin a turn, or has produced nothing new after its allowed runtime. An owner that by the first audit has neither pushed nor added a trail row is stuck too. An agent blocked on a reply from you or the operator does not count as stuck; give it the reply.
4. Replace stuck agents immediately with a new agent whose brief merges the old scope. Do not wait for the old agent to acknowledge a stop.
5. If the audit changed anything the operator would care about, finish it with a catch-up written per the `catch-up` skill ([../../catch-up/SKILL.md](../../catch-up/SKILL.md)). If nothing changed, say nothing.

## 7. When the operator says stop

Send every owner, all at once, an order to make no further writes. Each owner replies with where it is, keeps its brief, and waits to be released.

## Subagents

- Per PR, one writing owner on the `feature` role, or whichever role fits the work, tuned using the policy in [../SKILL.md](../SKILL.md). It is responsible for the build, the PR, the babysit loop, and the merge.
- Per PR, a verification swarm on the `swarm-workers` role. Its agents are read-only apart from scratch directories, and its lanes cover gates, live proof, diff audit, and security audit.
- A lone verifier for heads that changed only slightly.
- New owners to replace stuck ones.

## Reply

Write a catch-up following the `catch-up` skill. For every PR give its current state and verdict. List what has merged, each countersign you issued and why, any gates the operator still holds, and links to all PRs and decision trails.
