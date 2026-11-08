# Rendered Evidence

browser capability가 있거나 사용자가 rendered-evidence JSON handoff를 제공할 때만 이 규칙을 읽는다.

## Capability gate

- rendered evidence를 얻기 위해 Playwright, Axe, browser, dependency를 설치하지 않는다.
- 유효한 handoff가 없으면 `static_only` 또는 `unavailable`을 보고한다. visual hierarchy, actual contrast, keyboard, accessibility, behavior pass를 주장하지 않는다.
- handoff를 인용하기 전 `scripts/collect-rendered-evidence.sh --input <capture.json>`로 검증한다.

## 최소 증거

모든 rendered observation에는 surface/URL, viewport width/height, state, locator, capture time, 그리고 bounding rectangle, overflow, computed style primitive, focus-visible observation, motion-preference observation 중 하나 이상의 관찰 사실이 필요하다.

project breakpoint가 알려져 있으면 우선하고, 없으면 375, 768, 1280 폭을 확인한다. 실제 surface가 노출한 state만 검사한다. screenshot은 hierarchy, spacing, asset fit 논의에는 쓸 수 있지만 semantic, keyboard, WCAG, end-to-end behavior claim에는 쓰지 않는다.

## Finding 경계

rendered finding에는 viewport, state, locator, captured value, 뒷받침하는 exact claim을 기록한다. 정적 finding은 observed rendered fact가 독립적으로 claim을 확인할 때만 rendered finding으로 승격한다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

capability gate와 최소 증거 필드는 이 패키지 자체 계약이다. Playwright와 Axe라는 도구 이름은 설치하지 말아야 할 대상으로만 나오며 외부 문서를 인용하지 않는다.
