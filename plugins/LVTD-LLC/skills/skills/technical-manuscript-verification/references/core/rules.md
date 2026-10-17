# Technical Manuscript Verification Rules

Use these rules when auditing technical manuscripts for runnable accuracy and reader safety.

## Core Rules

### 1. Verify What Can Be Verified

Do not stop at "looks right" when execution or inspection is practical.

- Run commands in a clean or clearly described environment.
- Lint or parse config and code blocks where tools exist.
- Check links and official documentation for volatile claims.
- Render or inspect diagrams and screenshots when layout matters.

### 2. Name The Supported Environment

Every technical instruction implies an environment.

- State OS, architecture, shell, package manager, runtime, tool version, provider, and hardware when relevant.
- If variants are supported, mark which steps differ.
- If variants are not supported, say so.

### 3. Track Evidence Per Item

Keep a verification table.

- Mark each item as verified, failed, partially verified, untested, or unsafe to test.
- Include the method used.
- Include the exact fix or remaining evidence needed.

### 4. Prioritize Reader Risk

Fix high-risk items first.

- Security exposure, privacy harm, data loss, irreversible changes, and cost surprises outrank style.
- Broken prerequisites outrank minor output mismatches.
- Commands with destructive flags require context and rollback.

### 5. Verify Expected Outputs

A reader needs to know whether each step worked.

- Include expected command output, status, page state, file path, or test result.
- Explain acceptable variation.
- Add troubleshooting when the expected result is absent.

### 6. Treat Current Details As Perishable

Tool-specific steps, UI paths, vendor pricing, policies, package names, and version-sensitive commands can drift.

- Verify against primary sources when giving precise current instructions.
- Move volatile walkthroughs to updateable companion resources when possible.
- Keep the book focused on durable concepts and decision frames.

## Guidelines

- Prefer small verification passes by chapter or artifact type.
- Keep raw logs or command outputs when they help reproduce a finding.
- Do not run destructive commands against real user systems.
- Ask for a safe fixture, container, sample repo, or dry-run mode when needed.
- Separate author preference from technical necessity.

## Exceptions

- **Unsafe commands**: Do not execute destructive, privileged, costly, or externally visible commands unless the environment is explicitly disposable.
- **Unavailable systems**: Mark as untested and state the evidence needed.
- **Proprietary tools**: Use documentation, screenshots, or user-provided access notes when direct verification is impossible.

## Quick Reference

| Rule | Summary |
|------|---------|
| Verify | Run or inspect what can be checked. |
| Environment | State where instructions are supported. |
| Evidence | Track method and result per item. |
| Risk | Fix harmful failures before polish. |
| Output | Show readers what success looks like. |
| Drift | Check current details or move them online. |
