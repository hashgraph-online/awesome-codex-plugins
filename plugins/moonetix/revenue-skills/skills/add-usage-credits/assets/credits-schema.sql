-- Usage credits schema for PostgreSQL 12 or newer.
--
-- Amounts are whole credits. If a price needs fractions, store a smaller unit
-- (1 displayed credit = 1000 stored) and keep every column an integer.
--
-- An account is whoever owns the credits: a user, a team or a workspace. Point
-- credit_accounts.account_id at that table and create the row when the owner is created.
--
-- credit_accounts.balance is a cache of SUM(credit_ledger.amount) for the account.
-- Only the ledger code writes it, in the same transaction as the ledger row.
-- credit_accounts.reserved is the sum of the account's open reservations.
-- What the account can spend right now is balance - reserved.
--
-- MySQL and SQLite differences are listed in references/credit-ledger.md.

CREATE TABLE credit_accounts (
  account_id  BIGINT PRIMARY KEY,
  balance     BIGINT NOT NULL DEFAULT 0,
  reserved    BIGINT NOT NULL DEFAULT 0 CHECK (reserved >= 0)
);

CREATE TABLE credit_ledger (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES credit_accounts (account_id),
  amount      BIGINT NOT NULL CHECK (amount <> 0),
  kind        TEXT NOT NULL,
  ref         TEXT NOT NULL,
  actor       TEXT NOT NULL DEFAULT 'system',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, ref)
);

CREATE INDEX credit_ledger_account ON credit_ledger (account_id, id);

-- One row per piece of metered work whose cost is known only afterwards.
-- status moves open -> committed or open -> released, once.
CREATE TABLE credit_reservations (
  id          TEXT PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES credit_accounts (account_id),
  feature     TEXT NOT NULL,
  amount      BIGINT NOT NULL CHECK (amount > 0),
  used        BIGINT CHECK (used >= 0 AND used <= amount),
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'committed', 'released')),
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  settled_at  TIMESTAMPTZ
);

CREATE INDEX credit_reservations_open ON credit_reservations (expires_at) WHERE status = 'open';

-- Only when some credits expire (a monthly allowance that resets, promotional credits
-- with an end date, packs with a validity period). One row per positive ledger entry.
-- remaining falls as credits are spent, oldest expiry first.
CREATE TABLE credit_grants (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES credit_accounts (account_id),
  kind        TEXT NOT NULL,
  ref         TEXT NOT NULL,
  amount      BIGINT NOT NULL CHECK (amount > 0),
  remaining   BIGINT NOT NULL CHECK (remaining >= 0 AND remaining <= amount),
  expires_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, ref)
);

CREATE INDEX credit_grants_spendable ON credit_grants (account_id, expires_at) WHERE remaining > 0;
