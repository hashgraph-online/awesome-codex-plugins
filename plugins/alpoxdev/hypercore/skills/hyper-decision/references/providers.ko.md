# 결정 API 경로 참조

결정 API는 하나의 공유 입력과 여러 개의 타입 지정 질문을 받아, 생성 텍스트 대신 확률이 붙은 타입
답을 돌려줍니다. 지금은 여러 벤더가 이 계약을 제공하고, 형식은 와이어 방언 둘과 SDK 하나로
나뉩니다. 방언마다 필드 이름, 컨테이너 모양, 신뢰도 값의 위치가 다릅니다. 잘못된 줄을 고르면
요청이 거부되거나, 그 경로가 만들지도 않은 숫자를 임계값으로 읽게 됩니다.

이 파일은 경로 층, 방언 대응표, 경로를 고르는 순서, 그리고 1차 계약이 없어 코드를 만들면 안 되는
경로를 담습니다. 가격, 한도, 모델 아이디, 엔드포인트 세부는 여기가 아니라 `official/` 아래 세
스냅샷에 있습니다.

## Contents

- 갱신 정책
- 경로 층
- 방언 대응표
- 경로 선택 순서
- 미검증 경로
- Sources
- Evidence grade

## 갱신 정책

- last_verified_at: 2026-11-08
- refresh_when:
  - 경로가 엔드포인트, 인증 헤더, 방언, 받는 모델 아이디를 바꿀 때
  - 어느 경로에서든 질문 유형 이름이나 응답 필드가 바뀔 때
  - 경로가 층을 옮길 때, 예를 들어 프리뷰가 정식 출시되거나 경로가 은퇴할 때
  - 미검증 목록의 경로가 1차 요청 계약을 낼 때
  - 새 벤더가 결정 API를 낼 때

이 파일이 30일보다 낡았고 네트워크가 살아 있으면 벤더 문서를 읽기 전용으로 다시 읽습니다.
네트워크가 없으면 값을 짐작하지 말고 스냅샷 날짜를 그대로 밝힙니다.

## 경로 층

층은 생성한 산출물이 무엇을 전제해도 되는지 정합니다. 층은 벤더가 아니라 경로의 성질이고, 한
벤더가 여러 층에 나타날 수 있습니다.

- **T1**은 공유 입력 위의 타입 질문에 답하는 네이티브 결정 엔드포인트입니다.
- **T2**는 T1이나 T3 경로 앞에 선 SDK나 게이트웨이입니다. 자체 보정을 더하지 않습니다.
- **T3**은 범용 언어 모델 위의 흉내입니다. 열거형이 붙은 구조화 출력과, 그 벤더가 아직 돌려주는
  경우에만 토큰 로그 확률을 씁니다.
- **T4**는 고정 분류 체계의 분류기, 가드레일, 판정기입니다. 결정 API가 아니라 부록입니다.

`Status`의 뜻은 이렇습니다. `verified`는 이 스냅샷이 받아 둔 1차 문서가 요청과 응답 계약을 적어
둔 경우이고, `unverified`는 그런 문서가 없는 경우입니다. verified 줄은 코드를 만들어도 되는
근거입니다. unverified 줄은 찾아봐야 할 이름일 뿐입니다.

`Checker route`는 그 줄의 요청 본문을 검사하는 `scripts/check-decision-request.sh`의 `--route`
값이고, 검사기가 그 경로를 모델링하지 않으면 `none`입니다.

### T1: 네이티브 결정 API

