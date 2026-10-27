# Формат кандидатов и подтверждённых изменений

Кандидат и пакет записи — разные артефакты. Диагностические сценарии создают только кандидатов и никогда не заполняют решение за человека.

## Кандидат ручной проверки

| Поле | Назначение |
|---|---|
| `candidate_id` | Устойчивый идентификатор строки |
| `object_name` | Понятное название объекта |
| `proposed_action` | Предлагаемое изменение |
| `proposed_value` | Предлагаемое значение |
| `source` | Источник исходной строки |
| `source_row_sha256` | Контрольная сумма исходной строки |
| `evidence` | Проверяемое основание без секретов |
| `scope` | Точная область действия |
| `reviewer` | Пусто до ручной проверки |
| `reviewed_at` | Пусто до ручной проверки |
| `expires_at` | Срок действия решения |
| `decision` | Пусто до ручной проверки |
| `reversal_ref` | Ссылка на возврат прежнего состояния, если применимо |
| `candidate_status` | Изначально `pending_review` |

Синтетический пример кандидата:

```tsv
C-001	Поиск / пример / группа услуг	REVIEW_NEGATIVE	пример слова	search-query-report	<sha256>	строка отчёта и смысловой конфликт	campaign:example/group:service						pending_review
```

## Кандидат в минус-слова

Для `REVIEW_NEGATIVE` из поисковых запросов или Wordstat в `proposed_value` — одно безопасное слово (`SAFE_ONE_TOKEN`) или неразрывная пара слов (`SAFE_SHORT_MASK`), а в `evidence` — дополнительные поля:

| Поле | Назначение |
|---|---|
| `blocked_intent` | Какое нецелевое намерение отсекается |
| `candidate_kind` | `SAFE_ONE_TOKEN` или `SAFE_SHORT_MASK` |
| `source_type` | `sqr`, `wordstat` или `general_guard` (отдельно утверждённая общая защита) |
| `source_query_examples` | Полные запросы — только как доказательство |
| `reduction_reason` | Почему кандидат минимален и безопасен |
| `product_or_route` и `landing_url` | Какой маршрут защищён |
| `protected_check`, `target_conflict_check`, `neighbor_route_check` | Все три — `PASS` |

Полный запрос никогда не копируется в `proposed_value`, даже если в нём одно-два слова. Действия `ADD_NEGATIVE_PHRASE`, `PHRASE_MINUS` и поле `params.phrase` для очистки по запросам запрещены; без сокращения до безопасного слова или маски кандидат блокируется. Порядок: `agent_negative_from_wave.md` → `agent_minus_words_from_negative.md` → `validate_negatives_prompt.md` → `agent_validation_checklist.md`.

## Переход к записи

Только строки с действующим ручным решением `approved` могут быть вручную перенесены в отдельный пакет по `direct_write_pack.schema.json`. Пакет содержит снимок источника, контрольную сумму, подтверждение владельца, ограничение баллов, сведения обратимости и чтение результата. Для применения используется только `direct_write_gate.py --apply`.
