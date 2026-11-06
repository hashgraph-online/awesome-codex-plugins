#!/usr/bin/env bash
set -euo pipefail

# host0 publish script — two-phase static deploy via the host0 REST API.
# stdout: the live url (only). stderr: progress + publish_result.* /
# login_result.* contract lines.
#
# exit codes: 0 ok · 1 error · 3 waiting for the user to approve a device
# login in their browser (show them the link + code, then run again).

# bump on every change to this script: it rides in x-host0-client
# (<agent>/<version>) so the first-deploy metrics can tell script versions apart.
PUBLISH_SH_VERSION="2026.11.04"
DEFAULT_BASE_URL="https://host0.ai"
BASE_URL="$DEFAULT_BASE_URL"
CREDENTIALS_FILE="$HOME/.host0/credentials"
# a device login in progress (base url, device code, user code, expiry) —
# lets the next run pick up the approval instead of starting over.
DEVICE_STATE_FILE="$HOME/.host0/device.json"
API_KEY=""
API_KEY_SOURCE="none"
ALLOW_NONHOST0_BASE_URL=0
NAME=""
SLUG=""
APP_ID=""
VISIBILITY=""
CLIENT=""
MESSAGE=""
TARGET=""
MODE="publish"          # publish | login | login-wait
NO_LOGIN=0
LOGIN_WAIT_SECONDS="${HOST0_LOGIN_WAIT_SECONDS:-90}"

# set only when *this run* created the app — the cleanup trap deletes it if the
# run then fails before the app goes live. never set for an app resolved via
# --slug / --app-id / the state file.
CREATED_APP_ID=""
CREATED_APP_SLUG=""
CLEANUP_DONE=0

usage() {
  cat <<'USAGE'
Usage: publish.sh <dir|file> [options]
       publish.sh --pull --slug <slug> [dir]
                                   Download an app's live files to edit them
       publish.sh --login          Start (or re-show) a device login
       publish.sh --login-wait     Wait for the user to approve it

Publishes a directory of static files — or a single file (a PDF, an image, one
HTML page), which is served at the app's root URL — to host0 and prints the
live URL.

With no API key, publish.sh starts a device login: it prints a link + code and
exits 3 — show them to the user, then run the same command again.

Options:
  --name <text>           App display name when creating (default: directory or
                          file basename). The URL gets a random slug — rename it
                          to something readable in the dashboard, or with
                          PATCH /api/v1/apps/{app_id} {"slug": "…"}
  --slug <slug>           Update the existing app with this slug (its current one)
  --app-id <uuid>         Update the existing app with this id
  --visibility <mode>     Set visibility after publish: private (default: owner +
                          invited emails) | link (anyone with the URL, never
                          indexed) | public (public on the web, indexable)
  --message <text>        A note for this version, e.g. "New pricing table"
                          (≤ 200 characters; shown in the version list)
  --pull                  Download the live version of --slug/--app-id into
                          [dir] (default: ./<slug>; must be empty or new), set
                          up so publishing that folder updates the same app
  --client <name>         Agent name for attribution (e.g. claude-code, claude-ai,
                          cursor). Default: $HOST0_CLIENT, else detected from
                          the environment, else "unknown"
  --api-key <key>         API key (prefer $HOST0_API_KEY or ~/.host0/credentials)
  --base-url <url>        API base (default: https://host0.ai)
  --allow-nonhost0-base-url
                          Allow sending the API key to a non-default base URL
  --login                 Start a device login (or re-show the pending one) and
                          exit 3: the user approves it in their browser
  --login-wait            Wait for that approval, save the key, exit 0
                          (3 = still pending, 1 = denied)
  --wait <seconds>        How long to wait for an approval (default 90, or
                          $HOST0_LOGIN_WAIT_SECONDS)
  --no-login              With no API key, fail instead of starting a login
  --help                  Show this help

Exit codes: 0 ok · 1 error · 3 waiting for the user's approval
USAGE
  exit 1
}

die() { echo "error: $1" >&2; exit 1; }

# on a failed run, delete the app this run created so a failed first publish
# doesn't leave an orphan app (it counts against the account's app cap). only
# ever touches an app created by this run, and only before it went live.
cleanup_orphan_app() {  # cleanup_orphan_app <exit status>
  local rc=$1
  if [[ $rc -eq 0 || "$CLEANUP_DONE" -eq 1 || -z "$CREATED_APP_ID" ]]; then
    return 0
  fi
  CLEANUP_DONE=1

  local code status_out
  # a finalize that went through on the server but whose answer never came
  # back (a reset, a not_pending whose status read then failed) leaves a
  # live app behind this failure. ask the deployment first and never delete
  # blind: a live — or unknown — deployment keeps the app.
  if [[ -n "${DEPLOYMENT_ID:-}" ]]; then
    set +e
    status_out=$(net_curl idem -sS "$BASE_URL/api/v1/deployments/$DEPLOYMENT_ID" \
      -K "$AUTH_CFG" \
      -H "x-host0-client: ${CLIENT_HEADER_VALUE:-unknown/$PUBLISH_SH_VERSION}" \
      -w '\n%{http_code}' 2>/dev/null)
    code=$?
    set -e
    if [[ $code -ne 0 || "${status_out##*$'\n'}" != "200" ]] ||
       [[ "$(echo "${status_out%$'\n'*}" | jq -r '.live // false' 2>/dev/null)" != "false" ]]; then
      echo "warning: not deleting the app this run created ($CREATED_APP_SLUG, $CREATED_APP_ID) — its deployment may have gone live. Check it with GET $BASE_URL/api/v1/apps/$CREATED_APP_SLUG and delete it from your dashboard if it isn't." >&2
      echo "publish_result.cleanup=failed" >&2
      echo "publish_result.cleanup_slug=$CREATED_APP_SLUG" >&2
      return 0
    fi
  fi

  set +e
  code=$(net_curl once -sS -o /dev/null -w '%{http_code}' -X DELETE \
    "$BASE_URL/api/v1/apps/$CREATED_APP_ID" \
    -K "$AUTH_CFG" \
    -H "x-host0-client: ${CLIENT_HEADER_VALUE:-unknown/$PUBLISH_SH_VERSION}" 2>/dev/null)
  set -e

  if [[ "$code" =~ ^2[0-9][0-9]$ ]]; then
    echo "Cleaning up: deleted the app this run created ($CREATED_APP_SLUG) — it never went live." >&2
    echo "publish_result.cleanup=deleted" >&2
    echo "publish_result.cleanup_slug=$CREATED_APP_SLUG" >&2
  else
    echo "warning: could not delete the app this run created ($CREATED_APP_SLUG, $CREATED_APP_ID) — delete it from your dashboard (HTTP $code)." >&2
    echo "publish_result.cleanup=failed" >&2
    echo "publish_result.cleanup_slug=$CREATED_APP_SLUG" >&2
  fi
}
# EXIT: the orphan cleanup (it still needs the key), then the private temp dir
# holding the key's curl config goes.
on_exit() {
  local rc=$?
  cleanup_orphan_app "$rc"
  if [[ -n "${SECRET_DIR:-}" ]]; then rm -rf "$SECRET_DIR"; fi
  exit "$rc"
}
# the signal traps exit rather than clean up directly, so the EXIT trap runs
# once with a non-zero status (on a bare INT trap $? can still be 0).
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# every request goes through net_curl: sandboxes (claude.ai and friends) see
# transient connection resets, tls failures and connect timeouts on the way
# out, so a failed transport is retried up to 4 times (1s, 2s, 4s backoff).
# curl exit 6/7/35 (dns, connect, tls handshake) never reached the server and
# are always retried, and so is a 28 that timed out while connecting or in the
# tls handshake ("SSL connection timeout", "Connection timed out after") —
# seen from claude.ai sandboxes on 2026-09-30. other 28s and 52/56 (timeout
# mid-transfer, empty reply, reset) may have reached the server, so only calls
# marked idempotent retry them. on final failure it returns 1 — never curl's
# own code (3 is ours: "waiting for approval").
NET_ATTEMPTS=4
net_curl() {  # net_curl idem|once <curl args…> → curl's stdout
  local mode="$1" attempt=1 delay=1 rc out host="" a retry errf
  shift
  errf=$(mktemp "${TMPDIR:-/tmp}/host0-curl.XXXXXX")
  for a in "$@"; do
    if [[ "$a" =~ ^https?://([^/]+) ]]; then host="${BASH_REMATCH[1]}"; break; fi
  done
  while :; do
    set +e
    out=$(curl --connect-timeout 10 "$@" 2>"$errf")
    rc=$?
    set -e
    cat "$errf" >&2
    if [[ $rc -eq 0 ]]; then
      rm -f "$errf"
      printf '%s' "$out"
      return 0
    fi
    retry=0
    case "$rc" in
      6|7|35) retry=1 ;;
      28) if [[ "$mode" == "idem" ]] || grep -qE 'SSL connection timeout|Connection timed out after|Failed to connect|Resolving timed out' "$errf"; then retry=1; fi ;;
      52|56) [[ "$mode" == "idem" ]] && retry=1 ;;
    esac
    if [[ $retry -eq 1 && $attempt -lt $NET_ATTEMPTS ]]; then
      attempt=$((attempt + 1))
      echo "host0: network hiccup reaching ${host:-host0} (curl $rc) — retrying $attempt/$NET_ATTEMPTS" >&2
      sleep "$delay"
      delay=$((delay * 2))
      continue
    fi
    rm -f "$errf"
    printf '%s' "$out"
    if [[ $retry -eq 1 ]]; then
      echo "host0: could not reach ${host:-host0} after $NET_ATTEMPTS attempts (curl $rc) — if this keeps happening, the network may be blocking ${host:-it}: ask the user to allow it." >&2
    fi
    return 1
  done
}

