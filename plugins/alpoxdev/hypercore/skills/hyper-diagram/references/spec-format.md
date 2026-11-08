# Spec Format

Use this reference before writing a `<slug>.diagram.json`. Copy the matching file from `assets/examples/` and change its content; the examples are shapes, not facts.

## Contents

- Common fields
- Node kinds and edge kinds
- Graph types: architecture, dataflow, flowchart, state
- erd
- class
- sequence
- tree and mindmap
- timeline
- gantt
- layers

## Common Fields

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | one of the twelve types below |
| `title` | yes | shown as the heading and the page title |
| `subtitle` | no | scope and as-of line |
| `description` | yes, 20+ chars | long description under the board |
| `badge` | no | replaces the type badge text |
| `theme` | no | `light` (default) or `dark` |
| `lang` | no | `ko` by default |
| `legend` | no | `false` hides it; `{ "kinds": {"service": "API"}, "edges": {"async": "이벤트"} }` renames entries |
| `legendTitle` | no | legend heading, `범례` by default |

Ids match `[A-Za-z0-9_-]+` and are unique across the whole spec.

## Node Kinds And Edge Kinds

Node `kind` sets color, icon, and legend entry: `user`, `client`, `edge`, `service`, `data`, `cache`, `queue`, `storage`, `cloud`, `security`, `external`, `ai`, `process`, `decision`, `start`, `end`, `event`, `doc`, `team`, `note`, `neutral` (default). `icon` overrides the icon with another kind name, or `false` removes it.

Edge `kind`: `default`, `primary` (main path), `async` (dashed), `auth` (dashed), `data`, `deploy` (dotted), `error`, `return` (dashed). `dashed: true|false` and `dotted: true` override the line style.

## Graph Types: architecture, dataflow, flowchart, state

```json
{ "type": "architecture", "direction": "right", "spacing": 36,
  "groups": [{ "id": "aws", "label": "AWS", "kind": "cloud", "parent": null, "dashed": false }],
  "nodes":  [{ "id": "api", "label": "결제 API", "sub": "Hono · :8080", "kind": "service", "group": "aws", "shape": "rect" }],
  "edges":  [{ "from": "user", "to": "api", "label": "HTTPS", "kind": "primary" }] }
```

- `direction`: `right` | `down` | `left` | `up`. Defaults: architecture, dataflow, state `right`; flowchart `down`.
- `spacing`: node gap in px (default 36). Raise it when labels crowd.
- Groups nest through `parent`; a node joins one group through `group`. An edge may end at a group id.
- `shape`: `rect`, `soft`, `pill`, `diamond`, `cylinder`, `parallelogram`, `circle`. Flowchart picks it from `kind` when absent (`start`/`end` pill, `decision` diamond, `data` cylinder, `doc` parallelogram).
- State: a `start` or `end` node without `label` becomes a dot.
- Node order in the array is kept where the layout allows; reorder it to remove crossings.

## erd

Nodes carry `columns`; edges carry `card`.

```json
{ "id": "orders", "label": "orders", "kind": "data",
  "columns": [{ "name": "id", "type": "bigint", "key": "PK" }, { "name": "user_id", "type": "bigint", "key": "FK" }] }
{ "from": "users", "to": "orders", "label": "주문한다", "card": "1:N" }
```

`key` is free text, usually `PK`, `FK`, `UK`, or `PK,FK`. `card` puts its left part at `from` and its right part at `to`.

## class

```json
{ "id": "gw", "label": "PaymentGateway", "stereotype": "interface", "abstract": false,
  "attributes": ["- apiKey: string"], "methods": ["+ approve(req): Result"] }
{ "from": "toss", "to": "gw", "kind": "implement" }
```

Edge `kind` here is the relation: `inherit`, `implement`, `compose`, `aggregate`, `depend`, `assoc` (default), `link`. The legend names each relation in Korean.

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

Messages are numbered in order. A message to itself draws a loop. Use `kind: "return"` for replies.

## tree and mindmap

```json
{ "type": "tree", "direction": "down", "arrows": false,
  "root": { "id": "root", "label": "repo", "children": [{ "id": "apps", "label": "apps", "sub": "배포 단위", "edgeLabel": "포함" }] } }
```

- tree: `direction` `down` (default) or `right`; `arrows: true` adds arrowheads.
- mindmap: same `root` shape; branches split left and right by size, each first-level branch gets its own color unless it sets `kind`.

## timeline

```json
{ "type": "timeline", "events": [{ "id": "a", "date": "14:02", "label": "실패율 경보", "sub": "결제 실패 12%", "kind": "security" }] }
```

Events are drawn in array order, alternating above and below one axis. `date` is free text.

## gantt

```json
{ "type": "gantt", "today": "2026-11-18",
  "tasks": [
    { "id": "d", "label": "설계 검토", "start": "2026-11-09", "days": 5, "section": "준비", "done": true },
    { "id": "api", "label": "결제 API", "after": "d", "days": 10, "section": "개발" },
    { "id": "rel", "label": "출시", "start": "2026-12-08", "milestone": true }
  ] }
```

Dates are `YYYY-MM-DD`. A task needs `start` or `after`, and `days`, `end` (inclusive), or `milestone`. `done: true` fills the bar.

## layers

```json
{ "type": "layers",
  "layers": [{ "id": "l1", "label": "화면", "sub": "presentation", "kind": "client",
               "items": [{ "id": "w", "label": "웹" }, { "id": "a", "label": "인증", "kind": "security" }] }] }
```

Layers stack top to bottom in array order; items take the layer's `kind` unless they set their own.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Field names, defaults, and accepted values | this package's `assets/runtime/*.js` |
| Diagram families mirrored from common text-diagram tools | <https://mermaid.js.org/intro/> |

### Evidence grade

`LOCAL` - this file documents this package's own spec format.
