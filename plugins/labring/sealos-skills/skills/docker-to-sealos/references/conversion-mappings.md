# Docker to Sealos Conversion Mapping Guide

This document provides detailed mapping rules from Docker Compose configuration to Sealos templates.

## Dual-Source Input Merging (Compose + Official Kubernetes)

When an application provides both a Docker Compose file and an official Kubernetes installation method, the conversion must use dual-source merging rather than single-source inference.

### Merging Principles

1. Sealos specifications and SKILL MUST rules take priority (security/platform constraints must not be violated)
2. The official Kubernetes installation method takes priority over Compose for application runtime semantics
3. The existing Template serves as the topology baseline during updates; the selected Compose services and `deploy.replicas` values serve as the topology baseline for new conversions
4. Generic default values are only used when the above sources are absent

### Key Alignment Fields

- First-time initialization and admin bootstrap fields (bootstrap admin/org/user/password)
- External access related fields (domain/port/secure/tls termination assumption)
- Protocol and gateway behavior (Ingress backend protocol, service appProtocol, path routing)
- Health checks and startup ordering (liveness/readiness/startup probe)
- Officially recommended startup parameters and commands

### Conflict Resolution

When the official Kubernetes method conflicts with Compose:

- Preserve Sealos MUST and security rules
- Align bootstrap fields, external endpoints, protocols, probes, startup ordering, and other runtime semantics with the official Kubernetes method
- Retain the selected source's topology-bearing resources, feature conditions, and replica counts
- Record key decisions in the output (only record items with ambiguity)

## Source Topology Preservation

Treat topology and runtime semantics as separate contracts. The source Template or selected Compose mode defines the topology-bearing resource inventory, feature conditions, and replica counts. Official Kubernetes docs/manifests refine runtime behavior within that topology.

A component is runtime-required when the selected source mode cannot start or provide its documented core behavior without that component. An official chart default, production recommendation, scaling example, or optional worker does not make the component runtime-required. Add optional or recommended workers, caches, and HA replicas only when the selected source topology or explicit user intent includes them.

Keep application feature inputs isolated. A database input may gate its database Cluster and related bootstrap resources. An object-storage input may gate its ObjectStorageBucket and documented storage settings. Those inputs must not change unrelated workload inventory, worker/cache presence, or replica counts.

For topology-sensitive work, record the exact expected contract in `.sealos/topology-evidence/<app-name>.yaml`. Keep this validator-only evidence outside `template/<app-name>/index.yaml`.

```yaml
apiVersion: docker-to-sealos/v1
kind: TopologyEvidence
metadata:
  name: demo-topology
spec:
  appName: demo
  source: template/demo/index.yaml@base-revision
  resources:
    - kind: StatefulSet
      name: ${{ defaults.app_name }}
      when: always
      replicas: 1
    - kind: Cluster
      name: ${{ defaults.app_name }}-pg
      when: inputs.enable_postgresql === 'true'
      components:
        - name: postgresql
          replicas: 1
    - kind: ObjectStorageBucket
      name: ${{ defaults.app_name }}
      when: inputs.enable_s3_storage === 'true'
```

Evidence contract:

- `spec.appName`: Template `metadata.name` and evidence filename.
- `spec.source`: existing Template revision, selected Compose URL/revision, or another stable source identifier.
- `spec.resources`: exact multiset of topology-bearing resources.
- `kind` and `name`: resource identity. Supported kinds are `Deployment`, `StatefulSet`, `DaemonSet`, `CronJob`, KubeBlocks `Cluster`, and `ObjectStorageBucket`.
- `when`: `always` for unconditional resources or the normalized inner `${{ if(...) }}` condition. Nested conditions use ` && ` in nesting order.
- `replicas`: required positive integer for `Deployment` and `StatefulSet`.
- `components`: required list of unique `{name, replicas}` objects for KubeBlocks `Cluster` component specs.

One-shot `Job` resources remain outside topology evidence and continue through their dedicated bootstrap rules.

Run topology validation with both files:

```bash
python scripts/check_consistency.py --skill SKILL.md --references references --rules-file references/rules-registry.yaml --artifacts template/demo/index.yaml,.sealos/topology-evidence/demo.yaml
```

