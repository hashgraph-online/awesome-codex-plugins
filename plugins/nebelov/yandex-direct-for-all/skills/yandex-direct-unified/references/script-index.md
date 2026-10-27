# Переносимые сценарии

Пути считаются относительно корня подключаемого модуля.

## Wordstat v2

- mcp/yandex-wordstat/src/index.mjs — сервер Wordstat v2.
- mcp/yandex-wordstat/src/convert.mjs — преобразования Wordstat и общий межпроцессный учёт скорости и почасовой стоимости.
- mcp/yandex-wordstat/scripts/wordstat_cloud_gateway_collect.py — файловый сбор исходных ответов с продолжением.
- skills/yandex-performance-ops/scripts/normalize_wordstat_regions.py — нормализация регионов.
- skills/yandex-performance-ops/scripts/render_wordstat_geo.py — представление географии.
- skills/yandex-performance-ops/scripts/render_wordstat_mask_demand.py — представление спроса по маскам.
- skills/yandex-performance-ops/scripts/render_wordstat_seasonality.py — представление динамики.
- skills/yandex-performance-ops/scripts/render_wordstat_wave.py — сводка волны без смыслового решения.

## Установка и проверка

- scripts/install_bundle.sh — план, применение и откат управляемой установки.
- scripts/validate_bundle.sh — проверка состава модуля.
- scripts/validate_repository.sh — проверка всего хранилища.

## Доступ

- scripts/start_yandex_user_auth.sh — встроенный вход: `--service direct --client-login ЛОГИН` для Директа, `--service metrika` для Метрики (профили `legacy_direct` и `master_yandex`).
- scripts/exchange_yandex_user_code.sh — обмен кода подтверждения на токен в режиме ручного ввода кода.
- scripts/preflight_yandex_user_token.py — обязательная проверка после входа: токен выдан ожидаемому приложению, служба читается.
- scripts/render_yandex_token_env.py — закрытый файл переменных окружения из закрытого файла токена.
- skills/yandex-performance-ops/scripts/check_access_paths.py — проверка файла доступа: `--access-file ФАЙЛ`.
- skills/yandex-performance-ops/scripts/metrika_oauth_verification_code.py — совместимый запуск входа в Метрику.

## Выдача и Wordstat с выбором провайдера

- scripts/collect_organic_serp.sh — органическая выдача.
- scripts/collect_ad_serp.sh — рекламная выдача.
- scripts/collect_wordstat_wave.sh — волна Wordstat.
- scripts/provider_select.sh — общий выбор провайдера: `--provider yandex-cloud|xmlriver|auto`.
- skills/xmlriver-serp-research/scripts/xmlriver_collect.py — сборщик XMLRiver с журналом и лимитом расходов.

## Жизненный цикл клиента

Каталог `skills/yandex-direct-client-lifecycle/scripts/`:

- scaffold_client_lifecycle.py — слой файлов клиента;
- sitemap_probe_batch.py и firecrawl_scrape.py — сбор страниц сайта (ключ Firecrawl — в `FIRECRAWL_API_KEY`);
- yandex_search_batch.py и yandex_search_ads_batch.py — пакетный сбор выдачи;
- verify_research_bundle.py — проверка полноты исследовательского пакета.

## Снимок действующего кабинета

Каталог `skills/yandex-performance-ops/scripts/`:

- collect_direct_cabinet_snapshot.py — основной снимок: `--access-file --output-dir --campaign-ids --from --to --include-sqr`;
- collect_direct_management_snapshot.py — структура кабинета: `--access-file --output-dir --campaign-ids --name-regex`;
- fetch_sqr_parallel.py — поисковые запросы: `--access-file --campaigns|--campaigns-file --from --to --output-dir --workers`;
- collect_operational_precheck.py, audit_campaign_meta.py, audit_ad_delivery_failures.py — точечные проверки;
- collect_all.py и fetch_sqr.sh — запасной ручной режим.

