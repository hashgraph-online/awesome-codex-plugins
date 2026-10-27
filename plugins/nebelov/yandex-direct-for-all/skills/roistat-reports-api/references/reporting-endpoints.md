# Roistat Reporting Endpoints

Короткий reference для работы с отчетами `Roistat` через API.

## Публично документированные источники

- Analytics API index:
  - `https://help-ru.roistat.com/API/methods/analytics/`
- Построение отчетов:
  - `https://help-ru.roistat.com/features/Analitika_i_otchety/Analitika/Postroenie_otchetov/`
- Пользовательские показатели:
  - `https://help-ru.roistat.com/features/Analitika_i_otchety/Polzovatelskie_pokazateli/`
- Отчет `Новые клиенты`:
  - `https://help-ru.roistat.com/features/Analitika_i_otchety/Specialnye_otchety/Novie_klienti/`

## Канонические методы

### 1. `POST /project/analytics/data`

Главный метод для сборки нового отчета с нуля.

Использовать для:

- измерений `dimensions`;
- метрик `metrics`;
- фильтров `filters`;
- периода `period`;
- атрибуционных срезов через метрики с `attribution`.

### 2. `POST /project/analytics/data/export/excel`

Нужен, когда кроме JSON/TSV требуется настоящий Excel-отчет, собранный API-путем.

### 3. `POST /project/analytics/reports`

Полезен как discovery-layer:

- получить список сохраненных отчетов проекта;
- понять их `levels`, `shownMetrics`, `date_filter_type`, project-specific filters.

Не считать публично документированным write-методом для создания отчетов.

### 3b. `POST /project/analytics/report`

Непубличный, но live-подтвержденный write-метод для saved reports в кабинете.

Подтвержденный контракт:

```json
{
  "report": {
    "title": "API | Директ | Атрибуция MTD | новые/повторные",
    "settings": {
      "date_filter_type": "lead",
      "levels": [],
      "shownMetrics": []
    },
    "folderId": null,
    "isSystem": 0
  }
}
```

Практика использования:

- create: передавать `report` без `id`;
- update: передавать `report` с уже существующим `id`;
- для `operator="in"` в saved report не передавать массивы строк; нормальный формат кабинета тут ожидает массив объектов `{"value","label"}`;
- после каждого write перечитывать `POST /project/analytics/reports` и проверять, что изменился только целевой объект.

Проверено живым прогоном (контракт непубличный и может измениться):

- `POST /project/analytics/report` с произвольным телом на верхнем уровне возвращал `internal_error`;
- `POST /project/analytics/report` с телом `{"report": {...}}` успешно создал новый saved report;
- `POST /project/analytics/report` с `{"report": {..., "id": "<saved_id>"}}` успешно обновил этот saved report.

### 4. `GET /project/analytics/metrics/custom/list`

Нужен, чтобы понять:

- какие кастомные метрики уже заведены в проекте;
- как называются `custom_<id>`;
- зависят ли они от тегов, статусов или полей сделки.

### 5. `POST /project/analytics/attribution-models`

Возвращает список доступных моделей атрибуции.

Обычно полезны:

- `default`
- `first_click`
- `last_click`
- `last_paid_click`

### 6. `POST /project/integration/order/list`

Слой верификации.
Использовать, когда агрегат отчета надо сверить с реальными сделками и визитами.

Рекомендуемый паттерн:

- фильтр по `creation_date`;
- `roistat <> ""`;
- `extend=["visit"]`.

### 7. `GET /project/health/indicator/list`

Состояние процессов проекта: загрузка расходов, обновление аналитики. Используется при расхождении расходов с рекламной системой. Вызов: `roistat_query.sh <выход.json> project/health/indicator/list --http-method GET`.

### 8. Ручные значения показателей (`manual/value/*`)

- Значения загружаются публичными методами `manual/value/*`; считает внешний сценарий, а не движок Roistat.
- Значение привязано к конкретному `source` и уровню и не распределяется на дочерние источники автоматически.
- Для скользящего окна — одно значение на период по каждому `source`; для произвольных дат — по дням (тяжелее, быстрее упирается в `request_limit_error`: нужны паузы с нарастанием, ограничение параллельности, фоновое выполнение).
- `manual/value/add` не допускает пересекающихся периодов: старое значение за тот же период сначала удаляется.

## Сверка оплат за период сырыми сделками

`analytics/list-orders` с периодом, точным фильтром канала и условием `payment_sales > 0` возвращает и старые заявки, оплаченные в периоде, и неоплаченные заявки периода. После чтения отобрать `status=paid` и `paid_date` в полуоткрытом периоде нужного часового пояса, проверить уникальность сделок и сверить число и сумму с `payment_sales` и `payment_revenue` из `analytics/data`. Число всех строк ответа не равно числу оплат. `date_filter_type=payment` в этом методе может игнорироваться — результат проверять, а не доверять успешному ответу. Проход только по датам создания заявок этот отбор не заменяет.

## Значения по умолчанию для нового отчёта

- Измерения `marker_level_1`…`marker_level_3`; уровни 4–6 — отдельной второй волной: полный срез часто упирается в `Too many data`.
- Метрики: `leads`, `first_leads`, `repeated_leads`, `sales`, `new_sales`, `repeated_sales`, `revenue`, `clients`, `paid_clients`, `cpl`, `cpo`, `cac`, `ltv`, `conversion_*`.
- Поля заказа `order_field_N` добавляются в боевой отчёт только при живом доказанном соответствии.

## Практические правила

- Новый отчет собирай отдельной JSON-спекой.
- Существующие saved reports не редактируй.
- Если проблема пользователя формулируется как “старые лиды в текущем месяце”, всегда добавляй audit по сделкам/визитам, а не ограничивайся агрегатом.
- Если нужны “новые заявки от новых клиентов”, сначала проверь, покрывается ли это встроенными метриками `first_leads` / `repeated_leads`, затем проверь проектные custom metrics.
- Если нужен клиентский слой, проверь доступность `clients` / `paid_clients` и условия отчета `Новые клиенты`.
