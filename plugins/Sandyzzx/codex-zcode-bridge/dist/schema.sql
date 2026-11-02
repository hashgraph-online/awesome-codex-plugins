-- Isolated WP6B/WP6C candidate schema v13. Task/Attempt are durable domain
-- projections; manager_operations and manager_operation_events remain the two
-- lifecycle structures required by ADR-014 v1.1.
PRAGMA foreign_keys=ON;
CREATE TABLE tasks (
  task_id TEXT PRIMARY KEY,
  task_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(task_json) AND json_type(task_json)='object' AND length(CAST(task_json AS BLOB))<=1048576),
  status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','completed','failed','cancelled','waiting_for_master')),
  current_attempt INTEGER NOT NULL DEFAULT 1 CHECK(current_attempt>=1),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
) STRICT;

CREATE TABLE attempts (
  task_id TEXT NOT NULL,
  attempt INTEGER NOT NULL CHECK(attempt>=1),
  generation INTEGER CHECK(generation IS NULL OR generation>=1),
  status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','completed','failed','cancelled','waiting_for_master')),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  continuation_operation_id TEXT UNIQUE,
  continuation_json TEXT CHECK(continuation_json IS NULL OR (json_valid(continuation_json) AND json_type(continuation_json)='object' AND length(CAST(continuation_json AS BLOB))<=1048576)),
  continuation_digest TEXT CHECK(continuation_digest IS NULL OR length(continuation_digest)=64),
  queued_cancel_id TEXT UNIQUE,
  queued_cancel_request_digest TEXT CHECK(queued_cancel_request_digest IS NULL OR length(queued_cancel_request_digest)=64),
  queued_cancel_event_cursor INTEGER UNIQUE CHECK(queued_cancel_event_cursor IS NULL OR queued_cancel_event_cursor BETWEEN 1 AND 9007199254740991),
  queued_cancelled_at TEXT,
  queued_cancel_operation_id TEXT,
  queued_cancel_result_digest TEXT CHECK(queued_cancel_result_digest IS NULL OR length(queued_cancel_result_digest)=64),
  queued_cancel_result_json TEXT CHECK(queued_cancel_result_json IS NULL OR (json_valid(queued_cancel_result_json) AND json_type(queued_cancel_result_json)='object' AND length(CAST(queued_cancel_result_json AS BLOB))<=65536)),
  PRIMARY KEY(task_id,attempt),
  UNIQUE(task_id,generation),
  UNIQUE(task_id,attempt,generation),
  FOREIGN KEY(task_id) REFERENCES tasks(task_id),
  CHECK ((continuation_operation_id IS NULL AND continuation_json IS NULL AND continuation_digest IS NULL)
      OR (attempt>1 AND continuation_operation_id IS NOT NULL AND continuation_json IS NOT NULL AND continuation_digest IS NOT NULL)),
  CHECK ((queued_cancel_id IS NULL AND queued_cancel_request_digest IS NULL AND queued_cancel_event_cursor IS NULL
      AND queued_cancelled_at IS NULL AND queued_cancel_operation_id IS NULL
      AND queued_cancel_result_digest IS NULL AND queued_cancel_result_json IS NULL)
      OR (status='cancelled' AND queued_cancel_id IS NOT NULL AND length(queued_cancel_id) BETWEEN 1 AND 128
          AND queued_cancel_request_digest IS NOT NULL AND queued_cancel_event_cursor IS NOT NULL AND queued_cancelled_at IS NOT NULL
          AND queued_cancel_result_digest IS NOT NULL AND queued_cancel_result_json IS NOT NULL))
) STRICT;

CREATE TABLE authority_metadata (
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  schema_version INTEGER NOT NULL CHECK(schema_version=13),
  next_generation INTEGER NOT NULL DEFAULT 0 CHECK(next_generation>=0),
  next_event_cursor INTEGER NOT NULL DEFAULT 0 CHECK(next_event_cursor BETWEEN 0 AND 9007199254740991),
  policy_version INTEGER,
  policy_generation INTEGER NOT NULL DEFAULT 0 CHECK(policy_generation>=0),
  capacity_limit INTEGER CHECK(capacity_limit BETWEEN 1 AND 8),
  policy_operation_id TEXT,
  CHECK ((policy_generation=0 AND policy_version IS NULL AND capacity_limit IS NULL AND policy_operation_id IS NULL)
      OR (policy_generation>0 AND policy_version=1 AND capacity_limit IS NOT NULL AND policy_operation_id IS NOT NULL))
) STRICT;

-- A fresh database is usable only after its bootstrap and Capacity policy have
-- committed a durable production Authority receipt.
CREATE TABLE fresh_install_receipt (
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  receipt_id TEXT NOT NULL UNIQUE CHECK(length(receipt_id) BETWEEN 1 AND 128),
  verifier_version TEXT NOT NULL CHECK(length(verifier_version) BETWEEN 1 AND 128),
  created_at TEXT NOT NULL
) STRICT;

CREATE TRIGGER fresh_install_receipt_no_update BEFORE UPDATE ON fresh_install_receipt
BEGIN SELECT RAISE(ABORT,'fresh install receipt is immutable'); END;
CREATE TRIGGER fresh_install_receipt_no_delete BEFORE DELETE ON fresh_install_receipt
BEGIN SELECT RAISE(ABORT,'fresh install receipt is immutable'); END;

