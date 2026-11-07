# 질문 설계 참조

Jev 요청은 `state` 하나와 유형이 붙은 질문 묶음입니다. 답을 쓸 수 있는지 없는지는 질문이
정합니다. 질문마다 좁은 판단 하나만 묻고, 뜻은 전부 `instructions` 안에 담고, 이웃한 선택지
사이의 경계를 분명히 그어야 합니다. 이 파일은 그 습관, 코드가 주도권을 쥐는 추출 방식, 한국어
입력을 다루는 법, 현재 버전에서 알려진 한계와 우회법, 그리고 오프라인 검사기를 쓸 수 없을 때
사람이 직접 돌리는 점검표를 담습니다.

가격, 한도, 모델 아이디는 맨 끝에 링크한 플랫폼 스냅샷에 있고 여기에는 없습니다.

## Contents

- 질문 아이디는 모델에 전달되지 않습니다
- 질문 하나에 판단 하나
- 구조화된 지시문
- Choice 기준: what, not_for, examples
- Score 단계는 상황으로
- Noul의 true와 false 설명
- 후보 추출
- 한국어 입력
- jev-1.13의 한계와 우회법
- 요청 유효성 점검표
- Sources

## 질문 아이디는 모델에 전달되지 않습니다

벤더 문서는 질문 아이디가 "모델에 전달되지 않고 추론에도 쓰이지 않는다"고 적습니다 (api,
2026-10-01). `refund_requested` 같은 아이디는 코드가 답을 찾는 이름표일 뿐입니다. 모델이 읽는
것은 `instructions`이므로 질문의 뜻은 전부 거기에 있어야 합니다. 아이디만 보면 뜻이 분명해
보이는 순간이 가장 위험합니다. 지시문을 대충 쓰고 지나가면 아무도 쓰지 않은 질문에 답이
돌아옵니다.

## 질문 하나에 판단 하나

맥락만 눈앞에 있으면 아는 사람이 1초에 끝내는 판단을 물으세요. "이 메시지가 긴급한가?"는 그런
질문입니다. "이 메시지를 분석해 가장 좋은 조치를 고르라"는 아닙니다. 느린 추론이 필요하다는
뜻이고, 그런 일은 코드가 맡아야 합니다.

판단이 서로 독립적인 여러 요인에 달려 있으면 요인마다 따로 묻고 답을 자기 코드에서 합치세요.
요인별로 나누면 틀린 답이 어느 요인에서 나왔는지 추적할 수 있습니다. 여러 판단을 한 질문에
섞으면 어디서 어긋났는지 보이지 않습니다.

질문은 한 요청에 모아 보내세요. 모든 질문이 같은 state를 보고 각자 답하므로, 질문을 더해도
응답 시간은 거의 그대로이고 지금 쓰지 않을 질문도 비용이 아주 작습니다.

## 구조화된 지시문

`instructions`는 문자열, 객체, 배열을 받습니다. 짧고 뜻이 하나뿐인 질문은 문자열로 두세요.
구조가 필요해지는 경우는 세 가지입니다. 질문에 배경이나 예시가 붙을 때, 질문의 일부가 코드에서
올 때, 여러 질문의 문장이 비슷해 서로 구분해야 할 때입니다.

질문은 한 필드에, 그 질문이 가리키는 데이터는 다른 필드에 넣습니다. 이 절과 Choice 기준 절의 JSON
조각은 요청 전체가 아니라 질문 조각이므로, 각각 요청의 `questions` 아래에 넣습니다.

```json
"same_as_record": {
  "type": "noul",
  "instructions": {
    "potential_duplicate": { "name": "John Smith", "location": "Oakland, California" },
    "question": "Is the resume for the same person as `potential_duplicate`?"
  }
}
```

요청 한 건의 최소 형태는 `state`, `model`, `questions`를 갖추면 되고, 두 직접 경로에서 모두
검사기를 통과합니다.

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

질문이 구조화된 state의 한 부분을 겨냥하면 그 부분을 백틱 안에 경로로 적으세요. "Does
`ticket.messages[0].text` request a refund?"처럼 씁니다. 경로가 있으면 모델이 state의 어느
조각을 판단할지 알고, 나머지 조각은 판단에 끼어들지 않습니다. 데이터베이스에서 온 값은 문자열
틀에 끼워 넣지 말고 이름 있는 필드에 따로 두세요. 질문을 다시 쓰지 않고 값만 바꿀 수 있습니다.

