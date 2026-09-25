CREATE TABLE IF NOT EXISTS webhook_replay_events (
    event_id TEXT PRIMARY KEY CHECK (
        LENGTH(BTRIM(event_id)) = 36
    ),
    received_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS webhook_replay_events_expiry_index
ON webhook_replay_events (expires_at);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    delivery_id TEXT PRIMARY KEY CHECK (
        LENGTH(BTRIM(delivery_id)) > 0
    ),
    direction TEXT NOT NULL CHECK (
        direction IN ('inbound', 'outbound')
    ),
    event_id TEXT NOT NULL CHECK (LENGTH(BTRIM(event_id)) = 36),
    correlation_id TEXT NOT NULL CHECK (
        LENGTH(BTRIM(correlation_id)) > 0
    ),
    event_type TEXT NOT NULL CHECK (LENGTH(BTRIM(event_type)) > 0),
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'retrying', 'accepted', 'succeeded', 'failed')
    ),
    attempt_count BIGINT NOT NULL CHECK (attempt_count >= 0),
    next_attempt_at TIMESTAMPTZ,
    response_status INTEGER CHECK (
        response_status IS NULL OR (response_status BETWEEN 100 AND 599)
    ),
    failure_code TEXT NOT NULL DEFAULT '' CHECK (
        LENGTH(failure_code) <= 64
    ),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (direction, event_id),
    CHECK (
        (direction = 'inbound' AND status = 'accepted'
         AND attempt_count = 1 AND next_attempt_at IS NULL)
        OR (direction = 'outbound'
            AND status IN ('pending', 'retrying', 'succeeded', 'failed'))
    )
);

CREATE INDEX IF NOT EXISTS webhook_deliveries_status_next_attempt_index
ON webhook_deliveries (status, next_attempt_at);
