-- Subscription entitlements, PostgreSQL. Adapt names and key types to the project.
--
-- MySQL: TEXT keys become VARCHAR(255) with a binary collation (utf8mb4_bin), because the
-- default collations ignore case and two provider ids that differ only in case would collide.
-- BIGINT stays, TIMESTAMPTZ becomes DATETIME(3) in UTC, the partial index becomes a plain index.
-- SQLite: BIGINT and TEXT work as written; store times as integer Unix seconds.
--
-- Times are the provider's, stored as UTC. Never compare them with a local-time column.

-- One row per subscription at the provider. A user may have several; access is the union.
CREATE TABLE subscriptions (
  provider               TEXT        NOT NULL,           -- 'stripe', 'app_store', 'google_play', 'paddle', 'revenuecat'
  provider_id            TEXT        NOT NULL,           -- sub_..., originalTransactionId, purchase token, sub_..., app user + entitlement
  user_id                BIGINT      NOT NULL,           -- from the app's own checkout record, never from the event
  plan                   TEXT        NOT NULL,           -- the app's plan, mapped from the provider's price or product id
  status                 TEXT        NOT NULL,           -- the provider's status, as the provider spells it
  period_start           TIMESTAMPTZ,                    -- start of the current period at the provider
  paid_through           TIMESTAMPTZ,                    -- end of the last period that was paid
  grace_until            TIMESTAMPTZ,                    -- set while a renewal payment is being retried
  cancel_at_period_end   BOOLEAN     NOT NULL DEFAULT false,
  trial                  BOOLEAN     NOT NULL DEFAULT false,
  revoked_at             TIMESTAMPTZ,                    -- refund, chargeback or revocation: access ends here
  revoked_reason         TEXT,
  provider_version       BIGINT      NOT NULL DEFAULT 0, -- the provider's ordering value, or the time the object was fetched (ms)
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, provider_id)
);
CREATE INDEX subscriptions_user ON subscriptions (user_id);

-- Links a provider subscription to the account that started the checkout. Written before the
-- user is sent to the provider, read when the first event or the reconciliation job sees the
-- subscription.
CREATE TABLE subscription_checkouts (
  id          TEXT        PRIMARY KEY,                   -- passed to the provider: metadata, appAccountToken, obfuscated account id
  user_id     BIGINT      NOT NULL,
  plan        TEXT        NOT NULL,
  status      TEXT        NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'expired')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One free trial per identity. The identity key comes from the sign-up guard: a normalized
-- email, a verified phone, a payment fingerprint or the store's own account.
CREATE TABLE trial_claims (
  identity_key  TEXT        PRIMARY KEY,
  user_id       BIGINT      NOT NULL,
  provider      TEXT        NOT NULL,
  provider_id   TEXT        NOT NULL,
  claimed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Verified events, as in the build-webhook-endpoint skill. The primary key makes a repeat a no-op.
CREATE TABLE subscription_events (
  provider     TEXT        NOT NULL,
  event_id     TEXT        NOT NULL,
  type         TEXT        NOT NULL,
  received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, event_id)
);

-- Credits per paid period go through the project's ledger, with the unique (kind, ref) key the
-- add-usage-credits and build-ledger skills use. The reference is built from the subscription and
-- the start of the period it paid for, for example 'stripe:sub_123:1763300000'.
