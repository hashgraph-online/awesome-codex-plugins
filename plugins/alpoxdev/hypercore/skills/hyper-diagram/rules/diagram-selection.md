# Diagram Selection

Use this rule file before deciding what to draw. It owns the structure-to-type choice, the split rule, and the content and wording rules every spec follows.

## 1. Structure → Type

Ask what the reader must answer, then pick the first row that fits.

| The reader asks | Structure | Type |
|---|---|---|
| What parts exist and how do they connect? | components, services, boundaries | `architecture` |
| What happens next, and where does it branch? | steps, decisions, loops | `flowchart` |
| Where does the data go and what changes it? | sources, transforms, sinks | `dataflow` |
| Who calls whom, in what order? | participants, ordered messages | `sequence` |
| What status can it be in, and what moves it? | states, transitions | `state` |
| What tables exist and how do they relate? | entities, keys, cardinality | `erd` |
| What types exist and how do they depend? | classes, interfaces, members | `class` |
| What contains what, with one parent each? | strict hierarchy | `tree` |
| What ideas hang off one topic? | radial brainstorm | `mindmap` |
| When did things happen? | ordered dated events | `timeline` |
| How long does each task take and what waits on what? | dated tasks, dependencies | `gantt` |
| Which layer sits on which? | stacked tiers with members | `layers` |

Tie-breaks:

- A request that names a type uses it, unless the structure cannot be drawn in it; then say so and use the fitting type.
- A process with decisions is `flowchart`; a process that is mostly one service calling another is `sequence`.
- Containment with cross-links is `architecture` with groups, not `tree`.
- Mermaid input keeps its meaning, not its styling: `flowchart`/`graph` → `flowchart` (or `architecture` for a component map), `sequenceDiagram` → `sequence`, `stateDiagram` → `state`, `erDiagram` → `erd`, `classDiagram` → `class`, `gantt` → `gantt`, `mindmap` → `mindmap`, `timeline` → `timeline`.

## 2. Size And Split

- Aim for 5-25 elements. Above about 40 nodes, or 9 sequence participants, draw an overview plus one detail diagram per area, each a separate spec and file set.
- One diagram answers one question. A second question becomes a second diagram.
- Leave out elements that do not change the answer. Fold repeated instances into one node with a count in `sub` ("워커 ×4").

## 3. Content Rules

- `title`: the subject and the view, as a noun phrase ("결제 서비스 아키텍처"). Never "다이어그램" alone.
- `subtitle`: the scope and the as-of point ("범위: 주문 생성부터 정산까지 · 기준 2026-11-08").
- `label`: the name the team uses, short; product and code names as written. `sub`: one role, tech, or port detail.
- Edge `label`: a verb or a protocol that says what crosses ("토큰 검증", "SQL", "정산 이벤트"). Avoid "사용", "연결", "호출" alone. Leave an edge unlabeled only when its meaning is obvious from the two ends.
- `kind` carries meaning, not taste: use the kind that matches what the node is, so the legend reads true. Use `primary` edges for the one main path; `async`, `auth`, `data`, `error`, `return`, `deploy` only when that is what the edge is.
- `description`: two to four sentences that walk the main path in words and name every inferred element ("인증 서버의 위치는 설정 파일에 없어 추정했습니다").
- Korean wording follows the user's language rules: plain declaratives, no filler.

## 4. Evidence

- From a repository, read the files that prove each element (entry points, config, compose, schema, routes) before drawing it.
- An element with no proof is drawn only when the picture would mislead without it, and it is named as inferred in `description`.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Title, legend, specific relation labels, element type made explicit | <https://c4model.com/diagrams/notation> |
| Mermaid diagram families used as input mapping | <https://mermaid.js.org/intro/> |
| Long description beside a complex image | <https://www.w3.org/WAI/tutorials/images/complex/> |
| The type table, the size bounds, and the split rule | this package's choice |

### Evidence grade

`LOCAL` - the selection table and size bounds are this package's design, not a validated optimum.
