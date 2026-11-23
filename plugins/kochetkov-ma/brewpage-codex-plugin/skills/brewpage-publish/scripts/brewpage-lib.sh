#!/usr/bin/env bash
# Sourced (!=executed) by scripts/brewpage-run.sh, the skill's only entry: sets HISTORY_FILE + helpers.
# Keeps token history at the workspace root and validates query parameters.

BP_ROOT="$PWD"
HISTORY_FILE="$BP_ROOT/brewpage-history.md"
# Run dirs stay outside the workspace; only brewpage-run.sh writes into them.
BP_TMPDIR="${TMPDIR:-/tmp}"
BP_TMPDIR="${BP_TMPDIR%/}"
# User-Agent on every brewpage.app request: <client>/<shipped version> (+https://brewpage.app).
BP_UA="brewpage-codex/0.2.2 (+https://brewpage.app)"

bp_history() {
  local operation="$1"
  shift
  python3 "$(dirname "${BASH_SOURCE[0]}")/history.py" "$operation" "$BP_ROOT" "${HISTORY_FILE#"$BP_ROOT/"}" "$@"
}

# Creates the history file if absent, keeps it mode 600, and makes sure git
# never picks it up — the skill used to only *ask* the user to keep it private.
bp_history_init() {
  command -v python3 >/dev/null || { echo 'FAILED: python3 required for secure history'; return 1; }
  bp_history init <<'HEADER'
# brewpage.app — Published Pages

> Owner tokens authorize in-place updates and deletion. Keep this file and its management links private.
> Use `brewpage-run.sh update` with the saved target or a protected proof file. A 409 OLD_PUBLICATION_READ_ONLY needs an explicit replacement decision before a new create.

| Date | URL | Owner Token | TTL | Type | Owner API | Identity |
|------|-----|-------------|-----|------|-----------|----------|
HEADER
}

# shellcheck disable=SC2016 # backticks = literal markdown code spans
bp_history_append() {
  if [ "$#" -ge 5 ]; then
    printf '| %s | [%s](%s) | `%s` | %sd | %s | %s | `%s` |\n' \
      "$(date -u '+%Y-%m-%d %H:%M')" "$1" "$1" "$2" "$3" "$4" "$5" "${6:-}" | bp_history append ${BP_VERIFY_RECEIPT:+verify-owner}
  else
    printf '| %s | [%s](%s) | `%s` | %sd | %s |\n' \
      "$(date -u '+%Y-%m-%d %H:%M')" "$1" "$1" "$2" "$3" "$4" | bp_history append ${BP_VERIFY_RECEIPT:+verify-owner}
  fi
}

# BD02: ns/ttl/entry arrive as single-quoted literals; re-checked here as data before the URL.
# Explicit char lists, never a-z ranges: bash 3.2 en_US.UTF-8 collation lets [a-z] match A-Z and accents.
bp_validate() {
  local ns="$1" days="$2" entry="$3"
  case "$ns" in
    *[!abcdefghijklmnopqrstuvwxyz0123456789-]* | '') echo "FAILED: namespace must be 1-32 chars of a-z0-9-"; return 1 ;;
  esac
  [ "${#ns}" -ge 1 ] && [ "${#ns}" -le 32 ] || { echo "FAILED: namespace must be 1-32 chars"; return 1; }
  case "$days" in
    '' | *[!0123456789]*) echo "FAILED: ttl must be a positive integer"; return 1 ;;
  esac
  [ "$days" -ge 1 ] || { echo "FAILED: ttl must be >= 1"; return 1; }
  if [ -n "$entry" ]; then
    case "$entry" in
      *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._/-]* | */../* | ../* | */..) echo "FAILED: entry must be a plain relative file name"; return 1 ;;
    esac
  fi
  return 0
}

# rc 0: path ends in .html/.htm, any case; such a file is always published as a page.
bp_is_html_path() {
  case "${1:-}" in *.[Hh][Tt][Mm] | *.[Hh][Tt][Mm][Ll]) return 0 ;; *) return 1 ;; esac
}

