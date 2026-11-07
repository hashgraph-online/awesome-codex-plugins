# Jev 플랫폼 스냅샷

벤더 문서가 말하는 Jev 플랫폼의 모습을 한 파일에 모았습니다. HTTP 엔드포인트, 질문과 응답의
형태, 이 파일을 쓴 시점의 한도와 가격, 현재 버전에서 알려진 거친 부분, 그리고 이 스냅샷이 다루는
세 경로를 담습니다. Sources에 적은 문서를 2026-10-01에 직접 읽고 옮겼습니다. 가격, 한도,
모델 별칭, 경로 계약은 이 스킬에서 이 파일에만 둡니다.

## Contents

- 갱신 정책
- 평가 엔드포인트
- 모델, 별칭, 한도, 가격
- 질문 유형
- 응답 유형과 신뢰도
- jev-1.13의 거친 부분
- 공식 에이전트 스킬
- Vercel AI SDK와 AI Gateway
- b.ai Decisions API
- Sources

## 갱신 정책

- last_verified_at: 2026-10-01
- refresh_when:
  - 벤더 문서가 요청 한도, 가격, 모델 별칭을 바꿀 때
  - 경로가 엔드포인트를 추가하거나 없앨 때
  - 질문이나 응답의 형태(`noul`, `choice`, `score`, `boolean`)가 바뀔 때
  - 현재 Jev 버전의 거친 부분 목록이 바뀔 때
- supports_rules:
  - `rules/modes-and-routing.md`
  - `rules/safety-and-boundaries.md`

이 스냅샷이 30일보다 낡았고 네트워크가 살아 있으면 벤더 문서를 읽기 전용으로 다시 읽고 여기
날짜를 고칩니다. 네트워크가 없으면 값을 짐작하지 말고 스냅샷 날짜를 그대로 밝힙니다.

## 평가 엔드포인트