-- Published migration evidence. A migration row is written only after the
-- staging import and independent readback succeeded.
CREATE TABLE migration_runs (
  migration_id TEXT PRIMARY KEY CHECK(length(migration_id) BETWEEN 1 AND 128),
  state TEXT NOT NULL CHECK(state='verified'),
  source_root_digest TEXT NOT NULL CHECK(length(source_root_digest)=64),
  source_manifest_json TEXT NOT NULL CHECK(
    json_valid(source_manifest_json) AND json_type(source_manifest_json)='object'
    AND length(CAST(source_manifest_json AS BLOB))<=67108864
  ),
  source_manifest_digest TEXT NOT NULL CHECK(length(source_manifest_digest)=64),
  source_task_count INTEGER NOT NULL CHECK(source_task_count>=0),
  source_artifact_count INTEGER NOT NULL CHECK(source_artifact_count>=0),
  source_artifact_bytes INTEGER NOT NULL CHECK(source_artifact_bytes>=0),
  source_result_count INTEGER NOT NULL CHECK(source_result_count>=0),
  source_event_count INTEGER NOT NULL CHECK(source_event_count>=0),
  archive_directory TEXT NOT NULL CHECK(length(archive_directory) BETWEEN 1 AND 32767),
  archive_manifest_digest TEXT NOT NULL CHECK(length(archive_manifest_digest)=64),
  archive_source_tasks_root TEXT NOT NULL CHECK(length(archive_source_tasks_root) BETWEEN 1 AND 32767),
  archive_file_count INTEGER NOT NULL CHECK(archive_file_count>=0 AND archive_file_count=source_artifact_count),
  archive_byte_count INTEGER NOT NULL CHECK(archive_byte_count>=0 AND archive_byte_count=source_artifact_bytes),
  verifier_version TEXT NOT NULL CHECK(length(verifier_version) BETWEEN 1 AND 128),
  created_at TEXT NOT NULL,
  verified_at TEXT NOT NULL
) STRICT;

CREATE TRIGGER migration_runs_no_update BEFORE UPDATE ON migration_runs
BEGIN SELECT RAISE(ABORT,'migration run is immutable'); END;
CREATE TRIGGER migration_runs_no_delete BEFORE DELETE ON migration_runs
BEGIN SELECT RAISE(ABORT,'migration run is immutable'); END;

CREATE TABLE authority_switch (
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  authority_generation INTEGER NOT NULL CHECK(authority_generation=1),
  cutover_id TEXT NOT NULL UNIQUE CHECK(length(cutover_id) BETWEEN 1 AND 128),
  migration_id TEXT NOT NULL UNIQUE,
  source_root_digest TEXT NOT NULL CHECK(length(source_root_digest)=64),
  source_manifest_digest TEXT NOT NULL CHECK(length(source_manifest_digest)=64),
  archive_directory TEXT NOT NULL CHECK(length(archive_directory) BETWEEN 1 AND 32767),
  archive_manifest_digest TEXT NOT NULL CHECK(length(archive_manifest_digest)=64),
  archive_source_tasks_root TEXT NOT NULL CHECK(length(archive_source_tasks_root) BETWEEN 1 AND 32767),
  archive_file_count INTEGER NOT NULL CHECK(archive_file_count>=0),
  archive_byte_count INTEGER NOT NULL CHECK(archive_byte_count>=0),
  schema_version INTEGER NOT NULL CHECK(schema_version=13),
  protocol_version TEXT NOT NULL CHECK(length(protocol_version) BETWEEN 1 AND 128),
  runtime_roster_digest TEXT NOT NULL CHECK(length(runtime_roster_digest)=64),
  verifier_version TEXT NOT NULL CHECK(length(verifier_version) BETWEEN 1 AND 128),
  created_at TEXT NOT NULL,
  FOREIGN KEY(migration_id) REFERENCES migration_runs(migration_id)
) STRICT;

CREATE TRIGGER authority_switch_no_update BEFORE UPDATE ON authority_switch
BEGIN SELECT RAISE(ABORT,'authority switch receipt is immutable'); END;
CREATE TRIGGER authority_switch_no_delete BEFORE DELETE ON authority_switch
BEGIN SELECT RAISE(ABORT,'authority switch receipt is immutable'); END;

