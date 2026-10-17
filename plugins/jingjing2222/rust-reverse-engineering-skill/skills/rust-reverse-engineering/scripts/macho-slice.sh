#!/usr/bin/env bash

# Common helpers for choosing a single-slice analysis target from a universal Mach-O.

macho_normalize_arch() {
  case "$1" in
    arm64|arm64e|aarch64)
      echo "arm64"
      ;;
    x86_64|x86_64h|x86-64|amd64|i386)
      echo "x86_64"
      ;;
    *)
      echo "$1"
      ;;
  esac
}

macho_host_arch() {
  macho_normalize_arch "$(uname -m 2>/dev/null || echo unknown)"
}

macho_is_universal_target() {
  local target="$1"
  local file_out

  file_out="$(file "$target" 2>/dev/null || true)"
  [[ "$file_out" == *"Mach-O universal binary"* ]]
}

macho_list_arch_tokens() {
  local target="$1"

  if ! command -v lipo >/dev/null 2>&1; then
    return 1
  fi

  lipo -archs "$target" 2>/dev/null
}

macho_pick_arch_token() {
  local requested_arch="$1"
  shift

  local token
  local requested_norm
  local host_norm

  if [[ "$#" -eq 0 ]]; then
    return 1
  fi

  requested_norm="$(macho_normalize_arch "$requested_arch")"
  if [[ -n "$requested_norm" ]]; then
    for token in "$@"; do
      if [[ "$(macho_normalize_arch "$token")" == "$requested_norm" ]]; then
        echo "$token"
        return 0
      fi
    done
    return 1
  fi

  host_norm="$(macho_host_arch)"
  for token in "$@"; do
    if [[ "$(macho_normalize_arch "$token")" == "$host_norm" ]]; then
      echo "$token"
      return 0
    fi
  done

  for requested_norm in arm64 x86_64; do
    for token in "$@"; do
      if [[ "$(macho_normalize_arch "$token")" == "$requested_norm" ]]; then
        echo "$token"
        return 0
      fi
    done
  done

  echo "$1"
}

macho_resolve_target() {
  local target="$1"
  local requested_arch="${2:-}"
  local output_dir="${3:-}"
  local arch_words
  local arch_token
  local thin_target
  local token
  local -a arch_tokens

  MACHO_ORIGINAL_TARGET="$target"
  MACHO_ANALYSIS_TARGET="$target"
  MACHO_IS_UNIVERSAL="no"
  MACHO_ARCH_LIST=""
  MACHO_SELECTED_ARCH=""
  MACHO_SELECTED_ARCH_TOKEN=""

  if ! macho_is_universal_target "$target"; then
    return 0
  fi

  if ! command -v lipo >/dev/null 2>&1; then
    echo "Error: lipo is required to thin a universal Mach-O target before analysis." >&2
    return 1
  fi

  arch_words="$(macho_list_arch_tokens "$target" || true)"
  if [[ -z "$arch_words" ]]; then
    echo "Error: failed to enumerate Mach-O slices for $target" >&2
    return 1
  fi

  MACHO_IS_UNIVERSAL="yes"
  MACHO_ARCH_LIST="$(printf '%s\n' "$arch_words" | awk '{$1=$1; gsub(/ /,","); print}')"

  arch_tokens=()
  for token in $arch_words; do
    arch_tokens+=("$token")
  done

  arch_token="$(macho_pick_arch_token "$requested_arch" "${arch_tokens[@]}" || true)"
  if [[ -z "$arch_token" ]]; then
    echo "Error: requested Mach-O slice '$requested_arch' is not present. Available slices: $MACHO_ARCH_LIST" >&2
    return 1
  fi

  if [[ -z "$output_dir" ]]; then
    echo "Error: output directory is required when resolving a universal Mach-O target." >&2
    return 1
  fi

  mkdir -p "$output_dir"
  thin_target="$output_dir/$(basename "$target").${arch_token}"
  lipo -thin "$arch_token" "$target" -output "$thin_target"

  MACHO_ANALYSIS_TARGET="$thin_target"
  MACHO_SELECTED_ARCH_TOKEN="$arch_token"
  MACHO_SELECTED_ARCH="$(macho_normalize_arch "$arch_token")"
}

macho_write_metadata() {
  local metadata_path="$1"

  {
    echo "ORIGINAL_TARGET: $MACHO_ORIGINAL_TARGET"
    echo "ANALYSIS_TARGET: $MACHO_ANALYSIS_TARGET"
    echo "MACHO_UNIVERSAL: $MACHO_IS_UNIVERSAL"
    if [[ "$MACHO_IS_UNIVERSAL" == "yes" ]]; then
      echo "MACHO_ARCHES: $MACHO_ARCH_LIST"
      echo "MACHO_SELECTED_ARCH: $MACHO_SELECTED_ARCH"
      echo "MACHO_SELECTED_ARCH_TOKEN: $MACHO_SELECTED_ARCH_TOKEN"
    fi
  } > "$metadata_path"
}
