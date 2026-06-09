# Phase 0: Preflight

Detect the user's environment, record what's available, guide them to fix what's missing.

**Hard rule:** Every run must start with a preflight capability scan before touching the project.
That means:
- Detect tool availability first
- Detect auth/workspace state first
- Record which later phases are currently blocked

Preflight is responsible for early detection, but only some failures are immediate stop conditions.
Do not treat Docker, `gh`, or `buildx` as universal entry requirements — they become mandatory only if the run actually needs local image build/push.

## Tool Install Policy

When `docker`, `gh`, or `kubectl` is missing, do not just print commands and stop.
Ask directly:

```text
Missing <tool>. Install it now? (y/n)
```

If the user answers `y`, install the tool for the current platform, then re-run the corresponding check.
If the install command needs elevated privileges, package-manager setup, or manual UI interaction, explain that before running it.

## Step 1: Environment Detection

Detect the local toolchain on every run. These checks are fast, and re-running them avoids stale results after the user installs a missing dependency such as `gh` or `kubectl`.

### 1.1 Detect Installed Tools

Run all checks:

```bash
# Commonly needed
docker --version 2>/dev/null
git --version 2>/dev/null

# Optional (enables script acceleration)
node --version 2>/dev/null
python3 --version 2>/dev/null

# Optional (enables GHCR push — preferred over Docker Hub)
gh --version 2>/dev/null

# Conditional (required for update-mode rollout operations)
# Check PATH first, then fallback to ~/.agents/bin/
kubectl version --client 2>/dev/null || ~/.agents/bin/kubectl version --client 2>/dev/null

# Always available (system built-in)
curl --version 2>/dev/null | head -1
which jq 2>/dev/null
```

Version strings are present when installed, `null` when missing.

Record as `ENV`:
```
ENV.docker    = true/false
ENV.git       = true/false
ENV.node      = true/false
ENV.python    = true/false
ENV.kubectl   = true/false   (required for update-mode rollout operations)
ENV.gh        = true/false   (enables zero-interaction GHCR push)
ENV.curl      = true/false
ENV.jq        = true/false
```

### 1.2 Docker Daemon Check

Tool detection and Docker daemon status are different checks. Always verify the daemon separately:

```bash
docker info 2>/dev/null
```

- Not installed → guide by platform:
  - Ask: `Missing Docker. Install it now? (y/n)`
  - If user answers `y`:
    - macOS: run `brew install --cask docker`, then tell the user to open Docker Desktop
    - Linux: run `curl -fsSL https://get.docker.com | sh`
- Installed but daemon not running → "Please start Docker Desktop (macOS) or `sudo systemctl start docker` (Linux)."

**git** — if missing:
- `brew install git` (macOS) or `sudo apt install git` (Linux)

### Optional and Path-Dependent Tools

**gh CLI (GitHub CLI):**
- If present and authenticated → enables **zero-interaction GHCR push**
- `build-push.mjs` auto-detects `gh auth status` and uses `gh auth token` to login to `ghcr.io`
- GHCR push alone is not enough for Sealos. For private GHCR packages, the deploy step must create an image pull Secret using the local `gh` CLI session.
- `sealos-deploy` should never ask the user to type registry host/username/password when `gh auth status` is already available locally.
- Missing `gh` is **not** a universal preflight failure
- `gh` becomes mandatory only when the selected image destination is GHCR
- If `gh` is missing, ask:
  - `Missing gh. Install it now? (y/n)`
  - If user answers `y`:
    - macOS: run `brew install gh`
    - Debian/Ubuntu: run `sudo apt install gh`
- Do not trigger `gh auth login` during environment detection
- Only trigger `gh auth login` later if the run actually reaches a GHCR push path chosen by the user

**Docker Hub login session:**
- Needed only when the selected image destination is Docker Hub
- Docker Hub path assumes the pushed image will be public at deploy time
- Private Docker Hub images are out of scope for `sealos-deploy` pull-secret automation
- `docker login` may need to be run manually by the user in another terminal
- Do not treat a missing Docker Hub login as a universal preflight blocker
- Ask for the registry destination later in Phase 4, then enforce the matching login path

