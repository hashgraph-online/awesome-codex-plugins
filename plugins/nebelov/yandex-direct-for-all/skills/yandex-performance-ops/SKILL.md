---
name: yandex-performance-ops
description: "Глобальный навык для Яндекс.Директ/Wordstat/Roistat/Метрики: сбор новой семантики, аудит и оптимизация действующих кампаний, live-валидация, media-plan, competitor research и client-overlay контракт для любого локального проекта."
---

# Yandex Performance Ops

Глобальный навык для работы с performance-маркетингом Яндекса из любого локального проекта.

## Path Contract

- `<plugin-root>` = корень этого bundle, где лежат `.codex-plugin/plugin.json`, `skills/`, `mcp/`, `scripts/`.
- Repo-local пример: `./plugins/yandex-direct-for-all`
- Home-compatible install пример: `~/.codex/plugins/yandex-direct-for-all` или `~/.claude/plugins/yandex-direct-for-all`
- `<ops-skill-root>` = `<plugin-root>/skills/yandex-performance-ops`
- `<client-lifecycle-root>` = `<plugin-root>/skills/yandex-direct-client-lifecycle`
- В bundled docs и командах по умолчанию использовать `<plugin-root>/...` или `<ops-skill-root>/...`, а не жёсткий `~/.codex/skills/...`

Цель:
- хранить reusable-методологию, скрипты, промты и уроки в одном месте;
- держать в локальном проекте только контекст клиента и его уникальные правила;
- не терять наработки между `kartinium`, `siz`, `tenevoy` и новыми проектами.

## Что объединяет этот навык

Собрано и нормализовано из:
- `kartinium/.claude/skills/direct-search-semantics`
- `kartinium/.claude/skills/yandex-direct`
- `kartinium/.claude/skills/yandex-wordstat`
- `kartinium/.claude/skills/roistat-direct`
- `kartinium/.claude/skills/media-plan`
- `ads/siz/.claude/skills/direct-optimization`
- `ads/tenevoy/.claude/skills/direct-optimization`
- `ads/siz/.claude/skills/yandex-metrika`
- `ads/siz/.claude/skills/competitive-ads-extractor`
- статистические подходы из `ads/siz/.claude/skills/ppc-data-analysis`

Полная ревизия источников:
- [source_inventory.md](references/source_inventory.md)
- [completeness_audit_2026-03-05.md](references/completeness_audit_2026-03-05.md)

Этот global skill тоже не имеет права “перепридумывать” `Wordstat/Direct` слой мимо исходных source-skills.
Если есть конфликт между краткой интеграцией и source-skill по `Wordstat`, `direct-search-semantics` или `yandex-direct`, использовать source-skill как верхний канон.

Для `Wordstat` канонический reusable reference этого global skill лежит здесь:
- [wordstat_collection_framework.md](references/wordstat_collection_framework.md)
- [future_session_start_checklist.md](references/future_session_start_checklist.md)
Global skill обязан уже сам содержать полный канон Wordstat-сбора.
Локальные project docs могут только добавлять client-specific терминологию, но не заменять global framework.
Для клиентского research-отчета Wordstat теперь считать обязательным три отдельных слоя:
- спрос по базовым маскам;
- сезонность;
- география.

## Когда использовать

Используй этот навык, когда задача относится к одному из блоков:
- сбор новой поисковой семантики через официальный API;
- аудит и оптимизация уже работающих кампаний Яндекс.Директ;
- настройка и pre-moderation валидация поисковых кампаний;
- массовые проверки live-state через Direct API;
- SQR, минус-слова, структура, автотаргетинг, объявления, ExcludedSites;
- Roistat-first анализ лидов/продаж;
- Yandex Metrika отчёты и атрибуция;
- media-plan и plan-vs-fact;
- competitor creative research;
- синхронизация задач в YouGile;
- фиксация reusable-уроков после цикла работ.

## Главный принцип

Global skill = методология + reusable tooling.

Local project = клиентский overlay + client-specific rules.

## Обязательный client-facing report после live-apply

После любого live-изменения в кабинете нельзя ограничиваться коротким "сделано" или ссылкой на сырые JSON.
Нужно сразу собрать и показать пользователю human-readable report с тремя блоками:
- `что было` — исходная проблема, counts, затронутые `campaign_id/adgroup_id/ad_id`;
- `что сделал` — точные live-мутации, какие поля менялись, что сознательно не трогалось;
- `что стало` — read-back и post-check с цифрами `before/after`.

Минимум, который обязан попасть в такой отчёт:
- список затронутых сущностей;
- количество реально изменённых объектов;
- пути к артефактам `apply_results / readback / summary`;
- явное объяснение, почему были выбраны именно эти правки.

Если live-правки уже сделаны, но user-facing report ещё не показан, работа считается незавершённой.

Если user явно просит ускорить большой manual-review через локальные Codex CLI воркеры, это теперь канонический reusable path, а не разовая импровизация:
- launcher: `scripts/codex_cli_swarm_manual_review.py`
- search prompt: `templates/codex_swarm_search_worker_prompt.md`
- rsya prompt: `templates/codex_swarm_rsya_worker_prompt.md`
- search schema: `schemas/codex_swarm_search_chunk_response.schema.json`
- rsya schema: `schemas/codex_swarm_rsya_chunk_response.schema.json`

Этот swarm-path разрешён только как ускорение ручного verdict-слоя:
- launcher обязан собирать единый full `worker knowledge pack` из overlay + product/rules/lessons и отдавать его как canonical context для всего run;
- launcher обязан поверх full pack собирать `chunk focus context` как deterministic extract по текущему chunk;
- каждый Codex worker получает как required reads только `chunk focus context + prior manual context + chunk TSV`;
- full knowledge pack остаётся fallback-слоем и не должен быть обязательным read, если focus-context и prior-context уже достаточны;
- каждый worker обязан вручную покрыть каждый `candidate_id` своего chunk;
- scripts могут только чанковать, запускать, валидировать coverage и merge'ить;

Для 15d creative/growth refresh теперь каноничен отдельный reusable path:
- если задача = `ротация text/image losers` + `новые группы / growth plan`, не надо собирать полный giant-wave заново;
- собрать `Direct account snapshot` на нужное окно через `direct-orchestrator/scripts/collector_direct_account_snapshot.py` c `mode=ads`, чтобы получить:
  - `raw/direct_account_snapshot_v2/raw_bundle/ads/all_ads.tsv`
  - `raw/direct_account_snapshot_v2/raw_bundle/ad_texts/all_source_ads.json`
  - `raw/direct_account_snapshot_v2/raw_bundle/all_campaign_window_totals.tsv`
- собрать search SQR на то же окно через `direct-orchestrator/scripts/collector_search_query_wave.py` или fallback `<ops-skill-root>/scripts/fetch_sqr.sh`;
- `direct-orchestrator/scripts/local_wave_review.py` теперь обязан терпеть волны без `placements` и без `campaigns_meta.json`: в creative-only / growth-only refresh он должен падать обратно на `all_campaign_window_totals.tsv`;
- reusable creative builder: `scripts/build_creative_rotation_from_outliers.py`;
- reusable growth builder: `scripts/build_growth_structure_from_routes.py`;
- creative builder обязан выпускать совместимый комплект:
  - `03_creative_rotation_candidates.tsv`
  - `03_creative_rotation_candidates_v2.tsv`
  - `03_creative_rotation_skipped.tsv`
  - `03_creative_rotation_review.md`
- growth builder обязан выпускать:
  - `09_new_groups_candidates.tsv`
  - `09_missing_phrases_growth_review.md`
  - `12_growth_acceleration_pack.md`
  - а `09_structure_action_plan.tsv` затем собирается штатным `direct-orchestrator/scripts/build_structure_action_plan.py`;
- verdict по новым standalone search-кампаниям нельзя высасывать из воздуха: если 15d growth-layer подтверждает только `new group` / `test layer`, так и писать `новая РК не подтверждена`.
- Если пользователь дал `go` на live apply после такого refresh, канонический reusable apply-path теперь такой:
  1. собрать text-rotation validation/apply pack через `scripts/build_text_rotation_apply_pack_from_tsv.py`;
  2. прогнать `dry-run`, затем live apply через `scripts/apply_ad_replacement_pack.py`;
  3. собрать manifest новых search adgroups и применить его через `scripts/apply_search_adgroup_manifest.py`;
  4. сделать strict readback именно по новым `ad_ids` и `adgroup_ids`, а не полагаться только на giant `campaign_autotest.py` по всей кампании;
  5. отправлять на модерацию только новые объявления через `send_to_moderation.py --ad-ids ...`;
  6. RSYA image replacements не применять автоматически без visual/manual validation даже если refresh-docs их уже рекомендуют.
- `campaign_autotest.py` может быть полезен как общий фон, но для creative/growth live-wave он не должен быть единственным safety-gate: старые `WARN/FAIL` по legacy-сущностям слишком шумные. Канонический gate = strict readback новых сущностей + targeted moderation readback.

Для strict pre-apply перед live-правками теперь каноничен отдельный local-pack path:
- Search strict local pack builder: `scripts/build_local_search_negatives_pack.py`
- Search live drift-check: `scripts/dry_run_search_negatives_pack.py`
- RSYA strict local pack builder: `scripts/build_local_rsya_excluded_sites_pack.py`
- RSYA validator: `scripts/validate_excluded_sites_pack.py`
- RSYA live drift-check/apply helper: `scripts/apply_no_moderation_pack.py`

Правила этого preflight-контура:
- Search server-pack должен собираться только из `high-confidence stop-only` слоя; generic single-word adjectives, numeric junk и low-confidence typo garbage должны отрезаться builder'ом до dry-run.
- RSYA local pack обязан строиться по live `ExcludedSites` baseline, по placements evidence и по client formula (`tail_formula_v3`), а не тупо из manual decisions TSV.
- RSYA builder обязан быть `slot-aware`: если в кампании мало свободных `ExcludedSites`, pack берёт только strongest candidates и паркует overflow в blocked audit.
- RSYA apply/readback обязан канонизировать идентификаторы площадок (`strip/lower`, удаление схемы, `www.` и хвостового `/`) до drift-check и post-apply verify, потому что Direct может сам нормализовать домены/ids на readback.
- Validator и tail-formula не могут жить разными правилами: если client использует `tail_formula_v3`, `validate_excluded_sites_pack.py` обязан валидировать именно по ней, а не по legacy `>5 clicks & CTR>1%`.
- scripts не имеют права придумывать verdict вместо worker-а.
- каждый chunk должен запускаться в изолированном `CODEX_HOME`, чтобы parallel workers не дрались за system skills/install state.
- prompt обязан зажимать worker в короткий command-budget: сначала head knowledge-pack, потом prior-context и chunk, потом только targeted `rg/sed` при реальном противоречии.
- `<cheap-codex-model>` можно использовать как cheap default для bulk swarm only with guardrail: на Search он не должен быть единственным verdict-слоем. Mixed benchmark `2026-03-15` показал сильный bias к `keep`, особенно на brand-stop / route-fix / growth rows. Канонический режим: `mini` для draft/triage, сильная модель или человек для спорного хвоста и финального QA.

