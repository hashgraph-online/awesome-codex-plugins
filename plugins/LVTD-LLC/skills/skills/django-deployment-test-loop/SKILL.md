---
name: django-deployment-test-loop
description: "Make Django deployment changes test-driven across Docker, production settings, Gunicorn, WhiteNoise/static files, environment variables, Ansible/server setup, staging smoke tests, and release checks. Use when containerizing Django, preparing production config, debugging staging, automating deploys, or deciding what deployment behavior functional tests should verify."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Deployment Test Loop
  category: Django
  tags: django,tdd,deployment,docker,ansible
---

# Django Deployment Test Loop

Use this skill when deployment work should be proven by running the app in an environment closer to production. The goal is not to test Docker or Ansible for their own sake; it is to catch integration failures that ordinary dev-server tests miss.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 9-12, 18, 23, and Appendix A, especially Docker checks, production settings, static files, environment variables, Ansible deployment, staging functional tests, and server debugging.

## Workflow

1. Name the deployment risk.
   - Static files, production settings, database path, permissions, secrets, migrations, logging, email, hostnames, or container networking.

2. Choose the smallest production-like check.
   - Docker build/run smoke test.
   - Functional test against the container.
   - Staging functional test after deploy.
   - Server log or management-command check when browser tests are not the right proof.

3. Make configuration explicit.
   - Use environment variables for production differences.
   - Keep secrets out of images and source.
   - Fail fast for missing required settings.

4. Verify the deployed surface.
   - Run migrations in the deployed environment.
   - Check static collection/serving when `DEBUG=False`.
   - Check host allow-list and database write location.
   - Inspect logs for errors rather than relying only on HTTP status.

Read [deployment-patterns.md](references/deployment-patterns.md) for container, staging, and debugging patterns.

## Decision Rules

- If a failure only appears with `DEBUG=False`, reproduce with production-like settings locally first.
- If the problem involves filesystem permissions or mounted volumes, verify inside the running container.
- If the problem involves server config, run a staging smoke test before production.
- If a test needs real server data setup, use a safe management command or explicit fixture path, never ad hoc production mutations.
- If the deployment step is manual twice, consider codifying it in Ansible or the existing deployment tool.

## Guardrails

- Do not bake secrets or mutable database files into container images.
- Do not rely on local SQLite behavior as proof of deployed persistence.
- Do not run test setup commands against production unless the command is designed and guarded for that environment.
- Do not treat a successful image build as proof the app works.

## Verification

Before finishing, record:

- Risk being tested.
- Local Docker or staging command used.
- Migration/static/env/log evidence.
- Browser or HTTP smoke result.
- Rollback or cleanup note when deployment state changed.
