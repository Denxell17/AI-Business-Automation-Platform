CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    invoice_number TEXT NOT NULL UNIQUE CHECK (LENGTH(BTRIM(invoice_number)) BETWEEN 1 AND 40),
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    status TEXT NOT NULL CHECK (status IN ('draft', 'sent', 'paid', 'void')),
    due_date DATE,
    subtotal_cents BIGINT NOT NULL CHECK (subtotal_cents >= 0),
    tax_cents BIGINT NOT NULL CHECK (tax_cents >= 0),
    total_cents BIGINT NOT NULL CHECK (total_cents = subtotal_cents + tax_cents),
    created_by_user_id BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_invoices_customer_created ON invoices(customer_id, created_at);
CREATE INDEX idx_invoices_status_due ON invoices(status, due_date);

CREATE TABLE invoice_line_items (
    line_item_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
    line_number BIGINT NOT NULL CHECK (line_number > 0),
    description TEXT NOT NULL CHECK (LENGTH(BTRIM(description)) BETWEEN 1 AND 300),
    quantity NUMERIC(12, 3) NOT NULL CHECK (quantity > 0),
    unit_price_cents BIGINT NOT NULL CHECK (unit_price_cents >= 0),
    tax_rate_basis_points BIGINT NOT NULL CHECK (tax_rate_basis_points BETWEEN 0 AND 10000),
    line_subtotal_cents BIGINT NOT NULL CHECK (line_subtotal_cents >= 0),
    line_tax_cents BIGINT NOT NULL CHECK (line_tax_cents >= 0),
    line_total_cents BIGINT NOT NULL CHECK (line_total_cents = line_subtotal_cents + line_tax_cents),
    UNIQUE (invoice_id, line_number)
);
CREATE INDEX idx_invoice_line_items_invoice ON invoice_line_items(invoice_id, line_number);

CREATE FUNCTION prevent_invoice_line_item_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'invoice line item is immutable';
END;
$$;
CREATE TRIGGER immutable_invoice_line_item_update
BEFORE UPDATE ON invoice_line_items
FOR EACH ROW EXECUTE FUNCTION prevent_invoice_line_item_change();

CREATE TABLE invoice_payment_events (
    event_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'sent', 'paid', 'void')),
    actor_user_id BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_invoice_payment_events_invoice ON invoice_payment_events(invoice_id, created_at);

CREATE TABLE protected_documents (
    document_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
    document_type TEXT NOT NULL CHECK (document_type = 'invoice_pdf'),
    storage_key TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL CHECK (LENGTH(BTRIM(filename)) BETWEEN 1 AND 120),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    byte_size BIGINT NOT NULL CHECK (byte_size BETWEEN 1 AND 2097152),
    content_sha256 TEXT NOT NULL CHECK (LENGTH(content_sha256) = 64),
    created_by_user_id BIGINT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (invoice_id, document_type)
);

CREATE TABLE invoice_workflow_runs (
    invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
    execution_id TEXT NOT NULL UNIQUE REFERENCES workflow_executions(execution_id),
    workflow_id TEXT NOT NULL REFERENCES workflows(workflow_id),
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (invoice_id, execution_id)
);
