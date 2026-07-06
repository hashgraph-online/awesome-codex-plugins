# `ntm serve` — HTTP API Server

`ntm serve` exposes NTM functionality as a REST API with optional SSE streams and
WebSocket. Canonical routes live under `/api/v1/*`; the legacy `/api/*` tree is kept
for back-compat.

Source: `/dp/ntm/internal/cli/serve.go`, routes in `/dp/ntm/internal/serve/server.go`.

## Contents

- [Launch flags](#launch-flags) — host, port, auth, TLS
- [Auth mode summary](#auth-mode-summary) — `local`, `api_key`, `oidc`, `mtls`
- [Canonical REST map (`/api/v1/*`)](#canonical-rest-map-apiv1)
  - [Introspection](#introspection) — health, version, capabilities, openapi
  - [Config](#config)
  - [Sessions + panes](#sessions--panes)
  - [Agent lifecycle](#agent-lifecycle)
  - [Jobs (idempotent async work)](#jobs-idempotent-async-work)
  - [Robot adapters](#robot-adapters-convenient-single-shot-endpoints)
  - [Attention streams](#attention-streams) — SSE, WebSocket
  - [Additional families](#additional-families) — pipelines, mail, beads, CASS, etc
- [OpenAPI](#openapi)
- [SSE and WebSocket](#sse-and-websocket)
- [Scenario examples](#scenario-examples)

---

## Launch flags

All in `serve.go:55-66`.

| Flag | Default | Purpose |
|------|---------|---------|
| `--host` | `127.0.0.1` | Bind host |
| `--port` | `serve.DefaultPort` (check `ntm config show`) | Port |
| `--auth-mode` | `local` | `local` / `api_key` / `oidc` / `mtls` |
| `--api-key` | `""` | Required with `auth-mode=api_key` |
| `--oidc-issuer` | `""` | e.g. `https://accounts.google.com` |
| `--oidc-audience` | `""` | JWT aud claim |
| `--oidc-jwks-url` | `""` | JWKS discovery URL |
| `--mtls-cert` / `--mtls-key` | `""` | Server TLS cert + key |
| `--mtls-ca` | `""` | Client CA bundle (requires client certs) |
| `--cors-allow-origin` (repeatable) | localhost-only | CORS allowed origins |
| `--public-base-url` | `""` | External-facing URL (for generated links) |

`auth-mode=mtls` automatically selects HTTPS (`serve.go:210-212`).

## Auth mode summary

- **`local`**: no auth — only binds `127.0.0.1` by default. Suitable for localhost IPC.
- **`api_key`**: clients present a static key via `Authorization: Bearer <key>` or `X-API-Key`.
- **`oidc`**: validates JWTs against `--oidc-jwks-url`, checks `aud`/`iss`. Supports rotating keys.
- **`mtls`**: requires both server TLS cert + client cert; the client cert is the credential.

## Canonical REST map (`/api/v1/*`)

Registered in `server.go:972+`. Every mutating route is protected by `RequirePermission`
middleware with per-endpoint permissions enumerated in `serve/rbac.go`.

### Introspection

```
GET  /api/v1/health          GET  /api/v1/version        GET  /api/v1/capabilities
GET  /api/v1/security            GET  /api/v1/doctor         GET  /api/v1/openapi.json
GET  /docs  (Swagger UI, no auth)
```

### Config

```
GET   /api/v1/config
PATCH /api/v1/config
```

### Sessions + panes

```
GET  /api/v1/sessions
POST /api/v1/sessions                         # kernel-mediated create
GET  /api/v1/sessions/{id}                    # details
GET  /api/v1/sessions/{id}/status
POST /api/v1/sessions/{id}/attach
POST /api/v1/sessions/{id}/zoom
POST /api/v1/sessions/{id}/view
GET  /api/v1/sessions/{id}/events
GET  /api/v1/sessions/{id}/agents

# Per-pane
GET    /api/v1/sessions/{sessionId}/panes
GET    /api/v1/sessions/{sessionId}/panes/{idx}
GET    /api/v1/sessions/{sessionId}/panes/{idx}/output
GET    /api/v1/sessions/{sessionId}/panes/{idx}/title
POST   /api/v1/sessions/{sessionId}/panes/{idx}/input
POST   /api/v1/sessions/{sessionId}/panes/{idx}/interrupt
POST   /api/v1/sessions/{sessionId}/panes/{idx}/stream
DELETE /api/v1/sessions/{sessionId}/panes/{idx}/stream
PATCH  /api/v1/sessions/{sessionId}/panes/{idx}/title
```

### Agent lifecycle

```
GET  /api/v1/sessions/{sessionId}/agents
POST /api/v1/sessions/{sessionId}/agents/spawn
POST /api/v1/sessions/{sessionId}/agents/send
POST /api/v1/sessions/{sessionId}/agents/interrupt
POST /api/v1/sessions/{sessionId}/agents/wait
```

### Jobs (idempotent async work)

```
GET    /api/v1/jobs          POST /api/v1/jobs
GET    /api/v1/jobs/{id}     DELETE /api/v1/jobs/{id}
```

### Robot adapters (convenient single-shot endpoints)

Registered at `server.go:1000-1011`:

```
GET /api/v1/robot/status      /health      /snapshot    /digest
    /attention   /dashboard   /terse       /triage
    /plan        /graph       /activity    /alerts
```

### Attention streams

```
GET  /api/v1/attention/stream           # SSE of live events
GET  /api/v1/attention/events           # paginated replay
GET  /api/v1/attention/digest           # aggregated summary
POST /api/v1/attention/items/{cursor}/state    # mark handled
GET  /api/v1/ws                         # WebSocket
```

### Additional families

Registered via helpers in `server.go:1049-1070`:

- `registerPipelineRoutes`  → `/api/v1/pipelines/...`
- `registerMailRoutes`      → `/api/v1/mail/...`
- `registerBeadsRoutes`     → `/api/v1/beads/...`
- `registerScannerRoutes`   → `/api/v1/scanner/...`
- `registerCASSRoutes`      → `/api/v1/cass/...`
- `registerCheckpointRoutes`→ `/api/v1/checkpoints/...`
- `registerSafetyRoutes`    → `/api/v1/safety/...`
- `registerAccountsRoutes`  → `/api/v1/accounts/...`

## OpenAPI

- Live endpoint: `GET /api/v1/openapi.json` (`server.go:1088`).
- Swagger UI mounted at `/docs` and `/docs/` without auth (`server.go:1092-1093`).
- Static spec generator: `ntm openapi generate` (`openapi.go:126`).

## SSE and WebSocket

- `/api/v1/attention/stream` long-polls events; honor cursor replay via `?since-cursor=N`.
- Legacy `/events` (`server.go:952`) provided as back-compat.
- `/api/v1/ws` WebSocket for bidirectional control.

Cursor values are monotonic int64 per server; **not portable across machines**. On
`CURSOR_EXPIRED`, the response includes a `resync_command` ready to paste.

## Scenario examples

```bash
# Local-only, default port
ntm serve

# API-key protected on all interfaces
ntm serve --host=0.0.0.0 --port=7337 \
  --auth-mode=api_key --api-key="$(openssl rand -hex 32)"

# mTLS for mutual auth (external consumers)
ntm serve --host=0.0.0.0 --port=7443 \
  --auth-mode=mtls \
  --mtls-cert=/etc/ntm/server.pem \
  --mtls-key=/etc/ntm/server.key \
  --mtls-ca=/etc/ntm/client-ca.pem

# OIDC federation
ntm serve --auth-mode=oidc \
  --oidc-issuer=https://accounts.google.com \
  --oidc-audience=ntm-prod \
  --oidc-jwks-url=https://www.googleapis.com/oauth2/v3/certs
```
