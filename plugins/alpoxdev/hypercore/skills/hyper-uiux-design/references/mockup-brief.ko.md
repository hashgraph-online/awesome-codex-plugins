# 시안 브리프

최소 토큰을 정하거나 화면의 브리프를 쓸 때 이 참조를 읽습니다. 브리프는 한 테마의 화면 하나를 빠짐없이 서술한 글이고, 이미지 스킬이 레퍼런스를 보지 않고도 렌더링할 수 있게 씁니다.

브리프는 내용을 빼 놓은 레이아웃이 아니라 완성된 화면을 서술합니다. 결과를 출시된 앱처럼 읽히게 만드는 것은 [visual-quality-recipe.md](visual-quality-recipe.md)가 맡고, 브리프의 구조는 이 문서가 맡습니다.

## Contents

1. 브리프에 담는 것
2. 플랫폼별 캔버스
3. 브리프 뼈대
4. 최소 토큰 세트
5. 라이트와 다크
6. 수정 브리프

## 1. 브리프에 담는 것

| 담는 것 | 절대 담지 않는 것 |
|---|---|
| 화면의 목적 한 줄 | 제품, 브랜드, 디자이너 이름 |
| 플랫폼 프레임과 말로 쓴 캔버스 모양 | 레퍼런스 URL이나 레퍼런스 이미지 |
| 토큰 값: HEX 색, 글자 크기, 모서리, 간격 | 모델 이름이나 모델 옵션 |
| 위에서 아래로 본 영역과, 영역마다의 크기·간격·내용 | 실제 개인 정보 |
| 화면이 보여 주는 모든 문자열·숫자·날짜·이름을 철자까지 | 자리표시자, lorem ipsum, 글자를 대신하는 막대 |
| 지어낸 샘플 데이터와 앞뒤가 맞는 합계 | 한 이미지에 여러 화면을 넣으라는 요청 |

브리프 하나는 한 테마의 화면 하나이고 이미지 하나를 만듭니다.

정확한 문자열과 그 뒤의 샘플 데이터는 장식이 아니라 필수 내용입니다. 영역은 있는데 금액·개수·이름이 없는 브리프는 미완성이고, 돌아오는 이미지는 와이어프레임입니다.

## 2. 플랫폼별 캔버스

프레임은 시안이 나타내는 논리 화면입니다. 캔버스는 이미지 스킬에 요청하는 모양입니다. 브리프 안에는 모양을 말로 서술하고, 실제 비율이나 크기는 이미지 스킬의 구조화된 캔버스 값으로만 넘깁니다.

| 플랫폼 | 디자인 기준 논리 프레임 | 캔버스 모양 | 프레임 메모 |
|---|---|---|---|
| `mobile` | 393×852, 세로, 2배 스케일 | 긴 세로, 약 9:19.5 | 위에 상태 바, 아래에 홈 인디케이터, 하단 내비게이션은 안전 영역 안 |
| `tablet` | 세로 1024×1366 또는 가로 1366×1024 | 세로 약 3:4 또는 가로 약 4:3 | 방향을 밝힙니다. 가로 태블릿은 보통 사이드 레일이나 두 패널을 둡니다 |
| `web` | 1440×900 데스크톱 뷰포트 | 가로, 약 16:10 | 사용자가 요청하지 않으면 브라우저 틀 없이 뷰포트 안의 페이지만 그립니다 |

- 브리프 안에 프레임을 픽셀로 적고, 스크린샷 자체의 뷰포트로 씁니다: `393x852 logical at @2x, flat and straight on, edge to edge`. 모호한 비율에 픽셀 프레임이 없으면 책상 위에서 비스듬한 기기가 나옵니다.
- 런타임이 모양을 몇 가지만 제공하면 같은 방향에서 가장 가까운 것을 고르고, 요청한 모양과 돌아온 모양을 메모에 적으며, 반환된 이미지를 자르거나 크기를 바꾸지 않습니다.
- 긴 페이지는 첫 뷰포트로 그립니다. 그 아래 섹션은 각각 뷰포트 하나 높이의 별도 브리프입니다.
- 화면을 평평하게 정면으로, 가장자리까지 그립니다. 기기 사진, 원근, 손, 책상, 화면 둘레 그림자는 레이아웃을 가리므로 넣지 않습니다.
- 좁은 웹 레이아웃은 웹 프레임 메모를 붙인 `mobile` 브리프입니다.

## 3. 브리프 뼈대

