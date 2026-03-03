# /branch — 브랜치 생성 커맨드

TASK ID와 설명을 받아 프로젝트 git-flow 규칙에 맞는 브랜치를 생성하고 checkout한다.

## 사용법

```
/branch <task-id> <설명>
/branch hotfix <설명>
/branch docs <설명>
```

## 실행 절차

1. **현재 상태 확인**: `git status` 로 uncommitted 변경사항 확인. 있으면 사용자에게 알린다.
2. **main 최신화**: `git checkout main && git pull origin main`
3. **브랜치명 구성** (아래 규칙 적용):
   - feature: `feature/phase{N}/{task-id}-{kebab-case-desc}`
   - hotfix: `hotfix/{kebab-case-desc}`
   - docs: `docs/{kebab-case-desc}`
4. **브랜치 생성 및 checkout**: `git checkout -b {브랜치명}`
5. **결과 출력**: 생성된 브랜치명과 연관 Task 정보를 표시한다.

## 브랜치명 변환 규칙

- task-id의 Phase 번호(첫 번째 숫자)를 `phase{N}`에 사용
- 설명은 한국어/영어 모두 kebab-case로 변환 (공백 → `-`, 특수문자 제거, 소문자)
- 최대 50자로 제한

## 예시

```
/branch 1.2.3 이상 탐지 로직 구현
→ feature/phase1/1.2.3-이상-탐지-로직-구현

/branch 3.2.2 grafana dashboard json
→ feature/phase3/3.2.2-grafana-dashboard-json

/branch hotfix HPA metrics-server 미설치 오류
→ hotfix/hpa-metrics-server-미설치-오류

/branch docs TechStack 버전 매트릭스 업데이트
→ docs/techstack-버전-매트릭스-업데이트
```

## 참고

- Task ID 목록: `docs/TASKS.md`
- 브랜치 전략 상세: `CONTRIBUTING.md`, `CLAUDE.md`