- source_url: https://docs.typesafe.ai/api
- last_verified_at: 2026-10-01
- applies_to: 직접 HTTP 경로, 요청과 응답의 형태, 오류 코드
- volatility: stable
- summary: 엔드포인트 하나가 공유 `state`를 타입이 붙은 질문 묶음으로 평가하고 질문
  아이디마다 구조화된 답 하나를 돌려줍니다. 세 질문 유형이 모두 같은 주소로 가고, 본문의
  `model` 필드가 답할 버전을 고릅니다.

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer plus your key
Content-Type: application/json
```

요청 본문은 다음과 같습니다.

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `state` | 문자열, 객체, 배열 | 평가할 내용입니다. 대화 기록, 레코드, 또는 애플리케이션의 현재 상태를 넣습니다. |
| `model` | 문자열 | `"jev-latest"`가 대표 별칭입니다. 아래 별칭 표를 보십시오. |
| `questions` | 아이디에서 질문으로 가는 맵 | 직접 이름 붙이는 맵입니다. 답은 같은 아이디로 돌아옵니다. 벤더는 이 아이디가 "is not sent to the underlying model and is not used in inference"라고 적습니다(api, 2026-10-01). b.ai 문서는 이 맵이 비어 있으면 안 되고 아이디가 비었거나 공백뿐이어도 안 된다고 덧붙입니다. |

질문마다 `type`과 `instructions`가 있습니다. `instructions`는 문자열, 객체, 배열을 받으므로,
참고 자료가 붙은 긴 질문은 질문 필드와 자료 필드로 나눈 뒤 백틱으로 이름을 가리켜 쓸 수
있습니다. `criteria`는 문자열 하나로는 쓸 수 없습니다. `noul` 질문에서는 객체, `choice` 질문에서는
선택지에서 설명으로 가는 맵, `score` 질문에서는 순서가 있는 배열입니다.

응답 본문은 `model`(답한 버전 아이디), `answers`(질문 아이디별 답 하나), `usage`
(`input_tokens`와 `output_tokens`)입니다.

키가 없거나 틀리면 `401`, 본문이 검증을 통과하지 못하면 `422`와 함께 어긋난 필드를 알려줍니다.
한도를 넘으면 `429`, 서비스가 몰리면 `529`입니다. 뒤의 두 경우 벤더는 "back off and
retry after a short delay"라고 안내합니다(api, 2026-10-01). 클라이언트 SDK는 이 재시도를
기본으로 합니다.

Python SDK와 JavaScript SDK가 이 엔드포인트를 감쌉니다. JavaScript SDK 문서에는
`TypeSafeClient` 클래스, `client.systemOne`, `TYPESAFE_API_KEY` 환경변수, `choice()` 도우미가
나옵니다. 나머지 질문 유형의 도우미는 그 문서에 없으므로, 쓰기 전에 그 패키지의 타입 참조를
읽으십시오.

## 모델, 별칭, 한도, 가격

- source_url: https://docs.typesafe.ai/models
- last_verified_at: 2026-10-01
- applies_to: 모델 아이디와 별칭, 요청 한도, 컨텍스트 길이, 입력 형식, 언어 지원, 가격
- volatility: volatile
- summary: `jev-1.13.0`이 현재 버전 아이디입니다. 별칭 둘이 이 버전을 가리키고, 지금은 둘 다
  같은 빌드입니다. 요금은 입력 토큰에만 붙고 출력 토큰은 무료입니다. 요청 한도는 움직이며,
  벤더도 문서에 그렇게 적습니다.

| 항목 | 2026-10-01 기준 값 |
| --- | --- |
| 버전 아이디 | `jev-1.13.0` |
| `jev-latest` | `jev-1.13.0`으로 해석됩니다(클라이언트 SDK의 기본값) |
| `jev-preview` | 마찬가지로 `jev-1.13.0`을 가리킵니다. 지금은 프리뷰 빌드가 없습니다 |
| 가격 | Btok당 42달러, 또는 입력 100만 토큰당 0.042달러. 출력 토큰은 무료입니다 |
| 요청 한도 | 초당 100K 토큰, 초당 40요청 |
| 컨텍스트 | 요청당 64k 토큰. `state`와 가장 긴 질문 하나를 합쳐 32k |
| 입력 | 텍스트만 받습니다. 문자열, JSON 객체, 또는 텍스트 값의 배열입니다. 이미지, 오디오, 동영상은 없습니다 |

문서에는 한도가 "adjusting dynamically"이며 "can change without notice"라는 경고가 붙어
있습니다(models, 2026-10-01). 두 한도 중 하나를 넘으면 `429`가 돌아옵니다. state를 한 번만
읽고 질문을 병렬로 평가하므로, 한 요청에 질문을 여러 개 넣을 수 있습니다.

별칭은 새 릴리스가 나오면 옮겨가므로, 호출하는 쪽이 그대로여도 `jev-latest` 뒤의 답이 달라질
수 있습니다. 응답의 `model` 필드가 답한 버전을 알려줍니다. 신뢰도 임계값을 특정 버전에 맞춰
조정했다면 별칭 대신 그 버전 아이디를 고정하고 원하는 시점에 옮기십시오.

언어 지원은 영어가 훈련의 중심이고 정확도도 가장 높습니다. 다른 언어, 그중에서도 CJK 문자는
처리되지만 같은 수준은 아닙니다. 영어가 아닌 작업에 Jev를 쓰기 전에 자기 자료로 시험해 보고,
경로를 나눌 때 신뢰도를 가까이 보십시오.

`GET /v1/models`는 계정이 보낼 수 있는 이름을 설명과 출시일과 함께 돌려줍니다.

## 질문 유형

- source_url: https://docs.typesafe.ai/api
- last_verified_at: 2026-10-01
- applies_to: 세 질문 유형, 각 유형의 criteria 규칙, 각 유형의 답
- volatility: stable
- summary: 질문은 세 유형 중 하나입니다. 셋 모두 `type`과 `instructions`를 공유하고, 각자
  자기 `criteria` 규칙을 더합니다.

| 유형 | criteria | 답 |
| --- | --- | --- |
| `noul` | 선택입니다. `true`와 `false` 속성을 가진 객체이며, b.ai 경로에서는 이 두 키만 허용하고 값은 문자열, 객체, 배열이라고 덧붙입니다 | `noul`. 0(아니오)에서 1(예) 사이의 수입니다 |
| `choice` | 필수 맵입니다. 선택지에서 설명으로 갑니다. 선택지는 최대 255개이고, 따로 설명할 것이 없으면 `null`을 씁니다 | `choice`(확률이 가장 높은 선택지), 모든 선택지의 `probabilities`, `confidence` |
| `score` | 필수 배열입니다. 순서가 있는 단계 설명이 들어갑니다. 단계는 최소 둘, API는 열까지 받습니다. 항목은 문자열, 객체, 배열이고 `null`은 안 됩니다 | `score`(확률로 가중한 값이라 단계 사이에 놓일 수 있습니다), `legend`, `probabilities`, `confidence` |

`noul`은 "예"일 확률로 설명되며 정도 점수가 아닙니다. 0.5 근처는 불확실을 뜻합니다. `score`는
확률로 가중한 평균이라 단계가 셋이면 1.05처럼 돌아올 수 있고, `legend`가 단계 번호를 설명으로
되돌려 줍니다.

## 응답 유형과 신뢰도

- source_url: https://docs.typesafe.ai/confidence
- last_verified_at: 2026-10-01
- applies_to: 확신을 보고하는 방식과 그것으로 동작을 가르는 방법
- volatility: stable
- summary: Choice와 Score의 답에는 확률 분포의 모양에서 뽑은 0에서 1 사이의 `confidence`가
  붙습니다. 분포가 한쪽에 몰리면 값이 높고, 고르게 퍼지면 낮습니다. Noul 답에는 별도 신뢰도
  필드가 없습니다.

문서는 "a confidence threshold is not one number"라고 분명히 적습니다(confidence, 2026-10-01).
한 시스템 안에서도 동작마다 틀렸을 때의 대가가 다르므로 문턱을 다르게 잡아야 합니다. 벤더
예시는 0.5 아래를 사람에게 넘기고, 되돌릴 수 있는 동작은 그냥 실행하며, 되돌리기 어려운
동작에는 더 높은 문턱을 둡니다.

여기서 함께 가져갈 두 가지 주의가 있습니다. 형식이 맞는 것은 정답이 아닙니다. 형태를 갖춘
답도 틀릴 수 있으므로 임계값은 대표성 있는 라벨 데이터 위에서 정합니다. 그리고 `confidence`는
선택된 선택지의 확률이 아닙니다. 다른 통계량이 필요하면 날 확률 분포가 `probabilities`에
있습니다.

## jev-1.13의 거친 부분

- source_url: https://docs.typesafe.ai/model-jaggedness/jev-1.13
- last_verified_at: 2026-10-01
- applies_to: `jev-1.13`의 알려진 실패 유형과 벤더가 권하는 우회법
- volatility: volatile
- summary: 문서가 실패 유형 아홉 가지를 싣고 "Jev isn't perfect"로 시작합니다(jaggedness,
  2026-10-01). `jev-1.13`에 해당하며, 벤더가 직접 밝힌 검토일은 2026-09-17입니다.

| 번호 | 실패 유형 | 대신 할 일 |
| --- | --- | --- |
| 1 | 문자 그대로 읽기. 적힌 말을 따르고 의도는 읽지 않습니다 | 조건을 정확히 쓰고, 경계 사례는 criteria에 넣습니다 |
| 2 | 수와 계산. 세기, 산술, 숫자 표현이 믿기지 않습니다 | 계산은 코드에 두고, 16진수나 이진 값 대신 이름을 씁니다 |
| 3 | 날짜와 시간 비교. 날짜를 순서가 있는 값이 아니라 글자로 읽습니다 | 날짜 조각을 뽑고(닫힌 집합이라 Choice가 맞습니다), 조립과 비교는 코드가 합니다 |
| 4 | 우회. 이중 부정이나 여러 단계를 거치는 질문은 정확도를 깎습니다 | 단계를 줄이고, state에서 필요한 곳을 이름으로 가리킵니다 |
| 5 | 관련 없는 내용이 많은 state. 무관한 내용이 방해물이 됩니다 | 먼저 코드에서 걸러 내고, 질문에 필요한 필드만 보냅니다 |
| 6 | 적대적 내용. state는 데이터이고 기본적으로 적대로 다루지 않습니다 | 지시문을 정확히 쓰고, 널리 배포하기 전에 경계 사례를 시험합니다 |
| 7 | 어긋난 instructions와 criteria. 둘이 서로 다른 것을 요구할 수 있습니다 | criteria를 지시문의 연장으로 보고 문구를 맞춥니다 |
| 8 | 상식적인 구조 불변식. 질문과 그 부정의 합이 1이 아닐 수 있습니다 | 한 질문에 맞춘 임계값을 다른 질문으로 옮기지 않습니다 |
| 9 | 생성. 이 모델은 글을 만들어 내도록 훈련되지 않았습니다 | 생성 모델을 쓰거나, 추출을 후보 열거형 Choice로 바꿉니다 |

score 출력도 두 단계 사이의 정확한 수치를 되살리는 데는 약합니다. 값이 어떤 문턱을 넘는지는
판단할 수 있지만 값 자체를 복원하지는 못합니다.

## 공식 에이전트 스킬

- source_url: https://docs.typesafe.ai/agent-skill.md
- last_verified_at: 2026-10-01
- applies_to: 벤더가 배포하는 에이전트 스킬의 범위와 설치 방법
- volatility: volatile
- summary: 벤더는 코딩 에이전트에게 세 질문 유형, 구조 패턴, 평가 설계 모범 사례를 전하는
  스킬 하나를 배포합니다. 방향을 잡아 주는 안내입니다.

문서가 안내하는 설치 방법은 다음과 같습니다.

```bash
npx skills add typesafe-ai/skills --skill typesafe-ai
```

설치기는 어느 에이전트에 넣을지 묻고, 기본값은 프로젝트에만 설치하며, `-g`를 붙이면 전역으로
설치합니다. Claude Code 플러그인 경로도 있고 벤더의 스킬 폴더를 직접 복사하는 방법도 있습니다.
문서는 사본이 겹치지 않도록 한 가지 방법만 쓰라고 요청합니다. 갱신도 같은 설치기나 플러그인
마켓, 새 사본으로 합니다. 문서는 낡은 사본이 에이전트가 요청·응답 필드를 지어내는 원인이라고
적습니다.

이 스킬로 가져올 습관이 둘 있습니다. 질문과 임계값 같은 상수를 한 파일에 모아 사람이 검토할 수
있게 하고, 첫 초안을 그대로 받아들이지 말고 질문을 함께 고쳐 나가야 한다는 것입니다.

## Vercel AI SDK와 AI Gateway

- source_url: https://ai-sdk.dev/docs/ai-sdk-core/evaluation
- last_verified_at: 2026-10-01
- applies_to: `ai` 패키지의 평가 API, 그 질문 유형, 신뢰도 보고 방식
- volatility: volatile
- summary: SDK는 `experimental_evaluate`를 내놓습니다. 모델 하나와 공유 `state` 하나, 질문
  맵을 받아 질문 아이디마다 답 하나를 돌려줍니다. 이 API와 평가 모델 규격은 실험이며 패치
  릴리스에서 바뀔 수 있습니다.

코드를 쓸 때 걸리는 직접 경로와의 차이는 이렇습니다.

- 이 경로에서 예·아니오 판단의 질문 유형은 `noul`이 아니라 `boolean`입니다. 답에는 참일
  확률로 추정한 `probability`가 필수로 붙고, 유한하고 `[0, 1]` 안인지 검사합니다. SDK는
  보정을 보장하지 않습니다.
- Choice와 Score의 확률 분포는 여기서 선택이며, 언어 모델 어댑터는 아예 주지 않을 수 있습니다.
  분포가 있으면 기본 절대 허용 오차 `0.000001`로 합이 1인지 검사하고, 어긋나면 정규화하지 않고
  거부합니다.
- TypeSafe의 Choice·Score 신뢰도는 `result.providerMetadata?.typesafe?.confidence`에 질문
  아이디로 실립니다. 문서는 이것이 "is not the selected option's probability or a portable
  confidence measure"라고 경고합니다(evaluation, 2026-10-01).
- 문자열 모델 아이디는 기본 제공자를 따로 설정하지 않으면 Vercel AI Gateway로 해석됩니다.
  Gateway 인증은 `AI_GATEWAY_API_KEY` 또는 Vercel OIDC를 씁니다.
- 제공자 팩터리 형태도 있습니다: `typeSafeAi.evaluationModel('jev-latest')`.

Gateway의 모델 카드는 다음과 같습니다.

- source_url: https://vercel.com/ai-gateway/models/jev
- last_verified_at: 2026-10-01
- applies_to: Gateway에 올라온 Jev 항목
- volatility: volatile
- summary: 모델 아이디는 `typesafe-ai/jev`, 유형은 `evaluation`, 제공자는 `typesafe-ai`와
  `digitalocean`, 컨텍스트 창은 32,000, 최대 출력 토큰은 0, 가격은 입력 100만 토큰당
  0.042달러입니다. 세부 기능 정보는 보고되지 않았으므로 나머지는 미정으로 둡니다.

`@ai-sdk/typesafe-ai` 패키지의 버전은 이 스냅샷으로 확인되지 않았습니다. 숫자를 적는 대신
호출하는 프로젝트에 설치된 버전을 고정하십시오.

## b.ai Decisions API

- source_url: https://docs.b.ai/llmservice/api/decisions-api/
- last_verified_at: 2026-10-01
- applies_to: b.ai 경로, 그 요청·응답 필드, 정산 규칙
- volatility: volatile
- summary: 같은 모델을 쓰는 두 번째 공식 경로입니다. 분류, 점수화, 예·아니오 판단을 맡고,
  자유 서술 대신 구조화된 결과를 돌려줍니다.

- 엔드포인트는 `POST https://api.b.ai/v1/decisions`이고 `Content-Type: application/json`을
  씁니다. POST만 지원하므로 `stream`은 빼거나 `false`로 둡니다.
