# Spec 형식

`render-deck.sh`를 실행하기 전에 `<slug>.deck.json`을 씁니다. 아래 필드는 모두 `assets/runtime/layout.jq`가 읽고, 여기에 없는 필드는 무시합니다.

## Contents

- 덱 필드
- 슬라이드 종류
- 텍스트 필드와 단위
- 팔레트
- 차트
- 이미지
- 발표자 노트와 캡션
- 완전한 예시

## 덱 필드

| 필드 | 필수 | 뜻 |
|---|---|---|
| `slides` | 예 | 슬라이드 객체의 비어 있지 않은 배열 |
| `title` | 아니요 | 덱 제목이며 `docProps`에 남습니다 |
| `author` | 아니요 | 작성자이며 `docProps`에 남습니다 |
| `lang` | 아니요 | 기본값 `ko`이며 모든 텍스트 실행의 언어 태그가 됩니다 |
| `footer` | 아니요 | 바닥글 문구이며 쪽 번호도 함께 붙습니다 |
| `theme` | 아니요 | 팔레트 이름(기본 `ink`) 또는 팔레트 덮어쓰기 객체 |
| `fonts` | 아니요 | `{ "latin": "...", "eastAsian": "...", "mono": "..." }` |

`fonts.latin`의 기본값은 `Pretendard`이고 `fonts.eastAsian`은 `fonts.latin`을 따릅니다. 글꼴 이름은 읽는 사람의 컴퓨터에 그 글꼴이 있어야 보입니다. 덱은 이름만 기록하고 글꼴 파일을 넣지 않습니다.

## 슬라이드 종류

모든 슬라이드는 `kind`(기본 `bullets`)와 `notes`, 그리고 그 종류의 필드를 받습니다.

| `kind` | 필드 | 쓰임 |
|---|---|---|
| `title` | `title`, `subtitle`, `meta` | 표지, 어두운 배경 |
| `section` | `number`, `title`, `subtitle` | 장 구분, 어두운 배경 |
| `bullets` | `title`, `lead`, `bullets` | 한 슬라이드에 한 주장 |
| `columns` | `title`, `columns` | 나란한 카드 2~3개 |
| `stats` | `title`, `stats` | 앞세울 숫자 최대 4개 |
| `table` | `title`, `table` | `columns`, `rows`, `caption` |
| `chart` | `title`, `chart` | `type`, `categories`, `series`, `caption` |
| `image` | `title`, `image`, `caption` | 사진 한 장 |
| `quote` | `quote`, `attribution` | 한 줄 인용, 어두운 배경 |

`title`, `section`, `quote` 슬라이드는 어둡게, 나머지는 밝게 그립니다. 한 슬라이드에 두 종류를 섞지 않습니다. 글머리표 세 줄이 붙은 표가 필요하면 슬라이드를 둘로 나눕니다.

## 텍스트 필드와 단위

`bullets`는 문자열이나 객체를 받습니다.

```json
{ "text": "카드 인증에서 47%가 끊긴다", "level": 0, "bold": false, "size": 18, "color": "12171D", "bullet": true, "space": 6 }
```

| 필드 | 뜻 |
|---|---|
| `level` | `0` 또는 `1`이며, 1단계는 부모 크기에서 2포인트 줄고 들여쓰입니다 |
| `size` | 포인트 크기이며 0단계 기본값은 `18`입니다 |
| `space` | 이 줄 앞의 여백 포인트이며 0단계 기본값은 `6`입니다 |
| `bullet` | `false`이면 글머리표를 뺍니다 |

크기와 여백은 픽셀이 아니라 활자 포인트입니다. 배치는 이 값을 변환해 씁니다. CSS에서 가져온 값을 그대로 넣으면 의도한 크기의 3분의 1쯤으로 나옵니다.

`columns`는 `{ "heading": "...", "bullets": [...] }`의 배열이며 앞의 세 개만 배치합니다. `stats`는 `{ "value": "...", "label": "...", "note": "..." }`의 배열이며 앞의 네 개만 배치하고, `note`는 첫 항목에 있을 때만 그립니다.

## 팔레트

