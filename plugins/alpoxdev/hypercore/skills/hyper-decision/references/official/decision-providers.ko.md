# 결정 공급자 스냅샷

2026-11-08 기준으로 TypeSafe와 OpenAI를 뺀 나머지 결정형 API 공급자 전부, 그리고 게이트웨이 계층
둘, Vercel AI SDK의 제공자 지원 범위, 범용 모델 흉내 층, 고정 분류기 부록을 담습니다. 사실은 1차
벤더 문서에서 왔고, `B`로 표시한 줄만 제3자 집계에 기댑니다.

벤더 간 경로 비교와 층, 경로 선택 순서는 옆의 경로 참조에 있습니다. TypeSafe 사실은 Jev 스냅샷에,
OpenAI 사실은 OpenAI 스냅샷에 있습니다.

## Contents

- 갱신 정책
- Perplexity Decisions
- Microsoft-Decision-1
- Liquid AI d1
- Cloudflare Clef
- Cloudflare Clairic, 추출 전용
- Parallel Decisions
- Baseten 결정 모델
- Upstage Solar Decide
- Vercel AI SDK 제공자 지원 범위
- Vercel AI Gateway 결정
- OpenRouter 결정과 추출
- T3: 범용 모델 위의 흉내
- T4 부록: 고정 분류기, 가드레일, 판정기, 은퇴한 표면
- Sources
- Evidence grade

## 갱신 정책

- last_verified_at: 2026-11-08
- refresh_when:
  - 벤더가 엔드포인트, 인증, 모델 아이디, 질문 유형을 바꿀 때
  - 벤더가 베타를 벗어나 정식 출시하거나 은퇴할 때
  - 응답 필드가 바뀔 때, 특히 `confidence`의 위치나 존재 여부가 바뀔 때
  - 게이트웨이가 결정 표면이나 폴백 계약, 과금 규칙을 바꿀 때
  - AI SDK 제공자 패키지가 결정 팩토리를 내거나 흉내 범위를 바꿀 때
  - 부록의 은퇴 날짜가 지날 때

## Perplexity Decisions

- source_url: https://docs.perplexity.ai/docs/decisions/quickstart,
  https://docs.perplexity.ai/api-reference/decisions-post
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Perplexity는 System One 필드 이름(`state`와 `questions` 맵, `noul`/`choice`/`score`)을
  자기 `/v1/decisions` 경로에 그대로 쓰고 모델만 자기 것을 씁니다. 큰 벤더 중 Jev를 거의 그대로
  갈아 끼울 수 있는 쪽이고, TypeSafe를 빼면 신뢰도 공식을 공개한 유일한 벤더입니다.

| 항목 | 값 |
| --- | --- |
| 엔드포인트 | `POST https://api.perplexity.ai/v1/decisions` |
| 인증 | `Authorization: Bearer <key>` 전용, `x-api-key` 헤더는 401 |
| 모델 | `pplx-decider-v1.2`(27B)와 `pplx-decider-flash-v1.2`(4B), 별칭 `pplx-decider-latest`와 `pplx-decider-flash-latest` |
| 질문 유형 | `noul`, `choice`, `score` |
| `choice` 선택지 | 1~255, 설명은 `null` 허용 |
| `score` 단계 | 1~10, 산문은 "두 단계 이상 권장" |
| 요청당 질문 | 최소 1, `mode: web_grounding`에서는 최대 100 |
| 입력 | state와 질문 하나를 합쳐 256K 입력 토큰, 본문 32 MiB |
| 이미지 | 질문당 최대 8개, 각 2,048 타일 |
| 응답 필드 | `noul` 스칼라, `choice`와 `probabilities`·`confidence`, `score`와 `legend`·`probabilities`·`confidence` |
| 가격 | v1.2는 입력 100만 토큰당 `$0.02`, flash는 `$0.01`, 출력 무료 |
| 상태 | 정식 출시, 변경 이력의 2026년 10월 항목 |

실무 함정이 둘입니다. 첫째, 모델에 따라 질문 묶음마다 또는 질문마다 state를 다시 과금하므로 질문을
많이 담은 요청이 토큰당 요율이 말하는 만큼 싸지 않습니다. 둘째, `web_grounding`은 요청을 질문
100개로 제한하고 검색마다 요금 항목을 더합니다. 둘 다 답 단위가 아니라 요청 단위입니다.

Perplexity는 choice와 score 양쪽에 쓰는 신뢰도 공식을 공개합니다. 그래서 TypeSafe 말고 이 벤더만
생성 산출물에서 신뢰도의 유도를 적을 수 있습니다. 그래도 다른 벤더로 이식되지는 않습니다.

## Microsoft-Decision-1

- source_url: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Foundry에서 호스팅하고 고객 자기 Foundry 리소스의 Microsoft 전용 경로에서 System One
  모양으로 답하는 결정 모델입니다. Azure OpenAI Decisions와 다른 물건이고, 그쪽은 OpenAI 스냅샷에 있는
  `gpt-6-luna` 계약입니다.

| 항목 | 값 |
| --- | --- |
| 엔드포인트 | `<your-foundry-resource-endpoint>/providers/microsoft/v1/systemone` |
| 인증 | Microsoft Entra ID bearer 또는 `api-key` 헤더 |
| 모델 필드 | 기반 모델 이름이 아니라 배포 이름 |
| 질문 유형 | `noul`, `criteria` 맵을 쓰는 `choice`, 순서 있는 `criteria` 목록을 쓰는 `score` |
| 응답 필드 | 질문 이름을 키로 하는 `answers`, 각 항목은 `noul`, `probabilities`가 붙은 `choice`, `probabilities`가 붙은 `score`, 그리고 `model`과 `usage` |
| 입력 | 텍스트나 JSON state만, 이미지 경로는 문서화되지 않음 |
| 선택지와 단계 | 개수가 how-to 페이지에 없음 |
| 가격 | 입력 토큰 기준, 게이트웨이는 100만 토큰당 `$0.042`, 출력 `$0` |
| 상태 | Foundry에서 정식 출시, how-to `ms.date` 2026-10-07, 게이트웨이 등장 2026-10-09 |
| 지역 | 유럽(francecentral, germanywestcentral, italynorth, polandcentral, spaincentral, swedencentral, westeurope)과 아시아 태평양(australiaeast, japaneast, japanwest, koreacentral, southeastasia, southindia), 중동과 아프리카는 미제공 |

