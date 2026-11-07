# 모드와 라우팅

**목적**: 요청이 받으려는 산출물의 모양을 보고 알맞은 모드를 고르고, 그 요청이 애초에 Jev에 맞는 일인지 판정하고, 요청이 비워 둔 자리를 기본값으로 채웁니다.

모든 요청은 세 가지를 이 순서로 정합니다. 어느 모드인가, Jev가 맞는 도구인가, 요청이 말하지 않은 값은 무엇으로 두는가. 모드는 사용자가 쓴 낱말이 아니라 사용자가 받으려는 산출물에서 읽습니다. "분류"라고 썼어도 파이썬 파일을 달라고 하면 코드 모드입니다.

## 1. 모드 판별

사용자가 열어 볼 산출물을 기준으로 아래 표에서 한 줄을 고릅니다. 두 줄이 비슷해 보이면 사용자가 먼저 읽을 산출물 쪽을 택합니다.

| 모드 | 영어 신호 | 한국어 신호 | 산출물 |
|---|---|---|---|
| `design` | "should this use Jev", "is this a judgment problem", "Jev or code", "decision contract", "how should I split this" | "Jev로 하는 게 맞나", "판단 문제인가", "결정 계약", "어떻게 나눌까" | 적합성 판정과 결정 계약. 각 부분이 무엇을 판단하는지, 누가 그 판단을 소유하는지, 검토가 어디에 붙는지까지 적습니다 |
| `questions` | "write the questions", "question set", "criteria", "options", "scale" | "질문 만들어", "질문 묶음", "선택지", "기준", "점수 단계" | 요청에 그대로 붙여 넣을 수 있는 질문 묶음 |
| `code` | "call it from", "integration code", "client", "wire this into", "TypeScript", "Python" | "호출 코드", "연결 코드", "클라이언트", "연동" | 경로 하나와 언어 하나에 맞춘 호출 코드 |
| `template` | "request json", "constants file", "routing table", "starter", "skeleton" | "요청 JSON", "상수 파일", "라우팅 표", "템플릿", "뼈대" | 요청 JSON, 상수 파일, 라우팅 표 |
| `eval` | "evaluate", "test set", "labels", "thresholds", "how accurate", "before we ship" | "평가", "라벨", "임계값", "정확도", "검증 세트" | 평가 계획, 케이스 뼈대, 임계값 조정 계획 |
| `audit` | "audit", "find the LLM calls", "what should we replace", "where do we waste calls" | "감사", "LLM 호출 찾아", "교체 대상", "어디서 낭비하나" | 기존 호출을 훑은 순위표. 읽기 전용입니다 |
| `provider` | "which provider", "which route", "connect it", "setup", "environment" | "어느 경로", "어디로 연결", "설정", "환경 변수" | 경로 선택과 설정 안내 |

한 요청이 두 줄에 걸치기도 합니다. "설계해 주고 코드도 줘" 같은 경우입니다. 그때는 사용자가 먼저 읽을 산출물 순서로 실행하고, 어느 모드를 돌렸는지 밝힙니다.

## 2. 적합성 관문

모드를 실행하기 전에 이 관문을 먼저 통과시킵니다. 질문은 다섯 개이고, 순서대로 답합니다.

1. 정답이 닫힌 선택지 가운데 하나이거나, 순서가 있는 눈금 위의 한 점이거나, 예/아니오 판정인가?
2. 모델 없이 정확한 코드만으로 같은 답을 낼 수 있는가?
3. 결과물이 새로 쓴 글이거나 새로 쓴 코드여야 하는가?
4. 답이 산술, 개수 세기, 숫자를 다루는 여러 단계 추론에 달려 있는가?
5. 입력이 이미지나 소리, 또는 코드가 곧바로 읽을 수 있는 데이터베이스 행이 아니라 텍스트인가?

그다음 판정을 읽습니다.

표는 위에서 아래로 읽고 처음 맞는 줄을 택합니다. 1번이 아니오라는 것은 정답이 닫힌 집합도, 눈금도, 예/아니오도 아니라는 뜻입니다. 그러면 그것을 정하는 질문에 따라 `llm`(3번 예)이나 `code`(2번 예)으로 보고, 둘 다 아니면 이 요청은 Jev 판단이 아니라고 말하고 평범한 대안을 제시합니다.

| 판정 | 해당하는 경우 | 할 일 |
|---|---|---|
| `jev` | 1번 예, 2번 아니오, 3번 아니오, 4번 아니오, 5번 예 | 모드를 실행합니다. 질문 묶음이나 호출 코드를 만들고, 대비 선택지를 밝히고, 신뢰도가 낮은 구간에 사람 검토 경로를 붙입니다. |
| `decompose` | 4번 예이면서, 그 요청 안에 1번을 통과하고 2번 아니오, 3번 아니오, 5번 예인 판단 부분이 함께 있음 | 일을 쪼갠 설계를 냅니다. 산술과 정책은 코드가 맡고 판단은 Jev가 맡으며, 두 몫을 이 관문으로 다시 확인합니다. |
| `code` | 2번 예, 또는 4번 예, 또는 5번 아니오 | 멈춥니다. 코드가 정확하고 오프라인에서 돌고 시험할 수 있다는 이유를 말하고, Jev 산출물은 만들지 않습니다. 대신 평범한 코드 경로를 제안합니다. |
| `llm` | 3번 예 | 멈춥니다. 결과물이 생성된 글이나 생성된 코드인데, 판단 모델은 주어진 선택지에서 고를 뿐 쓰지는 않습니다. 이미 그 일을 하는 모델을 그대로 둡니다. |
| `hybrid` | 판단하는 부분과 생성하는 부분이 한 요청에 섞여 있음. 판단과 생성이 섞인 요청이면 `llm`보다 먼저 봅니다 | Jev 산출물은 아직 만들지 않습니다. 먼저 나눕니다. 어느 문장이 Jev로 가고 어느 문장이 언어 모델로 가는지 밝힌 뒤, Jev 몫만 실행합니다. |

