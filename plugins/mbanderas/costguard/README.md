# Maestro: Costguard

Cost auditor for Codex that flags CI/cron and cloud-spend waste via read-only
provider checks, then previews and applies surgical CI workflow fixes locally —
without writing to provider accounts or pushing git.

- **Static half (zero credentials):** reads `.github/workflows/*.yml` and app code
  to flag redundant CI triggers, missing `timeout-minutes`, missing concurrency
  cancellation, `paths-ignore` gaps, and over-scheduled crons.
- **Billing half (read-only, opt-in):** when a provider token is present,
  reconciles live billed resources against a declared allowlist and flags
  orphaned / over-provisioned resources across GitHub, Vercel, Supabase, Railway,
  Netlify, Neon, Cloudflare, Fly, Render, Sentry, Upstash, MongoDB Atlas, Datadog.
- **Fixes:** `fix` edits only `.github/workflows/*` files, dry-run by default,
  applied locally with `--apply`. Never writes to provider accounts, never pushes.

Part of the **Maestro** collection of agent tooling.

- Source & docs: https://github.com/mbanderas/costguard
- npm: `@costguard/costguard-mcp`

## Install (Codex)

```sh
codex plugin marketplace add mbanderas/costguard
codex plugin add costguard@costguard
```

Or run the CLI / MCP server directly with no checkout:

```sh
npx -y -p @costguard/costguard-mcp costguard audit <workspace>
npx -y @costguard/costguard-mcp            # MCP server
```

License: MIT
