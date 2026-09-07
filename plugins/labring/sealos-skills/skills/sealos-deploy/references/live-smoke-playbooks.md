# Live Smoke Playbooks

Use these playbooks after a Sealos Template API deployment reaches rollout success. A running Pod is a scheduling signal; the acceptance signal is the real Sealos App entry URL, app logs, and the first meaningful user workflow.

### Safety Contract: Confirmation and Evidence

Runtime repair, credential changes, public exposure, deletion, cleanup, and rollback are
explicitly confirmed operations. Record the operation, target, impact, confirmation, and
post-action evidence with credentials, cookies, tokens, Secret data, kubeconfig, and full
connection strings redacted. A read-only Runtime Truth report may recommend a mutation;
the deploy pipeline remains the owner that requests confirmation and performs it.

### Runtime Truth Workload Matrix

Apply the strongest applicable row and keep skipped probes explicit in the report:

| Class | Evidence required | Skipped by design |
| --- | --- | --- |
| Public web | App URL/live host, Launchpad network and port, fresh root/entrance, setup or auth, negative route, baseline/final logs/events, readiness, complete footprint | none of the web-entry checks |
| Private web | live identity, internal route, documented business action, baseline/final logs/events, readiness, complete footprint | Launchpad/public-domain check when no public Ingress exists |
| Worker | ready Pods, queue/work signal, logs/events/restarts, complete footprint | HTTP route, Launchpad, browser auth |
| Scheduled job | CronJob schedule, one expected Job/Pod completion, logs/events, full footprint, one schedule stability window | HTTP route and public network |
| Database-backed | live database objects and migrations plus dependent workload readiness | database checks unrelated to the declared app contract |
| S3-backed | authenticated upload/read/digest/delete, restricted raw object, bucket/Secret wiring | managed branch when the app explicitly selects local storage |

Every row still needs `runtimeReady`, `collectionOk`, sanitized output, a first/final
baseline comparison, and a minimum 60-second window. Partial evidence returns a safe
`stopped` or `error` result and never a success claim.

## Contents

