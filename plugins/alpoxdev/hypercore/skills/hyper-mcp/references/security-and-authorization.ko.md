# 보안과 인가

MCP 서버와 클라이언트, 그리고 둘을 묶는 호스트의 위협 모델과, 원격 서버가 `2026-07-28`에서 구현해야 하는 인가 규칙을 다룬다. 서버를 HTTP로 노출하기 전, 서드파티 서버를 설치하기 전, 사설 데이터를 만지는 도구를 승인하기 전에 읽는다.

> 영어판: [`security-and-authorization.md`](security-and-authorization.md)

## 목차

- What the protocol can and cannot promise
- Measured threat evidence
- Session-level risk: the lethal trifecta
- Authorization for remote servers
- Attack-specific mitigations
- Running local servers
- Server checklist

## What the protocol can and cannot promise

공식 로컬 서버 안내서는 한계를 분명히 말한다. "**어떤 검사도 서버가 무엇을 할지 입증하지 못한다.** 프로토콜은 서버가 주장하는 그대로인지, 약속한 것만 하는지 보장할 수 없다"(2026-11-07 확인). 이 문서의 나머지는 위험을 줄이는 장치로 읽고 안전의 증명으로 읽지 않는다.

| 층 | `2026-07-28` 규범 문구가 덮는 것 | 덮지 않는 것 |
|---|---|---|
| 트랜스포트와 인가 | 토큰 대상(audience), 토큰 패스스루 금지, PKCE, 리소스 지시자, `Origin` 검증, 상태 핸들 바인딩 | 없음 |
| 도구 메타데이터 | 서버를 신뢰하지 않는 한 클라이언트는 **annotation**을 신뢰할 수 없는 것으로 다루어야 한다(**MUST**) | 도구 **설명**에는 동등한 규칙이 없다. 정의 고정은 "클라이언트를 고를 때 볼 만한 속성"이지 프로토콜 요구사항이 아니다 |
| 조합 | 이름 충돌 구분(**SHOULD**) | 공유 모델 컨텍스트를 통한 서버 간 영향 |
| 프로세스 격리(stdio) | 없음. "클라이언트와 stdio 서버는 하나의 신뢰 영역을 공유한다" | 전부. 격리는 호스트와 운영자의 몫이다 |

## Measured threat evidence

| 위협 | 근거(2026-11-07 확인) | 시사하는 것 |
|---|---|---|
| 도구 오염(tool poisoning): 도구 이름이나 설명에 숨긴 지시 | MCPTox: 운용 중인 서버 45개, 실제 도구 353개, 생성한 사례 1,348개. 최고 공격 성공률 72.8%(o1-mini), 최고 거부율은 3% 미만(arXiv 2508.14925, 2026-09-29 개정). 실전 악용률이 아니라 실험실 벤치마크다. | 모델 정렬은 통제 수단이 아니다. 설명을 검토하고 도구 목록을 작게 유지한다. |
| 호출 없이 미치는 영향 | Trail of Bits(2025-04-21): 모델이 서버 사이에서 지시를 중계하기 때문에 서버가 *호출되지 않고도* 모델 동작을 조작할 수 있다. | 서버 사이의 연결을 격리해도 그 영향까지 격리되지는 않는다. |
| rug pull(승인 뒤 정의 변경) | 승인 뒤에도 정의가 바뀔 수 있다. "일회성 동의 대화상자와 패키지 고정으로는 이 면을 덮지 못한다"(로컬 서버 안내서). | 정의가 바뀌면 다시 묻는 호스트를 선호한다. |
| 신뢰하는 서버를 통한 주입 | 악의적인 GitHub 이슈가 에이전트를 조종해 사설 저장소 데이터를 유출시켰다. Invariant Labs는 이를 "GitHub MCP 서버 코드 자체의 결함이 아니다"라고 했다(2025-05-26). | 신뢰하는 서버도 신뢰할 수 없는 내용을 전달한다. |
| 과도한 권한의 자격증명 | `service_role`로 실행한 Supabase MCP가 권한을 하나도 위반하지 않고 연동 토큰을 공격자가 볼 수 있는 티켓에 복사했다(General Analysis, 2025-07-08). | 최소 권한은 프로토콜이 아니라 서버 운영자의 몫이다. |
| 인증 없는 로컬 리스너 | CVE-2025-49596: 0.14.1 미만 MCP Inspector가 웹 페이지에서 접근할 수 있는 인증 없는 프록시를 노출했다(2025-06-13 게시). | 루프백 바인딩은 인증이 아니다. |
| 서버가 제어하는 URL이 셸에 닿음 | CVE-2025-6514, CVSS 9.6: `mcp-remote` 0.0.5–0.1.15가 조작된 `authorization_endpoint`로 OS 명령 주입을 허용했다(2025-07-09 게시). | 클라이언트는 URL을 셸을 거쳐 열어서는 안 된다(**MUST NOT**). |

