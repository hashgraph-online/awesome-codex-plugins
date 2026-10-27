---
name: bounty-guard
description: Pre-flight GitHub bounty security scanner and on-chain Proof-of-Escrow MCP verifier for AI coding agents. Classifies GitHub bounties into SAFE_WITH_ESCROW, SAFE_NO_ESCROW, or QUARANTINE.
---

# BountyGuard Skill

## Overview

BountyGuard is a read-only pre-flight security audit tool and Model Context Protocol (MCP) server that evaluates open GitHub bounty issues before an AI agent invests compute.

## MCP Tools Provided

1. `list_escrows`: Lists all open verified Proof-of-Escrow GitHub bounties backed by locked on-chain reserves.
2. `verify_issue_escrow`: Verifies on-chain escrow backing for a specific GitHub issue (`owner/repo#number`).
3. `get_pool_leaderboard`: Returns live Proof-of-Work mining pool leaderboard telemetry.

## Local CLI Verification

Run the built-in Python module on any repository issue identifier:

```text
python3 -m bountyguard check owner/repo#1
```
