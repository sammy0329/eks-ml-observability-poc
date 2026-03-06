"""K8s 매니페스트 구조 검증 테스트."""
from pathlib import Path

import yaml

BASE = Path(__file__).parent.parent / "k8s" / "base"
HELM = Path(__file__).parent.parent / "k8s" / "helm-values"

ACCOUNT_ID = "523816102772"
REGION = "ap-northeast-2"
REGISTRY = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com"


def load(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


# ── inference-api ────────────────────────────────────────────────────────────

class TestInferenceApiDeployment:
    path = BASE / "inference-api" / "deployment.yaml"

    def test_file_exists(self):
        assert self.path.exists()

    def test_kind_is_deployment(self):
        assert load(self.path)["kind"] == "Deployment"

    def test_image_uses_ecr(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        image = containers[0]["image"]
        assert REGISTRY in image
        assert "inference-api" in image

    def test_container_port_8000(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        ports = [p["containerPort"] for p in containers[0]["ports"]]
        assert 8000 in ports

    def test_has_liveness_probe(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        assert "livenessProbe" in containers[0]

    def test_has_readiness_probe(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        assert "readinessProbe" in containers[0]

    def test_has_resource_limits(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        resources = containers[0]["resources"]
        assert "requests" in resources
        assert "limits" in resources

    def test_has_database_url_env(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        env_names = [e["name"] for e in containers[0].get("env", [])]
        assert "DATABASE_URL" in env_names


class TestInferenceApiService:
    path = BASE / "inference-api" / "service.yaml"

    def test_file_exists(self):
        assert self.path.exists()

    def test_kind_is_service(self):
        assert load(self.path)["kind"] == "Service"

    def test_port_8000(self):
        ports = load(self.path)["spec"]["ports"]
        assert any(p["port"] == 8000 for p in ports)


class TestInferenceApiHpa:
    path = BASE / "inference-api" / "hpa.yaml"

    def test_file_exists(self):
        assert self.path.exists()

    def test_kind_is_hpa(self):
        assert load(self.path)["kind"] == "HorizontalPodAutoscaler"

    def test_min_replicas(self):
        assert load(self.path)["spec"]["minReplicas"] == 1

    def test_max_replicas(self):
        assert load(self.path)["spec"]["maxReplicas"] == 5

    def test_cpu_target(self):
        metrics = load(self.path)["spec"]["metrics"]
        cpu_metrics = [m for m in metrics if m["type"] == "Resource"
                       and m["resource"]["name"] == "cpu"]
        assert len(cpu_metrics) == 1
        target = cpu_metrics[0]["resource"]["target"]
        assert target["averageUtilization"] == 50


# ── postgresql ───────────────────────────────────────────────────────────────

class TestPostgresql:
    def test_deployment_exists(self):
        assert (BASE / "postgresql" / "deployment.yaml").exists()

    def test_service_exists(self):
        assert (BASE / "postgresql" / "service.yaml").exists()

    def test_pvc_exists(self):
        assert (BASE / "postgresql" / "pvc.yaml").exists()

    def test_configmap_init_exists(self):
        assert (BASE / "postgresql" / "configmap-init.yaml").exists()

    def test_pvc_storage_request(self):
        pvc = load(BASE / "postgresql" / "pvc.yaml")
        storage = pvc["spec"]["resources"]["requests"]["storage"]
        assert storage  # 값이 있으면 통과

    def test_configmap_contains_schema(self):
        cm = load(BASE / "postgresql" / "configmap-init.yaml")
        data = list(cm["data"].values())[0]
        assert "CREATE TABLE" in data
        assert "deployments" in data
        assert "incidents" in data
        assert "scenario_runs" in data

    def test_service_port_5432(self):
        svc = load(BASE / "postgresql" / "service.yaml")
        ports = svc["spec"]["ports"]
        assert any(p["port"] == 5432 for p in ports)


# ── sensor-generator ─────────────────────────────────────────────────────────

class TestSensorGeneratorDeployment:
    path = BASE / "sensor-generator" / "deployment.yaml"

    def test_file_exists(self):
        assert self.path.exists()

    def test_kind_is_deployment(self):
        assert load(self.path)["kind"] == "Deployment"

    def test_image_uses_ecr(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        image = containers[0]["image"]
        assert REGISTRY in image
        assert "sensor-generator" in image

    def test_has_target_url_env(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        env_names = [e["name"] for e in containers[0].get("env", [])]
        assert "TARGET_URL" in env_names

    def test_has_profile_env(self):
        containers = load(self.path)["spec"]["template"]["spec"]["containers"]
        env_names = [e["name"] for e in containers[0].get("env", [])]
        assert "PROFILE" in env_names


# ── helm values ──────────────────────────────────────────────────────────────

class TestHelmValues:
    path = HELM / "kube-prometheus-stack.yaml"

    def test_file_exists(self):
        assert self.path.exists()

    def test_has_prometheus_section(self):
        assert "prometheus" in load(self.path)

    def test_has_grafana_section(self):
        assert "grafana" in load(self.path)

    def test_has_alertmanager_section(self):
        assert "alertmanager" in load(self.path)

    def test_grafana_admin_password_set(self):
        grafana = load(self.path)["grafana"]
        assert "adminPassword" in grafana

    def test_has_additional_rules(self):
        cfg = load(self.path)
        assert "additionalPrometheusRulesMap" in cfg
