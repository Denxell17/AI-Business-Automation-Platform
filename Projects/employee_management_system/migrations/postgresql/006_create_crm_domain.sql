CREATE TABLE leads (
    lead_id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK (LENGTH(BTRIM(name)) BETWEEN 1 AND 120),
    email TEXT NOT NULL DEFAULT '',
    phone_number TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL CHECK (stage IN
        ('new', 'contacted', 'qualified', 'unqualified', 'converted')),
    owner_user_id BIGINT REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_leads_stage ON leads(stage);
CREATE INDEX idx_leads_owner ON leads(owner_user_id);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    source_lead_id TEXT NOT NULL UNIQUE REFERENCES leads(lead_id),
    name TEXT NOT NULL CHECK (LENGTH(BTRIM(name)) BETWEEN 1 AND 120),
    email TEXT NOT NULL DEFAULT '',
    phone_number TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE FUNCTION prevent_customer_source_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.source_lead_id IS DISTINCT FROM OLD.source_lead_id THEN
        RAISE EXCEPTION 'customer source is immutable';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER immutable_customer_source
BEFORE UPDATE OF source_lead_id ON customers
FOR EACH ROW EXECUTE FUNCTION prevent_customer_source_change();

CREATE TABLE lead_notes (
    note_id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL REFERENCES leads(lead_id),
    body TEXT NOT NULL CHECK (LENGTH(BTRIM(body)) BETWEEN 1 AND 2000),
    created_by_user_id BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_lead_notes_lead ON lead_notes(lead_id, created_at);

CREATE TABLE crm_audit_events (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('lead', 'customer')),
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN
        ('created', 'updated', 'note_added', 'converted')),
    actor_user_id BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_crm_audit_entity
ON crm_audit_events(entity_type, entity_id, created_at);
