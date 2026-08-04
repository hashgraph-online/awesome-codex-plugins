# Codex Usage and Resets

[![CI](https://github.com/joelfarthing/codex-usage-and-resets/actions/workflows/ci.yml/badge.svg)](https://github.com/joelfarthing/codex-usage-and-resets/actions/workflows/ci.yml)
[![HOL Plugin Scanner](https://github.com/joelfarthing/codex-usage-and-resets/actions/workflows/hol-plugin-scanner.yml/badge.svg)](https://github.com/joelfarthing/codex-usage-and-resets/actions/workflows/hol-plugin-scanner.yml)

**Canonical project site:** [Codex Usage and Resets on Filament Labs](https://filamentlabs.io/CUAR/) — a visual tour, installation guidance, and field notes.

Codex Usage and Resets (CUAR) is a local Codex plugin from Filament Labs. It
turns the current Codex weekly usage window, banked reset inventory, and a tiny
local observation ledger into deterministic usage-planning facts:

- banked reset count and returned expiration details;
- used and remaining weekly usage;
- the whole-percentage precision limit, including an imminent-exhaustion
  warning when the reported remainder reaches 1%;
- pace above, below, or approximately at linear usage;
- projected exhaustion when the current average burn would exhaust capacity
  before the next scheduled reset; and
- an unexpected early return to zero used, reported conservatively as an
  observation rather than proof of the reset's cause or exact time.

CUAR uses the documented local Codex App Server
`account/rateLimits/read` method. It does not read Codex authentication files,
inspect session logs, call private ChatGPT endpoints, start a thread or model
turn, or consume a reset. CUAR is read-only toward Codex and OpenAI. Locally,
it keeps one sanitized usage snapshot and at most one recent reset observation,
ignoring and pruning either on the next successful report once it is more than
eight days old. A report that cannot form a trustworthy comparison clears the
comparison chain, so a later report cannot infer across the blind interval.

## Requirements

- Node.js 18 or newer
- a compatible local `codex` executable
- ChatGPT-backed Codex authentication
- a Codex client able to run local plugin skills

The same packaged skill and CLI are intended for Codex in the ChatGPT desktop
app, the Codex VS Code extension, and Codex CLI.

## Installation

Install from [the direct Codex Usage and Resets listing in the OpenAI Plugins
Directory](https://chatgpt.com/plugins/plugins_6a6920fb32b48191b80cb783761d4cd5):
open it and choose **Install plugin**. The directory copy is a reviewed,
versioned snapshot and does not automatically track this repository.

## Use

Invoke `$cuar` or ask Codex about current Codex usage, linear pace, projected
exhaustion, banked reset expirations, or whether an unexpected reset was
observed. CUAR's machine report is deterministic; the model explains what the
facts mean for planned work without recalculating its fields. OpenAI reports
usage in whole percentage points, so CUAR treats displayed remaining usage as
an upper bound rather than an exact measurement.

CUAR is independently developed and is not developed, supported, or endorsed
by OpenAI. Reset observation cannot rule out an account switch or every
coincident banked-reset change. Current observations and projections do not
promise future unscheduled resets.

## Validation and trust

The public repository runs its portable test suite on macOS and Linux across
supported Node.js versions. A separate
[HOL Guard](https://github.com/hashgraph-online/hol-guard) workflow scans the
plugin on pull requests and `main`, requires a score of at least 80, and fails
on any high-or-critical finding. Both workflows use read-only repository
permissions. They do not receive Marketplace credentials, upload SARIF, or
submit or publish the plugin.

Passing automated checks is reproducible project evidence, not certification,
endorsement, or Marketplace acceptance by OpenAI, HOL, Cisco, or any other
party.

The July 28, 2026 CUAR 0.1.1 pre-publication run used HOL Guard
`plugin-scanner` 2.0.1116 against both the public source and extracted release
ZIP. Both produced:

- `public-marketplace` policy: **PASS**;
- score: **97/100 — A, Excellent**;
- critical, high, medium, and low findings: **zero**;
- HOL runtime verification: **PASS**; and
- Cisco skill scanning: completed with the balanced policy and no elevated
  findings.

The two remaining notices are informational schema differences. HOL scores an
absent optional screenshot field as invalid; CUAR does not invent screenshots.
Cisco recommends a per-skill license field, while Codex skill authoring permits
only `name` and `description` frontmatter. The repository and plugin manifest
declare Apache-2.0.

## Privacy, security, and support

See [PRIVACY.md](./PRIVACY.md), [SECURITY.md](./SECURITY.md), and
[SUPPORT.md](./SUPPORT.md).
