# Jev 플랫폼 스냅샷

벤더 문서가 말하는 Jev 플랫폼의 모습을 한 파일에 모았습니다. HTTP 엔드포인트, 요청과 응답의 형태,
이 파일을 쓴 시점의 한도와 가격, 공개된 신뢰도 공식, 현재 버전에서 알려진 거친 부분, 클라이언트
SDK, 그리고 이 스냅샷이 다루는 모든 경로를 담습니다. Sources에 적은 문서를 2026-11-08에 직접 읽고
옮겼습니다. 가격, 한도, 모델 별칭, 경로 계약은 이 패키지에서 몇 안 되는 이 파일과 옆의 경로 참조,
그리고 바로 옆의 OpenAI 파일에 둡니다.

## Contents

- 갱신 정책
- System One 엔드포인트
- 모델, 별칭, 한도, 가격
- 질문 유형
- 응답 유형, 신뢰도, 그 공식
- 이미지, assets, Box
- 오류와 요청 규칙
- 모델의 거친 부분
- 클라이언트 SDK
- 공식 에이전트 스킬
- Vercel AI SDK와 AI Gateway
- 그 밖의 문서화된 경로
- 가용성
- Sources
- Evidence grade

## 갱신 정책

- last_verified_at: 2026-11-08
- refresh_when:
  - 벤더 문서가 요청 한도, 가격, 컨텍스트 창, 모델 별칭을 바꿀 때
  - 경로가 엔드포인트를 추가하거나 없앨 때
  - 질문이나 응답의 형태(`noul`, `choice`, `score`, `box`)가 바뀔 때
  - 거친 부분 목록, 신뢰도 공식, 오류 표가 바뀔 때
  - 클라이언트 SDK가 마이너 버전을 낼 때
- supports_rules:
  - `rules/modes-and-routing.md`
  - `rules/safety-and-boundaries.md`

이 스냅샷이 30일보다 낡았고 네트워크가 살아 있으면 벤더 문서를 읽기 전용으로 다시 읽고 여기
날짜를 고칩니다. 네트워크가 없으면 값을 짐작하지 말고 스냅샷 날짜를 그대로 밝힙니다.

## System One 엔드포인트

- source_url: https://docs.typesafe.ai/api/system-one.md
- last_verified_at: 2026-11-08
- applies_to: 직접 HTTP 경로, 요청과 응답의 형태, 오류 코드
- volatility: stable
- summary: 엔드포인트 하나가 공유 `state`에 대한 타입 질문에 답하고 질문 아이디마다 구조화된 응답
  하나를 돌려줍니다. 질문 유형 넷이 같은 URL로 가고, 본문의 `model` 필드가 답하는 버전을 정합니다.

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

`https://api.typesafe.ai/openapi.json`의 실제 스키마는 `info.version`이 `0.2.0`이고 경로를
`POST /v1/systemone`과 `GET /v1/models` 둘만 선언합니다.

요청 본문:

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `state` | 문자열, 객체, 배열 | 평가할 내용입니다. 텍스트, JSON, 이미지 자리표시자를 담은 구조입니다. |
| `model` | 문자열 | `jev-latest`가 기본 별칭입니다. 아래 별칭 표를 보십시오. |
| `questions` | 아이디를 키로 하는 질문 맵 | `minProperties: 1`입니다. 응답이 같은 아이디로 돌아옵니다. 벤더는 아이디가 추론에 쓰이지 않는다고 밝힙니다. |
| `assets` | 맵, 선택 | 불투명한 자리표시자를 키로 하는 미디어 자산입니다. 아래 이미지 절을 보십시오. |

스키마상 필수 필드는 `model`, `state`, `questions`입니다. 질문마다 `type`과 `instructions`를
가집니다. `instructions`와 criteria 각 항목은 문자열, 객체, 배열, `null`을 받습니다(스키마의
`EntryType`).

응답 본문은 `model`(답한 아이디), `answers`(질문 아이디마다 하나이고 각 항목이 `noul`, `choice`,
`score`, `box` 중 하나를 `type` 판별자로 가짐), 그리고 `input_tokens`와 `output_tokens`를 담은
`usage`입니다. 출력 토큰은 현재 무료로 문서화돼 있고, JavaScript SDK는 `usage`의 토큰 수가 `null`일
수 있다고 적습니다.

`GET /v1/models`는 `{ models: [{ name, description, release_date }] }`를 돌려줍니다. 벤더는 이
목록이 현재 별칭을 싣고, `jev-1.14.0` 같은 버전 아이디는 목록에 있든 없든 `model` 필드에서 받는다고
밝힙니다.

## 모델, 별칭, 한도, 가격

- source_url: https://docs.typesafe.ai/models.md
- last_verified_at: 2026-11-08
- applies_to: 모델 아이디와 별칭, 요청 한도, 컨텍스트 길이, 받는 입력, 질문 유형, 가격
- volatility: volatile
- summary: 두 버전이 살아 있습니다. `jev-1.14.0`이 현재 릴리스이고 두 별칭이 모두 이 버전을
  가리킵니다. 요금은 입력 토큰에만 붙고 출력 토큰은 무료입니다. 요청 한도는 더 이상 숫자로
  공개되지 않습니다.

