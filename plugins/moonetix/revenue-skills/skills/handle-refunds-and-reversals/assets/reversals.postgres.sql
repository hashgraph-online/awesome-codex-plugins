-- Records for refunds, disputes, reversed conversions and revocable grants.
-- PostgreSQL 11 or newer.
--
-- Each table stores a fact under the id the sender gave it, so the same fact is stored
-- once however often it is delivered. The ledger entries that follow from these facts are
-- posted by the reversal functions, never by hand.
--
-- The orders table is the project's own. Adapt the type of order_id and account_id to it.
-- The code needs four things from an order: who bought (account_id), what was paid
-- (price_cents, currency) and a row to lock.
--
-- MySQL and MariaDB: BIGINT UNSIGNED AUTO_INCREMENT for the id columns, VARCHAR(64) for
--   provider and source, VARCHAR(191) with COLLATE utf8mb4_bin for the id strings (the
--   default collations ignore case), DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) for the
--   timestamps. CHECK constraints are enforced from MySQL 8.0.16 and MariaDB 10.2.
-- SQLite: INTEGER PRIMARY KEY for the id columns and INTEGER Unix seconds for the timestamps.

-- One row per refund, as the provider reported it.
-- credits_taken is NULL until the refund has been applied to the ledger. It stays NULL
-- while the order is not credited yet: a refund can arrive before its payment.
CREATE TABLE refunds (
  id             BIGSERIAL PRIMARY KEY,
  provider       TEXT NOT NULL CHECK (provider <> ''),
  refund_id      TEXT NOT NULL CHECK (refund_id <> ''),
  order_id       TEXT NOT NULL REFERENCES orders (id),
  amount_cents   BIGINT NOT NULL CHECK (amount_cents > 0),
  credits_taken  BIGINT CHECK (credits_taken >= 0),
  received_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT refunds_provider_id_unique UNIQUE (provider, refund_id)
);

CREATE INDEX refunds_order ON refunds (order_id, id);

-- One row per dispute (chargeback). A dispute moves open -> won or open -> lost, once.
CREATE TABLE disputes (
  id             BIGSERIAL PRIMARY KEY,
  provider       TEXT NOT NULL CHECK (provider <> ''),
  dispute_id     TEXT NOT NULL CHECK (dispute_id <> ''),
  order_id       TEXT NOT NULL REFERENCES orders (id),
  status         TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'won', 'lost')),
  credits_taken  BIGINT CHECK (credits_taken >= 0),
  opened_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at      TIMESTAMPTZ,
  CONSTRAINT disputes_provider_id_unique UNIQUE (provider, dispute_id)
);

CREATE INDEX disputes_order ON disputes (order_id, id);

-- One row per conversion from a network that has no order on our side (an offer, a
-- reward callback). The credit and its reversal both write this row first, so they meet
-- on one key whichever arrives first.
--   credited:        the credit was posted
--   reversed:        credited, then taken back
--   reversed_early:  the reversal arrived first; the credit that follows posts nothing
CREATE TABLE conversions (
  source       TEXT NOT NULL CHECK (source <> ''),
  tx_id        TEXT NOT NULL CHECK (tx_id <> ''),
  account_id   BIGINT,
  amount       BIGINT CHECK (amount > 0),
  status       TEXT NOT NULL CHECK (status IN ('credited', 'reversed', 'reversed_early')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  reversed_at  TIMESTAMPTZ,
  PRIMARY KEY (source, tx_id)
);

CREATE INDEX conversions_early ON conversions (created_at) WHERE status = 'reversed_early';

-- What an order granted besides a balance: a plan, a license, an item, a seat.
-- Access checks read revoked_at at the time of use.
CREATE TABLE grants (
  id             BIGSERIAL PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES orders (id),
  account_id     BIGINT NOT NULL,
  item           TEXT NOT NULL CHECK (item <> ''),
  revoked_at     TIMESTAMPTZ,
  revoke_reason  TEXT CHECK (revoke_reason IN ('refund', 'dispute')),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT grants_order_item_unique UNIQUE (order_id, item),
  CONSTRAINT grants_reason_with_revoke CHECK ((revoked_at IS NULL) = (revoke_reason IS NULL))
);

CREATE INDEX grants_account ON grants (account_id) WHERE revoked_at IS NULL;
