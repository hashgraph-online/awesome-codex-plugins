#!/bin/sh
# AgentAvow hook launcher. Runs one hook script with the first working Python 3:
# python3, then python, then the Windows launcher (py -3). Each is tried with a
# one-line version check first, because on Windows "python3" is often a Microsoft
# Store stub that exists but does not run. With no working Python, it prints nothing
# and exits 0 (fail-open): the session and the tool call go ahead as if the hook
# were not installed. Reads no environment settings and sends nothing.
script="$1"
[ -f "$script" ] || exit 0
for py in python3 python "py -3"; do
  if $py -c "import sys; sys.exit(sys.version_info[0] != 3)" </dev/null >/dev/null 2>&1; then
    exec $py "$script"
  fi
done
exit 0
