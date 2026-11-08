# Workflow Routing

> 요청한 결과물을 분류하고, 작업이 쓰는 산출물을 만드는 단계만 더해 하나의 고정 순서로 실행합니다.

## 1. 작업 분류

요청한 결과물로 작업을 정한 뒤 저장소 파일로 확인합니다. 요청을 먼저 읽고, 신호가 가리키는 파일만 읽습니다.

| Job class | Requested output | Example words |
|---|---|---|
| Build | 바뀐 코드: 기능, 수정, 리팩토링, 마이그레이션, 도입. 데이터 모델, 스키마, 데이터베이스 마이그레이션, 튜닝한 쿼리나 인덱스, 데이터베이스 운영 변경. MCP 서버, 클라이언트, 호스트 설정. 디자인하거나 리디자인한 화면, 연출 화면. 사용자·고객사·기획자의 변경 요청을 기존 동작에 반영한 결과. 새로 만들거나 편집한 이미지 한 장이나 이미지 프롬프트 하나. 배포 준비 판정, 배포 구성, 배포, 배포 설정 변경, 배포 실패 수정. 또는 새로 만들거나 리팩터링한 스킬 폴더, 문서, 프롬프트 산출물 | 만들어, 추가해, 고쳐, 리팩토링해, 옮겨, 적용해, 연결해, 스키마 설계해, 인덱스 잡아줘, 디자인해, 리디자인해, AI 티 빼줘, 피드백 반영해, 요청대로 바꿔줘, 배포해, 배포 설정해, 배포 실패 고쳐, 점검해, 스킬로 만들어, 문서로 정리해, 프롬프트 만들어, implement, refactor, migrate, connect, redesign, apply this feedback, generate an image, deploy, ship to staging |
| Report | 코드 변경 없는 저장 보고서, 감사, 리뷰, 계획 | 조사만, 점검만, 리뷰만, 리포트만, 계획만, audit only, just the plan |
| Resume | 앞선 실행 이어가기 | 이어서, 계속, 재개, resume, continue |

계획 없는 한 곳 수정(오타, 문자열 하나, 설정 값 하나), 커밋만 하는 요청, PRD나 와이어프레임 패키지, 질문은 범위 밖입니다. 라우팅하지 않습니다.

## 2. 단계 신호

신호가 하나 있을 때만 그 단계를 더합니다. 라우팅 줄에 그 신호를 인용합니다.

