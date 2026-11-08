# 수정 Playbook

확인된 finding과 일치하는 항목만 읽는다. 시각적 차별화를 최적화하기 전에 brief, content, data shape, semantics, behavior를 보존한다.

## Gradient headline

1. brief, brand token, 명시적 reference가 gradient typography를 요구하는지 확인한다.
2. 요구되면 `preserve`하고 예외를 기록한다.
3. 아니면 기존 primary ink 또는 확인된 solid accent token으로 교체한다.
4. 렌더링 화면에서 contrast와 hero hierarchy를 확인한다. 렌더링이 없으면 hierarchy를 미검증으로 보고한다.

## Purple gradient

1. 가능하면 색을 명명된 project token에 연결한다.
2. 문서화된 brand gradient는 보존한다.
3. 근거 없는 gradient는 기존 solid surface/accent 또는 brief에 맞는 절제된 조합으로 바꾸되 새 palette를 발명하지 않는다.
4. contrast, dark mode, 인접 state style을 확인한다.

## Decorative orb, pill, dot, label, proof

1. content, interaction, state, semantic, brand, analytics, layout 역할을 확인한다.
2. 역할이 없고 source/DOM/brief 근거가 high-confidence일 때만 제거한다.
3. 의미 있는 accessible name과 status signal을 보존한다.
4. 제거 후 spacing, pointer event, contrast, layout shift/LCP 영향, responsive fit을 확인한다.

## 동일한 feature card 3개

1. 실제 3개 peer 또는 명시적 비교 요구인지 확인한다. 맞으면 개수를 보존한다.
2. value proposition 반복이라면 primary feature 1개+supporting list, 2-column zig-zag, asymmetric grid, typographic list, overflow가 상호작용 일부일 때만 intentional carousel 순으로 검토한다.
3. copy, link, action, reading order, semantics, data mapping을 보존한다.
4. desktop/mobile layout, keyboard order, CTA 위치, detector 출력을 확인한다.

## Card in card

1. 실제 grouping, interaction, elevation 의미를 가진 경계를 식별한다.
2. 중복 presentation wrapper만 제거하고 semantic group·clickable region은 flatten하지 않는다.
3. 남은 경계에 padding과 focus treatment를 유지한다.
4. DOM nesting, hit target, focus visibility, mobile spacing을 확인한다.

## `transition-all`

1. hover/focus/active/state style에서 실제 변하는 property를 열거한다.
2. `all`을 `color`, `background-color`, `border-color`, `opacity`, `transform` 등 의도된 property로 교체한다.
3. visible focus를 늦추는 focus-ring transition은 사용하지 않는다.
4. interaction state와 reduced-motion behavior를 확인한다.

## Layout property animation

동일한 동작과 reading order를 유지할 때만 transform/opacity를 우선한다. mechanics 변경이 state·layout correctness를 위협하면 자동 재작성하지 말고 보고·질문한다.

## Placeholder copy 또는 unsupported metric

1. local product source, fixture, CMS/data wiring, brief에서 provenance를 찾는다.
2. 기능 fixture가 아닌 명백한 placeholder decoration이면 대체 claim을 발명하지 말고 unsupported block을 제거한다.
3. metric, testimonial, logo, customer, product promise를 만들지 않는다.
4. copy가 test, localization, data contract, legal review에 참여하면 보존하고 질문한다.

## Fake browser/phone/IDE chrome

실제 screenshot을 감싸거나 제품 맥락을 전달하면 보존한다. 아니면 실제 asset, caption, alt text, layout semantic을 유지한 채 장식 control만 제거한다. 남은 asset이 목적을 전달하는지 확인한다.

## Focus/reduced motion/alt 누락

미적 slop이 아닌 품질 guard로 처리한다. 프로젝트 접근성 관습과 관찰 가능한 동작을 따른다. image가 informative인지 decorative인지 판단한 뒤 descriptive alt 또는 empty alt를 선택한다. source 검사만으로 전체 accessibility를 통과했다고 하지 않는다.

## 반복 section scaffold, glow, grid, monospace, pulse, heading skip

1. pattern이 명시 sequence, code/data/state treatment, 문서화된 elevation/material system, brand commitment가 아닌지 확인한다.
2. 구조 대안을 제안하기 전 `replacement-patterns.ko.md`를 읽고 data, action, semantic, focus order, responsive behavior를 보존한다.
3. `candidate` exception을 preserve evidence로 취급한다. finding을 suppress하거나 인접 brand/data 선택을 바꾸지 않는다.
4. heading order는 level을 바꾸기 전 component composition을 확인한다. pulse/motion은 state communication과 reduced-motion behavior를 보존한다.
5. 검증된 rendered handoff가 viewport/state/locator 사실을 확인하지 않는 한 static-only limitation을 보고한다.

## Baseline, waiver, rendered handoff

1. baseline은 detector v2 finding만 비교하며 design choice를 승인하지 않는다. `--only-new` 전 `rules/waivers-and-baselines.ko.md`를 읽는다.
2. optional waiver는 `validate-waivers.sh`로 검증한다. 좁은 범위, reason, source가 있어야 하며 P0 또는 protected contract를 숨길 수 없다.
3. 제공된 browser fact는 `collect-rendered-evidence.sh`로 검증한다. capture된 viewport/state/locator observation만 사용한다.
4. 이 input을 얻기 위해 tooling을 설치하거나 consumer config file을 쓰지 않는다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

수정 단계는 anti-pattern 목록과 safe-editing 규칙에서 나온 이 패키지 자체 guidance다. 외부 디자인·접근성 출처는 참조하지 않았다.
