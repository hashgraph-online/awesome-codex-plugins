# Expansion And Convergence

첫 수집 wave가 돌아온 뒤에 이 규칙 파일을 사용합니다. 이 파일은 `## EXPAND` lead 형식, 확장 wave, excursion, 그리고 수집을 멈추는 유일한 규칙을 담당합니다. `--quick`은 확장 wave를 돌리지 않고 이 파일을 건너뜁니다.

## 1. lead 형식

수집 결과, 즉 lane의 응답이나 leader가 하나의 axis를 직접 훑은 결과는 모두 다음 꼬리로 끝납니다.

```markdown
## EXPAND
- LEAD: <아직 조사하지 않은 발견> - WHY: <핵심 질문에 중요한 이유> - ANGLE: <시도할 별도 query 또는 source>
- DEAD END: <끝까지 파고들어 막다른 길로 확인된 lead>
```

확장할 것이 없는 결과는 `## EXPAND` 다음에 `none - <한 줄 이유>`를 적습니다. 이 꼬리가 없는 lane 응답은 미완성입니다. 꼬리를 요청하는 후속 메시지를 한 번 보내고, 그래도 오지 않으면 그 lane을 갭으로 기록합니다.

## 2. 확장 loop

| 요소 | 값 |
|---|---|
| 되먹임 | 새 `LEAD` 줄과 claim gate(`rules/claim-verification.md`)를 통과하지 못한 claim |
| 지표 | `expansion.md`에 남은 미확인 lead와 해당 깊이의 source floor |
| 보호 장치 | claim gate와 authority 규칙. lead는 side effect를 승인하지 못합니다 |
| 상한 | 해당 깊이의 확장 wave 예산(`SKILL.md`, 깊이 모드) |
| 결정 | 조사, 중복으로 종료, 막다른 길로 종료 중 하나를 lead마다 한 줄로 적습니다 |

wave마다 다음을 수행합니다.

1. 결과가 도착할 때마다 기록합니다. 요약, 새 ledger 행, `## EXPAND` 줄을 그대로 적습니다.
2. 새 lead를 `expansion.md`에서 지금까지 본 모든 lead와 대조해 중복을 제거합니다. 확정된 lead만 대상으로 하지 않습니다. 그래야 기각한 lead가 다시 나오지 않습니다.
3. 새 미확인 lead는 해당 깊이의 lane 상한 안에서 별도 query나 lane으로 조사합니다.
4. wave를 기록합니다. 실행한 lane이나 검색, 얻은 lead, 종료한 lead와 그 이유를 적습니다.
5. 사용자 조향을 전달합니다. 실행 도중 사용자가 범위, 출처, 언어, 형식을 바꾸면 그 표현을 그대로 기록하고 다음 wave 전에 살아 있는 모든 lane에 전달합니다.

## 3. excursion

excursion은 wave 계획에 없던 발견을 쫓는, 범위가 정해진 우회입니다. excursion 중에도 핵심 질문은 바뀌지 않습니다.

이름이 붙은 방아쇠가 있을 때만 들어가고, 어느 것인지 적습니다.

1. 그 발견이 claim table에 이미 있는 claim과 모순됩니다.
2. 사실이라면 최종 답이나 권고가 달라집니다.
3. 어떤 axis도 맡지 않은 source 영역을 엽니다.
4. 사용자의 조향이 그것을 가리킵니다(그 말을 인용합니다).

관심만으로는 방아쇠가 되지 않습니다. 그런 발견은 대기 중인 lead로 남습니다.

들어가기 전에 예산을 적습니다. 이 단계에서 쓸 검색 수나 lane 수입니다. excursion은 중첩 excursion을 최대 하나만 열 수 있습니다. 세 번째 단계가 필요하다는 것은 그 발견이 별도 연구 질문이라는 뜻입니다. 표면으로 꺼낸 뒤 해당 깊이의 상한 안에서 axis로 승격하거나 범위 밖 갭으로 기록합니다.

다음 중 하나가 성립하면 종료합니다.

- 방아쇠가 해소됐을 때. claim이 공인되거나 반박됐거나 그 의존 관계가 닫혔을 때입니다.
- 연속 두 번의 probe가 상위 답을 바꾸지 못했을 때
- 그 발견이 더는 어떤 claim의 상태도 바꾸지 못할 때
- 적어 둔 예산을 다 썼을 때

종료할 때마다 상위 답에서 excursion이 무엇을 바꿨는지 한 줄로 적습니다. `none - <이유>`도 유효하며 반드시 적어야 하는 결과입니다. 종료 후마다 핵심 질문을 다시 읽고 이번 실행이 여전히 그 질문에 답하는지 확인합니다. 아무것도 바꾸지 못한 excursion이 세 번 연속되면 그 실행에서는 excursion을 끝냅니다.

## 4. 중지 규칙

다음이 수집을 멈추는 유일한 규칙입니다. lane이 끝나는 것은 여기에 들지 않습니다.

수렴(converged) - source floor를 충족했고 다음 중 하나가 성립하면 수집을 멈춥니다.

- 미확인 lead가 하나도 남지 않았을 때. 각 lead를 조사했거나 종료했습니다.
- 연속 두 wave가 새 실행 가능 lead를 만들지 못했을 때
- 서로 다른 세 query에서 같은 결과가 새 내용 없이 반복될 때

lead가 바닥났는데 source floor에 아직 못 미치면 남은 wave를 floor를 채우는 표적 query에 씁니다. 상한이 먼저 오면 그 실행은 `exhausted`이고 부족분을 명시합니다.

최소 조건. `--deep`은 첫 wave 뒤에 lead가 남아 있으면 확장 wave를 최소 두 번 돌립니다.

소진(exhausted) - lead가 열린 채로 해당 깊이의 wave 상한에 닿았을 때, 또는 남은 시간이나 컨텍스트를 검증과 리포트에 써야 할 때 멈춥니다(대략 마지막 5분의 1을 그 둘에 남겨 둡니다). 이 실행은 수렴이 아니라 `exhausted`로 보고하고 네 항목을 적습니다. 닿은 상한, 열린 lead, 마지막 wave의 결과, 연장하면 무엇을 조사할지입니다. `--deep`에서는 연장을 질문 하나로 제시합니다. 답 없이 실행하지 않습니다.

차단(blocked) - 진전에 credential, 계정 작업, 구매, 또는 이 스킬의 권한 밖 side effect가 필요할 때 멈춥니다. 빠진 접근을 갭으로 명시합니다.

## Sources

> 확인 2026-11-03.

| Claim | Source |
|---|---|
| `## EXPAND` 꼬리, 지금까지 본 모든 lead를 대상으로 한 lead 중복 제거, 확장 wave, excursion 방아쇠, 예산, 종료 규칙, 되돌림 기록 한 줄, 사용자 조향 전달을 `ulw-research` 스킬에서 각색했습니다 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| 중지 조건에는 숫자 상한이 따릅니다. 예산 소진은 완료가 아니라 `exhausted`입니다. 진전이 없으면 중지합니다. 소진 보고에는 닿은 상한, 남은 거리, 마지막 판정, 재개 상태를 담습니다 | `instructions/loop-engineering/LOOP_ENGINEERING.md`, `instructions/loop-engineering/references/stop-conditions-and-verification.md` |
| 새 정보 없이 비슷한 결과가 세 번 반복되면 중지합니다 | `instructions/sourcing/reliable-search.md` |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지 자체의 loop를 서술합니다. 업스트림 스킬은 wave 상한 없이 확장을 돌립니다. 이 패키지는 수렴 규칙을 유지하고 저장소 loop 규칙이 요구하는 상한을 더합니다.
