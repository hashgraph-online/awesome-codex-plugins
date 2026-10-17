# Maintenance Evidence Contract

Use this contract to keep an OSS maintenance cycle reviewable and honest.

## Intake

Record the observation time and source URL for:

- repository visibility and license;
- open issues and pull requests;
- latest published release;
- default-branch CI;
- dependency or code security findings;
- external listings and real user feedback.

Unknown values remain unknown. Do not convert missing metrics into zero.

## Selected Change

The maintenance plan must state:

- the user or maintainer problem;
- why this is the smallest meaningful change;
- files or components expected to change;
- acceptance checks;
- rollback or failure route.

A linked issue is preferred but not mandatory when the rationale is concrete and
the change is independently verifiable, such as remediating a published security
advisory.

## Review Evidence

The change evidence must link or record:

- branch and pull request;
- fresh tests and build or plugin validation;
- fresh dependency/security audit;
- review summary with zero unresolved blocking findings;
- documentation and changelog updates.

## Release Gate

`review_oss_release_readiness` may pass only when:

- the repository is public and has an open-source license;
- the version and change impact are documented;
- tests pass;
- no critical or high security finding remains;
- documentation and changelog are updated;
- the pull request and completed review are linked.

## Adoption Follow-up

Keep separate categories:

- **Discovery:** directory listing, mention, or search visibility.
- **Interest:** star, watch, or discussion.
- **Evaluation:** installation attempt, feedback issue, or reproducible report.
- **Usage:** confirmed workflow use or downstream dependency.
- **Maintenance:** external pull request, repeat contributor, or co-maintainer.

Never describe one category as a stronger category without evidence.
