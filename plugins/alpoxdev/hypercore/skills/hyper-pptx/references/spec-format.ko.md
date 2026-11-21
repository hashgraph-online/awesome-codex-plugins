# Spec 형식

`render-deck.sh`를 실행하기 전에 `<slug>.deck.json`을 씁니다. 아래 필드는 모두 `assets/runtime/layout.jq`가 읽고, 여기에 없는 필드는 무시합니다.

## Contents

- 덱 필드
- 슬라이드 종류
- 텍스트 필드와 단위
- 팔레트와 그라디언트
- 모션
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
| `transition` | 아니요 | 모든 슬라이드의 기본 전환이며 슬라이드가 덮어쓸 수 있습니다 |

`fonts.latin`의 기본값은 `Pretendard`이고 `fonts.eastAsian`은 `fonts.latin`을 따릅니다. 글꼴 이름은 읽는 사람의 컴퓨터에 그 글꼴이 있어야 보입니다. 덱은 이름만 기록하고 글꼴 파일을 넣지 않습니다.

## 슬라이드 종류

모든 슬라이드는 `kind`(기본 `bullets`), `notes`, 그리고 그 종류의 필드를 받습니다. 종류마다 배치는 고정이며, 빠진 필드는 늘어나지 않고 빠진 채로 그립니다.

| `kind` | 필드 | 쓰임 |
|---|---|---|
| `title` | `title`, `subtitle`, `kicker`, `meta` | 표지, 어두운 배경 |
| `section` | `number`, `title`, `subtitle` | 장 구분, 어두운 배경 |
| `bullets` | `title`, `lead`, `bullets` | 한 슬라이드에 한 주장 |
| `columns` | `title`, `lead`, `columns` | 나란한 카드 2~3개 |
| `stats` | `title`, `lead`, `stats` | 카드로 세운 숫자 2~4개 |
| `kpi` | `title`, `lead`, `value`, `label`, `delta`, `bullets` | 숫자 하나가 주장이고 옆에 근거 목록이 붙는 경우 |
| `compare` | `title`, `lead`, `left`, `right` | 두 패널 비교, 개선 전후나 선택지 A/B |
| `timeline` | `title`, `lead`, `milestones` | 한 줄 위에 놓인 2~5단계 |
| `table` | `title`, `table` | `columns`, `rows`, `caption` |
| `chart` | `title`, `chart` | `type`, `categories`, `series`, `caption` |
| `image` | `title`, `image`, `caption` | 본문 폭을 채우는 사진 한 장 |
| `imagetext` | `title`, `lead`, `heading`, `bullets`, `image` | 주장 옆에 붙는 사진 |
| `hero` | `title`, `subtitle`, `image`, `scrim` | 사진이 곧 페이지, 어둡게 덮고 그 위에 글자 |
| `gallery` | `title`, `lead`, `images`, `caption` | 사진 1~4장을 한 줄로, 각 사진 아래 설명 |
| `quote` | `quote`, `attribution` | 한 줄 인용, 어두운 배경 |
| `statement` | `text`, `kicker`, `gradient` | 한 문장이 곧 페이지, 색 띠를 깐 어두운 배경 |
| `bigstat` | `value`, `label`, `note`, `kicker` | 숫자 하나가 주장 전체인 경우 |
| `process` | `title`, `steps` | 번호가 붙은 2~5단계 한 줄 |

`title`, `section`, `hero`, `quote`, `statement` 슬라이드는 어둡게, 나머지는 밝게 그립니다. 한 슬라이드에 두 종류를 섞지 않습니다. 글머리표 세 줄이 붙은 표가 필요하면 슬라이드를 둘로 나눕니다.

`kpi`는 "숫자 하나"를 쓰는 슬라이드입니다. `value`는 글자 수가 허용하는 만큼 크게 잡고(세 글자 96포인트, 여덟 글자 이상 54포인트), `label`이 그 숫자를 이름 붙이며, `delta`가 비교를 흐린 색으로 답니다. `bullets`는 오른쪽 칸에 놓이고 카드와 같은 행 높이를 쓰므로, 짧은 카드 옆에 긴 목록이 붙어도 단이 어긋나지 않습니다.

