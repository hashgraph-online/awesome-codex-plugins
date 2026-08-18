# Phase 6.5 Runtime Truth Pass

## Contents

- [Capture live identity](#capture-live-identity)
- [Verify Launchpad public networking](#verify-launchpad-public-networking)
- [Capture the runtime baseline](#capture-the-runtime-baseline)
- [Authenticate and verify routes](#authenticate-and-verify-routes)
- [Repair declarative ownership and credential residue](#repair-declarative-ownership-and-credential-residue)
- [Verify Jobs, logs, and footprint](#verify-jobs-logs-and-footprint)
- [Exercise the application](#exercise-the-application)
- [Verify Event convergence](#verify-event-convergence)
- [Acceptance checklist](#acceptance-checklist)

Run this pass after Template API deploy or kubectl fallback deploy. Accept the deployment only after the live application entry, Launchpad public network, logs, and first meaningful user workflow are verified.

In managed mode, every command shown below that uses `~/.sealos/kubeconfig` must instead use the kubeconfig/context injected into the Devbox (for example the active `KUBECONFIG` path supplied by the runtime). Do not copy it into the workspace or print it. The target namespace is always `SEALAI_NAMESPACE`; local mode keeps the literal local path and auth behavior shown in these examples.

## Runtime Truth Acceptance Contract

Runtime Truth produces one sanitized report at `.sealos/runtime-truth.json` and a typed
handoff to state/Canvas. A successful Template API response, rollout status, or single
HTTP 2xx response supplies deployment evidence; it does not complete Runtime Truth.
Every report names the selected workload class, live App/Instance identity, evidence
paths, redaction status, first/final scan timestamps, stability window, and terminal state.

| Workload class | Required probes | Conditional probes | Stopped/error result |
| --- | --- | --- | --- |
| Public web | live App URL/host, Launchpad public network, numeric Service port match, fresh root and configured entrance, auth/setup action, documented negative route, logs/events/readiness, full footprint | database final state and object flow when declared | `stopped` on runtime pending; `error` on URL/port/auth/log/footprint failure |
| Private web | live workload identity, fresh internal route, documented business action, logs/events/readiness, full footprint | Launchpad and public URL when no public Ingress exists; auth when the release is anonymous | `stopped` when no usable route or required setup proof exists |
| Worker | live workload identity, ready/converged Pods, queue or documented work signal, logs/events, restart delta, full footprint | HTTP smoke and Launchpad | `error` on active failure, restart, or missing work evidence |
| Scheduled job | CronJob identity and schedule, at least one expected Job/Pod result, completion/log evidence, event convergence, full footprint | HTTP smoke, Launchpad, and auth | `stopped` until one schedule period is observed; `error` on failed/non-zero Job |
| Database-backed | application identity, live database objects, migration markers, dependent workload readiness, logs/events, full footprint | HTTP/auth and object flow based on the app contract | `error` when a Job completed without proving final database state |
| S3-backed | application business flow, authenticated upload/read/content/delete, restricted anonymous raw object access, managed bucket/Secret wiring, logs/events, full footprint | local-storage branch when managed S3 is optional | `error` on digest mismatch, public raw object, missing bucket, or unresolved Secret |

All applicable classes capture an initial baseline after readiness and a final comparison
after a minimum 60-second stability window. Increase the window for a known queue,
reconciliation, or schedule period. An advancing Warning Event, restart delta, Pod
replacement, readiness flap, unresolved referenced Secret, active log finding, or
listing error keeps the result `stopped`/`error`.

`success` requires `runtimeReady: true`, `collectionOk: true`, complete redaction, the
strongest applicable probes above, and a verified live identity that matches the state
record. A deploy-only request ends `stopped` with `runtime_pending` until these fields
are present. Only this sanitized report can unlock the read-only Canvas observation tuple;
Canvas receives state/runtime paths and identity summaries while deploy keeps mutation,
cleanup, and rollback ownership.

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

Keep the requested app name, the live Instance/App names, and the returned host as separate values. Template API deployments may generate a different Instance name or ingress host. Use the host returned by the deploy response or live App resource for every subsequent smoke request.

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

When an HTTP Ingress contains several paths, place the root Prefix path `/` before more specific paths. Launchpad discovery and later edits use the first matching root route as the public entry. Keep the root route, manager label, backend Service, numeric port, ready endpoints, and App URL host aligned.

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

## Authenticate and Verify Routes

Run the root request from a fresh session before any setup or login request. For a path-based entrance, exercise both the configured App URL path and `/`; keep the path that reaches the real first-run or login screen as the App URL. A successful status code with SSR/browser failure text remains a failed entry.

Use the selected account flow from Phase 5.5. For deployer-supplied mandatory bootstrap, use the exact administrator values collected and validated during configuration. For runtime-generated mandatory bootstrap, retrieve the resolved credential from its Secret or documented live runtime source into a private local value without printing it, then use it for login. For functional first-user signup, register through the supported first-run form or API after readiness, then reuse that new session for authenticated checks. The helper supports JSON token and cookie-session flows, including dynamic CSRF cookie/header pairs:

```bash
node "<SKILL_DIR>/scripts/sealos-live-smoke.mjs" \
  --url "$APP_URL" \
  --login-method cookie-json \
  --login-path "/rest/noauth/auth/password" \
  --username "$ADMIN_USER" \
  --password "$ADMIN_PASSWORD" \
  --auth-path "/rest/system/status,/rest/system/connections"
```

Keep passwords, bearer tokens, cookies, CSRF values, captcha payloads, and runtime-derived secrets out of command echoes and reports. A runtime-derived credential is acceptable only when an opaque default seed is deterministically transformed and validated by the application startup path before the final process is `exec`-ed.

Use `--token-path` when the login response stores its bearer token outside the default locations. Use `--missing-api-path` for a documented API route that must return 404, and `--missing-page-path` for a browser/SPA route whose shell fallback may return 2xx/3xx. The helper marks an unexpected negative-probe status as a failed step.

## Repair Declarative Ownership and Credential Residue

When startup fails on bootstrap credential validation, classify it as a configuration-contract failure before resource tuning. Reconfirm the exact release's account mode, then repair every declarative layer that can recreate the invalid configuration:

1. Update the source Template first.
2. Follow `ownerReferences`, Instance identity, and manager labels to identify the highest writable live declarative owner, then patch that owner or the emitted Deployment/StatefulSet.
3. Roll out a fresh Pod and wait through one complete controller reconciliation window.
4. Re-read the workload and Pod environment key names to confirm removed administrator/root bootstrap keys remain absent.
5. Parse `kubectl.kubernetes.io/last-applied-configuration` and ControllerRevisions into key-name-only reports. Keep values redacted.
6. Recommend rotation for every credential that reached Template API args, workload history, annotations, or revisions.

Deleting historical annotations or ControllerRevisions requires the user's explicit confirmation. Record retained residue as a rotation requirement in the handoff.

## Verify Jobs, Logs, and Footprint

Capture the full footprint before cleanup or handoff. Include the Sealos `Instance`, App, Deployments/StatefulSets/DaemonSets, CronJobs, Jobs, Services, Ingresses, PVCs, KubeBlocks Clusters, and managed `ObjectStorageBucket` resources. `sealos-footprint.mjs` is read-only; deployment acceptance requires `collectionOk: true`, `runtimeReady: true`, and the expected resource inventory. Treat `cleanupComplete: true` as valid only when the listing succeeded and the filtered resource list is empty.

Treat a completed or TTL-expired init Job as historical evidence. Verify the live database final state directly: required databases, tables/views, extensions, indexes, roles, grants, search paths, and migration markers must exist before the app is accepted. PostgreSQL custom-database Jobs must wait for readiness and be idempotent; dependent workloads must gate on application migration state when required.

The first log scan establishes the baseline. A Pod in `Succeeded` phase with every container exit code `0` is a completed workload and does not create a `pod_not_ready` finding; failed or non-zero completion remains blocking. An init container may appear with `historicalCompletedInit: true` after the baseline when its completion time and exit code predate `baseline.generatedAt`, the Pod UID/restart/completion values are unchanged, and its output is unchanged. The comparison uses the baseline time as the log increment boundary. Any active main-container failure, new init failure, restart delta, readiness flap, advancing Warning Event, unresolved referenced Secret, OOM/CrashLoop, or repeated traceback is blocking.

## Exercise The Application

For every web application:

```bash
node "<SKILL_DIR>/scripts/sealos-live-smoke.mjs" --url "$APP_URL"
```

For login-gated web applications, identify the first-run, registration, or login flow from upstream docs, source code, the rendered template, or observed network/API behavior. Complete the selected account flow and verify at least one authenticated page or API route.

For deployer-supplied mandatory bootstrap, use the exact values validated in Phase 5.5. For runtime-generated mandatory bootstrap, retrieve and use the resolved value without printing it. For first-user signup, use the exact values submitted during registration. Mask passwords in command echoes, logs, summaries, and final output.

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

For S3-backed database applications, verify both planes in the same run: the application uses the expected KubeBlocks database Secret keys and final database objects, while the object-storage branch uses the managed bucket and approved object-storage Secret wiring. A healthy database Pod or a successful Job alone does not prove either final state.

For web applications, request a documented API negative route or unique missing static asset from the real App URL and scan logs once more:

```bash
MISSING_PATH="/api/<documented-missing-route>"
curl -k -sS -o /dev/null -w "%{http_code}\n" "$APP_URL$MISSING_PATH"
node "<SKILL_DIR>/scripts/sealos-log-scan.mjs" \
  --namespace "$NAMESPACE" --app "$APP_NAME" --since 10m --tail 300
```

Use a documented API or route that must return 404 for API-oriented applications. SPA/browser applications may serve the shell with HTTP 200 for arbitrary client routes; probe a unique missing static asset or documented API path and inspect the response content so an HTML fallback does not count as route coverage.

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

## Managed completion handshake

When `SEALAI_DEPLOY_MODE=managed`, Runtime Truth is not complete until the Codex has made the task-scoped MCP call below after **all** applicable checks pass:

```text
deployment_completed({
  workloads: [{ apiVersion, kind, name, namespace }],
  publicUrl: "https://<tenant-domain-app-url>"   // optional: include when the deployment exposes a public URL
})
```

The call has two valid decisions:

- `decision: "accepted_stop"` — Brain observed the reported workload as Ready and, when `publicUrl` was provided, the public URL returned 2xx. End the turn and report the result through the normal Codex response stream.
- `decision: "repair"` — Brain found that a reported workload or Pod is missing or not Ready, or the provided `publicUrl` did not return 2xx. Stay in the same turn, inspect the relevant Pod/events/logs, diagnose the cause, repair or re-apply the template, and call `deployment_completed` again with the current workload references.

Respect `SEALAI_TURN_DEADLINE_AT` as the single hard limit; there is no per-turn or per-repair cap. When the deadline is exhausted, stop with a fatal managed failure rather than claiming success. A missing, unavailable, malformed, or unauthorized `deployment_completed` tool is also a fatal managed failure. Do not replace this handshake with `verify-report.json`, `turn-report.json`, a webhook, or a text assertion.

## Acceptance Checklist

- Pods and initContainers are complete or ready.
- Service endpoints are populated.
- Public web apps have a Launchpad report with `ok: true`, the expected Service port, and an App URL host match.
- Root Prefix routes appear before more specific HTTP paths, and the root backend uses a numeric Service port.
- The actual App URL loads from a fresh session.
- Login-gated apps complete the selected first-user signup or mandatory bootstrap login flow and one authenticated action. Passwords remain masked in all output.
- Source Template and live declarative ownership converge after account-flow repair; removed bootstrap key names stay absent through one reconciliation window, and sensitive historical key names are reported with values redacted.
- A documented API negative route or unique missing static asset returns the expected 404, and the follow-up log scan has no traceback-style `HTTPException` / `NotFound` noise; SPA shell fallback responses are classified by content.
- SSR/browser failure text such as `Application error`, `server-side exception`, `Internal Server Error`, and `Unhandled Runtime Error` is absent from smoke responses.
- Recent logs are clear of recurring startup, migration, bootstrap, and access-control failures.
- The final runtime report has `ok: true`, zero `active-failure` Events, zero restart deltas, and a complete stability window.
- Private object-storage flows pass authenticated upload, application read/download, content consistency, and raw-object access restriction checks. Optional local and managed branches each pass their branch-specific workflow.
- The full footprint includes and then accounts for Instance, App, Jobs, KubeBlocks, PVCs, and ObjectStorageBucket resources.
- Main business containers keep `command`/`args` short and close to the official entrypoint; repeated file preparation, permission repair, database bootstrap, or compatibility self-healing belongs in initContainers, Jobs, or ConfigMap scripts.
- Shell wrappers in main containers end with `exec <final-process>` so signal handling remains correct.
- Database-backed apps have the expected live database objects, because Job completion or TTL cleanup is only historical evidence.

For app-specific guidance, load `<SKILL_DIR>/references/live-smoke-playbooks.md`.
