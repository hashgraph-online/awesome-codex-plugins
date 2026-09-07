# Task Playbook 08: Competitor Search SERP

Когда использовать:
- сбор конкурентных объявлений в поиске;
- поиск angle / offer / CTA / proof pattern;
- подготовка hypotheses по отстройке.

## Truth Layer

- raw SERP captures
- query list from current targets and growth gaps
- client-specific search collection auth path

## Важное правило по auth

- Не зашивать секреты и токены в global skill.
- Если у проекта есть `YANDEX_TRANSFER_BUNDLE_*.md` или аналогичный handoff-файл, сначала прочитать его.
- Из transfer bundle брать только:
  - auth mode
  - credential location
  - search collection path
  - какие токены для чего допустимы
- Если в текущем проекте есть защищённый файл передачи доступа, используй только его подтверждённую схему и не переноси содержимое в публичный набор.

## Что читать

- `references/competitor_research_workflow.md`
- `templates/competitor_research_prompt.md`
- `references/task_playbooks/00_output_contract.md`

## Порядок

1. Собрать query list.
2. Поднять client-specific auth and routing из transfer bundle / overlay.
3. Для search-слоя по умолчанию собирать не sample из нескольких фраз, а full matrix:
   - все active accepted ON keywords
   - нормализованные query variants
   - отдельно по каждому региону
4. Если пользователь просит `МО`, `ЛО` и `РФ`, default matrix = `mo`, `lo`, `rf_all`.
5. Снять raw SERP captures по каждой фразе и региону.
6. Отдельно сохранить:
   - ad text
   - visible URL
   - landing URL
   - timestamp
   - screenshot / snippet
7. Только потом делать human analysis.
8. Вывести usable patterns и taboo list.

## Типовой output-bundle

- `00_scope.md`
- `01_raw_index.md`
- `02_findings.tsv`
- `03_query_list.tsv`
- `03_serp_captures.jsonl`
- `03_keyword_region_manifest.tsv`
- `03_theme_matrix.tsv`
- `04_validation.md`
- `05_pre_apply_summary.md`

## Перед apply показать пользователю

- какие competitor patterns замечены;
- какие домены лидируют по каждому региону;
- по каким query-clusters SERP наиболее плотный;
- что можно адаптировать;
- как именно отстроиться;
- какие идеи остаются hypothesis-only.