판정 예시입니다.

| 요청 | 판정 | 이유 |
|---|---|---|
| "compute the difference between two dates" | `code` | 날짜 계산은 정답이 하나입니다. 날짜 라이브러리가 정확히 맞히고, 판단 모델은 날짜에 약하다고 문서에 적혀 있습니다. |
| "write a reply email" | `llm` | 결과물이 새로 쓴 글입니다. 판단 모델은 주어진 선택지에서 고르고 쓰지는 않습니다. |
| "classify these tickets into 5 queues" | `jev` | 다섯 개 대기열은 닫힌 집합이고, 티켓은 텍스트이며, 하는 일은 티켓마다 하나를 고르는 것입니다. |
| "score these leads 1 to 10 on fit" | `jev` | 단계 수가 정해진 순서 눈금을 텍스트 입력에 적용합니다. |
| "decide whether this clause is risky and rewrite it if it is" | `hybrid` | 위험 여부는 텍스트에 대한 예/아니오 판단이고, 고쳐 쓰는 일은 생성입니다. |
| "work out the refund amount and decide whether it needs approval" | `decompose` | 규칙에서 환불액을 계산하는 일은 코드가 하고, 승인 여부를 판단하는 일은 Jev가 합니다. |
| "summarize this document" | `llm` | 요약은 아직 없는 글을 만들어 냅니다. |

판정이 `jev`가 아니면 그 사실을 분명히 말하고 대안을 함께 냅니다. 틀릴 Jev 산출물로 얼버무리지 않습니다.

관문은 요청이 Jev에 판단을 맡기려는 결정에 돌립니다. `audit`에서는 후보 호출마다 한 번씩, 그 호출을 목록에 올리기 전에 돌립니다. `provider`와, 산출물이 판단이 아니라 동작인 요청(예: "이 키를 코드에 넣고 실행해줘")은 Jev 산출물을 만들지 않으므로 관문이 적용되지 않고, 실행을 이어갈지 멈출지는 안전 규칙이 정합니다. 관문 판정에 이르기 전에 안전 규칙이나 빠진 권한에서 실행이 끝나는 경우도 있습니다.

## 3. 필수 입력 기본값

무엇을 묻기 전에 저장소에서 먼저 채웁니다.

- **언어.** `package.json`이 있고 `pyproject.toml`이 없으면 TypeScript입니다. `pyproject.toml`이 있으면 Python입니다. 둘 다 없거나 둘 다 있으면 TypeScript입니다. 무엇을 골랐는지 한 줄로 밝힙니다.
- **경로.** [`../references/providers.md`](../references/providers.md)의 선택 순서를 그대로 따라 위에서 아래로 내려갑니다. 참조에 없는 경로를 지어내지 않습니다.
- **모델과 계약 세부.** [`../references/official/jev-platform.md`](../references/official/jev-platform.md)에서 읽습니다. 고정된 값인 것처럼 산출물 안에 다시 적지 않습니다.
- **모호할 때.** 가장 가까운 모드로 진행하면서 빠진 사실 하나만 묻습니다. 묻기 쉬운 것이 아니라 답에 따라 산출물이 달라지는 사실을 고릅니다. 질문을 여러 개 늘어놓고 일을 시작하지 않습니다.

## 4. 산출물 위치

사용자가 경로를 지정했으면 그곳에 씁니다. 지정하지 않았으면 `.hyper/jev-maker/<주제>/` 아래에 씁니다. `<주제>`는 요청에서 뽑은 짧은 이름입니다.

```text
.hyper/jev-maker/<topic>/
├── request.json
├── constants.ts
└── eval-cases.jsonl
```

이미 있는 파일은 확인 없이 덮어쓰지 않습니다. 먼저 읽고, 옆 파일로 쓰거나 바꿔도 되는지 물은 뒤에 씁니다. 쓴 파일은 경로를 모두 보고합니다.

## Sources

> Links checked 2026-10-01.

| Claim | Source |
|---|---|
| The mode set, the mode signals, the one-missing-fact rule, and the fit-gate questions | user instruction, 2026-10-01 |
| Jev's documented limits on dates, counting, arithmetic, and text generation, which drive the `code`, `llm`, and `decompose` verdicts | `../references/official/jev-platform.md` |
| The language defaults, the route order, and what each route reads | `../references/providers.md` |
| The output path default and the no-overwrite rule | repository policy |

### Evidence grade

`LOCAL`: 라우팅 규칙은 저장소 정책과 사용자 지시입니다. `VENDOR`: Jev의 문서화된 한계는 링크한 스냅샷이 담고 있고, 이 파일에 옮겨 적지 않았습니다.