이 모델은 산문을 만들지 않습니다. how-to는 "자유 형식 응답이나 서면 근거를 만들지 않고, 텍스트나
JSON에 대한 집중된 판단을 내려 타입이 붙은 수치 결정을 돌려준다"고 적습니다. 결정 모델이 무엇을 위한
것인지에 대한 자료 전체에서 가장 깔끔한 문장입니다.

선택지와 단계 개수가 문서화되지 않았으므로 이 경로의 한도를 공표하지 않습니다. 자체 값을 짐작하는
대신 이식 가능한 경계(선택지 2~255, 단계 2~10)를 지킵니다.

## Liquid AI d1

- source_url: https://docs.liquid.ai/api/guides/decisions,
  https://docs.liquid.ai/lfm/models/decision-models
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Liquid는 TypeSafe의 System One API를 자기 경로에 문자 그대로 구현해 호스팅 상품으로
  팔고, 추가 프리미티브가 붙은 오픈웨이트 결정 모델도 냅니다.

| 항목 | 값 |
| --- | --- |
| 엔드포인트 | `POST https://api.liquid.ai/decisions/v1/systemone` |
| 인증 | `Authorization: Bearer liquid_<key>` |
| 호스팅 모델 | `d1.1`(기본, 65,536 컨텍스트)과 `d1-ultra`(32,768) |
| 오픈웨이트 모델 | LFM Open License의 `d1-2B`, `d1-omni-2B`, `d1-omni-600M` |
| 질문 유형, 호스팅 | `noul`, `choice`, `score` |
| 질문 유형, 오픈웨이트 | `box`/`boxes`와 `multiple: true` 다중 선택 choice 추가 |
| 한도 | 요청당 이미지 8개, 본문 4.5 MB, 패치 10,000개 |
| 응답 필드 | `noul` 스칼라, `choice`와 `score`의 `probabilities`와 `confidence` |
| 과금 | 입력 토큰만, 출력 무료 |
| 오류 | 검증 실패는 `422` |
| 상태 | 정식 출시(호스팅) |

벤더는 이 모델이 "생성 토큰 없이 보정된 Noul, Choice, Score 답을 돌려준다"고 설명합니다. "보정된"은
마케팅 형용사로 다룹니다. 이 파일의 어느 벤더도 보정 곡선이나 오차 지표를 공개하지 않습니다.

모델 아이디 함정이 하나 있습니다. Liquid 자기 문서는 `d1.1`을 기본 호스팅 모델로 적고, `d1`과
`d1-ultra`는 게이트웨이에서 쓰는 이전 모델이라고 설명합니다. 게이트웨이 카탈로그는 `liquid/d1`과
`liquid/d1-ultra`를 싣습니다. 모델 아이디를 쓸 때 `d1`과 `d1.1`을 같은 것으로 다루지 않습니다.

## Cloudflare Clef

- source_url: https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef/, 그리고 같은 계열
  모델 페이지
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Workers AI에서 호스팅하는 오픈 결정 모델 계열이고, 자체 HTTP 결정 경로가 아니라 Workers
  AI 바인딩으로 부릅니다. `noul`을 쓰므로 OpenAI 방언과 페이로드가 섞일 수 없습니다.

| 모델 | 크기와 컨텍스트 | 모달리티 | 가격 |
| --- | --- | --- | --- |
| `@cf/cloudflare/clef` | 27B, 65,536 컨텍스트 | 텍스트, JSON state, 이미지(요청당 4개) | 입력 100만 토큰당 `$0.24` |
| `@cf/cloudflare/clef-flash` | 9B, 24,576 컨텍스트 | 텍스트, JSON state, 이미지(요청당 4개) | 입력 100만 토큰당 `$0.038` |
| `@cf/cloudflare/clef-omni` | 30B 전문가 혼합, 활성 3B, 64,000 컨텍스트 | 오디오 클립 4개와 비디오 2개 추가 | 입력 100만 토큰당 `$0.15` |

공통 성질: 요청당 질문 1~64개, 질문 아이디는 문자와 숫자, `_`, `.`, `-`로 최대 100자,
`noul`/`choice`/`score` 전용, 제로 데이터 보존, 출력 토큰 무과금. 출력 스키마는 choice 응답에 `type`,
`choice`, `probabilities`, `confidence`를 요구하고 `noul`을 0~1로 제한합니다.

호출은 Worker 안에서 `env.AI.run("@cf/cloudflare/clef")`이거나 REST 형태
`POST /client/v4/accounts/{account_id}/ai/run/@cf/cloudflare/clef`입니다. 요청 본문은 `model`과
`input`을 담고 `state`와 `questions`가 최상위가 아니라 `input` 안에 들어갑니다. `/v1/systemone`
예제를 복사한 코드가 가장 먼저 깨지는 지점이 이 중첩입니다.

## Cloudflare Clairic, 추출 전용

- source_url: https://developers.cloudflare.com/ai/models/@cf/cloudflare/clairic/
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: 질문에 답하는 대신 타입 필드를 돌려주는 System One 계열 모델입니다. 결정 경로가 아니라
  추출 경로이고 프리뷰입니다.

| 항목 | 값 |
| --- | --- |
| 모델 | `@cf/cloudflare/clairic`, 65,536 컨텍스트 |
| 필드 타입 | `text`, `number`, `date`, `time`, `datetime`, `duration`, `list`, `estimate`, `forecast` |
| 요청 | 문서화된 상한이 없는 `fields` 맵과 `reference_date` |
| 응답 필드 | `value`, `guess`, `span` 또는 `spans`, `p_null`, `confidence`, `source`, 그리고 분포 키(`mean`, `median`, `p10`, `p90`, `p_below`, `p_above`, `quantiles`, `steps`) |
| 입력 | 텍스트와 PNG·JPEG·WebP 이미지 최대 4개 |
| 그 밖의 한도 | 8,192 토큰 패스 |
| 가격 | 입력 100만 토큰당 `$0.10` |
| 상태 | 프리뷰 |

결정 모양 설계가 원하는 필드가 `p_null`입니다. 그 필드가 없을 확률이고, 추출이 거절에 가장 가까이
가는 값입니다. 추출을 "있음/없음" choice로 모델링하면 값과 그 분포를 잃으므로, 생성 산출물에서 두
경로를 분리합니다.

