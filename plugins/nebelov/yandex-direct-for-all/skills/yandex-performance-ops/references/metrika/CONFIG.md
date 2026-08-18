# Переносимая настройка Метрики

Навык не хранит пользовательские токены, номера счётчиков и целей. Все такие значения создаются после установки в закрытом файле конкретного пользователя.

## Авторизация без своего приложения

В наборе намеренно сохранён публичный идентификатор общего OAuth-приложения Метрики. Каждый установивший набор может разрешить доступ к своему аккаунту без создания своего приложения:

```bash
plugins/yandex-direct-for-all/scripts/start_yandex_user_auth.sh --service metrika
```

Запуск откроет страницу согласия Яндекса, сохранит токен и файл с `YANDEX_METRIKA_TOKEN` с правами `0600`, а затем лично проверит доступ чтением. Секрет приложения в набор не включается и для этого сценария не нужен.

## Переменные

- `YANDEX_METRIKA_TOKEN` — OAuth-токен с правом чтения;
- `YANDEX_METRIKA_PROJECT_ROOT` — корень текущего проекта, по умолчанию текущая папка;
- `YANDEX_METRIKA_CONFIG_FILE` — явный путь к закрытому файлу настроек;
- `YANDEX_METRIKA_CACHE_DIR` — закрытая папка кэша.

Если файл настрек создаётся вручную, в нём допустима только строка вида:

```bash
YANDEX_METRIKA_TOKEN=USER_OAUTH_TOKEN
```

Файлу нужны права `0600`, а его папке — `0700`. Номера счётчиков и целей передаются командами `--counter` и `--goals`; в публичные примеры они не вшиваются.

## Запуск

```bash
plugins/yandex-direct-for-all/scripts/collect_metrika.sh counters
plugins/yandex-direct-for-all/scripts/collect_metrika.sh goals --counter COUNTER_ID
plugins/yandex-direct-for-all/scripts/collect_metrika.sh traffic_summary --counter COUNTER_ID --date1 YYYY-MM-DD --date2 YYYY-MM-DD
```

Выгрузки и кэш не публикуются.
