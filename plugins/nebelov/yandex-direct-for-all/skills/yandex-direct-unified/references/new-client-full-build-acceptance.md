# Полная приёмка новой сборки

Этот файл обязателен для нового клиента, мультисайтовой сборки,
комбинаторных объявлений и любой записи новых черновиков в Яндекс.Директ.

Он не заменяет `main-workflow.md`, `keyword-collection-runbook.md`,
`build-and-ops.md` или `workflow-supervisor.md`. Его задача — связать их
результаты в один полный двухпроходный контроль, чтобы отдельный успешный
слой не скрывал пропуск другого слоя.

## Обязательный артефакт

Создай:

```text
full-build-acceptance.tsv
```

Строгая схема:

```tsv
stage	gate_id	level	entity_type	entity_key	field_or_artifact	source_of_truth	decision_source	permission_scope	expected	prepared	accepted	read_back	comparison_mode	evidence_path	status	blocker	reviewer
```

Допустимые `stage`:

1. `pre_write`
2. `post_write`

Допустимые `status`:

1. `PASS`
2. `FIX_REQUIRED`
3. `BLOCKED`
4. `NOT_APPLICABLE`

`NOT_APPLICABLE` разрешён только для явно названного локального
поля/артефакта, у которого нет API-записи, и всегда требует причины в
`blocker`.

## Два прохода

`pre_write=PASS` возможен только когда:

1. полный ожидаемый набор равен подготовленному по стабильным `entity_key`;
2. все обязательные поля и хеши совпадают;
3. нет лишних, пропущенных или подменённых строк;
4. нет пустого обязательного пользовательского решения;
5. permission scope разрешает именно планируемое действие;
6. все нижележащие канонические проверки имеют доказательный `PASS`.

`post_write=PASS` возможен только когда:

1. проверяется тот же полный набор `entity_key`, что и в `pre_write`;
2. результат записи и точный API readback подтверждают каждую сущность и
   обязательное поле;
3. нет лишних новых сущностей;
4. защищённый контур равен предобразу;
5. серверная нормализация подтверждена отдельной reconciliation-строкой по
   контракту нормализации ответов (раздел «Нормализация ответов API» ниже).

Равенство одних количеств недостаточно. Сверяй:

- точное множество `entity_key`;
- человекопонятное имя;
- родительскую сущность;
- посадочную;
- цель и отдельные экономические поля;
- гео;
- канал и места показа;
- тексты и расширения;
- image SHA-256 и API hash;
- обязательные настройки;
- отсутствие лишних объектов.

Правильные количества при подменённой посадочной, цели, группе, объявлении,
изображении или кампании — `BLOCKED` с
`full_scope_entity_reconciliation_failed`.

## Обязательные проверки (gate_id)

Каждая строка ниже обязательна в применимом объёме. Файл собирает доказательства
других справочников и не повторяет их реализацию.