이 순서대로 모든 줄을 채웁니다. invariant로 표시한 줄은 세트의 모든 브리프에 글자 그대로 반복합니다.

브리프는 빈 칸을 채운 서식이 아니라 이미지 도구에 넘기는 하나의 연속된 글로 씁니다. 아래 뼈대는 에이전트가 채우는 개요이고, 완성된 브리프는 산문으로 읽힙니다.

```text
<Artifact and frame sentence>  [invariant]
A full-screen mobile app UI screenshot, portrait, 393x852 logical at @2x,
flat and straight on, edge to edge. The raw screenshot, not a device render.

<Register>
One or two sentences: the product, the screen's job, and the visual register
in the product's own terms, e.g. "calm, precise, information-dense but airy,
the look of a shipped finance app".

<Visual language and negatives>
"Light theme. No gradients, no glow, no glass blur, no decorative blobs,
no stock illustrations."

<Color>  [invariant per theme]
<role #hex> for each: page, surface, hairline, text primary, text secondary,
accent, accent tint, danger. One accent.

<Type>  [invariant per theme]
One typeface character with Hangul support. A scale with real numbers:
"greeting 14, section 18 bold, row title 15 semibold, body 15, caption 12,
headline amount 40 bold with tabular figures and tight tracking."

<Regions, numbered, top to bottom>
1. <region>: <components, sizes, gaps, alignment, and the actual content
   inside this region, inline>
2. ...

<Closing requirement>  [invariant]
"Every Korean string must be rendered fully and correctly, spelled right,
crisp. No placeholder bars, no blurred text, no lorem ipsum."

<Must not appear>  [invariant, extended per screen]
"brand logos or names, real app icons, watermarks, device frame, extra
screens, signal bars and wifi glyphs that were not asked for"
```

영역 목록의 규칙:

1. 콘텐츠를 그 콘텐츠를 보여 주는 영역에 넣습니다. `개수가 붙은 섹션 헤더`는 영역 한 줄이고, 다섯 행의 이름·건수·금액·퍼센트는 다음 영역의 줄입니다.
2. 영역마다 크기를 줍니다. 높이, 간격, 여백, 모서리를 숫자로 씁니다. `다섯 행, 각 64 높이에 12 간격`은 렌더링되고, `분류 목록`은 안 됩니다.
3. 아이콘을 지정하거나, 아이콘이 들어가는 타일을 지정합니다. `36x36 색조 타일 안의 단순한 포크·나이프 라인 아이콘`은 글리프 하나를 만들고, `단순한 외곽선 아이콘`은 매번 다른 것을 지어냅니다.
4. 모든 문자열을 따옴표로 묶어 나오는 자리에 한 번씩 씁니다. 떨어져 있는 별도 문자열 목록을 두지 않습니다. 분리된 문자열은 구조 없이 떠 있습니다.
5. 주 동작 하나를 밝히고 무엇이 그것을 주 동작으로 만드는지 적습니다: 크기, 채움, 화면에서 유일하게 온전한 강조색이라는 점.

호출 전에 브리프 옆에 적어 둘 점검은 다음과 같습니다.

- 영역이 밝힌 순서와 크기대로 있다
- 브리프의 모든 문자열·숫자·날짜·이름이 현실적이고 다 쓰여 있다
- 숫자의 앞뒤가 맞는다: 부분의 합이 총액이고 퍼센트의 합이 100이다
- 렌더링한 각 문자열이 한 글자씩 일치하고 한 번씩 나온다
- 주 동작이 하나이고 강조색이다
- 화면 유형이 기대하는 밀도를 갖는다([visual-quality-recipe.md](visual-quality-recipe.md) 7절)
- 로고, 브랜드 이름, 기기 프레임이 없다
- 캔버스 방향이 일치한다

## 4. 최소 토큰 세트

프로젝트에 디자인 문서나 토큰이 없을 때만 씁니다. 여러 시안의 일관성을 지키는 가장 작은 세트이고 `provisional`로 기록합니다.

