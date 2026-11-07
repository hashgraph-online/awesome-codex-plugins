"""Private per-user cache for short-lived API access tokens.

A token is trusted only when its file is a regular file this user owns that
nobody else can read, so another local user cannot plant or read a token.
"""

import json
import os
import stat
import sys
import tempfile
import time


def cache_dir():
    """Per-user cache folder, created with mode 0700 when missing."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Local")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.join(
            os.path.expanduser("~"), ".cache")
    path = os.path.join(base, "kicad-happy")
    os.makedirs(path, mode=0o700, exist_ok=True)
    return path


def load_token(name, client_id):
    """Cached token for `client_id`, or None. Never raises."""
    try:
        path = os.path.join(cache_dir(), name + ".json")
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            return None
        if sys.platform != "win32" and (
                st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) & 0o077):
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        token = data.get("token")
        if (data.get("client_id") == client_id and isinstance(token, str) and token
                and data.get("expires_at", 0) > time.time()):
            return token
    except (OSError, ValueError, AttributeError, TypeError, RecursionError):
        pass
    return None


def store_token(name, client_id, token, ttl_s):
    """Write the token with mode 0600 from creation. Best effort."""
    tmp = None
    try:
        folder = cache_dir()
        fd, tmp = tempfile.mkstemp(dir=folder, prefix=f".{name}.", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            os.chmod(tmp, 0o600)
            json.dump({"client_id": client_id, "token": token,
                       "expires_at": time.time() + ttl_s}, f)
        os.replace(tmp, os.path.join(folder, name + ".json"))
        tmp = None
    except OSError:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass
