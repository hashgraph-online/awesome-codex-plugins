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

Сценарии записи не считаются разрешёнными только из-за наличия в каталоге. Их допускает единый договор записи и отдельное разрешение пользователя.
