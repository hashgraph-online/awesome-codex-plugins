#!/usr/bin/env bash
# Wait for Sealos workloads to become ready, then optionally probe the public URL.
#
# Usage:
#   wait-app.sh [-n ns] [-t seconds] [-u url] <workload> [workload ...]
#   wait-app.sh [-n ns] [-t seconds] [-u url] -l <label-selector>
#
# Workloads: deployment/<name>, statefulset/<name>, cluster/<name> (KubeBlocks).
# With -l, deployments/statefulsets matching the selector are discovered.
# Exits 0 only when every workload is ready (and the URL, if given, responds
# with HTTP < 500). On failure prints pod diagnostics and exits 1.
set -u

KUBECONFIG="${KUBECONFIG:-$HOME/.sealos/kubeconfig}"
export KUBECONFIG

NAMESPACE=""
TIMEOUT=600
URL=""
SELECTOR=""

while getopts "n:t:u:l:" opt; do
  case "$opt" in
    n) NAMESPACE="$OPTARG" ;;
    t) TIMEOUT="$OPTARG" ;;
    u) URL="$OPTARG" ;;
    l) SELECTOR="$OPTARG" ;;
    *) exit 2 ;;
  esac
done
shift $((OPTIND - 1))

NS_ARGS=()
if [ -n "$NAMESPACE" ]; then
  NS_ARGS=(-n "$NAMESPACE")
fi

WORKLOADS=("$@")
if [ -n "$SELECTOR" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && WORKLOADS+=("$line")
  done < <(
    kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get deployments,statefulsets -l "$SELECTOR" \
      -o custom-columns='K:.kind,N:.metadata.name' --no-headers 2>/dev/null |
      awk '{print tolower($1) "/" $2}'
    kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get clusters.apps.kubeblocks.io -l "$SELECTOR" \
      -o custom-columns='N:.metadata.name' --no-headers 2>/dev/null |
      awk '{print "cluster/" $1}'
  )
fi

if [ "${#WORKLOADS[@]}" -eq 0 ]; then
  echo '{"error":"no workloads given or matched"}' >&2
  exit 2
fi

workload_ready() {
  # $1 = kind/name -> echoes "ready|<detail>" or "waiting|<detail>"
  local kind="${1%%/*}" name="${1#*/}" desired ready phase
  case "$kind" in
    deployment|deploy)
      desired=$(kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get deployment "$name" -o jsonpath='{.spec.replicas}' 2>/dev/null) || { echo "waiting|not found"; return; }
      ready=$(kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get deployment "$name" -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
      ;;
    statefulset|sts)
      desired=$(kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get statefulset "$name" -o jsonpath='{.spec.replicas}' 2>/dev/null) || { echo "waiting|not found"; return; }
      ready=$(kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get statefulset "$name" -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
      ;;
    cluster)
      phase=$(kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get cluster.apps.kubeblocks.io "$name" -o jsonpath='{.status.phase}' 2>/dev/null) || { echo "waiting|not found"; return; }
      if [ "$phase" = "Running" ]; then echo "ready|Running"; else echo "waiting|phase=$phase"; fi
      return
      ;;
    *)
      echo "waiting|unknown kind $kind"
      return
      ;;
  esac
  desired="${desired:-1}"
  ready="${ready:-0}"
  if [ "$ready" -ge "$desired" ] 2>/dev/null; then
    echo "ready|$ready/$desired"
  else
    echo "waiting|$ready/$desired"
  fi
}

image_broken_pods() {
  # Image identity/auth failures: these never self-heal.
  kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get pods --no-headers 2>/dev/null |
    awk '$3 ~ /(ImagePullBackOff|ErrImagePull|InvalidImageName)/ {print $1 "|" $3}'
}

crash_broken_pods() {
  # Crash/config failures: often transient while databases and their secrets
  # are still coming up (KubeBlocks account secrets appear late) — only fatal
  # when they persist well past startup.
  kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get pods --no-headers 2>/dev/null |
    awk '$3 ~ /(CrashLoopBackOff|CreateContainerConfigError|OOMKilled)/ {print $1 "|" $3}'
}

