# /pr — PR 생성 커맨드

현재 브랜치의 변경사항을 분석하여 프로젝트 컨벤션에 맞는 PR을 자동으로 생성한다.

## 사용법

```
/pr
/pr <추가 설명>
```

## 실행 절차

1. **현재 브랜치 확인**: `git branch --show-current`
   - `main` 이면 중단하고 사용자에게 알린다.

2. **변경사항 분석** (병렬 실행):
   - `git log main..HEAD --oneline` — 커밋 목록
   - `git diff main...HEAD --stat` — 변경 파일 목록
   - 브랜치명에서 Task ID 추출 (예: `feature/phase1/1.2.3-*` → Task `1.2.3`)

3. **Task 정보 조회**: `docs/TASKS.md` 에서 해당 Task ID의 설명과 DoD 항목을 읽는다.

4. **PR 제목 구성**:
   - 형식: `{type}({scope}): {한국어 설명}`
   - 브랜치명과 커밋 메시지에서 type/scope 추론
   - 예: `feat(api): Z-score 이상 탐지 로직 및 POST /predict 엔드포인트 구현`

5. **PR 본문 작성**: `.github/PULL_REQUEST_TEMPLATE.md` 템플릿의 각 섹션을 분석 내용으로 채운다:
   - **요약**: 커밋 메시지 + diff stat 기반 1~2문장 요약
   - **변경 유형**: type에서 자동 체크
   - **관련 태스크**: 추출한 Task ID + 제목
   - **주요 변경 내용**: 변경 파일 목록 기반 bullet
   - **DoD 체크**: `docs/TASKS.md`에서 읽은 DoD 항목 그대로 옮김
   - **배포 참고사항**: 변경 파일 경로에 따라 자동 추론 (`k8s/` → EKS 재배포, `db/` → 마이그레이션 등)

6. **원격 브랜치 push**: `git push -u origin {브랜치명}`

7. **PR 생성**: `gh pr create --title "..." --body "..."` 실행 후 PR URL 출력

## PR 제목 예시

```
feat(api): Z-score 이상 탐지 로직 및 POST /predict 엔드포인트 구현
feat(obs): Prometheus 알람 룰 및 Grafana 대시보드 통합
chore(k8s): EKS Deployment·Service·HPA 매니페스트 추가
feat(db): 운영 이벤트 테이블 스키마 및 CRUD API 구현
```

## 참고

- PR 템플릿: `.github/PULL_REQUEST_TEMPLATE.md`
- 컨벤션 규칙: `CLAUDE.md`, `CONTRIBUTING.md`
- Task 목록: `docs/TASKS.md`