| 항목 | 2026-11-08 기준 값 |
| --- | --- |
| 버전 아이디 | `jev-1.14.0`(2026-10-14), `jev-1.13.0` |
| `jev-latest` | `jev-1.14.0`으로 해석, SDK 기본값 |
| `jev-preview` | `jev-1.14.0`으로 해석, 벤더는 지금 프리뷰 빌드가 없다고 밝힘 |
| 가격 | 입력 10억 토큰당 `$42`, 100만 토큰당 `$0.042`. 출력 토큰 무료 |
| 요청 한도 | 조직별로 정해지고 개발자 콘솔에 표시, 초당 토큰과 초당 요청으로 측정 |
| 컨텍스트 | 요청당 64k 토큰, state와 가장 긴 질문 하나에 32k |
| 롱 컨텍스트 | `TypeSafe-Danger-Zone-Long-Context: true`를 보내면 두 한도가 262k 토큰으로 올라감 |
| 질문 유형 | 1.14는 Choice, Score, Noul, Box. 1.13은 Choice, Score, Noul |
| 입력 | 텍스트와 이미지, 오디오와 비디오는 아직 네이티브 지원 없음 |

요청 한도는 분명히 적어 둘 만합니다. 현재 공개된 숫자 한도가 없습니다. 2026-09-29 아카이브에는 초당
250,000 토큰과 분당 1,200 요청이 있었고, 2026-10-03 아카이브에는 초당 100K 토큰과 초당 80 요청이
있었고, 그 뒤 숫자가 페이지에서 완전히 빠졌습니다. 생성 산출물에 박은 고정 숫자는 역사적 값입니다.
한도를 넘으면 `429`가 돌아옵니다.

롱 컨텍스트 헤더는 토큰당 가격이 같고 기본 한도 안에 머무는 것보다 느리고 덜 정확하다고
문서화돼 있습니다. 1.13과 1.14 모두에서 동작하고 기본은 꺼져 있습니다.

언어 지원은 이렇습니다. 1.14 변경 이력이 "다국어 지원 개선"을 들고, 벤더는 영어가 정확도가 가장
높은 곳이라고 밝힙니다. 영어가 아닌 작업은 자기 데이터로 먼저 검증한 뒤 신뢰합니다.

별칭은 릴리스가 나오면 움직이므로 호출자 쪽을 바꾸지 않아도 `jev-latest` 뒤의 답이 바뀔 수
있습니다. 응답의 `model` 필드가 답한 버전을 알려줍니다. 한 버전에 맞춰 신뢰도 임계값을 조정했다면
그 버전 아이디를 고정하고 의도적으로 옮깁니다.

## 질문 유형

- source_url: https://docs.typesafe.ai/primitives.md
- last_verified_at: 2026-11-08
- applies_to: 질문 유형 넷, 각 유형의 criteria 규칙, 그리고 각 유형의 답
- volatility: stable
- summary: 질문은 네 유형 중 하나입니다. 넷 모두 `type`과 `instructions`를 공유하고, 셋은 자기
  criteria 규칙을 더하며 Box는 더하지 않습니다.

| 유형 | criteria | 응답 |
| --- | --- | --- |
| `noul` | 선택인 `NoulCriteria`, `true`와 `false`, null 허용 | `noul`, 0~1 숫자, 별도 신뢰도 없음 |
| `choice` | 선택지와 설명의 맵, 스키마 `minProperties: 1`, `maxProperties: 255` | `choice`, `probabilities`, `confidence` |
| `score` | 단계 설명의 순서 배열, 스키마 `minItems: 1`, `maxItems: 10`, 산문은 두 단계 이상 | `score`, `legend`, `probabilities`, `confidence` |
| `box` | 없음, 벤더는 "Box는 criteria를 받지 않는다"고 적음 | 네 변을 담은 `box`, 그리고 `null`일 수 있는 `confidence` |

`noul`은 답이 예일 확률이고 정도 점수가 아닙니다. 0.5 근처는 불확실을 뜻합니다. `score`는 단계
인덱스의 확률 가중 평균이라 세 단계 답이 `1.05`로 올 수 있고, `legend`가 단계 인덱스를 설명으로
되돌립니다. HTTP JSON에서 legend 키는 문자열로 만든 정수이고, Python SDK는 정수로 노출합니다.

요청을 생성할 때 중요한 문서화된 충돌이 하나 있습니다. OpenAPI 스키마는 단계 하나짜리 `score`를
받고(`minItems: 1`), 산문은 "두 단계 이상이어야 한다"고 적습니다. AI SDK는 TypeSafe와 Perplexity가
단계 하나를 받고 그때 점수 `0`에 확률 `1`을 돌려준다고 문서화합니다. 생성 산출물에는 이식성을 위해
두 단계 이상을 두고, API가 한 단계를 거부하지 않는다는 점은 알아 둡니다.

## 응답 유형, 신뢰도, 그 공식

- source_url: https://docs.typesafe.ai/confidence.md
- last_verified_at: 2026-11-08
- applies_to: 확실성을 어떻게 보고하고 계산하며 행동을 어떻게 가두는지
- volatility: stable
- summary: Choice와 Score 응답은 답의 확률 분포에서 계산한 0~1 `confidence`를 담습니다. 분포가 한
  곳에 몰리면 값이 높고 고르게 퍼지면 낮습니다. Noul 응답에는 신뢰도 필드가 없습니다. Box 응답은
  `null`일 수 있는 신뢰도를 담습니다.

벤더가 이제 공식을 공개합니다.

