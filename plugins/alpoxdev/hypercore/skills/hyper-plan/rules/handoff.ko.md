# 인계

리뷰 판정이 나오면 이 파일을 사용합니다. 이 파일은 채팅 요약, 자동 인계 결정, 거부와 전달 단어, 정지 보고를 맡습니다.

## 1. 인계 요약 형태

완성된 계획 파일에서 끌어낸 아래 구조를 한국어로 전달합니다. 행은 명령이나 검색으로 세고 추정하지 않습니다.

1. **이 계획이 이끄는 일** - 수행할 작업을 한두 문장으로 적습니다.
2. **영향받는 사용자와 이상 상태** - 결과가 닿는 대상과, 실행이 끝난 뒤 그 대상에게 새로 생기거나 달라지는 것을 적습니다.
3. **형태** - todo 수(`- [ ] <N>.` 행), `F` 행 수, wave 수, tier 구성을 적습니다. 예: `6 low, 2 medium, 1 high`.
4. **요청 밖 추가** - 탐색에서 드러나 계획에 접어 넣은 항목과 한 줄 이유를 적습니다. 없으면 `none`이라고 씁니다.
5. **검증** - 최종 검증 wave와 완료를 증명할 핵심 QA 명령을 적습니다.
6. **실행 인계** - 다음 단계, 전달 방식, 계획 경로를 적습니다.

## 2. 자동 인계 규칙

아래 조건을 모두 갖출 때 `hyper-execute`로 이어갑니다. 이 단계는 질문이 아니라 자동입니다. 조건 세 가지가 성립하면 같은 세션에서 인계를 진행합니다.

1. 계획 파일이 있고 `rules/plan-review.ko.md`의 구조 자기 점검을 통과했으며, 필요한 리뷰가 승인했거나 열린 블로커 없이 수렴했다
2. 사용자가 거부하지 않았고, 계획을 먼저 승인받겠다고 하지도 않았다
3. 미해결 소유자 결정이 없다

사용자가 플래그를 줬든 문장으로 말했든 §3에서 정한 전달 플래그를 그대로 넘깁니다. `--make-pr`, `--ship`이 여기에 해당합니다.

턴을 끝내지 않고 같은 세션에서 실행 스킬을 호출해 이어갑니다. 런타임의 스킬 기능으로 `hyper-execute`를 불러오고(스킬이 일반 파일인 환경에서는 그 `SKILL.md`를 읽고), slug와 전달 플래그를 넘겨 첫 단계부터 따릅니다. 넘어가기 전에 계획에 `Auto-execute: yes`를 기록합니다. 그 스킬이 이 세션에 설치되어 있지 않을 때만 `Auto-execute: no (execution skill not installed)`로 멈추고, 사용자가 직접 실행할 수 있도록 정확한 호출 `hyper-execute <slug>`와 전달 플래그를 출력합니다.

## 3. 거부와 전달 단어

명시적 거부는 계획 뒤에서 실행을 멈춥니다. 다음 표현이 해당합니다.

- `--plan-only`
- "plan only", "just the plan"
- "계획만", "계획만 세워줘", "실행하지 말고", "실행하지 마", "실행은 나중에"
- "don't execute", "no execution"

승인 보류도 계획 뒤에서 실행을 멈추지만 작업을 끝내지는 않습니다. 다음 표현이 해당합니다.

- "승인은 내가 할게", "내가 승인할게"
- "I'll approve", "wait for my approval"

승인 보류는 `approval: user`로 기록하고, 계획을 전달한 뒤 `Auto-execute: no (approval requested)`로 멈춥니다. 이후 메시지에서 사용자가 승인하면 같은 계획으로 실행에 이어갑니다. 계획을 다시 만들지 않고, 계획 자체가 바뀌지 않은 한 리뷰도 다시 돌지 않습니다.

전달 단어는 모드를 고릅니다. 플래그와 자연어 표현을 모두 알아듣습니다.

| Word or flag | Handoff value | Effect |
|---|---|---|
| 없음 | `Delivery: local` | 구현이 통합 기준 브랜치에 커밋되고 push하지 않는다 |
| `--make-pr`, "make a PR", "PR만", "PR까지만", "PR로" | `Delivery: make-pr` | 구현이 풀 리퀘스트로 도착하고 병합하지 않는다 |
| `--ship`, "ship", "merge it", "머지까지", "배포까지" | `Delivery: ship` | 풀 리퀘스트를 만든 뒤 검사가 통과하면 병합한다 |

