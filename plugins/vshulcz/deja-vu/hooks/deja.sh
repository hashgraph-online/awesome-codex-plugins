#!/bin/sh
# Bridges Codex's hooks to the deja binary.
#
# The plugin can be installed before deja itself is, so a missing binary must
# not look like a broken hook: we say once, through the hook's own JSON, how to
# get it, and otherwise stay silent. Exit status is always 0 — a hook that fails
# is a hook that interrupts the user.
set -u

find_deja() {
	if [ -n "${DEJA_BIN:-}" ] && [ -x "${DEJA_BIN}" ]; then
		printf '%s' "$DEJA_BIN"
		return
	fi
	if command -v deja >/dev/null 2>&1; then
		command -v deja
		return
	fi
	for candidate in \
		"$HOME/.local/bin/deja" \
		"/opt/homebrew/bin/deja" \
		"/usr/local/bin/deja" \
		"$HOME/go/bin/deja"; do
		if [ -x "$candidate" ]; then
			printf '%s' "$candidate"
			return
		fi
	done
}

# `deja install codex-auto` writes the same SessionStart hook into Codex's own
# hooks.json. Codex runs both files, so without this the digest arrives twice —
# and the installer's copy is the one `deja install` keeps current.
HOOKS="${CODEX_HOME:-$HOME/.codex}/hooks.json"
# The installer records an absolute path to the binary, so match the
# subcommand rather than a bare `deja hook-`.
if [ -f "$HOOKS" ] && grep -qE 'deja[^"]*hook-(context|prompt|precompact|tool)' "$HOOKS" 2>/dev/null; then
	cat >/dev/null 2>&1 || true
	exit 0
fi

DEJA=$(find_deja)

if [ -z "${DEJA:-}" ]; then
	# Drain stdin so Codex never blocks on the pipe.
	cat >/dev/null 2>&1 || true
	if [ "${1:-}" = "hook-context" ]; then
		printf '{"systemMessage":"the deja-vu plugin is installed but the deja binary is not on PATH — install it with: brew install deja-vu"}\n'
	fi
	exit 0
fi

exec "$DEJA" "$@"
