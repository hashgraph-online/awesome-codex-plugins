#!/usr/bin/env bash
# brewpage-run.sh <probe|limits|stage|preflight|publish|update|owner-store|owner-recovery|owner-pending|owner-reconcile|cleanup> [flags].
# Values arrive as single-quoted argv, never as shell source.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=SCRIPTDIR/brewpage-lib.sh
. "$HERE/brewpage-lib.sh"

die() { printf 'FAILED: %s\n' "$1"; exit 1; }
# rc 0 when the flag at $2 has a value after it ($1 = remaining argc).
need() { [ "$1" -ge 2 ] || die "$2 needs a value"; }

# curl's form grammar parses commas/semicolons even inside shell-quoted argv.
form_file() {
  local path="$2"
  path="${path//\\/\\\\}"
  path="${path//\"/\\\"}"
  printf '%s=@"%s"' "$1" "$path"
}

BP_FRESH=""
BP_RECOVERY_DIR=""
BP_VERIFY_RECEIPT=""
# Allocates a run dir, EXIT discards it until re-armed: also when bp_run_dir rejects it.
new_run() {
  BP_FRESH=$(bp_prepare) || die "cannot allocate a private run directory"
  trap 'bp_discard "$BP_FRESH"' EXIT
}

usage() {
  cat <<'USAGE'
brewpage-run.sh probe <path>
brewpage-run.sh limits
brewpage-run.sh stage --run <run_id|''> --text <chunk>
brewpage-run.sh preflight <file|site-dir|site-zip> --path P [--entry F] [--password-file ABS] [--owner-token-file ABS]
  [--confirmed --review-sha256 SHA256]
brewpage-run.sh publish <html|html-file|json|file|site-dir|site-zip> --ns <ns> [--ttl N] [--entry F]
  [--delivery-mode path|subdomain] --password-file <ABS|''> [--state JSON] [--confirmed --review-sha256 SHA256] (--text T | --run ID | --path P)
  [--anonymous | --owner-target URL | --owner-token-file ABS] [--domain HOST] [--no-save --private-output]
brewpage-run.sh update <html|html-file|json|file|site-dir|site-zip> --target URL --password-file ''
  [--owner-token-file ABS] [--entry F] [--state JSON] [--confirmed --review-sha256 SHA256] (--text T | --run ID | --path P)
brewpage-run.sh owner-store --target OWNER_API_URL --reader READER_URL --owner-token-file ABS [--private-output]
brewpage-run.sh owner-recovery --private-output
brewpage-run.sh owner-pending --private-output
brewpage-run.sh owner-reconcile --operation REF --resolution-file ABS --private-output [--external-only]
brewpage-run.sh cleanup --run <run_id>
--ns and --password-file are required; --password-file '' explicitly selects no password.
Repeat --exclude-file ABS for additional protected files on preflight, publish or update.
--state: Page data config, a JSON object ({} = defaults); HTML pages and sites only.
Empty --ttl uses 15; empty --entry/--delivery-mode/--state are omitted. Prints OK/CONFIRM:/FAILED:; CONFIRM exits 2.
--private-output requires a verified owner-only channel; it may print private receipts and storage paths.
USAGE
}

# Read-only: type + source-tree estimates for Step 3; never uploads, never writes.
cmd_probe() {
  [ "$#" -eq 1 ] || die "probe takes exactly one path"
  local p="$1" abs html_files entry
  if [ -d "$p" ]; then
    abs=$(cd "$p" && pwd -P)
    # Hidden paths (root .well-known/ aside) never ship; entry = server rule: index.html, else shallowest HTML.
    html_files=$(cd "$abs" && find . -type f \( -name '*.html' -o -name '*.htm' \) | sed 's|^\./||' | LC_ALL=C sort |
      awk -F/ '{ for (i = 1; i <= NF; i++) if ($i ~ /^\./ && !(i == 1 && $i == ".well-known")) next; print }')
    if [ -f "$abs/index.html" ]; then entry=index.html; else
      entry=$(printf '%s\n' "$html_files" | awk -F/ 'NF { print NF "\t" $0 }' | LC_ALL=C sort -s -n -k1,1 | sed -n '1p' | cut -f2-)
    fi
    printf 'TYPE: site-dir\nPATH: %s\nFILES: %s\nHTML: %s\nSIZE_KB: %s\nENTRY: %s\n' "$abs" \
      "$(find "$abs" -type f | wc -l | tr -d ' ')" "$(printf '%s' "$html_files" | grep -c . || true)" \
      "$(du -sk "$abs" | cut -f1)" "${entry:-none}"
  elif [ -f "$p" ]; then
    abs="$(cd "$(dirname "$p")" && pwd -P)/$(basename "$p")"
    node "$HERE/publish.mjs" file --path "$abs" --check-only yes --history-file "$HISTORY_FILE" || exit 1
    local type=file
    case "$p" in *.zip) type=site-zip ;; esac
    if bp_is_markdown_path "$p"; then type=markdown; fi
    if bp_is_html_path "$p"; then type=html-file; fi
    printf 'TYPE: %s\nPATH: %s\nBYTES: %s\nMIME: %s\n' "$type" "$abs" "$(wc -c < "$abs" | tr -d ' ')" \
      "$(file --mime-type -b -- "$abs" 2>/dev/null || echo unknown)"
  else
    printf 'TYPE: none\n'
  fi
}

