# Autopilot, stack

You are the root. Working without supervision, you build and verify a queue of changes, then hand them over as a single linear chain of PRs, each based on the branch below it. The operator reviews that chain and lands it. You decide how the chain is shaped, and you never merge any part of it.

All of [autopilot-full.md](autopilot-full.md) applies here, with one exception: what happens to work after it is verified. Read both playbooks again from trunk on every audit. If they conflict, follow this one.

## Choosing between the two

autopilot-full fits when each PR stands alone and the operator gave you authority to land them. This playbook fits when any of these holds: the operator intends to review the work before it lands, items depend on one another or must land in a set order, or you have no merge authority.

## Steps

1. **Owners stop short of landing.** Owners follow autopilot-full, except that the report they send at the end is "stack-ready" where autopilot-full says merge-ready. An owner does not rebase its branch onto any other branch, trunk included. It does not retarget, merge, or close a PR, and it does not turn on auto-merge. You control the chain's structure, and landing belongs to the operator. An item that depends on another item branches off its parent item's branch. Trunk is never the starting point for such an item.
2. **Only you change the chain's structure.** An owner pushes to its own branch and nowhere else, and each time it reports its tip it also names which link should sit below it. Rebasing and retargeting links is your job alone: with two agents doing it on the same chain, each one's rebase overwrites the other's. Add each PR to the chain once it is clean, following dependency order, and set its base to the parent link's branch with the resolved forge CLI. A stacking tool is not needed. After you push to an owner's branch, the owner takes your commit as both its new base and the SHA for its next lease. If a rebase conflicts, the owner resolves the conflict in its own slice and gives the result back to you, and you push it.
3. **You absorb trunk movement.** Before landing starts, run autopilot-full step 5's check (could the trunk change affect this link?) against every link, and where the answer is yes, rebase the chain starting from the bottom. After that, apply the patch-identity rule from [shipping.md](shipping.md) to one link at a time, with each link's parent serving as its base.
4. **Hand the chain over, then leave it alone.** Every PR in the chain states its own verdict, and links that cross a trust boundary also state their `security-review` result. From the moment landing starts, the only permitted write to the chain is the retarget after a merge that Shipping allows. Any other write could break a landing the operator has in progress. If a problem turns up while the operator is landing, report it to the operator through yourself, and hold the fix until the operator approves it.

## Subagents

The same owners and verification swarms as autopilot-full, except that owners do not land anything.

## Reply

Write a catch-up following the `catch-up` skill. Give links to the bottom and top PRs of the chain, one line per link stating its verdict, and every item you parked or left out, with the reason.
