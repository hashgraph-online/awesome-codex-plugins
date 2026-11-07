#!/usr/bin/env bash
# lint-check.sh - Run quality checks for every detected stack (node/rust/python).
# Prints a PRE_DEPLOY_SUMMARY line so callers never infer coverage from prose.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
STACK_DETECT="$SCRIPT_DIR/stack-detect.sh"
PM_DETECT="$SCRIPT_DIR/pm-detect.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pre-deploy-lint.XXXXXX")"
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

# Run a command and always replay the captured output: stdout first, then stderr.
run_phase() {
  phase_status=0
  run_captured "$@" || phase_status=$?
  cat "$RUN_OUT"
  cat "$RUN_ERR" >&2
  return "$phase_status"
}

# Same as run_phase, with a single KEY=VALUE prefix applied to the child environment.
run_phase_env() {
  env_pair="$1"
  shift
  env_status=0
  run_captured env "$env_pair" "$@" || env_status=$?
  cat "$RUN_OUT"
  cat "$RUN_ERR" >&2
  return "$env_status"
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

# Validates package.json and sets HAS_TYPECHECK / HAS_LINT to 1 or 0.
# Returns 1 when the file cannot be read or its shape is invalid.
load_node_scripts() {
  parsed=""
  parsed="$(jq -r '
    if type != "object" then "invalid-object"
    elif (has("scripts") and (.scripts | type) != "object") then "invalid-scripts"
    elif ([.scripts // {} | to_entries[] | select(.value | type != "string")] | length) > 0 then "invalid-values"
    else
      (.scripts // {}) as $scripts
      | [$scripts.typecheck, $scripts.lint]
      | map(if type == "string" and length > 0 then "1" else "0" end)
      | join(" ")
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
    "")
      echo "Error: Unable to read or parse package.json: invalid JSON" >&2
      return 1
      ;;
    *)
      HAS_TYPECHECK="${parsed%% *}"
      HAS_LINT="${parsed##* }"
      return 0
      ;;
  esac
}

local_bin() {
  LOCAL_BIN=""
  if [ -e "node_modules/.bin/$1" ]; then
    LOCAL_BIN="node_modules/.bin/$1"
    return 0
  fi
  return 1
}

resolve_py_tool() {
  PY_TOOL=""
  if [ -e ".venv/bin/$1" ]; then
    PY_TOOL=".venv/bin/$1"
    return 0
  fi
  if command -v "$1" >/dev/null 2>&1; then
    PY_TOOL="$1"
    return 0
  fi
  return 1
}

node_script_command() {
  if [ "$PM" = "yarn" ]; then
    NS_CMD=(yarn "$1")
  else
    NS_CMD=("$PM" run "$1")
  fi
}

# Print a gate header; run it when a command is given, otherwise report the skip.
run_gate() {
  gate_label="$1"
  gate_reason="$2"
  shift 2
  printf '\n--- [node] %s ---\n' "$gate_label"
  if [ -z "$gate_reason" ] && [ "$#" -gt 0 ]; then
    gate_status=0
    run_captured "$@" || gate_status=$?
    if [ "$gate_status" -eq 0 ]; then
      echo "✓ $gate_label passed"
      EXECUTED=$((EXECUTED + 1))
    else
      cat "$RUN_OUT"
      cat "$RUN_ERR" >&2
      GATE_FAILED=1
    fi
    return 0
  fi
  printf '(skipped: %s)\n' "$gate_reason"
  SKIPPED=$((SKIPPED + 1))
  return 0
}

run_node_checks() {
  if [ ! -e "$PM_DETECT" ]; then
    echo "Error: pm-detect.sh not found or not executable" >&2
    return 1
  fi
  package_manager || return 1
  load_node_scripts || return 1
  printf '\n=== [node] Running checks ===\n'
  GATE_FAILED=0
  if [ "$HAS_TYPECHECK" -eq 0 ] && [ ! -e tsconfig.json ]; then
    run_gate Typecheck "no typecheck script and no tsconfig.json"
  elif [ "$HAS_TYPECHECK" -eq 1 ]; then
    node_script_command typecheck
    run_gate Typecheck "" "${NS_CMD[@]}"
  elif local_bin tsc; then
    run_gate Typecheck "" "$LOCAL_BIN" --noEmit
  else
    run_gate Typecheck "typescript is not installed locally; run the project's own typecheck script instead"
  fi
  eslint_config=0
  for candidate in eslint.config.js eslint.config.mjs .eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json; do
    if [ -e "$candidate" ]; then
      eslint_config=1
      break
    fi
  done
  if [ "$HAS_LINT" -eq 1 ]; then
    node_script_command lint
    run_gate Lint "" "${NS_CMD[@]}"
  elif [ "$eslint_config" -eq 0 ]; then
    run_gate Lint "no lint script and no ESLint config"
  elif local_bin eslint; then
    run_gate Lint "" "$LOCAL_BIN" .
  else
    run_gate Lint "eslint is not installed locally"
  fi
  if [ "$GATE_FAILED" -eq 0 ]; then
    return 0
  fi
  return 1
}

clippy_command() {
  run_captured cargo --version || true
  cargo_version="$(trim_whitespace "$(cat "$RUN_OUT")")"
  cargo_major=""
  cargo_minor=""
  if [[ "$cargo_version" =~ ^cargo\ ([0-9]+)\.([0-9]+) ]]; then
    cargo_major="${BASH_REMATCH[1]}"
    cargo_minor="${BASH_REMATCH[2]}"
  fi
  if [ -n "$cargo_major" ] && { [ "$cargo_major" -gt 1 ] || { [ "$cargo_major" -eq 1 ] && [ "$cargo_minor" -ge 97 ]; }; }; then
    echo "(warnings denied through CARGO_BUILD_WARNINGS=deny, which preserves the build cache)"
    CLIPPY_ENV="CARGO_BUILD_WARNINGS=deny"
    CLIPPY_CMD=(cargo clippy --all-targets --all-features)
    return 0
  fi
  echo "(warnings denied through \`-- -D warnings\`; toolchain older than Cargo 1.97)"
  CLIPPY_ENV=""
  CLIPPY_CMD=(cargo clippy --all-targets --all-features -- -D warnings)
  return 0
}

run_rust_checks() {
  printf '\n=== [rust] Running checks ===\n'
  if ! command -v cargo >/dev/null 2>&1; then
    echo "Error: cargo not found for Rust project" >&2
    return 1
  fi
  RUST_FAILED=0
  if ! command -v rustfmt >/dev/null 2>&1; then
    printf '%s\n' "--- [rust] cargo fmt --check ---" "(skipped: rustfmt is not installed)"
    SKIPPED=$((SKIPPED + 1))
  else
    echo "--- [rust] cargo fmt --check ---"
    fmt_status=0
    run_phase cargo fmt --all -- --check || fmt_status=$?
    if [ "$fmt_status" -eq 0 ]; then
      echo "✓ Format check passed"
      EXECUTED=$((EXECUTED + 1))
    else
      RUST_FAILED=1
    fi
  fi
  echo ""
  clippy_command
  echo "--- [rust] cargo clippy ---"
  clippy_status=0
  if [ -n "$CLIPPY_ENV" ]; then
    run_phase_env "$CLIPPY_ENV" "${CLIPPY_CMD[@]}" || clippy_status=$?
  else
    run_phase "${CLIPPY_CMD[@]}" || clippy_status=$?
  fi
  if [ "$clippy_status" -eq 0 ]; then
    echo "✓ Clippy passed"
    EXECUTED=$((EXECUTED + 1))
  else
    RUST_FAILED=1
  fi
  echo ""
  echo "--- [rust] cargo check ---"
  check_status=0
  run_phase cargo check --all-targets --all-features || check_status=$?
  if [ "$check_status" -eq 0 ]; then
    echo "✓ Cargo check passed"
    EXECUTED=$((EXECUTED + 1))
  else
    RUST_FAILED=1
  fi
  if [ "$RUST_FAILED" -eq 0 ]; then
    return 0
  fi
  return 1
}

run_python_checks() {
  printf '\n=== [python] Running checks ===\n'
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
  PY_FAILED=0
  LINT_TOOL=""
  if resolve_py_tool ruff || resolve_py_tool flake8; then
    LINT_TOOL="$PY_TOOL"
  fi
  if [ -n "$LINT_TOOL" ]; then
    case "$LINT_TOOL" in
      *ruff)
        echo "--- [python] Ruff ---"
        lint_status=0
        run_phase "$LINT_TOOL" check . || lint_status=$?
        if [ "$lint_status" -eq 0 ]; then
          echo "✓ Ruff passed"
          EXECUTED=$((EXECUTED + 1))
        else
          PY_FAILED=1
        fi
        ;;
      *)
        echo "--- [python] Flake8 ---"
        lint_status=0
        run_phase "$LINT_TOOL" . || lint_status=$?
        if [ "$lint_status" -eq 0 ]; then
          echo "✓ Flake8 passed"
          EXECUTED=$((EXECUTED + 1))
        else
          PY_FAILED=1
        fi
        ;;
    esac
  else
    printf '%s\n' "--- [python] Lint ---" "(skipped: ruff/flake8 not found)"
    SKIPPED=$((SKIPPED + 1))
  fi
  echo ""
  if resolve_py_tool mypy; then
    echo "--- [python] Mypy ---"
    mypy_status=0
    run_phase "$PY_TOOL" . || mypy_status=$?
    if [ "$mypy_status" -eq 0 ]; then
      echo "✓ Mypy passed"
      EXECUTED=$((EXECUTED + 1))
    else
      PY_FAILED=1
    fi
  else
    echo "--- [python] Type/Syntax ---"
    syntax_status=0
    run_phase "$PYTHON_BIN" -m compileall -q -x '(^|/)(\.git|\.venv|node_modules|dist|build)(/|$)' . || syntax_status=$?
    if [ "$syntax_status" -eq 0 ]; then
      echo "✓ Syntax compile check passed (fallback)"
      EXECUTED=$((EXECUTED + 1))
    else
      PY_FAILED=1
    fi
  fi
  if [ "$PY_FAILED" -eq 0 ]; then
    return 0
  fi
  return 1
}

main() {
  echo "=========================================="
  echo "  Pre-Deploy Quality Checks"
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
  TOTAL_EXIT=0
  while IFS= read -r stack; do
    if [ -z "$stack" ]; then
      continue
    fi
    if [ "$STOP_NEW_WORK" -eq 1 ]; then
      return 1
    fi
    case "$stack" in
      node)
        run_node_checks || TOTAL_EXIT=1
        ;;
      rust)
        run_rust_checks || TOTAL_EXIT=1
        ;;
      python)
        run_python_checks || TOTAL_EXIT=1
        ;;
      *)
        echo "Warning: Unknown stack '$stack'" >&2
        ;;
    esac
  done <<< "$stacks"
  echo ""
  echo "=========================================="
  if [ "$TOTAL_EXIT" -ne 0 ]; then
    echo "  ✗ Quality checks failed"
  elif [ "$EXECUTED" -eq 0 ]; then
    echo "  - No quality check executed (skipped is not passed)"
  else
    echo "  ✓ All executed quality checks passed"
  fi
  echo "=========================================="
  echo "PRE_DEPLOY_SUMMARY executed=$EXECUTED skipped=$SKIPPED"
  return "$TOTAL_EXIT"
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