command -v curl >/dev/null 2>&1 || die "requires curl — install curl and retry"
command -v jq >/dev/null 2>&1 || die "requires jq — install jq (e.g. brew install jq / apt install jq) and retry"

# secrets never go on a command line: argv is readable by every local user
# (ps). the bearer key reaches curl through a config file (-K, any curl
# version) and the device code through a request-body file, both 0600 in a
# 0700 temp dir that the EXIT trap removes (a kill -9 leaves it behind, in
# the user's own temp dir).
SECRET_DIR=$(umask 077 && mktemp -d "${TMPDIR:-/tmp}/host0-secrets.XXXXXX") ||
  die "could not create a private temp dir in ${TMPDIR:-/tmp}"
chmod 700 "$SECRET_DIR"
AUTH_CFG="$SECRET_DIR/auth.curlrc"
DEVICE_BODY_FILE="$SECRET_DIR/device-token.json"

# write the curl config that carries the bearer key; call again whenever
# API_KEY changes. builtins only (printf), so the key never reaches an argv.
write_auth_config() {
  local k="$API_KEY"
  case "$k" in
    *[[:space:][:cntrl:]]*) die "the API key contains whitespace or control characters — check HOST0_API_KEY / --api-key / $CREDENTIALS_FILE" ;;
  esac
  # curl config quoting: backslash and double quote are escaped inside "…"
  k=${k//\\/\\\\}
  k=${k//\"/\\\"}
  ( umask 077 && printf 'header = "authorization: Bearer %s"\n' "$k" > "$AUTH_CFG" )
}

if command -v shasum >/dev/null 2>&1; then
  SHA_TOOL="shasum"
elif command -v sha256sum >/dev/null 2>&1; then
  SHA_TOOL="sha256sum"
else
  die "requires shasum or sha256sum for file hashing"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)       NAME="$2"; shift 2 ;;
    --slug)       SLUG="$2"; shift 2 ;;
    --app-id)     APP_ID="$2"; shift 2 ;;
    --visibility) VISIBILITY="$2"; shift 2 ;;
    --client)     CLIENT="$2"; shift 2 ;;
    --message)    MESSAGE="$2"; shift 2 ;;
    --api-key)    API_KEY="$2"; API_KEY_SOURCE="flag"; shift 2 ;;
    --base-url)   BASE_URL="$2"; shift 2 ;;
    --allow-nonhost0-base-url) ALLOW_NONHOST0_BASE_URL=1; shift ;;
    --login)      MODE="login"; shift ;;
    --login-wait) MODE="login-wait"; shift ;;
    --pull)       MODE="pull"; shift ;;
    --wait)       LOGIN_WAIT_SECONDS="$2"; shift 2 ;;
    --no-login)   NO_LOGIN=1; shift ;;
    --help|-h)    usage ;;
    -*)           die "unknown option: $1" ;;
    *)            [[ -z "$TARGET" ]] && TARGET="$1" || die "unexpected argument: $1"; shift ;;
  esac
done

[[ "$LOGIN_WAIT_SECONDS" =~ ^[0-9]+$ ]] || die "invalid --wait: $LOGIN_WAIT_SECONDS (seconds, e.g. --wait 90)"

if [[ "$MODE" == "publish" ]]; then
  [[ -n "$TARGET" ]] || usage
  # a directory (its contents become the site root) or one file (served at /).
  if [[ -d "$TARGET" ]]; then
    TARGET_KIND="dir"
  elif [[ -f "$TARGET" ]]; then
    TARGET_KIND="file"
  else
    die "not a file or directory: $TARGET — publish the directory that contains index.html, or a single file"
  fi
fi

if [[ -n "$VISIBILITY" ]]; then
  case "$VISIBILITY" in
    private|link|public) ;;
    *) die "invalid --visibility: $VISIBILITY (must be private, link, or public)" ;;
  esac
fi

BASE_URL="${BASE_URL%/}"