**Node.js:**
- If missing, no problem. Pipeline uses fallback mode:
  - `score-model.mjs` → AI reads files and applies scoring rules directly
  - `detect-image.mjs` → AI runs curl commands for Docker Hub / GHCR API
  - `build-push.mjs` → AI runs `docker buildx` commands directly
  - `sealos-auth.mjs` → AI runs curl to exchange token for kubeconfig (workspace list/switch not available in fallback mode)

**Python:**
- If missing, Sealos template validation (Phase 5) uses AI self-check instead of `quality_gate.py`

**kubectl (required for in-place updates):**
- Needed for updating already-deployed apps with `kubectl set image` and `kubectl rollout`
- If `kubectl` is missing, ask:
  - `Missing kubectl. Install it now? (y/n)`
  - If user answers `y`:
    - macOS: run `brew install kubectl`
    - Debian/Ubuntu: run `sudo apt install kubectl`
- If `kubectl` is available outside PATH, use the absolute path for all kubectl commands

## Step 2: Capability Classification

Before touching the project, classify findings into:
- immediate stop conditions
- warnings that may become blocking later
- optional accelerators

### 2.1 Immediate Stop Conditions

Stop before project inspection only when one of these is true:
- Sealos authentication is unavailable and cannot be completed
- Workspace selection is incomplete
- The user provided a GitHub URL and `git` is unavailable, so the repository cannot be cloned
- `curl` is unavailable, so auth and fallback API checks cannot run

These are true entry blockers for a deploy run.

### 2.2 Build-Path Warnings

Detect these now and report them early, but do **not** stop the run yet:
- Docker CLI missing
- Docker daemon not running
- `gh` missing
- `gh auth status` failing
- Docker builder unavailable (`docker buildx version` or equivalent)
- Container registry connectivity looks unhealthy

These findings become hard blockers only if the run later determines that local image build/push is required.

### 2.3 Update-Path Warnings

Detect these now and report them early, but do **not** stop a fresh deploy:
- `kubectl` missing
- kubeconfig present but unusable

These become hard blockers only if the run enters UPDATE mode or needs rollout verification through kubectl.

### 2.4 Early Reporting Rule

At the end of preflight, explicitly tell the user:
- which items are ready
- which items are warnings only
- which later path each warning would block

Example:
- "Docker is not ready. This will block Phase 4 local build, but we can still continue to detect whether an existing image can be reused."
- "`kubectl` is missing. Fresh deploy can continue, but UPDATE mode and rollout verification will be blocked until it is installed."

## Step 3: Project Context

**Execution order override:** Do **not** execute this section until Step 4 auth/workspace checks are complete.
Run **Step 4: Sealos Cloud Auth** first, satisfy the immediate stop conditions, then come back to Step 3.

This section is intentionally documented here for readability, but it is operationally blocked behind Step 4.

Determine what we're deploying and gather project information.

### 2.1 Resolve Working Directory

**A) User provided a GitHub URL:**
```bash
WORK_DIR=$(mktemp -d)
git clone --depth 1 "<github-url>" "$WORK_DIR"
GITHUB_URL="<github-url>"
```

**B) User provided a local path:**
```bash
WORK_DIR="<local-path>"
```

**C) No input — deploy current project (most common):**
```bash
WORK_DIR="$(pwd)"
```

### 2.2 Git Repo Detection

```bash
# Is it a git repo?
git -C "$WORK_DIR" rev-parse --is-inside-work-tree 2>/dev/null

# Git metadata
git -C "$WORK_DIR" remote get-url origin 2>/dev/null      # → GITHUB_URL (if github.com)
git -C "$WORK_DIR" branch --show-current 2>/dev/null       # → BRANCH
git -C "$WORK_DIR" log --oneline -1 2>/dev/null            # → latest commit
```

Record:
```
PROJECT.work_dir    = resolved path
PROJECT.is_git      = true/false
PROJECT.github_url  = "https://github.com/owner/repo" or empty
PROJECT.repo_name   = basename of directory or parsed from URL
PROJECT.branch      = current branch
```

If `PROJECT.github_url` exists, parse `owner` and `repo` for Phase 2 image detection.

### 2.3 Read README

README is the single most important file for understanding a project. Read it now.

