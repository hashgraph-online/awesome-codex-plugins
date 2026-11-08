# 공식 엔드포인트

> Tier 0: 플랫폼이 자기 엔드포인트를 공개했으면 HTML을 건드리기 전에 그 데이터를 읽습니다.

## 1. 엔드포인트 색인

| 플랫폼 | 엔드포인트 | 2026-11-07 측정 | 비고 |
|---|---|---|---|
| Bluesky | `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=<handle>`, `app.bsky.feed.getAuthorFeed?actor=<handle>&limit=<n>` | 200 | 프로필과 피드는 공개, 검색은 인증이 필요할 수 있음 |
| Mastodon | `https://<instance>/api/v1/accounts/lookup?acct=<user>`, 그다음 `/api/v1/accounts/<id>/statuses` | 미측정 | 공개 타임라인은 인스턴스마다 다름 |
| Hacker News | `https://hacker-news.firebaseio.com/v0/item/<id>.json`, `topstories.json`; 검색은 `https://hn.algolia.com/api/v1/search?query=<q>` | 200 | 인증 없음 |
| Reddit | `<게시물 또는 목록 URL>.json` | 데스크톱·모바일 사용자 에이전트 모두 403, `old.reddit.com`은 302 | 공식 API와 그 OAuth 없이는 사용할 수 없는 것으로 봅니다. 정책 결정인 거부를 넘어 더 오르지 않습니다 |
| X / Twitter | `https://syndication.twitter.com/srv/timeline-profile/screen-name/<handle>`; 단일 게시물은 `https://publish.twitter.com/oembed?url=<post URL>` | syndication 200, oEmbed 301 | oEmbed 리다이렉트는 한 번 따라가고 호스트를 다시 확인합니다 |
| Wikipedia | `https://<lang>.wikipedia.org/api/rest_v1/page/summary/<title>`, `/page/html/<title>` | 200 | 설명이 붙은 사용자 에이전트를 보냅니다 |
| arXiv | `https://export.arxiv.org/api/query?search_query=<q>&max_results=<n>` | 200 | Atom. 3초에 한 번 이하 |
| Stack Exchange | `https://api.stackexchange.com/2.3/search?intitle=<q>&site=stackoverflow` | 미측정 | IP마다 익명 할당량 |
| CrossRef | `https://api.crossref.org/works?query=<q>` | 미측정 | 사용자가 주소를 줄 때만 `mailto`를 붙입니다 |
| GitHub | `gh api repos/<owner>/<repo>` 또는 `https://api.github.com/repos/<owner>/<repo>` | 미측정 | 익명 한도가 낮음. 사용자 자신의 요청에만 기존 `gh` 로그인을 씁니다 |
| npm / PyPI | `https://registry.npmjs.org/<pkg>`, `https://pypi.org/pypi/<pkg>/json` | PyPI 200 | 인증 없음 |
| Wayback | `references/headless-recipes.md` §6 | 200 | 아카이브 사본은 tier 2 |
| YouTube 등 미디어 | `yt-dlp --dump-json` | 미측정 | 미디어 추출기, `references/headless-recipes.md` §5 |
| 피드 | 페이지의 `<link rel="alternate" type="application/rss+xml">` | 미측정 | 최근 글에는 피드가 가장 깨끗한 출처 |

## 2. 엔드포인트 규칙

- 엔드포인트 결과는 출처 `api`이며 보고서에 엔드포인트 경로를 적습니다.
- 엔드포인트의 긍정 증명은 값이 비어 있지 않은 문서화된 키(`displayName`, `title`, `extract`, `entry`)입니다.
- 익명 사용에 401이나 403으로 답하는 엔드포인트는 클라이언트 필터가 아니라 인가 신호입니다. 같은 데이터를 얻으려고 HTML 긁기로 돌아가지 않습니다. `rules/access-policy.md` §2로 보고하거나, 사용자가 요청했을 때만 사용자 본인 자격 증명을 씁니다.
- 문서화된 속도 제한을 지키고, 목록에는 대량 게이트를 적용합니다.
- 여기 나오는 플랫폼 이름은 공개 엔드포인트의 색인이지 사이트별 긁기 규칙이 아닙니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 엔드포인트 목록 | `code-yeongyu/oh-my-openagent`(`dev` 브랜치)의 `ultimate-browsing` 스킬, 2026-11-07에 읽음 |
| 측정 결과 | 2026-11-07에 이 저장소의 네트워크에서 한 요청. 결과는 네트워크에 따라 다르고 예고 없이 바뀜 |
| arXiv 요청 간격 | <https://info.arxiv.org/help/api/tou.html> |
| Bluesky 공개 API 호스트 | <https://docs.bsky.app/docs/advanced-guides/api-directory> |
