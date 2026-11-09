# Anti-pattern 목록

Detector 출력이나 렌더링 관찰을 rule에 연결할 때만 이 목록을 읽는다. Registry는 판단 보조이며 보편적 금지 목록이 아니다. `autofix`는 명시된 예외 확인 후에만 결정적 대체가 안전할 수 있다는 뜻이다.

## 목차

- 규칙 표
- Registry 해석
- 두 번째 물결과 검토 날짜
- Sources

## 규칙 표

| ID | Category | Scope | 기본 severity | Static | Autofix | Pattern과 예외 |
|---|---|---|---|---:|---:|---|
| `surface.gradient-text` | surface | default-risk | P2 | yes | no | Gradient clip headline; 명시적 brand/reference typography 보존 |
| `surface.purple-gradient` | surface | default-risk | P2 | yes | no | Purple→blue/pink gradient; 문서화된 brand token 보존 |
| `surface.random-glow` | surface | review-only | P3 | no | no | hierarchy·brand 역할 없는 glow |
| `surface.decorative-orb` | surface | default-risk | P2 | partial | yes | content, interaction, semantic, brand 역할 없는 orb/blob |
| `surface.thick-side-stripe` | surface | default-risk | P2 | yes | no | 의미 없는 두꺼운 card edge |
| `surface.thin-side-stripe` | surface | default-risk | P2 | yes | no | 둥근 모서리나 카드형 상자의 얇은 한쪽 테두리; state나 브랜드 의미를 담는지 확인한다 |
| `surface.pseudo-stripe` | surface | default-risk | P2 | yes | no | 단색 배경의 1–6px `::before`/`::after` 바; state나 브랜드 의미를 담는지 확인한다 |
| `surface.inset-stripe` | surface | default-risk | P2 | yes | no | 한쪽 가장자리만 그리는 `inset` box-shadow; state나 브랜드 의미를 담는지 확인한다 |
| `surface.gradient-border-image` | surface | default-risk | P2 | yes | no | 그라디언트 `border-image`; state나 브랜드 의미를 담는지 확인한다 |
| `surface.hard-stop-band` | surface | default-risk | P2 | yes | no | 하드 스톱 선형 그라디언트 밴드; state나 브랜드 의미를 담는지 확인한다 |
| `surface.uniform-radius` | surface | context-dependent | P3 | no | no | 모든 hierarchy level의 동일 radius; design-system token 예외 |
| `surface.uniform-shadow` | surface | context-dependent | P3 | no | no | 모든 곳의 동일 elevation; 명시적 elevation system 예외 |
| `surface.status-dot` | surface | default-risk | P3 | partial | yes | state·legend 없는 dot |
| `surface.version-label` | surface | default-risk | P3 | partial | yes | 제품 의미 없는 장식용 “v2.0/new” label |
| `surface.decorative-pill` | surface | default-risk | P3 | no | yes | category, state, action 역할 없는 pill |
| `surface.token-drift` | surface | default-risk | P2 | no | no | 확인된 token 밖 literal color/font; local 예외 가능 |
| `structure.three-equal-cards` | structure | context-dependent | P1 | partial | no | 동일 icon-heading-copy 카드 3개; 실제 3개 peer 비교 보존 |
| `structure.card-in-card` | structure | default-risk | P2 | yes | no | semantic grouping 없는 presentation card 중첩 |
| `structure.centered-hero` | structure | review-only | P3 | no | no | 반복 centered hero; page purpose 예외 |
| `structure.template-sequence` | structure | review-only | P2 | no | no | 제품별 IA 없는 Hero→3 features→CTA→footer |
| `structure.ai-nav` | structure | review-only | P3 | no | no | wordmark-left, links-middle, CTA-right fingerprint |
| `structure.ai-footer` | structure | review-only | P3 | no | no | generic Product/Company/Resources/Legal 4열 footer |
| `structure.bento-without-ia` | structure | context-dependent | P2 | no | no | priority·data와 무관한 bento 배치 |
| `copy.placeholder-person` | typography-copy | default-risk | P1 | yes | yes | John/Jane Doe 또는 명백한 fake testimonial identity |
| `copy.placeholder-brand` | typography-copy | default-risk | P1 | yes | yes | Acme/Nexus/SmartFlow형 placeholder를 실제 brand처럼 사용 |
| `copy.cliche` | typography-copy | context-dependent | P3 | yes | no | Elevate, seamless, next-gen, unleash, game-changer; 인용·domain 예외 |
| `copy.unsupported-metric` | typography-copy | default-risk | P1 | partial | yes | local source 없는 percentage·metric claim |
| `copy.unsupported-proof` | typography-copy | default-risk | P1 | no | yes | source 없는 testimonial, trust badge, proof bar, claim |
| `motion.transition-all` | motion-interaction | universal | P2 | yes | yes | broad transition; 실제 바뀌는 property로 교체 |
| `motion.layout-property` | motion-interaction | universal | P1 | yes | no | top/left/width/height/margin/padding animation |
| `motion.missing-reduced-motion` | motion-interaction | universal | P1 | partial | no | 큰 motion에 reduced-motion path 없음 |
| `motion.scale-everywhere` | motion-interaction | default-risk | P2 | yes | no | 무관한 control/card의 동일 hover scale |
| `motion.hover-only` | motion-interaction | universal | P1 | no | no | 필수 affordance·content가 hover에서만 제공됨 |
| `quality.missing-focus-visible` | quality | universal | P1 | no | no | visible control의 focus 억제 후 명확한 대체 없음 |
| `quality.missing-alt` | quality | universal | P1 | partial | no | informative image alt 누락; decorative image는 empty alt 가능 |
| `quality.mobile-overflow-risk` | quality | universal | P1 | no | no | fixed/min-width overflow 가능성; 렌더링 확인 필요 |
| `quality.fake-chrome` | quality | default-risk | P2 | yes | no | 근거 없는 장식용 browser/phone/IDE/terminal chrome |
| `structure.repeated-eyebrow` | structure | review-only | P3 | yes | no | 반복 eyebrow/kicker signature; 실제 hierarchy/sequence를 전달하면 보존 |
| `structure.numbered-section-label` | structure | context-dependent | P3 | yes | no | 01/02/03 marker; 사용자가 따라야 할 sequence면 보존 |
| `structure.identical-icon-card-cluster` | structure | context-dependent | P2 | yes | no | 세 feature-card/icon-tile signature; 실제 peer data/action 보존 |
| `surface.radial-glow` | surface | review-only | P3 | yes | no | Radial glow signature; 목적 있는 lighting/brand material 보존 |
| `surface.grid-background` | surface | review-only | P3 | yes | no | 반복 gradient grid; 실제 map/canvas/blueprint context 보존 |
| `surface.border-plus-wide-shadow` | surface | context-dependent | P3 | yes | no | Border와 wide shadow 조합; 문서화된 elevation system 보존 |
| `type.decorative-monospace` | typography-copy | default-risk | P3 | yes | no | 장식적 technical language와 monospace; code, ID, log, measurement, 실제 state 보존 |
| `motion.pulse-without-state` | motion-interaction | default-risk | P2 | yes | no | Pulse signature; recording, sync, unread, notification, live state 보존 |
| `quality.heading-skip` | quality | universal | P2 | yes | no | 정적 h1→h3 heading skip; component composition은 review 필요 |
| `type.unchosen-default-font` | typography-copy | default-risk | P3 | no | no | Inter, Roboto, 시스템 스택, 유행하는 디스플레이 서체를 브리프나 시스템에 이유 없이 모든 곳에 사용; 문서화된 브랜드 서체는 보존 |
| `type.font-not-shipped` | quality | universal | P2 | no | no | 선언한 서체를 빌드가 로드하지 않아 화면이 조용히 폴백; 의도적으로 선언한 시스템 스택은 보존 |
| `surface.second-wave-default` | surface | review-only | P3 | no | no | 첫 물결의 모습에서 벗어나려고 크림 배경에 이탤릭 세리프 디스플레이, 에메랄드 "안전한" 강조색, 네오브루탈리즘 하드 오프셋 섀도를 쓰는 경우; 브리프나 참조가 요구하면 보존 |
| `structure.bento-escape` | structure | context-dependent | P2 | no | no | 타일 크기가 우선순위나 데이터를 따르지 않는 벤토 그리드; 실제 우선순위를 담은 벤토는 보존 |
| `copy.ai-sparkle` | typography-copy | default-risk | P3 | no | no | 반짝임, 마술봉, 별 아이콘과 "AI 색"으로 쓰는 보라색; 브랜드가 이미 그 표식을 쓰면 보존 |
| `quality.missing-states` | quality | universal | P1 | no | no | 로딩, 빈 상태, 오류 상태가 없거나 비어 있음; 화면이 그 상태에 도달할 수 없을 때만 의도적 부재를 보존 |
| `quality.contrast-below-floor` | quality | universal | P1 | no | no | 텍스트나 필요한 비텍스트 요소가 대비 기준 아래; 렌더링이나 토큰 계산으로 확인해야 함 |
| `structure.mockup-boxed` | structure | review-only | P2 | no | no | 연출 제품 창을 고른 여백으로 카드에 축소; 슬롯 자체가 카드 썸네일이면 보존 |
| `quality.focus-suppressed` | quality | universal | P1 | yes | no | `outline: none` 또는 `focus:outline-none` 소스 서명; 똑같이 잘 보이는 `:focus-visible` 대체가 있으면 보존 |
| `quality.zoom-blocked` | quality | universal | P1 | yes | no | `user-scalable=no`나 `maximum-scale=1`이 들어간 viewport meta; 예외 없음 |
| `quality.clickable-div` | quality | universal | P1 | yes | no | 클릭 핸들러가 붙은 `div`나 `span`; role, 상태 속성, 키보드 지원을 갖춘 사용자 정의 컨트롤만 보존 |
| `quality.dead-anchor` | quality | universal | P2 | yes | no | 목적지가 없는 `href="#"`; `#id`로 쓴 실제 페이지 내 앵커는 보존 |
| `quality.media-unsized` | quality | universal | P2 | yes | no | width, height, aspect-ratio가 없는 `img`, `video`, `iframe`; 요소의 CSS가 종횡비를 정하면 보존 |
| `copy.em-dash` | typography-copy | default-risk | P3 | yes | no | 소스 텍스트의 엠대시; 인용한 원문과 소유자가 승인한 문장 견본은 보존 |
| `copy.generic-cta` | typography-copy | context-dependent | P3 | yes | no | 라벨이 "Get started", "Learn more", "Try now", "Explore", "Discover"인 경우; 브랜드 가이드가 요구하는 라벨은 보존 |
| `structure.viewport-height` | structure | context-dependent | P3 | yes | no | `100vh`나 `h-screen` 섹션; 모바일에서 `dvh`를 쓰는 의도된 전체 화면 보기는 보존 |
| `quality.dead-control` | quality | universal | P1 | no | no | 실제 동작이 없는 버튼, 링크, 드롭다운, 폼, 또는 목적지가 없는 내비게이션 항목; 눈에 보이게 라벨을 붙인 "Coming soon"은 보존 |
| `quality.theme-broken` | quality | universal | P1 | no | no | 출시한 라이트 또는 다크 테마가 대비, 글꼴, 레이아웃을 깨뜨림 |
| `quality.patch-script` | quality | universal | P1 | no | no | 문자열 치환으로 소스나 CSS를 다시 쓰는 스크립트로 추가한 기능 |
| `copy.fabricated-claim` | typography-copy | universal | P1 | no | no | 근거 없는 보안, 규정 준수, 성능, 고객 주장 |
| `copy.assumed-asset` | typography-copy | default-risk | P1 | no | no | 확인 없이 최종본으로 만든 로고, 아바타, 제품 표시, 사람 사진; 라벨을 붙인 자리 표시는 보존 |
| `copy.emoji-decoration` | typography-copy | default-risk | P3 | no | no | 제목, 목록, 배지, 버튼의 이모지; 사용자 콘텐츠인 이모지는 보존 |
| `structure.template-faq` | structure | universal | P2 | no | no | 이 제품의 사용자가 묻지 않은 템플릿 질문으로 만든 FAQ |
| `structure.uniform-rhythm` | structure | context-dependent | P2 | no | no | 모든 섹션이 같은 제목 + 부제 + 카드 그리드; RHYTHM 1이 선언된 선택이면 보존 |
| `structure.alternating-background` | structure | review-only | P3 | no | no | 섹션 사이의 유일한 변화가 배경색 |
| `structure.three-step-default` | structure | context-dependent | P3 | no | no | "작동 방식"이 언제나 번호 붙은 둥근 아이콘 셋; 실제 과정이 세 단계면 보존 |
| `structure.pricing-default` | structure | context-dependent | P2 | no | no | 실제 요금제와 무관하게 3단계에 가운데 "Most popular" 배지; 실제 요금제 수와 이유 있는 강조는 보존 |
| `structure.demo-without-product` | structure | default-risk | P1 | no | no | 작동하는 모습을 보여 주지 않는 제품 판매 페이지, 또는 약관이나 개인정보 페이지가 없는 가입 |
| `structure.skeleton-product-shot` | structure | default-risk | P2 | no | no | 히어로나 기능 "스크린샷"으로 쓴 스켈레톤 막대 |
| `structure.dashboard-shell` | structure | context-dependent | P2 | no | no | 화면의 역할보다 먼저 고른 사이드바 + 상단 바 + 지표 카드 넷 + 차트 + 표 |
| `structure.filler-feed` | structure | universal | P1 | no | no | 지어낸 사람과 사건으로 채운 활동 피드 |
| `structure.chart-without-question` | structure | review-only | P3 | no | no | 일반적인 제목만 있고 답하는 질문이 없는 차트 |
| `structure.generic-columns` | structure | review-only | P3 | no | no | 데이터와 무관한 Name / Status / Date / Actions 열 |
| `structure.product-clone` | structure | default-risk | P2 | no | no | 사용자가 요청하지 않은 유명 제품에서 베낀 전체 겉모습 |
| `surface.dark-default` | surface | context-dependent | P3 | no | no | 기술스러워 보여서만 쓴 다크 테마; 이유를 밝힌 개발자, 미디어, 창작 도구는 보존 |
| `surface.arrow-everywhere` | surface | review-only | P3 | no | no | 거의 모든 버튼에 붙은 화살표 |
| `surface.generic-illustration` | surface | default-risk | P3 | no | no | 제품과 연결이 없는 스톡이나 3D 블롭 일러스트 |
| `surface.dose-exceeded` | surface | default-risk | P2 | no | no | 내비게이션 바, 카드, 모달, 사이드바에 한꺼번에 블러, 모든 곳의 글로우, 모든 요소의 pill 모양, 또는 사방의 큰 그림자 |
| `type.default-icon-set` | typography-copy | review-only | P3 | no | no | 뒤에 아무 결정도 없는 하나의 기본 얇은 선 라이브러리에서 가져온 모든 아이콘 |