## Choice 기준: what, not_for, examples

Choice는 확률이 가장 높은 선택지 하나를 돌려줍니다. 그러니 선택지가 서로 구분되어야 합니다.
선택지 설명은 객체로 쓸 수 있고, 그 선택지가 무엇을 덮는지, 무엇이 다른 선택지에 속하는지,
예시가 무엇인지 적습니다. 이 조각은 질문 하나의 `criteria` 부분이고 요청 전체가 아닙니다.

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

모든 선택지에서 같은 필드 이름을 쓰세요. 그래야 모델이 나란히 비교할 수 있습니다. `not_for`는
이 패키지가 쓰는 필드 이름이고, 벤더가 제시하는 형태는 세 부분 설명입니다. 헷갈리기 쉬운
선택지일수록 이 대조가 차이를 만듭니다.

목록이 모든 입력을 덮지 못할 수 있으면 `other`나 `none of the above` 같은 대비책 선택지를
넣으세요. 어디에도 맞지 않는 요청이 가장 가까운 선택지로 밀려 들어가는 대신 "해당 없음"으로
보고됩니다. Choice에 `none`, `other`, `unknown` 키가 없으면 오프라인 검사기가
`NO_FALLBACK_OPTION` 경고를 냅니다. 이 검사는 휴리스틱이며 벤더 규칙이 아닙니다.

## Score 단계는 상황으로

Score는 정해 둔 단계를 따라 확률로 가중된 위치를 돌려주고, 그 위치는 두 단계 사이에 놓일 수
있습니다. 단계마다 사람이 손가락으로 짚을 수 있는 상황을 적으세요. "매우 화남"은 읽는 사람마다
다른 뜻이지만, "강한 표현을 쓰고 불만을 되풀이함"은 다르지 않습니다. 단계마다 설명을 붙이고
필요하면 예시 상황도 붙이세요. 낮은 쪽 끝도 꼭 정의해야 중간 단계가 설 자리를 얻습니다.

단계는 정확한 수치를 복원하는 데 약합니다. 중간 점수는 나올 수 있지만 그 수가 실제 값을 정확히
잰 값은 아닙니다. 임계값을 넘는지 보거나 정렬할 때 쓰고, 수량을 되살리는 데는 쓰지 마세요.

## Noul의 true와 false 설명

Noul에서 `criteria`는 선택 사항입니다. 쓸 때는 `true`와 `false` 두 키만 허용되고, 각 값은 그
쪽이 자기 도메인에서 무엇을 뜻하는지 적은 문자열, 객체, 배열입니다. criteria를 지시문의 연장으로
보고 두 문장의 표현을 맞추세요. `true` 쪽 설명이 아니오처럼 읽히는 Noul은 이미 알려진 실패
유형입니다.

Noul이 돌려주는 것은 "예"일 확률 하나뿐입니다. 값이 0.5 근처면 모델이 예와 아니오에 같은 무게를
준 것이고, 이는 중간 세기의 답이 아니라 불확실입니다. 정도가 필요하면 단계를 정의한 Score를
쓰세요.

## 후보 추출

모델은 글을 잘 만들지 못하고 셈도 믿을 수 없습니다. 두 일 모두 코드가 맡습니다. 추출 방식은
모델이 잘하는 부분에만 모델을 남깁니다.

1. 코드가 원하는 값의 후보를 열거합니다. 정규식, 파서, 또는 후보를 제안하는 생성 모델을 씁니다.
2. Jev가 후보 가운데 하나를 Choice 질문으로 고릅니다.
3. 코드가 고른 값을 후보 목록에서 그대로 복사해 정규화합니다.

벤더도 같은 분담을 권합니다. "extract possible options using regex or a generative model and let
jev-1.13 pick the correct extraction" (jaggedness, 2026-10-01).

두 부분을 따로 재세요. 실패 원인이 서로 다릅니다.

- **후보 포함률**: 정답 값이 후보 안에 들어 있기는 한가? 이 수치가 낮으면 열거 코드의 문제이고,
  질문 문장을 고쳐도 낫지 않습니다.