# attribution: x-host0-client: <agent>/<publish.sh version>, sent to the
# platform api only (never to upload hosts). <agent> = --client >
# $HOST0_CLIENT > detected from the environment > "unknown". detection uses
# the markers agents set in the shells they spawn — the same list as vercel's
# @vercel/detect-agent (AI_AGENT is its proposed standard). CURSOR_TRACE_ID
# comes last: every process started from cursor's terminal inherits it,
# including other agents run there.
detect_agent() {
  # claude code sets claude-code_2-1-309_agent: label the agent, not its version
  if [[ "${AI_AGENT:-}" =~ ^([^_]+)_[0-9][0-9.-]*_agent$ ]]; then echo "${BASH_REMATCH[1]}"
  elif [[ -n "${AI_AGENT:-}" ]]; then echo "$AI_AGENT"
  elif [[ -n "${CLAUDECODE:-}${CLAUDE_CODE:-}" ]]; then
    if [[ -n "${CLAUDE_CODE_IS_COWORK:-}" ]]; then echo "claude-cowork"; else echo "claude-code"; fi
  elif [[ -n "${CODEX_SANDBOX:-}${CODEX_CI:-}${CODEX_THREAD_ID:-}" ]]; then echo "codex"
  elif [[ -n "${GEMINI_CLI:-}" ]]; then echo "gemini-cli"
  elif [[ -n "${CURSOR_AGENT:-}" || "${CURSOR_EXTENSION_HOST_ROLE:-}" == "agent-exec" ]]; then echo "cursor-cli"
  elif [[ -n "${ANTIGRAVITY_AGENT:-}" ]]; then echo "antigravity"
  elif [[ -n "${AUGMENT_AGENT:-}" ]]; then echo "augment-cli"
  elif [[ -n "${OPENCODE_CLIENT:-}" ]]; then echo "opencode"
  elif [[ -n "${COPILOT_MODEL:-}${COPILOT_ALLOW_ALL:-}${COPILOT_GITHUB_TOKEN:-}" ]]; then echo "github-copilot"
  elif [[ -n "${REPL_ID:-}" ]]; then echo "replit"
  elif [[ -d /opt/.devin ]]; then echo "devin"
  elif [[ -n "${CURSOR_TRACE_ID:-}" ]]; then echo "cursor"
  fi
}
# lowercase, [a-z0-9._-] (anything else → "-"), trimmed, at most 40 chars.
sanitize_agent() {
  local v
  v=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9._-' '-')
  v="${v#-}"; v="${v:0:40}"; v="${v%-}"
  printf '%s' "$v"
}
AGENT_NAME=""
for candidate in "$CLIENT" "${HOST0_CLIENT:-}" "$(detect_agent)"; do
  [[ -n "$candidate" ]] || continue
  AGENT_NAME=$(sanitize_agent "$candidate")
  [[ -n "$AGENT_NAME" ]] && break
done
CLIENT_HEADER_VALUE="${AGENT_NAME:-unknown}/$PUBLISH_SH_VERSION"

# api key resolution: flag > env > credentials file
if [[ -z "$API_KEY" && -n "${HOST0_API_KEY:-}" ]]; then
  API_KEY="$HOST0_API_KEY"
  API_KEY_SOURCE="env"
fi
if [[ -z "$API_KEY" && -f "$CREDENTIALS_FILE" ]]; then
  API_KEY=$(tr -d '[:space:]' < "$CREDENTIALS_FILE")
  [[ -n "$API_KEY" ]] && API_KEY_SOURCE="credentials"
fi

# safety guard: never send the api key — or run a sign-in — against an
# arbitrary endpoint. this must run before any network request.
if [[ "$BASE_URL" != "$DEFAULT_BASE_URL" && "$ALLOW_NONHOST0_BASE_URL" -ne 1 ]]; then
  if [[ ( "$MODE" == "publish" || "$MODE" == "pull" ) && -n "$API_KEY" ]]; then
    die "refusing to send API key to non-default base URL; pass --allow-nonhost0-base-url to override"
  fi
  die "refusing to sign in against a non-default base URL; pass --allow-nonhost0-base-url to override"
fi

# die with the api's message (and any preflight problem lines) from a json
# error response.
check_api_error() {
  local resp="$1" ctx="$2"
  if ! echo "$resp" | jq -e . >/dev/null 2>&1; then
    die "$ctx: unexpected non-JSON response: $(echo "$resp" | head -c 300)"
  fi
  if echo "$resp" | jq -e 'type == "object" and has("error")' >/dev/null 2>&1; then
    local msg
    msg=$(echo "$resp" | jq -r '.message // .error')
    # `problems` comes in two shapes: objects with a .message (preflight_failed)
    # and plain strings (invalid_manifest, invalid_record). Handle both — under
    # `set -euo pipefail` a jq type error here would abort the script and
    # swallow the api's actionable message entirely, which is the opposite of
    # what a rejection is for.
    echo "$resp" | jq -r '
      (.problems // [])
      | if type == "array" then .[] else empty end
      | if type == "string" then . else (.message // tostring) end
      | "  - " + .' >&2 || true
    # a stored key that stopped working (revoked, or from another stack): a
    # publish only starts a device login when there is no key at all, so say
    # how to replace it rather than leave the agent looping on the 401.
    if [[ "$(echo "$resp" | jq -r '.error')" == "unauthorized" ]]; then
      local fix="publish.sh --login to sign in again (the new key replaces $CREDENTIALS_FILE once the user approves), then publish again."
      case "$API_KEY_SOURCE" in
        env)  fix="Unset HOST0_API_KEY, then run $fix" ;;
        flag) fix="Drop --api-key, then run $fix" ;;
        *)    fix="Run $fix" ;;
      esac
      echo "host0: the API key from $API_KEY_SOURCE was rejected — it may have been revoked. $fix" >&2
    fi
    # the machine code + (on a plan limit Pro lifts) where to upgrade, in the
    # key=value result contract — the agent tells the user which limit was
    # hit, offers the free fix first, and only then the link.
    echo "publish_result.error=$(echo "$resp" | jq -r '.error')" >&2
    local upgrade
    upgrade=$(echo "$resp" | jq -r '.upgrade_url // empty')
    if [[ -n "$upgrade" ]]; then echo "publish_result.upgrade_url=$upgrade" >&2; fi
    die "$ctx: $msg"
  fi
}

# ── device login ──
# the agent never handles the user's email or password: POST /auth/device
# returns a link + short code, the user approves it on host0 in their own
# browser, and a poll of /auth/device/token hands back the api key once.

DEV_DEVICE_CODE=""
DEV_USER_CODE=""
DEV_URI=""
DEV_URI_COMPLETE=""
DEV_INTERVAL=5
DEV_EXPIRES_AT=0

