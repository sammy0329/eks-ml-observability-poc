"""Grafana 프로비저닝·대시보드 구조 검증 테스트."""
import json
from pathlib import Path

import yaml

OBS = Path(__file__).parent.parent / "observability" / "grafana"
DATASOURCE_YML = OBS / "provisioning" / "datasources" / "prometheus.yml"
DASHBOARD_PROVIDER_YML = OBS / "provisioning" / "dashboards" / "provider.yml"
DASHBOARD_JSON = OBS / "dashboards" / "inference-api.json"


def load_yaml(path):
    with path.open() as f:
        return yaml.safe_load(f)


def load_json(path):
    with path.open() as f:
        return json.load(f)


# ── Task 3.2.1: 프로비저닝 설정 ─────────────────────────────────────────────

class TestDatasourceProvisioning:
    def test_datasource_file_exists(self):
        assert DATASOURCE_YML.exists()

    def test_datasource_is_prometheus(self):
        cfg = load_yaml(DATASOURCE_YML)
        ds_list = cfg.get("datasources", [])
        types = [ds["type"] for ds in ds_list]
        assert "prometheus" in types

    def test_datasource_url_points_to_prometheus(self):
        cfg = load_yaml(DATASOURCE_YML)
        for ds in cfg["datasources"]:
            if ds["type"] == "prometheus":
                assert "prometheus" in ds["url"]

    def test_datasource_is_default(self):
        cfg = load_yaml(DATASOURCE_YML)
        for ds in cfg["datasources"]:
            if ds["type"] == "prometheus":
                assert ds.get("isDefault") is True


class TestDashboardProvider:
    def test_provider_file_exists(self):
        assert DASHBOARD_PROVIDER_YML.exists()

    def test_provider_has_providers(self):
        cfg = load_yaml(DASHBOARD_PROVIDER_YML)
        assert "providers" in cfg
        assert len(cfg["providers"]) >= 1

    def test_provider_points_to_dashboards_dir(self):
        cfg = load_yaml(DASHBOARD_PROVIDER_YML)
        paths = [p.get("options", {}).get("path", "") for p in cfg["providers"]]
        assert any("dashboards" in p for p in paths)


# ── Task 3.2.2: 대시보드 JSON ────────────────────────────────────────────────

class TestDashboardJson:
    def _dashboard(self):
        return load_json(DASHBOARD_JSON)

    def _panels(self):
        db = self._dashboard()
        panels = []
        for item in db.get("panels", []):
            if item.get("type") == "row":
                panels.extend(item.get("panels", []))
            else:
                panels.append(item)
        return panels

    def test_dashboard_file_exists(self):
        assert DASHBOARD_JSON.exists()

    def test_dashboard_has_title(self):
        assert self._dashboard().get("title")

    def test_dashboard_has_at_least_8_panels(self):
        assert len(self._panels()) >= 8

    def test_rps_panel_exists(self):
        titles = [p.get("title", "").lower() for p in self._panels()]
        assert any("rps" in t or "request" in t for t in titles)

    def test_error_rate_panel_exists(self):
        titles = [p.get("title", "").lower() for p in self._panels()]
        assert any("error" in t for t in titles)

    def test_latency_panel_exists(self):
        titles = [p.get("title", "").lower() for p in self._panels()]
        assert any("latency" in t or "p95" in t for t in titles)

    def test_missing_rate_panel_exists(self):
        titles = [p.get("title", "").lower() for p in self._panels()]
        assert any("missing" in t for t in titles)

    def test_drift_score_panel_exists(self):
        titles = [p.get("title", "").lower() for p in self._panels()]
        assert any("drift" in t for t in titles)

    def test_anomaly_rate_panel_exists(self):
        titles = [p.get("title", "").lower() for p in self._panels()]
        assert any("anomaly" in t for t in titles)

    def test_panels_reference_prometheus_datasource(self):
        for panel in self._panels():
            ds = panel.get("datasource")
            if ds and isinstance(ds, dict):
                assert ds.get("type") == "prometheus"

    def test_dashboard_has_time_range(self):
        db = self._dashboard()
        assert "time" in db
        assert "from" in db["time"]
        assert "to" in db["time"]
