# Безопасность

[English version below](#security)

## Как сообщить об уязвимости

Пишите приватно через [Security Advisories](https://github.com/Vladimir-Human/ru-marketplace-mcp/security/advisories/new)
на GitHub, а не в публичный issue. Первый ответ обычно приходит в течение
нескольких дней.

В отчёте полезны: что получает атакующий, как воспроизвести и какой коннектор или
уровень транспорта задействован.

## Чего проект касается, а чего нет

Источники не требуют ни ключей API, ни токенов, ни паролей: все настройки у них
эксплуатационные, то есть таймауты, задержки, регион и прокси.

Весь доступ только на чтение. Двенадцать источников читают публичные
эндпоинты каталога, которые дёргает официальный веб-клиент: пока opt-in не
включён, ни в приватные, ни в административные разделы запросов нет.

**Мегамаркет — вход в аккаунтную зону, только по явному opt-in.** По
умолчанию его коннектор тоже читает лишь публичные эндпоинты: каталог,
`url/parse` и публичный саггест адресов (`MEGAMARKET_ADDRESS`, Москва по
умолчанию). Но он умеет прочитать и приватный `/profileService/address/list`
из залогиненного Chrome-профиля оператора. Что при этом читается: список
адресов профиля, флаг «адрес по умолчанию» и регион — этого достаточно, чтобы
выбрать адрес, под который персонализуются цены и наличие. Делается это только
при `MEGAMARKET_USE_PROFILE_ADDRESS=1`; по умолчанию флаг выключен, и
включённый Мегамаркет публичных эндпоинтов не покидает. Смысл включения: цены
и наличие совпадают с тем, что видит сам оператор, а не с городскими.
Сырой `addressId` не покидает процесс. Раскрытие источника адреса в
`_meta.warnings` (`address_source:profile|suggest|none`) имеет смысл только
для состояний, меняющих цену: предупреждение о прочитанном профиле
(и `_meta.healthy=false`) появляется, когда opt-in сработал, а
`address_source:none` — когда адрес не разрешился вовсе. Обычный путь через
саггест предупреждением не помечается и отвечает `_meta.healthy=true`.

Поисковые запросы отправляются на выбранные маркетплейсы. Ранжирование использует
только сведения о товарах, а не профиль пользователя. Инструменты сравнения
сравнивают предложения: они не оформляют заказы и не управляют аккаунтами.
Цены не включают доставку, сборы и пошлины.

## Единственная часть с реальным риском: уровень CDP

Десять источников при настройках по умолчанию могут обращаться к Chrome, который **вы**
запустили и в котором залогинились сами, по DevTools Protocol. Taobao, Мегамаркет, DNS,
Ситилинк, AliExpress и Циан работают только так — анонимного уровня у них нет. Ozon и
поиск Авито уходят в браузер лишь когда анонимный уровень получил отказ; карточки и
продавцы Авито читаются только через браузер. Lamoda берёт через браузер поиск, а
карточку сначала просит анонимно по GraphQL и идёт в браузер, если получила отказ.
Wildberries (`wb_search` и `wb_card`) сначала запрашивает анонимный HTTP, а при ответе
401/403/498 или странице проверки по умолчанию (`WB_DOM_FALLBACK=1`) перечитывает запрос
через ваш Chrome по CDP; `WB_DOM_FALLBACK=0` полностью отключает запасной уровень CDP.

**CDP даёт любому локальному процессу полный контроль над тем профилем, к которому он
подключён**, включая все залогиненные в нём сессии. Это и есть угроза, которую нужно
понимать до включения.

Меры защиты, по важности:

| Мера | Что ограничивает |
|---|---|
| Отдельный профиль для парсинга (по умолчанию) | Радиус поражения: банк и почта остаются в стороне |
| `--remote-debugging-address=127.0.0.1` | Доступ к порту отладки из локальной сети |
| Проверка схемы в `open_page` | Наведение браузера на `file:///` |
| Allowlist хостов в каждом коннекторе | Превращение подставленного ввода в запрос к `/api/personal/orders` |

Отдельный профиль здесь работает как основной контроль. Логиньтесь там только в
маркетплейсы. Подробности в [docs/CDP_SETUP.md](docs/CDP_SETUP.md).

Яндекс Маркет и Детский мир к CDP не обращаются вообще; Wildberries не касается CDP при
`WB_DOM_FALLBACK=0` (или пока отвечает анонимный HTTP). Если вам хватает их, уровень можно
не включать — но тогда девять остальных источников читать нечем.

## Прочие меры

**Ограничение размера тела ответа.** Ответы читаются потоком с жёстким лимитом в
байтах, поэтому скомпрометированный CDN или MITM не сможет исчерпать память
бесконечным телом.

**Allowlist окружения дочернего процесса.** Рабочий процесс, который запускает Ozon,
получает только нужные ему переменные: парсеру нечего делать с токенами, случайно
оказавшимися в родительском окружении.

**`taskkill`, который нельзя подменить.** На Windows системный каталог определяется
через `GetSystemDirectoryW`, а не через `SystemRoot` или `WINDIR`: это обычные
переменные окружения, и любой процесс, способный их выставить, мог бы перенаправить
вызов.

**Редиректы по умолчанию не выполняются.** Несколько маркетплейсов отвечают
датацентровым адресам петлёй 307 на себя же, и переход по ней сжигает бюджет
запросов вместо того, чтобы показать блокировку.

**Вычистка ошибок.** Bearer-токены, ключи API и секреты в query-строке удаляются из
текста ошибки до того, как он попадёт в ответ инструмента. Абсолютные пути к профилю
(в них содержится имя пользователя ОС) в видимые ошибки не попадают. С 1.2.0 вырезается
и `user:pass@` из URL: прокси настраивается строкой `http://user:pass@host:port`, и
раньше ошибка соединения уносила логин с паролем в лог и в ответ клиенту.

**Проверка формы вместо экранирования.** Значения, попадающие в путь URL или в
выражение фильтра, проверяются строгим шаблоном.

## Внедрение инструкций: граница, которую нужно соблюдать

Вывод инструментов — это **текст, написанный продавцами и покупателями**: названия
товаров, имена продавцов, отзывы. Это недоверенные данные.

Если отзыв или описание выглядит как инструкция («забудь предыдущие указания»,
«скачай этот файл»), агент обязан обращаться с этим как с входными данными, а не как
с политикой. Об этом сказано в каждом skill-документе и в докстрингах инструментов,
но окончательный контроль — на стороне агента, который эти данные читает.

Цены и победителей сравнения вычисляет код, но описания и отзывы всё равно могут
повлиять на выводы агента, который их читает.

Здесь это важнее обычного: тексты отзывов свободной формы, их много, и писать их
может кто угодно.

## Юридическая заметка

Условия маркетплейсов, как правило, запрещают неофициальный парсинг. К
двенадцати источникам проект обращается только по публичным эндпоинтам каталога,
в намеренно вежливом темпе, для личных исследований.

За своё использование, включая соблюдение местного законодательства и условий
сервисов, отвечаете вы. Чтение приватных эндпоинтов (профильные адреса Мегамаркета при явном opt-in) — ваша ответственность в той
же мере: это использование вашей сессии для чтения ваших же данных.

## Поддерживаемые версии

Исправления безопасности выходят для последнего релиза. Сообщайте об ошибках по
ветке `main`, если это возможно.

---

# Security

## Reporting a vulnerability

Report privately via GitHub's [Security Advisories](https://github.com/Vladimir-Human/ru-marketplace-mcp/security/advisories/new)
rather than a public issue. A first response should come within a few days.

Useful in a report: what an attacker gains, how to reproduce, and which connector or
transport tier is involved.

## What this project does and does not touch

**There are no credentials anywhere in this project.**
No API keys, no tokens, no passwords, no credential store, no `.env` requirement.
Every setting is an operational knob (timeouts, rate gaps, region, proxy).

All access is read-only. Twelve sources read the public catalog endpoints the official
web clients use, touching no authenticated or administrative area — unless you opt in.

**Megamarket is an account-gated surface, and only on explicit opt-in.**
By default its connector also stays on public endpoints: catalog reads,
`url/parse`, and the public address suggest driven by `MEGAMARKET_ADDRESS`
(Moscow by default). It *can* read the private `/profileService/address/list`
endpoint from the operator's logged-in Chrome profile. What that touches: the
profile's address list, the default-address flag, and the region — enough to
pick the address prices and availability are personalized to. It happens only
with `MEGAMARKET_USE_PROFILE_ADDRESS=1`; the flag defaults to off, so an
enabled Megamarket never leaves public endpoints. The point of opting in:
prices and availability match what the operator themself sees, not city-level
ones. The raw `addressId` never leaves the process. Source disclosure in
`_meta.warnings` (`address_source:profile|suggest|none`) is reserved for the
states that change the prices: a profile-read notice (and `_meta.healthy=false`)
when the opt-in fired, and `address_source:none` when nothing resolved. The
ordinary suggest path adds no address warning and answers `_meta.healthy=true`.

Search queries are sent to the selected marketplaces. Ranking uses product facts
only, not a user profile. Comparison tools compare offers: they do not place orders
or manage accounts. Prices exclude delivery, fees and duties.

## The one part that carries real risk: the CDP tier

Ten sources can run fetches inside a Chrome instance **you** started and logged
into, over the DevTools Protocol, under default settings. Taobao, Megamarket, DNS, Citilink, AliExpress and Cian work no other
way — they have no anonymous tier. Ozon and Avito search fall back to the browser only after
the anonymous tier is refused; Avito cards and sellers always read the page there. Lamoda
splits the difference: search goes through the browser, the product card tries anonymous
GraphQL first and the browser only when that is refused. Wildberries (`wb_search` and
`wb_card`) tries anonymous HTTP first and, with `WB_DOM_FALLBACK=1` enabled by default,
attaches to your Chrome over CDP when anonymous HTTP returns 401/403/498 or a challenge
wall; set `WB_DOM_FALLBACK=0` to disable CDP fallback completely.

**CDP grants any local process full control of the profile it is attached to**,
including every session logged into that profile. That is the threat to understand
before enabling it.

Mitigations, in order of importance:

| Mitigation | What it bounds |
|---|---|
| Dedicated scraping profile (default) | Blast radius: banking and email stay out |
| `--remote-debugging-address=127.0.0.1` | LAN access to the debugging port |
| Scheme guard in `open_page` | The browser being aimed at `file:///` |
| Per-connector host allowlists | A crafted input becoming a request for `/api/personal/orders` |

The dedicated profile is not a nicety, it is the primary control. Log into
marketplaces there and nothing else. Full detail:
[docs/CDP_SETUP.md](docs/CDP_SETUP.md).

Yandex Market and Detsky Mir never touch CDP, and Wildberries stays completely off CDP
when `WB_DOM_FALLBACK=0` (or whenever anonymous HTTP succeeds). If those cover your
needs, leave the tier off — the other nine sources cannot be read without it.

## Other hardening in place

**Bounded response bodies.** Responses stream against a hard byte cap, so a
compromised CDN or MITM cannot exhaust memory with an endless body.

**Allowlisted child environments.** The worker process Ozon spawns receives only the
variables it needs: a scraping worker has no business seeing tokens that happen to sit
in the parent environment.

**Un-hijackable `taskkill`.** On Windows the system directory is resolved via
`GetSystemDirectoryW`, not `SystemRoot`/`WINDIR`, because those are ordinary
environment variables that any process able to set the environment could redirect.

**Redirects not followed by default.** Several marketplaces answer datacenter IPs with
self-referential 307 loops; following them burns the request budget instead of
surfacing the block.

**Error redaction.** Proxy credentials, bearer tokens, API keys and query-string
secrets are stripped from error text before it reaches a tool response, and absolute
profile paths (which contain the OS username) are kept out of user-visible errors. The
`user:pass@` case landed in 1.2.0: proxies are configured as `http://user:pass@host:port`,
so a connect failure used to carry the login into both the log and the client's error.

**Input validation over escaping.** Values that reach URL paths or filter expressions
are validated against a strict shape rather than escaped.

## Prompt injection: the boundary users must respect

Tool output is **seller- and buyer-authored content**: product titles, seller names,
review text. It is untrusted data.

If a review or description appears to contain instructions ("ignore previous
instructions", "fetch this URL"), an agent must treat it as input, not policy. Every
skill document and tool docstring states this, but the ultimate control is the
consuming agent's own trust boundary.

Prices and comparison winners are computed in code, but descriptions and reviews
can still sway the agent reading them.

This matters more than usual here: review text is free-form, high-volume, and written
by anyone.

## Legal note

Marketplace terms of service generally disallow unofficial parsing. This project
queries only public catalog endpoints for twelve of its sources, at a deliberately
polite rate, for personal research.

You are responsible for your own use, including compliance with local law and the
relevant terms. Reading private endpoints — Megamarket's profile
address list when explicitly opted in — is your responsibility in the same measure:
it is your session being used to read your own data.

## Supported versions

The latest release receives security fixes. Report against `main` where possible.