| 유형 | 공식 | 비고 |
| --- | --- | --- |
| Noul | 없음 | 문서가 편의용으로 `abs(2p - 1)`을 제시할 뿐 API 필드가 아님 |
| Choice | `(p_max - 1/n) / (1 - 1/n)` | `n`은 선택지 수 |
| Score | `max(0, 1 - sum(p_i * abs(i - m)) / MAD_unif)`, `MAD_unif = (1/n) * sum(abs(i - (n-1)/2))` | `m`은 점수 평균, `i`는 단계 인덱스 |

Choice 신뢰도가 최고 확률의 변환이므로 벤더는 둘 다 확인해도 "독립적인 증거가 더해지지 않는다"고
적습니다. 행동을 취할 선택지의 확률에 임계값을 걸고, 그 숫자를 위험으로 읽습니다. 0.9 위에서만
행동하는 규칙은 틀린 선택지가 10퍼센트 미만일 때 행동한다는 뜻입니다.

벤더가 제시하는 출발 임계값은 이렇습니다. Noul은 `0.7`과 `0.3`, 그 사이 구간에는 코드에서 별도
결과를 둡니다. Score 라우팅은 `confidence < 0.5`입니다. 벤더는 또 "신뢰도 임계값은 하나의 숫자가
아니다"라고 분명히 적고, 올바른 값이 도메인과 그 사례에서의 모델 성능에 달려 있다고 밝힙니다.

생성 산출물마다 옮기는 경고 둘. 형식이 맞는 것이 올바름을 보장하지 않습니다. 잘 만든 답도 틀릴 수
있습니다. 그리고 `confidence`는 선택한 답이 맞을 확률이 아닙니다.

## 이미지, assets, Box

- source_url: https://docs.typesafe.ai/images.md
- last_verified_at: 2026-11-08
- applies_to: 이미지 입력, `assets` 맵, 게이트 헤더, 한도
- volatility: volatile
- summary: 이미지는 살아 있는 두 버전 모두에서 `state`, `instructions`, `criteria`에 받고, 헤더와
  요청 단위 `assets` 맵을 통과해야 합니다. Box 질문은 1.14가 필요합니다.

이미지와 Box는 이미지나 Box 질문을 담은 모든 요청에서 `TypeSafe-Danger-Zone-Images: true`로
게이트됩니다. 헤더가 없으면 요청이 `400`을 돌려줍니다.

전송 방식은 둘입니다.

- `assets` 맵을 쓴 JSON. 자산마다 불투명한 자리표시자를 키로 두고, 이미지마다 UUID를 쓰기를
  권합니다. `state`의 문자열, 질문 `instructions`, `criteria` 안에서 그 자리표시자가 나올 때마다
  자산으로 치환됩니다. 객체 키는 치환하지 않습니다.
- 멀티파트. JSON 요청이 `request`라는 이름의 첫 파트이고, 이미지가 각자의 파트입니다.

자산 필드는 `type`(선택이지만 보낼 때는 `image`여야 함), `format`(`png`, `jpg`, `jpeg`, `data_base64`와
함께면 필수), `data_base64`, `part`(멀티파트 파트 이름, `part`가 있으면 `data_base64`는 무시)입니다.

벤더 한도 표는 이렇습니다.

| 항목 | 한도 |
| --- | --- |
| 파일 크기 | 이미지 파일당 16 MiB |
| 가로와 세로 | 각각 280~1568 픽셀 |
| 전체 픽셀 | 78,400~2,458,624 |
| 요청 하나의 전체 이미지 | 32 MiB |
| 확장된 요청 | 참조를 모두 이미지로 바꾼 뒤 32 MiB |
| 참조 길이 | 참조마다 UTF-8 1,024바이트 이하, 요청 전체 65,536바이트 이하 |
| 형식 | PNG와 JPEG, 움직이는 PNG는 거부 |

모든 자산은 참조돼야 하고, 참조되지 않은 자산이 있으면 `400`입니다. 참조할 때마다 이미지가 다시
들어가므로 같은 참조를 되풀이하면 토큰도 다시 씁니다. API는 EXIF와 색 프로필을 포함한 모든
메타데이터를 지우고 EXIF 방향을 적용하지 않습니다. 이미지마다 입력 토큰으로 세며 별도 이미지
요금은 없습니다.

Box는 `primitives/box.md`와 스키마 기준으로 이렇습니다.

- `BoxQuestion`은 `type`을 필수로 받고 그 밖에는 `instructions`만 받습니다. criteria를 받지
  않습니다.
- `BoxAnswer`는 `type`, `box`, `confidence`를 필수로 받습니다. `BoxCoordinates`는 `top`, `bottom`,
  `left`, `right`를 필수로 받고, 각 값은 높이나 너비에 대한 0~1 비율이며 그 변이 예측한 위치의
  기댓값으로 문서화돼 있습니다.
- `confidence`는 `number | null`입니다. 스키마 예시는 `null`, 본문 예시는 `0.92`입니다.
- "찾지 못함" 답이 없습니다. 없는 대상을 묻는 Box 질문도 네 변을 돌려주므로 짝이 되는 Noul과 함께
  씁니다.
- 벤더는 이미지와 Box를 "Dreamer-ready"로 표시합니다. "이미지와 Box 질문은 아직 프로덕션 준비가
  됐다고 부를 우리 기준에 못 미친다"고 적고, 요청 형식과 답과 한도가 릴리스 사이에 바뀔 수 있다고
  밝힙니다.

