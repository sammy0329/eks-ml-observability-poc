# 기여 가이드 (Contributing Guide)

> EKS 기반 C4I-Style Sensor Anomaly Observability PoC

---

## 브랜치 전략 (Git-flow)

### 브랜치 흐름

```mermaid
gitGraph
    commit id: "초기 커밋"

    branch feature/phase1/1.2.1-fastapi-skeleton
    checkout feature/phase1/1.2.1-fastapi-skeleton
    commit id: "feat(api): FastAPI 앱 스켈레톤 및 /healthz 엔드포인트 추가"
    commit id: "feat(api): Z-score 이상 탐지 로직 구현"
    commit id: "feat(api): Prometheus RED 메트릭 계측 추가"

    checkout main
    merge feature/phase1/1.2.1-fastapi-skeleton id: "PR #1 merge"

    branch feature/phase2/2.1.1-timeseries-generator
    checkout feature/phase2/2.1.1-timeseries-generator
    commit id: "feat(generator): 시계열 데이터 생성 엔진 구현"
    commit id: "feat(generator): HTTP 스트림 클라이언트 및 시나리오 프로파일 추가"

    checkout main
    merge feature/phase2/2.1.1-timeseries-generator id: "PR #2 merge"

    branch feature/phase3/3.2.2-grafana-dashboard
    checkout feature/phase3/3.2.2-grafana-dashboard
    commit id: "feat(obs): Grafana 대시보드 JSON 프로비저닝 추가"

    branch hotfix/alertmanager-webhook-config
    checkout hotfix/alertmanager-webhook-config
    commit id: "fix(obs): Alertmanager 웹훅 수신기 설정 오류 수정"

    checkout main
    merge hotfix/alertmanager-webhook-config id: "hotfix merge"

    checkout feature/phase3/3.2.2-grafana-dashboard
    merge main id: "main sync"
    commit id: "feat(obs): 입력 품질 패널 추가"

    checkout main
    merge feature/phase3/3.2.2-grafana-dashboard id: "PR #3 merge"
```

### 브랜치 명명 규칙

| 종류 | 패턴 | 예시 |
|------|------|------|
| 기능 개발 | `feature/phase{N}/{task-id}-{kebab-desc}` | `feature/phase1/1.2.3-anomaly-detection-logic` |
| 긴급 수정 | `hotfix/{kebab-desc}` | `hotfix/hpa-metrics-server-missing` |
| 문서 작업 | `docs/{kebab-desc}` | `docs/update-techstack-mermaid` |

> Task ID는 `docs/TASKS.md` 기준

---

## 커밋 컨벤션

### 형식

```
<type>(<scope>): <한국어 subject>

[optional body]

[optional footer]
```

### Type / Scope

```
type  → feat | fix | docs | chore | refactor | test | ci | perf | style
scope → api | generator | obs | db | k8s | infra | docs | ci
```

### 예시

```bash
feat(api): Z-score 기반 이상 탐지 로직 및 POST /predict 엔드포인트 추가
fix(api): PredictRequest 빈 values 배열 유효성 검사 오류 수정
feat(obs): HighErrorRate·HighLatency Prometheus 알람 룰 추가
feat(obs): RED 메트릭 및 입력 품질 패널 포함 Grafana 대시보드 프로비저닝
chore(k8s): inference-api HPA 매니페스트 추가 (CPU 50%, min:1, max:5)
feat(db): deployments·incidents·scenario_runs 테이블 init.sql 생성
test(api): 이상 탐지기 스파이크·결측 케이스 단위 테스트 추가
docs: TechStack·PLAN·TASKS 문서 및 Mermaid 다이어그램 추가
chore(infra): ap-northeast-2 t3.medium 노드 eksctl cluster.yaml 추가
```

### 규칙

- `type(scope):` 는 **영어 소문자**
- subject는 **한국어**, **72자 이내**, **마침표 없음**
- body: "왜" 변경했는지 (무엇이 아닌 이유)
- atomic commit — 하나의 커밋에 하나의 논리적 변경

---

## PR 워크플로우

```mermaid
flowchart LR
    A([main에서 브랜치 생성]) --> B[작업 + 커밋]
    B --> C{로컬 검증\npytest / docker-compose}
    C -- 실패 --> B
    C -- 통과 --> D[PR 생성\n템플릿 작성]
    D --> E{코드 리뷰\n자기 검토}
    E -- 수정 필요 --> B
    E -- 승인 --> F([main에 squash merge])
    F --> G[브랜치 삭제]
```

### PR 제목 형식

```
{type}({scope}): {한국어 설명}
```

예시:
```
feat(api): Z-score 이상 탐지 및 /predict 엔드포인트 구현
feat(obs): Prometheus 알람 룰 및 Grafana 대시보드 통합
chore(k8s): EKS Deployment·Service·HPA 매니페스트 추가
```

### PR 체크리스트

PR 생성 전 확인:

- [ ] 브랜치명이 `feature/phase{N}/{task-id}-{desc}` 형식을 따름
- [ ] `pytest -v` 전체 통과
- [ ] `ruff check . && ruff format .` 통과
- [ ] `docker-compose up` 로컬 스택 정상 기동 확인 (해당 시)
- [ ] 관련 Task ID가 PR 본문에 명시됨
- [ ] `.env` 등 시크릿 파일이 커밋에 포함되지 않음

---

## 로컬 개발 → EKS 배포 워크플로우

```mermaid
flowchart TD
    A["로컬 개발\n(Day 1-3)"] --> B["docker-compose up\n전체 스택 기동"]
    B --> C["시나리오 리허설\nS1·S2·S3 로컬 검증"]
    C --> D["PR → main merge"]
    D --> E["docker build\n이미지 빌드"]
    E --> F["aws ecr push\nECR 이미지 푸시"]
    F --> G["eksctl create cluster\nEKS 클러스터 생성 (Day 4)"]
    G --> H["kubectl apply\nDeployment·Service·HPA"]
    H --> I["helm install\nkube-prometheus-stack"]
    I --> J["데모 시나리오 실행\n(Day 5)"]
    J --> K["eksctl delete cluster\n클러스터 즉시 삭제"]

    style G fill:#ff6b6b,color:#fff
    style H fill:#ff6b6b,color:#fff
    style I fill:#ff6b6b,color:#fff
    style J fill:#ff6b6b,color:#fff
    style K fill:#ff6b6b,color:#fff
```

> 빨간색 단계는 EKS 과금 구간입니다. Day 5 완료 즉시 클러스터를 삭제하세요.
