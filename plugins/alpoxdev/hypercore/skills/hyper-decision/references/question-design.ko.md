# 질문 설계 참조

결정 요청은 공유 입력 하나와 타입이 붙은 질문 묶음입니다. 답을 쓸 수 있는지 없는지는 질문이
정합니다. 질문마다 좁은 판단 하나만 묻고, 뜻은 전부 그 질문의 지시문 안에 담고, 이웃한 선택지
사이의 경계를 분명히 그어야 합니다. 이 파일은 그 습관, 중립 유형 이름과 경로마다 다른 방언, 질문이
향하는 상태, 코드가 주도권을 쥐는 추출 방식, 거절이 지니는 뜻, 그리고 오프라인 검사기를 쓸 수 없을
때 사람이 직접 돌리는 점검표를 담습니다.

가격, 한도, 모델 아이디는 [`./providers.md`](./providers.md)와 [`./official/`](./official/) 아래
스냅샷에 있고 여기에는 없습니다.

## Contents

- 상태에 대한 사람 시험
- 판단은 모델에, 결정은 코드에
- 중립 유형과 그 유형이 타는 방언
- 질문 아이디는 이름표입니다
- 질문 하나에 판단 하나
- 구조화된 지시문
- Choice 기준
- 대비책: 짝 불리언을 먼저
- Score 단계는 상황으로
- Boolean의 true와 false 설명
- Box 질문
- 선택지 순서는 측정되는 편향입니다
- 거절은 낮은 확률이 아닙니다
- state 인코딩
- 후보 추출
- 한국어 입력
- 문서로 밝힌 약점
- 요청 유효성 점검표
- Sources

## 상태에 대한 사람 시험

상태는 요청에서 품질을 가장 자주 가르는 부분이고, 그 시험은 단순합니다. 이 상태와 이 질문만 보고도
능력 있는 사람이 곧바로, 직관으로 답할 수 있는가. 질문이 이 시험을 통과하지 못하면 고칠 곳은 대개
문장이 아니라 상태입니다.

- 사람이 볼 것을 그대로 주십시오. 메시지를 보낸 사람, 잘린 마지막 줄이 아니라 전체 대화, 원시
  아이디나 마크업이 아니라 이름, 전체 목록이 아니라 질문이 향하는 항목입니다.
- 코드가 이미 아는 사실은 상태에 적어 두십시오. "`replies`의 메시지는 모두 환불 처리 뒤에
  도착했다"처럼 적으면 모델이 같은 사실을 다시 알아낼 필요가 없습니다.
- 모델이 알 수 없는 것은 함께 넣으십시오. 사내 제품 코드가 무엇을 가리키는지 같은 정보입니다.
- 모든 필드가 관련 있게 하십시오. 한 질문을 위해 넣은 필드가 다른 질문의 답을 흔들 수 있고,
  벤더도 관련 없는 내용이 많은 상태를 문서로 밝힌 약점으로 꼽습니다.

출처: <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) 및
<https://docs.typesafe.ai/model-jaggedness.md>.

## 판단은 모델에, 결정은 코드에

결정이 기대는 판단을 물으십시오. 결정 자체는 코드의 표로 두십시오. "이 티켓을 상위로 올려야
하나?"처럼 모델에게 결정을 시키는 질문은 대개 층위가 틀렸습니다. 그 답은 코드에 있어야 보이고
시험할 수 있는 정책이고, 모델은 그 정책이 읽을 입력을 공급해야 합니다.

설계하면서 그 표를 적어 보십시오. 판단 조합에 정해진 결과가 없다면 그것은 시스템의 설계 공백이며,
질문을 넓혀 덮는 것보다 코드에서 정하는 편이 낫습니다.

출처: <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## 중립 유형과 그 유형이 타는 방언

중립 유형 네 가지로 확인된 모든 경로를 덮습니다. 방언이 바뀌면 와이어 이름과 컨테이너 모양이
달라지므로, 한 경로에 맞춰 쓴 질문 묶음은 다른 경로의 질문 묶음이 아닙니다.

| 중립 유형 | 묻는 것 | System One 방언 | OpenAI 결정 방언 | AI SDK |
| --- | --- | --- | --- | --- |
| `boolean` | P(true) 스칼라 하나 | `noul` | `predicate` | `boolean` |
| `choice` | 닫힌 집합에서 선택지 하나와 분포 | `choice`, `criteria`는 선택지에서 설명으로 가는 맵 | `choice`, `choices: [{ value, description }]` | `choice` |
| `score` | 정렬된 단계 위의 위치와 분포 | `score`, `criteria`는 단계 설명의 정렬된 배열 | `score`, `levels: [{ label, description }]` | `score` |
| `box` | 이미지 안 대상 주위의 네 변 | `box`, Jev 1.14 전용 | 지원하지 않음 | 계약에는 `box`가 있고 TypeSafe 공급자만 구현 |

- 설계 중에는 System One 방언을 기준으로 두는 편이 좋습니다. 선택지 맵이 가장 쓰기 쉽기
  때문입니다. 변환은 경계에서 하고 설계 노트에서는 하지 마십시오.