```bash
# Find README (case-insensitive)
ls "$WORK_DIR"/README* "$WORK_DIR"/readme* 2>/dev/null | head -1
```

Read the README content and extract:
- **Project description** — what does this project do?
- **Tech stack** — language, framework, database
- **Run/build instructions** — how to build, what port it listens on
- **Docker references** — `docker run`, `docker pull`, image names (ghcr.io/..., dockerhub/...)
- **Environment variables** — any `.env` examples or config descriptions

Record key findings in `PROJECT.readme_summary` for use in Phase 1 (assess) and Phase 2 (detect).

This avoids re-reading README in every phase. The AI already has it in context.

## Step 4: Sealos Cloud Auth (OAuth2 Device Grant Flow)

This step must complete before Step 3 project context begins in practice.

Uses RFC 8628 Device Authorization Grant — no token copy-paste needed.

### 4.0 Region Selection

Before auth, let the user choose which Sealos Cloud region to deploy to.

Read the default region and available regions from config:
```bash
DEFAULT_REGION=$(jq -r '.default_region' "<SKILL_DIR>/config.json")
```

**Always ask the user to confirm or choose a region.** Present the regions from `config.json` and allow custom input:

```
Which Sealos Cloud region do you want to deploy to?

  1. https://usw-1.sealos.io  (default)
  2. https://gzg.sealos.run
  3. https://bja.sealos.run
  4. https://hzh.sealos.run
  5. Enter a custom region URL

Default: https://usw-1.sealos.io
```

The region list comes from `config.json` `regions` array. If `regions` is not present, show only `default_region`.

If the user has an existing `~/.sealos/auth.json`, read the previously used region and offer it as an option:
```bash
PREV_REGION=$(jq -r '.region // empty' ~/.sealos/auth.json 2>/dev/null)
```

If `PREV_REGION` exists and differs from `DEFAULT_REGION`, include it in the choices.

Record the user's choice as `REGION` for use throughout the rest of this step and Phase 6.

**If the user picks a different region than the existing `~/.sealos/auth.json`**, the existing kubeconfig is invalid — force re-authentication.

### 4.1 Check auth status:

**With Node.js:**
```bash
node "<SKILL_DIR>/scripts/sealos-auth.mjs" check
```
Returns: `{ "authenticated": true/false, "kubeconfig_path": "...", "workspace": "ns-xxx" }`

**Without Node.js:**
```bash
test -f ~/.sealos/kubeconfig && echo '{"authenticated":true}' || echo '{"authenticated":false}'
```

### 4.2 If not authenticated — Device Grant Login:

**With Node.js (recommended):**
```bash
node "<SKILL_DIR>/scripts/sealos-auth.mjs" login [region-url]
```

If the script fails with `"error":"fetch failed"` or TLS/certificate error, retry with `--insecure`:
```bash
node "<SKILL_DIR>/scripts/sealos-auth.mjs" login [region-url] --insecure
```

If it still fails, fall back to curl (see below). **Once you switch to curl, use curl for the entire remaining flow** — do NOT mix curl and Node.js mid-flow.

The script will:
1. `POST <region>/api/auth/oauth2/device` with the `client_id` from `config.json`
2. Output a verification URL and user code to stderr
3. Auto-open the browser for the user
4. Poll `POST <region>/api/auth/oauth2/token` every 5s until approved
5. Exchange access_token for regional token via `POST <region>/api/auth/regionToken`
6. Save kubeconfig to `~/.sealos/kubeconfig` (mode 0600)
7. Save access_token, regional_token, and current_workspace to `~/.sealos/auth.json`

**Important — AI must always show the clickable URL to the user:**
Even though the script attempts to auto-open the browser, it may fail (e.g., headless environment, SSH session, sandbox restrictions).
After running the script, YOU (the AI) must extract the verification URL from stderr output and display it as a clickable link to the user:
```
Please click the link below to authorize:
<verification_uri_complete>
Authorization code: <user_code>
```
This ensures the user can always complete authorization regardless of whether auto-open succeeded.

Stdout outputs JSON result: `{ "kubeconfig_path": "...", "region": "...", "workspace": "ns-xxx" }`

**Without Node.js (curl fallback):**

