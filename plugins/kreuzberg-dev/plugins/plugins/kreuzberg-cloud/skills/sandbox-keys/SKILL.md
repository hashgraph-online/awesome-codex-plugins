---
name: sandbox-keys
description: Use when the user wants short-lived Kreuzberg Cloud credentials for evaluation, demos, or smoke tests.
license: MIT
---

# Sandbox keys

Sandbox credentials are short-lived evaluation keys for trying Kreuzberg Cloud without creating a production project. They are still credentials and must not be committed to source control or pasted into shared logs.

## Use sandbox keys for

- first-time evaluation
- local demos
- smoke tests against disposable documents
- onboarding flows that verify SDK setup

## Use production keys for

- business-critical workflows
- recurring jobs
- CI on protected branches
- workloads that exceed the sandbox quota

## Handling

Load sandbox keys through the same environment-variable or SDK configuration path as production keys. Do not silently switch an existing production workflow to a sandbox key; ask the user which credential type they want.

Sandbox keys expire automatically. After expiration or quota exhaustion, mint a fresh key or switch to a production key.
