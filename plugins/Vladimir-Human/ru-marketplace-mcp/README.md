# ru-marketplace-mcp

**Русский** · [English](README.en.md)

[![CI](https://github.com/Vladimir-Human/ru-marketplace-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Vladimir-Human/ru-marketplace-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ru-marketplace-mcp.svg)](https://pypi.org/project/ru-marketplace-mcp/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-stdio%20%7C%20http-orange.svg)](https://modelcontextprotocol.io)

**MCP-серверы для российских и китайских маркетплейсов.** Цены, наличие,
рейтинги, отзывы и реквизиты продавцов с Wildberries, Ozon, Яндекс Маркета,
Детского мира, Авито, AliExpress, Taobao, Мегамаркета, Lamoda, DNS и Ситилинка.
Плюс недвижимость с Циана и
сравнение цен по всем товарным источникам одним вызовом.

Только чтение. Ключи API, токены и регистрация не нужны — площадки с жёстким
анти-ботом читаются через ваш собственный Chrome. Одно исключение по желанию:
опциональный MPStats берёт платный токен (`MPSTATS_MP_AUTH`) — без него всё
остальное работает как прежде.

<p align="center">
  <img src="docs/assets/demo-compare.svg" width="760"
       alt="compare_prices(&quot;кроссовки мужские&quot;): предложения Wildberries и Яндекс Маркета по цене, дешевле всего wildberries 712 ₽">
</p>

<sub>Пример вызова из раздела [«Сравнение цен»](docs/TOOLS.ru.md#сравнение-цен--compare_).</sub>

## Быстрый старт

Нужны **Python 3.12+** и [uv](https://docs.astral.sh/uv/).

Без checkout пакет ставится с PyPI и сам подключается к найденному клиенту
(`--dry-run` покажет план и ничего не запишет):

```bash
uvx ru-marketplace-mcp setup
```

Или в один клик: [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-0098FF?logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=marketplace&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22ru-marketplace-mcp%22%2C%22compare-mcp%22%5D%7D) [![Install in Cursor](https://img.shields.io/badge/Cursor-Install_MCP-000000?logo=cursor&logoColor=white)](https://cursor.com/en/install-mcp?name=marketplace&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJydS1tYXJrZXRwbGFjZS1tY3AiLCJjb21wYXJlLW1jcCJdfQ==)

Для установки клиента, выбора источников и проверки первого предложения —
[пошаговый старт](docs/QUICKSTART.md). Node нужен только для тестов разработчика.
Публикация на PyPI (для владельца): [DEPLOYMENT.md — PyPI](docs/DEPLOYMENT.md#pypi-maintainer).

[Первый успешный запрос](docs/QUICKSTART.md) · [Архитектура](docs/ARCHITECTURE.md) ·
[Как добавить источник](docs/ADDING_A_SOURCE.md) · [Про анти-бот](docs/ANTI_BOT.md)

---

## Что внутри

| Сервер            | Инструментов | Что нужно, чтобы читалось                                                  | Что умеет                                                                                 |
| ----------------- | ------------ | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Wildberries**   | 8            | анонимный HTTP                                                             | Поиск, карточки, отзывы, вопросы о товаре, реквизиты продавца, каталог и товары категории |
| **Яндекс Маркет** | 2            | анонимный HTTP                                                             | Цены разных продавцов, разбивка оценок по звёздам, отзывы                                 |
| **Детский мир**   | 3            | анонимный HTTP                                                             | Детские товары, наличие в офлайн-магазинах, категории                                     |
| **Ozon**          | 3            | ваш Chrome; с домашнего IP часто и без него                                | Поиск, карточки, отзывы                                                                   |
| **Авито**         | 3            | ваш Chrome + российский домашний IP и запросы вразрядку — иначе блок по IP | Поиск объявлений, карточки, репутация продавца                                            |
| **Taobao**        | 2            | ваш Chrome с активным входом в Taobao                                      | Поиск и карточки, цены в юанях                                                            |
| **Мегамаркет**    | 2            | ваш Chrome с активным входом — анонимной сессии API отдаёт пусто           | Поиск и карточки через мобильный API                                                      |
| **Lamoda**        | 2            | карточки: HTTP GraphQL → Chrome при отказе; поиск — Chrome                            | Поиск, карточки с размерами                                                               |
| **DNS**           | 2            | ваш Chrome (Qrator)                                                        | Поиск и карточки электроники                                                              |
| **Ситилинк**      | 2            | ваш Chrome (Qrator)                                                        | Поиск и карточки электроники                                                              |
| **AliExpress**    | 2            | ваш Chrome (x5sec)                                                       | Поиск и карточки, цены в рублях                            |
| **Циан**          | 2            | ваш Chrome (WAF по IP)                                                     | Недвижимость: поиск по фильтрам (продажа, аренда, посуточно) и карточка объявления         |
| **Сравнение**     | 4            | опрашивает всё перечисленное                                               | «Где дешевле?» одним вызовом                                                              |
| **MPStats**       | 2            | платный аккаунт MPStats, cookie `mp_auth` (опционально)                    | Продажи/остатки/графики за 30 дней по SKU Ozon/WB, остатки по складам (FBS/FBO)           |

Читается анонимно, без браузера: Wildberries, Яндекс Маркет и Детский мир.
Карточки Lamoda сначала читаются по HTTP GraphQL; при отказе нужен ваш Chrome
(CDP) для запасного уровня. Остальным нужен ваш залогиненный Chrome (CDP). Taobao и
Мегамаркет вдобавок требуют активного входа в саму площадку — без него Taobao
упирается в стену логина, а Мегамаркет отдаёт пустой ответ. Авито ещё и блокирует
по IP: с датацентрового адреса это глухой отказ, с российского домашнего — работает,
если не частить запросами. Запросы к CDP-источникам идут вразрядку: очередь
подряд без пауз роняет их (DNS и Taobao в проверке так и деградировали), поэтому
коннекторы держат паузу между вызовами сами. Точное состояние из вашей сессии
покажет `marketplace-mcp doctor`.

MPStats стоит особняком: это единственный **платный** источник. Без
`MPSTATS_MP_AUTH` объединённый `marketplace-mcp` вообще не монтирует его
инструменты — они всё равно отвечали бы `auth_missing` — поэтому он опционален
и подключается по желанию, на остальные тринадцать серверов он не влияет никак.
Отдельный `mpstats-mcp` запускается и без токена и на вызовы отвечает
`auth_missing`.

Всего 39 инструментов в 14 серверах на общем рантайме `mcp-core`. Плюс объединённый
`marketplace-mcp`, который монтирует всё разом — одна запись в конфиге клиента
вместо четырнадцати. У него два своих инструмента: `marketplace_sources` (какие
коннекторы поднялись, а какие отвалились и почему) и `marketplace_health` (жив ли
Chrome, какие хосты остывают, какую страницу открыть человеку). С токеном MPStats
в нём 41 инструмент, без токена — 39: те же смонтированные источники минус два
`mpstats_*`, плюс эти два.

**Проверка 2.7.0:** 30 октября с одного адреса Wildberries при отказе API (HTTP 403) сам прочитал поиск через Chrome: 40 товаров, у всех цена. Код остальных источников с v2.6.0 не менялся; их проверял [прогон v2.6.0](docs/releases/RELEASE_NOTES_v2.6.0.md#статус-живой-проверки) того же дня (12 из 13 источников, MPStats без токена). [Подробности v2.7.0](docs/releases/RELEASE_NOTES_v2.7.0.md#что-проверено).

## Подключение к MCP-клиенту

Каждый сервер — консольная команда, поэтому пути в конфиге не зашиваются.

<details open>
<summary><b>Claude Desktop</b> — <code>claude_desktop_config.json</code></summary>

Windows: `%APPDATA%\Claude\claude_desktop_config.json`
macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

Самый короткий путь — `marketplace-mcp setup`: команда находит Claude Desktop,
Cursor и Claude Code, пишет им конфиг (по умолчанию профиль `compare`),
запускает scraping-Chrome, прогоняет `doctor` и предлагает `unblock` для
источника, закрытого браузером. `--dry-run` только печатает шаги и файлы.

```console
marketplace-mcp setup
```

Если клиент нетипичный или нужен один конкретный, тот же конфиг пишет
`install --write`:

```console
marketplace-mcp install claude --write
```

Команда допишет запись `marketplace` в конфиг Claude Desktop
(`%APPDATA%\Claude\claude_desktop_config.json` на Windows,
`~/Library/Application Support/Claude/claude_desktop_config.json` на macOS,
`~/.config/Claude/claude_desktop_config.json` на Linux). Путь к `uv` и к вашему
checkout подставятся абсолютными (у десктопного клиента часто нет PATH
терминала), чужие серверы и остальные настройки конфига останутся на месте,
старый файл сохранится как `claude_desktop_config.json.bak-<метка>`. Остаётся
перезапустить клиент. `--dry-run` показывает, что именно будет записано, и
ничего не пишет; `--per-source` возвращает старую раскладку — по записи на
источник — и с `--profile` не сочетается.

По умолчанию запись запускает `compare-mcp` — профиль `compare`: 4 инструмента
сравнения цен, самый дешёвый в каждом запросе. `--profile decision` добавляет
осмотр карточки из шортлиста (5 инструментов), `--profile full` берёт
`marketplace-mcp` со всеми инструментами источников — в несколько раз дороже
(замер по профилям — в [docs/TOOLS.md](docs/TOOLS.md)).
Меняется только консольная команда записи, имя `marketplace` остаётся прежним.
Подробнее о выборе режима — [dsh/README.md](dsh/README.md) и
`docs/QUICKSTART.md`.

Если конфиг удобнее править руками, начните с одной записи:

```jsonc
{
  "mcpServers": {
    "marketplace": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "compare-mcp"],
    },
  },
}
```

Если нужны отдельные серверы, `marketplace-mcp install claude --per-source`
напечатает готовый блок для вставки. Путь к вашему checkout там уже подставлен:
заглушку `/path/to/ru-marketplace-mcp` править руками не придётся. При установке из
wheel вместо путей печатаются консольные команды на PATH. Неизвестное имя клиента
(допустимы `claude`, `claude-code`, `cursor`, `dsh`) команда отклоняет с пояснением и
кодом возврата 2 — молча подставить блок для Claude она не может.

У браузерного уровня есть ещё команды: `marketplace-mcp browser start`
(запустить scraping-Chrome; по умолчанию окно видно, `--hidden` — за экраном),
`marketplace-mcp browser status` (достижим ли CDP-эндпоинт, какая версия Chrome,
сколько вкладок и где окно) и `marketplace-mcp browser show` (окно
scraping-Chrome на экран — на Windows автозапуск коннектора стартует за экраном,
и без этого нельзя ни войти руками, ни пройти проверку сайта). Когда `doctor`
показывает стену, `marketplace-mcp unblock <source>` откроет нужную страницу в
новой вкладке, подождёт, пока вы пройдёте проверку или войдёте, и перепроверит
только этот источник. Ни одна из этих команд не ходит в сайты сама и не решает
проверку за человека.

Минимальный
вариант вручную:

```jsonc
{
  "mcpServers": {
    "wildberries": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "wb-mcp"],
    },
    "ozon": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "ozon-mcp"],
    },
    "compare-prices": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "compare-mcp"],
    },
  },
}
```

Путь пишите с прямыми слешами `/` или двойными обратными `\\`. Полный список
команд — `wb-mcp`, `ozon-mcp`, `yandex-mcp`, `detmir-mcp`, `avito-mcp`,
`taobao-mcp`, `megamarket-mcp`, `lamoda-mcp`, `dns-mcp`, `citilink-mcp`,
`compare-mcp`, `marketplace-mcp`.

### Только нужные площадки: `MARKETPLACE_SOURCES`

Объединённый сервер монтирует все источники, а описания их инструментов уходят
в контекст **в каждом запросе**. Переменная `MARKETPLACE_SOURCES` оставляет
только перечисленные:

```jsonc
{
  "mcpServers": {
    "marketplace": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "marketplace-mcp"],
      "env": {
        "MARKETPLACE_SOURCES": "wildberries,ozon,yandex_market,avito,aliexpress,dns,compare",
      },
    },
  },
}
```

Имена — канонические (`wildberries`, `ozon`, `yandex_market`, `detsky_mir`,
`avito`, `taobao`, `megamarket`, `lamoda`, `dns`, `citilink`, `aliexpress`,
`cian`, `compare`, `mpstats`); короткие псевдонимы `wb`, `ym`/`yandex`, `detmir`, `ali`
тоже принимаются. Неизвестное имя отклоняется при запуске с перечнем
поддерживаемых источников, чтобы опечатка не превратилась в частичный сервер.
Переменная не задана или пуста — монтируется всё, как раньше.
Отключённые источники видно в `marketplace_sources`: они попадают в `skipped`
с пометкой, что их сняли, а не что они не импортировались. `compare_prices`
опрашивает ровно тот же набор.

</details>

<details>
<summary><b>Claude Code</b></summary>

Установка плагина (15 навыков + MCP) одной командой:

```text
/plugin install ru-marketplace-mcp --marketplace Vladimir-Human/ru-marketplace-mcp
```

Или подключение серверов вручную из локального клона:

```bash
claude mcp add wildberries -- uv run --directory /путь/к/ru-marketplace-mcp wb-mcp
claude mcp add yandex-market -- uv run --directory /путь/к/ru-marketplace-mcp yandex-mcp
claude mcp add detsky-mir -- uv run --directory /путь/к/ru-marketplace-mcp detmir-mcp
claude mcp add ozon -- uv run --directory /путь/к/ru-marketplace-mcp ozon-mcp
claude mcp add compare-prices -- uv run --directory /путь/к/ru-marketplace-mcp compare-mcp
```

</details>

<details>
<summary><b>Cursor</b> — <code>.cursor/mcp.json</code></summary>

```jsonc
{
  "mcpServers": {
    "compare-prices": {
      "command": "uv",
      "args": ["run", "--directory", "/путь/к/ru-marketplace-mcp", "compare-mcp"],
    },
  },
}
```

</details>

<details>
<summary><b>Другой stdio-клиент</b></summary>

Запустите `uv run --directory /путь/к/репозиторию <команда>`, где команда — одна из
`wb-mcp`, `ozon-mcp`, `yandex-mcp`, `detmir-mcp`, `aliexpress-mcp`, `cian-mcp`, `compare-mcp`. Серверы говорят по
JSON-RPC через stdin и stdout, диагностику пишут в stderr. Опциональный
`mpstats-mcp` запускается так же, с `MPSTATS_MP_AUTH` в окружении.

</details>

<details>
<summary><b>DeepSeek Harness (dsh)</b> — плагин-бандл</summary>

В dsh это не запись `mcpServers`, а слой профиля. Бандл лежит в подкаталоге
[`dsh/`](dsh/README.md) и ставится штатным менеджером плагинов (`pnpm` нужен на PATH):

```console
dsh plugin --profile web add ru-marketplace-mcp-dsh
# или напрямую из GitHub:
dsh plugin --profile web add github:Vladimir-Human/ru-marketplace-mcp#path:/dsh
```

Сразу после установки появляются 15 навыков и **ни одного** MCP-инструмента: все три
строки MCP выключены, пока не задана переменная `RU_MARKETPLACE_MCP_DIR` с путём к
клону.
<!-- tools-cost:start -->
Так сделано потому, что смонтированный сервер платится в каждом запросе:
рекомендуемый режим сравнения цен стоит ≈1.7k токенов, режим с инспекцией
карточки — ≈2.0k, полный набор — ≈13.4k (оценка по `tools/list`;
подробности в [docs/TOOLS.md](docs/TOOLS.md)).
<!-- tools-cost:end -->
Включение и полный режим описаны в [dsh/README.md](dsh/README.md).

</details>

После подключения перезапустите клиент и прогоните `marketplace-mcp doctor`. Он
запускает канарейку каждого коннектора: код `0` — все выбранные проверки здоровы,
`1` — дрейф парсера, `2` — признанный блок или непроверенный источник, `3` — не
удалось записать status-файл, `4` — сломалась самопроверка или вызов doctor
(включая ошибку аргументов). Nightly поднимает тревогу на `1` и `4`, но не на `2`.
Отказ бюджета получает причину `budget_refused`, а не статус здоровой проверки.

## Инструменты

Сгенерированный справочник по инструментам с параметрами и ценой контекста:
[docs/TOOLS.md](docs/TOOLS.md).

Канарейки `*_selfcheck` в этом перечне не значатся намеренно: они не публикуются
по MCP, потому что диагностика оператора стоила бы модели ~7,5 тыс. токенов в
каждом запросе. Запускает их `marketplace-mcp doctor` — все разом, из командной
строки.

Подробно по каждой площадке, с таблицами инструментов и примерами, — в
[docs/TOOLS.ru.md](docs/TOOLS.ru.md):

- [Wildberries — `wb_*`](docs/TOOLS.ru.md#wildberries--wb_)
- [Яндекс Маркет — `yandex_*`](docs/TOOLS.ru.md#яндекс-маркет--yandex_)
- [Детский мир — `detmir_*`](docs/TOOLS.ru.md#детский-мир--detmir_)
- [Ozon — `ozon_*`](docs/TOOLS.ru.md#ozon--ozon_)
- [Авито — `avito_*`](docs/TOOLS.ru.md#авито--avito_)
- [Taobao — `taobao_*`](docs/TOOLS.ru.md#taobao--taobao_)
- [Мегамаркет, Lamoda, DNS, Ситилинк](docs/TOOLS.ru.md#мегамаркет-lamoda-dns-ситилинк)
- [AliExpress — `aliexpress_*`](docs/TOOLS.ru.md#aliexpress--aliexpress_)
- [Циан — `cian_*`](docs/TOOLS.ru.md#циан--cian_)
- [Сравнение цен — `compare_*`](docs/TOOLS.ru.md#сравнение-цен--compare_)
- [MPStats — `mpstats_*`](docs/TOOLS.ru.md#mpstats--mpstats_)

## Навыки для агента

У каждого коннектора — свой навык в `skills/`: пятнадцать штук, по одному
на источник плюс общий `marketplace`. Навык это не пересказ README: он объясняет агенту, когда за этот
источник вообще браться, чего у источника нет, и каким его ответам нельзя верить
без второго взгляда.

| Навык                         | Сервер            |
| ----------------------------- | ----------------- |
| `skills/wb-connector`         | `wb-mcp`          |
| `skills/ozon-connector`       | `ozon-mcp`        |
| `skills/yandex-connector`     | `yandex-mcp`      |
| `skills/detmir-connector`     | `detmir-mcp`      |
| `skills/avito-connector`      | `avito-mcp`       |
| `skills/taobao-connector`     | `taobao-mcp`      |
| `skills/megamarket-connector` | `megamarket-mcp`  |
| `skills/lamoda-connector`     | `lamoda-mcp`      |
| `skills/dns-connector`        | `dns-mcp`         |
| `skills/citilink-connector`   | `citilink-mcp`    |
| `skills/aliexpress-connector` | `aliexpress-mcp`  |
| `skills/cian-connector`       | `cian-mcp`        |
| `skills/compare-prices`       | `compare-mcp`     |
| `skills/mpstats-connector`    | `mpstats-mcp`     |
| `skills/marketplace`          | `marketplace-mcp` |

`mcp-core` — общий рантайм под остальными серверами. Своего навыка у него нет.

Соответствие проверяется тестом
(`packages/marketplace-connector/tests/test_skills_parity.py`): новый коннектор
без навыка роняет прогон, как и навык, который называет несуществующий
инструмент или забыл существующий. До этого теста навык DNS почти год советовал
формат ссылки `/product/<24-hex>/` — тот самый шаблон, который чинили как баг.

Скиллы едут в Docker-образ (`/app/skills/`), но **в колёсах их нет**: `skills/`
лежит в корне репозитория. При установке release-wheel возьмите навыки
из репозитория отдельно; пакета `ru-marketplace-mcp` с PyPI это тоже касается.

## Настройка

Все параметры задаются переменными окружения с префиксом коннектора. Все
необязательные.

Для проверок в браузере добавлен опциональный режим сохранения вкладки:
`CHROME_CHALLENGE_HANDOFF_S=120`. После завершения проверки повтор того же
запроса от того же клиента (в той же MCP-сессии или, по stdio, к тому же процессу
сервера) продолжает чтение этой вкладки. Поддержка и ограничения
описаны в [настройке Chrome](docs/CDP_SETUP.md#optional-challenge-handoff).

| Префикс              | Основные параметры                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `WB_`                | `TIMEOUT`, `MIN_GAP`, `DEFAULT_DEST`, `NET_RETRIES`, `MAX_BODY_BYTES`, `CACHE_TTL`, `PROXY`                                      |
| `YANDEX_`            | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `PROXY`                                                                                       |
| `DETMIR_`            | `REGION` (`RU-MOW`, `RU-SPE` и другие), `CACHE_TTL`, `PROXY`                                                                     |
| `OZON_`              | `TIMEOUT`, `MIN_GAP`, `IMPERSONATE`, `CACHE_TTL`, `PROXY`                                                                        |
| `AVITO_`             | `TIMEOUT`, `MIN_GAP`, `IMPERSONATE`, `CACHE_TTL`, `PROXY`, `LOCATION_ID`                                                         |
| `TAOBAO_`            | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`,                                                                                               |
| `ALI_`               | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`                                                                                                |
| `MEGAMARKET_`        | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `USE_PROFILE_ADDRESS` (0/1, по умолчанию 0 — приватный список адресов профиля не читается; 1 = адрес по умолчанию из залогиненного профиля, цены «как видит оператор») |
| `LAMODA_`            | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `PROXY`                                                                                       |
| `DNS_` / `CITILINK_` | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`                                                                                                |
| `CHROME_`            | `CDP_HOST`, `CDP_PORT`, `SCRAPING_PROFILE`, `BINARY`, `HEADLESS`, `STEALTH`                                                      |
| `COMPARE_`           | `SOURCE_TIMEOUT`                                                                                                                 |
| `MPSTATS_`           | `MP_AUTH` (единственный обязательный — без него инструменты отвечают `auth_missing`), `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `PROXY` |
| `MCP_`               | `TRANSPORT` (`stdio` по умолчанию, либо `http`), `HTTP_HOST`, `HTTP_PORT`                                                        |

`CHROME_CDP_HOST` указывает, куда дозвониться CDP-клиенту (по умолчанию
`127.0.0.1`). Из контейнера ставьте `chrome` (сайдкар) или `host.docker.internal`
— это открывает tier-2 источники (Ozon, Авито, Taobao, Мегамаркет, Lamoda,
DNS, Ситилинк, AliExpress, Циан) в Docker без host networking. Подробности в
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

`*_CACHE_TTL=0` выключает кэш. `*_PROXY` перекрывает стандартные `HTTPS_PROXY` и
`ALL_PROXY` — свой префикс есть у семи коннекторов: `WB_`, `YANDEX_`, `DETMIR_`,
`OZON_`, `AVITO_`, `LAMODA_` и `MPSTATS_`. У Taobao своего нет намеренно: поиск там
подписан и ходит через собственный клиент. У Мегамаркета, DNS и Ситилинка тоже нет:
их трафик идёт через ваш Chrome, а его egress — дело настроек браузера. Кэшируются
только удачные ответы: запомнить сбой значило бы растянуть секундную помеху на весь
TTL.

У Ozon прокси применяется к первому уровню. Второй идёт через ваш собственный Chrome,
и его трафик — дело настроек этого браузера.

**Секрет один, и тот опциональный.** Всем серверам, кроме MPStats, ничего не нужно:
нечего настраивать, нечему утечь. У MPStats есть `MPSTATS_MP_AUTH` — JWT платного
аккаунта, и потому его место только в env клиентской записи: в коде и коммитах его
нет и быть не должно.

## Разработка

```bash
git clone https://github.com/Vladimir-Human/ru-marketplace-mcp.git
cd ru-marketplace-mcp
uv sync --all-packages
uv run pytest -q -m "not live and not cdp"    # 3442 офлайн-тестов, сеть не нужна
uv run pytest -q -m "not live"                # то, что гоняет CI
uv run pytest -q -m "not live" --cov          # покрытие, порог 70% в CI
uv run ruff check . && uv run ruff format --check .
uv run mypy                                   # что проверять — в [tool.mypy] files
uv run mypy --platform win32                  # ловит ошибки, видимые только на Windows
uv run python scripts/check_no_print.py       # запись в stdout ломает JSON-RPC
uv run python scripts/check_versions.py       # одна версия во всех 93 местах
```

Проверка живого эндпоинта:

```bash
uv run python -c "
import asyncio
from wb_connector.server import wb_selfcheck
print(asyncio.run(wb_selfcheck()).status)   # ждём success
"
```

Часть тестов прогоняет **настоящий JS-экстрактор коннектора** по снятой разметке
и проверяет результат против цен, которые в тот момент были на странице. Для
этого нужен Node с jsdom:

```bash
npm install jsdom      # либо NODE_PATH на уже установленный
uv run pytest -q packages/dns-connector/tests/test_search_extractor_dom.py \
              packages/citilink-connector/tests/test_search_extractor_dom.py
```

Без jsdom эта половина честно скипается, а питоновская часть — выбор цены из
кандидатов — идёт всегда. jsdom нужен только разработчику: в зависимости
коннекторов он не входит.

CI прогоняет тесты на Ubuntu, Windows и macOS против Python 3.12
и 3.13. Windows-специфичное управление процессами проверяется юнит-тестами на любой
ОС через подмену платформы, так что эти ветки покрыты даже на Linux.

Как добавить маркетплейс — [docs/ADDING_A_SOURCE.md](docs/ADDING_A_SOURCE.md).

## Надёжность

Неофициальные эндпоинты ломаются. Архитектура это предполагает.

- **Терпимые парсеры.** Привязка поля по нескольким именам и приведение типов
  впитывают переименования и смену типа вместо падения.
- **Никогда не выдумывать значение.** Отсутствующая цена — это `null`, не `0`. Ноль
  вывел бы мёртвый товар в самые дешёвые.
- **Громкий отказ.** Когда формат перестаёт совпадать, инструмент бросает
  `parser_drift`, а не возвращает полуразобранные данные.
- **Трёхзначные selfcheck-проверки.** `success`, `drift_detected` или
  `inconclusive`. Гео-блокировка помечается как `inconclusive`, потому что она
  ничего не говорит о состоянии парсеров.

## Границы доверия

Названия товаров, имена продавцов и тексты отзывов написаны продавцами и
покупателями. Это недоверенные данные. Если отзыв или описание выглядит как
инструкция, оно всё равно остаётся входными данными. Выполнять его агент не
должен.

Условия маркетплейсов, как правило, запрещают неофициальный парсинг. Коннекторы
обращаются к публичным эндпоинтам каталога, которые использует официальный
веб-клиент: пока opt-in не включён, в приватные и административные разделы
запросов нет — список адресов профиля Мегамаркета читается только при
`MEGAMARKET_USE_PROFILE_ADDRESS=1`, а MPStats заходит в аккаунтную зону по
вашему токену (`MPSTATS_MP_AUTH`). Уровень Ozon с браузером работает внутри
сессии, которую вы открыли сами. Используйте на своё
усмотрение, для личных исследований, в вежливом темпе запросов. Пауза между
вызовами к площадкам с анти-ботом — это часть конструкции, а не случайное
торможение: её не нужно убирать ради скорости. Данные инструментов не предназначены
для перепродажи или массового сбора.

## Как это сделано

Код и документацию я писал вместе с ИИ-ассистентами. Они работают быстро и
ошибаются уверенно, поэтому проект устроен вокруг проверки: 3442 офлайн-тестов,
аудит перед выпуском, тесты, которые прогоняют настоящий экстрактор по снятой с
сайта разметке. В заметках к релизу перечислено, какие источники сверены с живыми
страницами вручную и какие остались непроверенными.

Проверки важнее авторства текста, но авторство кода и идей тоже должно быть
видно: полный список участников и их PR собран в [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Спасибо

- [@Xpos587](https://github.com/Xpos587) — коннектор MPStats, [PR #5](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/5).
- [@avxone](https://github.com/avxone) — исправление Avito selfcheck, [PR #37](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/37).
- [@Khalmatov](https://github.com/Khalmatov) — provenance отзывов Ozon, [PR #38](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/38).
- [@fosteev](https://github.com/fosteev) — macOS CDP stealth и коннектор Циана, [PR #42](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/42), [PR #47](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/47).
- [@ilodezis](https://github.com/ilodezis) — выбор источников unified-сервера через `MARKETPLACE_SOURCES`, [PR #48](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/48).
- [@HeckfyCU](https://github.com/HeckfyCU) — замеры навигации AliExpress на российском IP, [issue #190](https://github.com/Vladimir-Human/ru-marketplace-mcp/issues/190): по его замерам найден и исправлен предел ожидания страницы.
- [@XaruStar](https://github.com/XaruStar) — разбор живого ответа Ozon `webListReviews` со строковым `itemId`, [issue #214](https://github.com/Vladimir-Human/ru-marketplace-mcp/issues/214): по нему исправлен учёт `own_reviews` и проверка `item_id` в `ozon_selfcheck`.

## Лицензия

MIT, файл [LICENSE](LICENSE).
