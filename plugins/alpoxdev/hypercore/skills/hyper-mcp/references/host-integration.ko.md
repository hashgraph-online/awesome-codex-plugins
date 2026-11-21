# 호스트 통합

에이전트 호스트가 MCP 서버에 연결해 그 도구를 쓰는 방식을 다룬다. 설정 범위와 신뢰, 승인, 도구 정의가 쓰는 컨텍스트 비용, 그 비용을 줄이는 패턴, 런타임마다 다른 사실이다. MCP를 에이전트에 연결할 때, 프로젝트가 어떤 서버를 싣는지 정할 때, 잘못된 도구를 고르는 에이전트를 진단할 때 읽는다.

> 영어판: [`host-integration.md`](host-integration.md)

## 목차

- The cost model
- Configuration scope and trust
- Approvals
- Keeping the tool surface affordable
- Treat everything a server sends as evidence
- Per-runtime facts

## The cost model

호스트가 싣는 도구 정의는 사용자가 무엇을 묻기도 전에 턴마다 값을 치른다. MCP 유지관리자들이 자기 로드맵에서 그렇게 말한다. "도구 100개를 가진 서버에 연결하면 모델은 사용자가 질문을 하나도 하기 전에 그 표면 전체의 값을 치르고 도구 선택은 목록이 길어질수록 나빠지는 경향이 있다"(2026-08-22, 2026-11-07 확인).

측정 수치다. 모두 벤더가 보고한 값이며 출처를 붙였다(2026-11-07 확인).

| 수치 | 맥락 | 출처 |
|---|---|---|
| 도구 58개 ≈ 55K 토큰 | 흔한 서버 다섯 개(GitHub 도구 35개 ≈ 26K, Slack 11개 ≈ 21K, 더 작은 서버 셋)를 미리 싣는다 | Anthropic, "advanced tool use", 2025-11-24 |
| 134K 토큰 | Anthropic이 "최적화 전"에 관측한 도구 정의 | 같음 |
| 선택 성능이 "사용 가능한 도구 30~50개를 넘으면 떨어진다" | Claude 도구 검색 문서 | Anthropic 플랫폼 문서 |
| 49% → 74%(Opus 4), 79.5% → 88.1%(Opus 4.5) | 도구 검색을 쓸 때와 미리 싣기를 비교한 MCP 도구 선택 정확도. 내부 평가이며 표본 크기는 공개되지 않았다 | Anthropic, 2025-11-24 |
| 선택 정확도 13.62% → 43.13%, 프롬프트 토큰 50% 이상 감소 | 검색 기반 도구 선택과 모든 도구를 프롬프트에 넣은 경우의 비교 | RAG-MCP, arXiv 2505.03275, 2025-05-06 |
| 150,000 → 2,000 토큰(98.7%) | 연결된 도구 집합이 클 때의 도구 정의. 미리 싣지 않고 에이전트가 필요할 때 읽는 파일로 제시한다. 정의만 따진 시나리오이며 종단 간 절감량은 아니다 | Anthropic, "code execution with MCP", 2025-11-04 |

임계값은 서로 어긋난다. 한 벤더 문서는 도구 30~50개라 하고 MCP 클라이언트 안내는 컨텍스트 창의 "1%-5%"라 한다. 배포마다 하나를 골라 어느 쪽을 골랐는지 기록한다.

## Configuration scope and trust