- OpenAI 방언에서는 질문 컨테이너가 맵이 아니라 배열이고, 항목마다 `name`이 필수이며, `criteria`
  필드가 아예 없습니다. 이 필드를 넣은 질문은 검사기가 `CRITERIA_NOT_SUPPORTED`로 거부합니다.
- AI SDK는 질문을 그대로 공급자에게 넘기므로 질문 유형 지원은 SDK가 아니라 공급자의 성질입니다.
  Anthropic과 Google 어댑터는 분포를 아예 돌려주지 않습니다.
- `box`는 호스팅 경로에서 한 벤더의 기능입니다. 이미지 요구가 붙은 실험으로 다루고 일반 계약의
  일부로 보지 마십시오.

출처: <https://docs.typesafe.ai/primitives.md>,
<https://developers.openai.com/api/reference/resources/decisions/methods/create.md>,
<https://ai-sdk.dev/docs/ai-sdk-core/decisions>.

## 질문 아이디는 이름표입니다

System One 방언에서 질문 컨테이너는 아이디에서 질문으로 가는 맵이고, 2026-10-01에 받아 둔 벤더 API
페이지는 아이디가 "모델에 전달되지 않고 추론에도 쓰이지 않는다"고 적습니다. 이 패키지가 2026-11-08에
받아 둔 페이지는 맵과 최소 크기를 설명할 뿐 그 문장을 되풀이하지 않으므로, 아이디 노출 여부는 그
날짜의 벤더 진술로 보고 계약으로 기대하지 마십시오.

OpenAI 방언에서는 질문마다 `name`이 필요하고 답이 그 이름을 그대로 돌려줍니다. 그 `name`이 모델에
닿는지는 여기 받아 둔 페이지에 적혀 있지 않고, 레퍼런스는 그것을 답의 식별자로 설명합니다.

어느 쪽이든 설계 규칙은 같습니다. 모델이 읽는 것은 지시문이므로 질문의 뜻은 전부 거기에 있어야
합니다. `refund_requested` 같은 아이디는 코드가 답을 찾는 이름표일 뿐입니다. 아이디만 보면 뜻이
분명해 보이는 순간이 가장 위험합니다. 지시문을 대충 쓰고 지나가면 아무도 쓰지 않은 질문에 답이
돌아옵니다.

출처: <https://docs.typesafe.ai/api/system-one.md> 및
<https://developers.openai.com/api/reference/resources/decisions/methods/create.md>.

## 질문 하나에 판단 하나

맥락만 눈앞에 있으면 아는 사람이 1초에 끝내는 판단을 물으십시오. "이 메시지가 긴급한가?"는 그런
질문입니다. "이 메시지를 분석해 가장 좋은 조치를 고르라"는 아닙니다. 느린 추론이 필요하다는
뜻이고, 그런 일은 코드가 맡아야 합니다.

판단이 서로 독립적인 여러 요인에 달려 있으면 요인마다 따로 묻고 답을 자기 코드에서 합치십시오.
요인별로 나누면 틀린 답이 어느 요인에서 나왔는지 추적할 수 있습니다. 여러 판단을 한 질문에
섞으면 어디서 어긋났는지 보이지 않습니다.

질문은 한 요청에 모아 보내십시오. 모든 질문이 같은 상태를 보고 각자 답하므로, 질문을 더해도 응답
시간은 거의 그대로이고 지금 쓰지 않을 질문도 비용이 아주 작습니다.

## 구조화된 지시문

`instructions`는 이 필드가 있는 모든 방언에서 문자열, 객체, 배열을 받습니다. 짧고 뜻이 하나뿐인
질문은 문자열로 두십시오. 구조가 필요해지는 경우는 세 가지입니다. 질문에 배경이나 예시가 붙을 때,
질문의 일부가 코드에서 올 때, 여러 질문의 문장이 비슷해 서로 구분해야 할 때입니다.

질문은 한 필드에, 그 질문이 가리키는 데이터는 다른 필드에 넣습니다. 이 절의 JSON 조각은 요청
전체가 아니라 질문 조각이므로, 각각 요청의 질문 컨테이너 아래에 넣습니다.

```json
"same_as_record": {
  "type": "noul",
  "instructions": {
    "potential_duplicate": { "name": "John Smith", "location": "Oakland, California" },
    "question": "Is the resume for the same person as `potential_duplicate`?"
  }
}
```

System One 방언에서 요청 한 건의 최소 형태는 `state`, `model`, `questions`를 갖추면 됩니다.

```json
{
  "state": "Payouts have been failing since Monday.",
  "model": "jev-latest",
  "questions": {
    "needs_human": {
      "type": "noul",
      "instructions": "Does this ticket need a human agent, rather than an automated reply?"
    }
  }
}
```

위 두 예시의 모델 아이디는 한 벤더의 것입니다. 경로마다 받는 아이디와 그 날짜는
[`./official/jev-platform.md`](./official/jev-platform.md)와
[`./official/openai-decisions.md`](./official/openai-decisions.md)에 있습니다.

