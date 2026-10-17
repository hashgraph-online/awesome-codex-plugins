# Django Deployment Test Patterns

## Production-Like Smoke Sequence

1. Build the image or package.
2. Run the app with `DEBUG=False` and explicit environment variables.
3. Run migrations against the intended database.
4. Check `/`, health endpoint, or the smallest meaningful user journey.
5. Inspect logs for errors.
6. Verify static assets are served.

Use this before assuming a staging or production failure is infrastructure-only.

## Container Checks

| Risk | Check |
| --- | --- |
| Port mapping | `curl` the host-mapped port and container port deliberately |
| Missing dependency | Start the container from a clean build |
| Static files | Run `collectstatic` and request a known asset |
| Database path | Inspect env vars and filesystem from inside the container |
| Permissions | Write a row or run a management command as the runtime user |
| Logs | Trigger a controlled error in a safe environment and verify logging |

## Environment Variables

Keep production differences explicit:

- `DJANGO_DEBUG` or equivalent.
- `SECRET_KEY`.
- `ALLOWED_HOSTS`.
- Database URL or path.
- Email provider configuration.
- Static file and logging settings.

Tests should fail clearly when required variables are missing.

## Staging Functional Tests

Use staging tests for a small number of cross-system journeys:

- App serves with production settings.
- Database writes persist.
- Static files load.
- Email or external integration is reachable through the intended fake or staging provider.

Avoid running the whole local Selenium suite against staging unless the environment is designed for it.

## Debugging Remote Failures

Collect evidence in this order:

1. HTTP response and current URL.
2. Container or process logs.
3. Effective environment variables, excluding secrets.
4. Database migration state.
5. Static file presence.
6. Network/DNS reachability.

Do not patch around a remote failure until the failed layer is identified.
