-- Ledger schema for PostgreSQL 11 or newer.
--
-- Amounts are whole numbers in the smallest unit the app uses: cents, coins, points.
-- accounts.balance is a cache of SUM(ledger.amount) for that account. Only the posting
-- function writes it, in the same transaction as the ledger row.
--
-- If the balance already lives on another table (for example users.balance), keep it
-- there: remove the accounts table below and point ledger.account_id at that table.
-- If one owner can hold several balances (coins and gems, USD and EUR), add owner and
-- unit columns to accounts with UNIQUE (owner_id, unit). Never add up different units.

CREATE TABLE accounts (
  id       BIGINT PRIMARY KEY,
  balance  BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE ledger (
  id           BIGSERIAL PRIMARY KEY,
  account_id   BIGINT NOT NULL REFERENCES accounts (id),
  amount       BIGINT NOT NULL CHECK (amount <> 0),
  kind         TEXT NOT NULL CHECK (kind <> ''),
  ref          TEXT NOT NULL CHECK (ref <> ''),
  actor        TEXT NOT NULL DEFAULT 'system',
  note         TEXT,
  reverses_id  BIGINT REFERENCES ledger (id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ledger_kind_ref_unique UNIQUE (kind, ref)
);

CREATE INDEX ledger_account_created ON ledger (account_id, created_at, id);
CREATE INDEX ledger_reverses ON ledger (reverses_id) WHERE reverses_id IS NOT NULL;

-- Corrections are new entries. A row that could be edited or deleted is not evidence.
CREATE FUNCTION ledger_is_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'ledger rows are append-only: post a correcting entry instead';
END;
$$;

CREATE TRIGGER ledger_no_update_or_delete
  BEFORE UPDATE OR DELETE ON ledger
  FOR EACH ROW EXECUTE FUNCTION ledger_is_append_only();

CREATE TRIGGER ledger_no_truncate
  BEFORE TRUNCATE ON ledger
  FOR EACH STATEMENT EXECUTE FUNCTION ledger_is_append_only();
