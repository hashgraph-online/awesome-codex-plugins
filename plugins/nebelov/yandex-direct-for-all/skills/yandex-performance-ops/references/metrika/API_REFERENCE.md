# Действующие маршруты API Метрики

Проверено по официальной документации Яндекса 14 июля 2026 года.

## Отчёты

| Маршрут | Назначение |
|---|---|
| `GET https://api-metrika.yandex.net/stat/v1/data` | табличный отчёт |
| `GET https://api-metrika.yandex.net/stat/v1/data/bytime` | отчёт с разбивкой по времени |

Для CSV сценарии навыка добавляют `.csv` к маршруту. Основные параметры:

- `ids` — счётчики;
- `metrics` — до 20 метрик;
- `dimensions` — до 10 группировок;
- `date1`, `date2` — границы периода;
- `filters` — фильтр сегментации;
- `accuracy` — точность выборки;
- `limit` и `offset` — постраничная выдача табличного отчёта;
- `group` — интервал для `bytime`, в том числе `day`, `week` и `month`.

Ответ JSON содержит исходные параметры в `query`, строки в `data`, общие значения в `totals` и признаки выборки `sampled`, `sample_share`, `sample_size` и `sample_space`. При анализе их нельзя терять.

## Управление

| Маршрут | Назначение |
|---|---|
| `GET https://api-metrika.yandex.net/management/v1/counters` | доступные счётчики |
| `GET https://api-metrika.yandex.net/management/v1/counter/{counter}` | свойства счётчика |
| `GET https://api-metrika.yandex.net/management/v1/counter/{counter}/goals` | цели счётчика |

## Авторизация

Токен передаётся в заголовке `Authorization: OAuth ...`. Для чтения нужно право `metrika:read`; для изменений — `metrika:write`. Эти сценарии используют только чтение.

## Официальные источники

- <https://yandex.ru/dev/metrika/en/stat/openapi/data>
- <https://yandex.ru/dev/metrika/en/stat/openapi/bytime>
- <https://yandex.ru/dev/metrika/en/management/openapi/counter/counters>
- <https://yandex.ru/dev/metrika/en/intro/authorization>