## 오류와 요청 규칙

- source_url: https://docs.typesafe.ai/api/errors.md
- last_verified_at: 2026-11-08
- applies_to: 상태 코드, 본문 규칙, 압축, 문서화된 기계 판독 코드 하나
- volatility: stable
- summary: 오류 표에 일곱 줄이 있고, 요청 규칙은 크기, 중첩, 숫자, 압축을 분명히 정합니다.

| 상태 | 뜻 |
| --- | --- |
| `400` | 요청 규칙을 어겼거나 이미지·자산 규칙이 실패 |
| `401` | 키가 없거나 잘못됨 |
| `413` | 본문이 너무 큼 |
| `415` | 지원하지 않는 미디어 타입, 지원하지 않는 압축 인코딩 포함 |
| `422` | 본문 검증 실패, 본문이 문제 필드를 지목 |
| `429` | 요청 한도 초과 |
| `529` | 서비스가 일시적으로 과부하 |

요청 규칙:

- 본문 크기 최대 32 MiB, 헤더는 세지 않습니다.
- 바이트 순서 표시(BOM)가 없는 UTF-8 JSON.
- 중첩 최대 64단계.
- 유한한 숫자만, `NaN`, `Infinity`, `1e400` 같은 값은 거부합니다.
- `Content-Encoding: gzip`(또는 `x-gzip`)이나 `zstd`를 받고, zstd 창은 최대 8 MiB입니다. 32 MiB
  한도는 압축 본문과 푼 본문 모두에 적용됩니다.

문서 전체에서 기계 판독이 되는 오류 코드는 `max_tokens_exceeded` 하나뿐입니다. 이미지와 자산 실패는
산문 사유가 붙은 평범한 `400`이나 `413`입니다. OpenAPI 문서는 `/v1/systemone`에 `200`, `400`,
`422`만 선언하고, `401`, `413`, `415`, `429`, `529`는 산문으로만 문서화돼 있습니다.

벤더는 `429`와 `529`에 짧게 물러났다 재시도하라고 안내합니다. 클라이언트 SDK가 기본으로 이렇게
합니다. 정확한 기본값은 SDK 절에 있습니다.

## 모델의 거친 부분

- source_url: https://docs.typesafe.ai/model-jaggedness.md
- last_verified_at: 2026-11-08
- applies_to: 현재 모델 계열의 알려진 실패 모드와 벤더가 권하는 우회법
- volatility: volatile
- summary: 페이지가 실패 모드 아홉 가지를 싣습니다. 더 이상 버전에 묶여 있지 않습니다. 제목에
  버전이 없고 본문에도 버전 문자열이 없습니다. 옛 "상식적 구조 불변식" 모드가 교체됐습니다.

| # | 실패 모드 | 대신 이렇게 |
| --- | --- | --- |
| 1 | 문자 그대로 읽기: 적힌 말을 따르고 그 뒤의 의도를 놓침 | 조건을 정확히 쓰고 경계 사례를 criteria에 둡니다 |
| 2 | 수와 계산: 세기, 산술, 숫자 표기가 불안정 | 산술은 코드에 두고 16진수나 2진수 값 대신 이름을 씁니다 |
| 3 | 날짜와 시간 비교: 날짜를 순서 있는 양이 아니라 텍스트로 읽음 | 닫힌 집합으로 조각을 뽑고 코드에서 조립해 비교합니다 |
| 4 | 우회: 이중 부정과 여러 단계 질문이 정확도를 깎음 | 단계를 줄이고 관련 state를 이름으로 지목합니다 |
| 5 | 무관한 내용이 많은 큰 state: 관계없는 내용이 방해물로 작동 | 코드에서 먼저 걸러 질문에 필요한 필드만 보냅니다 |
| 6 | 적대적 내용: state는 데이터이고 기본적으로 적대적으로 취급되지 않음 | 프롬프트를 정확히 쓰고 널리 배포하기 전에 경계 사례를 시험합니다 |
| 7 | 지시와 criteria의 모순: 둘이 서로 싸울 수 있음 | criteria를 지시의 연장으로 보고 문구를 맞춥니다 |
| 8 | Choice 선택지 순서: 선택지 순서가 답에 영향을 줄 수 있고 Jev가 앞 선택지 쪽으로 기움 | 순서를 바꿔 답이 일관된지 확인합니다 |
| 9 | 생성: 모델이 텍스트 생성을 학습하지 않음 | 생성 모델을 쓰거나 추출을 열거 선택지 위의 Choice로 바꿉니다 |

목록에 딸리는 진술이 둘 더 있습니다. 세기가 Math 절 안에서 불안정하다고 따로 지목됩니다. 그리고
Score 단계는 수치 보정이 약합니다. 벤더는 Jev가 "가까운 두 단계 사이를 보간해 정확한 숫자를
복원하는 데 도움이 되지 못한다"고 적습니다. Score는 값이 임계값을 넘는지 판단하는 데 쓰고 값을
복원하는 데는 쓰지 않습니다.

옛 8번 모드는 부정과 동일성 지침을 담고 있었고, 질문과 그 부정형의 확률 합이 1을 넘던 예제도 그
안에 있었습니다. 그 절은 현재 페이지에서 사라졌습니다. 실무적 교훈은 남습니다. 질문과 그 부정형의
합이 1이라고 가정하지 않고, 한 질문에 맞춘 임계값을 다른 질문으로 옮기지 않습니다.

