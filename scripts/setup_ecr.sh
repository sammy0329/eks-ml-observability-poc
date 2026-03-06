#!/usr/bin/env bash
# ECR 리포지토리 생성 및 이미지 빌드/푸시 스크립트
# 사용법: ./scripts/setup_ecr.sh [push|create-only]
#   push         (기본값) 리포지토리 생성 + 이미지 빌드 + ECR 푸시
#   create-only  리포지토리 생성만 수행

set -euo pipefail

# ── 설정 ──────────────────────────────────────────────────────────────────────
REGION="ap-northeast-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
TAG="${IMAGE_TAG:-latest}"
MODE="${1:-push}"

REPOS=(
  "inference-api"
  "sensor-generator"
)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── ECR 로그인 ─────────────────────────────────────────────────────────────────
ecr_login() {
  echo "[1/3] ECR 로그인 ($REGISTRY)"
  aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin "$REGISTRY"
  echo "     ✓ 로그인 성공"
}

# ── ECR 리포지토리 생성 (이미 존재하면 스킵) ────────────────────────────────────
create_repositories() {
  echo "[2/3] ECR 리포지토리 생성"
  for repo in "${REPOS[@]}"; do
    if aws ecr describe-repositories \
         --repository-names "$repo" \
         --region "$REGION" \
         --output text > /dev/null 2>&1; then
      echo "     - ${repo}: 이미 존재 (스킵)"
    else
      aws ecr create-repository \
        --repository-name "$repo" \
        --region "$REGION" \
        --image-scanning-configuration scanOnPush=true \
        --output text > /dev/null
      echo "     + ${repo}: 생성 완료"
    fi
  done
}

# ── 이미지 빌드 및 푸시 ────────────────────────────────────────────────────────
build_and_push() {
  echo "[3/3] 이미지 빌드 및 푸시 (tag: $TAG)"

  # inference-api
  local api_image="${REGISTRY}/inference-api:${TAG}"
  echo "  → inference-api 빌드..."
  docker build \
    --platform linux/amd64 \
    -t "$api_image" \
    "${ROOT_DIR}/inference-api"
  echo "  → inference-api 푸시..."
  docker push "$api_image"
  echo "     ✓ inference-api: ${api_image}"

  # sensor-generator
  local sg_image="${REGISTRY}/sensor-generator:${TAG}"
  echo "  → sensor-generator 빌드..."
  docker build \
    --platform linux/amd64 \
    -t "$sg_image" \
    "${ROOT_DIR}/sensor-generator"
  echo "  → sensor-generator 푸시..."
  docker push "$sg_image"
  echo "     ✓ sensor-generator: ${sg_image}"
}

# ── 완료 메시지 ────────────────────────────────────────────────────────────────
print_summary() {
  echo ""
  echo "================================================"
  echo " ECR 설정 완료"
  echo "================================================"
  echo " Registry  : ${REGISTRY}"
  echo " Region    : ${REGION}"
  echo " Tag       : ${TAG}"
  echo ""
  echo " 이미지 URI:"
  for repo in "${REPOS[@]}"; do
    echo "   ${REGISTRY}/${repo}:${TAG}"
  done
  echo ""
  echo " 다음 단계: k8s 매니페스트에서 위 URI를 image 필드에 입력하세요."
  echo "================================================"
}

# ── 메인 ──────────────────────────────────────────────────────────────────────
main() {
  echo "================================================"
  echo " sensor-obs-poc ECR 설정"
  echo " Account: ${ACCOUNT_ID} / Region: ${REGION}"
  echo "================================================"
  echo ""

  ecr_login
  create_repositories

  if [[ "$MODE" == "push" ]]; then
    build_and_push
  else
    echo "[3/3] create-only 모드 — 이미지 빌드 생략"
  fi

  print_summary
}

main
