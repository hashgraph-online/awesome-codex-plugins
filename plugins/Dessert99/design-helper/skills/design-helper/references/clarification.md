# Clarifying a design request

Ask more when the decision is less defined, not merely when the message is short.
Questions clarify intent and constraints; specimens resolve visual preferences.

## Decide what needs a question

Inspect the target and existing design system first. For each uncertainty, ask whether
different answers would produce meaningfully different comparisons or affect different
components. If not, use project conventions instead of asking. Reuse earlier answers.

Choose the most consequential unknown and ask one short question. After the answer,
reassess what remains; do not walk through a predetermined questionnaire. Explain the
reason briefly when the relevance is not obvious. Keep terminology grounded in the
user's request and the actual component.

Useful questions, only when their answers are missing:

- Purpose: `이 목록에서 지금 가장 불편한 점은 무엇인가요?`
- Scope: `이번 변경은 이 화면에만 적용하려는 건가요, 공통 카드 규칙을 바꾸려는 건가요?`
- System direction: `현재 스타일 안에서 다듬으려는 건가요, 다른 방향도 탐색하려는 건가요?`
- Conditions: `이 목록은 긴 제목이나 항목이 많은 경우도 고려해야 하나요?`
- Tradeoff: `이번에는 한눈에 보이는 정보량과 읽기 편함 중 어느 쪽이 우선인가요?`

Do not ask about scope again at apply time if already resolved.

## Examples

**Clear:** `이 카드의 radius만 비교해줘. 높이와 색은 유지해.`
Read the current radius scale and draw. No purpose interview or routine count question.

**Partly clear:** `버튼이 답답해. 다듬어줘.`
Ask where it feels cramped. If the answer is `글자가 좌우 테두리에 붙어 있어`, compare
horizontal padding while holding other properties fixed. Do not ask permission to
compare padding when that answer already establishes the problem.

**Broad:** `모달의 글 목록을 개선하고 싶어.`
Inspect it, then ask what is difficult today. If the answer is `글이 많아 찾기 어려워`,
check existing content and search/navigation behavior. Ask what identifying information
people use to find a post only if it is still unknown and changes the comparison.
Clarify density versus readability only if that tradeoff remains relevant. Draw once
the answers establish a useful comparison.

**Blank slate:** `카드를 새로 만들고 싶어.`
If the task and content are unknown, ask what the card is for. Once purpose and essential
constraints are clear, show labeled starting points. An absent design does not mean an
absent purpose, and the user need not choose aesthetic values in words first.

## When to stop

You can explain what the alternatives help decide, what stays fixed, and which target
is affected. Remaining visual uncertainty belongs in the specimens. No fixed question
count, mandatory sign-off, or repeat approval before drawing or applying a clear choice.
If a later answer changes the goal, clarify only the newly consequential uncertainty.