`compare`는 `{ "heading": "...", "bullets": [...] }` 두 개를 받습니다. 글머리표 크기는 두 쪽 중 더 좁은 쪽에 맞춰 16~24포인트에서 정하고, 두 패널은 리드 줄 아래 남은 자리에서 함께 가운데로 옵니다.

`statement`는 글머리표 없는 한 문장입니다. `text`는 길이에 따라 40, 34, 28포인트로 잡히고, `kicker`는 위에 붙는 작은 표제, `gradient`는 글자 뒤에 까는 띠입니다. 읽는 사람이 기억해야 할 문장에 쓰고, 두 번째 제목처럼 쓰지 않습니다.

`bigstat`은 `stats`와 다릅니다. `stats`는 숫자 2~4개를 한 격자에서 비교하고, `bigstat`은 숫자 하나를 주장으로 세웁니다. `value`는 네 글자까지 150포인트로 잡히고 아홉 글자에서 72포인트로 내려가며, `label`이 그 숫자의 뜻을 밝히고, `note`가 출처를 답니다.

`process`는 `{ "heading": "...", "text": "..." }`의 `steps`를 2~5개 받습니다. 카드 높이는 가장 긴 표제와 본문에서 계산하므로 두 줄짜리 단계도 잘리지 않고, 여섯 단계는 열이 읽히지 않으므로 `PROCESS_TOO_MANY` 오류입니다.

`timeline`은 `{ "label": "...", "title": "...", "text": "..." }`를 받습니다. `label`은 기준선 위의 날짜나 단계 표시, `title`은 단계 이름, `text`는 아래 설명입니다. 다섯 개가 상한이며 여섯 번째는 발표 화면에서 읽히지 않습니다.

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

`columns`는 `{ "heading": "...", "bullets": [...] }`의 배열이며 앞의 세 개만 배치하고, 카드 높이는 카드 자신의 제목과 항목 길이에서 나오고, 짧은 카드 셋이 제목 아래 띠로 주저앉지 않도록 본문 높이의 62%를 최소로 두므로 글자 아래에 빈 블록이 남지 않습니다. `stats`는 `{ "value": "...", "label": "...", "note": "..." }`의 배열이며 앞의 네 개만 배치합니다. `note`는 항목마다 붙일 수 있고, 한 줄의 값은 가장 긴 문자열에 맞춘 하나의 크기를 함께 쓰므로 짧은 숫자가 긴 숫자를 압도하지 않고, 카드에는 `columns`와 같은 62% 하한이 적용되어 숫자 셋으로 된 줄도 페이지를 지탱합니다.

## 팔레트와 그라디언트

| 이름 | 생김새 |
|---|---|
| `ink` | 중성 회색에 따뜻한 주황 강조 |
| `paper` | 미색 종이에 갈색 글자 |
| `navy` | 기업용 남색 |
| `forest` | 짙은 초록 |
| `slate` | 차가운 회청색 |
| `mono` | 흰 바탕 검정, 색 강조 없음 |
| `ocean` | 짙은 남색에 청록 짝 |
| `plum` | 보라에 자홍 짝 |
| `ember` | 따뜻한 바탕에 탄 주황 |
| `sand` | 베이지 바탕에 흙색 강조 |

토큰은 객체로 덮어씁니다.

```json
{ "theme": { "base": "navy", "accent": "0F766E", "surface": "E6F4F1" } }
```

색은 `#` 없는 여섯 자리 16진수입니다. `bg`, `fg`, `accent`, `accent2`, `muted`, `surface`, `tint`, `line`은 밝은 토큰이고, `darkBg`, `darkFg`, `darkMuted`, `darkAccent`, `darkAccent2`, `darkSurface`, `darkTint`는 어두운 토큰입니다. 어두운 슬라이드도 같은 색 계열을 쓰므로 회색으로 떨어지지 않습니다. 색은 덱 단위 결정입니다. 슬라이드는 물려받으며, 페이지 하나가 다른 색을 필요로 한다면 그 덱에 팔레트가 둘 있다는 신호입니다.

