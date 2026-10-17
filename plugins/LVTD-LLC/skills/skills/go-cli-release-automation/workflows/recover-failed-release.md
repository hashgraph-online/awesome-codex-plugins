# Recover Failed Release Workflow

1. [ ] Stop automatic retries until the completed states are known.
2. [ ] Inventory tag, release, assets, checksums, package metadata, and announcements.
3. [ ] Immediately revert or disable package metadata that points to a missing asset.
4. [ ] Trust only the exact CI-recorded artifact and digest; never a local rebuild.
5. [ ] Upload the missing asset only when its CI digest matches the package checksum.
6. [ ] Otherwise supersede with a new version; never replace bytes under the old version.
7. [ ] Refresh package metadata from the verified release and repeat clean
       install, smoke, and uninstall checks.
8. [ ] Rotate exposed credentials and document the durable recovery state.

## Exit Criteria

- [ ] Every channel references one verified immutable artifact set.
- [ ] Retrying the recovery does not duplicate or mutate the release.
