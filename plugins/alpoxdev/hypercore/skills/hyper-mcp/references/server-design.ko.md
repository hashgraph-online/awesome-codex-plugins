# 서버 설계

MCP 서버가 무엇을 노출할지(도구, 리소스, 프롬프트, 오류, 상태, 서버 지침)를 설계하는 방법을 다룬다. 모델이 올바르게 쓸 수 있고 호스트가 감당해서 적재할 수 있어야 한다. 규범 규칙은 `2026-07-28` 명세에서 오고 설계 지침은 호스트 벤더가 공개한 평가에서 오며 그 사실을 표시한다.

> 영어판: [`server-design.md`](server-design.md)

## 목차

- Pick the primitive by who controls it
- Tool surface
- Errors
- State across calls
- Asking for input mid-call
- Resources and prompts
- Server instructions
- Annotations
- Extensions
- Verify the design

## Pick the primitive by who controls it

서버 개요는 각 프리미티브를 누가 언제 쓰는지 누가 결정하는지를 확정한다(2026-11-07 확인).

| 프리미티브 | 제어 주체 | 쓰는 곳 | 쓰지 않는 곳 |
|---|---|---|---|
| 도구 | 모델 | 모델이 실행을 결정해야 하는 행동과 조회 | 애플리케이션이 자체 일정으로 붙여야 하는 데이터 |
| 리소스 | 애플리케이션 | 호스트가 붙이거나 사용자가 고르는 컨텍스트. 파일, 레코드, 스키마. URI로 식별한다 | 부수 효과가 있는 작업 |
| 프롬프트 | 사용자 | 사람이 명시적으로 호출하는 템플릿. 슬래시 명령 같은 것 | 모델이 늘 따라야 하는 숨은 지시 |

"사용자 제어"는 프롬프트를 *언제* 쓰는지 정하지 *내용을 누가 쓰는지* 정하지 않는다. 프롬프트 내용은 서버가 쓰므로 프롬프트는 다른 것과 마찬가지로 서버가 공급하는 텍스트다.

호출 가능한 작업이 아니라 워크플로 지식이 필요하면 Skills 확장(`io.modelcontextprotocol/skills`, Beta)이 에이전트 스킬을 호스트가 지연해서 읽는 리소스로 제공한다. "호스트는 필요하기 전에 파일을 가져와서는 안 된다(**MUST NOT**)"(skills 확장 페이지, 2026-11-07 확인). 선택제이고 호스트 지원이 고르지 않으니 대상 호스트를 확인하지 않고 의존하지 않는다.

## Tool surface

규범 규칙(도구 페이지, 2026-11-07 확인):

- 이름은 1~128자에 대소문자를 구분하고 `A-Z a-z 0-9 _ - .`만 쓰며 서버 안에서 유일한 것이 좋다(**SHOULD**). SEP-986은 원래 `/`를 허용하는 1~64자를 제안했지만 명세 본문이 그것을 대체한다.
- `tools/list`는 연결마다 또는 다른 요청의 부수 효과로 달라져서는 안 된다(**MUST NOT**). 요청의 인가에 따라 달라지는 것은 달라져도 된다(**MAY**). 호출자의 스코프가 허용하는 도구만 돌려주는 경우가 그렇다.
- 도구는 결정적인 순서로 돌아오는 것이 좋다(**SHOULD**). "도구가 모델 컨텍스트에 포함될 때 LLM 프롬프트 캐시 적중률이 좋아진다".
- `inputSchema`는 유효한 JSON 스키마 객체여야 한다(**MUST**)(기본 2020-12이고 2020-12 키워드를 모두 쓸 수 있다). 매개변수가 없는 도구는 `{"type": "object", "additionalProperties": false}`를 쓴다.
- `outputSchema`가 있으면 서버는 그에 맞는 `structuredContent`를 돌려주어야 하고(**MUST**), 하위 호환을 위해 직렬화한 JSON을 텍스트 블록에도 돌려주는 것이 좋다(**SHOULD**).

Anthropic의 도구 평가 작업("Writing effective tools for agents", 2025-09-11, 2026-11-07 확인)에서 온 설계 지침이다. 프로토콜이 아니라 벤더 관행이다.

