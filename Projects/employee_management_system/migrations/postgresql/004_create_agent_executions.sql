CREATE TABLE IF NOT EXISTS agent_executions (
    agent_execution_id TEXT PRIMARY KEY CHECK (
        LENGTH(BTRIM(agent_execution_id)) > 0
    ),
    agent_template_id TEXT NOT NULL,
    agent_template_name TEXT NOT NULL CHECK (
        LENGTH(BTRIM(agent_template_name)) > 0
    ),
    model_name TEXT NOT NULL CHECK (
        LENGTH(BTRIM(model_name)) > 0
    ),
    status TEXT NOT NULL CHECK (
        status IN (
            'running',
            'completed',
            'failed'
        )
    ),
    input_text TEXT NOT NULL CHECK (
        LENGTH(BTRIM(input_text)) > 0
    ),
    output_text TEXT,
    error_message TEXT,
    requested_by_user_id BIGINT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    CHECK (
        (
            status = 'running'
            AND output_text IS NULL
            AND error_message IS NULL
            AND finished_at IS NULL
        )
        OR (
            status = 'completed'
            AND output_text IS NOT NULL
            AND LENGTH(BTRIM(output_text)) > 0
            AND error_message IS NULL
            AND finished_at IS NOT NULL
        )
        OR (
            status = 'failed'
            AND output_text IS NULL
            AND error_message IS NOT NULL
            AND LENGTH(BTRIM(error_message)) > 0
            AND finished_at IS NOT NULL
        )
    ),
    FOREIGN KEY (agent_template_id)
        REFERENCES agent_templates(agent_template_id),
    FOREIGN KEY (requested_by_user_id)
        REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS
    agent_executions_template_started_index
ON agent_executions (
    agent_template_id,
    started_at DESC
);

CREATE INDEX IF NOT EXISTS
    agent_executions_user_started_index
ON agent_executions (
    requested_by_user_id,
    started_at DESC
);