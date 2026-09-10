CREATE TABLE IF NOT EXISTS agent_templates (
    agent_template_id TEXT PRIMARY KEY CHECK (
        LENGTH(BTRIM(agent_template_id)) > 0
    ),
    name TEXT NOT NULL CHECK (
        LENGTH(BTRIM(name)) > 0
    ),
    description TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL CHECK (
        LENGTH(BTRIM(system_prompt)) > 0
    ),
    model_name TEXT NOT NULL CHECK (
        LENGTH(BTRIM(model_name)) > 0
    ),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (
        status IN ('draft', 'active', 'inactive')
    ),
    created_by_user_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (created_by_user_id)
        REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS agent_templates_status_name_index
ON agent_templates (
    status,
    name
);