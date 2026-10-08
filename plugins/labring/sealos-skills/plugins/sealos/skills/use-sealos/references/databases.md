# Databases on Sealos (KubeBlocks)

Databases are KubeBlocks `Cluster` CRs, never plain Deployments/StatefulSets.
Each database needs four resources in order: ServiceAccount → Role →
RoleBinding → Cluster (all four named identically), plus an optional init Job.

## Naming and connection cheat sheet

With cluster name `<app>-pg` etc. (`<app>` = `${{ defaults.app_name }}`):

| Engine | Cluster name | Credential secret | In-namespace host (append `.${{ SEALOS_NAMESPACE }}.svc`) | Port |
|---|---|---|---|---|
| PostgreSQL | `<app>-pg` | `<app>-pg-conn-credential` (endpoint/host/port/username/password) | `<app>-pg-postgresql` | 5432 |
| MySQL | `<app>-mysql` | `<app>-mysql-conn-credential` (same keys) | `<app>-mysql-mysql` | 3306 |
| MongoDB | `<app>-mongo` | `<app>-mongo-mongodb-account-root` (username/password) | `<app>-mongo-mongodb` | 27017 |
| Redis | `<app>-redis` | `<app>-redis-redis-account-default` (username/password) | `<app>-redis-redis-redis` | 6379 |
| Kafka | `<app>-broker` | `<app>-broker-account-admin` | `<app>-broker-broker` | 9092 |

Always inject `username`/`password` (and host/port when present) via
`secretKeyRef`; for Redis/Mongo the host is the fixed Service FQDN above.
Account secrets (Redis/Mongo) appear only after the component pod starts —
wait for the Cluster phase to reach `Running` before judging the app.

## PostgreSQL (full shape; adapt names for other engines)

```yaml
apiVersion: apps.kubeblocks.io/v1alpha1
kind: Cluster
metadata:
  name: ${{ defaults.app_name }}-pg
  labels:
    kb.io/database: postgresql-16.4.0
    clusterdefinition.kubeblocks.io/name: postgresql
    clusterversion.kubeblocks.io/name: postgresql-16.4.0
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
spec:
  affinity:
    podAntiAffinity: Preferred
    tenancy: SharedNode
  clusterDefinitionRef: postgresql
  clusterVersionRef: postgresql-16.4.0
  terminationPolicy: Delete
  componentSpecs:
    - componentDefRef: postgresql
      name: postgresql
      replicas: 1
      disableExporter: true
      enabledLogs: [running]
      serviceAccountName: ${{ defaults.app_name }}-pg
      switchPolicy: { type: Noop }
      resources:
        limits: { cpu: 500m, memory: 512Mi }
        requests: { cpu: 50m, memory: 51Mi }
      volumeClaimTemplates:
        - name: data
          spec:
            accessModes: [ReadWriteOnce]
            resources: { requests: { storage: 3Gi } }
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${{ defaults.app_name }}-pg
  labels:
    sealos-db-provider-cr: ${{ defaults.app_name }}-pg
    app.kubernetes.io/instance: ${{ defaults.app_name }}-pg
    app.kubernetes.io/managed-by: kbcli
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ${{ defaults.app_name }}-pg
  labels:
    sealos-db-provider-cr: ${{ defaults.app_name }}-pg
    app.kubernetes.io/instance: ${{ defaults.app_name }}-pg
    app.kubernetes.io/managed-by: kbcli
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
rules:
  - apiGroups: ['*']
    resources: ['*']
    verbs: ['*']
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${{ defaults.app_name }}-pg
  labels:
    sealos-db-provider-cr: ${{ defaults.app_name }}-pg
    app.kubernetes.io/instance: ${{ defaults.app_name }}-pg
    app.kubernetes.io/managed-by: kbcli
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ${{ defaults.app_name }}-pg
subjects:
  - kind: ServiceAccount
    name: ${{ defaults.app_name }}-pg
```

