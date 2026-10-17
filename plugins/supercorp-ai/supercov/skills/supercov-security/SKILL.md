---
name: supercov-security
description: Scans a repository's source for security vulnerabilities with the supercov CLI, pointing to the line of each finding and mapping it to CWE classes. Use when the user asks for a security scan or audit, whether code is secure, or to find vulnerabilities, injection, hardcoded secrets or other insecure code.
license: MIT
---

# Supercov security

Run `npx supercov security` for the whole repository, or `npx supercov security patch` for what a change introduced. It checks every source file for twelve named risks and points to the line. `npx supercov docs security` prints the guide for the installed version.

It sends source files to TypeSafe using the `TYPESAFE_API_KEY` environment variable. A user who set the key has opted in, so run it without asking again. If the key is missing the command says so: tell the user how to set it, then review the code by hand and say Supercov did not check it.
