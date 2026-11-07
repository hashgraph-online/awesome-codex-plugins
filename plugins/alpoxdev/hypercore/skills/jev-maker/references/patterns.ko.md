# 판단 패턴 참조

질문 하나는 좁은 판단 하나를 묻고, 호출 하나에 서로 독립된 질문을 여럿 담을 수 있습니다. 그 판단의
모양이 세 가지를 정합니다. 어떤 질문 유형을 쓸지, 코드가 여러 답을 어떻게 합칠지, 그리고 임계값이
어디에 놓일지입니다. 이 파일은 이 파일이 다루는 여덟 가지 패턴을 질문 유형과 벤더 쿡북에 이어 주고,
공식 문서가 정리한 패턴 네 가지와 신뢰도를 읽는 규칙을 담습니다.

아래 쿡북 이름과 링크는 2026-10-01에 받아 둔 벤더 쿡북 목록에서 가져왔습니다. 각 레시피가
보여 주는 임계값은 그 레시피의 예시일 뿐, 그대로 베낄 값이 아닙니다.

## Contents

- 판단 여덟 가지 모양
- 분류
- 탐지
- 점수화
- 라우팅
- 검색
- 선별
- 순위
- 검증
- 공식 패턴 네 가지
- 신뢰도 규칙
- 쿡북 목록
- Sources

## 판단 여덟 가지 모양

모양마다 맞는 질문 유형, 코드가 답을 합치는 방식, 임계값을 다루는 법, 그리고 가장 가까운 벤더
쿡북을 적었습니다.

### 분류

- **질문 유형:** 라벨 전체를 담은 Choice. 목록이 모든 입력을 덮지 못할 수 있으면 `other`를
  넣습니다.
- **합성 방식:** 코드가 고른 선택지를 분기로 옮깁니다. 층이 있는 분류 체계는 층마다 Choice를
  하나씩 두고, 아래 층은 위 층의 답이 정합니다.
- **임계값:** `confidence`로 관문을 만들고 불확실한 구간은 사람이나 상위 층으로 넘깁니다.
  확신 있는 답과 동전 던지기를 같은 통에 넣는 것이 흔한 실수입니다.
- **가까운 쿡북:** [Hierarchical classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification)

### 탐지

- **질문 유형:** 확률 자체가 신호일 때는 Noul. 예를 들어 메시지에 개인정보가 들어 있는지
  묻는 경우입니다. 탐지 대상에 정도가 있으면 Score를 씁니다.
- **합성 방식:** 코드가 확률에 임계값을 걸어 경로를 고릅니다. 같은 state를 보는 탐지기 여러
  개는 한 요청에 담고 코드에서 합칩니다.
- **임계값:** 놓쳤을 때의 손실과 잘못 걸렸을 때의 손실이 다르므로 두 방향에 보통 다른 값을
  씁니다. 둘 다 라벨이 붙은 자료로 맞추고, 두 임계값 사이에 놓인 확률은 어느 경로도 아니고 검토로
  보냅니다.
