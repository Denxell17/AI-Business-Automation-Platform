-- Additive only. Advanced assistant remains disabled until explicitly enabled.
CREATE TABLE IF NOT EXISTS assistant_entries (
    entry_id TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    session_version BIGINT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('chat', 'action', 'usage')),
    payload TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assistant_user ON assistant_entries(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_assistant_expiry ON assistant_entries(expires_at);
CREATE TABLE IF NOT EXISTS assistant_budgets (
    scope TEXT NOT NULL,
    day TEXT NOT NULL,
    used BIGINT NOT NULL CHECK (used > 0),
    PRIMARY KEY (scope, day)
);
