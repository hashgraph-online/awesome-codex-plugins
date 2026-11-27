# Patterns to choose from

Candidates come from here, not from invention. Each category lists common patterns,
what each gains and costs, and the conditions that change the answer: draw those
conditions with the candidates. Pick two to four that genuinely differ for the task;
add the current flow as `A 지금` when there is one.

The categories follow the steps: 3 흐름 uses the flow shapes, 4 화면 구성 the screen
layouts, 5 상호작용 the rest.

## Flow shapes (step 3)

| pattern | gains | costs |
|---|---|---|
| 한 화면에서 처리 (inline) | no screen change, fastest for repeated work | little room for detail; actions can hide |
| 목록 옆 패널 (master-detail) | detail and list together, list keeps its place | needs width; cramped on small screens |
| 상세로 갔다가 돌아옴 | room for detail, a URL per item | screen changes, list position easily lost |
| 단계별 마법사 (wizard) | one decision at a time, few errors | slow for experts, hard to review the whole |
| 모달 안에서 처리 | context stays behind, focused | blocks the page; long content scrolls badly |

Conditions: how often the task repeats in a row; how much detail a decision needs;
screen width.

## Screen layout (step 4)

| pattern | gains | costs |
|---|---|---|
| 가장 중요한 정보를 위에 | the decision is visible at once | the rest needs scrolling |
| 묶음으로 나눔 (sections, cards) | scannable groups | more vertical space |
| 탭으로 나눔 | short screen | hidden content, extra clicks |
| 표 (table) | comparing many items on the same fields | narrow screens, long text |
| 목록 (list of cards) | varied content per item | weaker column comparison |

Conditions: number of items; whether people compare across items; field lengths.

## Detail view

모달, 오른쪽 패널, 새 페이지, 줄 펼치기 (expand in place). Conditions: amount of detail;
whether people go through items one after another.

## Lists with a lot of data

쪽 번호, 더 보기 버튼, 무한 스크롤, 묶어서 접기 (grouping). Conditions: 200 rows or more;
whether people return to a position; whether a total count matters.

## Search and filter

입력하는 즉시 결과, 버튼을 눌러 검색, 필터 칩, 필터 패널, 저장된 보기. Conditions: data
size and speed; how many filters are combined; whether the same filters repeat daily.

## Creating and editing

한 화면 폼, 단계별 폼, 표 안에서 바로 고치기 (inline edit), 모달 폼. Conditions: number of
fields; whether fields depend on each other; how often edits happen.

## Validation

입력 중 바로, 칸을 떠날 때, 제출할 때, 서버 확인 뒤. Conditions: whether a field's rule is
hard to guess; cost of a failed submit.

## Feedback

화면 아래 알림 (toast), 그 자리에 표시 (inline), 배너, 상태 줄 바꾸기. Conditions: whether
the result must be read later; whether the person keeps working.

## Confirming and undoing

확인 창, 되돌리기 알림 (undo), 입력해서 확인 (type to confirm), 확인 없이 바로. Conditions:
how often the action happens in a row; whether it can be reversed at all; its cost.

## Empty, loading and error

From `evaluate.md`, the state list. Each state's treatment is a candidate set: 안내 문구만,
안내와 다음 행동 버튼, 예시나 샘플 보여 주기 (empty); 자리 표시 (skeleton), 진행 표시, 이전
내용 유지 (loading); 그 자리 안내, 다시 시도 버튼, 입력 보존 (error).

## First use

빈 상태에서 안내, 단계별 둘러보기 (tour), 예시 데이터, 안내 없이 바로. Conditions: whether
the task is self-explanatory; how often new people arrive.
