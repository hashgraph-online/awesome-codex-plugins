# Docker Image

Target guide for a repository whose only deployment signal is a `Dockerfile`: this guide builds the image, pushes it to a registry, and proves the pushed manifest and the running container. Read it after `rules/target-detection.md` routes here. When a `compose.yaml` also exists, the Compose guide owns the run and this one only supplies the build.

## Contents

- Canonical Configuration
- Authentication
- Build And Push
- Success Test
- Status And Logs
- Failure Table
- Approval Required
- Checked
- Sources

## Canonical Configuration

One multi-stage `Dockerfile` builds the artifact in a builder stage and copies only that artifact into a minimal runtime stage. The image is the deliverable here, so the runtime stage carries the whole contract: pinned base, non-root user, exec-form command, health probe, and a build context narrowed by `.dockerignore`.

```dockerfile
# syntax=docker/dockerfile:1

FROM node:22.20.0-bookworm-slim@sha256:0000000000000000000000000000000000000000000000000000000000000000 AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build

FROM gcr.io/distroless/nodejs22-debian12:nonroot@sha256:0000000000000000000000000000000000000000000000000000000000000000 AS runtime
WORKDIR /app
COPY --from=build --chown=nonroot:nonroot /src/dist ./dist
COPY --from=build --chown=nonroot:nonroot /src/node_modules ./node_modules
USER nonroot:nonroot
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD ["/nodejs/bin/node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
ENTRYPOINT ["/nodejs/bin/node", "dist/server.js"]
```

| Rule | Why it is in the template |
|---|---|
| `# syntax=docker/dockerfile:1` on line 1 | Pins the BuildKit frontend, so cache and secret mounts behave the same on every machine instead of falling back to a bundled frontend |
| Base pinned by tag **and** digest | A tag is mutable; the digest is the bytes that were reviewed. Keep the human tag next to it for the update path |
| Named builder stage plus a minimal runtime stage | The toolchain, source, and dev dependencies stay behind; only the built artifact enters the final image |
| `COPY --from=build --chown=…` | The runtime files are owned by the non-root user before `USER` drops privilege |
| `USER` with an explicit uid or name | Process starts unprivileged. Naming a group drops every other group membership, and an image with no primary group runs as `root` |
| `ENTRYPOINT`/`CMD` in exec form | Shell form runs under `/bin/sh -c`, so the app is not PID 1 and never receives `SIGTERM`. `JSONArgsRecommended` flags this |
| `HEALTHCHECK` with `--start-period` | Probe failures during `start-period` do not count against `--retries`, which prevents a slow boot from being marked `unhealthy` |
| `.dockerignore` next to the `Dockerfile` | Keeps secrets, `.git`, `node_modules`, and build output out of the context, so `COPY . .` cannot ship them |

The update path for a digest pin is paired, never optional: a bot rewrites the digest on a schedule (Dependabot with `package-ecosystem: docker`, or `docker scout recommendations` to see the suggested base), and a human reviews the diff. Refreshing only the base is `docker build --pull`; rebuilding every stage is `--no-cache`, and they solve different problems.

`.dockerignore` at minimum contains `**/.git`, `**/node_modules`, `**/.env`, `**/.env.*`, `dist`, `build`, and the test fixture directories. Narrow the context before adding a `COPY` exclusion, because an ignored file that a later `COPY` names is a build-check violation, not a smaller image.

Check the file before building, not after pushing:

```sh
docker build --check .
```

`--check` reports violations from the build-check suite and exits non-zero when any are reported, so it is a gate. `SecretsUsedInArgOrEnv` and `JSONArgsRecommended` come from this suite; both are cheaper to fix here than after a registry push.

## Authentication

Log in non-interactively with the token on stdin. A token passed with `-p` lands in shell history and in the process list, so it is never used.

```sh
printf '%s' "$TOKEN" | docker login <registry> -u <user> --password-stdin
```

Check the credential exists without printing it, then feed it to the login:

```sh
[ -n "${GHCR_TOKEN:-}" ] && echo ghcr-token-set
printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u <github-user> --password-stdin
```

