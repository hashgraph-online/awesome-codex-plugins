# Lessons Registry

Реестр общих уроков, которые нельзя терять между `kartinium`, `siz`, `tenevoy` и новыми проектами.

## Семантика и ключи

1. `ПАРСИНГ != АНАЛИЗ`.
   Скрипты только собирают raw-данные. Решения о target/negative/minus принимаются вручную по raw-файлам.
2. Анализ ключевых слов из Wordstat, SQR и Roistat всегда делать без analysis-скриптов.
   Допустимы только raw выгрузки, TSV/JSON, заметки и ручной разбор мной.
3. Маска = единица обнаружения спроса, а не обязательно готовая ключевая фраза.
   Обычно это 1 слово; иногда 2 слова, если термин неразделим.
4. Каждую маску нужно парсить full-depth.
   Для Wordstat это `numPhrases=2000`, а не усечённая выборка.
5. После полного парсинга уже выбирать:
   - целевые фразы;
   - нецелевые фразы;
   - минимальные минус-слова.
6. Минус-слова должны быть минимальными блокирующими токенами.
   Не превращать большие нецелевые фразы в большие минус-фразы, если достаточно одного слова.
7. Не надо плодить все словоформы минус-слова.
   Яндекс сам склоняет базовую форму во многих случаях.
8. Phrase-level evidence из SQR не равно production-ready минус-фразам.
   После manual-review обязателен отдельный reduction-step:
   - выделить минимальный блокирующий токен или короткую safe-маску;
   - проверить конфликт с target intent;
   - только потом строить live-pack.
9. Client report не имеет права смешивать:
   - поисковые фразы, по которым нашли мусор;
   - реальные stop-words / safe-маски, которые были добавлены в кабинет.
   Если смешать эти слои, пользователь получает ложную картину и это считается workflow-ошибкой.
8. Если в клиентском отчете нужны спрос, сезонность и география из Wordstat, это должен делать один и тот же reusable collector-path.
   Разовые ручные вызовы `wordstat_*` для сезонности или географии - такая же ошибка, как и ручной парсинг хвоста.
   Канонический путь:
   - `wordstat_collect_wave.js --dynamics true --regions-report true --regions-tree true`
   - затем `render_wordstat_mask_demand.py`
   - затем `render_wordstat_seasonality.py`
   - затем `render_wordstat_geo.py`

## Объявления и структура

1. Тексты объявлений обязаны соответствовать ключам конкретной группы.
   Кросс-групповые дубли копирайта - баг.
2. Группы должны оставаться семантически чистыми.
   Если группа смешивает интенты, нужно дробить её раньше, чем писать объявления.
3. Быстрые ссылки, уточнения и допэлементы - часть целостности объявления, а не опция.
4. `ACCEPTED` live ad нельзя автоматически считать безопасным для клона.
   Перед split/incubator apply нужен отдельный creative-precheck и safe subset объявлений.
5. `ExcludedSites after-pack` и `ad replacement pack` нельзя считать готовыми только по markdown.
   Перед live apply они должны пройти отдельные скриптовые apply-safety validators:
   `validate_excluded_sites_pack.py` и `validate_ad_replacement_pack.py`.
6. Полный optimisation cycle действующего search-кабинета нельзя считать законченным без отдельного creative lane.
   Минимальный обязательный набор:
   - current ads raw;
   - ad-level performance;
   - text outliers;
   - replacement pack;
   - future copy/test pack.
7. Если в одной группе крутятся почти одинаковые тексты, это не "нормальный A/B test", а creative debt.
   До роста ставок или broad-экспансии такой долг надо фиксировать отдельным replacement/test планом.

## Scope и планирование

1. Если пользователь просит оптимизировать существующий кабинет и отдельно называет приоритетные РК, это по умолчанию приоритет очереди, а не разрешение забыть остальные активные кампании.
2. Для account-wide optimisation default scope = все активные кампании нужного канала.
   Сужать scope можно только при явном `только эти кампании`.
3. Если пользователь отдельно сказал, что conversions/leads считаются некорректно, skill обязан сначала явно переопределить optimisation truth-layer, а уже потом строить plan и verdict.
4. Для operational Direct-задач нельзя считать `plan-only` default-режимом.
   Если пользователь просит сделать/внедрить/оптимизировать, default path = `plan -> apply -> self-check`.
5. После live-apply нельзя отдавать пользователю только факт изменения или ссылку на raw JSON.
   Обязателен client-facing report:
   - `что было`;
   - `что сделал`;
   - `что стало`;
   - counts `before/after`;
   - список затронутых `campaign_id/adgroup_id/ad_id`;
   - пути к `apply_results/readback/summary`.
   Если этого нет в ответе пользователю, workflow считается незавершённым.
