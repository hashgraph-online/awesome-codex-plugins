# Phase 6.5 Runtime Truth Pass

## Contents

- [Capture live identity](#capture-live-identity)
- [Verify Launchpad public networking](#verify-launchpad-public-networking)
- [Capture the runtime baseline](#capture-the-runtime-baseline)
- [Exercise the application](#exercise-the-application)
- [Verify Event convergence](#verify-event-convergence)
- [Acceptance checklist](#acceptance-checklist)

Run this pass after Template API deploy or kubectl fallback deploy. Accept the deployment only after the live application entry, Launchpad public network, logs, and first meaningful user workflow are verified.

## Capture Live Identity

Read the App URL from the live App resource when possible:

```bash
APP_NAME="<app-name>"
APP_URL=$(KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get apps.app.sealos.io/"$APP_NAME" -n "$NAMESPACE" \
  -o jsonpath='{.spec.data.url}' 2>/dev/null)
```

If the live App resource has no URL, use the URL returned by Template API or the rendered fallback URL.

Collect the runtime footprint before any HTTP request:

```bash
node "<SKILL_DIR>/scripts/sealos-footprint.mjs" \
  --namespace "$NAMESPACE" --app "$APP_NAME"
```

Confirm the live root Ingress backend, application Service, and ready endpoints:

```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get ingress,svc,endpoints -n "$NAMESPACE" \
  -l "cloud.sealos.io/app-deploy-manager=$APP_NAME" -o wide
```

For resources rewritten by Launchpad, inspect all manager-labeled Ingresses and Services. A random network name is valid only when its backend Service, ready endpoints, Launchpad network, and App URL still describe the same public entry.

## Verify Launchpad Public Networking

For every web application with a public root-path Ingress, read the expected public Service port from the rendered template or live Ingress and run:

```bash
PUBLIC_PORT="<public-service-port>"
node "<SKILL_DIR>/scripts/sealos-launchpad-network.mjs" \
  --app "$APP_NAME" \
  --app-url "$APP_URL" \
  --expected-port "$PUBLIC_PORT"
```

Private applications with no public Ingress skip this command. Public application acceptance requires:

- `ok: true`
- API `code: 200`
- at least one network with `openPublicDomain: true`
- a complete public or custom domain
- a network port matching `$PUBLIC_PORT`
- an App URL host matching the Launchpad network host

The helper emits only allowlisted network fields. Treat `launchpad_api_error`, `public_network_missing`, `expected_port_missing`, and `app_url_host_mismatch` as template or live-resource failures. When the public URL works but Launchpad has no public network, verify that the root Prefix Ingress uses `backend.service.port.number`, that the number matches the referenced Service `spec.ports[].port`, and that the App URL has not retained a replaced Service's host.

## Capture The Runtime Baseline

Capture the initial runtime baseline after readiness. This scan records Warning Events as observations while preserving log, Pod readiness, and kubectl failures as blocking findings:

```bash
RUNTIME_EVIDENCE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/sealos-runtime.XXXXXX")
INITIAL_BASELINE="$RUNTIME_EVIDENCE_DIR/initial-baseline.json"
FINAL_RUNTIME_REPORT="$RUNTIME_EVIDENCE_DIR/final-runtime.json"

node "<SKILL_DIR>/scripts/sealos-log-scan.mjs" \
  --namespace "$NAMESPACE" --app "$APP_NAME" --since 10m --tail 300 \
  > "$INITIAL_BASELINE"
```

## Exercise The Application

For every web application:

```bash
node "<SKILL_DIR>/scripts/sealos-live-smoke.mjs" --url "$APP_URL"
```

For login-gated web applications, identify the first-run, registration, or login flow from upstream docs, source code, the rendered template, or observed network/API behavior. Complete the flow and verify at least one authenticated page or API route.

If administrator credentials were collected in Phase 5.5, use those exact deploy-time values for the login smoke. Mask the password in command echoes, logs, summaries, and final output.

When credentials and API paths are known, use the helper for the repeatable HTTP portion:

```bash
node "<SKILL_DIR>/scripts/sealos-live-smoke.mjs" \
  --url "$APP_URL" \
  --captcha-path "/api/get_validate_code" \
  --login-path "/api/login" \
  --username "$ADMIN_USER" \
  --password "$ADMIN_PASSWORD" \
  --auth-path "/api/languages/get"
```

After the browser/API smoke, scan recent logs again:

```bash
node "<SKILL_DIR>/scripts/sealos-log-scan.mjs" \
  --namespace "$NAMESPACE" --app "$APP_NAME" --since 10m --tail 300
```

For applications with private object storage enabled, complete an application-level storage smoke through the authenticated UI or documented API:

1. Upload a uniquely named file with known bytes through the application.
2. Read or download that object through the application and compare its bytes or SHA-256 digest with the source file.
3. Confirm the successful read uses the application's authenticated proxy or a time-bounded presigned URL.
4. Request the raw bucket/object endpoint without application credentials and confirm an access-restricted response such as HTTP 401 or 403.
5. Delete the smoke object through the application when the product supports deletion.

For optional object storage, exercise both supported branches. The local-storage branch must complete upload, read/download, digest comparison, and deletion using its local persistence path. The managed-S3 branch must complete the same workflow through the managed bucket and managed Secret wiring, plus the private raw-object access check.

For web applications, request one random missing path from the real App URL and scan logs once more:

```bash
MISSING_PATH="/__sealos_missing_$(date +%s)"
curl -k -sS -o /dev/null -w "%{http_code}\n" "$APP_URL$MISSING_PATH"
node "<SKILL_DIR>/scripts/sealos-log-scan.mjs" \
  --namespace "$NAMESPACE" --app "$APP_NAME" --since 10m --tail 300
```

## Verify Event Convergence

Finish with an Event convergence comparison. Use 60 seconds as the minimum. Increase the window to cover one complete known reconciliation, health-check, queue, or scheduled-work period:

```bash
STABILITY_SECONDS=60
sleep "$STABILITY_SECONDS"
node "<SKILL_DIR>/scripts/sealos-log-scan.mjs" \
  --namespace "$NAMESPACE" --app "$APP_NAME" --since 10m --tail 300 \
  --baseline "$INITIAL_BASELINE" \
  --min-window-seconds "$STABILITY_SECONDS" \
  > "$FINAL_RUNTIME_REPORT"
```

Parse `$FINAL_RUNTIME_REPORT`. Acceptance requires `ok: true`, zero `active-failure` Events, zero restart deltas, stable Ready transitions, and resolved Secrets referenced by historical `secret not found` Events.

For intentional fault injection, preserve three reports:

1. Capture a pre-injection report for the known-good state.
2. Inject the failure, record its expected symptoms, and recover the workload to Ready.
3. Capture a fresh recovery baseline after Ready, wait the full stability window, and run the final comparison against the recovery baseline.

The pre-injection report proves the fault window. The recovery baseline prevents intentional Warning history from contaminating the final comparison. Any Warning count or last-seen advance, restart delta, Pod replacement, Ready transition, or unresolved Secret after the recovery baseline fails acceptance.

Inspect the live main container startup command for managed app workloads:

```bash
KUBECONFIG=~/.sealos/kubeconfig kubectl --insecure-skip-tls-verify \
  get pod/<pod> -n "$NAMESPACE" \
  -o jsonpath='{range .spec.containers[*]}{.name}{" command="}{.command}{" args="}{.args}{"\n"}{end}'
```

## Acceptance Checklist

- Pods and initContainers are complete or ready.
- Service endpoints are populated.
- Public web apps have a Launchpad report with `ok: true`, the expected Service port, and an App URL host match.
- The actual App URL loads from a fresh session.
- Login-gated apps complete setup/login with deploy-time administrator credentials and one authenticated action. Passwords remain masked in all output.
- A random missing path returns HTTP 404 and the follow-up log scan has no traceback-style `HTTPException` / `NotFound` noise.
- SSR/browser failure text such as `Application error`, `server-side exception`, `Internal Server Error`, and `Unhandled Runtime Error` is absent from smoke responses.
- Recent logs are clear of recurring startup, migration, bootstrap, and access-control failures.
- The final runtime report has `ok: true`, zero `active-failure` Events, zero restart deltas, and a complete stability window.
- Private object-storage flows pass authenticated upload, application read/download, content consistency, and raw-object access restriction checks. Optional local and managed branches each pass their branch-specific workflow.
- Main business containers keep `command`/`args` short and close to the official entrypoint; repeated file preparation, permission repair, database bootstrap, or compatibility self-healing belongs in initContainers, Jobs, or ConfigMap scripts.
- Shell wrappers in main containers end with `exec <final-process>` so signal handling remains correct.
- Database-backed apps have the expected live database objects, because Job completion or TTL cleanup is only historical evidence.

For app-specific guidance, load `<SKILL_DIR>/references/live-smoke-playbooks.md`.
