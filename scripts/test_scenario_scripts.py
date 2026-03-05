"""시나리오 실행 스크립트 및 alerting 룰 검증 테스트."""
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).parent
SCENARIO_SCRIPT = SCRIPTS_DIR / "run_scenario.sh"
ALERTING_RULES_PATH = SCRIPTS_DIR.parent / "observability" / "prometheus" / "alerting_rules.yml"
PROFILES_DIR = SCRIPTS_DIR.parent / "sensor-generator" / "profiles"


def load_alerting_rules():
    with ALERTING_RULES_PATH.open() as f:
        return yaml.safe_load(f)


class TestScenarioScript:
    def test_run_scenario_script_exists(self):
        assert SCENARIO_SCRIPT.exists(), "scripts/run_scenario.sh 파일이 없습니다"

    def test_script_is_executable(self):
        import stat
        mode = SCENARIO_SCRIPT.stat().st_mode
        assert mode & stat.S_IXUSR, "run_scenario.sh 실행 권한이 없습니다"

    def test_script_contains_s1_scenario(self):
        content = SCENARIO_SCRIPT.read_text()
        assert "s1" in content.lower() or "S1" in content or "load" in content

    def test_script_contains_s2_scenario(self):
        content = SCENARIO_SCRIPT.read_text()
        assert "s2" in content.lower() or "S2" in content or "error" in content

    def test_script_contains_s3_scenario(self):
        content = SCENARIO_SCRIPT.read_text()
        assert "s3" in content.lower() or "S3" in content or "quality" in content

    def test_script_references_docker_compose(self):
        content = SCENARIO_SCRIPT.read_text()
        assert "docker" in content.lower()


class TestAlertingRulesForRehearsal:
    def test_alerting_rules_file_exists(self):
        assert ALERTING_RULES_PATH.exists()

    def test_high_error_rate_for_duration_is_short(self):
        """리허설용: HighErrorRate for 기간이 2m 이하여야 함."""
        rules = load_alerting_rules()
        alert_rules = rules["groups"][0]["rules"]
        error_rule = next(r for r in alert_rules if r["alert"] == "HighErrorRate")
        # for 값 파싱 (예: "1m", "2m", "5m")
        for_val = error_rule.get("for", "5m")
        minutes = int(for_val.replace("m", ""))
        assert minutes <= 2, f"HighErrorRate for={for_val}; 리허설용 2m 이하 권장"

    def test_high_request_rate_for_duration_is_short(self):
        """리허설용: HighRequestRate for 기간이 2m 이하여야 함."""
        rules = load_alerting_rules()
        alert_rules = rules["groups"][0]["rules"]
        rr_rule = next(r for r in alert_rules if r["alert"] == "HighRequestRate")
        for_val = rr_rule.get("for", "5m")
        minutes = int(for_val.replace("m", ""))
        assert minutes <= 2, f"HighRequestRate for={for_val}; 리허설용 2m 이하 권장"

    def test_high_missing_rate_for_duration_is_short(self):
        """리허설용: HighMissingRate for 기간이 2m 이하여야 함."""
        rules = load_alerting_rules()
        alert_rules = rules["groups"][0]["rules"]
        missing_rule = next(r for r in alert_rules if r["alert"] == "HighMissingRate")
        for_val = missing_rule.get("for", "5m")
        minutes = int(for_val.replace("m", ""))
        assert minutes <= 2, f"HighMissingRate for={for_val}; 리허설용 2m 이하 권장"


class TestScenarioProfiles:
    def test_all_scenario_profiles_exist(self):
        for name in ["normal", "load", "error", "quality_degradation"]:
            path = PROFILES_DIR / f"{name}.yaml"
            assert path.exists(), f"프로파일 없음: {name}.yaml"

    def test_s1_load_profile_high_rps(self):
        """S1: load 프로파일 RPS가 충분히 높아야 함 (>=20)."""
        with (PROFILES_DIR / "load.yaml").open() as f:
            cfg = yaml.safe_load(f)
        assert cfg["rps"] >= 20, f"S1 rps={cfg['rps']}; 부하 시나리오는 20 RPS 이상 권장"

    def test_s2_error_profile_has_error_ratio(self):
        """S2: error 프로파일 error_ratio가 0.1 이상."""
        with (PROFILES_DIR / "error.yaml").open() as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("error_ratio", 0) >= 0.1, "S2 error_ratio가 너무 낮음"

    def test_s3_quality_degradation_profile_has_high_missing_rate(self):
        """S3: quality_degradation 프로파일 missing_rate가 0.3 초과."""
        with (PROFILES_DIR / "quality_degradation.yaml").open() as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("missing_rate", 0) > 0.3, "S3 missing_rate가 HighMissingRate 임계치 미달"