| Registry | Credential | Note |
|---|---|---|
| GHCR | `GITHUB_TOKEN` inside a workflow, or a PAT with `read:packages` / `write:packages` | The first push creates a **private** package. Add `LABEL org.opencontainers.image.source=https://github.com/<owner>/<repo>` so the package links back to the repository |
| Docker Hub | PAT or OAT, not the account password | 2FA and SSO accounts reject the password at the CLI; an OAT can be scoped to repositories and kept apart from account usage |

Credentials land in `~/.docker/config.json`, base64 by default, or in a `credsStore` / `credHelpers` helper such as `osxkeychain`, `secretservice`, `wincred`, or `pass`. Prefer the helper. Never log in on the user's behalf: a missing credential stops the run at this step and the exact command is reported.

## Build And Push

Build for the architecture of the host that will run the image, and push in the same command. A local `docker build` on arm64 hardware produces an arm64 image, and that image fails on an amd64 server.

```sh
SHA=$(git rev-parse --short HEAD)
IMG=<registry>/<owner>/<image>:$SHA

docker buildx build \
  --platform linux/amd64 \
  --secret id=npmrc,src="$HOME/.npmrc" \
  --tag "$IMG" \
  --tag <registry>/<owner>/<image>:latest \
  --push .
```

| Choice | Rule |
|---|---|
| Platform | `--platform linux/amd64` when the only runtime is an amd64 server; `--platform linux/amd64,linux/arm64` when both must run. One platform per distinct runtime requirement, not a default pair |
| Tag | The git SHA is the deployable tag. `latest` may ride along for humans but is never the tag a deploy pins. An immutable digest is what a rollback points at |
| Secrets | `--secret id=…,src=…` mounts the value at `/run/secrets/<id>` for the one `RUN` that needs it. `ARG` and `ENV` persist in `docker history` and in provenance attestation, so a token never travels that way |
| Output | `--push` is the output. The `docker-container` driver does not load the result into the local image store, so a build without `--push` or `-o` leaves nothing to inspect locally |
| Cache | `--mount=type=cache` for package manager and compiler caches; mount by `target=` so the two stages do not share a path by accident |
| Verification of the build | `docker build --check .` first, then this push; a failed check is never bypassed by pushing anyway |

When the builder has to be created explicitly (older engines, or CI without a default builder), the push requirement is the trap:

```sh
docker buildx create --name container-builder --driver docker-container --bootstrap --use
docker buildx build --platform linux/amd64 --tag "$IMG" --push .
```

Private Git context needs its own secret form: `--secret id=GIT_AUTH_TOKEN` for Basic auth with the user name `x-access-token`, or `--secret id=GIT_AUTH_HEADER` for an arbitrary header such as GitLab's `CI_JOB_TOKEN`. Per host, name the id after the host, for example `id=GIT_AUTH_TOKEN.github.com,env=GITHUB_TOKEN`.

## Success Test

Success is the pushed manifest listing the runtime platform, and the image starting on a host of that architecture and passing its own health probe.

```sh
docker buildx imagetools inspect <registry>/<owner>/<image>:$SHA
docker run --rm --platform linux/amd64 <registry>/<owner>/<image>:$SHA
docker image inspect -f '{{.Os}}/{{.Architecture}}' <registry>/<owner>/<image>:$SHA
```

- `imagetools inspect` prints one `Platform:` line per manifest entry. `linux/amd64` must appear there, and every additional platform in the tag must be one the runtime actually has.
- A push that exited `0` proves the bytes were accepted, not that the manifest has the right platform. Read the manifest.
- On the target host, `uname -m` decides what will run: `x86_64` needs `linux/amd64`, `aarch64` needs `linux/arm64`.
- A local `docker run` on the build machine can pass through emulation and hide a wrong platform. Confirm on the runtime architecture, or read `.Architecture` from the pulled image.
- Health: the container must reach `healthy` under `docker inspect`, and the probe command must return `0`. A container that is `running` with no health check has proven only that the process started.

## Status And Logs

