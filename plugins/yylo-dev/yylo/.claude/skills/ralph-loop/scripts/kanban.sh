#!/usr/bin/env bash

# kanban.sh
#
# Purpose: Kanban wrapper with Python environment setup
#
# This script ensures juno-kanban always executes from the project root directory
# with the proper Python virtual environment activated.
#
# Usage: ./.juno_task/scripts/kanban.sh [juno-kanban arguments]
# Example: ./.juno_task/scripts/kanban.sh list --limit 5
# Example: ./.juno_task/scripts/kanban.sh list -f json --raw  # (flag order normalized)
# Example: ./.juno_task/scripts/kanban.sh -f json --raw list  # (also works)
# Cold exact reads are transparent; archive-search is explicit and bounded.
# Archive maintenance requires owner approval and external plan/create receipts.
# Example: ./.juno_task/scripts/kanban.sh archive-pack doctor
#
# Note: Global flags (-f/--format, -p/--pretty, --raw, -v/--verbose, -c/--config)
#       can be placed anywhere in the command line. This wrapper normalizes them
#       to appear before the command for juno-kanban compatibility.
#
# Environment Variables:
#   JUNO_DEBUG=true    - Show [DEBUG] diagnostic messages
#   JUNO_VERBOSE=true  - Show [KANBAN] informational messages
#   (Both default to false for silent operation)
#
# Created by: yylo init command
# Date: Auto-generated during project initialization

set -euo pipefail  # Exit on error, undefined variable, or pipe failure

# DEBUG OUTPUT: Show that kanban.sh is being executed (only if JUNO_DEBUG=true)
# Note: JUNO_DEBUG is separate from JUNO_VERBOSE for fine-grained control
if [ "${JUNO_DEBUG:-false}" = "true" ]; then
    echo "[DEBUG] kanban.sh is being executed from: $(pwd)" >&2
fi

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR=".venv_juno"
SCRIPTS_DIR=".juno_task/scripts"
INSTALL_SCRIPT="${SCRIPTS_DIR}/install_requirements.sh"

# Logging functions
log_info() {
    # Only print if JUNO_VERBOSE is set to true
    if [ "${JUNO_VERBOSE:-false}" = "true" ]; then
        echo -e "${BLUE}[KANBAN]${NC} $1"
    fi
}

log_success() {
    # Only print if JUNO_VERBOSE is set to true
    if [ "${JUNO_VERBOSE:-false}" = "true" ]; then
        echo -e "${GREEN}[KANBAN]${NC} $1"
    fi
}

log_warning() {
    # Only print if JUNO_VERBOSE is set to true
    if [ "${JUNO_VERBOSE:-false}" = "true" ]; then
        echo -e "${YELLOW}[KANBAN]${NC} $1"
    fi
}

log_error() {
    # Always print errors regardless of JUNO_VERBOSE; stdout remains machine-safe.
    echo -e "${RED}[KANBAN]${NC} $1" >&2
}

# Function to check if we're inside .venv_juno specifically
# CRITICAL: Don't just check for ANY venv - check if we're in .venv_juno
is_in_venv_juno() {
    # A shell may inherit another project's identically named `.venv_juno`.
    # Compare canonical directories, not basename/substrings, before skipping
    # activation of this controller's environment.
    local active_venv expected_venv
    [ -n "${VIRTUAL_ENV:-}" ] && [ -d "${VIRTUAL_ENV:-}" ] || return 1
    active_venv=$(cd "${VIRTUAL_ENV:-}" 2>/dev/null && pwd -P) || return 1
    expected_venv=$(cd "$PROJECT_ROOT/$VENV_DIR" 2>/dev/null && pwd -P) || return 1
    [ "$active_venv" = "$expected_venv" ]
}

