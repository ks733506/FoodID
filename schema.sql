-- items table for pantry/inventory entries
--
-- Notes:
-- - `created_at` and `updated_at` default to the current timestamp at
--   insertion time. The trigger below updates `updated_at` automatically
--   when rows are modified.
-- - The trigger is written to avoid unbounded recursion: it only runs when
--   the `updated_at` value was not explicitly changed by the UPDATE statement.
--   This keeps the implementation simple while ensuring `updated_at` reflects
--   the last modification time.

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity >= 0),
  created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

-- Optional index to speed up lookups by name (useful for UI search/filtering)
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);

-- Trigger to update updated_at on row update.
-- The WHEN clause ensures the trigger only fires when the UPDATE did not
-- already set a new `updated_at` value. This prevents the trigger from
-- repeatedly updating the row and looping.
CREATE TRIGGER IF NOT EXISTS items_updated_at
AFTER UPDATE ON items
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