| Question | Command |
|---|---|
| Manifest platforms and sizes | `docker buildx imagetools inspect <image>:<tag>` |
| What was built and when | `docker image inspect -f '{{.Created}} {{.Os}}/{{.Architecture}}' <image>` |
| Container state, exit code, health | `docker inspect -f '{{.State.Status}} {{.State.ExitCode}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' <container>` |
| Last health probe output | `docker inspect -f '{{json .State.Health}}' <container>` |
| Bounded runtime log | `docker logs --tail 200 --timestamps <container>` |
| Build log of one stage | `docker buildx build --progress=plain --target <stage> .` |
| Registry tags and digests | `docker buildx imagetools inspect <image>` |
| Exit 137 containers | `docker ps -a --filter 'exited=137' --format '{{.Names}} {{.Status}}'` |

Every log command carries `--tail` or a time window; none is left streaming. `State.Health.Log` keeps the last probe output (up to 4096 bytes), which is where a `curl: not found` or a `connection refused` is visible without re-running anything.

Exit codes decide the reading: `0` on a long-running service means the command was not foregrounded; `137` is SIGKILL from an OOM kill or an exceeded stop timeout; `143` is a normal SIGTERM stop. `unhealthy` plus a passing `running` state means the probe itself is wrong, not the process.

## Failure Table

| # | Signature | Cause | Fix | Check | Tier | Source |
|---|---|---|---|---|---|---|
| 1 | `exec format error` at container start, `standard_init_linux.go` in the line | The image was built for the build machine's architecture and pushed to a host of another one | Rebuild with `--platform linux/amd64` (or the host's platform), push the same tag, pull on the host | `imagetools inspect` lists the runtime platform and the container starts | proceed | <https://docs.docker.com/build/building/multi-platform/> |
| 2 | `no matching manifest for linux/amd64 in the manifest list entries` | Only one architecture was pushed, so no manifest entry matches the pulling host | Build and push the missing platform, or a multi-platform tag | the same `docker pull` on the host succeeds | proceed | <https://docs.docker.com/build/building/multi-platform/> |
| 3 | A token or password appears in `docker history`, in an `ARG`/`ENV` line, or in a provenance attestation | The secret was passed as `ARG` or `ENV` instead of a secret mount | Move it to `RUN --mount=type=secret` and pass `--secret` at build time; treat the credential as leaked and rotate it | `docker history --no-trunc <image>` shows no secret, `--check` reports no `SecretsUsedInArgOrEnv` | explicit approval (rotating the credential) | <https://docs.docker.com/build/building/secrets/>, <https://docs.docker.com/reference/build-checks/> |
| 4 | `failed to compute cache key: "/app/x" not found`, or a `COPY` that silently omits files | The file is excluded by `.dockerignore` but named by a `COPY`, or the path is relative to the wrong stage | Fix the `.dockerignore` pattern or the `COPY` path; keep the context narrow and the copy explicit | `docker build --check .` reports no `CopyIgnoredFile`, and the build resolves the path | proceed | <https://docs.docker.com/reference/build-checks/> |
| 5 | Runtime fails with `Cannot find module`, `no such file`, or an empty directory | The artifact stayed in the builder stage, or `COPY --from` names the wrong stage or path | Copy the built artifact from the named builder stage into the runtime stage, and confirm the path inside the builder | the file exists in the final image: `docker run --rm <image> ls <path>` | proceed | <https://docs.docker.com/build/building/multi-stage/> |
| 6 | `permission denied` on a write, a socket bind below 1024, or a cache directory | `USER` is unset, or files were copied as root and are not writable by the runtime user | `COPY --chown=<user>:<group>`, create writable directories before `USER`, and bind an unprivileged port | the container runs and writes its state path as the non-root user | proceed | <https://docs.docker.com/reference/dockerfile/> |
| 7 | Push stalls and fails near ten minutes, or the registry rejects a layer | One layer exceeds the registry's per-layer size, or the upload window closed under a slow link | Split the layer, shrink the artifact, and lower `--max-concurrent-uploads` on a narrow link | the push completes and `imagetools inspect` shows the new digest | proceed | <https://docs.docker.com/reference/cli/docker/image/push/>, <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry> |

## Approval Required

