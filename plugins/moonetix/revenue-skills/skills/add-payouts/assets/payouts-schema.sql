-- Payout schema for PostgreSQL 12 or newer.
--
-- It sits next to a ledger: accounts (id, balance) and ledger (account_id, amount, kind,
-- ref, created_at, UNIQUE (kind, ref)). Point the foreign keys at the project's own tables.
-- Amounts are whole numbers. payouts.amount is in the unit of the ledger, payout_minor is
-- what the provider is asked to send, in the minor unit of the currency (cents).
--
-- MySQL and SQLite differences are listed in references/payout-state-machine.md.

-- Where an account is paid. A changed destination is a new row, the old one is closed.
CREATE TABLE payout_destinations (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id   BIGINT NOT NULL REFERENCES accounts (id),
  method       TEXT NOT NULL,
  details      TEXT NOT NULL,
  fingerprint  TEXT NOT NULL,
  usable_from  TIMESTAMPTZ NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  removed_at   TIMESTAMPTZ
);

-- One open destination per account. Remove this index if users may keep several.
CREATE UNIQUE INDEX payout_destinations_open ON payout_destinations (account_id) WHERE removed_at IS NULL;
CREATE INDEX payout_destinations_fingerprint ON payout_destinations (fingerprint);

-- One row per withdrawal. The id is also the idempotency key sent to the provider and the
-- ref of the ledger entries 'payout' and 'payout_refund'.
CREATE TABLE payouts (
  id              TEXT PRIMARY KEY,
  account_id      BIGINT NOT NULL REFERENCES accounts (id),
  request_key     TEXT NOT NULL,
  amount          BIGINT NOT NULL CHECK (amount > 0),
  currency        TEXT NOT NULL,
  payout_minor    BIGINT NOT NULL CHECK (payout_minor > 0),
  destination_id  BIGINT NOT NULL REFERENCES payout_destinations (id),
  destination     TEXT NOT NULL,
  status          TEXT NOT NULL
                  CHECK (status IN ('in_review', 'pending', 'sending', 'paid', 'failed', 'rejected', 'canceled')),
  review_reason   TEXT,
  reviewed_by     TEXT,
  provider_ref    TEXT,
  failure_code    TEXT,
  attempts        INTEGER NOT NULL DEFAULT 0,
  next_check_at   TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at         TIMESTAMPTZ,
  settled_at      TIMESTAMPTZ,
  UNIQUE (account_id, request_key)
);

CREATE INDEX payouts_account ON payouts (account_id, created_at);
CREATE INDEX payouts_open ON payouts (status, next_check_at) WHERE status IN ('in_review', 'pending', 'sending');
