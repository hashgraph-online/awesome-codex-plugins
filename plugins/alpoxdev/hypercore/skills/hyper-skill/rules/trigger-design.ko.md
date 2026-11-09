# 트리거 설계

**Purpose**: 스킬이 올바른 요청에서 발동하고, 틀린 요청에서는 비켜나게 만듭니다.

트리거 동작은 확률적입니다. 이 파일의 어떤 규칙도 문장 하나를 읽어서 증명되지 않으므로, 아래 모든
규칙은 단정이 아니라 점검 가능한 형태로 씁니다.

## 1. 설명 규칙

`description`은 다음을 설명해야 합니다.

- 스킬이 무엇을 하는지
- 언제 쓰여야 하는지
- 모호할 때 어느 이웃 요청을 소유하지 않는지

약한 예:

```yaml
description: Helps with skills.
```

나은 예:

```yaml
description: Use this skill when the user asks to create or refactor a reusable Codex skill folder, including SKILL.md trigger wording, rules, references, scripts, assets, and validation checks. Do not use for generic documentation that is not a skill.
```

설명은 **3인칭**으로 씁니다. 이 필드는 시스템 프롬프트에 주입되며, 인칭이 흔들리는 설명("I can help
you…", "You can use this to…")은 발견에 문제를 만듭니다. 위 예시처럼 명령형 `Use this skill when…`
형태를 선호합니다. 이미 3인칭이고 결과를 앞세웁니다.

## 2. 작성 패턴

- 런타임이 산문 설명을 받으면 `Use this skill when...`으로 시작합니다.
- 사용자 의도와 결과를 내부 구현 세부보다 앞에 둡니다.
- 가장 중요한 트리거 용어를 **첫 문장**에 둡니다. 검토한 모든 런타임이 긴 설명의 뒷부분을 줄이거나
  버릴 수 있으므로(§6), 트리거가 마지막 절에 기대면 안 됩니다.
- 가까운 이웃이 있으면 짧은 부정 경계를 넣습니다. 언제 발동하는지만 말하는 설명은 선택자에게 되돌아갈
  길을 주지 않습니다.
- 모든 메타 스킬과 겹칠 만큼 넓은 설명은 피합니다.

## 3. 두 축

트리거 예시는 **서로 직교하는 두 축**으로 만듭니다. 두 축은 서로를 대체하지 않으며, 둘을 교차해야만
실제 실패를 잡습니다.

| 축 | 값 | 검증하는 것 |
|---|---|---|
| 활성화 | positive / negative / boundary | 설명이 올바른 요청에만 반응하는가 |
| 호출 방식 | explicit / implicit / contextual / negative control | 이름 없이도 맞는가, 그리고 오발동하지 않는가 |

| 호출 방식 | 의미 | 예 |
|---|---|---|
| explicit | 스킬 이름을 직접 부릅니다 | `Use $hyper-skill to build a skill` |
| implicit | 이름 없이 자연어로 설명과 맞습니다 | `Create a reusable skill folder for me` |
| contextual | 도메인 맥락이 섞인 실제 업무 문장입니다 | `Make this migration review procedure run identically every time` |
| negative control | 발동하면 안 되는 비슷한 요청입니다 | `Clean up this runbook so it reads better` |

## 4. 트리거 케이스 형태

트리거 케이스는 불리언이 아닙니다. 케이스마다 자기 실행 횟수와 임계값을 갖고, 실행은 그 결과 비율을
기록합니다.

```json
[
  { "id": "p1", "prompt": "Create a Codex skill for SQL migration review", "expect": "trigger", "runs": 3, "threshold": 0.5 },
  { "id": "p2", "prompt": "Refactor this SKILL.md so it loads references correctly", "expect": "trigger", "runs": 3, "threshold": 0.5 },
  { "id": "p3", "prompt": "스킬 폴더를 새로 만들고 검증 규칙까지 넣어줘", "expect": "trigger", "runs": 3, "threshold": 0.5 },
  { "id": "n1", "prompt": "Rewrite this runbook for readability", "expect": "no_trigger", "runs": 3, "threshold": 0.5 },
  { "id": "n2", "prompt": "Summarize these OpenAI docs", "expect": "no_trigger", "runs": 3, "threshold": 0.5 },
  { "id": "b1", "prompt": "Create a guide for writing skills", "expect": "no_trigger", "runs": 3, "threshold": 0.5, "note": "depends on output shape" }
]
```

실행은 케이스마다 측정된 `trigger_rate`를 덧붙이므로, 결과 파일은 같은 키에 결과를 더해 갖습니다.

```json
{ "id": "p1", "expect": "trigger", "runs": 3, "threshold": 0.5, "trigger_rate": 1.0 }
```

규칙:

- **모든 케이스가 자기 `runs`와 `threshold`를 밝힙니다.** 기본값을 상속하게 두지 않습니다. `runs`가
  비율의 의미를 바꾸므로 값이 쓰이는 자리에서 보여야 합니다.
- `3`회 실행과 `0.5` 임계값은 표준이 권하는 **시작점**이며 검증된 최적값이 아닙니다. 관측된 퍼짐이
  너무 넓어 케이스를 임계값과 구분할 수 없으면 `runs`를 올립니다.
- 목표 크기에 맞추려고 케이스를 채우지 않습니다. 새로 탐침하는 것이 없는 케이스는 증거가 아니라
  호출만 늘립니다. 기존 행이 탐침하지 않는 것을 탐침할 때만 행을 더하고, 실제 실패는 그때마다 행으로
  승격합니다.
- 이것은 `stochastic-model` 측정입니다. 결과와 함께 모델·런타임 식별자와 실행 횟수를 기록하고, 고정
  시드만으로는 분산을 추정하지 못한다는 점을 적습니다.

## 5. 설명 최적화

설명을 한 번 쓰는 것으로 끝나지 않습니다. 반복 편집은 조정에 쓴 예시에 과적합됩니다. 다음 규칙은
규범입니다.

- SK-O-1: 질의 집합을 **훈련과 검증**으로 나눕니다. 훈련으로 개선하고 **검증** 통과율로 선택합니다.
- SK-O-2: **가장 좋은 설명이 마지막 설명이 아닐 수 있습니다.** 나중 반복이 검증에서 더 낮으면 이전 반복을 유지합니다.
- SK-O-3: 설명은 최적화하는 동안 길어집니다. 편집할 때마다 **1024자 한도**를 다시 확인합니다.
- SK-O-4: 미세 조정이 도움이 되지 않으면 형용사를 더하지 말고 **구조를 바꿉니다**. 다른 프레이밍이나 다른 문장 형태입니다.

최종 검증 점수만 보고하는 실행은 개선의 증거가 아닙니다. 선택이 드러나도록 반복마다 훈련과 검증
수치를 보고합니다.

출처는 검증된 최적값이 아니라 권고로 실무 한계를 덧붙입니다. 질의 약 20개(트리거해야 할 것 8-10개,
트리거하지 말아야 할 것 8-10개), 반복 사이에 고정하는 대략 60/40 훈련·검증 분할, 편집에 되먹이는
것은 훈련 실패만, 반복 약 다섯 번, 그다음 새 질의 5-10개로 재시험입니다. 근접 오답 질의가 가장 값진
부정 사례입니다.

## 6. 설명 예산

설명은 고정된 목록 예산을 두고 경쟁하며, 검토한 각 런타임은 그것을 다르게 재고 자릅니다.

| 런타임 | 구속하는 한도 | 넘칠 때 일어나는 일 |
|---|---|---|
| Agent Skills 명세 | `description` 1-1024자 | 정의되지 않습니다. 이 필드는 검증 대상이며 잘라 내지 않습니다 |
| Codex | 최초 목록은 컨텍스트 창의 2%, 창을 알 수 없으면 8,000자. `skills.max_context_tokens`로 최대 10,000토큰까지 올립니다 | **먼저 설명을 줄이고**, 스킬 집합이 크면 일부 스킬을 **최초 목록에서 아예 빼며** 경고를 냅니다 |
| Claude Code | 컨텍스트 창의 1%, 각 항목의 `description` + `when_to_use`는 **1,536자**에서 잘림 | 설명을 **가장 적게 호출한** 스킬부터 떨어뜨리며, 이름은 모두 남습니다 |
| Claude API | 요청당 스킬 최대 20개 | 스킬을 통합하거나 요청을 다른 스킬 집합으로 라우팅합니다 |

결과:

- 1,024자 명세 한도와 1,536자 Claude Code 목록 자르기는 다른 한도입니다. 설명은 스킬을 설치할 모든
  런타임 중 가장 빡빡한 한도에 맞춥니다.
- 핵심 트리거를 앞에 둡니다. 구별해 주는 단어가 끝에 있으면 요청과 대조되기 전에 잃을 수 있습니다.
- Codex의 실패 양상은 잘림만이 아닙니다. 최초 목록에 나타나지 않는 스킬은 후보가 아니므로, 단지 긴
  설명은 실제 가용성 위험입니다.
- 두 런타임 모두 잘린 설명을 오류로 보고하지 않습니다. 키워드를 잃은 스킬은 애초에 맞지 않은 스킬과
  똑같이 보입니다.
- **이 저장소는 컨텍스트 창을 알 수 없을 때 이미 Codex 예산을 넘겼습니다.** Sources 아래의 측정을
  보십시오. 긴 설명에는 이유가 필요합니다.

## 6a. 수동 전용 스킬

자동 발동이 사용자가 의도하지 않은 피해를 낼 수 있는 스킬, 즉 배포, 게시, 삭제, 전송은 수동으로
표시해 명시적 호출로만 실행되게 합니다. Claude Code에서는 `disable-model-invocation: true`, Codex
`agents/openai.yaml`에서는 `policy.allow_implicit_invocation: false`입니다. 둘 다 런타임 전용
스위치이므로(`rules/skill-anatomy.md`, SK-P-3) 각 스위치 옆에 런타임 이름을 적고, 스킬 자체 계약에도
부작용 게이트를 둡니다. 스위치를 무시하는 런타임은 그래도 스킬을 자동 선택하기 때문입니다.

## 7. 공존

스킬은 홀로 발동하지 않습니다. 하나를 더하면 다른 스킬의 요청을 가져가며 그것을 나쁘게 만들 수
있습니다.

- **공존은 부차적 항목이 아니라 평가 차원입니다.** 질문은 이것입니다. 이 스킬을 더하면 기존 스킬이
  나빠지는가? 지목된 실패는 새 설명이 넓어 기존 스킬의 **트리거를 가로채는** 것입니다.
- 근접 오답 케이스로 측정합니다. 새 스킬의 동사와 명사를 공유하지만 이웃에게 속하는 요청입니다.
  설명이 너무 넓을 때 실패하는 케이스이며, 평범한 부정 예시로는 잡지 못하는 케이스입니다.

이 저장소의 측정된 겹침은 Sources에 기록합니다. `refactor` 토큰을 이 스킬과 형제 산출물 작성 스킬
여러 개가 공유하므로, 공존 케이스는 재사용 가능한 *스킬 폴더*를 재사용 가능한 *프롬프트*, *문서*,
*지침 파일*과 구분해야 합니다. 측정은 개수만 적고 이웃 이름은 적지 않습니다. 규칙 파일이 이웃 이름을
적으면 그 파일만으로 쓸 수 없게 됩니다(`rules/self-containment.md`, SK-S-2).

## 8. 범위 경계

스킬이 소유하지 않는 것을 밝힙니다. 모든 경계는 그 산출물을 소유한 스킬의 이름이 아니라 산출물의
형태로 서술합니다(`rules/self-containment.md`, SK-S-2).

예:

- 산출물이 스킬 폴더이거나 스킬 리팩터링이면 이 스킬이 소유합니다
- 일반 문서, 런북, 가이드는 범위 밖입니다
- 재사용 가능한 프롬프트 산출물은 범위 밖입니다
- 출처 기반 사실 확인은 범위 밖입니다
- 구현 전 계획은 범위 밖입니다
- 커밋 생성은 범위 밖입니다

## 9. 안티패턴

- 모호한 설명
- 직업이 아니라 도구만 나열하는 설명
- 트리거 시점이 아니라 직업만 나열하는 설명
- 트리거하면 안 되는 예시가 없음
- 이웃 스킬과 겹칠 만큼 넓은 설명
- `runs`나 `threshold`를 밝히지 않고 상속하는 트리거 케이스
- 최종 검증 점수만 보고해 반복 사이의 선택이 보이지 않게 하는 것
- 길이 한도를 다시 확인하지 않고 설명을 키우는 것
- 근접 오답 케이스가 없어 트리거 가로채기를 한 번도 측정하지 않는 것
- 배포, 게시, 삭제 스킬을 수동 전용 스위치와 계약 게이트 없이 자동 발동에 열어 두는 것

## Sources

> 확인 2026-11-03.

| 주장 | 출처 |
|---|---|
| 네 가지 호출 방식(explicit, implicit, contextual, negative control), 10-20개 프롬프트 시작 집합, 네 가지 평가 축 | <https://developers.openai.com/blog/eval-skills> |
| 지표로서의 트리거 비율, 3회 실행, 0.5 기본 임계값, 훈련·검증 분할, "가장 좋은 것이 마지막이 아닐 수 있음", 1024자 재확인, `SK-O-1`부터 `SK-O-4`의 구조 변경 대안, 약 20개 질의·다섯 반복·새 질의 5-10개 한계, 가장 값진 부정 사례로서의 근접 오답 | <https://agentskills.io/skill-creation/optimizing-descriptions> |
| `description`의 1024자 한도, `name`이 부모 디렉터리와 일치해야 함 | <https://agentskills.io/specification> |
| Codex의 2%·8,000자 목록 예산, 최대 10,000토큰까지의 `skills.max_context_tokens`, 먼저 줄이고 이후 생략, 생략 경고, `allow_implicit_invocation` | <https://learn.chatgpt.com/docs/build-skills> |
| Claude Code의 1% 목록 예산, 항목당 1,536자 한도, 적게 호출한 순서로 떨어짐, `disable-model-invocation` | <https://code.claude.com/docs/en/skills> |
| 평가 차원으로서의 공존, 트리거 가로채기 실패, 요청당 20개 스킬이라는 API 한도 | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise> |
| 측정된 비율에 대한 `stochastic-model` 측정 계약 | `instructions/autoresearch/references/config-and-metrics.md` §2 |
| 저장소 측정, 2026-11-09: `description` 필드 합계가 15,932자인 스킬 26개(8,000자 대체 한도 초과). `refactor`가 설명 4개에, `create`가 3개에 나타남 | 이 저장소 |

### 증거 등급

최적화 규칙은 `PRIMARY`입니다. 명세 사이트가 직접 말합니다. 10-20개 프롬프트 수치와 약 20개 질의
한계는 출처가 권하는 시작점이며 검증된 최적값이 아니므로, 이 파일은 그 이유로 필수 케이스 개수를 두지
않습니다. 목록 동작은 `VENDOR`입니다. 각 런타임이 자기 자르기를 설명하며 서로 다릅니다. 저장소 수치는
이 저장소를 측정한 값이며, 갱신할 때 위의 규칙 본문을 건드리지 않도록 여기 맨 아래에 둡니다.