6. После apply нельзя доверять только собственному намерению или `200 OK`.
   Нужны read-back, item-level result checks и явная фиксация, что реально изменилось.
7. Для real replacement ad-layer недостаточно `ads.add + moderation`.
   Если старый loser должен уйти, нужна полная closure-цепочка:
   `new ad ACCEPTED/ON -> old ad suspend -> old ad archive -> pair read-back old/new ids`.
8. Dangerous autotargeting в действующих search-группах нельзя оставлять на ручной ad-hoc логике.
   Для account-wide apply нужен отдельный reusable-runner c dry-run, `keywords.update` и read-back по `---autotargeting`.
9. Shared negative sets в Direct API имеют асимметричный JSON-формат.
   Для `negativekeywordsharedsets.add` поле должно быть `NegativeKeywords: [..]`,
   а для `campaigns.update` в unified campaigns привязка должна идти как
   `NegativeKeywordSharedSetIds: {"Items": [id]}`.
9. Если пользователь хочет убрать `24/7`, а явный график компании не подтверждён из source-of-truth,
   safest fallback не `9-18`, а только night-cut.
   Практический default: убрать глубокую ночь и оставить основной коммерческий день/вечер, затем проверить по live-readback и autotest.
10. Для SQR/поисковых фраз нельзя начинать с машинного shortlist-а минус-слов.
   Правильный путь:
   - fresh raw;
   - полный ручной просмотр каждой строки;
   - manual verdict layer;
   - reduction-layer до минимальных stop-words / safe-масок;
   - только потом pre-apply pack из `approved_negative`.
11. Нельзя убирать уже добавленные фразы, новые поисковые фразы или ранее найденные строки только потому, что они кажутся "очевидным мусором".
   До exact ручного verdict по строке любое удаление/минусация считается нарушением workflow.
12. Если пользователь отдельно потребовал "просмотреть вручную каждую строку", это жёсткий gate.
   До завершения такого gate live-минуса и rollback по SQR запрещены.
13. Reusable apply-script для no-moderation packs не должен по умолчанию принимать negative tasks с полем `phrase`.
   Такой apply разрешён только через explicit override, иначе agent слишком легко пронесёт phrase-pack в live.

## Источники правды

1. Если у клиента реально подключён Roistat, он первый источник по лидам/продажам/выручке.
2. Если Roistat не подключён или неполон, fallback = Metrika + Direct Reports.
3. Live API/state всегда выше старой markdown-документации.
4. Если пользователь сказал что локальные raw-выгрузки устарели, они автоматически переходят в архивный слой.
   Решения по active/live-задачам в этот момент принимаются только по fresh live-snapshot из Direct/Roistat/YouGile.
5. Даже local-only цикл надо завершать YouGile-sync с ссылками на docs/raw bundle и явной пометкой, был ли live apply.
6. Если через YouGile API нельзя прикладывать файлы, критичный summary нельзя прятать только в локальных md.
   Минимум дублировать прямо в задачу/чат:
   - live-state;
   - checkpoint dates;
   - reaction rules;
   - decision thresholds.

## API gotchas

1. Для short-window РСЯ placements рабочий universal рецепт = `CUSTOM_REPORT` + `Placement` + `AdNetworkType=AD_NETWORK`.
   Не рассчитывать на `PLACEMENT_PERFORMANCE_REPORT` как на надёжный общий источник.
2. `ExcludedSites` в `Campaigns.get` может прийти как `null`.
   Любой collector/validator/rotation-script должен быть null-safe.
3. `RSYA junk` = не только `app/VPN`.
   Отдельный класс кандидатов — явный `site-trash inventory`: mobile news / video / feed / off-topic garbage-sites.
   Но тематически релевантные publishers без явного мусорного сигнала блокировать нельзя.
4. Если логика отбора или apply-pack изменилась в ходе одной волны, старые docs/index нельзя оставлять молча.
   Нужно обновить исходный doc или явно пометить его `superseded by ...`, а затем синхронизировать review-index, overlay и YouGile.
5. Для больших operational skills нужен канонический верхний слой:
   - hard rules;
   - session modes;
   - parallel validation mesh.
   Исторические примеры и dated cases должны быть вторичны и не могут переопределять этот слой.
6. Для РСЯ-stoplists проверять не только лимит `1000`, но и baseline-consistency:
   new site не должен уже лежать в текущем `ExcludedSites`,
   `after_items` обязан совпадать с `baseline ∪ add_sites`,
   root domains `yandex.ru`/`ya.ru` запрещены.
