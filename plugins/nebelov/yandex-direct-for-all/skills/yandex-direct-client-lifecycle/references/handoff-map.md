# Handoff Map

## Этот skill владеет

1. intake;
2. client KB;
3. source inventory;
4. competitor raw collection;
5. research planning;
6. proposal pack;
7. human-review flow;
8. build-ready handoff artifacts.

## `yandex-performance-ops` владеет

1. official Wordstat execution;
2. Direct/Metrika raw collectors (и Roistat, если подключён);
3. semantics operations and validation packs;
4. campaign build and pre-moderation validation;
5. live apply;
6. post-apply monitoring;
7. daily/weekly operating loop.

## `russian-b2b-service-contracts` владеет

1. рамочный договор;
2. ТЗ;
3. акт;
4. приемка/оплата/ЭДО-пакет.

## Transition Condition

Переключайся из `yandex-direct-client-lifecycle` в `yandex-performance-ops`, когда есть:

1. `client-kb.md`
2. `source-register.tsv`
3. `proposal-pack.md`
4. `product-map.md`
5. `routing-map.tsv`
6. `./.codex/yandex-performance-client.json`
7. human decision по first-wave scope

Если этого нет, значит build/live делать рано.
