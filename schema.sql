-- Schema for FoodID inventory application
--
-- items table stores pantry/inventory entries.
--
-- Notes:
-- - `created_at` and `updated_at` default to the current timestamp at insertion.
-- - The trigger below automatically updates `updated_at` whenever a row is modified.
-- - The WHEN clause prevents recursion: it only fires if `updated_at` was not
--   explicitly changed by the UPDATE statement. This ensures `updated_at` always
--   reflects the last modification time without looping.
-- - This schema matches the migration logic in db.py (index + trigger).

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity >= 0),
  created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

-- Index to speed up lookups by name (useful for UI search/filtering).
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);

-- Trigger to update `updated_at` on row update.
-- Fires only when the UPDATE did not explicitly set a new `updated_at` value.
-- This prevents infinite recursion and ensures `updated_at` reflects the last change.
CREATE TRIGGER IF NOT EXISTS items_updated_at
AFTER UPDATE ON items
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE items
  SET updated_at = CURRENT_TIMESTAMP
  WHERE id = OLD.id;
END;
