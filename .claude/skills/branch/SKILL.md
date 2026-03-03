# Skill: branch

## Description
`docs/TASKS.md`의 Task ID와 설명을 받아 프로젝트 git-flow 규칙에 맞는 브랜치를 생성하고 checkout한다.

## Triggers
- `/branch`
- 사용자가 새 작업을 시작하며 브랜치 생성을 요청할 때

## Usage
```
/branch <task-id> <설명>
/branch hotfix <설명>
/branch docs <설명>
```

## Instructions

### 1. 현재 상태 확인
`git status`로 uncommitted 변경사항을 확인한다. 있으면 사용자에게 알리고 계속할지 물어본다.

### 2. main 최신화
```bash
git checkout main && git pull origin main
```

### 3. 브랜치명 구성 규칙

| 입력 | 브랜치 패턴 |
|------|------------|
| `<task-id> <설명>` | `feature/phase{N}/{task-id}-{kebab-desc}` |
| `hotfix <설명>` | `hotfix/{kebab-desc}` |
| `docs <설명>` | `docs/{kebab-desc}` |

- task-id 첫 번째 숫자 = Phase 번호 (`1.2.3` → `phase1`)
- 설명은 kebab-case 변환 (공백 → `-`, 소문자, 특수문자 제거)
- 최대 60자 제한

### 4. 브랜치 생성 및 checkout
```bash
git checkout -b {브랜치명}
```

### 5. 결과 출력
생성된 브랜치명, 관련 Task 요약(`docs/TASKS.md` 참조), 다음 단계 안내를 출력한다.

## Examples

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

## References
- 브랜치 전략: `CLAUDE.md` § Git-flow 브랜치 전략
- 브랜치 흐름 다이어그램: `CONTRIBUTING.md`
- Task 목록: `docs/TASKS.md`
