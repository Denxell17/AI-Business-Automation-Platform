ALTER TABLE workflows
ADD COLUMN n8n_enabled BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS webhook_deliveries_completed_at_index
ON webhook_deliveries (completed_at)
WHERE completed_at IS NOT NULL;
