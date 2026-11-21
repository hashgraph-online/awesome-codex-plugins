# Rendered Measurements

렌더링된 증거 handoff를 검토할 때나 주장이 브라우저가 그린 무엇을 기반으로 할 때 이 문서를 읽는다. 정적 소스 검토는 contrast, 글자 크기, spacing rhythm, overlap, overflow를 측정하지 않는다. 이 값들은 browser capability가 만든 경우에만 숫자가 된다.

## 1. What a renderer must produce

측정값을 주장하는 browser capability는 **MUST** 숫자를 만들어야 한다. 각 capture는 viewport width/height, surface state, 그리고 확인한 각 폭에서의 observation 값을 기록한다. 기본 확인 폭은 375, 768, 1280 CSS px이고 모든 layout이 져야 하는 320px 리플로 검사를 함께 본다. 이 폭 집합은 `rules/craft-floor.md` §4가 소유하며, 알려진 project breakpoint가 있으면 그 값을 우선한다.

- computed foreground와 painted background color pair를 `#rgb` 또는 `#rrggbb` hex로 기록한다. background는 글자 아래 실제로 칠해진 색이며 scrim을 포함한다. foreground를 먼저 쓴다.
- text role별 computed font size(`display`, `heading`, `body`, `caption`, `control`)를 CSS px로 측정해 기록하며, stylesheet에서 읽은 값이 아니라 layout에서 측정한 값이다.
- 각 heading과 그 첫 content block 사이의 vertical gap을 CSS px로 기록한다.
- overlap 검사에 사용할 element rectangle을 기록한다: text box(`textRect`)와 container box(`rect`)이며, 각각 `x`, `y`, `width`, `height`를 가진다.
- 확인한 각 폭에서의 horizontal overflow를 viewport edge를 넘은 CSS px 수로 기록하며, stress string(길게 끊기지 않은 토큰)을 함께 넣어 wrapping이 동작하게 한다.
- 사용한 정확한 `stressString` 값을 기록하여 다른 렌더러가 같은 측정을 반복할 수 있게 한다.

측정값이란 locator와 viewport가 함께 있는 숫자만이 된다. screenshot은 spacing과 asset fit 논의에 쓸 수 있지만, contrast, 글자 크기, overlap, overflow의 증거가 절대 되지 않는다.

## 2. Thresholds the collector applies

`scripts/collect-rendered-evidence.sh`는 이 숫자들에서 세 종류의 finding을 계산한다. 각 finding은 locator, viewport, state, 측정한 값, threshold, 실패 여부를 가진다.

- **Contrast.** 선형화된 relative luminance를 이용한 WCAG 2.x ratio `(L1 + 0.05) / (L2 + 0.05)`를 jq에서 contrast-check awk 명령과 같은 `0.03928` linearization 임계값으로 계산한다. 4.5 미만이면 일반 텍스트 pair는 failing이 된다. 반올림하지 않은 ratio가 판정하며, 저장되는 `ratio`는 표시용으로 반올림한 값이다.
- **Overlap.** 같은 capture 안에서 서로 다른 두 observation의 `textRect`가 공유하는 가로·세로 확장 중 작은 값을 계산한다. text-on-text overlap이 4 CSS px를 초과하면 failing이 된다.
- **Overflow.** 확인한 폭에서 numeric `overflowX`가 2 CSS px를 초과하면 failing이 되며, finding에 그 width를 기록한다.

## 3. When measurements do not exist

browser capability가 없거나, handoff에 측정 field가 하나도 없으면 측정 status는 근거(reason)와 함께 `not_run`이 된다. 절대 pass가 되지 않는다. 모든 임계값을 만족한 측정값을 가진 handoff는 값을 보고하고 통과하며, 실패한 측정값이 하나라도 있으면 rendered evidence로는 통과하지 않는다.

## Sources

> 확인 2026-11-09.

| 주장 | 출처 |
|---|---|
| 상대 휘도, `0.03928` 선형화 임계값, 대비 비율, 일반 텍스트의 4.5:1 임계값 | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (상대 휘도와 대비 비율의 정의) |
| 렌더링 측정값 집합을 숫자로 된 finding에 대한 linter로 보는 아이디어 (칠해진 배경 위의 contrast, 계산한 글자 크기, overlap, overflow) | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), 이 패키지 자체 문장으로 재작성했다. 원본 저장소에는 라이선스가 없으며 텍스트나 코드를 복사하지 않았다. |
| 4px overlap과 2px overflow finding 임계값, 측정값이 없을 때 `not_run`으로 두는 규칙 | 이 패키지 자체 선택이며 위 §2와 §3에 적혀 있다. |

### Evidence grade

contrast 공식은 규범 WCAG 2.2이며, 계산 예시 값(`#999999` on `#ffffff` = 2.85, `#000000` on `#ffffff` = 21.00)은 `contrast-check.md`의 기준 표에서 재현할 수 있다. overlap과 overflow 임계값은 이 패키지 자체 계약이며, WCAG 요구사항이 아니다.
