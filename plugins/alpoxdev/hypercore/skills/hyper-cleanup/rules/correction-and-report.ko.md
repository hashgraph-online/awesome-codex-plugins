# 교정과 보고

수정 뒤 게이트가 실패할 때, 그리고 마무리 보고를 쓰기 전에 이 파일을 읽습니다. hunk 단위 교정, 되돌림 한계, `.hyper/cleanup/<slug>.md` 보고서, 마지막 한 줄을 맡습니다.

## 1. 실패한 게이트는 잡음이 아니라 근거다

수정 뒤 검사가 실패하면 그 실패는 hunk를 이름으로 댑니다. 다른 것을 바꾸기 전에 그것을 찾습니다.

1. **어느 hunk인가.** 실패한 case를 동작 잠금의 기준과 비교합니다. 이전에 통과했는데 지금 실패하는 case는 이번 실행의 수정이 원인입니다.
2. **메커니즘.** 수정과 실패를 잇는 문장 하나를 씁니다. 문장에 "그다음 무언가"가 필요하면 메커니즘을 이해하지 못한 것이고, 그 hunk는 추측하지 않고 되돌립니다.
3. **가장 작은 교정.** 현재 파일 내용을 기준으로 그 hunk만 고치거나 되돌립니다. 수정은 그 줄만 건드립니다.

기준에 이미 있던 실패는 이번 실행이 고칠 것이 아닙니다. 출력과 함께 보고서의 기준 빨강 목록으로 가고 그대로 둡니다.

## 2. 파일이 아니라 hunk를 고친다

교정의 단위는 hunk와 현재 내용입니다.

- 실패한 hunk가 소유한 줄만 고칩니다. 주변 함수를 다시 쓰는 교정은 자체 위험이 있는 새 변경입니다.
- 고치기 전에 파일을 다시 읽습니다. 다른 수정, 포매터, 동시 세션이 실패 실행 이후에 파일을 바꿨을 수 있습니다.
- 교정이 영향을 줄 수 있는 검사만 다시 돌립니다. 한 줄 고친 뒤 전체 스위트를 다시 돌리는 것은 얻는 것 없이 보고를 늦춥니다.

예외 없이 금지하는 교정:

- `git checkout -- <file>`, `git restore <file>`, `git reset`, 사용자의 미커밋 작업까지 버리는 모든 파일 단위 되돌림
- 같은 파일에 우연히 있는 무관한 hunk 삭제나 재작성
- 바뀐 동작이 통과하도록 기대값, 스냅숏, 단언을 고치는 일
- 실패한 테스트를 skip, 집중, 격리로 표시하는 일
- 게이트를 초록으로 만들려고 경고를 끄거나, catch를 넓히거나, 재시도를 더하는 일

게이트가 올바르게 잡은 동작 변경은 게이트의 버그가 아닙니다. 정리가 그 동작을 지킬 수 없으면 hunk를 되돌리고 한계를 보고서에 적습니다.

## 3. 교정이 반복될 때

같은 hunk에서 두 번 실패하면 시도를 끝냅니다. hunk를 되돌리고 실패 출력과 함께 보존한 코드에 기록합니다. 같은 줄에 세 번째 시도는 끈기가 아니라 헛돎입니다.

여기서 세 결과가 정당하고, 어느 것도 실행의 실패가 아닙니다.

- 단위가 남고 보고서가 이유를 적는다
- 단위가 기준 형태로 되돌아가고 보고서가 거부한 검사를 이름으로 댄다
- 필요한 기능이 없어 실행이 `blocked`로 끝나고 정확한 명령과 오류를 적는다

## 4. 마지막 게이트, 한 번

손댄 영역에 저장소가 요구하는 검사를 마지막에 한 번 돌립니다. 그다음 사용자가 읽듯이 diff를 검토합니다.

