# Sealos Template Development Specification

## Template File Organization Specification

### Directory Structure Requirements

All templates must be organized according to the following directory structure:

```
templates/
└── template/
    └── <template-name>/    # The folder name must match the template's name field
        └── index.yaml       # The template file must be named index.yaml
```

### Example

```
templates/
└── template/
    ├── formbricks/
    │   └── index.yaml      # formbricks template file
    ├── langflow/
    │   └── index.yaml      # langflow template file
    └── fastgpt/
        └── index.yaml      # fastgpt template file
```

### Naming Rules

1. The folder name must be consistent with the `metadata.name` field in the Template CR
2. The template file must be named `index.yaml`
3. Folder names should use lowercase letters and hyphens; avoid underscores or other special characters
4. **The `metadata.name` of the Template CR must be hardcoded in lowercase letters** and cannot use variables (such as `${{ defaults.app_name }}`)

### Example

```yaml
# Correct example
apiVersion: app.sealos.io/v1
kind: Template
metadata:
  name: typesense  # ✅ Hardcoded lowercase name
spec:
  defaults:
    app_name:
      type: string
      value: typesense-${{ random(8) }}  # ✅ Variables can be used here

# Incorrect example
metadata:
  name: ${{ defaults.app_name }}  # ❌ Error: Variables cannot be used
```

## Resource Creation Order Specification

Resources within a template must be created in the following order:

### 1. Template CR
Create the Template metadata definition first

### 2. Object Storage
```yaml
apiVersion: objectstorage.sealos.io/v1
kind: ObjectStorageBucket
```

### 3. Database Resources
Database resources must be created in the following order:
1. **ServiceAccount**
2. **Role**
3. **RoleBinding**
4. **Cluster** (the actual database instance)
5. **Job** (if database initialization is needed)

### 4. Application Resources
Application resources must be created in the following order:
1. **ConfigMap** (application configuration files)
2. **Deployment/StatefulSet** (main application)
3. **Service**
4. **Ingress**
5. **App**

### Example Structure
```
Template CR
---
ObjectStorageBucket
---
Redis ServiceAccount
---
Redis Role
---
Redis RoleBinding
---
Redis Cluster
---
PostgreSQL ServiceAccount
---
PostgreSQL Role
---
PostgreSQL RoleBinding
---
PostgreSQL Cluster
---
PostgreSQL Init Job
---
Application StatefulSet
---
Application Service
---
Application Ingress
---
App
```

### App CRD Specification (Important!)

The `App` resource is the **last** resource in the template. It provides the Sealos dashboard entry point for the deployed application.

**Complete and definitive schema — only these fields are valid:**

```yaml
apiVersion: app.sealos.io/v1
kind: App
metadata:
  name: ${{ defaults.app_name }}
  labels:
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
spec:
  data:
    url: https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
  displayType: normal
  icon: <icon-url>
  name: <human-readable app title>
  type: link
```

**Allowed `spec` fields (exhaustive list):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.url` | string | **yes** | App access URL (Ingress host) |
| `displayType` | string | no | Display mode (`normal`) |
| `icon` | string | no | App icon URL |
| `name` | string | no | Human-readable title shown in dashboard |
| `type` | string | no | Entry type (`link`) |

**When generating templates in this repository, treat these enum values as fixed:** `displayType` must be `normal`, and `type` must be `link`. Do not emit alternatives such as `standalone` or `web`.

**Do NOT add any other fields.** Fields like `menuData`, `nameColor`, `template`, etc. do not exist in the App CRD and will cause `strict decoding error: unknown field` on apply.

### Multi-Service Web Runtime Contract

For split-service web apps, classify each component before writing resources:

- **Browser entry**: dashboard, console, setup UI, or docs page opened by users.
- **REST API**: authenticated application or dashboard API.
- **Protocol gateway**: OpenAI-compatible, webhook, or SDK-facing API surface.
- **Docs/static service**: optional public documentation.
- **Worker**: background processor with no public Service/Ingress unless upstream explicitly exposes one.

The App CRD `spec.data.url` must point to the browser entry URL that works from a fresh Sealos launch. Test the root path and any login/setup/entrance path from upstream docs or source. Choose the path that loads without prior navigation and reaches login, registration, or setup.

For SSR/Next.js/React server apps, HTTP status is not enough. Treat the entry as failed when the response body contains visible runtime failure text such as:

- `Application error`
- `server-side exception`
- `Internal Server Error`
- `Unhandled Runtime Error`
- Next.js runtime digest markers such as `NEXT_`

These failures invalidate the App URL and any HTTP probe path even when the HTTP status is 2xx or 3xx.

Use `nginx.ingress.kubernetes.io/app-root` only after the target path has been verified as a stable fresh-session entry. It must not hide a broken root path, missing public URL configuration, or wrong backend service routing.

Public and internal URLs must stay separate:

- Browser-facing env vars use public HTTPS URLs: `https://${{ defaults.<host> }}.${{ SEALOS_CLOUD_DOMAIN }}`.
- Backend-to-backend env vars use Kubernetes Service DNS names, for example `http://<service>.${{ SEALOS_NAMESPACE }}.svc.cluster.local:80`.
- Use public URLs for server-side callbacks only when upstream explicitly requires external callback or OAuth-style redirect behavior.

