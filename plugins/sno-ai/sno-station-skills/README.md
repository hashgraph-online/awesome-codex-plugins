# Sno Station Skills (standalone)

Twelve skills from [Sno Station Skills](https://github.com/sno-ai/sno-station-skills) that work on their
own: no Sno Station programs, no hooks, and no account.

- **less-is-more**: write the least code that works, and cut what an agent over-built.
- **owner-intent-audit**: check plans, tests or code against what the owner actually asked for.
- **agentic-walkthrough**: prove that a reported run caused its real effect, one observable per step.
- **first-principles-review**: challenge a product idea or design before it becomes code. Runs only when you name it.
- **e2e-environment-preflight**: check the services, hosts and endpoints an end-to-end run needs, before it starts.
- **e2e-red-triage**: decide whether one failed end-to-end test is a product defect or an environment fault.
- **charter**: write or review the brief that tells an executor what to deliver and how success is proven.
- **shellscript-coder**, **ts-coder**, **python-coder**, **rust-coder**: write production Shell, TypeScript, Python or Rust that fits the repository, stays small, and is checked with the repository's own commands.
- **test-writer**: write tests that exercise the real code, can fail when it is wrong, and run only what changed.

## What the plugin runs

The skills are instructions for Claude. They read and write files in your project and run shell commands
there, the same way Claude already does when you ask. `first-principles-review` includes two local Python
scripts that extract and check its report. Each skill also ships a self-test under `scripts/selftest/`.
Nothing in this plugin sends data anywhere, calls a remote service, or installs packages.

The full set of 37 skills, most of which work with Sno Station, is in the
[`sno-station` plugin](https://github.com/sno-ai/sno-station-skills#install-as-a-plugin).

Licensed under the Apache License, Version 2.0.
