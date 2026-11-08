# Target Detection

Use this rule at the start of every run except `preflight`, before naming a target. It owns the signal order, conflicts, and the one question allowed when the signals do not decide.

## 1. Signals

Read the target root, then match in this order. The first row that matches decides, unless the request names a target.

| Order | Signal file or request fact | Target | Guide |
|---|---|---|---|
| 1 | `.railway/railway.ts`, `.railway/railway.py`, `.railway/railway.go`, `railway.toml`, `railway.json`, or a linked `.railway/` directory | `railway` | `references/targets/railway.md` |
| 2 | `cloudflare.config.ts` (the `cf` CLI path) or `wrangler.jsonc`, `wrangler.json`, `wrangler.toml` (the Wrangler path) | `cloudflare` | `references/targets/cloudflare.md` |
| 3 | `config/deploy.yml` (Kamal), or a server address, SSH host, Coolify, or Dokploy named in the request | `vps` | `references/targets/vps.md` |
| 4 | `compose.yaml`, `compose.*.yaml`, `docker-compose.yml`, `docker-compose.*.yml` | `compose` | `references/targets/compose.md` |
| 5 | `Dockerfile` with none of the above | `docker-image` | `references/targets/docker-image.md` |

Record the deciding file and the line or key that decided it in the target line.

## 2. Conflicts

- The request names a target ("Railway에", "to Cloudflare", "VPS로"): that target wins over the files. When the named target has no configuration yet, the mode is `setup`.
- A `Dockerfile` or compose file next to a platform file is a build input of that platform, not a second target: Railway builds a `Dockerfile` it finds, and a Kamal or Coolify server runs compose or images.
- A compose file plus a server address in the request routes to `vps`, which reads `references/targets/compose.md` as its second guide.
- Two platform files (for example `railway.toml` and `wrangler.jsonc`) with no target in the request: ask one question naming both, recommend the one whose service matches the requested app path, and say the run continues with the recommendation if no answer comes.
- No signal and no target in the request: in `setup`, ask one question listing the five targets with a recommendation from the stack (`Dockerfile`-capable server app → `railway`, static or edge app → `cloudflare`); in any other mode, report that no deployment target was found and stop.

## 3. CLI Check

After the target is decided, check its CLI without network or credentials:

| Target | Check |
|---|---|
| `railway` | `command -v railway && railway --version` |
| `cloudflare` | the project-local binary first: `npx --no-install wrangler --version`, or `npx --no-install cf --version` on the `cf` path |
| `docker-image`, `compose` | `docker --version && docker compose version && docker buildx version` |
| `vps` | `command -v kamal && kamal version` on the Kamal path; `ssh -V` otherwise |

A missing CLI is recorded with its effect. The run never installs one globally; it reports the install command and stops at the step that needs it.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Railway reads `railway.toml` or `railway.json` until 2026-12-01 and replaces them with `.railway/railway.ts` authoring files | <https://docs.railway.com/config-as-code/reference>, `railway config --help` (railway 5.71.0, 2026-11-07) |
| Railway always builds with a `Dockerfile` when it finds one | <https://docs.railway.com/config-as-code/reference> |
| `cloudflare.config.ts` is the `cf` CLI configuration, in open beta | <https://developers.cloudflare.com/cf/projects/cloudflare-config/> |
| New Wrangler projects use `wrangler.jsonc` | <https://developers.cloudflare.com/workers/wrangler/configuration/> |
| Kamal reads `config/deploy.yml` | <https://kamal-deploy.org/docs/configuration/overview/> |

### Evidence grade

`LOCAL` - the signal order and the tie-breaks are this package's design.