| Stage | Add it when | Evidence to quote |
|---|---|---|
| `hyper-research` | 작업이 저장소 밖 사실에 달려 있습니다. 라이브러리나 서비스 선택, 새 메이저 버전, 낯선 외부 API, "최신" / "latest" 동작 | 요청 문구 |
| `hyper-issue` | 요청이 이슈 등록이나 기록을 원하거나("이슈 등록해줘", "이슈로 남겨줘", "register these as issues"), 이슈 번호를 적거나(`#1~3`, `#4, #7`, `1~3번 이슈`), 열린 이슈를 골라 묶을 조건을 주거나, 범위·수용 기준이 빠진 이슈를 지목할 때입니다 | 요청 문구, 그리고 트래커와 지목된 번호, 라벨, 질의 |
| `hyper-seo` | 작업이 이름이 정해진 사이트나 페이지 묶음의 검색 또는 AI 답변 노출에 관한 것입니다 | 요청 문구와 대상 URL 또는 앱 경로 |
| `hyper-google-analytics` | 결과물이 GA4 작업입니다. 사이트에 GA4나 Google 태그를 설치하거나 고치기, GA4 속성이나 그 태그 감사, 속성 설정 변경(맞춤 측정기준, 키 이벤트, 보존 기간, 필터), GA4 보고서 데이터 분석, GA4 데이터가 빠지거나 틀린 이유 찾기 | 요청 문구와 읽은 태그 파일. `gtag(`나 `googletagmanager.com`, `G-` 측정 ID, `@next/third-parties/google`이 든 파일입니다 |
| `hyper-architecture` | 작업이 폴더, 라우트, 모듈, 데이터나 서버 경계, 플랫폼 설정을 재구성하거나, 새 라우트·모듈·서버 경계를 만드는 기능을 추가하거나, 린트·포맷·타입 도구(oxlint, Prettier, rustfmt, clippy)를 셋업하거나 통일하거나, 빌드·런타임 성능을 최적화합니다 | 요청 문구와 읽은 스택 매니페스트(`package.json`, `Cargo.toml` 등) |
| `hyper-database` | 작업이 데이터 모델이나 스키마를 설계·리뷰하거나, 데이터베이스 마이그레이션이나 백필을 쓰거나 리뷰하거나, 느린 쿼리·인덱스·핫 키·핫 파티션을 튜닝하거나, 데이터베이스 엔진이나 매니지드 데이터 서비스를 고르거나, 데이터베이스 운영(백업과 복구, 복제와 장애 조치, 커넥션 풀, 업그레이드, 데이터베이스 보안, 모니터링)을 바꿉니다 | 요청 문구와, 있으면 읽은 스키마·마이그레이션·ORM·드라이버 파일(`schema.prisma`, `drizzle.config.ts`, `migrations/` 폴더, `package.json`의 `pg`나 `ioredis`, compose 파일의 데이터베이스 이미지 등) |
| `hyper-mcp` | 작업이 MCP(Model Context Protocol) 서버, 클라이언트, 호스트 MCP 설정을 만들거나 고치거나 이전하거나 점검하거나 연결합니다. 또는 MCP 레지스트리 메타데이터를 준비합니다 | 요청 문구와, 있으면 읽은 MCP 의존성이나 설정 파일(`package.json`의 `@modelcontextprotocol/*`, `pyproject.toml`의 `mcp`, `.mcp.json`, `server.json` 등) |
| `hyper-decision` | 작업이 decision API 호출을 설계하거나 쓰거나 연결하거나 평가하거나 감사하거나 경로를 정합니다. decision API 호출은 글 대신 타입 판단(예/아니오 확률, 닫힌 선택지 중 하나, 순서 있는 점수, 이미지 상자)을 돌려주는 모델 호출이며 TypeSafe Jev, OpenAI Decisions, 다른 결정 공급자, Vercel AI SDK나 AI Gateway, OpenRouter, 범용 LLM 위 에뮬레이션을 거칩니다. 라벨만 돌려주는 기존 LLM 호출을 감사하는 일도 해당합니다 | 요청 문구와, 있으면 읽은 결정 의존성이나 호출(`@typesafe-ai/sdk`, `typesafe-sdk`, `@ai-sdk/typesafe-ai`, 코드 속 `experimental_decide`나 `client.decisions.create`, 설정 파일의 `api.typesafe.ai` 등) |
| `hyper-design` | 요청한 결과물이 보이는 모습 자체가 핵심인 화면입니다. 새 화면·페이지·컴포넌트 디자인, 기존 UI 리디자인, 히어로·카드·데모용 연출 화면, 디자인 브리프나 `DESIGN.md`, generic한 "AI 티" 패턴의 점검이나 제거 | 요청 문구와 대상 UI 경로, 그리고 있으면 읽은 스타일·디자인 시스템 파일(`DESIGN.md`, 토큰 파일, `tailwind.config.*` 등) |
| `hyper-feedback` | 입력이 기존 동작에 대해 제품 언어로 쓴 변경 요청입니다. 사용자, 고객사, 기획자가 직접 보내거나 전달된 피드백, 불만, 티켓, 회의 메모, 기획 수정, 새 문구이고, 사용자가 그것을 파악해 반영하길 원합니다("알아서 파악해서 고쳐", "피드백 반영해", "이 메모대로 반영") | 요청 문구와 인용한 피드백 원문, 그리고 작성자나 전달 경로 |
| `hyper-imagegen` | 요청한 결과물 전부가 새 이미지 한 장, 제공한 이미지 한 장의 편집, 바로 쓸 수 있는 이미지 프롬프트 하나입니다 | 요청 문구, 그리고 있으면 제공한 편집 원본이나 참고 자료 경로 |
| `hyper-plan` | Build 작업이 여러 파일이나 단계를 건드리거나, Report 작업이 계획을 요청합니다 | 요청 문구 |
| `hyper-execute` | 첫 단계일 때만: `.hyper/plans/` 아래 계획 파일이 이미 있고 사용자가 실행이나 재개를 원합니다 | 읽은 계획 경로 |
| `hyper-mass` | 사용자가 의존성 그래프, DAG, "의존성 그래프", "단계별 병렬"을 요청하거나, 일부가 먼저 끝나야 다른 일이 시작되는 여러 작업이 있고 계획 파일을 원하지 않습니다 | 요청 문구 |
| `hyper-skill` | 요청한 결과물이 재사용 스킬 폴더입니다. 새 스킬, 또는 기존 스킬의 트리거, 계약, 리소스, 검증 리팩터링 | 요청 문구, 그리고 이미 있으면 대상 `skills/<name>/SKILL.md` |
| `hyper-documentation` | 요청한 결과물이 새로 만들거나 리팩터링하는 문서 산출물입니다. README, `AGENTS.md`, AI가 읽기 좋은 문서(지침 베이스, 에이전트 가이드, 런북, 스펙, 규칙 묶음), 재사용 프롬프트 산출물(역할·시스템·에이전트 프롬프트, 프롬프트 템플릿이나 팩, 프롬프트 평가 픽스처) | 요청 문구, 그리고 이미 있으면 대상 경로 |
| `hyper-git` | 전달하지 않는 꼬리(`hyper-skill`, `hyper-documentation`, `hyper-feedback`, 또는 마지막 구축 단계인 `hyper-database`, `hyper-mcp`, `hyper-decision`, `hyper-design`, `hyper-google-analytics`) 뒤에서 사용자가 커밋과 푸시, 또는 지정 브랜치로 병합과 푸시를 요청합니다. `hyper-skill`, `hyper-documentation`, `hyper-feedback` 뒤에서는 PR도 해당합니다. 같은 체인이 배포까지 하면 `hyper-deploy` 앞에서 실행합니다. `hyper-imagegen` 뒤에는 붙지 않습니다. 그 산출물은 전달된 이미지이거나 git이 무시하는 `.hyper/imagegen/` 파일이기 때문입니다. `hyper-deploy` 뒤에도 붙지 않습니다 | 전달 문구와 지정한 대상 브랜치 |
| `hyper-deploy` | 작업이 배포나 배포 관련 발견입니다. 배포 준비 판정, 첫 배포 구성, 지목한 환경으로의 배포, 기존 배포 설정 변경, 실패했거나 비정상인 배포의 원인 진단과 수정 | 요청 문구와, 읽은 배포 파일(`Dockerfile`, `compose.yaml`, `wrangler.jsonc`, `.railway/railway.ts`, `railway.toml`, `config/deploy.yml` 등) |

## 3. 단계 순서

