#!/usr/bin/env bash
# build-run.sh - Run the build phase for every detected stack (node/rust/python).
# Prints a PRE_DEPLOY_SUMMARY line so callers never infer coverage from prose.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
STACK_DETECT="$SCRIPT_DIR/stack-detect.sh"
PM_DETECT="$SCRIPT_DIR/pm-detect.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pre-deploy-build.XXXXXX")"
EXECUTED=0
SKIPPED=0
STOP_NEW_WORK=0
REQUESTED_SIGNAL=""
CURRENT_PID=""

cleanup() {
  if [ -n "$TMP_ROOT" ] && [ -d "$TMP_ROOT" ]; then
    rm -rf "$TMP_ROOT"
  fi
}

# Invoked from the trap handlers below, which shellcheck cannot see.
# shellcheck disable=SC2329
on_signal() {
  signal_name="$1"
  if [ -z "$REQUESTED_SIGNAL" ]; then
    REQUESTED_SIGNAL="$signal_name"
  fi
  STOP_NEW_WORK=1
  # Bash starts asynchronous children with SIGINT ignored, so a forwarded INT
  # never reaches them; TERM does, and it terminates children whether they trap
  # it or take the default action. The parent still re-raises the original
  # signal after reaping its child.
  forward_signal="$signal_name"
  if [ "$forward_signal" = "INT" ]; then
    forward_signal="TERM"
  fi
  if [ -n "$CURRENT_PID" ]; then
    kill -s "$forward_signal" "$CURRENT_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

# Trim leading and trailing whitespace, mirroring String.prototype.trim for ASCII text.
trim_whitespace() {
  trimmed="$1"
  trimmed="${trimmed#"${trimmed%%[![:space:]]*}"}"
  trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
  printf '%s' "$trimmed"
}

# Run a command with its output captured in files; sets RUN_OUT and RUN_ERR.
# Returns the child exit code, or 1 without spawning once a signal has arrived.
run_captured() {
  RUN_OUT="$TMP_ROOT/stdout.log"
  RUN_ERR="$TMP_ROOT/stderr.log"
  : > "$RUN_OUT"
  : > "$RUN_ERR"
  if [ "$STOP_NEW_WORK" -eq 1 ]; then
    return 1
  fi
  "$@" > "$RUN_OUT" 2> "$RUN_ERR" &
  child_pid=$!
  CURRENT_PID=$child_pid
  child_status=0
  wait "$child_pid" || child_status=$?
  CURRENT_PID=""
  return "$child_status"
}

# Run a command and replay its captured output: stdout first, then stderr.
run_replay() {
  replay_status=0
  run_captured "$@" || replay_status=$?
  cat "$RUN_OUT"
  cat "$RUN_ERR" >&2
  return "$replay_status"
}

is_build_module_missing() {
  text="$1"
  case "$text" in
    *$'\n') text="${text%$'\n'}" ;;
  esac
  case "$text" in
    *$'\r') text="${text%$'\r'}" ;;
  esac
  build_missing_re='^(.+: )?No module named build$'
  [[ "$text" =~ $build_missing_re ]]
}

package_manager() {
  pm_status=0
  run_captured bash "$PM_DETECT" || pm_status=$?
  if [ "$pm_status" -ne 0 ]; then
    cat "$RUN_ERR" >&2
    return 1
  fi
  PM="$(trim_whitespace "$(cat "$RUN_OUT")")"
  return 0
}

# Validates package.json and sets SCRIPT_PRESENT to 1 or 0.
# Returns 1 when the file cannot be read or its shape is invalid.
has_package_script() {
  script_name="$1"
  parsed=""
  parsed="$(jq -r --arg name "$script_name" '
    if type != "object" then "invalid-object"
    elif (has("scripts") and (.scripts | type) != "object") then "invalid-scripts"
    elif ([.scripts // {} | to_entries[] | select(.value | type != "string")] | length) > 0 then "invalid-values"
    else
      (.scripts // {}) as $scripts
      | ($scripts[$name] // "") as $value
      | (($value | type) == "string" and ($value | length) > 0)
      | tostring
    end
  ' package.json 2>/dev/null)" || parsed=""
  case "$parsed" in
    invalid-object)
      echo "Error: Invalid package.json: expected a JSON object" >&2
      return 1
      ;;
    invalid-scripts)
      echo "Error: Invalid package.json: expected scripts to be an object" >&2
      return 1
      ;;
    invalid-values)
      echo "Error: Invalid package.json: expected script values to be strings" >&2
      return 1
      ;;
    true)
      SCRIPT_PRESENT=1
      return 0
      ;;
    false)
      SCRIPT_PRESENT=0
      return 0
      ;;
    *)
      echo "Error: Unable to read or parse package.json: invalid JSON" >&2
      return 1
      ;;
  esac
}

