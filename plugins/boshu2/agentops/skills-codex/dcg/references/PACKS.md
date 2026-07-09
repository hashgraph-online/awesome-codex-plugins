# DCG Rule Packs

DCG uses a modular pack system with 49+ rule packs organized by domain.

## Core Packs (Always Enabled)

These cannot be disabled—they catch the most common destructive patterns.

### core.git

| Pattern | Blocked | Safe Alternative |
|---------|---------|-----------------|
| `git reset --hard` | Yes | `git stash` |
| `git checkout -- <file>` | Yes | `git stash push <file>` |
| `git clean -f` | Yes | `git clean -n` (dry-run) |
| `git push --force` | Yes | `git push --force-with-lease` |
| `git branch -D` | Yes | `git branch -d` (checks merge) |
| `git stash drop` | Yes | `git stash list` first |
| `git stash clear` | Yes | Review stashes first |

**Safe patterns (allowed):**
- `git checkout -b` — Creating branches
- `git restore --staged` — Unstaging files
- `git clean -n` / `--dry-run` — Preview mode
- `git push --force-with-lease` — Safe force push

### core.filesystem

| Pattern | Blocked | Condition |
|---------|---------|-----------|
| `rm -rf /` | Yes | Always |
| `rm -rf /*` | Yes | Always |
| `rm -rf ~` | Yes | Always |
| `rm -rf /home` | Yes | System paths |
| `rm -rf /path` | Depends | Non-temp paths blocked |

**Safe patterns (allowed):**
- `rm -rf /tmp/*` — Temp directory
- `rm -rf /var/tmp/*` — Temp directory
- `rm -rf $TMPDIR/*` — User temp
- `rm -rf ./build` — Relative paths in project

---

## Optional Packs by Category

Enable with `DCG_PACKS` or in `.dcg.toml`:

```toml
[packs]
enabled = ["database.postgresql", "kubernetes.kubectl", "cloud.aws"]
```

### Database Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `database.postgresql` | Data destruction | `DROP DATABASE`, `TRUNCATE`, `DELETE` w/o WHERE |
| `database.mysql` | Data destruction | `DROP`, `TRUNCATE`, unsafe deletes |
| `database.mongodb` | Collection drops | `db.dropDatabase()`, `db.collection.drop()` |
| `database.redis` | Data wipes | `FLUSHALL`, `FLUSHDB`, `DEBUG SEGFAULT` |
| `database.sqlite` | File deletion | `.backup` overwrites, `DROP TABLE` |

### Container Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `containers.docker` | System prune | `docker system prune -a`, `docker rm -f $(...)` |
| `containers.compose` | Stack destruction | `docker-compose down -v --rmi all` |
| `containers.podman` | Same as docker | Pod and container mass deletion |

### Kubernetes Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `kubernetes.kubectl` | Namespace/cluster | `delete namespace`, `delete --all`, `drain --force` |
| `kubernetes.helm` | Release destruction | `helm uninstall`, `helm delete --purge` |
| `kubernetes.kustomize` | Dangerous applies | `delete -k` without confirmation |

### Cloud Provider Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `cloud.aws` | Resource destruction | `aws ec2 terminate-instances`, `aws s3 rb --force` |
| `cloud.azure` | Resource groups | `az group delete`, `az vm delete` |
| `cloud.gcp` | Project/instance | `gcloud projects delete`, instance termination |

### Storage Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `storage.s3` | Bucket destruction | `aws s3 rb`, `aws s3 rm --recursive` |
| `storage.gcs` | Bucket destruction | `gsutil rm -r`, `gsutil rb` |
| `storage.azure_blob` | Container deletion | `az storage container delete` |
| `storage.minio` | S3-compatible ops | `mc rb --force` |

### Infrastructure Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `infrastructure.terraform` | State destruction | `terraform destroy`, `terraform state rm` |
| `infrastructure.ansible` | Dangerous playbooks | File deletion tasks, service stops |
| `infrastructure.pulumi` | Stack destruction | `pulumi destroy`, `pulumi stack rm` |

### CI/CD Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `cicd.github_actions` | Workflow deletion | Dangerous `run:` commands in workflows |
| `cicd.gitlab_ci` | Pipeline destruction | Risky `script:` blocks |
| `cicd.circleci` | Config issues | Destructive commands in jobs |
| `cicd.jenkins` | Pipeline risks | Shell steps with dangerous commands |