같은 질문을 OpenAI 방언으로 옮기면 입력이 `input`으로 가고, 질문에 이름이 붙고, 맵이 배열로
바뀝니다. `input` 값은 문자열, 입력 항목의 배열, 또는 `input_json`으로 넘기는 JSON 객체입니다.

```json
{
  "input": "Payouts have been failing since Monday.",
  "model": "gpt-6-luna",
  "questions": [
    {
      "type": "predicate",
      "name": "needs_human",
      "instructions": "Does this ticket need a human agent, rather than an automated reply?"
    }
  ]
}
```

질문이 구조화된 상태의 한 부분을 겨냥하면 그 부분을 백틱 안에 경로로 적으십시오. "Does
`ticket.messages[0].text` request a refund?"처럼 씁니다. 경로가 있으면 모델이 상태의 어느 조각을
판단할지 알고, 나머지 조각은 판단에 끼어들지 않습니다. 데이터베이스에서 온 값은 문자열 틀에 끼워
넣지 말고 이름 있는 필드에 따로 두십시오. 질문을 다시 쓰지 않고 값만 바꿀 수 있습니다.

출처: <https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md> 및
<https://docs.typesafe.ai/primitives/advanced.md>.

## Choice 기준

Choice는 확률이 가장 높은 선택지 하나를 돌려주므로 선택지가 서로 구분되어야 합니다. 선택지 설명은
객체로 쓸 수 있고, 그 선택지가 무엇을 덮는지, 무엇이 다른 선택지에 속하는지, 예시가 무엇인지
적습니다. 이 조각은 System One 질문 하나의 `criteria` 부분이고 요청 전체가 아닙니다.

```json
"criteria": {
  "card_setup": {
    "what": "Purpose, eligibility, or setup",
    "not_for": "Quantity, transaction, or merchant restrictions",
    "examples": ["How can I get a disposable virtual card?"]
  },
  "card_limits": {
    "what": "Quantity, transaction, or merchant restrictions",
    "not_for": "Purpose, eligibility, or setup",
    "examples": ["How many can I make per day?"]
  }
}
```

모든 선택지에서 같은 필드 이름을 쓰십시오. 그래야 모델이 나란히 비교할 수 있습니다. `not_for`는
이 패키지가 쓰는 필드 이름이고, 벤더가 제시하는 형태는 세 부분 설명입니다. 헷갈리기 쉬운
선택지일수록 이 대조가 차이를 만듭니다.

OpenAI 방언에서는 같은 내용이 `choices` 배열이 되고, 설명은 문자열이나 객체입니다.

```json
"choices": [
  { "value": "card_setup", "description": "Purpose, eligibility, or setup. Not for quantity, transaction, or merchant restrictions. Example: how can I get a disposable virtual card?" },
  { "value": "card_limits", "description": "Quantity, transaction, or merchant restrictions. Not for purpose, eligibility, or setup. Example: how many can I make per day?" }
]
```

모델에는 짧은 목록이 아니라 전체 목록을 주십시오. Choice는 선택지를 255개까지 받고 선택지를 더할
때마다 토큰이 몇 개씩 들며, 목록을 잘라 생긴 오분류가 그 토큰보다 비싸다고 벤더가 적습니다.

출처: <https://docs.typesafe.ai/primitives/choice.md>,
<https://docs.typesafe.ai/primitives.md>,
<https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions>.

## 대비책: 짝 불리언을 먼저

Choice는 아무것도 맞지 않아도 선택지 하나를 돌려주고, Box는 대상이 없어도 네 변을 돌려줍니다.
"해당 없음"은 요청 밖으로 나와야 하고, 방법이 둘입니다.

- **짝 불리언. 이 패키지는 이것을 기본으로 권합니다.** 같은 상태에 `boolean` 질문을 하나 더 두어
  "나열한 선택지 가운데 맞는 것이 있는가?"를 묻습니다. 벤더는 `other` 선택지가 실제 선택지와 확률을
  다투기 때문이라며 짝 질문 쪽으로 기울었고, 자기 시험에서 `other`나 `none of the above`보다
  "낫게 동작했다"고 적습니다. 다만 그 근거 수치는 공개하지 않았으므로 벤더 지침으로 다루고 측정된
  결과로 다루지 마십시오.
- **`other`나 `none of the above` 선택지. 여전히 쓸 만한 대안입니다.** 질문 하나로 끝나고 답 집합이
  닫힌 채로 남으며, 항목마다 결정 하나를 원하는 호출자에게는 이 경로밖에 없습니다. 확률 비용을
  받아들이고 재십시오. 그 선택지는 공짜 이름표가 아니라 실제 경쟁자입니다.

Choice에 `none`, `other`, `unknown` 선택지가 없으면 오프라인 검사기가 `NO_FALLBACK_OPTION` 경고를
냅니다. 이것은 휴리스틱이고 API 규칙이 아니며, 짝 질문은 알지 못합니다. 그래서 짝 질문을 쓴
요청에도 경고가 남습니다. 경고를 지우려고 죽은 선택지를 넣지 말고, 인계할 때 그 사실을 밝히십시오.