# load the saved login for this base url; returns 1 when there is none.
device_load() {
  [[ -f "$DEVICE_STATE_FILE" ]] || return 1
  local line
  line=$(jq -r --arg b "$BASE_URL" '
    select(.base_url == $b and (.device_code // "") != "")
    | [.device_code, .user_code, .verification_uri, .verification_uri_complete,
       (.interval // 5 | tostring), (.expires_at // 0 | tostring)] | @tsv
  ' "$DEVICE_STATE_FILE" 2>/dev/null || true)
  [[ -n "$line" ]] || return 1
  IFS=$'\t' read -r DEV_DEVICE_CODE DEV_USER_CODE DEV_URI DEV_URI_COMPLETE DEV_INTERVAL DEV_EXPIRES_AT <<< "$line"
  [[ "$DEV_INTERVAL" =~ ^[0-9]+$ && "$DEV_EXPIRES_AT" =~ ^[0-9]+$ ]] || return 1
  return 0
}

device_expired() { [[ $(date +%s) -ge $DEV_EXPIRES_AT ]]; }

device_clear() { rm -f "$DEVICE_STATE_FILE"; }

# the block the agent relays to the user (stderr; stdout stays empty).
device_print() {
  local left minutes next
  left=$(( DEV_EXPIRES_AT - $(date +%s) ))
  [[ $left -gt 0 ]] || left=0
  minutes=$(( (left + 59) / 60 ))
  if [[ "$MODE" == "publish" ]]; then
    next="then run this same command again — it waits up to ${LOGIN_WAIT_SECONDS}s for the approval and carries on."
  else
    next="then run publish.sh --login-wait — it waits up to ${LOGIN_WAIT_SECONDS}s for the approval and saves the key."
  fi
  {
    echo "host0: sign-in needed — approve this agent in your browser (no email or password is typed here)."
    echo ""
    echo "  Open:  $DEV_URI_COMPLETE"
    echo "  Code:  $DEV_USER_CODE   (the page shows the same code — check it matches)"
    echo "  Expires in $minutes minutes."
    echo ""
    echo "Next: show the link and code to the user, $next"
    echo ""
    echo "login_result.status=pending"
    echo "login_result.verification_url=$DEV_URI_COMPLETE"
    echo "login_result.user_code=$DEV_USER_CODE"
    echo "login_result.expires_in=$left"
  } >&2
}

# start a new login, save it, print the block, exit 3.
device_start() {  # device_start [note]
  local resp
  if [[ -n "${1:-}" ]]; then echo "$1" >&2; fi
  resp=$(net_curl once -sS -X POST "$BASE_URL/api/v1/auth/device" \
    -H "x-host0-client: $CLIENT_HEADER_VALUE" \
    -H "content-type: application/json" -d '{}')
  check_api_error "$resp" "start sign-in"
  DEV_DEVICE_CODE=$(echo "$resp" | jq -r '.device_code // empty')
  DEV_USER_CODE=$(echo "$resp" | jq -r '.user_code // empty')
  DEV_URI=$(echo "$resp" | jq -r '.verification_uri // empty')
  DEV_URI_COMPLETE=$(echo "$resp" | jq -r '.verification_uri_complete // empty')
  DEV_INTERVAL=$(echo "$resp" | jq -r '.interval // 5')
  DEV_EXPIRES_AT=$(( $(date +%s) + $(echo "$resp" | jq -r '.expires_in // 600') ))
  [[ -n "$DEV_DEVICE_CODE" && -n "$DEV_USER_CODE" ]] || die "start sign-in: unexpected response: $resp"

  # the device code (it redeems the key) goes to jq through the environment,
  # never its argv.
  ( umask 077
    mkdir -p "$(dirname "$DEVICE_STATE_FILE")"
    H0_DEVICE_CODE="$DEV_DEVICE_CODE" jq -n --arg b "$BASE_URL" --arg u "$DEV_USER_CODE" \
      --arg v "$DEV_URI" --arg c "$DEV_URI_COMPLETE" \
      --argjson i "$DEV_INTERVAL" --argjson e "$DEV_EXPIRES_AT" \
      '{base_url: $b, device_code: env.H0_DEVICE_CODE, user_code: $u, verification_uri: $v,
        verification_uri_complete: $c, interval: $i, expires_at: $e}' \
      > "$DEVICE_STATE_FILE"
    chmod 600 "$DEVICE_STATE_FILE" )
  device_print
  exit 3
}

save_api_key() {  # save_api_key <key> — atomic, 0600
  ( umask 077
    mkdir -p "$(dirname "$CREDENTIALS_FILE")"
    tmp=$(mktemp "$CREDENTIALS_FILE.XXXXXX")
    printf '%s' "$1" > "$tmp"
    chmod 600 "$tmp"
    mv -f "$tmp" "$CREDENTIALS_FILE" )
}

# poll until approved (key saved → returns 0), or exit: 3 still pending at the
# deadline, 1 denied, 3 with a fresh code when the old one expired. never
# prints the key.
device_wait() {
  local deadline now out rc status body err key email prefix
  deadline=$(( $(date +%s) + LOGIN_WAIT_SECONDS ))
  echo "Waiting for approval of code $DEV_USER_CODE (up to ${LOGIN_WAIT_SECONDS}s)…" >&2
  # the poll body carries the device code: a 0600 file, not an argv
  ( umask 077 && H0_DEVICE_CODE="$DEV_DEVICE_CODE" jq -n '{device_code: env.H0_DEVICE_CODE}' > "$DEVICE_BODY_FILE" )
  while :; do
    set +e
    out=$(net_curl idem -sS -X POST "$BASE_URL/api/v1/auth/device/token" \
      -H "x-host0-client: $CLIENT_HEADER_VALUE" \
      -H "content-type: application/json" \
      --data-binary "@$DEVICE_BODY_FILE" \
      -w '\n%{http_code}')
    rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "warning: could not reach $BASE_URL to check the sign-in — trying again." >&2
    else
      status="${out##*$'\n'}"
      body="${out%$'\n'*}"
      key=$(echo "$body" | jq -r '.api_key // empty' 2>/dev/null || true)
      err=$(echo "$body" | jq -r '.error // empty' 2>/dev/null || true)
      if [[ "$status" == "200" && -n "$key" ]]; then
        email=$(echo "$body" | jq -r '.email // empty')
        prefix=$(echo "$body" | jq -r '.key_prefix // empty')
        save_api_key "$key"
        device_clear
        API_KEY="$key"
        API_KEY_SOURCE="device"
        echo "Signed in as ${email:-your account} — API key saved to $CREDENTIALS_FILE." >&2
        echo "login_result.status=approved" >&2
        echo "login_result.email=$email" >&2
        echo "login_result.key_prefix=$prefix" >&2
        echo "login_result.credentials_file=$CREDENTIALS_FILE" >&2
        return 0
      fi
      case "$err" in
        authorization_pending) ;;
        slow_down)
          DEV_INTERVAL=$(echo "$body" | jq -r '.interval // empty')
          [[ "$DEV_INTERVAL" =~ ^[0-9]+$ ]] || DEV_INTERVAL=10
          ;;
        access_denied)
          device_clear
          echo "login_result.status=denied" >&2
          die "the sign-in was denied in the browser — run again to start a new one only if the user asks."
          ;;
        expired_token)
          device_clear
          device_start "The previous code expired — here is a new one."
          ;;
        invalid_device_code)
          device_clear
          device_start "The previous sign-in is no longer valid — here is a new one."
          ;;
        *)
          check_api_error "$body" "sign-in"
          die "sign-in: unexpected response (HTTP $status): $(echo "$body" | head -c 300)"
          ;;
      esac
    fi
    now=$(date +%s)
    if [[ $(( now + DEV_INTERVAL )) -gt $deadline ]]; then
      device_print
      exit 3
    fi
    sleep "$DEV_INTERVAL"
  done
}

