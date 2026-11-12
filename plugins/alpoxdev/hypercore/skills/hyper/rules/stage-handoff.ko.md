# Stage Handoff

> 각 단계에 정확한 요청을 주고, 저장된 산출물을 디스크에서 확인하고, 마지막 단계가 완료를 증명할 때까지 그 산출물을 넘깁니다.

## 1. 단계 계약

런타임의 스킬 기능으로 각 단계 스킬을 불러오고(스킬이 일반 파일이면 그 `SKILL.md`를 읽고) 첫 단계부터 따릅니다. 실행 안의 모든 일은 그 단계가 소유합니다.

| Stage | Request passed to the stage | Artifact that must exist before the next stage | Passed forward |
|---|---|---|---|
| `hyper-research` | 작업이 달려 있는 질문과 그 질문이 뒷받침할 결정("이 저장소에 맞는 상태관리 라이브러리, 다음에 도입할 것"). 웹 조사형이면 "평범한 요청으로 읽지 못하는 출처마다 그 출처 하나에 `hyper-browsing`을 불러오고, 출처 표시와 보고서 경로를 `sources.md`에 적을 것"도 넘깁니다 | `.hyper/research/[NN].<slug>.md`와, 그 `sources.md`가 인용하는 모든 `.hyper/browsing/<slug>/report.md` | 보고서 경로와 추천 한 줄 |
| `hyper-issue` | `--from-hyper`, 등록할 항목·이슈 번호·선택 조건, 그리고 트래커, 저장소, 초안만 같은 사용자 제한. "이슈마다 `hyper:` 블록을 담아 영어로 등록하고, 레인 명세를 쓰고, `hyper` 실행을 또 시작하지 말 것"도 넘깁니다 | 트래커에서 다시 읽은 등록 이슈와 `.hyper/issues/<slug>/batch.md` | 이슈 번호와 URL, 명세 경로. `hyper-plan`에는 "명세의 Lane 표에서 레인 최대 네 개 묶음마다 웨이브 하나를 계획할 것. 레인 하나는 병렬 레인 하나이고 그 안의 이슈는 순서대로. 이슈마다 `verify`가 그 행의 게이트. 목록은 고정"을 넘깁니다 |
| `hyper-seo` | 대상, 그리고 Build 작업이면 허용 동작 `recommend`, Report 작업이면 사용자가 말한 모드 | `.hyper/seo/<slug>/` 아래 보고서 | 보고서 경로와 critical·warning 결과 |
| `hyper-google-analytics` | 사용자 요청 그대로, 요청에 있는 사이트 URL이나 속성 ID, 모드 단어, 모든 앞 단계 산출물 경로 | `.hyper/google-analytics/<slug>/report.md`. 마지막 상태 줄에 그 모드의 종료 결과(`audited`, `installed`, `changed`, `reported`, `fixed`, `exhausted`, `stopped-for-approval`, `delayed`, `blocked`, `handoff`)를 적습니다 | `hyper-git`이 뒤따를 때 바뀐 경로, 그리고 보고서 경로와 심각도별 발견 |
| `hyper-google-tagmanager` | 사용자 요청 그대로, 요청에 있는 컨테이너 ID와 사이트 URL, 모드 단어, 모든 앞 단계 산출물 경로 | `.hyper/gtm/<slug>/report.md`. `결과:` 줄에 `verified`, `partial`, `proposed`, `exhausted`, `blocked` 중 하나를 적습니다 | `hyper-git`이 뒤따를 때 바뀐 경로, 그리고 보고서 경로와 승인이 필요해 제안으로 남긴 동작 |
| `hyper-architecture` | Build 작업에서는 "아키텍처 감사만, 파일 경로와 함께 결과 보고, 수정 금지"와 대상 경로. 마지막 단계일 때는 사용자 요청 그대로 | 라우팅 줄과 결과를 워크플로 기록의 단계 메모에 옮긴 것. 감사 모드에서는 이 단계가 자기 파일을 저장하지 않기 때문입니다 | 단계 메모 위치와 결과 |
| `hyper-database` | 계획이나 mass 단계 앞에서는 "리뷰만, 파일 경로와 함께 결과·설계 브리프·엔진 선택 보고, 수정 금지"와 대상 경로, 모든 앞 단계 산출물 경로. 마지막 단계일 때는 사용자 요청 그대로와 모든 앞 단계 산출물 경로 | `.hyper/database/<slug>/report.md`. 마지막 단계일 때는 검증 절이 각 확인을 실행 결과와 함께, 또는 사유를 붙인 `not run`으로 적습니다 | 보고서 경로와 critical, high 발견 |
| `hyper-mcp` | 계획이나 mass 단계 앞에서는 "점검만, 파일 경로와 함께 결과 보고, 수정 금지"와 대상 경로, 모든 앞 단계 산출물 경로. 마지막 단계일 때는 사용자 요청 그대로와 모든 앞 단계 산출물 경로 | `.hyper/mcp/<slug>/report.md`. 마지막 단계일 때는 검증 표에 대상이 주장하는 era로 실행한 MCP Inspector 결과도 들어 있어야 합니다 | 보고서 경로와 critical, high 발견 |
| `hyper-decision` | 계획이나 mass 단계 앞에서는 "`design`이나 `audit` 모드만, 파일 경로와 호출별 경로 층, 각 경로가 확률을 돌려주는지와 함께 결정 계약이나 읽기 전용 감사 표 작성, 감사 대상 코드 수정 금지"와 대상 경로, 모든 앞 단계 산출물 경로. 마지막 단계일 때는 사용자 요청 그대로와 모든 앞 단계 산출물 경로 | `.hyper/decision/<topic>/`(또는 사용자가 준 경로) 아래 산출물과, 쓴 경로 전부, 모드, 적합성 판정, 경로와 층, 요청 파일마다 그 경로의 `check-decision-request.sh` 종료 코드나 수동 점검표를 적용했다는 메모를 담은 단계 보고 | `hyper-plan`이 뒤따르면 계약이나 감사 경로와 그 결정 행, `hyper-git`이 뒤따르면 바뀐 경로 |
| `hyper-design` | 계획이나 mass 단계 앞에서는 "보고서만: 새 화면이면 디자인 브리프를 쓰고 기존 화면이면 점검, 수정 금지"와 대상 경로, 모든 앞 단계 산출물 경로. 마지막 단계일 때는 사용자 요청 그대로와 모든 앞 단계 산출물 경로 | `.hyper/design/<slug>/brief.md`(brief-only) 또는 `.hyper/design/<slug>/report.md`. 마지막 단계일 때는 보고서가 그 단계의 보고서 검증기를 통과하고 정석 수치 점검 결과와 검토 방식을 기록해야 합니다 | 브리프나 보고서 경로와 P0, P1 발견 |
| `hyper-frontend` | 계획이나 mass 단계 앞에서는 "`verify` 모드만: 실제 브라우저에서 무엇이 깨지는지 파일 경로와 캡처 매트릭스와 함께 보고, 수정 금지"와 대상 경로, 모든 앞 단계 산출물 경로. `brief-only` 모드의 `hyper-design` 뒤에서는 사용자 요청 그대로와 그 안에서 만들 모습인 브리프 경로. 마지막 단계일 때는 사용자 요청 그대로와 모든 앞 단계 산출물 경로 | `.hyper/frontend/<slug>/report.md`. `Result:` 줄 하나(`delivered`, `delivered_unverified`, `awaiting_input`, `blocked`)로 끝나고 스크롤 소유권, 상태 매트릭스, `static`·`rendered`·`not verified` 라벨이 붙은 주장별 증거를 담음 | `hyper-git`이 뒤따르면 바뀐 경로, `hyper-plan`이 뒤따르면 보고서 경로와 발견 사항 |
| `hyper-feedback` | 사용자 요청 그대로와 인용한 피드백 원문, 작성자나 전달 경로, 사용자의 제약, 모든 앞 단계 산출물 경로 | 항목별 상태와 검증 절(명령과 출력, 잔여 검색 결과)을 담은 `.hyper/feedback/<slug>/report.md`. 실행이 `handoff`로 끝났으면 `.hyper/feedback/<slug>/brief.md`도 | `hyper-git`이 뒤따르면 바뀐 경로, `hyper-plan`을 덧붙이면 브리프 경로와 전달 플래그 |
| `hyper-debug` | 사용자 요청 그대로와 실패 근거(트레이스 발췌, 실패한 명령이나 테스트 이름, 관찰한 출력과 기대한 출력), 수정을 요청했는지, 사용자의 제약, 모든 앞 단계 산출물 경로 | `Result:` 줄 하나(`confirmed`, `fixed`, `handoff`, `unconfirmed`, `awaiting_input`, `blocked`)로 끝나는 `.hyper/debug/<slug>.md`. 재현 방법, 확인한 원인의 토글 증명, `fixed`면 빨강에서 초록으로 바뀐 명령 출력을 담습니다 | `hyper-git`이 뒤따르면 바뀐 경로, `hyper-plan`을 덧붙이면 기록 경로와 전달 플래그 |
| `hyper-review` | 사용자 요청 그대로와 리뷰 대상(diff, 커밋 범위, base가 붙은 브랜치, 풀 리퀘스트 번호, 또는 "작업 트리"), 모드 단어(`review-only`, 사용자가 수정을 요청했을 때만 `review-and-fix`), 사용자의 제약, 모든 앞 단계 산출물 경로 | `.hyper/review/<slug>.md`. 대상, 콘텐츠 동일성(`HEAD`, diff 다이제스트, 미추적 다이제스트와 개수), QA 매트릭스, 리뷰어 영수증, 수정 순서의 블로커, `Result:` 줄 하나(`passed`, `failed: <n> blockers`, `inconclusive: <증명 못 한 행>`, `fixed: <n> blockers repaired, review passed on <identity>`, `awaiting_input`, `blocked`)를 담습니다 | 보고서 경로와 그 `Result:` 줄. `review-and-fix`에서는 `hyper-git`이 뒤따를 때 바뀐 경로 |
| `hyper-cleanup` | 사용자 요청 그대로와 정리할 파일 목록이나 diff, 동작을 잠그는 테스트 명령, 사용자의 전달 단어, 앞 단계 산출물 경로 전부 | `.hyper/cleanup/<slug>.md`. 동작 잠금, 사다리 결정, 지운 헌크, 테스트 원장, 보존한 코드, `Result:` 줄 하나(`clean`, `no-change`, `awaiting_input`, `blocked`)를 담습니다 | `hyper-git`이 뒤따를 때 바뀐 경로, 보고서 경로와 그 `Result:` 줄 |
| `hyper-data` | 사용자 요청 그대로와 질문, 데이터셋 경로, 요청에 있으면 읽는 사람의 시간대, 앞 단계 산출물 경로 전부 | `Result:` 줄 하나(`answered`, `prerequisite_missing`, `awaiting_input`, `blocked`)로 끝나는 `.hyper/data/<slug>/report.md`. 답을 먼저 쓰고, `answered`면 쿼리, 행 수, 소요 시간, 입력 digest를 담습니다 | - |
| `hyper-handoff` | 사용자 요청 그대로, 모드(쓰기, 확인, 이어받기), 지목한 메모 경로나 slug, 앞 단계 산출물 경로 전부 | `Check:` 줄(`pass`, `unverified-standalone: <질문 번호>`, `self: pass`, `self: fail: <질문 번호>`, `skipped by user` 중 하나)이 있는 `.hyper/handoff/<slug>/memo.md`. 이어받기 모드는 세 줄 되풀이 | - |
| `hyper-imagegen` | 사용자 요청 그대로, 있으면 제공한 편집 원본이나 참고 자료 경로, 모든 앞 단계 산출물 경로 | 종료 상태 한 줄(`generated_verified`, `generated_caveated`, `prompt_saved`, `awaiting_input`, `blocked` 중 하나)과 그 근거. 런타임이 돌려준 이미지 기록이나 `.hyper/imagegen/<topic>/` 아래 파일의 상대 경로와 digest | - |
| `hyper-plan` | 사용자의 원래 요청, 꼭 읽어야 할 앞 단계 산출물 경로 전부, 전달 플래그, 사용자가 말했다면 `--plan-only`나 승인 보류 | `## Handoff` 섹션이 있는 `.hyper/plans/<slug>.md` | 없음. 이 단계가 스스로 `hyper-execute`로 이어집니다 |
| `hyper-debate` | 토론을 선택한 표현이 그대로 들어간 사용자의 원래 요청, 꼭 읽어야 할 앞 단계 산출물 경로 전부, 전달 플래그. 승인 지점은 정확히 한 번이고 두 번째 질문을 하지 않는다는 점을 함께 넘깁니다 | `.hyper/debate/<slug>/` 영수증(라운드 1~3과 장부)과, 같은 계획 모양으로 쓴 `.hyper/plans/<slug>.md`. 묶음 끝의 `Result:`는 `planned`, `reduced-planned`, `awaiting-approval`, `declined`, `blocked` 중 하나 | 없음. 승인 뒤에 이 단계가 스스로 `hyper-execute`로 이어집니다 |
| `hyper-execute` | 계획 slug와 전달 플래그 | `status`가 `complete`인 `.hyper/execute/<slug>/state.json`과 출력된 완료 블록 | - |
| `hyper-mass` | 목표, 성공 기준, 앞 단계 산출물 경로 전부 | `status`가 `completed`인 `run.settled` 이벤트로 끝나는 `.hyper/mass/<run-key>/run.jsonl` | - |
| `hyper-loop` | 사용자 요청 그대로와 그 목표·기준, 재개라면 루프 slug, 사용자의 제약, 앞 단계 산출물 경로 전부 | `status`가 `complete`, `blocked`, `paused` 중 하나인 `.hyper/loop/<slug>/final-gate.json`. `complete`면 종료 코드 0으로 끝난 `verify-loop-state.sh --final` 실행 결과 | `hyper-git`이 뒤따를 때는 바뀐 경로 |
| `hyper-skill` | 사용자의 원래 요청, 있으면 대상 `skills/<name>/` 경로, 꼭 읽어야 할 앞 단계 산출물 경로 전부 | `skills/<name>/SKILL.md`와 `SKILL.ko.md`, 그리고 그 단계의 검증 handoff에 오류 0개로 기록된 검증기 실행 결과 | `hyper-git`이 뒤따를 때는 바뀐 경로 |
| `hyper-documentation` | 사용자의 원래 요청, 있으면 대상 경로, 꼭 읽어야 할 앞 단계 산출물 경로 전부 | 요청한 경로에 만들거나 고친 산출물, 고른 모드의 검증 handoff, 기계가 읽는 프롬프트 산출물이면 파싱 결과 | `hyper-git`이 뒤따를 때는 바뀐 경로 |
| `hyper-git` | 모드(커밋, PR이나 작업 브랜치 전체 병합이면 워크플로), 커밋 범위로 삼을 앞 단계의 바뀐 경로, 사용자 순서대로의 대상 브랜치, 사용자의 제한("커밋만", "main 빼고") 그대로 | 보고한 각 커밋 SHA가 모든 원격 대상에서 발견된 것(`git fetch origin <target>` 뒤 `git branch -r --contains <sha>`, 또는 `+` 줄이 없는 `git cherry origin/<target> <branch>`), 또는 `gh pr view`로 읽은 상태를 붙인 PR URL | - |
| `hyper-deploy` | 사용자 요청 그대로, 환경 이름을 가리키는 말("staging", "프로덕션", "preview"), 꼭 읽어야 할 앞 단계 산출물 경로 전부, 계획 단계 뒤에 오면 실행 완료 블록 | `Result` 줄에 `ready`, `unproven`, `deployed`, `changed`, `fixed`, `exhausted`, `stopped-for-approval`, `blocked`, `handoff` 중 하나를 적고 그 근거를 붙인 `.hyper/deploy/<slug>/report.md` | 없음. 체인의 마지막 단계입니다 |

