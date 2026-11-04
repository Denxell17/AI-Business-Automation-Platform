CREATE TABLE IF NOT EXISTS assistant_demo_leads (
    lead_id TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    name TEXT NOT NULL CHECK (name = 'Synthetic Demo Lead'),
    company TEXT NOT NULL CHECK (company = 'Fictional Company'),
    stage TEXT NOT NULL CHECK (stage = 'new'),
    created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assistant_demo_leads_user ON assistant_demo_leads(user_id);
CREATE TABLE IF NOT EXISTS assistant_demo_entries (
    entry_id TEXT PRIMARY KEY REFERENCES assistant_entries(entry_id) ON DELETE CASCADE
);
