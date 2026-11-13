# 렌더 파이프라인

명령 다섯 개가 원본을 모든 형식으로 바꾼다. 스킬 폴더에서 실행하며, 각 명령은 결정적이고 패키지에 포함된 자산과 헤드리스 브라우저에만 의존한다.

상대 그림 경로는 임시 폴더가 아니라 출력 디렉터리 기준으로 풀린다. 그림 파일은 4단계 전에 모두 `$OUT`에 둔다. 원본 옆에 둔 그림은 `images`에 `false`로 잡히고 모든 형식에서 빈 상자로 나온다.

## 1. 목차

- [1. 목차](#1-목차)
- [2. 렌더러 찾기](#2-렌더러-찾기)
- [3. 실행 블록](#3-실행-블록)
- [4. 각 단계가 만드는 것](#4-각-단계가-만드는-것)
- [5. 점검 기록 읽기](#5-점검-기록-읽기)
- [6. 명령이 실패할 때](#6-명령이-실패할-때)
- [7. Sources](#sources)

## 2. 렌더러 찾기

Chromium 계열 브라우저를 헤드리스 모드로 쓰면 HTML, PDF, 페이지 이미지를 모두 만들 수 있다. 작성 전에 하나를 찾아 두어, 없는 기기를 미리 알 수 있게 한다.

```bash
RT="skills/hyper-report/assets/runtime"
for c in chrome-headless-shell chromium chromium-browser; do command -v "$c"; done
find "$HOME/Library/Caches/ms-playwright" "$HOME/.cache/ms-playwright" \
  -maxdepth 4 -type f -name 'chrome-headless-shell' -perm -u+x 2>/dev/null | sort -r | head -1
ls "/Applications/Chromium.app/Contents/MacOS/Chromium" \
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" 2>/dev/null
```

존재하고 실행 가능한 첫 경로를 `BROWSER`로 정한다. 하나도 없으면 쓸 수 있는 형식은 `md`뿐이다. `BROWSER_MISSING`을 보고하고, 작업 도중에 브라우저를 설치하지 않는다.

JPEG에는 `sips`(macOS)나 `magick`/`convert`가 필요하다. DOCX에는 `textutil`(macOS)이 필요하다. 둘 다 선택 사항이므로, 없어도 PNG와 나머지 형식은 동작한다.

```bash
command -v sips magick convert textutil
```

## 3. 실행 블록

변수 네 개를 정하고 블록을 실행한다. `SRC`는 작성한 원본, `SLUG`은 출력 파일 이름의 뿌리, `OUT`은 출력 디렉터리, `THEME`은 테마 이름이다.

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
# 상대 그림 경로가 풀리도록 출력 디렉터리의 HTML로 렌더한다

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

7단계의 변환 두 개만 선택 사항이다. 여기서 실패하면 형식 하나가 빠질 뿐 보고서는 남는다. `set -e`가 실행을 중단하지 않도록 위와 같이 보호한다.

## 4. 각 단계가 만드는 것

| 단계 | 입력 | 출력 | 실패 방식 |
|---|---|---|---|
| 1 | `report.md` | `body.md`, `meta.tsv` | frontmatter를 닫지 않으면 파일 전체가 본문이 된다 |
| 2 | `body.md` | `body.html` | 출력이 비면 원본이 frontmatter뿐이다 |
| 3 | 블록 HTML + 자산 | `report.html` | 테마 파일이 없으면 테마 자리표시자가 빈 채로 남는다 |
| 4 | `report.html` | 레이아웃 상태 JSON | 상태가 없으면 런타임이 실행되지 않았다 |
| 5 | `report.html` | `report.pdf` | 페이지 수가 레이아웃과 어긋날 수 있다 |
| 6 | `report.html?page=N` | `report-01.png`, … | 빈 페이지는 페이지 번호가 범위를 벗어났다는 뜻이다 |
| 7 | HTML, PNG | `.docx`, `.jpg` | 변환기가 없으면 그 형식만 빠진다 |

## 5. 점검 기록 읽기

레이아웃 상태는 JSON 객체 하나다.

```json
{"pages":3,"pageWidth":794,"pageHeight":1123,"overflow":[],"wide":[],
 "empty":[],"images":[{"src":"assets/chart.png","ok":true}],"toc":4,"words":1840}
```

| 필드 | 통과 조건 | 실패의 의미 |
|---|---|---|
| `pages` | 1 이상 | 페이지가 하나도 나뉘지 않았다 |
| `overflow` | `[]` | 블록이 페이지 밖으로 잘렸다. 블록을 나눈다 |
| `wide` | `[]` | 블록이 열 폭을 넘는다. 열을 빼거나 이미지를 줄인다 |
| `empty` | `[]` | 빈 페이지가 나왔다. 대개 잘못 놓인 `:::pagebreak`가 원인이다 |
| `images[].ok` | 모두 `true` | 이미지 경로가 틀렸거나 파일이 없다 |
| `toc` | 제목 수와 일치 | 예상보다 적으면 제목이 블록 안에 중첩돼 있다 |

PDF가 같은지 확인한다.

```bash
LC_ALL=C grep -a -o '/Count [0-9][0-9]*' "$OUT/$SLUG.pdf" | awk '{if ($2>m) m=$2} END{print m+0}'
```

이 수치는 `pages`와 같아야 한다. 다르면 인쇄 엔진이 DOM을 다시 배치한 것이며, 페이지 상자가 `@page` 크기와 정확히 같지 않을 때 생긴다.

## 6. 명령이 실패할 때

| 오류 | 원인 | 고치기 |
|---|---|---|
| `body.html`이 빔 | 원본이 frontmatter뿐이거나 frontmatter를 닫지 않았다 | `---`로 frontmatter를 닫는다 |
| `data-report-state`가 빔 | 브라우저가 스크립트를 실행하지 않았다 | `--virtual-time-budget`을 늘린다. 브라우저가 Chromium 계열인지 확인한다 |
| `pdfPages != pages` | 페이지 상자와 `@page`가 어긋난다 | 포함된 `report.css`를 고치지 않고 쓴다 |
| 페이지 이미지가 하얗다 | 페이지 번호가 `pages`를 넘었다 | 짐작한 수가 아니라 `pages`까지 반복한다 |
| `sips: no such file` | macOS가 아니고 ImageMagick도 없다 | JPG를 포기한다. PNG는 영향받지 않는다 |
| `textutil: command not found` | macOS가 아니다 | DOCX를 포기하고 그렇게 밝힌다 |

같은 실패 명령을 두 번 재시도하지 않는다. 실패한 점검은 보통 살펴볼 수 있는 파일을 남기므로, 만들어진 산출물을 읽는다.

## 7. Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| `--print-to-pdf`, `--screenshot`, `--dump-dom`, `--virtual-time-budget`, `--force-device-scale-factor`, `--hide-scrollbars` | <https://developer.chrome.com/docs/chromium/headless> |
| PDF 라이브러리 없이 페이지 수를 재는 수단으로서의 PDF `/Count` 항목 | 이 패키지의 2026-11-13 측정. Chromium은 페이지 트리 노드마다 `/Count`를 하나 쓴다 |
| `sips -s format jpeg`와 `textutil -convert docx` | <https://ss64.com/mac/sips.html>, <https://ss64.com/mac/textutil.html> |
| BSD와 GNU에 걸친 `mktemp -d` 템플릿 이식성 | <https://man.openbsd.org/mktemp.1> |