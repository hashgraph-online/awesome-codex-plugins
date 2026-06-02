#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ts_common.sh
source "$SCRIPT_DIR/ts_common.sh"

TAILNET="$(tailnet)"
CALL=(bash "$SCRIPT_DIR/ts_call.sh")

usage() {
  cat <<'USAGE'
Usage:
  ts_api.sh <command> [args]

Read:
  status
  devices
  device <device-id>
  routes <device-id>
  keys [--all]
  users
  dns
  services
  policy

Mutate, always run --dry-run before --yes:
  rename-device <device-id> <new-name> [--dry-run|--yes]
  authorize-device <device-id> <true|false> [--dry-run|--yes]
  expire-device-key <device-id> [--dry-run|--yes]
  update-device-key <device-id> <true|false> [--dry-run|--yes]
  set-device-tags <device-id> '<json-tags-array>' [--dry-run|--yes]
  set-device-routes <device-id> '<json-routes-array>' [--dry-run|--yes]
  create-auth-key '<json-body>' [--dry-run|--yes]
  validate-policy <file> [--dry-run|--yes]
  set-policy <file> [--dry-run|--yes]

Examples:
  ts_api.sh devices
  ts_api.sh keys --all
  ts_api.sh rename-device node-id server-1 --dry-run
  ts_api.sh set-device-tags node-id '["tag:server"]' --dry-run
USAGE
}

require_json_array() {
  local value="$1"
  jq -e 'type=="array"' <<<"$value" >/dev/null
}

write_flag_or_die() {
  local flag="${1:-}"
  case "$flag" in
    --dry-run|--yes)
      printf '%s' "$flag"
      ;;
    "")
      echo "error: mutating command requires --dry-run or --yes" >&2
      exit 1
      ;;
    *)
      echo "error: expected --dry-run or --yes, got $flag" >&2
      exit 1
      ;;
  esac
}

cmd="${1:-}"
if [[ -z "$cmd" ]]; then
  usage
  exit 1
fi
shift