- **선택 정확도**: 정답이 후보에 있었을 때 모델이 그것을 골랐는가? 이 수치가 낮으면 질문의
  문제이고, 대개 선택지가 서로 구분되지 않는 탓입니다.

끝에서 끝까지 잰 정확도 하나만 보면 어느 쪽이 고장 났는지 가려집니다. 두 수치를 함께 남기고
고장 난 쪽을 고치세요.

## 한국어 입력

지시문은 기본적으로 영어로 쓰세요. 영어가 벤더의 주 훈련 언어이고 정확도가 가장 높습니다. 다른
언어는 CJK 문자권까지 포함해 처리되지만 같은 수준은 아닙니다 (models, 2026-10-01).

state는 들어온 언어 그대로 두세요. 판단 대상이 되는 내용을 옮기면 심판대에 올라간 증거 자체가
달라집니다. 모델은 주어진 state를 그대로 읽습니다.

한국어는 벤더가 가장 잘 다루는 범위 밖이므로, 직접 시험해 볼 때까지는 검증되지 않은 것으로
다루세요.

1. 신뢰할 수 있는 라벨을 붙인 한국어 자료로 파일럿을 돌립니다.
2. 답을 라벨과 견주고 어긋난 곳을 기록합니다.
3. 신뢰도가 낮은 답을 사람에게 넘기는 관문을 두고, 근거가 얇은 동안에는 검토 구간을 넓게
   잡습니다.
4. 임계값을 맞춰 두었다면 버전이 붙은 모델 아이디를 고정해, 별칭이 조용히 옮겨가도 값이
   흔들리지 않게 합니다.

## jev-1.13의 한계와 우회법

벤더가 이 버전의 알려진 실패 유형 아홉 가지와 우회법을 함께 적어 두었습니다 (jaggedness,
2026-10-01). 설계 원칙은 하나로 모입니다. 판단은 모델에 맡기고 계산은 코드가 가져갑니다.

| 실패 유형 | 질문 설계에서의 우회법 |
| --- | --- |
| 문자 그대로 읽기: 의도가 아니라 적힌 말을 따름 | 조건을 `instructions`에 정확히 적고 경계 사례는 criteria에 넣습니다 |
| 수와 숫자: 셈과 숫자 표현이 불안정함 | 셈과 계산은 코드가 하고, 16진수나 이진수 대신 이름이나 구간을 보냅니다 |
| 날짜와 시간 비교: 날짜를 순서가 있는 값이 아니라 글로 읽음 | 닫힌 집합에 대한 Choice로 날짜 조각을 뽑고 비교는 코드가 합니다 |
| 우회 추론: 이중 부정과 여러 단계를 건너는 질문은 정확도를 잃음 | 단계를 줄이고 관련 state 경로를 바로 지목합니다 |
| 관련 없는 내용이 많은 state: 무관한 내용이 주의를 흐림 | 코드에서 먼저 걸러 질문에 필요한 필드만 보냅니다 |
| 적대적 내용: state는 데이터이고 기본적으로 적대로 다루지 않음 | criteria를 정확히 쓰고 널리 배포하기 전에 경계 사례를 시험합니다 |
| 지시문과 criteria의 충돌: 둘이 서로 다른 것을 요구함 | criteria를 지시문의 연장으로 보고 두 문장을 맞춥니다 |
| 상식적 구조 불변식: 질문과 그 부정이 1로 합쳐질 필요가 없음 | 한 질문이나 한 유형에서 맞춘 임계값을 다른 곳으로 옮기지 않습니다 |
| 생성: 글을 만들어 내도록 훈련되지 않음 | 위의 후보 추출 방식을 쓰고 글은 코드가 다룹니다 |

같은 문서에서 하나 더. Score 출력은 두 단계 사이의 정확한 수치를 되살리는 데 약합니다. 값이
임계값을 넘는지는 판단하지만 값을 복원하지는 못합니다.

## 요청 유효성 점검표

bash나 jq가 없거나 검사기를 지운 환경처럼 오프라인 검사기를 돌릴 수 없을 때 사람이 직접 확인하는
목록입니다. `../scripts/check-jev-request.sh`의 검사를 하나씩 그대로 옮겼고, 그 스크립트가
출력하는 오류 코드도 함께 적었습니다.

