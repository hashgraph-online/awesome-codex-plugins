# Jev 경로 참조

Jev를 부르는 공식 문서 경로는 셋이고, 각각 계약이 다릅니다. 이들을 섞는 것이 요청이 거부되는
가장 빠른 길입니다. 엔드포인트가 다르고, 인증 헤더가 다르고, 예·아니오 질문 유형의 이름이 직접
경로와 Vercel AI SDK 경로에서 서로 다릅니다. 이 파일에 세 경로를 나란히 놓고, 어느 것을 먼저
고를지 정하고, 공식 문서가 없어 코드를 만들면 안 되는 경로를 적습니다.

가격, 한도, 모델 별칭은 여기가 아니라 옆의 플랫폼 스냅샷에 있습니다.

## Contents

- 갱신 정책
- 경로 비교
- 경로 선택 순서
- 미검증 경로
- Sources

## 갱신 정책

- last_verified_at: 2026-10-01
- refresh_when:
  - 경로가 엔드포인트, 인증 헤더, 받는 모델 아이디를 바꿀 때
  - 어느 경로에서든 질문 유형 이름이 바뀔 때
  - 미검증 목록의 경로가 공식 문서를 낼 때
  - Jev를 싣는 새 경로가 생길 때

## 경로 비교

상태의 뜻은 이렇습니다. `verified`는 이 스냅샷이 받아 둔 벤더 문서가 그 경로의 계약을 적어 둔
경우이고, `unverified`는 그런 문서가 없는 경우입니다. verified 줄은 코드를 만들어도 되는
근거가 됩니다. unverified 줄은 찾아봐야 할 이름일 뿐입니다.

| 경로 | 엔드포인트 | 인증 | 모델 아이디 | 질문 유형 | 신뢰도 위치 | 환경변수 | 상태 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TypeSafe 직접 | `POST https://api.typesafe.ai/v1/systemone` | `Authorization: Bearer plus your key` | `jev-latest`, `jev-preview`, `jev-1.13.0` | `noul`, `choice`, `score` | choice와 score는 `answers.<id>.confidence`, noul은 없음 | `TYPESAFE_API_KEY` | verified |
| b.ai | `POST https://api.b.ai/v1/decisions` | `Authorization: Bearer <key>`, 또는 `x-api-key: <key>` | `jev-1.13.0`, `jev-latest`만 | `noul`, `choice`, `score` | choice와 score는 `answers.<id>.confidence`, noul은 없음 | `BAI_API_KEY`(프로젝트 관례 이름이며 벤더가 밝힌 이름이 아닙니다) | verified |
| Vercel AI SDK와 AI Gateway | 직접 엔드포인트가 없습니다. SDK가 모델을 찾고, 문자열 아이디는 기본 provider를 설정하지 않았을 때 Vercel AI Gateway로 갑니다 | Gateway 키를 담은 `AI_GATEWAY_API_KEY`, 또는 Vercel OIDC | 문자열 아이디 `typesafe-ai/jev`, 또는 `typeSafeAi.evaluationModel('jev-latest')` | `boolean`, `choice`, `score` | 질문 아이디별 `result.providerMetadata?.typesafe?.confidence` | `AI_GATEWAY_API_KEY` | verified |

표에 담기 어려운 차이는 이렇습니다.

- 직접 경로 둘에서 예·아니오 유형의 이름은 `noul`입니다. SDK 경로에서는 `boolean`입니다.
  SDK 요청에 `noul`을 쓰거나 직접 요청에 `boolean`을 쓰면 오류입니다.
- b.ai 경로는 모델 아이디를 정확히 둘만 받습니다. 직접 경로는 `jev-preview`도 받습니다.
- b.ai 경로는 POST만 지원하므로 `stream`은 빼거나 `false`로 둡니다. `true`는 그 계약에 없습니다.
- SDK 경로는 실험 단계입니다. 평가 API와 평가 모델 규격이 패치 릴리스에서 바뀔 수 있으므로
  설치된 패키지 버전을 고정하십시오.
- SDK 경로의 `boolean` 답에는 `probability`가 필수이고, choice와 score의 확률 분포는 거기서
  선택입니다. 직접 경로에서는 choice와 score 답마다 `probabilities`가 붙습니다.
- 환경변수 이름을 적어 둔 이유는 코드가 실호출을 제안하기 전에 이름의 존재만 확인할 수 있게
  하기 위해서입니다. 값은 호출 시점에 환경에서 읽고, 출력하거나 로그에 남기거나 파일에 쓰지
  않습니다.

## 경로 선택 순서

맞는 첫 규칙을 고르고, 결과를 건넬 때 어느 경로를 골랐는지 밝힙니다.

1. 저장소가 이미 `ai` 패키지에 의존하면 AI SDK 경로와 `boolean` 질문 유형을 씁니다. 그 패키지가
   이미 설치되어 있고 프로젝트의 다른 모델 호출도 그리로 가기 때문입니다.
2. 아니면 환경에 `BAI_API_KEY`가 있으면(이름만 확인하고 값은 보지 않습니다) b.ai 경로를 씁니다.
   `BAI_API_KEY`는 이 프로젝트가 정한 관례 이름이고, 이 스냅샷에 담긴 벤더 문서는 그 경로의
   환경변수 이름을 밝히지 않습니다. 기기에 키 이름이 설정되어 있다는 것은 그 기기에 대한
   증거이지 이 프로젝트에 대한 증거가 아닙니다. 잠금 파일, 설정, 기존 클라이언트 코드, 환경 변수
   예시 파일처럼 프로젝트 자체의 파일이 다른 경로를 가리키면 그 경로가 이기고, 둘이 어긋나면 어느
   경로를 골랐는지와 그 이유를 밝힙니다.