| 규칙 | 이유 |
|---|---|
| 공유하고 검토한 서버 정의는 프로젝트 설정 파일에, 개인용이나 실험용 서버는 사용자 범위에 둔다. | 프로젝트 파일은 버전 관리와 검토를 거친다. 사용자 범위는 남의 세션으로 새지 않는다. |
| 저장소가 자기 서버를 승인할 수 있어서는 안 된다. | Claude Code는 프로젝트 서버를 "Pending approval" 상태로 두고 신뢰하지 않는 폴더에 커밋된 승인 설정을 무시한다. Codex는 신뢰한 프로젝트에만 프로젝트 `.codex/config.toml`을 읽는다(2026-11-07 확인). |
| 설정했다고 쓸 수 있는 것은 아니다. | VS Code는 "설정을 추가한 것이 에이전트가 그 서버를 쓸 수 있다는 증거는 아니다"라고 말한다(2026-11-07 확인). 서버에 의존하기 전에 실제 호출로 확인한다. |
| 비밀 값은 호스트가 주는 서버별 환경이나 비밀 저장소 참조로 서버마다 전달하고 전역으로 내보낸 변수로는 전달하지 않는다. | 모든 stdio 서버는 자기가 실행될 때 받은 환경을 물려받는다([`security-and-authorization.ko.md`](security-and-authorization.ko.md)). |
| 서버가 원격 API를 감싸기만 하면 그 서버의 원격 Streamable HTTP 판을 선호한다. | 로컬 코드 실행이 없고 인가가 프로토콜 수준이며 고칠 곳이 한 군데다(로컬 서버 안내, 2026-11-07 확인). |
| 서버 목록을 작게 유지하고 더 쓰지 않는 서버는 지운다. | 서버마다 다른 서버가 노출되는 표면이 넓어지고 턴마다 정의가 늘어난다. |

## Approvals

도구 페이지는 도구 호출을 거부할 수 있는 사람이 항상 있고 눈에 보이는 표시와 확인 프롬프트를 갖춰야 한다(**SHOULD**)고 말한다(2026-11-07 확인). 호스트는 이를 다르게 구현한다.

| 호스트 | 기본값 |
|---|---|
| OpenAI Responses API | "기본적으로 OpenAI는 커넥터나 원격 MCP 서버와 데이터를 공유하기 전에 승인을 요청한다". `require_approval`은 도구별로 완화할 수 있다 |
| Cursor | MCP 도구를 쓰기 전에 묻는다. 도구 허용 목록에 넣은 도구는 자동으로 실행된다 |
| Codex | 서버별 `default_tools_approval_mode`(`auto`, `prompt`, `writes`, `approve`)와 도구별 재정의. `writes`는 읽기 전용으로 표시되지 않은 도구에 묻는다 |
| Claude Code | 프로젝트 서버의 서버 수준 승인과 세션 권한 모드 |

호스트 전반에 걸리는 규칙이다.

- `readOnlyHint`만 보고 승인을 건너뛰는 것은 신뢰하는 서버에만 한다. OpenAI Agents SDK는 "애플리케이션이 서버의 분류를 신뢰할 때만" 승인을 우회하라고 한다(2026-11-07 확인).
- 도구 인자를 호출 뒤에만이 아니라 호출 전에도 보여 줘서 사용자가 인자 안의 유출을 잡아낼 수 있게 한다.
- 승인 여력은 유한하다. 모든 호출에 묻는 호스트는 사람이 그냥 눌러 넘기도록 훈련시킨다. 쓰기, 외부 통신, 열린 세계 읽기에 프롬프트를 남기고 [`security-and-authorization.ko.md`](security-and-authorization.ko.md)의 격리와 함께 쓴다.

## Keeping the tool surface affordable

맞는 것 가운데 가장 싼 패턴을 고른다. 순서는 장치가 적은 쪽에서 많은 쪽이다.