| 지침 | 구체적 형태 |
|---|---|
| "도구가 많다고 결과가 늘 좋아지지는 않는다." | API 엔드포인트마다 1:1로 감싸지 말고 과업 중심으로 도구 몇 개를 만든다. `list_users` + `list_events` + `create_event` 대신 `schedule_event`, `read_logs` 대신 `search_logs`다. |
| 서비스나 리소스로 네임스페이스를 나눈다 | 관련 도구에 접두사나 접미사를 붙인다. 기사에 따르면 이 선택이 평가에 "적지 않은 영향"을 주므로 측정한다. |
| 신호가 강한 필드를 돌려준다 | `uuid`나 `mime_type` 같은 불투명한 식별자보다 이름, URL, 파일 유형을 앞세운다. 호출자가 ID를 가끔 필요로 하면 `response_format` 열거형(`concise` / `detailed`)을 둔다. 기사는 간결한 응답으로 토큰이 대략 3분의 1로 줄었다고 측정했다. |
| 응답 크기에 상한을 둔다 | 합리적인 기본값으로 페이지를 나누고 거르고 잘라낸다. 잘린 출력에는 더 받는 방법을 적는다. |
| 매개변수 이름을 모호하지 않게 짓는다 | `user`가 아니라 `user_id`다. 새로 온 동료에게 설명하듯 각 도구를 설명한다. |

호스트는 자체 상한을 적용한다. Claude Code는 도구 출력이 10,000 토큰을 넘으면 경고하고 기본으로 25,000 토큰에서 자른다(Claude Code MCP 문서, 2026-11-07 확인). 호출자가 감당할 수 있는 양보다 많이 돌려주는 서버는 명세가 무엇을 허용하든 그 호출자에게는 고장 난 서버다.

## Errors

도구 페이지는 두 채널을 구분한다(2026-11-07 확인).

| 채널 | 쓰는 곳 | 형태 |
|---|---|---|
| 프로토콜 오류 | 알 수 없는 도구, 잘못된 요청, 서버 결함 | JSON-RPC `error`(예: `-32602`) |
| 도구 실행 오류 | API 실패, 입력 검증 실패, 비즈니스 규칙 위반 | `isError: true`와 읽을 수 있는 `content`를 담은 `result` |

클라이언트는 실행 오류를 모델에 넘겨야 한다(**SHOULD**). "스스로 교정할 수 있게" 하려는 것이다. 프로토콜 오류는 넘겨도 된다(**MAY**). 검증 실패는 실행 채널에 넣고 메시지는 모델이 행동할 수 있는 지시로 쓴다. 코드나 스택 추적 대신 "출발 날짜가 잘못되었습니다. 미래 날짜여야 합니다. 현재 날짜는 …" 같은 식이다.

## State across calls

프로토콜 세션은 없다. 호출 사이에 상태가 필요한 서버는 만드는 도구에서 명시적 핸들을 돌려주고 이후 호출에서 인수로 받는다. 도구 페이지는 이것을 규범이 아닌 설계 지침으로 제시한다(2026-11-07 확인).

- **핸들은 이름이지 자격 증명이 아니다.** 인증 서버는 호출마다 호출자와 핸들을 대조해 확인한다. 인증이 없는 서버는 핸들을 고엔트로피(UUIDv4 등)로 만들고 수명을 짧게 둔다.
- **핸들은 불투명하게 유지한다.** 구조를 인코딩하면 파싱과 추측을 부른다.
- **수명을 만드는 도구의 설명에 적는다**("장바구니는 24시간 비활성 후 만료됩니다"). 모델이 상태를 만들기 전에 보게 하려는 것이다.
- **만료됐거나 모르는 핸들은 그렇다고 말하는 도구 실행 오류를 돌려준다.** 모델이 새로 만들어 복구할 수 있다.

같은 패턴의 보안 쪽, 곧 핸들을 인증된 사용자에 묶는 일은 [`security-and-authorization.ko.md`](security-and-authorization.ko.md)에 있다.

## Asking for input mid-call

도구에 확인이나 빠진 매개변수가 필요하면 실패하는 대신 `elicitation/create` 요청을 담은 `InputRequiredResult`를 돌려준다([`protocol-2026-07-28.ko.md`](protocol-2026-07-28.ko.md)).