고른 단계는 항상 이 순서로 실행합니다. 고르지 않은 단계는 건너뜁니다.

```text
hyper-research -> hyper-issue -> hyper-seo -> hyper-google-analytics -> hyper-architecture -> hyper-database -> hyper-mcp -> hyper-decision -> hyper-design -> hyper-feedback -> (hyper-plan [-> hyper-execute] | hyper-mass | hyper-execute | hyper-skill | hyper-documentation | hyper-imagegen) [-> hyper-git] [-> hyper-deploy]
```

두 전달 갈래를 모두 고르면 `hyper-git`이 먼저, `hyper-deploy`가 마지막에 실행합니다. `hyper-deploy` 뒤에는 어떤 단계도 오지 않습니다.

- 앞 단계(`hyper-research`, `hyper-seo`, `hyper-architecture`)는 꼬리 단계에 쓸 근거를 만듭니다. Build 작업에서는 보고서 모드로 실행하고, 코드 변경은 꼬리 단계가 합니다.
- `hyper-google-analytics`는 마지막 구축 단계입니다. 사이트 코드와 속성 설정을 스스로 고치고 수집을 증명하므로 `hyper-database`처럼 뒤에 `hyper-git`이 붙을 수 있습니다. 같은 체인이 전달이나 배포까지 하면 `hyper-git`과 `hyper-deploy` 앞에서 실행하고, `hyper-deploy` 뒤에는 절대 오지 않습니다. `hyper-seo`도 고르면 `hyper-seo`가 먼저 실행되고 이 단계가 그 결과를 측정합니다.
- `hyper-database`가 마지막으로 고른 단계면 꼬리 단계입니다. 직접 스키마를 설계하거나 무중단 마이그레이션을 쓰거나 쿼리·인덱스를 튜닝하거나 운영 설정을 바꾸고 결과를 검증합니다. 뒤에 `hyper-plan`이나 `hyper-mass`가 오면 리뷰 모드(설계 브리프, 스키마·마이그레이션 리뷰, 엔진 선택)로 실행하고 저장한 보고서가 계획의 입력이 됩니다.
- `hyper-mcp`가 마지막으로 고른 단계면 꼬리 단계입니다. 직접 만들거나 고치거나 이전하거나 연결하고 결과를 검증합니다. 뒤에 `hyper-plan`이나 `hyper-mass`가 오면 점검 모드로 실행하고 그 보고서가 계획의 입력이 됩니다.
- `hyper-decision`이 마지막으로 고른 단계면 꼬리 단계입니다. 결정 산출물(질문, 호출 코드, 템플릿, 평가 계획, 감사 표, 경로 설정)을 쓰고 오프라인 요청 검사기를 직접 돌립니다. 뒤에 `hyper-plan`이나 `hyper-mass`가 오면 `design`이나 `audit` 모드로 실행하고 저장한 결정 계약이나 감사 표가 계획의 입력이 됩니다.
- `hyper-design`가 마지막으로 고른 단계면 꼬리 단계입니다. 직접 화면을 디자인하거나 리디자인하거나 연출 화면을 만들거나 정리하고 결과를 검증합니다. 뒤에 `hyper-plan`이나 `hyper-mass`가 오면 아직 없는 화면은 `brief-only` 모드로, 기존 화면은 `audit` 모드로 실행하고 저장한 브리프나 보고서가 계획의 입력이 됩니다.
- `hyper-feedback`이 마지막으로 고른 단계면 꼬리 단계입니다. 직접 수정 예산 안의 항목을 모두 반영하고 스스로 검증합니다. 실행이 `handoff`로 끝나면 같은 실행에서 그 뒤에 `hyper-plan`을 붙이고 `.hyper/feedback/<slug>/brief.md`를 필수 입력으로 넘깁니다. 라우팅 줄에는 이 조건부 단계를 `hyper-feedback [-> hyper-plan]`으로 씁니다. `applied`로 끝나면 계획 단계는 실행하지 않습니다.
- `hyper-issue`는 다른 상류 단계처럼 꼬리에 쓸 근거를 만듭니다. 이슈를 등록하고 레인 명세를 쓰며, `hyper-plan`이 명세의 레인 하나를 웨이브 안의 병렬 레인 하나로 바꿉니다. 등록 단어나 이슈 번호가 있으면 기본으로 `hyper-plan`까지 이어지므로, 레인을 실행하고 전달한 뒤에야 실행이 끝납니다. 기록만 원하는 단어("등록만", "이슈만", "작업은 하지 마", "manifest only")가 있을 때만 `hyper-issue`가 마지막 단계입니다.
- `hyper-issue`가 직접 넘긴 요청(`.hyper/issues/<slug>/batch.md`를 지목하고 이슈 단계가 끝났다고 밝힘)은 `hyper-issue`를 다시 실행하지 않습니다. 1단계를 명세 경로와 함께 `done`으로 기록하고 `hyper-plan`에서 시작합니다.
- 그 밖의 경우 꼬리 단계는 정확히 하나입니다. `hyper-plan`(스스로 `hyper-execute`로 이어짐), `hyper-mass`, 기존 계획에 대한 `hyper-execute` 단독, 스킬 폴더에 대한 `hyper-skill`, 문서나 프롬프트 산출물에 대한 `hyper-documentation`, 이미지 한 장이나 이미지 프롬프트 하나에 대한 `hyper-imagegen` 중 하나입니다.
- `hyper-git`은 혼자서 꼬리 단계가 되지 않습니다. 파일은 바꾸지만 전달은 맡지 않는 꼬리 뒤에 붙습니다. `hyper-plan`, `hyper-execute`, `hyper-mass`는 스스로 전달하므로 `hyper-git`이 뒤따르지 않습니다.
- `hyper-deploy`는 체인의 마지막 단계입니다. 앞 단계가 만든 결과를 배포하며, 뒤에 `hyper-git`이 붙지 않습니다. 사용자가 커밋·푸시·병합 전달까지 요청했으면 `hyper-git`이 `hyper-deploy` 앞에 실행합니다.
- 같은 요청이 코드까지 바꾸면 코드 체인을 먼저 실행하고, `hyper-deploy` 단계는 실행 완료 블록 뒤에 시작합니다. 아직 완성되지 않은 트리가 아니라 끝난 변경을 배포하기 위해서입니다.
- Report 작업에서는 요청한 마지막 단계에서 체인이 끝납니다. 계획을 요청한 Report 작업은 `--plan-only`로 `hyper-plan`에서 끝납니다.
- 최대 네 단계까지 실행하고 `hyper-deploy`도 그 안에 셉니다. 더 필요해 보이는 체인은 작업 두 개입니다. 첫 작업을 실행하고 두 번째는 다음 단계로 보고합니다.
- `hyper-browsing`은 단계가 아니라 동반 스킬입니다. 이 순서에서 자리를 차지하지 않고 네 단계 상한에도 세지 않습니다. 리서치가 웹 조사형일 때 `hyper-research` 단계에 붙입니다. 질문이 실시간 웹 출처(검색 결과, 벤더·커뮤니티·뉴스 페이지, 시장·동향 데이터, 외부 문서, 이름을 댄 URL)에 기대는 경우이며, "인터넷 검색", "웹에서", "최신", "동향", "사례", "latest" 같은 말이나 URL이 신호입니다. 리서치가 저장소만 다루거나(소스 코드 분석, 로컬 파일과 이력) `hyper-research` 단계를 고르지 않았으면 붙이지 않습니다.

