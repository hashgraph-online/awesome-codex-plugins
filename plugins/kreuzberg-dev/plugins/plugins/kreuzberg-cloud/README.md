# kreuzberg-cloud

Managed document extraction for Codex using Kreuzberg Cloud.

This plugin ships skills for using the hosted Kreuzberg extraction API with explicit user approval before any local file is uploaded. It covers API-key setup, job submission, job polling, presigned uploads, sandbox evaluation, and usage reporting.

## Install

Self-host:

```text
/plugin marketplace add kreuzberg-dev/plugins
/plugin install kreuzberg-cloud@kreuzberg
```

## API key

Set a Kreuzberg Cloud API key in the `KREUZBERG_API_KEY` environment variable, or configure the official SDK according to the upstream documentation.

Do not commit API keys or sandbox keys to source control. Treat all keys as credentials even when they are short lived.

## Skills shipped

| Skill | Trigger |
|-------|---------|
| **kreuzberg-cloud** | Use when the user wants managed extraction, webhook delivery, presigned uploads, sandbox evaluation, or usage tracking instead of local CLI extraction. |
| **offloading-extraction** | Use when the user wants to submit documents or URLs to the hosted extraction service. |
| **tracking-cloud-jobs** | Use after an extraction job has been submitted and status or results need to be retrieved. |
| **presigned-uploads** | Use for large files where direct object-storage upload is preferable to in-band request bodies. |
| **managing-cloud-usage** | Use when the user asks about quota, billing visibility, or processed-page counts. |
| **sandbox-keys** | Use when the user wants short-lived evaluation credentials for demos or smoke tests. |

## Safety model

- Confirm with the user before uploading local files or document contents to the hosted API.
- Prefer the official TypeScript or Python SDKs for executable examples.
- Keep API keys in environment variables or local secret stores.
- Use local `kreuzberg` extraction for air-gapped, confidential, or no-network workflows.

## See also

- **Marketplace**: [kreuzberg-dev/plugins](https://github.com/kreuzberg-dev/plugins)
- **Upstream**: [kreuzberg-dev/kreuzberg-cloud](https://github.com/kreuzberg-dev/kreuzberg-cloud)
- **Sibling plugins**: [kreuzberg](../kreuzberg/README.md), [kreuzcrawl](../kreuzcrawl/README.md)