## 클라이언트 SDK

- source_url: https://docs.typesafe.ai/sdk/javascript.md, https://docs.typesafe.ai/sdk/python.md
- last_verified_at: 2026-11-08
- applies_to: 패키지 이름, 버전, 환경변수, 재시도 기본값
- volatility: volatile
- summary: 두 SDK 모두 2026-10-14에 나왔고, 둘 다 이미지와 Box를 지원하며, 같은 환경변수 네 이름을
  읽습니다.

| 항목 | JavaScript | Python |
| --- | --- | --- |
| 패키지 | `@typesafe-ai/sdk` `0.7.0`(2026-10-14) | `typesafe-sdk` `0.7.5`(2026-10-14), import `typesafe_sdk` |
| 런타임 하한 | Node.js 22 이상 | Python 3.10 이상 |
| 클라이언트 | `TypeSafeClient` | `TypeSafeClient`와 `AsyncTypeSafeClient` |
| API 키 변수 | `TYPESAFE_API_KEY` | `TYPESAFE_API_KEY`(`API_KEY_ENV`) |
| Base URL 변수 | `TYPESAFE_BASE_URL`, 기본 `https://api.typesafe.ai` | `TYPESAFE_BASE_URL`(`BASE_URL_ENV`) |
| 모델 변수 | `TYPESAFE_DEFAULT_MODEL`, 기본 `jev-latest` | `TYPESAFE_DEFAULT_MODEL`(`DEFAULT_MODEL_ENV`) |
| 로그 수준 변수 | `TYPESAFE_LOG_LEVEL`, 기본 `warn` | `TYPESAFE_LOG_LEVEL`(`LOG_LEVEL_ENV`) |
| 요청 압축 | Node 22.15 이상에서 1 KiB 이상 본문을 zstd로, `compression: false`로 해제 | 기본 zstd, `zstd` extra 제공 |
| 기본 타임아웃 | 10,000ms | `DEFAULT_TIMEOUT = 10.0`, `RetryPolicy`는 `timeout=30.0` |

재시도 기본값은 문서 기준으로 이렇습니다.

- JavaScript `RetryPolicy`: `maxRetries 2`, `httpStatuses {408, 429, 500~599}`, `backoffInitialMs 500`,
  `backoffMaxMs 5000`, `backoffJitter 0.25`, `maxRetryAfterMs 60000`, `respectRetryAfter true`,
  연결 오류와 타임아웃 오류 재시도.
- Python `RetryPolicy`: `max_retries=2`, `backoff_initial=0.5`, `backoff_max=5.0`,
  `backoff_jitter=0.25`, `http_statuses={408, 429, 500~599}`, `respect_retry_after=True`,
  `timeout=30.0`.

기본 집합이 빼놓은 것을 보십시오. `529`가 두 목록 어디에도 없습니다. 정책을 넓히지 않으면 과부하
응답이 호출자에게 그대로 올라갑니다.

그 밖에 문서화된 표면: JavaScript 패키지는 `TypeSafeClient`, `choice()` 도우미, `box()` 도우미,
`image()`, `Image.fromBase64()`, 자산 도우미, `ENV`, 타입이 붙은 오류 클래스를 내보내고 이미지
요청을 멀티파트로 보냅니다. Python 패키지는 `system_one(...)`, `models.list()`,
`response_model=` 옵션, 그리고 유형별 뷰 `nouls`, `choices`, `scores`, `boxes`를 노출합니다.

## 공식 에이전트 스킬

- source_url: https://docs.typesafe.ai/agent-skill.md
- last_verified_at: 2026-11-08
- applies_to: 벤더가 배포하는 에이전트 스킬과 설치 방법
- volatility: volatile
- summary: 벤더가 에이전트 스킬 하나를 내놓습니다. 코딩 에이전트에게 질문 유형, 패턴, 평가 구성
  관행을 알려 주는 안내이자 설계 보조입니다.

설치 경로가 둘로 문서화돼 있고, 페이지는 사본이 겹치지 않도록 하나만 쓰라고 합니다.

```bash
npx skills add typesafe-ai/skills --skill typesafe-ai
```

```bash
claude plugin marketplace add typesafe-ai/skills
claude plugin install typesafe@typesafe-ai
```

설치기는 어느 에이전트를 대상으로 할지 묻고, 기본으로 프로젝트 로컬에 설치하며, `-g`로 전역 설치를
받습니다. 갱신은 같은 설치기나 플러그인 마켓플레이스로 하고, 페이지는 낡은 사본이 요청·응답 필드를
지어내는 원인이라고 적습니다. GitHub 저장소는 아직 열리지만 문서 링크가 `/go/*` 접두사를 써서 정식
페이지로 리다이렉트됩니다.

## Vercel AI SDK와 AI Gateway

- source_url: https://ai-sdk.dev/docs/ai-sdk-core/decisions
- last_verified_at: 2026-11-08
- applies_to: `ai` 패키지의 결정 API, 질문 유형, 신뢰도 보고, Jev용 게이트웨이 경로
- volatility: volatile
- summary: SDK 함수는 이제 `experimental_decide`이고 옛 이름 `experimental_evaluate`는 폐기
  별칭입니다. 제공자 인터페이스는 `Experimental_DecisionModelV4`이고 안정 제공자 계약과 분리돼
  있습니다.

