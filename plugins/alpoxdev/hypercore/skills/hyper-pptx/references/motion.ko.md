# 모션

덱이 한꺼번에 나타나지 않아야 할 때, 장 사이 전환을 걸 때, 애니메이션 이름이 왜 거부됐는지 물을 때 읽습니다.

## Contents

- 모션의 비용
- 전환은 슬라이드에 붙는다
- 애니메이션은 도형에 붙는다
- 아홉 가지 효과가 쓰는 것
- 역할과 대상
- 타이밍 트리 안의 id
- 의도적으로 넣지 않은 것
- 확인한 것과 확인하지 못한 것

## 모션의 비용

모션은 이 패키지에서 조용히 실패하는 유일한 부분입니다. 틀린 전환 이름이나 중복된 시간 노드 id는 파일 열기를 막지 않습니다. 파워포인트가 복구를 제안하고, 복구가 끝나면 슬라이드가 사라집니다. 이 기기에 파워포인트가 없어 재생을 확인할 수 없으므로, 아래 규칙은 작성기가 스키마가 보장하는 것 안에 머물게 하려고 있습니다.

그래서 스킬 전체에 두 가지가 이어집니다.

- 모든 이름은 배치 단계에서 닫힌 목록과 대조합니다. 모르는 이름은 가까운 이름으로 바꾸지 않고 오류입니다.
- 애니메이션 대상은 배치 단계가 부여한 도형 id입니다. 작성자가 짐작한 이름으로 쓰지 않습니다.

기본값은 모션 없음입니다. `transition`과 `animation`이 없는 덱은 모션이 생기기 전과 같은 바이트를 냅니다.

## 전환은 슬라이드에 붙는다

```json
{ "transition": "fade" }
{ "transition": { "effect": "push", "speed": "fast" } }
{ "transition": false }
```

덱의 `transition`은 모든 슬라이드의 기본값이고, 슬라이드가 덮어쓸 수 있습니다. `false`와 `"none"`은 둘 다 이 슬라이드에 전환이 없다는 뜻입니다. 만들어진 요소는 `p:transition`의 직계 자식 하나이며, 그 `p:transition`이 `p:sld`의 직계 자식입니다.

```xml
<p:transition spd="med"><p:fade/></p:transition>
```

| 효과 | 하는 일 |
|---|---|
| `fade` | 페이지를 교차 페이드 |
| `cut` | 섞지 않고 교체 |
| `dissolve` | 임의 픽셀 디졸브 |
| `push` | 새 페이지가 `dir`에서 밀고 들어옴 |
| `wipe` | `dir` 방향으로 새 페이지를 드러냄 |
| `cover` | 새 페이지가 이전 페이지를 덮음 |
| `split` | 가운데에서 양쪽으로 열림 |
| `strips` | 세로 띠 교체 |
| `zoom` | 새 페이지가 커지며 등장 |
| `plus` | 두 축으로 열림 |
| `pull` | 이전 페이지가 `dir`로 끌려 나감 |
| `randomBar` | 막대가 임의 순서로 |
| `checker` | 사각 격자 |
| `blinds` | 가로 블라인드 |
| `diamond` | 마름모 와이프 |
| `circle` | 원 와이프 |
| `wedge` | 쐐기 와이프 |
| `wheel` | 살 하나 |
| `random` | 임의 효과 |
| `comb` | 빗살 와이프 |
| `newsflash` | 나타났다 줄어듦 |
| `morph` | 파워포인트 2019 이상 개체 변형 |
| `none` | 전환 없음 |

방향은 필드가 아닙니다. 방향을 받는 효과는 스키마에서 값이 고정돼 있습니다(`p:push`는 `dir="u"`). 작성자가 정한 방향은 파워포인트가 무시하므로, 설명과 다르게 움직입니다. 작성기는 효과에 맞는 값을 그대로 냅니다.

`spd`는 `slow`, `med`, `fast`입니다. `morph`는 밀리초 단위 `p14:dur`도 함께 기록합니다. 파워포인트 2019가 읽는 속성이며, `spd`는 이전 판을 위해 남깁니다.

