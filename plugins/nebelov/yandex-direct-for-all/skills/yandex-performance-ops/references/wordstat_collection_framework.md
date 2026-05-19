# Wordstat Collection Framework

Канонический reusable reference для нового сбора семантики в Яндекс.Директ.

Этот документ сам является глобальным каноном `Wordstat`-слоя для будущих сессий Codex.
Локальные project docs могут только дополнять его client-specific терминологией и каталогом.

Path contract:
- `<plugin-root>` = корень этого bundle, где лежат `.codex-plugin/plugin.json`, `skills/`, `mcp/`, `scripts/`.
- Repo-local пример: `./plugins/yandex-direct-for-all`
- Home-compatible install пример: `~/.codex/plugins/yandex-direct-for-all` или `~/.claude/plugins/yandex-direct-for-all`

## Канон

`СТРУКТУРА -> МАСКИ -> РЕВЬЮ МАСОК -> ПАРСИНГ СКРИПТОМ -> [полный успех] -> АНАЛИЗ -> ЧИСТКА -> ГРУППИРОВКА`

Критические следствия:
- парсинг и анализ всегда разнесены;
- Wordstat нельзя дёргать one-off запросами по ходу семантической работы;
- до анализа должен существовать полный raw bundle по wave;
- default path = file-first:
  - сначала `preflight-save` / `collect-wave-save`;
  - потом открывать только сохранённые `_summary.json`, `_manifest.json`, `.tsv`, `.md`;
  - не тянуть длинные raw JSON и полные stdout/stderr в контекст без причины;
- competitor collection для exhaustive coverage начинается только после вручную валидированного keyword set.
- канонический launcher для Wordstat = `<plugin-root>/skills/yandex-performance-ops/scripts/wordstat_tool.sh`
- discovery order всегда такой:
  - global wrapper;
  - global `wordstat_preflight.sh` / `wordstat_collect_wave.js`;
  - только потом project-local fallback.

## Фаза 0. Product Map

До первого Wordstat-запуска обязателен `product map`.

Для каждого продукта/кластера фиксировать:
- официальное название;
- разговорные названия;
- тендерные/закупочные формулировки;
- жаргон;
- аббревиатуры;
- ошибки написания;
- латиница/кириллица;
- применения по отраслям.

Источники:
- сайт клиента;
- клиентская переписка;
- каталоги и посадочные;
- конкуренты;
- отраслевые словари, ГОСТ, Wikipedia;
- тендерные площадки;
- маркетплейсы;
- при наличии Метрика/search queries.

## Фаза 1. Masks

Маска = базовая поисковая единица, из которой нельзя убрать слово без потери смысла.

### Источники для масок

Приоритет источников:
- Wordstat `associations`;
- поисковые подсказки;
- конкуренты и их каталоги;
- сайт клиента и product map;
- Метрика/search queries, если есть;
- Wikipedia, ГОСТ, отраслевые справочники;
- форумы, отзывы, тендеры, маркетплейсы.

### Уровни масок

1. `L1 root`
- широкие корневые маски;
- где возможно однословные;
- задача: увидеть весь ландшафт и неожиданные ветки.

2. `L2 product`
- продуктовые маски;
- для второго круга по умолчанию `2 слова`;
- формула: `продукт x тип/материал/характеристика/применение`.

3. `L3 typo/special`
- ошибки написания;
- спецмаски, если они реально встречаются в спросе.

4. `L4 competitor`
- бренды конкурентов;
- добавлять отдельной волной или отдельным контуром, не смешивать молча с базовым product-wave.

### Что обязательно для Wave 1

`Wave 1` обязан включать однословные `L1` root-маски.

`Wave 2` строится уже из двухсловных product/object masks.

`Wave 2` обязателен после gap-analysis по итогам `Wave 1`.

### Сколько масок обычно нужно

- `1 товар/услуга`: обычно `10-20`
- `категория`: обычно `30-50`
- `большой каталог`: `100+`

Это ориентир для полноты, а не лимит.

## Фаза 1.5. Mask Review

Перед парсингом обязателен review списка масок.

Минимум два review-потока:
- `web/source synonyms review`
  Искать пропущенные синонимы, жаргон, ошибки написания, отраслевые формулировки.
- `Wordstat associations review`
  Проверять широкие маски и вытаскивать новые корневые направления из `associations`.