모든 전달에 적용하는 규칙:

- 단계를 done으로 표시하기 전에 산출물을 디스크에서 읽습니다. 파일 없이 채팅에서만 완료를 주장한 단계는 전달 실패입니다.
- `hyper-git` 단계는 앞 단계의 완료 근거가 통과한 뒤에만 시작합니다. 검증기에 실패한 작업은 전달로 넘어가지 않습니다.
- 앞 단계 산출물은 경로로 넘기고 다음 단계에 필요한 결론만 최대 세 줄 덧붙입니다. 보고서 전체를 붙여 넣지 않습니다.
- 사용자의 제약(범위 제한, 제외 경로, "커밋하지 말고")은 모든 단계에 그대로 넘깁니다.
- 계획 단계 뒤에 오는 `hyper-deploy` 단계는 실행 완료 블록 뒤에만 시작합니다. 그래서 완료 블록을 요청의 일부로 받고, 아직 바뀌는 중인 트리가 아니라 전달이 끝난 결과를 배포합니다.

`hyper-research` 단계 안의 `hyper-browsing` 동반 규칙:

- 단계 스킬처럼 런타임의 스킬 기능으로 불러오고, 막힌 출처 하나씩 처리합니다. 출처 URL, 그 출처가 뒷받침할 조사 질문, 그 주장에 날짜가 붙은 사본을 써도 되는지를 넘깁니다.
- 종료 상태 `blocked`와 `needs_user`는 체인을 멈추지 않습니다. 리서치 단계가 그 출처를 접근 불가로 기록하고 다른 채널로 계속합니다. 체인은 리서치 단계 자체가 멈출 때만 멈춥니다.
- `sources.md` 행이 인용한 접근 보고서 파일이 없으면 산출물이 없는 것과 같이 리서치 전달 실패입니다.
- `hyper-browsing` 스킬이 설치돼 있지 않으면 리서치 단계는 막힌 출처를 접근 불가로 기록하고, 마무리 보고에 `npx skills add alpoxdev/hypercore --skill hyper-browsing`을 적습니다.