# Function to activate virtual environment
activate_venv() {
    local venv_path="$1"

    if [ ! -d "$venv_path" ]; then
        log_error "Virtual environment not found: $venv_path"
        return 1
    fi

    # Activate the venv
    # shellcheck disable=SC1091
    if [ -f "$venv_path/bin/activate" ]; then
        source "$venv_path/bin/activate"
        log_success "Activated virtual environment: $venv_path"
        return 0
    else
        log_error "Activation script not found: $venv_path/bin/activate"
        return 1
    fi
}

# Function to ensure Python environment is ready
ensure_python_environment() {
    log_info "Checking Python environment..."

    # Step 1: Check if we're already in .venv_juno specifically
    if is_in_venv_juno; then
        log_success "Already inside .venv_juno virtual environment"
        return 0
    fi

    # Step 2: Not in .venv_juno - check if .venv_juno exists in project root
    if [ -d "$VENV_DIR" ]; then
        log_info "Found existing virtual environment: $VENV_DIR"

        # Activate the venv
        if activate_venv "$VENV_DIR"; then
            return 0
        else
            log_error "Failed to activate virtual environment"
            return 1
        fi
    fi

    # Step 3: .venv_juno doesn't exist - need to create it
    log_warning "Virtual environment not found: $VENV_DIR"
    log_info "Running install_requirements.sh to create virtual environment..."

    # Check if install_requirements.sh exists
    if [ ! -f "$INSTALL_SCRIPT" ]; then
        log_error "Install script not found: $INSTALL_SCRIPT"
        log_error "Please run 'yylo init' to initialize the project"
        return 1
    fi

    # Make sure the script is executable
    chmod +x "$INSTALL_SCRIPT"

    # Run the install script
    if bash "$INSTALL_SCRIPT"; then
        log_success "Python environment setup completed successfully"

        # After install, activate the venv if it was created
        if [ -d "$VENV_DIR" ]; then
            if activate_venv "$VENV_DIR"; then
                return 0
            fi
        fi

        return 0
    else
        log_error "Failed to run install_requirements.sh"
        log_error "Please check the error messages above"
        return 1
    fi
}

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Resolve the canonical controller from the invocation checkout. The shared
# resolver never changes refs and refuses invalid explicit/registered settings.
RESOLVER="$SCRIPT_DIR/controller_resolver.py"
if [[ ! -f "$RESOLVER" ]]; then
    echo "ERROR: Controller resolver not installed: $RESOLVER" >&2
    exit 1
fi
INVOCATION_CWD="$PWD"
# Preserve the initialized source checkout before controller resolution changes
# cwd. juno-kanban uses this only for opt-in registry policy evaluation.
export JUNO_KANBAN_INVOCATION_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
RESOLVED_ENV=$(python3 "$RESOLVER" --cwd "$INVOCATION_CWD" --operation kanban --format shell)
eval "$RESOLVED_ENV"
PROJECT_ROOT="$JUNO_TASK_ROOT"

# Kanban runtime and storage both belong to the verified controller checkout.
cd "$PROJECT_ROOT"

# Runtime selection deliberately follows the executable installed in .venv_juno.
# Never prepend a neighboring source checkout to PYTHONPATH: source integration
# alone does not authorize switching the active Kanban storage implementation.

# Arrays to store normalized arguments (declared at script level for proper handling)
declare -a NORMALIZED_GLOBAL_FLAGS=()
declare -a NORMALIZED_COMMAND_ARGS=()

