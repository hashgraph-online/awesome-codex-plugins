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

## Установка

Claude Code 2.1.275 и новее — одной командой:

    /plugin install yandex-direct-for-all --marketplace nebelov/yandex-direct-for-all

Claude Code 2.1.78–2.1.274:

    /plugin marketplace add nebelov/yandex-direct-for-all
    /plugin install yandex-direct-for-all@yandex-direct-for-all

Codex:

    codex plugin marketplace add nebelov/yandex-direct-for-all

Ручная установка из клона (сначала план, затем `--apply`; цели codex, claude или both):

    bash scripts/install_bundle.sh --target both
    bash scripts/install_bundle.sh --target both --apply

Нужны `uv`, Node.js 20+, npm и rsync. Установщик проверяет их до записи и
подготавливает закреплённые зависимости серверов в промежуточной копии.

Платный `mcp/yandex-search` по умолчанию выключен и не выполняет сетевых вызовов без ручного или заранее разрешённого режима.

## Проверка выпуска (для разработчиков)

    bash scripts/release_gate.sh

Нужны дополнительно bun 1.3+, gitleaks и git.