- 인증은 두 가지입니다. `Authorization: Bearer plus your key`를 쓰거나, 같은 값을 `x-api-key`
  헤더에 넣습니다.
- `model`은 `jev-1.13.0` 또는 `jev-latest`만 됩니다. 이 경로는 다른 아이디를 받지 않습니다.
- `state`는 문자열, 객체, 배열을 받습니다. `null`, 수, 불리언은 거부합니다.
- `questions`는 비어 있지 않은 맵입니다. 아이디가 비었거나 공백뿐이면 안 됩니다.
- `noul`의 criteria는 생략할 수 있습니다. 넣을 때는 키가 `"true"`와 `"false"`뿐인 객체여야
  하고, 각 값은 문자열, 객체, 배열입니다.
- `choice`의 criteria는 필수이고 선택지 1개에서 255개를 담습니다. 설명은 `null`이어도 됩니다.
- `score`의 criteria는 필수이고 항목 2개에서 10개짜리 배열입니다. 각 항목은 문자열, 객체,
  배열이고 `null`은 안 됩니다.

응답 필드는 직접 경로와 같습니다. `model`, `answers`, `usage`입니다. 이 경로는 답의 규칙을 더
분명히 적어 둡니다. `confidence`는 choice와 score에 필수이고, 문서는 "noul does not return a
separate confidence"라고 밝힙니다(decisions, 2026-10-01). choice와 score의 `probabilities`는
그 질문의 선택지 키나 문자열 단계 번호를 정확히 담아야 하고, "the values must sum to 1 within a
tolerance of 0.0001"입니다(decisions, 2026-10-01). score 답에는 문자열 단계 번호를 null이 아닌
설명으로 되돌리는 `legend`도 필요합니다. 신뢰도는 분포에서 뽑은 값이며 선택지 확률의 최댓값으로
다시 계산해서는 안 됩니다. 문서는 이것이 답의 정확도도 아니라고 경고합니다.

