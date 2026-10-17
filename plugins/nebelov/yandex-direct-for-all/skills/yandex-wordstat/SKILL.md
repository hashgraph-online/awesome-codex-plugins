---
name: yandex-wordstat
description: "Узкий актуальный справочник по Yandex Search API Wordstat v2: методы, схемы, авторизация, квоты, регионы, устройства и динамика. Для рекламного процесса сначала использовать yandex-direct-unified."
---

# Yandex Wordstat API v2

Этот файл не задает порядок сбора семантики, смысловые решения, минус-слова, структуру кампаний или готовность к сборке.

Для любых задач Яндекс.Директа, ключевых фраз, SQR, семантики и стоп-слов сначала открыть `yandex-direct-unified`, его обязательные references и `keyword-collection-runbook.md`. Этот файл использовать только как справочник по текущему Wordstat API.

## Канонический транспорт

- Базовый адрес: `https://searchapi.api.cloud.yandex.net`.
- Текущая версия: синхронный REST API v2.
- Старый `https://api.wordstat.yandex.net/v1/*` и метод `userInfo` не использовать.
- `folderId` передается в теле каждого запроса.
- Для локального клиента рабочий сбор идет по целевому гео; вся Россия может использоваться только как явно обозначенный фон.

## Авторизация

Разрешены два варианта:

1. API-ключ: заголовок `Authorization: Api-Key <key>`.
2. IAM-токен: заголовок `Authorization: Bearer <iam-token>`.

Для API-ключа нужна область `yc.search-api.execute`, а сервисному аккаунту или пользователю — роль `search-api.webSearch.user` на нужный каталог.

Секреты нельзя печатать, передавать в аргументах процесса или сохранять в raw/manifest. Канонический credential-файл должен находиться в закрытом каталоге `700`, иметь владельца рабочего пользователя и права `600`.

## Общие перечисления

Устройства:

- `DEVICE_ALL`;
- `DEVICE_DESKTOP`;
- `DEVICE_PHONE`;
- `DEVICE_TABLET`.

Если передается список `devices`, в нем не более трех значений. Для `topRequests` и `dynamics` список `regions` содержит не более 100 строковых ID.

## Методы

### `POST /v2/wordstat/topRequests`

Назначение: спрос за последние 30 дней, популярные вложенные фразы и ассоциации.

Запрос:

```json
{
  "phrase": "обязательная фраза до 400 символов",
  "numPhrases": 2000,
  "regions": ["регион"],
  "devices": ["DEVICE_ALL"],
  "folderId": "каталог"
}
```

`numPhrases`: от 1 до 2000.

Ответ:

```json
{
  "totalCount": 0,
  "results": [{"phrase": "...", "count": 0}],
  "associations": [{"phrase": "...", "count": 0}]
}
```

Ассоциаций в одном ответе бывает не более 20. Для Директа и `results`, и `associations` сохраняются как raw и дальше проходят только workflow `yandex-direct-unified`.

### `POST /v2/wordstat/dynamics`

Назначение: динамика спроса.

Запрос:

```json
{
  "phrase": "обязательная фраза до 400 символов",
  "period": "PERIOD_MONTHLY",
  "fromDate": "2026-01-01T00:00:00Z",
  "toDate": "2026-07-01T00:00:00Z",
  "regions": ["регион"],
  "devices": ["DEVICE_ALL"],
  "folderId": "каталог"
}
```

Периоды: `PERIOD_MONTHLY`, `PERIOD_WEEKLY`, `PERIOD_DAILY`. Даты передаются в RFC3339. Для недельной и месячной динамики допустим только оператор `+`; для дневной поддерживаются все операторы Wordstat.

Ответ:

```json
{
  "results": [{"date": "2026-01-01T00:00:00Z", "count": 0, "share": 0.0}]
}
```

### `POST /v2/wordstat/regions`

Назначение: распределение спроса за последние 30 дней.

Запрос:

```json
{
  "phrase": "обязательная фраза до 400 символов",
  "region": "REGION_ALL",
  "devices": ["DEVICE_ALL"],
  "folderId": "каталог"
}
```

Значения `region`: `REGION_ALL`, `REGION_CITIES`, `REGION_REGIONS`. Путь `/v2/wordstat/regionsDistribution` неверен: это было смешение имени gRPC-метода с REST-путем.

Ответ:

```json
{
  "results": [
    {"region": "ID", "count": 0, "share": 0.0, "affinityIndex": 0.0}
  ]
}
```

### `POST /v2/wordstat/getRegionsTree`

Назначение: дерево поддерживаемых регионов.

Запрос содержит только `folderId`:

```json
{"folderId": "каталог"}
```

Ответ:

```json
{
  "regions": [
    {"id": "ID", "label": "Название", "children": []}
  ]
}
```

Метод официально не тарифицируется, но лишние вызовы запрещены.

## Квоты и повтор

- Не более 10 запросов в секунду.
- Не более 100 запросов в час суммарно для `topRequests`, `dynamics`, `regions` и `getRegionsTree`; дерево регионов имеет нулевую стоимость, но потребляет запрос квоты.
- В v2 нет `userInfo` и ответа с остатком дневной квоты.
- Сборщик обязан вести локальный почасовой учет, ограничивать скорость и обрабатывать HTTP 429/`Retry-After`.
- При ограничении сохраняются raw, manifest, закрытые маски и очередь незакрытых масок. После разрешенного ожидания сбор продолжается с незакрытого элемента без дублей.
- Ошибка целевой маски должна попасть в `wordstat_errors_retry_log.tsv`; волна не закрывается, пока повтор не дал результат либо маска явно не помечена `blocked` с причиной.

## Операторы

Поддерживаются операторы Wordstat `-`, `+`, `!`, кавычки, квадратные и круглые скобки. Их семантика применяется по официальной документации Wordstat. Операторная форма маски не является автоматически готовым ключом Директа.

## Правила для Директа

1. Сначала `intake-gate`, product/routing/protected layers и pre-Wordstat извлечение синонимов.
2. Затем raw Wordstat/SQR.
3. После raw: `SAFE_STOP` только с protected-check, сохраняемый prefilter, затем полный построчный смысловой разбор.
4. Скрипт не имеет права выбирать ключи, ставить semantic verdict или объявлять coverage `PASS`.
5. Каждая raw-строка получает `candidate_id` либо явное решение с причиной.
6. Live apply, минус-слова, черновики и любые записи в Директ требуют отдельного явного разрешения пользователя.

## Первоисточники

- https://aistudio.yandex.ru/docs/ru/search-api/concepts/wordstat.html
- https://aistudio.yandex.ru/docs/ru/search-api/api-ref/Wordstat/
- https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/wordstat_service.proto
