---
name: k8s-kaniko-job
description: >
  Sandbox build executor for Sealos deploys: build a container image from
  source with an in-cluster Kaniko Job and push it to GHCR, for environments
  without a Docker daemon (Brain managed Devbox sandboxes). Use only when a
  managed deploy (SEALAI_DEPLOY_MODE=managed) needs an image built from
  project source; local interactive deploys build with docker buildx instead
  (see the use-sealos skill).
allowed-tools: Bash(kubectl:*), Bash(python3:*), Bash(tar:*), Bash(curl:*), Bash(bash:*)
---

# K8s Kaniko Job

Builds `linux/amd64` images inside the Kubernetes namespace when no Docker
daemon exists. One script owns the whole flow — do not hand-roll Jobs or
Secrets around it:

```bash
python3 scripts/kaniko-build.py --image ghcr.io/<owner>/<repo>:<tag> \
  [--context <dir>] [--dockerfile <path-relative-to-context>] \
  [--build-arg KEY=value ...]
```

Resolve `scripts/` against this skill's directory. Run the script from the
project workspace so it finds `.sealos/build-runtime.json`.

## How it works

```text
tar the context (excludes .git/.sealos/.versitygw-*)
  → DevBox-local VersityGW S3 store (POSIX dir, served on port 1319)
  → Kaniko Job in the current namespace pulls s3://... via the
    Job-reachable endpoint from .sealos/build-runtime.json
  → pushes the tagged image to ghcr.io with a build-only registry Secret
  → digest captured from the pod termination message
```

Everything is resolved automatically, in order: CLI flags →
`.sealos/build-runtime.json` (written by the control plane: Job-reachable
`s3Endpoint`, S3 `secretKeyRef`, build deadline) → DevBox runtime env
(`KANIKO_CONTEXT_POSIX_DIR`, `S3_ENDPOINT`, `SEALOS_DEVBOX_JWT_SECRET`, ...) →
defaults. The Job runs with `backoffLimit: 0`, an active deadline capped at
1800s, `ttlSecondsAfterFinished: 3600`, and the current ServiceAccount.

## Preconditions

- `kubectl` pointed at the sandbox namespace (injected kubeconfig; the script
  never selects a region, workspace, or other namespace).
- `GITHUB_TOKEN` with the `write:packages` scope. The target image owner must
  equal the token's login, lowercased: `ghcr.io/<login>/<repo>:<tag>`. Tag
  with the commit SHA or a timestamp, never `latest`.
- Namespace permissions to create Jobs/Secrets and read Pods/logs.
- A Dockerfile inside the context (write one first if missing — rules in
  `../use-sealos/references/build.md` §1; the buildx/registry sections of
  that file do not apply here).

## Reading the result

On success stdout is JSON with `digest` and `image_ref`
(`ghcr.io/<owner>/<repo>@sha256:...`). Prefer `image_ref` in deployment
manifests — the digest pin survives tag mutation. If `digest` is null (rare:
termination message lost), fall back to the tag reference in `image`.

`pull` reports downstream pull behavior:

- `anonymous` — the package is public; no pull secret needed.
- `private` — GHCR packages are private by default. Create a pull secret in
  the namespace and reference it from the workload
  (`imagePullSecrets: [{name: <app>-pull}]`, fixed literal name):

  ```bash
  kubectl create secret docker-registry <app>-pull \
    --docker-server=ghcr.io --docker-username=<login> \
    --docker-password="$GITHUB_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -
  ```

- `indeterminate` — verify by watching the first pod pull, and add the pull
  secret if it hits `ErrImagePull`.

## Failure triage

The script reports the Job and namespace on failure without echoing raw Pod
logs or Kubernetes error text, which may contain credentials. Inspect the
named Job and Pods directly, then summarize only redacted findings.

| Symptom | Cause → fix |
|---|---|
| Job pod `ImagePullBackOff` on the executor image | cluster cannot pull `gcr.io/kaniko-project/executor` → report; there is no local fallback |
| Kaniko log: `error uploading context` / S3 connection refused | the Job cannot reach the VersityGW endpoint → check `.sealos/build-runtime.json.s3Endpoint`; never point the Job at 127.0.0.1 |
| Kaniko log: `401/403` on push | token scope or owner mismatch → the script validates both before creating the Job; inspect the token and image owner privately |
| Dockerfile build error | fix the Dockerfile in the workspace and rerun; each run creates a fresh Job |
| Job deadline exceeded | build too slow → trim the context (`.dockerignore`), use smaller base images |

Build-only Secrets (`use-sealos-ghcr-auth-*`) are namespace-local with no TTL;
the Job itself is garbage-collected after an hour. Leave cleanup to sandbox
teardown unless the user asks.

Never print `GITHUB_TOKEN`, S3 credentials, or Secret payloads. Never pass
secrets through `--build-arg` — build args are visible in the Job spec.
`--render-only` prints a synthetic, redacted Job manifest for structural
inspection; it does not reveal values from the runtime contract or build args.