출처: <https://docs.typesafe.ai/primitives.md>,
<https://docs.typesafe.ai/patterns/companion-noul.md>, 벤더 지침
<https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## Score 단계는 상황으로

Score는 정해 둔 단계를 따라 확률로 가중된 위치를 돌려주고, 그 위치는 두 단계 사이에 놓일 수
있습니다. 단계마다 사람이 손가락으로 짚을 수 있는 상황을 적으십시오. "매우 화남"은 읽는 사람마다
다른 뜻이지만, "강한 표현을 쓰고 불만을 되풀이함"은 다르지 않습니다. 단계마다 설명을 붙이고
필요하면 예시 상황도 붙이십시오. 낮은 쪽 끝도 꼭 정의해야 중간 단계가 설 자리를 얻습니다.

단계는 정확한 수치를 복원하는 데 약합니다. 중간 점수는 나올 수 있지만 그 수가 실제 값을 정확히 잰
값은 아닙니다. 벤더도 자기 Score 단계가 수치 보정에 약하고, 가장 가까운 두 단계 사이를 보간해 정확한
수를 되살리지는 못한다고 적습니다. 임계값을 넘는지 보거나 정렬할 때 쓰고, 수량을 되살리는 데는 쓰지
마십시오.

단계 수는 경로마다 다릅니다. System One 방언은 1개에서 10개까지 받고 10개를 넘으면 경고하며,
b.ai는 최소 2개를 요구하고, OpenAI 방언은 2개에서 10개이며, AI SDK는 1개도 받지만 이식성 경고를
냅니다. 단계 하나로는 모든 답이 같은 점수로 접히기 때문입니다.

출처: <https://docs.typesafe.ai/primitives/score.md> 및
<https://docs.typesafe.ai/model-jaggedness.md>.

## Boolean의 true와 false 설명

예/아니오 질문에서 `criteria`는 선택 사항입니다. 쓸 때는 `true`와 `false` 두 키만 허용되고, 각
값은 그 쪽이 자기 도메인에서 무엇을 뜻하는지 적은 문자열, 객체, 배열입니다. criteria를 지시문의
연장으로 보고 두 문장의 표현을 맞추십시오. `true` 쪽 설명이 아니오처럼 읽히는 질문은 이미 알려진
실패 유형입니다.

Boolean이 돌려주는 것은 "예"일 확률 하나뿐입니다. 값이 0.5 근처면 모델이 예와 아니오에 같은 무게를
준 것이고, 이는 중간 세기의 답이 아니라 불확실입니다. 정도가 필요하면 단계를 정의한 Score를
쓰십시오.

출처: <https://docs.typesafe.ai/primitives/noul.md>.

## Box 질문

Box는 이미지 높이와 너비에 대한 비율로 네 변을 돌려주고, 결과가 없는 경우를 두지 않습니다. "찾지
못함" 답이 없으므로 대상이 없는 질문에도 네 변이 돌아옵니다. Box에는 대상이 보이는지 묻는 짝
불리언을 반드시 붙이고, 그 답으로 좌표를 걸러 쓰십시오.

Box에는 요청 안의 이미지, Jev 1.14 모델, 벤더의 이미지 헤더가 필요하고, 벤더는 이미지와 Box를
프로덕션 준비가 되지 않은 기능으로 표시합니다. Box에 기대는 경로를 그 사실 없이 내보내지 마십시오.
그 뒤의 모델 아이디와 한도, 헤더 이름은 [`./official/jev-platform.md`](./official/jev-platform.md)에
있습니다.

출처: <https://docs.typesafe.ai/primitives/box.md> 및 <https://docs.typesafe.ai/images.md>.

## 선택지 순서는 측정되는 편향입니다

Choice 선택지의 순서가 답을 바꿀 수 있고, 벤더는 자기 모델이 앞에 오는 선택지 쪽으로 기운다고
관측했습니다. 벤더가 제시하는 시험은 선택지 순서를 바꿔 답이 그대로인지 확인하는 것입니다. 같은
시험이 설명이 아니라 라벨이 선택지인 Choice에도 적용됩니다. 순서를 바꾸는 비용은 싸고, 답이
뒤집히면 그 질문은 내용이 아니라 위치로 정해지고 있다는 뜻입니다. 한 번 손으로 돌리는 대신 평가
계획에 넣으십시오.

출처: <https://docs.typesafe.ai/model-jaggedness.md>.

## 거절은 낮은 확률이 아닙니다

OpenAI 방언에는 질문마다 네 번째 답 유형이 있고, 거절은 확률이 낮은 predicate 답과 다릅니다.
거절을 `probability: 0`이나 첫 번째 선택지, 점수 0으로 바꾸지 말고 분기를 따로 두십시오. 그것은
답이 아니라 거절된 요청입니다. AI SDK는 같은 상황을 던져진 거절 오류로 드러내므로, `probability`만
읽는 코드는 잘못 읽는 대신 멈춥니다.

출처: <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> 및
<https://ai-sdk.dev/docs/ai-sdk-core/decisions>.

## state 인코딩

상태는 값 하나이고, 방언마다 싣는 방식이 다릅니다.