## 4. 체인 레시피

| Job | Chain |
|---|---|
| 아키텍처 점검만 | `hyper-architecture` |
| 린트·포맷·타입 도구 셋업이나 통일, 빌드·런타임 성능 최적화 | 직접 수정하는 마지막 단계로 `hyper-architecture` 단독 |
| 리팩토링이나 구조 변경 | `hyper-architecture` -> `hyper-plan` |
| 여러 파일에 걸친 기능이나 수정 | `hyper-plan` |
| 라우트, 모듈, 서버 경계를 추가하는 기능 | `hyper-architecture` -> `hyper-plan` |
| 라이브러리나 기술 선택 후 도입 | `hyper-research` -> `hyper-plan` |
| 이슈 기록만, 또는 배치 명세만("등록만", "명세만") | `hyper-issue` |
| 이슈를 등록하거나 번호를 적고 그 레인을 구현("이슈 등록해줘", "#1~3 작업해줘") | `hyper-issue` -> `hyper-plan` |
| 명세를 들고 `hyper-issue`가 넘긴 요청 | `hyper-plan`, `hyper-issue`는 `done`으로 기록 |
| 이슈의 수정에 낯선 외부 사실이 필요 | `hyper-research` -> `hyper-issue` -> `hyper-plan` |
| 프레임워크나 메이저 버전 마이그레이션 | `hyper-research` -> `hyper-architecture` -> `hyper-plan` |
| 스키마 설계, 마이그레이션 작성, 쿼리·인덱스 튜닝, 데이터베이스 운영 변경 | `hyper-database` |
| 데이터베이스 리뷰, 엔진 선택, 설계 브리프만 | 리뷰나 choose 모드의 `hyper-database` 단독 |
| 저장소가 아직 쓰지 않는 엔진이나 데이터 서비스("Valkey로 옮겨", "DynamoDB 도입") | `hyper-research` -> `hyper-database` |
| PR이나 배포로 전달하는 데이터베이스 변경, 또는 애플리케이션 코드까지 바뀌는 변경 | `hyper-database`(리뷰) -> `hyper-plan` |
| MCP 서버나 클라이언트 구축, 수정, 이전, 연결 | `hyper-mcp` |
| MCP 점검이나 보고서만 | `hyper-mcp` 점검 모드 단독 |
| 낯선 외부 API를 감싸는 MCP 서버("Notion API를 MCP로") | `hyper-research` -> `hyper-mcp` |
| PR이나 배포로 전달하는 MCP 변경, 또는 MCP 밖 모듈도 바꾸는 변경 | `hyper-mcp`(점검) -> `hyper-plan` |
| decision API 질문, 호출 코드, 템플릿, 평가 계획, 감사, 경로 설정("결정 모델로 바꿔", "Jev 질문 설계", "OpenAI Decisions 호출 코드") | `hyper-decision` |
| 그 참조가 다루지 않는 decision API 경로나 공급자("새로 나온 결정 모델 붙여줘") | `hyper-research` -> `hyper-decision` |
| PR이나 배포로 전달하는 decision API 변경, 또는 애플리케이션 전반의 호출을 다시 연결하는 변경("라벨만 돌려주는 LLM 호출 전부 바꾸고 PR까지") | `hyper-decision`(`design`이나 `audit`) -> `hyper-plan` |
| 화면 디자인, 리디자인, 연출 화면, generic 패턴 정리 | `hyper-design` |
| 화면 점검이나 디자인 방향만 | `audit`나 `brief-only` 모드의 `hyper-design` 단독 |
| PR이나 배포로 전달하는 화면 작업, 또는 API·데이터·라우트 변경도 필요한 작업 | `hyper-design`(`audit`나 `brief-only`) -> `hyper-plan` |
| 최신 외부 지침에 기대는 화면("최신 가이드라인 확인해서") | `hyper-research` -> `hyper-design` |
| 사용자, 고객사, 기획자의 변경 요청을 기존 동작에 반영 | `hyper-feedback` |
| 같은 요청에 직접 수정 예산을 넘는 항목(새 라우트, 스키마 변경, API 계약)이 있음 | `hyper-feedback` -> `hyper-plan`. 계획 단계는 변경 요청 단계가 `handoff`로 끝났을 때 붙입니다 |
| 최신 외부 사실에 기대는 변경 요청("최신 정책에 맞게 바꿔달래") | `hyper-research` -> `hyper-feedback` |
| 이미지 한 장 생성, 제공한 이미지 한 장 편집, 이미지 프롬프트 하나 작성 | `hyper-imagegen` |
| 최신 외부 지침이나 참고 자료에 기대는 이미지("최신 프롬프트 가이드 참고해서") | `hyper-research` -> `hyper-imagegen` |
| 리서치 보고서만 | `hyper-research` |
| SEO 감사나 보고서만 | `hyper-seo` |
| SEO 점수 루프("최대 점수까지", "keep improving the score") | 최적화 모드의 `hyper-seo` 단독 |
| SEO 수정을 계획된 변경으로 구현 | `hyper-seo` -> `hyper-plan` |
| 사이트에 GA4 설치나 수정("사이트에 GA4 달아줘") | `hyper-google-analytics` |
| GA4 설치나 수정 뒤 병합·푸시("GA4 달고 dev에 머지·푸시") | `hyper-google-analytics` -> `hyper-git` |
| 검색 노출 감사 뒤 GA4 측정 구성("SEO 점검하고 GA4 측정까지 세팅해줘") | `hyper-seo` -> `hyper-google-analytics` |
| 지난달 GA4 보고서 데이터 분석("지난달 GA 유입 데이터 분석해서 리포트 줘") | `analyze` 모드의 `hyper-google-analytics` 단독 |
| 의존 순서가 있는 다중 에이전트 작업 | `hyper-mass`. 앞 단계 신호가 있으면 그 단계를 앞에 둡니다 |
| 기존 계획 실행이나 재개 | `hyper-execute` |
| 스킬 폴더를 새로 만들거나 리팩터링 | `hyper-skill` |
| 최신 공식 문서에 기대는 스킬 폴더("최신 규격", "latest spec") | `hyper-research` -> `hyper-skill` |
| README, `AGENTS.md`, 문서, 규칙 묶음, 재사용 프롬프트, 템플릿, 팩, 프롬프트 평가 픽스처를 새로 만들거나 리팩터링 | `hyper-documentation` |
| 최신 외부 출처나 공급자 지침에 기대는 문서나 프롬프트 | `hyper-research` -> `hyper-documentation` |
| 스킬 폴더, 문서, MCP, decision API, 인터페이스, 데이터베이스, GA4 분석, 변경 요청 반영 뒤 커밋과 푸시("커밋하고 푸시까지") | 그 체인 -> 커밋 모드의 `hyper-git` |
| 같은 작업 뒤 지정 브랜치로 병합과 푸시("dev, main에 머지하고 푸시") | 그 체인 -> 이번 실행의 커밋에 `&& <branch>` 대상을 붙인 커밋 모드의 `hyper-git`, 작업 브랜치 전체를 병합해야 하면 워크플로 모드 |
| 스킬 폴더, 문서, 변경 요청 반영 뒤 PR("PR까지") | 그 체인 -> 워크플로 모드의 `hyper-git`. MCP, decision API, 인터페이스, 데이터베이스 작업에 "PR까지"나 "ship"이 붙으면 위의 리뷰나 점검 -> `hyper-plan` 경로를 유지합니다 |
| 지목한 환경으로 배포("배포해줘", "staging에 올려줘", "deploy it to staging") | `deploy` 모드의 `hyper-deploy` |
| 실패했거나 죽거나 비정상인 배포 수정("배포 실패 고쳐줘", "로그 보고 원인 찾아서 고쳐줘") | `diagnose` 모드의 `hyper-deploy` |
| 배포 전 준비 점검("배포 전 점검", "배포 전 검사만") | `preflight` 모드의 `hyper-deploy`. "고치지 말고"가 붙으면 validate-only입니다 |
| 배포 구성이 없는 저장소의 첫 구성과 비프로덕션 배포 | `setup` 모드의 `hyper-deploy` 뒤에 그 단계의 `deploy` 단계 |
| 기존 배포의 환경 변수·헬스 체크·플랫폼 설정을 바꾸고 다시 배포 | `change` 모드의 `hyper-deploy` 뒤에 그 단계의 `deploy` 단계 |
| 저장소와 이 스킬의 대상 안내서가 다루지 않는 플랫폼에 배포 | `hyper-research` -> `hyper-deploy` |
| 코드를 바꾸고 배포까지("기능 고치고 배포까지", "Fix the bug and deploy it to staging") | `hyper-plan` -> `hyper-deploy`. 계획 단계가 스스로 `hyper-execute`로 이어지고, 배포 단계는 그 실행 완료 블록 뒤에 시작합니다 |

