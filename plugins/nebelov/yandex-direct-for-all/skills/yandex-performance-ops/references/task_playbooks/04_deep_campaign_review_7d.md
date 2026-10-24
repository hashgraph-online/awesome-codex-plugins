# Task Playbook 04: Deep Campaign Review 7d

Когда использовать:
- полный review каждой активной РК;
- weekly operating review по аккаунту.

## Truth Layer

- live Direct state
- live Direct reports
- sales source (CRM or Roistat) as primary business truth when connected; otherwise Direct reports and Metrika goals
- Metrika только как вспомогательная аналитика

## Что читать

- `templates/weekly_review_prompt.md`
- `templates/search_query_prompt.md`
- `templates/ad_components_prompt.md`
- `templates/bids_prompt.md`
- `templates/structure_prompt.md`
- `references/task_playbooks/00_output_contract.md`

## Порядок

1. Сделать Stage 0 YouGile monitoring first.
2. Собрать полный raw bundle.
3. По каждой РК разобрать:
   - SQR
   - adgroups
   - criteria
   - queries
   - ads
   - image hashes
   - bids/modifiers
   - structure
   - placements
   - settings/meta
4. На старте показать proof of coverage:
   - все search-РК окна
   - все РСЯ РК окна
   - где есть полный raw, а где только monitor/read-only verdict
5. После campaign-level review сделать account-level summary.
6. Отдельно зафиксировать:
   - daily anomalies
   - `Reports vs sales source` discrepancies (если источник продаж подключён)
   - top-3 priorities
7. По каждой search-РК обязательно дать два слоя:
   - `что сдержать / починить`
   - `что усиливать / что добавлять для роста`

## Типовой output-bundle

- `00_scope.md`
- `01_raw_index.md`
- `02_findings.tsv`
- `03_campaign_<cid>_review.md`
- `03_account_weekly_summary.md`
- `03_daily_anomalies.md`
- `03_reports_vs_sales_source.md` (без подключённого источника продаж — одна строка «источник продаж не подключён»)
- `04_validation.md`
- `05_pre_apply_summary.md`

## Перед apply показать пользователю

- кампании с highest urgency;
- где top drains на уровне group / criteria / query / ad / image;
- какой план правок по каждой РК;
- какой прогноз по каждой proposed wave;
- какой growth-plan по каждой РК;
- что относится к `server-ready`;
- что только `monitor-only`;
- где вывод causal, а где только correlation.

Обязательный campaign-review minimum:

- полное имя кампании и ID
- top adgroups by spend
- top criteria by spend
- top clicked queries by spend
- ad-level losers / winners
- image-level outsiders / keepers
- business winners / near-winners по источнику продаж (если подключён)
- diagnosis
- plan of changes
- growth actions
- forecast