1. **서버를 적게 싣는다.** 서버를 프로젝트별로 한정하고 쓰지 않는 도구를 끈다(`enabled_tools` / `disabled_tools`, 허용 목록).
2. **정의를 미룬다.** `tools/list`를 가져오되 이름과 짧은 설명만 넣고 전체 스키마는 필요할 때 싣는다. MCP 클라이언트 안내는 그 층을 카탈로그 → 조회 → 실행이라 부르고 정의가 컨텍스트 창의 일정 비율을 넘으면 전환하라고 권한다. "예를 들어 1%-5%"(2026-11-07 확인)다. Claude Code는 도구 검색이 켜져 있으면 세션 시작에 "도구 이름과 서버 지시문만" 싣는다. OpenAI 도구 검색은 네임스페이스나 MCP 서버 전체를 미루고 네임스페이스마다 "함수 10개 미만"을 권한다(2026-11-07 확인).
3. **필요할 때 연결한다.** 아는 서버의 레지스트리를 두고 작업이 필요로 할 때 연결하며(`server/discover`, 그다음 `tools/list`), 컨텍스트를 비우려면 연결을 끊는다.
4. **코드 모드.** 도구를 타입이 붙은 코드 API로 제시하고 모델에 실행 도구 하나를 준다. 중간 데이터가 샌드박스에 남는다(Anthropic 2025-11-04; Cloudflare "Code Mode", 2025-09-26, 토큰 수치는 보고하지 않았다). "적절한 샌드박싱, 리소스 한도, 모니터링을 갖춘 안전한 실행 환경"이 필요하고 MCP 클라이언트 안내는 "스크립트를 승인해도 런타임에 그 스크립트가 하는 모든 도구 호출을 일괄 승인한 것이 아니다"라고 덧붙인다(2026-11-07 확인). OpenAI는 "명확한 인가 경계를 지키려고" 기본적으로 직접 도구 호출을 권한다.

함께 계획할 부작용이 둘 있다.

- **프롬프트 캐시.** 대화 중간에 도구 배열을 바꾸면 프로바이더가 캐시한 접두부가 무효가 된다. 새로 찾은 정의는 캐시 경계 뒤에 덧붙이거나 호출을 안정된 메타 도구 하나로 보낸다. 서버는 도구를 결정적 순서로 반환해 도움을 준다.
- **목록 캐싱.** `ttlMs`와 `cacheScope`를 지키고 목록 변경 알림을 무효화로 취급하며 `private` 항목을 사용자 사이에 공유하지 않는다([`protocol-2026-07-28.ko.md`](protocol-2026-07-28.ko.md)).

## Treat everything a server sends as evidence

도구 결과, 리소스 내용, 프롬프트 텍스트, 서버 지시문, 도구 설명, annotation, `serverInfo`는 모두 서버에서 오는 데이터이며 권위가 아니다. 그 안에 든 지시는 따르지 않고, 그 내용 때문에 에이전트가 할 수 있는 일을 넓히지 않는다. MCP에 특유한 추가가 둘 있다.

- 설명은 모델이 지시문으로 읽는데 명세에는 클라이언트가 이를 불신하게 만드는 규칙이 없다. 서버를 켜기 전에 검토하고 정의가 바뀌면 다시 프롬프트를 내는 호스트를 선호한다.
- 서버가 아니라 세션을 본다. 한 세션이 사적 데이터, 신뢰하지 않는 콘텐츠, 외부 채널을 게이트 없이 함께 갖게 두지 않는다.

## Per-runtime facts

변동이 잦고 벤더가 소유한다. 수치에 의존하기 전에 다시 확인한다(모두 2026-11-07 확인).