**문서 전체**

1. 파일이 올바른 JSON입니다. 아니면 `INVALID_JSON`, 문서가 검사기의 파서가 읽을 수 있는 깊이보다
   깊게 중첩되면 `INPUT_TOO_DEEP`.
2. 뿌리가 JSON 객체입니다. 배열이나 스칼라가 아닙니다. 아니면 `ROOT_NOT_OBJECT`.
3. `state`가 있고 문자열, 객체, 배열 가운데 하나입니다. `null`, 숫자, 불리언은 거부됩니다.
   아니면 `STATE_MISSING` 또는 `STATE_TYPE`.
4. `model`이 비어 있지 않은 문자열입니다. 아니면 `MODEL_MISSING`.
5. 모델 아이디가 경로에 맞습니다. 직접 경로는 `jev-`로 시작하고(확인되지 않은 별칭은
   `MODEL_UNVERIFIED` 경고), b.ai는 `jev-1.13.0` 또는 `jev-latest`이며, AI SDK는 비어 있지 않은
   문자열이면 됩니다. 아니면 `MODEL_UNSUPPORTED`.

**질문 묶음**

6. `questions`가 비어 있지 않은 객체입니다. 아니면 `QUESTIONS_MISSING` 또는 `QUESTIONS_EMPTY`.
7. 아이디마다 공백이 아닌 글자가 있습니다. 아니면 `QUESTION_ID_BLANK`.
8. 각 항목이 JSON 객체입니다. 아니면 `QUESTION_NOT_OBJECT`. `type`이나 `instructions` 필드가
   없는 경우는 이 코드가 아니라 아래 9번과 10번이 잡습니다.
9. `type`이 해당 경로의 이름 가운데 하나입니다. 직접 경로와 b.ai는 `noul`, `choice`, `score`,
   AI SDK는 `boolean`, `choice`, `score`입니다. 아니면 `QUESTION_TYPE`.
10. `instructions`가 있고 문자열, 객체, 배열 가운데 하나입니다. 아니면
    `INSTRUCTIONS_MISSING` 또는 `INSTRUCTIONS_TYPE`.

**유형별 criteria**

11. 예/아니오(`noul`, AI SDK에서는 `boolean`): criteria는 선택 사항입니다. 쓸 때 각 키는 `true`
    또는 `false`이고 어느 키든 생략할 수 있으므로, 빈 객체와 키 하나짜리 객체가 모두 통과합니다.
    값이 있는 키의 값은 문자열, 객체, 배열입니다. 아니면 `NOUL_CRITERIA_TYPE`,
    `NOUL_CRITERIA_KEY`, `NOUL_CRITERIA_VALUE` 가운데 하나.
12. `choice`: criteria는 선택지 1개에서 255개까지 담은 필수 객체이고, 선택지 설명은 `null`,
    문자열, 객체, 배열 가운데 하나입니다. 아니면 `CHOICE_CRITERIA_MISSING`,
    `CHOICE_CRITERIA_COUNT`, `CHOICE_CRITERIA_VALUE` 가운데 하나.
13. `score`: criteria는 항목 2개에서 10개까지 담은 필수 배열이고, 각 항목은 문자열, 객체, 배열
    가운데 하나이며 `null`은 안 됩니다. 아니면 `SCORE_CRITERIA_MISSING`,
    `SCORE_CRITERIA_COUNT`, `SCORE_LEVEL_TYPE` 가운데 하나. AI SDK 경로에서는 10개를 넘겨도
    경고에 그칩니다. 그 경로가 상한을 문서에 두지 않았지만 요청이 다른 경로로 옮겨지지 않기
    때문입니다.

12번과 13번의 255개, 2개에서 10개라는 경계는 오프라인 검사기가 강제하는 값입니다. 그 뒤에 있는
벤더 설명은 [플랫폼 스냅샷](../references/official/jev-platform.md)에서 읽으세요. 예/아니오
criteria의 값과 score 단계에서 `null` 설명을 막는 것도 검사기 자체의 제약이고 직접 경로 문서와
맞습니다. AI SDK 경로 문서는 `null` 설명을 허용하므로 이것은 AI SDK 규칙이 아닙니다.