Для огромных Search SQR очередей канонический deterministic reduction-layer теперь такой:
- reusable script: `scripts/search_negative_marker_engine.py`;
- project wrapper: `direct-orchestrator/scripts/run_search_negative_marker_cycle.py`;
- это не auto-verdict и не auto-stop, а только shrink-engine перед manual negative review;
- обязательный порядок:
  - bootstrap уже вручную подтверждённых `exclude` / `growth` правил;
  - apply этих правил к новой SQR очереди с audit-файлами `excluded` и `growth_hold`;
  - split остатка на `negative_candidate_rows` и `protected_route_hold`;
  - build compact marker cards только по `negative_candidate_rows`;
- marker cards разрешены только двух типов: `token` и `phrase`;
- `phrase` имеет приоритет над `token`;
- growth/route-like хвост не должен смешиваться с negative-review и обязан уходить в `protected_route_hold` или другой explicit hold-layer;
- user ничего не подтверждает вручную: все manual rules в этот слой приносит агент из уже просмотренных строк;
- карточка marker review обязана быть короткой: `marker`, `scope`, `matched_rows`, `cost/clicks`, `3-5 примеров`.

Минимальный reusable запуск:

```bash
python3 <ops-skill-root>/scripts/codex_cli_swarm_manual_review.py \
  --kind search \
  --queue <review/manual queue.tsv> \
  --project-root <client project root> \
  --merge-into <review/manual_decisions.tsv> \
  --overlay <client overlay json> \
  --local-skill <local skill path> \
  --product-catalog <product catalog path> \
  --search-rules <search rules path> \
  --lessons <lessons path> \
  --manual-decisions <existing manual decisions tsv> \
  --workers 4 \
  --chunk-size 25 \
  --model <cheap-codex-model> \
  --reasoning-effort medium \
  --sandbox danger-full-access \
  --approval-policy never
```

Секреты, board ids и брендовые аксиомы не зашивать в global-skill.

### Правило 0: CLAUDE.md в каждом клиентском проекте (ОБЯЗАТЕЛЬНО!)

При инициализации ЛЮБОГО нового клиентского проекта Директа — ПЕРВЫМ делом создать `.claude/CLAUDE.md` в папке проекта со следующим содержимым:
```markdown
# Проект: [Имя клиента]

## ЖЕЛЕЗНОЕ ПРАВИЛО
ПЕРЕД любым действием с кампаниями — СНАЧАЛА прочитай навык:
- `<ops-skill-root>/SKILL.md`
- optional project-local companion skill, если он реально существует
- `memory/lessons.md` в папке проекта (если есть)

НИКОГДА не импровизируй со ставками, стратегиями, минус-словами.
Все решения — ТОЛЬКО на основе навыка и данных.

## Валюта аккаунта: [KZT/RUB/BYN]
## OAuth токен: [путь к файлу]
## Логин: [client-login]
```

Без этого файла работа с проектом ЗАПРЕЩЕНА. Файл гарантирует что агент не начнёт импровизировать, а сначала прочитает навык и lessons.

Client overlay обязан переопределять build-layer до первого API write, если в нём заданы:
- стратегии `Search` / `РСЯ`;
- `GoalId` / `PriorityGoals`;
- гео (`RegionIds`);
- правило по минус-словам для `РСЯ`;
- формат `group names`;
- формат `DisplayUrlPath`.
- text guardrails и запрещённые термины для Direct copy.

Если overlay противоречит generic defaults скрипта, применять overlay, а не generic defaults.
Если overlay требует `РСЯ без минус-фраз`, clearing pattern в API = `NegativeKeywords: null`; пустой `Items: []` не считать допустимым способом очистки.

Гео-правило на будущее:
- `МО` в речи клиента неоднозначно и нельзя автоматически трактовать как `область без Москвы`;
- если клиент говорит `вся МО`, `полный МО`, `Москва и область`, использовать полный регион `RegionIds=[1]`;
- вариант `область без Москвы` допустим только при явном подтверждении и тогда задаётся как `RegionIds=[1,-213]`.

Client-specific rule sets для discovery и review должны лежать в локальных reference-файлах проекта и подключаться через overlay.

Минимум для reusable full-review:
- `references/product-catalog.md`
- `references/search-stop-word-rules.json`
- `references/rsya-placement-rules.json`

Скрипты не должны знать конкретный `GoalId`, `client_key`, бренд клиента или special-case campaign id из кода. Эти значения надо брать из overlay, raw bundle или local references.

Перед любым новым циклом работ сначала проходить `future_session_start_checklist.md`.
Если в проекте уже есть готовые артефакты и рабочие скрипты, нельзя игнорировать их и идти через импровизацию.

Для `RSYA stop-sites` reusable-правило теперь такое:
- `Clicks >= 5 + (CTR > 1% или app/game/vpn)` = только базовый каркас;
- финальный verdict обязан учитывать ещё `Cost`, `AvgCpc`, `goal conversions`, `campaign benchmark CPA`, тип площадки и protected-platform hints;
- крупные платформы/marketplace нельзя блокировать по одному package-id;
- если есть `clicks > 0` и `cost = 0`, агент не перекладывает это на пользователя, а сам ставит действие `перепроверка raw/source -> потом стоп` или `мониторинг следующей волны`.

Для больших `RSYA placement` очередей теперь каноничен отдельный deterministic `queue prefilter` ДО ручного verdict-слоя:
- reusable script: `scripts/prefilter_rsya_manual_queue.py`;
- это не auto-stop и не auto-verdict, а только фильтр очереди `manual review / monitor / anomaly quarantine`;
- safe-default для всех клиентов:
  - `low_signal_skip`: `conversions = 0`, `clicks < 3`, `CTR < 1%`, `cost < 20`;
  - `zero_click_tail_skip`: `clicks = 0`, `cost = 0`, `impressions < 150`;
  - `protected_low_signal_skip`: `protected/yandex`, `conversions = 0`, `clicks < 5`, `cost < 100`;
  - `app_like_low_signal_skip`: `app-like`, `conversions = 0`, `clicks < 2`, `cost < 35`;
  - `anomaly_quarantine`: `clicks > 0 and cost = 0` или `conversions > 0 and cost = 0`.
- пороги prefilter хранить в client/local rules file (`queue_prefilter`), а не в коде;
- строки из `auto_skipped` нельзя считать готовыми stop-sites: это только `monitor/skip from manual stop review`;
- строки из `anomaly_quarantine` не должны попадать ни в auto-stop, ни в обычный manual-stop shortlist до raw/source recheck.

Если build, структура или тексты начинаются после upstream-исследования через lifecycle-слой, downstream skill обязан сначала проверить наличие трех ручных артефактов:

1. `research/analysis/единая-карта-конкурентов.md`
2. `research/analysis/пакет-структуры-будущего-кабинета.md`
3. `research/analysis/пакет-текстов-и-офферов.md`
4. `research/analysis/готовые-тексты-для-директа.tsv`

Если их нет, не перескакивать сразу к сборке кабинета "из головы", а сначала дособрать этот upstream handoff.

Перед сборкой текстов или отправкой их человеку предпочтителен такой путь:

1. ручная подготовка текстов в `готовые-тексты-для-директа.tsv`;
2. прогон через `scripts/validate_direct_copy_pack.py`;
3. только потом перенос в build-слой.

Если задача дошла до стадии `pre-moderation`, reusable-канон теперь требует отдельного channel split:

1. `Search` и `РСЯ` считаются разными deliverables и не собираются из одного универсального copy-pack.
2. До build/moderation handoff должны существовать отдельные артефакты:
   - `search-group-map`
   - `search-negative-bundles`
   - `search-ad-copy-pack`
   - `rsya-group-map`
   - `rsya-copy-and-image-pack`
3. Для `Search` обязательны:
   - точная группа/интент;
   - landing;
   - negative bundle;
   - text guardrails.
4. Для `РСЯ` обязательны:
   - audience;
   - trigger;
   - message angle;
   - image brief;
   - avoid-list для модерации и mismatch intent.
   - `5` уникальных ad variants на каждую группу;
   - `5` уникальных изображений на каждую группу;
   - file-first карта `group x variant -> template_id/title/image_url`, если изображения берутся из продуктовых шаблонов.
5. Нельзя переносить поисковый copy-pack в `РСЯ` без отдельной переработки под visual/message intent.
6. Нельзя считать `модерация готова`, пока этот channel split не собран и не проверен.
7. Для `Search` production default:
   - на каждую группу должно быть `ровно 5` уникальных объявлений до стадии `moderation-ready`;
   - все `5` должны соответствовать ключам внутри этой группы и заметно отличаться друг от друга по angle / promise / pain / CTA.
   - default bidding strategy = `WB_MAXIMUM_CONVERSION_RATE` с оплатой за клики;
   - default `GoalId` для стратегии = `13`, если overlay явно не задаёт другой search goal;
   - для `Search` в auto strategy нельзя оставлять `BidCeiling=null`; нужен явный `BidCeiling` / max CPC из overlay или approved bid baseline;
   - если в кампании до этого стоял manual bidding и есть `DailyBudget`, при переводе в auto strategy budget нужно переносить в weekly layer, а `DailyBudget` сбрасывать в `null`.
8. Для `РСЯ` production default:
   - на каждую группу должно быть `ровно 5` уникальных объявлений;
   - на каждую такую пятёрку должно быть `5` уникальных изображений;
   - default bidding strategy = `PAY_FOR_CONVERSION_MULTIPLE_GOALS`;
   - default optimisation intent для `РСЯ` = все approved lead goals клиента: звонок / форма / messenger, если пользователь не задал иной shortlist;
   - для unified `РСЯ` с несколькими целями использовать exact enum `PAY_FOR_CONVERSION_MULTIPLE_GOALS` и nested block `PayForConversionMultipleGoals`;
   - `PriorityGoals` должны содержать все approved lead goals клиента; без них multi-goal стратегия невалидна;
   - single-goal `PAY_FOR_CONVERSION` допустим только как явно согласованный fallback; в нём обязателен `GoalId` и `Cpa`;
   - `WB_MAXIMUM_CLICKS` в `РСЯ` нельзя ставить по умолчанию.
