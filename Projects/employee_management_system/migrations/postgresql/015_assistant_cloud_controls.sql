CREATE TABLE IF NOT EXISTS assistant_cloud_control (
    control_id INTEGER PRIMARY KEY CHECK (control_id = 1)
);
INSERT INTO assistant_cloud_control(control_id) VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS assistant_cloud_leases (
    lease_id TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    model_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    expires_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assistant_cloud_lease_expiry ON assistant_cloud_leases(expires_at);
CREATE TABLE IF NOT EXISTS assistant_cloud_status (
    scope TEXT PRIMARY KEY,
    unavailable_until BIGINT NOT NULL,
    reason TEXT NOT NULL
);
