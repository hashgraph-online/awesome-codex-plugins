#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install-dep.sh <dependency>

Install or help install a dependency used by the Rust reverse-engineering skill.

Available dependencies:
  file           file type detection utility
  strings        strings extraction utility
  headers        readelf / llvm-readelf / otool style header tooling
  nm             nm / llvm-nm style symbol tooling
  disassembler   objdump / llvm-objdump / otool style disassembly tooling
  rustfilt       Rust symbol demangler
  debugger       gdb or lldb
  ghidra         Ghidra / analyzeHeadless
  ida            IDA Pro (manual)
  binaryninja    Binary Ninja (manual)

The script auto-detects your OS and package manager, installs directly when it can,
and prints exact manual instructions when it cannot.
EOF
  exit 0
}

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

DEP="$1"

OS="unknown"
PKG_MANAGER="none"
HAS_SUDO=false

case "$(uname -s)" in
  Darwin) OS="macos" ;;
  Linux) OS="linux" ;;
esac

if command -v brew >/dev/null 2>&1; then
  PKG_MANAGER="brew"
elif command -v apt-get >/dev/null 2>&1; then
  PKG_MANAGER="apt"
elif command -v dnf >/dev/null 2>&1; then
  PKG_MANAGER="dnf"
elif command -v pacman >/dev/null 2>&1; then
  PKG_MANAGER="pacman"
fi

if command -v sudo >/dev/null 2>&1; then
  HAS_SUDO=true
fi

info() {
  echo "[INFO] $*"
}

ok() {
  echo "[OK] $*"
}

fail() {
  echo "[FAIL] $*" >&2
}

manual() {
  echo "[MANUAL] $*" >&2
  exit 2
}

has_any() {
  for tool in "$@"; do
    if command -v "$tool" >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

add_to_profile() {
  local line="$1"
  local profile=""
  if [[ -f "$HOME/.zshrc" ]]; then
    profile="$HOME/.zshrc"
  elif [[ -f "$HOME/.bashrc" ]]; then
    profile="$HOME/.bashrc"
  elif [[ -f "$HOME/.profile" ]]; then
    profile="$HOME/.profile"
  fi

  if [[ -z "$profile" ]]; then
    info "Add this to your shell profile: $line"
    return 0
  fi

  if ! grep -qF "$line" "$profile" 2>/dev/null; then
    echo "$line" >> "$profile"
    info "Added to $profile: $line"
    info "Start a new shell or source $profile to apply it."
  fi
}

ensure_brew_formula_on_path() {
  local formula="$1"
  local prefix=""
  prefix="$(brew --prefix "$formula" 2>/dev/null || true)"
  if [[ -n "$prefix" && -d "$prefix/bin" ]]; then
    export PATH="$prefix/bin:$PATH"
    add_to_profile "export PATH=\"$prefix/bin:\$PATH\""
  fi
}

pkg_install() {
  local brew_pkg="$1"
  local apt_pkg="$2"
  local dnf_pkg="$3"
  local pacman_pkg="$4"

  case "$PKG_MANAGER" in
    brew)
      if [[ -z "$brew_pkg" ]]; then
        manual "No Homebrew formula configured for this dependency."
      fi
      info "Installing $brew_pkg via Homebrew..."
      brew install "$brew_pkg"
      ensure_brew_formula_on_path "$brew_pkg"
      ;;
    apt)
      if [[ -z "$apt_pkg" ]]; then
        manual "Run the manual installation for this dependency on apt-based systems."
      fi
      if [[ "$HAS_SUDO" != true ]]; then
        manual "Run: sudo apt-get update && sudo apt-get install -y $apt_pkg"
      fi
      info "Installing $apt_pkg via apt..."
      sudo apt-get update -qq
      sudo apt-get install -y -qq "$apt_pkg"
      ;;
    dnf)
      if [[ -z "$dnf_pkg" ]]; then
        manual "Run the manual installation for this dependency on dnf-based systems."
      fi
      if [[ "$HAS_SUDO" != true ]]; then
        manual "Run: sudo dnf install -y $dnf_pkg"
      fi
      info "Installing $dnf_pkg via dnf..."
      sudo dnf install -y "$dnf_pkg"
      ;;
    pacman)
      if [[ -z "$pacman_pkg" ]]; then
        manual "Run the manual installation for this dependency on pacman-based systems."
      fi
      if [[ "$HAS_SUDO" != true ]]; then
        manual "Run: sudo pacman -S --noconfirm $pacman_pkg"
      fi
      info "Installing $pacman_pkg via pacman..."
      sudo pacman -S --noconfirm "$pacman_pkg"
      ;;
    *)
      manual "No supported package manager found."
      ;;
  esac
}

install_xcode_cli_tools() {
  if [[ "$OS" != "macos" ]]; then
    manual "This helper is only available on macOS."
  fi

  if xcode-select -p >/dev/null 2>&1; then
    ok "Xcode Command Line Tools already installed"
    return 0
  fi

  if ! command -v xcode-select >/dev/null 2>&1; then
    manual "Install Xcode Command Line Tools manually from Apple Developer tools."
  fi

  info "Triggering Xcode Command Line Tools installer..."
  if xcode-select --install >/dev/null 2>&1; then
    manual "Finish the Xcode Command Line Tools installation, then rerun this script."
  fi

  manual "Run: xcode-select --install"
}

verify_any() {
  local dep_name="$1"
  shift
  if has_any "$@"; then
    ok "$dep_name is ready"
  else
    fail "$dep_name installation did not expose any expected command in PATH"
    exit 1
  fi
}

