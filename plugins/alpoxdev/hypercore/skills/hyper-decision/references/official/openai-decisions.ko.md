# OpenAI Decisions 스냅샷

OpenAI 자체 문서가 말하는 Decisions API의 모습을 한 파일에 모았습니다. 엔드포인트, 요청과 응답의
형태, 한도, 가격, Azure 변형, 게이트웨이 경로, 그리고 확률을 원하는 호출자에게 OpenAI 일반 모델이
무엇을 주고 무엇을 주지 않는지를 담습니다. Sources에 적은 문서를 2026-11-08에 직접 읽고 옮겼습니다.

이 파일은 이 패키지에서 자주 바뀌는 벤더 사실을 두는 자리 중 하나입니다. 벤더 간 경로 비교는 옆의
경로 참조에, TypeSafe 사실은 그 옆 파일에 있습니다.

## Contents

- 갱신 정책
- 엔드포인트와 인증
- 요청 형태
- 질문
- 응답과 거절
- 한도
- 가격
- 상태와 날짜
- Azure OpenAI Decisions
- Vercel AI Gateway의 OpenAI 호환 결정
- OpenAI 일반 모델이 주는 것과 주지 않는 것
- 고정 분류기로서의 모더레이션
- Evals, grader, 파인튜닝
- Sources
- Evidence grade

## 갱신 정책

- last_verified_at: 2026-11-08
- refresh_when:
  - 엔드포인트, 받는 모델, 인증 헤더가 바뀔 때
  - 질문 유형, 응답 필드, 거절 동작이 바뀔 때
  - 한도, 가격, 캐시 입력 요율이 바뀔 때
  - Azure 배포 지역이 늘거나 줄 때
  - 일반 모델이 로그 확률을 얻거나 잃을 때
  - evals와 파인튜닝 은퇴 날짜가 지날 때

이 파일이 30일보다 낡았고 네트워크가 살아 있으면 벤더 문서를 읽기 전용으로 다시 읽습니다. 네트워크가
없으면 값을 짐작하지 말고 스냅샷 날짜를 그대로 밝힙니다.

## 엔드포인트와 인증

- source_url: https://developers.openai.com/api/docs/guides/decisions.md
- last_verified_at: 2026-11-08
- applies_to: 엔드포인트, 모델, SDK 진입점
- volatility: volatile
- summary: 엔드포인트 하나가 하나의 입력에 대한 타입 질문에 답합니다. `gpt-6-luna`가 지원되는 유일한
  모델입니다.

| 항목 | 값 |
| --- | --- |
| 경로 | OpenAI API의 `POST /v1/decisions` |
| Python SDK | `client.decisions.create(...)` |
| 인증 | 표준 OpenAI API 키를 쓰는 `Authorization: Bearer <OPENAI_API_KEY>` |
| 모델 | `gpt-6-luna`, 현재 지원되는 유일한 모델로 문서화됨 |
| 벤더의 표현 | 문서는 이 API가 "텍스트, 이미지, JSON을 평가하고 Responses API보다 약 10배 빠르게 타입 답을 돌려준다"고 적음 |

10배라는 숫자에는 벤치마크가 없습니다. 데이터셋도 지연 백분위도 방법론도 함께 공개되지
않았습니다. 벤더 주장으로 다루고 설계 근거로 쓰지 않습니다.

## 요청 형태

- source_url: https://developers.openai.com/api/reference/resources/decisions/methods/create.md
- last_verified_at: 2026-11-08
- applies_to: `input` 필드와 그 형태, `input_json` 파트
- volatility: stable
- summary: `input`이 TypeSafe 방언의 `state` 자리를 대신하고, 단순 문자열보다 많은 형태를 받습니다.

| 형태 | 설명 |
| --- | --- |
| 문자열 | 일반 텍스트 입력, 최대 10,485,760자 |
| 입력 항목 | 메시지와 도구 호출을 포함한 항목 배열이라 대화나 에이전트 기록을 입력으로 쓸 수 있음 |
| `input_json` | 자체 한도가 붙은 JSON 파트: 256 KiB, 값 10,000개, 컨테이너 32단계 |
| 이미지 | 받음, URL로 준 이미지 포함, Azure 문서는 요청당 이미지 128개와 합계 32 MB로 제한 |

