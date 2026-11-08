# Headless Recipes

> Tier 1 and tier 2 commands: one axis per attempt, every result written to a file so its size, markers, and digest can be checked.

## Contents

1. Plain Request
2. Client Fingerprint Impersonation
3. Structured Metadata
4. Reader
5. Media
6. Archive Copy (Tier 2)

## 1. Plain Request

```bash
mkdir -p .hyper/browsing/<slug>/attempts .hyper/browsing/<slug>/content
out=.hyper/browsing/<slug>/attempts/<n>.html
curl -sL --compressed -m 25 -o "$out" -w '%{http_code}\t%{size_download}\t%{url_effective}\n' \
  -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -H 'Accept-Language: ko-KR,ko;q=0.9,en;q=0.8' \
  "<URL>"
grep -o '<title>[^<]*' "$out" | head -1
```

Change one axis per retry: the URL variant, the user agent family (Safari, Safari iOS, Chrome, Chrome Android, Firefox), the referer (`-e "<scheme>://<host>/"` or a search-engine referer), or the device class. Never add `-b` cookies taken from a browser.

## 2. Client Fingerprint Impersonation

curl_cffi reproduces a browser's TLS and HTTP/2 fingerprint. Use it only when it is installed, or in a task-owned virtual environment that is removed afterwards.

```bash
if python3 -I -c 'import curl_cffi' 2>/dev/null; then
  PY=python3
else
  python3 -m venv .hyper/browsing/<slug>/venv &&
  .hyper/browsing/<slug>/venv/bin/pip install -q curl_cffi &&   # no pin: pip picks the newest wheel for this Python
  PY=.hyper/browsing/<slug>/venv/bin/python3
fi
"$PY" -I -c 'import curl_cffi; print(curl_cffi.__version__)'   # record this version in the report
"$PY" -I - "<URL>" safari .hyper/browsing/<slug>/attempts/<n>.html <<'EOF'
import sys
from curl_cffi import requests
url, target, path = sys.argv[1:4]
r = requests.get(url, impersonate=target, timeout=25, allow_redirects=True)
open(path, "wb").write(r.content)
print(r.status_code, len(r.content), r.url, sep="\t")
EOF
```

Impersonation families to rotate, one per attempt: `safari`, `safari_ios`, `chrome`, `chrome_android`, `firefox`. All five aliases ran on curl_cffi 0.13.0 under Python 3.9 on 2026-11-07. Do not pin a minimum version: recent releases (0.15 and later) ship wheels only for newer Python versions, so `curl_cffi>=0.15` fails on an older default interpreter. Version-specific target names (`chrome131`, `safari2601`) change between releases; use one only after checking the installed version's documentation.

## 3. Structured Metadata

When the body is real but the page is large or partial, extract the fields the request needs.

```bash
f=.hyper/browsing/<slug>/attempts/<n>.html
grep -o '<meta[^>]*property="og:[^"]*"[^>]*>' "$f"                     # Open Graph
grep -o '<link[^>]*rel="canonical"[^>]*>' "$f"                         # canonical URL (proof layer 4)
awk '/<script[^>]*application\/ld\+json/,/<\/script>/' "$f"            # JSON-LD blocks
grep -o '<link[^>]*type="application/\(rss\|atom\)+xml"[^>]*>' "$f"    # feed discovery
```

A JSON-LD `@type` of `Article`, `NewsArticle`, `Product`, or `VideoObject` with the expected name counts as positive proof.

## 4. Reader

A reader renders the page and returns text. Its result is provenance `reader`. Send no cookies or authorization to it.

```bash
curl -s -m 30 ${JINA_API_KEY:+-H "Authorization: Bearer $JINA_API_KEY"} "https://r.jina.ai/<URL>"
```

Observed 2026-11-07 from this repository's network: an anonymous request for `https://example.com` returned HTTP 200 with the page title. The upstream skill recorded anonymous access as refused (401); treat anonymous access as unreliable and record which one the run saw. A reader does not pass WAFs that block its own servers.

