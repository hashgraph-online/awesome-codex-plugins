# Changelog

All notable changes to this skill are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com); versions are semver and
must match `metadata.version` in SKILL.md.

## [0.4.4] - 2026-10-28

### Added

- `metadata.display-name` "Amazon Ads Reporting": a human-readable label for catalogs
  and skill pickers. Instructions and triggering are unchanged.

## [0.4.3] - 2026-10-20

### Fixed

- Remove the obsolete test forbidding the repository-required changelog; standard-library package tests now run in CI.

## [0.4.2] - 2026-10-18

### Fixed

- `references/ad-hoc-reporting.md` no longer names a field-catalog tool the connected MCP may lack. When the integration has no catalog or validation operation, Amazon's Reporting API v1 Dimensions and Metrics documentation is the catalog, and CreateReport validates the list with 400 codes that name each problem.
