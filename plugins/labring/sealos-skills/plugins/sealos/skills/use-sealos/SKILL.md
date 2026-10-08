---
name: use-sealos
description: >
  Deploy and operate apps on Sealos Cloud: sign in to a Sealos account, deploy
  any project or self-hosted app (from the template store, an official Docker
  image, or project source code), provision managed databases (PostgreSQL,
  MySQL, MongoDB, Redis, Kafka), create S3-compatible object storage, expose
  public HTTPS domains, check status and logs, and troubleshoot failures. Use
  this skill whenever the user mentions Sealos (in any language, e.g. "部署到
  Sealos"), or asks to deploy, host, or self-host an application, website, or
  database without naming another platform. Typical trigger: "deploy X to
  Sealos" / "帮我把 X 部署到 Sealos".
allowed-tools: Bash(kubectl:*), Bash(python3:*), Bash(docker:*), Bash(curl:*), Bash(bash:*), Bash(git:*), Bash(gh:*), Bash(command:*)
---

# Use Sealos

## Sealos resource model

Sealos Cloud is a multi-tenant Kubernetes platform. Everything a user owns
lives in one **namespace** (`ns-xxx`) per **workspace**, accessed with a
restricted **kubeconfig** (`~/.sealos/kubeconfig`). Within the namespace:

- **Apps** are ordinary Deployments/StatefulSets + Service + Ingress, labeled
  `cloud.sealos.io/app-deploy-manager: <app>` so the Sealos "App Launchpad" UI
  can manage them. Public HTTPS comes free via `<host>.<region-domain>` and a
  wildcard cert.
- **Databases** are KubeBlocks `Cluster` CRs managed by the "Database" UI.
- **Template store** hosts 200+ one-click templates (`sealos-api.py
  store-list`); deployed templates are tracked as instances and appear in the
  UI.
- **Object storage** buckets are `ObjectStorageBucket` CRs with S3-compatible
  credentials in managed secrets.
- A **region** is one cluster + domain (e.g. `usw-1.sealos.io` for
  international, `bja.sealos.run` etc. for China). The Template API lives at
  `https://template.<region-domain>`.

## Tools

Resolve `scripts/` and `references/` against this skill's directory, not the
project working directory.

- `scripts/sealos-api.py` — auth (`status`, `login`, `workspaces`, `switch`)
  and the Template API (`deploy`, `store-list`). Deploying through the
  Template API (not raw `kubectl apply`) is what makes resources show up as a
  deletable unit in the Sealos UI.
- `kubectl` with `export KUBECONFIG=~/.sealos/kubeconfig` — all reads,
  debugging, and deletions. The kubeconfig is namespace-scoped; you cannot see
  or touch other tenants.
- `scripts/wait-app.sh` — post-deploy verification (workload readiness + URL
  probe + failure diagnostics).
- `docker buildx` — only for the source-build path.

## Preflight

If `SEALAI_DEPLOY_MODE` is `managed` (a Brain-managed sandbox), stop here and
follow [../sealos-deploy/SKILL.md](../sealos-deploy/SKILL.md) instead — that
mode forbids login and interactive prompts. Everything below is the local
interactive path.

```bash
python3 scripts/sealos-api.py status
```

- `authenticated: true` → proceed; note `namespace` and `region_domain`.
- Not authenticated → run `python3 scripts/sealos-api.py login` **in the
  background**, watch its stderr, and relay the sign-in URL to the user the
  moment it prints (the code expires; never sit silently until the command
  ends). Users can alternatively paste a kubeconfig from the Sealos web
  console (top-left avatar → kubeconfig) into `~/.sealos/kubeconfig`.
- Wrong region? `login --region <url>`. Wrong workspace? `workspaces` +
  `switch <name>`.

Deploys, database creation, and storage consume the account's quota/balance —
if a deploy is rejected with a quota error, report it; do not silently retry
with smaller numbers.

## Deploy decision tree (the 15-minute path)

When the user wants something deployed, classify it FIRST — the wrong path
wastes the whole time budget:

1. **Known self-hosted product** (Uptime Kuma, Metabase, n8n, ...):
   `python3 scripts/sealos-api.py store-list --search <name>`.
   - Store hit → deploy the store template ([deploy.md](references/deploy.md),
     Path A). Fastest and battle-tested; done in ~3 min.
   - No store hit → check [recipes.md](references/recipes.md) for a
     ready-made recipe, else use the official Docker image and write a
     template ([deploy.md](references/deploy.md), Path B). **Never build a
     product from source when an official image exists.**
2. **User's own project (has source code)**: look for an existing
   Dockerfile/compose file, else generate one, build for **linux/amd64**,
   push, then deploy the image ([build.md](references/build.md) then
   [deploy.md](references/deploy.md) Path B).
3. **Just a database / bucket**: [databases.md](references/databases.md) /
   platform.md's object storage section — deploy as a minimal template.

After ANY deploy, verify before reporting:

```bash
bash scripts/wait-app.sh -u https://<host>.<region-domain> deployment/<name> [cluster/<name>-pg ...]
```

On `*.sealos.io` regions, local deploys also claim a Brain Project in-script;
if `brain_adoption.ok` is false, or `warnings` still lists
`incompleteResourceSet` after verify, run `sealos-api.py adopt <instance>` —
never redeploy. On `*.sealos.run` this is skipped
(`brain_adoption.reason: not-sealos-io`). See
[deploy.md](references/deploy.md).

## Quick operations

```bash
export KUBECONFIG=~/.sealos/kubeconfig
kubectl get deploy,sts,pods                                   # what's running
kubectl get clusters.apps.kubeblocks.io                       # databases
kubectl get ingress -o custom-columns='NAME:.metadata.name,HOST:.spec.rules[0].host'  # public URLs
kubectl logs deploy/<name> --tail=100                         # app logs
kubectl describe pod <pod>                                    # scheduling/pull issues
kubectl get events --field-selector type=Warning --sort-by=.lastTimestamp | tail -20
kubectl scale deploy/<name> --replicas=2                      # scale
python3 scripts/sealos-api.py store-list --search <query>     # template store
```

## Routing

| Intent | Reference |
|---|---|
| Deploy anything (store template, image, or built artifact) | [deploy.md](references/deploy.md) |
| Dockerfile / image build / registry push for user source | [build.md](references/build.md) |
| Provision or connect PostgreSQL/MySQL/MongoDB/Redis/Kafka | [databases.md](references/databases.md) |
| Manifest rules when writing template YAML (labels, Ingress, storage, quota ladder, object storage) | [platform.md](references/platform.md) |
| Status, logs, debugging, scaling, deletion, cost hygiene | [operate.md](references/operate.md) |
| Per-app recipes for popular self-hosted software | [recipes.md](references/recipes.md) |
| Brain managed sandbox (`SEALAI_DEPLOY_MODE=managed`) | [../sealos-deploy/SKILL.md](../sealos-deploy/SKILL.md) |

Load only what the task needs — usually one reference, two at most.

## Execution rules

1. **Never report a deploy as successful without evidence**: `wait-app.sh`
   exits 0 AND the public URL returns a real page (2xx/3xx, and for
   SSR apps the body is not an error page). If verification fails, triage via
   [operate.md](references/operate.md) — do not re-deploy blindly.
2. Production images are built and pushed as **linux/amd64** (`docker buildx
   build --platform linux/amd64`). Apple Silicon defaults produce arm64
   images that crash-loop on Sealos with `exec format error`.
3. Resource requests/limits follow the platform ladder
   ([platform.md](references/platform.md)); requests are derived from limits,
   and memory always uses `Mi` values.
4. Deploy through the Template API. Fall back to `kubectl apply` only for
   single resources during debugging, and remember `kubectl apply` rejects
   Deployment+`volumeClaimTemplates` (use StatefulSet).
5. Destructive actions (deleting apps, databases, buckets; switching
   workspace on a shared machine), public-access changes, credential rotation,
   and system-tool installation require explicit user confirmation first.
6. Never print secret values. Read them into shell variables or pipe them;
   show the user only names and how to fetch values.
7. After mutations, read back state (`kubectl get ...`) before describing it.
8. One deploy at a time per app name; name collisions in a shared namespace
   break selectors. Random suffixes (`-a1b2c3d4`) are there for a reason —
   keep them.
9. If the agent sandbox blocks writes outside the workspace, escalate file
   access for writing `~/.sealos/kubeconfig`, using the Docker socket, and any
   command that must read that kubeconfig.

## Response format

After each operation report: what was deployed/changed (names + namespace),
the public URL if any, verification evidence (ready state, HTTP code), and
credentials location (secret names, never values). On failure: the failing
resource, the decisive log/event lines, and the next action you are taking.
