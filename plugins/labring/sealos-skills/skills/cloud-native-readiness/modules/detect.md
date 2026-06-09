# Module: Existing Docker Artifacts Detection

## Purpose

Detect whether the project already has Docker/K8s configuration and assess its completeness.

## Execution Steps

### Step 1: Scan for Docker Files

```bash
# Dockerfile variants
find . -maxdepth 3 -name "Dockerfile" -o -name "Dockerfile.*" -o -name "*.Dockerfile" 2>/dev/null | grep -v node_modules

# Docker Compose variants
find . -maxdepth 3 \( -name "docker-compose.yml" -o -name "docker-compose.yaml" -o -name "compose.yml" -o -name "compose.yaml" -o -name "docker-compose.*.yml" \) 2>/dev/null | grep -v node_modules

# .dockerignore
find . -maxdepth 3 -name ".dockerignore" 2>/dev/null | grep -v node_modules

# Docker documentation
find . -maxdepth 3 -name "DOCKER.md" -o -name "docker-README.md" 2>/dev/null | grep -v node_modules

# Docker-related env files
find . -maxdepth 3 -name ".env.docker*" -o -name "*.dev.vars*" 2>/dev/null | grep -v node_modules

# Entrypoint scripts
find . -maxdepth 3 -name "docker-entrypoint.sh" -o -name "entrypoint.sh" 2>/dev/null | grep -v node_modules
```

### Step 2: Scan for Kubernetes / Deployment Manifests

```bash
# Kubernetes manifests
find . -maxdepth 4 -type d \( -name "k8s" -o -name "kubernetes" -o -name "kube" -o -name "manifests" \) 2>/dev/null | grep -v node_modules

# Helm charts
find . -maxdepth 4 -type d -name "charts" 2>/dev/null | grep -v node_modules
find . -maxdepth 4 -name "Chart.yaml" 2>/dev/null | grep -v node_modules

# Kustomize
find . -maxdepth 4 -name "kustomization.yaml" -o -name "kustomization.yml" 2>/dev/null | grep -v node_modules

# Skaffold
find . -maxdepth 2 -name "skaffold.yaml" 2>/dev/null

# Tilt
find . -maxdepth 2 -name "Tiltfile" 2>/dev/null

# Docker Swarm
grep -rl "deploy:" docker-compose*.yml compose*.yml 2>/dev/null | head -5
```

### Step 3: Scan for CI/CD Docker Build Steps

```bash
# GitHub Actions
grep -rl "docker" .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null
grep -rE "docker.*build|docker.*push|ghcr\.io|docker\.io" .github/workflows/ 2>/dev/null | head -10

# GitLab CI
grep -E "docker|image:|registry" .gitlab-ci.yml 2>/dev/null | head -10

# Other CI
find . -maxdepth 2 \( -name "Jenkinsfile" -o -name ".circleci" -o -name "bitbucket-pipelines.yml" \) 2>/dev/null
```

### Step 4: Detect Container Registry References

```bash
# Search for registry references in all config files
grep -rE "(ghcr\.io|docker\.io|registry\.hub|ecr\.aws|gcr\.io|azurecr\.io|quay\.io)/[a-z0-9._/-]+" . \
  --include="*.yml" --include="*.yaml" --include="*.json" --include="*.toml" --include="*.md" \
  2>/dev/null | grep -v node_modules | head -10

# Check package.json for docker-related scripts
grep -E '"docker|"container|"image' package.json 2>/dev/null
```

### Step 5: Assess Quality of Existing Artifacts

If Dockerfile found, check for:

```bash
# Multi-stage build?
grep -c "^FROM" Dockerfile

# Non-root user?
grep -E "USER|useradd|adduser" Dockerfile

# Health check?
grep "HEALTHCHECK" Dockerfile

# Proper .dockerignore?
if [ -f ".dockerignore" ]; then
  wc -l .dockerignore
  grep -E "node_modules|\.git|\.env" .dockerignore
fi

# Fixed base image version (not :latest)?
grep "^FROM" Dockerfile | grep -v ":latest"

# Uses COPY before RUN for cache optimization?
grep -n "^COPY\|^RUN" Dockerfile | head -20
```

If docker-compose found, check for:

```bash
# Health checks defined?
grep -c "healthcheck" docker-compose.yml

# Volumes for persistent data?
grep -c "volumes:" docker-compose.yml

# Networks defined?
grep -c "networks:" docker-compose.yml

# Environment variables properly handled?
grep -cE "env_file|\$\{" docker-compose.yml

# Restart policy?
grep -E "restart:" docker-compose.yml
```

### Step 6: Produce Artifact Inventory

**Output Format**:

```yaml
artifacts:
  status: "complete | partial | none"

  dockerfile:
    found: true | false
    paths: ["Dockerfile", "apps/api/Dockerfile"]
    quality:
      multi_stage: true | false
      non_root_user: true | false
      health_check: true | false
      fixed_versions: true | false
      cache_optimized: true | false
      score: "{good | acceptable | poor}"

  docker_compose:
    found: true | false
    paths: ["docker-compose.yml"]
    quality:
      health_checks: true | false
      volumes: true | false
      networks: true | false
      env_handling: true | false
      restart_policy: true | false
      score: "{good | acceptable | poor}"

  dockerignore:
    found: true | false
    paths: [".dockerignore"]
    covers_essentials: true | false  # node_modules, .git, .env

  kubernetes:
    found: true | false
    type: "raw manifests | helm | kustomize | none"
    paths: []

  ci_cd:
    docker_build: true | false
    registry_push: true | false
    platforms: ["github-actions", "gitlab-ci"]

  registry:
    found: true | false
    references: ["ghcr.io/org/repo"]

  entrypoint:
    found: true | false
    paths: []

  documentation:
    found: true | false
    paths: []

  # Overall completeness
  completeness:
    has_build: true | false          # Can build an image
    has_orchestration: true | false   # Can run with dependencies
    has_deployment: true | false      # Can deploy to K8s/cloud
    has_ci: true | false             # Automated build pipeline
    summary: "Production-ready | Development-ready | Incomplete | None"
```

### Decision Points

Based on artifact inventory:

**Complete** (`status: "complete"`):
- Has Dockerfile with acceptable+ quality
- Has docker-compose with all dependent services
- Has .dockerignore
→ Report findings, no need for `dockerfile-skill`

**Partial** (`status: "partial"`):
- Has some artifacts but missing key pieces
- Or has artifacts with poor quality
→ Report gaps, suggest improvements or invoke `dockerfile-skill`

**None** (`status: "none"`):
- No Docker artifacts found
→ Proceed to `dockerfile-skill` if readiness score permits