| 이름 | 생김새 |
|---|---|
| `ink` | 중성 회색에 따뜻한 주황 강조 |
| `paper` | 미색 종이에 갈색 글자 |
| `navy` | 기업용 남색 |
| `forest` | 짙은 초록 |
| `mono` | 흰 바탕 검정, 색 강조 없음 |

토큰은 객체로 덮어씁니다.

```json
{ "theme": { "base": "navy", "accent": "0F766E", "surface": "E6F4F1" } }
```

색은 `#` 없는 여섯 자리 16진수입니다. `bg`, `fg`, `accent`, `muted`, `surface`, `line`은 밝은 슬라이드 토큰입니다. 어두운 슬라이드는 같은 팔레트에서 파생되므로 `bg`를 바꿔도 어두운 슬라이드는 그대로입니다.

## 차트

```json
{ "chart": { "type": "column", "categories": ["W1", "W2"], "series": [{ "name": "실패율", "values": [8.4, 7.1] }] } }
```

`type`은 `column`(기본), `bar`(가로), `line`, `pie`, `stacked` 중 하나입니다. 값은 문자열이 아니라 JSON 숫자여야 합니다. `pie`는 첫 계열만 그립니다. 범주 개수와 각 계열의 값 개수가 같아야 합니다.

## 이미지

```json
{ "image": { "path": "/abs/path/shot.png", "aspect": 1.7778 } }
```

`path`는 로컬 `png`, `jpg`, `gif` 파일이어야 합니다. 원격 주소는 거부합니다. 덱이 네트워크에 기대지 않게 하려는 것입니다. `aspect`는 가로를 세로로 나눈 값이며 실제 파일과 맞아야 합니다. 그림을 상자에 잘라 넣지 않고 맞춰 넣기 때문입니다. `height`는 본문 폭에 맞추기 전 시작 높이를 EMU로 덮어씁니다.

그림은 만들지 않습니다. 사용자가 준 파일, 차트 내보내기, 다른 도구의 결과 파일 경로를 spec에 적습니다.

## 발표자 노트와 캡션

`notes`는 실제 파워포인트 발표자 노트가 됩니다. 덱을 열면 노트 창에 그대로 보입니다. 표, 차트, 이미지 아래의 캡션은 실제 텍스트 도형이며 자기 자리를 미리 비워 두므로 위 내용과 겹치지 않습니다.

## 완전한 예시

```json
{
  "title": "결제 실패율 개선",
  "footer": "결제팀",
  "theme": "ink",
  "fonts": { "latin": "Pretendard", "eastAsian": "Pretendard" },
  "slides": [
    { "kind": "title", "title": "결제 실패율 3주 만에 12% 줄이기", "subtitle": "원인 분석과 3단계 개선안", "meta": "2026-11-13" },
    { "kind": "bullets", "title": "결제 실패는 3개 구간에서 발생한다", "lead": "실패 로그 12만 건을 구간별로 나눴습니다.",
      "bullets": ["카드 인증 단계 실패 47%", { "text": "잔액 부족 응답 지연 31%", "level": 1 }], "notes": "로그 기준" },
    { "kind": "stats", "title": "한눈에 보는 개선 효과",
      "stats": [{ "value": "12%", "label": "실패율 감소" }, { "value": "3주", "label": "적용 기간" }] },
    { "kind": "chart", "title": "주간 실패율", "chart": { "type": "line", "categories": ["W1", "W2"],
      "series": [{ "name": "실패율", "values": [8.4, 7.1] }], "caption": "배포 후 2주" } }
  ]
}
```

## Sources

> 확인 2026-11-13.

| Claim | Source |
|---|---|
| 슬라이드 크기 13.333 × 7.5인치와 EMU 좌표 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| 발표자 노트는 `notesSlide` 파트에 저장됨 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-notes-slides> |
| 차트 파트는 범주와 값을 캐시로 함께 가짐 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |

### 근거 등급

`LOCAL` - 이 파일의 필드 이름과 기본값은 모두 이 패키지의 `assets/runtime/layout.jq`에서 읽었고, 2026-11-13에 종류마다 렌더링해 확인했습니다.