| 방언 | 상태가 지나는 길 | 실무 규칙 |
| --- | --- | --- |
| System One | `state`는 문자열, JSON 객체, 배열이고, 이미지는 자리표시자로 키를 잡은 `assets` 맵을 통해 `state`, `instructions`, `criteria`에 들어갑니다 | 질문이 경로를 지목하면 JSON 객체를 보내고, 이미지가 정말 판단의 일부일 때만 자리표시자와 이미지 헤더를 쓰십시오 |
| OpenAI 결정 | `input`은 문자열, 입력 항목의 배열(메시지, 도구 기록), 또는 `input_json`으로 넘기는 JSON 객체입니다 | 구조화 경로는 `input_json`이고 자체 한도가 있으므로 중첩을 얕게 두고 질문이 읽는 필드만 보내십시오 |
| AI SDK | `state`는 문자열, JSON 객체, 또는 콘텐츠 파트의 배열입니다 | JSON 배열을 그대로 보내면 콘텐츠 파트로 읽히므로 레코드는 객체로 감싸십시오 |

방언과 무관한 규칙도 있습니다. JSON 객체는 중첩 64단계 아래로 두고, 유한한 수만 보내고, 상태는
들어온 언어 그대로 두십시오. 판단 대상이 되는 내용을 옮기면 심판대에 올라간 증거 자체가
달라집니다.

출처: <https://docs.typesafe.ai/concepts/state.md>,
<https://developers.openai.com/api/reference/resources/decisions/methods/create.md>,
<https://ai-sdk.dev/docs/ai-sdk-core/decisions>.

## 후보 추출

모델은 글을 잘 만들지 못하고 셈도 믿을 수 없습니다. 두 일 모두 코드가 맡습니다. 추출 방식은
모델이 잘하는 부분에만 모델을 남깁니다.

1. 코드가 원하는 값의 후보를 열거합니다. 정규식, 파서, 또는 후보를 제안하는 생성 모델을 씁니다.
2. 결정 모델이 후보 가운데 하나를, 후보를 선택지로 둔 Choice 질문으로 고릅니다.
3. 코드가 고른 값을 후보 목록에서 그대로 복사해 정규화합니다.

벤더도 같은 분담을 권합니다. 정규식이나 생성 모델로 후보를 뽑고, 옳은 추출을 결정 모델이 고르게
하라는 것입니다.

두 부분을 따로 재십시오. 실패 원인이 서로 다릅니다.

- **후보 포함률**: 정답 값이 후보 안에 들어 있기는 한가? 이 수치가 낮으면 열거 코드의 문제이고,
  질문 문장을 고쳐도 낫지 않습니다.
- **선택 정확도**: 정답이 후보에 있었을 때 모델이 그것을 골랐는가? 이 수치가 낮으면 질문의
  문제이고, 대개 선택지가 서로 구분되지 않는 탓입니다.

끝에서 끝까지 잰 정확도 하나만 보면 어느 쪽이 고장 났는지 가려집니다. 두 수치를 함께 남기고 고장
난 쪽을 고치십시오.

출처: <https://docs.typesafe.ai/model-jaggedness.md> 및
<https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23).

## 한국어 입력

지시문은 기본적으로 영어로 쓰십시오. 벤더는 영어를 가장 잘 지원하는 언어로 설명하고, 지금 모델
계보는 이전보다 나은 다국어 지원을 광고하지만 그 개선을 잰 공개 자료는 여기 받아 둔 페이지에
없습니다.

상태는 들어온 언어 그대로 두고, 한국어 입력은 직접 시험해 볼 때까지 검증되지 않은 것으로
다루십시오.

1. 신뢰할 수 있는 라벨을 붙인 한국어 자료로 파일럿을 돌립니다.
2. 답을 라벨과 견주고 어긋난 곳을 기록합니다.
3. 신뢰도가 낮은 답을 사람에게 넘기는 관문을 두고, 근거가 얇은 동안에는 검토 구간을 넓게
   잡습니다.
4. 임계값을 맞춰 두었다면 버전이 붙은 모델 아이디를 고정해, 별칭이 조용히 옮겨가도 값이
   흔들리지 않게 합니다.

한 결정 벤더는 한국어 강점을 내세우지만 베타 상태이고, 그 요청 계약은 이 패키지가 열어 본 1차
명세에 없습니다. 벤더의 언어 주장은 시험할 가설로 다루고 파일럿을 건너뛸 이유로 쓰지 마십시오.

출처: <https://docs.typesafe.ai/changelog.md>, <https://docs.typesafe.ai/models.md>,
<https://arxiv.org/abs/2609.37647>.

## 문서로 밝힌 약점

벤더가 자기 모델의 실패 유형 아홉 가지와 우회법을 함께 적어 두었습니다. 설계 원칙은 하나로
모입니다. 판단은 모델에 맡기고 계산은 코드가 가져갑니다. 그 페이지는 더 이상 버전별로 나뉘어 있지
않으므로, 실제로 쓰는 모델에 대고 읽으십시오. 그 예시에서 임계값을 맞췄다면 그 값은 그 예시를 낸
버전에 맞춰진 것으로 다루십시오.

