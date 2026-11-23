# 런타임 호출 메타데이터 (`hyper-interview`)

`hyper-interview`는 사용자가 직접 호출할 때만 시작하는 요구사항 인터뷰 스킬입니다. 에이전트 호스트마다 수동 전용 스위치를 읽는 메타데이터 위치가 다르므로, `SKILL.md`의 `<routing_rule>`을 실제 판정 기준으로 두고 호스트별 힌트는 선택 메타데이터로만 함께 둡니다.

| 호스트 / 런타임 | 선택 메타데이터 위치 | 동작 |
|---|---|---|
| Codex | `agents/openai.yaml` (`policy.allow_implicit_invocation: false`) | 모델의 암묵적 자동 호출을 막고 사용자의 명시적 호출만 허용합니다(`추정` / 공식 문서 기준). |
| Claude Code / `omp` | `SKILL.md` 머리말 `disable-model-invocation: true` | 지원 호스트에서 수동 전용 스킬로 표시해 모호한 구현 요청이 인터뷰로 자동 진입하지 않게 합니다(`추정` / 공식 문서 기준). |
| Antigravity (`agy`) 및 기타 호스트 | 알 수 없는 선택 필드로 무시 | `SKILL.md`의 `<routing_rule>`이 그대로 작동하여 현재 턴에 이름 호출이 없으면 인터뷰를 시작하지 않습니다. |

머리말 스위치 하나에 계약을 맡기지 않습니다. 호스트가 `disable-model-invocation`이나 `agents/openai.yaml`을 읽지 않아도 `<routing_rule>`이 명시적 호출 없는 인터뷰 시작을 막습니다.

## Sources

> 확인 2026-11-21.

| 주장 | 출처 |
|---|---|
| `agents/openai.yaml`의 `allow_implicit_invocation` 정책 | <https://learn.chatgpt.com/docs/build-skills> |
| `disable-model-invocation` 머리말 플래그 | <https://code.claude.com/docs/en/skills.md>, <https://raw.githubusercontent.com/can1357/oh-my-pi/HEAD/docs/skills.md> |
| 런타임 전용 머리말 필드는 계약의 필수 하중을 지지 않음(`SK-P-3`) | `instructions/skill/SKILL_AUTHORING.md` |
