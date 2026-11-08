# 인터페이스 문구

쓰기 모드가 제목, 버튼, 라벨, 빈 상태와 오류 상태, 섹션 텍스트를 쓰거나 고칠 때, 그리고 감사 발견 사항이 문구에 관한 것일 때 읽는다. 인터페이스 문구만 다룬다. 장문 글과 이메일은 범위 밖이다. 아래 모든 항목에 규칙 두 가지가 적용된다. 원문이나 사용자가 주지 않은 사실, 이름, 숫자, 날짜, 인용, 고객을 지어내지 않는다. 그리고 문구를 말투를 잃은 기본값으로 살균하지 않는다.

## 목차

- 1. 징후
- 2. 지적하지 말 것
- 3. 초안, 감사, 최종
- 4. 한국어 문구

## 1. 징후

| 징후 | 이전 | 이후 |
|---|---|---|
| 빈 어휘: unlock, elevate, empower, seamless, cutting-edge, revolutionary, next-generation, AI-powered, effortless, robust, game-changer | "Unlock seamless collaboration to elevate your team." | "Work with your team in one shared space." |
| 의미 부풀리기: "the future of", "a new era of", "a testament to" | "Ushering in a new era of work." | "Cuts the time your team spends in status meetings." |
| 이름을 대지 않는 신뢰 주장: 근거 없는 "trusted by thousands", "industry-leading", "SOC 2 compliant" | "Trusted by thousands of teams." | 실제로 쓰기 허락을 받은 고객을 밝히거나 주장을 없앤다 |
| 일반 CTA: Get started, Learn more, Try now, Explore, Discover | "Get started" | "Create a free workspace", "Book a 20-minute walkthrough" |
| 모든 목록에 강제로 적용한 셋의 법칙 | "Innovation, inspiration, and insights." | 내용이 실제로 가진 항목 수 |
| "Not just X, it's Y"와 뒤에 붙인 조각("no guessing") | "It's not just a dashboard, it's a command center." | "The dashboard opens on the jobs that failed overnight." |
| 단문 남발의 과장과 무대 지시("Read that again.") | "No templates. No defaults. No limits." | 평범한 문장 하나 |
| 거짓 범위: "from first click to final invoice" | "From onboarding to scale." | "Handles quotes, invoices, and payment reminders." |
| 행위자 없는 피동과 사람의 동사를 붙인 추상화("the dashboard understands") | "The pricing page was updated." | "We rewrote the pricing page to show the new plans." |
| 목록과 카드의 모든 단어를 대문자로 시작(Title Case) | "Instant Alerts Delivered To Slack" | "Instant alerts delivered to Slack" |
| 전부 대문자인 절과 모든 핵심어의 굵게 표시 | "WE NEED TO MOVE NOW." | 문장 자체에 담은 강조 |
| 연결자로 쓰는 엠대시(`copy.em-dash`) | "Send invoices in minutes — and get paid sooner." | "Send invoices in minutes and get paid sooner." |
| 제목과 목록 앞에 붙은 이모지 | "🚀 Launch faster" | "Launch faster" |
| 챗봇 잔재와 군더더기: "I hope this helps", "In order to", "It is important to note" | | 없앤다 |
| 아무 말도 하지 않는 빈 상태, 로딩, 오류 문구: "No data", "Something went wrong" | "No data available." | "No invoices yet. Create one to see it here." / "Payment failed: the card was declined. Try another card." |

## 2. 지적하지 말 것

세련된 표현, 격식 있는 어휘, 전환어 하나, 인용한 원문의 엠대시 하나, 짧은 강조 문장 하나, 둥근따옴표는 그 자체로 징후가 아니다. 무리를 찾는다. 구체적이고 지어내기 어려운 세부, 뒤섞인 감정, 시대가 드러나는 언급, 문장 길이의 변화는 건드리지 않는다. 사람의 흔적이다. 사용자가 직접 쓴 문장 견본은 방향이다. 그에 맞춘다. 그 견본이 `rules/delivery-gate.md`가 금지하는 패턴을 쓰면 조용히 두거나 지우지 말고 문제를 제기한다.

## 3. 초안, 감사, 최종

1. 제품 자신의 명사와 동사로 문구 초안을 쓴다.
2. 질문 두 개로 감사한다. "여기서 생성된 것처럼 읽히는 곳은 어디인가?" "원문에 없는 사실, 이름, 숫자, 날짜, 인용을 말하는 곳이 있는가?"
3. 두 답에 맞춰 고친 뒤 텍스트에서 `—`를 한 번 더 찾아본다.

## 4. 한국어 문구

같은 징후가 한국어에도 적용된다(상투 문구 "혁신적인", "끊김 없는", "차세대", "AI 기반"; 근거 없는 "수천 개 팀이 신뢰"; 일반 CTA "시작하기", "더 알아보기"). 구체적인 행동("무료 워크스페이스 만들기")을 앞세운다. 제품의 말투(격식 있는 합니다체 또는 친근한 해요체)를 한 화면에서 일관되게 유지하고 연결자로 엠대시를 쓰지 않는다.

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 징후 목록, 이전과 이후 예시, "지적하지 말 것", 사람 글의 흔적, 초안·감사·최종 루프 | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-copywriting/SKILL.md` and R-02, R-15, R-16, R-36; MIT, Copyright 2026 Miqdad Badjuber), reduced to interface copy and rewritten for this package |
| 오류 메시지는 무엇이 실패했고 어떻게 고치는지 비난 없이 말한다 | <https://www.nngroup.com/articles/error-message-guidelines/> |

### Evidence grade

측정 없는 실무자 목록이다. 출처 자체가 징후 하나는 잡음이고 무리가 신호라고 말한다.