После review:
- дополнить маски;
- заморозить `01-masks-wave1.tsv`;
- только потом запускать collector.

Артефакты review:
- `review_web_synonyms.md`
- `review_wordstat_assoc.md`
- обновленный `01-masks-wave1.tsv`

## Фаза 2. Wordstat Parsing

### Только reusable collector

Разовый ручной вызов `wordstat_*` для основного сбора запрещён.

Допустимый путь:
- `masks-file`
- reusable wave collector
- raw output per mask

Канонический скрипт:
- `scripts/wordstat_collect_wave.js`

Канонический preflight:
- `scripts/wordstat_preflight.sh`

Канонический launcher:
- `scripts/wordstat_tool.sh`

Примеры:
```bash
bash <plugin-root>/skills/yandex-performance-ops/scripts/wordstat_tool.sh where
bash <plugin-root>/skills/yandex-performance-ops/scripts/wordstat_tool.sh preflight-save semantics/<product>/preflight
bash <plugin-root>/skills/yandex-performance-ops/scripts/wordstat_tool.sh collect-wave-save \
  --masks-file semantics/<product>/01-masks-wave1.tsv \
  --output-dir semantics/<product>/raw/wordstat_wave1 \
  --num-phrases 2000 --dynamics true --regions-report true --regions-tree true \
  --min-mask-words 1 --max-mask-words 1 \
  --enforce-mask-word-range true --full-depth true
```

### File-first режим обязателен

Для агентской работы default path теперь такой:
- collector сначала сохраняет raw и свои stdout/stderr в файлы;
- затем рендеры тоже сохраняются в `.tsv/.json`;
- только после этого агент открывает уже сохранённые файлы частями;
- сырые Wordstat rows и длинные JSON не тащить в контекст без необходимости.

### Параметры и raw

Обязательное правило:
- `numPhrases=2000`
- это и есть потолок `40 страниц` на маску;
- анализировать только верхушку массива запрещено;
- после сбора нужно лично просмотреть каждую строку из `topRequests` и `associations`.

Что собирать:
- `topRequests`
- `associations`
- `totalCount`

Что сохранять:
- отдельный raw-файл на каждую маску;
- логи wave;
- при необходимости dynamics/regions отдельными скриптовыми волнами, не вручную.
- географию и дерево регионов собирать тем же collector-ом:
  - `--regions-report true`
  - `--regions-tree true`
- для клиентского отчета потом рендерить тремя отдельными слоями:
  - спрос;
  - сезонность;
  - география.

### Организация парсинга

Reusable collector обязан:
- читать `masks-file`;
- вызывать Wordstat API по каждой маске;
- сохранять отдельный raw-файл на маску;
- при необходимости собирать отдельные `regions_<mask>.json`;
- при необходимости собирать `_regions_tree.json`;
- логировать прогресс и ошибки;
- продолжать wave при ошибке отдельной маски;
- сохранять audit trail по дублям и invalid masks.

## Клиентский слой спроса

После полного raw collection и ручной валидации нужно отдельно рендерить клиентский слой спроса.

Обязательный порядок:
- широкие корневые маски показывать отдельно как обзорный ландшафт;
- точные базовые маски показывать отдельно как рабочий слой;
- использовать только `totalCount` по каждой базовой маске;
- не суммировать вложенные запросы внутри маски;
- не складывать разные маски между собой как единый объем рынка.
- seasonality и geography выводить отдельными renderer-слоями, а не текстом "по памяти".

## Completeness Gate

До анализа обязательно проверить:
- число raw-файлов совпадает с числом масок;
- пустые и ошибочные raw-файлы вынесены в retry-list;
- новые маски из `associations` вынесены в backlog;
- все SKU/кластеры из product map покрыты хотя бы одной маской.

Пока gate не пройден, analysis-фаза не начинается.

## Фаза 3. Анализ

Анализ по raw-файлам делать только вручную агентами/оператором.

Запрещено:
- analysis-скрипты для автоматической классификации;
- смешивание анализа и новых Wordstat API вызовов в одном шаге.

Минимальные классы:
- `target_commercial`
- `target_product`
- `competitor`
- `info`
- `job`
- `wrong_product`
- `wrong_type`
- `geo`
- `doubtful`