| 실패 유형 | 질문 설계에서의 우회법 |
| --- | --- |
| 문자 그대로 읽기: 의도가 아니라 적힌 말을 따름 | 조건을 `instructions`에 정확히 적고 경계 사례는 criteria에 넣습니다 |
| 수와 숫자: 셈과 숫자 표현이 불안정함 | 셈과 계산은 코드가 하고, 16진수나 이진수 대신 이름이나 구간을 보냅니다 |
| 날짜와 시간 비교: 날짜를 순서가 있는 값이 아니라 글로 읽음 | 닫힌 집합에 대한 Choice로 날짜 조각을 뽑고 비교는 코드가 합니다 |
| 우회 추론: 이중 부정과 여러 단계를 건너는 질문은 정확도를 잃음 | 단계를 줄이고 관련 상태 경로를 바로 지목합니다 |
| 관련 없는 내용이 많은 상태: 무관한 내용이 주의를 흐림 | 코드에서 먼저 걸러 질문에 필요한 필드만 보냅니다 |
| 적대적 내용: 상태는 데이터이고 기본적으로 적대로 다루지 않음 | criteria를 정확히 쓰고 널리 배포하기 전에 경계 사례를 시험합니다 |
| 지시문과 criteria의 충돌: 둘이 서로 다른 것을 요구함 | criteria를 지시문의 연장으로 보고 두 문장을 맞춥니다 |
| 선택지 순서: 앞 선택지가 답을 끌어당김 | 순서를 바꿔 답이 그대로인지 확인합니다 |
| 생성: 글을 만들어 내도록 훈련되지 않음 | 위의 후보 추출 방식을 쓰고 글은 코드가 다룹니다 |

출처: <https://docs.typesafe.ai/model-jaggedness.md>.

## 요청 유효성 점검표

bash나 jq가 없거나 검사기를 지운 환경처럼 오프라인 검사기를 돌릴 수 없을 때 사람이 직접 확인하는
목록입니다. `../scripts/check-decision-request.sh`의 검사를 그대로 옮겼고, 그 스크립트가 출력하는
오류 코드도 함께 적었습니다. 스크립트는 `--route systemone`, `--route openai`, `--route aisdk`,
`--route bai`를 받고, 기본값은 `systemone`입니다.

검사는 다섯 묶음입니다. 모든 경로가 공유하는 것, 컨테이너가 요구하는 것, 질문 항목이 요구하는 것,
criteria가 요구하는 것, 그리고 한 경로만 싣는 이미지 자산입니다. 실제 경로에 맞는 묶음을 읽으십시오.

**모든 경로**

1. 파일이 올바른 JSON입니다. 아니면 `INVALID_JSON`, 문서가 검사기의 파서가 읽을 수 있는 깊이보다
   깊게 중첩되면 `INPUT_TOO_DEEP`.
2. 뿌리가 JSON 객체입니다. 배열이나 스칼라가 아닙니다. 아니면 `ROOT_NOT_OBJECT`.
3. 문서 안 어느 문자열 값도 자격 증명처럼 생기지 않았습니다. 객체 키는 검사하지 않고, 그 값을 그대로
   출력하지도 않습니다. 아니면 `SECRET_IN_REQUEST`.

**컨테이너**

4. `systemone`: `state`가 있고 문자열, 객체, 배열 가운데 하나이며, `model`이 비어 있지 않은
   문자열입니다. 아니면 `STATE_MISSING`, `STATE_TYPE`, `MODEL_MISSING`. `questions`는 비어 있지 않은
   객체입니다. 아니면 `QUESTIONS_MISSING` 또는 `QUESTIONS_EMPTY`.
5. `bai`: 같은 조건에 더해 `model`이 정확히 `jev-1.13.0` 또는 `jev-latest`여야 하고
   (`MODEL_UNSUPPORTED`), `stream`이 없거나 `false`여야 하며(`STREAM_NOT_SUPPORTED`), `assets`가
   없어야 합니다(`ASSETS_NOT_SUPPORTED`).
6. `aisdk`: `state`가 있고 위와 같은 타입이며, `questions`가 비어 있지 않은 객체입니다. `model`
   필드는 없고, 최상위 `model`은 알 수 없는 필드입니다.
7. `openai`: `input`이 있고 문자열이나 비어 있지 않은 배열입니다. 필드가 없으면 `INPUT_MISSING`,
   비었거나 공백뿐인 문자열과 빈 배열은 `INPUT_EMPTY`, 그 밖의 타입은 `INPUT_TYPE`입니다. `model`이
   비어 있지 않은 문자열이고, `questions`가 1개에서 400개까지의 배열입니다(배열이 아니면
   `QUESTIONS_MISSING`, 비었으면 `QUESTIONS_EMPTY`, 400개를 넘으면 `QUESTIONS_COUNT`).

**질문 항목**

8. `systemone`과 `bai`: 각 항목이 객체이고(`QUESTION_NOT_OBJECT`), 아이디가 공백이 아니며
   (`QUESTION_ID_BLANK`), `type`이 `noul`, `choice`, `score` 가운데 하나이고 `systemone`에서만
   `box`도 됩니다(`QUESTION_TYPE`). `instructions`가 있고 문자열, 객체, 배열 가운데
   하나입니다(`INSTRUCTIONS_MISSING`, `INSTRUCTIONS_TYPE`).