case "$MODE" in
  login)
    # re-show a login that's still pending for this base url rather than
    # minting a second code the user might confuse with the first.
    if device_load && ! device_expired; then
      device_print
      exit 3
    fi
    device_start
    ;;
  login-wait)
    device_load || die "no sign-in in progress — run publish.sh --login first"
    if device_expired; then
      device_clear
      device_start "The previous code expired — here is a new one."
    fi
    device_wait
    exit 0
    ;;
  publish|pull)
    if [[ -z "$API_KEY" ]]; then
      if [[ "$NO_LOGIN" -eq 1 ]]; then
        die "no API key found (--no-login). Run publish.sh --login to sign in — the user approves a link + code in their browser, nothing personal is typed here — or pass --api-key / set HOST0_API_KEY."
      fi
      if device_load; then
        if device_expired; then
          device_clear
          device_start "the previous code expired — here is a new one."
        fi
        device_wait
      else
        device_start
      fi
    fi
    write_auth_config
    ;;
esac

# single-file mode keeps its state next to the file, keyed by the file name
# (STATE_SOURCE), so two files published from one folder stay two apps. a
# directory's entries carry source "." (legacy entries have none = ".").
if [[ "$MODE" == "pull" ]]; then
  STATE_DIR=""  # pull writes its own state file (below)
elif [[ "$TARGET_KIND" == "dir" ]]; then
  TARGET_ABS=$(cd "$TARGET" && pwd)
  STATE_DIR="$TARGET_ABS/.host0"
  STATE_SOURCE="."
  DEFAULT_NAME=$(basename "$TARGET_ABS")
else
  TARGET_FILE_ABS="$(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")"
  STATE_DIR="$(dirname "$TARGET_FILE_ABS")/.host0"
  STATE_SOURCE=$(basename "$TARGET_FILE_ABS")
  DEFAULT_NAME="${STATE_SOURCE%.*}"
  [[ -n "$DEFAULT_NAME" ]] || DEFAULT_NAME="$STATE_SOURCE"
fi
STATE_FILE="$STATE_DIR/state.json"

# probe request whose http status matters (state-file resolution). sets the
# globals API_BODY / API_HTTP_STATUS instead of echoing, because a command
# substitution would run in a subshell and lose the status.
API_BODY=""
API_HTTP_STATUS=""
api_probe() {
  local method="$1" path="$2" out rc
  set +e
  out=$(net_curl idem -s -X "$method" "$BASE_URL$path" \
    -K "$AUTH_CFG" \
    -H "x-host0-client: $CLIENT_HEADER_VALUE" \
    -w '\n%{http_code}')
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    API_BODY=""
    API_HTTP_STATUS="000"
    return 0
  fi
  API_HTTP_STATUS="${out##*$'\n'}"
  API_BODY="${out%$'\n'*}"
}

# POST creates things (an app, a deployment), so it only retries failures that
# provably never reached the server; everything else is safe to repeat.
api() {
  local method="$1" path="$2" body="${3:-}" mode="idem"
  [[ "$method" == "POST" ]] && mode="once"
  if [[ -n "$body" ]]; then
    net_curl "$mode" -sS -X "$method" "$BASE_URL$path" \
      -K "$AUTH_CFG" \
      -H "x-host0-client: $CLIENT_HEADER_VALUE" \
      -H "content-type: application/json" \
      -d "$body"
  else
    net_curl "$mode" -sS -X "$method" "$BASE_URL$path" \
      -K "$AUTH_CFG" \
      -H "x-host0-client: $CLIENT_HEADER_VALUE"
  fi
}

compute_sha256() {
  local f="$1"
  if [[ "$SHA_TOOL" == "shasum" ]]; then
    shasum -a 256 "$f" | cut -d' ' -f1
  else
    sha256sum "$f" | cut -d' ' -f1
  fi
}

# a path from the api that --pull may write under its folder: relative, no
# empty / "." / ".." segment (backslashes count as separators), and not in
# .host0/ — where the state file lives — in any letter case (macOS and
# Windows filesystems fold case). mirrors isSafeRelativePath in
# packages/cli/src/commands/pull.ts.
pull_path_ok() {  # pull_path_ok <path> → 0 when safe
  local n first
  [[ -n "$1" ]] || return 1
  n="/${1//\\//}/"
  case "$n" in
    *//*|*/./*|*/../*) return 1 ;;
  esac
  first="${n#/}"
  first="${first%%/*}"
  [[ "$(printf '%s' "$first" | tr '[:upper:]' '[:lower:]')" != ".host0" ]]
}