- 클라이언트가 선언한 모드(`form`, `url`)만 요청한다. 아니면 요청이 `-32021`로 실패한다.
- form 모드는 원시형 속성의 평평한 객체만 받는다. 비밀번호, API 키, 토큰, 결제 자격 증명을 여기로 요청하지 않는다. 그것들은 URL 모드로 간다.
- 클라이언트가 답한다고 가정하지 않는다. 답이 없어도 절반만 적용된 변경이 남지 않게 도구를 설계한다.
- Roots나 Sampling 위에 새 기능을 만들지 않는다. 둘 다 폐기 예정(Deprecated)이다. 디렉터리는 도구 매개변수나 설정으로 받고 서버에 생성이 필요하면 모델 공급자를 직접 호출한다.

## Resources and prompts

- 리소스 없음은 `-32602`를 돌려준다(클라이언트는 예전 `-32002`도 계속 받아야 한다(**SHOULD**)). 서버는 없는 리소스에 빈 `contents` 배열로 답해서는 안 된다(**MUST NOT**).
- `file://` 리소스는 디렉터리 순회 공격을 막도록 경로를 정제해야 한다(**MUST**).
- 도구가 돌려주는 리소스 링크는 "`resources/list` 요청 결과에 나타난다고 보장되지 않는다". 모델이 목록으로 발견하는 데 의존하게 만들지 않는다.
- 프롬프트 입력과 출력은 인젝션을 검증해야 한다(**MUST**).
- 목록 엔드포인트는 불투명 커서로 페이지를 나눈다. 클라이언트는 커서를 파싱해서는 안 되고(**MUST NOT**), `nextCursor`가 없으면 끝이다.

## Server instructions

`server/discover`는 `instructions`를 돌려줄 수 있다. 호스트가 모델 컨텍스트에 넣어 서버 기능이 어떻게 맞물리는지 설명할 수 있는 텍스트다(discover 페이지, 2026-11-07 확인). 유지보수자의 지침(server-instructions 글, 2025-11-03, 2026-11-07 확인):

- 도구와 리소스가 스스로 전달할 수 없는 것을 적는다. 도구 사이의 순서, 도구 사이 관계, 속도 한도, 운용 제약이다.
- 도구 설명을 반복하지 않는다. 마케팅 문구를 넣지 않는다. 일반적인 행동 지침을 주지 않는다. 설명서를 쓰지 않는다.
- 지침은 행동을 보장하지 않는다. "중요한 동작은 지침에 의존하지 마라. 특히 보안이나 프라이버시 영역에서는 더욱 그렇다. 그런 것은 결정적 규칙이나 훅으로 구현하는 편이 낫다."
- 호스트가 지침을 넣을지, 어디에 넣을지 정한다. 의존하기 전에 대상 호스트에서 시험한다.

글 자체의 평가는 작고 그렇게 밝혀져 있다. 호스트 하나에서 40개 세션을 돌렸고 한 모델은 의도한 3단계 검토 워크플로를 지침이 있을 때 10번 중 8번, 없을 때 10번 중 2번 따랐으며 다른 모델은 10번 중 9번과 10번 중 10번 따랐다. 효과 크기가 아니라 지침이 일부 모델에 도움이 된다는 증거로 읽는다.

## Annotations

`ToolAnnotations`는 네 가지 힌트와 `title`을 담는다. 힌트는 `readOnlyHint`(기본 `false`), `destructiveHint`(기본 `true`), `idempotentHint`(기본 `false`), `openWorldHint`(기본 `true`)다. 기본값은 최악을 가정하고 클라이언트는 서버를 신뢰하지 않는 한 annotation을 신뢰할 수 없는 것으로 다뤄야 한다(**MUST**)(도구 페이지, annotation 글 2026-03-16, 2026-11-07 확인).

- 사실대로 설정한다. 읽기 전용 도구에는 `readOnlyHint: true`, 추가만 하는 도구에는 `destructiveHint: false`, 닫힌 영역 도구에는 `openWorldHint: false`다. 호스트는 이것으로 언제 확인을 요구할지 정한다.
- 안전을 이것에 기대지 않는다. "신뢰할 수 없는 서버는 거짓말할 수 있다", 그리고 "도구가 데이터를 유출할 수 없다는 보장이 필요하면 그것은 네트워크 제어나 샌드박스의 일이지 불리언 힌트의 일이 아니다."
- annotation은 도구 하나를 설명한다. 위험은 세션의 다른 도구에 달려 있다([`security-and-authorization.ko.md`](security-and-authorization.ko.md)).