| gate_id | Что доказать |
|---|---|
| `permission_scope` | точная граница `read_only / local_draft / draft_write / moderation / launch` |
| `brand_search_boundary` | брендовый поиск имеет прямое решение пользователя |
| `client_sheet_output_contract` | клиентская таблица не раскрывает внутренние evidence/source/reason/reviewer поля без запроса |
| `campaign_architecture` | логичное объединение без механической нарезки; группы и объявления сохранены |
| `review_evidence_and_widget` | отзывы клиента и значимых конкурентов проверены по первоисточникам, темам и услугам; для каждой целевой посадочной есть решение по отзывам/виджету либо явный `proof_gap`, а непроверенный рейтинг не стал рекламным фактом |
| `service_segment_jtbd` | все существенные услуги × сегменты после исследования спроса, конкурентов и отзывов имеют полный JTBD и связаны с архитектурой, текстами, расширениями и посадочной |
| `copy_source_provenance` | каждый текст и расширение имеет локальную цепочку demand → competitor/reviews → JTBD → client fact/proof; exact readback соответствует этой цепочке |
| `full_entity_inventory` | ожидаемые кампании, группы, объявления, ключи и изображения имеют стабильные ключи |
| `channel_placement_matrix` | Search/Network соответствуют каналу; у РСЯ Search выключен |
| `product_gallery_boundary` | ProductGallery включён только для отдельного товарного маршрута, не для услуги |
| `geo_exact_set` | полное подтверждённое гео и отрицательные регионы совпадают |
| `campaign_economics` | утверждённые goal value, strategy goal, payment type, применимый CPA/bid ceiling и weekly budget не смешаны; самостоятельный ROI/CAC/margin не требуется |
| `time_targeting_three_layer` | weekly grid, `ConsiderWorkingWeekends`, holidays совпадают отдельно |
| `autotargeting_eight_fields` | пять категорий и три брендовых режима прочитаны полностью |
| `keyword_coverage` | полный candidate/synonym universe и решения |
| `negative_provenance_layers` | реальные исключения и generic guards существуют раздельно |
| `responsive_ad_7_3` | обычное комбинаторное объявление имеет 7 заголовков и 3 текста |
| `responsive_ad_object_count_format` | legacy TextAd-пакет имеет 5 объектов; ResponsiveAd использует утверждённый entity inventory и 7/3 внутри каждого обычного объекта |
| `responsive_ad_semantic_quality` | понятный продукт, отдельные доказанные углы, нет bare fragment и permutation-only |
| `product_property_positive_rule` | доказанный product title и отдельно доказанный property title не склеены как дубль |
| `value_led_sitelinks_callouts` | ссылки и уточнения передают подтверждённую ценность |
| `rsya_images_3_5` | 3–5 самостоятельных сцен, вычисляемый scene id, полный lineage, SHA, закреплённая до генерации политика попарного сравнения и два попарных визуальных контроля точного манифеста |
| `rsya_image_scene_distinctness` | один исходный кадр и его фон/кроп/масштаб/формат/цвет/зеркало/поворот занимают один слот; события генерации, общий предок, маски и диптихи доказаны захешированными реестрами |
| `rsya_image_scene_set_reuse` | один доказанный набор повторяется только внутри одинакового точного `route_uid` с `same_route_scene_set_reuse` |
| `search_zero_rsya_images` | Поиск не наследует изображения РСЯ |
| `authorized_draft_manifest` | запись содержит только разрешённые новые черновики |
| `protected_scope_unchanged` | защищённые кампании имеют сопоставимые pre/post snapshots |
| `api_readback_normalization_contract` | нормализатор и его тесты проходят точный whitelist |
| `direct_partial_write_reconciliation` | любой ответ Ads.update завершается полным чтением порции и точной классификацией каждого объявления |
| `direct_partial_write_resume` | журнал читается до выбора baseline/resume guard; повтор отправляет только exact preimage; совпадение одновременно с preimage и target считается готовым target |
| `full_scope_post_readback` | весь, а не первый частичный набор, считан обратно |

Нет обязательной строки или доказательного `PASS` — `BLOCKED` с
`full_build_acceptance_missing`.

Ворота записи модуля (`direct_write_gate.py`) при частичном ответе останавливаются до
чтения результата и не продолжают тот же запуск. Поэтому `direct_partial_write_reconciliation`
и `direct_partial_write_resume` закрываются вручную: полное чтение затронутых объектов,
классификация каждого объекта (записан, не записан, неизвестно), новый пакет только на
незаписанное после сверки с состоянием «до». Пока сверка не сделана — `BLOCKED`.

## Связь проверки и блокера

Эта таблица связывает gate и blocker в одной строке. Регрессионный валидатор
не имеет права искать gate и blocker независимо в разных местах.

