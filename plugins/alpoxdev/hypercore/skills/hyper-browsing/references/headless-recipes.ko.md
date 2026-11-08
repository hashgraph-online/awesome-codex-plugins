# 헤드리스 명령

> Tier 1과 tier 2 명령입니다. 시도마다 축 하나만 바꾸고, 모든 결과를 파일로 남겨 크기·표식·다이제스트를 검사합니다.

## 목차

1. 평범한 요청
2. 클라이언트 지문 위장
3. 구조화 메타데이터
4. 리더
5. 미디어
6. 아카이브 사본(Tier 2)

## 1. 평범한 요청

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

재시도마다 축 하나만 바꿉니다. URL 변형, 사용자 에이전트 계열(Safari, Safari iOS, Chrome, Chrome Android, Firefox), referer(`-e "<scheme>://<host>/"` 또는 검색 엔진 referer), 기기 종류입니다. 브라우저에서 가져온 쿠키를 `-b`로 더하지 않습니다.

## 2. 클라이언트 지문 위장

curl_cffi는 브라우저의 TLS와 HTTP/2 지문을 재현합니다. 이미 설치됐을 때, 또는 끝나면 지우는 작업 전용 가상 환경에서만 씁니다.

```bash
if python3 -I -c 'import curl_cffi' 2>/dev/null; then
  PY=python3
else
  python3 -m venv .hyper/browsing/<slug>/venv &&
  .hyper/browsing/<slug>/venv/bin/pip install -q curl_cffi &&   # 버전 고정 없음: pip가 이 Python에 맞는 최신 wheel을 고른다
  PY=.hyper/browsing/<slug>/venv/bin/python3
fi
"$PY" -I -c 'import curl_cffi; print(curl_cffi.__version__)'   # 이 버전을 보고서에 기록한다
"$PY" -I - "<URL>" safari .hyper/browsing/<slug>/attempts/<n>.html <<'EOF'
import sys
from curl_cffi import requests
url, target, path = sys.argv[1:4]
r = requests.get(url, impersonate=target, timeout=25, allow_redirects=True)
open(path, "wb").write(r.content)
print(r.status_code, len(r.content), r.url, sep="\t")
EOF
```

시도마다 하나씩 돌릴 위장 계열: `safari`, `safari_ios`, `chrome`, `chrome_android`, `firefox`. 2026-11-07에 Python 3.9의 curl_cffi 0.13.0에서 다섯 별칭이 모두 동작했습니다. 최소 버전을 고정하지 않습니다. 최근 판(0.15 이후)은 새 Python용 wheel만 내놓아서 오래된 기본 인터프리터에서는 `curl_cffi>=0.15`가 설치에 실패합니다. 판에 묶인 대상 이름(`chrome131`, `safari2601`)은 판마다 바뀌므로 설치된 판의 문서를 확인한 뒤에만 씁니다.

## 3. 구조화 메타데이터

본문은 진짜인데 페이지가 크거나 일부만 필요하면 요청한 필드를 추출합니다.

```bash
f=.hyper/browsing/<slug>/attempts/<n>.html
grep -o '<meta[^>]*property="og:[^"]*"[^>]*>' "$f"                     # Open Graph
grep -o '<link[^>]*rel="canonical"[^>]*>' "$f"                         # canonical URL (증명 4층)
awk '/<script[^>]*application\/ld\+json/,/<\/script>/' "$f"            # JSON-LD 블록
grep -o '<link[^>]*type="application/\(rss\|atom\)+xml"[^>]*>' "$f"    # 피드 발견
```

`@type`이 `Article`, `NewsArticle`, `Product`, `VideoObject`이고 기대한 이름이 붙은 JSON-LD는 긍정 증명으로 셉니다.

## 4. 리더

리더는 페이지를 렌더링해 텍스트를 돌려줍니다. 결과는 출처 `reader`입니다. 리더에 쿠키나 인가를 보내지 않습니다.

```bash
curl -s -m 30 ${JINA_API_KEY:+-H "Authorization: Bearer $JINA_API_KEY"} "https://r.jina.ai/<URL>"
```

2026-11-07에 이 저장소의 네트워크에서 `https://example.com`에 대한 익명 요청이 HTTP 200과 페이지 제목을 돌려줬습니다. 상위 스킬은 익명 접근을 거부(401)로 기록했습니다. 익명 접근은 불안정하게 보고 이번 실행이 본 쪽을 기록합니다. 리더는 리더 자신의 서버를 막는 WAF를 통과하지 못합니다.

리더의 200은 내용의 증거가 아닙니다. 같은 날 `https://www.crunchbase.com/organization/openai`에 대한 리더 요청은 200과 883바이트로 끝났지만, 본문은 `Attention Required! | Cloudflare`와 `Target URL returned error 403` 경고였습니다. 리더 결과도 §2의 증명 층으로 검사하고, 챌린지 표식이 있으면 `challenge`로 판정합니다.

