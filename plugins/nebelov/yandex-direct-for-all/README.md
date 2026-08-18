# Модуль Yandex Direct For All

Основной навык: skills/yandex-direct-unified/SKILL.md. Старые навыки yandex-performance-ops и yandex-direct-client-lifecycle сохранены как совместимые переходники.

## Состав

- skills/yandex-direct-unified — общий порядок;
- skills/yandex-wordstat — справочник Wordstat v2;
- mcp/yandex-direct — безопасное чтение Директа;
- mcp/yandex-wordstat — Wordstat v2;
- mcp/yandex-search — Yandex Search API;
- skills/yandex-cloud-search-cost-control — контроль расходов платного поиска;
- scripts/install_bundle.sh — план, применение и откат установки;
- config/yandex_oauth_public_profiles.json — два общих открытых приложения авторизации.

Любой пользователь может авторизовать свой аккаунт Директа и Метрики через общие приложения. Собственное приложение не требуется. Секретов приложений и пользовательских токенов в модуле нет.

## Проверка

    bash scripts/release_gate.sh

Платный `mcp/yandex-search` по умолчанию выключен и не выполняет сетевых вызовов без ручного или заранее разрешённого режима.

## Установка

    bash scripts/install_bundle.sh --target codex
    bash scripts/install_bundle.sh --target codex --apply

Для Клода замените codex на claude; для обеих сред используйте both.

Для применения нужны `uv`, Node.js и npm. Установщик проверяет их до записи и
подготавливает закреплённые зависимости серверов в промежуточной копии.