# no existing component of <dir>/<path> below <dir> is a symlink, so a write
# can't be redirected out of the folder.
pull_no_symlinks() {  # pull_no_symlinks <dir> <path> → 0 when clean
  local cur="$1" rest="$2" part
  while [[ -n "$rest" ]]; do
    part="${rest%%/*}"
    if [[ "$rest" == */* ]]; then rest="${rest#*/}"; else rest=""; fi
    cur="$cur/$part"
    [[ -L "$cur" ]] && return 1
  done
  return 0
}

# ── pull: the live version of an app into a folder ──
# for updating an app from a new chat (no local copy): download every live
# file, record the app in <dir>/.host0/state.json, and the next publish of
# <dir> becomes the app's next version. h0.json comes along, so shared data
# keeps its collections.
if [[ "$MODE" == "pull" ]]; then
  APP_REF="${SLUG:-$APP_ID}"
  [[ -n "$APP_REF" ]] || die "--pull needs --slug <slug> (or --app-id <uuid>) — the app to download"
  echo "Listing the live files of $APP_REF..." >&2
  FILES_RESP=$(api GET "/api/v1/apps/$APP_REF/files")
  check_api_error "$FILES_RESP" "list files"
  APP_ID=$(echo "$FILES_RESP" | jq -r '.app_id')
  APP_SLUG=$(echo "$FILES_RESP" | jq -r '.slug')
  LIVE_URL=$(echo "$FILES_RESP" | jq -r '.url')
  LIVE_VERSION=$(echo "$FILES_RESP" | jq -r '.version // empty')
  DEST="${TARGET:-$APP_SLUG}"
  if [[ -e "$DEST" && ! -d "$DEST" ]]; then
    die "$DEST is a file — pass an empty or new folder to pull into"
  fi
  if [[ -d "$DEST" ]] && [[ -n "$(ls -A "$DEST" | grep -v '^\.host0$' || true)" ]]; then
    die "$DEST isn't empty — pull into a new folder (e.g. publish.sh --pull --slug $APP_SLUG ./$APP_SLUG-live) so nothing local is overwritten"
  fi
  FILE_ROWS=$(echo "$FILES_RESP" | jq -r '.files[] | [.path, .download_url, (.sha256 // "")] | @tsv')
  # check every path before anything is written (as the CLI does)
  if [[ -n "$FILE_ROWS" ]]; then
    while IFS=$'\t' read -r fpath furl fsha; do
      # %b undoes @tsv's escapes (a backslash comes through doubled)
      pull_path_ok "$fpath" || die "refusing an unsafe path from the api: $(printf '%b' "$fpath")"
    done <<< "$FILE_ROWS"
  fi
  mkdir -p "$DEST"
  DEST_ABS=$(cd "$DEST" && pwd)
  # a .host0 that is a symlink (or a file) would send the state file elsewhere
  if [[ -L "$DEST_ABS/.host0" ]] || { [[ -e "$DEST_ABS/.host0" ]] && [[ ! -d "$DEST_ABS/.host0" ]]; }; then
    die "$DEST_ABS/.host0 isn't a plain folder — remove it, or pull into a new folder"
  fi
  COUNT=0
  while IFS=$'\t' read -r fpath furl fsha; do
    [[ -n "$fpath" ]] || continue
    pull_no_symlinks "$DEST_ABS" "$fpath" || die "refusing to write $fpath through a symlink in $DEST_ABS"
    mkdir -p "$DEST_ABS/$(dirname "$fpath")"
    # the bearer key goes to the api base url only — signed data-plane urls
    # carry their own authorization.
    if [[ "$furl" == "$BASE_URL/"* ]]; then
      net_curl idem -sS -f -o "$DEST_ABS/$fpath" "$furl" \
        -K "$AUTH_CFG" \
        -H "x-host0-client: $CLIENT_HEADER_VALUE" >/dev/null || die "could not download $fpath"
    else
      net_curl idem -sS -f -o "$DEST_ABS/$fpath" "$furl" >/dev/null || die "could not download $fpath"
    fi
    if [[ -n "$fsha" && "$fsha" != "null" ]]; then
      got=$(compute_sha256 "$DEST_ABS/$fpath")
      [[ "$got" == "$fsha" ]] || die "$fpath downloaded with the wrong hash ($got, expected $fsha) — run --pull again"
    fi
    COUNT=$((COUNT + 1))
  done <<< "$FILE_ROWS"

  # the same state entry a publish of DEST writes, so the next publish of the
  # folder updates this app instead of creating one.
  mkdir -p "$DEST_ABS/.host0"
  PULL_STATE_FILE="$DEST_ABS/.host0/state.json"
  [[ ! -L "$PULL_STATE_FILE" ]] || die "$PULL_STATE_FILE is a symlink — remove it, or pull into a new folder"
  if [[ -f "$PULL_STATE_FILE" ]]; then STATE=$(cat "$PULL_STATE_FILE"); else STATE='{"apps":{}}'; fi
  entry=$(jq -n --arg a "$APP_ID" --arg s "$APP_SLUG" --arg u "$LIVE_URL" \
    --arg b "$BASE_URL" --arg t "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{app_id: $a, slug: $s, url: $u, base_url: $b, source: ".", updated_at: $t}')
  STATE=$(echo "$STATE" | jq --arg k "$APP_SLUG" --arg a "$APP_ID" --argjson e "$entry" \
    '.apps = ((.apps // {}) | with_entries(select(.value.app_id != $a))) | .apps[$k] = $e')
  echo "$STATE" | jq '.' > "$PULL_STATE_FILE"

  # stdout: the folder, nothing else
  echo "$DEST_ABS"
  echo "" >&2
  echo "pull_result.dir=$DEST_ABS" >&2
  echo "pull_result.app_id=$APP_ID" >&2
  echo "pull_result.slug=$APP_SLUG" >&2
  echo "pull_result.url=$LIVE_URL" >&2
  echo "pull_result.version=$LIVE_VERSION" >&2
  echo "pull_result.files=$COUNT" >&2
  exit 0
fi

# extension → content-type map (mirrors src/lib/hosting/validate.ts)
guess_content_type() {
  local f="$1" ext
  ext=$(echo "${f##*.}" | tr '[:upper:]' '[:lower:]')
  case "$ext" in
    html|htm)    echo "text/html; charset=utf-8" ;;
    css)         echo "text/css; charset=utf-8" ;;
    js|mjs)      echo "text/javascript; charset=utf-8" ;;
    json|map)    echo "application/json" ;;
    svg)         echo "image/svg+xml" ;;
    png)         echo "image/png" ;;
    jpg|jpeg)    echo "image/jpeg" ;;
    gif)         echo "image/gif" ;;
    webp)        echo "image/webp" ;;
    ico)         echo "image/x-icon" ;;
    txt|md|markdown) echo "text/plain; charset=utf-8" ;;
    xml)         echo "application/xml" ;;
    woff)        echo "font/woff" ;;
    woff2)       echo "font/woff2" ;;
    wasm)        echo "application/wasm" ;;
    webmanifest) echo "application/manifest+json" ;;
    pdf)         echo "application/pdf" ;;
    avif)        echo "image/avif" ;;
    mp4)         echo "video/mp4" ;;
    webm)        echo "video/webm" ;;
    mp3)         echo "audio/mpeg" ;;
    csv)         echo "text/csv; charset=utf-8" ;;
    *)           echo "application/octet-stream" ;;
  esac
}

# walk the directory: skip .DS_Store, .host0/, and anything inside a hidden
# directory (.git/, .cache/, …)
MANIFEST_JSON="[]"
FILE_MAP="{}"
add_file() {  # add_file <manifest path> <absolute local path>
  local rel="$1" f="$2" sz ct h
  sz=$(wc -c < "$f" | tr -d ' ')
  ct=$(guess_content_type "$f")
  h=$(compute_sha256 "$f")
  MANIFEST_JSON=$(echo "$MANIFEST_JSON" | jq --arg p "$rel" --argjson s "$sz" --arg c "$ct" --arg h "$h" \
    '. + [{"path":$p,"size":$s,"content_type":$c,"sha256":$h}]')
  FILE_MAP=$(echo "$FILE_MAP" | jq --arg p "$rel" --arg a "$f" '. + {($p):$a}')
}
if [[ "$TARGET_KIND" == "file" ]]; then
  # one file, at the root of the deploy under its own name — the server
  # answers / with it (single-file rule) and /<name> as well.
  add_file "$STATE_SOURCE" "$TARGET_FILE_ABS"
fi
while [[ "$TARGET_KIND" == "dir" ]] && IFS= read -r -d '' f; do
  rel="${f#"$TARGET_ABS"/}"
  [[ "$(basename "$rel")" == ".DS_Store" ]] && continue
  [[ "$rel" =~ (^|/)\.[^/]+/ ]] && continue
  add_file "$rel" "$f"
done < <([[ "$TARGET_KIND" == "dir" ]] && find "$TARGET_ABS" -type f -print0 | sort -z)

