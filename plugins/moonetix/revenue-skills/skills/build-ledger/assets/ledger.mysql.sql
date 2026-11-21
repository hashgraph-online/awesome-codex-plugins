-- Ledger schema for MySQL 8.0.16 or newer and MariaDB 10.4 or newer (InnoDB).
--
-- Amounts are whole numbers in the smallest unit the app uses: cents, coins, points.
-- accounts.balance is a cache of SUM(ledger.amount) for that account. Only the posting
-- function writes it, in the same transaction as the ledger row.
--
-- If the balance already lives on another table (for example users.balance), keep it
-- there: remove the accounts table below and point ledger.account_id at that table,
-- with the same column type as that table's key.
-- If one owner can hold several balances (coins and gems, USD and EUR), add owner and
-- unit columns to accounts with UNIQUE (owner_id, unit). Never add up different units.
--
-- Older MySQL versions parse CHECK constraints and ignore them. On those, the posting
-- function is the only guard against a zero amount.

CREATE TABLE accounts (
  id       BIGINT UNSIGNED NOT NULL,
  balance  BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

-- kind and ref use a binary collation. The default collations ignore case, which would
-- make the ids "tx_AbC" and "tx_abc" collide on the unique key.
-- created_at is DATETIME, which stores what the session clock says: connect in UTC.
CREATE TABLE ledger (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  account_id   BIGINT UNSIGNED NOT NULL,
  amount       BIGINT NOT NULL,
  kind         VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  ref          VARCHAR(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  actor        VARCHAR(191) NOT NULL DEFAULT 'system',
  note         VARCHAR(500) NULL,
  reverses_id  BIGINT UNSIGNED NULL,
  created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY ledger_kind_ref_unique (kind, ref),
  KEY ledger_account_created (account_id, created_at, id),
  KEY ledger_reverses (reverses_id),
  CONSTRAINT ledger_account_fk FOREIGN KEY (account_id) REFERENCES accounts (id),
  CONSTRAINT ledger_reverses_fk FOREIGN KEY (reverses_id) REFERENCES ledger (id),
  CONSTRAINT ledger_amount_nonzero CHECK (amount <> 0),
  CONSTRAINT ledger_kind_present CHECK (kind <> ''),
  CONSTRAINT ledger_ref_present CHECK (ref <> '')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Corrections are new entries. A row that could be edited or deleted is not evidence.
-- TRUNCATE fires no trigger: do not grant DROP on this table to the application user.
CREATE TRIGGER ledger_no_update BEFORE UPDATE ON ledger
FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ledger rows are append-only';

CREATE TRIGGER ledger_no_delete BEFORE DELETE ON ledger
FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ledger rows are append-only';