생성 코드에 따라오는 결과가 둘입니다. 첫째, 결정 요청이 문자열 하나로 제한되지 않습니다. 에이전트
기록이나 구조화 레코드가 공유 입력이 될 수 있고, 그래서 도구를 쓰는 루프 안의 게이트로 쓸 만합니다.
둘째, `input_json` 한도가 보통 JSON 페이로드보다 작아서 큰 레코드는 넣기 전에 덜어내거나 나눠야
합니다.

## 질문

- source_url: https://developers.openai.com/api/reference/resources/decisions/methods/create.md
- last_verified_at: 2026-11-08
- applies_to: `questions` 배열과 질문 유형 셋
- volatility: stable
- summary: `questions`는 맵이 아니라 배열이고, 항목마다 응답을 키로 잡는 고유 `name`을 가집니다.
  요청 하나가 질문 1~400개를 받습니다.

| 유형 | 요청 필드 | 응답 필드 |
| --- | --- | --- |
| `predicate` | `instructions` | `probability`, 0~1 숫자 |
| `choice` | `instructions`, `choices`: `{ value, description }` 배열, 2~255개, `value`는 고유 | `choice`, `probabilities[]`, `confidence` |
| `score` | `instructions`, `levels`: `{ label, description }` 배열, `minItems: 2`, `maxItems: 10` | `score`(단계 인덱스의 확률 가중 평균이라 단계 사이에 올 수 있음), `probabilities[]`, `confidence` |

문서 기준으로 choice의 `value`는 문자열이나 불리언일 수 있습니다. 질문마다 `name`이 있어야 응답을
쓸 수 있습니다. 응답이 이 값을 키로 잡고, 이름이 없는 질문은 `name: null`로 돌아옵니다.

서로 독립인 질문은 한 배열에 넣습니다. 의존하는 순서("손상을 먼저 확인하고 수리 분류를 고른다")는
별도 요청으로 나누라고 벤더가 안내합니다. 한 요청 안의 질문은 서로의 답을 읽지 못합니다.

점수 하한은 여기서 2입니다. TypeSafe 스키마는 1을 받습니다. 두 방언을 함께 겨냥하는 요청 생성기는
단계를 2개 이상으로 유지합니다.

## 응답과 거절

- source_url: https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions
- last_verified_at: 2026-11-08
- applies_to: 거절을 포함한 응답 유니온
- volatility: stable
- summary: 질문마다 응답 객체 하나가 오고 그 타입이 `predicate`, `choice`, `score`, `refusal` 중
  하나입니다. Azure 문서가 중요한 구분을 적습니다. "거절은 확률이 낮은 predicate 답과 다릅니다."

거절은 네 번째 응답 유형이고, 확률이 낮은 답도 아니고 실패한 요청도 아닙니다. 생성 코드는 거절에서
분기해야 합니다. 거절을 `probability: 0`이나 첫 선택지, 점수 0으로 바꾸면 "모델이 거절했다"를
"모델이 아니라고 했다"로 조용히 바꾸게 되고, 그 둘은 다른 결정입니다. 거절은 낮은 신뢰도 답과 같은
곳으로, 또는 사람에게 보냅니다.

응답마다 `name`이 돌아오므로 TypeSafe 방언이 질문 아이디로 키를 잡는 것처럼 질문 이름으로 응답을
키로 잡을 수 있습니다.

## 한도

- source_url: https://developers.openai.com/api/reference/resources/decisions/methods/create.md
- last_verified_at: 2026-11-08
- applies_to: 요청 단위 개수와 필드별 크기
- volatility: volatile
- summary: 질문 수는 넉넉하고 JSON 페이로드 크기는 빡빡합니다.