한도가 둘 있습니다. 두 사용량 값은 필수이고 그 합이 2147483647을 넘으면 안 되며, 16 MiB보다 큰
응답은 거부합니다. 답이나 사용량이 잘못되면 추정치를 붙인 성공 대신 오류를 냅니다.

요청 한도는 여기서 다르게 동작합니다. `429`의 본문이 비었거나 JSON이 아닐 수 있으므로 파싱
전에 HTTP 상태를 먼저 봅니다. 재시도는 상한을 둔 지수 백오프로 합니다. 이 엔드포인트는 멱등성을
보장하지 않으므로, 타임아웃 뒤의 재시도가 상류 작업을 되풀이할 수 있습니다. 한 요청 안의
질문은 서로 독립적으로 평가됩니다. 한 질문이 다른 질문의 답을 읽지 못하므로, 서로 의존하는
질문은 요청을 나누거나 코드에서 결과를 합칩니다.

정산 환산율은 고정입니다.

- source_url: https://docs.b.ai/llmservice/models/jev-1.13.0/
- last_verified_at: 2026-10-01
- applies_to: b.ai 모델 페이지의 기능 목록과 크레딧 환산
- volatility: volatile
- summary: 모델 아이디는 `jev-1.13.0`이고 `jev-latest`가 이 버전으로 해석됩니다. 크레딧은
  1달러 = 1,000,000 크레딧으로 정산하고, Jev는 입력 토큰에만 요금이 붙습니다. 같은 문서가 64K와
  32K 컨텍스트 한도, 선택지 255개와 단계 2~10개 한도, noul에 별도 신뢰도가 없다는 점을
  되풀이합니다.

