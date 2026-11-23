# Hyper 라우팅 예시 모음

`hyper`의 도메인별 확장 라우팅 예시 모음입니다. `SKILL.ko.md` 코어 예시만으로 판단되지 않는 도메인 요청이나 경계 사례를 확인할 때만 선택적으로 읽습니다.

## 목차

- 1. 도메인별 구축·보고 예시
- 2. 경계 및 동률 판정 예시
- Sources

## 1. 도메인별 구축·보고 예시

- "사이트에 GA4 달아줘" -> `hyper-google-analytics`
- "SEO 점검하고 GA4 측정까지 세팅해줘" -> `hyper-seo` -> `hyper-google-analytics`
- "이 Next.js 사이트에 GTM 달고 구매 이벤트까지 태그로 보내줘. 컨테이너는 GTM-ABC1234." -> `hyper-google-tagmanager`
- "이 CSV에서 지역별 월 매출 집계해줘." -> `hyper-data`
- "컨텍스트 거의 찼어. 새 세션에서 이어서 할 수 있게 핸드오프 메모 써줘." -> `hyper-handoff`
- "이 목표 세 개 다 끝날 때까지 돌리고 dev에 머지·푸시해줘. 목표마다 테스트 통과가 기준이야." -> `hyper-loop` -> `hyper-git` (`&& dev`)
- "2026년 국내 SaaS 가격 동향 인터넷 검색으로 조사해서 리포트로 줘." -> `hyper-research`, 막힌 출처는 동반 스킬 `hyper-browsing`
- "사내 배포 체크리스트를 스킬로 만들어줘. 최신 Agent Skills 규격 확인해서." -> `hyper-research` -> `hyper-skill`
- "이 저장소 배포 런북을 에이전트가 읽기 좋게 다시 정리해줘." -> `hyper-documentation`
- "Build a reusable code-review system prompt with an eval fixture, checked against the latest provider prompting guide." -> `hyper-research` -> `hyper-documentation`
- "이 세 가지 이슈로 등록해줘." -> `hyper-issue`(등록, 레인) -> `hyper-plan` -> `hyper-execute`
- "사내 DB 조회하는 MCP 서버 만들어서 호스트에 연결까지 해줘." -> `hyper-mcp`
- "Migrate our MCP server to the current spec and open a PR." -> `hyper-mcp`(점검) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "티켓 분류 호출을 결정 모델로 바꿀 질문이랑 호출 코드 만들어줘." -> `hyper-decision`
- "Find every LLM call that only returns a label, move them to a decision API, and open a PR." -> `hyper-decision`(감사) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "새 요금제 페이지 디자인해서 만들어줘. AI가 만든 티 안 나게." -> `hyper-design`
- "Redesign the dashboard so it stops looking generic, and open a PR." -> `hyper-design`(점검) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "설정 화면 테이블이 길어지면 푸터가 밀려나. 본문만 스크롤되게 고쳐줘." -> `hyper-frontend`
- "Build the checkout form from this screenshot exactly and check it in a browser, then open a PR." -> `hyper-frontend`(verify) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "hyper로 블로그 히어로 이미지 하나 만들어줘. 최신 이미지 프롬프트 가이드 참고해서." -> `hyper-research` -> `hyper-imagegen`
- "주문 서비스 DB 스키마 설계하고 마이그레이션까지 만들어줘. Postgres야." -> `hyper-database`
- "결제 테이블 구조 바꾸고 관련 API까지 고쳐서 PR까지." -> `hyper-database`(리뷰) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "배포가 healthcheck에서 계속 실패해. 로그 보고 원인 찾아서 고쳐줘." -> `hyper-deploy`(진단)
- "고객사 피드백 메일이야. 뭘 고쳐야 하는지 다 찾아서 반영하고 dev, main에 머지·푸시해줘." -> `hyper-feedback` -> `hyper-git` (`&& dev && main`)
- "Review PR #412 against `dev` and tell me whether it can merge." -> `hyper-review`(review-only)
- "src/pricing/에 아무도 안 부르는 도우미들 정리해줘. 동작은 그대로." -> `hyper-cleanup`

## 2. 경계 및 동률 판정 예시

- "이 런북 정리하고 PR까지." -> `hyper-documentation` -> `hyper-git`(워크플로 모드). 계획 체인의 전달 단어는 `hyper-plan`이 소유합니다.
- "랜딩 페이지 디자인하고 히어로 이미지도 넣어줘." -> 결과물이 화면 전체이므로 `hyper-design`이 맡고, `hyper-imagegen`은 이미지나 프롬프트 하나가 산출물 전부일 때만 씁니다.
- "배포 런북 정리해줘." -> 배포 문서이므로 `hyper-documentation`이 맡고, 실제 배포 실행인 `hyper-deploy`는 쓰지 않습니다.
- "이 프로젝트 MEMORY.md 정리해줘." -> 지속 문서는 `hyper-documentation`이 맡고, 진행 상태 메모인 `hyper-handoff`와 구분합니다.
- "고객이 대시보드가 촌스럽대. 리디자인해줘." -> 시각 리디자인이므로 `hyper-design`이 맡고, 기존 동작 변경 요청인 `hyper-feedback`과 구분합니다.
- "새 요금제 페이지 만들어줘. 디자인은 알아서." -> 기본은 `hyper-design` 단독이며, 브라우저 레이아웃·상태·모션 증명까지 요구할 때만 `hyper-design`(`brief-only`) -> `hyper-frontend`로 잇습니다.
- "GA4에 맞춤 측정기준 만들고 GTM 컨테이너에서 그 값 보내게 태그도 고쳐줘." -> `hyper-google-analytics` -> `hyper-google-tagmanager`.
- "계획만 세우고 구현은 나중에 전문 스킬로 해줘." -> `hyper-plan`(`--plan-only`)으로 계획 행에만 전문 스킬을 기록하고 수정을 위해 열지 않습니다.
- "`@skills/<name>/` 참고해서 이 문서 정리해줘." -> 경로 언급은 위치 힌트일 뿐 실행 권한이 아니며, 산출물이 문서이므로 `hyper-documentation`이 맡습니다.

## Sources

> 확인 2026-11-23.

| Claim | Source |
|---|---|
| 점진적 공개(`SK-P-2`)를 위해 `hyper/SKILL.ko.md`에서 분리한 도메인별 라우팅 예시와 경계 판정 사례 | [workflow-routing.ko.md](../rules/workflow-routing.ko.md), [stage-handoff.ko.md](../rules/stage-handoff.ko.md), `instructions/skill/references/progressive-disclosure.ko.md` |
