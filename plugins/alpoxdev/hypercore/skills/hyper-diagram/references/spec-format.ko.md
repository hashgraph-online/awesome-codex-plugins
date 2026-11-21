# Spec 형식

`<slug>.diagram.json`을 쓰기 전에 이 참고 파일을 사용합니다. `assets/examples/`에서 맞는 파일을 복사해 내용만 바꿉니다. 예시는 모양일 뿐 사실이 아닙니다.

## Contents

- 공통 필드
- 노드 종류와 간선 종류
- 그래프 타입: architecture, dataflow, flowchart, state
- erd
- class
- sequence
- tree와 mindmap
- timeline
- gantt
- layers

## Common Fields

| 필드 | 필수 | 뜻 |
|---|---|---|
| `type` | 예 | 아래 12개 타입 중 하나 |
| `title` | 예 | 제목과 페이지 제목 |
| `subtitle` | 아니요 | 범위와 기준 시점 줄 |
| `description` | 예, 20자 이상 | 보드 아래 긴 설명 |
| `badge` | 아니요 | 타입 배지 글을 바꿈 |
| `theme` | 아니요 | `light`(기본) 또는 `dark` |
| `lang` | 아니요 | 기본 `ko` |
| `legend` | 아니요 | `false`면 숨김, `{ "kinds": {"service": "API"}, "edges": {"async": "이벤트"} }`로 항목 이름 변경 |
| `legendTitle` | 아니요 | 범례 제목, 기본 `범례` |

id는 `[A-Za-z0-9_-]+`에 맞아야 하고 spec 전체에서 하나뿐이어야 합니다.

## Node Kinds And Edge Kinds

노드 `kind`는 색, 아이콘, 범례 항목을 정합니다: `user`, `client`, `edge`, `service`, `data`, `cache`, `queue`, `storage`, `cloud`, `security`, `external`, `ai`, `process`, `decision`, `start`, `end`, `event`, `doc`, `team`, `note`, `neutral`(기본). `icon`에 다른 종류 이름을 쓰면 아이콘이 바뀌고, `false`면 아이콘을 뺍니다.

간선 `kind`: `default`, `primary`(주 경로), `async`(점선), `auth`(점선), `data`, `deploy`(점 선), `error`, `return`(점선). `dashed: true|false`와 `dotted: true`로 선 모양을 바꿉니다.

## Graph Types: architecture, dataflow, flowchart, state

```json
{ "type": "architecture", "direction": "right", "spacing": 36,
  "groups": [{ "id": "aws", "label": "AWS", "kind": "cloud", "parent": null, "dashed": false }],
  "nodes":  [{ "id": "api", "label": "결제 API", "sub": "Hono · :8080", "kind": "service", "group": "aws", "shape": "rect" }],
  "edges":  [{ "from": "user", "to": "api", "label": "HTTPS", "kind": "primary" }] }
```

- `direction`: `right` | `down` | `left` | `up`. 기본값은 architecture, dataflow, state가 `right`, flowchart가 `down`입니다.
- `spacing`: 노드 간격(px, 기본 36). 라벨이 빽빽하면 키웁니다.
- 그룹은 `parent`로 중첩하고, 노드는 `group`으로 그룹 하나에 들어갑니다. 간선은 그룹 id에서 끝날 수 있습니다.
- `shape`: `rect`, `soft`, `pill`, `diamond`, `cylinder`, `parallelogram`, `circle`. flowchart는 지정이 없으면 `kind`로 고릅니다(`start`/`end`는 pill, `decision`은 diamond, `data`는 cylinder, `doc`은 parallelogram).
- state: `label`이 없는 `start`·`end` 노드는 점으로 그립니다.
- 배치가 허용하는 한 배열의 노드 순서를 지킵니다. 교차를 없애려면 순서를 바꿉니다.

## erd

노드에 `columns`, 간선에 `card`를 씁니다.