install_file_dep() {
  if has_any file; then
    ok "file already available"
    return 0
  fi

  case "$OS" in
    macos)
      pkg_install "file-formula" "" "" ""
      ;;
    linux)
      pkg_install "" "file" "file" "file"
      ;;
    *)
      manual "Install the 'file' utility manually."
      ;;
  esac

  verify_any "file" file
}

install_strings_dep() {
  if has_any strings llvm-strings gstrings; then
    ok "strings-compatible tool already available"
    return 0
  fi

  case "$OS" in
    macos)
      pkg_install "llvm" "" "" ""
      ;;
    linux)
      pkg_install "" "binutils" "binutils" "binutils"
      ;;
    *)
      manual "Install strings, llvm-strings, or gstrings manually."
      ;;
  esac

  verify_any "strings" strings llvm-strings gstrings
}

install_headers_dep() {
  if has_any readelf llvm-readelf greadelf otool; then
    ok "header-analysis tool already available"
    return 0
  fi

  case "$OS" in
    macos)
      if command -v otool >/dev/null 2>&1; then
        ok "otool already available"
        return 0
      fi
      if [[ "$PKG_MANAGER" == "brew" ]]; then
        pkg_install "llvm" "" "" ""
      else
        install_xcode_cli_tools
      fi
      ;;
    linux)
      pkg_install "" "binutils" "binutils" "binutils"
      ;;
    *)
      manual "Install readelf, llvm-readelf, greadelf, or otool manually."
      ;;
  esac

  verify_any "headers" readelf llvm-readelf greadelf otool
}

install_nm_dep() {
  if has_any nm llvm-nm gnm; then
    ok "symbol table tool already available"
    return 0
  fi

  case "$OS" in
    macos)
      if command -v nm >/dev/null 2>&1; then
        ok "nm already available"
        return 0
      fi
      if [[ "$PKG_MANAGER" == "brew" ]]; then
        pkg_install "llvm" "" "" ""
      else
        install_xcode_cli_tools
      fi
      ;;
    linux)
      pkg_install "" "binutils" "binutils" "binutils"
      ;;
    *)
      manual "Install nm, llvm-nm, or gnm manually."
      ;;
  esac

  verify_any "nm" nm llvm-nm gnm
}

install_disassembler_dep() {
  if has_any objdump llvm-objdump gobjdump otool; then
    ok "disassembler already available"
    return 0
  fi

  case "$OS" in
    macos)
      if command -v otool >/dev/null 2>&1; then
        ok "otool already available"
        return 0
      fi
      if [[ "$PKG_MANAGER" == "brew" ]]; then
        pkg_install "llvm" "" "" ""
      else
        install_xcode_cli_tools
      fi
      ;;
    linux)
      pkg_install "" "binutils" "binutils" "binutils"
      ;;
    *)
      manual "Install objdump, llvm-objdump, gobjdump, or otool manually."
      ;;
  esac

  verify_any "disassembler" objdump llvm-objdump gobjdump otool
}

install_rustfilt_dep() {
  if has_any rustfilt; then
    ok "rustfilt already available"
    return 0
  fi

  if command -v cargo >/dev/null 2>&1; then
    info "Installing rustfilt via cargo..."
    cargo install rustfilt
    export PATH="$HOME/.cargo/bin:$PATH"
    add_to_profile 'export PATH="$HOME/.cargo/bin:$PATH"'
    verify_any "rustfilt" rustfilt
    return 0
  fi

  manual "Install cargo first, then run: cargo install rustfilt"
}

install_debugger_dep() {
  if has_any gdb lldb; then
    ok "debugger already available"
    return 0
  fi

  case "$OS" in
    macos)
      install_xcode_cli_tools
      ;;
    linux)
      pkg_install "" "lldb" "lldb" "lldb"
      ;;
    *)
      manual "Install lldb or gdb manually."
      ;;
  esac

  verify_any "debugger" gdb lldb
}

install_ghidra_dep() {
  if has_any analyzeHeadless ghidraRun ghidra; then
    ok "Ghidra already available"
    return 0
  fi

  case "$PKG_MANAGER" in
    brew)
      pkg_install "ghidra" "" "" ""
      ;;
    dnf)
      pkg_install "" "" "ghidra" ""
      ;;
    *)
      manual "Install Ghidra manually from https://ghidra-sre.org/ or use Homebrew: brew install ghidra"
      ;;
  esac

  verify_any "ghidra" analyzeHeadless ghidraRun ghidra
}

install_ida_dep() {
  manual "Install IDA Pro manually from Hex-Rays, then ensure idat64 or ida64 is in PATH."
}

install_binaryninja_dep() {
  manual "Install Binary Ninja manually, then ensure the binaryninja launcher is in PATH."
}

case "$DEP" in
  file)
    install_file_dep
    ;;
  strings)
    install_strings_dep
    ;;
  headers)
    install_headers_dep
    ;;
  nm)
    install_nm_dep
    ;;
  disassembler)
    install_disassembler_dep
    ;;
  rustfilt)
    install_rustfilt_dep
    ;;
  debugger)
    install_debugger_dep
    ;;
  ghidra)
    install_ghidra_dep
    ;;
  ida)
    install_ida_dep
    ;;
  binaryninja)
    install_binaryninja_dep
    ;;
  *)
    fail "Unknown dependency: $DEP"
    usage
    ;;
esac
