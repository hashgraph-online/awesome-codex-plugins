# 12. Wordstat Collection Pipeline

Path contract:
- `<plugin-root>` = корень bundled plugin, например `./plugins/yandex-direct-for-all` или `~/.codex/plugins/yandex-direct-for-all`

Используй этот playbook, когда задача звучит как:
- собрать новую семантику;
- собрать ключи через Wordstat;
- сделать wave 1 / wave 2;
- подготовить валидированный keyword set для competitor collection.

## Выходные артефакты

- `semantics/<product>/00-product-map.md`
- `semantics/<product>/01-masks-wave1.tsv`
- `semantics/<product>/review_web_synonyms.md`
- `semantics/<product>/review_wordstat_assoc.md`
- `semantics/<product>/raw/wordstat_wave1/*`
- `semantics/<product>/wave1_completeness.md`
- `semantics/<product>/02-masks-wave2.tsv`

## Порядок

1. Собрать `product map`.
2. Сформировать `Wave 1` masks:
   - сначала `L1` root;
   - потом `L2` product.
3. Провести обязательный review масок:
   - web/source synonyms;
   - Wordstat associations.
4. Пройти Wordstat preflight:
```bash
bash <plugin-root>/skills/yandex-performance-ops/scripts/wordstat_preflight.sh
```
5. Запустить collector:
```bash
node <plugin-root>/skills/yandex-performance-ops/scripts/wordstat_collect_wave.js \
  --masks-file semantics/<product>/01-masks-wave1.tsv \
  --output-dir semantics/<product>/raw/wordstat_wave1 \
  --num-phrases 2000 --dynamics true \
  --min-mask-words 1 --max-mask-words 2 \
  --enforce-mask-word-range true --full-depth true
```
6. Пройти completeness gate:
   - все raw на месте;
   - нет пустых/ошибочных файлов;
   - новые маски вынесены в `Wave 2`.
7. Только после этого анализировать raw вручную.
8. Собрать `Wave 2` и повторить цикл.
9. Только после вручную валидированного keyword set строить exhaustive competitor jobs `keyword x geo`.

## Жёсткие запреты

- не делать one-off `wordstat_*` вызовы вместо collector-а;
- не смешивать парсинг и анализ;
- не запускать exhaustive competitor collection до валидации keyword set;
- не использовать analysis-скрипты для автоматической классификации ключей.

## Public-Safe Post-Review Gates

After raw Wordstat collection and mask review:

- Render exact demand, seasonality, and geography as separate script outputs.
- Keep broad landscape roots separate from exact working masks.
- Move only `core` and explicitly approved `support` routes into build-prep.
- Keep `proof-only` and `speculative` routes as evidence/backlog unless a separate decision promotes them.
- Do not hardcode personal install paths; use `<plugin-root>` and `<ops-skill-root>` in examples.
