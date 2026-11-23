# Hyper Routing Examples Catalog

Extended domain-by-domain routing examples for `hyper`. Load this reference only when classifying an unfamiliar domain request or checking a tie-break boundary that the core examples in `SKILL.md` do not already settle.

## Contents

- 1. Domain Build and Report Examples
- 2. Boundary and Tie-Break Examples
- Sources

## 1. Domain Build and Report Examples

- "사이트에 GA4 달아줘" -> `hyper-google-analytics`
- "SEO 점검하고 GA4 측정까지 세팅해줘" -> `hyper-seo` -> `hyper-google-analytics`
- "이 Next.js 사이트에 GTM 달고 구매 이벤트까지 태그로 보내줘. 컨테이너는 GTM-ABC1234." -> `hyper-google-tagmanager`
- "이 CSV에서 지역별 월 매출 집계해줘." -> `hyper-data`
- "컨텍스트 거의 찼어. 새 세션에서 이어서 할 수 있게 핸드오프 메모 써줘." -> `hyper-handoff`
- "이 목표 세 개 다 끝날 때까지 돌리고 dev에 머지·푸시해줘. 목표마다 테스트 통과가 기준이야." -> `hyper-loop` -> `hyper-git` (`&& dev`)
- "2026년 국내 SaaS 가격 동향 인터넷 검색으로 조사해서 리포트로 줘." -> `hyper-research` with `hyper-browsing` for blocked sources
- "사내 배포 체크리스트를 스킬로 만들어줘. 최신 Agent Skills 규격 확인해서." -> `hyper-research` -> `hyper-skill`
- "이 저장소 배포 런북을 에이전트가 읽기 좋게 다시 정리해줘." -> `hyper-documentation`
- "Build a reusable code-review system prompt with an eval fixture, checked against the latest provider prompting guide." -> `hyper-research` -> `hyper-documentation`
- "이 세 가지 이슈로 등록해줘." -> `hyper-issue` (register, lanes) -> `hyper-plan` -> `hyper-execute`
- "사내 DB 조회하는 MCP 서버 만들어서 호스트에 연결까지 해줘." -> `hyper-mcp`
- "Migrate our MCP server to the current spec and open a PR." -> `hyper-mcp` (audit) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "티켓 분류 호출을 결정 모델로 바꿀 질문이랑 호출 코드 만들어줘." -> `hyper-decision`
- "Find every LLM call that only returns a label, move them to a decision API, and open a PR." -> `hyper-decision` (audit) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "새 요금제 페이지 디자인해서 만들어줘. AI가 만든 티 안 나게." -> `hyper-design`
- "Redesign the dashboard so it stops looking generic, and open a PR." -> `hyper-design` (audit) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "설정 화면 테이블이 길어지면 푸터가 밀려나. 본문만 스크롤되게 고쳐줘." -> `hyper-frontend`
- "Build the checkout form from this screenshot exactly and check it in a browser, then open a PR." -> `hyper-frontend` (verify) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "hyper로 블로그 히어로 이미지 하나 만들어줘. 최신 이미지 프롬프트 가이드 참고해서." -> `hyper-research` -> `hyper-imagegen`
- "주문 서비스 DB 스키마 설계하고 마이그레이션까지 만들어줘. Postgres야." -> `hyper-database`
- "결제 테이블 구조 바꾸고 관련 API까지 고쳐서 PR까지." -> `hyper-database` (review) -> `hyper-plan` -> `hyper-execute` (`--make-pr`)
- "배포가 healthcheck에서 계속 실패해. 로그 보고 원인 찾아서 고쳐줘." -> `hyper-deploy` (diagnose)
- "고객사 피드백 메일이야. 뭘 고쳐야 하는지 다 찾아서 반영하고 dev, main에 머지·푸시해줘." -> `hyper-feedback` -> `hyper-git` (`&& dev && main`)
- "Review PR #412 against `dev` and tell me whether it can merge." -> `hyper-review` (review-only)
- "src/pricing/에 아무도 안 부르는 도우미들 정리해줘. 동작은 그대로." -> `hyper-cleanup`

## 2. Boundary and Tie-Break Examples

- "이 런북 정리하고 PR까지." -> `hyper-documentation` -> `hyper-git` (workflow mode); delivery words on a plan chain stay in `hyper-plan`.
- "랜딩 페이지 디자인하고 히어로 이미지도 넣어줘." -> Interface is the deliverable (`hyper-design`); `hyper-imagegen` runs only when one image or prompt is the entire output.
- "배포 런북 정리해줘." -> Document about deploying (`hyper-documentation`), not a live deployment (`hyper-deploy`).
- "이 프로젝트 MEMORY.md 정리해줘." -> Durable memory document (`hyper-documentation`), not an in-progress handoff memo (`hyper-handoff`).
- "고객이 대시보드가 촌스럽대. 리디자인해줘." -> Visual redesign (`hyper-design`), not existing-behavior feedback (`hyper-feedback`).
- "새 요금제 페이지 만들어줘. 디자인은 알아서." -> `hyper-design` alone unless rendered layout/state/motion verification is also requested (`hyper-design` brief-only -> `hyper-frontend`).
- "GA4에 맞춤 측정기준 만들고 GTM 컨테이너에서 그 값 보내게 태그도 고쳐줘." -> `hyper-google-analytics` -> `hyper-google-tagmanager`.
- "계획만 세우고 구현은 나중에 전문 스킬로 해줘." -> `hyper-plan` (`--plan-only`), recording the specialist in the plan row without opening it for edits.
- "`@skills/<name>/` 참고해서 이 문서 정리해줘." -> Mentioned path is a locator hint, not execution authority; deliverable is a document (`hyper-documentation`).

## Sources

> Checked 2026-11-23.

| Claim | Source |
|---|---|
| Domain routing examples and boundary tie-breaks extracted from `hyper/SKILL.md` for progressive disclosure (`SK-P-2`) | [workflow-routing.md](../rules/workflow-routing.md), [stage-handoff.md](../rules/stage-handoff.md), `instructions/skill/references/progressive-disclosure.md` |