## Parallel Decisions

- source_url: https://docs.parallel.ai/decisions/question-types,
  https://docs.parallel.ai/getting-started/pricing
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: 답하기 전에 웹 근거를 검색하고 요청 단위로 인용을 돌려주는 결정 API입니다. 토큰이 아니라
  요청으로 과금하는 유일한 벤더입니다.

| 항목 | 값 |
| --- | --- |
| 엔드포인트 | `POST https://api.parallel.ai/v1/decisions` |
| 인증 | `x-api-key: <key>` |
| 모델 선택 | `model` 대신 기본값 `fast`인 `mode` 필드 |
| 질문 유형 | `noul`, criteria 키 2~255개의 `choice`, 단계 2~10개의 `score` |
| 요청당 질문 | 1~100 |
| 입력 | state를 포함해 질문 하나당 최대 32,000 입력 토큰 |
| 응답 필드 | `noul` 0~1, `probabilities`가 붙은 `choice`, `legend`와 `probabilities`가 붙은 `score`, 그리고 `refusal`과 요청 단위 `citations[]` |
| 이미지 | 없음, `400`으로 거부 |
| 가격 | 요청 1,000건당 `$1`, 요청마다 질문 100개까지 |
| 상태 | 정식 출시 |

이 벤더의 응답 타입 표에는 다른 모든 벤더와 달리 `confidence` 필드가 없습니다. `citations`는 요청
단위입니다. 배열이 "호출 전체의 출처를 담고, 개별 답에 출처를 매핑하지 않는다"고 적혀 있습니다. 생성
산출물이 답마다 인용이 있는 것처럼 그리면 안 됩니다.

요청 단위 가격이 보통의 비용 모델을 뒤집습니다. 한 요청에 질문 100개를 넣어도 하나를 넣은 것과
같은 값이라, 묶어 보내는 것이 이 경로의 경제적 근거 전부입니다.

## Baseten 결정 모델

- source_url: https://docs.baseten.co/inference/model-apis/decision-models
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: Baseten이 작은 결정 모델들을 System One API 뒤에 호스팅하고, 크기 셋에 가격 셋을 붙입니다.

| 항목 | 값 |
| --- | --- |
| 엔드포인트 | `POST https://inference.baseten.co/v1/systemone` |
| 모델 | `joey-1`(2B), `elephant-1`(9B), `mammoth-1`(27B, Qwen3.5-27B 튠) |
| 컨텍스트 | 16,384 토큰 |
| 질문 유형 | `noul`, `choice`, `score` |
| 가격 | 입력 100만 토큰당 각각 `$0.01`, `$0.035`, `$0.10` |
| 상태 | 제공 중, 게이트웨이 등장 2026-10-21, 2026-10-27까지 무료 주간 |

모델 카드는 "한 번의 순전파로 답의 확률과 신뢰도를 돌려준다"고 광고하고, 집계 사이트는 이 모델들에
이미지 16개까지를 적습니다. 게이트웨이 카드는 이미지를 말하지 않으므로 이미지 지원은 경로마다 다르고
직접 경로에서는 확인되지 않았습니다.

## Upstage Solar Decide

- source_url: https://developers.upstage.ai/docs/models/solar-decide.md
- last_verified_at: 2026-11-08
- volatility: volatile
- grade: `B`, 아래 참조
- summary: System One 엔드포인트로 서빙하는 베타 결정 모델입니다. 이 파일에서 숫자가 출처마다 맞지
  않는 유일한 항목이고, 그래서 경로 참조가 이 경로를 미검증으로 적습니다.

| 항목 | 값 | 충돌 |
| --- | --- | --- |
| 상태 | 베타 | 없음 |
| 스키마 | "Jev와 같은 /v1/systemone 스키마를 쓴다" | 필드 목록, 응답 스키마, 한도 표가 없음 |
| 컨텍스트 | 한 출처는 512K, 다른 출처는 524K | 미해결 |
| 가격 | 한 출처는 입력 100만 토큰당 `$0.05`, 다른 출처는 `$0.1` | 미해결 |
| 출시 | 모델 페이지는 2026-09-22, 집계 페이지는 2026-09-28 | 미해결 |
| 질문 유형 | `noul`, `choice`, `score` | 없음 |
| 입력 | 텍스트만 | 없음 |

`B` 등급인 이유는 1차 페이지가 호환성과 상태만 적고 요청 필드, 응답 필드, 한도를 하나도 밝히지
않기 때문입니다. 생성 산출물은 이 경로를 이름으로 들고 베타라고 말할 수 있습니다. 한도나 가격을
적을 수는 없고, 호출 코드를 만들 수도 없습니다.

## Vercel AI SDK 제공자 지원 범위

- source_url: https://ai-sdk.dev/docs/ai-sdk-core/decisions, 그리고 패키지별 소스
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: 제공자 패키지 일곱이 결정 인터페이스를 구현합니다. 넷은 네이티브, 둘은 구조화 출력 위
  흉내, 하나는 게이트웨이 프록시입니다.

| 패키지 | 팩토리 | 와이어 엔드포인트 | 종류 | 질문 유형 | 확률 | 신뢰도 위치 |
| --- | --- | --- | --- | --- | --- | --- |
| `@ai-sdk/typesafe-ai` 3.0.34 | `typeSafeAi.decisionModel(id)` | `POST {baseURL}/systemone`, 이미지가 있으면 멀티파트 | 네이티브 | 넷 모두, `boolean`은 `noul`로, `box`는 그대로 매핑 | choice와 score의 네이티브 `probabilities` | `typesafe.confidence[questionId]`와 `typesafe.legend[questionId]` |
| `@ai-sdk/openai` 4.0.110 | `openai.decisionModel('gpt-6-luna')` | `POST {baseURL}/v1/decisions` | 네이티브 | choice, score, `predicate`로 매핑한 boolean | `probabilities` 레코드, 소수 둘째 자리 반올림 | `openai.confidence[questionId]` |
| `@ai-sdk/perplexity` 5.0.27 | `perplexity.decisionModel(id)` | `POST {baseURL}/v1/decisions` | 네이티브 | choice, score, `noul`로 매핑한 boolean, box 미지원 | "반올림도 정규화도 없는" 네이티브 분포 | `perplexity.confidence`와 `perplexity.legend` |
| `@ai-sdk/parallel` 3.0.3 | `parallel.decisionModel('fast')` | `POST {baseURL}/decisions`, 본문 키가 `mode` | 네이티브, 웹 근거 | choice, score, `noul`로 매핑한 boolean, 파일과 box 없음 | 네이티브 `probabilities`, score는 0부터 시작하는 가중 평균 | `parallel.confidence`, `parallel.legend`, 그리고 `citations` |
| `@ai-sdk/anthropic` 4.0.98 | `anthropic.decisionModel(id)` | Messages API와 구조화 출력, JSON 도구 대체 경로 | 흉내 | choice, score, boolean | 언제나 없음 | 없음 |
| `@ai-sdk/google` 4.0.113 | `google.decisionModel(id)` | Gemini `generationConfig.responseJsonSchema` | 흉내 | choice, score, boolean | 언제나 없음 | 없음 |
| `@ai-sdk/gateway` 4.0.137 | `gateway.decisionModel(id)` | `POST {baseURL}/decision-model`, `ai-decision-model-specification-version: 4`와 `ai-model-id` 헤더 | 프록시 | choice, score, boolean, box는 클라이언트에서 거부 | 라우팅된 모델이 주는 그대로 | 제공자가 정의한 블롭을 그대로 전달 |