| gate_id | verdict | blocker_or_positive_contract |
|---|---|---|
| `brand_search_boundary` | `BLOCKED` | `brand_search_unapproved` |
| `client_sheet_output_contract` | `BLOCKED` | `client_sheet_internal_columns_exposed` |
| `product_gallery_boundary` | `BLOCKED` | `service_product_gallery_enabled` |
| `keyword_coverage` | `BLOCKED` | `missing_keyword_coverage_gate` или `target_synonym_family_uncovered` |
| `campaign_architecture` | `BLOCKED` | `campaign_architecture_unproven` |
| `review_evidence_and_widget` | `BLOCKED` | `review_evidence_or_widget_plan_missing` |
| `service_segment_jtbd` | `BLOCKED` | `service_segment_jtbd_coverage_missing` |
| `copy_source_provenance` | `BLOCKED` | `copy_source_provenance_missing` |
| `full_entity_inventory` | `BLOCKED` | `full_scope_entity_reconciliation_failed` |
| `full_scope_post_readback` | `BLOCKED` | `full_scope_entity_reconciliation_failed` |
| `channel_placement_matrix` | `BLOCKED` | `campaign_channel_strategy_mismatch` |
| `autotargeting_eight_fields` | `BLOCKED` | `autotargeting_full_state_missing` |
| `geo_exact_set` | `BLOCKED` | `geo_scope_mismatch` |
| `campaign_economics` | `BLOCKED` | `goal_value_strategy_price_confused` или `mandatory_setting_unconfirmed` |
| `time_targeting_three_layer` | `BLOCKED` | `schedule_override_unreconciled` |
| `negative_provenance_layers` | `BLOCKED` | `search_negatives_missing` или `real_negative_layer_substituted_by_generic` |
| `responsive_ad_7_3` | `BLOCKED` | `responsive_ad_components_incomplete` |
| `responsive_ad_semantic_quality` | `BLOCKED` | `responsive_ad_semantic_quality_failed` или `responsive_ad_permutation_only` |
| `value_led_sitelinks_callouts` | `BLOCKED` | `sitelink_value_set_missing` или `callout_value_set_missing` |
| `rsya_images_3_5` | `BLOCKED` | `rsya_image_set_incomplete` |
| `rsya_image_scene_distinctness` | `BLOCKED` | `rsya_image_scene_evidence_missing` |
| `rsya_image_scene_distinctness` | `BLOCKED` | `rsya_image_scene_lineage_collision` |
| `rsya_image_scene_distinctness` | `BLOCKED` | `rsya_image_scene_distinctness_unproven` |
| `rsya_image_scene_distinctness` | `BLOCKED` | `rsya_image_panel_lineage_unproven` |
| `rsya_image_scene_distinctness` | `BLOCKED` | `rsya_image_multi_panel_over_quota` |
| `rsya_image_scene_set_reuse` | `BLOCKED` | `rsya_image_scene_set_reuse_unproven` |
| `search_zero_rsya_images` | `BLOCKED` | `rsya_image_assignment_unproven` |
| `permission_scope` | `BLOCKED` | `permission_scope_violation` |
| `authorized_draft_manifest` | `BLOCKED` | `permission_scope_violation` |
| `protected_scope_unchanged` | `BLOCKED` | `protected_campaigns_unchanged_unproven` |
| `api_readback_normalization_contract` | `BLOCKED` | `api_readback_normalization_overaccepted` или `verifier_hotfix_unreviewed` |
| `direct_partial_write_reconciliation` | `BLOCKED` | `direct_partial_write_reconciliation_missing` |
| `direct_partial_write_resume` | `BLOCKED` | `direct_partial_write_resume_unreachable` |
| `direct_partial_write_resume` | `BLOCKED` | `direct_preimage_target_overlap_retried` |
| `product_property_positive_rule` | `PASS` | два отдельно доказанных смысловых угла |
| `responsive_ad_object_count_format` | `PASS` | корректный ResponsiveAd entity inventory не блокируется legacy-счётчиком 5 объектов |
| `rsya_image_registered_diptych` | `PASS` | две заранее зарегистрированные законченные панели плюс третья независимая сцена с полным lineage |
| `rsya_image_scene_set_reuse` | `PASS` | один проверенный трёхсценовый набор повторён только внутри одинакового точного `route_uid` |

## Неизвестные настройки

Если обязательное значение нельзя получить из разрешённого для него источника
(денежные параметры — цель стратегии, ценность цели, CPA или потолок ставки, недельный бюджет,
тип оплаты — только из решения заказчика; счётчик, цели и их номера — из текущего кабинета и
Метрики; остальное — из утверждённого досье сборки):

1. не придумывай его;
2. не оставляй поле пустым;
3. не пропускай настройку;
4. задай пользователю один точный вопрос;
5. поставь `BLOCKED` с `mandatory_setting_unconfirmed`.

Это обязательно для цели, ценности цели, применимого CPA или bid ceiling,
недельного бюджета, типа оплаты, стратегии, гео, расписания, брендового поиска,
товарного канала, модерации и запуска. Маржа, ROI и CAC бизнеса не являются
обязательными полями этой приёмки: рассчитывать их можно только в отдельно
поставленной задаче на подтверждённых входных данных.

`review_evidence_and_widget`, `service_segment_jtbd` и `copy_source_provenance` проверяются в обоих проходах.
Для отзывов `pre_write` проверяет локальные первоисточники, тематическое покрытие и план/`proof_gap` по каждой посадочной; `post_write` сверяет, что в прочитанных рекламных материалах нет неподтверждённых рейтингов, цитат или ссылок. Состояние виджета сайта проверяется на самой странице, а не через поля API Директа.
В `pre_write` сверяется полный локальный набор JTBD и цепочки происхождения с
точным подготовленным содержимым. В `post_write` точные прочитанные из API
заголовки, тексты, быстрые ссылки и уточнения сопоставляются с теми же строками
локального манифеста. Не запрашивай у Direct несуществующие JTBD/evidence поля.

## Клиентские таблицы семантики