| 묶음 | 토큰 | 고르는 방법 |
|---|---|---|
| 색 | 배경, 표면, 테두리·구분선, 주 글자, 보조 글자, 강조, 강조 위 글자, 강조 색조, 위험 | 강조색은 하나만 둡니다. 사용자가 밝힌 색이 있으면 그것을 강조색으로 쓰고, 없으면 하나를 고르고 골랐다고 밝힙니다. 나머지는 모두 무채색이 맡고, 강조 색조는 선택 상태와 아이콘 타일용으로 강조색을 옅게 쓴 값입니다. |
| 글꼴 | 서체 성격 하나, 헤드라인·제목·본문·캡션 네 단계, 굵기 둘 | 프로젝트가 이미 쓰는 글꼴이 없으면 라이선스가 걸린 글꼴 이름이 아니라 성격을 적습니다. 실제 숫자로 쓰고, 헤드라인과 본문의 비율을 2.5~2.8 근처로 둡니다. 본문 크기는 논리 단위로 웹 16, 모바일 15보다 작지 않게 합니다. |
| 모서리 | 컨트롤용 값 하나, 카드용 값 하나, 알약·타일용 값 하나 | 최대 세 값입니다. |
| 간격 | 기준 단위 하나와 좌우 여백·묶음 간격에 쓰는 배수 | 기준은 4나 8이고 배수로만 씁니다. |

규칙은 다음과 같습니다.

- 쓰기 전에 주 글자, 보조 글자, 강조 위 글자의 대비를 각 배경에 대해 계산하고, 각각 최소 기준을 통과할 때까지 토큰을 조정합니다.
- 브랜드 색처럼 사용자가 밝힌 요구사항은 받은 그대로 세트에 넣습니다. 글자색으로 대비를 통과하지 못하면 채움에만 쓰고 통과하는 글자색을 따로 고른 뒤 그렇게 했다고 밝힙니다.
- 최소 세트에 두 번째 강조색, 그라데이션, 장식 스타일을 더하지 않습니다. 그것은 시각 방향에 속하고 별도 산출물입니다.
- 임시 세트는 임시라고 밝혀 넘깁니다. 구현자는 사용자가 받아들이기 전까지 그것을 프로젝트의 디자인 시스템으로 취급하지 않습니다.

## 5. 라이트와 다크

- 테마마다 자체 토큰 열을 가진 별도 브리프와 이미지입니다.
- 다크 토큰은 반전하지 않고 고릅니다. 순수한 검정이 아닌 어두운 배경, 배경보다 한 단계 밝은 표면, 여전히 보이는 테두리, 위에 놓인 글자가 대비를 통과하도록 조정한 강조색입니다.
- 두 브리프 사이에는 Theme 줄과 Tokens 블록만 바뀝니다. 영역, 문자열, 컴포넌트는 같게 두어 두 이미지를 비교할 수 있게 합니다.
- `both`면 라이트 버전을 먼저 생성하고 검토합니다.

## 6. 수정 브리프

- 앞선 브리프를 통째로 복사합니다.
- 한 가지를 바꾸고 맨 위에 한 줄을 더합니다: `Revision <n>: <what changed and why>`.
- 실패가 콘텐츠 자리의 막대였다면 막대를 좁거나 옅게 만드는 것이 아니라 콘텐츠를 씁니다.
- 실패가 렌더링된 글자였다면 렌더링 문자열 수는 그대로 두고 철자나 자리를 고칩니다. 문자열을 줄이는 것은 최후 수단이고 첫 수단이 아닙니다.
- 실패가 세트의 화면 사이 흔들림이었다면 다른 이미지를 묘사하지 않고 흔들린 불변 요소를 더 정확히 다시 적습니다.

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| 모바일·태블릿·웹 대상, 라이트·다크 테마, 프로젝트 토큰 먼저, 없으면 색·글꼴·모서리·간격의 최소 세트 | user instruction, 2026-11-15 (new skill request) |
| 모양은 말로 서술하고 실제 비율이나 크기는 구조화된 값으로, 역할과 자리가 붙은 정확한 문자열, 브리프당 이미지 하나, 시리즈 전체에 반복하는 공통 불변 요소 | this package's image-generation skill contract, restated for screens |
| 영역 목록 안의 콘텐츠, 픽셀 뷰포트 프레임, 글자를 대신하는 막대 금지 | 이 패키지의 전후 비교 실험, `.hyper/uiux-design/quality-2026-11-15/`, 2026-11-15 |
| 토큰 세트에 적용하는 대비 최소 기준 | <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html> |

### Evidence grade

`LOCAL`: 세 논리 프레임, 캔버스 모양, 뼈대, 최소 토큰 표, 본문 크기 하한은 이 패키지가 시안용으로 고른 기본값이고 플랫폼 요구사항이 아닙니다. 프로젝트 자체의 프레임 크기와 토큰이 있으면 그것으로 대체합니다. 콘텐츠 규칙과 픽셀 프레임은 같은 모델과 같은 토큰으로 한 이 패키지 자체 비교로 뒷받침됩니다.
