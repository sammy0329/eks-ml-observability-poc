# User Guide — EKS ML Observability PoC

> 이 가이드는 프로젝트를 **처음 실행하는 사람**을 위한 단계별 실행 매뉴얼입니다.
> 아키텍처·설계 배경은 [README](../README.md), 운영 결과는 [REPORT](REPORT.md)를 참조하세요.

---

## 사전 요구사항

### 필수 도구

| 도구 | 버전 | 설치 확인 |
|------|------|-----------|
| Python | 3.12+ | `python --version` |
| uv | 최신 | `uv --version` |
| Docker | 24+ | `docker --version` |
| docker-compose | v2+ | `docker compose version` |
| kubectl | 1.31+ | `kubectl version --client` |
| eksctl | 최신 | `eksctl version` |
| Helm | 3+ | `helm version` |
| AWS CLI | v2 | `aws --version` |
| gh (GitHub CLI) | 최신 | `gh --version` |

### AWS 계정 설정

```bash
# AWS 자격증명 확인
aws sts get-caller-identity

# 리전 설정 (이 프로젝트는 ap-northeast-2 고정)
export AWS_DEFAULT_REGION=ap-northeast-2
```

> **신규 AWS 계정 주의**: Auto Scaling Group(ASG)을 통한 EC2 기동이 free-tier-eligible 인스턴스로 제한될 수 있습니다.
> 이 경우 `m7i-flex.large` (2 vCPU / 8 GiB, free-tier-eligible) 를 사용합니다. ([트러블슈팅](#troubleshooting) 참조)

---

## Part 1 — 로컬 개발 환경

### 1-1. 저장소 클론 및 환경 설정

```bash
git clone https://github.com/sammy0329/eks-ml-observability-poc.git
cd eks-ml-observability-poc
```

### 1-2. inference-api 개발 환경

```bash
cd inference-api
uv sync

# 단위 테스트 실행
uv run pytest -v

# 린트/포맷 검사
uv run ruff check . && uv run ruff format .

# 개발 서버 단독 실행 (선택)
uv run uvicorn app.main:app --reload --port 8000
```

### 1-3. sensor-generator 개발 환경

```bash
cd sensor-generator
uv sync

# 단위 테스트 실행
uv run pytest -v
```

### 1-4. 전체 로컬 스택 실행 (docker-compose)

```bash
# 프로젝트 루트에서
docker compose up -d

# 상태 확인
docker compose ps
```

**접속 포인트:**

| 서비스 | URL | 계정 |
|--------|-----|------|
| API Docs | http://localhost:8000/docs | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Alertmanager | http://localhost:9093 | — |

### 1-5. 로컬 시나리오 테스트

```bash
# sensor-generator 프로파일 전환 (docker-compose 환경)
docker compose exec sensor-generator sh -c "PROFILE=load python -m sensor_generator"

# 또는 docker-compose.yml의 environment를 변경 후 재시작
docker compose restart sensor-generator
```

### 1-6. 스택 종료

```bash
docker compose down
# 볼륨(PostgreSQL 데이터)까지 삭제하려면:
docker compose down -v
```

---

## Part 2 — EKS 배포

> **비용 주의**: EKS 클러스터 실행 중 약 $0.34/hr 과금됩니다. 데모 완료 후 즉시 삭제하세요.

### 2-1. EKS 클러스터 생성

```bash
eksctl create cluster -f infra/eksctl/cluster.yaml
# 약 15~20분 소요
# → 완료 시 kubeconfig 자동 업데이트
```

```bash
# 노드 상태 확인
kubectl get nodes
# NAME                                            STATUS   ROLES    AGE   VERSION
# ip-192-168-xx-xx.ap-northeast-2.compute...     Ready    <none>   ...   v1.31.x
```

### 2-2. ECR 리포지토리 생성 및 이미지 빌드·푸시

```bash
./scripts/setup_ecr.sh
# - inference-api, sensor-generator ECR 리포지토리 생성
# - linux/amd64 이미지 빌드 및 푸시
```

### 2-3. EBS CSI 드라이버 설치 (PostgreSQL PVC 필수)

```bash
aws eks create-addon \
  --cluster-name sensor-obs-poc \
  --addon-name aws-ebs-csi-driver \
  --region ap-northeast-2 \
  --resolve-conflicts OVERWRITE

# 설치 완료 확인 (~30초)
aws eks describe-addon \
  --cluster-name sensor-obs-poc \
  --addon-name aws-ebs-csi-driver \
  --region ap-northeast-2 \
  --query 'addon.status'
# → "ACTIVE"
```

### 2-4. K8s 매니페스트 배포

```bash
# PostgreSQL (순서 중요: PVC → ConfigMap → Deployment → Service)
kubectl apply -f k8s/base/postgresql/

# inference-api
kubectl apply -f k8s/base/inference-api/

# sensor-generator
kubectl apply -f k8s/base/sensor-generator/
```

```bash
# 전체 Pod 상태 확인
kubectl get pods
# NAME                               READY   STATUS    RESTARTS
# inference-api-xxx                  1/1     Running   0
# postgres-xxx                       1/1     Running   0
# sensor-generator-xxx               1/1     Running   0
```

### 2-5. 모니터링 스택 설치 (Helm)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f k8s/helm-values/kube-prometheus-stack.yaml \
  --timeout 10m

# 설치 확인
helm list -n monitoring
kubectl get pods -n monitoring
```

### 2-6. inference-api ServiceMonitor 적용

> Helm values의 `additionalServiceMonitors`가 동작하지 않는 경우가 있으므로 직접 적용합니다.

```bash
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: inference-api
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  selector:
    matchLabels:
      app: inference-api
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
  namespaceSelector:
    matchNames:
      - default
EOF
```

```bash
# Prometheus 타겟 확인 (포트포워드 후 UI에서)
# http://localhost:9090/targets → inference-api UP 확인
```

### 2-7. metrics-server 설치 (HPA 필수)

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# HPA 상태 확인 (~60초 후)
kubectl get hpa
# NAME            REFERENCE                  TARGETS       MINPODS   MAXPODS   REPLICAS
# inference-api   Deployment/inference-api   cpu: 17%/50%  1         5         1
```

### 2-8. 접속 (포트포워드)

```bash
# 터미널 3개에서 각각 실행
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward svc/inference-api 8000:8000
```

| 서비스 | URL | 계정 |
|--------|-----|------|
| Grafana | http://localhost:3000 | admin / prom-operator |
| Prometheus | http://localhost:9090 | — |
| API Docs | http://localhost:8000/docs | — |
| Alertmanager | `kubectl port-forward -n monitoring svc/kube-prometheus-stack-alertmanager 9093:9093` | — |

---

## Part 3 — 데모 시나리오 실행

### 사전 확인

```bash
# 모든 Pod Running 확인
kubectl get pods -A | grep -v Running | grep -v Completed

# HPA 정상 상태 확인 (cpu 값이 <unknown>이 아닌지)
kubectl get hpa
```

### S1 — 부하 증가 (HPA 스케일아웃)

```bash
# 1. normal → load 전환
kubectl set env deployment/sensor-generator PROFILE=load

# 2. CPU 상승 모니터링 (약 60초 대기)
watch kubectl get hpa
# cpu: 17%/50% → cpu: 63%/50%, REPLICAS: 1→2

# 3. 안정화 확인 (추가 90초)
# cpu: 32%/50%, REPLICAS: 2 (부하 분산)

# 4. 복구
kubectl set env deployment/sensor-generator PROFILE=normal
```

**Grafana 확인 경로:** Dashboards → Kubernetes / Compute Resources / Workload → inference-api

**예상 결과:**

| 지표 | 전 | 부하 중 | 안정화 후 |
|------|-----|---------|----------|
| CPU | 17% | 63% | 32% |
| Replicas | 1 | 2 | 2 |

### S2 — 에러 주입 (HighErrorRate 알람)

```bash
# 1. error 프로파일 전환
kubectl set env deployment/sensor-generator PROFILE=error

# 2. 에러율 확인
# Prometheus: rate(http_requests_total{status=~"4..|5.."}[1m]) / rate(http_requests_total[1m])

# 3. 약 2분 후 알람 확인
# Prometheus /alerts → HighErrorRate: FIRING (Value≈0.32)

# 4. 복구
kubectl set env deployment/sensor-generator PROFILE=normal
```

**예상 결과:** 422 에러율 ~32%, `for: 2m` 후 `HighErrorRate` FIRING

### S3 — 입력 품질 저하 (HighMissingRate 알람)

```bash
# 1. quality_degradation 프로파일 전환
kubectl set env deployment/sensor-generator PROFILE=quality_degradation

# 2. missing rate 확인
# Prometheus: input_missing_rate

# 3. 약 2분 후 알람 확인
# Prometheus /alerts → HighMissingRate: FIRING (Value=0.5)

# 4. 복구
kubectl set env deployment/sensor-generator PROFILE=normal
```

**예상 결과:** missing rate 50% (임계 30% 초과), `for: 2m` 후 `HighMissingRate` FIRING

### PostgreSQL 운영 이벤트 기록

```bash
kubectl exec -it deploy/postgres -- psql -U postgres -d sensor_obs
```

```sql
-- 시나리오 실행 기록
INSERT INTO scenario_runs (scenario, profile, started, ended, notes)
VALUES ('S1', 'load', NOW(), NOW() + INTERVAL '3 minutes', 'CPU 17%→63%, HPA 1→2 replica');

INSERT INTO scenario_runs (scenario, profile, started, ended, notes)
VALUES ('S2', 'error', NOW(), NOW() + INTERVAL '4 minutes', 'HighErrorRate 발화, 에러율 32%');

INSERT INTO scenario_runs (scenario, profile, started, ended, notes)
VALUES ('S3', 'quality_degradation', NOW(), NOW() + INTERVAL '3 minutes', 'HighMissingRate 발화, missing rate 50%');

-- 확인
SELECT * FROM scenario_runs ORDER BY id;
SELECT * FROM incidents;
```

---

## Part 4 — 클러스터 삭제 (비용 절약)

```bash
# 1. ECR 리포지토리 삭제
aws ecr delete-repository --repository-name inference-api \
  --region ap-northeast-2 --force
aws ecr delete-repository --repository-name sensor-generator \
  --region ap-northeast-2 --force

# 2. 클러스터 삭제 (~10~15분)
eksctl delete cluster --name sensor-obs-poc --region ap-northeast-2

# 3. 잔존 리소스 확인
aws cloudformation list-stacks \
  --region ap-northeast-2 \
  --stack-status-filter CREATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName,`eksctl`)].StackName'
# → [] (비어 있으면 완전 삭제)

aws ec2 describe-nat-gateways \
  --region ap-northeast-2 \
  --filter Name=state,Values=available \
  --query 'NatGateways[].NatGatewayId'
# → [] (비어 있으면 완전 삭제)
```

---

## Troubleshooting

### ASG 인스턴스 기동 실패 — "not eligible for Free Tier"

신규 AWS 계정에서 ASG를 통한 자동 기동이 free-tier-eligible 인스턴스로 제한될 수 있습니다.

```bash
# 허용 인스턴스 타입 조회
aws ec2 describe-instance-types \
  --region ap-northeast-2 \
  --filters "Name=free-tier-eligible,Values=true" \
  --query 'InstanceTypes[*].{Type:InstanceType,vCPU:VCpuInfo.DefaultVCpus,MemMiB:MemoryInfo.SizeInMiB}' \
  --output table
```

`infra/eksctl/cluster.yaml`의 `instanceType`을 `m7i-flex.large`로 변경 후 재시도.

### EBS PVC가 Pending에서 진행되지 않음

EKS 1.29+에서 in-tree EBS 프로비저너가 deprecated됩니다.

```bash
aws eks create-addon --cluster-name sensor-obs-poc \
  --addon-name aws-ebs-csi-driver --region ap-northeast-2
```

### PostgreSQL initdb 실패 (lost+found)

```
initdb: error: directory exists but is not empty — It contains a lost+found directory
```

`k8s/base/postgresql/deployment.yaml`에 환경변수 추가:

```yaml
env:
  - name: PGDATA
    value: /var/lib/postgresql/data/pgdata
```

### HPA TARGETS가 `<unknown>` 으로 표시됨

metrics-server가 설치되지 않은 경우입니다.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Prometheus가 inference-api 메트릭을 수집하지 못함

Helm values의 `additionalServiceMonitors`가 동작하지 않는 경우 ServiceMonitor를 직접 적용합니다. ([2-6 참조](#2-6-inference-api-servicemonitor-적용))

---

## 관련 문서

| 문서 | 내용 |
|------|------|
| [README](../README.md) | 프로젝트 개요, 아키텍처, 기술 스택 |
| [PLAN](PLAN.md) | 5일 구현 계획 |
| [TASKS](TASKS.md) | Epic/Task DoD 체크리스트 |
| [TechStack](TechStack.md) | 기술 선택 근거 매트릭스 |
| [REPORT](REPORT.md) | 데모 시나리오 실행 결과 및 교훈 |