공용 흉내 어댑터는 `@ai-sdk/provider-utils`에 있고, 선택지 라벨 하나, 점수 숫자 하나, boolean에는
프롬프트로 받은 P(true)를 돌려주며 `probabilities` 키를 아예 만들지 않습니다. 모델 변덕이 아니라
구조상의 차이입니다. Anthropic과 Google에서 `answer.probabilities?.[answer.choice]`가 `undefined`인
것은 설계입니다.

모든 제공자에 적용되는 핵심 동작:

| 동작 | 세부 |
| --- | --- |
| 진입점 | `experimental_decide`, `experimental_evaluate`는 폐기 별칭 |
| 제공자 계약 | `Experimental_DecisionModelV4`, `specificationVersion: 'v4'`, `doDecide`, 안정 제공자 계약과 분리돼 있고 패치 릴리스에서 바뀔 수 있음 |
| 검증 | 분포를 답과 대조해 맞지 않으면 정규화하지 않고 거부, 기본 절대 허용 오차 `0.000001`, `rounding` 선언은 반올림된 값마다 마지막 자리 반 단위를 허용 |
| 거절 | 거절 응답은 `Experimental_DecisionRefusalError`를 던짐, 부분 결과 없음 |
| 보정 | "SDK는 제공자 사이의 보정을 약속하지 않는다" |
| 로그 확률 | SDK의 공개 결정 타입에 `logprob` 심볼이 없어 그 경로로 흉내 낼 수 없음 |
| 미지원 옵션 | `reasoning`과 `maxOutputTokens`는 어디서나 받지만 네이티브 제공자는 거의 다 `unsupported` 경고를 냄 |

Baseten, Liquid, Microsoft-Decision-1, ScaleDown에는 어떤 제공자 패키지도 결정 팩토리를 내지
않습니다. 게이트웨이 카탈로그가 그중 여럿으로 라우팅하는데도 그렇습니다. 그런 호출이 필요하면
`POST /systemone`을 구현한 base URL을 붙인 TypeSafe 제공자가 유일하게 문서화된 길이고, 그 벤더들의
페이로드를 받는지는 확인되지 않았습니다.

## Vercel AI Gateway 결정

- source_url: https://vercel.com/docs/ai-gateway/modalities/decision,
  https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: 게이트웨이가 네이티브와 흉내 모델 앞에 하나의 계약을 두고, 결정 표면을 둘 노출하며, 다른
  경로에는 없는 신뢰도 기반 폴백을 더합니다.

표면 둘:

| 표면 | 경로 | 방언 | 비고 |
| --- | --- | --- | --- |
| OpenAI 호환 | `POST https://ai-gateway.vercel.sh/v1/decisions` | OpenAI Decisions | `predicate`, 1~255개의 `choice`, 2~10단계의 `score`, GET은 405 |
| TypeSafe 호환 | base URL `https://ai-gateway.vercel.sh/typesafe`, `POST /typesafe/v1/systemone`, `GET /typesafe/v1/models` | System One | TypeSafe SDK에서 base URL만 바꿈, 응답에 `provider_metadata.gateway`가 더 붙음 |

결정 폴백은 자료 전체에서 유일한 결정 전용 승격 장치입니다.

| 측면 | 계약 |
| --- | --- |
| 항목 모양 | 문자열은 실행 오류 폴백, `{ model, when }`은 성공한 1차 답이 `when`에 맞을 때 재실행 |
| 조건 | Choice와 Score에는 `{ question, confidenceBelow }`, Boolean과 Noul에는 `{ question, probabilityBetween: [lo, hi] }`(양끝 포함), 질문 없는 형태는 해당 유형의 모든 질문을 검사 |
| 조합자 | `any`, `all`, `atLeast: { count, conditions }` |
| 구조 규칙 | 조건 객체가 첫 항목이어야 하고 `models`는 하나만 담을 수 있음, `question`은 1~256자이고 요청의 질문 이름이어야 함, 임계값은 `[0, 1]`의 유한수에 `lo <= hi`, 조합자마다 조건 1~20개, 중첩 최대 5, 결정 요청만 받고 아니면 과금 전에 `400`, 조건 모델은 1차와 달라야 함, 요청당 폴백 단계 하나 |
| 표시값 | 언어 모델이 답하면 TypeSafe 호환 표면은 `confidence: 0`과 `probabilities: {}`를 사용 불가 표시로 돌려주고, `/v1/decisions`는 `confidence`와 `probabilities`를 뺌, Noul은 표시값을 쓰지 않음 |
| 발동 사유 | `confidence_below`, `confidence_unavailable`, `probability_between`, `refused` |
| 헤더 | `x-ai-gateway-decision-fallback-{triggered, final-model, primary-model, triggering-questions, triggering-questions-truncated}`, 폐기 예정인 `x-ai-gateway-evaluation-fallback-*`도 함께 전송 |
| 과금 | 폴백이 걸리면 1차와 폴백 두 단계를 모두 과금, 답을 합치지 않음, 성공한 결정 단계는 최대 둘, 조건에 맞았지만 실패한 폴백은 폴백의 오류를 돌려주고 1차는 여전히 과금 |

