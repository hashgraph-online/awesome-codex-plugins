-- Tables for sign-up screening, held bonuses, promo codes and trial claims.
-- PostgreSQL. Adapt names and id types to the project. Notes for MySQL and SQLite are at the end.

-- The uniqueness key for accounts. Mail is still sent to users.email, the address as typed.
-- NULL is allowed so that existing duplicates can be left without a key (see the backfill notes).
ALTER TABLE users ADD COLUMN email_normalized TEXT;
CREATE UNIQUE INDEX users_email_normalized_key ON users (email_normalized);

-- One row per sign-up attempt, including refused ones. This is what support reads.
CREATE TABLE signup_assessments (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id        BIGINT,                       -- NULL when no account was created
  email_key      TEXT        NOT NULL,         -- keyed hash of the normalized address, '' when invalid
  ip             TEXT,
  network_prefix TEXT,
  score          INTEGER     NOT NULL,
  decision       TEXT        NOT NULL CHECK (decision IN ('allow', 'review', 'block')),
  reasons        JSONB       NOT NULL,         -- [{"code": "...", "points": 40, "detail": "..."}]
  created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX signup_assessments_user ON signup_assessments (user_id);
CREATE INDEX signup_assessments_created ON signup_assessments (created_at);

-- Fixed-window attempt counters. window_start is Unix seconds, computed by the application.
CREATE TABLE velocity_counters (
  rule         TEXT    NOT NULL,               -- 'ip-hour', 'ip-day', 'network-day', 'email-day'
  subject      TEXT    NOT NULL,               -- the address, the prefix, or the email key
  window_start BIGINT  NOT NULL,
  hits         INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (rule, subject, window_start)
);

-- A bonus is a promise first and a balance later. 'held' is not spendable.
CREATE TABLE bonus_grants (
  user_id     BIGINT      NOT NULL REFERENCES users (id),
  kind        TEXT        NOT NULL,            -- 'signup', or 'referral:<invited user id>'
  amount      BIGINT      NOT NULL CHECK (amount > 0),
  status      TEXT        NOT NULL CHECK (status IN ('held', 'released', 'void')),
  hold_reason TEXT,                            -- 'email_unverified', 'review', ...
  created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  decided_at  TIMESTAMPTZ,
  PRIMARY KEY (user_id, kind)
);

CREATE TABLE promo_codes (
  code            TEXT        PRIMARY KEY,     -- stored in upper case
  amount          BIGINT      NOT NULL CHECK (amount > 0),
  max_redemptions INTEGER     NOT NULL CHECK (max_redemptions > 0),
  redeemed        INTEGER     NOT NULL DEFAULT 0,
  expires_at      TIMESTAMPTZ,
  CHECK (redeemed >= 0 AND redeemed <= max_redemptions)
);

CREATE TABLE promo_redemptions (
  code       TEXT        NOT NULL REFERENCES promo_codes (code),
  user_id    BIGINT      NOT NULL REFERENCES users (id),
  amount     BIGINT      NOT NULL CHECK (amount > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (code, user_id)
);

-- One trial per identity, ever. No foreign key to users: the claim outlives the account.
CREATE TABLE trial_claims (
  product       TEXT        NOT NULL,
  identity_kind TEXT        NOT NULL,          -- 'email', 'card', 'phone'
  identity_key  TEXT        NOT NULL,          -- keyed hash of the normalized value
  user_id       BIGINT      NOT NULL,
  claimed_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (product, identity_kind, identity_key)
);

-- MySQL: use VARCHAR(191) for every TEXT column that is part of a key, JSON for JSONB,
--   DATETIME for TIMESTAMPTZ (store UTC), BIGINT AUTO_INCREMENT for the identity column.
--   CHECK constraints are enforced from 8.0.16; on older versions the application is the only guard.
-- SQLite: INTEGER PRIMARY KEY for the identity column, TEXT for JSONB and TIMESTAMPTZ.
--   ALTER TABLE cannot add a UNIQUE column, which is why the index is created separately above.
