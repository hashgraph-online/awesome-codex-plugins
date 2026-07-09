# Live Smoke Playbooks

Use these playbooks after a Sealos Template API deployment reaches rollout success. A running Pod is a scheduling signal; the acceptance signal is the real Sealos App entry URL, app logs, and the first meaningful user workflow.

## Runtime Truth Pass

Run this pass after Phase 6 for every deployment unless the user explicitly asks for deploy-only output.

1. Capture the namespace, app name, Instance name, and actual App URL from the Template API response or the `apps.app.sealos.io` resource.
2. Inspect runtime state with the Sealos kubeconfig:
   - `get pod,app,instances.app.sealos.io,svc,ingress,pvc`
   - `describe pod/<pod>`
   - initContainer logs and main container logs
   - live main container `command`/`args`
   - KubeBlocks Cluster status for database-backed apps
3. Visit the actual App URL exactly as Sealos launches it. Test the root path and the configured App URL path when the app uses an entrance or safe-path mechanism.
4. For login-gated web apps, complete registration or login, confirm a token/session, and open at least one authenticated page or API route.
5. Scan recent logs after login with `scripts/sealos-log-scan.mjs`. Treat recurring application errors as deployment failures even when all Pods are Running.
6. Request one random missing path such as `/__sealos_missing_<timestamp>` against the real App URL. Accept HTTP 404 only when the follow-up log scan stays clear of traceback-style `HTTPException` / `NotFound` noise.
7. Treat visible SSR/browser failure text such as `Application error`, `server-side exception`, `Internal Server Error`, and `Unhandled Runtime Error` as failed smoke even when HTTP returns 2xx/3xx.
8. Inventory the full footprint before cleanup or handoff:
   - `instances.app.sealos.io`
   - `apps.app.sealos.io`
   - Deployments/StatefulSets/CronJobs/Jobs
   - Services/Ingresses
   - PVCs
   - KubeBlocks Clusters
9. For test deployments, clean the named footprint only after the runtime pass:
   - Instance resource
   - App resource
   - matching workloads and Jobs
   - matching Services and Ingresses
   - matching PVCs
   - matching KubeBlocks Clusters when created for the test

## Stuck Pod Debug Checklist

Use this checklist when a Pod stays Pending, Init, CrashLoopBackOff, or Ready=false.

- `describe pod` events, initContainer statuses, probes, and mounted volumes.
- Init logs for shell quoting issues, missing files, failed migrations, and database bootstrap errors.
- Main container logs after each template patch, including errors emitted after readiness succeeds.
- KubeBlocks Cluster readiness and database secret names.
- Database objects required by the application. A completed or TTL-expired Job is historical evidence; the target DB state is the acceptance signal.
- PVC binding, permissions, and init copy behavior.
- Instance and App resources, because Template API deployments include a Sealos Instance layer.

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
- One random missing path returns HTTP 404 without traceback-style log noise.
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
- One random missing path returns HTTP 404 without traceback-style dashboard/API log noise.
- Recent dashboard, API, gateway, and worker logs are clear of recurring SSR, migration, auth/session, and service-to-service URL errors.
- Gateway or worker pods that depend on database migrations wait for required tables or migration markers, not only PostgreSQL readiness.
- Public browser URLs and internal service URLs are not mixed: browser-facing config uses public HTTPS hosts, while backend-to-backend config uses Kubernetes Service DNS.

Debug loop:

If the App URL shows `Application error: a server-side exception has occurred`, read dashboard/API logs first, then verify App URL path, public URL env vars, API backend URL, migration completion gates, and Redis/PostgreSQL readiness behavior before reporting success.

## Generic Login-Gated Web App

Minimum smoke:

1. Load the real App URL.
2. Find the login, registration, setup, or bootstrap admin route from upstream docs, source, first-run page, or API traffic.
3. Complete the first-run setup or login with generated credentials.
4. Confirm success with one of:
   - HTTP 2xx JSON success flag
   - token/cookie/session persistence
   - authenticated page loads
   - authenticated API returns app data
5. Request a random missing path and confirm HTTP 404.
6. Scan logs after the authenticated action and missing-path request.

For apps with path-based entrances, visit the exact path configured in the App resource and the root URL. Pick the App URL that succeeds from a fresh browser session.

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
- One authenticated missing path returns HTTP 404.
- Logs stay clear after login and the missing-path request.
- A 60-second stability check keeps the Pod `1/1 Running` with zero restarts.