| Action | Tier |
|---|---|
| Reading the manifest, image config, container state, health log, and build-check output; `docker build` to a local tag; editing the `Dockerfile` or `.dockerignore` in the repository | proceed |
| Pushing a new tag to a registry | proceed |
| Pushing an existing tag that a running deployment pins, or re-pushing a tag whose digest is already deployed (it overwrites the tag) | explicit approval |
| Deleting an image or a tag from the registry (`docker buildx imagetools` removal, a registry delete call), pruning a registry, or deleting a local image a deployment still uses | explicit approval |
| Logging in on the user's behalf, creating a registry account or package, printing a token, or asking for the token value in chat | never |

Approval covers the one action it names. An approval to overwrite one tag does not cover the tag on a second environment, and an approval to delete one image does not cover the tag that the deployment is pinned to.

## Checked

> Volatile. Checked 2026-11-07; re-read the live page when a flag, a limit, or a digest decides the run.

| Fact | Value |
|---|---|
| Docker Engine | 27.3.1, run locally on 2026-11-07 |
| Compose | v2.30.3 (`up --wait --wait-timeout --no-deps --force-recreate --remove-orphans`) |
| buildx | v0.18.0, `docker-container` driver available |
| Build checks | `docker build --check` exits non-zero on any reported violation |
| Digest form | `image:tag@sha256:…`; the tag stays for the update path |
| GHCR limits | 10 GB per layer, 10-minute upload window |
| Push concurrency | Five layers at a time by default, `--max-concurrent-uploads` to lower it |
| Health check defaults | `interval` 30s, `timeout` 30s, `start-period` 0s, `start-interval` 5s, `retries` 3 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Pin the base image version to a specific digest for supply-chain traceability | <https://docs.docker.com/build/building/best-practices/> |
| Build arguments are not recommended for passing secrets | <https://docs.docker.com/reference/dockerfile/> |
| Secrets passed as `ARG`/`ENV` persist in the final image; use secret mounts | <https://docs.docker.com/build/building/secrets/> |
| Multi-stage builds leave the toolchain and unwanted files behind, and `--target` selects a stage | <https://docs.docker.com/build/building/multi-stage/> |
| A `linux/amd64` container cannot run on an arm64 host without emulation | <https://docs.docker.com/build/building/multi-platform/> |
| `--check` exits non-zero when violations are reported | <https://docs.docker.com/build/checks/> |
| `SecretsUsedInArgOrEnv` and `CopyIgnoredFile` are build-check rules | <https://docs.docker.com/reference/build-checks/> |
| `docker login` with `--password-stdin` keeps the password out of shell history | <https://docs.docker.com/reference/cli/docker/login/> |
| GHCR login form, private default visibility, `org.opencontainers.image.source` label, 10 GB per layer, 10-minute timeout | <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry> |
| `docker image push` uploads five layers at a time by default | <https://docs.docker.com/reference/cli/docker/image/push/> |
| `--push` is shorthand for `--output=type=registry,unpack=false` | <https://docs.docker.com/reference/cli/docker/buildx/build/> |
| `imagetools inspect` lists each platform in the manifest | <https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/> |
| Exit 137 means the container was killed with SIGKILL | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| `HEALTHCHECK` defaults and the meaning of `start-period` for retries | <https://docs.docker.com/reference/dockerfile/> |
| `docker init` writes `.dockerignore`, `Dockerfile`, `compose.yaml`, and overwrites existing files | <https://docs.docker.com/reference/cli/docker/init/> |
| A multi-platform image cannot be loaded into the local image store | <https://docs.docker.com/build/ci/github-actions/multi-platform/> |
| Scout reports vulnerable packages and recommends a base upgrade | <https://docs.docker.com/scout/> |

### Evidence grade

`DIRECT` for the local tool surface: Docker Engine 27.3.1, Compose v2.30.3, and buildx v0.18.0 were run on 2026-11-07, and the flags in this guide come from those binaries. `SECONDARY` for registry behaviour that only a live registry shows, such as GHCR's per-layer size, the upload window, and first-push visibility; those are quoted from Docker's and GitHub's own documentation and were not exercised against a registry in this environment. The digest in the template is a zeroed example, not a published image: resolve a real digest with `docker buildx imagetools inspect` before using the file.