`hyper-plan`이 들어간 행은 Report 작업이 아니면 `hyper-execute`로 이어집니다.

## 5. 동률 처리

- 긴 요청 안에서 사용자가 이름을 댄 단계("hyper-research로 조사하고 바로 적용해")는 고르고, 나머지 단계는 여전히 신호를 따릅니다.
- 결과물 전체가 막힌 페이지 하나의 내용인 요청("이 403 페이지 본문만 가져와")은 `hyper` 작업이 아닙니다. `hyper-browsing`이 단독으로 처리합니다. 조사 중에 만난 막힌 출처는 동반 스킬로서 `hyper-research` 단계 안에 둡니다.
- `hyper-issue`는 `hyper-skill`이나 `hyper-documentation`과 한 체인에서 실행하지 않습니다. 이슈 기록이나 배치 명세는 그 자체가 산출물이고, 스킬 폴더나 일반 문서는 각자의 단계로 갑니다.
- 이슈를 등록하거나 번호를 적으면 `hyper-issue`를 `hyper-plan` 앞에 놓습니다. 사용자가 기록만 원하는 단어를 썼을 때만 체인이 `hyper-issue`에서 끝납니다.
- `hyper-mass`와 `hyper-plan`은 한 체인에서 함께 실행하지 않습니다. 명시 신호가 있을 때만 `hyper-mass`를 고르고, 아니면 `hyper-plan`을 고릅니다.
- `hyper-skill`과 `hyper-plan`은 한 체인에서 함께 실행하지 않습니다. 요청한 결과물이 스킬 폴더면 `hyper-skill`을 고릅니다. 계획 파일은 그 단계의 입력이 아닙니다.
- `hyper-documentation`은 `hyper-plan`과 한 체인에서 함께 실행하지 않습니다. 주된 결과물로 고릅니다. README, `AGENTS.md`, 문서, 재사용 프롬프트 산출물은 모드를 스스로 고르는 `hyper-documentation`, 스킬 폴더는 `hyper-skill`입니다.
- `hyper-mcp`와 `hyper-skill`은 한 체인에서 함께 실행하지 않습니다. 요청한 결과물이 스킬 폴더면 MCP에 관한 스킬이라도 `hyper-skill`을 고릅니다.
- `hyper-decision`과 `hyper-skill`은 한 체인에서 함께 실행하지 않습니다. 요청한 결과물이 스킬 폴더면 결정 모델에 관한 스킬이라도 `hyper-skill`을 고릅니다. 모더레이션 정책, 분류기 프롬프트, 결정 모델에 관한 문서는 `hyper-documentation`으로 갑니다.
- 분류기 학습, 모델 파인튜닝, 데이터셋 파이프라인 구축 요청은 `hyper-decision` 작업이 아니며 기존 행대로 보냅니다. 타입 판단을 돌려주는 모델 호출이 결과물이거나 감사 대상일 때만 `hyper-decision`을 붙입니다.
- decision API 작업에 전달 단어("PR까지", "ship")가 있으면 `hyper-decision`을 `design`이나 `audit` 모드로 `hyper-plan` 앞에 둡니다. 전달은 계획과 실행 단계만 맡기 때문입니다.
- `hyper-mcp`와 `hyper-architecture`는 작업이 MCP 밖의 폴더, 라우트, 모듈도 재구성할 때만 함께 실행합니다. MCP만 다루는 작업은 아키텍처 단계 없이 `hyper-mcp`로 보냅니다.
- MCP 작업에 전달 단어("PR까지", "ship")가 있으면 `hyper-mcp`를 점검 모드로 `hyper-plan` 앞에 둡니다. 전달은 계획과 실행 단계만 맡기 때문입니다.
- `hyper-design`는 `hyper-skill`, `hyper-documentation`과 한 체인에서 함께 실행하지 않습니다. 디자인에 관한 스킬 폴더, 일반 문서, 프롬프트는 각자의 단계로 가고, 제품의 시각 체계를 기록하는 프로젝트 `DESIGN.md`는 `hyper-design`로 갑니다.
- 주된 결과물이 동작(새 API, 데이터 흐름, 버그 수정)인 기능은 화면이 있어도 기존 행대로 라우팅합니다. 요청이 보이는 모습 자체를 요구할 때("디자인 신경 써서", "AI 티 안 나게", "redesign")만 `hyper-design`를 더합니다.
- 화면 작업에 전달 단어("PR까지", "ship")가 있으면 `hyper-design`를 `audit`나 `brief-only` 모드로 `hyper-plan` 앞에 둡니다. 전달은 계획과 실행 단계만 맡기 때문입니다.
- `hyper-imagegen`은 `hyper-plan`, `hyper-mass`, `hyper-skill`, `hyper-documentation`, `hyper-design`과 한 체인에서 함께 실행하지 않습니다. 주된 결과물로 고릅니다. 이미지 한 장이나 이미지 프롬프트 하나는 `hyper-imagegen`, 그림이 들어간 인터페이스는 `hyper-design`, 이미지용 재사용 프롬프트 팩이나 템플릿은 `hyper-documentation`으로 갑니다. 이미지 분석이나 평가는 `hyper` 작업이 아닙니다.
- `hyper-imagegen` 단계가 `awaiting_input`으로 끝나면 질문 하나를 이미 했으므로 체인은 그 자리에서 멈추고 답을 받으면 재개합니다.
- `hyper-feedback`은 `hyper-skill`, `hyper-documentation`, `hyper-imagegen`, `hyper-mass`, `hyper-design`과 한 체인에서 함께 실행하지 않습니다. 생김새가 핵심인 요청("리디자인", "AI 티 안 나게")은 `hyper-design`, 스킬 폴더나 문서에 대한 변경 요청은 그 단계, 의존 그래프를 명시한 요청은 `hyper-mass`로 갑니다.
- 제품 언어로 쓴 변경 요청은 한 항목이 스키마, 라우트, API 변경을 필요로 해도 `hyper-feedback`으로 갑니다. 그 단계가 예산 안 항목을 반영하고 나머지는 `brief.md`로 `hyper-plan`에 넘깁니다. `hyper-architecture`나 `hyper-database`는 사용자가 그 점검을 이름이나 말로 요청했을 때만 앞에 붙입니다.
- 위치와 새 값을 이미 지정한 한 곳 수정("이 버튼 문구 하나만 바꿔줘")은 `hyper` 작업이 아닙니다. 항목이 여럿이거나 위치를 모르거나 느낌만 말한 요청("복잡하대", "불편하대")은 `hyper-feedback`으로 갑니다.
- 변경 요청 작업의 전달 단어는 변경 요청 단계가 `applied`로 끝나면 `hyper-git`으로 갑니다. `handoff`로 끝나면 덧붙인 `hyper-plan`의 전달 플래그로 넘기고 `hyper-git`은 뺍니다. 계획과 실행 단계가 스스로 전달하기 때문입니다.
- `hyper-feedback` 단계가 `awaiting_input`으로 끝나면 질문 하나를 이미 했으므로 체인은 그 자리에서 멈추고 답을 받으면 재개합니다.
- `hyper-database`는 `hyper-skill`, `hyper-documentation`과 한 체인에서 함께 실행하지 않습니다. 데이터베이스에 관한 스킬 폴더나 문서는 각자의 단계로 갑니다.
- GA에 관한 문서("GA 운영 가이드 문서 써줘")는 `hyper-documentation`으로 가고, GA 스킬 폴더 자체를 만드는 일은 `hyper-skill`로 갑니다. 검색 노출 감사는 GA4를 측정 행 하나로 적더라도 `hyper-seo`에 남깁니다.
- 속성 쓰기(속성 생성, 필터 활성화, 보존 기간 축소, 라이브 사이트의 동의 기본값 변경, 보관, 삭제)에 대한 승인 질문은 `hyper`가 아니라 `hyper-google-analytics` 단계가 맡습니다. 이 오케스트레이터는 요청에 있는 속성 ID나 사이트 URL을 그대로 넘기고 사용자를 대신해 승인하지 않습니다.
- 데이터베이스를 조회하는 MCP 서버("사내 DB 조회하는 MCP 서버")는 `hyper-mcp`로 갑니다. 작업이 스키마, 마이그레이션, 인덱스, 데이터베이스 설정까지 바꿀 때만 `hyper-database`를 더합니다.
- `hyper-architecture`와 `hyper-database`는 작업이 폴더나 모듈을 재구성하면서 스키마나 쿼리까지 바꿀 때만 함께 실행합니다. 영속 계층 배치만 다루는 일("repository 레이어 정리")은 `hyper-architecture`에 남깁니다.
- `hyper-database`와 다른 구축 꼬리(`hyper-mcp`, `hyper-decision`, `hyper-design`)를 함께 골랐다면 작업이 여러 모듈에 걸친 것입니다. 각 단계를 보고서 모드(리뷰, 점검, `design`, `brief-only`)로 실행하고 체인을 `hyper-plan`에서 끝냅니다.
- 데이터베이스 작업에 전달 단어("PR까지", "ship")가 있으면 `hyper-database`를 리뷰 모드로 `hyper-plan` 앞에 둡니다. 전달은 계획과 실행 단계만 맡기 때문입니다.
- `hyper-git`은 `hyper-plan`, `hyper-execute`, `hyper-mass`와 한 체인에서 함께 실행하지 않습니다. 같은 단어를 그 단계들의 전달 플래그가 이미 받습니다. 다른 단계 없이 Git만 원하는 요청(커밋, 워크트리, 병합만)은 `hyper` 작업이 아닙니다. 이슈 기록은 `hyper-issue`로 갑니다.
- `hyper-deploy`는 자신이 배포할 코드를 바꾸는 꼬리 단계보다 먼저 실행하지 않고, 뒤에 어떤 단계도 붙지 않습니다. 순서상 마지막 단계이기 때문입니다. 커밋·푸시·병합 전달까지 요청한 작업은 `hyper-git`을 `hyper-deploy` 바로 앞에 둡니다.
- `hyper-deploy`와 `hyper-documentation`은 주된 결과물로 가릅니다. 실제로 실행하는 배포나 그 수정은 `hyper-deploy`, 배포 런북·안내서·체크리스트처럼 문서로 쓰는 것은 `hyper-documentation`입니다.
- `hyper-deploy`와 `hyper-skill`은 한 체인에서 함께 실행하지 않습니다. 배포에 관한 스킬 폴더는 `hyper-skill`로 갑니다.
- 한 곳만 고치고 아무것도 배포하지 않는 CI 워크플로 파일 수정은 `hyper` 작업이 아닙니다. 이 체인 밖의 한 곳 수정입니다. CI가 배포하도록 만드는 요청은 플랫폼 설정과 배포 명령을 맡는 `hyper-deploy`로 갑니다.
- 프로덕션 배포, 롤백, 데이터·볼륨 작업, 삭제, 비용 증가, DNS·방화벽 변경, 자격 증명에 대한 승인 질문은 `hyper-deploy` 단계가 맡습니다. 그 단계가 자기 게이트와 자기 명령으로 묻습니다. 이 오케스트레이터는 그 질문에 답하거나 사용자를 대신해 승인하지 않습니다.
- `hyper-git` 전달 단계에서 `main`, `master`, 기본 브랜치, 배포 브랜치로 병합하는 일은 사용자가 그 브랜치를 지정했을 때만 합니다.
- 기존 계획 파일이 새 계획보다 우선하는 경우는 사용자가 그 파일을 가리키거나 재개를 말했을 때뿐입니다. 관계없는 옛 계획이 있는 새 Build 요청은 새 계획을 씁니다.
- 스택이 아키텍처 단계의 지원 범위 밖이어도 그 단계는 유지합니다. 그 단계가 파일로 지원 여부를 정하고 사유와 함께 멈추며, `rules/stage-handoff.md` §4가 그 정지를 건너뜀으로 기록합니다.