7. Если пакет не требует moderation (`settings + negatives + ExcludedSites`), его не надо применять тремя разными ручными командами.
   Нужен единый executable runner с dry-run и read-back validation, чтобы не было drift между шагами.
8. При `ads.add` нельзя копировать `TextAd.AdExtensions` как есть.
   `ads.get` отдаёт объектный список расширений, но `ads.add` принимает только `TextAd.AdExtensionIds`.
9. Новый unified-search adgroup может автоматически получить `---autotargeting` со всеми категориями `YES`,
   даже если source-clone делался без AT.
   Для incubator/copy-кампаний это нельзя оставлять молча: нужен immediate read-back и перевод в `EXACT only`.
10. Для `keywords.update` autotargeting:
   - `Competitor` не является допустимым ключом в `AutotargetingSettings.Categories`;
   - конкурентные запросы выключаются через `BrandOptions.WithCompetitorsBrand=NO`;
   - preferred fix для forced-AT в controlled-search = `Exact YES`, `Alternative/Accessory/Broader NO`, `WithCompetitorsBrand NO`.
11. После `campaigns.add` create payload нельзя считать полноценным post-create подтверждением.
   Для новых кампаний нужно сохранять отдельный `campaigns.get` read-back хотя бы по:
   `UnifiedCampaign.PriorityGoals`, `CounterIds`, `Settings`.
12. `DefaultBusinessId` резолвить live через `businesses.get` по целевому домену.
   Нельзя blindly копировать business id из donor campaign/ad payload: он может не существовать в текущем аккаунте.
13. `campaigns.get.Settings` может содержать `SHARED_ACCOUNT_ENABLED`, но `campaigns.add/update` это поле не принимает.
   Любой clone/repair script должен фильтровать settings перед apply.
14. `TrackingParams=null` на кампании не равен автоматической поломке tracking.
   Если полный template живёт на группах, а `Href` чистый, это валидное состояние; autotest должен проверять ownership, а не просто наличие строки на campaign-level.
15. Нельзя дублировать один и тот же tracking одновременно в `Href`, campaign-level и group-level.
   Сначала выбрать owner слоя tracking, потом валидировать именно его.
16. Нельзя механически сводить donor-based incubators в один регион только ради унификации.
   Если два инкубатора происходят из разных donor campaigns, сначала сохранить региональное разделение, либо полностью переразвести кластеры так, чтобы не осталось внутреннего аукционного пересечения.
17. `ads.moderate` у draft unified-search кампаний может поднять `Campaign.State` в `ON`.
   Если пользователь разрешил только модерацию, safe default = сразу `campaigns.suspend`, чтобы не получить автозапуск после одобрения.
18. `ads.get/adgroups.get` нельзя массово вызывать с произвольным числом `CampaignIds`.
   Для cabinet-wide audit делать batch-read, иначе API вернёт `4001` по лимиту массива.
19. Параллельный Reports API сбор ломается, если `ReportName` генерируется слишком грубо.
   `campaign_id + ms timestamp + random suffix` должен быть стандартом для reusable collectors.
20. `Ad failure audit` нельзя подменять общим creative audit.
   Критичный вопрос — есть ли активные accepted groups без live ads именно из-за ad-layer.
   Legacy draft/archived хвосты и paused variants надо учитывать отдельно, а не выдавать за текущую поломку.
21. `ACCEPTED/ON` ad тоже может иметь реальный defect на уровне компонентов.
   Если `SitelinksModeration=REJECTED` или домены `Href` и sitelinks не совпадают, это отдельный repair-case даже при живой доставке объявления.
   Для таких кейсов нужен узкий point-fix pack: current set -> accepted donor set -> post-readback.
22. Для `ads.update`/`ads.archive` нельзя доверять только top-level `200 OK`.
   Нужно обязательно проверять `UpdateResults` / `ArchiveResults` на item-level `Errors`, иначе partial-failure будет замаскирован как success.
23. После `ads.update` component-level repair immediate read-back может ещё показывать старый `REJECTED`.
   Нужен settle-check через короткий лаг: если обновление реально встало, ad часто переходит в `MODERATION`, а `StatusClarification` становится `Идут показы предыдущей версии объявления`.
24. Для placement-domain в РСЯ Roistat не годится как доказательство `0 лидов`.
   Verdict по stop-sites нужно строить только через Direct Reports API:
   `CUSTOM_REPORT` + `Placement` + `AdNetworkType=AD_NETWORK` + goal клиента (`Goals=[goal_id]`) + `AttributionModels=["LC"]`.
   Если в placements-row `Conversions_* > 0`, площадку блокировать нельзя.