**Important: once you enter the curl path, complete ALL steps with curl. Do NOT switch to Node.js or Python mid-flow.**

First, read constants from `<SKILL_DIR>/config.json`:
```bash
# Read skill constants (client_id, default_region)
CLIENT_ID=$(jq -r '.client_id' "<SKILL_DIR>/config.json")
DEFAULT_REGION=$(jq -r '.default_region' "<SKILL_DIR>/config.json")
```

Step 1 — Request device authorization:
```bash
REGION="${REGION:-$DEFAULT_REGION}"
DEVICE_RESP=$(curl -ksf -X POST "$REGION/api/auth/oauth2/device" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}&grant_type=urn:ietf:params:oauth:grant-type:device_code")
```
Note: `-k` skips TLS verification for self-signed certificates.

Extract fields from response:
```bash
DEVICE_CODE=$(echo "$DEVICE_RESP" | grep -o '"device_code":"[^"]*"' | cut -d'"' -f4)
USER_CODE=$(echo "$DEVICE_RESP" | grep -o '"user_code":"[^"]*"' | cut -d'"' -f4)
VERIFY_URL=$(echo "$DEVICE_RESP" | grep -o '"verification_uri_complete":"[^"]*"' | cut -d'"' -f4)
INTERVAL=$(echo "$DEVICE_RESP" | grep -o '"interval":[0-9]*' | cut -d: -f2)
INTERVAL=${INTERVAL:-5}
```

Step 2 — Show the authorization link to user:
```
Please click the link below to authorize:
$VERIFY_URL
Authorization code: $USER_CODE
```
If `VERIFY_URL` is empty, use `verification_uri` instead and show the user code separately.

Step 3 — Poll for token:
```bash
while true; do
  sleep "$INTERVAL"
  TOKEN_RESP=$(curl -ksf -X POST "$REGION/api/auth/oauth2/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "client_id=${CLIENT_ID}&grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=$DEVICE_CODE")

  # Check for access_token in response
  ACCESS_TOKEN=$(echo "$TOKEN_RESP" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
  if [ -n "$ACCESS_TOKEN" ]; then
    break
  fi

  # Check for terminal errors
  ERROR=$(echo "$TOKEN_RESP" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
  case "$ERROR" in
    authorization_pending) continue ;;
    slow_down) INTERVAL=$((INTERVAL + 5)) ;;
    access_denied) echo "User denied authorization"; exit 1 ;;
    expired_token) echo "Device code expired"; exit 1 ;;
    *) echo "Error: $ERROR"; exit 1 ;;
  esac
done
```

Step 4 — Exchange token for regional token + kubeconfig (still curl):
```bash
REGION_RESP=$(curl -ksf -X POST "$REGION/api/auth/regionToken" \
  -H "Authorization: $ACCESS_TOKEN" \
  -H "Content-Type: application/json")
# Server returns { data: { token, kubeconfig } }
REGIONAL_TOKEN=$(echo "$REGION_RESP" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
# Extract kubeconfig — it's a multi-line YAML value inside JSON
mkdir -p ~/.sealos
node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf-8')); process.stdout.write(d.data.kubeconfig)" <<< "$REGION_RESP" > ~/.sealos/kubeconfig 2>/dev/null \
  || python3 -c "import sys,json; print(json.load(sys.stdin)['data']['kubeconfig'])" <<< "$REGION_RESP" > ~/.sealos/kubeconfig
chmod 600 ~/.sealos/kubeconfig
```
Note: kubeconfig is multi-line YAML embedded in JSON — simple grep won't work. Use node/python one-liner to extract it. Save auth metadata with tokens:
```bash
cat > ~/.sealos/auth.json << EOF
{"region":"$REGION","access_token":"$ACCESS_TOKEN","regional_token":"$REGIONAL_TOKEN","authenticated_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","auth_method":"oauth2_device_grant"}
EOF
chmod 600 ~/.sealos/auth.json
```

### 4.3 Workspace Selection (every deploy)

After auth is confirmed, **always** let the user choose which workspace to deploy to. The last-used workspace is the default.