## Runtime Bundle Consistency

When official compose/docs define multiple cooperating runtime services, treat the service set as a single versioned runtime bundle. Use one official release, compose file, or docs artifact as the evidence source for API, frontend/console, worker, realtime, gateway, and other required components.

Do not upgrade one bundle component independently. Keep component image tags, public entry routes, and critical env vars aligned with the same evidence source.

Record the evidence contract in a separate validator-only YAML file, such as `.sealos/runtime-bundle-evidence.yaml`. Do not write this evidence into `template/<app>/index.yaml`.

```yaml
apiVersion: docker-to-sealos/v1
kind: RuntimeBundleEvidence
metadata:
  name: demo-runtime-bundle
spec:
  appName: demo
  source: https://example.com/releases/v1/docker-compose.yml
  images:
    - ghcr.io/example/api:1.0.0
    - ghcr.io/example/console:1.0.0
  components:
    - ${{ defaults.app_name }}
    - ${{ defaults.app_name }}-console
  routes:
    - path: /
      service: ${{ defaults.app_name }}
    - path: /console
      service: ${{ defaults.app_name }}-console
  env:
    - PUBLIC_ENDPOINT
```

Evidence contract:

- `spec.appName`: Template `metadata.name` that this evidence validates.
- `spec.source`: official compose/docs/release artifact URL or identifier.
- `spec.images`: exact image refs expected from that source.
- `spec.components`: workload names that must be emitted as managed app workloads.
- `spec.routes`: `path` plus `service` entries that must appear in Service and Ingress resources.
- `spec.env`: critical env var names that must remain present on managed workloads.

Run validation with both files included:

```bash
python scripts/check_consistency.py --skill SKILL.md --references references --rules-file references/rules-registry.yaml --artifacts template/demo/index.yaml,.sealos/runtime-bundle-evidence.yaml
```

For web consoles or frontends, keep the official public entry path reachable through an explicit Service and Ingress rule. A frontend/console component may be merged into the API workload only when the official image embeds that entry and runtime validation proves the route works after login.

## Core Concept Mapping

### Docker Compose Service → Sealos Resources

A single service in Docker Compose needs to be converted into multiple Sealos resources:

```yaml
# Docker Compose
services:
  app:
    image: myapp:1.0.0
    ports:
      - "3000:3000"
    volumes:
      - ./data:/app/data
    environment:
      - DB_HOST=postgres
```

Converts to:

```yaml
# Sealos Template
---
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${{ defaults.app_name }}

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}

---
# Ingress (if public access is required)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
```

For a single-component StatefulSet with no documented headless or stable per-Pod DNS requirement, set `spec.serviceName` to the public application Service and keep the workload, Service, root Ingress, and manager identity aligned. Preserve documented HA/headless governing Services and expose them through a separate public application Service.

## Image Mapping

Warning: Example images must use a pinned version, preferring an exact version tag (e.g., `v2.2.0`); only use a digest when a stable version tag cannot be determined. Using `:latest` is prohibited.
Warning: Compose variable image expressions (e.g., `${IMAGE}`, `${IMAGE:-ghcr.io/example/app}`) must not be retained in the final template; they must be resolved to concrete image references during the conversion phase.

### Docker Compose
```yaml
services:
  app:
    image: nginx:1.27.2
    # or
    build: ./app
```

### Sealos Template
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    originImageName: nginx:1.27.2  # Must be added
spec:
  revisionHistoryLimit: 1
  template:
    spec:
      automountServiceAccountToken: false
      containers:
        - name: ${{ defaults.app_name }}
          image: nginx:1.27.2
          imagePullPolicy: IfNotPresent  # Must be set
```

Notes:
- Omit `imagePullSecrets` for public images. For private-registry images, reference only the app-scoped image pull Secret `${{ defaults.app_name }}`.
- `sealos-deploy` should create or refresh that Secret automatically from local `gh` CLI credentials when deploying private GHCR images.
- Reusable templates should not expose raw registry credential inputs as user-facing form fields.

## Port Mapping

### Docker Compose
```yaml
services:
  app:
    ports:
      - "3000:3000"
      - "8080:80"
