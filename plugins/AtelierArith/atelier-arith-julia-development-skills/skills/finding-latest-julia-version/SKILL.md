---
name: finding-latest-julia-version
description: Use when you need the latest stable JuliaLang version number (e.g., to fill `VERSION=` in an install script) instead of hard-coding a value
---

# Finding the Latest Stable Julia Version

Hard-coding `VERSION=1.x.y` rots quickly. JuliaLang publishes machine-readable
metadata; query it directly.

## Preferred: official `versions.json`

This is the same source `juliaup` and the official installer use. Each release
carries a `stable: true|false` flag plus per-platform tarball URLs and SHA-256
hashes — useful both for picking a version and for verifying the download.

```sh
curl -fsSL https://julialang-s3.julialang.org/bin/versions.json \
  | jq -r 'to_entries
           | map(select(.value.stable))
           | map(.key)
           | sort_by(split(".") | map(tonumber? // 0))
           | last'
# → 1.12.6   (example, as of writing)
```

If `jq` is unavailable, use Python:

```sh
curl -fsSL https://julialang-s3.julialang.org/bin/versions.json \
  | python3 -c 'import sys, json
d = json.load(sys.stdin)
stable = [v for v, m in d.items() if m.get("stable")]
stable.sort(key=lambda s: tuple(int(x) for x in s.split("-")[0].split(".")))
print(stable[-1])'
```

To list the latest patch within a specific minor series (e.g., the newest 1.11.x):

```sh
curl -fsSL https://julialang-s3.julialang.org/bin/versions.json \
  | jq -r 'to_entries
           | map(select(.value.stable and (.key | startswith("1.11."))))
           | map(.key)
           | sort_by(split(".") | map(tonumber? // 0))
           | last'
```

## Fallback: GitHub Releases API

Use when the S3 endpoint is blocked but `api.github.com` is reachable. Note
that GitHub's "latest" tag follows GitHub release marking, not the JuliaLang
`stable` flag, so prefer `versions.json` when both work.

```sh
curl -fsSL https://api.github.com/repos/JuliaLang/julia/releases/latest \
  | jq -r .tag_name | sed 's/^v//'
# → 1.12.6
```

## Last resort: human page

Open <https://julialang.org/downloads/> and read the "Current stable release"
line. Only do this when no automated approach works; the page is HTML and
shape-changes break scrapers.

## Notes

- `versions.json` also gives you `files[].url` and `files[].sha256` per
  platform — use these to script a verified download instead of constructing
  the URL by hand.
- This skill returns a version *string*; the actual install steps live in
  [[installing-julia]].
