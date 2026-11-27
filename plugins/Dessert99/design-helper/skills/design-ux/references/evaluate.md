# Judging a flow

Facts come from `walk.cjs` and `check.cjs`. Judgments come from the two methods below,
which are how UX practitioners inspect a design without users. Both are written on the
caption apart from the facts, so the user can tell a measurement from an opinion.

## Walkthrough (step by step)

For each step of the candidate's strip, ask the four questions of a cognitive
walkthrough. The first "no" is the step where a person would get stuck; write it.

1. Does the person know this step is what they need to do now?
2. Can they see the control that does it?
3. Will they connect that control with what they want?
4. After acting, can they tell it worked?

Write it as the step, then what blocks it, in Korean:
`2단계: 취소 버튼이 ⋯ 메뉴 안에 숨어 있어 찾기 어렵습니다.` No step blocks: say so.

## Principles (only when broken)

Nielsen's ten usability heuristics. Name one only when the candidate breaks it, with the
step. Korean names to use:

| heuristic | 이름 | broken when, for example |
|---|---|---|
| Visibility of system status | 상태가 보이지 않음 | nothing shows that saving or loading is happening |
| Match with the real world | 쓰는 말과 다름 | labels in system terms (`상태 코드 3`) |
| User control and freedom | 되돌리기 없음 | a destructive action is final at once, no undo or cancel |
| Consistency and standards | 일관성 없음 | the same action looks or sits differently across screens |
| Error prevention | 실수를 막지 못함 | an easy slip leads straight to a costly result |
| Recognition over recall | 기억에 의존함 | the person must remember something from a previous screen |
| Flexibility and efficiency | 반복이 느림 | a frequent task has no shortcut or bulk path |
| Minimalist design | 불필요한 정보가 많음 | the key information competes with what isn't needed now |
| Error recovery | 오류에서 빠져나오기 어려움 | an error says what failed but not what to do |
| Help and documentation | 안내 없음 | a first-time person has no way to learn the step |

## States

The states a flow can reach. In step 6, draw those the chosen flow can actually reach.

| 상태 | what to show |
|---|---|
| 정상 | the ordinary case, real data |
| 처음 | nothing created yet: what this is and how to start |
| 결과 없음 | a search or filter found nothing: why, and how to widen it |
| 불러오는 중 | something is happening; keep the layout from jumping |
| 오류 | what failed, whether data was lost, what to do next |
| 일부만 성공 | some items worked and some didn't: which, and what next |
| 많음 | far more data than usual: paging, grouping, performance |
| 긴 글 | long names and text: wrapping, truncation, tooltips |
| 권한 없음 | the person can see but not act, or can't see: why |

## The recommendation

Weigh the facts first (fewer steps, no lost place, keyboard completion), then the
walkthrough, then broken principles. When they disagree, say which one decided it.