3. 그 밖에는 `TYPESAFE_API_KEY`를 쓰는 TypeSafe 직접 경로입니다.

규칙이 둘 이상 맞으면 앞의 규칙이 이깁니다. 경로를 바꾸는 일은 요청 단위의 결정이지 조용히
기본값으로 둘 세부가 아닙니다. 질문 유형 이름과 신뢰도 위치가 함께 바뀌므로, 만들어지는 요청과
파싱 코드도 같이 바뀝니다.

키가 있다는 사실도, 신뢰도가 높다는 사실도 실호출을 허가하지 않습니다. 첫 실제 요청 전에
사용자에게 묻고, 비용을 알리고, 질문에 답하는 데 필요한 최소 횟수만 씁니다.

## 미검증 경로

아래 경로들은 Jev를 알리거나 재판매하지만, 이 스냅샷에는 그 계약을 적은 공식 문서가 없습니다.
이 목록은 그런 경로를 이름으로 알아보기 위한 것이지, 코드를 만들기 위한 것이 아닙니다.

- OpenRouter. 벤더의 Python SDK 문서가 OpenRouter base URL과 OpenRouter 모델 슬러그를 예제로
  싣고 있으므로 경로 자체는 있습니다. 다만 그 슬러그는 다른 곳에서 쓰는 모델 아이디와 다르고,
  이 스냅샷에는 현재 지원하는 아이디나 요청 형태를 적은 문서가 없습니다. 이 경로로 돌아다니는
  모델 이름은 확인되지 않은 것으로 다루십시오.
- Cloudflare.
- Netlify.
- DigitalOcean. Gateway 모델 카드가 제공자로 `digitalocean`을 적어 두었지만, 그것은 목록일 뿐
  문서화된 경로 계약이 아닙니다.
- AI/ML API.

위 항목 모두에 적용되는 지침입니다. 코드를 만들지 말고, 벤더의 공식 문서를 먼저 읽어
엔드포인트, 인증 헤더, 받는 모델 아이디, 질문 유형 이름을 확인하십시오. 확인한 뒤 그 경로를
자기 verified 줄과 함께 이 파일에 적고 나서야 코드를 만들 수 있습니다.

비교 표에 없는 경로에도 같은 규칙이 적용됩니다. verified 줄이 없는 경로는 미검증 경로이고,
미검증 경로에는 코드를 만들지 않습니다.

## Sources

> Links checked 2026-10-01. Next re-verification: 2026-10-31.

| 주장 | 출처 |
| --- | --- |
| 직접 엔드포인트, Bearer 헤더, 질문 유형 이름 셋, 받는 모델 별칭, choice와 score의 신뢰도 경로 | <https://docs.typesafe.ai/api> |
| 직접 경로가 받는 모델 아이디의 근거가 된 별칭 표 | <https://docs.typesafe.ai/models> |
| b.ai 엔드포인트, 인증 헤더 둘, 받는 모델 아이디 둘, POST 전용과 `stream` 생략 또는 false, 답의 신뢰도 규칙 | <https://docs.b.ai/llmservice/api/decisions-api/> |
| SDK 경로의 `boolean` 유형, 선택인 확률 분포, Gateway 신뢰도 경로, `AI_GATEWAY_API_KEY` 인증 | <https://ai-sdk.dev/docs/ai-sdk-core/evaluation> |
| Gateway의 문자열 모델 아이디, 모델 카드의 제공자 목록, evaluation 모델 유형 | <https://vercel.com/ai-gateway/models/jev> |
| OpenRouter를 미검증 목록에 올린 근거가 된 base URL과 모델 슬러그 예제 | <https://docs.typesafe.ai/sdk/python/usage.md> |
| 직접 경로와 SDK 경로가 쓰는 환경변수 이름 | <https://docs.typesafe.ai/models> 및 <https://ai-sdk.dev/docs/ai-sdk-core/evaluation> |

### 증거 등급

verified 줄은 모두 `PRIMARY`입니다. 계약의 각 항목이 위 표에 적은 벤더 문서에서 나왔고,
2026-10-01에 받았습니다. 미검증 목록은 계약이 아니라 경로 안내이므로 `SECONDARY`입니다. 이
목록은 세상에 돌아다니는 경로 이름을 적어 둔 것이고, 이 스냅샷에는 그 경로를 적은 벤더 문서가
없습니다. 항목 하나(OpenRouter)는 벤더가 직접 낸 연동 예제에만 기대고 있는데, 그 예제는 계약
전체가 아니라 base URL과 모델 슬러그를 보여 줄 뿐입니다.

직접 경로의 환경변수 이름은 그 이름으로 키를 읽는 벤더의 SDK 문서에서 가져왔습니다.
`BAI_API_KEY`는 벤더가 밝힌 이름이 아니라 프로젝트 관례입니다. 이 스냅샷에 담긴 b.ai 문서는 그
경로의 환경변수 이름을 적지 않았고, 직접 provider(Gateway가 아닌 쪽)의 인증 방식과 환경변수도
담긴 문서에 없으므로 여기서도 확인된 사실로 적지 않습니다.

여기서 확인되지 않아 일부러 비워 둔 것: 클라이언트 패키지의 버전, 미검증 경로의 현재 모델
아이디, 그리고 미검증 경로가 스트리밍을 지원하는지 여부입니다.