코드를 쓸 때 중요한 사실:

- `experimental_decide({ model, state, questions, ... })`가 공유 state 하나를 두고 이름 붙은 질문의
  답을 정합니다. `experimental_evaluate`는 같은 모양의 폐기 별칭으로 남아 있고, 2026-10-05
  `ai@7.0.128`에서 이름이 바뀌었습니다.
- `Experimental_DecisionModelV4`는 `@ai-sdk/provider`에서 내보내고 `specificationVersion: 'v4'`,
  `provider`, `modelId`, `supportedQuestionTypes`, `doDecide()`를 가지며, 소스 주석이 패치 릴리스에서
  바뀔 수 있다고 밝힙니다. 설치 버전을 고정하십시오. 2026-11-06 기준 `ai` `7.0.164`,
  `@ai-sdk/provider` `4.0.36`이었습니다.
- 이 경로에서 예/아니오 질문 유형은 `boolean`이고 TypeSafe 제공자가 `noul`로 매핑합니다. Boolean
  응답은 `probability`를 필수로 가집니다. SDK는 제공자 사이의 보정을 약속하지 않습니다.
- TypeSafe 제공자 팩토리는 `typeSafeAi.decisionModel('jev-latest')`이고 옛 `evaluationModel`은 폐기
  별칭입니다. 패키지는 `@ai-sdk/typesafe-ai` `3.0.34`입니다.
- TypeSafe 제공자는 `TYPESAFE_AI_API_KEY`와 `TYPESAFE_AI_BASE_URL`(기본
  `https://api.typesafe.ai/v1`)을 읽습니다. TypeSafe SDK의 `TYPESAFE_API_KEY`와
  `TYPESAFE_BASE_URL`과 일부러 다른 이름입니다.
- TypeSafe 자체 choice와 score 신뢰도는 `result.providerMetadata.typesafe.confidence[questionId]`에,
  구조화된 Score legend는 `result.providerMetadata.typesafe.legend[questionId]`에 있습니다. 문서는
  신뢰도가 "선택한 선택지의 확률도, 이식 가능한 신뢰도 척도도 아니다"라고 경고합니다.
- 분포가 있으면 SDK가 답과 맞는지 검증하고, 틀린 출력은 정규화하지 않고 거부합니다. 기본 절대
  허용 오차는 `0.000001`입니다.
- 제공자 지원은 설계상 고르지 않습니다. TypeSafe 제공자는 `box`를 포함한 네 유형을 모두 지원하고,
  OpenAI, Perplexity, Parallel은 앞의 셋을 네이티브로 지원하며, Anthropic과 Google 어댑터는 구조화
  출력 위에서 셋을 흉내 내고 choice와 score 확률 분포를 아예 빼놓습니다.
- 결정을 인식하는 라우팅은 게이트웨이 경로에만 있고 `providerOptions.gateway.models`로 합니다.

게이트웨이 모델 아이디와 카드:

| 항목 | 값 |
| --- | --- |
| 게이트웨이 모델 아이디 | `typesafe-ai/jev`, 카탈로그에 `typesafe-ai/jev-1.13.0`과 `typesafe-ai/jev-1.14.0`도 있음 |
| 카드에 적힌 제공자 | `typesafe-ai`와 `digitalocean` |
| 카드의 컨텍스트 창 | 32,000 |
| 최대 출력 토큰 | 0 |
| 가격 | 입력 100만 토큰당 `$0.042`, 출력 `$0` |
| 카탈로그 타입 표기 | `evaluation`, `decision`이 아님, `decision`으로 거르면 아무것도 안 나옴 |
| 지원 명세 | `v4` |

게이트웨이는 Jev용 결정 표면을 둘 노출합니다. `predicate`, `choice`, `score` 질문을 받는 OpenAI 호환
`POST /v1/decisions`, 그리고 base URL `https://ai-gateway.vercel.sh/typesafe`에
`POST /typesafe/v1/systemone`과 `GET /typesafe/v1/models`를 두는 TypeSafe 호환 표면입니다.