case "$cmd" in
  status)
    "${CALL[@]}" getTailnetSettings \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --jq '{aclsExternallyManagedOn,devicesApprovalOn,devicesAutoUpdatesOn,devicesKeyDurationDays,usersApprovalOn,usersRoleAllowedToJoinExternalTailnets,networkFlowLoggingOn,regionalRoutingOn,postureIdentityCollectionOn,httpsEnabled}'
    ;;
  devices)
    "${CALL[@]}" listTailnetDevices \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --jq '.devices[] | {id,nodeId,name,hostname,user,addresses,authorized,tags,lastSeen,expires}'
    ;;
  device)
    device_id="${1:-}"
    [[ -n "$device_id" ]] || { echo "error: missing device-id" >&2; exit 1; }
    "${CALL[@]}" getDevice --params-json "{\"deviceId\":\"$device_id\"}"
    ;;
  routes)
    device_id="${1:-}"
    [[ -n "$device_id" ]] || { echo "error: missing device-id" >&2; exit 1; }
    "${CALL[@]}" listDeviceRoutes --params-json "{\"deviceId\":\"$device_id\"}"
    ;;
  keys)
    query="{}"
    if [[ "${1:-}" == "--all" ]]; then
      query='{"all":true}'
    fi
    "${CALL[@]}" listTailnetKeys \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --query-json "$query" \
      --jq '.[]? // .keys[]? // .'
    ;;
  users)
    "${CALL[@]}" listUsers \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --jq '.users[] | {id,loginName,displayName,role,status,type,created}'
    ;;
  dns)
    "${CALL[@]}" getDnsConfiguration --params-json "{\"tailnet\":\"$TAILNET\"}"
    ;;
  services)
    "${CALL[@]}" listServices --params-json "{\"tailnet\":\"$TAILNET\"}"
    ;;
  policy)
    "${CALL[@]}" getPolicyFile --params-json "{\"tailnet\":\"$TAILNET\"}" --raw
    ;;
  rename-device)
    device_id="${1:-}"
    new_name="${2:-}"
    flag="$(write_flag_or_die "${3:-}")"
    [[ -n "$device_id" && -n "$new_name" ]] || { echo "error: usage rename-device <device-id> <new-name> [--dry-run|--yes]" >&2; exit 1; }
    "${CALL[@]}" setDeviceName \
      --params-json "{\"deviceId\":\"$device_id\"}" \
      --body-json "$(jq -nc --arg name "$new_name" '{name:$name}')" \
      "$flag"
    ;;
  authorize-device)
    device_id="${1:-}"
    authorized="${2:-}"
    flag="$(write_flag_or_die "${3:-}")"
    [[ -n "$device_id" && -n "$authorized" ]] || { echo "error: usage authorize-device <device-id> <true|false> [--dry-run|--yes]" >&2; exit 1; }
    [[ "$authorized" == "true" || "$authorized" == "false" ]] || { echo "error: authorized must be true or false" >&2; exit 1; }
    "${CALL[@]}" authorizeDevice \
      --params-json "{\"deviceId\":\"$device_id\"}" \
      --body-json "{\"authorized\":$authorized}" \
      "$flag"
    ;;
  expire-device-key)
    device_id="${1:-}"
    flag="$(write_flag_or_die "${2:-}")"
    [[ -n "$device_id" ]] || { echo "error: missing device-id" >&2; exit 1; }
    "${CALL[@]}" expireDeviceKey --params-json "{\"deviceId\":\"$device_id\"}" "$flag"
    ;;
  update-device-key)
    device_id="${1:-}"
    disabled="${2:-}"
    flag="$(write_flag_or_die "${3:-}")"
    [[ -n "$device_id" && -n "$disabled" ]] || { echo "error: usage update-device-key <device-id> <true|false> [--dry-run|--yes]" >&2; exit 1; }
    [[ "$disabled" == "true" || "$disabled" == "false" ]] || { echo "error: keyExpiryDisabled must be true or false" >&2; exit 1; }
    "${CALL[@]}" updateDeviceKey \
      --params-json "{\"deviceId\":\"$device_id\"}" \
      --body-json "{\"keyExpiryDisabled\":$disabled}" \
      "$flag"
    ;;
  set-device-tags)
    device_id="${1:-}"
    tags="${2:-}"
    flag="$(write_flag_or_die "${3:-}")"
    [[ -n "$device_id" && -n "$tags" ]] || { echo "error: usage set-device-tags <device-id> '<json-tags-array>' [--dry-run|--yes]" >&2; exit 1; }
    require_json_array "$tags"
    "${CALL[@]}" setDeviceTags \
      --params-json "{\"deviceId\":\"$device_id\"}" \
      --body-json "$(jq -nc --argjson tags "$tags" '{tags:$tags}')" \
      "$flag"
    ;;
  set-device-routes)
    device_id="${1:-}"
    routes="${2:-}"
    flag="$(write_flag_or_die "${3:-}")"
    [[ -n "$device_id" && -n "$routes" ]] || { echo "error: usage set-device-routes <device-id> '<json-routes-array>' [--dry-run|--yes]" >&2; exit 1; }
    require_json_array "$routes"
    "${CALL[@]}" setDeviceRoutes \
      --params-json "{\"deviceId\":\"$device_id\"}" \
      --body-json "$(jq -nc --argjson routes "$routes" '{routes:$routes}')" \
      "$flag"
    ;;
  create-auth-key)
    body="${1:-}"
    flag="$(write_flag_or_die "${2:-}")"
    [[ -n "$body" ]] || { echo "error: usage create-auth-key '<json-body>' [--dry-run|--yes]" >&2; exit 1; }
    jq -e 'type=="object"' <<<"$body" >/dev/null
    "${CALL[@]}" createKey \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --body-json "$body" \
      "$flag"
    ;;
  validate-policy)
    file="${1:-}"
    flag="$(write_flag_or_die "${2:-}")"
    [[ -f "$file" ]] || { echo "error: policy file not found: $file" >&2; exit 1; }
    "${CALL[@]}" validateAndTestPolicyFile \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --body-file "$file" \
      "$flag"
    ;;
  set-policy)
    file="${1:-}"
    flag="$(write_flag_or_die "${2:-}")"
    [[ -f "$file" ]] || { echo "error: policy file not found: $file" >&2; exit 1; }
    "${CALL[@]}" setPolicyFile \
      --params-json "{\"tailnet\":\"$TAILNET\"}" \
      --body-file "$file" \
      "$flag"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "error: unknown command: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac
