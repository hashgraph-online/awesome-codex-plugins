# Sealos platform contract

Rules for writing template YAML that deploys through the Template API
(`sealos-api.py deploy`). Violating these produces resources that break, hit
quota validation, or stay invisible to the Sealos UI.

## Template envelope

A deployable template is one YAML file: a `Template` CR followed by resources,
separated by `---`.

```yaml
apiVersion: app.sealos.io/v1
kind: Template
metadata:
  name: myapp            # hardcoded lowercase; NEVER a variable
spec:
  title: 'myapp'
  url: ''
  gitRepo: ''
  author: ''
  description: 'What this deploys'
  readme: ''
  icon: ''
  templateType: inline
  locale: en
  categories: []
  defaults:
    app_name:
      type: string
      value: myapp-${{ random(8) }}
    app_host:
      type: string
      value: myapp-${{ random(8) }}
  inputs: {}
---
# resources follow
```

- `defaults` = generated values (names, hosts, random secrets). `inputs` =
  user-supplied values (email, external API keys). Both must be YAML strings;
  quote numbers and booleans (`default: "587"`).
- `${{ random(n) }}` yields n random chars — fine for opaque secrets, NOT for
  values with format constraints (hex, base64, UUID). Hardcode a valid value or
  make it a required input instead.
- Built-in variables usable anywhere in resources:
  - `${{ SEALOS_NAMESPACE }}` — user namespace (ns-xxx)
  - `${{ SEALOS_CLOUD_DOMAIN }}` — region app domain; `<host>.<domain>` is the public URL
  - `${{ SEALOS_CERT_SECRET_NAME }}` — wildcard TLS secret for Ingress
  - `${{ SEALOS_SERVICE_ACCOUNT }}` — used in object-storage secret names
- Resource order: databases (SA → Role → RoleBinding → Cluster → init Job),
  then ConfigMap → workload → Service → Ingress → App.

## Workload contract (Deployment / StatefulSet)

```yaml
apiVersion: apps/v1
kind: Deployment          # StatefulSet when persistent storage is needed
metadata:
  name: ${{ defaults.app_name }}
  annotations:
    originImageName: <image:tag>
    deploy.cloud.sealos.io/minReplicas: '1'
    deploy.cloud.sealos.io/maxReplicas: '1'
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
spec:
  replicas: 1
  revisionHistoryLimit: 1
  selector:
    matchLabels:
      app: ${{ defaults.app_name }}
  template:
    metadata:
      labels:
        app: ${{ defaults.app_name }}
    spec:
      automountServiceAccountToken: false
      containers:
        - name: ${{ defaults.app_name }}
          image: <image:tag>
          imagePullPolicy: IfNotPresent
          resources:
            requests: { cpu: 20m, memory: 25Mi }
            limits: { cpu: 200m, memory: 256Mi }
```

- `metadata.name`, `labels.app`, `labels.cloud.sealos.io/app-deploy-manager`,
  and the main container name must all be identical. The main component is
  `${{ defaults.app_name }}`; extra components append a suffix
  (`${{ defaults.app_name }}-worker`) with their own matching labels.
- Also set `cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}` on
  each namespaced resource's `metadata.labels` (workloads, Service, Ingress,
  App, ConfigMap, ObjectStorageBucket, …). Sealos groups the instance by this
  label; Brain adoption on `*.sealos.io` lists by it too. Never put it on
  `spec.template.metadata.labels`.
- Multi-component apps: give EVERY workload its own matching name/labels, talk
  between services via FQDN
  `<service>.${{ SEALOS_NAMESPACE }}.svc.cluster.local`, never bare service
  names.
- Env vars that reference other env vars (`$(VAR)`) must appear after the
  variable they reference.
- Private images: create the pull secret first, then reference it via
  `imagePullSecrets: [{name: ${{ defaults.app_name }}}]`. Public images: omit.

### Resource ladder

`limits.cpu` ∈ 100m, 200m, 500m, 1, 2, 3, 4, 8.
`limits.memory` ∈ 128Mi, 256Mi, 512Mi, 1024Mi, 2048Mi, 4096Mi, 8192Mi, 16384Mi
(always Mi — `2G`/`2Gi` forms break the quota preview).
`requests` = limits with the last digit dropped: `cpu: 1 → 100m`,
`memory: 512Mi → 51Mi`, `cpu: 200m → 20m`.

Starting points: lightweight tool 200m/256Mi; standard web app or database
500m/512Mi; heavy JVM/build/ML 2/2048Mi. When a pod OOMs or crawls, move one
ladder step at a time.

### Storage

