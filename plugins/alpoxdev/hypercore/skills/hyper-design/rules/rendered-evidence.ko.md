# Rendered Evidence

browser capability가 있거나 사용자가 rendered-evidence JSON handoff를 제공할 때만 이 규칙을 읽는다.

## Capability gate

- rendered evidence를 얻기 위해 Playwright, Axe, browser, dependency를 설치하지 않는다.
- 유효한 handoff가 없으면 `static_only` 또는 `unavailable`을 보고한다. visual hierarchy, actual contrast, keyboard, accessibility, behavior pass를 주장하지 않는다.
- handoff를 인용하기 전 `scripts/collect-rendered-evidence.sh --input <capture.json>`로 검증한다.

## Evidence minimum

모든 rendered observation에는 surface/URL, viewport width/height, state, locator, capture time, 그리고 bounding rectangle, overflow, computed style primitive, focus-visible observation, motion-preference observation 중 하나 이상의 관찰 사실이 필요하다.

project breakpoint가 알려져 있으면 우선하고, 없으면 375, 768, 1280 폭을 확인한다. 실제 surface가 노출한 state만 검사한다. screenshot은 hierarchy, spacing, asset fit 논의에는 쓸 수 있지만 semantic, keyboard, WCAG, end-to-end behavior claim에는 쓰지 않는다.

## Coverage list

surface 전체에 대한 주장에는 표본이 아니라 모든 surface가 필요하다. 캡처 계획은 collect 단계 전에 바뀐 컴포넌트를 가진 각 page, route, tab, modal, scroll position과 그 컴포넌트를 공유하는 모든 sibling surface를 이름으로 나열한다.

locator와 state가 자신이 보여 주는 surface를 밝혀야 캡처가 목록에 든다. coverage list는 요약이 아니라 체크리스트다. 각 항목이 자기 판정을 가지며 "대부분"은 항목이 아니다. 빠진 항목은 검사한 것이 아니다. 통과 규칙은 완전한 범위에서 모든 항목이 통과하는 것이므로, 빠지거나 실패한 항목이 하나라도 있으면 검토는 열린 채로 남는다.

공유 컴포넌트를 건드린 변경이면 그 컴포넌트를 쓰는 sibling surface가 수정되지 않았어도 목록에 들어간다. 같은 값을 읽는 sibling은 같은 방식으로 다시 확인한다.

## Freshness and hygiene

`capturedAt`이 소스 파일의 가장 늦은 수정 시각보다 이른 캡처는 `stale`이며 아무것도 증명하지 못한다. stale 결과는 캡처와 두 시각을 함께 밝히므로, 코드 수정이 아니라 새 캡처로 해결한다. 그 시각과 같거나 늦은 캡처는 이 규칙에서 stale이 아니다.

캡처 위생은 캡처마다 필드를 확인하는 일이다.

- **fileSignature.** 캡처가 파일 이름과 `fileSignature` 값을 가지면, signature는 이미지 형식을 뜻하며 파일 확장자와 맞아야 한다. `.png` 파일에 JPEG signature가 붙으면 무효이고, 다른 조합도 마찬가지다.
- **frameKind.** page 캡처는 `frameKind: page`다. window 캡처는 `frameKind: window`이며 page 증거가 아니다.

`collect-rendered-evidence.sh`는 `sourceMtime`, `fileSignature`, `frameKind`를 검증하고 stale이거나 무효인 캡처를 보고한다. 캡처에 기록한 dimensions는 선언한 viewport와 대조하며, 어긋나면 고쳐 주는 것이 아니라 finding으로 남긴다.

```json
{
  "viewport": { "width": 375, "height": 800 },
  "state": "default",
  "capturedAt": "2026-09-03T12:00:00Z",
  "sourceMtime": "2026-09-02T09:30:00Z",
  "frameKind": "page",
  "file": "settings-375.png",
  "fileSignature": "png",
  "dimensions": { "width": 375, "height": 800 },
  "observations": [
    { "locator": "main", "rect": { "x": 0, "y": 0, "width": 375, "height": 720 } }
  ]
}
```

`sourceMtime`은 ISO date-time 하나 또는 그 배열을 받고, 가장 늦은 값이 stale 판정을 정한다. `fileSignature`는 `png` 또는 `jpeg`이며, `.jpg`나 `.jpeg` 파일에는 `jpg`도 받는다.

## Finding boundary

rendered finding에는 viewport, state, locator, captured value, 뒷받침하는 exact claim을 기록한다. 정적 finding은 observed rendered fact가 독립적으로 claim을 확인할 때만 rendered finding으로 승격한다.

## Measurement contract

handoff에 measurement field(contrast pair, font size, rectangle pair, overflow)가 있으면, `collect-rendered-evidence.sh`는 locator를 포함한 finding으로 4.5 미만의 contrast, 4px 초과 text-on-text overlap, 2px 초과 horizontal overflow를 계산한다. 정의는 `references/rendered-measurements.md`, field는 `references/browser-evidence-schema.md`를 참조한다.

## Chart geometry checks

차트 산출물(`references/chart-artifact.md`)에서는 렌더링 결과로 세 가지 기하 검사를 측정한다.

1. 가장 큰 막대의 렌더링 높이는 `value / axisMax * plotHeight`에서 **1px** 이내다.
2. 범례 스와치의 computed color는 그 스와치가 가리키는 시리즈 색과 같다.
3. 첫 번째와 마지막 축 라벨은 플롯 상자 가장자리에서 잘리지 않고 안에 있다.

렌더링 측정값이 없으면 이 세 검사는 `unverified`이며 통과가 아니다.

measurement field가 없으면 status는 `not_run`이며 절대 pass가 되지 않는다. failing 측정값 하나라도 있으면 rendered evidence로는 통과하지 않는다.

## Sources

> 확인 2026-11-09.

| 주장 | 출처 |
|---|---|
| surface별 coverage list, 소스보다 이른 캡처를 stale로 보는 판정, page 전용 frame 검사의 아이디어 | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), 이 패키지 자체 문장으로 재작성했다. 원본 저장소에는 라이선스가 없으며 텍스트나 코드를 복사하지 않았다 |
| capability gate, 최소 증거 필드, `static_only` / `unavailable` 보고 규칙 | 위 절에 적힌 이 패키지 자체 계약 |
| PNG 파일 시그니처 `\x89PNG\r\n\x1a\n` | <https://www.w3.org/TR/png-3/> (§5.2 PNG file signature) |
| JPEG 이미지 시작 마커 `\xFF\xD8\xFF` | JPEG 규격의 SOI 마커이며 상수로만 기록했다. 페이지를 가져오지 않았고 수집기는 이 선두 바이트만 대조한다 |
| measurement contract 임계값 | 이 패키지의 `references/rendered-measurements.md` |

### Evidence grade

coverage list의 형태, stale 판정, `page` frame 요구는 라이선스가 없는 원본에서 아이디어만 받아 이 패키지 계약으로 재작성한 것이다. 두 파일 시그니처는 규범 형식 상수이며, 수집기는 선두 바이트만 대조하고 파일 나머지에 대해서는 아무것도 주장하지 않는다.
