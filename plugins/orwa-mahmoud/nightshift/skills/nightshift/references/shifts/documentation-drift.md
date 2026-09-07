# Documentation drift — finite — local docs that no longer match this repository

Links, commands, filenames, examples, and version pins in *this* repo's documentation, checked
against files that already exist here. The list is whatever a local pass reports, so it ends.

Use when README, contrib, or skill docs disagree with the tree: a moved path, a renamed command, a
version that only the docs still claim. Not a rewrite of positioning, voice, or product behaviour.

Supported on any repository that keeps documentation in-tree (markdown, man pages, `--help`
examples checked into the repo). Skip generated sites whose source of truth is elsewhere.
Never select this entry in artifact mode. Do not `git init` a notes folder to make docs commitable.

```text
- [ ] **Documentation drift — make in-repo docs match the current tree.**
  - Discovery: walk tracked documentation (README, docs/, skill and command files, examples) and
    collect local references — relative links, fenced commands, filenames, version strings that
    claim to describe this repository. Resolve each against the tree and the manifests that
    already exist here (plugin.json version, PATH commands the repo documents, files on disk).
    Do not query the network for "current" product claims.
  - Never select this entry when work mode is artifact.
  - Work one cluster per cycle (broken links, then stale commands, then version pins): restore
    the documentation to the repository's truth, or restore a renamed file if the docs are right
    and the tree drifted. Run the item gate, commit.
  - Never rewrite positioning, marketing voice, or safety claims to paper over a mismatch.
  - Never invent a command, flag, or skill the product does not ship so the docs become true.
  - Never change product behaviour, hooks, or runtime to match incorrect documentation — park
    that as a code fix; this shift only repairs docs (or restores a file the docs still name).
  - A reference that cannot be verified locally (third-party URL, marketplace listing) is out of
    scope: record it in snag-log.md as skipped, not as a pass.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when a full local pass reports no remaining in-repo drift, or every leftover is parked
    with a reason.
  - Verify: the item gate is green at every commit; a second local-link/command pass is clean
    for the files this shift touched.
```
