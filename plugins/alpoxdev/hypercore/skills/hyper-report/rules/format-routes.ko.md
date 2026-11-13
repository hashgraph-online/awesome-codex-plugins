# 형식 경로

소스 하나, 형식 여럿, 방향 하나. Markdown 소스를 작성하고, 그 소스에서 HTML을 렌더링하며, 나머지는 모두 HTML에서 파생한다.

## 1. HTML이 정본인 이유

HTML은 다른 모든 형식의 소스이면서 그 자체로 검사 가능한 유일한 산출물이다. PDF는 인쇄한 HTML이고, 페이지 이미지는 그 HTML의 한 페이지를 찍은 스크린샷이며, DOCX는 그 HTML의 변환이다. HTML을 고치면 모든 형식이 그 수정을 물려받는다. PDF를 손으로 고치면 다음 렌더가 그 수정을 조용히 버린다.

```
report.md  --(markdown.awk)-->  body.html
body.html + report.css + theme + report.js  --(assemble.awk)-->  report.html   <- canonical
report.html  --(headless print)-->    report.pdf
report.html  --(headless screenshot)--> report-01.png ... report-NN.png
report-NN.png --(sips / magick)-->     report-NN.jpg
report.html  --(textutil)-->          report.docx
report.md    --(copy)-->              report.md
```

## 2. 형식마다 지니는 것

| 형식 | 지니는 것 | 잃는 것 | 쓰는 경우 |
|---|---|---|---|
| HTML | 전부. 페이지 나눔, 테마, 표, 그림, 목차 | 없음. 다만 열려면 브라우저가 필요하다 | 독자가 화면에서 읽거나, 올바르게 인쇄되는 파일 하나가 필요할 때 |
| PDF | 페이지가 나뉜 그대로, 폰트 내장, 고정된 기하 | 텍스트 재흐름, 브라우저가 쓴 것 밖의 살아 있는 링크 | 독자가 인쇄하거나 메일로 보내거나 서명할 때 |
| PNG | 페이지마다 파일 하나, 기기 배율 1–3× | 텍스트 선택, 링크, 검색 | 슬라이드, 채팅 메시지, 게시판, 미리보기 |
| JPG | PNG와 같고 더 작다 | 텍스트에 압축 손상이 조금 더 남는다 | 목적지가 파일 크기를 제한하거나 PNG를 거부할 때 |
| DOCX | 편집 가능한 텍스트, 독자가 고칠 수 있다 | 정확한 페이지 나눔, 테마의 타이포그래피, 바닥글 번호 | 독자가 Word에서 편집하거나 논평해야 할 때 |
| Markdown | 작성한 소스, 이식 가능 | 파이프라인이 적용한 모든 레이아웃 | 독자가 텍스트를 원하거나 다른 곳에서 다시 렌더링할 때 |

DOCX는 예의상 내보내는 형식이며 레이아웃을 그대로 지키는 형식이 아니다. 전달할 때 그렇게 밝힌다. Word는 자체 엔진과 폰트로 텍스트를 다시 배치하므로 Word의 페이지 나눔은 PDF와 맞지 않는다.

## 3. 형식 선택

밝힌 독자에게 필요한 가장 작은 집합을 고른다.

- 형식을 말하지 않았고 화면에서 읽는 독자면 `html,pdf`.
- 형식을 말하지 않았고 인쇄나 메일이면 `html,pdf`.
- 채팅이나 슬라이드 목적지면 `png`만, 또는 중요한 페이지에 `pdf`와 `png`를 함께.
- 독자가 편집해야 하면 `docx`를 더하고 페이지 나눔을 경고한다.
- 페이지가 제한된 작업("한 장")이면 페이지 수가 산출물의 제약이므로 형식을 더하기 전에 그것을 확인한다.

파이프라인이 할 수 있다는 이유만으로 사용자가 요청하지 않은 형식을 더하지 않는다. 사용자가 하나를 원했는데 파일 다섯 개를 내는 것은 파일 하나보다 나쁜 전달이다.

## 4. 렌더러가 없을 때

형식은 이 순서로 퇴화하고, 그 퇴화는 숨기지 않고 보고한다.

| 없는 것 | 여전히 되는 것 | 보고되는 것 |
|---|---|---|
| Chromium 계열 브라우저 | `md`만 | `BROWSER_MISSING`. 브라우저가 렌더링 경로 전체다 |
| `textutil`(macOS 아님) | `html`, `pdf`, `png` | `DOCX_UNAVAILABLE` |
| `sips`와 ImageMagick | `html`, `pdf`, `png` | `jpg` 요청에 한해 `RASTERIZER_MISSING` |

형식을 만들어 내려고 실행 중에 렌더러를 설치하지 않는다. 어떤 형식이 왜 안 되는지 보고하고, 나머지를 전달하고, 결정은 사용자에게 맡긴다.

## 5. 페이지가 단위

Markdown을 뺀 모든 형식은 페이지 단위로 다뤄지므로, 페이지 수는 HTML에서 한 번 정해지고 파생 형식 모두가 그것에 맞는다.

- `report.js`의 레이아웃 단계가 내용이 몇 페이지를 차지하는지 정한다.
- PDF는 정확히 그 수만큼 인쇄해야 한다. 어긋나면 막는 발견이다.
- 이미지 내보내기는 페이지마다 하고, 1부터 번호를 붙이며 두 자리로 0을 채운다.
- 바닥글의 페이지 번호는 `current / total`이고, 페이지 나눔 뒤에 확정된다.

그래서 소스는 흐르는 텍스트 중간에 수동 페이지 나눔을 담을 수 없고, 명시적 `:::pagebreak` 표시를 통해서만 담는다. 페이지 나눔기는 그 표시를 강한 경계로 존중한다.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| 렌더링 기본 요소로서의 헤드리스 인쇄, 스크린샷, DOM 덤프 | <https://developer.chrome.com/docs/chromium/headless> |
| `@page` 크기와 여백, 고정 기하 인쇄 모델 | <https://developer.mozilla.org/en-US/docs/Web/CSS/@page> |
| macOS 이미지 변환기로서의 `sips`, macOS 문서 변환기로서의 `textutil` | <https://ss64.com/mac/sips.html>, <https://ss64.com/mac/textutil.html> |
| Word에서 다시 배치한 DOCX가 브라우저 페이지 나눔과 다른 점 | 문서화된 보장이 아니라, 이 패키지가 macOS 26.2에서 Word 자체 레이아웃 엔진으로 잰 측정 |