**With Node.js:**
```bash
node "<SKILL_DIR>/scripts/sealos-auth.mjs" list
```
Returns:
```json
{
  "current": "ns-abc",
  "workspaces": [
    { "uid": "...", "id": "ns-abc", "teamName": "My Team", "role": 0, "nstype": 1 },
    { "uid": "...", "id": "ns-def", "teamName": "Dev Team", "role": 0, "nstype": 0 },
    { "uid": "...", "id": "ns-ghi", "teamName": "Staging", "role": 2, "nstype": 0 }
  ]
}
```

Present the workspace list to the user. **Put the `current` workspace first**, mark it as last used:

```
Which workspace do you want to deploy to?

  1. ns-abc — My Team ← current
  2. ns-def — Dev Team
  3. ns-ghi — Staging

Default: ns-abc (My Team)
```

Display format is `id — teamName`. The `current` field from the JSON indicates the last-used workspace — always list it first.

- If the user picks the same workspace as `current` → no action needed, kubeconfig is already valid.
- If the user picks a different workspace → switch:

```bash
node "<SKILL_DIR>/scripts/sealos-auth.mjs" switch <ns-id>
```

This updates `~/.sealos/kubeconfig` and records the new workspace as `current_workspace` in `auth.json` for next time.

**Without Node.js (curl fallback):**

List workspaces:
```bash
NS_RESP=$(curl -ksf "$REGION/api/auth/namespace/list" \
  -H "Authorization: $REGIONAL_TOKEN")
```

Parse and present options to user. If the user picks a different workspace:
```bash
SWITCH_RESP=$(curl -ksf -X POST "$REGION/api/auth/namespace/switch" \
  -H "Authorization: $REGIONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"ns_uid\":\"$TARGET_UID\"}")
NEW_TOKEN=$(echo "$SWITCH_RESP" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)

# Get new kubeconfig
KC_RESP=$(curl -ksf "$REGION/api/auth/getKubeconfig" \
  -H "Authorization: $NEW_TOKEN")
node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf-8')); process.stdout.write(d.data.kubeconfig)" <<< "$KC_RESP" > ~/.sealos/kubeconfig 2>/dev/null \
  || python3 -c "import sys,json; print(json.load(sys.stdin)['data']['kubeconfig'])" <<< "$KC_RESP" > ~/.sealos/kubeconfig
chmod 600 ~/.sealos/kubeconfig

# Update auth.json with new token
REGIONAL_TOKEN="$NEW_TOKEN"
```

**If only one workspace exists**, skip the selection prompt and use it directly.

## Step 5: Ready

Only reach this section after:
- Step 1 environment detection/checks passed
- Step 2 capability classification completed
- Step 4 auth/workspace checks passed
- And only then Step 3 project context was collected

Report to user with a short readiness summary. This is a user-facing status snapshot, not a full artifact dump.
Keep it focused on the key capabilities and blockers only.

Do **not** add a "full details" section in the default output.

Recommended format:

```
Project:
  ✓ <PROJECT.repo_name> (<PROJECT.work_dir>)
  ✓ git: <BRANCH> ← <GITHUB_URL or "local only">
  ✓ README: <one-line summary of what the project does>

Environment:
  ○ Docker <version>         (or: ✗ Docker — local build path currently blocked)
  ✓ git <version>
  ○ Node.js <version>        (or: ✗ Node.js — using AI fallback mode)
  ○ Python <version>          (or: ✗ Python — template validation via AI)
  ○ kubectl <version>        (or: ✗ kubectl — update/rollout path blocked)
  ○ gh <version>             (or: ✗ gh CLI — local GHCR push path blocked)

Auth:
  ✓ Sealos Cloud (<region>)
  ✓ Workspace: <ns-id> (<teamName>)
```

If Docker, `gh`, buildx, or registry connectivity are not ready, report them now as path-specific warnings. Only upgrade them to hard blockers if Phase 2/3 confirms that local build/push is required.

Output rules:
- Show only the high-signal items a user needs to decide whether to continue
- Do not print raw command output or exhaustive diagnostics in the normal summary
- If a capability is missing, explain briefly which later path it blocks
- Prefer one-line project identification plus compact Environment/Auth sections over long prose

Record `ENV` and `PROJECT` for subsequent phases → proceed to `modules/pipeline.md`.
