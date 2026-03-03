# eks-ml-observability-poc

EKS에 배포한 FastAPI 추론 API를 Prometheus/Grafana로 관측하고(지연·에러·트래픽), 알람과 오토스케일링을 검증하는 운영 PoC

---

## 프로젝트 구조

```
eks-ml-observability-poc/
├── inference-api/          # FastAPI 추론 서비스
│   ├── app/                # 앱 소스 코드
│   │   └── __init__.py
│   └── tests/              # 단위/통합 테스트
│       └── __init__.py
├── sensor-generator/       # 합성 센서 데이터 생성기
│   ├── sensor_generator/   # 생성기 패키지
│   │   └── __init__.py
│   ├── profiles/           # 시나리오 YAML 프로파일
│   └── tests/              # 생성기 테스트
│       └── __init__.py
├── observability/          # 관측 스택 설정
│   ├── prometheus/         # Prometheus 설정 및 알람 룰
│   ├── grafana/
│   │   ├── dashboards/     # Grafana 대시보드 JSON
│   │   └── provisioning/   # 데이터소스·대시보드 프로비저닝
│   └── alertmanager/       # Alertmanager 설정
├── k8s/                    # Kubernetes 매니페스트
│   ├── base/               # Deployment, Service, HPA, ConfigMap
│   └── helm-values/        # kube-prometheus-stack Helm values
├── infra/
│   └── eksctl/             # eksctl 클러스터 설정 YAML
├── scripts/                # 유틸리티 셸 스크립트
└── docs/                   # 프로젝트 문서
    ├── PLAN.md             # 5일 구현 계획
    ├── TASKS.md            # Task 분해 목록
    └── TechStack.md        # 기술 스택 매트릭스
```

---

## 빠른 시작 (로컬)

```bash
# 의존성 설치 (inference-api)
cd inference-api
uv sync

# 개발 서버 실행
uvicorn app.main:app --reload

# 테스트 실행
pytest -v

# 코드 검사
ruff check . && ruff format .
```

## 전체 스택 실행 (docker-compose)

```bash
docker-compose up -d
```

---

## 데모 시나리오

| 시나리오 | 설명 |
|----------|------|
| S1 부하 증가 | 트래픽 급증 → p95 latency 상승 → HPA 스케일아웃 |
| S2 에러 주입 | 버그 버전 배포 → error rate 상승 → 알람 → 롤백 |
| S3 품질 저하 | 결측/드리프트 데이터 주입 → 도메인 메트릭 변화 |

---

## 관련 문서

- [구현 계획](docs/PLAN.md)
- [Task 분해](docs/TASKS.md)
- [기술 스택](docs/TechStack.md)
- [기여 가이드](CONTRIBUTING.md)