- если пользователь просит брать изображения из шаблонов, default source = `последние реальные template covers` из live-каталога/БД, а не выдуманные concept-art placeholders.
- если изображения берутся с сайта клиента, брать их только с соответствующей landing/page этого кластера; переносить фото между чужими посадочными нельзя.
- `DisplayUrlPath` не должен быть техническим id/slugs вида `p1-*`, если у клиента нет такого явного правила. Default = человекочитаемый путь.
- `DisplayUrlPath` должен проходить build-time валидацию: человекочитаемый, без технических префиксов и длиной не более `20` символов.
- имена групп в кабинете не должны оставаться техническими кодами, если не требуется служебная отладка. Default = человекопонятные имена.
- если клиент явно требует `РСЯ` без минус-фраз, build-layer не должен автоматически протаскивать generic negative bundles в `РСЯ`.
- если клиент задаёт разные правила оптимизации для `Search` и `РСЯ`, global skill обязан сохранить channel-specific split и не пытаться выровнять стратегии между каналами.
- в текстах Direct слово `WhatsApp` запрещено: не использовать его в `Title`, `Title2`, `Text`, `callouts`, `sitelink titles/descriptions`.
- если на сайте есть WhatsApp как факт, в Direct copy использовать нейтральные замены типа `быстрая связь`, `связь с менеджером`, `быстрый расчет`.
- статус `live / включено` нельзя объявлять по одному `ResumeResults`. После `campaigns.resume` обязателен свежий `campaigns.get` с проверкой `State`, `Status`, `StatusPayment`, `StatusClarification`.
- если после `resume` кампания остаётся `State=OFF`, skill обязан назвать точный blocker из live API и не писать, что запуск завершён.

Товарный или фидовый слой не считать обязательной частью стандартного пакета.
Добавлять его только по прямому запросу пользователя или после отдельного решения в клиентском документе.

Для competitor-review reusable-слой обязан хранить не только лидирующие домены, но и сами тексты объявлений конкурентов:
- отдельный generated file с колонками `query / region / domain / title / snippet / url`;
- HTML-отчёт обязан показывать этот слой напрямую, а не только счётчики появлений.

Для клиентского веб-отчета канонический путь теперь такой:

1. подготовленные ручные артефакты;
2. машинные рендеры таблиц;
3. HTML-страница без ссылок на внутренние markdown-файлы;
4. `build_secure_client_report.py`;
5. локальная проверка;
6. mobile check `390px`;
7. live check после деплоя.

## Client Overlay Contract

По умолчанию навык ищет локальный файл клиента в таком порядке:
- `./.codex/yandex-performance-client.json`
- `./claude/yandex-performance-client.json`
- `./.claude/yandex-performance-client.json`
- путь из `YANDEX_PERFORMANCE_CLIENT_CONTEXT`

В public bundle client overlays не хранятся. Они должны жить в локальном private project-layer вне git, например:
- `./.codex/yandex-performance-client.json`

Шаблоны:
- [client_context.example.json](templates/client_context.example.json)
- [routing_map.example.tsv](templates/routing_map.example.tsv)
- [campaign_id_map.example.json](templates/campaign_id_map.example.json)
- [copy_map.example.json](templates/copy_map.example.json)

Описание полей:
- [local_overlay_contract.md](references/local_overlay_contract.md)
- [yandex_cloud_search_handoffs.md](references/yandex_cloud_search_handoffs.md)

Быстрый scaffold:
```bash
python3 <ops-skill-root>/scripts/init_client_context.py \
  --output ./.codex/yandex-performance-client.json \
  --client-key acme
```

## Источники данных и иерархия истины

1. Direct API / Reports API / Wordstat API / Roistat API / Metrika API
2. Локальные raw-файлы, собранные скриптами
3. Локальный client overlay
4. Локальные client-specific skills/docs
5. Markdown-документация и агентские выводы

Если live-data конфликтует с локальными доками, верить live-data.
Если пользователь сказал что локальные raw-выгрузки устарели, пункт `2` временно исключается из принятия решений до нового live-сбора.

## Жёсткие правила

1. `ПАРСИНГ != АНАЛИЗ`
- парсинг только официальными API и скриптами;
- анализ делать только вручную мной по raw-файлам;
- не домешивать новые API-вызовы в фазу анализа.
- если в локальном проекте есть `build_decision_report.py`, `build_executive_review.py`, `build_executive_html.py` или похожие рендеры, они не имеют права повышать `review/generated/*safe_ready.tsv` до пользовательского статуса `ready_now`. User-facing verdict слой обязан идти только из `review/manual/*.tsv` и, если проект хранит решения отдельными файлами, `review/manual_decisions/*.tsv`.
- если ручной verdict по строке не внесён, верхний слой обязан прямо показывать `manual gate incomplete` / `manual_verdict_required`, а не маскировать machine shortlist под готовый пакет правок.
- reusable queue-builders обязаны поддерживать и legacy raw paths, и новые `*_v2/raw_bundle/*` пути; path drift не оправдывает переход назад к machine-only verdict.
- scripts имеют право только:
  - собирать;
  - чистить;
  - нормализовать;
  - сортировать;
  - чанковать;
  - рендерить данные.
- scripts не имеют права:
  - ставить вердикты;
  - предлагать стоп-слова, стоп-площадки, рост, ставки, новые группы, мониторинг;
  - решать что target / non-target вместо ручного построчного анализа.
- analysis-скрипты для классификации ключей, фраз, минус-слов и масок запрещены.
- анализ ключевых слов из Wordstat, SQR и Roistat делать без скриптов, только вручную по raw-выгрузкам.
- upstream research по SERP/footprint/competitor pages тоже не собирать вручную по одной фразе.
  Default path = batch job-spec + collector script.
  Для этого использовать:
  - `<client-lifecycle-root>/scripts/yandex_search_batch.py`
  - `<client-lifecycle-root>/scripts/yandex_search_ads_batch.py`
  - `<client-lifecycle-root>/scripts/build_domain_shortlist_from_serp.py`
  - `<client-lifecycle-root>/scripts/firecrawl_scrape.py --jobs-file ...`
  - `<client-lifecycle-root>/scripts/build_followup_jobs_from_serp.py`
  - `<client-lifecycle-root>/scripts/split_tsv_batch.py`
  - `<client-lifecycle-root>/scripts/merge_sitemap_batch_outputs.py`
  - `<client-lifecycle-root>/scripts/render_serp_wave.py`
  - `<client-lifecycle-root>/scripts/render_ad_serp_wave.py`
  - `<client-lifecycle-root>/scripts/render_sitemap_candidates.py`
  - `<client-lifecycle-root>/scripts/render_page_capture_inventory.py`
- полный competitor collection строить не от случайных стартовых запросов, а от вручную валидированного keyword set.
  Допустим ранний scout/reconnaissance для проверки рынка и пайплайна, но exhaustive `organic SERP` / `ad SERP` waves запускаются только после этапа:
  - official `Wordstat` raw;
  - ручная валидация масок, ключей и минус-логики;
  - формирование job-matrix `keyword x geo`.
- для каждого validated keyword нужно сохранять raw-query trail и потом расширять найденные домены через sitemap/page-capture.
- до follow-up сборов сначала строить таблицу повторяемости доменов и вручную утверждать укороченный shortlist.
  Default path на будущее:
  - брать `топ-15` повторяющихся доменов из подтвержденной выдачи Яндекса;
  - до shortlist-builder-а механически исключать очевидные некоммерческие URL-паттерны: статьи, новости, справочники, PDF;
  - не тянуть `sitemap/page-capture` по длинному хвосту слабых доменов.
- после live `organic SERP` wave follow-up jobs должны тоже строиться скриптом, а не вручную:
  - `serp_results.tsv -> page-capture-jobs.tsv`
  - `serp_results.tsv -> sitemap-jobs.tsv`
  - затем только batch collectors по этим job-файлам.
- если batch слишком большой или медленный, разбивать jobs нужно тоже скриптом:
  - `split_tsv_batch.py` для chunk-files;
  - затем несколько collector workers по chunk-TSV;
  - затем merge/normalize step скриптом, без ручной склейки.

2. Wordstat только официальный
- запрещён веб-скрейп Wordstat;
- `numPhrases=2000` обязателен для полного охвата масок.
- канонический порядок всегда такой:
  - `СТРУКТУРА -> МАСКИ -> РЕВЬЮ МАСОК -> ПАРСИНГ СКРИПТОМ -> [полный успех] -> АНАЛИЗ -> ЧИСТКА -> ГРУППИРОВКА`;
  - нельзя перепрыгивать из масок сразу в анализ;
  - нельзя делать one-off `wordstat_*` вызовы вместо wave-collector workflow.
- до любого парсинга обязателен `product map`:
  - официальные названия;
  - разговорные названия;
  - тендерные/закупочные формулировки;
  - жаргон;
  - аббревиатуры;
  - ошибки написания;
  - латиница/кириллица;
  - применения по отраслям.
- `Wave 1` обязан начинаться с `L1` root-масок.
  Где это семантически возможно, root-маски должны быть однословными.
- после `L1` в тот же `Wave 1` добавляются `L2` product masks.
  Для нового круга правил:
  - `Wave 1` в `9/10` случаев строится на однословных масках;
  - `Wave 2` допускает двухсловные маски;
  - трехсловные маски не считать default path без явной причины.
- в клиентском или внутреннем отчете слой спроса из Wordstat нужно показывать отдельно:
  - широкие корневые маски как обзорный ландшафт;
  - точные базовые маски как рабочий слой;
  - использовать только `totalCount` по маске;
  - не суммировать вложенные запросы и не складывать маски между собой как единый объем рынка.
- но для ручного анализа `totalCount` недостаточен:
  - по каждой approved mask надо собирать полный официальный ceiling `2000 строк = 40 страниц`;
  - затем лично просматривать каждую строку `topRequests` и `associations`;
  - только после такого row-by-row review разрешено выделять `target`, `new mask`, `adjacent`, `stop-candidate`, `noise`.
- для SQR manual-review разрешены только два вида deterministic propagation из manual-approved слоя:
  - если стоп-слово уже подтверждено вручную в прошлой или текущей волне, можно автоматически убрать из новой очереди unresolved-строки, где это exact single-word минус встречается в `query`/`criterion`;
  - это не новый verdict, а dedupe/preprocessing;
  - если уже внесён ручной verdict c exact query / exact token / exact phrase внутри конкретного `ad_group_name`, можно строить `manual-approved rulebook` и детерминированно распространять это решение на unresolved-строки только при exact/scope-safe match;
  - такой propagation не придумывает новый action: он берёт только уже утверждённый `assistant_action`/`assistant_reason` из manual decision;
  - конфликтующие matches не auto-apply, а уходят в отдельный conflict-файл;
  - любой skip/propagation обязан идти с audit-файлами `что исключено`, `rulebook`, `auto-decisions`, `conflicts`, `remaining`.
- если full row-by-row manual-review Search-хвоста становится неэкономным, перед любым swarm/manual escalation разрешён только один дополнительный deterministic слой:
  - `search_negative_marker_engine.py`;
  - он не имеет права принимать verdict за строку;
  - он имеет право только:
    - bootstrap already-approved `exclude` и `park_growth` rules;
    - автоматически вычитать строки, уже покрытые этими правилами;
    - автоматически парковать `growth/route/protected` хвост вне negative-review;
    - строить компактные marker cards по оставшемуся `negative_candidate` слою.