재현성 결함이 하나 열려 있습니다. 게이트웨이에서 `response.modelId`가 보낸 별칭 그대로 돌아오고,
결과의 어느 필드도 버전을 지목하지 않습니다(vercel/ai 이슈 #21213, 2026-09-20부터 열림).
`jev-latest`는 2026-10-14에 1.13에서 1.14로 옮겼으므로, 핀을 걸지 않은 게이트웨이 호출은 요청을
바꾸지 않아도 모델이 바뀔 수 있습니다. 재현성이 필요한 곳에는 버전 아이디를 고정하고 응답이 밝힌
모델을 기록합니다.

## 그 밖의 문서화된 경로

아래 경로는 모두 같은 모델의 공식 경로이고 각자 자기 계약을 가집니다. 벤더 간 비교와 경로 선택
순서는 옆의 경로 참조에 있습니다.

### b.ai Decisions API

- source_url: https://docs.b.ai/llmservice/api/decisions-api/
- last_verified_at: 2026-11-08
- summary: `POST https://api.b.ai/v1/decisions`, Bearer 또는 `x-api-key`, POST 전용에 `stream`은 생략
  하거나 `false`. `jev-1.13.0`과 `jev-latest`만 받고 box 유형이 없습니다.

응답 규칙: choice와 score는 `confidence`를 담고 noul은 담지 않습니다. `probabilities`는 그 질문의
선택지 키나 문자열 단계 인덱스를 정확히 담아야 하고 값의 합이 0.0001 안에서 1이어야 합니다. score
응답은 `legend`도 담습니다. 사용량 두 값은 필수이고 합이 2147483647을 넘을 수 없으며, 16 MiB를 넘는
응답은 거부합니다. `429`는 본문이 비었거나 JSON이 아닐 수 있으므로 상태 코드를 먼저 확인합니다.
멱등성 보장이 없으므로 타임아웃 뒤 재시도가 작업을 되풀이할 수 있습니다. 크레딧은 1달러 =
1,000,000 크레딧으로 정산합니다.

1.14 모델 페이지가 b.ai sitemap에 없습니다. 따라서 그곳에 1.14가 없다는 판단은 sitemap 범위의
사실이고 증명은 아닙니다.

### DigitalOcean Inference

- source_url: https://docs.digitalocean.com/products/inference/how-to/use-system-one-api/
- last_verified_at: 2026-11-08
- summary: `Authorization: Bearer $MODEL_ACCESS_KEY`로 `POST https://inference.do-ai.run/v1/systemone`
  을 호출하고, `typesafe-jev-1.13.0` 아이디 하나만 서빙합니다. 벤더가 마지막으로 확인한 날은
  2026-09-28입니다.

문서는 텍스트 state와 `noul`, `choice`, `score` 유형만 적습니다. 이미지 경로와 box 유형은 문서화하지
않고, Jev가 제3자 모델이라 계정이 자격 등급에 있어야 한다고 밝힙니다. 벤더가 문서화할 때까지 이
경로에서 이미지와 box는 미지원으로 다룹니다.

### OpenRouter

- source_url: https://openrouter.ai/docs/guides/community/jev
- last_verified_at: 2026-11-08
- summary: 표면이 둘입니다. `POST https://openrouter.ai/api/alpha/decisions`는 알파이고 벤더가 모양이
  바뀔 수 있다고 경고합니다. `POST https://openrouter.ai/api/v1/systemone`은 System One 표면입니다.
  Jev 모델 아이디는 `typesafe/jev-1.14`이고, base URL `https://openrouter.ai/api`에 TypeSafe SDK를
  붙일 때 쓰는 라우터 별칭은 `~typesafe/jev-latest`입니다.

모델 엔드포인트는 컨텍스트 길이 `262,144`와 프롬프트 토큰당 `$0.000000042`를 보고합니다. Box 질문은
"TypeSafe Jev 엔드포인트만 서빙하고 다른 제공자는 업스트림으로 보내기 전에 `400`으로 거부"합니다.
OpenRouter의 모델 목록은 TypeSafe 모양이 아니라서 TypeSafe SDK의 `models.list()`가 그곳에서
실패합니다.

## 가용성

- source_url: https://status.typesafe.ai/index.json
- last_verified_at: 2026-11-08
- summary: 읽은 시점에 상태 피드가 2026-11-07 갱신 기준으로 사고 여덟 건을 싣고 있었습니다.
  `2026-10-30 System overload`, `2026-10-14 Elevated Latency`, `2026-09-28 Degradation in API
  Traffic`, `2026-09-21 API issues` 등입니다.

피드는 공개 가동률을 보고하지 않습니다. 모든 자원의 `uptime` 필드가 null입니다. 서비스는 빠르고
쓸모 있지만 고르게 가용하지는 않다고 보고, 실패하면 안 되는 요청 경로에는 재시도와 대체 경로를 두고,
가동률 숫자를 인용하지 않습니다.

## Sources

> Links checked 2026-11-08.

| 주장 | 출처 |
| --- | --- |
| `/v1/systemone` 경로, Bearer 헤더, 요청 필드, 질문 아이디 규칙, 응답 필드 | <https://docs.typesafe.ai/api/system-one.md> |
| OpenAPI `info.version` 0.2.0, 경로 둘, `questions` 최소 개수, `assets` 맵, 1~255와 1~10 한도, 응답 `type` 판별자, Box의 `confidence` 유니온, 헤더 열거형 둘 | <https://api.typesafe.ai/openapi.json> |
| 질문 유형 넷과 각 criteria 규칙, Box가 criteria를 받지 않는다는 규칙 | <https://docs.typesafe.ai/primitives.md>, <https://docs.typesafe.ai/primitives/box.md> |
| `jev-1.14.0`과 `jev-1.13.0`, 두 별칭의 1.14 해석, 조직별 요청 한도 문구, 64k/32k 기본값, 262k 롱 컨텍스트 헤더, 버전별 질문 유형, 텍스트와 이미지 입력 | <https://docs.typesafe.ai/models.md> |
| 2026-10-14의 1.14 출시, 다국어 지원, Box, 이미지, 롱 컨텍스트 | <https://docs.typesafe.ai/changelog.md> |
| 이미지 헤더, `assets` 규칙, 한도 표, 메타데이터 제거, 이미지의 토큰 비용 | <https://docs.typesafe.ai/images.md>, <https://docs.typesafe.ai/concepts/state.md> |
| 신뢰도 공식 셋, "독립적인 증거가 더해지지 않는다" 문장, 0.7·0.3·0.5 출발 임계값 | <https://docs.typesafe.ai/confidence.md> |
| 오류 일곱 줄, 32 MiB 본문 한도, 중첩 64단계, 유한수 규칙, 압축 규칙, `max_tokens_exceeded` | <https://docs.typesafe.ai/api/errors.md> |
| 거친 부분 아홉 가지, 8번이 Choice 선택지 순서라는 점, 버전 표기 부재, 약한 Score 보간 | <https://docs.typesafe.ai/model-jaggedness.md> |
| Noul과 Score 라우팅의 문서화된 임계값 | <https://docs.typesafe.ai/patterns/probability-routing.md>, <https://docs.typesafe.ai/patterns/confidence-routing.md> |
| JS SDK 버전, Node 하한, `ENV` 변수 이름, 재시도 기본값, 압축 동작 | <https://docs.typesafe.ai/sdk/javascript.md>, <https://docs.typesafe.ai/sdk/javascript/changelog.md>, <https://docs.typesafe.ai/sdk/javascript/api/variables/ENV.md>, <https://docs.typesafe.ai/sdk/javascript/api/interfaces/RetryPolicy.md> |
| Python SDK 버전, 상수, 재시도 기본값, 유형별 뷰 | <https://docs.typesafe.ai/sdk/python.md>, <https://docs.typesafe.ai/sdk/python/changelog.md>, <https://docs.typesafe.ai/sdk/python/api/constants.md>, <https://docs.typesafe.ai/sdk/python/api/retries.md> |
| 에이전트 스킬 설치 경로 둘과 낡은 사본 경고 | <https://docs.typesafe.ai/agent-skill.md> |
| `experimental_decide`, `Experimental_DecisionModelV4`, `boolean` 매핑, 허용 오차, 제공자 지원 범위 | <https://ai-sdk.dev/docs/ai-sdk-core/decisions>, <https://ai-sdk.dev/docs/reference/ai-sdk-core/decide> |
| `typeSafeAi.decisionModel`, `TYPESAFE_AI_API_KEY`, `TYPESAFE_AI_BASE_URL`, `providerMetadata.typesafe.confidence`, `.legend` | <https://ai-sdk.dev/providers/ai-sdk-providers/typesafe-ai>, <https://github.com/vercel/ai/pull/24627> |
| 2026-10-05 `ai@7.0.128`의 `experimental_evaluate`에서 `experimental_decide`로의 개명 | <https://github.com/vercel/ai/pull/21935> |
| 게이트웨이 모델 아이디, 제공자, 컨텍스트, 출력 토큰, 가격, `evaluation` 타입 | <https://vercel.com/ai-gateway/models/jev> |
| 버전이 붙은 게이트웨이 아이디 셋, `v4` 명세, `evaluation` 항목 15개 | <https://ai-gateway.vercel.sh/v1/models> |
| OpenAI 호환 게이트웨이 결정 경로와 질문 한도 | <https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions> |
| TypeSafe 호환 게이트웨이 경로 | <https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe> |
| 별칭만 돌아오는 `modelId` 결함 | <https://github.com/vercel/ai/issues/21213> |
| b.ai 엔드포인트, 인증 헤더, 받는 아이디, 응답 규칙, 0.0001 허용 오차, 사용량 합 상한, 16 MiB 한도, 429 안내 | <https://docs.b.ai/llmservice/api/decisions-api/> |
| b.ai 모델 페이지, 크레딧 환산, 컨텍스트 한도, 경고 | <https://docs.b.ai/llmservice/models/jev-1.13.0/> |
| DigitalOcean 엔드포인트, `MODEL_ACCESS_KEY`, 단일 아이디, 등급 제한 | <https://docs.digitalocean.com/products/inference/how-to/use-system-one-api/> |
| OpenRouter 표면 둘, 알파 경고, box 거부 규칙, `typesafe/jev-1.14` 아이디 | <https://openrouter.ai/docs/guides/community/jev> |
| OpenRouter 컨텍스트 길이와 프롬프트 가격 | <https://openrouter.ai/api/v1/models/typesafe/jev-1.14/endpoints> |
| TypeSafe SDK의 OpenRouter base URL과 슬러그 | <https://docs.typesafe.ai/sdk/python/usage/basic.md> |
| 상태 페이지 사고 목록과 null 가동률 필드 | <https://status.typesafe.ai/index.json> |
| 위 문서를 찾는 데 쓴 문서 목록 | <https://docs.typesafe.ai/llms.txt> |

### Evidence grade

가용성 절과 표시해 둔 제3자 사실 둘을 빼면 이 파일의 모든 항목이 `PRIMARY`입니다. 각 사실이 설명
대상 서비스의 벤더 문서에서 나왔고 2026-11-08에 받아 두었습니다. 게이트웨이 카탈로그의 `evaluation`
타입 표기와 15개 항목 수는 Vercel의 실제 API에서 온 Vercel에 관한 벤더 사실이고 TypeSafe에 관한
사실이 아니며, 쓰는 자리에서 표시했습니다. 상태 페이지는 벤더가 운영하는 BetterStack 피드라서 사고
목록은 `PRIMARY`이고, 그 피드가 공개하지 않는 가동률을 추론한 부분에서는 `SECONDARY`입니다.

이 문서들로 확인되지 않아 일부러 비워 둔 것: 현재의 숫자 요청 한도, 어떤 보정 약속, 벤더 산문 밖의
지연 시간 벤치마크, 그리고 1.13 지원 종료 날짜(어느 문서도 밝히지 않습니다).