## Extensions

확장은 `{vendor-prefix}/{extension-name}` 식별자로 코어 밖 능력을 더하고 "항상 기본으로 꺼져 있으며 명시적 선택이 필요하다"(확장 개요, 2026-11-07 확인). 한쪽이 확장을 갖지 않으면 다른 쪽은 코어 동작으로 물러나거나 요청을 거부해야 한다(**MUST**).

| 확장 | 상태(2026-11-07) | 쓰는 때 |
|---|---|---|
| MCP Apps(`io.modelcontextprotocol/ui`) | Stable | 도구 결과가 호스트가 샌드박스 프레임에 렌더링하는 대화형 UI일 때 |
| Tasks(`io.modelcontextprotocol/tasks`) | Beta, 코어로 이동 중 | 클라이언트가 `tasks/get`으로 폴링하는 장기 작업. 지원을 선언한 클라이언트에만 작업을 돌려준다 |
| Skills(`io.modelcontextprotocol/skills`) | Beta | 에이전트 스킬을 지연해서 읽는 리소스로 제공할 때 |
| OAuth Client Credentials, Enterprise-Managed Authorization | Stable | 기계 대 기계 접근과 기업 ID 공급자 정책 |

커뮤니티 클라이언트 지원 표와 Apps 개요는 어떤 호스트가 어떤 확장을 구현했는지가 서로 다르다. 두 목록 대신 대상 호스트에서 확인한다.

## Verify the design

프로토콜 준수([`build-test-ship.ko.md`](build-test-ship.ko.md))는 모델이 도구를 쓸 수 있다는 것을 보여주지 않는다. Anthropic의 도구 평가 방법(2026-11-07 확인): 여러 번, 때로는 수십 번의 도구 호출이 필요한 현실적인 과업을 만들고 각 과업에 검증 가능한 결과를 붙인다. 서식 때문에 정답을 거부하는 검증기를 피하고 시험 세트를 남겨 둔다. 정확도와 함께 호출 수, 토큰, 오류를 추적한다. 검토자가 최종 답만이 아니라 진행 경로도 확인할 수 있게 실행마다 대화 기록과 도구 호출을 남긴다.

## Sources

> 확인 2026-11-07. 명세 페이지는 `2026-07-28` 판이며 블로그 날짜는 각 페이지에 표시된 값이다.

| 주장 | 출처 | 게재 |
|---|---|---|
| 프리미티브별 제어 모델 | <https://modelcontextprotocol.io/specification/2026-07-28/server> | 2026-07-28 판 |
| 도구 이름, 목록 규칙, 스키마, 오류, 상태 기반 도구 지침, annotation 신뢰 | <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> | 2026-07-28 판 |
| 리소스 오류, 순회 규칙 | <https://modelcontextprotocol.io/specification/2026-07-28/server/resources> | 2026-07-28 판 |
| 프롬프트 제어의 뉘앙스와 검증 | <https://modelcontextprotocol.io/specification/2026-07-28/server/prompts> | 2026-07-28 판 |
| 커서 불투명성 | <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination> | 2026-07-28 판 |
| elicitation 모드와 비밀 금지 | <https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation> | 2026-07-28 판 |
| discover 결과의 `instructions` | <https://modelcontextprotocol.io/specification/2026-07-28/server/discover> | 2026-07-28 판 |
| 최초 도구 이름 제안 | <https://modelcontextprotocol.io/seps/986-specify-format-for-tool-names> | 최종 SEP |
| 서버 지침 지침과 평가 | <https://blog.modelcontextprotocol.io/posts/2025-11-03-using-server-instructions/> | 2025-11-03 |
| annotation 의미와 한계 | <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/> | 2026-03-16 |
| 확장 식별자, 선택제, 상태 | <https://modelcontextprotocol.io/extensions/overview> | 날짜 없음 |
| Skills 확장의 지연 검색 | <https://modelcontextprotocol.io/extensions/skills/overview> | 날짜 없음 |
| 도구 설계와 평가 방법 | <https://www.anthropic.com/research/writing-tools-for-agents> | 2025-09-11 |
| 호스트 출력 경고와 상한 | <https://code.claude.com/docs/en/mcp> | 2026-11-07 확인 |