## 2. 계획에서 실행으로 넘어가는 단계

`hyper-plan`은 자기 조건이 맞으면 같은 세션에서 `hyper-execute`로 이어집니다. 이 스킬은 그 실행을 직접 시작하지 않습니다.

계획 단계가 돌아오면 계획의 `## Handoff` 줄을 읽습니다.

| `Auto-execute` value | Meaning | Next action |
|---|---|---|
| `yes` | 계획 단계 안에서 실행이 돌았습니다 | `.hyper/execute/<slug>/state.json`을 확인합니다. `complete`면 체인이 끝나고, `active`나 `paused`면 실행이 진행 중이거나 멈춘 것이므로 그 실행 자신의 보고가 결정합니다 |
| `no (plan only requested)` 또는 `no (approval requested)` | 사용자가 계획 뒤에 멈추라고 했습니다 | Report 작업으로 체인을 끝냅니다 |
| 그 밖의 `no (...)` | 계획 단계가 강제 정지에 걸렸습니다 | 그 사유로 체인을 멈춥니다(§5) |

## 3. 워크플로 기록

첫 단계 전에 `.hyper/workflows/<slug>.md`를 씁니다. `<slug>`는 작업을 나타내는 짧은 kebab-case 이름이고, 다른 작업의 파일이 이미 있으면 `-2`, `-3`을 붙입니다. 경로, 스킬 이름, 플래그를 빼고 한국어로 씁니다.