`accent2`는 짝 색입니다. 차트의 두 번째 계열, 프로세스 뒤쪽 단계의 배지, 강조 옆의 작은 블록에 씁니다. 순위가 아니라 짝입니다.

그라디언트는 색 둘과 각도이며, 쌍이나 객체로 씁니다.

```json
{ "gradient": ["0F172A", "134E4A"] }
{ "gradient": { "from": "0F172A", "to": "134E4A", "angle": 90 } }
```

`angle`은 DrawingML과 같이 x축 양의 방향에서 반시계로 잰 각도입니다. `0`은 왼쪽에서 오른쪽, `90`은 위에서 아래입니다. 형식이 틀리면 슬라이드 파트를 만들지 않고 배치 단계에서 `GRADIENT_INVALID`로 실패합니다.

## 모션

전환은 슬라이드에, 애니메이션은 그 슬라이드의 도형 하나 이상에 붙습니다. 둘 다 선택이며, 어느 쪽도 없으면 덱은 이전과 똑같이 렌더됩니다.

```json
{ "transition": "fade" }
{ "transition": { "effect": "morph", "speed": "med", "duration": 700 } }
{ "animation": [
    { "effect": "fade", "target": "title", "trigger": "with-previous", "duration": 400 },
    { "effect": "fly", "target": "body", "direction": "up", "delay": 100 }
] }
```

| `transition` 효과 | 설명 |
|---|---|
| `fade`, `cut`, `dissolve` | 단순 |
| `push`, `wipe`, `cover`, `split`, `strips`, `zoom`, `plus`, `pull`, `randomBar` | 방향이 고정 |
| `checker`, `blinds`, `diamond`, `circle`, `wedge`, `wheel`, `random`, `comb`, `newsflash` | 모양만 |
| `morph` | 파워포인트 2019 이상, 그 아래 판은 페이드로 대체 |
| `none` | 이 슬라이드에는 전환 없음 |

`speed`는 `slow`, `med`, `fast`입니다. 이 목록 밖의 이름은 `TRANSITION_UNKNOWN`으로 실패합니다. 파워포인트가 모르는 전환 요소를 만나면 파일 전체의 복구를 제안하기 때문에, 가까운 이름으로 바꾸지 않고 거부합니다.

| `animation` 효과 | 갈래 |
|---|---|
| `appear`, `fade`, `wipe`, `fly`, `zoom`, `split` | 등장 |
| `grow`, `spin` | 강조 |
| `exitFade` | 퇴장 |

| 필드 | 뜻 |
|---|---|
| `effect` | 위 아홉 중 하나이며 다른 값은 `ANIMATION_EFFECT_UNKNOWN`입니다 |
| `target` | `all`(기본, 내용 도형 전부), 역할(`title`, `body`, `kicker`, `table`, `chart`, `image`, `decor`), 도형 id, 또는 이들의 배열 |
| `trigger` | `on-click`(기본), `with-previous`, `after-previous` |
| `direction` | `up`(기본), `down`, `left`, `right`이며 `fly`와 `wipe`가 씁니다 |
| `duration` | 밀리초, 기본 `500` |
| `delay` | 트리거 뒤 지연 밀리초, 기본 `0` |

`target: "all"`은 장식과 쪽 정보를 건너뜁니다. 제목 아래 규칙선까지 등장하면 페이지가 스스로 조립되는 것처럼 보입니다. 아무 도형도 맞지 않는 대상은 대상 없는 타이밍 트리를 만드는 대신 `ANIMATION_TARGET_EMPTY`로 실패합니다.

모션은 ECMA-376 스키마를 보고 씁니다. 발표장에서 이것이 무엇을 뜻하는지와 의도적으로 넣지 않은 것은 `motion.md`에 있습니다.

## 차트

```json
{ "chart": { "type": "column", "categories": ["W1", "W2"], "series": [{ "name": "실패율", "values": [8.4, 7.1] }] } }
```

