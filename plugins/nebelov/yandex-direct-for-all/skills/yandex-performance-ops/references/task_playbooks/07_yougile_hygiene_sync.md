# Порядок 07: безопасная синхронизация с YouGile

Используйте этот порядок для подготовки рабочего пространства, переноса
материалов в чат или создания задач из `tasks.tsv`. Все три сценария по
умолчанию работают только как локальная проверка. Они не читают YouGile и не
пишут в него без `--apply`.

## Неподвижные правила

- Ключ записи передаётся только через `YOUGILE_WRITE_API_KEY`.
- Для применения одновременно нужны `YOUGILE_WRITE_ARMED=1`, `--apply`,
  закрытый файл разрешения и закрытая папка доказательств.
- Описание операции и все входные файлы закрепляются контрольными суммами.
- Разрешение должно иметь права `0600`, точное действие, понятное название
  места назначения, контрольную сумму и неистёкший `expires_at`.
- Перед записью сохраняется состояние `before.json`; после записи выполняется
  контрольное чтение и создаются `after.json`, `readback.json`, `diff.json` и
  `reversal-candidate.json`.
- Служебные номера YouGile остаются в закрытых доказательствах и не выводятся в
  обычный отчёт.
- Старые, архивные и действующие доски проверяются раздельно. Удаление,
  архивирование и объединение не входят в эти три сценария и требуют отдельного
  точного разрешения.

## Общая форма разрешения

```json
{
  "approved": true,
  "action": "НАЗВАНИЕ_ДЕЙСТВИЯ",
  "target_ref": "Понятное название проекта, доски или чата",
  "spec_sha256": "КОНТРОЛЬНАЯ_СУММА_ИЗ_ПРОВЕРКИ",
  "expires_at": "2026-07-15T12:00:00+03:00"
}
```

После создания файла выполните `chmod 600 approval.json`. Допустимые действия:

- `bootstrap_yougile_workspace`;
- `push_yougile_file_bundle`;
- `sync_yougile_tasks`.

## Подготовка проекта, досок и колонок

Описание рабочего пространства содержит `project.title` и непустой список
`boards`. У каждой доски нужны уникальные `alias`, `title` и колонки с
уникальными `alias` и `title`. Начальные задачи необязательны.

Проверка без сети:

```bash
python3 scripts/bootstrap_yougile_workspace.py --spec workspace.json
```

Применение после копирования напечатанной контрольной суммы в разрешение:

```bash
YOUGILE_WRITE_ARMED=1 YOUGILE_WRITE_API_KEY="$YOUGILE_WRITE_API_KEY" \
python3 scripts/bootstrap_yougile_workspace.py \
  --spec workspace.json \
  --approval approval.json \
  --evidence-dir .private/yougile-bootstrap \
  --apply
```

Сценарий ищет объекты по точному названию, отклоняет неоднозначные совпадения,
создаёт только отсутствующие объекты и читает каждый созданный объект обратно.

## Перенос файлов в чат

Закрытый файл набора имеет права `0600` и такую форму:

```json
{
  "target_ref": "Чат задачи Еженедельный отчёт",
  "chat_id": "REPLACE_WITH_CHAT_ID",
  "files": [
    {
      "path": "./00_scope.md",
      "sha256": "REPLACE_WITH_FILE_SHA256"
    }
  ]
}
```

Сначала выполните только проверку:

```bash
python3 scripts/push_yougile_file_bundle.py --bundle bundle.json
```

Затем примените точный подтверждённый набор:

```bash
YOUGILE_WRITE_ARMED=1 YOUGILE_WRITE_API_KEY="$YOUGILE_WRITE_API_KEY" \
python3 scripts/push_yougile_file_bundle.py \
  --bundle bundle.json \
  --approval approval.json \
  --evidence-dir .private/yougile-files \
  --apply
```

После каждого сообщения сценарий читает его обратно. В опубликованной схеме
REST API нет удаления сообщения, поэтому файл возврата содержит перечень
сообщений для ручного исправления при необходимости.

## Создание задач из таблицы

Скопируйте `templates/yougile-board-presets.example.json` в закрытый файл,
замените все заглушки реальными колонками и установите права `0600`. Пакет
синхронизации также должен иметь права `0600`:

```json
{
  "target_ref": "Доска рекламных задач",
  "tasks_file": "./tasks.tsv",
  "tasks_sha256": "REPLACE_WITH_TASKS_SHA256",
  "columns_file": "./yougile-board-presets.json",
  "columns_sha256": "REPLACE_WITH_COLUMNS_SHA256",
  "board_preset": "default",
  "campaign_name": "Поисковые кампании",
  "category": null,
  "priority": null
}
```

Проверка без сети и применение:

```bash
python3 scripts/sync_yougile.py --package sync-package.json

YOUGILE_WRITE_ARMED=1 YOUGILE_WRITE_API_KEY="$YOUGILE_WRITE_API_KEY" \
python3 scripts/sync_yougile.py \
  --package sync-package.json \
  --approval approval.json \
  --evidence-dir .private/yougile-sync \
  --apply
```

Проверка дублей обязательна и выполняется по точному понятному названию задачи.
Отключить её параметром командной строки нельзя.

## Состав итогового набора

- `00_scope.md`
- `01_raw_index.md`
- `02_findings.tsv`
- `03_duplicate_matrix.tsv`
- `04_validation.md`
- `05_pre_apply_summary.md`
- `06_yougile_handoff.md`

Перед отдельным разрешением на архивирование или удаление покажите человеку:
какие задачи объединяются, какие наблюдения остаются, где живёт актуальная
волна и что именно признано безопасным испытательным шумом.
