# CLAUDE.md — 프로젝트 지시사항

> Claude Code가 이 프로젝트에서 작업할 때 항상 준수하는 규칙입니다.

## 프로젝트 개요

EKS 기반 C4I-Style Sensor Anomaly Observability PoC.
FastAPI 추론 서비스 + 합성 센서 생성기 + Prometheus/Grafana 관측 스택 + PostgreSQL 운영 이벤트 DB를 EKS에 배포하고 3가지 데모 시나리오(S1/S2/S3)를 실행한다.

- 상세 계획: `docs/PLAN.md`
- 작업 목록: `docs/TASKS.md`
- 기술 스택: `docs/TechStack.md`

---

## Git-flow 브랜치 전략

### 브랜치 구조

| 브랜치 패턴 | 용도 | 분기 원점 | 머지 대상 |
|------------|------|----------|----------|
| `main` | 배포 가능한 안정 브랜치 | — | — |
| `feature/phase{N}/{task-id}-{kebab-desc}` | 기능 개발 | main | main (PR) |
| `hotfix/{kebab-desc}` | 긴급 수정 | main | main (PR) |
| `docs/{kebab-desc}` | 문서 전용 작업 | main | main (PR) |

### 브랜치 생성 규칙

1. 모든 작업은 `main`에서 분기한 브랜치에서 진행한다.
2. 브랜치명은 `docs/TASKS.md`의 Task ID와 연동한다.
3. 작업 완료 후 PR → main (squash merge 권장).
4. 브랜치명은 모두 소문자 kebab-case 사용.

### 브랜치명 예시

```
feature/phase1/1.2.3-anomaly-detection-logic
feature/phase2/2.1.1-timeseries-generator
feature/phase3/3.2.2-grafana-dashboard-json
feature/phase4/4.2.1-k8s-deployment-manifest
hotfix/hpa-metrics-server-missing
docs/update-techstack-mermaid
```

---

## 커밋 컨벤션 (Conventional Commits)

### 형식

```
<type>(<scope>): <한국어 subject>

[optional body — 왜 변경했는지]

[optional footer]
```

### Type

| type | 용도 |
|------|------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `chore` | 빌드/설정/의존성 변경 |
| `refactor` | 기능 변화 없는 코드 개선 |
| `test` | 테스트 추가/수정 |
| `ci` | CI/CD 설정 변경 |
| `perf` | 성능 개선 |
| `style` | 코드 스타일 (포매팅 등) |

### Scope (프로젝트 전용)

| scope | 대상 경로 |
|-------|----------|
| `api` | `inference-api/` |
| `generator` | `sensor-generator/` |
| `obs` | `observability/` (prometheus/grafana/alertmanager) |
| `db` | DB 스키마, 마이그레이션 |
| `k8s` | `k8s/` Kubernetes 매니페스트 |
| `infra` | `infra/` eksctl/클러스터 설정 |
| `docs` | `docs/`, `CLAUDE.md`, `CONTRIBUTING.md` |
| `ci` | `.github/workflows/` |

### 커밋 메시지 예시

```
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

- subject는 **한국어**로 작성
- type과 scope는 **영어 소문자** 유지
- subject **72자 이내** 권장, **마침표 없음**
- body는 "왜" 변경했는지 설명 (무엇이 아닌 이유)
- breaking change는 footer에 `BREAKING CHANGE: <설명>` 명시
- 커밋은 하나의 논리적 변경 단위로 유지 (atomic commit)

---

## 코드 작성 규칙

- **Python**: `ruff` 포맷터/린터 준수 (`ruff check . && ruff format .`)
- **테스트**: 구현과 동일 브랜치에 포함, `pytest -v` 통과 필수
- **시크릿**: `.env` 파일은 절대 커밋하지 않음 (`.gitignore` 필수 확인)
- **EKS 관련 작업**: Day 4-5 이전에는 로컬 docker-compose 환경에서 검증

---

## PR 규칙

- PR 제목 형식: `{type}({scope}): {한국어 설명}` (커밋 컨벤션과 동일)
- PR 본문은 `.github/PULL_REQUEST_TEMPLATE.md` 템플릿 사용
- 관련 Task ID (`docs/TASKS.md`) 를 PR 본문에 반드시 명시
- 스크린샷/캡처가 있는 경우 Artifacts 섹션에 첨부