## 6. 전달 단어와 보고서 전용 단어

그것을 소유한 단계에 그대로 넘깁니다. 사용자가 말하지 않은 것을 고르지 않습니다.

| User words | Passed to |
|---|---|
| 없음 | local 전달(단계 기본값) |
| "PR까지", "PR만", "make a PR", `--make-pr` | `--make-pr` |
| "머지까지", "배포까지", "ship", `--ship` | `--ship` |
| "계획만", "실행하지 말고", "plan only", `--plan-only` | `--plan-only`. 체인은 계획 뒤에 끝납니다 |
| "승인은 내가 할게", "I'll approve" | 말한 그대로 승인 보류를 넘깁니다. 체인은 계획 뒤에 끝납니다 |
| 전달하지 않는 꼬리 뒤의 "커밋하고 푸시", "commit and push" | 커밋 모드의 `hyper-git` 전달 단계 |
| 전달하지 않는 꼬리 뒤의 "<branch>, <branch>에 머지하고 푸시", "merge into dev and main" | 그 대상을 지정 순서대로 받는 `hyper-git` 전달 단계 |
| `hyper-skill`, `hyper-documentation`, `hyper-feedback` 뒤의 "PR까지" | 워크플로 모드(PR)의 `hyper-git` 전달 단계 |

