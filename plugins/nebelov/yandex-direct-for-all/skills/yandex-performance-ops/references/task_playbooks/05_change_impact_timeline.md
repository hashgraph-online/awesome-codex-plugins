# Task Playbook 05: Change Impact Timeline

Когда использовать:
- разбор изменений за месяц;
- before/after review по мартовским или недельным изменениям.

## Truth Layer

- `change_tracker.py`
- daily Direct reports
- daily sales source (CRM or Roistat) if connected
- live apply docs / YouGile notes

## Что читать

- `references/task_playbooks/00_output_contract.md`

## Порядок

1. Собрать timeline изменений.
2. Для каждого изменения зафиксировать baseline и соседние competing changes.
3. Сравнить минимум `1d`, `3d`, `7d`.
4. Для каждого изменения держать три слоя:
   - `factual change`
   - `measured after-state`
   - `causality confidence`
5. Выдать только один из классов:
   - `probable_causal`
   - `correlation_only`
   - `insufficient_evidence`
6. Не придумывать causal verdict без observational support.

## Типовой output-bundle

- `00_scope.md`
- `01_raw_index.md`
- `02_findings.tsv`
- `03_change_matrix.tsv`
- `03_change_attribution.md`
- `04_validation.md`
- `05_pre_apply_summary.md`

## Перед apply показать пользователю

- какие прошлые изменения реально помогли;
- какие только совпали по времени;
- какие уроки надо перенести в следующие волны.

Минимальный pre/post bundle:

- точная дата изменения
- pre window
- post window
- delta по impressions / clicks / ctr / cost / avg cpc / direct conversions
- verbal verdict без фантазий