# rc 0: path ends in .md/.markdown, any case; rendered through /api/html, never a raw download.
bp_is_markdown_path() {
  case "${1:-}" in *.[Mm][Dd] | *.[Mm][Aa][Rr][Kk][Dd][Oo][Ww][Nn]) return 0 ;; *) return 1 ;; esac
}

# rc 0: file holds a whole HTML document: doctype or <html> first, after an optional BOM and whitespace.
bp_is_html_document() {
  python3 -c 'import re,sys; sys.exit(0 if re.match(rb"(?:\xef\xbb\xbf)?\s*<(?:!doctype\s+html|html)(?=[\s>])", open(sys.argv[1],"rb").read(), re.I) else 1)' "$1"
}

# rc 0: file decodes as UTF-8; jq --rawfile would silently replace any other bytes.
bp_is_utf8() {
  python3 -c 'import sys; open(sys.argv[1],"rb").read().decode("utf-8")' "$1" 2>/dev/null
}

# Allocate before writing inputs; only the generated ASCII basename is substituted into blocks.
bp_prepare() {
  mkdir -p "$BP_TMPDIR" || return 1
  (umask 077; mktemp -d "$BP_TMPDIR/brewpage.XXXXXX")
}

bp_run_dir() {
  local id="${1:-}"
  case "$id" in
    brewpage.??????) : ;;
    *) echo "FAILED: invalid publish run id"; return 1 ;;
  esac
  case "$id" in *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.]*) echo "FAILED: invalid publish run id"; return 1 ;; esac
  BP_RUN_DIR="$BP_TMPDIR/$id"
  [ -d "$BP_RUN_DIR" ] && [ ! -L "$BP_RUN_DIR" ] && [ -O "$BP_RUN_DIR" ] &&
    [ -n "$(find "$BP_RUN_DIR" -maxdepth 0 -type d -perm 0700 -print)" ] || {
      echo "FAILED: publish run directory must be owned, private and non-symlink"; return 1;
    }
}

bp_cleanup() {
  [ -n "${BP_RUN_DIR:-}" ] || return 0
  bp_run_dir "${BP_RUN_DIR##*/}" || return 1
  rm -rf -- "$BP_RUN_DIR"
}

# Removes a dir this call just made via bp_prepare, even one bp_run_dir rejects (bp_cleanup refuses it).
bp_discard() {
  case "${1:-}" in "$BP_TMPDIR"/brewpage.??????) rm -rf -- "$1" ;; esac
}

# jq: X-Password header line from $password; error() on <4 chars or a control char (header injection).
# shellcheck disable=SC2016 # $password/$p are jq variables
BP_PW_FILTER='($password | rtrimstr("\n")) as $p |
  if ($p | length) >= 4 and ($p | explode | all(. >= 32 and . != 127))
  then "X-Password: " + $p else error("invalid password") end'

