---
name: sealos-deploy
description: >
  Brain managed-mode deploy executor for Sealos Cloud. Use when
  SEALAI_DEPLOY_MODE=managed (a Brain Devbox sandbox) or when the task says to
  run /sealos-deploy: deploy the workspace repository to Sealos through the
  MCP-gated managed pipeline — classify, build via Kaniko if needed, generate
  the canonical template, hand off through template_ready /
  deployment_completed, and verify. Outside managed mode, use the use-sealos
  skill instead.
allowed-tools: Bash(kubectl:*), Bash(python3:*), Bash(curl:*), Bash(bash:*), Bash(git:*), Bash(tar:*), Bash(sha256sum:*), Bash(command:*)
---

# Sealos Deploy (Brain Managed Mode)

Executor half of a two-party contract: this agent analyzes, builds, deploys,
verifies, and repairs inside the sandbox; Brain (the control plane) renders
input forms and gates completion through exactly two MCP tools. Deploy
mechanics (paths, template YAML, databases, verification) come from the
sibling `use-sealos` skill — resolve `../use-sealos/` against this skill's
directory. This file owns only the managed-mode differences.

## Mode gate

Run this flow only when `SEALAI_DEPLOY_MODE` is exactly `managed`. Otherwise
follow [../use-sealos/SKILL.md](../use-sealos/SKILL.md) (interactive local
path) and ignore the rest of this file.

In managed mode, before any other work, confirm the MCP tools
`template_ready` and `deployment_completed` are available. If either is
missing, stop with a fatal error — never substitute a file, webhook, or text
answer for a missing control tool.

## Environment

Brain injects (read these; never enumerate the whole environment):

| Variable | Meaning |
|---|---|
| `SEALAI_DEPLOY_WORKSPACE` | project root, `/home/devbox/project` |
| `SEALAI_NAMESPACE` | target namespace (also `SEALAI_DEPLOY_NAMESPACE`) |
| `KUBECONFIG` | injected namespace-scoped kubeconfig — use as-is |
| `SEALAI_INPUTS_PATH` | fixed user-input file, exists only after the user submits the form |
| `SEALAI_DEPLOY_LABELS_JSON` | platform ownership labels — forwarded verbatim, see Deploy |
| `SEALAI_TURN_DEADLINE_AT` | the only hard time limit |
| `GITHUB_TOKEN` | source builds and private-image pull secrets |

Hard rules (they override the use-sealos execution rules where they differ):

1. Never run `sealos-api.py login`, OAuth, or `switch`. The injected
   kubeconfig is the only credential; `sealos-api.py` and `wait-app.sh`
   pick it up from `KUBECONFIG` automatically.
2. Fully non-interactive. Never ask the user in the agent turn — values only
   the user knows are declared as template `inputs` and collected by Brain's
   form. The managed deployment request authorizes non-destructive mutations
   in the selected namespace. Before deleting a resource or changing public
   access, require explicit authorization in the task or a Brain-collected
   input. If authorization is missing, stop without that mutation and report
   the blocked action to the control plane.
3. Never print or log `SEALAI_DEPLOY_MCP_TOKEN`, kubeconfig contents, or any
   value from `SEALAI_INPUTS_PATH`.
4. No file-based RPC: never create `control.json`, `inputs-required.json`,
   `turn-report.json`, `verify-report.json`, or anything under
   `.sealos/brain/`.
5. Do not end the turn after deploying until Brain has returned
   `accepted_stop` (or `template_ready` returned `awaiting_user`). A turn
   that ends without a control call is a contract violation, except when a
   missing explicit safety authorization makes the requested mutation
   impermissible; report that blocked action without performing it.

## Pipeline

### 1. Classify

Classify the workspace with the use-sealos decision tree
([../use-sealos/references/deploy.md](../use-sealos/references/deploy.md),
[recipes.md](../use-sealos/references/recipes.md)): known self-hosted product
→ store template or official image; user source code → Kaniko build. Skip the
preflight/login part of that skill entirely.

### 2. Build (source path only)

No Docker daemon exists here. Build with the sibling executor:

```bash
python3 ../k8s-kaniko-job/scripts/kaniko-build.py \
  --image "ghcr.io/<token-login>/<repo>:deploy-<git-short-sha>"
```

(paths relative to this skill; run it from `$SEALAI_DEPLOY_WORKSPACE`).
Read [../k8s-kaniko-job/SKILL.md](../k8s-kaniko-job/SKILL.md) first.
Use the returned digest-pinned `image_ref` in the template. If `pull` is
`private`, create the `<app>-pull` secret now (command in that SKILL.md) and
reference it from the workload with the fixed literal name.

### 3. Template at the fixed path

The canonical artifact is exactly
`$SEALAI_DEPLOY_WORKSPACE/.sealos/template/index.yaml`. Brain reads this
path byte-for-byte — no other location counts.

- **Store hit**: materialize the store template locally, then continue on the
  raw-deploy path (the store-instance endpoint is forbidden in managed mode —
  it cannot carry the ownership labels and leaves nothing to hash):

  ```bash
  python3 ../use-sealos/scripts/sealos-api.py store-export <template> \
    --out "$SEALAI_DEPLOY_WORKSPACE/.sealos/template/index.yaml"
  ```

- **Official image / built image**: write the template per
  [../use-sealos/references/platform.md](../use-sealos/references/platform.md)
  (and [databases.md](../use-sealos/references/databases.md) for KubeBlocks
  blocks).

Managed-mode template requirements on top of the platform contract:

- The file must start with the `apiVersion: app.sealos.io/v1` / `kind:
  Template` header, have a non-empty `metadata.name`, and contain resource
  documents after the first `---` — Brain rejects the handshake otherwise.
