#!/usr/bin/env bash
# _lib.sh: helpers shared by the edit-pack recipes. Source it; do not run it.
#
# The recipes use the pinned CLIs from $B2M_EDIT_HOME (default ~/.brief2mp4/edit), never whatever
# older copy happens to be on the PATH. Works from the skill folder and from the installed copy,
# on macOS, Linux and Windows (Git Bash).

B2M_EDIT_HOME="${B2M_EDIT_HOME:-$HOME/.brief2mp4/edit}"
B2M_RECIPE="${B2M_RECIPE:-recipe}"

b2m_die() { printf '%s: %s\n' "$B2M_RECIPE" "$1" >&2; exit "${2:-1}"; }

b2m_need() { command -v "$1" >/dev/null 2>&1 || b2m_die "$1 not found. The skill's doctor script (scripts/doctor.sh) prints how to install it." 3; }

# b2m_cli <app folder>: path of the pinned CLI, for any of the three layouts (macOS, Linux bin/, Windows .exe).
b2m_cli() {
  local n="$1" c
  for c in "$B2M_EDIT_HOME/$n/$n-cli" "$B2M_EDIT_HOME/$n/bin/$n-cli" "$B2M_EDIT_HOME/$n/$n-cli.exe"; do
    if [[ -f "$c" ]]; then printf '%s' "$c"; return 0; fi
  done
  b2m_die "$n-cli is not installed in $B2M_EDIT_HOME. Install it with: bash <skill folder>/edit/install_edit.sh --components ${n%craft}" 3
}

# b2m_abs <path>: absolute path, then native form (C:/... under Git Bash) for the Windows .exe files.
b2m_abs() {
  local p="$1"
  case "$p" in /*|[A-Za-z]:*) ;; *) p="$PWD/$p" ;; esac
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$p"; else printf '%s' "$p"; fi
}

# b2m_str <text>: the text as a JSON string (quotes, backslashes, newlines escaped).
b2m_str() { node -p 'JSON.stringify(process.argv[1])' -- "$1"; }

# b2m_pick <js expression>: read the CLI's JSON-lines output on stdin as array L, print the expression.
b2m_pick() {
  node -e '
const L = require("fs").readFileSync(0, "utf8").split("\n").filter(s => s.trim().startsWith("{")).map(s => JSON.parse(s));
const v = (function (L) { return eval(process.argv[1]); })(L);
console.log(Array.isArray(v) ? v.join(" ") : v);' "$1"
}

# b2m_secs <file>: duration of a media file in seconds.
b2m_secs() { ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$1" | head -1; }

# b2m_workdir: a fresh temp folder, removed when the recipe exits (unless B2M_KEEP_WORK=1).
b2m_workdir() {
  B2M_WORK="$(mktemp -d)"
  if [[ "${B2M_KEEP_WORK:-0}" != 1 ]]; then trap 'rm -rf "${B2M_WORK:?}"' EXIT; fi
}

b2m_usage() { sed -n '2,/^set -/p' "$1" | sed '$d' | sed 's/^# \{0,1\}//'; }
