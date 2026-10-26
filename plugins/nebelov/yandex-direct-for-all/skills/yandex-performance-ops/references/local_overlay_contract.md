# Local Overlay Contract

Global skill хранит логику. Локальный проект хранит контекст клиента.

Файл по умолчанию:
- `./.codex/yandex-performance-client.json`

## Что должно быть в overlay

### `client_key`
- короткий ключ клиента/проекта;
- используется в артефактах и лейблах.

### `analytics`
- `source_priority`: порядок доверия данным;
- `sales_source`: `none | crm | roistat` — подключённый источник продаж (по умолчанию `none`: продажи не проверяются, выводы об окупаемости не делаются);
- `roistat_first`: только если Roistat подключён — использовать ли его как первую инстанцию;
- `manual_analysis_required`: если `true`, анализ руками мной без analysis-скриптов;
- `roistat_attribution`: какие модели атрибуции проверять (`first_click`, `last_click`).

### `analysis`
- `keywords_manual_only`: ключевые слова и фразы анализировать только вручную;
- `analysis_scripts_forbidden`: запрет на analysis-скрипты;
- `roistat_keyword_analysis_manual_only`: отдельный guardrail для ключей/фраз из Roistat.

Этот блок нужен, чтобы future-agent не смешал парсинг и анализ даже при наличии raw TSV/JSON.

### `direct`
- `login`: Client-Login или логин клиента;
- `tracking_params`: единый UTM-шаблон;
- `regions`: список регионов;
- `counter_ids`: CounterIds для кампаний;
- `priority_goals`: массив целей с value;
- `campaign_defaults`: бюджет, placement types, time targeting, offer retargeting, default negatives.

### `metrika`
- `counter_id`
- `goal_id`

### `wordstat`
- `regions`
- `devices`

### `roistat` (необязательно, только при `enabled: true`)
- `enabled`
- `api_key_env`
- `project_env`
- `base_url`
- `marker_level_1`
- `marker_level_2_search`

Секреты Roistat хранить только в env.

### `yougile`
- `project_id`
- `legacy_board_id`: опционально, если старая доска ещё нужна как архив;
- `boards`: массив досок workspace.

Рекомендуемый формат одной доски:
- `alias`
- `title`
- `purpose`
- `board_id`
- `columns`: словарь `lane_alias -> column_uuid`

Для старых проектов допустим fallback:
- `board_id`
- `board_columns`

Но для агентного control-plane каноническая схема уже multi-board, а не single-board.

### `search_routing`
- `routing_map_path`
- `cluster_map_path`
- `campaign_id_map_path`
- `campaign_ids`: опциональный встроенный словарь alias → campaign id, если отдельного файла ещё нет.

### `collector_defaults`
- `operational_window_days`
- `goal_id`
- `rsya_campaign_ids`

Этот блок нужен для operator-panel и central collector-plane:
- чтобы panel могла подставлять дефолтное окно и default campaign sets;
- чтобы collector workflow не угадывал IDs и goal на лету;
- чтобы новые клиентские адаптации были repeatable.

### `references`
- `product_maps`: локальные карты продукта/каталоги;
- `local_skill_paths`: клиентские навыки, которые нельзя потерять и нельзя переписывать как global;
- `rules`: локальные аксиомы, red lines, protected words, роутинговые правила;
- `docs`: полезные локальные отчёты и документы.

## Файлы рядом с overlay

Обычно рядом с overlay или в проекте нужны:
- `product-map.md`
- `routing-map.tsv`
- `cluster-map.tsv`
- `campaign-id-map.json`
- `protected-words.txt`
- `negative_axioms.md`
- `ad-copy-notes.md`

## Чего не должно быть в overlay

- OAuth access tokens
- client secret
- Roistat API key
- Basic auth пароли
- anything that rotates frequently
- пути на локальные analysis-скрипты, которые автоматически решают что target/negative/minus
