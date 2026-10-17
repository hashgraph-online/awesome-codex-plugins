---
name: firecrawl-cli-installation
description: |
  Install the official Firecrawl CLI and handle authentication.
  Package: https://www.npmjs.com/package/firecrawl-cli
  Source: https://github.com/firecrawl/cli
  Docs: https://docs.firecrawl.dev/sdks/cli
---

# Firecrawl CLI Installation

## Quick Setup (Recommended)

```bash
npx -y firecrawl-cli@1.16.2 init -y --browser
```

This installs `firecrawl-cli` globally, authenticates via browser, and installs all skills.

This setup is safe to re-run when the CLI is missing, stale, or only partially configured.

If `firecrawl` is already installed and you want to update it first:

```bash
npm update -g firecrawl-cli
```

Skills are installed globally across all detected coding editors by default.

To install skills manually:

```bash
firecrawl setup skills
```

## Manual Install

```bash
npm install -g firecrawl-cli@1.16.2
```

## Verify

First check status:

```bash
firecrawl --status
```

Then run one small real request to prove install, auth, and output all work:

```bash
mkdir -p .firecrawl
firecrawl scrape "https://firecrawl.dev" -o .firecrawl/install-check.md
```

The install is healthy when both commands succeed.

## Authentication

Authenticate using the built-in login flow:

```bash
firecrawl login --browser
```

This opens the browser for OAuth authentication. Credentials are stored securely by the CLI.

### If authentication fails

Ask the user how they'd like to authenticate:

1. **Login with browser (Recommended)** - Run `firecrawl login --browser`
2. **Enter API key manually** - Run `firecrawl login --api-key "<key>"` with a key from firecrawl.dev

### Command not found

If `firecrawl` is not found after installation:

1. Ensure npm global bin is in PATH
2. Try: `npx firecrawl-cli@1.16.2 --version`
3. Reinstall: `npm install -g firecrawl-cli@1.16.2`
