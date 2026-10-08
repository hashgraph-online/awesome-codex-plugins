#!/bin/sh

set -eu

case "$0" in
  /*) script_path=$0 ;;
  *) script_path=$PWD/$0 ;;
esac
script_dir=$(CDPATH= cd "${script_path%/*}" && pwd) || exit 1
command -v node >/dev/null 2>&1 || {
  printf '%s\n' 'ERROR: Node.js 20 or newer is required.' >&2
  exit 1
}
exec node "$script_dir/../control-plane/open-console.mjs" "$@"