# Read-only: the server's current user-facing upload limits (GET /api/limits), one KEY: value per line.
cmd_limits() {
  [ "$#" -eq 0 ] || die "limits takes no arguments"
  command -v jq >/dev/null || die "jq required"
  local body
  body=$(curl -q -s -A "$BP_UA" https://brewpage.app/api/limits) || die "limits request failed"
  printf '%s' "$body" | jq -er '(.sites // empty) as $s | def mb: . / 1048576 * 10 | round / 10;
    "REQUEST_MAX_MB: \(.requestMaxBytes | mb)", "SITE_MAX_FILES: \($s.maxFiles)", "SITE_MAX_FILE_MB: \($s.maxFileBytes | mb)",
    "SITE_MAX_TOTAL_MB: \($s.maxTotalBytes | mb)", "SITE_MAX_ARCHIVE_EXPANSION_MB: \($s.maxArchiveExpansionBytes | mb)",
    "PATH_MAX_CHARS: \($s.maxPathChars)", "PATH_MAX_BYTES: \($s.maxPathBytes)", "NAME_MAX_BYTES: \($s.maxNameBytes)"' 2>/dev/null ||
    die "limits unavailable (unexpected response)"
}

# Allocates a run (empty --run) or appends to it; chunks rejoin with one newline between them.
cmd_stage() {
  local run="" text="" have_text=0 file
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --run) need "$#" "$1"; run="$2"; shift 2 ;;
      --text) need "$#" "$1"; text="$2"; have_text=1; shift 2 ;;
      *) die "unknown stage argument: $1" ;;
    esac
  done
  [ "$have_text" = 1 ] || die "stage needs --text"
  if [ -z "$run" ]; then
    new_run
    run="${BP_FRESH##*/}"
  fi
  bp_run_dir "$run" || exit 1
  file="$BP_RUN_DIR/brewpage-content.md"
  local bytes
  bytes=$(printf '%s' "$text" | python3 -I -S -c '
import fcntl, os, stat, sys
fd = os.open(sys.argv[1], os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
with os.fdopen(fd, "ab") as target:
    fcntl.flock(target, fcntl.LOCK_EX)
    info = os.fstat(target.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
        sys.exit(1)
    if info.st_size:
        target.write(b"\n")
    target.write(sys.stdin.buffer.read())
    target.flush()
    print(os.fstat(target.fileno()).st_size)
' "$file" 2>/dev/null) || die "staged content destination is unsafe"
  printf 'RUN: %s\nBYTES: %s\n' "$run" "$bytes"
  # Staged: the run outlives this call for the next chunk and the publish.
  trap - EXIT
}

cmd_cleanup() {
  [ "$#" -eq 2 ] && [ "$1" = --run ] || die "cleanup takes --run <run_id>"
  bp_run_dir "$2" || exit 1
  bp_cleanup
  printf 'CLEANED: %s\n' "$2"
}

lock_history() {
  exec 9< "$BP_ROOT"
  export BREWPAGE_HISTORY_LOCK_FD=9
  bp_history lock
}

cmd_owner_store() {
  local target="" reader="" source=""
  BP_PRIVATE_OUTPUT=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --target) need "$#" "$1"; target="$2"; shift 2 ;;
      --reader) need "$#" "$1"; reader="$2"; shift 2 ;;
      --owner-token-file) need "$#" "$1"; source="$2"; shift 2 ;;
      --private-output) BP_PRIVATE_OUTPUT=1; shift ;;
      *) die "unknown owner-store argument: $1" ;;
    esac
  done
  [ -n "$target" ] && [ -n "$reader" ] && [ -n "$source" ] || die "owner-store needs target, reader and private owner token file"
  lock_history && bp_history_init && bp_history store "$target" "$reader" "$source" || exit 1
  echo 'OWNER TOKEN SAVED'
  if [ "$BP_PRIVATE_OUTPUT" = 1 ]; then printf 'OWNER RECEIPT FILE: %s (0600)\n' "$HISTORY_FILE"; fi
}