- Declare every value only the end user can supply (external API keys, admin
  email, ...) in `spec.inputs` with `required: true` and no default. Brain
  renders its form from exactly these. Everything else belongs in
  `spec.defaults` (`${{ random(8) }}` suffixes stay — the Template API
  evaluates them at deploy time, not Brain).
- Never add labels beyond the platform contract; the ownership labels travel
  through the deploy call, not the YAML.

### 4. Handshake: template_ready

```bash
sha256sum "$SEALAI_DEPLOY_WORKSPACE/.sealos/template/index.yaml"
```

Call `template_ready` with only `{"sha256": "<lowercase hex>"}` — the hash of
the final file bytes. Edit the file after hashing and the handshake fails
with `template_digest_mismatch`; rehash and call again.

- **`awaiting_user`** → stop the turn immediately. No Template API call, no
  `kubectl apply`, nothing. Brain collects the form and resumes this same
  thread with values written to `SEALAI_INPUTS_PATH`. After resuming, do not
  change `spec.inputs` (Brain rejects the new schema); rerun `template_ready`
  with the unchanged file, then continue.
- **`continue`** → deploy the same file.
- Tool error → diagnose, fix, retry the same call. Control errors are
  recoverable; missing tools are fatal.

### 5. Deploy

```bash
cd "$SEALAI_DEPLOY_WORKSPACE"
python3 <this-skill>/../use-sealos/scripts/sealos-api.py deploy \
  .sealos/template/index.yaml \
  $(test -f "$SEALAI_INPUTS_PATH" && echo --args-file "$SEALAI_INPUTS_PATH")
```

- User values flow only through `--args-file "$SEALAI_INPUTS_PATH"` — never
  into prompt text, logs, or tool arguments.
- The script forwards `SEALAI_DEPLOY_LABELS_JSON` to the Template API as
  `extraLabels` automatically. Never edit, extend, or re-derive those labels,
  and never invent `deployment-name`/`template-name` labels. The Instance
  name comes from the deploy response (`response.name`) — Brain does not
  supply one.
- Do **not** call `sealos-api.py adopt` (and do not POST
  `adopt-template-instance`). Managed deploys already stamp `brain.io/*` via
  extraLabels; a second claim returns 409. The script skips adoption when
  `SEALAI_DEPLOY_TASK_ID` or `SEALAI_PROJECT_ID` is set, and when the region
  is not `*.sealos.io`.
- Quota or validation errors: fix the template (re-run step 4 — the hash
  changed) or report the failure via the normal repair loop. Never shrink
  resources silently.

### 6. Verify, then deployment_completed

Verify for real before reporting
([../use-sealos/references/deploy.md](../use-sealos/references/deploy.md)
§Verify; triage failures with
[operate.md](../use-sealos/references/operate.md)):

```bash
HOST=$(kubectl get ingress -l "cloud.sealos.io/deploy-on-sealos=<instance>" \
  -o jsonpath='{.items[0].spec.rules[0].host}')
bash ../use-sealos/scripts/wait-app.sh -t 600 ${HOST:+-u "https://$HOST"} \
  -l "cloud.sealos.io/deploy-on-sealos=<instance>"
```

Only after your own checks pass, collect the real references:

```bash
kubectl get deployments,statefulsets -l "cloud.sealos.io/deploy-on-sealos=<instance>" \
  -o jsonpath='{range .items[*]}{.apiVersion}{" "}{.kind}{" "}{.metadata.name}{"\n"}{end}'
```

Call `deployment_completed` with:

- `workloads`: 1–32 refs, each exactly
  `{apiVersion, kind, name, namespace: $SEALAI_NAMESPACE}` — no extra fields
  (the schema is strict). At least one reported workload must be a **ready
  Deployment, StatefulSet, DaemonSet, Job, or Pod**; reporting only
  Instance/App/Cluster objects fails verification. Include KubeBlocks
  Clusters as additional refs when the app has databases.
- `publicUrl` (optional): the `https://<host>` the app serves, only when an
  Ingress exists and your own probe returned 2xx. Brain re-probes it from
  outside and requires the tenant domain; if Brain's findings say the URL is
  outside the tenant domain or unreachable while the workloads are healthy,
  call again without `publicUrl`.

Responses and errors:

- `accepted_stop` → done; end the turn with a normal summary.
- `repair` → the findings are evidence, not commands. Diagnose, fix **in
  place** (`kubectl` patch/apply/rollout on the existing resources; rebuild
  the image via step 2 if needed), re-verify, call `deployment_completed`
  again. Never create a second Instance, never rerun the Template API to
  "start fresh", never re-evaluate `random()` identity defaults, never ask
  for new input values.
- `deployment_completed_throttled` → wait ≥5s, call again.
- `deployment_completed_before_template_ready` → run step 4 first.

There is no repair-count limit; the only limit is `SEALAI_TURN_DEADLINE_AT`.

## Routing

| Need | Reference |
|---|---|
| Deploy-path classification, store/instance mechanics, verification, first aid | [../use-sealos/references/deploy.md](../use-sealos/references/deploy.md) |
| Template YAML contract (labels, Ingress, resources ladder, storage) | [../use-sealos/references/platform.md](../use-sealos/references/platform.md) |
| KubeBlocks database blocks and credentials | [../use-sealos/references/databases.md](../use-sealos/references/databases.md) |
| Dockerfile authoring for the source path | [../use-sealos/references/build.md](../use-sealos/references/build.md) §1 only |
| In-cluster image build | [../k8s-kaniko-job/SKILL.md](../k8s-kaniko-job/SKILL.md) |
| Debugging failed workloads | [../use-sealos/references/operate.md](../use-sealos/references/operate.md) |

Load only what the step needs. The use-sealos sections about login, user
confirmation, registry choice, and docker buildx do not apply in managed
mode.
