"""Entry point: `py -3 -m agent_bridge ...` (cwd = examples/python) or
`py -3 <skill>/examples/python/agent_bridge ...` from anywhere (hooks)."""
import os
import sys

if not __package__:                      # run as a directory/script: make the package importable
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent_bridge.cli import main
else:
    from .cli import main

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

main()
