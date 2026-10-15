CREATE TABLE n8n_demo_events (
    event_id UUID PRIMARY KEY,
    correlation_id VARCHAR(128) NOT NULL,
    workflow_id VARCHAR(128) NOT NULL,
    body_sha256 CHAR(64) NOT NULL,
    callback_event_id UUID NOT NULL UNIQUE,
    callback_occurred_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'accepted' CHECK (
        status IN ('accepted', 'processing', 'completed', 'dead')
    ),
    result_status VARCHAR(16) CHECK (
        result_status IS NULL OR result_status IN ('completed', 'failed')
    ),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    lease_expires_at TIMESTAMPTZ,
    failure_code VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CHECK (
        (status = 'completed' AND result_status IS NOT NULL AND completed_at IS NOT NULL)
        OR (status <> 'completed' AND completed_at IS NULL)
    )
);

CREATE INDEX n8n_demo_events_claim_index
ON n8n_demo_events (status, lease_expires_at, created_at);