run_node_build() {
  printf '\n=== [node] Build ===\n'
  package_manager || return 1
  has_package_script build || return 1
  if [ "$SCRIPT_PRESENT" -eq 0 ]; then
    echo "[node] No build script found in package.json. Skipping."
    SKIPPED=$((SKIPPED + 1))
    return 0
  fi
  case "$PM" in
    bun) build_cmd=(bun run build) ;;
    pnpm) build_cmd=(pnpm run build) ;;
    yarn) build_cmd=(yarn build) ;;
    npm) build_cmd=(npm run build) ;;
    *)
      echo "Error: Unknown package manager: $PM" >&2
      return 1
      ;;
  esac
  build_status=0
  run_replay "${build_cmd[@]}" || build_status=$?
  if [ "$build_status" -ne 0 ]; then
    return 1
  fi
  echo "✓ Node build completed"
  EXECUTED=$((EXECUTED + 1))
  return 0
}

run_rust_build() {
  printf '\n=== [rust] Build ===\n'
  if ! command -v cargo >/dev/null 2>&1; then
    echo "Error: cargo not found for Rust project" >&2
    return 1
  fi
  rust_status=0
  run_replay cargo build --release || rust_status=$?
  if [ "$rust_status" -ne 0 ]; then
    return 1
  fi
  echo "✓ Rust build completed"
  EXECUTED=$((EXECUTED + 1))
  return 0
}

run_compile_fallback() {
  compile_status=0
  run_replay "$PYTHON_BIN" -m compileall -q -x '(^|/)(\.git|\.venv|node_modules|dist|build)(/|$)' . || compile_status=$?
  if [ "$compile_status" -ne 0 ]; then
    return 1
  fi
  echo "✓ Python compile fallback completed"
  return 0
}

run_python_build() {
  printf '\n=== [python] Build ===\n'
  PYTHON_BIN=""
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
  fi
  if [ -z "$PYTHON_BIN" ]; then
    echo "Error: python/python3 not found for Python project" >&2
    return 1
  fi
  if command -v poetry >/dev/null 2>&1 && [ -e poetry.lock ]; then
    poetry_status=0
    run_replay poetry build || poetry_status=$?
    if [ "$poetry_status" -ne 0 ]; then
      return 1
    fi
    echo "✓ Python build completed (poetry)"
  elif [ -e pyproject.toml ] || [ -e setup.py ]; then
    probe_status=0
    run_captured "$PYTHON_BIN" -m build --version || probe_status=$?
    if [ "$probe_status" -eq 0 ]; then
      build_status=0
      run_replay "$PYTHON_BIN" -m build || build_status=$?
      if [ "$build_status" -ne 0 ]; then
        return 1
      fi
      echo "✓ Python build completed (python -m build)"
    elif is_build_module_missing "$(cat "$RUN_ERR")"; then
      echo "[python] build module not found. Running compile fallback."
      run_compile_fallback || return 1
    else
      cat "$RUN_OUT"
      cat "$RUN_ERR" >&2
      return "$probe_status"
    fi
  else
    echo "[python] Packaging files not found. Running compile fallback."
    run_compile_fallback || return 1
  fi
  EXECUTED=$((EXECUTED + 1))
  return 0
}

main() {
  echo "=========================================="
  echo "  Pre-Deploy Build Phase"
  echo "=========================================="
  if [ ! -e "$STACK_DETECT" ]; then
    echo "Error: stack-detect.sh not found or not executable" >&2
    return 1
  fi
  detect_status=0
  run_captured bash "$STACK_DETECT" || detect_status=$?
  if [ "$detect_status" -ne 0 ]; then
    cat "$RUN_ERR" >&2
    return "$detect_status"
  fi
  stacks="$(cat "$RUN_OUT")"
  while IFS= read -r stack; do
    if [ -z "$stack" ]; then
      continue
    fi
    if [ "$STOP_NEW_WORK" -eq 1 ]; then
      return 1
    fi
    case "$stack" in
      node)
        run_node_build || return 1
        ;;
      rust)
        run_rust_build || return 1
        ;;
      python)
        python_status=0
        run_python_build || python_status=$?
        if [ "$python_status" -ne 0 ]; then
          return "$python_status"
        fi
        ;;
      *)
        echo "Warning: Unknown stack '$stack'" >&2
        ;;
    esac
  done <<< "$stacks"
  echo ""
  echo "=========================================="
  if [ "$EXECUTED" -eq 0 ]; then
    echo "  - No build executed (skipped is not passed)"
  else
    echo "  ✓ Build phase completed"
  fi
  echo "=========================================="
  echo "PRE_DEPLOY_SUMMARY executed=$EXECUTED skipped=$SKIPPED"
  return 0
}

main_status=0
main || main_status=$?

if [ -n "$REQUESTED_SIGNAL" ]; then
  trap - EXIT INT TERM
  if [ -n "$CURRENT_PID" ]; then
    wait "$CURRENT_PID" 2>/dev/null || true
  fi
  cleanup
  kill -s "$REQUESTED_SIGNAL" $$
fi
exit "$main_status"