- канонические выходы этого слоя:
  - `search_excluded_by_marker_rules.tsv`
  - `search_growth_hold.tsv`
  - `search_protected_route_hold.tsv`
  - `search_negative_candidate_rows.tsv`
  - `search_negative_marker_cards.tsv`
  - `search_negative_marker_examples.tsv`
- good-state для этого слоя:
  - active negative review становится на порядок меньше raw queue;
  - целевые хвосты типа `потолки/LED/скрытый монтаж/парящий профиль/плинтус` не попадают в marker cards только потому, что там встретился случайный модификатор;
  - явный non-target хвост (`другой товар`, `B2B`, `чужой бренд`, `marketplace`, `alien use-case`) остаётся в negative candidates.

Для Search negatives перед live apply теперь обязателен отдельный dry-run слой, а не только validation JSON:
- reusable script: `scripts/dry_run_search_negatives_pack.py`;
- он читает уже подготовленный `search_negatives_pack_apply.json`, снимает live `NegativeKeywords` по adgroup и проверяет:
  - drift между live baseline и `before_keywords` из pack;
  - сколько минусов уже стоят в группе;
  - сколько реально будет добавлено после merge;
- если есть drift, status должен быть `blocked`, а live apply запрещён до пересборки pack;
- canonical outputs: JSON + text report с `drift_count`, `dry_run_add_count`, `skip_existing_count`.

Для RSYA apply теперь канонический hard blocker такой:
- если validation/analysis слой всё ещё содержит `manual_review_count > 0`, `validation_pack_rsya.py` обязан ставить status=`blocked`;
- `prepare_apply_rsya_excluded_sites.py` обязан повторно hard-fail'ить, если в validation summary не ноль manual tail;
- правило простое: `RSYA not touch until manual tail is closed`.
- если пользователь просит `просмотреть поисковые фразы`, `собрать минус-фразы`, `разобрать SQR`, `посмотреть новые поисковые фразы` или явно требует `вручную каждую строку`, default path только такой:
  - свежий live/raw сбор;
  - полный ручной row-by-row review каждой строки;
  - сохранение verdict-слоя в `review/manual/*.tsv` или эквивалентный manual-layer;
  - сбор decision table/report;
  - reduction-layer: phrase-level evidence из manual-layer обязано быть сведено к production-safe stop-words / коротким safe-маскам на нужном scope;
  - отдельный validation-layer: `single-token only` или явно одобренные короткие safe-маски, плюс conflict-check с target words;
  - и только потом pre-apply pack из `approved_negative`.
- если объём manual-review слишком велик и user явно разрешил swarm:
  - резать очередь на bounded chunks;
  - запускать несколько локальных `codex exec` воркеров на `<cheap-codex-model>` с `model_reasoning_effort="medium"` по умолчанию;
  - для escalation / conflict-validation / final QA поднимать более сильную модель (`<strong-codex-model>` или project-approved codex model) только на спорный хвост;
  - для local file-only review по умолчанию НЕ копировать пользовательский `config.toml` в worker `CODEX_HOME`, чтобы воркеры не поднимали лишние MCP-серверы и не тратили токены на startup-шум;
  - промт воркера обязан ссылаться на global skill, local skill, overlay, product catalog / local rules, existing manual decisions и chunk TSV;
  - worker не имеет права редактировать master queue / master decisions напрямую, только вернуть schema-valid JSON;
  - launcher обязан провалить chunk, если `candidate_id` coverage неполный, есть extra ids, есть duplicates или пустые `assistant_action` / `assistant_reason`;
  - merge в `manual_decisions.tsv` разрешён только после такого validation pass.
- запрещено начинать такой workflow с:
  - machine shortlist;
  - `safe_ready`;
  - auto-mined stop words;
  - broad phrase collapse;
  - удаления уже добавленных или новых поисковых фраз до ручного verdict по строке.
- если в кабинете уже есть добавленные фразы, новые поисковые фразы или ранее залитые минуса, это не повод механически их убирать.
  Сначала вручную смотреть сырые строки поисковых фраз, потом принимать решение по exact query/token/phrase.
- live apply/rollback по SQR-минусам заблокирован, пока manual gate не закрыт полностью.
- дубликаты можно схлопывать только после ручного verdict по exact query.
  Нельзя сначала схлопнуть хвост, а потом делать вид, что вся группа строк уже просмотрена вручную.
- phrase-level evidence не равно production-ready минус-фраза.
  Фразы из manual SQR review нельзя лить в кабинет как есть, если из них можно безопасно выделить короткий блокирующий токен или короткую safe-маску.
- канонический production-layer для SQR-negatives:
  - `review/manual/*` = evidence и verdict;
  - `review/manual_reduced/*` или эквивалент = сокращённые stop-words / safe-маски;
  - `live_apply/*negative_tasks*.tsv` разрешён только из reduced-layer.
- reusable apply-path по умолчанию обязан отклонять tasks, где negative params содержат `phrase`, если нет отдельного explicit override от пользователя и письменного объяснения, почему token-reduction невозможен.
- user-facing/client-facing отчет обязан различать:
  - `по каким поисковым фразам нашли проблему`;
  - `какие короткие стоп-слова или safe-маски реально добавили`.
  Нельзя выдавать phrase-level evidence за список реально добавленных production-stop-слов.
- канонический renderer для этого слоя:
  - `scripts/render_wordstat_mask_demand.py`
  - вход = config TSV с approved masks и путями к raw;
  - выход = `wordstat-demand-exact.tsv`, `wordstat-demand-roots.tsv`, `_summary.json`
- обязательные соседние renderer-слои:
  - `scripts/render_wordstat_seasonality.py`
  - `scripts/render_wordstat_geo.py`
  - выход = `wordstat-seasonality-matrix.tsv`, `wordstat-geo-priority.tsv`, `_summary.json`
- канонический collector обязан уметь собирать и эти raw-слои:
  - `--dynamics true`
  - `--regions-report true`
  - `--regions-tree true`
- если для сезонности или географии возникает соблазн сделать разовый `wordstat_*` вызов вручную, это считать нарушением workflow.
  Сначала расширять или переиспользовать `scripts/wordstat_collect_wave.js`.
- после составления `Wave 1` обязателен отдельный `mask review`:
  - web/source synonym review;
  - Wordstat association review на широких масках;
  - только потом запуск collector-а.

3. `Pre-moderation` = отдельный gate, а не хвост build-этапа
- до `ads.moderate` должны быть собраны и проверены:
  - отдельный `Search` pack;
  - отдельный `РСЯ` pack;
  - channel-specific negatives / intent guards;
  - moderation-safe promises;
  - image brief / actual creatives для `РСЯ`;
  - live-readiness checks.
- если чего-то из этого нет, статус должен оставаться `handoff-ready`, но не `moderation-ready`.
- `Wave 1` и `Wave 2` обязательны.
  `Wave 2` строится из gap-analysis по итогам `Wave 1`, а не угадыванием “что еще спросить”.
- парсинг Wordstat допустим только reusable collector-ом из `masks-file -> raw files`.
  Парсинг вручную по одной маске через MCP/tool вызовы запрещён.
- канонический Wordstat entrypoint на этом маке:
  - `bash <ops-skill-root>/scripts/wordstat_tool.sh preflight ...`
  - `bash <ops-skill-root>/scripts/wordstat_tool.sh collect-wave ...`
  - `bash <ops-skill-root>/scripts/wordstat_tool.sh preflight-save ...`
  - `bash <ops-skill-root>/scripts/wordstat_tool.sh collect-wave-save ...`
- discovery order для Wordstat всегда такой:
  - global wrapper `<ops-skill-root>/scripts/wordstat_tool.sh`;
  - global `wordstat_preflight.sh` / `wordstat_collect_wave.js`;
  - только потом project-local fallback из `.claude/skills/direct-search-semantics/scripts/`.
- локальные project scripts нельзя молча считать primary path, если global canonical wrapper доступен.
- режим по умолчанию для агентской работы = `file-first`:
  - raw, summaries, logs и render outputs сначала сохранять в файлы;
  - в контекст не вытаскивать сырые rows/JSON, если это не нужно для точечной проверки;
  - после сбора открывать уже сохранённые `.tsv/.json/.md` частями через `sed/head/rg`.
- до анализа обязателен completeness gate:
  - число raw-файлов должно совпадать с числом масок;
  - пустые/ошибочные raw-файлы должны быть выявлены;
  - новые маски из associations должны быть вынесены в gap/wave2 backlog.
- analysis-скрипты для классификации Wordstat-ключей и минус-слов запрещены.
  После полного raw collection анализ делать только вручную агентами/оператором по raw bundle.
- Не считать Wordstat автоматически только `OAuth`-задачей или только `Cloud`-задачей.
- Сначала нужно live-проверкой определить, какой официальный путь реально доступен клиенту:
  - существующий legacy OAuth-app path;
  - или `Yandex Cloud Search API -> Wordstat`.
- Если legacy path исторически работал у клиента, его нельзя отбрасывать без проверки.
- Если `oauth` токен содержит `wordstat:api`, но live collector получает `403 Forbidden`, это не считать просто "нужно заново авторизоваться".
  Нужно проверить:
  - корректный method/header;
  - не упирается ли проект в `ClientId/app approval`;
  - не нужен ли переход на cloud-path.
- Если preflight написан на `httpx`, не использовать `response.ok`: у `httpx` authoritative-флаг успеха это `response.is_success`.
- Operator-facing Wordstat status должен различать:
  - внутренний баг интеграции;
  - `blocked` по `401/403`;
  - `ready`.
  Нельзя показывать человеку общее `failed`, если live diagnostics уже доказывают конкретный `blocked` verdict по endpoint checks.
- Для cloud-варианта заранее фиксировать:
  - `folder_id`
  - auth mode (`API key` или `IAM token`/service account)
  - роль на сервис-аккаунте `search-api.webSearch.user`
  - какой именно Search API endpoint используется в collector.
- Если в локальном проекте cloud-search path еще не оформлен, сначала проверить:
  - свой private credentials file вне git
  - `references/yandex_cloud_search_handoffs.md`
- Такой bundle считать bridge-path: использовать можно, но отдельно фиксировать, что клиентский собственный cloud-search path еще не оформлен.

3. Roistat first, если он реально подключён у клиента
- заявки/продажи/выручка берутся из Roistat как primary-source;
- Direct/Metrika goal-based conversions использовать как fallback.
- Исключение: verdict по `placement-domain` в РСЯ нельзя строить по Roistat, потому что у него нет надёжного dimension для домена площадки.
  Для stop-sites обязателен Direct Reports API по полю `Placement` с goal клиента (`Goals=[goal_id]`, обычно Roistat goal) и `AttributionModels=["LC"]`.
  Нельзя писать "эта площадка дала 0 лидов" только на основании Roistat.