| 경로 | 엔드포인트 | 인증 헤더 | 환경변수 | 방언 | 질문 유형 | 확률 출처 | 신뢰도 위치 | 상태(날짜) | 검사기 경로 | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TypeSafe 직접 | `POST https://api.typesafe.ai/v1/systemone` | `Authorization: Bearer <key>` | `TYPESAFE_API_KEY` | System One | `noul`, `choice`, `score`, `box`(Jev 1.14 전용) | `choice.probabilities`, `score.probabilities`, `noul.noul`은 P(true) | choice와 score는 `answers.<id>.confidence`, box는 `null`일 수 있음, noul은 없음 | GA, `jev-1.14.0` 2026-10-14 출시 | `systemone` | verified |
| OpenAI Decisions | OpenAI API의 `POST /v1/decisions`(SDK는 `client.decisions.create`) | `Authorization: Bearer <key>` | `OPENAI_API_KEY` | OpenAI Decisions | `predicate`, `choice`, `score` | `predicate.probability`, `choice.probabilities[]`, `score.probabilities[]`와 확률 가중 `score` | choice와 score는 `answers[].confidence`, predicate는 없음 | GA 2026-10-22, 모델 `gpt-6-luna` 전용 | `openai` | verified |
| Azure OpenAI Decisions | Azure 리소스의 `POST /openai/v1/decisions`(SDK는 `decisions.create`) | `api-key: <key>` 또는 Microsoft Entra ID | 벤더 문서가 변수 이름을 밝히지 않음, 키를 직접 넘김 | OpenAI Decisions | OpenAI와 같음 | OpenAI와 같음 | OpenAI와 같음 | 지역별 배포 중, East US 2 제외, 문서 날짜 2026-11-06 | `openai` | verified |
| Perplexity Decisions | `POST https://api.perplexity.ai/v1/decisions` | `Authorization: Bearer <key>`(`x-api-key`는 401) | `PERPLEXITY_API_KEY`는 프로젝트 관례, 벤더 문서는 변수를 밝히지 않음 | System One | `noul`, `choice`, `score` | `choice.probabilities`, `score.probabilities`, `noul.noul`은 P(yes) | choice와 score는 `answers.<id>.confidence`, 공식 공개 | GA, 변경 이력의 2026년 10월 항목 | `systemone` | verified |
| Microsoft-Decision-1 | `<foundry-endpoint>/providers/microsoft/v1/systemone` | Entra ID bearer 또는 `api-key` | 벤더 문서가 변수 이름을 밝히지 않음 | System One | `noul`, `choice`, `score` | `answers.<id>.probabilities` | `answers.<id>.confidence` | Foundry에서 GA, 문서 날짜 2026-10-07 | `systemone` | verified |
| Liquid AI d1 | `POST https://api.liquid.ai/decisions/v1/systemone` | `Authorization: Bearer liquid_<key>` | 벤더 문서가 변수 이름을 밝히지 않음 | System One | 호스팅은 `noul`, `choice`, `score`, 오픈웨이트는 `box`/`boxes`와 다중 선택 choice 추가 | choice와 score의 `probabilities` | `confidence` | GA(호스팅), 오픈웨이트는 LFM Open License | `systemone` | verified |
| Cloudflare Clef | `POST https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/cloudflare/clef`(또는 `env.AI.run`) | `Authorization: Bearer $CLOUDFLARE_API_TOKEN` | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | System One | `noul`, `choice`, `score` | 질문마다 `probabilities` | choice와 score의 `confidence` | 모델 카드상 GA, 제로 데이터 보존 | `systemone` | verified |
| Parallel Decisions | `POST https://api.parallel.ai/v1/decisions` | `x-api-key: <key>` | 벤더 문서가 변수 이름을 밝히지 않음 | System One, `model` 대신 `mode` | `noul`, `choice`(2~255), `score`(2~10단계) | choice와 score의 `probabilities`, 응답 타입 표에 `confidence` 필드 없음 | 문서화되지 않음, 대신 요청 단위 `citations[]` | GA | `systemone` | verified |
| Baseten 결정 모델 | `POST https://inference.baseten.co/v1/systemone` | `Authorization: Bearer <key>` | 벤더 문서가 변수 이름을 밝히지 않음 | System One | `noul`, `choice`, `score` | `probabilities`와 신뢰도 | `confidence` | 제공 중, 문서 수정 2026-10-29 | `systemone` | verified |
| Upstage Solar Decide | System One 엔드포인트, 벤더 콘솔 문서가 렌더링되지 않았고 요청 명세 URL도 확인되지 않음 | Upstage 키 또는 OpenRouter 경유 | 문서화되지 않음 | System One | `noul`, `choice`, `score` | "모델이 직접 돌려주는 보정된 확률" | 따로 공개되지 않음 | 베타, 문서 버전 날짜 2026-09-22 | `none` | unverified(아래 참조) |
| DigitalOcean(Jev 재판매) | `POST https://inference.do-ai.run/v1/systemone` | `Authorization: Bearer $MODEL_ACCESS_KEY` | `MODEL_ACCESS_KEY`(벤더 예시의 이름) | System One | `noul`, `choice`, `score`, box 없음 | Jev가 주는 `probabilities` | `confidence` | GA 재판매, 문서 최종 확인 2026-09-28, `typesafe-jev-1.13.0` 전용 | `systemone` | 1.13 계약 기준 verified |
| b.ai(Jev 재판매) | `POST https://api.b.ai/v1/decisions` | `Authorization: Bearer <key>` 또는 `x-api-key: <key>` | `BAI_API_KEY`는 프로젝트 관례, 벤더 문서는 변수를 밝히지 않음 | System One | `noul`, `choice`, `score`, box 없음 | `probabilities` | `confidence` | `jev-1.13.0` 또는 `jev-latest` 전용, sitemap에 1.14 없음 | `bai` | verified |