## Registry 해석

Static `yes`는 포함 detector가 그 규칙의 source signature를 내보낸다는 뜻이지 UI 결함 확정이 아니다. `partial`은 heuristic signature로 내보내며 결함으로 확정하려면 맥락이나 렌더링이 필요하다는 뜻이다. `no`는 포함 detector가 그 규칙을 내보내지 않는다는 뜻이며, 소스 읽기에서만 명시적 warrant와 caveat를 갖춰 보고한다. 수정 단계에는 `fix-playbook.md`를 읽는다.

`scripts/rule-registry.sh`의 registry는 `yes`와 `partial` 행만 담는다. 따라서 detector가 내보낼 수 없는 `ruleId`는 `--rules`, `--config`, waiver validator에서 모두 거부된다.

Detector v2는 `engine`, `evidenceKind`, detection/remediation confidence, cluster, exception status를 보고한다. `candidate` exception은 계속 보이는 review item이며 finding을 suppress하거나 automatic removal 권한을 주지 않는다.

## 두 번째 물결과 검토 날짜

Static 열이 `no`인 모든 행은 검토 규칙이다. 번들 검출기가 이들을 내보내지 않으므로 소스 읽기, 납품 게이트, 정석 수치 체크리스트, 독립 검토에서 보고한다. 기본값은 해마다 바뀌므로 최소 6개월마다 아래 출처와 이 표를 다시 읽는다. 랜딩, 대시보드, 장식 행의 대신 할 일은 `references/screen-patterns.md`에 있다.

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| detector rule ID, 분류, scope, severity, 예외 설명 | 이 패키지 자체 registry이며 `scripts/rule-registry.sh`가 구현한다 |
| 출판사 열 곳에서 반복되는 기본값(보라 그라디언트, 기본 서체, 동일 아이콘 카드, 글로우, 그라디언트 텍스트, eyebrow, 획일적 반경)의 빈도 | <https://github.com/febbhav/signs-of-ai-design/tree/854b46f18dee5cc174d45cec8cd4f3142fe46984>, <https://www.adriankrebs.ch/blog/design-slop/>, <https://www.925studios.co/blog/ai-slop-design-tells>, <https://github.com/ch040602/anti-ai-slop> |
| 두 번째 물결의 기본값과 그 시대 구분 | <https://impeccable.style/slop/>, <https://solodesign.cc/blog/ai-design-slop-the-tells/> |
| 선언한 서체는 빌드에 실제로 있어야 한다 | <https://tailthemes.com/blog/ai-design-slop-quality-gate> (2026-08-20) |
| AI 기능은 반짝임 아이콘이나 보라색 AI 색 없이 보여 준다; 상자에 담긴 창은 붙여 넣은 스크린샷처럼 읽힌다 | <https://github.com/benjitaylor/skills> (`stageshow` folder, commit `299140f`) (MIT) |
| 검출기 행(`quality.zoom-blocked`부터 `structure.viewport-height`까지)과 그 뒤의 검토 행(죽은 컨트롤, 깨진 테마, 패치 스크립트, 지어낸 주장, 가정한 자산, 템플릿 FAQ, 섹션 리듬, 요금제와 세 단계 기본값, 대시보드 셸, 채우기 피드, 질문 없는 차트, 일반 열, 제품 복제, 다크 기본값, 화살표, 일러스트, 사용량 상한, 기본 아이콘 세트) | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Part 1 and R-01 to R-40, `antislop-ui/SKILL.md`; MIT, Copyright 2026 Miqdad Badjuber). The IDs, scopes, and severities are this package's own. |

### Evidence grade

빈도는 2025-2026년 글에서 뽑은 편의 표본이며 상당수는 anti-slop 도구 판매자가 쓴 것이다. 이 수치는 목록의 순서를 정할 뿐 실제 보급률을 증명하지 않는다.