### Secrets Management Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `secrets.vault` | Secret deletion | `vault kv delete`, `vault secrets disable` |
| `secrets.aws_secrets` | Secret destruction | `aws secretsmanager delete-secret` |
| `secrets.doppler` | Config deletion | `doppler configs delete` |
| `secrets.onepassword` | Vault destruction | `op vault delete` |

### Messaging Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `messaging.kafka` | Topic deletion | `kafka-topics.sh --delete` |
| `messaging.rabbitmq` | Queue/exchange | `rabbitmqctl delete_queue` |
| `messaging.nats` | Stream deletion | `nats stream delete` |
| `messaging.sqs_sns` | Queue destruction | `aws sqs delete-queue` |

### Search & Analytics Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `search.elasticsearch` | Index deletion | `DELETE /index`, `_delete_by_query` |
| `search.algolia` | Index clear | `clearObjects`, `deleteIndex` |
| `search.meilisearch` | Index destruction | Index deletion APIs |
| `search.opensearch` | Same as ES | Index and alias deletion |

### Monitoring Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `monitoring.datadog` | Monitor deletion | API calls to delete monitors |
| `monitoring.prometheus` | Rule deletion | Recording rule destruction |
| `monitoring.splunk` | Index deletion | Index and data destruction |
| `monitoring.newrelic` | Alert deletion | Policy and condition removal |
| `monitoring.pagerduty` | Service deletion | Escalation policy destruction |

### Backup Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `backup.restic` | Snapshot deletion | `restic forget --prune` |
| `backup.borg` | Archive deletion | `borg delete`, `borg prune` |
| `backup.rclone` | Remote deletion | `rclone delete`, `rclone purge` |
| `backup.velero` | Backup destruction | `velero backup delete` |

### Platform Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `platform.github` | Repo destruction | `gh repo delete` |
| `platform.gitlab` | Project deletion | `glab project delete` |

### DNS Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `dns.cloudflare` | Zone destruction | `cloudflare dns delete` |
| `dns.route53` | Record deletion | `aws route53 change-resource-record-sets DELETE` |

### Payment Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `payment.stripe` | Customer/sub deletion | API calls to delete customers |
| `payment.braintree` | Transaction voids | Refund and void operations |
| `payment.square` | Payment cancellation | Payment and customer deletion |

### Load Balancer Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `lb.elb` | LB destruction | `aws elb delete-load-balancer` |
| `lb.haproxy` | Config destruction | Runtime API deletions |
| `lb.nginx` | Config issues | Dangerous reload patterns |
| `lb.traefik` | Dynamic config | Router and service deletion |

### CDN Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `cdn.cloudflare_workers` | Worker deletion | `wrangler delete` |
| `cdn.cloudfront` | Distribution deletion | `aws cloudfront delete-distribution` |
| `cdn.fastly` | Service destruction | Service and VCL deletion |

### API Gateway Packs

| Pack | Blocks | Examples |
|------|--------|----------|
| `api.apigee` | Proxy deletion | API proxy and product deletion |
| `api.aws` | Gateway destruction | `aws apigateway delete-rest-api` |
| `api.kong` | Route deletion | Service and route destruction |

---

## Enabling Packs

### Via Environment Variable

```bash
export DCG_PACKS="database.postgresql,kubernetes.kubectl,cloud.aws"
```

### Via Project Config (.dcg.toml)

```toml
[packs]
enabled = [
    "database.postgresql",
    "database.mysql",
    "kubernetes.kubectl",
    "kubernetes.helm",
    "cloud.aws",
    "storage.s3"
]
```

### Via User Config (~/.config/dcg/config.toml)

```toml
[packs]
enabled = ["containers.docker", "platform.github"]
```

### Disabling Specific Packs

```bash
# Disable helm even if kubernetes is enabled
export DCG_DISABLE="kubernetes.helm"
```

---

## Pack Inspection

```bash
# List all packs
dcg packs

# Show patterns in a pack
dcg packs --verbose database.postgresql

# Check which packs would match a command
dcg explain "kubectl delete namespace prod"
```