- **가까운 쿡북:** [Guardrails for LLMs](https://docs.typesafe.ai/cookbooks/llm_guardrails)

### 점수화

- **질문 유형:** 단계를 구체적인 상황으로 적은 Score. 차원마다 Score를 하나씩 두고, 합치는
  일은 내가 정한 가중치로 코드가 합니다.
- **합성 방식:** 각 Score를 같은 범위로 정규화한 뒤 가중치를 곱해 더합니다. 합쳐진 값이 틀렸을
  때 어느 차원 탓인지 알 수 있도록 원래 Score도 남겨 둡니다.
- **임계값:** Score는 임계값을 넘거나 못 넘습니다. 단계 사이에서 정확한 수치를 뽑아내려 하지
  마세요.
- **가까운 쿡북:** [Classifying RAG passages](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)

### 라우팅

- **질문 유형:** 처리기 전체를 담은 Choice. 어디로 보낼지 선택지 하나가 담당합니다. 처리기마다
  자기 몫과 옆 처리기 몫을 설명합니다.
- **합성 방식:** 코드가 답이 가리킨 분기를 부릅니다. 목적지가 인자를 필요로 하면 인자마다 닫힌
  집합에 대한 질문을 따로 만들어, 유형이 붙은 함수를 호출합니다.
- **임계값:** 라우팅 자체에 `confidence` 관문을 걸고, 불확실한 구간에는 가장 가까운 곳으로
  밀어 넣는 대신 대비책 처리기를 둡니다.
- **가까운 쿡북:** [Function calling](https://docs.typesafe.ai/cookbooks/function_calling)

### 검색

- **질문 유형:** 평범한 문장으로 된 질문에서 후보 행이나 구절 아이디를 고르는 Choice, 그리고 그
  문서에 답이 들어 있는지 확인하는 Noul.
- **합성 방식:** 코드가 후보 집합을 먼저 만들고 한 번에 보낸 뒤, 답을 그 집합을 가리키는
  포인터로 읽습니다. 글 자체는 후보에서 그대로 복사하고 새로 만들지 않습니다.
- **임계값:** Noul에는 확률 임계값을, Choice에는 신뢰도 관문을 겁니다. "이 문서에는 답이 없음"
  분기를 따로 두면 빈 결과가 정직해집니다.
- **가까운 쿡북:** [Line-by-line search](https://docs.typesafe.ai/cookbooks/semantic_find)

### 선별

- **질문 유형:** 두 가지입니다. 추린 목록에서 하나를 고를 때는 목록에 대한 Choice를 쓰고, 후보마다
  점수를 매길 때는 후보별 Score나 Noul로 매긴 뒤 코드에서 줄을 세웁니다. 목록이 작아 코드에서
  나열할 수 있으면 질의와 후보를 짝지어 질문을 하나씩 만듭니다.
- **합성 방식:** 코드가 목록을 만들고 후보 묶음마다 요청을 하나씩 보낸 뒤 상위를 남깁니다.
  검색기는 코드에 그대로 두고, 모델은 검색기가 찾아 온 것의 순서만 다시 잡습니다.
- **임계값:** 신뢰도로 자동 처리하는 경로와 사람이 검토하는 경로를 견주고, 관문이 움직일 때 두
  경로가 얼마나 같은 판단을 내리는지 봅니다.
- **가까운 쿡북:** [Re-ranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe)

### 순위

- **질문 유형:** 후보에 대한 Choice 또는 Score. 선택지를 나열한 순서는 순위가 아닙니다. 후보별
  Score로, 또는 Choice 답의 `probabilities`로 코드에서 줄을 세웁니다.
- **합성 방식:** 코드가 답을 기준으로 줄을 세우고, 첫 요청이 요약만 봤다면 상위 몇 개를 더
  자세한 state와 다시 견줍니다.
- **임계값:** 자르는 순위는 제품이 정할 일이고 모델이 정할 일이 아닙니다. 검토할 항목을 하나
  더 늘리는 비용과 놓치는 비용이 균형을 이루는 지점에 둡니다.
- **가까운 쿡북:** [Skill suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion)

### 검증

- **질문 유형:** 주장과 그 주장이 인용한 출처에 대한 Choice 또는 Noul. Noul 하나로는 "출처에 근거가
  없다"와 "출처를 확인할 수 없다"를 구분하지 못합니다. 세 상태짜리 Choice를 쓰거나, 그 출처만으로
  주장을 확인할 수 있는지 묻는 질문을 따로 둡니다.
- **합성 방식:** 코드가 주장과 출처를 state 안에 나란히 두고 짝마다 질문을 하나씩 만듭니다.
  판정은 코드의 검토 경로를 움직입니다.
- **임계값:** 근거가 없는 주장과 확인할 수 없는 주장은 서로 다른 결과입니다. 분기를 따로 두고,
  불확실한 구간은 통과가 아니라 검토로 보냅니다.
- **가까운 쿡북:** [Double-checking citations](https://docs.typesafe.ai/cookbooks/citation_check)

## 공식 패턴 네 가지

- **Speculative fan-out.** 코드가 필요로 할 수도 있는 질문을 한 호출에 모두 보냅니다. 일부
  입력에서만 쓸 답도 포함하고, 쓰지 않을 답은 코드가 무시합니다. 질문은 병렬로 돌고 자기 토큰만
  쓰므로 지금 쓰지 않을 질문의 비용은 거의 없습니다. <https://docs.typesafe.ai/patterns/fan-out>
- **Confidence-gated routing.** 답은 무엇을 할지 말하고, `confidence`는 그것을 자동으로 해도
  되는지, 물어봐야 하는지, 사람에게 넘겨야 하는지 말합니다. 답 자체에 섞지 말고 두 번째 축으로
  쓰세요. <https://docs.typesafe.ai/patterns/confidence-routing>
- **Composite scoring.** 넓은 판단을 원자적인 Score 여러 개로 쪼개고, 내가 쥔 가중치로 코드에서
  합칩니다. 합친 결과가 팀의 판단과 어긋나면 프롬프트가 아니라 가중치를 바꿉니다.
  <https://docs.typesafe.ai/patterns/composite-scoring>
- **Intent routing.** 들어온 요청을 분류해 맞는 처리기로 보냅니다. 결정적 로직, 전문 모델, 사람
  가운데 하나입니다. 분류는 모델이 하고, 라우팅 표는 코드가 쥡니다.
  <https://docs.typesafe.ai/patterns/intent-routing>

한 요청 안에서 다른 답에 기대는 질문은 답할 수 없습니다. 두 번째 질문이 첫 답을 받아야 state를
만들거나 선택지를 정하거나 데이터를 가져올 수 있다면 요청을 나눠 두 번 보내세요. 그럴 필요가
없다면 둘 다 첫 요청에 담고 코드에서 합칩니다.

## 신뢰도 규칙

- Choice와 Score 답에는 확률 분포의 모양에서 뽑아낸 0에서 1 사이의 `confidence`가 붙습니다.
  한쪽에 봉우리가 몰려 있으면 높게, 고르게 퍼져 있으면 낮게 나옵니다.
- Noul 답에는 따로 붙는 `confidence`가 없습니다. 확률 자체가 신호이고, 0.5 근처는 모델이 예와
  아니오에 같은 무게를 준 상태입니다. 이는 불확실이지 중간 세기의 답이 아니며, 세기로 읽는 것이
  대표적인 실수입니다.
- `confidence`는 뽑힌 선택지의 확률이 아닙니다. 다른 통계가 필요하면 전체 분포가
  `probabilities`에 있으니 직접 계산하세요.
- 임계값은 사용자의 자료로 평가합니다. 벤더의 예시와 쿡북의 숫자는 설명일 뿐 보편 규칙이
  아닙니다. "the correct threshold values depend on your domain and the performance of the model
  for your use case" (confidence, 2026-10-01).
- 임계값은 시스템마다 하나가 아닙니다. 동작마다 다른 관문이 어울리고, 되돌리기 어려운 동작에
  더 높은 문턱이 갑니다. 벤더 예시도 0.5 아래는 사람에게 넘기고, 되돌릴 수 있는 동작은 그냥
  처리하고, 위험한 동작 앞에서는 더 확인합니다.
- 임계값은 질문 유형이나 질문 사이를 옮겨 다니지 않습니다. 어떤 질문과 그 부정이 1로 합쳐질
  보장이 없고, Noul에서 맞춘 값을 Choice로 가져갈 수 없습니다.
- 특정 모델 버전에 맞춰 임계값을 조정했다면 그 버전 아이디를 고정하세요. 별칭이 조용히 옮겨가도
  답이 흔들리지 않습니다.

## 쿡북 목록

벤더 목록에 실린 레시피는 아래와 같습니다. 이름을 누르면 해당 페이지로 갑니다.

| 쿡북 | 보여 주는 것 |
| --- | --- |
| [Self-consistency: nouls](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook) | 불확실한 확률을 사람 검토로 넘기면서 noul 값을 계속 보이게 두기 |
| [Self-consistency: choices](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) | 검열 판단에 불확실 결과를 더하고 라벨 일치도를 견주기 |
| [Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions) | 질문 여럿을 한 호출에 담을 때의 비용과 지연을 잰 비교 |
| [Re-ranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe) | 어휘 검색기로 추린 목록을 질의와 후보 짝마다 한 질문으로 다시 세우기 |
| [Line-by-line search](https://docs.typesafe.ai/cookbooks/semantic_find) | 문서의 행을 질의에 견주고 그 문서가 답을 품었는지 확인하기 |
| [Structure recovery](https://docs.typesafe.ai/cookbooks/autoformat) | 줄을 다시 이어 붙인 뒤 블록마다 분류해 잃어버린 서식을 되살리기 |
| [Function calling](https://docs.typesafe.ai/cookbooks/function_calling) | 자연어 요청을 닫힌 집합 인자를 가진 유형 함수 호출로 바꾸기 |
| [Skill suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion) | 큰 목록의 순위를 매기고 상위 몇 개를 전문과 함께 다시 확인하기 |
| [Knowledge graph entity alignment](https://docs.typesafe.ai/cookbooks/entity_alignment) | 두 목록의 항목이 같은 제품을 가리키는지, 어긋난 필드와 함께 판단하기 |
| [Classifying RAG passages](https://docs.typesafe.ai/cookbooks/classifying_rag_passages) | 검색된 구절에 점수를 매기고 답변 모델로 보낼 것을 코드에서 고르기 |
| [Double-checking citations](https://docs.typesafe.ai/cookbooks/citation_check) | 인용문의 맥락이 주장을 받치는지 원문과 견주기 |
| [Guardrails for LLMs](https://docs.typesafe.ai/cookbooks/llm_guardrails) | 모델로 들어가고 나오는 메시지를 위험 확률과 심각도로 걸러내기 |
| [SDE cascade](https://docs.typesafe.ai/cookbooks/sde_cascade) | 값싼 단계, 확인 단계, 비싼 단계로 이어지는 추출 연쇄 |
| [Date extraction](https://docs.typesafe.ai/cookbooks/date_extraction_cookbook) | 문서가 부른 날짜 조각을 뽑고 코드에서 해석과 검증까지 하기 |
| [Pre-parsed value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook) | 정규식으로 후보를 찾고 모델이 요청한 구간을 고르게 하기 |
| [Hierarchical classification](https://docs.typesafe.ai/cookbooks/hierarchical_classification) | 깊은 라벨 계층을 Choice 확률 위의 병렬 탐색으로 내려가기 |
| [Autoresearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) | 자유로운 글을 숫자 특징으로 바꿔 하위 모델을 훈련하기 |
| [Classification using confidence](https://docs.typesafe.ai/cookbooks/classification_using_confidence) | Choice 답의 신뢰도를 읽어 세부 라벨과 상위 라벨 가운데 고르기 |

## Sources

> Links checked 2026-10-01

| 주장 | 출처 |
| --- | --- |
| 질문 유형 세 가지와 각 답의 형태, 코드가 바로 쓸 수 있는 유형을 고르라는 지침 | <https://docs.typesafe.ai/primitives> |
| Choice와 Score의 신뢰도, Noul 확률 자체가 신호라는 점, 임계값이 도메인에 달렸다는 주의 | <https://docs.typesafe.ai/confidence> |
| Composite scoring, speculative fan-out, confidence-gated routing, intent routing이 공식 패턴이라는 점 | <https://docs.typesafe.ai/patterns/confidence-routing> 및 <https://docs.typesafe.ai/patterns.md> 아래의 나머지 패턴 문서 |
| 질문 여러 개를 한 호출에 담고 답을 코드에서 합치기 | <https://docs.typesafe.ai/concepts/how-to-build-with-system-one> |
| 임계값을 질문이나 유형 사이로 옮기지 않기, 약한 Score 보간 | <https://docs.typesafe.ai/model-jaggedness/jev-1.13> |
| 쿡북 이름과 주소, 각 레시피가 보여 주는 것 | <https://docs.typesafe.ai/llms.txt> |
| 형식이 맞는다고 정답은 아니며 임계값은 대표성 있는 자료로 맞춰야 한다는 주의 | <https://docs.b.ai/llmservice/models/jev-1.13.0/> |

### Evidence grade

위 벤더 사실은 `PRIMARY`입니다. 모양과 패턴, 신뢰도 규칙이 각각 2026-10-01에 받아 둔 벤더
문서에서 나왔고, 쿡북 이름과 링크는 제3자 목록이 아니라 벤더가 낸 목록에서 가져왔습니다. 벤더
진술이 아니라 이 패키지의 권장인 부분은 `LOCAL`입니다.

판단 모양과 특정 쿡북을 이어 주는 것은 이 패키지의 권장입니다. 각 줄에 건 쿡북 페이지는 벤더의
레시피지만, 그 짝짓기는 벤더 목록이 밝히지 않은 편집상의 선택입니다.

여기서 확인되지 않아 일부러 비워 둔 것: 보편적으로 권장되는 임계값, 가격, 요청 한도, 모델
별칭입니다. 그 값들은 이 파일 옆의 플랫폼 스냅샷에 있습니다.