카탈로그 특이점: `GET https://ai-gateway.vercel.sh/v1/models`가 결정 항목 15개를 모두
`"type": "evaluation"`으로 표기하는데, 문서 페이지와 UI 필터, SDK는 결정이라고 부릅니다.
`type == "decision"`으로 거르면 아무것도 안 나오고, `evaluation`이나 모델 아이디로 걸러야 합니다.
Vercel 자기 API에 관한 Vercel 쪽 사실이고, 생성 산출물이 박아 둘 성질은 아닙니다.

SDK의 `GatewayDecisionModelId` 유니온은 그 15개 중 14개만 담고 `parallel/parallel-decisions-fast`를
빼놓습니다. 유니온이 `(string & {})`로 끝나므로 자동완성 공백이고 실행 차단은 아닙니다.

## OpenRouter 결정과 추출

- source_url: https://openrouter.ai/docs/guides/community/jev,
  https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request,
  https://openrouter.ai/docs/guides/community/extractions
- last_verified_at: 2026-11-08
- volatility: volatile
- summary: 15개 이상 벤더 앞에 선 집계자이고, 봉투 모양은 같지만 내용이 다른 알파 경로가 둘입니다.
  결정은 `questions`, 추출은 `fields`입니다.

| 측면 | 결정 | 추출 |
| --- | --- | --- |
| 경로 | `POST https://openrouter.ai/api/alpha/decisions`, 그리고 `POST /api/v1/systemone` | `POST https://openrouter.ai/api/alpha/extractions` |
| 내용 | `noul`, criteria 맵을 쓰는 `choice`, 배열을 쓰는 `score`, `box` | `fields`의 타입은 `text`, `number`, `date`, `time`, `datetime`, `duration`, `list`, `estimate`, `forecast`, `reference_date`와 기본 0.5인 `null_threshold` |
| 응답 필드 | 선택적인 `confidence`가 붙는 `noul`, `probabilities`와 `confidence`가 붙는 `choice`, `legend`·`probabilities`·`confidence`가 붙는 `score`, `confidence`가 붙는 `box`, 사용량에 `cost` | `value`, `guess`, `span`, `p_null`, `confidence`, `source`, `spell_confidence`, 추정에는 분포 키 |
| 입력 | `state`는 문자열·객체·배열, `image_url`·`input_audio`·`video_url` 파트, 어댑터가 푸는 `assets` 맵 | 텍스트 state만, 이미지와 PDF는 `assets`로 |
| 상태 | 알파, "모양이 바뀔 수 있음" | 알파, 읽은 시점 모델 넷 |
| 가격 | 제공자 가격 통과와 OpenRouter 수수료, `usage.cost` 반환 | 통과 |

벤더 자기 페이지의 단단한 규칙이 둘입니다. Box는 "TypeSafe Jev 엔드포인트만 서빙하고 다른 제공자는
업스트림으로 보내기 전에 `400`으로 거부"합니다. 그리고 엔드포인트가 서빙할 수 없는 요청은 `400`으로
실패합니다. 어느 질문 유형과 미디어 파트, 자산 참조를 받는지가 제공자에 달려 있고, 어댑터 표가
벤더마다 다르며 모델에 따라 이미지 상한이 4, 8, 16, 128로 갈립니다.

두 경로 사이를 옮기는 것은 키 이름 변경이 아닙니다. 벤더는 "질문을 필드로 다시 쓰고 키 이름도 바꿔야
한다"고 적습니다. 추출 산출물과 결정 산출물을 분리합니다.

`output_modalities=decisions`의 36개 항목은 별칭과 무료 등급을 포함한 집계 값이라 벤더 수가 아닙니다.
`B` 등급이고 생성 산출물에 넣을 사실이 아닙니다.

결정 API가 아닌 것이 하나 있습니다. Jev 라우팅 표면(`typesafe/jev-router`)은 채팅 모델과 추론 강도를
고르고 텍스트를 돌려줍니다. 그것을 결정 엔드포인트로 다루는 설계는 틀렸습니다.

## T3: 범용 모델 위의 흉내

T3 경로는 닫힌 집합을 강제하지만 라벨 단위 확률을 만들지 않습니다. 이 표는 그런 경로를 부르는 요청에
정직하게 답하고, 생성된 임계값으로 흘려보내지 않기 위해 있습니다.

| 벤더 | 닫힌 집합 강제 | 확률 출처 | 주의 |
| --- | --- | --- | --- |
| OpenAI 일반 모델 | `strict: true`인 `json_schema` 구조화 출력, 제약 디코딩 | `top_logprobs` 0~20의 `logprobs`, `logit_bias`는 Chat Completions 전용, Responses는 `include` | GPT-6 Astra는 로그 확률 없음, GPT-5.4와 5.2는 `reasoning.effort: none`에서만, GPT-5·mini·nano는 오류, 열거 상한 1,000개, 라벨 단위 분포 없음 |
| Anthropic | `output_config.format` JSON 스키마 또는 strict 도구 사용, 제약 디코딩 | 없음, Messages API 참조에 `logprob`이 0회 등장 | 열거형 대소문자 보장 없음, 최신 주력 모델에서 강제 `tool_choice`는 400이라 분류기 도구 하나 패턴은 `auto`여야 함, 4.6 이후 prefill 미지원 |
| Google | `response_format` JSON 스키마를 상태 기계로 컴파일, `text/x.enum`은 구형 `generateContent` 전용 | 구형 `generateContent`의 `response_logprobs`, 상위 0~20개 | `responseLogprobs`는 Gemini 3.x에서 폐기 예고, Interactions API에는 로그 확률 필드 없음, 미지원 스키마 제약은 조용히 제거 |
| xAI | `enum`, `const`, `anyOf`를 받는 `response_format.json_schema` | 쓸 수 없음, `logprobs`는 "`grok-4.20` 이후 모델에서 지원하지 않고 설정하면 조용히 무시" | 결정 엔드포인트 없음, `guidelines` 모더레이션은 `decline` 동작만 있고 점수 없음 |
| Groq | 일부 모델의 `strict: true` 제약 디코딩 | 없음, `logprobs`와 `top_logprobs` 모두 "아직 어떤 모델도 지원하지 않음" | `strict`는 일부 모델 전용이고 기본은 best-effort |
| Mistral | `strict: true`를 붙인 `json_object` 또는 `json_schema` `response_format` | OpenAPI의 `logprobs`, `top_logprobs`, `prompt_logprobs` | 토큰 단위이고 라벨 단위가 아님, 분류기 상품은 폐기 |
| Together | 지원 모델의 `response_format` `json_schema` | 토큰별 `logprob`과 `top_logprobs`가 붙은 `logprobs` | 토큰 단위, 분류용 사용은 문서화된 용례일 뿐 계약이 아님 |
| Fireworks | JSON 스키마와 사용자 BNF 문법 모드 | `logprobs`, `--max-logprobs` 기본값 5 | `json_schema`를 쓰면 추론 출력이 꺼짐, `pattern`은 best-effort |
| AWS Bedrock | `outputConfig.textFormat` 또는 `response_format`, JSON Schema Draft 2020-12 부분집합에 24시간 캐시되는 컴파일 문법 | 모델별 로그 확률 | Guardrails 신뢰도는 서수(`NONE`/`LOW`/`MEDIUM`/`HIGH`), LLM 판정은 오프라인 평가 작업이고 엔드포인트가 아님 |