```

> The Sealos gateway terminates TLS at the Ingress layer by default. If Compose exposes both `80` and `443`, and the backend service does not require HTTPS, the conversion should preferentially keep the HTTP port and remove `443`, while also not mounting in-container certificate directories (e.g., `/etc/nginx/ssl`, `/etc/ssl`, `/certs`).

### Sealos Template

#### Container Port Configuration
```yaml
spec:
  revisionHistoryLimit: 1
  template:
    spec:
      automountServiceAccountToken: false
      containers:
        - name: ${{ defaults.app_name }}
          ports:
            - containerPort: 3000
            - containerPort: 80
```

#### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
spec:
  ports:
    - name: tcp-3000
      port: 3000
      targetPort: 3000
    - name: tcp-8080
      port: 8080
      targetPort: 80
  selector:
    app: ${{ defaults.app_name }}
```

#### Ingress Configuration (Public Access)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
  labels:
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager-domain: ${{ defaults.app_host }}
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: 32m
    nginx.ingress.kubernetes.io/server-snippet: |
      client_header_buffer_size 64k;
      large_client_header_buffers 4 128k;
    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/backend-protocol: HTTP
    nginx.ingress.kubernetes.io/client-body-buffer-size: 64k
    nginx.ingress.kubernetes.io/proxy-buffer-size: 64k
    nginx.ingress.kubernetes.io/proxy-send-timeout: '300'
    nginx.ingress.kubernetes.io/proxy-read-timeout: '300'
    nginx.ingress.kubernetes.io/configuration-snippet: |
      if ($request_uri ~* \.(js|css|gif|jpe?g|png)) {
        expires 30d;
        add_header Cache-Control "public";
      }
spec:
  rules:
    - host: ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      http:
        paths:
          - pathType: Prefix
            path: /
            backend:
              service:
                name: ${{ defaults.app_name }}
                port:
                  number: 3000
  tls:
    - hosts:
        - ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      secretName: ${{ SEALOS_CERT_SECRET_NAME }}
```

Keep `Service.spec.ports[].name` populated, and route root-path Prefix Ingress backends through the matching numeric `service.port.number`. Launchpad public-address discovery compares that number with `Service.spec.ports[].port`.

#### WebSocket Ingress Mapping

Select WebSocket ingress when Compose/docs expose a public endpoint through `ws://`, `wss://`, CDP/Chrome DevTools, game socket traffic, or a port/service named `websocket`, `ws`, or `wss`. Service port names should preserve the protocol signal:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
spec:
  ports:
    - name: websocket
      port: 3000
      targetPort: 3000
      protocol: TCP
  selector:
    app: ${{ defaults.app_name }}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
  labels:
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager-domain: ${{ defaults.app_host }}
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: 32m
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/backend-protocol: WS
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
    - host: ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      http:
        paths:
          - pathType: Prefix
            path: /
            backend:
              service:
                name: ${{ defaults.app_name }}
                port:
                  number: 3000
  tls:
    - hosts:
        - ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      secretName: ${{ SEALOS_CERT_SECRET_NAME }}
```

When an app exposes separate HTTP and WebSocket public surfaces, create separate host defaults and separate ingress resources like the EaglerCraft pattern. When one public entry serves only WebSocket traffic, use the WebSocket ingress set even if the container port is named `http` upstream.

#### TLS Offload Normalization (80/443 Dual-Port Scenario)

```yaml
# Docker Compose
services:
  app:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - certs:/etc/nginx/ssl

# After conversion (Sealos)
# - workload/service only retains port 80
# - Ingress continues to use the platform certificate
# - /etc/nginx/ssl is no longer converted to a PVC mount
```

## Environment Variable Mapping

### Docker Compose
```yaml
services:
  app:
    environment:
      - NODE_ENV=production
      - API_KEY=secret123
      - DB_HOST=postgres
```

### Sealos Template

#### Plain Environment Variables
```yaml
spec:
  revisionHistoryLimit: 1
  template:
    spec:
      automountServiceAccountToken: false
      containers:
        - name: ${{ defaults.app_name }}
          env:
            - name: NODE_ENV
              value: production