When workers, protocol gateways, or background services depend on database migrations, gate startup on app-specific database state such as migration markers or required tables, not merely on the database port.

## Defaults and Inputs Configuration Specification

### Basic Principles

**Important distinction:**
- `defaults`: Used to store **automatically generated** values (such as random strings, random ports, etc.)
- `inputs`: Used to store values that **require user input** (such as email, API Key, custom configurations, etc.)

### Defaults Configuration

Values in `defaults` are automatically generated when the template is parsed and do not require user interaction:

```yaml
defaults:
  app_host:
    type: string
    value: typesense-${{ random(8) }}  # ✅ With application name prefix
  app_name:
    type: string
    value: typesense-${{ random(8) }}  # ✅ Application name
  api_key:
    type: string
    value: ${{ random(32) }}           # ✅ Randomly generated secret key
```

**Notes:**
1. `app_host` must include an application name prefix (e.g., `typesense-${{ random(8) }}`)
2. `app_name` must include `${{ random(8) }}` to ensure uniqueness
3. Randomly generated configurations (secret keys, passwords, etc.) should be placed in `defaults`, not in `inputs`

### Inputs Configuration

Values in `inputs` need to be filled in by the user at deployment time:

```yaml
inputs:
  admin_email:
    description: 'Administrator email address'
    type: string
    default: ''
    required: true
  enable_feature_x:
    description: 'Enable advanced feature X'
    type: boolean
    default: 'false'
    required: false
```

**When to use inputs:**
- ✅ User's email address
- ✅ Custom domain name
- ✅ API Key for external services (needs to be provided by the user)
- ✅ Feature toggles (enable/disable certain features)
- ✅ Application-level optional object storage/S3 features documented by the official source, with `type: boolean` and conditions such as `inputs.enable_object_storage === 'true'`
- ❌ Randomly generated secret keys (should be placed in defaults)
- ❌ Automatically generated configurations (should be placed in defaults)

### Startup-Critical Input Defaults

Some applications validate bootstrap values before the HTTP server becomes ready. Admin passwords, API keys, salts, install tokens, and feature toggles used by entrypoints must have defaults that pass the application's own startup checks.

When an app documents password complexity, generate defaults with deterministic required character classes around the random segment:

```yaml
inputs:
  admin_password:
    description: Admin password. Leave the generated default or use at least 8 characters with uppercase, lowercase, number, and special character.
    type: string
    default: "Example@${{ random(16) }}!1"
    required: true
```

Avoid empty strings, weak examples, and bare `${{ random(n) }}` for startup-critical passwords, because the random function may not emit all required classes. During live validation, check first boot logs and the login/setup path using the generated default.

## Internationalization (i18n) Configuration

### Basic Format

Templates need to add `locale` and `i18n` configuration to support multiple languages:

```yaml
spec:
  locale: en  # Default language
  i18n:
    zh:
      description: '中文描述'
```

### Configuration Example

```yaml
apiVersion: app.sealos.io/v1
kind: Template
metadata:
  name: example
spec:
  title: 'Example App'
  description: 'An example application for demonstration'
  locale: en
  i18n:
    zh:
      description: '一个用于演示的示例应用程序'
```

### Supported Fields

The i18n configuration supports translation of the following fields:
- `description` - Application description

### Notes