```markdown
# <job title>

- 요청: <the user's request, verbatim>
- 작업 종류: build | report | resume
- 전달: local | make-pr | ship | plan-only | git:<mode> <targets>
- 상태: running | done | stopped
- 정지 사유: <reason, or 없음>

## 단계

| # | 단계 | 선택 근거 | 상태 | 산출물 |
|---|---|---|---|---|
| 1 | hyper-architecture | "폴더 구조 리팩토링" + package.json `next` | done | 단계 메모 1 |
| 2 | hyper-plan | 여러 파일 변경 | running | .hyper/plans/<slug>.md |

## 단계 메모

### 1. hyper-architecture
<routing line and findings with file paths>
```

단계 상태 값은 `pending`, `running`, `done`, `skipped`, `stopped`입니다. 단계가 시작될 때와 끝날 때 상태 줄을 출력하기 전에 행을 갱신합니다.

## 4. 단계 결과

| Stage result | Action |
|---|---|
| 산출물이 있고 단계가 성공을 보고함 | `done`으로 표시하고 `<#>/<total> <stage> 완료 - <artifact>`를 출력한 뒤 다음 단계를 시작합니다 |
| 앞 단계 자리의 `hyper-architecture`가 지원하지 않는 스택으로 멈춤 | 사유와 함께 `skipped`로 표시하고 계속합니다. 그 출력은 참고 근거였기 때문입니다 |
| 단계가 요청의 결과물 형태가 다르다며 멈춤 | 한 번 다시 라우팅합니다(§6) |
| `hyper-imagegen`이 `awaiting_input`으로 끝남 | 그 단계의 질문 하나를 그대로 전하고 `stopped`로 표시합니다. 답을 받으면 같은 단계부터 재개합니다 |
| `hyper-feedback`이 `handoff`로 끝남 | `done`으로 표시하고, `brief.md`를 필수 입력으로, 사용자의 전달 플래그를 함께 넘기는 `hyper-plan`을 다음 단계로 붙이며, 계획에 있던 `hyper-git` 단계는 뺍니다 |
| `hyper-feedback`이 `awaiting_input`으로 끝남 | 그 단계의 질문 하나를 그대로 전하고 `stopped`로 표시합니다. 답을 받으면 같은 단계부터 재개합니다 |
| `hyper-feedback`이 `exhausted`로 끝남 | 실패한 명령과 출력을 적어 `stopped`로 표시합니다. `hyper-git` 단계는 시작하지 않습니다 |
| `hyper-debug`가 `handoff`로 끝남 | `done`으로 표시하고, `.hyper/debug/<slug>.md`를 필수 입력으로, 사용자의 전달 플래그를 함께 넘기는 `hyper-plan`을 다음 단계로 붙이며, 계획에 있던 `hyper-git` 단계는 뺍니다 |
| `hyper-debug`가 `unconfirmed`로 끝남 | `Assumption:` 줄과 그것을 확인할 점검을 적어 `done`으로 표시합니다. 고칠 대상이 증명되지 않았으므로 `hyper-git`이나 `hyper-plan` 단계는 시작하지 않습니다 |
| `hyper-debug`가 `awaiting_input`으로 끝남 | 그 단계의 질문 하나를 그대로 전하고 `stopped`로 표시합니다. 답을 받으면 같은 단계부터 재개합니다 |
| `hyper-review`가 `passed`로 끝남 | `done`으로 표시하고 보고서 경로와 `Result:` 줄을 마무리 보고로 넘깁니다. 뒤에 붙인 `hyper-git` 단계는 사용자의 전달 단어가 있을 때만 시작합니다 |
| `hyper-review`가 review-only 모드에서 `failed`나 `inconclusive`로, 또는 한정된 수정 회차를 마친 뒤 `failed`로 끝남 | 보고서의 블로커나 증명 못 한 행을 적어 `done`으로 표시하고 거기서 체인을 멈춥니다. `hyper-git` 단계는 시작하지 않고, 마무리 보고에 다시 리뷰하기 전에 무엇을 바꿔야 하는지 적습니다 |
| `hyper-review`가 `awaiting_input`이나 `blocked`로 끝남 | 그 단계의 질문 하나나 환경 장애를 그대로 전하고 `stopped`로 표시합니다. 답을 받으면 같은 단계부터 재개합니다 |
| `hyper-data`가 `awaiting_input`이나 `prerequisite_missing`으로 끝남 | 그 단계의 질문 하나, 또는 없는 엔진과 설치 명령을 그대로 전하고 `stopped`로 표시합니다. 답을 받거나 설치한 뒤 같은 단계부터 재개합니다 |
| `hyper-handoff`가 `Check: unverified-standalone: <질문 번호>`나 `Check: self: fail: <질문 번호>`로 끝남 | `done`으로 표시하고 실패한 질문 번호를 마무리 보고에 단서로 넘깁니다. `hyper-git` 단계는 뒤따르지 않습니다 |
| `hyper-handoff`가 찾지 못한 사실 때문에 멈춤 | 빠진 사실 하나를 그대로 전하고 `stopped`로 표시합니다. 답을 받으면 같은 단계부터 재개합니다 |
| `hyper-loop`가 `blocked`나 `paused`로 끝남 | `final-gate.json`의 목표와 실패 서명이나 멈춘 이유를 적어 `stopped`로 표시합니다. `hyper-git` 단계는 시작하지 않고, "이어서"를 받으면 `.hyper/loop/<slug>/`에서 루프를 재개합니다 |
| `hyper-frontend`가 `delivered_unverified`로 끝남 | `done`으로 표시하고 보고서의 없었던 브라우저 기능을 마무리 보고에 주의 사항으로 옮깁니다. `hyper-git` 단계는 사용자의 전달 단어가 있을 때만 이어집니다 |
| `hyper-frontend`가 `awaiting_input`으로 끝남 | 그 단계의 질문 하나를 그대로 전하고 `stopped`로 표시합니다. 답을 받으면 같은 단계부터 재개합니다 |
| `hyper-frontend`가 `blocked`로 끝남 | 보고서의 실패한 캡처와 증거를 적어 `stopped`로 표시합니다. `hyper-git`이나 `hyper-plan` 단계는 시작하지 않습니다 |
| `hyper-google-analytics`가 `exhausted`, `stopped-for-approval`, `delayed`, `blocked`, `handoff`로 끝나거나 `hyper-google-tagmanager`가 `proposed`, `exhausted`, `blocked`로 끝남 | 보고서의 승인이 필요한 제안 동작, 실패한 확인, 막힌 이유를 적고 `stopped`로 표시합니다. `hyper-git`이나 `hyper-deploy` 단계는 시작하지 않고, 승인이나 수정 뒤 "이어서"로 같은 단계에서 재개합니다 |
| 단계가 사용자 결정, 자격 증명, 충돌, 실패한 게이트로 멈춤 | `stopped`로 표시하고 체인을 끝냅니다(§5) |
| 단계 스킬이 설치되지 않았거나 불러올 수 없음 | `stopped`로 표시하고 체인과 `npx skills add alpoxdev/hypercore --skill <stage>`를 보고합니다 |