한 줄은 검사기가 무엇을 검사하는지 짚어야 합니다. Cloudflare Workers AI 본문은 `model`과 `input`을
담고 `state`와 `questions`가 `input` 안에 중첩되므로, `systemone` 검사기 경로는 전송 봉투가 아니라 안쪽
페이로드를 검사합니다.

### T2: SDK와 게이트웨이

| 경로 | 엔드포인트 또는 SDK 진입점 | 인증 헤더 | 환경변수 | 방언 | 질문 유형 | 확률 출처 | 신뢰도 위치 | 상태(날짜) | 검사기 경로 | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Vercel AI SDK | `experimental_decide({ model, state, questions })`, `Experimental_DecisionModelV4`와 `doDecide` | 제공자 패키지마다 다름 | TypeSafe 제공자는 `TYPESAFE_AI_API_KEY`, OpenAI 제공자는 `OPENAI_API_KEY` | AI SDK | `boolean`, `choice`, `score`, `box`, 모델마다 지원이 다름 | 네이티브 제공자는 `probabilities`를 그대로 넘기고, Anthropic·Google 어댑터는 돌려주지 않음 | `providerMetadata.<provider>.confidence[questionId]`, TypeSafe는 `.legend`도 | 실험적, 2026-11-06 기준 `ai@7.0.164` | `aisdk` | verified |
| Vercel AI Gateway, OpenAI 호환 결정 | `POST https://ai-gateway.vercel.sh/v1/decisions`, `gateway.decisionModel('<vendor>/<model>')` | `Authorization: Bearer $AI_GATEWAY_API_KEY` 또는 Vercel OIDC | `AI_GATEWAY_API_KEY` | OpenAI Decisions | `predicate`, `choice`(1~255), `score`(2~10단계) | 라우팅된 모델이 주는 확률 | `providerMetadata.gateway...`, 언어 모델 폴백은 신뢰도를 주지 않음 | GA 경로, 결정 폴백 문서 2026-10-08 | `openai` | verified |
| Vercel AI Gateway, TypeSafe 호환 결정 | `POST https://ai-gateway.vercel.sh/typesafe/v1/systemone`, `GET /typesafe/v1/models` | `Authorization: Bearer $AI_GATEWAY_API_KEY` | `AI_GATEWAY_API_KEY` | System One | TypeSafe 엔드포인트에서 `noul`, `choice`, `score`, `box` | 라우팅된 모델이 주는 확률 | `confidence`, 언어 모델이 답하면 사용 불가 표시로 `0`과 `probabilities: {}` | GA 경로, 같은 폴백 계약 | `systemone` | verified |
| OpenRouter decisions(알파) | `POST https://openrouter.ai/api/alpha/decisions` | `Authorization: Bearer $OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | `assets`가 붙은 System One 봉투 | `noul`, `choice`, `score`, `box`는 TypeSafe 엔드포인트에서만, 다른 제공자는 `400`으로 거부 | 라우팅된 모델이 주는 확률 | 라우팅된 모델이 주면 `confidence` | 알파, "모양이 바뀔 수 있음" | `systemone` | 알파로 verified |
| OpenRouter System One | `POST https://openrouter.ai/api/v1/systemone` | `Authorization: Bearer $OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | System One | TypeSafe 엔드포인트에서 `noul`, `choice`, `score`, `box` | 라우팅된 모델이 주는 확률 | `confidence` | 운영 중, TypeSafe SDK의 `base_url`과 `~typesafe/jev-latest`로 호출 | `systemone` | verified |
| OpenRouter 추출(알파) | `POST https://openrouter.ai/api/alpha/extractions` | `Authorization: Bearer $OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | 추출 `fields` | 없음, 타입 필드(`text`, `number`, `date`, `time`, `datetime`, `duration`, `list`, `estimate`, `forecast`) | 필드마다 `confidence`, `p_null` | 필드마다 | 알파 | `none` | 알파로 verified |

### T3: 범용 언어 모델 위의 흉내

| 경로 | 진입점 | 방언 | 강제할 수 있는 질문 유형 | 확률 출처 | 주의 | 검사기 경로 | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI 일반 모델 | Responses 또는 Chat Completions의 `json_schema` strict와, 모델이 허용할 때의 logprobs | 구조화 출력과 토큰 로그 확률 | `boolean`, `choice`, `score`를 JSON 스키마 열거형이나 순서 숫자로 | 문서화된 곳에서만 토큰 로그 확률, `top_logprobs` 상한 20 | 라벨 단위 확률 없음, GPT-6 Astra는 로그 확률 자체가 없음 | `none` | verified |
| Anthropic | Messages API의 `output_config.format` JSON 스키마 또는 strict 도구 사용 | 구조화 출력 | `boolean`, `choice`, `score` | 없음, Messages API에 로그 확률 없음 | 최신 주력 모델에서 강제 `tool_choice`는 400 | `none` | verified |
| Google | `response_format` JSON 스키마 또는 구형 `generateContent` 로그 확률 | 구조화 출력 | `boolean`, `choice`, `score` | 구형 `generateContent` 로그 확률, Gemini 3.x에서 폐기 예고 | Interactions API에는 없음 | `none` | verified |
| xAI | `response_format.json_schema` | 구조화 출력 | `boolean`, `choice`, `score` | 쓸 수 없음, `grok-4.20` 이후 `logprobs`는 조용히 무시됨 | 결정 엔드포인트 없음 | `none` | verified |
| Groq | 일부 모델의 `strict: true` 제약 디코딩 | 구조화 출력 | `boolean`, `choice`, `score` | 없음, 모든 모델에서 `logprobs`와 `top_logprobs` 미지원 | 기본은 best-effort 스키마 | `none` | verified |
| Mistral | `response_format` JSON 스키마 | 구조화 출력 | `boolean`, `choice`, `score` | `logprobs`, `top_logprobs`, `prompt_logprobs` | 토큰 단위, 라벨 단위 아님 | `none` | verified |
| Together | `response_format` `json_schema` | 구조화 출력 | `boolean`, `choice`, `score` | `logprobs`와 `top_logprobs` | 토큰 단위 | `none` | verified |
| Fireworks | JSON 스키마 또는 BNF 문법 모드 | 구조화 출력 | `boolean`, `choice`, `score` | `logprobs`, `--max-logprobs` 기본 5 | `json_schema`를 쓰면 추론 출력이 꺼짐 | `none` | verified |
| Bedrock | `outputConfig.textFormat` 또는 `response_format`의 JSON Schema 부분집합 | 구조화 출력 | `boolean`, `choice`, `score` | 모델별 로그 확률 | Guardrails 신뢰도는 서수 등급 | `none` | verified |

호출자가 임계값을 걸 확률을 필요로 할 때 T3 경로는 답이 아닙니다. 분포를 돌려주지 않고, 프롬프트로
받은 자기 추정은 보정된 확률이 아닙니다.

### T4: 고정 분류 체계의 분류기, 가드레일, 판정기

결정 API가 아닙니다. 요청이 이런 이름을 대면 인식해서, 생성된 결정 코드가 아니라 감사나 설계
메모로 보내기 위해 적어 둡니다. 세부는 `official/decision-providers.md`의 부록 표에 있습니다.

| 경로 | 돌려주는 것 | 결정 경로가 아닌 이유 |
| --- | --- | --- |
| OpenAI, Mistral 모더레이션 | 고정 분류 목록에 대한 0~1 `category_scores` | 호출자가 라벨 집합을 정할 수 없음 |
| Azure Content Safety, Bedrock Guardrails | 심각도 구간 또는 `NONE`/`LOW`/`MEDIUM`/`HIGH` | 서수 등급을 확률처럼 임계값에 쓸 수 없음 |
| Google `classifyText`, `moderateText` | 고정 분류 체계에 대한 신뢰도 | 체계가 고정이고 호출자 질문이 없음 |
| Scorable, Contextual LMUnit, Galileo | 0~1 점수 또는 5점 척도와 근거 | 질문별 확률이 아니라 판정 점수 |
| 은퇴: Patronus, Atla Selene, Cohere classify, OpenAI Evals와 grader, Inception Mercury Decide | 지속되는 것 없음 | 은퇴했거나 은퇴 중, 날짜는 부록 참조 |

## 방언 대응표

검증된 모든 줄을 세 가지 와이어 모양이 덮습니다. 왼쪽의 중립 이름이 생성 산출물이 생각해야 하는
개념이고, 각 열이 실제로 와이어에 나가는 모양입니다.

| 개념 | System One 방언 | OpenAI Decisions 방언 | AI SDK |
| --- | --- | --- | --- |
| 공유 입력 키 | `state`(문자열, 객체, 배열) | `input`(문자열, 또는 메시지와 도구 호출을 포함한 입력 항목 배열) | `state`(문자열, JSON 객체, 콘텐츠 파트 배열) |
| 질문 컨테이너 | `questions`는 아이디를 키로 하는 맵 | `questions`는 배열이고 각 항목이 고유한 `name`을 가짐 | `questions`는 아이디를 키로 하는 맵 |
| 예/아니오 유형 | `noul` | `predicate` | `boolean` |
| 예/아니오 응답 | `noul`, 0~1 숫자, 신뢰도 없음 | `probability`, 0~1 숫자 | `probability`, 필수 |
| 선택지 | `criteria`는 선택지와 설명의 맵, 1~255개 | `choices`는 `{ value, description }` 배열, 2~255개 | `criteria` 맵 또는 제공자의 네이티브 모양 |
| 선택 응답 | `choice`, `probabilities`, `confidence` | `choice`, `probabilities[]`, `confidence` | 네이티브면 `choice`, `probabilities` |
| 점수 단계 | `criteria`는 단계 설명의 순서 배열, 스키마 1~10, 산문은 2개 이상 | `levels`는 `{ label, description }` 배열, 2~10 | `criteria` 순서 배열 |
| 점수 응답 | `score`(확률 가중 평균), `legend`, `probabilities`, `confidence` | `score`, `probabilities[]`, `confidence` | 네이티브면 `score`, `legend` |
| 박스 | `box`의 `top`, `bottom`, `left`, `right`는 0~1 비율, `confidence` 포함, Jev 1.14 전용 | 미지원 | 스펙에는 `box`가 있고 TypeSafe 제공자만 구현 |
| 거절 | 별도 응답 유형 없음 | 질문마다 네 번째 응답 유형 | SDK가 `Experimental_DecisionRefusalError`를 던짐 |
| 신뢰도 위치 | `answers.<id>.confidence` | `answers[].confidence` | `providerMetadata.<provider>.confidence[questionId]` |
| 분포 | choice와 score에 항상 있음 | choice와 score에 항상 있음 | 선택적, Anthropic·Google 어댑터는 구조상 없음 |

대응표에서 따라 나오고 실무에서 걸리는 규칙은 이렇습니다.

- 거절은 부정 답이 아닙니다. `probability: 0`이나 첫 선택지, 점수 0으로 바꾸지 않습니다.
- `noul`, `predicate`, `boolean`은 모두 P(true) 스칼라 하나를 담습니다. 어느 벤더도 그 숫자를
  신뢰도라고 부르지 않습니다.
- `confidence`는 벤더별 값이고 이식되지 않습니다. TypeSafe, Perplexity, AI SDK의 제공자 메타데이터만
  이 값을 담고, 계산 방식도 서로 다릅니다.
- `box`는 호스팅 경로에서 TypeSafe Jev 1.14 전용입니다. Liquid 오픈웨이트에는 `box`가 붙지만,
  호스팅 d1 경로는 `noul`/`choice`/`score`만 문서화합니다.
- `state`로 JSON 배열을 보내면 AI SDK는 콘텐츠 파트 목록으로 읽습니다. 레코드는 객체나 타입이 붙은
  파트로 감쌉니다.

## 경로 선택 순서

저장소에 이미 있는 것에서 시작합니다. 처음 맞는 규칙을 고르고, 산출물을 넘길 때 어느 경로를 왜
골랐는지 밝힙니다.

1. **이미 있는 의존성이 정합니다.** 프로젝트가 이미 `ai` 패키지에 의존하고, 이 파일의 경로 중 하나가
   그 패키지에 결정 제공자를 이미 공급한다면 AI SDK 경로를 씁니다. 패키지가 설치돼 있고 프로젝트의
   다른 모델 호출이 이미 그 패키지를 지나기 때문에 의존성이 정합니다.
2. **OpenAI 의존성과 기존 OpenAI 사용이 정합니다.** 프로젝트가 이미 `openai` 패키지에 의존하고 지금
   OpenAI를 호출한다면 OpenAI Decisions를 씁니다. `OPENAI_API_KEY`를 이미 들고 있는 클라이언트에
   메서드 하나를 더하는 비용이면 끝납니다.
3. **TypeSafe 의존성이 정합니다.** 프로젝트가 `@typesafe-ai/sdk`나 `typesafe-sdk`에 의존하거나 코드와
   설정에 `api.typesafe.ai`가 있다면 TypeSafe 직접 경로를 씁니다.
4. **그 밖에는 밝힌 제약으로 고릅니다.** 저장소에서 정할 근거가 없다면 호출자가 무엇을 필요로 하는지
   묻고 한 경로를 권합니다. 분포, 박스 출력, 가장 넓은 질문 유형 집합이 필요하면 TypeSafe 직접,
   프로젝트가 이미 OpenAI 모양이거나 Azure 배포가 배포 경로라면 OpenAI Decisions입니다. 이유를 한
   문장으로 밝힙니다.
5. **T3로 조용히 내려가지 않습니다.** 호출자가 행동에 쓸 확률을 필요로 할 때 T3 경로는 선택지가
   아닙니다. 분포를 돌려주지 않는다고 말하고 T1 경로나 검토 경로를 대신 제안합니다.

환경변수 이름이 설정돼 있는 것은 프로젝트 파일보다 약한 근거입니다. 키 이름이 증명하는 것은 그
기계의 상태이지 이 저장소의 상태가 아닙니다. 잠금 파일, 설정, 기존 클라이언트 코드, 환경변수 예시처럼
프로젝트 자체 파일이 다른 경로를 대면 그 경로가 이기고, 둘이 어긋날 때는 어느 경로를 왜 골랐는지
밝힙니다.

키가 있다는 것도, 신뢰도가 높다는 것도 실제 호출을 승인하지 않습니다. 첫 실제 요청 전에 묻고,
비용을 밝히고, 질문에 답하는 최소 횟수로 호출을 줄입니다.

## 미검증 경로

이 경로들은 결정 모델을 판매하거나 중계하거나 앞에 서지만, 이 스냅샷에는 코드를 만들 만큼 온전한
1차 요청 계약이 없습니다. 요청이 이 이름을 대면 알아보기 위해 적어 두는 것이지 코드를 만들기 위한
것이 아닙니다.

- **Netlify AI Gateway.** 문서는 TypeSafe SDK가 `TYPESAFE_API_KEY`와 `TYPESAFE_BASE_URL`을 읽는다는 점과
  Jev 모델 아이디 네 개를 적지만, 주입을 설명할 뿐 자체 요청 계약은 없습니다. TypeSafe SDK 위의 배포
  편의로 보고, 쓰기 전에 주입되는 base URL을 확인합니다.
- **AI/ML API.** 한 벤더 모델 페이지가 `POST https://api.aimlapi.com/v1/decisions`와
  `typesafe/jev-1.14`를 광고하고, 생성된 스키마 페이지는 점수 하한에서 TypeSafe 스키마와 어긋납니다.
  레인들이 하나의 계약에 합의하지 못했으므로 코드를 만들지 않습니다.