코드 변경 체인에서 "배포까지"의 동률 처리: "배포까지"는 두 뜻을 함께 가집니다. 그래서 두 뜻을 모두 반영합니다. 계획 단계는 `--ship`(병합 전달)을 받고 체인은 꼬리 뒤에 `hyper-deploy`를 더합니다. 배포 단계는 실행 완료 블록 뒤에만 시작하므로 ship 전달이 먼저 끝나고, 그다음 병합된 결과에 배포를 실행합니다. 사용자가 플랫폼 언급 없이 ship 전달만 뜻하면("머지까지") `--ship`만 넘기고 `hyper-deploy`를 건너뜁니다. 병합 없이 배포만 뜻하면("배포만") `--ship` 없이 `hyper-deploy`만 실행합니다.

## 7. 애매함

- 파일과 요청으로 체인이 정해지면 묻지 않고 라우팅합니다.
- 두 체인의 근거가 같고 잘못 고르면 작업 대부분을 다시 해야 할 때만 질문 하나를 합니다. 예를 들어 지원 앱이 두 개인 저장소에서 경로 없이 "구조 바꿔줘"라고 한 경우입니다. 후보 체인을 나열하고 하나를 권장하며, 답이 없으면 권장안으로 진행한다고 밝힙니다.
- 요청이 저장소와 어긋나면(사용자가 말한 스택이 매니페스트에 없음) 두 근거를 함께 보여 주고 한 번 묻습니다.

