# Deploying to Sealos

Every path ends as a **template instance**: one deployable, verifiable,
deletable unit tracked by the Sealos UI. All rendered resources carry the
label `cloud.sealos.io/deploy-on-sealos: <instance-name>` — use it for
verification and cleanup.

## Path A — template store (known products; ~3 min)

```bash
python3 scripts/sealos-api.py store-list --search <product>
python3 scripts/sealos-api.py store-get <template>        # inputs + quota
python3 scripts/sealos-api.py deploy-store <template> [--name <instance>] \
  [--args-json '{"KEY":"value"}']
```

- `store-get` shows `args`: entries with `"required": true` and no default
  must be supplied via `--args-json`/`--args-file`. Ask the user only for
  values only they know (their email, external API keys); everything else has
  sane defaults.
- Check [recipes.md](recipes.md) first — it maps popular products to exact
  template names and known-good args.
- The response lists every created resource. The instance name is `name` in
  the response (defaults to `<template>-<random8>`).

## Path B — generated template (official image or built image; ~5-10 min)

For self-hosted products missing from the store, and for user images built via
[build.md](build.md).

1. **Research before writing**: official image + tag, listen port, required
   env, persistence paths, database/cache dependencies. Prefer the project's
   own `docker-compose.yml` as the source of truth. Check
   [recipes.md](recipes.md) for a ready recipe.
2. **Write the template** into `.sealos/template.yaml` (inside the project) or
   a temp dir, following [platform.md](platform.md) exactly:
   - Template CR envelope with `defaults.app_name: <app>-${{ random(8) }}`
   - one KubeBlocks block per database dependency
     ([databases.md](databases.md)), wired via `secretKeyRef`
   - workload (StatefulSet if it writes to disk) + Service + Ingress + App CR
3. **Dry-run** — free validation plus quota preview:
   ```bash
   python3 scripts/sealos-api.py deploy /path/to/template.yaml --dry-run
   ```
4. **Deploy** (drop `--dry-run`). The response `name` is the instance name.

## Brain project (local deploys on `*.sealos.io`)

Brain only exists on international Sealos (`*.sealos.io`, e.g. `usw-1`). After
a successful Template API apply there, `sealos-api.py` claims the instance as
a Brain Project (`brain_adoption` on stdout). Retry with
`python3 scripts/sealos-api.py adopt <instance>` when `brain_adoption.ok` is
false, **or** when `warnings` still contains `incompleteResourceSet` after
verification — never redeploy (that creates a second Instance). Skip adoption
when the current region is `*.sealos.run`, or when Brain managed mode
(`SEALAI_DEPLOY_TASK_ID` / `SEALAI_PROJECT_ID`) already stamped `extraLabels`.

## Verify (every path, no exceptions)

```bash
export KUBECONFIG=~/.sealos/kubeconfig
HOST=$(kubectl get ingress -l "cloud.sealos.io/deploy-on-sealos=<instance>" \
  -o jsonpath='{.items[0].spec.rules[0].host}')
bash scripts/wait-app.sh -t 600 -u "https://$HOST" \
  -l "cloud.sealos.io/deploy-on-sealos=<instance>"
```

`wait-app.sh` waits for Deployments/StatefulSets/KubeBlocks Clusters matching
the selector, fails fast on non-recovering pods with diagnostics, then probes
the URL. Success = exit 0 AND a sensible HTTP code (200/30x; 401/403 is fine
for login-walled apps). For SSR apps also `curl -sL` the page and reject
bodies containing "Application error" / "Internal Server Error".

Heavy apps (Rails/PHP/JVM) can need 1-3 more minutes after pods turn ready
before the first request answers — wait-app keeps probing until the timeout,
so don't shortcut it. If the URL still fails with code 000 while workloads
are ready, check your own network before blaming the app: probe a known-good
host in the same region.

Report to the user: public URL, instance name, initial credentials location
(secret name or template README), and how to remove it
(`sealos-api.py delete <instance>`).

## First-aid table

| Symptom | Cause → fix |
|---|---|
| 409 `ALREADY_EXISTS` | **Check reality before retrying**: the create endpoint is not atomic and sometimes reports 409 for a deploy that actually landed (its internal retry collides with itself). Run `kubectl get all,cluster -l "cloud.sealos.io/deploy-on-sealos=<name>"` — if resources exist, proceed to verification as if the deploy succeeded. If nothing exists, the name is genuinely taken or its resources are still finalizing from an earlier delete (KubeBlocks clusters take minutes) → redeploy under a **fresh** name, never the just-failed one |
| 400 `INVALID_PARAMETER` | missing required args → `store-get`, supply `--args-json` |
| 403/quota message on deploy | namespace quota/balance → report to user, do not shrink silently |
| `ImagePullBackOff` | typo'd tag, arm64-only image, or private registry → fix tag / rebuild amd64 / add pull secret ([build.md](build.md)) |
| `CrashLoopBackOff` | read `kubectl logs` — usually missing env or database not ready yet (KubeBlocks Cluster still starting is normal for the first ~2 min) |
| Pod `Pending` | quota exceeded or PVC unbound → `kubectl describe pod`, lower resources one ladder step or free quota |
| URL 503/404 after ready | Ingress port ≠ Service port, or app binds 127.0.0.1 → check Service/port and the app's bind address |
| Persistent 500, DB up, env correct | writable-dir ownership: an initContainer running as root leaves root-owned files the app user can't rewrite → chown app dirs as the LAST init step; read the app's own error log inside the pod, not just `kubectl logs` |
| `exec format error` in logs | arm64 image on amd64 nodes → rebuild with `--platform linux/amd64` |

Iterating on a failed Path-B deploy: fix the template, `sealos-api.py delete
<instance>`, redeploy. Quick experiments may `kubectl set env/image` directly,
but fold every fix back into the template so the final artifact reproduces.