OWASP MCP Top 10(MCP01–MCP10)은 체크리스트 어휘로 쓸 만하다. 다만 프로젝트 스스로 베타 릴리스라고 밝히므로 표준이 아니라 분류 체계로 인용한다.

## Session-level risk: the lethal trifecta

사설 데이터 접근, 신뢰할 수 없는 내용 노출, 외부와 통신하는 능력을 한 세션에 모으면 공격자가 제어하는 내용 한 조각으로 그 세션을 유출로 몰아갈 수 있다(Willison, 2025-06-16). MCP 유지관리자들도 같은 틀을 쓴다. "위험 프로파일은 개별 서버의 속성이 아니라 세션의 속성이다"(도구 annotation 글, 2026-03-16). 호스트가 함께 불러오는 서버 묶음 전체를 평가하고 서버를 하나씩 따로 보지 않는다.

## Authorization for remote servers

인가는 선택 사항이고 트랜스포트 범위에 묶인다. HTTP 기반 서버는 인가 명세를 따르는 것이 좋다(**SHOULD**). "STDIO 트랜스포트를 쓰는 구현은 이 명세를 따르지 않는 것이 좋고(**SHOULD NOT**), 대신 환경에서 자격증명을 가져와야 한다"(인가 명세, 2026-11-07 확인).

| 단계 | 요구사항 |
|---|---|
| 기반 표준 | 인가 서버는 기밀 클라이언트와 공개 클라이언트에 OAuth 2.1을 구현해야 한다(**MUST**). |
| 리소스 발견 | MCP 서버는 OAuth 2.0 Protected Resource Metadata(RFC 9728)를 게시해야 한다(**MUST**). 클라이언트는 이를 사용해야 하며(**MUST**), `WWW-Authenticate`에 리소스 메타데이터 URL이 있으면 그 URL을 읽고 없으면 잘 알려진 경로로 대체한다. |
| 인가 서버 발견 | 서버는 RFC 8414 또는 OpenID Connect 디스커버리를 제공한다. 클라이언트는 둘 다 지원해야 한다(**MUST**). 받아온 메타데이터의 `issuer`는 URL을 만들 때 쓴 발급자와 같아야 하고(**MUST**), 다르면 클라이언트는 그 메타데이터를 사용해서는 안 된다(**MUST NOT**). |
| 클라이언트 등록 | 클라이언트는 클라이언트 ID를 얻어야 한다(**MUST**). 우선순위는 사전 등록, Client ID Metadata Documents(CIMD), Dynamic Client Registration, 사용자에게 묻기 순이다. DCR은 `2026-07-28`에서 폐기 예정(Deprecated)이고 CIMD를 지원하지 않는 인가 서버용으로만 남는다. |
| PKCE | 클라이언트는 PKCE를 구현해야 하고(**MUST**), 서버 메타데이터가 PKCE를 알리지 않으면 진행을 거부해야 한다(**MUST**). |
| 리소스 지시자 | 클라이언트는 인가 요청과 토큰 요청 모두에 MCP 서버를 가리키는 RFC 8707 `resource` 파라미터를 보내야 한다(**MUST**). |
| 발급자 검증 | 인가 서버는 `iss`를 반환하는 것이 좋다(**SHOULD**)(RFC 9207). 클라이언트는 코드를 교환하기 전에 존재하는 `iss`를 검증해야 한다(**MUST**). |
| 자격증명 바인딩 | 클라이언트는 저장한 자격증명을 발급자별로 구분해야 하고(**MUST**), 다른 인가 서버와 재사용해서는 안 된다(**MUST NOT**). |
| 토큰 사용 | 토큰은 `Authorization: Bearer`로만 다니고 쿼리 문자열에는 절대 넣지 않는다. 서버는 토큰이 자신을 대상으로 발급됐는지 검증해야 한다(**MUST**). |
| 패스스루 금지 | 서버는 다른 대상으로 발급된 토큰을 받거나 전달해서는 안 된다(**MUST NOT**). 업스트림 API를 호출하려면 서버가 자기 OAuth 클라이언트로 행동한다. |
| 스코프 | 서버는 `WWW-Authenticate` 챌린지에 필요한 `scope`를 적는 것이 좋고(**SHOULD**), 스코프가 부족하면 `403`과 `insufficient_scope`로 답한다. 클라이언트는 챌린지가 요구한 스코프를 먼저 요청한다. `*`나 `all` 같은 전부 포괄 스코프는 피한다. |