# {password_file} slot: absolute path to a readable non-symlink regular file with a valid password.
bp_password_check() {
  case "${1:-}" in /*) : ;; *) echo "FAILED: password file must be an absolute path"; return 1 ;; esac
  [ -f "$1" ] && [ ! -L "$1" ] || { echo "FAILED: password source must be a non-symlink regular file"; return 1; }
  [ -r "$1" ] || { echo "FAILED: password file is not readable"; return 1; }
  command -v jq >/dev/null || { echo "FAILED: jq required"; return 1; }
  jq -ner --rawfile password "$1" "$BP_PW_FILTER" >/dev/null 2>&1 ||
    { echo "FAILED: password must have at least 4 characters and no control characters"; return 1; }
}

# Prelude: explicit run id/password policy, no implicit shared credential discovery.
bp_begin() {
  NS="$1"; DAYS="$2"; ENTRY="$3"
  bp_run_dir "${4:-}" || return 1
  trap bp_cleanup EXIT
  trap 'exit 1' HUP INT TERM
  bp_validate "$NS" "$DAYS" "$ENTRY" || return 1
  BP_DELIVERY_MODE="${6:-}"
  case "$BP_DELIVERY_MODE" in ''|path|subdomain) : ;; *) echo "FAILED: delivery mode must be path or subdomain"; return 1 ;; esac
  case "${5:-}" in none|file) BP_PASSWORD_MODE="$5" ;; *) echo "FAILED: explicit password mode required"; return 1 ;; esac
  if [ "${BP_NO_SAVE:-0}" = 0 ]; then
    bp_history_init || { echo "FAILED: cannot initialize history file"; return 1; }
  fi
  command -v jq >/dev/null || { echo "FAILED: jq required"; return 1; }
  BP_HEADER_FILE=""
  if [ "$BP_PASSWORD_MODE" = file ]; then
    local source_file="$BP_RUN_DIR/brewpage-password-source.txt" password_source=""
    [ -f "$source_file" ] && [ ! -L "$source_file" ] || { echo "FAILED: password source path file missing or unsafe"; return 1; }
    IFS= read -r password_source < "$source_file" || true
    bp_password_check "$password_source" || return 1
    # Page access password the owner chose for this publication (X-Password); no system or account credential.
    local password_file="$BP_RUN_DIR/page-password-copy.txt"
    [ ! -e "$password_file" ] && [ ! -L "$password_file" ] || { echo "FAILED: page password copy already exists"; return 1; }
    (umask 077; cat -- "$password_source" > "$password_file") || return 1
    BP_HEADER_FILE="$BP_RUN_DIR/password-header.txt"
    # Re-checks the copied bytes: the source may change after bp_password_check.
    (umask 077; jq -ner --rawfile password "$password_file" "$BP_PW_FILTER" > "$BP_HEADER_FILE") 2>/dev/null ||
      { echo "FAILED: password must have at least 4 characters and no control characters"; return 1; }
  fi
}

# curl reads the header file; neither shell argv nor output contains the password.
# A function has its own positional parameters, so no `set --` juggling is needed.
bp_request() {
  local method="$1" url="$2"
  shift 2
  case "$url" in
    https://brewpage.app/api/*) : ;;
    *) echo 'FAILED: request destination must be the official BrewPage API' >&2; return 1 ;;
  esac
  if [ -n "${BP_DELIVERY_MODE:-}" ]; then
    set -- -H "X-Delivery-Mode: $BP_DELIVERY_MODE" "$@"
  fi
  if [ -n "${BP_OWNER_HEADER_FILE:-}" ]; then
    set -- -H "@$BP_OWNER_HEADER_FILE" "$@"
  fi
  if [ -n "${BP_HEADER_FILE:-}" ]; then
    set -- -H "@$BP_HEADER_FILE" "$@"
  fi
  if [ "${BP_FIRST_CREATE:-0}" = 1 ]; then
    if [ "$method" != GET ]; then printf '%s' "$BP_OPERATION_REQUEST" | bp_history pending || return 1; fi
  fi
  local output status
  : > "$BP_RUN_DIR/http-status.txt" || return 1
  output=$(curl -q -s -A "$BP_UA" -X "$method" "$url" "$@" -w $'\nBP_HTTP_STATUS:%{http_code}') || return 1
  status="${output##*$'\n'BP_HTTP_STATUS:}"
  case "$status" in
    [0123456789][0123456789][0123456789])
      printf '%s' "$status" > "$BP_RUN_DIR/http-status.txt" || return 1
      printf '%s' "${output%$'\n'BP_HTTP_STATUS:*}"
      ;;
    *) return 1 ;;
  esac
}

bp_response_status() { cat "$BP_RUN_DIR/http-status.txt"; }

bp_post() { bp_request POST "$@"; }

bp_owner_begin() {
  local intent="$1" target="$2" source="$3" selected
  BP_OWNER_HEADER_FILE="$BP_RUN_DIR/owner-token.txt"
  selected=$(bp_history select "$intent" "$target" "$source" "$BP_OWNER_HEADER_FILE") || return 1
  BP_OWNER_API="$selected"
  BP_FIRST_CREATE=0
  if [ ! -f "$BP_OWNER_HEADER_FILE" ]; then
    BP_OWNER_HEADER_FILE=""
    if [ "$intent" != update ] && [ "${BP_NO_SAVE:-0}" = 0 ]; then BP_FIRST_CREATE=1; fi
  fi
  BREWPAGE_OPERATION_ID=$(python3 -I -S -c 'import secrets; print(secrets.token_hex(12))') || return 1
  export BREWPAGE_OPERATION_ID
}

bp_prepare_recovery() {
  BP_RECOVERY_DIR="${1:-${HISTORY_FILE%/*}}"
  if [ "${BP_NO_SAVE:-0}" = 1 ]; then exec 8< "$BP_RECOVERY_DIR" || return 1; fi
  bp_recovery receipt-ready
}

bp_recovery() {
  python3 "$(dirname "${BASH_SOURCE[0]}")/history.py" "$1" "$BP_RECOVERY_DIR" brewpage-recovery.json "${BP_NO_SAVE:-0}" "$BP_ROOT" "$BP_RUN_DIR"
}

bp_operation_request() {
  [ "${BP_FIRST_CREATE:-0}" = 1 ] || return 0
  BP_OPERATION_REQUEST=$(printf '%s' "${5:-}" | python3 -I -S -c '
import hashlib,json,os,stat,sys
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs
operation,method,endpoint,kind,source,delivery,password=sys.argv[1:]
fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
with os.fdopen(fd,"rb") as payload:
 info=os.fstat(payload.fileno())
 if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1: raise ValueError("unsafe request payload")
 digest=hashlib.sha256()
 for chunk in iter(lambda:payload.read(65536),b""): digest.update(chunk)
request={"method":method,"endpoint":endpoint,"kind":kind,"namespace":parse_qs(urlsplit(endpoint).query)["ns"][0],"payloadSha256":digest.hexdigest(),"passwordProtected":password=="file","deliveryMode":delivery}
state=sys.stdin.buffer.read()
if state: request["stateSha256"]=hashlib.sha256(state).hexdigest()
if kind=="files": request["uploadName"]=os.path.basename(source)
print(json.dumps({"operationId":operation,"request":request,"recordedAt":datetime.now(timezone.utc).isoformat()},separators=(",",":")))
' "$BREWPAGE_OPERATION_ID" "$1" "$2" "$3" "$4" "${BP_DELIVERY_MODE:-}" "$BP_PASSWORD_MODE")
}

# Accept a server explanation only when it agrees with the transport status.
bp_error_reason() {
  printf '%s' "$1" | jq -sr --arg status "$2" --rawfile proof "${BP_OWNER_HEADER_FILE:-/dev/null}" '
    select(length == 1) | .[0] | select(type == "object" and (.status | tostring) == $status)
    | [(.ownerToken // ""), (.manageUrl // ""), ($proof | sub("^X-Owner-Token: ";"") | rtrimstr("\n"))] as $private
    | (.message // .error // "") | strings | reduce ($private[] | strings | select(length > 0)) as $secret (. ; split($secret) | join("[redacted]"))
    | "HTTP \($status): \(explode | map(if . < 32 or . == 127 then 32 else . end) | implode | .[0:400])"' 2>/dev/null || true
}

# Private recovery is separate from the ordinary reader-facing result.
bp_unsaved() {
  local receipt="$1"
  if [ "${BP_NO_SAVE:-0}" = 0 ]; then
    echo 'NOTICE: publication confirmed; owner history could not be saved securely'
  fi
  if [ -n "${BP_RECOVERY_DIR:-}" ]; then
    if printf '%s\n' "$receipt" | bp_recovery receipt; then
      echo 'OWNER RECOVERY SAVED'
      return 0
    fi
  fi
  echo 'NOTICE: protected recovery could not be verified; reconcile this receipt before another write'
  return 1
}

bp_receipt_link() {
  local response="$1" status="$2" method="$3" endpoint="$4"
  printf '%s' "$response" | jq -ser --arg status "$status" --arg method "$method" --arg endpoint "${endpoint%%\?*}" --arg ns "$NS" --rawfile proof "${BP_OWNER_HEADER_FILE:-/dev/null}" '
    select(length == 1) | .[0] | select(type == "object") | . as $body
    | .result.action as $action
    | select(if $method == "PUT" then $status == "200" and ($action == null or $action == "updated")
             elif $status == "200" then $action == "merged"
             else $status == "201" and ($action == null or $action == "created" or $action == "created_missing_assets" or $action == "merged") end)
    | .ownerLink | strings | capture("^https://brewpage\\.app/api/(?<kind>html|json|files|sites)/(?<ns>[a-z0-9-]{1,32})/(?<id>[A-Za-z0-9_-]{1,128})$") as $owner
    | select($body.id == $owner.id and $body.namespace == $owner.ns)
    | ("https://brewpage.app/api/" + $owner.kind) as $api
    | (if $method == "PUT" then "/" + $owner.ns + "/" + $owner.id else "" end) as $target
    | select(($api + $target) == $endpoint or ($owner.kind == "html" and $endpoint == ("https://brewpage.app/api/files" + $target)))
    | select($method == "PUT" or $owner.ns == $ns)
    | $body.link | strings | select(test("^https://[A-Za-z0-9.-]+(?:/[^[:space:][:cntrl:]#|`]*|[?][^[:space:][:cntrl:]#|`]*)?$") and . != $body.manageUrl and . != $body.managementLink)
    | . as $link | select([($body.ownerToken // ""), ($proof | sub("^X-Owner-Token: ";"") | rtrimstr("\n"))]
        | map(strings | select(length > 0) | . as $secret | $link | contains($secret)) | any | not)
  ' 2>/dev/null
}

# Every confirmed result retains effective reader facts, independently of credential storage.
bp_finish() {
  local response="$1" days="$2" type="$3" method="$4" endpoint="$5" url token fcount owner_api identity reason receipt status nonowned_merge=0 saved=0 failed=0 reused=""
  if [ -n "${BP_OWNER_HEADER_FILE:-}" ]; then
    IFS= read -r reused < "$BP_OWNER_HEADER_FILE" || return 1
    reused="${reused#X-Owner-Token: }"
  fi
  status=$(bp_response_status) || return 1
  url=$(bp_receipt_link "$response" "$status" "$method" "$endpoint") || url=""
  if [ -z "$url" ]; then
    reason=$(bp_error_reason "$response" "$status")
    if [ "${BP_FIRST_CREATE:-0}" = 1 ] && [ -n "$status" ] && [ "$status" -ge 400 ] && [ "$status" -lt 500 ] && [ "$status" -ne 408 ]; then
      bp_history clear || return 1
    fi
    case "$status" in
      4[0123456789][0123456789])
        if [ "$status" != 408 ]; then echo "FAILED: publish rejected (${reason:-HTTP $status})"; else echo 'FAILED: outcome unknown; reconcile this write before trying again'; fi
        ;;
      *) echo "FAILED: outcome unknown; reconcile this write before trying again (${reason:-no definitive receipt})" ;;
    esac
    return 1
  fi
  if printf '%s' "$response" | jq -e '.result.action == "merged" and .result.extras.isOwner == false' >/dev/null 2>&1; then
    token=""; reused=""; nonowned_merge=1
  else
    token=$(printf '%s' "$response" | jq -r '.ownerToken | strings | select(test("^[A-Za-z0-9]{32}$"))')
  fi
  owner_api=$(printf '%s' "$response" | jq -r '.ownerLink')
  identity=$(printf '%s' "$response" | jq -c '{id, namespace, type, routingCohort, deliveryMode, modeLocked, hostingVersion, managementLink, manageUrl, entryFile, createdAt, expiresAt}')
  receipt=$(printf '%s' "$response" | jq -c --rawfile proof "${BP_OWNER_HEADER_FILE:-/dev/null}" --arg api "$owner_api" --arg op "${BREWPAGE_OPERATION_ID:-}" \
    '{origin:"https://brewpage.app",ownerApi:$api,readerUrl:.link,ownerToken:((.ownerToken | strings | select(test("^[A-Za-z0-9]{32}$"))) // ($proof | sub("^X-Owner-Token: ";"") | rtrimstr("\n"))),operationId:$op,
      identity:{id,namespace,type,routingCohort,deliveryMode,modeLocked,hostingVersion,managementLink,manageUrl,entryFile,createdAt,expiresAt},manageUrl}')
  local label="$type"
  if [ "$type" = site ]; then
    fcount=$(printf '%s' "$response" | jq -r '(.fileCount | numbers) // "?"')
    label="site ($fcount files)"
  fi
  if [ -n "$reused" ] && [ -n "$token" ] && [ "$token" != "$reused" ]; then
    bp_unsaved "$receipt" || true
    failed=1
  elif [ "$nonowned_merge" = 1 ]; then
    if [ "${BP_FIRST_CREATE:-0}" = 1 ]; then bp_history clear || return 1; fi
  elif [ -n "${token:-$reused}" ]; then
    if [ "${BP_NO_SAVE:-0}" = 0 ]; then
      if bp_history_append "$url" "${token:-$reused}" "$days" "$label" "$owner_api" "$identity"; then
        saved=1
      else
        bp_unsaved "$receipt" || true
        failed=1
      fi
    elif [ -n "$token" ] && [ -z "$reused" ]; then
      bp_unsaved "$receipt" || failed=1
    fi
  elif [ "${BP_FIRST_CREATE:-0}" = 1 ]; then
    echo 'NOTICE: owner proof missing from the first receipt; recover it before another create'
  fi
  if [ "$type" = site ]; then
    echo "OK $url | Files: $fcount"
  else
    echo "OK $url"
  fi
  if [ -n "${BP_VERIFY_RECEIPT:-}" ]; then
    if [ -n "$reused" ] && { [ "${BP_EXPLICIT_PROOF:-0}" = 0 ] || [ "$saved" = 0 ]; }; then
      echo 'OWNER TOKEN REUSED'
    elif [ "$saved" = 1 ]; then
      echo 'OWNER TOKEN SAVED'
      if [ "${BP_PRIVATE_OUTPUT:-0}" = 1 ]; then printf 'OWNER RECEIPT FILE: %s (0600)\n' "$HISTORY_FILE"; fi
    fi
  fi
  if [ "$nonowned_merge" -eq 1 ]; then echo 'NOTICE: existing publication returned without ownership; no owner capability saved'; fi
  printf '%s' "$response" | jq -r --rawfile proof "${BP_OWNER_HEADER_FILE:-/dev/null}" '
    [(.ownerToken // ""), (.manageUrl // ""), (.managementLink // ""), ($proof | sub("^X-Owner-Token: ";"") | rtrimstr("\n"))] as $private |
    def line: strings | reduce ($private[] | strings | select(length > 0)) as $secret (. ; split($secret) | join("[redacted]"))
      | explode | map(if . < 32 or . == 127 then 32 else . end) | implode;
    (.visibilityNotice | line | "VISIBILITY: " + .), (.notices[]? | select(.code != "owner-token-new") | .message | line | "NOTICE: " + .),
    (.customDomain? | select(type == "object") | {hostname,status,suspended,problem,nextStep,records,serving,url,nextCheckAt} | walk(if type == "string" then line else . end) | "DOMAIN: " + tojson)' 2>/dev/null || true
  [ "$failed" = 0 ]
}

# Confirmation approves one archive digest; every run still discards its temporary payload.
bp_archive_gate() {
  local rc="$1" manifest="$2" zip="$3"
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
    [ -n "$zip" ] && rm -f "$zip"
    echo "FAILED: archive not verified (publish.mjs exit $rc) — nothing was uploaded"
    return 1
  fi
  if [ "$rc" -eq 2 ] || [ "${BREWPAGE_CONFIRMED:-0}" = 1 ] || [ -n "${BREWPAGE_REVIEW_SHA256:-}" ]; then
    local digest
    digest=$(python3 - "$zip" <<'PY'
import hashlib, os, stat, sys
fd = os.open(sys.argv[1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
with os.fdopen(fd, 'rb') as archive:
    info = os.fstat(archive.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
        raise ValueError('unsafe archive snapshot')
    digest = hashlib.sha256()
    for block in iter(lambda: archive.read(65536), b''):
        digest.update(block)
    print(digest.hexdigest())
PY
    ) || { echo 'FAILED: cannot hash reviewed archive'; return 1; }
    if [ "${BREWPAGE_CONFIRMED:-0}" != 1 ] || [ "${BREWPAGE_REVIEW_SHA256:-}" != "$digest" ]; then
      echo "REVIEW_SHA256: $digest"
      echo "CONFIRM: review this manifest, then re-run with --confirmed --review-sha256 $digest"
      return 2
    fi
  fi
  ENTRY=$(printf '%s\n' "$manifest" | sed -n 's/^ENTRY: //p')
}