1. `locale` specifies the default language, typically set to `en`
2. Currently only `zh` (Chinese) translation is supported
3. `i18n.zh.description` should use Simplified Chinese
4. Technical field names and default values do not need translation
5. If the Chinese title is the same as `spec.title`, it is recommended to omit `i18n.zh.title`

## Categories Restrictions

When creating Sealos templates, the `categories` field cannot be customized and must be selected from the following predefined options:

- `tool` - Utility applications
- `ai` - AI/Machine Learning related applications
- `game` - Game applications
- `database` - Database applications
- `low-code` - Low-code platforms
- `monitor` - Monitoring applications
- `dev-ops` - DevOps tools
- `blog` - Blog/Content management systems
- `storage` - Storage applications
- `frontend` - Frontend applications
- `backend` - Backend applications

### Example
```yaml
categories:
  - storage  # Correct: Using a predefined category
  - tool     # Correct: Multiple categories can be selected
  # - media  # Error: Not in the allowed list
```

## Storage Specification

### emptyDir Restriction (Important!)

**Sealos does not support emptyDir!** All scenarios requiring temporary storage must be converted to persistent storage.

**Incorrect example:**
```text
volumes:
  - name: config-storage
    emptyDir: {}  # Error! Sealos does not support emptyDir
```

**Correct approach:**
- For StatefulSet: Use `volumeClaimTemplates` to create persistent storage
- For Deployment: Consider whether storage is truly needed; if so, switch to StatefulSet
- For temporary configuration: Consider using ConfigMap or Secret
- Keep standard StatefulSet workload labels such as `app` and `cloud.sealos.io/app-deploy-manager`; omit only `cloud.sealos.io/deploy-on-sealos` from StatefulSet metadata labels and claim template metadata labels.

### PersistentVolumeClaim Usage Restriction

Storage cannot create PersistentVolumeClaim independently; it must use the `volumeClaimTemplates` field within a Deployment or StatefulSet.

### Deployment + volumeClaimTemplates — Sealos Template API Only (Important!)

`volumeClaimTemplates` on a **Deployment** is a **Sealos-specific extension**. It works only when deployed through the Sealos Template API (`POST /api/v2alpha/templates/raw`). Standard Kubernetes `kubectl apply` will reject a Deployment with `volumeClaimTemplates`:

```
error: Deployment in version "v1" cannot be handled as a Deployment:
  strict decoding error: unknown field "spec.volumeClaimTemplates"
```

**When using kubectl apply as a fallback**, you must handle this:
1. If the resource is `kind: Deployment` with `spec.volumeClaimTemplates` → remove the `volumeClaimTemplates` field and the corresponding `volumeMounts` entries before applying, OR convert to a `StatefulSet`.
2. If the resource is `kind: StatefulSet` with `spec.volumeClaimTemplates` → this is standard Kubernetes and works fine with kubectl apply.

**Recommendation for template authors:** When persistent storage is needed, prefer `StatefulSet` over `Deployment` to ensure compatibility with both the Template API and kubectl apply.

### volumeClaimTemplates Format

```yaml
volumeClaimTemplates:
  - metadata:
      annotations:
        path: /var/lib/headscale  # Mount path
        value: '1'                 # Fixed value
      name: vn-varvn-libvn-headscale  # Naming rules see below
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 1Gi
```

### Naming Rules

`metadata.name` reuses the value of `metadata.annotations.path`, with special characters replaced by "vn-":
- `/` is replaced with `vn-`
- `-` is replaced with `vn-`
- Other special characters are also replaced with `vn-`

For example:
- `/var/lib/headscale` → `vn-varvn-libvn-headscale`
- `/usr/src/app/upload` → `vn-usrvn-srcvn-appvn-upload`
- `/cache` → `vn-cache`

## ConfigMap Configuration Specification

### Naming Rules

The ConfigMap name must match the `metadata.name` of the workload that mounts it.

### File Storage Rules

Place all configuration files for the same workload in one ConfigMap. Each ConfigMap `data` key must be derived from the full mount path using `scripts/path_converter.py` vn naming:

**Conversion rules:**
- Replace `/` in the path with `vn-`
- Replace `-` in the path with `vn-`
- Replace `.` in the path with `vn-`
- Other special characters are also replaced with `vn-`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
data:
  # Original path: /etc/nginx/conf.d/default.conf
  # After conversion: vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf
  vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf: |
    server {
      listen 80;
      ...
    }
  # Original path: /tmp/chart.ini
  # After conversion: vn-tmpvn-chartvn-ini
  vn-tmpvn-chartvn-ini: |
    [cluster]
    seedlist = example
