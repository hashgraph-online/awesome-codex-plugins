# Publish Homebrew Package Workflow

1. [ ] Choose a formula for a conventional source/binary CLI or a cask when
       distributing a macOS app/bundle or current Homebrew/GoReleaser policy
       requires it; verify current upstream guidance.
2. [ ] Verify the release URL is immutable and publicly reachable as intended.
3. [ ] Populate exact platform checksums from the published artifacts.
4. [ ] Select only the production/default artifact, never an internal debug profile.
5. [ ] Update a separate tap through its own narrowly scoped credential or trusted workflow.
6. [ ] For casks or macOS bundles, satisfy signing/notarization policy before publication.
7. [ ] Run current `brew style` and strict/online audit commands as applicable.
8. [ ] Install through the explicit trusted tap name, run `version`, exercise one
       command, and uninstall in a clean environment.

## Exit Criteria

- [ ] Package metadata references verified release bytes.
- [ ] Clean installation works on each supported Homebrew architecture.