```

#### Sensitive Values in Business Containers (Non-Database Connection Fields)
```yaml
# Deployment
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}
          env:
            - name: API_KEY
              value: ${{ defaults.api_key }}
```

Notes:
- Sensitive values for non-database connection fields use `env[].value` (from `defaults` or `inputs`).
- Database connection fields (`endpoint`/`host`/`port`/`username`/`password`) must use `secretKeyRef`.
- Only Kubeblocks database Secrets and object storage Secrets are allowed.

#### Referencing Database Connections
```yaml
env:
  - name: DB_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: endpoint
  - name: DB_HOST
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: host
  - name: DB_PORT
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: port
  - name: DB_USERNAME
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: username
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: password
```

#### URL/DSN Variable Composition (When `endpoint` Is Only `host:port`)
```yaml
env:
  - name: SEALOS_DATABASE_POSTGRES_HOST
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: host
  - name: SEALOS_DATABASE_POSTGRES_PORT
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: port
  - name: SEALOS_DATABASE_POSTGRES_USERNAME
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: username
  - name: SEALOS_DATABASE_POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: password
  - name: DATABASE_URL
    value: postgres://$(SEALOS_DATABASE_POSTGRES_USERNAME):$(SEALOS_DATABASE_POSTGRES_PASSWORD)@$(SEALOS_DATABASE_POSTGRES_HOST):$(SEALOS_DATABASE_POSTGRES_PORT)/postgres
```

Notes:
- This pattern should only be used when the source value is a URL/DSN pointing to a recognized database service.
- URL fields such as `DATABASE_URL` are allowed to reference component variables injected by approved DB `secretKeyRef` via `$(VAR)`.
- Assembling database URLs by referencing non-secret source variables is not allowed.

## Volume Mapping

### Docker Compose Volumes → Sealos VolumeClaimTemplates

**Important**: Sealos does not support emptyDir; all storage must be persistent.

Before creating a PVC for a host-directory mount, classify the target path:

- Use persistent storage for user data, uploads, model caches, database-adjacent state, and writable runtime state.
- Use ConfigMap mounts for source-controlled config files or scripts.
- Leave the path unmounted when the image already ships required dependency manifests, config defaults, or bootstrap metadata at the same path.

Dify sandbox is the failure pattern: official Compose mounts `./volumes/sandbox/dependencies:/dependencies`, while `langgenius/dify-sandbox:0.2.15` expects `dependencies/python-requirements.txt` to exist in the image/repo runtime path. A fresh Sealos PVC mounted at `/dependencies` contains only `lost+found`, hides the required file, and produces `failed to setup runner dependencies`.

#### Docker Compose
```yaml
services:
  app:
    volumes:
      - ./data:/app/data
      - ./config:/app/config
```

#### Sealos Template (Using StatefulSet)
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
spec:
  revisionHistoryLimit: 1
  template:
    spec:
      automountServiceAccountToken: false
      containers:
        - name: ${{ defaults.app_name }}
          volumeMounts:
            - name: vn-appvn-data
              mountPath: /app/data
            - name: vn-appvn-config
              mountPath: /app/config
  volumeClaimTemplates:
    - metadata:
        annotations:
          path: /app/data
          value: '1'
        name: vn-appvn-data
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
    - metadata:
        annotations:
          path: /app/config
          value: '1'
        name: vn-appvn-config
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
```

### Docker Compose ConfigMap → Sealos ConfigMap

#### Docker Compose
```yaml
services:
  nginx:
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

#### Sealos Template
```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
data:
  vn-etcvn-nginxvn-nginxvn-conf: |
    server {
      listen 80;
      ...
    }

---
# Deployment
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}
          volumeMounts:
            - name: ${{ defaults.app_name }}-cm
              mountPath: /etc/nginx/nginx.conf
              subPath: vn-etcvn-nginxvn-nginxvn-conf
      volumes:
        - name: ${{ defaults.app_name }}-cm
          configMap:
            name: ${{ defaults.app_name }}
```

Omit `defaultMode` for ConfigMap volumes unless the application explicitly requires a non-default file mode. Scripts invoked through `/bin/sh /path/script` do not need executable bits.

## Database Service Mapping

### Docker Compose
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data
```