**경로별 항목과 공통 항목**

14. b.ai에서는 `stream`이 없거나 `false`입니다. 아니면 `STREAM_NOT_SUPPORTED`.
15. 문서 안 어느 문자열 값도 자격 증명처럼 생기지 않았습니다. 객체 키는 검사하지 않고, 그 값을
    그대로 출력하지도 않습니다. 아니면 `SECRET_IN_REQUEST`. 검사기는 `sk-` 뒤에 영숫자 16자
    이상이 붙은 형태와, 대소문자를 구분하는 `Bearer ` 뒤에 `[A-Za-z0-9._-]` 문자가 16자 이상
    붙은 형태를 찾습니다.

**요청을 실패시키지 않고 남기는 경고:** 최상위 키가 `state`, `model`, `questions`, `stream`
밖일 때 `UNKNOWN_TOP_LEVEL_FIELD`, 선택지가 1개에서 255개이면서 `none`, `other`, `unknown`
선택지가 없을 때 `NO_FALLBACK_OPTION`, 길이를 4로 나눈 어림값이 state와 가장 긴 질문의 합을
API 예산 위로 밀어 올릴 때 `STATE_LARGE`, 직접 경로의 별칭이 알려진 목록 밖일 때
`MODEL_UNVERIFIED`.

**종료 코드.** 오류가 없으면 0, 읽을 수 없는 파일이나 검사기 파서의 깊이 한계를 넘은 문서까지 포함해
오류가 하나라도 있으면 1, 사용법 문제(파일 인자 없음, 읽을 수 없는 파일, 알 수 없는 경로)면
2입니다. 실행은 스킬 폴더에서 이렇게 합니다.

```bash
bash scripts/check-jev-request.sh --route direct path/to/request.json
```

초록불은 모양만 본 결과로 받아들이세요. 형식이 맞는 요청도 나쁜 질문일 수 있고, 둘 가운데
어느 쪽인지는 라벨이 붙은 자료에 돌려 봐야 드러납니다.

## Sources

> Links checked 2026-10-01

| 주장 | 출처 |
| --- | --- |
| 질문 아이디는 모델에 전달되지 않고 추론에도 쓰이지 않음 | <https://docs.typesafe.ai/api> |
| `instructions`가 문자열, 객체, 배열을 받고 질문 필드와 데이터 필드로 나뉠 수 있음 | <https://docs.typesafe.ai/api> |
| 구조화된 지시문, what과 not_for와 examples로 이루어진 대조형 Choice 기준, 백틱 안의 state 경로 | <https://docs.typesafe.ai/concepts/how-to-build-with-system-one> |
| Choice, Score, Noul 지침, `other` 또는 `none of the above` 선택지, Noul의 0.5가 지니는 뜻 | <https://docs.typesafe.ai/primitives> |
| 신뢰도가 Choice와 Score 답에만 붙음 | <https://docs.typesafe.ai/confidence> |
| 실패 유형 아홉 가지와 우회법, 코드가 맡는 추출 분담, 약한 Score 보간 | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| 영어가 주 훈련 언어이고 CJK를 포함한 다른 언어에는 주의가 필요하다는 설명 | <https://docs.typesafe.ai/models> |
| 옆의 패턴 파일에 적은 레시피 이름을 확인한 쿡북 목록 | <https://docs.typesafe.ai/llms.txt> |

점검표는 이 패키지의 `../scripts/check-jev-request.sh`를 2026-10-01에 읽고 옮겼습니다.

### Evidence grade

설계 규칙은 모두 `PRIMARY`입니다. 각 항목이 2026-10-01에 받아 표에 적은 벤더 문서에서
나왔습니다. 요청 유효성 점검표는 `LOCAL`입니다. 벤더 주장이 아니라 저장소 검사기의 규칙과 오류
코드를 그대로 옮긴 것이고, 그 검사기 자체도 같은 벤더 문서를 근거로 삼습니다.

여기서 다루지 않고 스냅샷에 남긴 것: 가격, 요청 한도, 모델 아이디, 엔드포인트, 경로마다 다른
계약의 차이입니다.