| 항목 | 한도 |
| --- | --- |
| 요청당 질문 | 1~400 |
| `choice` 질문의 선택지 | 2~255, 값은 고유 |
| `score` 질문의 단계 | 2~10 |
| `probabilities` 배열 하나의 항목 | 최대 2,000 |
| 문자열 입력 | 최대 10,485,760자 |
| `input_json` | 최대 256 KiB, 값 10,000개, 컨테이너 32단계 |
| 요청당 이미지 | 128개, 합계 32 MB, 같은 계약을 적은 Azure 문서 기준 |

`probabilities` 상한 2,000은 선택지 255개짜리 choice 질문 몇백 개로도 접근합니다. 선택지 수를
제한하거나 요청을 나눕니다.

## 가격

- source_url: https://developers.openai.com/api/docs/guides/decisions.md
- last_verified_at: 2026-11-08
- applies_to: 입력 요금과 출력 항목
- volatility: volatile
- summary: 입력 토큰에 요금이 붙고 출력은 과금하지 않습니다.

| 항목 | 값 |
| --- | --- |
| 캐시되지 않은 입력 | 100만 토큰당 `$0.10` |
| 출력 | `/v1/decisions`에서는 과금 없음 |
| 캐시 입력 | 문서의 "uncached" 표현은 캐시 요율이 있음을 시사함, 이 스냅샷은 캐시 요율 숫자를 인용하지 않음 |

이 엔드포인트의 출력 토큰은 구조상 0입니다. 생성할 것이 없습니다. 모델 페이지의 토큰당 요율은 같은
모델을 일반 엔드포인트에서 쓸 때의 값이고 `/v1/decisions`의 값이 아닙니다.

받아 둔 문서 어디에도 지역별 가격 할증이 없으므로 여기에도 적지 않습니다. Azure 가격은 Azure 자체
가격 페이지에 있고 이 스냅샷은 그것을 주장하지 않습니다.

## 상태와 날짜

- source_url: https://developers.openai.com/api/docs/changelog.md
- last_verified_at: 2026-11-08
- applies_to: 출시 일정
- volatility: stable
- summary: 한 달 안에 베타를 거쳐 정식 출시됐습니다.

| 날짜 | 사건 |
| --- | --- |
| 2026-10-06 | `gpt-6-luna`로 Decisions API 베타 공개 |
| 2026-10-22 | `gpt-6-luna`로 Decisions API 정식 출시 |

베타는 요청당 질문 200개를 받았고 정식 출시는 400개를 받습니다. 변경 이력 자체가 그 변경을 그렇게
설명합니다. 날짜는 변경 이력이 주장하는 값이고, 독립적인 두 번째 날짜 표기는 찾지 못했습니다.

## Azure OpenAI Decisions

- source_url: https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions
- last_verified_at: 2026-11-08
- applies_to: 같은 엔드포인트의 Azure 변형
- volatility: volatile
- summary: Azure는 고객 자기 리소스의 전용 경로에서 같은 요청·응답 계약을 서빙하고, OpenAI 경로에서
  복사한 코드를 깨뜨리는 운영 차이가 둘 있습니다.

| 항목 | 값 |
| --- | --- |
| 경로 | `{resource}.openai.azure.com`의 `/openai/v1/decisions` |
| 모델 | `gpt-6-luna` 배포 전용, `model` 필드가 모델 아이디가 아니라 배포 이름을 받음 |
| 인증 | `api-key` 헤더 또는 Microsoft Entra ID |
| 요청당 질문 | 최대 400 |
| 요청당 이미지 | 최대 128개, 합계 32 MB |
| 배포 | `gpt-6-luna`가 있는 지역으로 순차 배포, "East US 2는 배포에서 제외" |
| SDK 하한 | openai-python 3.26.0 이상, openai-node 7.30.0 이상, OpenAI .NET 2.15.0 이상 |
| 문서 날짜 | `ms.date` 2026-11-06 |

배포 이름 규칙이 이 경로에서 404를 내는 가장 흔한 원인입니다. 모델 아이디는 OpenAI 경로에서 되고
Azure에서 실패합니다. 보편적 가용성을 광고하지도 않습니다. 배포에서 빠진 지역은 배포 문제처럼 보이는
오류를 돌려줍니다.