FILES_TOTAL=$(echo "$MANIFEST_JSON" | jq 'length')
[[ "$FILES_TOTAL" -gt 0 ]] || die "no files found in $TARGET (resolved from $(pwd)) — pass the folder that contains index.html, or a single file"

# resolve the app: --app-id > --slug > state file (this base url, newest
# first) > create
ACTION="update"
APP_SLUG=""
APP_VISIBILITY=""
# cached state entries found unusable with the active key; pruned on save.
STALE_SLUGS=()

if [[ -n "$APP_ID" ]]; then
  RESP=$(api GET "/api/v1/apps/$APP_ID")
  check_api_error "$RESP" "app lookup"
  APP_SLUG=$(echo "$RESP" | jq -r '.slug')
  APP_VISIBILITY=$(echo "$RESP" | jq -r '.visibility')
elif [[ -n "$SLUG" ]]; then
  RESP=$(api GET "/api/v1/apps")
  check_api_error "$RESP" "app lookup"
  APP_ID=$(echo "$RESP" | jq -r --arg s "$SLUG" '.apps[] | select(.slug == $s) | .app_id' | head -n 1)
  [[ -n "$APP_ID" ]] || die "no app with slug '$SLUG' in this account — drop --slug to create a new app, or list yours with: curl -sS $BASE_URL/api/v1/apps -H 'authorization: bearer …'"
  APP_SLUG="$SLUG"
  APP_VISIBILITY=$(echo "$RESP" | jq -r --arg s "$SLUG" '.apps[] | select(.slug == $s) | .visibility' | head -n 1)
