-- 内测名单（Cloudflare D1）。只存邮箱、邀请码、谁邀请的、语言、时间；不存 IP。
CREATE TABLE IF NOT EXISTS waitlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  ref TEXT UNIQUE NOT NULL,
  referred_by TEXT,
  lang TEXT,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_waitlist_referred_by ON waitlist(referred_by);