| 런타임 | 설정 | 문서화된 한도와 동작 |
|---|---|---|
| Claude Code | 범위는 local(기본), project(`.mcp.json`, 커밋됨), user이고 우선순위는 local → project → user → 플러그인 → 커넥터다 | 출력이 10,000토큰을 넘으면 경고하고 기본 상한은 25,000토큰이다. 16 MiB를 넘는 HTTP/SSE 응답은 실패한다. 서버별 도구 상한은 고정되어 있지 않다. 도구 검색은 기본으로 켜져 있다 |
| Codex | `~/.codex/config.toml`, 신뢰한 프로젝트에만 프로젝트 `.codex/config.toml` | `startup_timeout_sec` 기본 10, `tool_timeout_sec` 기본 60, `enabled_tools` / `disabled_tools`, 도구별 승인과 출력 한도 |
| VS Code | `.vscode/mcp.json`(`servers`) 또는 이식 가능한 `.mcp.json`(`mcpServers`) | 서버 신뢰 프롬프트, 도구별 확인, macOS와 Linux의 선택적 샌드박스 |
| Cursor | `.cursor/mcp.json`(프로젝트), `~/.cursor/mcp.json`(전역) | 기본으로 승인, 도구별 허용 목록. 문서화된 숫자 도구 상한은 없다 |
| OpenAI Responses API | 서버마다 `server_url`, `allowed_tools`, `require_approval`을 가진 `mcp` 도구 하나 | 기본으로 승인 켜짐. 요청마다 가져오는 도구 정의가 토큰을 쓴다 |
| OpenAI Agents SDK | `MCPServerStdio`, `MCPServerStreamableHttp`, 호스팅 도구 | `client_session_timeout_seconds` 기본 5. 서버 접두부가 붙은 도구 이름은 선택 사항이다 |

런타임 중립적인 서술은 공유 규칙에 둔다. 이 표를 넘는 런타임별 사실이 중요하면 기억에 기대지 말고 그 런타임의 현재 문서를 읽는다.

## Sources

> 확인 2026-11-07. 날짜가 표시되지 않은 벤더 문서는 날짜가 없고 블로그·논문 날짜는 각 페이지에 찍힌 값이다.

| 주장 | 출처 | 게재 |
|---|---|---|
| 도구 100개의 비용과 로드맵의 점진적 발견 | <https://blog.modelcontextprotocol.io/posts/mcp-roadmap/> | 2026-08-22 |
| 지연 로딩 계층, 1~5% 임계값, 필요할 때 연결, 캐시 경계, 코드 모드 인가 | <https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices> | 2026-07-28 판 |
| 도구 58개에 55K 토큰, 관측된 134K, 도구 검색을 쓴 정확도 | <https://www.anthropic.com/research/advanced-tool-use> | 2025-11-24 |
| 도구 30~50개에서의 성능 저하, 미룬 도구의 한도 | <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool> | 2026-11-07 확인 |
| 검색 기반 선택 정확도 | <https://arxiv.org/abs/2505.03275> | 2025-05-06 |
| 코드 실행 패턴과 그 98.7% 시나리오 | <https://www.anthropic.com/research/code-execution-with-mcp> | 2025-11-04 |
| 코드 모드 | <https://blog.cloudflare.com/code-mode/> | 2025-09-26 |
| Claude Code의 범위, 승인, 한도, 도구 검색 | <https://code.claude.com/docs/en/mcp> | 2026-11-07 확인 |
| Codex 설정, 신뢰한 프로젝트, 승인 모드, 타임아웃 | <https://learn.chatgpt.com/docs/extend/mcp> | 2026-11-07 확인 |
| VS Code 설정과 "설정은 증거가 아니다" | <https://code.visualstudio.com/docs/agent-customization/mcp-servers> | 2026-11-07 확인 |
| Cursor 설정과 승인 | <https://cursor.com/docs/mcp> | 2026-11-07 확인 |
| Responses API의 MCP 도구와 기본 승인 | <https://developers.openai.com/api/docs/guides/tools-connectors-mcp> | 2026-11-07 확인 |
| 함수 10개 미만인 네임스페이스 | <https://developers.openai.com/api/docs/guides/tools-tool-search> | 2026-11-07 확인 |
| 기본 인가 경계로서의 직접 도구 호출 | <https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling> | 2026-11-07 확인 |
| Agents SDK의 승인 지침과 타임아웃 기본값 | <https://openai.github.io/openai-agents-python/mcp/> | 2026-11-07 확인 |
| 사람의 개입(human in the loop) SHOULD 규칙 | <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> | 2026-07-28 판 |
| 로컬 서버의 원격 우선과 작은 목록 | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security> | 2026-07-28 판 |