그 문서에는 지킬 만한 경고도 있습니다. 형식이 맞는 것이 올바른 판단을 보장하지 않으므로,
임계값은 대표성 있는 데이터로 검증하고 동작이 일정해야 하면 버전 아이디를 고정하십시오. 같은
문서가 믿기 어려운 영역으로 산술, 세기, 날짜 비교, 여러 단계 추론을 들고, CJK 문자를 포함한
다국어 작업에는 그 작업에 맞춘 검증이 필요하다고 적습니다. 문서에 실린 가격은 표준
참고가이며, 충전 보너스와 계정 혜택이 실제 비용을 낮출 수 있습니다.

## Sources

> Links checked 2026-10-01. Next re-verification: 2026-10-31.

| 주장 | 출처 |
| --- | --- |
| 엔드포인트, 헤더, 요청 필드, 질문 아이디 규칙, 응답 필드, 401/422/429/529 동작 | <https://docs.typesafe.ai/api> |
| 질문 유형 세 가지와 각 유형의 criteria 규칙, 답의 형태 | <https://docs.typesafe.ai/api> |
| 모델 아이디, 별칭 둘, 가격, 요청 한도, 컨텍스트 예산, 텍스트 전용 입력, 언어 지원 설명 | <https://docs.typesafe.ai/models> |
| 신뢰도의 유도, "한 숫자가 아니다" 규칙, 벤더 예시의 0.5 하한 | <https://docs.typesafe.ai/confidence> |
| 거친 부분 아홉 가지, 각 우회법, 2026-09-17 검토일 | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| 공식 스킬의 범위, 설치 명령, 상수를 한 파일에 두는 습관, 낡은 사본 문제 | <https://docs.typesafe.ai/agent-skill.md> |
| `experimental_evaluate`, `boolean` 유형, 분포 허용 오차, Gateway 신뢰도 경로, Gateway 인증 | <https://ai-sdk.dev/docs/ai-sdk-core/evaluation> |
| Gateway 모델 카드: 아이디, 유형, 제공자, 컨텍스트 창, 출력 토큰, 가격 | <https://vercel.com/ai-gateway/models/jev> |
| b.ai 엔드포인트, 인증 헤더 둘, 모델 아이디, 유형별 criteria 규칙, 응답 필드, 0.0001 허용 오차, 사용량 합 상한, 16 MiB 한도, 429 안내 | <https://docs.b.ai/llmservice/api/decisions-api/> |
| b.ai 모델 페이지: 아이디, 크레딧 환산, 컨텍스트 한도, 다국어와 형식 준수 경고 | <https://docs.b.ai/llmservice/models/jev-1.13.0/> |
| `TypeSafeClient`, `client.systemOne`, `TYPESAFE_API_KEY`, `choice()` 사실을 확인한 JavaScript SDK 문서 | <https://docs.typesafe.ai/sdk/javascript.md> |
| 위 문서를 찾는 데 쓴 문서 목록 | <https://docs.typesafe.ai/llms.txt> |

### 증거 등급

이 문서의 모든 항목이 `PRIMARY`입니다. 위 표의 각 줄은 설명 대상 서비스의 벤더 문서이고,
2026-10-01에 원문 그대로 받아 이 스냅샷의 증거와 함께 저장했습니다. 예외는 b.ai 문서 둘입니다.
두 페이지는 자바스크립트로 그려지므로 원문 markdown이 아니라 렌더된 본문 텍스트를 읽었습니다.
본문은 끝까지 읽었고 두 번 읽은 내용이 같았습니다.

이 문서들로 확인되지 않아 일부러 비워 둔 것: `@ai-sdk/typesafe-ai` 패키지의 버전, JavaScript
SDK가 `choice()` 말고 다른 질문 유형의 도우미를 가진다는 주장, 그리고 벤더 쿡북의 개수입니다.