- 파일 목록이 아니라 diff 전체를 읽습니다.
- 제거한 모든 줄에 원장 행이 있고, 남긴 후보마다 이유가 있는지 확인합니다.
- 동작 잠금의 명령이 기준과 같은 결과를 내는지 확인합니다. 기록한 기준 빨강 case는 예외입니다.
- 트리에 디버그 출력, 임시 파일, 스크래치 스크립트, 이번 실행의 잔여 산출물이 없는지 확인합니다.

수정 없이 보고만 하는 정리도 기준 명령을 돌리고 보고서를 씁니다.

## 5. 보고서

보고서는 `.hyper/cleanup/<slug>.md`에 실행 하나당 파일 하나로 둡니다. 절이 고정되어 있어 두 실행을 비교할 수 있습니다.

```markdown
# Cleanup: <slug>

## Scope
- Request: <the user's words, quoted>
- Base: <branch or commit> — <HEAD sha>
- Files in scope: <paths>
- Files read as context: <paths>
- Working tree before: <clean | N modified, M untracked>

## Behavior lock
- Command: <exact command>
- Before: <pass | fail with case names>
- After: <pass | fail with case names>
- Baseline red: <case names with output, or none>

## Ladder decisions
| Unit | Rung | Decision | Proof |
|---|---|---|---|
| src/app.ts:42 | 4 | nested ternary flattened | same branches, same order |

## Removed hunks
| Path | Lines | Category | Replacement |
|---|---|---|---|
| src/app.ts | 42-48 | 3 excess complexity | early return |

## Tests ledger
| Test | Mark | Keeper or reason | Proof |
|---|---|---|---|

## Preserved code
- <unit> — <why it stayed: KEEP row, unproven guard, out-of-scope layer>

## Checks
| Check | Command | Result |
|---|---|---|

## Risks
- <a deferred risk, a ceiling, an unverified equivalence, or none>

Result: <terminal>
```

수정이 없는 보고서도 보고서입니다. 범위, 잠금, 검토한 것의 사다리 행, 보존한 코드가 값을 만듭니다.

## 6. 결과

보고서는 `Result:` 줄 하나로 끝납니다.

| 결과 | 뜻 |
|---|---|
| `clean` | 승인된 수정이 들어갔고, 잠금이 여전히 통과하며, 원장이 완전하다 |
| `no-change` | 범위 안에서 증명을 통과한 것이 없다. 보고서가 검토한 것과 단위마다 남은 이유를 기록한다 |
| `awaiting_input` | 파일로 정할 수 없는 모호함 때문에 질문 하나를 했다 |
| `blocked` | 필요한 기능, 접근, 명령을 쓸 수 없었다. 정확한 공백과 시도한 명령을 보고한다 |

`no-change`는 실제 결과이고 부드러운 실패가 아닙니다. 코드가 하중을 받는 코드베이스에서 꼼꼼히 읽고 아무것도 자르지 않는 실행이 정답입니다.

## 7. 보고서에 절대 없는 것

- 돌리지 않은 검사를 통과했다는 서술, 또는 다른 트리의 이전 실행 결과를 이번 통과로 쓰는 일
- 분류도 증명도 없는 제거 hunk
- 지키는 쪽이나 분류 증명 없이 지운 테스트
- 정리라고 부른 동작 변경
- 이 흐름에서 만든 커밋, 푸시, 병합, 풀 리퀘스트

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| 교정은 소유한 hunk만 건드리고 파일 전체를 되돌리지 않으며, 바뀐 동작을 통과시키려 기대값을 바꾸지 않음 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 교정 뒤 실패했거나 영향을 받는 검사만 다시 실행 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 사다리 결정, 분류, 대체, 안전한 이유를 파일별로 기록 | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| 보고서의 범위, 동작 잠금, 사다리, 원장, 보존, 검사, 위험 절 | integrator contract, 2026-11-10 (issue #24) |
| 네 결과와 `Result:` 줄 | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - 보고서 절 순서, 네 결과, 교정 두 번 제한은 이 패키지의 설계입니다. hunk 단위 교정, 파일 단위 되돌림 금지, 기대값 변경 금지는 라이선스가 없는 저장소에서 자기 말로 다시 썼으며 텍스트나 코드를 복사하지 않았습니다.