Каждый отсеянный запрос должен оставаться в trace как минус-фраза/negative candidate, а не “исчезать”.

### Канонические выходы анализа

- `target_phrases_wave*.tsv`
- `negative_phrases_wave*.tsv`
- `doubtful_phrases_wave*.tsv`
- `competitor_phrases_wave*.tsv`
- `minus_candidates_wave*.tsv`

### Правила анализа

- не создавать analysis-скрипты для классификации;
- не делать новых API-вызовов в анализе;
- неоднозначное переносить в `doubtful`, а не насильно классифицировать;
- каждый минус-кандидат должен иметь причину и ссылку на raw evidence.
- row-by-row review обязателен:
  - каждая строка должна пройти через один из статусов `target_commercial`, `target_product`, `competitor`, `info`, `job`, `wrong_product`, `wrong_type`, `geo`, `doubtful`;
  - стоп-слова и минус-кандидаты появляются только после такого просмотра, а не из догадок по верхним строкам.

## Фаза 3.5. Doubtful Validation

Сомнительные запросы валидировать отдельным шагом после основной классификации.

Правила:
- сначала дождаться завершения всех классификаторов;
- сделать backup campaign files;
- собрать `doubtful.tsv`;
- валидировать батчами;
- затем отдельным шагом применить verdict в `keywords.tsv` и `minus.tsv`.

Артефакт валидации:
- `validated_doubtful.tsv`

## Фаза 4. Minus Logic

Три уровня минус-логики:
- account;
- campaign;
- adgroup.

Кросс-минусовка между поисковыми кампаниями обязательна при широком соответствии.

Каждый отсеянный запрос сохранять как полную минус-фразу.

### Правила минус-логики

- account negatives:
  - инфо;
  - работа;
  - DIY;
  - б/у, аренда, прокат.
- campaign negatives:
  - кросс-минусовка соседних продуктовых РК;
  - категорийные нерелевантные подтипы.
- adgroup negatives:
  - тонкая развязка близких вариантов внутри кампании.

Ловушки:
- не минусовать глобально то, что реально продается клиентом;
- города не минусовать при `Вся РФ`;
- материалы и модификаторы проверять осторожно;
- конкурентов либо выделять отдельно, либо минусовать осознанно;
- писать полные слова и полные фразы, не обрубки.

## Фаза 5. Grouping And Export

Финальный путь:
- `raw`
- `classified`
- `campaigns`
- `negatives`
- `FINAL_REPORT.md`

Группировка и export идут только после:
- полного raw collection;
- анализа;
- doubtful validation;
- минус-логики.

## Фаза 6. QA

Обязательные проверки:
- все SKU клиента покрыты;
- синонимы учтены;
- кросс-минусовка есть;
- нет конфликтов `key <-> minus`;
- нет дублей между группами;
- competitor traffic либо выделен отдельно, либо заминусован осознанно;
- формат готов к загрузке в Direct.

## Типовые ошибки

Нельзя:
- стартовать с узких масок и пропускать root-layer;
- опираться только на Wordstat без product map и review;
- использовать `numPhrases` меньше `2000` для full-depth wave;
- парсить вручную по одной маске;
- смешивать парсинг и анализ;
- считать pre-semantics competitor scout полным competitor set.

## Справка по операторам

- без оператора: все словоформы и хвосты;
- `""`: только эти слова;
- `!`: фиксирует форму слова;
- `+`: учитывает стоп-слово;
- `[]`: фиксирует порядок;
- `-`: исключает слово;
- `()` и `|`: группировка и ИЛИ.

Операторы использовать осознанно для исследований точной частотности и проверки рисков по минус-словам, а не хаотично во время основного wave-collection.

## Build-Prep Classification Gate

Before a Wordstat wave becomes build-prep, every product or offer in the product map must have one of these statuses:

- `core`: direct commercial route, eligible for build-prep by default.
- `support`: adjacent/support route, eligible only when landing and copy match the intent.
- `proof-only`: evidence/research layer; not first-wave build-prep without a separate decision.
- `speculative`: weak signal or unsupported route; keep in backlog until proof exists.

Completeness checks must confirm that broad category roots, support roots, and adjacency roots are either covered by masks or explicitly discarded with a reason. Do not let proof-only or speculative offers leak into standalone commercial masks by default.
