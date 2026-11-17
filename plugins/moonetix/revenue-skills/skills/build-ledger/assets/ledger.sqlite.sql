-- Ledger schema for SQLite 3.24 or newer.
--
-- Amounts are whole numbers in the smallest unit the app uses: cents, coins, points.
-- accounts.balance is a cache of SUM(ledger.amount) for that account. Only the posting
-- function writes it, in the same transaction as the ledger row.
--
-- If the balance already lives on another table (for example users.balance), keep it
-- there: remove the accounts table below and point ledger.account_id at that table.
-- If one owner can hold several balances (coins and gems, USD and EUR), add owner and
-- unit columns to accounts with UNIQUE (owner_id, unit). Never add up different units.
--
-- SQLite enforces foreign keys only on connections that ran PRAGMA foreign_keys = ON.
-- Run it on every connection the application opens, not only here.

PRAGMA foreign_keys = ON;

CREATE TABLE accounts (
  id       INTEGER PRIMARY KEY,
  balance  INTEGER NOT NULL DEFAULT 0
);

-- created_at is Unix time in seconds, UTC.
CREATE TABLE ledger (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id   INTEGER NOT NULL REFERENCES accounts (id),
  amount       INTEGER NOT NULL CHECK (typeof(amount) = 'integer' AND amount <> 0),
  kind         TEXT NOT NULL CHECK (kind <> ''),
  ref          TEXT NOT NULL CHECK (ref <> ''),
  actor        TEXT NOT NULL DEFAULT 'system',
  note         TEXT,
  reverses_id  INTEGER REFERENCES ledger (id),
  created_at   INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER)),
  UNIQUE (kind, ref)
);

CREATE INDEX ledger_account_created ON ledger (account_id, created_at, id);
CREATE INDEX ledger_reverses ON ledger (reverses_id) WHERE reverses_id IS NOT NULL;

-- Corrections are new entries. A row that could be edited or deleted is not evidence.
CREATE TRIGGER ledger_no_update BEFORE UPDATE ON ledger
BEGIN
  SELECT RAISE(ABORT, 'ledger rows are append-only: post a correcting entry instead');
END;

CREATE TRIGGER ledger_no_delete BEFORE DELETE ON ledger
BEGIN
  SELECT RAISE(ABORT, 'ledger rows are append-only: post a correcting entry instead');
END;
