# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

A monorepo has web and worker jobs with path filters. Documentation-only PRs should pass the required aggregator; a selected web job failure must fail it. No protection-setting mutation is authorized.

## Expected output

Detect package managers, runtime pins and existing check names first. Return the changed workflow plus a truth table covering selected pass, selected fail, cancelled, unexpected skip and docs-only no-work. Keep the aggregator on every relevant PR and evaluate selected upstream results under always(). Supply the exact required-check setting as a proposal.

## Failure case

The workflow is valid YAML but the gate is itself path-filtered. Treat the indefinitely pending required check as unresolved; move the condition into selected lanes and test the aggregator on a docs-only PR.

## Validation

Run project tests and workflow validation, then inspect actual CI job conclusions for representative PRs. A skipped unselected lane is acceptable; a failed/cancelled selected lane cannot be converted to success. Record final commit and check name.

## Coverage and routing

Suede AI CI and branch-protection wiring for any repo and any stack: path-aware jobs, a single aggregator required check that cannot deadlock, lockfile hygiene, runtime pinning from the repo, and the exact branch-protection settings. Use when asked to set up CI, protect main, make CI block a bad merge, fix a required check that hangs pending forever, or repair duplicate or misfiring pipelines. Detects the repo's real apps, package managers, and runtime versions first; emits workflow files and settings, never pushes or flips protection itself. NOT FOR: reviewing or grading the change the gate is failing on (use suede-code); designing the AI eval cases to wire in (use suede-ai-eval); post-merge release packaging (use suede-launch-packaging).
