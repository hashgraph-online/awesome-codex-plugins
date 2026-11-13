# New commits, and fresh reviews

## New commits are not a reset

When the PR's head or base moves:

1. Record the new SHAs, move the old target to the overview's **Target history**, update **Current target** and the
   change map, and look at what changed since the revision you reviewed. If history was rewritten or the
   comparison isn't available, say so rather than assuming the new commits simply add to the old ones.
2. Map the changes to existing areas and accepted findings. Propose which areas to revisit and any new ones.
3. Ask before starting follow-up investigations, unless the user already asked ("check the new commits against our
   findings"). Mark affected evidence and accepted findings `recheck`; earlier human decisions stay recorded.
4. Mark the areas you revisit `revisiting`, and areas the user had reviewed `rereview`, keeping the revision and
   reasons of the earlier review.
5. Append the follow-up evidence: whether each issue is fixed, still there, changed, or caused something new. The user
   adjudicates new candidates and confirms each area again.

Write a new `inputs/<base>..<head>/` folder (or a new snapshot) for the new comparison before dispatching; don't
overwrite the old one. Pass earlier area notes to investigators as historical leads, labeled with the revision each
examined: they're things to check again at the new target, not evidence already checked there. Record the head each
area actually examined. "Appears unaffected" is an assessment, not a check against the new head. Keep old wording and
posted records identifiable when a finding becomes outdated or fixed.

## A fresh review only when the user asks

New commits, a resumed session or a request for a follow-up review don't mean a reset. Reset only when the user asks
for a fresh review or agrees one is warranted; ask if a request is ambiguous.

1. Let running investigators finish (or stop them) and save their output first.
2. Create `archive/<timestamp>/` and move only this skill's files into it: `review.md`, `overview.md`, `inputs/`,
   `areas/`, `findings/`, `deliveries/`, and any other file `review.md` records as belonging to the review. Leave
   `kickoff.md`, `plan.md`, `investigations/`, `measurements/`, second-opinion run folders and older archives where
   they are; link to them from the new `review.md` instead. Never move a folder that holds a registered git worktree
   (a second-opinion run's `checkout/`). Check the move worked before writing anything new. If archiving fails, stop.
3. Start a clean `review.md` with only the PR's identity, the target and the archive's location. Build a new overview
   and plan without importing the old conclusions or candidates.
4. Don't read the archive's analysis into the fresh pass unless the user asks. Before posting anything later, check the
   archived delivery records so you don't post a comment twice.

Never delete an archive without the user's permission. Resetting the folder changes nothing on the code host.