## 8. 라우팅 줄

첫 단계 전에 한국어 한 줄을 출력합니다.

```text
워크플로: <stage> -> <stage> -> ... (전달: local|make-pr|ship|plan-only|git:<mode> <targets>) / 근거: <stage>=<signal>; <stage>=<signal>
```

첫 단계 전에 멈추는 실행은 같은 줄에 체인 대신 정지 사유를 씁니다.

동반 스킬이 붙은 `hyper-research` 단계는 `hyper-research(+hyper-browsing)`으로 쓰고, 근거에는 웹 조사를 가리키는 말을 적습니다: `근거: hyper-research(+hyper-browsing)="인터넷 검색으로 동향 조사"`.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 열여덟 단계 스킬, 동반 스킬, 오케스트레이터 역할 | user instruction, 2026-11-06(오케스트레이터 역할); `hyper-deploy`를 더해 열다섯 단계로 늘린 사용자 지시, 2026-11-07; `hyper-feedback`을 더해 열여섯 단계로 늘린 사용자 지시, 2026-11-07; `hyper-decision`을 더해 열일곱 단계로 늘린 사용자 지시, 2026-11-08; `hyper-google-analytics`를 더해 현재의 열여덟 단계로 늘린 사용자 지시, 2026-11-08; 웹 조사형 리서치에 `hyper-browsing`을 붙인 사용자 지시, 2026-11-07 |
| 각 단계의 트리거, 결과물, 제외 범위. `hyper-mass`가 계획 파일 실행을 제외하고 `hyper-execute`가 기존 계획을 요구한다는 점 포함 | 이 저장소의 각 단계 스킬 `SKILL.md`, 2026-11-06 |
| 전달 단어, 계획만·승인 보류 단어, 계획에서 실행으로 자동 연결 | 이 저장소의 계획 스킬 handoff 규칙, 2026-11-06 |
| 단계 순서, 네 단계 상한, 레시피, 동률 처리 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
