# Publish Tagged Release Workflow

1. [ ] Verify branch protection, CI success, clean source, and intended commit.
2. [ ] Select the semantic version and review generated release notes.
3. [ ] Create the signed or protected tag according to project policy.
4. [ ] Let the protected release job build and publish from that tag.
5. [ ] Verify artifact names, checksums, signatures/attestations, and version output.
6. [ ] Record release URL and artifact digests for downstream channels.
7. [ ] Trigger package metadata updates only after artifact verification.

## Exit Criteria

- [ ] Published bytes trace to the intended tag and pass smoke checks.
- [ ] No unpublished local rebuild is used downstream.
