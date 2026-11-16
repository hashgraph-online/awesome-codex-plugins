# Security policy

## Reporting a vulnerability

Please report security issues privately by email to [hello@gitranks.com](mailto:hello@gitranks.com), not in a public
issue. Include what you found, how to reproduce it, and which part it affects: this repository (the plugin, its
manifests and the skill) or the GitRanks Contribute MCP server at `https://mcp.gitranks.com/mcp`.

We reply as soon as we can and keep you updated until it is fixed.

## What this repository contains

This repository has no server code. It holds manifests that point your agent at the hosted MCP server, a skill and two
commands. It never stores credentials: you sign in with OAuth in your own client, or paste your own token into your
client's settings. See "What is sent to GitRanks" in the README for everything the plugin sends.

## Supported versions

Only the latest release is supported. Update to it before reporting.