- Для ежедневного Roistat snapshot через `project/analytics/data` использовать `dimensions=["daily"]`.
  Если использовать `date`, API может вернуть `internal_error` даже при валидном периоде и фильтрах.

4. Нет импровизации при live-правках
- сначала raw dump;
- потом агентский/ручной анализ;
- потом `tasks.tsv`/final pack;
- потом dry-run;
- потом live apply.
- Если reusable helper поставляется как shell-script, вызывать его через явный интерпретатор (`bash script.sh`), а не надеяться на execute-bit на конкретном сервере.

5. Никакой отправки на модерацию и запуска без явного разрешения пользователя
- `ads.moderate` только после подтверждения;
- `campaigns.resume` только после подтверждения.
- после `campaigns.resume` всегда делать readback через `campaigns.get`; без этого запуск не считается подтверждённым.

6. Все reusable-уроки после цикла работ надо поднимать обратно в global-skill
- промт;
- чеклист;
- скрипт;
- gotcha;
- критерий preflight/validation.

7. Устаревшие локальные выгрузки = архив, не source of truth
- Если задача про active кампанию или live-правку, сначала определить статус локальных raw-файлов.

8. Яндекс-выдачу не собирать браузерным обходом
- для Яндекс-поиска и Яндекс-рекламы канонический путь только официальный:
  - API;
  - экспорт;
  - подтвержденная выгрузка из интерфейса;
- браузерный collector не считать допустимым рабочим методом для Яндекс-выдачи;
- для поисковых рекламных объявлений Яндекса подтвержден рабочий путь через `Yandex Search API` в `FORMAT_HTML`;
- этот путь уже доказан на `tenevoy` и описан в `references/yandex_search_api_search_ads_path.md`;
- не путать поисковые рекламные объявления с `РСЯ`: для `РСЯ` отдельный официальный источник должен подтверждаться отдельно;
- если не подтвержден именно нужный рекламный слой, так и фиксировать это в статусе проекта, а не подменять его браузерным парсингом.

9. Операторские и клиентские документы писать на русском языке
- summary, analysis, proposal, status и handoff по умолчанию оформлять на русском;
- англицизмы оставлять только там, где без них теряется точность API/сущности.
- Если пользователь сказал что `data/`/локальные выгрузки устарели, их нельзя использовать для:
  - решения по ставкам;
  - решения по запуску/паузе;
  - оценки текущей эффективности;
  - вывода "что происходит сейчас".
- В таком сценарии обязательный порядок:
  - live Direct state;
  - live Direct reports;
  - live Roistat;
  - current YouGile;
  - затем уже старые локальные файлы как исторический фон.
- Для каждого такого кейса сохранять новый live-snapshot в отдельную свежую папку, а не перетирать старые дампы.
- Даже без указания пользователя проверять устаревание по датам:
  - `mtime` старше `48 часов` для active/live-задачи = suspect;
  - старше `72 часов` = default archive layer;
  - если окно отчёта заканчивается не `today/yesterday`, локальный файл не использовать как primary-source для текущих решений;
  - дата окончания отчёта важнее даты изменения файла.

8. `ACCEPTED` live ad != safe clone
- Если задача включает split/incubator/copy кампаний или групп, текущие live-объявления нельзя считать автоматически пригодными для повторного добавления.
- Перед возможным apply обязателен отдельный creative-precheck bundle:
  - safe ads count;
  - skipped ads count;
  - причины пропуска;
  - diff `source ads found -> safe clone ads`.
- Если source ad не проходит precheck по длине текста или обязательным полям, его нельзя заливать "как есть" даже если он уже ACCEPTED в старой кампании.

9. Операционный период не угадывать
- Для SQR, площадок РСЯ, weekly review и быстрых чисток нельзя молча выбирать окно `2d/7d/30d`.
- Если пользователь явно задал период, он обязателен.
- Если пользователь период не задал, его нужно вывести из задачи и зафиксировать в precheck/plan.
- Client-specific override (например, `2 дня только сейчас`) не поднимать как universal rule в global skill.

10. Coverage-checklist обязателен
- Полный optimisation cycle не должен ограничиваться только структурой или только ставками.
- Перед завершением плана проверить, что были рассмотрены:
  - SQR negatives / new targets / routing / match type;
  - RSYA placements / excluded-sites rotation;
  - ad losers -> replace/create;
  - bids / budgets / device-demo / schedule;
  - structure / cross-negatives / landing relevance / assets.
- Для действующего search-кабинета блок `ad losers -> replace/create` считать обязательным не только как одна строка checklist, а как отдельный creative lane:
  - current ads raw;
  - ad-level performance;
  - `text outliers`;
  - `replacement pack`;
  - новый copy/test pack хотя бы для первой волны.
- План optimisation действующего кабинета без явного creative lane считать неполным даже если negatives/keys/structure уже разобраны.
- Если какой-то блок сознательно не вошёл в план, это надо явно указать как out-of-scope, а не молча пропустить.

11. Scope действующего кабинета не сужать молча
- Если пользователь просит оптимизировать существующий кабинет/аккаунт, default scope = все активные кампании нужного канала в этом кабинете.
- Если пользователь отдельно называет `priority campaigns` вроде "усилить бетон и щебень", это по умолчанию приоритет очереди работ, а не разрешение игнорировать остальные активные РК.
- Narrow scope только при явной формулировке пользователя вида `только эти кампании` / `остальные не трогаем`.
- Если в запросе одновременно присутствуют:
  - `все РК / весь кабинет / account-wide optimisation`;
  - и named priorities,
  skill обязан:
  - либо взять full scope и внутри него отметить очереди;
  - либо коротко уточнить противоречие до того, как сузить plan/apply.

12. Любой цикл заканчивается синхронизацией в YouGile
- Даже если цикл был `local-only` и live apply не делался, в конце надо создать или обновить umbrella-task.
- В описании фиксировать:
  - какие docs собраны;
  - где лежит raw bundle;
  - что уже применено live, а что не применялось;
  - какой следующий шаг разрешён.
- Если API/МСР YouGile не умеет вложения, нельзя оставлять в задаче только локальные пути.
  В описание или в chat message нужно дублировать:
  - фактический live-state;
  - чекпоинты мониторинга;
  - правила реакции;
  - ключевые прогнозы/пороги решений.
- Для переноса локальных `md/json/txt/tsv` в сам YouGile использовать inline-bundle workflow:
  - `python3 <ops-skill-root>/scripts/push_yougile_file_bundle.py --chat-id <task_id> --file <path>`
  - один файл = отдельное сообщение в чат задачи;
  - не ограничиваться локальными markdown links, если пользователю нужен handoff прямо в YouGile.
- Новый client workspace в YouGile создавать только по API, без браузерного/ручного UI-path:
  - `python3 <ops-skill-root>/scripts/bootstrap_yougile_workspace.py --spec <json> --output <json>`
  - после bootstrap обязательно записывать project identifiers and board mappings и `columns` в локальный overlay.
- Перед созданием проверять дубли по backlog/title.

13. Plan-only не считать default mode
- Если пользователь просит `оптимизировать / исправить / внедрить / применить / сделать`, а не `только план / только аудит / только review`, default mode = довести цикл до реализации в рамках разрешённого scope.
- Для таких задач skill не должен останавливаться на review-pack, если нет отдельного blocker-а:
  - manual gate;
  - явный запрет на live apply;
  - отсутствие критичных входных данных;
  - высокий apply-risk без подтверждения.
- После pre-apply presentation следующий default step = apply или подготовка executable apply-pack, а не пассивная остановка на markdown summary.
- После любого apply обязателен self-check:
  - read-back из Direct API;
  - item-level проверка результатов apply;
  - rerun relevant validators/autotest;
  - фиксация `что реально изменилось`, `что не изменилось`, `что надо перепроверить позже`.
- Если skill не пошёл в apply, он обязан явно назвать blocker, а не маскировать остановку как завершённую работу.

14. После исправления логики не оставлять conflicting docs
- Если в ходе той же волны изменилась логика отбора, валидации или scope apply-pack, старые md-файлы нельзя оставлять как будто они всё ещё актуальны.
- Нужно сделать одно из двух:
  - обновить исходный doc;
  - или явно пометить его `superseded by ...`.
- Одновременно обновлять:
  - review-index / umbrella-doc;
  - overlay docs list;
  - YouGile description.

15. Канонический слой важнее исторических примеров
- Канонические для будущих сессий секции:
  - `Жёсткие правила`;
  - `Session Modes`;
  - `Parallel Validation Mesh`;
  - `Основные workflow`.
- Если пример из старого кейса конфликтует с этими секциями, пример игнорировать.

14. `ads.add` != `ads.get` по расширениям
- В `ads.get` текстовые объявления возвращают `TextAd.AdExtensions`.
- В `ads.add` нужно передавать `TextAd.AdExtensionIds`, а не `TextAd.AdExtensions`.
- Любой reusable script, который копирует ads, должен делать явную конвертацию `AdExtensions -> AdExtensionIds`.

15. Новый incubator adgroup в unified-search может сам создать `---autotargeting`
- Даже если source-clone шёл без `---autotargeting`, после `adgroups.add` Direct может автоматически создать AT-keyword.

16. Audience token separation обязательна
- Если в проекте есть отдельный master-token для Audience (`oauth_master_token.json` или явный audience token path), использовать его только для Audience API.
- Direct API должен использовать свой основной Direct token.
- Metrika должна использовать свой отдельный token/env.
- Нельзя молча переиспользовать audience-master token для Direct/Metrika только потому, что он “тоже OAuth”.

16.1. Валидный OAuth-token != доступ к нужному клиенту
- Любой новый OAuth token JSON, который дал пользователь, сначала проверять live-preflight по трем плоскостям:
  - `Wordstat userInfo`;
  - `Direct campaigns.get`;
  - `Metrika management`.
- Если token технически живой, но `Direct` показывает чужие кампании или `Metrika` не видит ожидаемый `counter_id`, такой token нельзя считать клиентским.
- Не делать вывод "token рабочий" до проверки привязки к конкретным активам клиента:
  - ожидаемый `counter_id`;
  - ожидаемый Direct login/campaign set;
  - expected account ownership markers.
- Если `Wordstat` дает `403`, а `Direct/Metrika` работают, это фиксировать как отдельный verdict:
  - `Direct/Metrika ready`;
  - `Wordstat blocked or unapproved`.
- Если человеческий login не подтверждается в `Direct`, но `Metrika` уже открыла целевой счетчик, использовать `owner_login` из `Metrika` как следующий кандидат для `Client-Login` и повторять Direct probe с ним.
- В таком кейсе не подменять client-auth другими токенами и не считать проблему решенной без отдельной авторизации/approval под нужным аккаунтом.