| `type` | 그리는 것 |
|---|---|
| `column`(기본) | 세로 묶음 막대 |
| `bar` | 가로 묶음 막대, 값 축이 아래 |
| `stacked` | 세로 누적 막대 |
| `stackedBar` | 가로 누적 막대 |
| `line` | 표식이 붙은 꺾은선 |
| `area` | 아래를 옅게 채운 꺾은선 |
| `scatter` | 점, 범주가 숫자면 x가 되고 아니면 순서가 x가 됩니다 |
| `pie` | 첫 계열만 |
| `doughnut` | 첫 계열만, 링 두께는 `hole` |
| `combo` | 왼쪽 값 축에 막대, 오른쪽 보조 축에 선 |

| 필드 | 뜻 |
|---|---|
| `categories` | 문자열 배열이며 범주 축이 되거나 산점도의 x 값이 됩니다 |
| `series` | `{ "name": "...", "values": [...], "as": "bar" \| "line" }`의 배열 |
| `as` | 혼합 차트에서만: 계열이 어느 그룹에 속하는지. 첫 계열은 `bar`, 나머지는 `line`이 기본입니다 |
| `labels` | `true`이면 모든 점, 막대, 조각에 값을 답니다 |
| `legend` | `none`, `bottom`, `top`, `left`, `right`, `topRight`이며 계열이 둘 이상이면 기본 `bottom`입니다 |
| `numberFormat` | `0.0`, `#,##0`, `0%` 같은 엑셀 서식이며 축 눈금과 값에 적용됩니다 |
| `valueAxisTitle` | 값 축 옆에 세로로 세우는 캡션 |
| `categoryAxisTitle` | 범주 축 아래에 붙는 캡션 |
| `hole` | 도넛 링 두께 백분율, 기본 `50` |
| `caption` | 차트 아래 한 줄, 자기 자리를 미리 비워 둡니다 |

값은 문자열이 아니라 JSON 숫자여야 하고, 모든 계열이 범주마다 값 하나를 가져야 합니다. `combo`는 단위가 다른 두 계열을 한 장에 놓으려고 존재합니다. 비율 계열이 오른쪽 축을 쓰면 수백 단위 막대 옆에서 납작해지지 않고 제 모양을 지킵니다. 두 그룹은 범주 축을 공유합니다.

## 이미지

```json
{ "image": { "path": "/abs/path/shot.png", "alt": "재시도 안내 화면", "fit": "contain", "side": "right", "credit": "내부 시안" } }
```

| 필드 | 뜻 |
|---|---|
| `path` | 로컬 `png`, `jpg`, `gif`의 경로이며 상대 경로는 spec 파일이 있는 폴더 기준으로 풀립니다. 원격 주소는 거부합니다. 덱이 네트워크에 기대지 않게 하려는 것입니다 |
| `alt` | 그림에 적히는 대체 텍스트이며 납품에는 필수입니다. 보지 못하는 읽는 사람에게 그림을 설명하는 유일한 문장입니다 |
| `fit` | `contain`(그림 전체, 여백 허용), `fill`(상자에 맞춰 자름), `cover`. 종류마다 기본값이 다릅니다 |
| `side` | `imagetext` 전용이며 `right`(기본) 또는 `left`입니다 |
| `credit` | 캡션 뒤에 구분자와 함께 붙습니다 |
| `aspect` | 가로를 세로로 나눈 값이며 파일을 읽을 수 없을 때만 필요하고, 실제 파일과 맞아야 합니다 |
| `caption` | `gallery`의 사진별 설명이거나 `image` 슬라이드의 캡션입니다 |

`fit` 기본값은 `image`가 `contain`, `imagetext`와 `gallery`가 `fill`, `hero`가 항상 `fill`입니다. `hero`는 사진이 곧 페이지이기 때문입니다. `fill`은 그림 가운데를 `srcRect`로 잘라 내므로 파워포인트에서도 잘린 모습이 보이고 미리보기에서 같은 창을 재현합니다. 그림은 만들지 않습니다. 사용자가 준 파일, 차트 내보내기, 다른 도구의 결과 파일 경로를 spec에 적습니다.

`gallery`는 사진 1~4장을 받고 각 항목은 `{ "path": ..., "alt": ..., "caption": ..., "fit": ... }`입니다. 사진 높이는 캡션이 차지할 자리를 뺀 뒤 계산하므로 설명이 위 사진을 덮지 않습니다.

