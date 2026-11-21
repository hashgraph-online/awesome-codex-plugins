# Security policy

## What this repository contains

Markdown skills (`skills/*/SKILL.md`), plugin manifests for Claude Code, Codex and Cursor, a remote MCP server entry (`.mcp.json`, `https://api.okdata.online/mcp`) and two maintenance scripts with no dependencies. Nothing here runs on install, and no key or secret is stored in the repository: the skills read the API key from the `OKDATA_API_KEY` environment variable, or the MCP client signs in with OAuth.

## Reporting a vulnerability

Please report security problems privately, not in a public issue: email hello@okdata.online with "security" in the subject.

Include what you found, how to reproduce it and what it affects (this repository, the MCP server or the okdata API). We will confirm we got it and tell you when a fix is out.

## Scope

In scope: the files in this repository, the MCP server at `api.okdata.online/mcp` and the API at `api.okdata.online`. A leaked or misused okdata API key can be revoked at any time in the okdata console; revoke it first, then tell us.