9. `aisdk`: 같은 조건에 `type`이 `boolean`, `choice`, `score`, `box` 가운데 하나입니다.
10. `openai`: 각 항목이 객체이고, `type`이 `predicate`, `choice`, `score` 가운데 하나이며
    (`QUESTION_TYPE`), `name`이 비어 있지 않고 요청 안에서 유일한 문자열이고 (`QUESTION_NAME_MISSING`,
    `QUESTION_NAME_TYPE`, `QUESTION_NAME_DUPLICATE`), `criteria` 필드가 없습니다
    (`CRITERIA_NOT_SUPPORTED`).

**유형별 criteria**

11. 예/아니오(`noul` 또는 `boolean`): criteria는 선택 사항입니다. 쓸 때 각 키는 `true` 또는
    `false`이고 어느 키든 생략할 수 있으며, 값이 있는 키의 값은 문자열, 객체, 배열입니다. 아니면
    `NOUL_CRITERIA_TYPE`, `NOUL_CRITERIA_KEY`, `NOUL_CRITERIA_VALUE` 가운데 하나이고, AI SDK
    경로에서는 `BOOLEAN_` 이름으로 나옵니다.
12. `systemone`, `bai`, `aisdk`의 `choice`: criteria는 선택지 1개에서 255개까지 담은 필수 객체이고,
    선택지 설명은 `null`, 문자열, 객체, 배열 가운데 하나입니다. 아니면
    `CHOICE_CRITERIA_MISSING`, `CHOICE_CRITERIA_COUNT`, `CHOICE_CRITERIA_VALUE` 가운데 하나.
13. `openai`의 `choice`: `choices`는 2개에서 255개까지 담은 필수 배열이고, 항목마다 문자열이나
    불리언인 `value`와 선택적인 설명이 있으며, 값은 서로 달라야 합니다. 아니면
    `CHOICE_CHOICES_MISSING`, `CHOICE_CHOICES_COUNT`, `CHOICE_NOT_OBJECT`, `CHOICE_VALUE_MISSING`,
    `CHOICE_VALUE_TYPE`, `CHOICE_DESCRIPTION_TYPE`, `CHOICE_VALUE_DUPLICATE` 가운데 하나.
14. `systemone`과 `aisdk`의 `score`: criteria는 항목 1개에서 10개까지 담은 필수 배열이고, 각 항목은
    문자열, 객체, 배열 가운데 하나이며 `null`은 안 됩니다. 아니면 `SCORE_CRITERIA_MISSING`,
    `SCORE_CRITERIA_COUNT`, `SCORE_LEVEL_TYPE` 가운데 하나. 단계가 하나면 `systemone`에서는
    `SCORE_LEVELS_SINGLE`, `aisdk`에서는 `SCORE_LEVELS_PORTABILITY` 경고가 붙습니다.
15. `bai`의 `score`: 같은 조건에 2개에서 10개이므로 단계 하나는 `SCORE_CRITERIA_COUNT`입니다.
16. `openai`의 `score`: `levels`는 2개에서 10개까지 담은 필수 배열이고, 항목마다 문자열 `label`과
    선택적인 설명이 있습니다. 아니면 `SCORE_LEVELS_MISSING`, `SCORE_LEVELS_COUNT`,
    `SCORE_LEVEL_NOT_OBJECT`, `SCORE_LABEL_MISSING`, `SCORE_LABEL_TYPE`,
    `SCORE_DESCRIPTION_TYPE` 가운데 하나.
17. `box`: criteria가 없어야 합니다(`BOX_CRITERIA_UNSUPPORTED`). `systemone`은 정렬, 모델 버전,
    이미지 헤더가 문서 밖에 있으므로 `BOX_REQUIREMENTS` 경고를 더하고, `aisdk`는 공급자 하나만
    구현하므로 `BOX_PROVIDER_PORTABILITY` 경고를 더합니다.

**자산, 그 필드를 싣는 경로에서만**

18. `systemone`만: `assets`는 비어 있지 않은 객체이고(`ASSETS_TYPE`), 자산마다 객체이며
    (`ASSET_NOT_OBJECT`), `type`이 `image`가 아니면 `ASSET_TYPE`, `data_base64`를 실은 자산은
    `format`이 `png`, `jpg`, `jpeg` 가운데 하나여야 합니다(`ASSET_FORMAT`). 상태나 질문의 어느
    문자열도 가리키지 않는 자산은 `ASSET_UNREFERENCED` 경고가 됩니다.

**요청을 실패시키지 않고 남기는 경고:** 최상위 키가 그 경로의 허용 목록 밖일 때
`UNKNOWN_TOP_LEVEL_FIELD`, Choice에 `none`, `other`, `unknown` 선택지가 없을 때
`NO_FALLBACK_OPTION`, 길이를 4로 나눈 어림값이 입력과 가장 긴 질문의 합을 32,000토큰 한도 위로
밀어 올릴 때 `INPUT_LARGE`, `openai`에서 문자열 `input`이 문서상 글자 상한을 넘을 때
`INPUT_TOO_LONG`, `openai`에서 모델이 `gpt-6-luna`가 아닐 때 `MODEL_UNVERIFIED`, 그리고 위에 적은
score와 box 경고입니다.

