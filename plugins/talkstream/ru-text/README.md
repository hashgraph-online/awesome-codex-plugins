# ru-text

[![Version](https://img.shields.io/github/v/release/talkstream/ru-text?label=version&color=2ea44f)](https://github.com/talkstream/ru-text/releases/latest) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Platforms](https://img.shields.io/badge/platforms-12-blue)](#быстрый-старт) [![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue?logo=anthropic)](https://github.com/anthropics/claude-plugins-community) [![GitHub Sponsors](https://img.shields.io/badge/Sponsor-30363D?logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/talkstream) [![GitHub stars](https://img.shields.io/github/stars/talkstream/ru-text?style=flat&label=stars)](https://github.com/talkstream/ru-text/stargazers) [![Last commit](https://img.shields.io/github/last-commit/talkstream/ru-text/main?label=updated)](https://github.com/talkstream/ru-text)

**Языки:** Русский | [English](README.en.md)

> 🌍 **Reading in English?** This page is in Russian on purpose — ru-text is a tool for Russian text quality, so its home page speaks Russian first. You're very welcome here, and the **full English version is one click away → [README in English](README.en.md)**. Everything below is mirrored there.

**Плагин для Claude Code, Codex, Notion, Cursor, GitHub Copilot и [ещё 7 платформ](#быстрый-старт) — качество русского текста** — типографика, информационный стиль, редактура, UX-тексты и деловая переписка.

~1 044 авторских правил, основанных на изучении 16 канонических русскоязычных источников. Все формулировки оригинальные — без дословного цитирования, с полной атрибуцией.

## Благодарности

Этот плагин существует потому, что несколько человек решили: русский текст в интернете заслуживает лучшего. Они написали книги, создали инструменты, поддерживали гайды и задали стандарты, на которые сегодня опираются тысячи редакторов, авторов и дизайнеров. Их работа изменила то, как пишут, оформляют и читают русский текст на экранах. Я глубоко благодарен каждому из них. Если этот плагин сэкономит вам время — пожалуйста, купите их книги и пользуйтесь их инструментами. Они это заслужили.


## Что делает плагин

ru-text даёт вашему ИИ-ассистенту глубокое понимание качества русского текста. Плагин активируется автоматически при создании или редактировании текста на русском: типографика применяется мгновенно, доменные справочники подгружаются по мере необходимости.

Работает с Claude Code (CLI и Desktop), Codex CLI, Notion, Cursor, GitHub Copilot, Gemini CLI, Google Antigravity, Windsurf, Continue.dev, Cline, JetBrains (Junie) и OpenClaw.

- **~1 044 правил** в 7 доменах, упакованных в 9 справочных файлов + дополнения
- **Автоактивация** — не нужно помнить о включении
- **Полное покрытие** — от длинного тире и кавычек-ёлочек до UX-микрокопирайтинга и тона деловой переписки
- **Не догма** — ваш явный запрос стиля всегда приоритетнее правил по умолчанию

## Сценарии использования

**Этот README.** Каждое тире, кавычка и пробел в этом документе соответствуют правилам самого плагина. Текст написан с подключённым ru-text.

**UX-микрокопирайтинг.** Пишете кнопки, ошибки, пустые состояния для русскоязычного приложения. Плагин подгружает 217 UX-правил: «Отмена» вместо «Нет», структура ошибок (что случилось + что делать), плейсхолдеры как примеры, а не инструкции.

**Деловое письмо.** Набрасываете email коллегам или клиентам. Плагин убивает канцелярит («довожу до сведения» → «сообщаю»), структурирует тему + первое предложение + призыв к действию, подсказывает уважительный тон без заискивания.

**Текст для лендинга.** Пишете блок «О компании» для IT-студии. Плагин заменяет штампы («команда профессионалов», «индивидуальный подход») на конкретные факты и цифры.

**README и документация.** Пишете документацию для open-source проекта на русском. Правильная типографика (ёлочки, тире, неразрывные пробелы), ясная структура «перевёрнутой пирамиды».

**Вычистка нейрослопа.** Текст похож на сгенерированный. Плагин ловит характерные приметы машинного текста: ложную антитезу («не X, а Y» без посылки), непрошенную самопохвалу («чётко, по делу, без воды»), сервисные реплики ассистента («Отличный вопрос!», «Надеюсь, помог») и пустые зачины («давайте разберёмся», «погрузимся»).

**Оценка качества текста.** Хотите знать, насколько хорош ваш текст? `/ru-text:ru-score` оценивает текст по 5 измерениям (типографика, чистота языка, грамотность, структура, точность для читателя) и возвращает балл от 0 до 10 с конкретными замечаниями по каждому измерению.

**Качество ИИ-агентов.** Встраиваете ИИ-инструменты в продукт и не уверены, как именно ответит агент на русском? ru-text гарантирует предсказуемо высокое качество текста от любого Claude-агента: единообразная типографика, никакого канцелярита, структура от читателя.

## Быстрый старт

Разделы упорядочены по популярности платформ среди разработчиков с ИИ-ассистентами на апрель 2026 года.

### Claude Code (CLI)

```bash
# Добавить community marketplace (один раз)
/plugin marketplace add anthropics/claude-plugins-community

# Установить плагин
/plugin install ru-text@claude-community
```

Опубликован в [community-маркетплейсе Claude Code](https://github.com/anthropics/claude-plugins-community). Размещение в [официальном маркетплейсе Anthropic](https://claude.com/plugins) запланировано.

### Claude Code (Desktop)

Команды установки те же, что и для CLI: откройте поле `/plugin` в приложении Claude Desktop и выполните две команды выше. Одна установка работает сразу в CLI, Desktop, VS Code, JetBrains и Web.

### Codex CLI

В сессии Codex используйте интерактивный браузер плагинов:

```
/plugins
```

Найдите «ru-text» и установите. Или используйте универсальный skills CLI (см. ниже).

### Notion

Два способа интеграции — подробности в [notion/README.md](notion/README.md):

**Навык Notion AI** (автономный, тариф Business/Enterprise):
1. Скопируйте [шаблон-страницу](notion/ru-text-notion-skill.md) в Notion
2. Назначьте страницу навыком AI
3. Выделите текст и вызовите «ru-text» из меню AI

**Notion через MCP** (с Claude Code, любой тариф):
1. Установите ru-text в Claude Code
2. Подключите [Notion MCP-сервер](https://developers.notion.com/guides/mcp/get-started-with-mcp)
3. Попросите Claude Code прочитать, проверить и обновить страницы Notion

### Cursor

Используйте команду плагинов в чате Cursor Agent:

```
/add-plugin
```

Найдите «ru-text» и установите. Если плагин не найден в маркетплейсе, скопируйте вручную:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text ~/.cursor/skills/ru-text
```

Windows (PowerShell):

```powershell
git clone https://github.com/talkstream/ru-text.git
Copy-Item -Recurse ru-text\skills\ru-text "$env:USERPROFILE\.cursor\skills\ru-text"
```

### GitHub Copilot

Если ru-text уже установлен для Claude Code в вашем проекте, Copilot обнаружит его автоматически. Иначе:

```bash
npx skills add talkstream/ru-text
```

Или скопируйте вручную:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text .github/skills/ru-text
```

Работает в VS Code, Visual Studio и JetBrains IDE с Copilot.

### Gemini CLI

```bash
gemini extensions install https://github.com/talkstream/ru-text
```

### Google Antigravity

Antigravity читает формат SKILL.md нативно. Скопируйте навык в глобальную папку навыков — он станет доступен во всех проектах:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text ~/.gemini/antigravity/skills/ru-text
```

Для конкретного проекта скопируйте навык в `<проект>/.agent/skills/ru-text`. Antigravity молод, и путь к навыкам зависит от версии — актуальный смотрите в [официальном codelab по навыкам Antigravity](https://codelabs.developers.google.com/getting-started-with-antigravity-skills).

### Windsurf

```bash
npx skills add talkstream/ru-text
```

Или скопируйте вручную:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text .windsurf/skills/ru-text
```

Вызов через `@ru-text` в чате Cascade. Также доступен через панель Cascade > Customizations > Skills.

### Continue.dev

Если ru-text уже установлен для Claude Code в вашем проекте, Continue обнаружит его автоматически. Иначе:

```bash
npx skills add talkstream/ru-text
```

Или скопируйте вручную:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text .continue/skills/ru-text
```

Работает в расширениях для VS Code и JetBrains.

### Cline

Если ru-text уже установлен для Claude Code в вашем проекте, Cline обнаружит его автоматически. Иначе:

```bash
npx skills add talkstream/ru-text
```

Или скопируйте вручную:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text .cline/skills/ru-text
```

Включите навыки в настройках Cline: Features > Enable Skills.

### JetBrains (Junie)

```bash
npx skills add talkstream/ru-text
```

Или скопируйте вручную:

```bash
git clone https://github.com/talkstream/ru-text.git
cp -r ru-text/skills/ru-text .junie/skills/ru-text
```

Работает в IntelliJ IDEA, PyCharm, WebStorm, GoLand, PhpStorm, RubyMine, RustRover, Rider, CLion и Android Studio.

### OpenClaw

```bash
openclaw skills install ru-text
```

Доступен на [ClawHub](https://clawhub.ai/talkstream/ru-text). Работает с любым LLM-провайдером и каналом, который поддерживает OpenClaw.

### Любая платформа через skills CLI

```bash
npx skills add talkstream/ru-text
```

### Из исходников

```bash
git clone https://github.com/talkstream/ru-text.git
```

Затем добавьте репозиторий как источник плагинов по документации вашей платформы.

Начните писать на русском — плагин подключится сам. Если ru-text делает ваши продукты лучше, поддержите [разработку](https://github.com/sponsors/talkstream).

## Обновление

Свежая версия — **v1.10.0** (что нового — в [CHANGELOG](CHANGELOG.md)). Узнать свою версию в Claude Code: `claude plugins list`.

**Основной способ** — для платформ на основе навыков (GitHub Copilot, Windsurf, Continue.dev, Cline, JetBrains Junie, Google Antigravity, ручная установка в Cursor). Повторите установку — команда подтянет последнюю версию из репозитория и перезапишет навык:

```bash
npx skills add talkstream/ru-text
```

**Claude Code (CLI и Desktop).** Сначала обновите кэш маркетплейса, затем плагин:

```bash
claude plugins marketplace update claude-community
claude plugins update ru-text@claude-community
```

Перезапустите Claude Code (или выполните `/reload-plugins`), чтобы изменения вступили в силу. То же самое можно сделать в меню `/plugin`, вкладка «Installed». Важно: community-маркетплейс закрепляет плагин на конкретной версии и подтягивает свежую с задержкой до суток — если сразу после релиза версия не сменилась, это нормально, дайте маркетплейсу обновить закрепление.

**Gemini CLI:**

```bash
gemini extensions update ru-text
```

**OpenClaw:**

```bash
openclaw skills update ru-text
```

**Codex CLI.** Откройте `/plugins`, найдите ru-text и обновите.

**Ручное копирование.** Если вы устанавливали навык вручную (`git clone` + `cp`), повторите шаги установки своей платформы — они перезапишут навык свежей версией.

## Домены

| Домен | Правил | Что покрывает |
|---|---|---|
| Типографика | 96 | Кавычки (ёлочки, лапки), тире, неразрывные пробелы, разрядка чисел, спецсимволы, сокращения |
| Информационный стиль | 197 | Стоп-слова (92 записи), структура текста, факты вместо оценок, регистр, редполитика Т–Ж |
| Редактура: пунктуация | 88 | Сложные предложения, 56 запятых-ловушек, вводные слова, точка с запятой |
| Редактура: грамматика | 171 | Заглавные буквы, согласование, 50+ плеоназмов, оформление списков, принципы чистого языка |
| UX-тексты | 217 | 58 надписей на кнопках, ошибки, пустые состояния, формы, уведомления, диалоги, онбординг |
| Деловая переписка | 128 | Структура писем, этикет мессенджеров, тон, 41 паттерн чистых формулировок, заметки к встречам |
| Антипаттерны | 138 | Пары «неправильно — правильно», сгруппированные по серьёзности: канцелярит, пассивный залог, многословие |

## Команды

| Команда | Описание |
|---|---|
| `/ru-text` | Активировать навык вручную (в большинстве случаев достаточно автоактивации) |
| `/ru-text:ru-check` | Запустить комплексную проверку качества текста |
| `/ru-text:ru-score` | Оценить качество текста по шкале 0–10 в 5 измерениях |

## Приоритет стиля

Если вы явно запрашиваете определённый стиль — разговорный, академический, SEO, литературный, юридический — ваш запрос приоритетнее правил по умолчанию. Плагин задаёт качественные настройки, а не жёсткие требования.

## Техническое качество

Собран по спецификациям плагинов Claude Code от Anthropic:
- SKILL.md: 587 слов, 90 строк (рекомендация: до 2 000 слов, до 500 строк)
- 9 справочных файлов загружаются по запросу, не при старте сессии
- ~1 044 правил, разбитых на 7 тематических блоков с прогрессивным раскрытием

## Уведомление об интеллектуальной собственности

Данный плагин является самостоятельным авторским произведением Арсения Камышева.

Правила и принципы, содержащиеся в плагине, представляют собой личное
понимание автором стандартов русской типографики, редактуры и текста,
сформированное за годы профессиональной практики и изучения опубликованных
источников, перечисленных ниже.

Все формулировки оригинальны. Ни один текст не цитируется дословно.
Лежащие в основе принципы (правила типографики, нормы грамматики, методы
редактуры) не являются объектами авторского права в силу ст. 1259(5) ГК РФ,
17 USC §102(b) и Бернской конвенции.

Авторы и издатели перечисленных источников не одобряли, не рецензировали
и не утверждали данный плагин. Ссылки на источники приводятся для удобства
читателя и дальнейшего изучения.

Названия продуктов являются товарными знаками соответствующих
правообладателей и используются исключительно в информационных целях.

## Дорожная карта

Следующие направления развития ru-text:

- **Telegram-бот** — проверка качества текста и /ru-score через Telegram
- **Расширение для браузера** — проверка русского текста в любом текстовом поле (Chrome, Firefox)
- **Плагин для WordPress** — типографика и оценка качества в редакторе Gutenberg

Идеи и предложения приветствуются — [создайте issue](https://github.com/talkstream/ru-text/issues) или [начните обсуждение](https://github.com/talkstream/ru-text/discussions).

## Источники и благодарности

### Типографика

| # | Источник | Вклад | Ссылка |
|---|---|---|---|
| 1 | **Артём Горбунов «Типографика и вёрстка»** (2017) | Базовые правила типографики: тире, кавычки, пробелы, экранная типографика | [bureau.ru/projects/book-typography/](https://bureau.ru/projects/book-typography/) |
| 2 | **Бюро Горбунова «Советы»** (2005–н. в., 4809+ советов) | Практические микросоветы по типографике, редактуре, дизайну | [bureau.ru/soviet/](https://bureau.ru/soviet/) |
| 3 | **А. Э. Мильчин, Л. К. Чельцова «Справочник издателя и автора»** (2021, 6-е изд.) | Пунктуация, сокращения, оформление чисел, редакционные конвенции | [store.artlebedev.com](https://store.artlebedev.com) |
| 4 | **Илья Бирман — Типографическая раскладка** (2007–н. в.) | Клавиатурная раскладка для набора типографически корректных символов | [ilyabirman.ru/typography-layout/](https://ilyabirman.ru/typography-layout/) |
| 5 | **Type.today — Журнал** (2016–н. в.) | Кириллический шрифтовой дизайн, подбор шрифтовых пар, удобочитаемость | [type.today](https://type.today) |

### Информационный стиль и ясное письмо

| # | Источник | Вклад | Ссылка |
|---|---|---|---|
| 6 | **Максим Ильяхов «Пиши, сокращай»** (2017, обн. 2025) | Основа инфостиля: удаление воды, борьба с канцеляритом, письмо от читателя | [book.glvrd.ru](https://book.glvrd.ru) |
| 7 | **Максим Ильяхов «Ясно, понятно»** (2019) | Продвинутый инфостиль: структура текста, убеждение, визуально-текстовая интеграция | [book.glvrd.ru](https://book.glvrd.ru) |
| 8 | **Редполитика Т–Ж** (2017–н. в., 56+ страниц) | Тон, форматирование, числа, стандарты делового письма | [journal.tinkoff.ru/manual/](https://journal.tinkoff.ru/manual/) |
| 9 | **Контур — Гайды** (2020–н. в.) | UX-тексты для B2B-софта: интерфейсные тексты, ошибки, онбординг | [guides.kontur.ru](https://guides.kontur.ru) |
| 10 | **Яндекс — Gravity UI** (2023–н. в.) | Дизайн-система с гайдлайнами для русскоязычных UI-текстов | [gravity-ui.com](https://gravity-ui.com) |

### Язык и письмо

| # | Источник | Вклад | Ссылка |
|---|---|---|---|
| 11 | **М. Ильяхов, Л. Сарычева «Новые правила деловой переписки»** (2018) | Структура писем, уважительный тон, этикет мессенджеров | [book.glvrd.ru](https://book.glvrd.ru) |
| 12 | **Нора Галь «Слово живое и мёртвое»** (1972, переиздания) | Первоисточник критики канцелярита, злоупотребления номинализацией, пассивного залога | [lib.ru](http://lib.ru/TRANSLATORS/NORA_GAL/slowo.txt) |
| 13 | **Д. Э. Розенталь — Справочники по правописанию** (1960-е–2000-е) | Авторитетная база по грамматике, пунктуации, орфографии | широко доступны |
| 14 | **Артемий Лебедев «Ководство»** (1998–н. в.) | Экранная типографика, тире и кавычки, читаемость дизайн-текста | [artlebedev.ru/kovodstvo/](https://www.artlebedev.ru/kovodstvo/) |
| 15 | **Ozon — UX Writing Practices** (2021–н. в.) | UX-тексты в масштабе: кнопки, уведомления, ошибки, продуктовые тексты | [habr.com](https://habr.com/ru/companies/ozontech/articles/821383/) |
| 16 | **ГОСТ Р 7.0.12-2011, ГОСТ 7.12-93** (Росстандарт) | Официальные стандарты библиографических сокращений | базы ГОСТ |

### Онлайн-инструменты

- **Главред** ([glvrd.ru](https://glvrd.ru)) — проверяет текст на качество инфостиля, подсвечивает воду, оценивает от 0 до 10
- **Типограф Лебедева** ([typograf.artlebedev.ru](https://www.artlebedev.ru/typograf/)) — автоматически исправляет типографику: кавычки, тире, неразрывные пробелы
- **Орфограммка** ([orfogrammka.ru](https://orfogrammka.ru)) — проверка грамматики, орфографии и пунктуации

## Автор

**Арсений Камышев** — [nafigator@gmail.com](mailto:nafigator@gmail.com) — [Telegram](https://t.me/nafigator) — [GitHub](https://github.com/talkstream)

## Поддержка

Я всю жизнь занимаюсь социальными проектами. В этой сфере я максимально эффективен для людей и общества, поэтому **всегда** нуждаюсь в финансовой поддержке. Если ru-text делает ваши продукты лучше, поддержите меня через [GitHub Sponsors](https://github.com/sponsors/talkstream).

## Лицензия

[MIT](LICENSE) | [Политика конфиденциальности](PRIVACY_POLICY.md)
