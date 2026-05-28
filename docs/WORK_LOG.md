# GymPT App Work Log

## 2026-05-28

### CI/CD workflow validation

- `gympt-app` 서비스별 GitHub Actions workflow를 점검했다.
- Docker build 및 ECR push 대상 workflow를 확인했다.
  - `agent-service-ci.yml`
  - `backend-api-ci.yml`
  - `posture-analysis-service-ci.yml`
  - `report-service-ci.yml`
  - `kvs-consumer-service-ci.yml`
- 각 서비스 workflow에 수동 실행용 `workflow_dispatch`를 추가했다.
- PR 이벤트에서는 ECR push와 GitOps 업데이트가 실행되지 않도록 조건을 정리했다.
- 수동 실행 또는 branch push에서는 Docker build, ECR push, GitOps image tag update 흐름이 실행되도록 수정했다.
- `lambda-package.yml`도 수동 실행 시 패키징/업로드 단계가 실행될 수 있도록 조건을 정리했다.
- `actionlint`로 workflow 문법을 검증했다.

### Agent service lint fix

- `agent-service` CI에서 Ruff lint 실패를 확인했다.
- 실패 원인:
  - `app/clients/bedrock_client.py`에 placeholder가 없는 f-string이 있었다.
- 수정 내용:
  - `logger.info(f"...")`를 일반 문자열 로그로 변경했다.
- 결과:
  - Ruff `F541 f-string without any placeholders` 에러를 해결했다.

### GitOps update flow fix

- 서비스 CI/CD workflow에서 ECR push 이후 `gympt-gitops/main`에 직접 push하려다 실패하는 것을 확인했다.
- 실패 원인:
  - `gympt-gitops/main`이 protected branch라 직접 push가 금지되어 있었다.
- 수정 내용:
  - 직접 `git push` 방식 제거
  - `peter-evans/create-pull-request`를 사용해 `gympt-gitops`에 image tag update PR을 자동 생성하도록 변경
- 적용 대상:
  - `agent-service-ci.yml`
  - `backend-api-ci.yml`
  - `posture-analysis-service-ci.yml`
  - `report-service-ci.yml`
  - `kvs-consumer-service-ci.yml`
- 결과:
  - 앱 repo에서 이미지를 빌드하고 ECR에 push한 뒤, GitOps repo에는 PR 기반으로 배포 tag 변경을 요청하는 구조가 되었다.

### Backend API build fix

- `backend-api` CI에서 Gradle compile 실패를 확인했다.
- 실패 원인:
  - `AgentService`와 `WorkoutRecommendation`에서 잘못된 package import를 사용하고 있었다.
  - 실제 클래스 위치와 import가 맞지 않았다.
- 확인한 실제 클래스 위치:
  - `com.gympt.backend.user.User`
  - `com.gympt.backend.user.UserRepository`
  - `com.gympt.backend.domain.BodyProfile`
- 수정 내용:
  - `AgentService.java`의 `User`, `UserRepository`, `BodyProfile` import를 실제 package에 맞게 수정했다.
  - `WorkoutRecommendation.java`에 `com.gympt.backend.user.User` import를 추가했다.
- 로컬 검증:
  - 로컬 Windows 환경에 Java/JAVA_HOME이 설정되어 있지 않아 Gradle build는 실행하지 못했다.
  - CI 에러 로그 기준으로 `cannot find symbol` 원인이 된 import mismatch는 수정했다.

### Current follow-up

- `gympt-app` PR에서 CI 재실행 결과 확인이 필요하다.
- `backend-api` Gradle build가 다음 CI에서 통과하는지 확인한다.
- 서비스 workflow가 ECR push 이후 `gympt-gitops` PR을 정상 생성하는지 확인한다.
- GitOps PR이 생성되면 팀원 승인 후 merge하여 ArgoCD 배포 흐름으로 이어간다.

### Main branch workflow trigger cleanup

- `dev` branch push 시 서비스 배포 workflow가 자동 실행되지 않도록 정리했다.
- 자동 실행 기준을 `main` branch push로 제한했다.
- 의도한 흐름:
  - feature/dev 작업 후 PR 생성
  - PR에서 테스트 확인
  - `main` merge 후 Docker build, ECR push, GitOps update PR 생성
- 적용 대상:
  - `agent-service-ci.yml`
  - `backend-api-ci.yml`
  - `posture-analysis-service-ci.yml`
  - `report-service-ci.yml`
  - `kvs-consumer-service-ci.yml`
  - `lambda-package.yml`
  - `frontend-deploy.yml`
- `actionlint`로 workflow 문법 검증을 완료했다.
