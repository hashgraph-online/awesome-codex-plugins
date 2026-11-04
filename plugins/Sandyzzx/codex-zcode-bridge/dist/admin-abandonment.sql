-- Narrow administrative recovery audit. This sidecar deliberately leaves the
-- v13 lifecycle tables unchanged; presentOperation() exposes the effective
-- terminal phase as admin_abandoned and never treats it as Cleanup Verified.
CREATE TABLE manager_admin_abandonments (
  operation_id TEXT PRIMARY KEY,
  operation_kind TEXT NOT NULL CHECK(operation_kind='attempt_lifecycle'),
  task_id TEXT NOT NULL,
  attempt INTEGER NOT NULL CHECK(attempt>=1),
  generation INTEGER NOT NULL CHECK(generation>=1),
  claim_id TEXT NOT NULL CHECK(length(claim_id) BETWEEN 1 AND 128),
  worker_identity_digest TEXT NOT NULL CHECK(length(worker_identity_digest)=64),
  original_revision INTEGER NOT NULL CHECK(original_revision>=1),
  event_sequence INTEGER NOT NULL UNIQUE CHECK(event_sequence=original_revision+1),
  outcome TEXT NOT NULL CHECK(outcome='admin_abandoned'),
  result_absent INTEGER NOT NULL CHECK(result_absent=1),
  cleanup_verified INTEGER NOT NULL CHECK(cleanup_verified=0),
  release_reason TEXT NOT NULL CHECK(release_reason='cleanup_incomplete'),
  request_digest TEXT NOT NULL CHECK(length(request_digest)=64),
  audit_json TEXT NOT NULL CHECK(
    json_valid(audit_json) AND json_type(audit_json)='object'
    AND length(CAST(audit_json AS BLOB))<=4096
  ),
  audit_digest TEXT NOT NULL CHECK(length(audit_digest)=64),
  abandoned_at TEXT NOT NULL,
  UNIQUE(task_id,attempt,generation),
  FOREIGN KEY(operation_id) REFERENCES manager_operations(operation_id),
  FOREIGN KEY(task_id,attempt,generation) REFERENCES attempts(task_id,attempt,generation)
) STRICT;

CREATE TRIGGER manager_admin_abandonments_no_update BEFORE UPDATE ON manager_admin_abandonments
BEGIN SELECT RAISE(ABORT,'administrative abandonment is immutable'); END;
CREATE TRIGGER manager_admin_abandonments_no_delete BEFORE DELETE ON manager_admin_abandonments
BEGIN SELECT RAISE(ABORT,'administrative abandonment is immutable'); END;
