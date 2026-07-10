# Runtime Log Hygiene

Use this reference when a live Sealos deployment reaches readiness but app logs still show recurring warnings, errors, tracebacks, or benign-looking route failures.

## Acceptance Pattern

Run log checks at three points for web applications:

1. After the first Ready state.
2. After setup, registration, or login.
3. After one random missing-path request such as `/__sealos_missing_<timestamp>`.

The random missing path should return HTTP 404 and leave recent application logs clear of traceback-style noise.

Treat these recurring signals as template failures until classified and fixed:

- `Traceback`
- `ERROR`
- `WARNING`
- `HTTPException`
- `werkzeug.exceptions.NotFound`
- `OOMKilled`
- `BackOff`
- migration, bootstrap, auth, permission, or database compatibility failures

## Flask, Superset, And AppBuilder

Flask-based applications may log framework-level exceptions for ordinary 404 requests. Superset and Flask-AppBuilder can emit `superset.views.error_handling:HTTPException` with `werkzeug.exceptions.NotFound` even when the browser behavior is correct.

Use exception-type filtering for benign 404 handling:

- Filter `werkzeug.exceptions.NotFound` from the noisy handler or logger.
- Keep other `HTTPException` classes visible.
- Apply the filter before handlers format the traceback.
- Re-run the random missing-path request after the patch.

For Superset templates, prefer a small `superset_config.py` logging filter that suppresses `NotFound` from the Superset error-handling logger and root handlers while keeping other HTTP errors and real exceptions visible.

## Runtime Dependency Installation

Runtime package installation is acceptable only when the upstream image requires a tiny compatibility package and rebuilding the image is outside the template scope.

Use quiet success behavior:

- Redirect installer stdout/stderr to a temporary log.
- Print the install log only when the command exits non-zero.
- Keep successful boot logs focused on app readiness and actionable warnings.

## Image-Bundled Dependency Paths

A Ready pod can still have a broken dependency setup when a template mounts an empty PVC over a path that the image already populates.

Detection signals:

- Logs contain `failed to setup runner dependencies`.
- Logs mention a missing file under a relative or mounted dependency path, such as `dependencies/python-requirements.txt`.
- `kubectl exec` shows the mounted path contains only filesystem bootstrap entries like `lost+found`.

Fix pattern:

1. Check the official image, source tree, or release tag for the missing file.
2. If the image provides the file, remove the PVC/volumeMount for that path.
3. Keep PVCs for real user data and writable runtime state.
4. Redeploy fresh and re-run setup/login plus log scan.

## Ephemeral Local Storage Pressure

Tune `ephemeral-storage` only from live runtime evidence.

Detection signals:

- Events contain `Pod ephemeral local storage usage exceeds the total limit of containers ...`.
- The pod is repeatedly `Evicted` while the workload's main process otherwise starts.
- `kubectl describe pod` shows tight `requests.ephemeral-storage` and `limits.ephemeral-storage` values for the failing container.
- Logs show large runtime extraction or dependency bootstrap shortly before eviction.

Debug pattern:

1. Inspect recent events with `kubectl get events --sort-by=.lastTimestamp` and filter for the workload name, `Evicted`, or `ephemeral`.
2. Inspect the failing container resources with `kubectl describe pod` or `kubectl get pod -o jsonpath`.
3. When the pod survives long enough, run `du -sh /opt /var /var/sandbox /tmp /root /var/cache 2>/dev/null` inside the container to identify runtime-expanded directories.
4. Patch the live workload to the smallest Mi value that covers observed writable-layer usage with startup margin.
5. Observe beyond the previous eviction window, then update both `requests.ephemeral-storage` and `limits.ephemeral-storage` together in the template.

Dify sandbox case study:

- `langgenius/dify-sandbox:0.2.15` expands Node and Python runner assets during startup.
- Observed writable-layer directories included `/opt/node-v20.20.0-linux-x64` at about `167Mi` and `/var/sandbox` at about `174Mi`.
- `300Mi` caused repeated eviction with `Pod ephemeral local storage usage exceeds the total limit of containers 300Mi`.
- `512Mi` kept `dify-sandbox` Ready with zero restarts after the old eviction window.

## Restricted-Compatible Security Context

When the image default UID is verified as non-root through image metadata, upstream docs, or `id` inside a live container, set restricted-compatible security context on managed app workloads and init Jobs:

- Pod level: `runAsNonRoot: true`, `runAsUser`, `runAsGroup`, `fsGroup`, `seccompProfile.type: RuntimeDefault`
- Container level: `allowPrivilegeEscalation: false`, `capabilities.drop: ["ALL"]`

When the image requires root or extra capabilities, document the runtime reason in template comments or review notes and keep the security context aligned with the verified image contract.

## Root Entrypoint With Non-Root Handoff

Some public images start as root, prepare storage, then switch identity through `su-exec`, `gosu`, `setpriv`, or a similar helper. Dropping all capabilities while leaving that handoff path active can break cold start with errors such as `setgroups(...): Operation not permitted`.

Preferred template pattern:

- Verify the final runtime UID/GID from image docs, image metadata, or a live container.
- Run the Pod directly as that UID/GID with `runAsNonRoot`, `runAsUser`, `runAsGroup`, `fsGroup`, and `fsGroupChangePolicy: OnRootMismatch` when persistent storage needs ownership-compatible writes.
- Move first-run config generation, permission preparation, and storage bootstrap into initContainers when the app provides an official offline command.
- Keep the main container close to the official entrypoint or a short `exec` wrapper.
- Validate both the first boot logs and the authenticated user flow before accepting the capability policy.

Use a narrower root/capability exception only when the image's documented runtime requires it after the direct UID/GID pattern is tested.

## Official Offline Config Generation

When an application ships an official command that can generate initial configuration without starting the server, prefer an initContainer that writes the generated files to persistent storage. Pass deployer credentials through declared inputs or env vars, keep the generated config on the PVC, and start the main container with the normal server command.

This pattern is useful for GUI apps with bootstrap credentials because it makes first-run state deterministic and keeps the main process startup small.

## Syncthing Case Study

Observed failure:

- Main container crashed on first boot.
- Logs included `chown: /var/syncthing: Operation not permitted`.
- Logs included `su-exec: setgroups(1000): Operation not permitted`.

Accepted fix:

- Use the verified Syncthing UID/GID `1000`.
- Set Pod security context with `runAsNonRoot: true`, `runAsUser: 1000`, `runAsGroup: 1000`, `fsGroup: 1000`, `fsGroupChangePolicy: OnRootMismatch`, and `seccompProfile.type: RuntimeDefault`.
- Generate GUI config in an initContainer with the official Syncthing command before the server starts.
- Keep the main container on the official server startup path.
- Validate `/rest/noauth/health`, login, an authenticated `/rest/system/status` call, a random authenticated 404, recent logs, and a 60-second stability window.
- The validated minimum app resources were `limits.cpu=100m`, `limits.memory=128Mi`, `requests.cpu=10m`, and `requests.memory=12Mi`.

## Fix Loop

1. Capture pod status, init logs, main logs, and current App URL behavior.
2. Patch the template or mounted config.
3. Deploy fresh or roll the workload.
4. Complete setup/login and one authenticated action.
5. Request a random missing path.
6. Re-scan logs and footprint.
7. Report success only when the live flow and logs are both clean.