**종료 코드.** 오류가 없으면 0, 읽을 수 없는 파일이나 검사기 파서의 깊이 한계를 넘은 문서까지
포함해 오류가 하나라도 있으면 1, 사용법 문제(파일 인자 없음, 읽을 수 없는 파일, 알 수 없는
경로)면 2입니다. 실행은 스킬 폴더에서 이렇게 합니다.

```bash
bash scripts/check-decision-request.sh --route openai path/to/request.json
```

초록불은 모양만 본 결과로 받아들이십시오. 형식이 맞는 요청도 나쁜 질문일 수 있고, 둘 가운데
어느 쪽인지는 라벨이 붙은 자료에 돌려 봐야 드러납니다.

## Sources

> Links checked 2026-11-08.

| 주장 | 출처 |
| --- | --- |
| 질문 아이디가 모델에 전달되지 않는다는 진술이 받아 둔 API 페이지에 있었음 | <https://docs.typesafe.ai/api/system-one.md> |
| 질문 맵과 `minProperties: 1`, `instructions`가 문자열, 객체, 배열을 받음 | <https://docs.typesafe.ai/api/system-one.md> 및 <https://docs.typesafe.ai/primitives/advanced.md> |
| 구조화된 지시문, 대조형 Choice 기준, 백틱 안의 상태 경로 | <https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md> |
| Choice 선택지 255개 상한과 선택지를 더할 때의 토큰 비용 | <https://docs.typesafe.ai/primitives/choice.md> |
| 원시 유형 네 가지, `other` 선택지보다 짝 불리언을 권하는 지침, 불리언 0.5의 뜻 | <https://docs.typesafe.ai/primitives.md> |
| Box 계약, 찾지 못함 답이 없다는 점, 프로덕션 준비 경고 | <https://docs.typesafe.ai/primitives/box.md> 및 <https://docs.typesafe.ai/images.md> |
| Score의 단계 수와 수치 보정이 약하다는 점 | <https://docs.typesafe.ai/primitives/score.md> 및 <https://docs.typesafe.ai/model-jaggedness.md> |
| 문서로 밝힌 약점 아홉 가지와 선택지 순서 편향 | <https://docs.typesafe.ai/model-jaggedness.md> |
| 방언별 상태 타입, 이미지 경로, 중첩과 수에 관한 요청 규칙 | <https://docs.typesafe.ai/concepts/state.md>, <https://docs.typesafe.ai/api/errors.md>, <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> |
| `predicate`, `choices`, `levels`, `input`, `input_json`, 필수 `name`, 거절 답 | <https://developers.openai.com/api/reference/resources/decisions/methods/create.md> 및 <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/decisions> |
| `boolean`, `choice`, `score`, `box` 이름, 언어 모델 어댑터에 분포가 없다는 점, 던져지는 거절 오류 | <https://ai-sdk.dev/docs/ai-sdk-core/decisions> |
| 사람 시험, 진리표로서의 결정, 층위가 틀린 질문 | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| 현재 모델 계보의 나은 다국어 지원과 영어가 가장 잘 지원되는 언어라는 설명 | <https://docs.typesafe.ai/changelog.md> 및 <https://docs.typesafe.ai/models.md> |
| 한국어 파일럿 규칙의 근거가 되는 다국어 정확도 격차 | <https://arxiv.org/abs/2609.37647> |
| 한국어 강점을 내세우는 베타 결정 벤더 | <https://developers.upstage.ai/docs/models/solar-decide.md> |
| 검사기의 경로, 코드, 종료 코드 | `../scripts/check-decision-request.sh` |

### Evidence grade

위 설계 규칙은 `PRIMARY`입니다. 각 항목이 2026-11-08에 받아 둔 벤더 문서에서 나왔고, 아이디 노출
문장만 2026-10-01에 받아 둔 같은 페이지의 벤더 진술이라 그 사실을 본문에 밝혔습니다. 검사기 항목도
`PRIMARY`이고, 설명이 아니라 이 패키지의 스크립트를 읽어 옮겼습니다. 다국어 격차는 `SECONDARY`로,
독립 프리프린트 하나에서 나왔습니다. 짝 불리언을 기본으로 두는 권장과 점검표의 묶음 구성은
`LOCAL`입니다. 전자는 벤더 지침 위에 이 패키지가 얹은 기본값이고, 후자는 스크립트 검사를 묶은 것이지
새 규칙을 더한 것이 아닙니다.

여기서 다루지 않고 스냅샷에 남긴 것: 가격, 요청 한도, 모델 아이디, 엔드포인트, 경로마다 다른
계약의 차이입니다. 그 값들은 [`./providers.md`](./providers.md)와 [`./official/`](./official/) 아래
스냅샷에 있습니다.
