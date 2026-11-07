# 보고서 템플릿

`.hyper/deploy/<slug>/report.md`를 쓸 때 이 참조를 사용합니다. `##` 제목은 영어로 두고 본문은 한국어로 씁니다.

## Template

```markdown
# <실행 제목>

- 모드: preflight | setup | deploy | change | diagnose
- 대상: <railway | cloudflare | docker-image | compose | vps> (<판단 파일>)
- 정체: <프로젝트 / 환경 / 서비스, Worker와 환경, 이미지 repo:tag, 또는 호스트와 Compose 프로젝트>
- 환경: <이름> (운영: yes | no)
- CLI: <바이너리> <--version에서 읽은 버전>
- 결과: ready | unproven | deployed | changed | fixed | exhausted | stopped-for-approval | blocked | handoff

## Evidence

- `<경로>:<줄>` - <그것이 보여 주는 것>
- `<명령>` -> <줄인 출력, 비밀 가림>

## Readiness

`bash skills/hyper-deploy/scripts/deploy-check.sh`의 `PRE_DEPLOY_SUMMARY executed=<n> skipped=<m>`, 종료 코드 <code>. 건너뛴 게이트: <이름 - 사유>.

## Actions

| # | 명령 | 등급 | 결과 |
|---|---|---|---|
| 1 | `<명령>` | proceed / named environment / approved | <상태나 출력 줄> |

## Diagnosis

| 증상 | 로그나 상태 줄 | 원인 | 수리 | 전 | 후 |
|---|---|---|---|---|---|

## Terminal State

- 배포: <ID나 버전> -> <상태>
- 상태 점검: <점검과 결과>
- 런타임 로그 구간: <제한한 구간과 치명적 오류 개수>

## Proposed, Not Run

- `<정확한 명령>` - <바뀌는 것>, <되돌리지 않는 것>, <제안하는 이유>

## Gaps And Risks

- <없는 CLI, 없는 자격 증명, `not run` 점검, 미해결 원인, 다시 확인했거나 하지 않은 자주 바뀌는 사실>
```

## Rules

- 모드가 만들 수 없는 절만 생략하고, 만들 수 있는데 아무 일도 없었으면 `none`이라고 씁니다.
- `## Actions`의 모든 명령은 이번 세션에서 실행했습니다.
- 토큰, 비밀, 연결 문자열을 가리고 무엇을 가렸는지 밝힙니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 보고서 필드와 결과 값 | 이 패키지의 설계, 2026-11-07 |
| 무엇을 시험했고 무엇을 관측했고 무엇을 생략했는지 기록하는 보고서 | `instructions/harness-engineering/references/evidence-and-recovery.md` |

### Evidence grade

`LOCAL` - 이 템플릿은 이 패키지 자체의 것입니다.
