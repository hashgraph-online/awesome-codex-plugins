# 콘텐츠 계층

> 빌드 시점 콘텐츠는 `src/content.config.ts`에서 로더와 Zod 스키마로 모델링하고, 모든 조회를 명시적으로 정렬하며, 라이브 컬렉션은 재빌드를 기다릴 수 없는 데이터에만 씁니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. Two kinds of collections

| 종류 | 설정 파일 | 로드 시점 | 어댑터 필요 |
|---|---|---|---|
| 빌드 시점 컬렉션 | `src/content.config.ts` | 빌드 시점 | 아니오 |
| 라이브 컬렉션 | `src/live.config.ts` | 요청 시점 | 예 |

`official` — 콘텐츠 계층이 유일한 콘텐츠 API입니다. 레거시 콘텐츠 컬렉션은 6.0에서 제거되어 `src/content/config.ts`는 더 이상 위치로 존재하지 않습니다(L-02, L-10).

## 2. Build-time collections

`official` — `src/content.config.ts`가 `collections`를 export하고, 각 항목은 필수 `loader`와 선택적 `schema`를 가집니다(L-10).

```ts
import { defineCollection, reference, z } from 'astro:content';
import { glob, file } from 'astro/loaders';

const blog = defineCollection({
  loader: glob({ base: './src/content/blog', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    publishedAt: z.coerce.date(),
    draft: z.boolean().default(false),
    author: reference('authors'),
  }),
});

const authors = defineCollection({
  loader: file('./src/content/authors.json'),
  schema: z.object({ name: z.string(), url: z.url().optional() }),
});

export const collections = { blog, authors };
```

규칙:

- `official` — `glob()`과 `file()`은 `astro/loaders`에서 옵니다. `glob()`은 URL 친화적인 id를 자동 생성하고, `file()`은 명시적 `id` 키가 필요하며 CSV 등 다른 형식을 위한 커스텀 `parser()`를 받습니다.
- `official` — `z`는 `astro/zod`에서 import합니다. `astro:content`의 `z` 재export는 6.0에서 제거됐고 `astro:schema`도 제거됐습니다.
- `official` — `reference('authors')`는 관계를 정의하고, 검증은 `getEntry()`나 `getEntries()`로 항목을 해석할 때 일어납니다.
- `official` — `deferRender: true`(7.1)는 Markdown 렌더링을 렌더 시점까지 미뤄 빌드 메모리를 줄입니다.
- `official` — Astro 6.0부터 Zod는 4입니다. `z.email()`이 `z.string().email()`을, `{ error }`가 `{ message }`를 대체하고, 기본값은 출력 타입과 맞아야 하며, `.prefault()`가 파싱된 기본값을 제공합니다(L-02).
- `hypercore-default` — 모든 컬렉션에 스키마를 붙입니다. 타입이 없는 컬렉션은 콘텐츠 오타를 빌드 실패가 아니라 런타임 페이지 오류로 만듭니다.

## 3. Querying

`official` — `getCollection()`과 `getEntry()`로 조회하고 `render()`로 렌더합니다(L-10).

```astro
---
import { getCollection, render } from 'astro:content';

const posts = (await getCollection('blog', ({ data }) => !data.draft)).sort(
  (a, b) => b.data.publishedAt.valueOf() - a.data.publishedAt.valueOf(),
);

const { Content } = await render(posts[0]);
---
```

규칙:

- `official` — 컬렉션 순서는 비결정적입니다. 출력에 순서가 보이면 항상 명시적으로 정렬합니다.
- `official` — `render(entry)`는 `{ Content, headings, remarkPluginFrontmatter }`를 돌려줍니다. 렌더하려고 항목의 원본 본문에 직접 손대지 않습니다.
- `hypercore-default` — 라우트 둘 이상이 같은 목록을 쓰면 필터와 정렬을 공유 조회 도우미에 둡니다. 정렬 규칙이 한 곳에 살게 됩니다.

## 4. Live collections

`official` — 라이브 컬렉션은 별도 `src/live.config.ts`에 있고, `defineLiveCollection()`로 선언하며, `loadCollection`/`loadEntry`를 구현한 커스텀 로더를 쓰고, `getLiveCollection()`/`getLiveEntry()`로 읽습니다. 어댑터가 필요하고 Astro는 내장 라이브 로더를 제공하지 않습니다(L-10).

규칙:

