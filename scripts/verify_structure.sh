#!/usr/bin/env bash
# Task 1.1.1 DoD 검증 스크립트
# 실행: bash scripts/verify_structure.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

check() {
  local desc="$1"
  local path="$2"
  if [ -e "$ROOT/$path" ]; then
    echo "  [PASS] $desc"
    ((PASS++)) || true
  else
    echo "  [FAIL] $desc — $path 없음"
    ((FAIL++)) || true
  fi
}

echo "=== Task 1.1.1 DoD 검증 ==="
echo ""

echo "── 디렉토리 존재 여부 ──"
check "inference-api/" "inference-api"
check "inference-api/app/" "inference-api/app"
check "inference-api/tests/" "inference-api/tests"
check "sensor-generator/" "sensor-generator"
check "sensor-generator/sensor_generator/" "sensor-generator/sensor_generator"
check "sensor-generator/profiles/" "sensor-generator/profiles"
check "sensor-generator/tests/" "sensor-generator/tests"
check "observability/" "observability"
check "observability/prometheus/" "observability/prometheus"
check "observability/grafana/" "observability/grafana"
check "observability/grafana/dashboards/" "observability/grafana/dashboards"
check "observability/grafana/provisioning/" "observability/grafana/provisioning"
check "observability/alertmanager/" "observability/alertmanager"
check "k8s/" "k8s"
check "k8s/base/" "k8s/base"
check "k8s/helm-values/" "k8s/helm-values"
check "infra/" "infra"
check "infra/eksctl/" "infra/eksctl"
check "scripts/" "scripts"
check "docs/" "docs"

echo ""
echo "── __init__.py / .gitkeep 존재 여부 ──"
check "inference-api/app/__init__.py" "inference-api/app/__init__.py"
check "inference-api/tests/__init__.py" "inference-api/tests/__init__.py"
check "sensor-generator/sensor_generator/__init__.py" "sensor-generator/sensor_generator/__init__.py"
check "sensor-generator/tests/__init__.py" "sensor-generator/tests/__init__.py"
check "sensor-generator/profiles/.gitkeep" "sensor-generator/profiles/.gitkeep"
check "observability/prometheus/.gitkeep" "observability/prometheus/.gitkeep"
check "observability/grafana/dashboards/.gitkeep" "observability/grafana/dashboards/.gitkeep"
check "observability/grafana/provisioning/.gitkeep" "observability/grafana/provisioning/.gitkeep"
check "observability/alertmanager/.gitkeep" "observability/alertmanager/.gitkeep"
check "k8s/base/.gitkeep" "k8s/base/.gitkeep"
check "k8s/helm-values/.gitkeep" "k8s/helm-values/.gitkeep"
check "infra/eksctl/.gitkeep" "infra/eksctl/.gitkeep"
check "scripts/.gitkeep" "scripts/.gitkeep"

echo ""
echo "── .gitignore 존재 여부 ──"
check ".gitignore 파일" ".gitignore"

echo ""
echo "── README.md 디렉토리 구조 문서화 여부 ──"
if grep -q "inference-api" "$ROOT/README.md" 2>/dev/null; then
  echo "  [PASS] README.md에 디렉토리 구조 문서화됨"
  ((PASS++)) || true
else
  echo "  [FAIL] README.md에 디렉토리 구조 미문서화"
  ((FAIL++)) || true
fi

echo ""
echo "=== 결과: PASS $PASS / FAIL $FAIL ==="

if [ "$FAIL" -gt 0 ]; then
  exit 1
else
  echo "모든 DoD 조건 충족 ✓"
  exit 0
fi