- `emptyDir` is NOT supported. Anything that writes to disk needs a
  `StatefulSet` with `volumeClaimTemplates` (standard k8s, works everywhere).
  A `Deployment` with `volumeClaimTemplates` is a Sealos extension that only
  works through the Template API — prefer StatefulSet.
- Standalone PVCs are not allowed; storage must come from
  `volumeClaimTemplates`.
- Claim name encodes the mount path: replace every `/`, `-`, `.` with `vn-`
  (`/var/lib/data` → `vn-varvn-libvn-data`), lowercased — k8s names forbid
  uppercase (`/var/www/FreshRSS/data` → `vn-varvn-wwwvn-freshrssvn-data`;
  the `path` annotation keeps the real casing) — and set annotations:

```yaml
volumeClaimTemplates:
  - metadata:
      name: vn-varvn-libvn-data
      labels:
        cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
      annotations:
        path: /var/lib/data
        value: '1'
    spec:
      accessModes: [ReadWriteOnce]
      resources:
        requests:
          storage: 1Gi
```

## ConfigMap contract

One ConfigMap per workload, named exactly like the workload, same `app` +
`cloud.sealos.io/app-deploy-manager` + `cloud.sealos.io/deploy-on-sealos`
labels. Each data key is the mount path
with `/`, `-`, `.` replaced by `vn-`; mount each key with `subPath` equal to
the key and a single volume named `<workload>-cm`:

```yaml
data:
  vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf: |
    server { ... }
# in the pod spec:
volumes:
  - name: ${{ defaults.app_name }}-cm
    configMap:
      name: ${{ defaults.app_name }}
volumeMounts:
  - name: ${{ defaults.app_name }}-cm
    mountPath: /etc/nginx/conf.d/default.conf
    subPath: vn-etcvn-nginxvn-confvn-dvn-defaultvn-conf
```

## Service contract

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
spec:
  ports:
    - port: 3000
  selector:
    app: ${{ defaults.app_name }}
```

Name, both labels, and `selector.app` identical. The Ingress backend port must
match a declared `spec.ports[].port`.

## Ingress contract (public HTTPS)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${{ defaults.app_name }}
  labels:
    app: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/app-deploy-manager-domain: ${{ defaults.app_host }}
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/proxy-body-size: 32m
    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/backend-protocol: HTTP
    nginx.ingress.kubernetes.io/client-body-buffer-size: 64k
    nginx.ingress.kubernetes.io/proxy-buffer-size: 64k
    nginx.ingress.kubernetes.io/proxy-send-timeout: '300'
    nginx.ingress.kubernetes.io/proxy-read-timeout: '300'
    nginx.ingress.kubernetes.io/server-snippet: |
      client_header_buffer_size 64k;
      large_client_header_buffers 4 128k;
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

The public URL is `https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}`.
For WebSocket endpoints change `backend-protocol` to `WS` and raise both proxy
timeouts to `'3600'`.

## App CR (dashboard entry)

Last resource in every template. Exactly these fields — anything else fails
strict decoding:

```yaml
apiVersion: app.sealos.io/v1
kind: App
metadata:
  name: ${{ defaults.app_name }}
  labels:
    cloud.sealos.io/app-deploy-manager: ${{ defaults.app_name }}
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
spec:
  data:
    url: https://${{ defaults.app_host }}.${{ SEALOS_CLOUD_DOMAIN }}
  displayType: normal
  icon: <icon-url or "">
  name: <human readable title>
  type: link
```

`spec.data.url` must be the browser entry that works from a fresh visit
(root, or the documented login/setup path).

## Object storage (S3-compatible)

```yaml
apiVersion: objectstorage.sealos.io/v1
kind: ObjectStorageBucket
metadata:
  name: ${{ defaults.app_name }}
  labels:
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
spec:
  policy: private        # private | publicRead | publicReadwrite
```

Wire credentials from the managed secrets — shared keys from
`object-storage-key`, the bucket name from the per-bucket secret:

```yaml
env:
  - name: S3_ACCESS_KEY
    valueFrom: { secretKeyRef: { name: object-storage-key, key: accessKey } }
  - name: S3_SECRET_KEY
    valueFrom: { secretKeyRef: { name: object-storage-key, key: secretKey } }
  - name: S3_ENDPOINT_HOST
    valueFrom: { secretKeyRef: { name: object-storage-key, key: external } }
  - name: S3_BUCKET
    valueFrom:
      secretKeyRef:
        name: object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}
        key: bucket
```

Use path-style addressing (`S3_ENABLE_PATH_STYLE=1` or the app's equivalent);
the endpoint is `https://$(S3_ENDPOINT_HOST)`.