Every database resource carries the same three labels (`sealos-db-provider-cr`,
`app.kubernetes.io/instance`, `app.kubernetes.io/managed-by: kbcli`) set to its
own cluster name. Also set `cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}`
on each resource's `metadata.labels` (not on pod templates). Sealos groups the
instance by this label; Brain adoption on `*.sealos.io` lists by it too. Do
not change the KubeBlocks identity labels.

## Engine-specific Cluster differences

- **MySQL** (`apecloud-mysql`): labels/refs `kb.io/database: ac-mysql-8.0.30-1`,
  `clusterDefinitionRef: apecloud-mysql`, `clusterVersionRef: ac-mysql-8.0.30-1`,
  component `componentDefRef: mysql`, `name: mysql`.
- **MongoDB**: no clusterDefinitionRef; component uses
  `componentDef: mongodb`, `name: mongodb`, `serviceVersion: "8.0.4"`, label
  `kb.io/database: mongodb-8.0.4`.
- **Redis**: `clusterDefinitionRef: redis`, `topology: replication`, label
  `kb.io/database: redis-7.2.7`; two components: `componentDef: redis-7`
  (`name: redis`, with `serviceVersion: "7.2.7"`, an env entry
  `- name: CUSTOM_SENTINEL_MASTER_NAME` and a data volume) and
  `componentDef: redis-sentinel-7` (`name: redis-sentinel`, own data volume).
- **Kafka**: components `kafka-broker` + `kafka-controller` (+ optional
  `kafka-exporter`), annotation `kubeblocks.io/extra-env` with
  `KB_KAFKA_ENABLE_SASL/KB_KAFKA_PUBLIC_ACCESS` flags, label
  `kb.io/database: kafka-3.3.2`.

Available versions vary per region; check before pinning something newer:
`kubectl get clusterversions.apps.kubeblocks.io` (cluster-scoped, readable).

## Creating an application database (PostgreSQL/MySQL)

KubeBlocks provisions the server with only the default database. When the app
needs its own database name, add an idempotent init Job:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ${{ defaults.app_name }}-pg-init
  labels:
    cloud.sealos.io/deploy-on-sealos: ${{ defaults.app_name }}
spec:
  backoffLimit: 3
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: pgsql-init
          image: postgres:16-alpine
          imagePullPolicy: IfNotPresent
          env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: ${{ defaults.app_name }}-pg-conn-credential
                  key: password
            - name: PG_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: ${{ defaults.app_name }}-pg-conn-credential
                  key: endpoint
          command:
            - /bin/sh
            - -c
            - |
              set -eu
              DB=myappdb
              until pg_isready -h "${PG_ENDPOINT%:*}" -p "${PG_ENDPOINT##*:}" -U postgres; do sleep 2; done
              psql "postgresql://postgres:${PGPASSWORD}@${PG_ENDPOINT}/postgres" -tAc \
                "SELECT 1 FROM pg_database WHERE datname='${DB}'" | grep -q 1 || \
              psql "postgresql://postgres:${PGPASSWORD}@${PG_ENDPOINT}/postgres" -v ON_ERROR_STOP=1 \
                -c "CREATE DATABASE \"${DB}\";"
```

The same pattern (init Job + engine CLI image + readiness wait + idempotent
create) covers extensions (`CREATE EXTENSION IF NOT EXISTS vector`), users, and
seed SQL. Apps that crash-loop until their database exists usually just need
this Job plus patience — the workload restarts and succeeds once the Job runs.

## Operations

```bash
export KUBECONFIG=~/.sealos/kubeconfig
kubectl get clusters.apps.kubeblocks.io                       # list + phase
kubectl get secret <app>-pg-conn-credential -o jsonpath='{.data.password}' | base64 -d
kubectl delete cluster.apps.kubeblocks.io <name>              # delete database
```

A Cluster is usable when `status.phase: Running` (`wait-app.sh cluster/<name>`
waits for exactly this).