```

### Volume Mount Specification

Create one ConfigMap volume per workload. The volume name must be `<workload metadata.name>-cm`. Every ConfigMap `data` key must have its own `volumeMount`, and `volumeMount.subPath` must exactly equal the ConfigMap `data` key.
Omit `defaultMode` for ConfigMap volumes unless the application explicitly requires a non-default file mode.

```yaml
volumes:
  - name: ${{ defaults.app_name }}-cm
    configMap:
      name: ${{ defaults.app_name }}
volumeMounts:
  - name: ${{ defaults.app_name }}-cm
    mountPath: /etc/nginx/conf.d/default.conf
    subPath: vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf
  - name: ${{ defaults.app_name }}-cm
    mountPath: /app/config.yml
    subPath: vn-appvn-configvn-yml
```

### Complete Example

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
  vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf: |
    server {
      listen 80;
      server_name localhost;
      location / {
        root /usr/share/nginx/html;
        index index.html;
      }
    }
  vn-appvn-configvn-yml: |
    database:
      host: localhost
      port: 5432

# Deployment
apiVersion: apps/v1
kind: Deployment
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
            - name: ${{ defaults.app_name }}-cm
              mountPath: /etc/nginx/conf.d/default.conf
              subPath: vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf
            - name: ${{ defaults.app_name }}-cm
              mountPath: /app/config.yml
              subPath: vn-appvn-configvn-yml
      volumes:
        - name: ${{ defaults.app_name }}-cm
          configMap:
            name: ${{ defaults.app_name }}
```

## Labels and Naming Specification

### app-deploy-manager Label Rules

1. Application workloads (Deployment/StatefulSet/DaemonSet) must include `metadata.labels.app`, and the value must be consistent with the resource's `metadata.name`
2. The value of `cloud.sealos.io/app-deploy-manager` must be consistent with the resource's `metadata.name` value
3. The `metadata.name` of each template's main application (the frontend application providing the public-facing port) must be `${{ defaults.app_name }}`
4. Other components should be named based on `${{ defaults.app_name }}` plus a component identifier, for example:
   - `${{ defaults.app_name }}-server`
   - `${{ defaults.app_name }}-ml`
   - `${{ defaults.app_name }}-redis`
5. Application Service must include `metadata.labels.app` and `metadata.labels.cloud.sealos.io/app-deploy-manager`, and `metadata.name`, both labels, and `spec.selector.app` must be exactly the same
6. Runtime component-level ConfigMap must include `metadata.labels.app` and `metadata.labels.cloud.sealos.io/app-deploy-manager`, and both must be consistent with `metadata.name`; ConfigMaps used only by init containers to copy initial config into persistent storage must not include either label
7. Root-path Ingress rules (`pathType: Prefix`, `path: /`) must keep `metadata.name` consistent with `metadata.labels.cloud.sealos.io/app-deploy-manager` and backend `service.name`; non-root or non-Prefix Ingress rules may use a distinct Ingress name and backend service
8. Root-path Ingress backends must use `service.port.number`, and the number must match a declared `spec.ports[].port` on the referenced application Service so Launchpad can discover the public address
9. For a single-component StatefulSet without a documented headless or stable per-Pod DNS requirement, set `spec.serviceName` to the public application Service and keep the workload, Service, root Ingress, and manager identity aligned. Preserve documented HA/headless governing Services and route public traffic through a separate application Service

### Container Naming Rules

The primary business container name must be consistent with the workload
`metadata.name` value. Sidecar/helper containers may use distinct descriptive
names when they are not the main business container.

```yaml
# Correct example
metadata:
  name: ${{ defaults.app_name }}
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}  # Must be consistent with metadata.name
        - name: metrics-sidecar          # Allowed: helper/sidecar container

# Correct example for sub-components
metadata:
  name: ${{ defaults.app_name }}-ml
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}-ml  # Must be consistent with metadata.name
```

### Example

```yaml
# Main application (correct)
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}

# Sub-component (correct)
metadata:
  name: ${{ defaults.app_name }}-ml
  labels:
    app: ${{ defaults.app_name }}-ml
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}-ml

# Incorrect example
metadata:
  name: ${{ defaults.app_name }}-server
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}  # Error: Label value does not match name
```