-- Every importable legacy file is retained byte-for-byte. Task scoped
-- artifacts reference the imported Task but are never interpreted as a second
-- online authority.
CREATE TABLE json_artifacts (
  artifact_id TEXT PRIMARY KEY CHECK(length(artifact_id) BETWEEN 1 AND 128),
  migration_id TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE CHECK(
    length(relative_path) BETWEEN 1 AND 1024
    AND instr(relative_path,'\')=0
    AND substr(relative_path,1,1)<>'/'
    AND relative_path NOT LIKE '%/../%'
    AND relative_path NOT IN ('..','.')
  ),
  task_id TEXT,
  attempt INTEGER CHECK(attempt IS NULL OR attempt>=1),
  kind TEXT NOT NULL CHECK(length(kind) BETWEEN 1 AND 64),
  byte_length INTEGER NOT NULL CHECK(byte_length>=0 AND byte_length<=67108864),
  sha256 TEXT NOT NULL CHECK(length(sha256)=64),
  content BLOB NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(migration_id) REFERENCES migration_runs(migration_id),
  FOREIGN KEY(task_id) REFERENCES tasks(task_id),
  CHECK(length(content)=byte_length)
) STRICT;

CREATE INDEX json_artifacts_task ON json_artifacts(task_id,relative_path);
CREATE TRIGGER json_artifacts_no_update BEFORE UPDATE ON json_artifacts
BEGIN SELECT RAISE(ABORT,'JSON artifact is immutable'); END;
CREATE TRIGGER json_artifacts_no_delete BEFORE DELETE ON json_artifacts
BEGIN SELECT RAISE(ABORT,'JSON artifact is immutable'); END;

-- Legacy terminal Results remain readable without fabricating an Operation or
-- permanent Claim that did not exist in the JSON Authority.
CREATE TABLE migrated_task_results (
  task_id TEXT NOT NULL,
  attempt INTEGER NOT NULL CHECK(attempt>=1),
  result_json TEXT NOT NULL CHECK(
    json_valid(result_json) AND json_type(result_json)='object'
    AND length(CAST(result_json AS BLOB))<=1048576
  ),
  result_digest TEXT NOT NULL CHECK(length(result_digest)=64),
  artifact_id TEXT NOT NULL,
  PRIMARY KEY(task_id,attempt),
  FOREIGN KEY(task_id,attempt) REFERENCES attempts(task_id,attempt),
  FOREIGN KEY(artifact_id) REFERENCES json_artifacts(artifact_id)
) STRICT;

-- Historical public events are a read projection only. Their cursors share
-- authority_metadata.next_event_cursor with current lifecycle events so reads
-- have one monotonic ordering domain.
CREATE TABLE migrated_task_events (
  event_cursor INTEGER PRIMARY KEY CHECK(event_cursor BETWEEN 1 AND 9007199254740991),
  task_id TEXT NOT NULL,
  attempt INTEGER CHECK(attempt IS NULL OR attempt>=1),
  source_sequence INTEGER NOT NULL CHECK(source_sequence>=1),
  event_type TEXT NOT NULL CHECK(length(event_type) BETWEEN 1 AND 128),
  at TEXT NOT NULL,
  summary TEXT NOT NULL,
  details_json TEXT CHECK(
    details_json IS NULL OR (
      json_valid(details_json) AND json_type(details_json)='object'
      AND length(CAST(details_json AS BLOB))<=1048576
    )
  ),
  details_digest TEXT CHECK(details_digest IS NULL OR length(details_digest)=64),
  artifact_id TEXT NOT NULL,
  UNIQUE(task_id,source_sequence),
  FOREIGN KEY(task_id) REFERENCES tasks(task_id),
  FOREIGN KEY(task_id,attempt) REFERENCES attempts(task_id,attempt),
  FOREIGN KEY(artifact_id) REFERENCES json_artifacts(artifact_id),
  CHECK ((details_json IS NULL AND details_digest IS NULL)
    OR (details_json IS NOT NULL AND details_digest IS NOT NULL))
) STRICT;

CREATE INDEX migrated_task_events_task_cursor ON migrated_task_events(task_id,event_cursor);
CREATE TRIGGER migrated_task_events_no_update BEFORE UPDATE ON migrated_task_events
BEGIN SELECT RAISE(ABORT,'migrated task events are immutable'); END;
CREATE TRIGGER migrated_task_events_no_delete BEFORE DELETE ON migrated_task_events
BEGIN SELECT RAISE(ABORT,'migrated task events are immutable'); END;

CREATE TABLE manager_operations (
  operation_id TEXT PRIMARY KEY,
  operation_kind TEXT NOT NULL CHECK(operation_kind IN ('attempt_lifecycle','capacity_policy_change')),
  request_digest TEXT NOT NULL CHECK(length(request_digest)=64),
  task_id TEXT,
  attempt INTEGER,
  generation INTEGER,
  reservation_id TEXT UNIQUE,
  revision INTEGER NOT NULL CHECK(revision>=1),
  phase TEXT NOT NULL CHECK(phase IN ('reserved','cancelled_before_launch','launch_intent','launch_unknown','launch_failed','running','result_committed','cleanup_pending','cleanup_verified','cleanup_unverified','cleanup_reverified','quarantined','released','policy_change_committed')),
  capacity_slot INTEGER CHECK(capacity_slot BETWEEN 1 AND 8),
  workspace_ref TEXT,
  workspace_identity_json TEXT,
  policy_generation INTEGER,
  capacity_limit INTEGER,
  created_at TEXT NOT NULL,
  launch_id TEXT UNIQUE,
  launch_epoch INTEGER,
  launch_token_digest TEXT,
  launch_intent_digest TEXT,
  launch_receipt_id TEXT UNIQUE,
  launch_receipt_digest TEXT,
  launch_identity_json TEXT,
  claim_id TEXT UNIQUE,
  claim_request_digest TEXT,
  claim_worker_identity_json TEXT,
  claim_worker_identity_digest TEXT,
  claim_launch_id TEXT,
  claim_generation INTEGER,
  claim_token_digest TEXT,
  result_status TEXT CHECK(result_status IN ('completed','failed','cancelled','waiting_for_master')),
  result_generation INTEGER,
  result_digest TEXT CHECK(result_digest IS NULL OR length(result_digest)=64),
  result_json TEXT CHECK(result_json IS NULL OR (json_valid(result_json) AND json_type(result_json)='object' AND length(CAST(result_json AS BLOB))<=65536)),
  result_commit_ref TEXT UNIQUE,
  FOREIGN KEY(task_id,attempt,generation) REFERENCES attempts(task_id,attempt,generation),
  CHECK ((operation_kind='attempt_lifecycle' AND task_id IS NOT NULL AND attempt IS NOT NULL AND generation IS NOT NULL
      AND reservation_id IS NOT NULL AND capacity_slot IS NOT NULL AND workspace_ref IS NOT NULL
      AND policy_generation IS NULL AND capacity_limit IS NULL AND phase<>'policy_change_committed')
    OR (operation_kind='capacity_policy_change' AND task_id IS NULL AND attempt IS NULL AND generation IS NULL
      AND reservation_id IS NULL AND capacity_slot IS NULL AND workspace_ref IS NULL AND workspace_identity_json IS NULL
      AND policy_generation IS NOT NULL AND capacity_limit BETWEEN 1 AND 8 AND phase='policy_change_committed'
      AND launch_id IS NULL AND launch_epoch IS NULL AND launch_token_digest IS NULL AND launch_intent_digest IS NULL
      AND launch_receipt_id IS NULL AND launch_receipt_digest IS NULL AND launch_identity_json IS NULL AND claim_id IS NULL AND claim_request_digest IS NULL
      AND claim_worker_identity_json IS NULL AND claim_worker_identity_digest IS NULL AND claim_launch_id IS NULL
      AND claim_generation IS NULL AND claim_token_digest IS NULL))
  ,CHECK ((launch_id IS NULL AND launch_epoch IS NULL AND launch_token_digest IS NULL AND launch_intent_digest IS NULL)
       OR (launch_id IS NOT NULL AND launch_epoch IS NOT NULL AND launch_epoch>=1 AND launch_token_digest IS NOT NULL
            AND length(launch_token_digest)=64 AND launch_intent_digest IS NOT NULL AND length(launch_intent_digest)=64))
  ,CHECK ((launch_receipt_id IS NULL AND launch_receipt_digest IS NULL AND launch_identity_json IS NULL)
       OR (launch_receipt_id IS NOT NULL AND launch_receipt_digest IS NOT NULL AND length(launch_receipt_digest)=64 AND launch_identity_json IS NOT NULL))
  ,CHECK ((claim_id IS NULL AND claim_request_digest IS NULL AND claim_worker_identity_json IS NULL
            AND claim_worker_identity_digest IS NULL AND claim_launch_id IS NULL AND claim_generation IS NULL AND claim_token_digest IS NULL)
       OR (claim_id IS NOT NULL AND length(claim_request_digest)=64 AND claim_worker_identity_json IS NOT NULL
            AND length(claim_worker_identity_digest)=64 AND claim_launch_id=launch_id AND claim_generation=generation
            AND claim_token_digest=launch_token_digest AND launch_receipt_digest IS NOT NULL
             AND phase IN ('running','result_committed','cleanup_pending','cleanup_verified','cleanup_unverified','cleanup_reverified','quarantined','released')))
  ,CHECK ((result_status IS NULL AND result_generation IS NULL AND result_digest IS NULL AND result_json IS NULL AND result_commit_ref IS NULL)
       OR (result_status IS NOT NULL AND result_generation=generation AND result_digest IS NOT NULL AND result_json IS NOT NULL
            AND result_commit_ref IS NOT NULL AND claim_id IS NOT NULL
             AND phase IN ('result_committed','cleanup_pending','cleanup_verified','cleanup_unverified','cleanup_reverified','quarantined','released')))
) STRICT;

CREATE UNIQUE INDEX lifecycle_task_attempt ON manager_operations(task_id,attempt) WHERE operation_kind='attempt_lifecycle';
CREATE UNIQUE INDEX lifecycle_task_generation ON manager_operations(task_id,generation) WHERE operation_kind='attempt_lifecycle';
CREATE UNIQUE INDEX lifecycle_active_slot ON manager_operations(capacity_slot) WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch');
CREATE UNIQUE INDEX policy_generation_unique ON manager_operations(policy_generation) WHERE operation_kind='capacity_policy_change';
CREATE UNIQUE INDEX lifecycle_launch_id_unique ON manager_operations(launch_id) WHERE launch_id IS NOT NULL;

CREATE TABLE manager_operation_events (
  event_cursor INTEGER PRIMARY KEY AUTOINCREMENT CHECK(event_cursor BETWEEN 1 AND 9007199254740991),
  operation_id TEXT NOT NULL,
  sequence INTEGER NOT NULL CHECK(sequence>=1),
  event_type TEXT NOT NULL CHECK(event_type IN ('capacity_policy_committed','observation_recorded','reserved','cancelled_before_launch','launch_intent','launch_receipt','launch_unknown','claim_committed','result_committed','cleanup_pending','cleanup_verified','cleanup_unverified','cleanup_reverified','quarantined','released','launch_failed','interaction_requested','interaction_reply_intent','interaction_reply_prepared','interaction_reply_committed','interaction_reply_accepted')),
  from_phase TEXT CHECK(from_phase IS NULL OR from_phase IN ('reserved','cancelled_before_launch','launch_intent','launch_unknown','launch_failed','running','result_committed','cleanup_pending','cleanup_verified','cleanup_unverified','cleanup_reverified','quarantined','released','policy_change_committed')),
  to_phase TEXT NOT NULL CHECK(to_phase IN ('reserved','cancelled_before_launch','launch_intent','launch_unknown','launch_failed','running','result_committed','cleanup_pending','cleanup_verified','cleanup_unverified','cleanup_reverified','quarantined','released','policy_change_committed')),
  generation INTEGER,
  evidence_json TEXT NOT NULL CHECK(json_valid(evidence_json) AND json_type(evidence_json)='object' AND length(CAST(evidence_json AS BLOB))<=2048),
  evidence_digest TEXT NOT NULL CHECK(length(evidence_digest)=64),
  at TEXT NOT NULL,
  UNIQUE(operation_id,sequence),
  FOREIGN KEY(operation_id) REFERENCES manager_operations(operation_id),
  CHECK ((sequence=1 AND from_phase IS NULL) OR (sequence>1 AND from_phase IS NOT NULL))
) STRICT;

CREATE TRIGGER events_no_update BEFORE UPDATE ON manager_operation_events BEGIN SELECT RAISE(ABORT,'append-only events'); END;
CREATE TRIGGER events_no_delete BEFORE DELETE ON manager_operation_events BEGIN SELECT RAISE(ABORT,'append-only events'); END;
CREATE TRIGGER operations_no_delete BEFORE DELETE ON manager_operations BEGIN SELECT RAISE(ABORT,'permanent operations'); END;
CREATE TRIGGER operation_identity_immutable BEFORE UPDATE ON manager_operations
WHEN OLD.operation_kind='capacity_policy_change'
 OR NEW.operation_id IS NOT OLD.operation_id OR NEW.operation_kind IS NOT OLD.operation_kind
 OR NEW.request_digest IS NOT OLD.request_digest OR NEW.task_id IS NOT OLD.task_id
 OR NEW.attempt IS NOT OLD.attempt OR NEW.generation IS NOT OLD.generation
 OR NEW.reservation_id IS NOT OLD.reservation_id OR NEW.capacity_slot IS NOT OLD.capacity_slot
 OR NEW.workspace_ref IS NOT OLD.workspace_ref OR NEW.workspace_identity_json IS NOT OLD.workspace_identity_json
 OR (OLD.launch_id IS NOT NULL AND (NEW.launch_id IS NOT OLD.launch_id OR NEW.launch_epoch IS NOT OLD.launch_epoch
     OR NEW.launch_token_digest IS NOT OLD.launch_token_digest OR NEW.launch_intent_digest IS NOT OLD.launch_intent_digest))
 OR (OLD.launch_receipt_id IS NOT NULL AND (NEW.launch_receipt_id IS NOT OLD.launch_receipt_id OR NEW.launch_receipt_digest IS NOT OLD.launch_receipt_digest OR NEW.launch_identity_json IS NOT OLD.launch_identity_json))
 OR (OLD.claim_id IS NOT NULL AND (NEW.claim_id IS NOT OLD.claim_id OR NEW.claim_request_digest IS NOT OLD.claim_request_digest
     OR NEW.claim_worker_identity_json IS NOT OLD.claim_worker_identity_json OR NEW.claim_worker_identity_digest IS NOT OLD.claim_worker_identity_digest
     OR NEW.claim_launch_id IS NOT OLD.claim_launch_id OR NEW.claim_generation IS NOT OLD.claim_generation OR NEW.claim_token_digest IS NOT OLD.claim_token_digest))
 OR (OLD.result_digest IS NOT NULL AND (NEW.result_status IS NOT OLD.result_status OR NEW.result_generation IS NOT OLD.result_generation
     OR NEW.result_digest IS NOT OLD.result_digest OR NEW.result_json IS NOT OLD.result_json OR NEW.result_commit_ref IS NOT OLD.result_commit_ref))
 OR NEW.revision<>OLD.revision+1
BEGIN SELECT RAISE(ABORT,'operation identity/revision violation'); END;
CREATE TRIGGER event_projection_binding BEFORE INSERT ON manager_operation_events
WHEN NOT EXISTS (SELECT 1 FROM manager_operations o WHERE o.operation_id=NEW.operation_id
 AND o.revision=NEW.sequence AND o.phase=NEW.to_phase AND o.generation IS NEW.generation)
BEGIN SELECT RAISE(ABORT,'event projection binding violation'); END;

CREATE TRIGGER launch_event_phase_guard BEFORE INSERT ON manager_operation_events
WHEN (NEW.event_type='launch_intent' AND NOT (NEW.from_phase='reserved' AND NEW.to_phase='launch_intent'))
 OR (NEW.event_type='launch_receipt' AND NOT (NEW.from_phase='launch_intent' AND NEW.to_phase='launch_intent'))
 OR (NEW.event_type='claim_committed' AND NOT (NEW.from_phase='launch_intent' AND NEW.to_phase='running'))
BEGIN SELECT RAISE(ABORT,'launch event phase violation'); END;

CREATE TRIGGER queued_cancel_event_phase_guard BEFORE INSERT ON manager_operation_events
WHEN NEW.event_type='cancelled_before_launch' AND NOT (NEW.from_phase='reserved' AND NEW.to_phase='cancelled_before_launch')
BEGIN SELECT RAISE(ABORT,'queued cancel event phase violation'); END;

CREATE TRIGGER cleanup_event_phase_guard BEFORE INSERT ON manager_operation_events
WHEN (NEW.event_type='cleanup_pending' AND NOT (NEW.from_phase='result_committed' AND NEW.to_phase='cleanup_pending'))
  OR (NEW.event_type='cleanup_unverified' AND NOT (NEW.from_phase='cleanup_pending' AND NEW.to_phase='cleanup_unverified'))
  OR (NEW.event_type='cleanup_reverified' AND NOT (NEW.from_phase='cleanup_unverified' AND NEW.to_phase='cleanup_reverified'))
  OR (NEW.event_type='cleanup_verified' AND NOT (NEW.from_phase IN ('cleanup_pending','cleanup_reverified') AND NEW.to_phase='cleanup_verified'))
  OR (NEW.event_type='released' AND NOT (NEW.from_phase='cleanup_verified' AND NEW.to_phase='released'))
BEGIN SELECT RAISE(ABORT,'cleanup/release event phase violation'); END;

CREATE TRIGGER cleanup_reverified_binding_guard BEFORE INSERT ON manager_operation_events
WHEN NEW.event_type='cleanup_reverified' AND NOT EXISTS (
  SELECT 1 FROM manager_operations o
    JOIN manager_operation_events u ON u.operation_id=o.operation_id AND u.event_type='cleanup_unverified'
      AND u.evidence_digest=json_extract(NEW.evidence_json,'$.prior_cleanup_event_digest')
  WHERE o.operation_id=NEW.operation_id AND o.operation_kind='attempt_lifecycle'
    AND o.phase='cleanup_reverified' AND o.revision=NEW.sequence AND o.generation=NEW.generation
    AND o.task_id=json_extract(NEW.evidence_json,'$.task_id')
    AND o.attempt=json_extract(NEW.evidence_json,'$.attempt')
    AND o.claim_id=json_extract(NEW.evidence_json,'$.claim_id')
    AND o.claim_generation=o.generation
    AND o.claim_worker_identity_digest=json_extract(NEW.evidence_json,'$.worker_identity_digest')
    AND o.launch_receipt_digest=json_extract(NEW.evidence_json,'$.launch_receipt_digest')
    AND o.result_commit_ref=json_extract(NEW.evidence_json,'$.result_commit_ref')
    AND u.sequence<NEW.sequence AND u.generation=NEW.generation
    AND json_extract(NEW.evidence_json,'$.operation_resources_complete')=1
    AND json_extract(NEW.evidence_json,'$.worker_tree_complete')=1
    AND json_extract(NEW.evidence_json,'$.workspace_touched')=0
    AND json_type(NEW.evidence_json,'$.resolved_recovery_event_digests')='array'
    AND json_array_length(NEW.evidence_json,'$.resolved_recovery_event_digests')<=8
    AND json_array_length(NEW.evidence_json,'$.resolved_recovery_event_digests')=(
      SELECT COUNT(*) FROM manager_operation_events h
      WHERE h.operation_id=NEW.operation_id AND h.event_type='observation_recorded'
        AND h.sequence<NEW.sequence AND json_extract(h.evidence_json,'$.reason')='recovery_hold'
        AND json_extract(h.evidence_json,'$.classification')='hold'
        AND json_extract(h.evidence_json,'$.reason_code') IN ('cleanup_identity_unknown','cleanup_incomplete'))
    AND NOT EXISTS (
      SELECT 1 FROM manager_operation_events h
      WHERE h.operation_id=NEW.operation_id AND h.event_type='observation_recorded'
        AND h.sequence<NEW.sequence AND json_extract(h.evidence_json,'$.reason') IN ('recovery_hold','recovery_quarantine')
        AND (json_extract(h.evidence_json,'$.reason')<>'recovery_hold'
          OR json_extract(h.evidence_json,'$.classification')<>'hold'
          OR json_extract(h.evidence_json,'$.reason_code') NOT IN ('cleanup_identity_unknown','cleanup_incomplete')))
    AND NOT EXISTS (
      SELECT 1 FROM json_each(NEW.evidence_json,'$.resolved_recovery_event_digests') j
      WHERE NOT EXISTS (
        SELECT 1 FROM manager_operation_events h
        WHERE h.operation_id=NEW.operation_id AND h.event_type='observation_recorded'
          AND h.evidence_digest=j.value AND h.sequence<NEW.sequence
          AND json_extract(h.evidence_json,'$.reason')='recovery_hold'
          AND json_extract(h.evidence_json,'$.classification')='hold'
          AND json_extract(h.evidence_json,'$.reason_code') IN ('cleanup_identity_unknown','cleanup_incomplete')))
    AND NOT EXISTS (
      SELECT 1 FROM manager_operation_events x
      WHERE x.operation_id=NEW.operation_id AND x.sequence>u.sequence AND x.sequence<NEW.sequence
        AND (x.event_type<>'observation_recorded'
          OR json_extract(x.evidence_json,'$.reason')<>'recovery_hold'
          OR json_extract(x.evidence_json,'$.classification')<>'hold'
          OR json_extract(x.evidence_json,'$.reason_code') NOT IN ('cleanup_identity_unknown','cleanup_incomplete')))
)
BEGIN SELECT RAISE(ABORT,'cleanup re-verification evidence binding violation'); END;

CREATE TRIGGER cleanup_verified_reverification_guard BEFORE INSERT ON manager_operation_events
WHEN NEW.event_type='cleanup_verified' AND NEW.from_phase='cleanup_reverified' AND NOT EXISTS (
  SELECT 1 FROM manager_operation_events r
  WHERE r.operation_id=NEW.operation_id AND r.event_type='cleanup_reverified'
    AND r.sequence=NEW.sequence-1 AND r.generation=NEW.generation
    AND json_extract(r.evidence_json,'$.cleanup_digest')=json_extract(NEW.evidence_json,'$.cleanup_digest')
    AND json_extract(r.evidence_json,'$.claim_id')=json_extract(NEW.evidence_json,'$.claim_id')
    AND json_extract(r.evidence_json,'$.worker_identity_digest')=json_extract(NEW.evidence_json,'$.worker_identity_digest'))
BEGIN SELECT RAISE(ABORT,'cleanup verified event must match re-verification evidence'); END;

-- Request and answer payloads are bounded auxiliary content only. Lifecycle
-- state is authoritative solely in manager_operations + immutable events.
CREATE TABLE manager_interaction_payloads (
  operation_id TEXT NOT NULL,
  request_id TEXT NOT NULL CHECK(length(request_id) BETWEEN 1 AND 512),
  task_id TEXT NOT NULL,
  attempt INTEGER NOT NULL CHECK(attempt>=1),
  generation INTEGER NOT NULL CHECK(generation>=1),
  claim_id TEXT NOT NULL,
  worker_identity_digest TEXT NOT NULL CHECK(length(worker_identity_digest)=64),
  request_method TEXT NOT NULL CHECK(request_method IN ('interaction/requestPermission','interaction/requestUserInput')),
  request_json TEXT NOT NULL CHECK(json_valid(request_json) AND json_type(request_json)='object' AND length(CAST(request_json AS BLOB))<=1048576),
  request_digest TEXT NOT NULL CHECK(length(request_digest)=64),
  answer_json TEXT CHECK(answer_json IS NULL OR (json_valid(answer_json) AND json_type(answer_json)='object' AND length(CAST(answer_json AS BLOB))<=20000)),
  answer_digest TEXT CHECK(answer_digest IS NULL OR length(answer_digest)=64),
  reply_id TEXT UNIQUE,
  PRIMARY KEY(operation_id,request_id),
  FOREIGN KEY(operation_id) REFERENCES manager_operations(operation_id),
  CHECK ((answer_json IS NULL AND answer_digest IS NULL AND reply_id IS NULL)
      OR (answer_json IS NOT NULL AND answer_digest IS NOT NULL AND reply_id IS NOT NULL))
) STRICT;
CREATE TRIGGER interaction_payload_insert_guard BEFORE INSERT ON manager_interaction_payloads
WHEN NOT EXISTS (
  SELECT 1 FROM manager_operations o JOIN tasks t ON t.task_id=o.task_id
    JOIN attempts a ON a.task_id=t.task_id AND a.attempt=o.attempt
  WHERE o.operation_id=NEW.operation_id AND o.operation_kind='attempt_lifecycle' AND o.phase='running'
    AND o.task_id=NEW.task_id AND o.attempt=NEW.attempt AND o.generation=NEW.generation
    AND o.claim_id=NEW.claim_id AND o.claim_generation=NEW.generation
    AND o.claim_worker_identity_digest=NEW.worker_identity_digest
    AND t.current_attempt=o.attempt AND t.status='running' AND a.status='running' AND a.generation=o.generation
)
BEGIN SELECT RAISE(ABORT,'interaction payload identity mismatch'); END;
CREATE TRIGGER interaction_payload_update_guard BEFORE UPDATE ON manager_interaction_payloads
WHEN NEW.operation_id IS NOT OLD.operation_id OR NEW.request_id IS NOT OLD.request_id
 OR NEW.task_id IS NOT OLD.task_id OR NEW.attempt IS NOT OLD.attempt OR NEW.generation IS NOT OLD.generation
 OR NEW.claim_id IS NOT OLD.claim_id OR NEW.worker_identity_digest IS NOT OLD.worker_identity_digest
 OR NEW.request_method IS NOT OLD.request_method OR NEW.request_json IS NOT OLD.request_json OR NEW.request_digest IS NOT OLD.request_digest
 OR OLD.answer_json IS NOT NULL OR NEW.answer_json IS NULL OR NEW.answer_digest IS NULL OR NEW.reply_id IS NULL
 OR NOT EXISTS (SELECT 1 FROM manager_operations o JOIN tasks t ON t.task_id=o.task_id
   JOIN attempts a ON a.task_id=t.task_id AND a.attempt=o.attempt
   WHERE o.operation_id=NEW.operation_id AND o.phase='running' AND o.task_id=NEW.task_id AND o.attempt=NEW.attempt
     AND o.generation=NEW.generation AND o.claim_id=NEW.claim_id AND o.claim_worker_identity_digest=NEW.worker_identity_digest
     AND t.current_attempt=o.attempt AND t.status='running' AND a.status='running' AND a.generation=o.generation)
BEGIN SELECT RAISE(ABORT,'interaction payload is immutable'); END;
CREATE TRIGGER interaction_payload_no_delete BEFORE DELETE ON manager_interaction_payloads BEGIN SELECT RAISE(ABORT,'interaction payload is immutable'); END;
CREATE TRIGGER interaction_event_phase_guard BEFORE INSERT ON manager_operation_events
WHEN NEW.event_type IN ('interaction_requested','interaction_reply_intent','interaction_reply_prepared','interaction_reply_committed','interaction_reply_accepted')
 AND NOT (NEW.from_phase='running' AND NEW.to_phase='running')
BEGIN SELECT RAISE(ABORT,'interaction event phase violation'); END;
CREATE TRIGGER interaction_event_payload_guard BEFORE INSERT ON manager_operation_events
WHEN NEW.event_type='interaction_requested' AND NOT EXISTS (
  SELECT 1 FROM manager_interaction_payloads p WHERE p.operation_id=NEW.operation_id
    AND p.request_id=json_extract(NEW.evidence_json,'$.request_id') AND p.generation=NEW.generation
    AND p.claim_id=json_extract(NEW.evidence_json,'$.claim_id')
    AND p.worker_identity_digest=json_extract(NEW.evidence_json,'$.worker_identity_digest')
    AND p.request_digest=json_extract(NEW.evidence_json,'$.request_digest')
    AND p.request_method=json_extract(NEW.evidence_json,'$.request_method'))
 OR NEW.event_type='interaction_reply_intent' AND NOT EXISTS (
  SELECT 1 FROM manager_interaction_payloads p WHERE p.operation_id=NEW.operation_id
    AND p.request_id=json_extract(NEW.evidence_json,'$.request_id') AND p.generation=NEW.generation
    AND p.claim_id=json_extract(NEW.evidence_json,'$.claim_id')
    AND p.worker_identity_digest=json_extract(NEW.evidence_json,'$.worker_identity_digest')
    AND p.reply_id=json_extract(NEW.evidence_json,'$.reply_id')
    AND p.answer_digest=json_extract(NEW.evidence_json,'$.answer_digest'))
 OR NEW.event_type='interaction_reply_prepared' AND NOT EXISTS (
  SELECT 1 FROM manager_interaction_payloads p JOIN manager_operation_events i
    ON i.operation_id=p.operation_id AND i.event_type='interaction_reply_intent'
      AND json_extract(i.evidence_json,'$.request_id')=p.request_id
  WHERE p.operation_id=NEW.operation_id AND p.request_id=json_extract(NEW.evidence_json,'$.request_id')
    AND p.generation=NEW.generation AND p.claim_id=json_extract(NEW.evidence_json,'$.claim_id')
    AND p.worker_identity_digest=json_extract(NEW.evidence_json,'$.worker_identity_digest')
    AND p.reply_id=json_extract(NEW.evidence_json,'$.reply_id')
    AND p.answer_digest=json_extract(NEW.evidence_json,'$.answer_digest')
    AND i.sequence<NEW.sequence AND json_extract(i.evidence_json,'$.reply_id')=p.reply_id
    AND json_extract(i.evidence_json,'$.answer_digest')=p.answer_digest)
 OR NEW.event_type='interaction_reply_committed' AND NOT EXISTS (
  SELECT 1 FROM manager_interaction_payloads p JOIN manager_operation_events i
    ON i.operation_id=p.operation_id AND i.event_type='interaction_reply_intent'
      AND json_extract(i.evidence_json,'$.request_id')=p.request_id
    JOIN manager_operation_events prep ON prep.operation_id=p.operation_id AND prep.event_type='interaction_reply_prepared'
      AND json_extract(prep.evidence_json,'$.request_id')=p.request_id
  WHERE p.operation_id=NEW.operation_id AND p.request_id=json_extract(NEW.evidence_json,'$.request_id')
    AND p.generation=NEW.generation AND p.claim_id=json_extract(NEW.evidence_json,'$.claim_id')
    AND p.worker_identity_digest=json_extract(NEW.evidence_json,'$.worker_identity_digest')
    AND p.reply_id=json_extract(NEW.evidence_json,'$.reply_id')
    AND p.answer_digest=json_extract(NEW.evidence_json,'$.answer_digest')
    AND i.sequence<prep.sequence AND prep.sequence<NEW.sequence
    AND json_extract(prep.evidence_json,'$.prepared_digest')=json_extract(NEW.evidence_json,'$.prepared_digest'))
 OR NEW.event_type='interaction_reply_accepted' AND NOT EXISTS (
  SELECT 1 FROM manager_interaction_payloads p JOIN manager_operation_events i
    ON i.operation_id=p.operation_id AND i.event_type='interaction_reply_intent'
      AND json_extract(i.evidence_json,'$.request_id')=p.request_id
    JOIN manager_operation_events c ON c.operation_id=p.operation_id AND c.event_type='interaction_reply_committed'
      AND json_extract(c.evidence_json,'$.request_id')=p.request_id
    JOIN manager_operation_events prep ON prep.operation_id=p.operation_id AND prep.event_type='interaction_reply_prepared'
      AND json_extract(prep.evidence_json,'$.request_id')=p.request_id
  WHERE p.operation_id=NEW.operation_id AND p.request_id=json_extract(NEW.evidence_json,'$.request_id')
    AND p.generation=NEW.generation AND p.claim_id=json_extract(NEW.evidence_json,'$.claim_id')
    AND p.worker_identity_digest=json_extract(NEW.evidence_json,'$.worker_identity_digest')
    AND p.reply_id=json_extract(NEW.evidence_json,'$.reply_id')
    AND p.answer_digest=json_extract(NEW.evidence_json,'$.answer_digest')
    AND json_extract(i.evidence_json,'$.reply_id')=p.reply_id
    AND json_extract(i.evidence_json,'$.answer_digest')=p.answer_digest
    AND i.sequence<prep.sequence AND prep.sequence<c.sequence AND c.sequence<NEW.sequence
    AND json_extract(c.evidence_json,'$.commit_digest')=json_extract(NEW.evidence_json,'$.commit_digest'))
BEGIN SELECT RAISE(ABORT,'interaction event payload binding violation'); END;