```json
{ "id": "orders", "label": "orders", "kind": "data",
  "columns": [{ "name": "id", "type": "bigint", "key": "PK" }, { "name": "user_id", "type": "bigint", "key": "FK" }] }
{ "from": "users", "to": "orders", "label": "주문한다", "card": "1:N" }
```

`key`는 자유 글이며 보통 `PK`, `FK`, `UK`, `PK,FK`입니다. `card`의 왼쪽은 `from` 끝에, 오른쪽은 `to` 끝에 붙습니다.

## class

```json
{ "id": "gw", "label": "PaymentGateway", "stereotype": "interface", "abstract": false,
  "attributes": ["- apiKey: string"], "methods": ["+ approve(req): Result"] }
{ "from": "toss", "to": "gw", "kind": "implement" }
```

여기서 간선 `kind`는 관계입니다: `inherit`, `implement`, `compose`, `aggregate`, `depend`, `assoc`(기본), `link`. 범례는 관계마다 한국어 이름을 씁니다.

## sequence

```json
{ "type": "sequence",
  "participants": [{ "id": "u", "label": "고객", "kind": "user" }],
  "messages": [
    { "from": "u", "to": "api", "label": "POST /payments", "kind": "primary" },
    { "from": "api", "to": "api", "label": "금액 검증" },
    { "divider": "캐시 미스" },
    { "note": "최대 3초 대기", "over": ["api", "pg"] }
  ] }
```

메시지는 순서대로 번호가 붙습니다. 자기 자신에게 보내는 메시지는 고리로 그립니다. 응답에는 `kind: "return"`을 씁니다.

## tree and mindmap

```json
{ "type": "tree", "direction": "down", "arrows": false,
  "root": { "id": "root", "label": "repo", "children": [{ "id": "apps", "label": "apps", "sub": "배포 단위", "edgeLabel": "포함" }] } }
```

- tree: `direction`은 `down`(기본) 또는 `right`, `arrows: true`면 화살촉을 붙입니다.
- mindmap: 같은 `root` 모양을 씁니다. 가지는 크기에 따라 좌우로 나뉘고, 첫 단계 가지는 `kind`를 지정하지 않으면 저마다 색을 받습니다.

## timeline

```json
{ "type": "timeline", "events": [{ "id": "a", "date": "14:02", "label": "실패율 경보", "sub": "결제 실패 12%", "kind": "security" }] }
```

사건은 배열 순서대로 축 하나의 위아래에 번갈아 그립니다. `date`는 자유 글입니다.

## gantt

```json
{ "type": "gantt", "today": "2026-11-18",
  "tasks": [
    { "id": "d", "label": "설계 검토", "start": "2026-11-09", "days": 5, "section": "준비", "done": true },
    { "id": "api", "label": "결제 API", "after": "d", "days": 10, "section": "개발" },
    { "id": "rel", "label": "출시", "start": "2026-12-08", "milestone": true }
  ] }
```

날짜는 `YYYY-MM-DD`입니다. 작업에는 `start`나 `after`, 그리고 `days`, `end`(그날 포함), `milestone` 중 하나가 필요합니다. `done: true`면 막대를 채웁니다.

## layers

```json
{ "type": "layers",
  "layers": [{ "id": "l1", "label": "화면", "sub": "presentation", "kind": "client",
               "items": [{ "id": "w", "label": "웹" }, { "id": "a", "label": "인증", "kind": "security" }] }] }
```

층은 배열 순서대로 위에서 아래로 쌓입니다. 항목은 자기 `kind`가 없으면 층의 `kind`를 따릅니다.

## Sources

> 확인 2026-11-08.

| Claim | Source |
|---|---|
| 필드 이름, 기본값, 허용 값 | 이 패키지의 `assets/runtime/*.js` |
| 흔한 텍스트 다이어그램 도구에서 가져온 다이어그램 종류 | <https://mermaid.js.org/intro/> |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지의 spec 형식을 설명합니다.