cmd_owner_recovery() {
  [ "$#" = 1 ] && [ "$1" = --private-output ] || die "owner-recovery requires --private-output through a verified owner-only channel"
  python3 "$HERE/history.py" receipt-read "${HISTORY_FILE%/*}" brewpage-recovery.json
}

cmd_owner_pending() {
  [ "$#" = 1 ] && [ "$1" = --private-output ] || die "owner-pending requires --private-output through a verified owner-only channel"
  bp_history pending-list
}

cmd_owner_reconcile() {
  local operation="" source="" private=0 legacy=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --operation) need "$#" "$1"; operation="$2"; shift 2 ;;
      --resolution-file) need "$#" "$1"; source="$2"; shift 2 ;;
      --private-output) private=1; shift ;;
      --external-only) legacy=external-only; shift ;;
      *) die "unknown owner-reconcile argument: $1" ;;
    esac
  done
  [ "$private" = 1 ] && [ -n "$operation" ] && [ -n "$source" ] || die "owner-reconcile needs exact operation, protected resolution file and --private-output"
  lock_history && bp_history reconcile "$operation" "$source" "$legacy" || exit 1
  echo 'RECORDED: external operator attestation; helper did not authenticate the source or perform a remote write'
  if [ -n "$legacy" ]; then echo 'NOTICE: no local request witness; external-only binding recorded'; fi
}

check_review() {
  if [ -n "$BREWPAGE_REVIEW_SHA256" ]; then
    [ "${#BREWPAGE_REVIEW_SHA256}" -eq 64 ] || die "review SHA256 must be 64 lowercase hex characters"
    case "$BREWPAGE_REVIEW_SHA256" in *[!0123456789abcdef]*) die "review SHA256 must be 64 lowercase hex characters" ;; esac
    [ "$BREWPAGE_CONFIRMED" = 1 ] || die "review SHA256 requires --confirmed"
  fi
}

bp_selected_file() {
  local path="$1" output_dir="$2" zip_snapshot="${3:-}" staged="${4:-}"
  (umask 077; mkdir "$output_dir") || return 1
  CHECKED_PATH="$output_dir/${path##*/}"
  node "$HERE/publish.mjs" file --path "$path" --out "$CHECKED_PATH" --history-file "$HISTORY_FILE" \
    --password-file "$pwfile" --owner-token-file "$ownerfile" --zip-snapshot "$zip_snapshot" --staged-content "$staged" \
    ${exclusions[@]+"${exclusions[@]}"}
}

bp_selected_site() {
  local kind="$1" path="$2" mcp_out="${3:-}" rc=0 manifest
  if [ "$kind" = site-dir ]; then
    CHECKED_PATH="$BP_RUN_DIR/site.zip"
    manifest=$(umask 077; node "$HERE/publish.mjs" pack --dir "$path" --out "$CHECKED_PATH" ${ENTRY:+--entry "$ENTRY"} \
      --history-file "$HISTORY_FILE" --password-file "$pwfile" --owner-token-file "$ownerfile" \
      ${mcp_out:+--mcp-out "$mcp_out"} ${exclusions[@]+"${exclusions[@]}"}) || rc=$?
  else
    bp_selected_file "$path" "$BP_RUN_DIR/archive" yes || return 1
    manifest=$(node "$HERE/publish.mjs" inspect --zip "$CHECKED_PATH" ${ENTRY:+--entry "$ENTRY"} \
      --history-file "$HISTORY_FILE" --password-file "$pwfile" --owner-token-file "$ownerfile" ${exclusions[@]+"${exclusions[@]}"}) || rc=$?
  fi
  printf '%s\n' "$manifest"
  bp_archive_gate "$rc" "$manifest" "$CHECKED_PATH"
}