16.2. UI по логину/паролю для Яндекс.Директа запрещён всегда
- Для `Yandex Direct` нельзя использовать вход в кабинет через UI по логину/паролю клиента:
  - ни через браузер;
  - ни через Playwright;
  - ни вручную как fallback;
  - ни для "быстрого preflight";
  - ни для create/update workflow.
- Логин/пароль клиента не считать допустимым operational path для Direct-работ вообще.
- Допустимые пути для `Direct`:
  - официальный `OAuth` token;
  - официальный API-path с уже выданным token file;
  - другой явно подтвержденный пользователем официальный machine path.
- Если у проекта есть только логин/пароль, а рабочего `OAuth/API` path нет:
  - остановить Direct apply/build;
  - явно назвать blocker;
  - запросить официальный auth path вместо UI-обхода.
- Если рабочего `OAuth/API` token file ещё нет, но доступен официальный OAuth app path:
  - в bundle сначала использовать `scripts/start_yandex_user_auth.sh` и `scripts/exchange_yandex_user_code.sh`;
  - default path теперь service-specific:
    - `direct` -> `local-callback`
    - `metrika/audience` -> `manual-code`
  - bundle использует built-in public app profile + `PKCE`, без обязательного ручного client secret;
  - сгенерировать auth URL;
  - дать пользователю готовую ссылку на авторизацию;
  - дождаться callback / confirmation code;
  - сохранить новый token file в проект и прогнать post-auth preflight;
  - и только потом продолжать Direct preflight/build.
- Это правило не ослабляется фразами вроде "новый клиент", "надо быстро проверить", "сейчас только черновики" или "потом заменим на API".

17. Audience hygiene нельзя маршрутизировать generic snapshot-ом
- Запросы уровня `TEN-620`, `минус-аудитории`, `мусорные лиды`, `Яндекс Аудитории` должны вести сначала в специализированный collector:
  - `collector.direct.audience_exclusion_state`
  - затем `analysis.audiences.hygiene`
- Generic `collector.direct.account_snapshot` здесь допустим только как fallback, если специализированный audience collector отсутствует.
- Для incubator/controlled-search слоя такой AT нельзя оставлять с дефолтными категориями.
- Сразу после create/read-back нужно привести его к `EXACT only` через `keywords.update`.

18. Для Yandex Audience -> Direct нельзя использовать raw `segment_id` как `ExternalId`
- `Yandex Audience segment id` и `Direct retargeting ExternalId` для custom audience segments не совпадают.
- Перед любым apply минус-аудиторий обязательный шаг:
  - `Direct Live 4 GetRetargetingGoals`
  - взять `GoalID` для `Type=audience_segment`
  - только этот `GoalID` использовать в `retargetinglists.add`.
- Если segment есть в Audience API и `processed`, но отсутствует в `GetRetargetingGoals`, apply должен блокироваться ещё на planning/validation, а не падать в production-write.
- Для `bidmodifiers` по audience exclusions подтверждённые payload rules такие:
  - `add`: `BidModifiers[].RetargetingAdjustments[]` с `RetargetingConditionId` и `BidModifier`
  - `set`: flat `BidModifiers[].Id` + `BidModifiers[].BidModifier`
  - `Type`, `Enabled`, `Accessible`, nested `RetargetingAdjustment` в `add/set` не использовать.

16. Для агентной системы collector-plane обязателен как отдельный слой
- Один агент или workflow отвечает только за сбор raw-данных и контроль качества сбора.
- Collector не должен сам делать стратегический анализ, правки или verdict.
- Collector-агентов может быть сколько угодно, если каждый из них атомарен и ограничен одной bounded parsing-задачей.
- Запрещено смешивать parsing-stage и analysis-stage внутри одного workflow, даже если это кажется быстрее.
- Для downstream-анализа collector обязан передать:
  - окно дат;
  - источник;
  - coverage;
  - ошибки/пропуски;
  - ссылки на raw artifacts.

17. Один executor agent = один atomic work item
- Нельзя проектировать workflow так, чтобы один исполнитель одновременно:
  - парсил;
  - анализировал;
  - валидировал;
  - применял;
  - писал отчёт.
- Богатый контекст допустим, но только через context bundle:
  - overlay;
  - raw artifacts;
  - linked tasks;
  - knowledge entries;
  - forecasts;
  - previous outcomes.

18. Для зрелого агентного Direct-ops использовать multi-board workspace, а не single-board backlog
- Минимальные плоскости:
  - intake/routing;
  - execution/approval;
  - monitoring/reporting;
  - research/growth;
  - knowledge;
  - system.
- Иначе backlog, мониторинг, системные задачи и growth-исследования смешиваются, а маршрутизация агентов становится недетерминированной.

16. `keywords.update` для autotargeting настраивается через `AutotargetingSettings`
- Категории: `Exact`, `Narrow`, `Alternative`, `Accessory`, `Broader`.
- Конкуренты управляются НЕ через `Categories.Competitor`, а через `BrandOptions.WithCompetitorsBrand`.
- Safe baseline для controlled-search incubator:
  - `Exact=YES`
  - `Alternative=NO`
  - `Accessory=NO`
  - `Broader=NO`
  - `WithCompetitorsBrand=NO`

17. `DefaultBusinessId` нельзя blindly копировать из donor-РК
- Перед `campaigns.add/update` организацию резолвить live через `businesses.get` по целевому домену и текущему аккаунту.
- `BusinessId/DefaultBusinessId` из старого ad payload может быть невалиден в текущем аккаунте или вообще не существовать.

18. `SelectionCriteria.CampaignIds` в `ads.get/adgroups.get` не безлимитный
- Для массового audit/read-back нельзя складывать произвольное число CampaignIds в один вызов.
- Если читаешь много РК разом, batch `CampaignIds` заранее.
- Иначе массовый audit падает на `4001: Превышено допустимое количество идентификаторов`.

19. Reports API требует реально уникальный `ReportName`
- Параллельные агенты/процессы не должны генерировать `ReportName` только по секунде времени.
- Для reusable collectors использовать `campaign_id + ms timestamp + random suffix`.
- Иначе параллельный сбор ловит `4000: same name but different parameters`.

20. `Ad failure audit` != `creative audit`
- Если задача про “объявления/группы не работают из-за ошибок”, нельзя подменять её diversity-аудитом или общим creative review.
- Канонический вопрос:
  - есть ли `ACCEPTED` adgroup в `ON` campaign без live ads из-за `REJECTED/MODERATION/DRAFT/OFF` ad-layer?
- `ARCHIVED` legacy ads, `DRAFT` old groups и вручную `SUSPENDED` variants нельзя автоматически считать текущей поломкой.
- В таком аудите отдельно классифицировать:
  - real delivery blockers;
  - component rejections;
  - pending drafts;
  - paused variants;
  - legacy deadwood.

18. `campaigns.get.Settings` != safe update payload
- В read-back `UnifiedCampaign.Settings` может приехать `SHARED_ACCOUNT_ENABLED`.
- При `campaigns.add/update` этот option надо вырезать, иначе будет `8000 unknown parameter/read-only`.

19. Tracking ownership нужно выбирать явно, но safe default = campaign + active groups
- Нельзя дублировать один и тот же `utm/roistat` одновременно в `Href`, на кампании и на группах.
- Теоретически owner может быть `campaign` ИЛИ `groups`, но в reusable live-ops safest pattern другой:
  - `UnifiedCampaign.TrackingParams` = полный template
  - все active `AdGroup.TrackingParams` = тот же полный template, если нет сознательного per-group override
- Пустой `TrackingParams=""` на группе не считать "нормальным наследованием" без явного client rule: это ломает автотесты, read-back и future apply.

20. `campaign_autotest.py` не должен hard-fail'ить кампанию только из-за пустого campaign-level tracking
- Сначала проверить group-level `TrackingParams`.
- `FAIL` только если tracking отсутствует или неполон и на кампании, и на группах; либо на группе задан частичный template, который перекрывает валидную кампанию.
- Но для live apply safe default всё равно = заполнить template и на кампании, и на active groups, чтобы не тащить ambiguity в следующие сессии.

21. `ads.update` по live ad нельзя считать "безопасным instant refresh" без read-back
- После изменения текста/Title у already running search ad возможен status-shift:
  - `State = ON`
  - `Status = MODERATION`
- Поэтому после каждого `ads.update` по live-layer обязателен immediate read-back:
  - `Id, State, Status, StatusClarification`
- Нельзя писать в apply-report "winner уже крутится", пока этот read-back не снят.

22. `adgroups.suspend` не использовать как основной cleanup primitive в ЕПК
- В unified-search live-слое `adgroups.suspend` может быть недоступен или вернуть `error 55 / operation not found`.
- Канонический cleanup-path:
  - `keywords.suspend` для мусорных фраз;
  - `ads.suspend` для слабого слоя;
  - `ads.archive` для legacy/deadwood, если слой больше не нужен.
- Cleanup verdict должен формулироваться на ad-layer, а не наивно на group-state.

23. `ads.moderate` для unified-search draft-кампаний может сам перевести кампанию из `OFF` в `ON`
- Если пользователь разрешил только модерацию, а не запуск, после `ads.moderate` надо сразу проверить `Campaign.Status/State`.
- Safe default: держать такие кампании в `SUSPENDED`, чтобы после одобрения они не стартовали автоматически без отдельного `go`.
- Reusable runner `send_to_moderation.py` должен по умолчанию применять этот safety-guard, а не надеяться, что состояние останется `OFF`.
- Для existing running campaigns safe default другой: модерировать только новые `ad_ids`, не переводить всю кампанию в `SUSPENDED` и не трогать текущую доставку. `send_to_moderation.py` должен сохранять `ON` у уже работающих кампаний и суспендить только те, что были `OFF` до moderation, если пользователь явно не попросил `--suspend-running-campaigns`.

24. Consumer-tail после copy refresh надо архивировать, а не только паузить
- Если старые ads уже признаны мусорным слоем, одного `SUSPENDED` мало: этот хвост продолжает шуметь в `campaign_autotest.py`, `ads.get` и ручных review.
- Канонический pattern:
  - сначала сохранить safe live-layer;
  - потом `ads.suspend`;
  - read-back;
  - затем `ads.archive`.
- Это особенно важно после смены JTBD/ЦА внутри уже работающей search-кампании.

25. Safe pattern для live search cleanup / audience pivot
- Если внутри running search-campaign меняется messaging и нужно быстро перевести её на другой intent:
  1. срежь generic keywords и placement leakage;
  2. оставь минимум один compliant control ad на каждое сохраняемое ядро;
  3. создай replacement ads с правильными `SitelinkSetId` и callouts;
  4. отправь на модерацию только новые `ad_ids`;
  5. архивируй consumer-tail только после read-back.
