"""Prometheus·Alertmanager 설정 파일 구조 검증 테스트."""
from pathlib import Path

import yaml

OBS = Path(__file__).parent.parent / "observability"
PROMETHEUS_YML = OBS / "prometheus" / "prometheus.yml"
ALERTING_RULES_YML = OBS / "prometheus" / "alerting_rules.yml"
ALERTMANAGER_YML = OBS / "alertmanager" / "alertmanager.yml"


def load(path):
    with path.open() as f:
        return yaml.safe_load(f)


# ── Task 3.1.1: prometheus.yml ──────────────────────────────────────────────

class TestPrometheusConfig:
    def test_file_exists(self):
        assert PROMETHEUS_YML.exists()

    def test_has_scrape_configs(self):
        cfg = load(PROMETHEUS_YML)
        assert "scrape_configs" in cfg
        assert len(cfg["scrape_configs"]) >= 1

    def test_inference_api_target_registered(self):
        cfg = load(PROMETHEUS_YML)
        jobs = [j["job_name"] for j in cfg["scrape_configs"]]
        assert "inference-api" in jobs

    def test_scrape_interval_15s_or_less(self):
        cfg = load(PROMETHEUS_YML)
        interval = cfg.get("global", {}).get("scrape_interval", "60s")
        # "15s" → 15
        seconds = int(interval.rstrip("s"))
        assert seconds <= 15

    def test_references_alerting_rules(self):
        cfg = load(PROMETHEUS_YML)
        rule_files = cfg.get("rule_files", [])
        assert len(rule_files) >= 1

    def test_alertmanager_target_configured(self):
        cfg = load(PROMETHEUS_YML)
        alerting = cfg.get("alerting", {})
        managers = alerting.get("alertmanagers", [])
        assert len(managers) >= 1


# ── Task 3.1.2: alerting_rules.yml ─────────────────────────────────────────

class TestAlertingRules:
    def _rules(self):
        cfg = load(ALERTING_RULES_YML)
        rules = {}
        for group in cfg.get("groups", []):
            for rule in group.get("rules", []):
                rules[rule["alert"]] = rule
        return rules

    def test_file_exists(self):
        assert ALERTING_RULES_YML.exists()

    def test_has_groups(self):
        cfg = load(ALERTING_RULES_YML)
        assert "groups" in cfg
        assert len(cfg["groups"]) >= 1

    def test_high_error_rate_rule_exists(self):
        assert "HighErrorRate" in self._rules()

    def test_high_request_rate_rule_exists(self):
        assert "HighRequestRate" in self._rules()

    def test_high_missing_rate_rule_exists(self):
        assert "HighMissingRate" in self._rules()

    def test_all_rules_have_expr_and_for(self):
        for name, rule in self._rules().items():
            assert "expr" in rule, f"{name}: expr 없음"
            assert "for" in rule, f"{name}: for 없음"

    def test_all_rules_have_annotations(self):
        for name, rule in self._rules().items():
            assert "annotations" in rule, f"{name}: annotations 없음"
            assert "summary" in rule["annotations"], f"{name}: summary 없음"

    def test_high_error_rate_threshold(self):
        rule = self._rules()["HighErrorRate"]
        assert "0.01" in rule["expr"] or "1" in rule["expr"]

    def test_high_request_rate_threshold(self):
        # S1 로컬 리허설: 15 RPS 초과
        rule = self._rules()["HighRequestRate"]
        assert "15" in rule["expr"]
        assert "request_count_total" in rule["expr"]

    def test_high_missing_rate_threshold(self):
        rule = self._rules()["HighMissingRate"]
        assert "0.3" in rule["expr"]


# ── Task 3.1.3: alertmanager.yml ───────────────────────────────────────────

class TestAlertmanagerConfig:
    def test_file_exists(self):
        assert ALERTMANAGER_YML.exists()

    def test_has_route(self):
        cfg = load(ALERTMANAGER_YML)
        assert "route" in cfg

    def test_has_receivers(self):
        cfg = load(ALERTMANAGER_YML)
        assert "receivers" in cfg
        assert len(cfg["receivers"]) >= 1

    def test_route_has_receiver(self):
        cfg = load(ALERTMANAGER_YML)
        assert "receiver" in cfg["route"]

    def test_route_receiver_matches_defined_receiver(self):
        cfg = load(ALERTMANAGER_YML)
        route_receiver = cfg["route"]["receiver"]
        receiver_names = [r["name"] for r in cfg["receivers"]]
        assert route_receiver in receiver_names