### Sealos Template

Use the full Kubeblocks Cluster configuration (refer to `database-templates.md`):

```yaml
apiVersion: apps.kubeblocks.io/v1alpha1
kind: Cluster
metadata:
  name: ${{ defaults.app_name }}-pg
  labels:
    kb.io/database: postgresql-16.4.0
    clusterdefinition.kubeblocks.io/name: postgresql
    clusterversion.kubeblocks.io/name: postgresql-16.4.0
spec:
  clusterDefinitionRef: postgresql
  clusterVersionRef: postgresql-16.4.0
  # ... full configuration see database-templates.md
```

## Service Dependency Mapping

### Docker Compose
```yaml
services:
  app:
    depends_on:
      - postgres
      - redis
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
```

### Sealos Template

#### Inter-Service Communication Using FQDN
```yaml
env:
  - name: DB_HOST
    value: ${{ defaults.app_name }}-pg-postgresql.${{ SEALOS_NAMESPACE }}.svc.cluster.local
  - name: REDIS_HOST
    value: ${{ defaults.app_name }}-redis-redis-redis.${{ SEALOS_NAMESPACE }}.svc.cluster.local
```

#### Or Using Secret
```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: password
  - name: DB_URL
    value: postgresql://postgres:$(POSTGRES_PASSWORD)@${{ defaults.app_name }}-pg-postgresql.${{ SEALOS_NAMESPACE }}.svc:5432/mydb
```

## Resource Limits Mapping

Compose resource values must be normalized to the Sealos ladder. Use Compose limits only to choose the nearest allowed `limits` tier. Normalize 1G-class memory to `1024Mi`; normalize higher GiB classes to Mi values such as `2048Mi`, `4096Mi`, `8192Mi`, or `16384Mi`. Never emit bare `2G/4G/8G/16G` limits because the Sealos Template API quota preview can parse them as 0. Ignore Compose reservations for `requests`; Sealos `requests` are derived from the selected `limits` by dropping the last numeric digit, so `1024Mi` maps to `102Mi` and `4096Mi` maps to `409Mi`.

### Docker Compose
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Sealos Template
```yaml
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}
          resources:
            limits:
              cpu: 1
              memory: 1024Mi
            requests:
              cpu: 100m
              memory: 102Mi
```

## Health Check Mapping

Conversion priority:
1. When Docker Compose has a `healthcheck`, convert it to `livenessProbe` + `readinessProbe`
2. When Compose does not provide one but the official documentation clearly specifies a health endpoint/command, `livenessProbe` + `readinessProbe` must still be generated
3. For applications with slow initial startup (e.g., those that need to initialize a database), a `startupProbe` must also be generated to avoid premature failure during startup

### Docker Compose
```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Official Health Check Example (authentik)
```yaml
containers:
  - image: ghcr.io/goauthentik/server:2025.12.3
    imagePullPolicy: IfNotPresent
    startupProbe:
      httpGet:
        path: /-/health/ready/
        port: 9000
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 90
    livenessProbe:
      httpGet:
        path: /-/health/live/
        port: 9000
    readinessProbe:
      httpGet:
        path: /-/health/ready/
        port: 9000
```

### Sealos Template
```yaml
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
```

## Command and Arguments Mapping

Main business containers should keep startup behavior close to the image's official entrypoint.
Use `command`/`args` only for official startup commands, Compose-native parameters, or a short wrapper that fixes one local precondition and then `exec`s the final process.
Move file preparation, permission repair, database/bootstrap SQL, compatibility views, package installs, and generated config into initContainers, one-shot Jobs, or ConfigMap-mounted scripts.

### Docker Compose
```yaml
services:
  app:
    command: ["npm", "start"]
    # or
    entrypoint: /app/start.sh
    command: arg1 arg2
```

### Sealos Template
```yaml
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}
          command: ["npm", "start"]
          # or
          command: ["/app/start.sh"]
          args: ["arg1", "arg2"]
