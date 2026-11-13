# Render pipeline

Five commands turn the source into every format. Run them from the skill folder; each is deterministic and depends only on the bundled assets plus a headless browser.

Relative image paths resolve against the output directory, not the scratch directory: put every figure file in `$OUT` before step 4. A figure left beside the source renders a `false` entry in `images` and a blank box in every format.

## 1. Contents

- [1. Contents](#1-contents)
- [2. Find a renderer](#2-find-a-renderer)
- [3. The block](#3-the-block)
- [4. What each step produces](#4-what-each-step-produces)
- [5. Reading the check record](#5-reading-the-check-record)
- [6. When a command fails](#6-when-a-command-fails)
- [7. Sources](#sources)

## 2. Find a renderer

A Chromium-family browser in headless mode does HTML, PDF, and page images. Find one before authoring, so a machine without one is known up front.

```bash
RT="skills/hyper-report/assets/runtime"
for c in chrome-headless-shell chromium chromium-browser; do command -v "$c"; done
find "$HOME/Library/Caches/ms-playwright" "$HOME/.cache/ms-playwright" \
  -maxdepth 4 -type f -name 'chrome-headless-shell' -perm -u+x 2>/dev/null | sort -r | head -1
ls "/Applications/Chromium.app/Contents/MacOS/Chromium" \
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" 2>/dev/null
```

Set `BROWSER` to the first path that exists and is executable. If none exists, `md` is the only format available; report `BROWSER_MISSING` and do not install a browser mid-run.

JPEG needs `sips` (macOS) or `magick`/`convert`. DOCX needs `textutil` (macOS). Both are optional: without them, PNG and the other formats still work.

```bash
command -v sips magick convert textutil
```

## 3. The block

Set four variables and run the block. `SRC` is the authored source, `SLUG` is the output stem, `OUT` is the output directory, `THEME` is a theme name.

```bash
set -euo pipefail
SRC=".hyper/report/onboarding/report.md"
OUT=".hyper/report/onboarding"
SLUG="report"
THEME="civic"
RT="skills/hyper-report/assets/runtime"
BROWSER="$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/hyper-report.XXXXXX")

mkdir -p "$OUT" "$WORK"

# 1. frontmatter -> meta.tsv, body without frontmatter
awk -v out="$WORK" '
  BEGIN { split("title subtitle author date theme footer", keys, " ") }
  NR == 1 && $0 != "---" { body = 1 }
  body == 0 && $0 == "---" && NR > 1 { body = 1; next }
  body == 0 {
    pos = index($0, ":"); if (pos == 0) next
    key = substr($0, 1, pos - 1); val = substr($0, pos + 1)
    gsub(/^[ \t]+|[ \t]+$/, "", key); gsub(/^[ \t]+|[ \t]+$/, "", val)
    gsub(/^"|"$/, "", val)
    for (i in keys) if (key == keys[i]) { print keys[i] "\t" val > (out "/meta.tsv"); break }
    next
  }
  { print }
' "$SRC" > "$WORK/body.md"

meta() { awk -F '\t' -v k="$1" '$1 == k { print substr($0, length($1) + 2); exit }' "$WORK/meta.tsv" 2>/dev/null; }
TITLE=$(meta title);  TITLE=${TITLE:-$SLUG}
FOOTER=$(meta footer); FOOTER=${FOOTER:-$TITLE}
THEME=${THEME:-$(meta theme)}

# 2. markdown -> block HTML
awk -f "$RT/markdown.awk" "$WORK/body.md" > "$WORK/body.html"

# 3. assemble the canonical HTML
awk -v tpl="$RT/report.html" -v body="$WORK/body.html" -v css="$RT/report.css" \
    -v theme="$RT/themes/$THEME.css" -v js="$RT/report.js" \
    -v title="$TITLE" -v footerLeft="$FOOTER" -v footerRight="" \
    -f "$RT/assemble.awk" > "$OUT/$SLUG.html"
# render from the output directory so relative image paths resolve

# 4. read back the layout record
"$BROWSER" --headless --disable-gpu --no-sandbox --virtual-time-budget=40000 \
  --dump-dom "file://$OUT/$SLUG.html?check=1" > "$WORK/dom.html"
STATE=$(grep -o 'data-report-state="[^"]*"' "$WORK/dom.html" | head -1 \
  | sed -e 's/^data-report-state="//' -e 's/"$//' \
  -e 's/&quot;/"/g' -e 's/&amp;/\&/g' -e 's/&lt;/</g' -e 's/&gt;/>/g')
printf '%s\n' "$STATE" | jq .

# 5. PDF
"$BROWSER" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --virtual-time-budget=40000 --print-to-pdf="$OUT/$SLUG.pdf" "file://$OUT/$SLUG.html"

# 6. one PNG per page at 2x
PAGES=$(printf '%s' "$STATE" | jq -r .pages)
W=$(printf '%s' "$STATE" | jq -r .pageWidth)
H=$(printf '%s' "$STATE" | jq -r .pageHeight)
mkdir -p "$OUT/$SLUG"
i=1
while [ "$i" -le "$PAGES" ]; do
  "$BROWSER" --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=2 --window-size="$W,$H" \
    --virtual-time-budget=40000 \
    --screenshot="$OUT/$SLUG/$(printf '%s-%02d.png' "$SLUG" "$i")" \
    "file://$OUT/$SLUG.html?page=$i"
  i=$((i + 1))
done

# 7. JPEG from the PNGs, then DOCX from the HTML
for png in "$OUT/$SLUG"/*.png; do
  sips -s format jpeg -s formatOptions 90 "$png" --out "$OUT/$SLUG-jpg/$(basename "$png" .png).jpg" >/dev/null
done 2>/dev/null || true
textutil -convert docx "$OUT/$SLUG.html" -output "$OUT/$SLUG.docx" 2>/dev/null || true

echo "pages=$PAGES html=$OUT/$SLUG.html pdf=$OUT/$SLUG.pdf"
rm -rf "$WORK"
```

Step 7's two conversions are the only optional ones: a failure there removes one format, not the report. Guard them as shown rather than letting `set -e` abort the run.

## 4. What each step produces

| Step | Input | Output | Failure mode |
|---|---|---|---|
| 1 | `report.md` | `body.md`, `meta.tsv` | Frontmatter never closed: the whole file becomes the body |
| 2 | `body.md` | `body.html` | Empty output means the source is only frontmatter |
| 3 | block HTML + assets | `report.html` | A missing theme file leaves the theme placeholder empty |
| 4 | `report.html` | layout state JSON | No state means the runtime did not execute |
| 5 | `report.html` | `report.pdf` | Page count can disagree with the layout |
| 6 | `report.html?page=N` | `report-01.png`, … | A blank page means the page index is out of range |
| 7 | HTML, PNGs | `.docx`, `.jpg` | Missing converter removes that format only |

## 5. Reading the check record

The layout state is one JSON object:

```json
{"pages":3,"pageWidth":794,"pageHeight":1123,"overflow":[],"wide":[],
 "empty":[],"images":[{"src":"assets/chart.png","ok":true}],"toc":4,"words":1840}
```

| Field | Pass condition | Meaning of a failure |
|---|---|---|
| `pages` | ≥ 1 | Nothing paginated |
| `overflow` | `[]` | A block was clipped off a page; split it |
| `wide` | `[]` | A block exceeds the column; drop a column or shrink an image |
| `empty` | `[]` | An empty page was emitted; usually a stray `:::pagebreak` |
| `images[].ok` | all `true` | An image path is wrong or the file is missing |
| `toc` | matches the heading count | Fewer than expected means headings are nested in a block |

Verify the PDF agrees:

```bash
LC_ALL=C grep -a -o '/Count [0-9][0-9]*' "$OUT/$SLUG.pdf" | awk '{if ($2>m) m=$2} END{print m+0}'
```

That number must equal `pages`. A mismatch means the print engine re-laid-out the DOM, which happens when a page box is not exactly the `@page` size.

## 6. When a command fails

| Error | Cause | Fix |
|---|---|---|
| Empty `body.html` | Source is frontmatter only, or the frontmatter was never closed | Close the frontmatter with `---` |
| Empty `data-report-state` | The browser ran no script | Raise `--virtual-time-budget`; confirm the browser is Chromium-family |
| `pdfPages != pages` | Page box and `@page` disagree | Use the bundled `report.css` unchanged |
| A page image is white | Page index beyond `pages` | Loop to `pages`, not to a guessed number |
| `sips: no such file` | Not macOS and no ImageMagick | Drop JPG; PNG is unaffected |
| `textutil: command not found` | Not macOS | Drop DOCX and say so |

Never retry the same failing command twice. Read the produced artifact, since a failing check usually leaves an inspectable file.

## 7. Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| `--print-to-pdf`, `--screenshot`, `--dump-dom`, `--virtual-time-budget`, `--force-device-scale-factor`, `--hide-scrollbars` | <https://developer.chrome.com/docs/chromium/headless> |
| The PDF `/Count` entry as a page-count probe without a PDF library | This package's measurement on 2026-11-13; Chromium writes one `/Count` per page tree node |
| `sips -s format jpeg` and `textutil -convert docx` | <https://ss64.com/mac/sips.html>, <https://ss64.com/mac/textutil.html> |
| `mktemp -d` template portability across BSD and GNU | <https://man.openbsd.org/mktemp.1> |