cmd_preflight() {
  local type="${1:-}" path="" pwfile="" ownerfile="" mcp_out="" ENTRY="" CHECKED_PATH=""
  local -a exclusions=()
  if [ "$#" -gt 0 ]; then shift; fi
  BREWPAGE_CONFIRMED=0
  BREWPAGE_REVIEW_SHA256=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --path) need "$#" "$1"; path="$2"; shift 2 ;;
      --entry) need "$#" "$1"; ENTRY="$2"; shift 2 ;;
      --password-file) need "$#" "$1"; pwfile="$2"; shift 2 ;;
      --owner-token-file) need "$#" "$1"; ownerfile="$2"; shift 2 ;;
      --exclude-file) need "$#" "$1"; exclusions+=(--exclude-file "$2"); shift 2 ;;
      --confirmed) BREWPAGE_CONFIRMED=1; shift ;;
      --review-sha256) need "$#" "$1"; BREWPAGE_REVIEW_SHA256="$2"; shift 2 ;;
      *) die "unknown preflight argument: $1" ;;
    esac
  done
  [ -n "$path" ] || die "preflight needs --path"
  check_review
  case "$type" in
    file) [ -z "$ENTRY$BREWPAGE_REVIEW_SHA256" ] || die "entry and review SHA256 apply to sites only" ;;
    site-dir | site-zip) : ;;
    *) die "preflight type must be file, site-dir or site-zip" ;;
  esac
  case "$path" in *$'\n'* | *$'\r'*) die "selected path must be one line" ;; esac
  new_run
  bp_run_dir "${BP_FRESH##*/}" || exit 1
  trap 'exit 1' HUP INT TERM
  case "$type" in
    file) bp_selected_file "$path" "$BP_RUN_DIR/checked" || exit 1 ;;
    site-dir) mcp_out="$BP_RUN_DIR/mcp-files.json"; bp_selected_site "$type" "$path" "$mcp_out" || exit $? ;;
    site-zip) bp_selected_site "$type" "$path" || exit $? ;;
  esac
  printf 'RUN: %s\nCHECKED_PATH: %s\n' "${BP_RUN_DIR##*/}" "$CHECKED_PATH"
  if [ -n "$mcp_out" ] && [ -f "$mcp_out" ]; then printf 'MCP_FILES_PATH: %s\n' "$mcp_out"; fi
  trap - EXIT
}