- Не делать "total cutover" без живого backup-layer, если пользователь отдельно не попросил жёсткий рискованный switch.
- Этот safety-pattern = временный аварийный контур, а не финальный build-state.
- Если пользователь просит `оптимизировать / дожать / добить`, search-group нельзя оставлять на `1-2 ads/group`.
- Финальная норма после cleanup для рабочего search-layer:
  - `5 ads/group`
  - все объявления проходят blacklist/moderation preflight и имеют полный extension-layer.
  - для `UNIFIED_AD_GROUP` не опираться на старое правило `3 desktop + 2 mobile`: в live API `TextAd.Mobile=YES` нормализуется обратно, поэтому safe default = просто `5` compliant text ads.

26. Hard blacklist для Direct copy и shared assets обязателен в reusable live-ops
- Safe default blacklist для русскоязычного Директа:
  - `VPN` / `ВПН`
  - `официальный сайт`
  - `без СМС` / `без смс`
- Этот blacklist проверяется не только по `Title/Title2/Text`, но и по всем переиспользуемым расширениям:
  - `SitelinkSet.Title/Description`
  - callouts / other shared extensions
- Если risky copy найден в shared `SitelinkSet`, нельзя считать задачу решённой после правки одного ad:
  1. создать новый safe `SitelinkSet`;
  2. bulk-update всех live `ad_ids`, которые смотрят на старый set;
  3. read-back'ом подтвердить `old_set_live_count = 0`;
  4. отдельным blacklist scan подтвердить, что findings остались только в `ARCHIVED`/legacy.
- Старый set может не удаляться, если на него ссылается архивный хвост. Это допустимо, если live-layer полностью перевязан.

## Session Modes

Используй один из четырёх режимов и не смешивай их молча:

1. `local-research`
- live/raw сбор без apply;
- цель = понять состояние, собрать baseline, зафиксировать findings.

2. `pre-apply-review`
- уже есть draft tasks / packs;
- цель = независимая проверка контента, coverage и apply-safety;
- live apply ещё запрещён.

3. `live-apply`
- только после явного разрешения пользователя;
- обязательны: preflight snapshot, dry-run, immediate read-back validation.
- если был `campaigns.add`, отдельно сохранить post-create `campaigns.get` snapshot с `UnifiedCampaign.PriorityGoals`, `CounterIds`, `Settings`, чтобы create payload не подменял фактический read-back.

4. `post-apply-monitoring`
- проверки `campaign_autotest`, live read-back, post-apply validation, YouGile-monitoring notes.

Если режим не назван пользователем, его нужно вывести из задачи и явно зафиксировать в doc.

## Parallel Validation Mesh

Если среда поддерживает параллельных агентов или параллельные tool-runs, перед любым live apply запускать не больше `3` независимых валидаторов:

1. `domain validator`
- проверяет содержимое конкретного пакета:
  - negatives → `validate_negatives_prompt.md`
  - RSYA placements → `validate_placements_prompt.md`
  - merged tasks → `validate_tasks_prompt.md`
  - clone/incubator → creative-precheck + safe subset

2. `coverage validator`
- проверяет, что optimisation loops не выпали:
  - SQR / RSYA / ads / bids / budgets / device-demo / structure / assets;
- если блок не вошёл, он должен быть явно помечен `out-of-scope` или `monitor-only`.

3. `apply-safety validator`
- проверяет:
  - есть ли fresh live-snapshot;
  - есть ли dry-run;
  - нет ли conflicting docs;
  - готов ли review-index;
  - подготовлен ли post-apply validation path.
- Для `ExcludedSites after-pack` использовать скриптовую проверку:
  - `python3 <ops-skill-root>/scripts/validate_excluded_sites_pack.py --help`
- Для `ad replacement pack` использовать скриптовую проверку:
  - `python3 <ops-skill-root>/scripts/validate_ad_replacement_pack.py --help`
- Для агентного workflow по stop-sites не перескакивать через слой:
  - `collector.direct.goal_placements`
  - `analysis.rsya.placement_rotation`
  - `validation.pack.rsya`
  - и только потом approval/apply.
- Если `validation.pack.rsya` технически `ready`, но не содержит реальных `add/remove`, prepare-слой apply обязан закончиться `blocked`.
  Нельзя плодить `awaiting_approval` для no-op пакета.

Если среда не поддерживает параллельных агентов, пройти те же 3 валидатора последовательно.

## Основные workflow

### 1. Новый клиент / новый проект

1. Создать локальный client overlay.
2. Заполнить routing map, cluster map, счётчики, цели, board columns, product notes.
3. Проверить доступы:
```bash
bash <ops-skill-root>/scripts/wordstat_preflight.sh
python3 <ops-skill-root>/scripts/oauth_get_token.py --help
```
4. Если есть Roistat, задать env и проверить query script.
5. Если нужен Metrika-layer, прочитать:
- [CONFIG.md](references/metrika/CONFIG.md)

### 2. Сбор новой семантики

Перед началом открыть:
- [wordstat_collection_framework.md](references/wordstat_collection_framework.md)
- [12_wordstat_collection_pipeline.md](references/task_playbooks/12_wordstat_collection_pipeline.md)

1. Собрать локальную product map по шаблону:
- [wordstat_product_map_template.md](templates/wordstat_product_map_template.md)

2. Сформировать `Wave 1` masks file по шаблону:
- [wordstat_masks_wave1_template.tsv](templates/wordstat_masks_wave1_template.tsv)

3. Провести обязательный `mask review`:
- web/source synonyms review;
- Wordstat associations review на широких масках;
- только после этого freeze `01-masks-wave1.tsv`.

4. Выполнить full-depth парсинг reusable collector-ом:
```bash
bash <ops-skill-root>/scripts/wordstat_tool.sh collect-wave-save \
  --masks-file semantics/<product>/01-masks-wave1.tsv \
  --output-dir semantics/<product>/raw/wordstat_wave1 \
  --num-phrases 2000 --dynamics true --regions-report true --regions-tree true \
  --min-mask-words 1 --max-mask-words 1 \
  --enforce-mask-word-range true --full-depth true
```

5. Пройти completeness gate:
- проверить, что каждая маска дала raw-файл;
- проверить, что нет пустых/ошибочных raw;
- вынести новые маски из associations в backlog `Wave 2`.

6. Только после completeness gate переходить к анализу:
- вручную/агентами, без analysis-скриптов;
- отделять target, doubtful, competitor, negatives;
- собирать минус-слова только после чтения raw.

7. После `Wave 1` gap-analysis собрать `Wave 2` из двухсловных масок и повторить цикл.

8. Лишь после вручную валидированного keyword set собирать exhaustive competitor jobs `keyword x geo`.

9. Если есть active Direct account, дополнительно собрать SQR/criteria/current structure:
```bash
bash <ops-skill-root>/scripts/fetch_sqr.sh \
  --token "$TOKEN" --login "$LOGIN" --campaigns "CID1,CID2" --days 30 \
  --output-dir semantics/<product>/raw/direct_wave1
```

10. Анализ делать только вручную мной; шаблоны ниже использовать как чеклисты и рамку, а не как analysis-скрипты:
- [agent_target_from_wave.md](templates/agent_target_from_wave.md)
- [agent_negative_from_wave.md](templates/agent_negative_from_wave.md)
- [agent_minus_words_from_negative.md](templates/agent_minus_words_from_negative.md)
- [agent_validation_checklist.md](templates/agent_validation_checklist.md)

### 3. Финализация и кластеризация

1. Подготовить локальный routing map / cluster map.
2. Собрать final pack:
```bash
python3 <ops-skill-root>/scripts/build_manual_final_pack.py --help
python3 <ops-skill-root>/scripts/validate_and_cluster.py --help
```
3. Проверить live-state:
```bash
python3 <ops-skill-root>/scripts/verify_live_readiness.py --help
python3 <ops-skill-root>/scripts/audit_group_ad_copy.py --help
python3 <ops-skill-root>/scripts/campaign_autotest.py --help
```

### 4. Аудит и оптимизация действующих РК

0. Trust preflight:
- проверить, можно ли доверять локальным raw-файлам;
- если они устарели или пользователь это подтвердил, начать с fresh live-snapshot;
- старые `data/` использовать только как исторический reference layer.
 - если пользователь прямо сказал, что conversions/leads считаются некорректно, до plan/scope обязателен явный reset optimisation truth:
   - какая метрика теперь primary;
   - какие метрики остаются supporting;
   - что точно нельзя использовать как главный verdict.
0.5. Scope precheck:
- сначала перечислить все активные кампании целевого канала;
- если пользователь назвал приоритетные РК, отметить их как queue A, но не выбрасывать остальные без явного `только`;
- если есть риск неверно сузить scope, сначала короткое уточнение, потом plan.
0.6. Mode precheck:
- если пользователь явно просит только обзор/аудит/план, режим = `review-only`;
- если пользователь просит оптимизировать/исправить/внедрить/применить, режим = `execute`;
- в `execute`-режиме после pre-apply summary default path = apply + self-check/read-back.
1. Полный raw dump кампании:
```bash
python3 <ops-skill-root>/scripts/collect_all.py --help
```
2. Если нужен short-window operational review по окну `N` дней:
```bash
python3 <ops-skill-root>/scripts/collect_operational_precheck.py --help
bash <ops-skill-root>/scripts/fetch_sqr.sh --help
```
   Правила:
   - placements для РСЯ собирать через `CUSTOM_REPORT` с полем `Placement` и `AdNetworkType=AD_NETWORK`;
   - для verdict по stop-sites placements обязаны включать goal-метрики: `Goals=[goal_id]`, `AttributionModels=["LC"]`, поля `Conversions`, `CostPerConversion`, `ConversionRate`;
   - `PLACEMENT_PERFORMANCE_REPORT` не считать universal source для этого шага;
   - `ExcludedSites` в `Campaigns.get` может быть `null`, все сборщики и валидаторы обязаны быть null-safe;
   - high-confidence мусор в РСЯ = не только `app/VPN`, но и явный `site-trash inventory` (mobile news / video / feed / off-topic garbage-site);
   - лиды/продажи на уровне кампании/группы/объявления/ключа брать только из Roistat.
   - при запросе "главная поисковая РК просела" сначала:
     1. определить primary CID из overlay;
     2. прогнать live `campaign_autotest.py`;
     3. сравнить `yesterday vs prev day vs 14d` по Roistat;
     4. сделать `day/day` split по adgroups;
     5. проверить фактические apply-артефакты/чейнджлог именно по этому CID;
     6. только потом делать вывод "просадку вызвали изменения".
