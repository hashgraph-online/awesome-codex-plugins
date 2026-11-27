# The checklist

The default checklist the record starts from. Rows the user adds ("느낌" items, extra
roles) join it like any other row. Korean text below is written into the record and
the sheet as is.

## Required and optional

The required areas come first. When they are all `확정`, `보류` or `해당 없음`, ask once
whether to continue with the optional areas: `필수 항목을 마쳤습니다. 레이아웃, 모션,
컴포넌트도 이어서 정할까요?`

| 영역 | 항목 | 구분 |
|---|---|---|
| 기반 | 목적과 주 사용자 | 필수 |
| 기반 | 분위기 | 필수 |
| 기반 | 출발점 | 필수 |
| 글자 | 역할 나누기 | 필수 |
| 글자 | 본문 서체, 제목 서체 | 필수 |
| 글자 | 본문 크기 | 필수 |
| 글자 | 크기 비율 | 필수 |
| 글자 | 줄 간격 | 필수 |
| 글자 | 굵기 단계 | 필수 |
| 간격 | 기본 단위 | 필수 |
| 간격 | 간격 단계 | 필수 |
| 간격 | 컴포넌트 안쪽 여백 | 필수 |
| 간격 | 묶음 사이 간격 | 필수 |
| 간격 | 밀도 | 필수 |
| 색 | 역할 나누기 | 필수 |
| 색 | 주 색 | 필수 |
| 색 | 회색 단계 | 필수 |
| 색 | 배경과 표면 | 필수 |
| 색 | 상태 색 | 필수 |
| 색 | 포커스 표시 | 필수 |
| 색 | 다크 모드 여부 | 필수 |
| 모양 | 역할 나누기 | 필수 |
| 모양 | 모서리 | 필수 |
| 모양 | 테두리 두께 | 필수 |
| 모양 | 그림자 단계 | 필수 |
| 구현 | 동작 접근성 방침 | 필수 |
| 레이아웃 | 최대 폭, 열 구성, 브레이크포인트 | 선택 |
| 모션 | 시간 단계, easing, 움직임 줄이기 대응 | 선택 |
| 컴포넌트 | 버튼, 입력창, 카드, 표, 내비게이션, 모달 | 선택 |

`역할 나누기` comes first in its area; the value rows after it follow the roles it
settled. A value row for a role the user removed becomes `해당 없음`.

## Default roles

Used only when the project has no token names for the area and the user named none
(`shared/decisions.md`, rule 4).

| 영역 | 역할 |
|---|---|
| 글자 | 큰 제목, 제목, 본문, 라벨, 보조 글, 코드 |
| 색 | 배경, 표면, 글자, 보조 글자, 테두리, 주 색, 성공, 경고, 오류, 포커스 |
| 모양 | 페이지, 컨테이너, 요소, 안쪽 |
| 간격 | 요소 안, 요소 사이, 묶음 사이, 구역 사이 |

## Default intents

Each area opens with these, in the section's first lines. The user may keep, change or
drop each one; they are recorded with the area's first pick.

**글자**
- 제목, 본문, 라벨, 보조 글은 한눈에 구분돼야 한다.
- 위계는 색만이 아니라 크기, 굵기, 위치로도 드러나야 한다.
- 여러 줄 본문은 편히 읽을 줄 간격과 줄 길이를 가져야 한다.

**간격**
- 관련 있는 것은 가깝게, 다른 묶음은 멀게 보여야 한다.
- 간격은 정해진 단계 안에서만 고른다.

**색**
- 본문 글자는 어떤 배경 위에서도 편히 읽혀야 한다.
- 의미는 색만으로 전하지 않는다. 아이콘이나 글이 함께 있어야 한다.
- 강조색은 드물게 써서 강조로 남게 한다.
- 키보드로 이동할 때 지금 위치가 늘 보여야 한다.

**모양**
- 안쪽 요소의 모서리는 감싸는 요소보다 둥글지 않아야 한다.
- 그림자가 깊을수록 실제로 위에 떠 있는 층이어야 한다.

**레이아웃**
- 긴 글은 줄이 지나치게 길어지지 않게 폭을 제한한다.

**모션**
- 움직임은 무엇이 바뀌었는지 알려 줄 때만 쓴다.
- 움직임 줄이기 설정에서는 바로 바뀌거나 짧게 바뀐다.

**컴포넌트**
- 같은 줄에 놓이는 컨트롤은 높이와 기준선이 맞아야 한다.

## Default checks

Written into each area file's `verify` when the area is first recorded. They are
measured with `check.cjs --a11y` and shown on captions; they never hide a specimen.

| 영역 | 검사 |
|---|---|
| 색 | 본문 글자 대비 4.5:1 이상, 큰 글자와 아이콘 3:1 이상, 포커스 표시 3:1 이상 |
| 컴포넌트 | 누르는 영역 44×44 이상 |