# Normalize argument order for juno-kanban
# juno-kanban requires global flags BEFORE the command, but users often
# write them after (e.g., "list -f json --raw" instead of "-f json --raw list")
# This function reorders arguments so global flags come first.
# Results are stored in NORMALIZED_GLOBAL_FLAGS and NORMALIZED_COMMAND_ARGS arrays.
normalize_arguments() {
    # Reset arrays
    NORMALIZED_GLOBAL_FLAGS=()
    NORMALIZED_COMMAND_ARGS=()
    local found_command=false

    # Known subcommands
    local commands="project create search get show update archive mark list merge ready deps order history doctor archive-search archive-pack reconcile convert rollback"

    while [[ $# -gt 0 ]]; do
        case $1 in
            # Global flags that take a value
            -f|--format|-c|--config|--project)
                if [[ -n "${2:-}" ]]; then
                    NORMALIZED_GLOBAL_FLAGS+=("$1" "$2")
                    shift 2
                else
                    NORMALIZED_GLOBAL_FLAGS+=("$1")
                    shift
                fi
                ;;
            --format=*|--config=*|--project=*)
                NORMALIZED_GLOBAL_FLAGS+=("$1")
                shift
                ;;
            # Global flags that don't take a value
            -p|--pretty|--raw|-v|--verbose|--version)
                NORMALIZED_GLOBAL_FLAGS+=("$1")
                shift
                ;;
            # Check if this is a known command
            *)
                # Check if this argument is a known command
                local is_command=false
                for cmd in $commands; do
                    if [[ "$1" == "$cmd" ]]; then
                        is_command=true
                        found_command=true
                        break
                    fi
                done

                # If we found a command, everything from here goes to command_args
                if $is_command || $found_command; then
                    NORMALIZED_COMMAND_ARGS+=("$1")
                    found_command=true
                else
                    # Before finding a command, treat as command arg
                    NORMALIZED_COMMAND_ARGS+=("$1")
                fi
                shift
                ;;
        esac
    done
}

# The optional housekeeping hook validates Kanban writes, not reads. Avoid a
# Python helper plus recursive wrapper startup for commands that are provably
# read-only; unknown/new command shapes remain fail-closed through the helper.
requires_contract_write_validation() {
    local command="${NORMALIZED_COMMAND_ARGS[0]:-}"
    local subcommand="${NORMALIZED_COMMAND_ARGS[1]:-}"
    case "$command" in
        project|get|show|list|search|ready|order|history|doctor|archive-search)
            return 1
            ;;
        deps)
            [[ "$subcommand" == "add" || "$subcommand" == "remove" ]]
            return
            ;;
        archive-pack)
            case "archive-pack:$subcommand" in
                archive-pack:plan|archive-pack:doctor) return 1 ;;
                *) return 0 ;;
            esac
            ;;
        "")
            # Commandless non-TTY input is the legacy create shortcut. Interactive
            # help and explicit --version do not mutate Kanban state.
            if [[ ! -t 0 ]]; then
                return 0
            fi
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