- **Upstage Solar Decide 요청 명세.** 모델은 실재하고 페이지도 1차 문서지만, 같은 `/v1/systemone`
  스키마를 쓴다는 말과 베타 표시만 있고 필드 목록, 한도 표, 응답 스키마가 없습니다. 공개된 가격
  두 개의 통화도 레인마다 다릅니다.
- **Convai Innovations Laya.** 게이트웨이 모델 카드는 확률이 붙은 타입 답을 설명하지만, 1차 문서를
  찾지 못했고 카드의 제공자 링크는 404입니다.
- **1차 요청 계약이 없는 그 밖의 경로.** 모델 카드, 변경 이력 한 줄, 게이트웨이 목록은 계약이
  아닙니다.

위 항목에는 모두 같은 지시가 붙습니다. 코드를 만들지 않습니다. 벤더 자체 문서를 먼저 읽고
엔드포인트, 인증 헤더, 받는 모델 아이디, 질문 유형 이름, 응답 필드를 확인한 뒤, 그 경로의 verified
줄을 이 파일에 더하고 나서 코드를 만듭니다.

층 표에 아예 없는 경로에도 같은 규칙이 붙습니다. verified 줄이 없으면 코드도 없습니다.

## Sources

> Links checked 2026-11-08.

| 주장 | 출처 |
| --- | --- |
| TypeSafe 직접 엔드포인트, Bearer 헤더, 질문 유형 넷, choice·score·box 응답 필드 | <https://docs.typesafe.ai/api/system-one.md>, <https://api.typesafe.ai/openapi.json> |
| `jev-1.14.0`의 2026-10-14 출시, `jev-1.13.0` 유지, 두 별칭 모두 1.14, Box 요구 조건 | <https://docs.typesafe.ai/models.md>, <https://docs.typesafe.ai/changelog.md> |
| TypeSafe SDK가 읽는 `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL`, `TYPESAFE_LOG_LEVEL` | <https://docs.typesafe.ai/sdk/javascript/api/variables/ENV.md>, <https://docs.typesafe.ai/sdk/python/api/constants.md> |
| OpenAI Decisions 엔드포인트, `gpt-6-luna`, `predicate`/`choice`/`score`, 질문 1~400, 선택지 2~255, 단계 2~10 | <https://developers.openai.com/api/docs/guides/decisions.md>, <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| OpenAI Decisions의 2026-10-06 베타와 2026-10-22 GA | <https://developers.openai.com/api/docs/changelog.md> |
| Azure 엔드포인트, `api-key` 또는 Entra ID, East US 2 제외 | <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| Perplexity 엔드포인트, Bearer 전용 인증, `noul`/`choice`/`score`, 공개된 신뢰도 공식, 선택지 1~255, 단계 1~10, 질문당 이미지 8개 | <https://docs.perplexity.ai/api-reference/decisions-post>, <https://docs.perplexity.ai/docs/decisions/quickstart> |
| Perplexity Decisions의 2026년 10월 출시 | <https://docs.perplexity.ai/docs/resources/changelog> |
| Microsoft-Decision-1의 `<foundry-endpoint>/providers/microsoft/v1/systemone`, 배포 이름을 `model`로 쓰는 규칙, 텍스트·JSON state 전용 | <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision> |
| Liquid의 `POST /decisions/v1/systemone`, TypeSafe System One 구현, 입력 전용 과금, 4.5 MB 본문 한도 | <https://docs.liquid.ai/api/guides/decisions> |
| Liquid의 호스팅 모델과 오픈웨이트의 box·다중 선택 추가 | <https://docs.liquid.ai/lfm/models/decision-models> |
| Clef와 Clef Flash의 모델 크기, 컨텍스트, 가격, 질문 1~64 한도 | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef/>, <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-flash/> |
| Clef Omni의 오디오·비디오 한도 | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clef-omni/> |
| Clairic의 추출 모델 성격과 `fields`, `p_null`, 추정·예측 분포 | <https://developers.cloudflare.com/ai/models/@cf/cloudflare/clairic/> |
| Parallel 엔드포인트, `x-api-key`, 질문 1~100, 선택지 2~255, 단계 2~10, 응답 타입 표, 요청 1,000건당 `$1` | <https://docs.parallel.ai/decisions/question-types>, <https://docs.parallel.ai/getting-started/pricing> |
| Parallel이 이미지를 400으로 거부하는 규칙 | <https://openrouter.ai/docs/guides/community/multimodal-decisions> |
| Baseten이 System One API로 결정 모델을 호스팅한다는 설명과 모델·컨텍스트 목록 | <https://docs.baseten.co/inference/model-apis/decision-models> |
| Upstage의 베타 표시, `/v1/systemone` 스키마 주장, 문서 버전 날짜 | <https://developers.upstage.ai/docs/models/solar-decide.md> |
| DigitalOcean 엔드포인트, `MODEL_ACCESS_KEY`, `typesafe-jev-1.13.0` 단일 아이디 | <https://docs.digitalocean.com/products/inference/how-to/use-system-one-api/> |
| b.ai 엔드포인트, 인증 헤더 둘, 받는 아이디 둘, box 유형 없음 | <https://docs.b.ai/llmservice/api/decisions-api/> |
| `experimental_decide`, `Experimental_DecisionModelV4`, 제공자별 지원 표 | <https://ai-sdk.dev/docs/ai-sdk-core/decisions>, <https://ai-sdk.dev/docs/reference/ai-sdk-core/decide> |
| AI SDK TypeSafe 제공자가 읽는 `TYPESAFE_AI_API_KEY`와 `TYPESAFE_AI_BASE_URL` | <https://ai-sdk.dev/providers/ai-sdk-providers/typesafe-ai> |
| Anthropic·Google 어댑터가 choice·score 분포를 빼는 규칙 | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> |
| 게이트웨이 `/v1/decisions` 경로, `predicate`/`choice`/`score` 유형, 1~255와 2~10 한도 | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> |
| 게이트웨이 `/typesafe/v1/systemone`과 `/typesafe/v1/models` 경로 | <https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe> |
| 결정 폴백, `confidence: 0`과 `probabilities: {}` 사용 불가 표시, 이중 과금 | <https://vercel.com/docs/ai-gateway/models-and-providers/decision-fallbacks> |
| 게이트웨이 카탈로그가 결정 모델을 아직 `"type": "evaluation"`으로 표기하는 사실 | <https://ai-gateway.vercel.sh/v1/models> |
| OpenRouter의 두 결정 표면, 알파 경고, TypeSafe 엔드포인트만 box를 서빙하는 규칙 | <https://openrouter.ai/docs/guides/community/jev>, <https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request> |
| OpenRouter 제공자별 어댑터 차이와 미지원 미디어의 400 | <https://openrouter.ai/docs/guides/community/multimodal-decisions> |
| OpenRouter 추출이 별도 `fields` 경로라는 점 | <https://openrouter.ai/docs/guides/community/extractions> |
| TypeSafe SDK의 OpenRouter base URL과 `~typesafe/jev-latest` 슬러그 | <https://docs.typesafe.ai/sdk/python/usage/basic.md> |
| Netlify가 `TYPESAFE_API_KEY`와 `TYPESAFE_BASE_URL`을 주입하는 사실 | <https://docs.netlify.com/build/ai-gateway/overview/> |
| AI/ML API가 광고하는 엔드포인트와 모델 아이디 | <https://aimlapi.com/models/typesafe-jev-1-14> |
| Laya의 게이트웨이 카드와 1차 문서 부재 | <https://vercel.com/ai-gateway/models/laya> |
| OpenAI 구조화 출력의 열거형 한도와 `top_logprobs` 상한 20 | <https://developers.openai.com/api/docs/guides/structured-outputs.md>, <https://developers.openai.com/api/reference/resources/chat/index.md> |
| GPT-6 Astra의 로그 확률 부재, GPT-5.4·5.2의 `reasoning.effort: none` 조건 | <https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md>, <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.4.md> |
| Anthropic 구조화 출력, 강제 `tool_choice`의 400, 로그 확률 부재 | <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>, <https://platform.claude.com/docs/en/api/messages> |
| Gemini의 열거형 표면, Gemini 3.x의 `responseLogprobs` 폐기 예고, 로그 확률 상한 0~20 | <https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/inference>, <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output> |
| xAI가 `grok-4.20` 이후 `logprobs`를 조용히 무시하는 사실 | <https://docs.x.ai/openapi.json> |
| Groq의 `logprobs`와 `top_logprobs` 미지원 | <https://console.groq.com/docs/api-reference> |
| Mistral 모더레이션 점수와 폐기된 분류기 공장 | <https://docs.mistral.ai/studio/safety-moderation> |
| Together의 `logprobs`, Fireworks의 문법 모드와 `--max-logprobs` 기본 5 | <https://docs.together.ai/docs/inference/chat/logprobs>, <https://docs.fireworks.ai/structured-responses/structured-response-formatting> |
| Bedrock의 구조화 출력 부분집합과 서수 Guardrails 신뢰도 | <https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GuardrailContentFilter.html> |
| 은퇴했거나 은퇴 중인 판정 제품 | <https://docs.patronus.ai/docs/lynx/overview>, <https://developers.openai.com/api/docs/deprecations> |

### Evidence grade

verified 줄은 모두 `PRIMARY`입니다. 각 계약 항목이 위 표에 적은 벤더 문서에서 나왔고 2026-11-08에
받아 두었습니다. 미검증 목록은 `SECONDARY`입니다. 계약이 아니라 경로 배제 경고이고, 각 항목은
목록이나 주입 방식, 일부 명세만 적은 벤더 문서에 기대며 온전한 요청·응답 계약에는 기대지 않습니다.

`B`는 벤더가 아니라 제3자 집계에서 온 사실에 붙습니다. 게이트웨이 카탈로그의 두 사실(`"evaluation"`
타입 표기와 15개 항목)과 OpenRouter 어댑터 표의 이미지 규칙입니다. 쓰는 자리에서 표시했고, 생성
산출물이 이것만 근거로 설 수는 없습니다.

여기서 확인하지 않아 일부러 비워 둔 것: 어느 벤더의 실제 지연 시간, 어떤 보정 주장, 그리고 미검증
경로의 현재 모델 아이디입니다.
