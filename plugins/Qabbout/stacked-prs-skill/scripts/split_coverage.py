#!/usr/bin/env python3
"""Compare Git tree entries rather than only file contents."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def git(*args):
    result = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or "git command failed")
    return result.stdout


def resolve(name, remote, local_first=False):
    candidates = [f"refs/remotes/{remote}/{name}", f"refs/heads/{name}"]
    if local_first:
        candidates.reverse()
    if name.startswith("refs/") or name.startswith(remote + "/"):
        candidates = [name]
    for candidate in [*candidates, name]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--end-of-options", candidate + "^{commit}"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return result.stdout.decode().strip()
    raise RuntimeError(f"no branch or commit named {name!r}")


def tree(commit):
    entries = {}
    for record in git("ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if record:
            metadata, path = record.split(b"\t", 1)
            entries[path] = tuple(metadata.decode().split())  # mode, type, object ID
    return entries


def changed(before, after):
    return set(filter(None, git("diff", "--name-only", "--no-renames", "-z", before, after).split(b"\0")))


def display(path):
    value = path.decode("utf-8", errors="backslashreplace")
    return json.dumps(value, ensure_ascii=False) if any(ord(c) < 32 or ord(c) == 127 for c in value) else value


def merged_entry(original, current, final):
    """Return an entry, 'conflict', or 'decide' for changes on both sides."""
    if current == final:
        return current
    if current is None or final is None:
        return "decide"
    # Do not text-merge symlinks, gitlinks, or type changes.
    if any(e and (e[1] != "blob" or e[0] not in ("100644", "100755")) for e in (original, current, final)):
        return "conflict"
    old_mode = original[0] if original else None
    if current[0] == final[0]:
        mode = current[0]
    elif current[0] == old_mode:
        mode = final[0]
    elif final[0] == old_mode:
        mode = current[0]
    else:
        return "conflict"
    with tempfile.TemporaryDirectory(prefix="stacked-prs-merge-") as directory:
        paths = [Path(directory) / name for name in ("current", "original", "final")]
        for path, entry in zip(paths, (current, original, final)):
            path.write_bytes(git("cat-file", "blob", entry[2]) if entry else b"")
        result = subprocess.run(["git", "merge-file", "-p", *map(str, paths)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            return "conflict"
        oid = subprocess.run(["git", "hash-object", "--stdin"], input=result.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.decode().strip()
        return (mode, "blob", oid)


def main():
    parser = argparse.ArgumentParser(description="Check file content, mode, and type coverage of a PR split. Does not change source files or push.")
    parser.add_argument("-r", dest="remote", default="origin", help="remote (default: origin)")
    parser.add_argument("-n", action="store_true", help="skip fetch")
    parser.add_argument("-v", action="store_true", help="list each file's first owning slice")
    parser.add_argument("-i", action="store_true", help="skip files changed on the base since the fork; reduces coverage")
    parser.add_argument("base")
    parser.add_argument("reference")
    parser.add_argument("slices", nargs="+")
    args = parser.parse_args()
    git("rev-parse", "--git-dir")
    if not args.n:
        git("fetch", "-q", "--", args.remote)
    base = resolve(args.base, args.remote)
    reference = resolve(args.reference, args.remote)
    # Slices are commonly checked before pushing. Never silently inspect an older remote copy.
    slices = [resolve(name, args.remote, local_first=True) for name in args.slices]
    fork = git("merge-base", base, reference).decode().strip()
    original, current, final = map(tree, (fork, base, reference))
    refs, moved = changed(fork, reference), changed(fork, base)
    merged = {p: merged_entry(original.get(p), current.get(p), final.get(p)) for p in refs & moved}
    trees = [tree(commit) for commit in slices]
    counts = [0] * len(slices)
    issues = dict.fromkeys(("missing", "intermediate", "reverts-base", "check", "decide", "extra"), 0)
    skipped = 0
    print(f"base {args.base} ({base[:12]}), reference {args.reference} ({reference[:12]}), fork point {fork[:12]}")
    for name, commit in zip(args.slices, slices):
        print(f"slice {name}: {commit[:12]} (local branch preferred; use {args.remote}/<branch> explicitly for remote)")
    for path in sorted(refs):
        if args.i and path in moved:
            skipped += 1
            continue
        old, now, fin, mrg = original.get(path), current.get(path), final.get(path), merged.get(path)
        owner, how, intermediate = None, "", []
        for index, entries in enumerate(trees):
            entry = entries.get(path)
            if entry == fin or (isinstance(mrg, tuple) and entry == mrg):
                if owner is None:
                    owner, how = index, "final" if entry == fin else "merged"
            elif entry != old and entry != now:
                intermediate.append(index + 1)
        label = display(path)
        if owner is None and mrg == "decide":
            issues["decide"] += 1
            print(f"DECIDE\t{label}\t(one side deleted it and the other changed it)")
            continue
        if owner is None and mrg == "conflict" and intermediate:
            owner, how = intermediate[0] - 1, "hand"
            intermediate = []
            issues["check"] += 1
            print(f"CHECK\tslice {owner + 1}\t{label}\t(check the hand merge by eye)")
        if owner is None:
            issues["missing"] += 1
            print(f"MISSING\t{label}")
        else:
            counts[owner] += 1
            if args.v:
                print(f"slice {owner + 1}\t{label}\t({how})")
            if how == "final" and path in moved and now != old and now != fin:
                issues["reverts-base"] += 1
                print(f"REVERTS-BASE\tslice {owner + 1}\t{label}")
        if intermediate:
            issues["intermediate"] += 1
            print(f"INTERMEDIATE\t{label}\t(slices {' '.join(map(str, intermediate))})")
    for index, commit in enumerate(slices):
        ancestor = git("merge-base", base, commit).decode().strip()
        for path in sorted(changed(ancestor, commit) - refs):
            issues["extra"] += 1
            print(f"EXTRA\tslice {index + 1}\t{display(path)}")
    print(f"reference changes {len(refs)} file(s); checked {len(refs) - skipped}; skipped {skipped}")
    for index, count in enumerate(counts):
        print(f"  slice {index + 1}  {args.slices[index]}: first final version of {count} file(s)")
        if not count:
            print(f"  NOTE: slice {index + 1} owns no file of the reference")
    print(", ".join(f"{name}: {count}" for name, count in issues.items()))
    return int(any(issues.values()))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
