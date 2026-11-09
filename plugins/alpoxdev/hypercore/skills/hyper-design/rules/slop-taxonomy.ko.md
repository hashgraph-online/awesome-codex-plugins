# Slop 분류 체계

finding을 분류하기 전에 읽는다. 이 파일은 finding class, rule ID, cluster 묶음을 소유한다.

## Finding classes

| Class | 의미 | 기본 처리 |
|---|---|---|
| `hard-gate` | 접근성, 동작, 보안 또는 명백한 responsive 실패 | 작업 권한에 따라 수정하거나 block하며 취향으로 축소하지 않음 |
| `default-risk` | 반복되는 AI 기본값과 강하게 닮았지만 의도적일 수 있음 | brief·정체성을 확인하고 근거가 있을 때만 교체 |
| `review-only` | specificity, 취향, 감정적 인상, 구조처럼 사람·agent 판단이 필요함 | caveat와 함께 보고하며 자동 수정 금지 |
| `informational` | 변경은 필요 없지만 유용한 관찰 | 관련 있을 때만 기록 |

## Registry scopes

- `universal`: 시각 취향과 무관한 안정적 품질·접근성 guard.
- `default-risk`: 정당한 brief·brand 예외가 있는 의심스러운 기본값.
- `context-dependent`: page type, domain, audience, data shape, brief가 필요함.
- `review-only`: 정적 일치만으로 gate가 될 수 없음.

## Categories

- `structure`: 반복 hero, feature grid, card, navigation, footer, bento, sidebar, section fingerprint.
- `surface`: gradient, glow, orb, decorative pill, status dot, side stripe, 획일적 radius/shadow, 임의 token.
- `typography-copy`: generic type 조합, cliché, placeholder 이름·brand, 근거 없는 metric·claim, 반복 eyebrow.
- `motion-interaction`: `transition-all`, 무차별 scale/reveal, layout animation, reduced motion 누락, hover-only affordance.
- `quality`: contrast/focus/semantic/responsive 결함, fake chrome, 렌더링 증거 없는 주장.

## 증거와 exception status

- `detection confidence`는 engine이 source, context, DOM, rendered signature를 얼마나 확실하게 찾았는지다.
- `remediation confidence`는 finding을 brief 또는 protected contract 위반 없이 바꿀 수 있는 확실성이다.
- `candidate` exception은 명시 local brand, data, real-state evidence가 preserve를 뒷받침한다는 뜻이다. review를 위해 계속 보이며 rule을 suppress하거나 auto-fix 권한을 주지 않는다.
- `generic-output risk`는 context-confirmed cluster를 바탕으로 한 `low`, `medium`, `high` 우선순위다. AI가 인터페이스를 작성했다는 증거가 아니다.

## 필수 예외 확인

- 명시적으로 요구한 브랜드 색, gradient, font, reference는 기본적으로 slop이 아니다.
- 실제 데이터가 3개 동등 비교 대상이거나 사용자가 요구하면 3-column은 slop이 아니다.
- 의료, 금융, 공공, B2B 관습은 반복된다는 이유만으로 generic이 아니다.
- 정적 일치는 visual hierarchy, contrast, usability, intent를 증명하지 못한다.
- 약한 신호가 여러 개여도 단순 합산으로 결정적 증거가 되지 않는다.

## 처리

Finding마다 정확히 하나를 선택한다.

- `remove`: 고신뢰 근거가 있는 무근거 장식 또는 placeholder.
- `replace`: 위험 패턴 근거가 있고 brief에 맞는 대안이 콘텐츠와 동작을 보존함.
- `preserve`: brand, brief, data, function이 패턴을 정당화함.
- `ask`: 사용자 결정이 안전한 결과를 실질적으로 바꿈.
- `block`: evidence, scope, authority가 부족함.

## 동시 출현과 generic-output risk

패턴 하나는 잡음이다. 그라디언트 하나, Inter 제목 하나, 카드 세 개는 각각 실제 결정일 수 있다. generic-output risk는 브리프, 브랜드, 데이터가 설명하지 않는 기본값이 함께 나타날 때 생긴다.

| 한 화면에서 설명되지 않은 `default-risk` 또는 `context-dependent` 발견 사항 | generic-output risk |
|---|---|
| 0-1 | `low` |
| 2-3 | `medium` |
| 4 이상 | `high` |

발견 사항은 예외 상태가 `not-checked`이거나 확인에서 뒷받침 근거를 찾지 못했을 때만 센다. `review-only` 발견 사항은 검토에 정보를 주지만 단독으로 등급을 올리지 않는다. 등급은 작업 순서를 정할 뿐 AI 저작을 증명하지 않는다.

## 고르지 않은 기본값과 표류

- 판단 대상은 스타일의 존재가 아니라 결정의 부재다. 브리프, 참조, 프로젝트 시스템 어디에서도 값의 이유를 대지 못하면 그 값은 발견 사항이다.
- 기본값 목록은 움직인다. 보라색 그라디언트, 글래스, 네온 글로우는 크림 배경에 이탤릭 세리프 디스플레이, 벤토 그리드, 에메랄드 강조색, 네오브루탈리즘 하드 섀도를 쓰는 쪽으로 넘어갔다. 한 기본값을 그 후속 기본값으로 바꾸는 것은 수정이 아니다. `references/anti-pattern-catalog.md`가 두 물결을 모두 나열한다.
- 카탈로그의 모든 규칙은 예외를 유지한다. 문서화된 브랜드 값, 실제 데이터 형태, 실제 상태는 규칙보다 우선한다.
- 모든 기법에 던질 질문은 그것이 무엇을 위해 쓰이는가다. 그라디언트, 글래스, 배지, 카드 그리드는 도구다. 발견 사항이 되는 것은 목적을 적지 않고 쓴 기법이거나 사용량 상한을 넘긴 기법이다(`rules/delivery-gate.md` §5).

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 발견 사항 등급, registry scope, 분류, 처리 방식 | 이 패키지 자체 어휘; 번들 rule registry가 같은 이름을 구현한다 |
| 일치 하나는 잡음이고 여러 개가 모이면 서명이다; 결정의 부재를 판단한다; 보라색이 크림과 이탤릭 세리프로 이동한다 | <https://github.com/febbhav/signs-of-ai-design/tree/854b46f18dee5cc174d45cec8cd4f3142fe46984> (CC BY-SA 4.0) |
| 1,590개 사이트에서 결정적 패턴 검사를 등급으로 세기(4개 이상 high, 2-3개 medium, 0-1개 low), 수동 검토 시 거짓 양성 약 5-10% | <https://www.adriankrebs.ch/blog/design-slop/> (2026-04-20) |
| 기본값의 세 시대(보라와 글래스, 베이지 에디토리얼, 네오브루탈리즘) | <https://impeccable.style/slop/> |
| 옛 기본값(indigo)이 금지된 뒤 새 기본값(emerald)이 등장 | <https://solodesign.cc/blog/ai-design-slop-the-tells/> (2026-06-06) |
| 기법 자체가 아니라 목적 없는 기법을 거부한다 | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Core Principle; MIT) |

### Evidence grade

등급 임계값은 규칙 세트가 다른 공개 점수 연구 하나에서 온 것이다. 작업 순서를 정하는 시작점이며 보정된 분류기가 아니다.