A reader's 200 is not evidence of content. On the same day a reader request for `https://www.crunchbase.com/organization/openai` ended 200 with 883 bytes, but the body was `Attention Required! | Cloudflare` plus a `Target URL returned error 403` warning. Check reader output with the proof layers in `rules/evidence-and-report.md` §2 and judge a challenge marker as `challenge`.

## 5. Media

```bash
yt-dlp --dump-json --skip-download "<URL>" > .hyper/browsing/<slug>/content/media.json
yt-dlp --write-sub --write-auto-sub --sub-lang 'ko,en' --skip-download \
  -o '.hyper/browsing/<slug>/content/%(id)s' "<URL>"
```

yt-dlp covers more than a thousand media sites; release 2026.10.26 was current on PyPI on 2026-11-07. When it is missing, mark the media extractor `skipped` or install it into the task-owned virtual environment. Download the media file itself only under the gate in `rules/access-policy.md` §4.

## 6. Archive Copy (Tier 2)

```bash
curl -s -m 20 "https://archive.org/wayback/available?url=<URL>"
# -> archived_snapshots.closest.url and .timestamp; fetch that URL, keep the timestamp
# --compressed is required: an archived raw (id_) response arrives gzip-encoded, and without it
# the binary bytes are written to the file while every size check still passes
curl -sL --compressed -m 30 -o .hyper/browsing/<slug>/attempts/<n>.html "<snapshot url>"
curl -s -m 20 "https://web.archive.org/cdx/search/cdx?url=<URL>&limit=-5&output=json"   # list recent snapshots
curl -s -m 20 "https://web.archive.org/cdx/search/cdx?url=<URL>&output=json&filter=statuscode:200&limit=-1"  # newest 200 snapshot timestamp
# the id_ suffix serves the original response without the archive toolbar and URL rewriting
#   https://web.archive.org/web/<timestamp>id_/<URL>
for d in archive.ph archive.md archive.li archive.is; do                                 # other archive, rotating hosts
  curl -s -m 15 -o /dev/null -w "$d\t%{http_code}\n" "https://$d/newest/<URL>"
done
```

Probe results on 2026-11-07 from this repository's network:

| Route | Result |
|---|---|
| Wayback availability API | 200, returned a snapshot URL and timestamp |
| Wayback CDX API | 200 with JSON rows (the upstream skill recorded 503 in 2026-08; it has recovered for now) |
| Wayback `web/<ts>/<URL>` (rewritten) | Unstable: one request returned 403 with a `Attention Required! \| Cloudflare` page, and the same URL minutes later returned 200 with the real page. Judge each body; on a challenge body, change one axis (the raw `id_` path) instead of resending the same request |
| Wayback `web/<ts>id_/<URL>` with `--compressed` | 200, 148,648 bytes, title `OpenAI - Crunchbase Company Profile & Funding`, 13,801 characters of body. A real copy |
| Wayback `web/<ts>id_/<URL>` without `--compressed` | 200 and 148,648 bytes, but gzip binary content (the raw view replays the stored `Content-Encoding: gzip`); size checks pass, so a text check is required |
| archive.today hosts (`.ph`, `.md`, `.li`, `.is`) | no response (connection failed) from this network |
| Google web cache | search interstitial, not a cache |

Check every archive body with the proof layers: archive hosts also serve rate-limit pages with a body, and SPA snapshots are often empty shells. Confirm the file is text first (`file <path>`, or a failed UTF-8 decode); when it is binary, change one axis (the raw `id_` path, `--compressed`) and fetch again.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The request grid, curl_cffi impersonation, reader, media extractor, and archive order | The `ultimate-browsing` skill in `code-yeongyu/oh-my-openagent` (branch `dev`), read 2026-11-07 |
| curl_cffi 0.17.0 and yt-dlp 2026.10.26 as current releases | <https://pypi.org/pypi/curl-cffi/json> and <https://pypi.org/pypi/yt-dlp/json>, read 2026-11-07 |
| Endpoint probe rows | requests from this repository's network on 2026-11-07; results depend on the network and change without notice |
| Wayback availability and CDX APIs | <https://archive.org/help/wayback_api.php> |