아홉 곳의 공통 실패는 이렇습니다. 호출자는 라벨 집합을 강제할 수 있고 때로 토큰 단위 숫자를 읽을 수
있지만, 한 번의 호출로 라벨마다의 확률을 얻지는 못합니다. 손으로 하려면 라벨마다 생성을 돌려 수열을
비교해야 하고, 그것은 다른 설계이고 훨씬 비쌉니다.

## T4 부록: 고정 분류기, 가드레일, 판정기, 은퇴한 표면

결정 API가 아닙니다. 요청이 이런 이름을 대면 생성된 결정 코드가 아니라 감사나 설계 메모로 가도록
적어 둡니다.

| 표면 | 출력 | 상태 | 결정 API가 아닌 이유 |
| --- | --- | --- | --- |
| OpenAI 모더레이션(`omni-moderation-latest`) | 고정 13개 분류에 대한 0~1 `category_scores`, `categories`, `flagged` | GA, 무료, 이미지 20 MB까지, 인라인 모더레이션 2026-06-04 추가 | 호출자가 라벨 집합을 정할 수 없음 |
| Mistral 모더레이션(`/v1/moderations`, `/v1/chat/moderations`) | `pii`, `jailbreaking` 등을 포함한 9~10개 분류의 `category_scores`와 불리언 `categories` | Moderation 2 GA 2026-03-01, 무료 | 고정 분류 체계, Mistral 분류기 상품은 폐기 |
| Mistral Shieldstral 1.0 | 자연어 정책 질문에 대한 예/아니오 분류 | 2026-08-04 공개 프리뷰 | 정책 프롬프트이고 확률이 없음 |
| Azure AI Content Safety | 0~7 심각도와 분류별 신뢰도 | GA, 프리뷰 기능 일부 2027-04-30 은퇴 | 고정 분류 체계, 심각도는 확률이 아님 |
| Azure OpenAI 콘텐츠 필터 | `prompt_filter_results`와 `content_filter_results`의 `safe`/`low`/`medium`/`high` 분류별 `severity`와 `filtered` | GA | 점수를 매기지 않고 막음, 걸린 프롬프트는 400 |
| Bedrock Guardrails(`ApplyGuardrail`) | `GUARDRAIL_INTERVENED` 또는 `NONE`인 `action`, 필터별 `NONE`/`LOW`/`MEDIUM`/`HIGH` 신뢰도, 문맥 접지의 `score` | GA | 서수 등급을 확률처럼 임계값에 쓸 수 없음 |
| Google `classifyText` / `moderateText` | Google 자기 분류 체계의 분류별 `confidence`, 일부에 심각도 | GA | 고정 분류 체계, 호출자 질문 없음 |
| Hugging Face Inference Providers의 `zero-shot-classification` / `text-classification` | `[{label, score}]`, `candidate_labels`와 `multi_label` | GA | 다중 질문 묶음 없음, 순서 점수 프리미티브 없음, 스키마 없음 |
| 가드 모델: Llama Guard 4, Qwen3Guard, Granite Guardian | `safe`/`unsafe`, `<score>yes</score>`, 3단계 심각도 같은 텍스트 라벨 | 모델 카드 현재 | 파싱해야 하는 텍스트 출력, 닫힌 집합 API 없음 |
| 가드 모델: ShieldGemma | Yes/No 로짓 위 `softmax`로 나온 실제 확률 | 문서 폐기 표시, 최종 수정 2026-01-15 | 이 묶음에서 숫자를 내는 유일한 가드 계열, 자체 호스팅 전용 |
| Prometheus 2 | 네 부분 프롬프트에서 나온 `[RESULT] (1-5)` | 모델 카드 날짜 없음 | 루브릭 점수이고 확률이 아님 |
| 리랭커: Cohere Rerank 5, Voyage, Jina | 문서마다 0~1 `relevance_score` | 현재 | 질문 하나에 대한 문서 집합의 순서 결정이고 호출자 질문 집합에 대한 결정이 아님, Cohere는 이 숫자가 선형이 아니라고 경고 |
| Scorable | 0~1 점수와 근거 | 현재 | 판정 점수이고 질문별 확률이 아님 |
| Contextual LMUnit | 5점 연속 척도 점수, 입력은 7,000 토큰까지 | 현재 | 판정 점수 |
| Galileo(Splunk Agent Observability) | 자기 지표의 True/False 정규화 로그 확률, `answer_options[]`와 `num_judges`를 받는 Decision Scorer | 2026-08-07 개편 이후 현재 | 관측성 제품이고 점수는 그쪽 지표이지 호출자 질문이 아님 |
| 은퇴: Patronus | 없음, "평가 API와 SDK, 평가기, Lynx, GLIDER, Percival이 모두 은퇴" | 은퇴 | 사라짐 |
| 은퇴: Atla Selene | 저장소 2025-07-21 아카이브, "Atla API는 더 이상 살아 있지 않음" | 은퇴 | 사라짐 |
| 은퇴: Cohere classify | `POST /v1/classify`는 v1 스펙에 남아 있고 문서 트리에서 폐기로 분류, 기본 임베드 모델 사용은 2025-01-31 폐기 | 사실상 수명 종료 | 임베드 최근접 분류기이고 LLM 분류기가 아니었음 |
| 은퇴 중: OpenAI Evals와 grader | 라벨 또는 0~1 점수 | 2026-10-31 읽기 전용, 2026-11-30 종료 | 종료 공지이고 경로가 아님 |
| 은퇴 중: Inception Mercury Decide | System One 엔드포인트에서 답마다 보정된 확률 | 배너 "2026년 11월 8일 종료" | 스냅샷 날짜에 수명 종료 |

