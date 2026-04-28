import json

from config.settings import Settings
from modules import idempotency
from modules.database import execute_query, init_database, migrate_database


def test_make_key_is_stable_for_dict_order():
    first = idempotency.make_key("query", {"b": 2, "a": 1}, "Hello   World")
    second = idempotency.make_key("query", {"a": 1, "b": 2}, "Hello World")

    assert first == second
    assert first.startswith("query:")


def test_idempotency_record_lifecycle(tmp_path, monkeypatch):
    db_path = tmp_path / "idempotency.db"
    monkeypatch.setattr(Settings, "DATABASE_PATH", str(db_path))
    init_database(str(db_path))
    migrate_database(str(db_path))

    key = idempotency.make_key("unit_operation", "same input")

    assert idempotency.start_operation("unit_operation", key) is True
    assert idempotency.start_operation("unit_operation", key) is False
    assert idempotency.get_completed_result("unit_operation", key) is None

    idempotency.complete_operation("unit_operation", key, {"answer": "done"})

    cached = idempotency.get_completed_result("unit_operation", key)
    assert cached["answer"] == "done"
    assert cached["idempotency_reused"] is True


def test_database_schema_version_adds_idempotency_workflow_and_auth_tables(tmp_path):
    db_path = tmp_path / "schema.db"
    init_database(str(db_path))
    migrate_database(str(db_path))

    tables = {
        row["name"]
        for row in execute_query(
            "SELECT name FROM sqlite_master WHERE type = ?",
            ("table",),
            str(db_path),
        )
    }
    version = execute_query("SELECT MAX(version) AS version FROM schema_version", db_path=str(db_path))
    query_log_columns = execute_query("PRAGMA table_info(query_logs)", db_path=str(db_path))

    assert "idempotency_keys" in tables
    assert "assessment_projects" in tables
    assert "dashboard_blueprints" in tables
    assert "training_materials" in tables
    assert version[0]["version"] == 7
    assert "idempotency_key" in {row["name"] for row in query_log_columns}


def test_database_schema_version_five_name_kept_for_backwards_compatibility(tmp_path):
    db_path = tmp_path / "schema_name_compat.db"
    init_database(str(db_path))
    migrate_database(str(db_path))

    tables = execute_query(
        "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
        ("table", "idempotency_keys"),
        str(db_path),
    )

    assert tables == [{"name": "idempotency_keys"}]


def test_completed_result_json_is_plain_json(tmp_path, monkeypatch):
    db_path = tmp_path / "json.db"
    monkeypatch.setattr(Settings, "DATABASE_PATH", str(db_path))
    init_database(str(db_path))

    key = idempotency.make_key("json_operation", {"value": 1})
    idempotency.start_operation("json_operation", key)
    idempotency.complete_operation("json_operation", key, {"items": {3, 1, 2}})

    row = execute_query(
        "SELECT result_json FROM idempotency_keys WHERE operation = ?",
        ("json_operation",),
        str(db_path),
    )[0]

    assert json.loads(row["result_json"]) == {"items": [1, 2, 3]}
