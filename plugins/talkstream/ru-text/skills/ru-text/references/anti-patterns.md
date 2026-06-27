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
CAPS LOCK ДЛЯ ВЫДЕЛЕНИЯ|**Полужирный** или *курсив*

Remaining 10: nested quotes, en-dash in ranges, double dashes, space before comma, no space after period, latin x vs multiplication sign, inconsistent ё, double spaces, (c) vs ©, minus vs em-dash in text. All covered in [typography.md](typography.md).

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

Anglicism|Russian|When anglicism OK
Дедлайн|Срок / Крайний срок|IT context
Фидбэк|Обратная связь / Отзыв|Non-IT audience
Митинг|Встреча / Совещание|General business
Апрувить|Утвердить / Согласовать|Any formal text
Кейс|Случай / Пример / Ситуация|Legal/marketing term
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