```

### Main Container Startup Contract

Use this decision flow before emitting a business container `command`/`args`:

1. If the image already has a valid `ENTRYPOINT`/`CMD`, omit `command` and `args` unless the upstream docs explicitly require parameters.
2. If Compose provides a simple command or args that are the application entrypoint, keep them.
3. If a small runtime precondition is required, use `workingDir` plus a short shell wrapper that ends with `exec`, for example:

```yaml
workingDir: /opt/billionmail/core
command:
  - /bin/sh
  - -ec
  - mkdir -p template && exec ./billionmail
```

4. If the startup block copies files, changes ownership/permissions, writes config, runs database clients, creates compatibility objects, installs packages, or spans multiple lines, move that logic out of the main container.

Bad main-container startup:

```yaml
command:
  - /bin/sh
  - -ec
  - |
    cp -r /defaults/* /data/
    chmod -R 777 /data
    psql -c 'CREATE VIEW ...'
    exec ./app
```

Good split:

- Config/data preparation: initContainer or ConfigMap script.
- Database bootstrap/compatibility: idempotent Job or initContainer.
- Main container: official entrypoint or short `exec` wrapper only.

### Volume-Dependent Arguments (Important!)

Docker Compose `command:` or `args` may reference paths that only exist because of a host volume mount in Compose. These paths may **not** exist inside the container image itself.

**Example — compose mounts a host dir for log output:**
```yaml
# Docker Compose
services:
  app:
    command: --log-dir /app/logs
    volumes:
      - ./logs:/app/logs     # host mount creates /app/logs
```

If the Sealos template does not provision a matching volume, the `/app/logs` directory will not exist and the container will crash at startup (e.g., `mkdir /app/logs: no such file or directory`).

**Resolution — check before converting:**
1. For each path referenced in `command:`/`args`, check whether it comes from a Compose `volumes:` mount.
2. If the path is a **log/data output directory** that only exists via host mount:
   - **Option A (preferred):** Drop the argument entirely — let the app use its built-in defaults (most apps log to stdout by default).
   - **Option B:** Add a matching `volumeClaimTemplates` (StatefulSet) or `emptyDir`-equivalent PVC to ensure the path exists.
3. If the path is an **essential config/script file** mounted from host → convert to ConfigMap mount instead.
4. Paths to executables or tools already inside the image (e.g., `npm start`, `/app/start.sh` from Dockerfile COPY) are safe to keep.

## Network Mode Mapping

### Built-in Edge Gateway (Traefik) Handling

When Compose includes both Traefik and business services, prefer using the Sealos platform Ingress capability and do not retain Traefik as an in-template workload.

Handling rules:

- If a service name or image is identifiable as Traefik, and at least one non-database business service exists, skip Traefik resource generation.
- The primary access entry point should target the business service (typically the first business service) via its Service, with the public domain exposed through Sealos Ingress.
- Only when the application contains only Traefik (no other business services) should Traefik be retained as a fallback, to avoid generating empty workloads.

Motivation:

- Avoid the additional forwarding complexity introduced by a dual-gateway setup (Traefik + Sealos Ingress).
- Reduce the risk of port, routing, and TLS configuration drift, making the template better aligned with Sealos platform capabilities.

### Docker Compose
```yaml
services:
  app:
    network_mode: host
    # or
    ports:
      - "3000:3000"
```

### Sealos Template

Sealos does not support host network mode; all access uses Service + Ingress:

```yaml
# Service (cluster-internal access)
apiVersion: v1
kind: Service
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
spec:
  ports:
    - name: tcp-3000
      port: 3000
  selector:
    app: ${{ defaults.app_name }}

---
# Ingress (public access)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
  labels:
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager-domain: ${{ defaults.app_host }}
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: 32m
    nginx.ingress.kubernetes.io/server-snippet: |
      client_header_buffer_size 64k;
      large_client_header_buffers 4 128k;
    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/backend-protocol: HTTP
    nginx.ingress.kubernetes.io/client-body-buffer-size: 64k
    nginx.ingress.kubernetes.io/proxy-buffer-size: 64k
    nginx.ingress.kubernetes.io/proxy-send-timeout: '300'
    nginx.ingress.kubernetes.io/proxy-read-timeout: '300'
    nginx.ingress.kubernetes.io/configuration-snippet: |
      if ($request_uri ~* \.(js|css|gif|jpe?g|png)) {
        expires 30d;
        add_header Cache-Control "public";
      }
spec:
  rules:
    - host: ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      http:
        paths:
          - pathType: Prefix
            path: /
            backend:
              service:
                name: ${{ defaults.app_name }}
                port:
                  number: 3000
```

## Object Storage Mapping

Classify the application capability before selecting resources. A bundled MinIO service identifies the S3-compatible provider layer; official application behavior determines whether the capability is optional.

Before adding Sealos ObjectStorage for an application feature, verify the upstream edition and license requirements. When S3/external object storage support is Enterprise, paid, commercial, subscription, or license-gated, the public template must use the community-supported storage path (usually filesystem/PVC) and must not expose a standard deployment input that provisions `ObjectStorageBucket` or injects S3 env vars for that feature. Add an enterprise-specific template branch only when the user explicitly requests that scope.

### Required Object Storage

Treat object storage as required when the application always initializes an S3 client, every documented deployment includes an S3-compatible backend, or the official docs make S3 initialization part of every supported deployment mode. Replace bundled MinIO with the unconditional Sealos `ObjectStorageBucket` resources required by the documented bucket topology, inject managed object-storage secrets, and resolve the provider during conversion.

#### Docker Compose (Required MinIO Dependency)

```yaml
services:
  app:
    image: example/app:1.0.0
    depends_on:
      - minio
    environment:
      S3_ENDPOINT: http://minio:9000
  minio:
    image: minio/minio:RELEASE.2025-09-07T16-13-09Z
    command: server /data
    volumes:
      - minio-data:/data
```

#### Sealos Template (Unconditional Managed Bucket)

```yaml
apiVersion: objectstorage.sealos.io/v1
kind: ObjectStorageBucket
metadata:
  name: ${{ defaults.app_name }}
spec:
  policy: private
```

Inject the managed Secret values into the application's documented environment variable names:

```yaml
env:
  - name: S3_ACCESS_KEY_ID
    valueFrom:
      secretKeyRef:
        name: object-storage-key
        key: accessKey
  - name: S3_SECRET_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        name: object-storage-key
        key: secretKey
  - name: S3_BUCKET
    valueFrom:
      secretKeyRef:
        name: object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}
        key: bucket
```

The required path contains the documented managed bucket set, managed Secret wiring, and any evidence-backed stateless compatibility proxy. Its object-store resource inventory is limited to those components. A compatibility proxy must record a credential-free HTTPS source URL or `user-request:<reference>` in `metadata.annotations.docker-to-sealos.object-storage-compatibility-proxy-source` and must not use persistent volumes.

Bucket-scoped object-storage secrets may append an additional lowercase suffix when one app needs multiple bucket values, for example `object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}-public`. Env names ending in `_BUCKET` may reference those bucket-scoped secrets.

### Application-Level Optional Object Storage

Use a conditional only when official docs show that the application remains functional with object storage disabled or with a documented local-filesystem mode. Model this application feature with a boolean input and configure the documented fallback in the false branch.

```yaml
inputs:
  enable_object_storage:
    description: "Enable the optional object storage feature"
    type: boolean
    default: "false"
    required: false

---
${{ if(inputs.enable_object_storage === 'true') }}
apiVersion: objectstorage.sealos.io/v1
kind: ObjectStorageBucket
metadata:
  name: ${{ defaults.app_name }}
spec:
  policy: private
${{ endif() }}
```

Provider/backend/type/mode/driver selectors stay out of `spec.inputs`. Names such as `use_sealos_objectstorage`, `object_storage_provider`, and `storage_backend` represent conversion decisions rather than application feature toggles.

### Externally Managed Object Storage

Expose external S3/object-storage credential inputs only when source docs or the user require an externally managed bucket. Record a credential-free HTTPS source URL or `user-request:<reference>` in `metadata.annotations.docker-to-sealos.external-object-storage-source` and use the external provider as the sole object-store data plane.

## CronJob Mapping

Any generated `CronJob` must include Sealos cron labels:

```yaml
metadata:
  labels:
    cloud.sealos.io/cronjob: <metadata.name>
    cronjob-launchpad-name: ""
    cronjob-type: image
```

## Common Patterns Summary

### Single-Container Application
- Docker Service → Deployment + Service + Ingress

### Multi-Container Application
- Each Docker Service → Independent Deployment + Service
- The main application uses `${{ defaults.app_name }}`
- Other components use `${{ defaults.app_name }}-<component>`

### Database Services
- Docker postgres/mysql/mongo/redis → Kubeblocks Cluster + ServiceAccount + Role + RoleBinding
- Kubernetes Deployment/StatefulSet/DaemonSet/Service resources that run or expose database servers map to Kubeblocks resources, while app initContainers and init/migration/bootstrap Jobs may use database client images for readiness and bootstrap gates.

### Persistent Storage
- Docker volumes → StatefulSet + volumeClaimTemplates

### Existing Template Resource Tuning
- Tune CPU and memory through the Sealos resource ladder, one dimension and one step at a time for each application main container, sidecar, initContainer, and Job.
- Select the lowest tier that passes a fresh role-specific personal low-load validation: cold start, readiness or successful completion, registration or login when applicable, at least two representative actions for long-running workloads, and a 60-second stability observation.
- Promote a candidate when OOM kills, restarts, readiness flaps, or resource-related timeouts occur. Record peak utilization percentages as diagnostic evidence.
- Treat `200m/256Mi` as the static initial candidate when source evidence supplies no explicit hard minimum. Keep KubeBlocks database components on their separate `500m/512Mi` contract.
- Apply the browser and remote-desktop interaction scenario only when the container itself runs that stack. Browser-accessed web applications use the general personal low-load flow.
- Preserve existing `ephemeral-storage` requests and limits exactly during template refreshes.
- Change `ephemeral-storage` only when live evidence shows `EphemeralStorage`, eviction, or disk-pressure failures for that workload.
- Adjust `requests.ephemeral-storage` and `limits.ephemeral-storage` together for the same container.
- Choose the smallest common Mi value that covers observed writable-layer usage plus startup margin; Dify sandbox uses `512Mi` after `300Mi` eviction and observed runner expansion under `/opt` and `/var/sandbox`.

### Configuration Files
- Docker config files → ConfigMap (using vn- naming convention)

### Public URL Configuration

Many web apps need their external URL configured to avoid hardcoded `localhost` references.
Without this, frontend API calls, OAuth callbacks, and webhook URLs will break in production.

#### Detection
Check source code/docs for:
- Env vars: `BASE_URL`, `SITE_URL`, `APP_URL`, `NEXTAUTH_URL`, `PUBLIC_URL`, `EXTERNAL_URL`, `HOSTNAME`
- Config files: node-config (`config/default.json`), PHP config, Rails `config/environments/production.rb`
- Code patterns: `getConfig(.*[Uu]rl`, `homeUrl`, `baseUrl`, `siteUrl`, fallback to `http://localhost`

#### Strategy A: Env Var (preferred when supported)
When the app reads its public URL from an environment variable:
```yaml
- name: APP_URL  # use the app's actual env var name
  value: https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
```

#### Strategy B: ConfigMap (for file-based config systems)
When the app reads its public URL from a config file (e.g., node-config, PHP config):

1. Create ConfigMap with the minimal config override containing only the public URL
2. Mount to the app's config directory using `subPath` to avoid overwriting other files
3. Follow standard ConfigMap naming/label conventions

```yaml
# ConfigMap — only include the minimal config needed for public URL
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
data:
  <config-filename>: |
    <minimal config content with public URL set to
     https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}>

# Deployment volumeMount — use subPath to mount single file
volumeMounts:
  - name: app-config
    mountPath: <app-config-dir>/<config-filename>
    subPath: <config-filename>

# Deployment volume
volumes:
  - name: app-config
    configMap:
      name: ${{ defaults.app_name }}
```

Real-world examples: see `skills/sealos-deploy/knowledge/lessons-learned.md` (EverShop case study)

### Sensitive Information
- Docker business env vars → `env[].value` (`defaults`/`inputs`)
