#!/usr/bin/env python3
"""Post a JS file to figma_execute through the local daemon. Usage: fx.py <file.js> [timeout_ms]

The daemon port comes from HTTP_PORT (default 8791), the same variable daemon.mjs reads.
The bearer token comes from the file daemon.mjs writes at boot,
<state-dir>/mcp-direct-<HTTP_PORT>.token, where <state-dir> is FIGMA_MAXXING_STATE_DIR
(default ~/.config/figma-maxxing).
"""
import json, os, sys, urllib.error, urllib.request
path = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
port = os.environ.get('HTTP_PORT') or '8791'
state_dir = os.environ.get('FIGMA_MAXXING_STATE_DIR') or os.path.join(os.path.expanduser('~'), '.config', 'figma-maxxing')
token_file = os.path.join(state_dir, f'mcp-direct-{port}.token')
try:
    token = open(token_file, encoding='utf-8').read().strip()
except FileNotFoundError:
    sys.exit(f'no daemon token at {token_file}: start daemon.mjs with the same HTTP_PORT and FIGMA_MAXXING_STATE_DIR')
code = open(path, encoding='utf-8').read()
req = urllib.request.Request(f'http://127.0.0.1:{port}',
    data=json.dumps({"name": "figma_execute", "arguments": {"code": code, "timeout": timeout}}).encode(),
    headers={'content-type': 'application/json', 'authorization': f'Bearer {token}'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit(f'daemon refused the call: HTTP {e.code} {e.read().decode(errors="replace")[:300]}')
except urllib.error.URLError as e:
    sys.exit(f'daemon not reachable: {e.reason}. Is daemon.mjs running on this HTTP_PORT?')
for c in r.get('content', [{"type": "text", "text": json.dumps(r)}]):
    print(c.get('text', ''))
