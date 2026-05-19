# Официальный путь сбора поисковых рекламных объявлений Яндекса

Дата фиксации: `2026-03-13`

## Что подтверждено

Для поисковых рекламных объявлений Яндекса подтвержден официальный production-path через `Yandex Search API` в режиме `FORMAT_HTML`.

Это не браузерный обход и не `Firecrawl`.

## Каноническая схема

1. Источник запросов:
   - валидированная матрица `keyword x geo`;
   - либо live ключи из search-кампаний через `Direct API`.
2. Источник выдачи:
   - `POST https://searchapi.api.cloud.yandex.net/v2/web/search`
   - `responseFormat = FORMAT_HTML`
3. Что сохраняется:
   - raw JSON ответа Search API;
   - декодированный raw HTML выдачи;
   - извлеченные поисковые рекламные блоки;
   - таблица `query / region / domain / title / snippet / url / позиции`.

## Подтверждающие remote-источники

- подтвержденные live notes и private proof-артефакты хранятся вне этого публичного репозитория
- в public bundle опираться на текущие collector scripts и текущий skill-канон

## Что именно доказано на Теневом

1. `collector.competitor.scan` уже работал в production workflow.
2. Источник запросов был:
   - `Direct API` -> активные `accepted/on` keywords search-кампаний.
3. Источник рекламной выдачи был:
   - `Yandex Search API` -> `FORMAT_HTML`.
4. Из HTML выделялись только поисковые рекламные блоки с признаком `Реклама`.
5. Несколько live runs подряд завершались повторяемо.

## Что считать закрытым

Закрыт именно слой:

- `Поиск Яндекса`
- `поисковые рекламные объявления`
- `официальный путь`

## Что не считать закрытым автоматически

Не считать автоматически закрытым:

- `РСЯ`
- сетевые объявления Яндекса вне поисковой выдачи
- любой browser-based обход Яндекса как рабочий production path

Для `РСЯ` нужен отдельный подтвержденный официальный источник.

## Public Artifact Boundary

Live proof artifacts, credential files, and project-local runtime outputs should live outside this public repository. Public docs should describe the artifact contract and expected filenames generically, without embedding private hosts, local absolute paths, tokens, client IDs, or account-specific workspace paths.