- [Runtime Truth Pass](#runtime-truth-pass)
- [First-User Signup and Mandatory Bootstrap](#first-user-signup-and-mandatory-bootstrap)
- [Event Convergence Gate](#event-convergence-gate)
- [Private Object Storage Acceptance](#private-object-storage-acceptance)
- [Stuck Pod Debug Checklist](#stuck-pod-debug-checklist)
- [BillionMail](#billionmail)
- [LLM Gateway / Multi-Service SSR Web App](#llm-gateway--multi-service-ssr-web-app)
- [Generic Login-Gated Web App](#generic-login-gated-web-app)

## Runtime Truth Pass

Run this pass after Phase 6 for every deployment unless the user explicitly asks for deploy-only output.

1. Capture the namespace, requested app name, live Instance/App names, and actual App URL from the Template API response or the `apps.app.sealos.io` resource. Continue with the returned host because Template API may mint a different Instance name or ingress host.
2. Inspect runtime state with the Sealos kubeconfig:
   - run `scripts/sealos-launchpad-network.mjs` for public web apps and require an open public network whose port and host match the live Service and App URL
   - `get pod,app,instances.app.sealos.io,svc,ingress,pvc`
   - `describe pod/<pod>`
   - initContainer logs and main container logs
   - live main container `command`/`args`
   - KubeBlocks Cluster status for database-backed apps
3. Visit the actual App URL exactly as Sealos launches it. Test the root path and the configured App URL path when the app uses an entrance or safe-path mechanism. When an Ingress has several HTTP paths, keep the root Prefix path `/` first so Launchpad discovers the intended public entry.
4. For login-gated web apps, complete the selected first-user signup or mandatory bootstrap login flow, confirm a token/session, and open at least one authenticated page or API route. Use `cookie-json` when the app emits a dynamic CSRF cookie/header pair, and keep credentials, cookies, tokens, and derived secrets masked in every report.
5. Scan recent logs after login with `scripts/sealos-log-scan.mjs`. Treat recurring application errors as deployment failures even when all Pods are Running.
6. Request a documented API negative route or unique missing static asset against the real App URL. API probes must return 404. SPA/browser apps may return the shell with HTTP 200 for client routes, so inspect the response content and accept the result only when the follow-up log scan stays clear of traceback-style `HTTPException` / `NotFound` noise.
7. Treat visible SSR/browser failure text such as `Application error`, `server-side exception`, `Internal Server Error`, and `Unhandled Runtime Error` as failed smoke even when HTTP returns 2xx/3xx.
8. Inventory the full footprint before cleanup or handoff:
   - `instances.app.sealos.io`
   - `apps.app.sealos.io`
   - Deployments/StatefulSets/CronJobs/Jobs
   - Services/Ingresses
   - PVCs
   - KubeBlocks Clusters
   - managed `ObjectStorageBucket` resources
9. For test deployments, clean the named footprint only after the runtime pass:
   - Instance resource
   - App resource
   - matching workloads and Jobs
   - matching Services and Ingresses
   - matching PVCs
   - matching KubeBlocks Clusters when created for the test
   - matching `ObjectStorageBucket` resources when created for the test

The footprint helper must report `collectionOk: true` before cleanup is called complete. Deployment acceptance also requires `runtimeReady: true` and the expected resource inventory. Permission or listing errors keep cleanup unresolved even when the visible workload list is empty.

Cleanup evidence keeps the named `Instance`, App, workloads, Jobs, Services, Ingresses,
PVCs, KubeBlocks resources, and `ObjectStorageBucket` resources together with the
collection report. Retained credential key names and historical Secret/annotation residue
remain rotation findings until the user confirms the cleanup or rotation action.

## First-User Signup and Mandatory Bootstrap

Classify the exact selected release before deployment:

| Account mode | Template behavior | Live smoke |
|---|---|---|
| Functional first-user signup | Keep optional administrator/root inputs and bootstrap injection absent | Register after readiness and verify one authenticated action |
| Mandatory bootstrap, deployer-supplied | Require every documented identity/password input with no default and validate exact upstream rules before deploy | Log in with the exact Phase 5.5 values |
| Mandatory bootstrap, runtime-generated | Omit administrator inputs, deterministically construct and validate the documented credential format, and retain the resolved value in a Secret or documented live runtime source | Retrieve the resolved value without printing it, then complete login and one authenticated action |
| Optional root reconciliation | Use the functional first-user signup contract | Register and verify the optional overlay remains absent |

When first boot exits on password policy, invalid root configuration, or reconciliation validation, inspect configuration before resources. Patch the source Template and highest writable live declarative owner, roll out a fresh Pod, wait through one reconciliation window, and confirm removed bootstrap key names remain absent. Inspect last-applied annotations and ControllerRevisions through redacted key-name-only reports, then recommend credential rotation.

## Event Convergence Gate

Capture an initial `sealos-log-scan.mjs` report after the workload reaches Ready. This no-baseline report records Warning Events as `observed` while log findings, Pod readiness failures, and kubectl errors retain failure status. A Pod in `Succeeded` phase with zero exit codes is a completed workload; failed or non-zero completion remains blocking. Init output from a container that completed before the baseline may be retained as `historicalCompletedInit: true` when completion time, exit code, Pod UID, restarts, and completion markers remain unchanged; the comparison uses the baseline timestamp as the log increment boundary. OOM, CrashLoop, traceback, active init/main failures, and changed completion signals remain blocking.

After the user workflow and missing-path check, wait at least 60 seconds and compare against the initial report:

```bash
node scripts/sealos-log-scan.mjs \
  --namespace "$NAMESPACE" --app "$APP_NAME" \
  > /tmp/sealos-initial-baseline.json

STABILITY_SECONDS=60
sleep "$STABILITY_SECONDS"
node scripts/sealos-log-scan.mjs \
  --namespace "$NAMESPACE" --app "$APP_NAME" \
  --baseline /tmp/sealos-initial-baseline.json \
  --min-window-seconds "$STABILITY_SECONDS"
```

Set `STABILITY_SECONDS` long enough to cover one full documented reconciliation, probe, queue, or scheduled-work period. Stable startup-probe and asynchronous Secret warnings become `historical-transient` after the referenced Secret exists, the Pod remains Ready, the Warning count and last-seen time stay fixed, and restart count stays fixed. A Warning advance, unresolved Secret, Pod replacement, Ready transition, or restart delta becomes `active-failure`.

For intentional fault injection, save a pre-injection report, perform the injection, recover to Ready, and capture a new recovery baseline. Run the final comparison against the recovery baseline after the full stability window. Keep the pre-injection report and injected symptoms as evidence of the controlled fault window.

## Private Object Storage Acceptance

Use this gate whenever object storage is enabled:

1. Authenticate through the real application flow.
2. Upload a uniquely named file containing known bytes through the application UI or documented API.
3. Read or download the object through the application and compare the resulting bytes or SHA-256 digest with the original.
4. Confirm delivery uses the application's authenticated proxy or a time-bounded presigned URL.
5. Request the raw bucket/object endpoint anonymously and confirm access remains restricted with HTTP 401, 403, or an equivalent provider response.
6. Delete the smoke object through the application when deletion is supported.

For optional S3, validate both branches independently. The local branch exercises the same authenticated upload/read/content/deletion workflow against local persistence. The managed branch exercises the workflow against Sealos object storage, verifies managed Secret wiring, and proves private raw-object access. For S3-backed database apps, verify the KubeBlocks Secret keys and required database objects in the same run; bucket credentials and database readiness are separate contracts.

## Stuck Pod Debug Checklist

Use this checklist when a Pod stays Pending, Init, CrashLoopBackOff, or Ready=false.

- `describe pod` events, initContainer statuses, probes, and mounted volumes.
- Init logs for shell quoting issues, missing files, failed migrations, and database bootstrap errors.
- Main container logs after each template patch, including errors emitted after readiness succeeds.
- KubeBlocks Cluster readiness and database secret names.
- Warning Event count/last-seen deltas, Pod Ready transitions, restart deltas, and current existence of Secrets named in `secret not found` Events.
- Database objects required by the application. A completed or TTL-expired Job is historical evidence; the target DB state is the acceptance signal. PostgreSQL init Jobs wait for readiness and are idempotent; migration-dependent workers gate on required tables or markers.
- PVC binding, permissions, and init copy behavior.
- Instance and App resources, because Template API deployments include a Sealos Instance layer.
- ObjectStorageBucket resources and managed object-storage Secrets when the app uses S3.

## BillionMail

Final Sealos-compatible entry behavior:

- `SAFE_PATH` / `SafePath` is empty.
- `apps.app.sealos.io.spec.data.url` points to the root App URL.
- The app launches directly from the root path in Sealos.
- Main container uses `workingDir: /opt/billionmail/core` with only the short wrapper `mkdir -p template && exec ./billionmail`.
- Data preparation, certificate/log-file setup, PostgreSQL compatibility objects, and relay/search-path repair are handled by initContainers or Jobs, not by the main container startup command.

Runtime acceptance:

- Pod reaches `9/9 Running` with zero crash loops after cold start.
- `GET /api/get_validate_code` returns a success response from the root App URL.
- `POST /api/login` succeeds with the generated admin credentials and returns a token/session.
- At least one authenticated API succeeds after login, such as `/api/languages/get`, `/api/settings/get_system_config`, or `/api/domains/list`.
- One documented API negative route or unique missing static asset passes without traceback-style log noise.
- Recent logs are clear of repeated `pg_indexes`, relay compatibility, and `access denied` errors.
- Live pod spec confirms the main container command remains a short exec wrapper and does not contain file preparation, permission repair, or database bootstrap.

Database bootstrap acceptance:

- PostgreSQL contains the compatibility view `public.pg_indexes`.
- PostgreSQL contains relay compatibility objects such as `bm_relay_old` and `uk_relay_domain`.
- The application role search path resolves expected public schema objects.
- InitContainer bootstrap is idempotent and self-healing so a one-shot Job cleanup or TTL expiry does not hide drift.

Bootstrap quoting guidance:

- Avoid PL/pgSQL `DO $$ ... $$` blocks in inline shell commands when a shell-level idempotency check can express the same logic.
- Use `psql -tAc "SELECT ..."` plus guarded `psql -c` or single-quoted heredocs for idempotent object creation.
- Use `psql -v name=value` variable interpolation inside heredocs for sensitive SQL values such as passwords. Do not rely on `psql -c "ALTER ROLE ... :'var'"`; psql colon variables are not expanded in that form.

## LLM Gateway / Multi-Service SSR Web App

Use this playbook for split-service apps with a dashboard, REST API, protocol gateway, docs service, and workers.

Component checks:

- Dashboard/browser entry: visit both root and the App resource URL path from a fresh session.
- API service: check readiness and recent logs before and after login or signup.
- Gateway/API protocol service: check readiness and recent logs; do not require provider credentials for basic startup unless upstream requires them.
- Worker: inspect logs after API migrations complete and after one authenticated dashboard action.
- Docs/static service: verify it serves a page if exposed publicly.

Runtime acceptance:

- The App URL reaches login, signup, or setup without `Application error: a server-side exception has occurred`.
- For login-gated apps, complete signup or login, then open at least one authenticated dashboard page.
- One documented API negative route or unique missing static asset passes without traceback-style dashboard/API log noise.
- Recent dashboard, API, gateway, and worker logs are clear of recurring SSR, migration, auth/session, and service-to-service URL errors.
- Gateway or worker pods that depend on database migrations wait for required tables or migration markers, not only PostgreSQL readiness.
- Public browser URLs and internal service URLs are not mixed: browser-facing config uses public HTTPS hosts, while backend-to-backend config uses Kubernetes Service DNS.

Debug loop:

If the App URL shows `Application error: a server-side exception has occurred`, read dashboard/API logs first, then verify App URL path, public URL env vars, API backend URL, migration completion gates, and Redis/PostgreSQL readiness behavior before reporting success.

## Generic Login-Gated Web App

Minimum smoke:

1. Load the real App URL.
2. Find the login, registration, setup, or bootstrap admin route from upstream docs, source, first-run page, or API traffic.
3. Complete the selected first-user signup or mandatory bootstrap login with the exact credentials for that flow.
4. Confirm success with one of:
   - HTTP 2xx JSON success flag
   - token/cookie/session persistence
   - authenticated page loads
   - authenticated API returns app data
5. Request a documented API negative route or unique missing static asset and confirm the expected 404 response.
6. Scan logs after the authenticated action and missing-path request.

For apps with path-based entrances, visit the exact path configured in the App resource and the root URL. Pick the App URL that succeeds from a fresh browser session.

For SPA/browser shells, arbitrary client routes can intentionally fall back to the shell with HTTP 200. Use a unique missing static asset or a documented API path for the negative-route check, then inspect content and logs together.

### Cookie + Dynamic CSRF Login

Use `scripts/sealos-live-smoke.mjs --login-method cookie-json` for apps whose root page sets a CSRF cookie and whose login API expects a matching dynamic header.

Example:

```bash
node scripts/sealos-live-smoke.mjs \
  --url "https://<app>.<domain>" \
  --login-method cookie-json \
  --csrf-cookie-prefix "CSRF-Token-" \
  --csrf-header-prefix "X-CSRF-Token-" \
  --login-path "/rest/noauth/auth/password" \
  --username "$GUI_USERNAME" \
  --password "$GUI_PASSWORD" \
  --auth-path "/rest/system/status,/rest/system/connections"
```

The helper loads the root page, stores cookies, maps `CSRF-Token-<id>` to `X-CSRF-Token-<id>`, posts JSON credentials, keeps the session cookie, and reuses the dynamic CSRF header on authenticated paths.

### Syncthing GUI

Runtime acceptance:

- `/rest/noauth/health` returns HTTP 200.
- Root HTML exposes the login form.
- `POST /rest/noauth/auth/password` returns HTTP 204 with the deploy-time GUI username/password.
- Authenticated `/rest/system/status` and `/rest/system/connections` return HTTP 200.
- One authenticated documented API negative route returns HTTP 404.
- Logs stay clear after login and the missing-path request.
- A 60-second stability check keeps the Pod `1/1 Running` with zero restarts.
