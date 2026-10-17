# Limitations and Boundaries

## This skill supports

- official desktop Obsidian CLI Sync command family
- capability-gated Publish command workflows when publish commands are present
- status and history inspection
- restore and publish mutation flows with explicit scope

## This skill does not cover

- Obsidian Headless Sync setup or server-side sync automation
- general note editing workflows
- community tools outside official CLI

## Operational limits

- Sync must be configured in the target vault
- Publish commands may not exist in every CLI build and must be probed before use
- desktop app availability is required
- mutating commands affect remote sync/publish state and require explicit intent
