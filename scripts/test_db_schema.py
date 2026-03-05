"""DB 스키마 init.sql 구조 검증 테스트."""
from pathlib import Path

INIT_SQL = Path(__file__).parent.parent / "db" / "init.sql"
SQL = INIT_SQL.read_text() if INIT_SQL.exists() else ""


class TestInitSql:
    def test_file_exists(self):
        assert INIT_SQL.exists()

    def test_deployments_table(self):
        assert "CREATE TABLE" in SQL and "deployments" in SQL

    def test_incidents_table(self):
        assert "incidents" in SQL

    def test_scenario_runs_table(self):
        assert "scenario_runs" in SQL

    def test_deployments_has_service_name(self):
        assert "service_name" in SQL

    def test_incidents_has_sensor_id_and_reason(self):
        assert "sensor_id" in SQL and "reason" in SQL

    def test_scenario_runs_has_scenario_and_profile(self):
        assert "scenario" in SQL and "profile" in SQL

    def test_has_timestamps(self):
        assert "TIMESTAMPTZ" in SQL or "TIMESTAMP" in SQL
