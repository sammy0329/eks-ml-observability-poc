# EKS ML Observability PoC — 운영 리포트

> 작성일: 2026-03-06
> 환경: AWS EKS (ap-northeast-2), K8s 1.31, m7i-flex.large × 2

---

## 개요

Z-score 기반 이상 탐지 FastAPI 서비스를 EKS에 배포하고 Prometheus/Grafana 관측 스택을 구축한 뒤,
3가지 데모 시나리오(S1 부하 증가 · S2 에러 주입 · S3 품질 저하)를 실행하여 알람·스케일링·관측 가능성을 검증했다.

---

## 시나리오별 결과

### S1 — 부하 증가 (HPA 스케일아웃)

**전환:** `kubectl set env deployment/sensor-generator PROFILE=load`

| 지표 | 전 (normal) | 부하 중 (load) | 후 (안정화) |
|------|------------|--------------|------------|
| CPU 사용률 | 17% | 63% | 32% |
| Replicas | 1 | 2 | 2 |
| HPA 상태 | cpu: 17%/50% | cpu: 63%/50% | cpu: 32%/50% |

**관측:**
- PROFILE=load 전환 약 60초 후 CPU 50% 임계 초과 → HPA 스케일아웃 발동
- replica 1→2로 증가 후 부하 분산, CPU 32%로 안정화
- Grafana `Kubernetes / Compute Resources / Workload` 대시보드에서 pod 2개 확인

**대응:** 자동 스케일아웃 (HPA 정상 동작)

---

### S2 — 에러 주입 (HighErrorRate 알람)

**전환:** `kubectl set env deployment/sensor-generator PROFILE=error`

| 지표 | 전 (normal) | 에러 주입 중 |
|------|------------|------------|
| 200 응답 | ~37 req/s | ~37 req/s |
| 422 응답 | 0 req/s | ~1 req/s |
| 에러율 | ~0% | 2.73% |
| HighErrorRate 알람 | Inactive | **FIRING** |

**관측:**
- PROFILE=error 전환 시 inference-api에 잘못된 형식의 요청 유입 → 422 Unprocessable Entity 발생
- 에러율 2.73% (임계 1% 초과), `for: 2m` 후 HighErrorRate FIRING
- Prometheus Alerts에서 `alertname="HighErrorRate"`, `severity="warning"`, Value=0.32 확인

**대응:** `kubectl set env deployment/sensor-generator PROFILE=normal` → 에러율 즉시 회복

---

### S3 — 입력 품질 저하 (HighMissingRate 알람)

**전환:** `kubectl set env deployment/sensor-generator PROFILE=quality_degradation`

| 지표 | 전 (normal) | 품질 저하 중 |
|------|------------|------------|
| input_missing_rate | ~0% | **50%** |
| HighMissingRate 알람 | Inactive | **FIRING** |

**관측:**
- PROFILE=quality_degradation 전환 시 NaN 비율 증가 → `input_missing_rate` 메트릭 상승
- missing rate 50% (임계 30% 초과), `for: 2m` 후 HighMissingRate FIRING
- Prometheus Alerts에서 `alertname="HighMissingRate"`, `severity="warning"`, Value=0.5 확인

**대응:** `kubectl set env deployment/sensor-generator PROFILE=normal` → missing rate 즉시 회복

---

## PostgreSQL 운영 이벤트 기록

```sql
SELECT * FROM scenario_runs ORDER BY id;
```

| id | scenario | profile | started | ended | notes |
|----|----------|---------|---------|-------|-------|
| 1 | S1 | load | 11:10 | 11:13 | CPU 17%→63%, HPA 1→2 replica |
| 2 | S2 | error | 11:13 | 11:17 | HighErrorRate 발화, 에러율 2.73% |
| 3 | S3 | quality_degradation | 11:18 | 11:21 | HighMissingRate 발화, missing rate 53% |

```sql
SELECT * FROM incidents;
```

| id | sensor_id | reason | anomaly_score | severity |
|----|-----------|--------|--------------|----------|
| 1 | sensor-eks-01 | variance_spike | 2.73 | warning |

---

## PRD 성공 기준(DoD) 달성 현황

| PRD DoD | 달성 여부 | 증거 |
|---------|----------|------|
| D1. EKS 배포 성공 + HPA 동작 캡처 | ✅ | Grafana CPU Usage 패널 (replica 1→2) |
| D2. Grafana 대시보드 스크린샷 | ✅ | Kubernetes / Compute Resources / Workload |
| D3. 알람 2종 이상 실제 발생 | ✅ | HighErrorRate + HighMissingRate FIRING |
| D4. 롤백/스케일 전/후 지표 캡처 | ✅ | CPU 17%→63%→32%, 에러율 0%→32%→0% |
| D5. PostgreSQL 운영 이벤트 기록 | ✅ | scenario_runs 3건, incidents 1건 |

---

## 트러블슈팅 요약

| 항목 | 원인 | 해결 |
|------|------|------|
| NodeGroup 인스턴스 기동 실패 | AWS 계정 ASG non-free-tier 차단 | m7i-flex.large (free-tier-eligible) 채택 |
| EBS PVC Pending | EKS 1.31 in-tree 프로비저너 deprecated | aws-ebs-csi-driver addon 설치 |
| PostgreSQL initdb 실패 | EBS lost+found 충돌 | PGDATA=/var/lib/postgresql/data/pgdata |
| sensor-generator 배포 실패 | 컨테이너 restartPolicy Forbidden | restartPolicy 필드 제거 |
| Prometheus 메트릭 미수집 | additionalServiceMonitors 미동작 | ServiceMonitor 직접 kubectl apply |
| HPA cpu: unknown | metrics-server 미설치 | metrics-server 별도 설치 |

---

## 개선 사항 / 교훈

1. **metrics-server는 EKS 기본 미포함** — HPA 사용 시 클러스터 생성 직후 설치 필요. `cluster.yaml`의 addons 섹션에 포함하거나 `eksctl` post-create hook 활용 권장.

2. **Helm additionalServiceMonitors 의존 금지** — 차트 버전에 따라 동작 여부가 달라짐. ServiceMonitor를 별도 매니페스트로 관리하는 것이 안전.

3. **EBS 직접 마운트 시 PGDATA 설정 필수** — PostgreSQL on EBS는 lost+found 문제가 항상 발생. initContainer로 디렉토리 생성하거나 PGDATA 서브디렉토리 지정.

4. **`kubectl set env` 단일 명령 시나리오 전환** — 롤백 없이 PROFILE 환경변수 하나로 부하/에러/품질 저하를 즉시 전환 가능. 데모 효율성 극대화.

5. **EKS PoC 비용 관리** — m7i-flex.large × 2 + EKS 제어 플레인 기준 약 $0.34/hr. 데모 후 즉시 `eksctl delete cluster` 실행 필수.