### Special Case: Database Resources

Database resources (Clusters created via kubeblocks) use dbprovider labels instead of `cloud.sealos.io/app-deploy-manager`.

Required labels:

1. `kb.io/database` must identify the KubeBlocks database/version.
2. `sealos-db-provider-cr` must equal `metadata.name`.
3. `clusterdefinition.kubeblocks.io/name` must identify the database engine, such as `postgresql`, `apecloud-mysql`, `mongodb`, `redis`, or `kafka`.
4. Related Pods, Services, and OpsRequests should carry `app.kubernetes.io/instance=<database name>` for dbprovider detail views. Generated templates may also place this label on the Cluster for consistency, but dbprovider's Cluster list path primarily keys on `clusterdefinition.kubeblocks.io/name`.

```yaml
# Correct labels for database resources
metadata:
  name: ${{ defaults.app_name }}-redis
  labels:
    kb.io/database: redis-7.2.7
    sealos-db-provider-cr: ${{ defaults.app_name }}-redis
    app.kubernetes.io/instance: ${{ defaults.app_name }}-redis
    clusterdefinition.kubeblocks.io/name: redis
```

## Object Storage Configuration

Use ObjectStorage only for application features available in the upstream self-hosted/community edition. If S3/object-storage support requires Enterprise, paid, commercial, subscription, or license activation, the public template must keep the supported filesystem/PVC storage path and must not expose an `ObjectStorageBucket` or S3 toggle for that feature.

### Mode Selection

1. Required capability: create the unconditional `ObjectStorageBucket` resources required by the documented bucket topology, inject their managed Secret values, and use Sealos ObjectStorage as the sole object-store data plane.
2. Application-level optional capability: use a boolean enable/disable input only when official docs provide a functional storage-disabled or local-filesystem mode, and configure that documented mode in the false branch.
3. Externally managed storage: expose credential inputs only with a credential-free HTTPS source URL or `user-request:<reference>` in `docker-to-sealos.external-object-storage-source`, and use the external provider as the sole data plane.

A bundled MinIO service is an S3-compatible provider implementation. Convert it to an unconditional Sealos bucket when the application requires S3-compatible storage. Keep provider/backend/type/mode/driver selectors out of `spec.inputs`.

A compatibility proxy may adapt requests when official protocol evidence requires it. Record that evidence as a credential-free HTTPS source URL or `user-request:<reference>` in `docker-to-sealos.object-storage-compatibility-proxy-source`, keep the proxy stateless, and omit persistent volumes.

### Environment Variable Settings

Object storage environment variable configuration must follow this format:

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
  - name: S3_ENDPOINT
    value: "https://$(BACKEND_STORAGE_MINIO_EXTERNAL_ENDPOINT)"
  - name: BACKEND_STORAGE_MINIO_EXTERNAL_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: object-storage-key
        key: external
  - name: S3_PUBLIC_DOMAIN
    value: "https://$(BACKEND_STORAGE_MINIO_EXTERNAL_ENDPOINT)"
  - name: S3_ENABLE_PATH_STYLE
    value: "1"
```

### Notes

1. Use `object-storage-key` for the shared `accessKey`, `secretKey`, `external`, and `internal` values.
2. Use `object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}` for the bucket value. Bucket-scoped variants may append a lowercase suffix, for example `object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}-public`.
3. S3_ENDPOINT and S3_PUBLIC_DOMAIN use environment variable references: `$(BACKEND_STORAGE_MINIO_EXTERNAL_ENDPOINT)`.
4. S3_ENABLE_PATH_STYLE must be set to "1".

## Ingress Configuration Specification

### Standard Format

Ingress must use the following format:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
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
                  number: <port-number>
  tls:
    - hosts:
        - ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      secretName: ${{ SEALOS_CERT_SECRET_NAME }}
```

### Notes

1. `metadata.name` must be `${{ defaults.app_name }}`
2. Must include the `cloud.sealos.io/app-deploy-manager-domain` label
3. `ssl-redirect` defaults to `'true'`
4. Includes a configuration-snippet for static resource caching
5. Backend service name must be `${{ defaults.app_name }}`
6. Backend service port must use numeric `number: <port-number>` and match the referenced Service `spec.ports[].port`; keep the Service port `name` for Kubernetes multi-port compatibility