## Vercel AI Gateway의 OpenAI 호환 결정

- source_url: https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions
- last_verified_at: 2026-11-08
- applies_to: 게이트웨이의 OpenAI 모양 결정 경로
- volatility: volatile
- summary: 게이트웨이가 `/v1/decisions`를 OpenAI 모양으로 노출하므로, 기존 OpenAI 클라이언트는
  base URL과 자격 증명, 모델 아이디만 바꿔 옮겨 옵니다.

| 항목 | 값 |
| --- | --- |
| 경로 | `POST https://ai-gateway.vercel.sh/v1/decisions` |
| 인증 | `Authorization: Bearer $AI_GATEWAY_API_KEY` 또는 Vercel OIDC |
| 질문 유형 | `predicate`, `choice`, `score` |
| 질문당 선택지 | 1~255 |
| 질문당 단계 | 2~10 |
| AI SDK 하한 | SDK 경로는 `ai` 7.0.128 이상 |

게이트웨이의 결정 폴백은 그 위에 얹히는 전송 계층입니다. 성공했지만 불확실한 답을 다른 모델로 다시
실행합니다. 따라오는 사실이 둘입니다. 폴백이 걸리면 두 단계 모두 과금됩니다. 그리고 폴백이 네이티브
결정 모델이 아니라 언어 모델일 때 OpenAI 모양 표면은 신뢰도와 확률 분포를 지어내지 않고 빼놓으므로,
생성 코드는 둘 다 선택 필드로 다뤄야 합니다. 세부는 옆의 공급자 스냅샷에 있습니다.

## OpenAI 일반 모델이 주는 것과 주지 않는 것

- source_url: https://developers.openai.com/api/docs/guides/structured-outputs.md,
  https://developers.openai.com/api/reference/resources/chat/index.md
- last_verified_at: 2026-11-08
- applies_to: 일반 모델 위의 흉내 경로와, 그것이 쓸 만한 확률을 거의 만들지 못하는 이유
- volatility: volatile
- summary: 구조화 출력은 닫힌 집합을 주고 신뢰도를 주지 않습니다. 로그 확률은 일부 모델에서 토큰
  단위 숫자를 주고, 사람들이 실제로 고르는 모델에서는 없습니다.

| 기능 | 주는 것 | 걸리는 한도 |
| --- | --- | --- |
| 구조화 출력, `strict: true`인 `json_schema` | 타입 객체만, 열거형은 제약 디코딩으로 강제 | 모든 열거 속성 합계 1,000개 값, 문자열 열거 하나가 250개를 넘으면 전체 15,000자, 속성 5,000개와 중첩 10단계, `additionalProperties: false` 필수, 루트는 객체, `allOf`, `not`, `if`/`then`/`else`, dependent 계열 미지원 |
| Chat Completions의 `logprobs`와 `top_logprobs` | 토큰 단위 로그 확률과 위치마다 최대 `top_logprobs`개의 대안 | `top_logprobs`는 0~20이고 돌아오는 항목이 요청보다 적을 수 있음 |
| Responses API의 `logprobs` | `include: ["message.output_text.logprobs"]`로 같은 토큰 단위 모양 | 같은 0~20 상한, Responses API에는 `logit_bias`가 아예 없음 |
| `logit_bias`, Chat Completions 전용 | 토큰 아이디마다 -100~100 편향 | 토큰 아이디 단위이고 라벨 단위가 아니라, 라벨이 단일 토큰이 아니면 라벨 API로 쓸 수 없음 |

흉내 계획을 망치는 것은 모델 게이팅입니다.

| 모델 | 로그 확률 |
| --- | --- |
| GPT-6 Astra | 전혀 지원하지 않음, 변경 이력이 "사용자 지정 `temperature`나 `top_p`, 로그 확률(`logprobs`)을 지원하지 않는다"고 적음 |
| GPT-5.4와 GPT-5.2 | `reasoning.effort`가 `none`일 때만 지원, 다른 추론 강도는 오류 |
| GPT-5, GPT-5-mini, GPT-5-nano | 어느 추론 강도에서도 오류 |