가드 모델에는 한 문장 정리가 붙습니다. 확인한 다섯 계열 중 하나만 숫자를 돌려주고 넷은 텍스트를
돌려줍니다. 결정 API가 없애려는 실패 모드가 정확히 그것입니다.

## Sources

> Links checked 2026-11-08.

| 주장 | 출처 |
| --- | --- |
| Perplexity 엔드포인트, Bearer 전용 인증, 모델과 별칭, `null` 허용 선택지 1~255, 단계 1~10, `web_grounding` 질문 100, 256K 입력, 32 MiB 본문, 질문당 이미지 8개, 신뢰도 공식, 질문별 state 재과금 | <https://docs.perplexity.ai/docs/decisions/quickstart>, <https://docs.perplexity.ai/api-reference/decisions-post> |
| Perplexity v1.2와 flash 가격, 2026년 10월 출시 | <https://docs.perplexity.ai/docs/resources/changelog> |
| Microsoft-Decision-1 경로, 인증, 배포 이름 규칙, 질문 유형, 텍스트 전용 state, GA 상태, 산문 없음 문장 | <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision> |
| Microsoft-Decision-1의 지역 가용성과 중동·아프리카 제외 | <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability> |
| Foundry의 결정 제품 둘, 셋째 없음 | <https://learn.microsoft.com/api/search?search=Decisions%20API>, <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure> |
| Liquid 엔드포인트, 인증, 호스팅·오픈웨이트 모델 아이디, 한도, 입력 전용 과금, 422 검증 오류 | <https://docs.liquid.ai/api/guides/decisions>, <https://docs.liquid.ai/lfm/models/decision-models> |
| Clef와 Clef Flash의 크기, 컨텍스트, 가격, 질문 1~64, 아이디 규칙, 출력 스키마 | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef/>, <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-flash/> |
| Clef Omni의 오디오·비디오 상한과 컨텍스트 | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-omni/> |
| Clairic의 필드 타입, `p_null`, 분포 키, 한도, 가격, 프리뷰 상태 | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clairic/> |
| Parallel 질문 유형, 질문 1~100, 질문당 32,000 토큰, 이미지 없음, 응답 타입 표 | <https://docs.parallel.ai/decisions/question-types>, <https://docs.parallel.ai/decisions/decisions-quickstart> |
| Parallel 요청 1,000건당 `$1`과 요청당 질문 100개 | <https://docs.parallel.ai/getting-started/pricing> |
| Parallel의 요청 단위 `citations`에 답별 매핑 없음 | <https://docs.parallel.ai/decisions/decisions-quickstart> |
| Baseten의 System One 호스팅, 모델 목록, 16,384 컨텍스트 | <https://docs.baseten.co/inference/model-apis/decision-models> |
| Baseten의 게이트웨이 등장 날짜와 가격대 | <https://vercel.com/changelog/basetens-mammoth-1-and-elephant-1-now-available-on-ai-gateway-for-free> |
| Upstage 베타 표시, `/v1/systemone` 스키마 주장, 문서 버전 날짜 | <https://developers.upstage.ai/docs/models/solar-decide.md> |
| AI SDK 결정 진입점, 제공자 계약, 허용 오차, 거절 동작, 보정 부인 | <https://ai-sdk.dev/docs/ai-sdk-core/decisions>, <https://ai-sdk.dev/docs/reference/ai-sdk-core/decide> |
| 제공자별 네이티브·흉내 구현, 질문 유형 지원, 흉내 어댑터가 분포를 내지 않는 점 | <https://raw.githubusercontent.com/vercel/ai/main/packages/provider-utils/src/decision-language-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/typesafe-ai/src/typesafe-ai-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/openai/src/openai-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/perplexity/src/perplexity-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/parallel/src/parallel-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/gateway/src/gateway-decision-model.ts> |
| 패키지별 한도, Perplexity의 질문 1~128과 Parallel의 이름 패턴 포함 | <https://raw.githubusercontent.com/vercel/ai/main/packages/perplexity/src/perplexity-decision-model.ts>, <https://raw.githubusercontent.com/vercel/ai/main/packages/parallel/src/parallel-decision-model.ts> |
| 다른 제공자 패키지에 결정 팩토리가 없음 | 같은 패키지 소스를 2026-11-08에 패키지별로 grep |
| 게이트웨이의 결정 표면 둘, 평가 모델에서 결정 모델로의 개명, 폐기 별칭 | <https://vercel.com/docs/ai-gateway/modalities/decision>, <https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe> |
| 게이트웨이 OpenAI 호환 결정 한도 | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> |
| 결정 폴백 계약 전부, 표시값, 발동 사유, 헤더, 이중 과금 | <https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks> |
| 신뢰도 기반 폴백 출시 | <https://vercel.com/changelog/confidence-based-decision-fallbacks> |
| 카탈로그 15개가 모두 `evaluation`으로 표기된 점과 Jev 아이디 셋 | <https://ai-gateway.vercel.sh/v1/models> |
| 게이트웨이 결정 모델 유니온이 15개 중 14개를 담는 점 | <https://raw.githubusercontent.com/vercel/ai/main/packages/gateway/src/gateway-decision-model-settings.ts> |
| OpenRouter 결정 경로, 알파 상태, box 제한, 어댑터 차이 | <https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request>, <https://openrouter.ai/docs/guides/community/multimodal-decisions> |
| OpenRouter 추출 경로, 필드 타입, 두 경로 사이 재작성 경고 | <https://openrouter.ai/docs/guides/community/extractions> |
| 결정 카탈로그 36개 항목, 별칭과 무료 등급, 15개 벤더 범위 | <https://openrouter.ai/api/v1/models?output_modalities=decisions> |
| Jev Router가 결정 엔드포인트가 아니라 라우팅 표면이라는 점 | <https://openrouter.ai/docs/guides/routing/routers/jev-router> |
| OpenAI 구조화 출력의 열거 상한과 `top_logprobs` 상한 | <https://developers.openai.com/api/docs/guides/structured-outputs.md>, <https://developers.openai.com/api/reference/resources/chat/index.md> |
| GPT-6 Astra의 로그 확률 부재, GPT-5.4와 5.2의 `reasoning.effort: none` 조건 | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md>, <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4.md> |
| Anthropic 구조화 출력, 강제 `tool_choice` 400, prefill 제거, 로그 확률 부재 | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>, <https://platform.claude.com/docs/en/build-with-claude/tool-use/implement-tool-use>, <https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency>, <https://platform.claude.com/docs/en/api/messages> |
| Gemini 구조화 출력, `text/x.enum`, 로그 확률 0~20 상한, Gemini 3.x의 `responseLogprobs` 폐기 | <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output>, <https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/inference> |
| xAI 스키마 지원, 조용히 무시되는 `logprobs`, 모더레이션 한계 | <https://docs.x.ai/developers/model-capabilities/text/structured-outputs.md>, <https://docs.x.ai/openapi.json>, <https://docs.x.ai/developers/advanced-api-usage/custom-moderation-controls.md> |
| Groq의 `logprobs`·`top_logprobs` 미지원과 제한적 `strict` | <https://console.groq.com/docs/api-reference>, <https://console.groq.com/docs/structured-outputs> |
| Mistral 모더레이션 점수, Shieldstral 프리뷰, 폐기된 분류기 | <https://docs.mistral.ai/studio/safety-moderation>, <https://docs.mistral.ai/models/shieldstral-1-0.md>, <https://docs.mistral.ai/resources/deprecated/finetuning/classifier_factory.md> |
| Together의 `logprobs`, Fireworks의 문법 모드와 `--max-logprobs` 기본값 | <https://docs.together.ai/docs/inference/chat/logprobs>, <https://docs.fireworks.ai/structured-responses/structured-response-formatting> |
| Bedrock 구조화 출력 부분집합, 문법 캐시, 서수 Guardrails 신뢰도 | <https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-independent-api.md>, <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailContentFilter.html> |
| Bedrock의 LLM 판정이 평가 작업이라는 점 | <https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation-judge.md> |
| OpenAI 모더레이션 분류, 무료 등급, 재보정 경고 | <https://developers.openai.com/api/docs/guides/moderation.md> |
| Azure Content Safety의 0~7 심각도와 2027-04-30 프리뷰 기능 은퇴 | <https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview>, <https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/harm-categories> |
| Azure OpenAI 콘텐츠 필터의 심각도 구간과 걸린 프롬프트의 400 | <https://learn.microsoft.com/en-us/azure/foundry-classic/foundry-models/concepts/content-filter> |
| Google `classifyText` 신뢰도와 `moderateText` 심각도 | <https://cloud.google.com/natural-language/docs/reference/rest/v2/ClassificationCategory>, <https://cloud.google.com/natural-language/docs/reference/rest/v2/documents/moderateText> |
| Hugging Face zero-shot·text classification 응답 모양 | <https://raw.githubusercontent.com/huggingface/hub-docs/main/docs/inference-providers/tasks/zero-shot-classification.md> |
| Llama Guard 4의 텍스트 출력, Qwen3Guard의 심각도, Granite Guardian의 `<score>`, ShieldGemma의 softmax 확률, Prometheus의 1~5 척도 | <https://llama.com/docs/model-cards-and-prompt-formats/llama-guard-4/>, <https://huggingface.co/Qwen/Qwen3Guard-Gen-8B/raw/main/README.md>, <https://huggingface.co/ibm-granite/granite-guardian-3.3-8b/raw/main/README.md>, <https://huggingface.co/google/shieldgemma-9b>, <https://huggingface.co/prometheus-eval/prometheus-7b-v2.0/raw/main/README.md> |
| Cohere Rerank의 보정 점수와 비선형 경고 | <https://docs.cohere.com/docs/rerank.md>, <https://docs.cohere.com/reference/rerank.md> |
| Voyage와 Jina 리랭크 출력 모양 | <https://docs.voyageai.com/reference/reranker-api.md>, <https://docs.jina.ai/llms.txt> |
| Scorable의 0~1 점수와 근거, LMUnit의 5점 척도 | <https://docs.scorable.ai/llms-full.txt>, <https://docs.contextual.ai/api-reference/lmunit/lmunit.md> |
| Galileo의 로그 확률 분류, Decision Scorer, Splunk 개편 | <https://docs.galileo.ai/concepts/luna/luna>, <https://docs.galileo.ai/api-reference/data/create-decision-scorer-version>, <https://docs.galileo.ai/> |
| Patronus 은퇴 공지 | <https://docs.patronus.ai/docs/lynx/overview> |
| Atla 저장소 아카이브와 비활성 API | <https://github.com/atla-ai/atla-sdk-python> |
| Cohere classify의 폐기 상태와 기본 임베드 폐기 날짜 | <https://docs.cohere.com/changelog/classify-default-model-deprecation.md> |
| OpenAI Evals의 읽기 전용 날짜와 종료 날짜 | <https://developers.openai.com/api/docs/deprecations> |
| Inception Mercury Decide의 종료 배너 | <https://openrouter.ai/inception/mercury-decide> |

### Evidence grade

Upstage 절만 `B`이고, 그 절 안에 표시했습니다. 1차 페이지가 상태와 스키마 호환성만 적고 요청 필드,
응답 필드, 한도를 공개하지 않으며 숫자가 출처마다 어긋나기 때문입니다. 나머지 벤더 절은 모두
`PRIMARY`입니다.

`SECONDARY`는 쓰는 자리에서 표시한 세 묶음입니다. OpenRouter 카탈로그의 36개 항목과 벤더 범위는 집계
사이트 자기 수치이고, Baseten 이미지 상한은 벤더가 아니라 집계 사이트에서 왔으며, 게이트웨이
카탈로그의 `evaluation` 타입 표기는 결정 API 계약이 아니라 Vercel API에 관한 Vercel 쪽 사실입니다.

이 문서들로 확인되지 않아 일부러 비워 둔 것: 어떤 벤더의 보정 측정값, 어떤 지연 시간 수치,
Microsoft-Decision-1의 선택지와 단계 개수, 그리고 AI SDK 제공자 패키지가 없는 벤더들의 페이로드를
TypeSafe 호환 base URL이 받는지 여부입니다.
