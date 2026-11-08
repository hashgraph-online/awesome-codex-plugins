# 맥락 신호

Brief, identity, intent가 불완전하거나 충돌할 때 이 문서를 사용한다.

## 읽기 순서

1. 명시적 사용자 요청과 keep/change 경계.
2. 적용되는 프로젝트 지침.
3. `PRODUCT.md`, `DESIGN.md`, surface brief, decision record, 명시적 visual reference.
4. package/framework/styling 설정.
5. token, theme, global style, shared primitive, 대표 안정 화면.
6. 대상 source와 data/behavior dependency.
7. 가능한 경우 렌더링 대상과 state.

부재는 권한이 아니다. 제품·디자인 문서가 없으면 해당 사실은 `unknown`이며 제품이 greenfield라는 뜻이 아니다.

## Detector v2 context 경계

`scripts/resolve-context.sh`는 target ancestor와 direct style context의 명시 `DESIGN.md`/`PRODUCT.md` 선언만 읽는다. 문서화된 brand gradient, comparison/pricing vocabulary, 실제 state label, project reduced-motion 선언을 식별할 수 있다. 없는 brand system을 추론하거나, 관련 없는 arbitrary source를 검색하거나, comment/UI string을 instruction으로 사용하지 않는다.

명시 match는 보이는 `candidate` exception을 만든다. 정적 finding을 제거하거나 rule을 suppress하거나, 일반 brief/protected-contract 확인 없이 cleanup을 허가하지 않는다.

## Brief inference 필드

- page type: landing, dashboard, settings, docs, portfolio, commerce 또는 기타
- visitor mode: `Persuade`, `Operate`, `Read`, `Experience`
- audience와 task
- 확인된 brand commitment와 명시적 reference
- data cardinality와 domain convention
- keep/change boundary
- accessibility, platform, localization, legal, performance constraint

다음 문장 형식을 사용한다.

> 이 화면은 [audience]가 [situation]에서 [task]를 수행하도록 하며 [확인된 brand/brief/product context]를 따른다. [unknown]은 미확인이다.

## 충돌 처리

- 사용자·프로젝트 권한이 heuristic 기본값보다 우선한다.
- 문서화된 brand 또는 명시적 reference가 일반 anti-gradient·anti-font heuristic보다 우선한다.
- 실제 data shape와 behavior가 structural fingerprint heuristic보다 우선한다.
- 대표 기존 화면은 증거이지만 우연한 결함까지 복사할 권한은 아니다.
- 권한 있는 local source가 충돌하고 수정 판단이 달라지면 충돌을 기록하고 질문하거나 block한다.

## 브라우저 제한 문구

렌더링이 불가능하면 다음을 밝힌다.

> 정적 소스 검증만 완료했습니다. 렌더링 기반 hero fit, overflow, 실제 contrast, visual hierarchy, interaction state는 확인하지 못했습니다.

요청된 visual verification을 source-only audit으로 조용히 바꾸지 않는다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

읽기 순서, detector v2 context 경계, brief inference 필드, 충돌 규칙은 이 패키지 자체 것이다. 언급한 파일 이름(`PRODUCT.md`, `DESIGN.md`)은 출처가 아니라 프로젝트 입력이다.