`strict: true`에 지원하지 않는 키워드가 오면 best-effort 출력이 아니라 오류가 납니다. 흉내 경로의
유일한 좋은 성질입니다. 조용히 신뢰도 없는 라벨을 돌려주는 대신 실패합니다.

어느 모델에서도 절대 주지 않는 것은 닫힌 집합 위의 라벨 단위 확률 분포입니다. Decisions API가 더하는
것이 정확히 그것이고, 확률에 임계값을 걸어야 하는 호출자를 구조화 출력 경로로 보내면 안 되는
이유입니다.

## 고정 분류기로서의 모더레이션

- source_url: https://developers.openai.com/api/docs/guides/moderation.md
- last_verified_at: 2026-11-08
- applies_to: 모더레이션 엔드포인트, 분류기이지만 결정 API는 아님
- volatility: stable
- summary: 모더레이션은 분류마다 0~1 점수를 돌려주고 텍스트와 이미지를 다루며 무료입니다. 라벨
  집합이 벤더 자기 분류로 고정돼 있어서 부록이고 경로가 아닙니다.

| 항목 | 값 |
| --- | --- |
| 모델 | `omni-moderation-latest`, `omni-moderation-2024-09-26`과 동등 |
| 엔드포인트 | `POST /v1/moderations`, SDK `client.moderations.create` |
| 입력 | 문자열, 문자열 배열, 멀티모달 배열, 이미지는 20 MB까지, 오디오는 분류하지 않음 |
| 출력 | 분류마다 0~1 `category_scores`, 불리언 `categories`, `flagged` |
| 분류 | `harassment`, `hate`, `illicit`, `illicit/violent`, `self-harm/intent` 등을 포함한 13개 |
| 비용 | 무료 |
| 무료 등급 한도 | 분당 250 요청, 하루 5,000 요청, 분당 10,000 토큰 |
| 인라인 모더레이션 | 2026-06-04 추가, 생성 요청에 `moderation` 객체를 넣으면 입력과 생성 출력 모두의 점수가 같은 응답에 옴 |

문서는 `category_scores`에 기대는 정책이 "시간이 지나며 재보정이 필요할 수 있다"고 경고합니다.
일반 경고의 정직한 형태입니다. 분류 점수는 모델 출력이고 모델 업그레이드에 따라 흔들리며, 고정된
정책 판정이 아닙니다.

## Evals, grader, 파인튜닝

- source_url: https://developers.openai.com/api/docs/deprecations.md
- last_verified_at: 2026-11-08
- applies_to: 은퇴 경로에 있는 판정기와 grader 표면
- volatility: volatile
- summary: eval 플랫폼과 그 grader가 공개된 종료 경로에 있고, 셀프서비스 파인튜닝은 새 작업을 받지
  않습니다. 둘 다 오래 갈 권장이 아닙니다.

| 표면 | 상태 |
| --- | --- |
| Evals 플랫폼 | 기존 사용자에게 2026-10-31부터 읽기 전용, 2026-11-30 종료 예정 |
| `label_model`, `score_model`을 포함한 grader | evals와 파인튜닝과 함께 폐기, `POST /v1/fine_tuning/alpha/graders/run`은 아직 응답하지만 안내 문서가 표면 전체를 폐기로 표시 |
| 셀프서비스 파인튜닝 | 2027-01-06부터 새 작업 불가, 새 조직은 이미 2026-05-07부터 작업 생성 불가, GPT-4.1과 4o 파인튜닝 베이스는 2027-01-14 종료 |
| 강화 파인튜닝 | 현재 문서에 존재하지 않음, 안내 경로가 Graders 문서로 리다이렉트됨 |

`label_model` grader는 닫힌 집합("각 항목에 부여할 라벨")과 구조화 출력을 지원하는 모델을 실제로
강제하므로 코드 예시에서는 결정 API처럼 읽힙니다. 종료 공지이고 권장이 아닙니다. 새 결정 경로를
그 위에 세우지 않습니다.

## Sources

> Links checked 2026-11-08.