통과시키려고 단계 산출물을 고치지 않고, 멈춘 단계를 더 약한 입력으로 다시 실행하지 않으며, 건너뜀으로 정한 경우가 아닌 정지를 넘어서 계속하지 않습니다.

## 5. 정지 보고

체인이 일찍 끝나면 한국어로 다음을 출력합니다.

1. 각 단계의 최종 상태를 붙인 라우팅 줄
2. 멈춘 단계, 그 단계 자신의 사유 한 줄, 사용자가 풀 수 있는 방법 하나
3. 나중에 "이어서"로 재개할 수 있게 기록 경로

## 6. 재라우팅과 재개

- 재라우팅: 단계가 요청의 결과물 형태가 다르다고 하면(계획 단계가 사실은 리서치 작업이라고 보고함) 그 근거로 `rules/workflow-routing.md`에 따라 체인을 다시 만들고, 두 체인을 모두 기록한 뒤 계속합니다. 두 번째로 형태가 맞지 않으면 실행을 멈춥니다.
- 재개: "이어서" / "continue"이면 이 순서로 이어갈 대상을 찾습니다. 요청에서 지목한 메모 경로, 현재 브랜치나 워크트리와 맞는 `.hyper/handoff/` 아래 열린 메모, 열린 워크플로 기록, 열린 실행 상태. 열린 메모는 이어받기 모드로 먼저 읽고, 그다음 메모가 가리키는 기록이나 실행을 이어갑니다. 닫힌 메모는 사용자가 지목하지 않으면 무시합니다. 기록이 있으면 멈춘 단계의 차단 요인이 사라졌는지 확인하고 `done`도 `skipped`도 아닌 첫 단계부터 다시 시작합니다. 기록은 없고 열린 실행 상태만 있으면 `hyper-execute` 단독으로 보냅니다. 셋 다 없는 평범한 "이어서 해줘"는 핸드오프 트리거가 아닙니다. 체인 중간에 쓴 메모는 `Where`에 워크플로 기록 경로를 적고, 기록은 그대로 두며 다음 세션은 메모를 먼저 읽습니다.

