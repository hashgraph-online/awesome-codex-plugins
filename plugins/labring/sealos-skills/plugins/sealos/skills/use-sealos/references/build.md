# Build and push images for Sealos

Only for deploying the user's own source code. Products with official images
never go through this path.

## 1. Find or write a Dockerfile

Use an existing Dockerfile/`docker-compose.yml` if present (compose: each
service becomes a workload; replace database services with KubeBlocks per
[databases.md](databases.md)).

When writing one, requirements that actually matter on Sealos:

- The server must listen on `0.0.0.0`, not `127.0.0.1`, and the port must be
  deterministic (hardcode or default the `PORT` env).
- Multi-stage builds; final stage on a slim/alpine base; run as non-root when
  the app allows.
- Respect lockfiles (`npm ci`, `pnpm install --frozen-lockfile`, `uv sync`,
  `go mod download`) and copy them before source for layer caching.
- Runtime config comes from env vars at deploy time — never bake secrets or
  `.env` files into the image.
- Next.js: set `output: 'standalone'` and copy `.next/standalone`; Vite/CRA
  static sites: build then serve via `nginx:alpine` with the SPA fallback
  (`try_files $uri /index.html`).

Verify locally when docker is available: `docker build` + `docker run` +
`curl localhost:<port>` before pushing — a 2-minute local check beats a
10-minute remote crash-loop.

## 2. Build for linux/amd64 and push

Sealos nodes are amd64. On Apple Silicon a default build produces arm64 and
the pod dies with `exec format error`.

```bash
docker buildx build --platform linux/amd64 -t <registry>/<repo>:<tag> --push .
```

Tag with something traceable (`$(date +%Y%m%d-%H%M%S)` or the git short SHA),
not `latest`.

Registry choice, in order:

1. **GHCR** when `gh` CLI is authenticated:
   ```bash
   gh auth token | docker login ghcr.io -u "$(gh api user -q .login)" --password-stdin
   docker buildx build --platform linux/amd64 -t ghcr.io/<user>/<app>:<tag> --push .
   ```
   The token needs the `write:packages` scope (`gh auth refresh -s write:packages`).
2. **Docker Hub** when `docker login` is already configured: image is
   `docker.io/<user>/<app>:<tag>`.
3. Neither → ask the user which registry to use; do not create accounts.

## 3. Private images: pull secret

GHCR images are private by default. Either make the package public
(`gh api --method PATCH /user/packages/container/<app> -f visibility=public`
— confirm with the user first), or create a pull secret in the Sealos
namespace and reference it from the workload:

```bash
export KUBECONFIG=~/.sealos/kubeconfig
kubectl create secret docker-registry <app>-pull \
  --docker-server=ghcr.io \
  --docker-username="$(gh api user -q .login)" \
  --docker-password="$(gh auth token)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

Then in the workload: `imagePullSecrets: [{name: <app>-pull}]`. Use a **fixed
literal name** (`<app>-pull`), not `${{ defaults.app_name }}` — the secret is
created before the template renders its random suffix, so a templated name
would never match. The secret survives instance deletion and is reused by
redeploys of the same app; delete it manually when the app is gone for good.

## 4. Hand off to deploy

Continue with [deploy.md](deploy.md) Path B using the pushed image reference.
`originImageName` in the workload annotation should be the image you pushed.
