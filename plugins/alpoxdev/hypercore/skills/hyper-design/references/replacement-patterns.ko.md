# 대체 패턴

confirmed `clean` 또는 `restyle` finding에 구조 또는 presentation 대안이 필요할 때만 이 참고 문서를 읽는다. 이 목록은 visual direction의 기본값이 아니라 선택지다. `restyle`은 `brief.md`에서 방향을 가져온다.

모든 대체안은 실제 data, copy, link/action, semantic, focus order, responsive behavior를 보존한다. 검증할 수 없으면 `ask` 또는 `block`한다.

| Rule/pattern | 고려할 대안 | 보존 / 사용하지 않을 때 | 검증 |
|---|---|---|---|
| 동일 feature-card cluster | primary feature 하나 + supporting list, task workflow, typographic list | 실제 peer data와 모든 CTA 보존; 실제 비교를 바꾸지 않음 | desktop/mobile order, keyboard order, action |
| 장식적 New/pulse dot | 날짜가 있는 static release label 또는 제거 | recording/live/sync/unread state와 accessible text 보존 | state semantic, reduced motion |
| 근거 없는 metric/proof | local provenance가 있는 proof 또는 제거 | metric, testimonial, logo, customer, promise를 발명하지 않음 | source provenance, localization/legal contract |
| Fake chrome | caption이 있는 실제 screenshot 또는 context가 있는 asset | alt text와 product context 보존 | asset meaning, responsive fit |
| Card in card | 실제 grouping/interaction 의미가 있는 경계 하나만 유지 | clickable/form boundary를 평면화하지 않음 | focus ring, hit target, mobile spacing |
| Gradient headline | 기존 confirmed primary ink 또는 solid accent token | 문서화된 brand/reference gradient 보존 | 가능할 때 rendered hierarchy/contrast |
| Side stripe + wide shadow | 의미 있는 state/accent boundary 하나 | 문서화된 elevation/state meaning 보존 | state distinction, dark mode, focus |
| Grid/radial/glow background | 제품 세계의 material 또는 quiet surface | 실제 map/canvas/blueprint context 보존 | content legibility, asset purpose |
| 장식적 monospace | 역할에 맞는 body/display token 또는 실제 icon system | code, ID, log, measurement, system state 보존 | readability, accessible name |
| Generic motion | state-linked transform/opacity + reduced-motion alternative | 실제 feedback/task state change 보존 | hover/focus/state, reduced motion |

대체 패턴으로 새 brand world를 만들거나, 정보 구조를 바꾸거나, proof를 발명하지 않는다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

대체 패턴은 공개된 pattern library가 아니라 이 패키지 자체 선택지이며, 각 항목은 패키지의 보존 규칙으로 제한된다.
