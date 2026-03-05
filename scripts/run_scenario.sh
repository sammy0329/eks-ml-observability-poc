#!/usr/bin/env bash
# run_scenario.sh — 로컬 리허설용 시나리오 실행 스크립트
#
# 사용법:
#   ./scripts/run_scenario.sh <시나리오> [duration]
#
# 시나리오:
#   s1   S1 부하 증가 (load 프로파일, RPS=50, duration=120s)
#        → request_latency_seconds p95 상승 + HighLatency 알람 발생 확인
#   s2   S2 에러 주입 (error 프로파일, error_ratio=0.3, duration=120s)
#        → error rate 상승 + HighErrorRate 알람 발생 확인
#   s3   S3 품질 저하 (quality_degradation 프로파일, missing_rate=0.4, duration=120s)
#        → input_missing_rate/drift_score 상승 + HighMissingRate 알람 발생 확인
#
# 사전 조건:
#   docker compose up -d (전체 스택 실행 중이어야 함)
#
# 알람 확인:
#   Prometheus: http://localhost:9090/alerts
#   Alertmanager: http://localhost:9093
#   Grafana:    http://localhost:3000

set -euo pipefail

SCENARIO="${1:-help}"
DURATION="${2:-120}"
COMPOSE_FILE="$(dirname "$0")/../docker-compose.yml"
PROJECT_DIR="$(dirname "$0")/.."

usage() {
  echo "사용법: $0 <s1|s2|s3> [duration_seconds]"
  echo ""
  echo "  s1  부하 증가 시나리오 (S1) — load 프로파일, RPS=50"
  echo "  s2  에러 주입 시나리오 (S2) — error 프로파일, error_ratio=0.3"
  echo "  s3  품질 저하 시나리오 (S3) — quality_degradation 프로파일"
  echo ""
  echo "예시: $0 s2 180"
  exit 1
}

run_sensor() {
  local profile="$1"
  local duration="$2"
  local sensor_id="$3"

  echo "=========================================="
  echo "시나리오 실행 중..."
  echo "  프로파일: ${profile}"
  echo "  duration: ${duration}s"
  echo "  sensor_id: ${sensor_id}"
  echo "=========================================="
  echo "메트릭 확인: http://localhost:9090"
  echo "알람 확인:   http://localhost:9090/alerts"
  echo "Grafana:     http://localhost:3000"
  echo ""

  docker compose -f "${COMPOSE_FILE}" run --rm \
    -e PROFILE="${profile}" \
    -e SENSOR_ID="${sensor_id}" \
    sensor-generator \
    python -m sensor_generator --profile "${profile}" \
      --url http://inference-api:8000 \
      --sensor-id "${sensor_id}" \
      --duration "${duration}"
}

case "${SCENARIO}" in
  s1|S1)
    echo "[S1] 부하 증가 시나리오 시작 (load 프로파일)"
    run_sensor "load" "${DURATION}" "sensor-s1-rehearsal"
    ;;
  s2|S2)
    echo "[S2] 에러 주입 시나리오 시작 (error 프로파일)"
    run_sensor "error" "${DURATION}" "sensor-s2-rehearsal"
    ;;
  s3|S3)
    echo "[S3] 품질 저하 시나리오 시작 (quality_degradation 프로파일)"
    run_sensor "quality_degradation" "${DURATION}" "sensor-s3-rehearsal"
    ;;
  *)
    usage
    ;;
esac

echo ""
echo "완료. Prometheus/Grafana에서 메트릭 변화를 확인하세요."
