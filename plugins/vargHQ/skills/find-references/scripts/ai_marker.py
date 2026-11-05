#!/usr/bin/env python3
"""Byte-scan files for AI provenance markers. A hit rejects. A miss proves nothing.

  python3 -I ai_marker.py <file-or-folder> [more ...]

For each file, prints the markers found in its raw bytes:

  REJECT  <path>  trainedAlgorithmicMedia, SynthID    an AI marker is present: label it AI, Never board only
  READ    <path>  c2pa                                a Content Credentials manifest with no AI marker: read it
  miss    <path>                                      no verdict: treat provenance as still unproven

It is a string check, not signature validation. Any re-encode, resize or platform upload can erase every marker, so
a web copy that reads clean may still be generated. Prove human origin from records (see references/never.md).

c2pa alone gets READ and not REJECT because Content Credentials are a general provenance format, not an AI label.
Open the manifest at https://verify.contentauthenticity.org/ (a person uploads the file) and reject if it names a
generator.

Exit code: 1 if any file is REJECT, 2 if any path could not be read, otherwise 0. Standard library only.
"""
import os
import sys

AI_MARKERS = [
    "trainedAlgorithmicMedia",  # IPTC digital source type
    "compositeWithTrainedAlgorithmicMedia",
    "SynthID",
    "OpenAI",
    "Made with Google AI",
]
MANIFEST_MARKERS = ["c2pa"]
CHUNK = 1 << 20


def scan(path):
    """Return the markers present in a file. Reads in chunks, so large videos are fine."""
    wanted = {m: m.encode() for m in AI_MARKERS + MANIFEST_MARKERS}
    overlap = max(len(b) for b in wanted.values()) - 1
    found, tail = set(), b""
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                return found
            window = tail + chunk
            found.update(name for name, raw in wanted.items() if name not in found and raw in window)
            tail = window[-overlap:]


def walk(paths):
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs.sort()
                for name in sorted(files):
                    if not name.startswith("."):
                        yield os.path.join(root, name)
        else:
            yield path


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    rejected = unreadable = False
    for path in walk(sys.argv[1:]):
        try:
            found = scan(path)
        except OSError as err:
            unreadable = True
            print(f"ERROR   {path}  {err.strerror}")
            continue
        markers = [m for m in AI_MARKERS + MANIFEST_MARKERS if m in found]
        if any(m in found for m in AI_MARKERS):
            rejected = True
            print(f"REJECT  {path}  {', '.join(markers)}")
        elif markers:
            print(f"READ    {path}  {', '.join(markers)}")
        else:
            print(f"miss    {path}")
    sys.exit(1 if rejected else 2 if unreadable else 0)


if __name__ == "__main__":
    main()
