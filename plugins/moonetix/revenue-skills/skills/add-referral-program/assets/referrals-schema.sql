-- Referral program schema for PostgreSQL 12 or newer.
--
-- It sits next to a ledger: accounts (id, balance) and ledger (account_id, amount, kind,
-- ref, created_at, UNIQUE (kind, ref)). Point the foreign keys at the project's own tables.
-- Rewards are posted to the ledger. These tables say who referred whom and where each
-- referral stands.
--
-- MySQL and SQLite differences are listed in references/codes-and-attribution.md.

-- One code per account that may refer others.
CREATE TABLE referral_codes (
  code        TEXT PRIMARY KEY,
  account_id  BIGINT NOT NULL UNIQUE REFERENCES accounts (id),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per referred account, written once in the sign-up transaction. The primary key
-- is the rule "an account has at most one referrer, for good".
CREATE TABLE referrals (
  referred_id     BIGINT PRIMARY KEY REFERENCES accounts (id),
  referrer_id     BIGINT NOT NULL REFERENCES accounts (id),
  code            TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'qualified', 'rewarded', 'reversed', 'blocked')),
  blocked_reason  TEXT,
  decided_by      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  qualified_at    TIMESTAMPTZ,
  reward_at       TIMESTAMPTZ,
  rewarded_at     TIMESTAMPTZ,
  CHECK (referred_id <> referrer_id)
);

CREATE INDEX referrals_referrer ON referrals (referrer_id, status);
CREATE INDEX referrals_due ON referrals (reward_at) WHERE status = 'qualified';

-- Facts that tie an account to a person or a device: a normalized email, a device id, a
-- network prefix, a payment fingerprint, a payout destination. Store hashes where the raw
-- value is not needed.
CREATE TABLE account_signals (
  account_id  BIGINT NOT NULL REFERENCES accounts (id),
  kind        TEXT NOT NULL,
  value       TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, kind, value)
);

CREATE INDEX account_signals_value ON account_signals (kind, value);

-- Only for a percentage of earnings. One row per earning of a referred account that paid
-- a commission. earning_ref is the reference of that earning in the ledger.
CREATE TABLE referral_commissions (
  earning_ref  TEXT PRIMARY KEY,
  referred_id  BIGINT NOT NULL REFERENCES referrals (referred_id),
  referrer_id  BIGINT NOT NULL REFERENCES accounts (id),
  amount       BIGINT NOT NULL CHECK (amount > 0),
  status       TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('posted', 'reversed')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX referral_commissions_referred ON referral_commissions (referred_id, status);
CREATE INDEX referral_commissions_referrer ON referral_commissions (referrer_id, created_at);