25. При расследовании "главная search-РК просела" нельзя сразу винить последние правки.
   Сначала обязательный чек-лист:
   - primary CID из overlay;
   - live autotest;
   - `yesterday vs prev day vs 14d` по Roistat;
   - `day/day` split по adgroups;
   - apply-артефакты именно по этому CID.
26. Для агентного Direct-ops single-board Kanban быстро превращается в мусор.
   Intake, execution, monitoring, research, knowledge и system должны жить на разных досках или в жёстко разделённых плоскостях.
   Иначе теряется deterministic routing и backlog перестаёт быть управляемым.
27. В агентной архитектуре нужен выделенный collector-plane.
   Сбор raw-данных и контроль качества сбора должны быть отдельной ответственностью до анализа и apply.
28. Один executor agent должен выполнять только один bounded work item.
   Глубокий контекст разрешён, но пакетование нескольких разнородных действий в один исполнительный run создаёт самоуправство и ломает контроль.
29. Долгий `codex exec` без новых JSON-событий не означает зависание.
   Для operator-facing chief administrator нужен heartbeat-слой: elapsed time, last signal age, event count и живой runtime trace в той же реплике.
30. Для Roistat daily snapshot через `project/analytics/data` default dimension = `daily`.
   `date` может отдавать `internal_error`, даже если остальные analytics-запросы проходят.
31. Shell helper scripts в reusable collectors надо вызывать через явный интерпретатор.
   Не полагаться на execute-bit сервера для `*.sh`; стандарт = `bash script.sh`.
32. Для stop-sites РСЯ между analysis и apply нужен отдельный validation slice.
   `placement_rotation_candidate_pack` нельзя считать готовым к approval только потому, что analysis закончился `ready`.
   Правильная цепочка:
   - `collector.direct.goal_placements`
   - `analysis.rsya.placement_rotation`
   - `validation.pack.rsya`
   - и только потом approval/apply слой.
33. Для validation stop-sites нужно переиспользовать `validate_excluded_sites_pack.py`, а не дублировать правила в новом коде.
   Ошибки валидации должны давать `blocked`, а успешная валидация должна выпускать отдельный `validated_excluded_sites_pack`.
34. В orchestrator UI workflow считается доказанным не в момент `queued`, а после полного browser E2E.
   Нормальный proof:
   - enqueue из панели;
   - pickup worker'ом;
   - артефакты в workspace;
   - новая карточка в UI.
   Если worker работает по cadence и даёт ожидаемую очередь, явный `worker --once` допустим как проверка, но это надо документировать как latency, а не зависание.
35. Approval-gated write workflow не должен создавать approval item для no-op validated pack.
   Если `validation` готова, но `add/remove = 0`, prepare-фаза обязана завершиться `blocked` с читаемым summary/report.
   Иначе `/approvals` засоряется ложными задачами и оператор теряет доверие к очереди.

## Навык и reusable-слой

1. Всё reusable после завершения цикла работ нужно поднимать в global-skill.
2. Всё client-specific должно оставаться локальным:
   - product catalog;
   - board ids;
   - landing rules;
   - brand protected words;
   - account quirks;
   - analysis scripts с бизнес-логикой.
3. Overlay должен хранить контекст клиента, но не секреты.

## Антирегресс

Перед завершением ревизии навыка проверить:

- добавлены ли новые guardrails в `SKILL.md`;
- попали ли новые уроки сюда;
- есть ли reusable template для нового типа анализа;
- есть ли reusable script только для парсинга, если он реально нужен;
- остались ли client-specific вещи локальными.
- не выпали ли обязательные optimisation loops:
  - SQR negatives/new targets;
  - RSYA placement rotation;
  - ad outsider rotation;
  - bids/structure/assets.

## 2026-05 Safety Lessons For Public Bundle

- Skill preflight is mandatory: reread the relevant skill/reference before any Direct, Wordstat, Metrika, Roistat, or YouGile action.
- Live traffic is not self-stoppable: campaign, ad group, ad, keyword, strategy, and placement stop/pause/suspend actions require explicit owner approval.
- Owner-facing reports should use human campaign/ad names by default; raw internal IDs belong in artifacts unless explicitly requested.
- Search-negative marker engines and prefilters are diagnostic only; final packs need fresh SQR, manual verdicts, word/safe-mask reduction, product conflict checks, preflight, approval, and readback.
- Search cleanup should start with high-impression rows, then low-CTR/high-impression tails, then cost/click/conversion layers.
- Product-family and adjacent-route terms must pass assortment checks before becoming stop words or negatives.
