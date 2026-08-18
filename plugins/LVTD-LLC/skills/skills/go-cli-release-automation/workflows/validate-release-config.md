# Validate Release Config Workflow

1. [ ] Confirm the version source, target matrix, archives, and package channels.
2. [ ] Run the release tool's current config validation command.
3. [ ] Build a snapshot from a clean tree without publishing.
4. [ ] Inspect archive names, contents, embedded versions, and checksums.
5. [ ] Give every profile distinct build IDs, archive names, tags, and public/internal policy.
6. [ ] Test every supported target/profile artifact natively or with a documented emulator.
7. [ ] Review tag triggers, full-SHA action pins, permissions, environments, and secret flow.
8. [ ] Install every publishable artifact and run version/help/smoke commands.
9. [ ] If PGO is enabled, verify the profile digest, main package, originating
       workload, and selected mode match the approved performance evidence.

## Exit Criteria

- [ ] Snapshot artifacts match the documented distribution contract.
- [ ] Validation required no publishing credential.
