-- Event store for a webhook endpoint, PostgreSQL 11 or newer.
--
-- One row per verified event that the endpoint acted on or refused. The primary key is
-- what makes a repeated delivery harmless: the second insert reports no row, and the
-- handler stops there. The row is written in the same transaction as the effect.
--
-- MySQL and MariaDB: use VARCHAR(64) for provider, VARCHAR(191) for event_id and type, both
--   with COLLATE utf8mb4_bin (the default collations ignore case, and the ids "evt_Ab" and
--   "evt_aB" would collide), DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) for received_at,
--   LONGTEXT for payload, and a plain index on (status, received_at).
-- SQLite: use INTEGER Unix seconds for received_at. Everything else works as written.

CREATE TABLE webhook_events (
  provider     TEXT NOT NULL CHECK (provider <> ''),
  event_id     TEXT NOT NULL CHECK (event_id <> ''),
  type         TEXT NOT NULL,
  -- received:  stored, waiting for the worker (only when events are processed from a queue)
  -- processed: the handler ran to the end and its transaction committed
  -- rejected:  genuine, but the content did not match the app's records; needs a person
  status       TEXT NOT NULL DEFAULT 'processed' CHECK (status IN ('received', 'processed', 'rejected')),
  detail       TEXT,
  payload      TEXT,
  received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, event_id)
);

CREATE INDEX webhook_events_open ON webhook_events (status, received_at) WHERE status <> 'processed';

-- Without a ledger, this table is the minimum that makes a credit happen once when the
-- event has no order row to close (a postback, a reward callback). Insert the key in the
-- same transaction as the balance update, and update only when the insert reported a row.
CREATE TABLE credited_transactions (
  source       TEXT NOT NULL CHECK (source <> ''),
  tx_id        TEXT NOT NULL CHECK (tx_id <> ''),
  account_id   BIGINT NOT NULL,
  amount       BIGINT NOT NULL CHECK (amount > 0),
  credited_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (source, tx_id)
);
