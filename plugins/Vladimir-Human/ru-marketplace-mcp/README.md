# ru-marketplace-mcp — MCP-серверы для маркетплейсов России и Китая

<!-- mcp-name: io.github.Vladimir-Human/ru-marketplace-mcp -->

**Русский** · [English](README.en.md) · [Установка для ИИ-агентов](llms-install.md) · [llms.txt](llms.txt)

[![CI](https://github.com/Vladimir-Human/ru-marketplace-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Vladimir-Human/ru-marketplace-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ru-marketplace-mcp.svg)](https://pypi.org/project/ru-marketplace-mcp/)
[![npm](https://img.shields.io/npm/v/ru-marketplace-mcp-dsh.svg?label=npm%20%28dsh%29)](https://www.npmjs.com/package/ru-marketplace-mcp-dsh)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-stdio%20%7C%20http-orange.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Живые цены, остатки, рейтинги, отзывы и реквизиты продавцов с 12 площадок РФ и
Китая: **Wildberries**, **Ozon**, **Яндекс Маркет**, **Авито**, **AliExpress**,
**Taobao**, **DNS**, **Ситилинк**, **Мегамаркет**, **Lamoda**, **Детский мир** и
недвижимость с **Циана**.

`compare_prices` сравнивает цены по всем товарным площадкам одним вызовом,
отсеивает флешки и чехлы по цене смартфона (`cheapest_comparable`) и не выдаёт
скидку по WB Кошельку, Яндекс Пэй или купону за обычную цену. Только чтение, без
ключей API и кабинета продавца: открытые площадки отвечают по HTTP, закрытые
анти-ботом — через ваш отдельный Chrome (для Taobao и Мегамаркета в нём нужен
обычный покупательский вход).

<p align="center">
  <img src="docs/assets/demo-compare.svg" width="560"
       alt="compare_prices(&quot;iphone 16 128gb&quot;): флешка 1 531 ₽ и цена по WB Кошельку 56 833 ₽ не побеждают; лидер comparable — Apple iPhone 16 за 64 990 ₽ на AliExpress">
</p>

<sub>Реальный разбор из раздела <a href="#настоящий-ответ">«Настоящий ответ»</a> (`c1-iphone16-128gb.json`).</sub>

## Быстрый старт

Нужны **Python 3.12+** и [uv](https://docs.astral.sh/uv/). Клонировать репозиторий
не нужно: одна команда скачает пакет с PyPI, найдёт установленные MCP-клиенты и
настроит подключение (`--dry-run` только покажет план):

```bash
uvx ru-marketplace-mcp setup
```

Или установка в один клик:

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-0098FF?logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=marketplace&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22ru-marketplace-mcp%22%2C%22compare-mcp%22%5D%7D)
[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_MCP-000000?logo=cursor&logoColor=white)](https://cursor.com/en/install-mcp?name=marketplace&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJydS1tYXJrZXRwbGFjZS1tY3AiLCJjb21wYXJlLW1jcCJdfQ==)

Для **Claude Desktop** без терминала — бандл `ru-marketplace-mcp-compare-<версия>.mcpb` в [GitHub Releases](https://github.com/Vladimir-Human/ru-marketplace-mcp/releases) (проверено на Windows, на macOS не проверялось).

### Какой профиль выбрать

Описания подключённых инструментов уходят модели в каждом запросе, поэтому
`setup` и `install` по умолчанию ставят компактный профиль `compare`:

| Профиль | Объём | Когда выбирать |
| --- | --- | --- |
| **`compare`** *(по умолч.)*<br>`compare-mcp` | 4 · ≈1.7k | Сравнить цены по площадкам и проверить карточку лидера |
| **`decision`**<br>`decision-mcp` | 5 · ≈2.0k | Всё из `compare` плюс осмотр шортлиста с отзывами |
| **`full`**<br>`marketplace-mcp` | 39 · ≈13.1k | Прямой поиск, отзывы, продавцы, категории и Циан |
| Одна площадка<br>`--per-source` | 2–8 · мин. | Нужен только один маркетплейс |

> **Безопасность и границы:** не включайте эти серверы в одну сессию агента с инструментами, которые читают личные данные и могут отправить их наружу без вашего подтверждения, и держите отдельный профиль Chrome без почты и банка ([SECURITY.md](SECURITY.md)).

[Первый успешный запрос](docs/QUICKSTART.md) · [Справочник инструментов](docs/TOOLS.md) ·
[Архитектура](docs/ARCHITECTURE.md) · [Про анти-бот](docs/ANTI_BOT.md)

---

## Поддерживаемые площадки (12 источников)

| Площадка | Доступ | Что умеет |
| --- | --- | --- |
| **Wildberries** (8) | HTTP (403 → Chrome) | Поиск, карты, отзывы, Q&A, seller ID, каталог |
| **Яндекс Маркет** (2) | прямой HTTP | Цены и отзывы, оценки по звёздам |
| **Детский мир** (3) | прямой HTTP | Детские товары, остатки, каталог |
| **Ozon** (3) | Chrome / HTTP | Поиск, карты, отзывы |
| **Авито** (3) | Chrome + паузы | Лоты, карты, рейтинг продавца |
| **Taobao** (2) | Chrome + вход | Поиск, карты, цены в юанях |
| **Мегамаркет** (2) | Chrome + вход | Поиск и карты через API |
| **Lamoda** (2) | HTTP → Chrome | Поиск, карты, размеры |
| **DNS** (2) | Chrome (Qrator) | Поиск и карты техники |
| **Ситилинк** (2) | Chrome (Qrator) | Поиск и карты техники |
| **AliExpress** (2) | Chrome (x5sec) | Поиск и карты в рублях |
| **Циан** (2) | Chrome (WAF IP) | Жильё: продажа, аренда, сутки |
| **Сравнение** (4) | по площадкам | «Где дешевле?», сверка, снимок |

Без браузера работают Wildberries, Яндекс Маркет и Детский мир (если API
Wildberries отвечает 403, поиск и карточки сами перечитываются через ваш Chrome).
Карточки Lamoda сначала идут по HTTP GraphQL и обращаются к Chrome (CDP) только
при отказе. Остальным нужен ваш Chrome с CDP, а Taobao и Мегамаркету — ещё и вход
в аккаунт площадки: без него Taobao упирается в страницу входа, а Мегамаркет
возвращает пустую выдачу. Авито режет датацентровые адреса и отвечает с обычного
(не облачного) подключения при спокойном темпе запросов. К браузерным источникам
коннекторы ходят с паузой: очередь без передышки роняет сессию (так на проверках
отваливались DNS и Taobao). Точное состояние из вашей среды покажет
`marketplace-mcp doctor`.

Аналитика MPStats переехала на официальный MCP-сервер MPStats (`https://mcp.mpstats.io/mcp?token=<ваш токен MPStats>`) и в текущий состав `ru-marketplace-mcp` не входит.

Всего 37 инструментов в 13 серверах на общем рантайме `mcp-core`, плюс
промежуточный `decision-mcp` (5 инструментов) и объединённый `marketplace-mcp`,
который монтирует всё под одной записью в конфиге клиента и добавляет два своих
инструмента — `marketplace_sources` (какие коннекторы поднялись, а какие
пропущены и почему) и `marketplace_health` (жив ли Chrome, какие хосты остывают,
какую страницу открыть человеку) — итого 39 инструментов.

### Настоящий ответ

`compare_prices(query="iphone 16 128gb")`. Ответы площадок записаны в Chrome на машине владельца 17 ноября 2026 года в 01:29 UTC (аудит, цикл 1, запись [c1-iphone16-128gb.json](packages/compare-connector/tests/benchmark/recordings/c1-iphone16-128gb.json)) и пропущены через код `2.11.0` (коммит `f39a786f`). Ниже оставлены ключевые поля и по одному предупреждению каждого типа; полный ответ ещё содержит `source_outcomes` и все 25 предложений в `offers`.

```json
{
  "query": "iphone 16 128gb",
  "sources_queried": [
    "aliexpress", "citilink", "dns",
    "taobao", "wildberries", "yandex_market"
  ],
  "sources_ok": [
    "aliexpress", "dns", "taobao", "wildberries", "yandex_market"
  ],
  "complete": false,
  "total_offers": 25,
  "cheapest": {
    "source": "aliexpress",
    "product_id": "1005009110731940",
    "title": "MOVESPEED флешка USB Type C 64/128/256/512 ГБ",
    "price_rub": 1531.0,
    "currency": "rub",
    "rating": 4.8,
    "url": "https://aliexpress.ru/item/1005009110731940.html"
  },
  "cheapest_comparable": {
    "source": "aliexpress",
    "product_id": "1005008110020734",
    "title": "Смартфон Apple iPhone 16, 8/128ГБ",
    "price_rub": 64990.0,
    "currency": "rub",
    "rating": 5.0,
    "url": "https://aliexpress.ru/item/1005008110020734.html"
  },
  "price_spread_rub": 93459.0,
  "warnings": [
    "partial: 1 of 6 marketplaces did not answer (citilink) ...",
    "conditional_price: wildberries/1415238452: 56833 RUB requires WB Wallet; not ranked",
    "info:conditional_price_available: yandex_market/103530694148: 72825 RUB with Yandex Pay",
    "price_outlier: the cheapest offer is 1531.0 ₽ against a median of 70299.0 ₽ across 17 offers ...",
    "comparable_price: the raw cheapest listing is an accessory, a different condition, variant or model; cheapest_comparable is the safer like-for-like candidate",
    "foreign_currency: 5 offer(s) are priced in cny, not roubles ... excluded from the ranking"
  ],
  "server_version": "2.11.0"
}
```

<details>
<summary>Полный список <code>warnings</code> из этой записи (15 строк)</summary>

```json
[
  "partial: 1 of 6 marketplaces did not answer (citilink) — prices below cover only aliexpress, dns, taobao, wildberries, yandex_market",
  "source_warning:aliexpress: 2 tile(s) advertise a coupon price; price_rub carries the regular price and the coupon value is not part of the response — treat 'cheapest' ranking with care",
  "source_warning:wildberries: dom_fallback: WB API refused this address (HTTP 403); read through the scraping Chrome, in the WB region set in that browser rather than dest",
  "source_warning:wildberries: wb_dom_search: price_rub is the WB Wallet price on search tiles (the regular card price is equal or a few % higher and shows only on the product page — verify leaders with wb_card)",
  "conditional_price: wildberries/1415238452: 56833 RUB requires WB Wallet; not ranked",
  "conditional_price: wildberries/580725150: 76922 RUB requires WB Wallet; not ranked",
  "conditional_price: wildberries/580725161: 76922 RUB requires WB Wallet; not ranked",
  "info:conditional_price_available: yandex_market/103572173063: 71800 RUB with Yandex Pay",
  "info:conditional_price_available: yandex_market/103530694148: 72825 RUB with Yandex Pay",
  "info:conditional_price_available: yandex_market/4775394349: 68107 RUB with Yandex Pay",
  "info:conditional_price_available: yandex_market/5302780524: 66699 RUB with Yandex Pay",
  "info:conditional_price_available: yandex_market/4775394347: 69323 RUB with Yandex Pay",
  "price_outlier: the cheapest offer is 1531.0 ₽ against a median of 70299.0 ₽ across 17 offers — check it is the same product and configuration",
  "comparable_price: the raw cheapest listing is an accessory, a different condition, variant or model; cheapest_comparable is the safer like-for-like candidate",
  "foreign_currency: 5 offer(s) are priced in cny, not roubles — their price is in price_native and they are excluded from the ranking and from cheapest"
]
```

</details>

Самым дешёвым формально оказалась флешка: в её названии есть «128». Поэтому ответ отдельно называет `cheapest_comparable`, то есть сам телефон, и предупреждает о выбросе цены. Цена Wildberries, которая действует только с WB Кошельком, показана, но в сравнении не участвует. Ситилинк в этом вызове ответил отказом, и ответ говорит, что он неполный.

## Подключение к MCP-клиенту

Самый короткий путь — `uvx ru-marketplace-mcp setup` (или `uv run marketplace-mcp setup`
из клона репозитория): команда находит установленные клиенты (**Claude Desktop**,
**Cursor**, **Claude Code**, **VS Code**, **Windsurf**, **Antigravity**,
**Gemini CLI**, **Codex CLI**), прописывает профиль `compare`, запускает
отдельный Chrome для парсинга, проверяет источники через `doctor` и предлагает
`unblock`, если площадка просит вход или капчу (`--dry-run` только показывает
шаги и файлы; `--no-browser` и `--no-doctor` пропускают браузер и сетевые вызовы).

Настроить один конкретный клиент (поддерживаются все **9 целей**):

```console
uvx ru-marketplace-mcp install <client> --write --profile compare
```

| Клиент (`<client>`) | Что обновляет `--write` |
| --- | --- |
| **Claude Desktop**<br>`claude` | `mcpServers.marketplace` в конфиге Claude Desktop + `.bak`; есть и `.mcpb` в [Releases](https://github.com/Vladimir-Human/ru-marketplace-mcp/releases) |
| **Cursor**<br>`cursor` | `mcpServers.marketplace` в `~/.cursor/mcp.json` + `.bak` |
| **VS Code**<br>`vscode` | **`servers.marketplace`** (`"type": "stdio"`) в `Code/User/mcp.json` + `.bak` |
| **Windsurf**<br>`windsurf` | `mcpServers.marketplace` в конфиге Windsurf + `.bak` |
| **Antigravity**<br>`antigravity` | `mcpServers.marketplace` в конфиге Antigravity + `.bak` |
| **Gemini CLI**<br>`gemini` | `mcpServers.marketplace` в `~/.gemini/settings.json` + `.bak` |
| **Claude Code**<br>`claude-code` | Печатает `claude mcp add marketplace --scope user -- ...` |
| **Codex CLI**<br>`codex` | Печатает `codex mcp add marketplace -- ...` |
| **DeepSeek Harness**<br>`dsh` | Печатает `cordis.patch.yml` (плагин — в спойлере и [dsh/README.md](dsh/README.md)) |

<sub>Пути конфигов: **Claude Desktop** — `%APPDATA%\Claude\claude_desktop_config.json` (Win), `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), `~/.config/Claude/claude_desktop_config.json` (Linux); **Windsurf** — `~/.codeium/windsurf/mcp_config.json`; **Antigravity** — `~/.gemini/config/mcp_config.json`. Перед записью создаётся копия `.bak-&lt;метка&gt;`.</sub>

По умолчанию ставится профиль `compare` (`compare-mcp`). `--profile decision`
переключает запись на `decision-mcp`, `--profile full` — на полный
`marketplace-mcp` (при перезаписи существующей записи добавьте `--force`;
`--write --dry-run` показывает дифф без записи; `--per-source` печатает или
пишет отдельные серверы по площадкам и с `--profile` не сочетается). Неизвестное
имя клиента команда отклоняет с кодом возврата `2`.

Управление браузером и разблокировкой:
- `marketplace-mcp browser start` — запустить отдельный Chrome для парсинга (по умолчанию окно видно, `--hidden` — за экраном);
- `marketplace-mcp browser status` — доступен ли CDP, версия Chrome, вкладки и положение окна;
- `marketplace-mcp browser show` — вывести окно на экран (на Windows автозапуск паркует его за экраном);
- `marketplace-mcp unblock <source>` — открыть страницу входа или проверки в новой вкладке, подождать, пока вы пройдёте её сами, и перепроверить только этот источник (капчу за человека команды не решают).

<details>
<summary><b>Ручная настройка JSON и выбор площадок (<code>MARKETPLACE_SOURCES</code>)</b></summary>

Для клиентов с `mcpServers` (Claude Desktop, Cursor, Windsurf, Antigravity, Gemini CLI, Cline, OpenCode) без клона репозитория:

```json
{
  "mcpServers": {
    "marketplace": {
      "command": "uvx",
      "args": ["--from", "ru-marketplace-mcp", "compare-mcp"]
    }
  }
}
```

Для **VS Code** (`Code/User/mcp.json` использует корневой ключ `"servers"` и `"type": "stdio"`):

```json
{
  "servers": {
    "marketplace": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "ru-marketplace-mcp", "compare-mcp"]
    }
  }
}
```

Из локального клона (пути с прямыми слешами `/` или двойными обратными `\\`):

```json
{
  "mcpServers": {
    "marketplace": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "compare-mcp"]
    }
  }
}
```

Полный список из 15 консольных точек входа: `wb-mcp`, `ozon-mcp`, `yandex-mcp`,
`detmir-mcp`, `avito-mcp`, `taobao-mcp`, `megamarket-mcp`, `lamoda-mcp`,
`dns-mcp`, `citilink-mcp`, `aliexpress-mcp`, `cian-mcp`, `compare-mcp`,
`decision-mcp`, `marketplace-mcp`. Все серверы общаются по JSON-RPC через stdin
и stdout, а диагностику пишут в stderr.

### Только нужные площадки в полном режиме: `MARKETPLACE_SOURCES`

Объединённый `marketplace-mcp` монтирует все источники сразу. Переменная
`MARKETPLACE_SOURCES` оставляет только перечисленные и экономит контекст:

```json
{
  "mcpServers": {
    "marketplace": {
      "command": "uv",
      "args": ["run", "--directory", "C:/путь/к/ru-marketplace-mcp", "marketplace-mcp"],
      "env": {
        "MARKETPLACE_SOURCES": "wildberries,ozon,yandex_market,avito,aliexpress,dns,compare"
      }
    }
  }
}
```

Имена канонические (`wildberries`, `ozon`, `yandex_market`, `detsky_mir`,
`avito`, `taobao`, `megamarket`, `lamoda`, `dns`, `citilink`, `aliexpress`,
`cian`, `compare`); короткие псевдонимы `wb`, `ym`/`yandex`, `detmir`, `ali`
тоже принимаются. Опечатка в имени остановит старт сервера со списком допустимых
площадок. Отключённые источники видны в `marketplace_sources` в поле `skipped`.
`compare_prices` опрашивает только выбранные товарные источники с текстовым
поиском (Детский мир и Циан туда не входят); явный `sources` для отключённой
площадки вернёт `bad_request`.

</details>

<details>
<summary><b>Claude Code</b> — плагин с 14 навыками или <code>claude mcp add</code></summary>

Установка плагина (14 навыков + MCP) одной командой:

```text
/plugin install ru-marketplace-mcp --marketplace Vladimir-Human/ru-marketplace-mcp
```

Или подключение компактного профиля `compare-mcp` через CLI:

```bash
claude mcp add marketplace --scope user -- uvx --from ru-marketplace-mcp compare-mcp
```

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

Сразу после установки появляются 14 навыков и **ни одного** MCP-инструмента: все три
строки MCP выключены, пока не задана переменная `RU_MARKETPLACE_MCP_DIR` с путём к
клону.
<!-- tools-cost:start -->
Так сделано потому, что смонтированный сервер платится в каждом запросе:
рекомендуемый режим сравнения цен стоит ≈1.7k токенов, режим с инспекцией
карточки — ≈2.0k, полный набор — ≈13.1k (оценка по `tools/list`;
подробности в [docs/TOOLS.md](docs/TOOLS.md)).
<!-- tools-cost:end -->
Включение и полный режим описаны в [dsh/README.md](dsh/README.md).

</details>

После подключения перезапустите клиент и проверьте доступность источников
командой `marketplace-mcp doctor` (подробнее в [docs/QUICKSTART.md](docs/QUICKSTART.md)):
код `0` — выбранные проверки здоровы, `1` — дрейф парсера, `2` — площадка
закрыта анти-ботом, ждёт Chrome/входа или лимита бюджета (`budget_refused`), `3` —
не записался `--status-file`, `4` — сбой самой проверки или неверные аргументы.
Тревогу поднимают коды `1` и `4`, а при `2` следуйте подсказке `next:` в выводе.

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

## Навыки для агента

У каждого коннектора — свой навык в `skills/`: четырнадцать штук, по одному
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
| `skills/marketplace`          | `marketplace-mcp` |

`mcp-core` — общий рантайм под остальными серверами. Своего навыка у него нет.

Соответствие проверяется тестом
([test_skills_parity.py](packages/marketplace-connector/tests/test_skills_parity.py)): новый коннектор
без навыка роняет прогон, как и навык, который называет несуществующий
инструмент или забыл существующий. До этого теста навык DNS почти год советовал
формат ссылки `/product/<24-hex>/` — тот самый шаблон, который чинили как баг.

Скиллы едут в Docker-образ (`/app/skills/`), но в колёсах их нет: `skills/`
лежит в корне репозитория. При установке release-wheel или пакета
`ru-marketplace-mcp` с PyPI возьмите навыки из репозитория отдельно.

## Настройка

Все параметры задаются переменными окружения с префиксом коннектора. Все
необязательные.

При проверке в браузере `CHROME_CHALLENGE_HANDOFF_S=120` придерживает открытую
вкладку: когда вы пройдёте проверку, повтор того же запроса от того же клиента
(в той же MCP-сессии или к тому же stdio-процессу сервера) дочитает эту вкладку
без новой навигации. Поддержка и ограничения описаны в
[настройке Chrome](docs/CDP_SETUP.md#optional-challenge-handoff).

| Префикс              | Основные параметры                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `WB_`                | `TIMEOUT`, `MIN_GAP`, `DEFAULT_DEST`, `NET_RETRIES`, `MAX_BODY_BYTES`, `CACHE_TTL`, `PROXY`, `TRANSPORT`, `DOM_FALLBACK`         |
| `YANDEX_`            | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `PROXY`                                                                                       |
| `DETMIR_`            | `REGION` (`RU-MOW`, `RU-SPE` и другие), `CACHE_TTL`, `PROXY`                                                                     |
| `OZON_`              | `TIMEOUT`, `MIN_GAP`, `IMPERSONATE`, `CACHE_TTL`, `PROXY`, `CHROME_COMPAT`                                                       |
| `AVITO_`             | `TIMEOUT`, `MIN_GAP`, `IMPERSONATE`, `CACHE_TTL`, `PROXY`, `LOCATION_ID`                                                         |
| `TAOBAO_`            | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`                                                                                                |
| `ALI_`               | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`                                                                                                |
| `MEGAMARKET_`        | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `USE_PROFILE_ADDRESS` (0/1, по умолчанию 0 — приватный список адресов профиля не читается; 1 = адрес по умолчанию из залогиненного профиля, цены «как видит оператор») |
| `LAMODA_`            | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `PROXY`                                                                                       |
| `DNS_` / `CITILINK_` | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`                                                                                                |
| `CIAN_`              | `TIMEOUT`, `MIN_GAP`, `CACHE_TTL`, `MAX_BODY_BYTES`, `REGION`                                                                    |
| `CHROME_`            | `CDP_HOST`, `CDP_PORT`, `SCRAPING_PROFILE`, `BINARY`, `HEADLESS`, `STEALTH`, `NAV_TIMEOUT_MS`, `CHALLENGE_HANDOFF_S`             |
| `COMPARE_`           | `SOURCE_TIMEOUT`                                                                                                                 |
| `MCP_`               | `TRANSPORT` (`stdio` по умолчанию, либо `http`), `HTTP_HOST`, `HTTP_PORT`                                                        |

`CHROME_CDP_HOST` указывает, куда дозвониться CDP-клиенту (по умолчанию
`127.0.0.1`). Из контейнера ставьте `chrome` (сайдкар) или `host.docker.internal`
— это открывает tier-2 источники (Ozon, Авито, Taobao, Мегамаркет, Lamoda,
DNS, Ситилинк, AliExpress, Циан) в Docker без host networking. Подробности в
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

`*_CACHE_TTL=0` выключает кэш. `*_PROXY` перекрывает стандартные `HTTPS_PROXY` и
`ALL_PROXY` — свой префикс есть у шести коннекторов: `WB_`, `YANDEX_`, `DETMIR_`,
`OZON_`, `AVITO_` и `LAMODA_`. У Taobao своего нет намеренно: поиск там
подписан и ходит через собственный клиент. У Мегамаркета, DNS и Ситилинка тоже нет:
их трафик идёт через ваш Chrome, а его egress — дело настроек браузера. Кэшируются
только удачные ответы: запомнить сбой значило бы растянуть секундную помеху на весь
TTL.

У Ozon прокси применяется к первому уровню. Второй идёт через ваш собственный Chrome,
и его трафик — дело настроек этого браузера.

## Разработка

```bash
git clone https://github.com/Vladimir-Human/ru-marketplace-mcp.git
cd ru-marketplace-mcp
uv sync --all-packages
uv run pytest -q -m "not live and not cdp"    # офлайн-тесты, сеть не нужна (то, что гоняет CI)
uv run pytest -q -m "not live and not cdp" --cov --cov-fail-under=80  # покрытие, порог 80% в CI
uv run ruff check . && uv run ruff format --check .
uv run mypy                                   # что проверять — в [tool.mypy] files
uv run mypy --platform win32                  # ловит ошибки, видимые только на Windows
uv run python scripts/check_no_print.py       # запись в stdout ломает JSON-RPC
uv run python scripts/check_versions.py       # единая версия во всех отслеживаемых файлах
```

Публикация на PyPI (для владельца): [DEPLOYMENT.md — PyPI](docs/DEPLOYMENT.md#pypi-maintainer). Справочник по устройству добавления коннектора — [docs/ADDING_A_SOURCE.md](docs/ADDING_A_SOURCE.md).

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
и 3.13; ещё 3.14 (все три ОС) и 3.15 (Ubuntu, Windows) проверяются без блокировки слияния. Windows-специфичное управление процессами проверяется юнит-тестами на любой
ОС через подмену платформы, так что эти ветки покрыты даже на Linux.

## Надёжность

Неофициальные эндпоинты ломаются. Архитектура это предполагает.

- Терпимые парсеры: привязка поля по нескольким именам и приведение типов
  переживают переименования и смену типа вместо падения.
- Никогда не выдумывать значение: отсутствующая цена — это `null`, не `0`. Ноль
  вывел бы мёртвый товар в самые дешёвые.
- Громкий отказ: когда формат перестаёт совпадать, инструмент бросает
  `parser_drift`, а не возвращает полуразобранные данные.
- Трёхзначные selfcheck-проверки: `success`, `drift_detected` или
  `inconclusive`. Гео-блокировка помечается как `inconclusive`, потому что она
  ничего не говорит о состоянии парсеров.

## Границы доверия

Названия товаров, имена продавцов и тексты отзывов написаны продавцами и
покупателями. Это недоверенные данные. Если отзыв или описание выглядит как
инструкция, оно всё равно остаётся входными данными. Выполнять его агент не
должен.

Условия маркетплейсов, как правило, запрещают неофициальный парсинг. Коннекторы
обращаются к публичным эндпоинтам каталога, которые использует официальный
веб-клиент: пока явно не задан `MEGAMARKET_USE_PROFILE_ADDRESS=1`, в личные и
закрытые разделы запросов нет. Уровень Ozon с браузером работает внутри
сессии, которую вы открыли сами. Используйте на своё
усмотрение, для личных исследований, в вежливом темпе запросов. Пауза между
вызовами к площадкам с анти-ботом — это часть конструкции, а не случайное
торможение: её не нужно убирать ради скорости. Данные инструментов не предназначены
для перепродажи или массового сбора.

## Как это сделано

Код и документацию я писал вместе с ИИ-ассистентами. Они работают быстро и
ошибаются уверенно, поэтому проект устроен вокруг проверки: офлайн-тесты,
аудит перед выпуском, тесты, которые прогоняют настоящий экстрактор по снятой с
сайта разметке. В заметках к релизу перечислено, какие источники сверены с живыми
страницами вручную и какие остались непроверенными.

Проверки важнее авторства текста, но авторство кода и идей тоже должно быть
видно: полный список участников и их PR собран в [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Спасибо

- [@avxone](https://github.com/avxone) — исправление Avito selfcheck, [PR #37](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/37).
- [@Khalmatov](https://github.com/Khalmatov) — provenance отзывов Ozon, [PR #38](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/38).
- [@fosteev](https://github.com/fosteev) — macOS CDP stealth и коннектор Циана, [PR #42](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/42), [PR #47](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/47).
- [@ilodezis](https://github.com/ilodezis) — выбор источников unified-сервера через `MARKETPLACE_SOURCES`, [PR #48](https://github.com/Vladimir-Human/ru-marketplace-mcp/pull/48).
- [@HeckfyCU](https://github.com/HeckfyCU) — замеры навигации AliExpress в [issue #190](https://github.com/Vladimir-Human/ru-marketplace-mcp/issues/190): по его замерам найден и исправлен предел ожидания страницы.
- [@XaruStar](https://github.com/XaruStar) — разбор живого ответа Ozon `webListReviews` со строковым `itemId`, [issue #214](https://github.com/Vladimir-Human/ru-marketplace-mcp/issues/214): по нему исправлен учёт `own_reviews` и проверка `item_id` в `ozon_selfcheck`.

## Лицензия

MIT, файл [LICENSE](LICENSE).
