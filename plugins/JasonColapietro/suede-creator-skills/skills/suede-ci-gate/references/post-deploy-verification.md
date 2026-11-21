# Post-Deploy Verification

Read this only after a production deploy has already landed. The merge gate this skill
wires is a pre-merge control; these are the checks that prove the deploy itself is
healthy. None of them are run by this skill automatically: the deploy pipeline's own
success status is not one of them.

1. **Live URL check**: fetch the production URL and confirm the expected route/page responds with 200. Do not rely on the deploy pipeline's success status alone.
2. **Critical path smoke test**: verify the primary user action works end-to-end on production (sign in, core action, result visible). If the deploy is backend-only, verify the API endpoint returns the expected shape.
3. **Regression check**: confirm the three most-used routes still respond. If analytics or error monitoring is connected, check for a spike in the 5 minutes after deploy.
4. **Rollback ready**: confirm the previous deploy is still accessible and rollback takes < 5 minutes. Document the rollback command before merging, not after.

Ship verdict after post-deploy: **verified** (all checks pass) | **watch** (minor anomalies, monitoring) | **rollback** (critical failure, initiate rollback immediately).

Record the exact command or URL behind each check. A check reported without the command
that produced it is not evidence, and the verdict above is advice to the user: it never
blocks or reverses an action on its own.
