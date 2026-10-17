# Russian Text Anti-Patterns

Catalog of common mistakes organized by severity. Format: wrong|correct.

## Contents
- [Critical: Typography (15 entries)](#critical-typography-15-entries)
- [Critical: Канцелярит и номинализация (32 entries)](#critical-канцелярит-и-номинализация-32-entries)
- [High: Vague Adjectives (11 entries)](#high-vague-adjectives-11-entries)
- [High: Passive Voice (10 entries)](#high-passive-voice-10-entries)
- [High: Sentence Bloat (15 entries)](#high-sentence-bloat-15-entries)
- [Medium: False Intensifiers (11 entries)](#medium-false-intensifiers-11-entries)
- [Medium: Tautology/Pleonasm (22 entries)](#medium-tautologypleonasm-22-entries)
- [Low: Anglicisms (11 entries)](#low-anglicisms-11-entries)
- [Low: Archaic (6 entries)](#low-archaic-6-entries)
- [Low: Overly Formal (5 entries)](#low-overly-formal-5-entries)
- [Summary](#summary)

## Critical: Typography (15 entries)

Full typography rules: see [typography.md](typography.md). Top 5 most frequent crimes:

Wrong|Correct
"кавычки" (straight)|«кавычки» (guillemets «ёлочки»)
Дефис вместо тире: "Москва - столица"|Москва -- столица (em-dash)
Три точки "..."|Многоточие … (U+2026, single glyph)
Знак номера: "No." или "#"|№ (знак номера)
ЭТО НУЖНО СДЕЛАТЬ СЕГОДНЯ, ИНАЧЕ РЕЛИЗ СОРВЁТСЯ|Обычный регистр; одно-два слова прописными не трогать — правило и его карв-ауты в AD-18

Remaining 10: nested quotes (R4), en-dash in ranges (R21–R26), double dashes (R14), space before comma (R40), no space after period (R41), latin x vs multiplication sign (R82), (c) vs © (R87), minus vs em-dash in text (R28) — all in [typography.md](typography.md). ⚠ Two of the ten are NOT in `typography.md` and were claimed to be. **Double spaces** have no rule anywhere in the corpus — they stay as hygiene the Quality Checklist asks for. **Inconsistent ё** is governed, but by [ux-writing.md](ux-writing.md) § L.3–L.5, not here. ⚠ An earlier repair of this sentence said the corpus has no rule for either, and that was the same error one layer down.

## Critical: Канцелярит и номинализация (32 entries)

Bureaucratic constructions and verb-hidden-inside-noun patterns. Anti-bureaucratic tradition: named by K. Chukovsky and N. Gal, operationalized for modern web/info-style by M. Ilyakhov.

Top 5 most frequent:

Wrong|Correct
Осуществлять деятельность|Работать
Произвести оплату|Оплатить / Заплатить
В настоящее время|Сейчас
Принимать участие|Участвовать
Нести ответственность|Отвечать (за)

Remaining 27 (split-predicate verb+noun → verb, plus officialese phrases): full dead→live catalog in [editorial-grammar.md](editorial-grammar.md) §H.2; the stop-word form of канцелярит is also in [info-style.md](info-style.md) §B.

## High: Vague Adjectives (11 entries)

Words that add volume but no information. If removing changes nothing -- delete.

Vague|Fix
Высококачественный продукт|Продукт [конкретное свойство: прочный, быстрый]
Оптимальное решение|Решение, которое [конкретное преимущество]
Инновационный подход|[Описание подхода]
Достаточно быстро|За 3 часа / К вечеру
Определённые трудности|[Названные трудности]
Соответствующие меры|[Конкретные действия]
Данный вопрос|Этот вопрос (or omit)
Ряд причин|Три причины: [1, 2, 3]
Определённым образом|[Описать, как именно]
Весьма существенно|На 40% / Вдвое
Комплексное решение|Решение, которое охватывает [что]

## High: Passive Voice (10 entries)

Passive hides the actor, making text evasive and bureaucratic.

Carve-out -- the passive says how the product behaves, not what a person did. Not flagged where the verb is something the product, tool or service does by itself and the sentence carries nothing but that: «Предупреждение выводится один раз за сессию», «Токены перестанут приниматься первого сентября», «Поле `updated_at` меняется при каждой записи». Naming the actor there only repeats the thing the page is already about. The verb decides first, so no heading buys the exemption: deciding, checking, reviewing, approving, notifying and sending are done by people, and «информация подлежит рассмотрению в установленные сроки» stays a finding -- naming the регламент beside it names nobody. A passive carried inside a larger point is not a behaviour line -- more of the same behaviour alongside keeps the exemption, an instruction, an inference or a person's commitment in the same sentence breaks it: «сколько запросов обрабатывается», set inside a sentence about what the real question is, stays a finding. A message shown to the reader is the message, not documentation about one: «Ваш запрос не может быть обработан» withholds the cause and the next step -- «Не смогли обработать запрос: истёк срок токена». Nothing else changes, including the default that the passive is fine when the agent is unknown or irrelevant. No row of the table below is exempt -- not one names a machine.

Passive|Active
Было принято решение|Мы решили / Руководитель решил
Отчёт будет подготовлен|Ольга подготовит отчёт
Работа выполняется|Команда выполняет работу
Задача была поставлена|Иван поставил задачу
Ошибка была допущена|Мы допустили ошибку
Вопрос рассматривается|Анна рассматривает вопрос, ответит до пятницы
Проект был завершён|Команда завершила проект
Меры будут приняты|[Кто] сделает [что] до [когда]
Совещание проведено|Мы провели совещание
Информация доведена до сведения|Мы сообщили команде

## High: Sentence Bloat (15 entries)

Sentences that could be half as long with no loss of meaning.

Bloated|Concise
В связи с тем, что проект находится на завершающей стадии реализации|Проект почти завершён
На сегодняшний день не представляется возможным дать однозначный ответ|Пока не можем ответить точно
Мы хотели бы выразить надежду на то, что|Надеемся
По результатам проведённого анализа установлено, что|Анализ показал:
Необходимо обратить особое внимание на тот факт, что|Обратите внимание:
Данная информация носит конфиденциальный характер|Информация конфиденциальная
Если у вас возникнут дополнительные вопросы, вы можете обратиться|Если есть вопросы -- пишите
Мы придерживаемся мнения о том, что|Считаем, что
Является ключевым фактором, определяющим|Определяет / Главная причина
В рамках проводимых мероприятий по улучшению|Чтобы улучшить
Следует отметить тот немаловажный факт, что|Важно:
Исходя из совокупности имеющихся факторов|Учитывая [что именно]
На протяжении длительного периода времени|Долго / С [года] по [год]
Таким образом, подводя итог всему вышесказанному|Итого
По вопросу, касающемуся|По поводу / О

## Medium: False Intensifiers (11 entries)

Words that claim to amplify but weaken because they substitute for evidence.

False Intensifier|Fix
Абсолютно уникальный|Уникальный (or describe why)
Очень важно|Важно (or explain why it matters)
Крайне необходимо|Необходимо (or state consequences)
Максимально эффективно|Эффективно: [метрика]
Реально классный|[Конкретное достоинство]
Совершенно очевидно|Вот данные: ...
Буквально взорвал|[Конкретный результат]
Невероятно быстрый|Обрабатывает 10K запросов/сек
По-настоящему|[Remove or replace with facts]
Самый лучший|Лучший по [критерий]
Довольно-таки неплохой|Хороший / Достойный

## Medium: Tautology/Pleonasm (22 entries)

Tautology: same meaning repeated (масло масляное). Pleonasm: redundant word already contained in neighbor (подняться вверх).

Top 5 most frequent:

Redundant|Fix
Свободная вакансия|Вакансия
Главный приоритет|Приоритет
Подняться вверх / спуститься вниз|Подняться / спуститься
Масло масляное|(убрать повтор)
Спросить вопрос|Задать вопрос / Спросить

Remaining 17 (период времени, передовой авангард, краткое резюме, совместное сотрудничество, другая альтернатива, ответная реакция, etc.): full catalog in [editorial-grammar.md](editorial-grammar.md) §E.1 (pleonasms) and §E.2 (cognate repeats).

## Low: Anglicisms (11 entries)

Use Russian when it carries the same meaning. Some anglicisms have no precise equivalent -- those are fine.

Anglicism|Russian|Replace when
Дедлайн|Срок / Крайний срок|Non-IT context
Фидбэк|Обратная связь / Отзыв|Non-IT audience
Митинг|Встреча / Совещание|General business
Апрувить|Утвердить / Согласовать|Any formal text
Кейс|Случай / Пример / Ситуация|Outside legal/marketing use
Ворк-шоп|Мастерская / Практикум|General audience
Тимлид|Руководитель группы|Formal HR documents
Коллаборация|Сотрудничество|General text
Факап|Провал / Ошибка|Any non-slang text
Пушить (задачу)|Продвигать / Настаивать|Non-slang context
Сетапить|Настраивать|Non-slang context

## Low: Archaic (6 entries)

Words that make text sound pre-revolutionary.

Archaic|Modern
Сие|Это
Оный|Тот / Этот
Коим образом|Каким образом / Как
Ибо|Потому что / Так как
Дабы|Чтобы
Токмо|Только

## Low: Overly Formal (5 entries)

Official language where it creates distance and discomfort.

Formal|Appropriate
Разрешите поинтересоваться...|Подскажите, пожалуйста...
Прошу принять к сведению|Имейте в виду
Выражаю благодарность|Спасибо!
Настоящим подтверждаю|Подтверждаю / Да, всё верно
Имею честь сообщить|Расскажу / Хочу поделиться

## Summary

Severity|Category|Entries
Critical|Typography|15
Critical|Канцелярит и номинализация|32
High|Vague adjectives|11
High|Passive voice|10
High|Sentence bloat|15
Medium|False intensifiers|11
Medium|Tautology/pleonasm|22
Low|Anglicisms|11
Low|Archaic|6
Low|Overly formal|5
**Total**||**138**
