---
name: vault-sync
description: Catch the knowledge vault up with work that landed WITHOUT a vault update — colleagues' pushes, merges into the production branch, sessions on another machine or without the hooks. The hooks keep the vault honest only for sessions on this machine, so that work arrives with no ritual attached and the vault silently drifts. Use whenever the user says "sync the vault", "catch up the vault", "update the notes to latest", "others pushed changes", "someone else worked on this", after pulling or merging unfamiliar work, when the post-merge hook reports the vault is behind, or on a periodic tidy.
---

# Vault sync: catching up with everyone else's work

The vault's write loop is hook-driven and therefore machine-local. Prompt hints, the pre-edit pointer and the Stop reminder fire only in agent sessions on a machine that has the vault. Work that lands on the remote from anyone else, or from a machine without the hooks, has no ritual attached. This skill closes that gap on demand.

## The one command

```bash
vault sync                 # every watched repo
vault sync api             # one target, by its key in vault.json
vault sync --json          # for scripting
```

Per watched repo it fetches, diffs `last-reconciled..<production_ref>`, and prints:

- the commit list for the window;
- **changed files grouped by owning vault note**, through the same reverse index the hooks use;
- **files matching no note**: a new module, or an undocumented surface of an old one;
- the lines the repo's version log (`CHANGELOG.md`, or whatever `version_log` names) gained in the window.

An empty window prints "vault is current". Say so and stop.

## The ritual

1. **Run the report.** Empty window → done. Otherwise work it note by note.
2. **Read the actual changes, not the commit messages.** For each "notes to review" group: `git -C <repo> log -p <start>..<head> -- <files>`, plus the changelog lines the report printed; their notes usually carry the why. The catching-up rule from the knowledge-vault skill applies verbatim: *a note written from a hazy recollection is worse than a stub. Write what the code says.*
3. **Update each owning note** per the knowledge-vault write half: amend *How it works* and *Gotchas*, keep every `[[link]]` reasoned, bump `updated`.
4. **Files matching no note** → the trigger table. A genuinely new module gets a stub from `_templates/Module.md` with honest *Where it lives* rows taken from the diff itself and at least one reasoned back-link from its domain. A new surface of an existing module gets a row in that note's *Where it lives*.
5. **Merge-state pass.** Merges in the window may make standing claims true: "(on `develop`, not yet on `main`)" markers, `status: in-progress` notes. Flip only what you verify: `git merge-base --is-ancestor <sha> <production_ref>` **plus a content grep**. A commit in the production branch's history is not proof the feature is live; work gets re-implemented under new commits, and reworked-away code can hide behind a merged one. Stamp flips "verified <date>"; mark what you attempted but couldn't verify "(re-verify)". A version that reached production in the window also gets its `7 Releases/` note (`/lightkeeper:release`, or the release-cut reconcile in the knowledge-vault skill).
6. **Honesty about other people's work.** Their code is on the remote, so notes about it say `status: shipped`. But you never had their reasoning. Where a choice looks deliberate and nothing explains it (no changelog note, no linked ticket, no commit body), write *"reason not recorded (author, `<sha>`)"* rather than inventing a rationale. A wrong why is the one thing the vault can never recover from.
7. **Finish:**

```bash
vault check --write        # must exit 0
vault sync --advance       # move the cursors to the heads you just reconciled
git -C <vault> add -A && git commit -m "vault-sync: <start>..<head> — Payment, Order, Notification"
```

The commit message names the window per repo and the notes touched. The next sync reads history to know what the last one covered.

## The post-merge hook

`vault init --git-hook` installs a `post-merge` hook in the checkout. It reports and never syncs. After a `git merge` or `git pull` lands on the production branch in that checkout, it prints how far the vault is behind: the window, the commit and file counts, the notes to review, and how many files match no note. Then it stops. Nothing is written and no cursor moves; catching up is still this skill's ritual.

It is deliberately narrow. A merge performed on the hosting site, a push, a rebase, a cherry-pick, or a conflicted merge finished with `git commit` all produce nothing. **A quiet merge is not evidence the vault is current.** `vault sync` is.

## Scale guidance

- **A handful of commits:** work inline, one pass.
- **A wave** (a staging-to-production merge, dozens of commits): group strictly by owning note, lean on the changelog entries in the window, and prefer honest stubs over rushed full notes for unfamiliar subsystems. Don't let one sync balloon. A documented cursor plus a follow-up beats a half-imagined write-up.

## Edge cases

- **Fetch fails** (offline): the report says so and runs against local refs. Fine for reading, but don't `--advance` on a stale head.
- **Cursor unknown** (history rewritten): the report refuses. Re-run with `--from <ref>` to set the window by hand, reconcile, then `--advance`. Never guess a window.
- **No cursor yet:** the report says "no cursor". That repo has never been reconciled. Reconcile it by hand first (`vault sync <target> --from <root commit> --json` lists every file that matches no note), then `vault sync --seed <target>`, which declares "current as of now" without a sweep.
- **New repo to watch:** add it under `repos` in `_meta/vault.json` with its `remote` or `path`, `watched` directories, `production_ref` and `version_log` if it has one; write its `8 Repos/` note; reconcile; then `vault sync --seed <target>`.

If `_meta/local.md` exists in this vault, read it now and follow it. It holds this vault's own rules, and where they conflict with the generic ones above, local.md wins.
