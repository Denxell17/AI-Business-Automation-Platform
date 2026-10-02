ALTER TABLE users
ADD COLUMN interface_language TEXT NOT NULL DEFAULT 'en'
CHECK (interface_language IN ('en', 'ja'));
