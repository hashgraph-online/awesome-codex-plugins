#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$base/node-runtime.sh"
node_binary=$(goal_progress_resolve_node)
exec "$node_binary" "$base/goal-progress.cjs" "$@"