## morph만 감싼다

`morph`는 ECMA-376 요소가 아닙니다. `p159` 이름 공간의 마이크로소프트 확장이므로 `mc:AlternateContent` 안에 씁니다. `p159`를 요구하는 `Choice`가 morph를 들고, `Fallback`이 평범한 페이드를 듭니다. 확장을 모르는 판은 대체를 골라 파일을 거부하지 않고 페이드를 보여줍니다.

이 패키지가 마크업 호환을 쓰는 곳은 여기 하나입니다. 나머지 전환은 파워포인트가 필요로 하지 않는 이름 공간 선언을 늘리지 않으려고 그냥 요소로 냅니다.

## 애니메이션은 도형에 붙는다

```json
{ "animation": [
    { "effect": "fade", "target": "title", "trigger": "on-click" },
    { "effect": "fly", "target": "body", "direction": "up", "delay": 100 },
    { "effect": "grow", "target": "chart", "trigger": "after-previous" }
] }
```

| 필드 | 기본값 | 뜻 |
|---|---|---|
| `effect` | `fade` | 아래 아홉 중 하나 |
| `target` | `all` | 역할, 도형 id, 또는 둘의 배열 |
| `trigger` | `on-click` | `on-click`, `with-previous`, `after-previous` |
| `direction` | `up` | `up`, `down`, `left`, `right`이며 `fly`와 `wipe`가 씀 |
| `duration` | `500` | 밀리초 |
| `delay` | `0` | 트리거 뒤 지연 밀리초 |

## 아홉 가지 효과가 쓰는 것

| 효과 | 갈래 | 쓰는 것 |
|---|---|---|
| `appear` | 등장 | `style.visibility`에 대한 `p:set` |
| `fade` | 등장 | 그 `p:set`과 `p:animEffect filter="fade"` |
| `wipe` | 등장 | `p:animEffect filter="wipe(dir)"` |
| `split` | 등장 | `p:animEffect filter="barn(inVertical)"` |
| `fly` | 등장 | 슬라이드 밖에서 들어오는 `ppt_x`·`ppt_y`의 `p:anim` |
| `zoom` | 등장 | 너비와 높이를 0에서 키우는 `p:anim` 둘 |
| `grow` | 강조 | `p:animScale by="150000,150000"` |
| `spin` | 강조 | 한 바퀴 도는 `p:animRot by="21600000"` |
| `exitFade` | 퇴장 | `p:animEffect filter="fade"` 뒤에 숨기는 `p:set` |

등장이 먼저 숨김에서 시작하는 이유는 `visible`로 만드는 `p:set`이 앞에서 돌기 때문입니다.이것이 없으면 도형은 슬라이드가 뜨는 순간 이미 보이고, 등장이 드러낼 것이 없습니다. 퇴장은 반대이며, 숨김 `p:set`은 `duration - 1` 밀리초 뒤로 미뤄 페이드가 끝나기 전에 사라지지 않게 합니다.

프리셋 id는 효과가 사용자 지정 애니메이션이 아니라 애니메이션 창에 자기 이름으로 보이게 합니다. `appear` 1, `fly` 2, `grow` 6, `spin` 8, `fade` 10, `split` 16, `wipe` 22, `zoom` 23입니다.

## 역할과 대상

작성자는 이름을 쓰고 슬라이드는 id를 가집니다. 둘 다 배치 단계에서 같은 도형 id로 풀립니다.

| 대상 | 맞는 것 |
|---|---|
| `all` | 내용 도형 전부, 장식과 쪽 정보는 건너뜀 |
| `title`, `body`, `kicker`, `table`, `chart`, `image`, `decor` | 그 역할을 가진 도형 |
| `s1` … `i1` … | 배치 단계가 부여한 도형 id |

`all`이 장식을 건너뛰는 것은 의도입니다. 제목 아래 규칙선, 배경 블록, 쪽 번호가 움직이면 페이지가 청중 앞에서 스스로 조립되는 것처럼 보이고, 이는 양식이 아니라 실수로 읽힙니다.