`2026-07-28` 공식 인가 튜토리얼은 여전히 사전 등록과 DCR만 설명하고 CIMD는 언급하지 않는다. 명세와 클라이언트 등록 페이지가 정본이므로 튜토리얼과 어긋나면 그쪽을 따른다. OAuth 2.1과 CIMD는 그 자체가 인터넷 드래프트이므로 문구가 바뀔 수 있다고 본다.

기계 대 기계와 기업 싱글 사인온은 선택형 확장이다. OAuth Client Credentials와 Enterprise-Managed Authorization(ID-JAG)이 그것이다. 둘 다 "MCP 클라이언트의 명시적 지원이 필요하고 기본으로 켜지는 일은 없다". 전자의 클라이언트 시크릿은 "장기 자격증명"이므로 확장이 허용하는 곳에서는 JWT 어설션을 선호한다(인가 확장 페이지, 2026-11-07 확인).

## Attack-specific mitigations

| 공격 | 요구 통제(출처: 보안 모범 사례, 2026-11-07 확인) |
|---|---|
| OAuth 프록시를 통한 혼동된 대리인 | 업스트림 클라이언트 ID가 고정된 프록시는 전달 전에 클라이언트별 동의를 받아야 한다(**MUST**). 클라이언트 이름과 스코프, `redirect_uri`를 보여 준다. 동의 페이지를 CSRF와 프레이밍에서 보호하고 `redirect_uri`를 정확히 일치시킨다. 동의 뒤에만 `state`를 설정한다. |
| 토큰 패스스루 | 서버를 대상으로 발급되지 않은 토큰을 받아서는 안 된다(**MUST NOT**). |
| 발견 단계의 SSRF | 서버 측에 배포한 클라이언트는 OAuth URL을 가져올 때 SSRF를 고려해야 한다(**MUST**). HTTPS를 요구하고 사설·루프백·링크 로컬 대역을 막고 리다이렉트 대상을 검증하는 것이 좋다(**SHOULD**). 손으로 쓴 IP 검사보다 이그레스 프록시를 선호한다. |
| 상태 핸들 탈취 | 서버는 들어오는 모든 요청을 검증해야 하고(**MUST**), 핸들을 가지고 있다는 사실을 인증으로 취급해서는 안 된다(**MUST NOT**). 인증된 사용자에 묶인 무작위의 만료되는 핸들(`<user_id>:<handle>`)을 쓰는 것이 좋다(**SHOULD**). `2025-11-25` 이전에 적용되던 세션 탈취 지침을 대체한다. |
| `requestState` 변조 | 인가나 업무 로직에 영향을 주는 상태는 무결성을 보호한다([`protocol-2026-07-28.ko.md`](protocol-2026-07-28.ko.md)). |
| 위험한 인가 URL | 클라이언트는 `http`/`https`(운영 환경은 `https`)만 허용해야 하고(**MUST**) `javascript:`, `data:`, `file:` 같은 스킴을 거부하며 셸을 거쳐 URL을 열어서는 안 된다(**MUST NOT**). |
| 원클릭 로컬 설치 | 원클릭 설정을 제공하는 클라이언트는 정확한 명령을 자르지 않고 보여 주어야 하고(**MUST**), 코드 실행임을 표시하고 명시적 승인을 요구한다. |
| 로컬 HTTP 서버 대상 DNS 리바인딩 | 서버는 `Origin`을 검증해야 하고(**MUST**)(불일치 시 `403`), `127.0.0.1`에 바인딩하는 것이 좋다(**SHOULD**). 그래도 실제 인증은 필요하다. "127.0.0.1 바인딩은 인증 경계가 아니다"(로컬 서버 안내서). |
| elicitation에서 비밀 요청 | 서버는 form 모드 elicitation으로 비밀번호, API 키, 토큰, 결제 자격증명을 요청해서는 안 된다(**MUST NOT**). 그런 입력은 URL 모드로 가고 서버는 URL 흐름을 완료한 사용자가 그 흐름을 시작한 사용자인지 확인해야 한다(**MUST**). |

## Running local servers

로컬 서버 안내서의 원칙이다. "서드파티 로컬 서버를 자신이 넘긴 권한을 정확히 가진 신뢰할 수 없는 코드로 다루고 그 권한은 가능한 한 적게 넘긴다"(2026-11-07 확인).