## 7. 마무리 보고

한국어로 보고합니다. 상태를 붙인 최종 체인, 각 산출물 경로, 마지막 단계의 완료 근거(실행 완료 블록, mass 실행의 검증 결과, `--final` 종료 코드를 담은 루프의 `final-gate.json`, 스킬 검증기 결과, 이슈 기록의 번호와 URL 및 명세 경로, 문서 모드의 검증 handoff, 데이터베이스 보고서의 검증 절, MCP 보고서의 검증 표, 쓴 경로 전부와 오프라인 요청 검사기 종료 코드를 담은 결정 단계 보고, 수집 증명을 담은 GA 보고서의 `Result` 줄, 태그 발화 증명을 담은 GTM 보고서의 `결과:` 줄, UI 보고서의 검증기 결과와 정석 수치 점검 줄, 변경 요청 보고서의 항목 표와 잔여 검색 결과, 토글 증명을 담은 디버그 기록의 `Result` 줄, 행 수와 입력 digest를 담은 데이터 보고서의 `Result` 줄, 이미지 단계의 종료 상태와 경로·digest·검사 기록, 원격 대상마다 확인한 Git 전달의 커밋 SHA, 배포 보고서의 `Result` 줄과 배포 ID·종료 상태, 보고서 경로), 전달 결과(로컬 커밋, PR URL, 병합), 동반 스킬의 접근 보고서와 그 종료 상태, 건너뛰거나 멈춘 단계와 그 사유를 담습니다.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| 단계 산출물 경로와 상태 값(`.hyper/research/`, `.hyper/seo/<slug>/`, `.hyper/google-analytics/<slug>/report.md`와 그 열 가지 종료 상태, `.hyper/gtm/<slug>/report.md`와 그 다섯 가지 결과, `.hyper/database/<slug>/report.md`, `.hyper/mcp/<slug>/report.md`, `.hyper/decision/<topic>/`와 그 검사기 경로, `.hyper/design/<slug>/brief.md`와 `report.md`, `.hyper/frontend/<slug>/report.md`와 프런트엔드 단계의 네 종료 상태, `.hyper/feedback/<slug>/report.md`와 `brief.md` 및 변경 요청 단계의 실행 종료 상태, `.hyper/debug/<slug>.md`와 디버그 단계의 여섯 종료 상태, `.hyper/review/<slug>.md`와 리뷰 단계의 여섯 `Result:` 값, `.hyper/cleanup/<slug>.md`와 정리 단계의 네 종료 상태, `.hyper/loop/<slug>/final-gate.json`과 그 세 가지 상태, `.hyper/data/<slug>/report.md`와 데이터 단계의 네 종료 상태, `.hyper/handoff/<slug>/memo.md`와 그 다섯 가지 `Check:` 값, `.hyper/imagegen/<topic>/`와 이미지 단계의 다섯 종료 상태, `.hyper/deploy/<slug>/report.md`와 그 아홉 가지 결과 값, `.hyper/plans/<slug>.md`, `state.json` `status`, `run.settled`, `skills/<name>/SKILL.md`, 문서 산출물 경로, Git 전달의 원격 브랜치 확인) | 이 저장소의 각 단계 스킬 `SKILL.md`와 references, 2026-11-09 |
| 계획 단계의 `## Handoff` 줄과 실행으로 자동 연결 | 이 저장소의 계획 스킬 handoff 규칙, 2026-11-06 |
| 아키텍처 단계가 지원하지 않는 스택에서 멈추고 없는 스킬의 설치 명령을 보고함 | 이 저장소의 아키텍처 스킬 stack-detection 규칙, 2026-11-06 |
| 채팅이 아니라 저장된 산출물과 지속 상태로 전달 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 워크플로 기록 형태, 건너뜀 규칙, 한 번의 재라우팅 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
| `hyper-browsing` 동반 규칙: 호출마다 막힌 출처 하나, 체인을 멈추지 않는 종료 상태, 보고서 존재 확인 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
| 재개 대상을 찾는 순서(지목한 메모, 열린 메모, 워크플로 기록, 실행 상태), 닫힌 메모 규칙, 평범한 이어서 요청 제외, 중간에 쓴 메모가 기록을 그대로 두는 규칙 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