| 주장 | 출처 |
| --- | --- |
| Decisions 안내: 엔드포인트, `gpt-6-luna` 단일 지원, "10배 빠름" 주장, 입력·출력 과금 구분, 질문 1~400 | <https://developers.openai.com/api/docs/guides/decisions.md> |
| 생성 레퍼런스: 질문 1~400, 선택지 2~255, `minItems: 2`와 `maxItems: 10`, 응답 필드, `input_json`과 문자열 입력 한도, `probabilities` 2,000 항목 상한 | <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| 2026-10-06 베타와 2026-10-22 정식 출시, 질문 200개에서 400개로의 변경 | <https://developers.openai.com/api/docs/changelog.md> |
| Azure의 `/openai/v1/decisions`, 배포 이름 규칙, 질문 400, 이미지 128개와 32 MB, `api-key` 또는 Entra ID, East US 2 제외, SDK 하한 | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| 거절과 낮은 확률 답의 구분 | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| 구조화 출력의 열거 1,000 한도, 250값과 15,000자 규칙, 속성 5,000과 중첩 10단계, `additionalProperties: false`, 미지원 키워드 오류 | <https://developers.openai.com/api/docs/guides/structured-outputs.md> |
| `top_logprobs` 0~20, 항목이 더 적게 올 수 있다는 설명, `logit_bias` -100~100 | <https://developers.openai.com/api/reference/resources/chat/index.md> |
| GPT-6 Astra의 `temperature`, `top_p`, `logprobs` 제거와 Responses의 `include` 제거 | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md> |
| GPT-5.4와 GPT-5.2의 `reasoning.effort: none` 조건, GPT-5·mini·nano의 오류 | <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4.md> |
| 2026-09-03 변경 이력의 GPT-6 Astra 로그 확률 항목 | <https://developers.openai.com/api/docs/changelog.md> |
| 모더레이션: `omni-moderation-latest`, 텍스트·이미지 입력, 오디오 없음, 무료, 20 MB 이미지, 재보정 경고, 13개 분류, 무료 등급 한도 | <https://developers.openai.com/api/docs/guides/moderation.md>, <https://developers.openai.com/api/reference/resources/moderations/index.md> |
| 2026-06-04 추가된 인라인 모더레이션 객체 | <https://developers.openai.com/api/docs/changelog.md> |
| 2026-10-31 읽기 전용과 2026-11-30 종료, 파인튜닝 종료 날짜 | <https://developers.openai.com/api/docs/deprecations.md> |
| grader가 라벨이나 0~1 점수를 돌려준다는 점, `label_model`의 구조화 출력 요구, grader 폐기 | <https://developers.openai.com/api/docs/guides/graders.md>, <https://developers.openai.com/api/reference/resources/graders/index.md> |
| 게이트웨이의 OpenAI 호환 결정 경로, 1~255와 2~10 한도, base URL 교체 | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions>, <https://vercel.com/changelog/openai-decisions-api-now-available-on-ai-gateway> |
| `gpt-6-luna`의 지원 엔드포인트와 `reasoning.effort` 값 | <https://developers.openai.com/api/docs/models/gpt-6-luna.md> |

### Evidence grade

이 파일의 모든 항목이 `PRIMARY`입니다. 각 사실이 설명 대상 제품의 OpenAI나 Microsoft 문서에서
나왔고 2026-11-08에 받아 두었으며, 예외는 게이트웨이 줄로 Vercel 자기 경로에 관한 Vercel 문서입니다.

두 항목은 `SECONDARY`이고 쓰는 자리에서 표시했습니다. "10배 빠름"은 벤치마크 없는 벤더 주장이고,
캐시 입력 요율의 존재는 가격 문장의 "uncached"라는 표현에서 추론한 것이지 숫자로 인용한 것이
아닙니다.

이 문서들로 확인되지 않아 일부러 비워 둔 것: OpenAI 경로의 지역별 가격 할증, 돌려주는 확률의 어떤
보정 약속, 캐시 입력 요율, 그리고 어떤 지연 시간 측정값입니다.
