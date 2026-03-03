"""docker-compose.yml 구조 검증 테스트."""
from pathlib import Path

import yaml

COMPOSE_PATH = Path(__file__).parent.parent / "docker-compose.yml"


def load_compose():
    with COMPOSE_PATH.open() as f:
        return yaml.safe_load(f)


class TestComposeStructure:
    def test_compose_file_exists(self):
        assert COMPOSE_PATH.exists(), "docker-compose.yml 파일이 없습니다"

    def test_both_services_defined(self):
        cfg = load_compose()
        services = cfg["services"]
        assert "inference-api" in services
        assert "sensor-generator" in services

    def test_inference_api_port_8000(self):
        cfg = load_compose()
        ports = cfg["services"]["inference-api"].get("ports", [])
        assert any("8000" in str(p) for p in ports)

    def test_inference_api_has_healthcheck(self):
        cfg = load_compose()
        svc = cfg["services"]["inference-api"]
        assert "healthcheck" in svc

    def test_sensor_generator_target_url(self):
        cfg = load_compose()
        env = cfg["services"]["sensor-generator"].get("environment", {})
        if isinstance(env, list):
            env = dict(e.split("=", 1) for e in env)
        assert "TARGET_URL" in env
        assert "inference-api" in env["TARGET_URL"]

    def test_sensor_generator_profile_env(self):
        cfg = load_compose()
        env = cfg["services"]["sensor-generator"].get("environment", {})
        if isinstance(env, list):
            env = dict(e.split("=", 1) for e in env)
        assert "PROFILE" in env

    def test_sensor_generator_depends_on_inference_api(self):
        cfg = load_compose()
        depends = cfg["services"]["sensor-generator"].get("depends_on", {})
        if isinstance(depends, list):
            assert "inference-api" in depends
        else:
            assert "inference-api" in depends
