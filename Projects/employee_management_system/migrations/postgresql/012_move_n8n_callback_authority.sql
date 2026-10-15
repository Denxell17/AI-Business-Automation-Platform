ALTER TABLE n8n_demo_events
ADD COLUMN outcome_attempt INTEGER NOT NULL DEFAULT 0 CHECK (
    outcome_attempt >= 0 AND outcome_attempt <= attempt_count
),
ADD COLUMN callback_attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (
    callback_attempt_count >= 0
);