- `official` — 라이브 컬렉션에서 Zod 스키마는 선택이지만, 있으면 로더의 타입보다 우선합니다.
- `official` — 라이브 로더 API 형태(`loadCollection`/`loadEntry`의 반환 타입과 오류 봉투)는 산문으로만 설명되고 전체 시그니처 페이지가 없습니다. 정확한 반환 형태는 타입이 붙은 예시로 확인되기 전까지 미확인으로 다룹니다.
- `official` — 7.0 릴리스 노트는 로더가 제공한 캐시 힌트를 읽는 `Astro.cache.set(entry)`를 보여 주지만, 캐싱 가이드는 명시적 옵션 객체만 문서화합니다. 힌트 형태는 `astro:content` 타입이 확인해 줄 때까지 미확인으로 다룹니다.
- `hypercore-default` — 최신성이 재빌드보다 나을 때만 라이브 컬렉션을 씁니다. 라우트 캐싱과 함께 쓰지 않으면 방문자마다 업스트림 호출이 발생합니다.

## 5. TypeScript

`official` — `astro sync`는 `astro:content`, `astro:env`, `astro:actions`를 위한 `.astro/types.d.ts`를 생성하고, dev, build, check 안에서 자동으로 돕니다(L-28).

- `official` — `strict`와 `strictest` tsconfig 템플릿은 콘텐츠 계층에 필요한 설정을 포함합니다. `base` 템플릿에는 `strictNullChecks: true`와 `allowJs: true`가 필요합니다.
- `hypercore-default` — `.astro/types.d.ts`를 손으로 고치지 않습니다. 수동 편집은 다음 sync에서 사라집니다.

## 6. What not to do

- `src/content/config.ts`를 만들지 않습니다. 현재 위치는 `src/content.config.ts`입니다.
- 컬렉션으로 모델링할 수 있는 콘텐츠를 페이지 안에서 `fs`로 읽지 않습니다.
- `astro:content`나 `astro:schema`에서 `z`를 import하지 않습니다.
- 정렬하지 않은 `getCollection()` 결과를 안정된 순서처럼 제시하지 않습니다.
- 어댑터가 없는 프로젝트에 라이브 컬렉션을 추가하지 않습니다.

## Checklist

- [ ] 모든 컬렉션이 `loader`를 밝히고, 라이브 컬렉션이 아니면 `schema`도 밝힙니다.
- [ ] `z`는 `astro/zod`에서 오고 Zod 4 문법(`z.email()`, `{ error }`)을 씁니다.
- [ ] 순서가 보이는 곳마다 `getCollection()` 결과를 정렬했습니다.
- [ ] `reference()` 관계를 `getEntry()`/`getEntries()`로 해석합니다.
- [ ] 라이브 컬렉션에 커스텀 로더, 어댑터, 캐싱 계획이 있습니다.
- [ ] 미확인 레인 항목(라이브 로더 시그니처, `Astro.cache.set(entry)`)을 문서화된 사실로 제시하지 않았습니다.
- [ ] `.astro/types.d.ts`를 손으로 고치지 않고 `astro sync`로 재생성했습니다.

## Sources

> Checked 2026-11-07. 사실은 2026-11-07에 해당 페이지를 연 Astro 조사 레인에서 나왔고, 레인 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `src/content.config.ts`, 필수 `loader`, 선택적 Zod `schema`, `glob()`/`file()` (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| `glob()` id 생성, `file()` 명시 id와 커스텀 parser, `deferRender` (L-10, L-50) | https://docs.astro.build/en/guides/content-collections/ |
| `getCollection()`/`getEntry()`, 비결정적 순서, `render(entry)` (L-10) | https://docs.astro.build/en/reference/modules/astro-content/ |
| `reference()` 관계는 해석 시점에 검증됩니다 (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| `src/live.config.ts`의 라이브 컬렉션, `defineLiveCollection()`, 커스텀 로더, 어댑터 요구 (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| 6.0의 Zod 4와 `z.email()`, `{ error }`, `.prefault()` (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| 6.0에서 레거시 컬렉션, `astro:schema`, `z` 재export 제거 (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| `astro sync`가 content, env, actions용 `.astro/types.d.ts`를 생성합니다 (L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| 콘텐츠 계층에 필요한 tsconfig 템플릿 요구 (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| 요청 시점 데이터와 함께 쓰는 라우트 캐싱 (L-30) | https://docs.astro.build/en/guides/caching/ |