# Main kanban logic
main() {
    log_info "=== juno-kanban Wrapper ==="

    # Select the canonical project interpreter before any Python-backed guard.
    # The guards intentionally reinvoke this wrapper once; activation is idempotent.
    if ! ensure_python_environment; then
        log_error "Failed to setup Python environment"
        exit 1
    fi
    log_success "Python environment ready!"

    # Normalize once before guards so read-only contract hooks can be skipped
    # without weakening validation for unknown or mutating command shapes.
    normalize_arguments "$@"

    # Mutations may not use argument-level storage redirection after canonical
    # resolution. Exact canonical spelling is tolerated for compatibility;
    # every other config refuses before body/stdin parsing or state creation.
    if requires_contract_write_validation; then
        local index configured canonical_config
        canonical_config=$(cd "$PROJECT_ROOT/.juno_task" && pwd -P)/config.json
        for ((index = 0; index < ${#NORMALIZED_GLOBAL_FLAGS[@]}; index++)); do
            if [[ "${NORMALIZED_GLOBAL_FLAGS[$index]}" == "-c" || "${NORMALIZED_GLOBAL_FLAGS[$index]}" == "--config" ]]; then
                configured="${NORMALIZED_GLOBAL_FLAGS[$((index + 1))]:-}"
            elif [[ "${NORMALIZED_GLOBAL_FLAGS[$index]}" == --config=* ]]; then
                configured="${NORMALIZED_GLOBAL_FLAGS[$index]#--config=}"
            else
                continue
            fi
            [[ -n "$configured" ]] || { log_error "canonical mutation config is missing"; exit 1; }
            configured=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$configured")
            [[ "$configured" == "$canonical_config" ]] || {
                log_error "Kanban mutation config must be canonical controller config: $canonical_config"
                exit 1
            }
        done
    fi

    # Sweep workers must route every Kanban operation through the coordinator's
    # assignment guard. The guard reinvokes this wrapper with the internal flag
    # after validating mutation ownership and establishing its audit boundary.
    if [[ -n "${ASSIGNED_TASK_ID:-}" && -n "${E2E_SWEEP_KANBAN_GUARD_DIR:-}" && -n "${E2E_SWEEP_KANBAN_RECORDS:-}" && "${E2E_SWEEP_KANBAN_INTERNAL:-}" != "1" ]]; then
        local guard_helper="${E2E_SWEEP_HELPER_PATH:-$PROJECT_ROOT/.juno_task/scripts/e2e_sweep_helper.py}"
        if [[ ! -f "$guard_helper" ]]; then
            log_error "E2E sweep assignment guard helper not found: $guard_helper"
            exit 1
        fi
        exec python3 "$guard_helper" guard-kanban -- "$0" "$@"
    fi

    # Projects with canonical E2E contracts validate create/body/tag writes before
    # canonical Kanban execution. The helper reinvokes this wrapper once internally.
    if [[ "${E2E_CONTRACT_VALIDATION_INTERNAL:-}" != "1" ]] && requires_contract_write_validation; then
        local contract_helper="${E2E_HOUSEKEEPING_HELPER_PATH:-$PROJECT_ROOT/.juno_task/scripts/e2e_housekeeping.py}"
        if [[ -f "$contract_helper" ]]; then
            exec python3 "$contract_helper" validate-kanban-write -- "$0" "$@"
        fi
    fi

    if [ "${JUNO_DEBUG:-false}" = "true" ]; then
        echo "[DEBUG] Original args: $*" >&2
        echo "[DEBUG] Normalized global flags: ${NORMALIZED_GLOBAL_FLAGS[*]:-<none>}" >&2
        echo "[DEBUG] Normalized command args: ${NORMALIZED_COMMAND_ARGS[*]:-<none>}" >&2
    fi

    # Execute the controller checkout's isolated runtime explicitly. Do not rely
    # on a hashed or unrelated global executable remaining earlier on PATH.
    local kanban_executable="$PROJECT_ROOT/.venv_juno/bin/juno-kanban"
    if [[ ! -x "$kanban_executable" ]]; then
        log_error "juno-kanban executable missing from controller environment: $kanban_executable"
        exit 1
    fi
    local policy_file="$SCRIPT_DIR/juno-toolchain-policy.sh"
    if [[ ! -f "$policy_file" ]]; then
        log_error "Juno 2 Kanban compatibility policy missing: $policy_file"
        exit 1
    fi
    # shellcheck source=juno-toolchain-policy.sh
    source "$policy_file"
    if ! juno_kanban_check_executable "$kanban_executable" controller-runtime; then
        exit 1
    fi
    log_info "Executing juno-kanban with normalized arguments"

    # Bind storage/config discovery to the resolved canonical controller. A
    # linked rollback checkout or global project registry must never redirect
    # reads or writes after sparse-controller cutover. Preserve an explicit
    # caller override for bounded maintenance commands.
    local arg_index arg
    local -a resolved_config_args=(--config "$PROJECT_ROOT/.juno_task/config.json")
    for ((arg_index = 0; arg_index < ${#NORMALIZED_GLOBAL_FLAGS[@]}; arg_index++)); do
        arg="${NORMALIZED_GLOBAL_FLAGS[$arg_index]}"
        if [[ "$arg" == "-c" || "$arg" == "--config" || "$arg" == --config=* ]]; then
            resolved_config_args=()
            break
        fi
    done

    # Execute with proper array expansion to preserve quoting
    # Use ${arr[@]+"${arr[@]}"} pattern to handle empty arrays with set -u
    #
    # Stdin handling:
    # Detect the type of stdin to determine whether to pass it through or redirect from /dev/null:
    # - 'p' (pipe): Pass through - user is piping data (e.g., echo "..." | kanban.sh create)
    # - '-' (regular file): Pass through - user is using heredoc (kanban.sh create << 'EOF')
    # - 'c' (character device) or other: Redirect from /dev/null to prevent hanging
    #   when called from tools that don't provide stdin (Issue #42, #60)
    #
    # Decide from command semantics rather than descriptor type. On macOS both a
    # populated subprocess pipe and an inherited idle descriptor can appear as a
    # socket; probing by type either discards real bodies or leaves query commands
    # hanging. Only commands whose syntax explicitly needs stdin receive it.
    local pass_stdin=false
    # Preserve the commandless stdin shortcut (`kanban.sh <<'EOF' ...`). This
    # includes socket-backed subprocess input on macOS, not only pipes/files.
    # Interactive no-argument calls remain nonblocking because a TTY is excluded.
    if [[ ${#NORMALIZED_COMMAND_ARGS[@]} -eq 0 && ! -t 0 ]]; then
        pass_stdin=true
    fi
    for ((arg_index = 0; arg_index < ${#NORMALIZED_COMMAND_ARGS[@]}; arg_index++)); do
        arg="${NORMALIZED_COMMAND_ARGS[$arg_index]}"
        if [[ ( "$arg" == "--body-file" || "$arg" == "--response-file" ) && "${NORMALIZED_COMMAND_ARGS[$((arg_index + 1))]:-}" == "-" ]] \
            || [[ "$arg" == "--body-file=-" || "$arg" == "--response-file=-" ]]; then
            pass_stdin=true
            break
        fi
    done
    if [[ "${NORMALIZED_COMMAND_ARGS[0]:-}" == "create" ]]; then
        # Bare create (including status/tag-only options) is the legacy implicit
        # stdin form. Recognized explicit body/title forms do not read stdin.
        pass_stdin=true
        if [[ "${NORMALIZED_COMMAND_ARGS[1]:-}" != -* && -n "${NORMALIZED_COMMAND_ARGS[1]:-}" ]]; then
            pass_stdin=false
        fi
        for arg in "${NORMALIZED_COMMAND_ARGS[@]:1}"; do
            [[ "$arg" == "--body" || "$arg" == --body=* || "$arg" == "--title" || "$arg" == --title=* || "$arg" == "--body-file" || "$arg" == --body-file=* ]] && pass_stdin=false
        done
        for ((arg_index = 0; arg_index < ${#NORMALIZED_COMMAND_ARGS[@]}; arg_index++)); do
            arg="${NORMALIZED_COMMAND_ARGS[$arg_index]}"
            if [[ "$arg" == "--body-file" && "${NORMALIZED_COMMAND_ARGS[$((arg_index + 1))]:-}" == "-" ]] || [[ "$arg" == "--body-file=-" ]]; then
                pass_stdin=true
            fi
        done
    fi

    if [[ "$pass_stdin" == true ]]; then
        "$kanban_executable" ${resolved_config_args[@]+"${resolved_config_args[@]}"} \
                    ${NORMALIZED_GLOBAL_FLAGS[@]+"${NORMALIZED_GLOBAL_FLAGS[@]}"} \
                    ${NORMALIZED_COMMAND_ARGS[@]+"${NORMALIZED_COMMAND_ARGS[@]}"}
    else
        "$kanban_executable" ${resolved_config_args[@]+"${resolved_config_args[@]}"} \
                    ${NORMALIZED_GLOBAL_FLAGS[@]+"${NORMALIZED_GLOBAL_FLAGS[@]}"} \
                    ${NORMALIZED_COMMAND_ARGS[@]+"${NORMALIZED_COMMAND_ARGS[@]}"} < /dev/null
    fi
}

# Run main function with all arguments
main "$@"
