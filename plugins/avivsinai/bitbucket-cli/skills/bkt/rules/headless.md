# Headless / CI authentication

Use `BKT_TOKEN` + `BKT_HOST` to run `bkt` in containers and CI pipelines without a prior `bkt auth login` or `bkt context create` step.

## Quick start

```bash
# Data Center — token-only bearer auth (default when no username is set)
export BKT_HOST=https://bitbucket.example.com
export BKT_TOKEN=my-personal-access-token
export BKT_PROJECT=MYPROJ   # optional default project
export BKT_REPO=my-service  # optional default repo
bkt pr list

# Bitbucket Cloud user API token — basic auth; username is required
export BKT_HOST=https://bitbucket.org
export BKT_TOKEN=my-api-token
export BKT_USERNAME=me@example.com
export BKT_WORKSPACE=my-workspace
export BKT_REPO=my-repo
bkt pr list

# Bitbucket Cloud repository/project/workspace access token — bearer auth
export BKT_TOKEN=my-resource-access-token
export BKT_AUTH_METHOD=bearer
unset BKT_USERNAME
bkt pr list
```

## Auth method rules

| Scenario | Resolved auth method |
|---|---|
| DC, no `BKT_USERNAME`, no `BKT_AUTH_METHOD` | `bearer` (default) |
| DC, `BKT_USERNAME` set, no `BKT_AUTH_METHOD` | `basic` |
| DC, `BKT_AUTH_METHOD=bearer` | `bearer` |
| DC, `BKT_AUTH_METHOD=basic` + no `BKT_USERNAME` | **error** — set `BKT_USERNAME` |
| Cloud, no `BKT_AUTH_METHOD` | `basic` (default); `BKT_USERNAME` is required |
| Cloud, `BKT_AUTH_METHOD=basic` | `BKT_USERNAME` is required |
| Cloud, `BKT_AUTH_METHOD=bearer` | bearer; `BKT_USERNAME` is not required |

## Environment variables

| Variable | Description |
|---|---|
| `BKT_TOKEN` | Authentication token. Bypasses keyring. |
| `BKT_HOST` | Bitbucket server URL. Required with `BKT_TOKEN` for config-free use. |
| `BKT_USERNAME` | Username for basic auth. Required for Cloud basic auth; optional for DC and Cloud bearer auth. |
| `BKT_AUTH_METHOD` | Auth method: `basic` or `bearer`. DC defaults to `bearer` when no username is set; Cloud defaults to `basic`. Use `bearer` for Cloud repository, project, or workspace access tokens. |
| `BKT_PROJECT` | Default Data Center project key. |
| `BKT_WORKSPACE` | Default Bitbucket Cloud workspace. |
| `BKT_REPO` | Default repository slug. |
| `BKT_CONFIG_DIR` | Config directory override. |
| `BKT_ALLOW_INSECURE_STORE` | Allow file-based credential storage. |
| `BKT_KEYRING_TIMEOUT` | Keyring operation timeout (e.g. `2m`). |
| `BKT_OAUTH_CLIENT_ID` | OAuth consumer key. Used at runtime when not embedded via ldflags (e.g. source and Nix builds). |
| `BKT_OAUTH_CLIENT_SECRET` | OAuth consumer secret. Same fallback logic as `BKT_OAUTH_CLIENT_ID`. |

## Saved-host behaviour

When `BKT_HOST` matches a host already in `~/.config/bkt/config.yml`, the saved entry is used as the base (preserving fields like `username` and `auth_method`). `BKT_TOKEN` always overrides the stored token. `BKT_USERNAME` and `BKT_AUTH_METHOD`, when set, override the saved values.

Cloud resource access tokens are not associated with a user. Commands that
require authenticated-user identity, such as cross-repository
`bkt pr list --mine`, still require user API-token or OAuth credentials.

## Bitbucket Pipelines example

```yaml
# bitbucket-pipelines.yml
pipelines:
  default:
    - step:
        script:
          - bkt pr list --mine
        variables:
          BKT_HOST: https://bitbucket.example.com
          BKT_TOKEN: $MY_PAT_SECRET
```
