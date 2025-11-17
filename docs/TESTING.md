# Testing Evidence

| Test Case | Description | Steps | Expected Result | Actual Result |
|-----------|-------------|-------|-----------------|---------------|
| `test_health` | API health endpoint responds successfully | Send `GET /health` | 200 response with `{ "status": "ok" }` | ✅ PASS |
| `test_db_file_created` | Database initialization creates SQLite file | Call `init_db()` with temporary path | DB file exists on filesystem | ✅ PASS |
| `test_create_and_list_items` | Create item and list via API | `POST /items` then `GET /items` | New item appears in list | ✅ PASS |
| `test_get_item_by_id` | Retrieve item by ID | Create item, then `GET /items/<id>` | Response matches created record | ✅ PASS |
| `test_update_item` | Update name and quantity | Create item, `PUT /items/<id>` | Response reflects updated fields | ✅ PASS |
| `test_delete_item` | Delete item by ID | Create item, `DELETE /items/<id>`, then `GET /items/<id>` | Delete returns success message; subsequent GET returns 404 | ✅ PASS |

_All tests executed with:_

```bash
pytest -q
```

Date of latest run: 2025-11-10