Для разового чтения ключей не отправлять пустой `SelectionCriteria` в `AdGroups.get` и `Keywords.get`: нужны `CampaignIds` или `Ids`, номера делятся на пачки по 10, каждый ключ сверяется со своей группой и кампанией. Ошибка Директа 58 («Незавершённая регистрация») означает, что регистрация приложения для работы с API не завершена (нет одобренной заявки на доступ), а не что токен устарел: пересоздание токена её не исправит.

## Проверка и подготовка пакетов

Каталог `skills/yandex-performance-ops/scripts/`:

- validate_direct_copy_pack.py — проверка пакета текстов;
- validate_direct_build_dossier.py — проверка досье сборки перед записью;
- validate_and_cluster.py — только техническая кластеризация и нарезка;
- verify_live_readiness.py и campaign_autotest.py — проверка готовности кампаний;
- validate_excluded_sites_pack.py и validate_ad_replacement_pack.py — проверка пакетов площадок и замены объявлений;
- build_text_rotation_apply_pack_from_tsv.py — пакет ротации текстов из таблицы;
- change_tracker.py — журнал изменений.

Проверки проверяют схему, арифметику, пропуски, трассу «сырая строка → `candidate_id`» и покрытие частей разбора; смысловых вердиктов они не выносят и PASS своему же набору не ставят.

## Запись

- skills/yandex-performance-ops/scripts/direct_write_gate.py — единственные ворота записи: `--pack ФАЙЛ_ПАКЕТА --pack-sha256 ФАЙЛ_СУММЫ` (путь к отдельному файлу с контрольной суммой пакета, а не сама сумма), без `--apply` только проверка пакета.
- Скрипты `deploy_search_campaigns.py`, `apply_*`, `send_to_moderation.py`, `resume_ads.py`, `retire_ads.py`, `update_ads_sitelinks.py`, `update_callouts_set.py`, `fix_autotargeting_exact_only.py` в том же каталоге — совместимые входы в эти ворота.
- prefilter_rsya_manual_queue.py — предварительная разметка очереди площадок, ручное решение остаётся пустым.

Отдельного канонического скрипта создания кампаний РСЯ нет. РСЯ не пропускается молча: либо проверенный скрипт добавляется в этот указатель, либо в `channel-plan.tsv` ставится `blocked` с причиной `tooling`. Пакет РСЯ требует `rsya-ad-copy-pack.tsv`, `rsya-image-asset-map.tsv`, личного осмотра изображений, проверки дублей, точной проверки геометрии без обрезки и растягивания, плана и чтения кнопок, пробного прогона, идемпотентного продолжения и чтения после записи. Изображение формата `REGULAR` требует пропорций от 3:4 до 4:3; отклонённый запрос и ответ сохраняются, фото не удаляется молча, неудачная загрузка не повторяется без исправления формата.

Опция `ENABLE_AREA_OF_INTEREST_TARGETING` устарела и не поддерживается: успешный ответ на её установку ничего не доказывает, проверять нужно `RegionIds`.

## Roistat и Метрика

- skills/yandex-performance-ops/scripts/roistat_query.sh — запросы к Roistat (`--if-configured` — тихо пропустить, если Roistat не подключён).
- skills/yandex-performance-ops/scripts/metrika/*.sh — счётчики, цели, конверсии, источники, UTM.

## Правила исполнения

- Если для действия есть скрипт, разовые вызовы оболочки или API не придумываются.
- Токен передаётся только файлом (`--access-file`, `--token-file`); сырой токен в аргументах запрещён.
- Долгие сборщики печатают ход работы.
- Сценарии записи идемпотентны и падают до записи при неверном входе. Перед записью — `validate_direct_build_dossier.py`.
- Ни один генератор, фильтр, расширитель, автоклассификатор или построитель плана не выбирает, не отбрасывает, не классифицирует, не ранжирует ключи по целевости, не утверждает покрытие и не собирает итоговый пакет ключей. Это смысловые решения человека или проверяющего.

Сценарии записи не считаются разрешёнными только из-за наличия в каталоге. Их допускает единый договор записи и отдельное разрешение пользователя.