### WebSocket Format

Use WebSocket ingress when the public entry is `ws://`, `wss://`, CDP/Chrome DevTools, a game socket, or a service/port named `websocket`, `ws`, or `wss`. Follow the EaglerCraft-style pattern: name the service port `websocket`, route the ingress to that port, and use the WS annotation set.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
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
                  number: <websocket-port-number>
  tls:
    - hosts:
        - ${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
      secretName: ${{ SEALOS_CERT_SECRET_NAME }}
```

## Database Connection Configuration

### PostgreSQL Environment Variables

All PostgreSQL environment variables are obtained from the secret automatically created by kubeblocks. The secret name format is: `${{ defaults.app_name }}-pg-conn-credential`

The secret contains the following keys:
- `endpoint`: Full connection endpoint (host:port)
- `host`: Hostname
- `password`: Password
- `port`: Port number
- `username`: Username (usually postgres)

### Usage Example

```yaml
env:
  # Configure host and port separately
  - name: DB_HOSTNAME
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

  # Or use endpoint to directly get host:port
  - name: DB_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-pg-conn-credential
        key: endpoint
```

### Other Databases

Other databases follow the same approved secret policy, with service-FQDN exceptions where KubeBlocks only exposes credentials:
- Redis: `${{ defaults.app_name }}-redis-redis-account-default` (legacy `${{ defaults.app_name }}-redis-account-default` may be accepted); host/port may use `${{ defaults.app_name }}-redis-redis-redis.${{ SEALOS_NAMESPACE }}.svc.cluster.local` and `6379`
- MySQL: `${{ defaults.app_name }}-mysql-conn-credential`
- MongoDB: `${{ defaults.app_name }}-mongo-mongodb-account-root` (or `${{ defaults.app_name }}-mongodb-mongodb-account-root` when the Cluster name uses `${{ defaults.app_name }}-mongodb`); MongoDB URLs may use `${{ defaults.app_name }}-mongo-mongodb.${{ SEALOS_NAMESPACE }}.svc:27017`

### PostgreSQL Database Initialization

PostgreSQL does not create a database by default. If the application needs a custom database (rather than using the default postgres database), it must be created via a Job.

**Important specification:**
- The database name should use the application's default value and should not be a user input parameter
- The database name should be related to the application name, typically using the application's short name or identifier
- For example: the langflow application uses the 'langflow' database, the fastgpt application uses the 'fastgpt' database

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ${{ defaults.app_name }}-pg-init
spec:
  backoffLimit: 3
  template:
    spec:
      containers:
        - name: pgsql-init
          image: postgres:16-alpine
          imagePullPolicy: IfNotPresent
          env:
            - name: PG_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: ${{ defaults.app_name }}-pg-conn-credential
                  key: password
            - name: PG_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: ${{ defaults.app_name }}-pg-conn-credential
                  key: endpoint
            - name: PG_DATABASE
              value: langflow
          command:
            - /bin/sh
            - -c
            - |
              set -eu
              for i in $(seq 1 60); do
                if pg_isready -h "${PG_ENDPOINT%:*}" -p "${PG_ENDPOINT##*:}" -U postgres -d postgres >/dev/null 2>&1; then
                  break
                fi
                sleep 2
              done
              pg_isready -h "${PG_ENDPOINT%:*}" -p "${PG_ENDPOINT##*:}" -U postgres -d postgres >/dev/null 2>&1
              if ! psql "postgresql://postgres:$(PG_PASSWORD)@$(PG_ENDPOINT)/postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='$(PG_DATABASE)'" | grep -q 1; then
                psql "postgresql://postgres:$(PG_PASSWORD)@$(PG_ENDPOINT)/postgres" -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$(PG_DATABASE)\";"
              fi
      restartPolicy: OnFailure
  ttlSecondsAfterFinished: 300
```

**Notes:**
1. Job name uses the format `${{ defaults.app_name }}-pg-init`
2. Uses the `postgres:16-alpine` image to keep it lightweight
3. `ttlSecondsAfterFinished: 300` ensures the Job is automatically cleaned up 5 minutes after completion
4. The initialization script must wait for PostgreSQL to be ready first (e.g., `pg_isready`)
5. The initialization script must be idempotent (check `pg_database` first, create only if it does not exist)
6. The database name should be hardcoded in the template, using the application's default database name (e.g., 'langflow' in the example above)

## Application Configuration Specification

### Inter-Service Communication Rules

**Important**: Services must reference each other using Fully Qualified Domain Names (FQDN); direct service names cannot be used.

FQDN format: `<service-name>.${{ SEALOS_NAMESPACE }}.svc.cluster.local`

```yaml
# Correct example: Using FQDN
env:
  - name: WORKER_URL
    value: http://${{ defaults.app_name }}-worker.${{ SEALOS_NAMESPACE }}.svc.cluster.local:4003
  - name: COUCH_DB_URL
    value: http://${{ defaults.app_name }}-svc-couchdb.${{ SEALOS_NAMESPACE }}.svc.cluster.local:5984
  - name: REDIS_URL
    value: redis://:$(REDIS_PASSWORD)@${{ defaults.app_name }}-redis-redis-redis.${{ SEALOS_NAMESPACE }}.svc:6379

# Incorrect example: Using service name directly
# - name: WORKER_URL
#   value: http://worker-service:4003  # Error: May fail to resolve
```

Note: Although the `.svc.cluster.local` suffix can be omitted in some cases (as in the REDIS_URL example above), it is recommended to always include the full domain name to ensure cross-namespace compatibility and clarity.

### Environment Variable Dependency Order Rules

**Important**: If an environment variable references another environment variable, the referenced variable must be defined before the variable that references it.

```yaml
env:
  # Correct example: REDIS_PASSWORD comes first, REDIS_URL comes after
  - name: REDIS_PASSWORD
    valueFrom:
      secretKeyRef:
        name: ${{ defaults.app_name }}-redis-redis-account-default
        key: password
  - name: REDIS_URL
    value: redis://:$(REDIS_PASSWORD)@${{ defaults.app_name }}-redis-redis-redis.${{ SEALOS_NAMESPACE }}.svc:6379

  # Incorrect example: If REDIS_URL is defined before REDIS_PASSWORD
  # - name: REDIS_URL
  #   value: redis://:$(REDIS_PASSWORD)@...  # Error: REDIS_PASSWORD is not defined yet
  # - name: REDIS_PASSWORD
  #   valueFrom: ...
```

This is because Kubernetes parses environment variables in the order they appear in the YAML. If a referenced variable has not been defined yet, the reference will fail.

### Required Security and Resource Management Configuration

All application Deployments or StatefulSets must include the following configurations:

1. **automountServiceAccountToken**: Must be set to `false` to avoid unnecessary permission exposure. Set it to `true` only when the application explicitly needs the Kubernetes API/service account token, evidenced by Kubernetes integration settings, `serviceAccountName`, or `sealos.io/service-account-token-reason` in workload annotations.
2. **revisionHistoryLimit**: Must be set to `1` to reduce resources consumed by historical revisions
3. **imagePullSecrets**: Omit for public images. For private-registry images, reference only the app-scoped pull Secret `${{ defaults.app_name }}`
4. **metadata.annotations**: Must include the following annotations:
   - `originImageName`: Original image name
   - `deploy.cloud.sealos.io/minReplicas`: Minimum replica count, typically set to `'1'`
   - `deploy.cloud.sealos.io/maxReplicas`: Maximum replica count, typically set to `'1'`

Recommended registry pull Secret model:

- Public-image managed workloads omit `imagePullSecrets`
- For private GHCR images, `sealos-deploy` creates or refreshes `${{ defaults.app_name }}` from local `gh` CLI credentials and the workload may reference it through `imagePullSecrets`
- If a private-registry template is deployed outside `sealos-deploy`, the operator must create the Secret manually before applying the workload

```yaml
apiVersion: apps/v1
kind: Deployment  # or StatefulSet
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
  annotations:
    originImageName: example/app:1.0.0  # Required: Original image name
    deploy.cloud.sealos.io/minReplicas: '1'  # Required: Minimum replica count
    deploy.cloud.sealos.io/maxReplicas: '1'  # Required: Maximum replica count
spec:
  revisionHistoryLimit: 1  # Must be set to 1
  template:
    spec:
      automountServiceAccountToken: false  # Default; only set true with evidenced Kubernetes API token need
      containers:
        - name: ${{ defaults.app_name }}
          # Other container configuration...
```

### Complete Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${{ defaults.app_name }}
  annotations:
    originImageName: example/app:1.0.0
    deploy.cloud.sealos.io/minReplicas: '1'
    deploy.cloud.sealos.io/maxReplicas: '1'
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
spec:
  revisionHistoryLimit: 1  # Revision history limit set to 1
  replicas: 1
  selector:
    matchLabels:
      app: ${{ defaults.app_name }}
  template:
    metadata:
      labels:
        app: ${{ defaults.app_name }}
    spec:
      automountServiceAccountToken: false  # Disable automatic service account token mounting
      containers:
        - name: ${{ defaults.app_name }}
          image: example/app:1.0.0
          imagePullPolicy: IfNotPresent
```

## Resource Quota Specification

### Resource Limit Configuration

**Important: The resources field of all containers must include both requests and limits.**

All containers in application Deployments or StatefulSets must use the fixed Sealos resource ladder. Do not invent intermediate values during template generation or resource tuning.

Allowed `limits.cpu` values use canonical Kubernetes quantities:

- `100m` (0.1 core)
- `200m` (0.2 core)
- `500m` (0.5 core)
- `1`
- `2`
- `3`
- `4`
- `8`

Allowed `limits.memory` values:

- `128Mi`
- `256Mi`
- `512Mi`
- `1024Mi`
- `2048Mi`
- `4096Mi`
- `8192Mi`
- `16384Mi`

`requests` must be derived from `limits` by dropping the last numeric digit:

| limits | requests |
|--------|----------|
| `cpu: 100m` | `cpu: 10m` |
| `cpu: 200m` | `cpu: 20m` |
| `cpu: 500m` | `cpu: 50m` |
| `cpu: 1` | `cpu: 100m` |
| `cpu: 2` | `cpu: 200m` |
| `cpu: 3` | `cpu: 300m` |
| `cpu: 4` | `cpu: 400m` |
| `cpu: 8` | `cpu: 800m` |
| `memory: 128Mi` | `memory: 12Mi` |
| `memory: 256Mi` | `memory: 25Mi` |
| `memory: 512Mi` | `memory: 51Mi` |
| `memory: 1024Mi` | `memory: 102Mi` |
| `memory: 2048Mi` | `memory: 204Mi` |
| `memory: 4096Mi` | `memory: 409Mi` |
| `memory: 8192Mi` | `memory: 819Mi` |
| `memory: 16384Mi` | `memory: 1638Mi` |

**Default lightweight application quota:**

```yaml
resources:
  requests:
    cpu: 20m
    memory: 25Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

**Standard backend or broker quota after validation:**

```yaml
resources:
  requests:
    cpu: 50m
    memory: 51Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**Heavy workload quota:**

```yaml
resources:
  requests:
    cpu: 200m
    memory: 204Mi
  limits:
    cpu: 2
    memory: 2048Mi
```

**Invalid examples:**

```yaml
# Incorrect: non-ladder values
resources:
  requests:
    cpu: 30m
    memory: 160Mi
  limits:
    cpu: 300m
    memory: 384Mi

# Incorrect: requests copied from old ratio guidance instead of deriving from limits
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 1
    memory: 1024Mi

# Incorrect: G/Gi forms can make Sealos Template API quota preview parse memory as 0; use Mi ladder values
resources:
  requests:
    cpu: 200m
    memory: 200Mi
  limits:
    cpu: 2
    memory: 2G
```

**Tuning guidance:**

1. Move only between allowed `limits` ladder values.
2. Recompute `requests` from the selected `limits`; do not preserve old requests.
3. If a StatefulSet fails readiness at a lower resource tier, recreate or cleanly roll the Pod before testing the next tier so a stale non-ready Pod is not mistaken for the next tier's result.
4. Choose the lowest tier that becomes Ready and passes application-level probes.

## Image Configuration Specification

### Image Pull Policy

The image pull policy for all containers must be set to `IfNotPresent`:

```yaml
spec:
  template:
    spec:
      containers:
        - name: ${{ defaults.app_name }}
          image: example/app:1.0.0
          imagePullPolicy: IfNotPresent  # Must use IfNotPresent
```

This helps to:
- Reduce unnecessary image pulls and improve deployment speed
- Reduce pressure on the image registry
- Save network bandwidth

## Other Notes

(More specifications and best practices to be added)