3. Анализ по промтам:
- [full_audit_plan_prompt.md](templates/full_audit_plan_prompt.md)
- [search_query_prompt.md](templates/search_query_prompt.md)
- [ad_components_prompt.md](templates/ad_components_prompt.md)
- [bids_prompt.md](templates/bids_prompt.md)
- [structure_prompt.md](templates/structure_prompt.md)
- [validate_negatives_prompt.md](templates/validate_negatives_prompt.md)
- [aggregation_prompt.md](templates/aggregation_prompt.md)
- [search_diagnostic_prompt.md](templates/search_diagnostic_prompt.md)
- [rsy_placements_prompt.md](templates/rsy_placements_prompt.md)
- [validate_placements_prompt.md](templates/validate_placements_prompt.md)
- [validate_tasks_prompt.md](templates/validate_tasks_prompt.md)
- [tasks_format.md](templates/tasks_format.md)
- [diagnostic_agent_bundle_template.md](templates/diagnostic_agent_bundle_template.md)
   Все выводы по raw-данным делаются вручную; шаблон нужен как строгая структура результата.
   Для account-wide optimisation существующего search-кабинета до первого пользовательского summary по умолчанию открыть минимум эти playbook-и:
   - `01_search_negatives_7d.md`
   - `03_creative_outliers_rotation.md`
   - `06_bids_and_modifiers_review.md`
   - `09_missing_phrases_growth.md`
4. Сбор `tasks.tsv`.
5. Пройти `Parallel Validation Mesh`:
- domain validator;
- coverage validator;
- apply-safety validator.
  Если в review-pack есть `ExcludedSites after` или `ad replacement pack`, дополнительно прогнать:
```bash
python3 <ops-skill-root>/scripts/validate_excluded_sites_pack.py --help
python3 <ops-skill-root>/scripts/validate_ad_replacement_pack.py --help
```
6. Dry-run:
```bash
python3 <ops-skill-root>/scripts/apply_no_moderation_pack.py --help
python3 <ops-skill-root>/scripts/apply_tasks.py --help
python3 <ops-skill-root>/scripts/clone_search_groups_to_new_campaign.py --help
```
7. Пост-валидация:
- [post_apply_validation_prompt.md](templates/post_apply_validation_prompt.md)
8. Обновить YouGile по итогам цикла, даже если это был только precheck/master-plan.

### 5. Metrika workflow

Использовать когда Roistat нет или нужен независимый слой проверки.

Preflight:
```bash
export YANDEX_METRIKA_TOKEN=...
bash <ops-skill-root>/scripts/metrika/counters.sh
bash <ops-skill-root>/scripts/metrika/goals.sh --counter <ID>
```

Справка:
- [API_REFERENCE.md](references/metrika/API_REFERENCE.md)
- [CUSTOM_REPORTS.md](references/metrika/CUSTOM_REPORTS.md)
- [PERIOD_COMPARISON.md](references/metrika/PERIOD_COMPARISON.md)
- [SEARCH_QUERIES.md](references/metrika/SEARCH_QUERIES.md)

### 6. Media-plan and plan-fact

1. Собрать Direct daily stats + Roistat/Metrika conversions.
2. Построить прогноз:
```bash
python3 <ops-skill-root>/scripts/forecast_engine.py --help
python3 <ops-skill-root>/scripts/test_forecast.py --help
```
3. При необходимости использовать шаблон:
- [media_plan_prompt.md](templates/media_plan_prompt.md)

### 7. Competitor creative research

Использовать для сбора рекламных сообщений и креативных паттернов конкурентов:
- [competitor_research_workflow.md](references/competitor_research_workflow.md)
- [competitor_research_prompt.md](templates/competitor_research_prompt.md)

### 8. Post-cycle revision

После завершения волны работ обязательно пройти:
- [agent_skill_revision_checklist.md](templates/agent_skill_revision_checklist.md)
- [lessons_registry.md](references/lessons_registry.md)

Если найден reusable-урок:
- фиксировать в локальном проекте;
- затем поднимать в global-skill.

## Скрипты

### Универсальные и promoted

- `scripts/collect_all.py`
- `scripts/collect_operational_precheck.py`
- `scripts/fetch_sqr.sh`
- `scripts/apply_tasks.py`
- `scripts/apply_no_moderation_pack.py`
- `scripts/apply_ad_replacement_pack.py`
- `scripts/clone_search_groups_to_new_campaign.py`
- `scripts/change_tracker.py`
- `scripts/roistat_query.sh`
- `scripts/campaign_autotest.py`
- `scripts/audit_campaign_meta.py`
- `scripts/oauth_get_token.py`
- `scripts/wordstat_preflight.sh`
- `scripts/wordstat_collect_wave.js`
- `scripts/wordstat_tool.sh`
- `scripts/render_wordstat_wave.py`
- `<client-lifecycle-root>/scripts/build_followup_jobs_from_serp.py`
- `scripts/build_minus_words.py`
- `scripts/filter_search_queue_by_known_minus_words.py`
- `scripts/validate_and_cluster.py`
- `scripts/build_manual_final_pack.py`
- `scripts/deploy_search_campaigns.py`
- `scripts/update_callouts_set.py`
- `scripts/send_to_moderation.py`
- `scripts/fix_autotargeting_exact_only.py`
- `scripts/retire_ads.py`
- `scripts/apply_shared_negative_set.py`
- `scripts/apply_time_targeting_schedule.py`
- `scripts/audit_group_ad_copy.py`
- `scripts/verify_live_readiness.py`
- `scripts/validate_excluded_sites_pack.py`
- `scripts/validate_ad_replacement_pack.py`
- `scripts/sync_yougile.py`
- `scripts/bootstrap_yougile_workspace.py`
- `scripts/init_client_context.py`
- `scripts/client_context.py`
- `scripts/forecast_engine.py`
- `scripts/test_forecast.py`
- `scripts/metrika/*.sh`

### Не promoted в global live-flow

Оставлены только как source input для будущей доработки, не как обязательные universal scripts:
- `analyze_wave.py`
- `audit_per_mask.py`
- `build_gap_wave2.py`
- `apply_manual_final_live.py`
- локальные product-specific catalogs
- локальные Roistat deep analyzers

Причины и backlog:
- [source_inventory.md](references/source_inventory.md)

## Templates

### Семантика

- `wordstat_product_map_template.md`
- `wordstat_masks_wave1_template.tsv`
- `wordstat_mask_review_template.md`
- `wordstat_doubtful_validation_template.tsv`
- `agent_target_from_wave.md`
- `agent_negative_from_wave.md`
- `agent_minus_words_from_negative.md`
- `agent_validation_checklist.md`
- `agent_group_copy_alignment.md`

### Диагностика и оптимизация

- `full_audit_plan_prompt.md`
- `search_query_prompt.md`
- `ad_components_prompt.md`
- `bids_prompt.md`
- `structure_prompt.md`
- `validate_negatives_prompt.md`
- `post_apply_validation_prompt.md`
- `weekly_review_prompt.md`
- `aggregation_prompt.md`
- `search_diagnostic_prompt.md`
- `rsy_placements_prompt.md`
- `validate_placements_prompt.md`
- `validate_tasks_prompt.md`
- `tasks_format.md`
- `diagnostic_agent_bundle_template.md`

### Planning and research

- `media_plan_prompt.md`
- `competitor_research_prompt.md`
- `client_adaptation_checklist.md`

## Task Playbooks

Если пользователь формулирует задачу как конкретный operational block, сначала открывай соответствующий playbook:

- [00_output_contract.md](references/task_playbooks/00_output_contract.md)
- [01_search_negatives_7d.md](references/task_playbooks/01_search_negatives_7d.md)
- [02_rsy_stop_sites_7d.md](references/task_playbooks/02_rsy_stop_sites_7d.md)
- [03_creative_outliers_rotation.md](references/task_playbooks/03_creative_outliers_rotation.md)
- [04_deep_campaign_review_7d.md](references/task_playbooks/04_deep_campaign_review_7d.md)
- [05_change_impact_timeline.md](references/task_playbooks/05_change_impact_timeline.md)
- [06_bids_and_modifiers_review.md](references/task_playbooks/06_bids_and_modifiers_review.md)
- [07_yougile_hygiene_sync.md](references/task_playbooks/07_yougile_hygiene_sync.md)
- [08_competitor_search_serp.md](references/task_playbooks/08_competitor_search_serp.md)
- [09_missing_phrases_growth.md](references/task_playbooks/09_missing_phrases_growth.md)
- [10_extra_control_layers.md](references/task_playbooks/10_extra_control_layers.md)
- [11_pre_apply_presentation.md](references/task_playbooks/11_pre_apply_presentation.md)
- [12_wordstat_collection_pipeline.md](references/task_playbooks/12_wordstat_collection_pipeline.md)

Логика использования:
- сначала брать `00_output_contract.md`, чтобы результат сразу ложился в типовой bundle;
- потом открывать только нужный task playbook, а не весь архив;
- если задача идёт к live apply, обязательно добавлять `11_pre_apply_presentation.md`;
- если задача про competitor SERP, сначала читать `08_competitor_search_serp.md`, а client-specific ключи и auth-path поднимать из project transfer bundle / overlay, не из global skill.
- если в проекте уже есть local generator/discovery scripts, использовать их как fallback или client-specific overlay; для Wordstat preflight/collector по умолчанию сначала использовать `<ops-skill-root>/scripts/wordstat_tool.sh`.
- при Wordstat-разборе по умолчанию сначала сохранять:
  - collector stdout/stderr;
  - raw bundle;
  - render outputs;
  - и только потом открывать файлы для чтения.

## Lessons and gotchas

Перед сложной работой сверять:
- [lessons_registry.md](references/lessons_registry.md)

## Быстрый preflight

```bash
test -f <ops-skill-root>/SKILL.md
python3 <ops-skill-root>/scripts/oauth_get_token.py --help
bash <ops-skill-root>/scripts/wordstat_preflight.sh
python3 <ops-skill-root>/scripts/campaign_autotest.py --help
```

## Safety Guardrails For Live Ops

These rules are part of the portable operator contract and apply before analysis, planning, or live collection:

- Always reread the relevant skill and canonical references before a Direct, Wordstat, Metrika, Roistat, or YouGile workflow.
- Prefer reusable scripts for collection/parsing; manual work is for interpretation, QA, verdicts, and safe marketing decisions.
- Do not stop, pause, suspend, archive, or otherwise cut live traffic without explicit owner approval for that traffic-reducing action.
- Do not present internal IDs, board IDs, client IDs, raw tokens, private paths, or local machine paths in owner-facing summaries unless the user explicitly asks for them.
- Search-negative workflows require fresh SQR, manual row verdicts, reduction to words/safe masks, product-scope conflict checks, preflight, approval, and Direct readback.
- Marker or prefilter output is diagnostic only; it is never live-ready without the manual verdict and readback workflow.
- If a task has any live mutation risk, dry-run/readback proof and explicit approval gates are mandatory.

For bundled docs and commands, keep using `<plugin-root>/...` and `<ops-skill-root>/...`; do not hardcode personal home paths in public plugin files.