`hero`는 캔버스 전체에 깔리는 `back` 층 사진, 단색 덮개, 그 위의 글자 순서로 그립니다. `scrim`은 검정 덮개의 불투명도이며 기본값은 `0.55`입니다. 사진이 복잡하면 올리고, 이미 어두우면 내립니다.

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
    { "kind": "title", "title": "결제 실패율 3주 만에 12% 줄이기", "subtitle": "원인 분석과 3단계 개선안", "kicker": "분기 리뷰", "meta": "2026-11-13" },
    { "kind": "bullets", "title": "결제 실패는 3개 구간에서 발생한다", "lead": "실패 로그 12만 건을 구간별로 나눴습니다.",
      "bullets": ["카드 인증 단계 실패 47%", { "text": "잔액 부족 응답 지연 31%", "level": 1 }], "notes": "로그 기준" },
    { "kind": "stats", "title": "한눈에 보는 개선 효과",
      "stats": [{ "value": "12%", "label": "실패율 감소" }, { "value": "3주", "label": "적용 기간" }] },
    { "kind": "kpi", "title": "실패율은 8.3%에서 7.1%로 내려갔습니다", "value": "7.1%", "label": "현재 주간 실패율",
      "delta": "직전 분기 평균 8.3% 대비 1.2%p 감소", "bullets": ["인증 구간 실패는 47%에서 39%로 줄었습니다"] },
    { "kind": "compare", "title": "처리 방식이 이렇게 달라졌습니다",
      "left": { "heading": "개선 전", "bullets": ["타임아웃 10초 고정", "재시도 없음"] },
      "right": { "heading": "개선 후", "bullets": ["타임아웃 3초", "대체 채널 자동 전환"] } },
    { "kind": "timeline", "title": "3주에 걸쳐 적용했습니다",
      "milestones": [{ "label": "11.01", "title": "인증 우회", "text": "3초 타임아웃" }, { "label": "11.08", "title": "잔액 안내", "text": "재시도 유도" }] },
    { "kind": "chart", "title": "주간 실패율", "chart": { "type": "combo", "categories": ["W1", "W2"],
      "series": [{ "name": "실패율", "values": [8.4, 7.1], "as": "bar" }, { "name": "성장률", "values": [8, 12], "as": "line" }],
      "labels": true, "numberFormat": "0.0", "caption": "배포 후 2주" } },
    { "kind": "imagetext", "title": "안내 화면도 함께 바꿨습니다", "heading": "재시도 유도",
      "bullets": ["실패 즉시 대체 채널을 안내합니다"], "image": { "path": "/abs/retry.png", "alt": "재시도 안내 화면" } },
    { "kind": "hero", "title": "다음 분기는 해외 결제입니다", "subtitle": "인증 지연 12초를 3초로 줄입니다",
      "image": { "path": "/abs/city.png", "alt": "도시 야경" }, "scrim": 0.6 }
  ]
}
```

## Sources

> 확인 2026-11-14.

| Claim | Source |
|---|---|
| 슬라이드 크기 13.333 × 7.5인치와 EMU 좌표 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| 발표자 노트는 `notesSlide` 파트에 저장됨 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-notes-slides> |
| 차트 파트는 범주와 값을 캐시로 함께 가짐 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| 혼합 차트는 축 쌍을 공유하는 두 차트 그룹임 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| `srcRect`는 그림 파일을 다시 쓰지 않고 잘라 냄 | <http://www.datypic.com/sc/ooxml/e-a_srcRect-1.html> |
| `p:transition`과 `p:timing`은 `p:sld`의 자식 | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.slide> |
| morph는 `p159` 확장이며 `mc:AlternateContent` 대체를 둠 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |

### 근거 등급

`LOCAL` - 이 파일의 필드 이름, 기본값, 종류는 모두 이 패키지의 `assets/runtime/layout.jq`에서 읽었고, 2026-11-14에 종류·차트 유형·전환·애니메이션마다 렌더링했습니다. PNG는 눈으로 확인했고, 전환과 애니메이션은 슬라이드 XML에서 확인했습니다. 이 환경에 파워포인트가 없어 실제 재생은 하지 못했습니다.
