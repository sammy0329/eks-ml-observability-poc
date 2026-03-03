# PRD — EKS 기반 C4I-Style Sensor Anomaly Observability PoC

## 0. 한 줄 요약

합성 센서 시계열 입력을 받아 이상 탐지(경량 통계 기반)를 수행하는 FastAPI 추론 서비스를 EKS에 배포하고, Prometheus/Grafana로 운영 지표(RED + 입력 품질 지표)를 관측·알람·대응(스케일/롤백)하는 PoC를 5일 내 완성한다. (데모는 외부 공개 없이 녹화/캡처로 제출)

## 1. 배경/맥락

- 목표 직무는 MLOps 플랫폼 기술 개발(백엔드) 성격이며 Docker/K8s, Grafana/Prometheus, PostgreSQL, 실시간 통신/데이터 처리 요구가 핵심이다.
- C4I 맥락에서는 실시간/준실시간 정보 유입의 신뢰성(지연·결측·품질 저하)에 대한 관측과 대응이 중요하므로, “모델 성능”보다 “운영 지표 기반 신뢰성 확보”가 더 설득력 있는 포트폴리오가 된다.

## 2. 목표(Goals)

- G1. EKS 위에서 서비스가 실제로 동작하는 배포 산출물 확보 (Deployment/Service/HPA).
- G2. 운영 지표를 정의하고 Prometheus로 수집, Grafana로 시각화 (대시보드 1장 이상).
- G3. 알람 룰을 정의하고(지연/에러율/입력 품질), 시나리오에서 실제로 알람이 발생하는 증거 확보.
- G4. 장애/부하/배포 결함 시나리오에서 대응(스케일아웃, 롤백 등)을 수행하고 “전/후 지표” 캡처.
- G5. 운영 이벤트(배포/알람/스케일/대응)를 PostgreSQL에 기록해 재현 가능한 실험/운영 흔적을 남긴다.

## 3. 비목표(Non-goals)

- Kubeflow 기반 학습 파이프라인(학습 자동화/재학습) 전체 구현은 이번 스코프에서 제외.
- 외부 사용자를 위한 인증/인가, 퍼블릭 상용 트래픽 운영은 제외(녹화/캡처로 대체).

## 4. 사용자/이해관계자

- 플랫폼/MLOps 엔지니어: 배포 버전별 지연·에러율 비교, 이상 징후 시 빠른 롤백 필요.
- 운영/SRE: 부하 급증 시 자동 확장과 알람 기반 대응, 장애 재현 가능한 기록 필요.
- 모델 사용자(내부): 입력 품질 저하(지연/결측/드리프트) 발생 여부를 빠르게 확인하고 싶음.

## 5. 핵심 시나리오(데모 3종)

- S1. 부하 증가 → p95 latency 상승 → HPA 스케일아웃 → 지표 안정화(전/후 캡처).
- S2. 오류 주입(카나리 버전) → error rate 상승 → 알람 발생 → 롤백 → 지표 회복(전/후 캡처).
- S3. 입력 품질 저하(지연/결측/드리프트 합성) → input_delay / missing_rate / drift_score 변화 관측 + (선택) 소프트 알람.

## 6. 기능 요구사항(Functional Requirements)

### 6.1 추론 API (FastAPI)

- 엔드포인트
  - `GET /healthz` : 헬스체크
  - `POST /predict` : 이상탐지 결과 반환
  - `GET /metrics` : Prometheus 스크랩 엔드포인트
- 입력(예시)
  - 센서 ID, timestamp, window 값 배열(최근 N 포인트)
  - 옵션: 지연/결측 플래그(시뮬레이터가 주입)
- 출력(예시)
  - `anomaly_score: float`
  - `is_anomaly: bool`
  - `reason: string` (예: missing_rate_high, variance_spike)

### 6.2 합성 센서 스트림 생성기

- 정상 구간 + 이상 구간(스파이크/드리프트/노이즈 증가/결측/지연)을 파라미터로 생성.
- “실시간처럼” 요청을 발생시키는 replay/stream 모드 제공.

### 6.3 메트릭 수집 (Prometheus)

- HTTP RED
  - request rate(RPS), error rate, latency(p95)
- 입력 품질/도메인 메트릭
  - `input_missing_rate`
  - `input_delay_ms`
  - `drift_score`(간단한 분포 거리/통계 기반)
  - `anomaly_rate`
- 배포/운영 메타데이터 메트릭(가능하면)
  - `app_version` 라벨 또는 별도 gauge

### 6.4 대시보드 (Grafana)

- 한 화면에서 다음이 보일 것:
  - RPS, error rate, p95 latency
  - CPU/mem, replica 수(HPA)
  - input_missing_rate, input_delay_ms, drift_score, anomaly_rate
- 시나리오 S1~S3 각각 “캡처 포인트”가 명확해야 함.

### 6.5 알람 (Prometheus Alerting Rules)

- 예시
  - error rate > 1% (5m)
  - p95 latency > 200ms (5m)
  - input_missing_rate > 임계치(5m) (소프트 알람)
- 알람 발생 로그/스크린샷을 데모 산출물로 남긴다.

### 6.6 운영 이벤트 저장 (PostgreSQL)

- 목적: 재현 가능한 운영 기록 (배포/스케일/알람/대응)
- 최소 테이블
  - `deployments(id, version, started_at, ended_at, result)`
  - `incidents(id, type, detected_at, resolved_at, action_taken, notes)`
  - `scenario_runs(id, scenario, started_at, ended_at, artifacts_uri)`
- API 또는 배치로 이벤트 적재.

## 7. 비기능 요구사항(Non-functional Requirements)

- 관측 가능성: 모든 데모 시나리오에서 “지표 변화”로 설명 가능해야 한다.
- 재현성: 동일 시나리오를 같은 파라미터로 다시 실행할 수 있어야 한다.
- 비용: EKS는 데모 직전/도중 최소 시간만 운영하고 완료 후 즉시 삭제한다(컨트롤 플레인 시간당 과금 존재). [web:25]

## 8. 성공 기준(Success Metrics / DoD)

- D1. EKS에서 서비스 배포 성공 + HPA 동작 캡처.
- D2. Grafana 대시보드 링크/스크린샷 1장 이상(RED + 입력품질).
- D3. 알람 2종 이상 실제 발생 증거(스크린샷/로그).
- D4. 롤백 또는 스케일로 “문제→대응→회복” 전/후 지표 캡처.
- D5. PostgreSQL에 운영 이벤트 기록이 남고, 조회 결과 캡처 1장 이상.

## 9. 산출물(Deliverables)

- GitHub repo
- 데모 영상(3~5분): S1~S3 시나리오 순서대로
- 캡처: Grafana 대시보드(전/후), 알람, 배포 이력/이벤트 DB 조회
- 문서: README(실행 방법), 운영 리포트(전/후 지표 비교)

## 10. 오픈 이슈

- (선택) Loki 도입 여부: MVP는 메트릭 중심, 시간이 남으면 알람 드릴다운용으로만 추가.
- (선택) 외부 엔드포인트: 공개 없이 녹화/캡처로 대체(기본).