사용자가 플래그를 적었든 문장으로 말했든, 정해진 플래그를 인계까지 그대로 넘깁니다.

## 4. 정지 조건

다음 중 하나라도 해당하면 자동 인계 없이 멈춥니다.

- 소유자 결정이 미해결이다: 되돌릴 수 없거나 파괴적인 변경, 롤백할 수 없는 마이그레이션, 새 비용이나 지출, 자격 증명이나 계정 접근, 외부 게시나 전송
- 사용자가 계획을 먼저 승인받겠다고 했다
- 필요한 고정밀 리뷰를 독립 리뷰어가 없어 실행할 수 없다
- 필요한 리뷰가 3라운드 안에 수렴하지 않았다
- 구조 자기 점검이 실패했고 새 근거 없이 고칠 수 없다
- `.hyper/plans/<slug>.md`에 계획 파일을 쓸 수 없다
- 사용자의 요구가 다른 출력 형태로 밝혀졌다. 요구사항 패키지나 리서치 리포트가 여기에 해당한다

## 5. 정지 보고

정지 사유를 계획의 어휘로 한 줄에 말한 뒤, 사용자가 막힌 부분을 풀 수 있는 일 하나를 밝힙니다. 계획 전체를 다시 읽지 않습니다.

| Reason | Line |
|---|---|
| 거부 | `Auto-execute: no (plan only requested)` |
| 승인 보류 | `Auto-execute: no (approval requested)` |
| 열린 소유자 결정 | `Auto-execute: no (owner decision pending: <topic>)` |
| 고정밀 리뷰 실행 불가 | `Auto-execute: no (high-accuracy review needs independent reviewers)` |
| 수렴하지 않은 리뷰 | `Auto-execute: no (review did not converge after 3 rounds)` |
| 실패한 자기 점검 | `Auto-execute: no (structural self-check failed: <check>)` |
| 쓸 수 없는 계획 파일 | `Auto-execute: no (plan file not writable: <path>)` |
| 실행 스킬 미설치 | `Auto-execute: no (execution skill not installed)` |

## 6. Handoff 절 필드

계획의 `## Handoff` 절은 정확히 이 줄들을 담습니다.

```markdown
## Handoff
- Auto-execute: yes | no (<reason>)
- Delivery: local | make-pr | ship
- Plan-only requested: yes | no
```

채팅 요약과 계획 파일은 일치해야 합니다. 채팅 값은 인계 시점에 계산하고, 파일 값은 요약을 보내기 전에 맞춰 고칩니다.

세 줄은 리뷰 판정 뒤에 씁니다. 계획 내용이 아니라 인계 결정을 기록하는 줄이므로, 이 줄을 고쳐도 승인은 무효가 되지 않고 리뷰 라운드도 다시 돌지 않습니다.

## 7. 인계가 절대 하지 않는 일

- 구현, 제품 코드 수정, 구현자 호출을 하지 않습니다.
- 자동 인계 조건이 성립하는데 "진행할까요?"라고 묻지 않습니다.
- 드래프트에 기록되지 않은 리뷰 영수증을 주장하지 않습니다.
- 같은 요청에 두 번째 계획을 시작하지 않습니다.
- 스스로 커밋, push, 풀 리퀘스트 생성을 하지 않습니다.

## Sources

> 확인 2026-11-03.

| Claim | Source |
|---|---|
| 인계 요약 형태와 세어서 보고하기는 OmO 공유 스킬 패키지의 `ulw-plan` 전달 형식을 각색한 것 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| 자동 인계 조건, 거부 단어, 전달 모드, 정지 조건, 인계 필드 값 | 사용자 지시, 2026-11-03. 이 패키지 자체 설계 |
| 자동 인계가 기본이고 허락 질문 없이 일어난다 | 사용자 지시, 2026-11-03 |
| 인계 값은 채팅이 아니라 지속 상태에도 적는다 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 승인은 채팅 암호가 아니라 기록되는 구조적 노드다 | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지의 인계 절차와 패밀리 계약의 게이트를 서술합니다. 거부 어휘는 고른 목록이고 자연어 전체를 해석하는 파서가 아닙니다.