else
  if [[ -f "$STATE_FILE" ]]; then
    # candidates = entries written against this base url (legacy entries have
    # no base_url and are accepted), most recently published first. never
    # "the first entry": one directory can accumulate several, and after an
    # accidental create the newest one is the app to keep updating.
    CANDIDATES=$(jq -r --arg b "$BASE_URL" --arg src "$STATE_SOURCE" '
      [ (.apps // {}) | to_entries[]
        | select((.value.base_url // $b) == $b)
        | select((.value.source // ".") == $src)
        | {slug: .key, app_id: (.value.app_id // ""), updated_at: (.value.updated_at // "")}
        | select(.app_id != "") ]
      | sort_by(.updated_at) | reverse
      | .[] | "\(.app_id)\t\(.slug)"
    ' "$STATE_FILE" 2>/dev/null || true)

    while IFS=$'\t' read -r cand_id cand_slug; do
      [[ -n "$cand_id" ]] || continue
      api_probe GET "/api/v1/apps/$cand_id"
      if [[ "$API_HTTP_STATUS" == "200" ]] &&
         echo "$API_BODY" | jq -e 'type == "object" and has("error") | not' >/dev/null 2>&1; then
        APP_ID="$cand_id"
        APP_SLUG=$(echo "$API_BODY" | jq -r '.slug')
        APP_VISIBILITY=$(echo "$API_BODY" | jq -r '.visibility')
        break
      fi
      case "$API_HTTP_STATUS" in
        401|403|404|410)
          # deleted, or written by a different account's key — drop it rather
          # than let it shadow a usable entry on every future run.
          echo "warning: cached app \"$cand_slug\" ($cand_id) is not available to this API key (HTTP $API_HTTP_STATUS) — dropping it from $STATE_FILE" >&2
          STALE_SLUGS+=("$cand_slug")
          ;;
        *)
          # a transient failure must not turn into a duplicate app.
          die "app lookup for cached app \"$cand_slug\" failed (HTTP $API_HTTP_STATUS) — not creating a duplicate; retry, or name the app explicitly with --slug/--app-id"
          ;;
      esac
    done <<< "$CANDIDATES"
  fi
  if [[ -z "$APP_ID" ]]; then
    if [[ ${#STALE_SLUGS[@]} -gt 0 ]]; then
      echo "warning: no app cached in $STATE_FILE is usable with this API key — creating a new app. If you meant to update an existing one, stop and re-run with --slug <slug>." >&2
    fi
    ACTION="create"
    APP_NAME="${NAME:-$DEFAULT_NAME}"
    echo "Creating app \"$APP_NAME\"..." >&2
    BODY=$(jq -n --arg n "$APP_NAME" '{name: $n}')
    RESP=$(api POST "/api/v1/apps" "$BODY")
    check_api_error "$RESP" "create app"
    APP_ID=$(echo "$RESP" | jq -r '.app_id')
    APP_SLUG=$(echo "$RESP" | jq -r '.slug')
    APP_VISIBILITY=$(echo "$RESP" | jq -r '.visibility')
    [[ "$APP_ID" != "null" && -n "$APP_ID" ]] || die "create app: unexpected response: $RESP"
    # from here on this run owns the app: if anything below fails before the
    # app goes live, the cleanup trap deletes it again.
    CREATED_APP_ID="$APP_ID"
    CREATED_APP_SLUG="$APP_SLUG"
  fi
fi

# step 1: start the deployment from the manifest
echo "Creating deployment ($FILES_TOTAL files)..." >&2
# the version's note rides along only when given (the api trims it and
# rejects > 200 characters with bad_request).
if [[ -n "$MESSAGE" ]]; then
  BODY=$(echo "$MANIFEST_JSON" | jq --arg m "$MESSAGE" '{files: ., message: $m}')
else
  BODY=$(echo "$MANIFEST_JSON" | jq '{files: .}')
fi
DEPLOY_RESP=$(api POST "/api/v1/apps/$APP_ID/deployments" "$BODY")
check_api_error "$DEPLOY_RESP" "create deployment"

DEPLOYMENT_ID=$(echo "$DEPLOY_RESP" | jq -r '.deployment_id')
FINALIZE_URL=$(echo "$DEPLOY_RESP" | jq -r '.upload.finalize_url')
TARGET_COUNT=$(echo "$DEPLOY_RESP" | jq '.upload.targets | length')
SKIPPED_COUNT=$(echo "$DEPLOY_RESP" | jq '.upload.skipped | length')
[[ "$DEPLOYMENT_ID" != "null" && -n "$DEPLOYMENT_ID" ]] || die "create deployment: unexpected response: $DEPLOY_RESP"

# scheme://host[:port] of a url — everything before the first path segment.
url_origin() {
  local u="$1" rest
  rest="${u#*://}"
  echo "${u%%://*}://${rest%%/*}"
}

# the server mints its api urls (finalize, and control-plane upload targets under
# /api/) from its own configured origin. if that origin isn't the one we're
# publishing to, stop here: the bearer key must never be sent to a host the
# caller didn't name, and continuing would fail later with a misleading auth
# error. upload targets on the data plane (signed /.h0/upload/ urls) live on
# another origin by design and never receive the key.
BASE_ORIGIN=$(url_origin "$BASE_URL")
while IFS= read -r mint_url; do
  [[ -n "$mint_url" ]] || continue
  mint_origin=$(url_origin "$mint_url")
  if [[ "$mint_origin" != "$BASE_ORIGIN" ]]; then
    die "upload targets are on $mint_origin but --base-url is $BASE_ORIGIN — the server mints these URLs from its configured platform origin. Re-run with --base-url $mint_origin (or set H0_PLATFORM_ORIGIN on the server to match)."
  fi
done < <(echo "$DEPLOY_RESP" | jq -r '[((.upload.targets // [])[].url | select(test("^[a-z]+://[^/]+/api/"))), .upload.finalize_url] | .[] | select(. != null and . != "")')

# step 2: upload each target (unchanged files were hash-skipped server-side)
if [[ "$SKIPPED_COUNT" -gt 0 ]]; then
  echo "Uploading $TARGET_COUNT files ($SKIPPED_COUNT unchanged, skipped)..." >&2
else
  echo "Uploading $TARGET_COUNT files..." >&2
fi

i=0
while [[ $i -lt $TARGET_COUNT ]]; do
  t_path=$(echo "$DEPLOY_RESP" | jq -r ".upload.targets[$i].path")
  t_url=$(echo "$DEPLOY_RESP" | jq -r ".upload.targets[$i].url")
  local_file=$(echo "$FILE_MAP" | jq -r --arg p "$t_path" '.[$p] // empty')
  [[ -n "$local_file" && -f "$local_file" ]] || die "missing local file for upload target: $t_path"

  header_args=()
  while IFS= read -r hline; do
    [[ -n "$hline" ]] && header_args+=(-H "$hline")
  done < <(echo "$DEPLOY_RESP" | jq -r ".upload.targets[$i].headers // {} | to_entries[] | \"\(.key): \(.value)\"")

  # send the bearer key only to our own api, never to a foreign upload host
  # (forward-compatible with presigned storage urls)
  # (exact origin match, not a prefix: http://localhost:3000.evil.com must not match)
  if [[ "$(url_origin "$t_url")" == "$BASE_ORIGIN" ]]; then
    header_args+=(-K "$AUTH_CFG")
  fi

  PUT_RESP=$(net_curl idem -sS -X PUT "$t_url" \
    "${header_args[@]+"${header_args[@]}"}" \
    --data-binary "@$local_file")
  check_api_error "$PUT_RESP" "upload $t_path"
  i=$((i + 1))
done

# step 3: finalize — the app isn't live until this succeeds
echo "Finalizing..." >&2
# retried like an idempotent call: if a retry lands after an attempt that did
# go through, the api answers not_pending — then the deployment's own status
# says whether it is live, and that is the answer.
FIN_RESP=$(net_curl idem -sS -X POST "$FINALIZE_URL" \
  -K "$AUTH_CFG" \
  -H "x-host0-client: $CLIENT_HEADER_VALUE" \
  -H "content-type: application/json" \
  -d '{}')
if [[ "$(echo "$FIN_RESP" | jq -r '.error // empty' 2>/dev/null || true)" == "not_pending" ]]; then
  STATUS_RESP=$(api GET "/api/v1/deployments/$DEPLOYMENT_ID")
  if [[ "$(echo "$STATUS_RESP" | jq -r '.live // false' 2>/dev/null || true)" == "true" ]]; then
    FIN_RESP="$STATUS_RESP"
  fi
fi
check_api_error "$FIN_RESP" "finalize"
LIVE_URL=$(echo "$FIN_RESP" | jq -r '.url')
[[ "$LIVE_URL" != "null" && -n "$LIVE_URL" ]] || die "finalize: unexpected response: $FIN_RESP"
# the version this publish went live as, and the one it replaced (empty on the
# first; also empty when a retried finalize was answered by the status call).
LIVE_VERSION=$(echo "$FIN_RESP" | jq -r '.version // empty' 2>/dev/null || true)
PREVIOUS_VERSION=$(echo "$FIN_RESP" | jq -r '.previous_version // empty' 2>/dev/null || true)

# the app is live — it is no longer a cleanup candidate. a failure in the
# steps below (state file, visibility) must never delete a live app.
CREATED_APP_ID=""

# save state (internal cache — never source of truth) before the optional
# visibility change: if that PATCH fails (e.g. public_app_limit_reached), the
# next run must still update this app rather than create a duplicate.
mkdir -p "$STATE_DIR"
if [[ -f "$STATE_FILE" ]]; then
  STATE=$(cat "$STATE_FILE")
else
  STATE='{"apps":{}}'
fi
for stale in ${STALE_SLUGS[@]+"${STALE_SLUGS[@]}"}; do
  STATE=$(echo "$STATE" | jq --arg k "$stale" 'del(.apps[$k])')
done
# base_url + updated_at are what make resolution unambiguous on the next run.
entry=$(jq -n --arg a "$APP_ID" --arg s "$APP_SLUG" --arg u "$LIVE_URL" \
  --arg b "$BASE_URL" --arg t "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg src "$STATE_SOURCE" \
  '{app_id: $a, slug: $s, url: $u, base_url: $b, source: $src, updated_at: $t}')
# entries are keyed by slug: an app renamed since the last run (dashboard,
# PATCH, or mcp rename_app) leaves its old key behind — drop every other
# entry for this app_id so the cache holds one entry per app.
STATE=$(echo "$STATE" | jq --arg k "$APP_SLUG" --arg a "$APP_ID" --argjson e "$entry" \
  '.apps = ((.apps // {}) | with_entries(select(.value.app_id != $a))) | .apps[$k] = $e')
echo "$STATE" | jq '.' > "$STATE_FILE"

# optional: set visibility
if [[ -n "$VISIBILITY" ]]; then
  echo "Setting visibility to $VISIBILITY..." >&2
  BODY=$(jq -n --arg v "$VISIBILITY" '{visibility: $v}')
  VIS_RESP=$(api PATCH "/api/v1/apps/$APP_ID" "$BODY")
  check_api_error "$VIS_RESP" "set visibility"
  APP_VISIBILITY=$(echo "$VIS_RESP" | jq -r '.visibility')
fi

# stdout: the live url, nothing else
echo "$LIVE_URL"

# stderr: machine-readable result contract
echo "" >&2
echo "publish_result.url=$LIVE_URL" >&2
echo "publish_result.app_id=$APP_ID" >&2
echo "publish_result.slug=$APP_SLUG" >&2
echo "publish_result.action=$ACTION" >&2
echo "publish_result.deployment_id=$DEPLOYMENT_ID" >&2
echo "publish_result.version=$LIVE_VERSION" >&2
echo "publish_result.previous_version=$PREVIOUS_VERSION" >&2
echo "publish_result.visibility=$APP_VISIBILITY" >&2
echo "publish_result.api_key_source=$API_KEY_SOURCE" >&2
echo "publish_result.files_total=$FILES_TOTAL" >&2
echo "publish_result.files_uploaded=$TARGET_COUNT" >&2
echo "publish_result.files_skipped=$SKIPPED_COUNT" >&2
echo "publish_result.state_pruned=${#STALE_SLUGS[@]}" >&2