## 5. 미디어

```bash
yt-dlp --dump-json --skip-download "<URL>" > .hyper/browsing/<slug>/content/media.json
yt-dlp --write-sub --write-auto-sub --sub-lang 'ko,en' --skip-download \
  -o '.hyper/browsing/<slug>/content/%(id)s' "<URL>"
```

yt-dlp는 천 개가 넘는 미디어 사이트를 다룹니다. 2026-11-07에 PyPI 최신은 2026.10.26이었습니다. 없으면 미디어 추출기를 `skipped`로 표시하거나 작업 전용 가상 환경에 설치합니다. 미디어 파일 자체는 `rules/access-policy.md` §4의 게이트가 있을 때만 내려받습니다.

## 6. 아카이브 사본(Tier 2)

```bash
curl -s -m 20 "https://archive.org/wayback/available?url=<URL>"
# -> archived_snapshots.closest.url 과 .timestamp. 그 URL을 요청하고 시각을 남긴다
# --compressed 필수: 아카이브 원본(id_) 응답은 gzip으로 오고, 없으면 이진 내용이 그대로 저장된다
curl -sL --compressed -m 30 -o .hyper/browsing/<slug>/attempts/<n>.html "<snapshot url>"
curl -s -m 20 "https://web.archive.org/cdx/search/cdx?url=<URL>&limit=-5&output=json"   # 최근 스냅숏 목록
curl -s -m 20 "https://web.archive.org/cdx/search/cdx?url=<URL>&output=json&filter=statuscode:200&limit=-1"  # 상태 200인 최근 스냅숏의 timestamp
# id_ 접미사는 아카이브가 덧붙인 툴바·재작성 없이 원본 응답을 준다
#   https://web.archive.org/web/<timestamp>id_/<URL>
for d in archive.ph archive.md archive.li archive.is; do                                 # 다른 아카이브, 호스트 회전
  curl -s -m 15 -o /dev/null -w "$d\t%{http_code}\n" "https://$d/newest/<URL>"
done
```

2026-11-07에 이 저장소의 네트워크에서 측정한 결과:

| 경로 | 결과 |
|---|---|
| Wayback availability API | 200, 스냅숏 URL과 시각을 돌려줌 |
| Wayback CDX API | JSON 행과 함께 200(상위 스킬은 2026-08에 503을 기록했으나 지금은 회복) |
| Wayback `web/<ts>/<URL>`(재작성본) | 불안정함: 한 번은 403과 `Attention Required! \| Cloudflare` 페이지를, 몇 분 뒤 같은 URL은 200과 진짜 페이지를 돌려줌. 본문마다 판정하고, 챌린지 본문이면 같은 요청을 다시 보내지 말고 축 하나(원본 `id_` 경로)를 바꿈 |
| Wayback `web/<ts>id_/<URL>` + `--compressed` | 200, 148,648바이트, 제목 `OpenAI - Crunchbase Company Profile & Funding`, 본문 13,801자. 진짜 사본 |
| `--compressed` 없는 Wayback `web/<ts>id_/<URL>` | 200, 148,648바이트지만 gzip 이진 내용(원본 보기가 저장된 `Content-Encoding: gzip`을 그대로 재생함). 크기 검사는 통과하므로 텍스트 검사가 필요 |
| archive.today 호스트(`.ph`, `.md`, `.li`, `.is`) | 이 네트워크에서 응답 없음(연결 실패) |
| 구글 웹 캐시 | 캐시가 아니라 검색 인터스티셜 |

아카이브 본문도 증명 층으로 확인합니다. 아카이브 호스트도 본문이 붙은 속도 제한 페이지를 주고, SPA 스냅숏은 빈 껍데기인 경우가 많습니다. 받은 파일이 텍스트인지 먼저 확인합니다(`file <path>`, 또는 UTF-8 디코딩 실패). 이진이면 축 하나(원본 id_ 경로, `--compressed`)를 바꿔 다시 받습니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 요청 격자, curl_cffi 위장, 리더, 미디어 추출기, 아카이브 순서 | `code-yeongyu/oh-my-openagent`(`dev` 브랜치)의 `ultimate-browsing` 스킬, 2026-11-07에 읽음 |
| curl_cffi 0.17.0과 yt-dlp 2026.10.26이 현재 판 | <https://pypi.org/pypi/curl-cffi/json>, <https://pypi.org/pypi/yt-dlp/json>, 2026-11-07에 읽음 |
| 엔드포인트 측정 행 | 2026-11-07에 이 저장소의 네트워크에서 한 요청. 결과는 네트워크에 따라 다르고 예고 없이 바뀜 |
| Wayback availability·CDX API | <https://archive.org/help/wayback_api.php> |