Внутренние `source`, `reason`, proof links и reviewer decisions остаются в
доказательных TSV. В клиентскую таблицу согласования не добавляй технические
колонки вроде источника канала или внутренней причины целевости без прямого
запроса пользователя. Нарушение — `client_sheet_internal_columns_exposed`.

## Нормализация ответов API

Допустимые различия между отправленным и прочитанным значением (белый список):

- сервер добавил поле, которого не было в запросе, и оно не входит в проверяемый набор;
- порядок элементов в массиве без смыслового порядка (множества регионов, целей, минус-фраз);
- идентификатор строкой против числа с тем же значением;
- склейка или нормализация минус-фраз и ключей, сопоставленная построчно по правилу из
  [правил работы](operating-rules.md), раздел «Технические лимиты API и записи».

Всё остальное — расхождение: лишний элемент массива, пропавший элемент, `true` против `1`
без явного контракта поля, другое число. Нормализатор ответов Директа и его тесты ведутся
в одном месте проекта. В приёмке сохраняй:

- версию или хеш нормализатора;
- путь к тестам;
- путь к reconciliation-отчёту;
- фактический verdict.

Любое принятие серверной разницы вне точного whitelist —
`api_readback_normalization_overaccepted`.

## Полнота объёма

Частичная первая волна не закрывает полный scope. Перед `PASS` проверь:

```text
expected entity keys
= prepared entity keys
= accepted write result keys
= read-back entity keys
```

Сверка выполняется отдельно для кампаний, групп, объявлений, ключей,
минус-фраз, быстрых ссылок, уточнений и изображений. Нельзя выдавать обработку
нескольких кампаний за завершение десятков ожидаемых кампаний.

## Регрессионная матрица

Для изменения этого workflow создай:

```text
full-build-regression-matrix.tsv
```

Схема:

```tsv
error_id	acceptance_gate_id	fixture	expected_verdict	expected_blocker	actual_verdict	actual_blocker	status	evidence_path	reviewer
```

На каждый отдельный подтверждённый дефект должна быть отрицательная fixture,
которая получает ожидаемый `BLOCKED` до записи или closeout.

Минимальные отрицательные семейства:

1. неверный город, исключённые фиды или цели, нет матрицы «кампания → посадочная»;
2. токен выпущен под другим аккаунтом или виден не тот кабинет;
3. товарная кампания для услуги и брендовый поиск без команды;
4. шумная/неполная семантика и внутренние колонки клиентской таблицы;
5. чрезмерная нарезка, смешанные counts и частичная запись;
6. РСЯ с Search placement, ProductGallery на услуге, полный автотаргетинг,
   неверное гео;
7. goal value перепутан с CPA, отсутствуют обязательные утверждённые стратегия,
   бюджет или цель; отсутствие самостоятельно рассчитанных ROI/CAC/margin не
   является дефектом;
8. воскресенье/holiday/working-weekend конфликт;
9. отсутствующие либо только generic negatives;
10. 3/1 вместо 7/3, bare technical title, шаблонные ссылки,
    permutation-only;
11. 0/1 изображение; один кадр с разными хешами, фоном, кропом, цветом,
    рамкой, зеркалом или поворотом; произвольные scene id; фиктивный либо
    пересекающийся диптих; три панели одного исходника; межмаршрутный повтор
    набора; пропущенные численные сравнения; устаревший хеш манифеста;
    RSYA image на Поиске;
12. запись при `read_only`, выход за manifest и изменение protected scope;
13. совпавшие counts при подменённом `entity_key`;
14. асимметричный pre/post, boolean как деньги, чрезмерная нормализация,
    неизвестный server default;
15. verifier hotfix без полного набора тестов, live readback и независимой
    проверки.
16. пропущенная существенная услуга × сегмент в JTBD или текст/расширение без
    полной demand → competitor → client fact/proof цепочки.

Отдельная положительная fixture:

- `product + separately supported property` получает `PASS`, только если оба
  угла имеют отдельные доказательства и не повторяют одно обещание.
- корректный комбинаторный `ResponsiveAd` получает `PASS` по числу объектов,
  если его object count совпадает с утверждённым entity inventory и каждый
  обычный объект имеет 7/3; legacy-счётчик 5 к нему не применяется.
- `independent_complete_panels` получает `PASS` только для заранее
  зарегистрированного диптиха из двух законченных различимых панелей плюс
  третья сцена из независимого события, с точными registry/policy hashes.
- `same_route_scene_set_reuse` получает `PASS` только при одинаковом точном
  `route_uid`; повтор между разными маршрутами остаётся `BLOCKED`.

После любого исправления, затрагивающего найденный дефект, независимый
проверяющий получает актуальную версию и повторяет целевой сценарий.