역할을 선언하지 않은 도형에도 역할이 있습니다. 글자는 `body`, 나머지는 `decor`입니다. 이 기본값이 없으면 작성자는 덱이 생기기 전에 id를 알아야 합니다.

아무 도형도 맞지 않는 대상은 `ANIMATION_TARGET_EMPTY`입니다. 대상 없는 타이밍 트리도 파일은 열리고, 증상은 발표 중에야 드러나는, 영원히 나타나지 않는 도형입니다.

## 타이밍 트리 안의 id

시간 노드 id는 덱 전체가 아니라 슬라이드 안에서 유일합니다. 애니메이션 행마다 id 네 개(행, 표시 설정, 최대 동작 노드 둘)를 잡고 클릭 묶음 래퍼가 하나를 쓰므로, 카운터는 대상마다 4, 묶음마다 1씩 올라갑니다. `pp_check_motion`이 기록된 XML을 다시 읽어 세 경우에 렌더를 실패시킵니다.

| 조건 | 코드 |
|---|---|
| 한 슬라이드에 `p:timing`이 둘 이상 | `MOTION_INVALID` |
| 슬라이드 안에서 `p:cTn id`가 반복 | `MOTION_INVALID` |
| 슬라이드에 없는 도형을 지목하는 `p:spTgt spid` | `MOTION_INVALID` |

이 셋이 복구 대화상자를 부르거나 조용히 아무 일도 하지 않는 실패 방식입니다. 렌더된 덱에 중복 id와 없는 대상을 주입해 둘 다 보고되는 것을 확인했습니다.

## 의도적으로 넣지 않은 것

- 모션 경로 없음. `p:animMotion`은 손으로 쓴 경로가 필요하고, 틀린 경로는 재생 전까지 보이지 않습니다.
- `p:media`와 매체 트리거 없음.
- 글자·단어 단위 빌드 없음. 텍스트 상자를 애니메이션 하위 실행으로 쪼개면 실행 구조가 바뀌고, 그 구조가 `edit-deck.sh`의 검색 기준입니다.
- 소리 없음.
- 마스터·레이아웃에 애니메이션 없음. 슬라이드 모션이 상속되지 않습니다.

이 중 하나가 필요하면 이 패키지가 확인할 수 없는 XML을 쓰게 하지 말고 파워포인트에서 직접 만듭니다.

## 확인한 것과 확인하지 못한 것

2026-11-14에 확인한 것:

- 전환 23종과 효과 9종이 배치 오류 없이 렌더되고, `ppt/slides/slideN.xml`에 기대한 요소와 속성이 있다.
- 모든 `p:spTgt`가 같은 슬라이드의 `p:cNvPr` id를 지목한다.
- 중복된 `p:cTn id`가 있는 슬라이드가 없다.
- `pp_check_motion`이 주입한 중복 id와 없는 대상을 잡는다.

확인하지 못한 것: 재생. 이 기기에 파워포인트가 없어 "프로젝터에서 morph가 어떻게 보이는가"는 여기서 답할 수 없습니다. XML은 스키마와 참조 구현에 맞습니다. 첫 실제 발표를 시험으로 봅니다.

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| `p:transition`은 `p:sld`의 자식이며 효과 요소 하나를 가짐 | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.slide> |
| 전환 효과 요소와 방향 속성 | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.transition> |
| `p:timing`은 `p:spTgt` 대상과 `p:cTn` 노드 트리를 만듦 | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.timing> |
| 애니메이션 프리셋 id가 애니메이션 창의 이름과 대응 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |
| morph는 `p159` 확장이며 `mc:AlternateContent`가 필요 | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |

### 근거 등급

`LOCAL` - 요소·속성·id 규칙은 작성기에서 읽었고 `ppt/slides/`의 렌더 결과로 확인했습니다. 재생은 스키마 근거이며, 이 기기에 파워포인트가 없습니다.
