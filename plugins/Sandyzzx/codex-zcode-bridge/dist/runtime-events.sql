-- Additive v14 compatibility extension. The base v14 tables and authority
-- receipts remain unchanged; schema.sql includes the same objects for fresh
-- installations.
CREATE TABLE runtime_task_events (
  event_cursor INTEGER PRIMARY KEY CHECK(event_cursor BETWEEN 1 AND 9007199254740991),
  operation_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  attempt INTEGER NOT NULL CHECK(attempt>=1),
  generation INTEGER NOT NULL CHECK(generation>=1),
  claim_id TEXT NOT NULL CHECK(length(claim_id) BETWEEN 1 AND 512),
  worker_sequence INTEGER NOT NULL CHECK(worker_sequence>=1),
  event_type TEXT NOT NULL CHECK(event_type IN (
    'session_ready','model_selected','turn_started','model_tool_call',
    'tool_status','model_output','turn_completed','turn_failed','report_ready'
  )),
  at TEXT NOT NULL,
  summary TEXT NOT NULL CHECK(length(cast(summary AS BLOB)) BETWEEN 1 AND 8192),
  details_json TEXT CHECK(
    details_json IS NULL OR (
      json_valid(details_json) AND json_type(details_json)='object'
      AND length(CAST(details_json AS BLOB))<=8192
    )
  ),
  details_digest TEXT CHECK(details_digest IS NULL OR length(details_digest)=64),
  UNIQUE(operation_id,worker_sequence),
  FOREIGN KEY(operation_id) REFERENCES manager_operations(operation_id),
  FOREIGN KEY(task_id,attempt) REFERENCES attempts(task_id,attempt),
  CHECK ((details_json IS NULL AND details_digest IS NULL)
      OR (details_json IS NOT NULL AND details_digest IS NOT NULL))
) STRICT;

CREATE INDEX runtime_task_events_task_cursor ON runtime_task_events(task_id,event_cursor);
CREATE TRIGGER runtime_task_events_no_update BEFORE UPDATE ON runtime_task_events
BEGIN SELECT RAISE(ABORT,'runtime task events are immutable'); END;
CREATE TRIGGER runtime_task_events_no_delete BEFORE DELETE ON runtime_task_events
BEGIN SELECT RAISE(ABORT,'runtime task events are immutable'); END;
CREATE TRIGGER runtime_task_events_identity_guard BEFORE INSERT ON runtime_task_events
WHEN NOT EXISTS (
  SELECT 1 FROM manager_operations o
    JOIN tasks t ON t.task_id=o.task_id
    JOIN attempts a ON a.task_id=t.task_id AND a.attempt=o.attempt
  WHERE o.operation_id=NEW.operation_id AND o.operation_kind='attempt_lifecycle'
    AND o.phase='running' AND o.task_id=NEW.task_id AND o.attempt=NEW.attempt
    AND o.generation=NEW.generation AND o.claim_id=NEW.claim_id
    AND o.claim_generation=o.generation
    AND t.current_attempt=o.attempt AND t.status='running'
    AND a.status='running' AND a.generation=o.generation
)
BEGIN SELECT RAISE(ABORT,'runtime task event identity mismatch'); END;