cmd_publish() {
  local action="$1"; shift
  local type="${1:-}" ns="" days=15 entry="" mode="" pwfile="" state="" text="" run="" path="" have_text=0 sources=0 have_password=0
  local target="" ownerfile="" owner_target="" domain="" anonymous=0 ttl_set=0 CHECKED_PATH=""
  local -a exclusions=()
  if [ "$#" -gt 0 ]; then shift; fi
  BP_NO_SAVE=0
  BP_PRIVATE_OUTPUT=0
  BREWPAGE_CONFIRMED=0
  BREWPAGE_REVIEW_SHA256=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --ns) need "$#" "$1"; ns="$2"; shift 2 ;;
      --ttl) need "$#" "$1"; days="${2:-15}"; ttl_set=1; shift 2 ;;
      --entry) need "$#" "$1"; entry="$2"; shift 2 ;;
      --delivery-mode) need "$#" "$1"; mode="$2"; shift 2 ;;
      --password-file) need "$#" "$1"; pwfile="$2"; have_password=1; shift 2 ;;
      --state) need "$#" "$1"; state="$2"; shift 2 ;;
      --text) need "$#" "$1"; text="$2"; have_text=1; sources=$((sources + 1)); shift 2 ;;
      --run) need "$#" "$1"; run="$2"; sources=$((sources + 1)); shift 2 ;;
      --path) need "$#" "$1"; path="$2"; sources=$((sources + 1)); shift 2 ;;
      --confirmed) BREWPAGE_CONFIRMED=1; shift ;;
      --review-sha256) need "$#" "$1"; BREWPAGE_REVIEW_SHA256="$2"; shift 2 ;;
      --target) need "$#" "$1"; target="$2"; shift 2 ;;
      --owner-target) need "$#" "$1"; owner_target="$2"; shift 2 ;;
      --owner-token-file) need "$#" "$1"; ownerfile="$2"; shift 2 ;;
      --domain) need "$#" "$1"; domain="$2"; shift 2 ;;
      --exclude-file) need "$#" "$1"; exclusions+=(--exclude-file "$2"); shift 2 ;;
      --anonymous) anonymous=1; shift ;;
      --no-save) BP_NO_SAVE=1; shift ;;
      --private-output) BP_PRIVATE_OUTPUT=1; shift ;;
      *) die "unknown publish argument: $1" ;;
    esac
  done
  [ "$have_password" -eq 1 ] || die "explicit --password-file choice required (empty means no password)"
  command -v python3 >/dev/null || die "python3 required for secure history"
  [ "$sources" -eq 1 ] || die "publish needs exactly one of --text, --run, --path"
  [ "$BP_NO_SAVE" = 0 ] || [ "$BP_PRIVATE_OUTPUT" = 1 ] || die "--no-save requires --private-output through a verified owner-only channel"
  check_review
  if [ "$action" = update ]; then
    [ -n "$target" ] || die "update needs --target with the exact publication URL"
    [ "$anonymous$BP_NO_SAVE$ttl_set" = 000 ] && [ -z "$owner_target$mode$pwfile$domain" ] || die "update needs owner proof and keeps existing visibility and expiry"
  else
    [ -z "$target" ] || die "--target applies to update only"
    if [ "$anonymous" = 1 ]; then [ -z "$ownerfile$owner_target" ] || die "--anonymous cannot be combined with saved owner proof"; fi
    if [ -n "$ownerfile" ]; then [ -z "$owner_target" ] || die "choose one owner proof source"; fi
  fi
  # A .html/.htm or markdown path is a page whichever of these a caller names.
  if [ -n "$path" ] && bp_is_html_path "$path"; then case "$type" in file | html) type=html-file ;; esac; fi
  if [ -n "$path" ] && [ "$type" = file ] && bp_is_markdown_path "$path"; then type=html; fi
  case "$type" in
    html) : ;;
    html-file) bp_is_html_path "$path" || die "html-file takes a .html or .htm --path" ;;
    json) [ -z "$path" ] || die "json takes --text or --run" ;;
    file | site-dir | site-zip) [ -n "$path" ] || die "$type takes --path" ;;
    *) die "unknown publish type: ${type:-<none>}" ;;
  esac
  case "$type" in site-dir | site-zip) : ;; *) [ -z "$entry" ] || die "--entry applies to sites only" ;; esac
  if [ -n "$domain" ]; then
    case "$type" in html | html-file | site-dir | site-zip) : ;; *) die "--domain applies to HTML and site creates only" ;; esac
    python3 -I -S -c 'import re,sys; s=sys.argv[1]; sys.exit(0 if len(s)<=253 and "." in s and all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",p) for p in s.split(".")) else 1)' "$domain" || die "--domain must be a lowercase ASCII hostname"
  fi
  case "$type" in site-dir | site-zip) : ;; *) [ -z "$BREWPAGE_REVIEW_SHA256" ] || die "review SHA256 applies to sites only" ;; esac
  if [ -n "$path" ]; then
    case "$type" in site-dir) [ -d "$path" ] || die "not a directory: $path" ;; *) [ -f "$path" ] || die "not a file: $path" ;; esac
  fi
  # Slot errors fail before the run is touched, so a staged run survives any bad flag or password file.
  if [ "$action" = update ]; then bp_validate "${ns:-target}" "$days" "$entry" || exit 1; else bp_validate "$ns" "$days" "$entry" || exit 1; fi
  case "$mode" in '' | path | subdomain) : ;; *) die "delivery mode must be path or subdomain" ;; esac
  if [ -n "$pwfile" ]; then bp_password_check "$pwfile" || exit 1; fi
  # Page data config travels as one compact JSON object; JSON and plain files take none.
  if [ -n "$state" ]; then
    case "$type" in html | html-file | site-dir | site-zip) : ;; *) die "--state applies to UTF-8 HTML pages and sites only" ;; esac
    state=$(printf '%s' "$state" | jq -cse 'if length == 1 and (.[0] | type) == "object" then .[0] else false end' 2>/dev/null) ||
      die "--state must be one JSON object, e.g. {}"
  fi

  local id pwmode=none
  if [ -n "$run" ]; then
    id="$run"
  else
    new_run
    id="${BP_FRESH##*/}"
  fi
  # An EXISTING run bp_run_dir rejects is left as is; only a fresh one is discarded.
  bp_run_dir "$id" || exit 1
  trap bp_cleanup EXIT
  if [ -n "$pwfile" ]; then
    pwmode="file"
    (umask 077; printf '%s\n' "$pwfile" > "$BP_RUN_DIR/brewpage-password-source.txt")
  fi
  local content="$BP_RUN_DIR/brewpage-content.md" ENTRY="$entry" resolved_entry=""
  if [ "$have_text" = 1 ]; then
    (umask 077; printf '%s' "$text" > "$content")
  elif [ -n "$run" ]; then
    [ -f "$content" ] || die "run $id has no staged text"
    bp_selected_file "$content" "$BP_RUN_DIR/checked" '' yes || exit 1
    content="$CHECKED_PATH"
  elif [ -n "$path" ]; then
    case "$type" in
      site-dir | site-zip) bp_selected_site "$type" "$path" || exit $?; resolved_entry="$ENTRY" ;;
      *)
        bp_selected_file "$path" "$BP_RUN_DIR/checked" || exit 1
        content="$CHECKED_PATH"
        case "$type" in
          html | html-file)
            if ! bp_is_utf8 "$content"; then
              [ "$action" != update ] || die "HTML update needs UTF-8 source"
              [ -z "$state" ] || die "--state applies to UTF-8 HTML pages and sites only"
              type=file
            fi
            ;;
        esac
        ;;
    esac
  fi

  lock_history || exit 1
  local intent=create method=POST endpoint="" kind response
  if [ "$action" = update ]; then
    intent=update
    method=PUT
  elif [ "$anonymous" = 1 ]; then
    intent=anonymous
  else
    target="$owner_target"
  fi
  bp_begin "${ns:-target}" "$days" "$entry" "$id" "$pwmode" "$mode" || exit 1
  ENTRY="$resolved_entry"
  bp_owner_begin "$intent" "$target" "$ownerfile" || exit 1
  if [ -n "$domain" ]; then
    case "$type" in html | html-file | site-dir | site-zip) : ;; *) die "requested domain cannot apply to the effective upload type; no publication sent" ;; esac
    [ -z "$pwfile" ] || die "custom domains need an HTML page or site without a password; no publication sent"
    if [ "$type" = html ]; then
      [ -z "$path" ] && bp_is_html_document "$content" || die "custom domains need supplied HTML format or a built site; no publication sent"
    fi
  fi
  [ -z "$domain" ] || [ -n "$BP_OWNER_HEADER_FILE" ] || die "requested domain needs existing applicable account owner proof before publishing"
  if [ -n "$domain" ]; then
    local domain_limits
    domain_limits=$(bp_request GET https://brewpage.app/api/limits) || die "cannot verify selected profile domain support; no publication sent"
    printf '%s' "$domain_limits" | jq -e '.reach == "profile" and .customDomains.enabled == true and (.customDomains.limit | type == "number" and . > 0)' >/dev/null 2>&1 ||
      die "selected proof does not establish an active profile with custom domains; no publication sent"
  fi
  if [ "$BP_NO_SAVE" = 0 ]; then bp_prepare_recovery || die "cannot prepare a protected owner recovery destination"; fi
  BP_VERIFY_RECEIPT=1
  BP_EXPLICIT_PROOF=0
  if [ -n "$ownerfile" ]; then BP_EXPLICIT_PROOF=1; fi
  case "$type" in html | html-file) kind=html ;; site-dir | site-zip) kind=sites ;; file) kind=files ;; *) kind="$type" ;; esac
  if [ "$action" = update ]; then
    [ -n "$BP_OWNER_HEADER_FILE" ] || die "update requires owner proof"
    case "$BP_OWNER_API" in https://brewpage.app/api/"$kind"/*) : ;; *) die "replacement type must match the targeted publication kind" ;; esac
    if [ -n "$ns" ]; then
      case "$BP_OWNER_API" in https://brewpage.app/api/"$kind/$ns"/*) : ;; *) die "--ns must match the targeted publication namespace" ;; esac
    fi
    endpoint="$BP_OWNER_API"
  else
    endpoint="https://brewpage.app/api/$kind?ns=$NS&ttl=$DAYS"
    if [ -n "$domain" ]; then endpoint="$endpoint&domain=$domain"; fi
  fi

  local unknown="request failed; outcome unknown, reconcile this write before trying again"
  case "$type" in
    html | html-file)
      local format=markdown
      if [ "$type" = html-file ] || { [ -z "$path" ] && bp_is_html_document "$content"; }; then format=html; fi
      jq -n --rawfile c "$content" --arg s "$state" '{content: $c} + (if $s == "" then {} else {state: ($s | fromjson)} end)' \
        > "$BP_RUN_DIR/payload.json"
      if [ "$action" = publish ]; then endpoint="$endpoint&format=$format"; elif [ "$format" = html ]; then endpoint="$endpoint?format=html"; fi
      if [ "$format" = html ] || [ "$action" = update ]; then
        case "$endpoint" in *\?*) endpoint="$endpoint&verbatim=true" ;; *) endpoint="$endpoint?verbatim=true" ;; esac
      fi
      bp_operation_request "$method" "$endpoint" "$kind" "$BP_RUN_DIR/payload.json" || die "cannot preserve request fingerprint before dispatch"
      response=$(bp_request "$method" "$endpoint" -H "Content-Type: application/json" -d @"$BP_RUN_DIR/payload.json") || die "$unknown"
      bp_finish "$response" "$DAYS" html
      ;;
    json)
      jq empty "$content" 2>/dev/null || die "payload is not valid JSON"
      bp_operation_request "$method" "$endpoint" "$kind" "$content" || die "cannot preserve request fingerprint before dispatch"
      response=$(bp_request "$method" "$endpoint" -H "Content-Type: application/json" -d @"$content") || die "$unknown"
      bp_finish "$response" "$DAYS" json
      ;;
    file)
      bp_operation_request "$method" "$endpoint" "$kind" "$content" || die "cannot preserve request fingerprint before dispatch"
      response=$(bp_request "$method" "$endpoint" -F "$(form_file file "$content")") || die "$unknown"
      bp_finish "$response" "$DAYS" file
      ;;
    site-dir | site-zip)
      local separator='&'
      if [ "$action" = update ]; then
        separator='?'
        if [ -z "$entry" ]; then
          local metadata
          metadata=$(bp_request GET "$endpoint") || die "cannot verify existing site entry; no replacement sent"
          ENTRY=$(printf '%s' "$metadata" | jq -er '.entryFile | strings | select(length > 0)' 2>/dev/null) || die "existing site entry is unresolved; no replacement sent"
          python3 -I -S -c 'import sys,zipfile; p=sys.argv[2]; safe=not p.startswith("/") and not any(s in ("",".","..") for s in p.split("/")) and not any(ord(c)<32 or ord(c)==127 for c in p); sys.exit(0 if safe and p in zipfile.ZipFile(sys.argv[1]).namelist() else 1)' "$CHECKED_PATH" "$ENTRY" || die "existing entry is absent or invalid in replacement; resolve the entry choice before publishing"
        fi
      fi
      endpoint="$endpoint${separator}entry=$(jq -nr --arg e "$ENTRY" '$e | @uri')"
      bp_operation_request "$method" "$endpoint" "$kind" "$CHECKED_PATH" "$state" || die "cannot preserve request fingerprint before dispatch"
      response=$(bp_request "$method" "$endpoint" -F "$(form_file archive "$CHECKED_PATH")" ${state:+--form-string "state=$state"}) || die "$unknown"
      bp_finish "$response" "$DAYS" site
      ;;
  esac
}

cmd="${1:-}"
if [ "$#" -gt 0 ]; then shift; fi
case "$cmd" in
  probe) cmd_probe "$@" ;;
  limits) cmd_limits "$@" ;;
  stage) cmd_stage "$@" ;;
  preflight) cmd_preflight "$@" ;;
  publish | update) cmd_publish "$cmd" "$@" ;;
  owner-store) cmd_owner_store "$@" ;;
  owner-recovery) cmd_owner_recovery "$@" ;;
  owner-pending) cmd_owner_pending "$@" ;;
  owner-reconcile) cmd_owner_reconcile "$@" ;;
  cleanup) cmd_cleanup "$@" ;;
  -h | --help) usage ;;
  *) usage; die "unknown subcommand: ${cmd:-<none>}" ;;
esac
