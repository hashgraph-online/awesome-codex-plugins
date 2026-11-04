# Changelog

## [0.3.0] - 2026-11-02

### Added

- "Identities": identities come from the login, each identity is for one
  provider, and each server shows the one or more for its provider. Resolve
  scope from the top down, ask when there are several, and name the identity
  searched in counts and "not found" replies.

## [0.2.1] - 2026-10-28

### Added

- `metadata.display-name` "Using Kuudo": a human-readable label for catalogs
  and skill pickers. Instructions and triggering are unchanged.

## [0.2.0] - 2026-10-18

### Changed

- Preserve stricter repository controls, including production-write bans and additional organizational approvals; skill safety rules are minimum safeguards.
- Limit repository overrides to workflow and presentation defaults; preserve skill safety boundaries for approvals, trusted targets, and unattended writes.
- Explicitly preserve later-message confirmations, typed shipment confirmations, separate DSP activation approval, and the exact seller-authored messaging exception.