1. **로컬에서 돌아야 하는지 먼저 묻는다.** 원격 API를 감싸기만 하는 서버는 로컬 실행으로 얻는 게 없다. 원격 Streamable HTTP 판을 선호한다.
2. **출처를 확인한다.** 게시자를 식별하고 정확한 패키지 이름을 확인하고 버전을 고정한다. 실행기 고정(`npx`, `uvx`)은 최상위 패키지만 고정하고 다이제스트로 고정한 컨테이너 이미지는 의존성 트리 전체를 고정한다.
3. **도구 목록을 읽는다.** 모델 없이 인스펙터로 읽고 설명에 도구의 일과 무관한 지시가 있는 서버는 뺀다.
4. **프로세스를 격리한다.** 서드파티 서버는 필요한 디렉터리 말고는 아무것도 마운트하지 않은 컨테이너나 VM에서 돌린다.
5. **자격증명을 격리한다.** 서버마다 범위를 좁힌 토큰을 서버별 설정으로 넘기고 전역으로 내보낸 셸 변수로는 절대 넘기지 않으며 장기 비밀은 OS 비밀 저장소에 둔다.
6. **파일시스템을 제한한다.** 가능한 한 좁은 루트를 주고 가능하면 읽기 전용으로 준다. 설정 허용 목록은 협조적 장치이고 경계는 컨테이너이다.
7. **목록을 작게 유지한다.** 설정한 모든 서버가 다른 모든 서버와 모델 컨텍스트를 공유한다.

## Server checklist

- [ ] 입력 검증, 접근 통제, 호출 속도 제한, 출력 정화를 갖춰야 한다(**MUST**). 도구 페이지의 서버 규칙 네 가지가 이것이다.
- [ ] `file://` 리소스는 경로 순회를 막도록 경로를 정화하고 프롬프트는 입력과 출력의 주입을 검증한다.
- [ ] 원격: 위 표의 OAuth 흐름, 요청마다 대상 검증, 토큰 패스스루 없음, 최소 권한 스코프.
- [ ] 로컬 HTTP: `Origin` 검증, 루프백 바인딩, 인증.
- [ ] 핸들과 `requestState`는 추측할 수 없고 만료된다. 사용자에 묶이고 무결성이 보호된다.
- [ ] `x-mcp-header`로 표시한 비밀이나 개인정보가 없고 elicitation URL에도 없다.
- [ ] annotation은 도구를 사실대로 설명하고 안전에 중요한 어떤 것도 클라이언트가 annotation을 지키는 데 기대지 않는다.

## Sources

> 확인 2026-11-07. 명세와 문서 페이지는 `2026-07-28` 판이며 권고와 연구 날짜는 각 페이지에 표시된 값이다.

| 주장 | 출처 | 게재 |
|---|---|---|
| 인가 범위, OAuth 2.1, RFC 9728, 대상과 패스스루 규칙 | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization> | 2026-07-28 판 |
| 발견 순서와 발급자 동일성 | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery> | 2026-07-28 판 |
| 등록 우선순위, CIMD, DCR 폐기 예정 | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration> | 2026-07-28 판 |
| PKCE, 리소스 지시자, 패스스루 금지 | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations> | 2026-07-28 판 |
| `iss` 검증, 발급자별 자격증명, DCR 폐기 예정 | <https://modelcontextprotocol.io/specification/2026-07-28/changelog> | 2026-07-28 판 |
| 공격 목록과 완화책 | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices> | 2026-07-28 판 |
| 로컬 신뢰 영역, "어떤 검사도 입증하지 못한다", rug pull, 격리 | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security> | 2026-07-28 판 |
| 튜토리얼이 사전 등록과 DCR만 다룸 | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization> | 2026-07-28 판 |
| annotation 신뢰 규칙, 서버 보안 MUST | <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> | 2026-07-28 판 |
| form 모드 비밀 금지, URL 모드 규칙 | <https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation> | 2026-07-28 판 |
| 인가 확장 선택형, 장기 클라이언트 시크릿 | <https://modelcontextprotocol.io/extensions/auth/overview> | 날짜 없음 |
| 세션 수준 위험 틀 | <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/> | 2026-03-16 |
| 치명적 삼중주(lethal trifecta) | <https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/> | 2025-06-16 |
| 도구 오염 벤치마크 | <https://arxiv.org/abs/2508.14925> | 2025-08-19, 2026-09-29 개정 |
| 호출 없는 영향 | <https://blog.trailofbits.com/2025/04/21/jumping-the-line-how-mcp-servers-can-attack-you-before-you-ever-use-them/> | 2025-04-21 |
| 도구 오염, rug pull, 그림자화 | <https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks> | 2025-04-01 |
| GitHub 서버를 통한 주입 | <https://invariantlabs.ai/blog/mcp-github-vulnerability> | 2025-05-26 |
| 과도한 권한의 Supabase 자격증명 | <https://generalanalysis.com/blog/supabase-mcp-blog> | 2025-07-08 |
| CVE-2025-49596 (Inspector) | <https://github.com/advisories/GHSA-7f8r-222p-6f5g> | 2025-06-13 |
| CVE-2025-6514 (`mcp-remote`) | <https://github.com/advisories/GHSA-6xpm-ggf7-wc3p> | 2025-07-09 |
| 위협 분류 체계(베타) | <https://owasp.org/projects/mcp-top-10> | 베타 |