broken_pods() {
  image_broken_pods
  crash_broken_pods
}

diagnose() {
  echo "--- pods ---" >&2
  kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get pods -o wide 2>&1 >&2
  echo "--- recent events (warnings) ---" >&2
  kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} get events --field-selector type=Warning \
    --sort-by=.lastTimestamp 2>/dev/null | tail -15 >&2
  local pod
  for pod in $(broken_pods | cut -d'|' -f1 | head -3); do
    echo "--- logs: $pod (last 40 lines) ---" >&2
    kubectl ${NS_ARGS[@]+"${NS_ARGS[@]}"} logs "$pod" --all-containers --tail=40 2>&1 | tail -40 >&2
  done
}

START=$(date +%s)
IMAGE_BROKEN_STREAK=0
CRASH_BROKEN_STREAK=0

while :; do
  ALL_READY=1
  STATES=""
  for w in "${WORKLOADS[@]}"; do
    state=$(workload_ready "$w")
    STATES="$STATES$w=${state#*|} "
    [ "${state%%|*}" = "ready" ] || ALL_READY=0
  done

  if [ "$ALL_READY" -eq 1 ]; then
    break
  fi

  if [ -n "$(image_broken_pods)" ]; then
    IMAGE_BROKEN_STREAK=$((IMAGE_BROKEN_STREAK + 1))
  else
    IMAGE_BROKEN_STREAK=0
  fi
  if [ -n "$(crash_broken_pods)" ]; then
    CRASH_BROKEN_STREAK=$((CRASH_BROKEN_STREAK + 1))
  else
    CRASH_BROKEN_STREAK=0
  fi

  ELAPSED=$(( $(date +%s) - START ))
  reason=""
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    reason="timeout after ${ELAPSED}s"
  elif [ "$IMAGE_BROKEN_STREAK" -ge 12 ] && [ "$ELAPSED" -ge 90 ]; then
    reason="image pull failing persistently (bad tag, wrong arch registry, or missing pull secret)"
  elif [ "$CRASH_BROKEN_STREAK" -ge 12 ] && [ "$ELAPSED" -ge 300 ]; then
    reason="pods crash-looping past the startup grace period"
  fi
  if [ -n "$reason" ]; then
    diagnose
    printf '{"ready":false,"reason":"%s","states":"%s"}\n' "$reason" "$STATES"
    exit 1
  fi

  echo "waiting (${ELAPSED}s): $STATES" >&2
  sleep 5
done

ELAPSED=$(( $(date +%s) - START ))

HTTP_CODE=""
if [ -n "$URL" ]; then
  while :; do
    # NOTE: -w prints its code even when curl fails (e.g. 000 on timeout), so
    # a `|| echo 000` fallback would concatenate into "000000" and a numeric
    # -lt test would then treat it as 0 and pass. Capture, then sanitize.
    HTTP_CODE=$(curl -k -s -o /dev/null -w '%{http_code}' --max-time 30 -L "$URL" 2>/dev/null) || true
    case "$HTTP_CODE" in *[!0-9]* | "") HTTP_CODE=000 ;; esac
    HTTP_CODE=$(printf '%03d' "$((10#$HTTP_CODE))")
    if [ "$HTTP_CODE" != "000" ] && [ "$HTTP_CODE" -lt 500 ]; then
      break
    fi
    ELAPSED=$(( $(date +%s) - START ))
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
      diagnose
      printf '{"ready":false,"reason":"workloads ready but URL not responding","url":"%s","last_http_code":"%s"}\n' "$URL" "$HTTP_CODE"
      exit 1
    fi
    echo "waiting for URL (${ELAPSED}s): last code $HTTP_CODE" >&2
    sleep 5
  done
fi

printf '{"ready":true,"elapsed_seconds":%s,"http_code":"%s"}\n' "$ELAPSED" "${HTTP_CODE:-skipped}"
