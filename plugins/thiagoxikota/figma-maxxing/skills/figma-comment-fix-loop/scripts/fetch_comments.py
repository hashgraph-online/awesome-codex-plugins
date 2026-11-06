#!/usr/bin/env python3
"""Save the raw comments of one Figma file to a JSON file.

Usage: python3 fetch_comments.py <fileKey> [output.json]

Reads the personal access token from the FIGMA_ACCESS_TOKEN environment
variable and sends it only to api.figma.com. The token is never printed,
logged or written to disk. Standard library only.

The output holds commenter handles and avatar URLs: keep it out of git.

Exit codes:
  0  comments saved
  1  the Figma API answered with an HTTP error (the first 300 bytes of the
     response body are printed, never the headers)
  2  usage error, or FIGMA_ACCESS_TOKEN is not set
  3  network error or timeout: no answer from api.figma.com
  4  the answer was not a JSON object; nothing was written
"""
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.request

API = "https://api.figma.com/v1/files/{key}/comments"
FILE_KEY = re.compile(r"^[0-9A-Za-z]{10,128}$")
TIMEOUT_S = 30
BODY_PREVIEW = 300


def preview(raw):
    """The first BODY_PREVIEW bytes of a response body, as one printable line."""
    text = raw[:BODY_PREVIEW].decode("utf-8", errors="replace")
    return " ".join(text.split()) or "(empty body)"


def main(argv):
    if len(argv) not in (2, 3) or not FILE_KEY.match(argv[1]):
        print("usage: fetch_comments.py <fileKey> [output.json]", file=sys.stderr)
        return 2
    token = os.environ.get("FIGMA_ACCESS_TOKEN", "").strip()
    if not token:
        print("FIGMA_ACCESS_TOKEN is not set in this shell. Export it, then run again.", file=sys.stderr)
        return 2
    out = argv[2] if len(argv) == 3 else "comments-raw.json"
    req = urllib.request.Request(API.format(key=argv[1]), headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as err:
        hints = {
            403: "the token lacks the comments scope, or it cannot see this file",
            404: "the file belongs to an account this token cannot read; ask the user to paste the comments",
            429: "rate limited; wait before retrying and do not loop",
        }
        try:
            body = err.read(BODY_PREVIEW)
        except (OSError, ValueError, AttributeError):
            body = b""
        print(f"Figma API returned {err.code}: {hints.get(err.code, 'see the body below')}", file=sys.stderr)
        print(f"Response body (first {BODY_PREVIEW} bytes): {preview(body)}", file=sys.stderr)
        return 1
    except urllib.error.URLError as err:
        if isinstance(err.reason, (TimeoutError, socket.timeout)):
            print(f"Timeout: api.figma.com did not answer within {TIMEOUT_S} s. Check the network, then run again once.", file=sys.stderr)
        else:
            print(f"Network error: {err.reason}", file=sys.stderr)
        return 3
    except (TimeoutError, socket.timeout):
        print(f"Timeout: api.figma.com stopped answering within {TIMEOUT_S} s. Run again once; do not loop.", file=sys.stderr)
        return 3
    try:
        data = json.loads(raw)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        print(f"The answer was not a JSON object, so nothing was written. First {BODY_PREVIEW} bytes: {preview(raw)}", file=sys.stderr)
        return 4
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    comments = data.get("comments", [])
    open_count = sum(1 for c in comments if not c.get("resolved_at"))
    print(f"{len(comments)} comments saved to {out} ({open_count} open)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
