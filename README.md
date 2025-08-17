# 로케 (ROKE) Backend

대전 지역 숨은 명소 발굴을 위한 AI 기반 지역 활성화 플랫폼의 백엔드 서비스입니다.

## 기술 스택

- **Spring Boot 3.2.0**
- **Java 17**
- **Gradle**
- **Spring Data JPA**
- **Spring Security**
- **MySQL 8.0** (Docker 로컬 개발)
- **MySQL** (AWS EC2 운영 환경)
- **JWT Authentication**
- **Swagger/OpenAPI**

## 프로젝트 구조

```
src/
├── main/
│   ├── java/
│   │   └── com/
│   │       └── loca/
│   │           ├── LocaBackendApplication.java
│   │           ├── controller/
│   │           ├── service/
│   │           ├── repository/
│   │           ├── entity/
│   │           ├── dto/
│   │           └── config/
│   └── resources/
│       ├── application.yml
│       └── application-dev.yml
└── test/
    └── java/
        └── com/
            └── loca/
```

## 실행 방법

### 1. 개발 환경 실행

```bash
./gradlew bootRun --args='--spring.profiles.active=dev'
```

### 2. 빌드

```bash
./gradlew build
```

### 3. JAR 파일 실행

```bash
java -jar build/libs/loca-backend-0.0.1-SNAPSHOT.jar
```

## API 엔드포인트

### 헬스 체크
- `GET /api/health` - 서비스 상태 확인

### Swagger UI
- `http://localhost:8080/api/swagger-ui.html` - API 문서

### phpMyAdmin (개발 환경)
- `http://localhost:8081` - MySQL 관리 도구
  - Username: root
  - Password: root1234

## 환경 설정

### 개발 환경 (dev)
- MySQL 8.0 (Docker) 사용
- 자동 테이블 생성/업데이트
- 상세 로깅 활성화
- phpMyAdmin 접근 가능 (포트 8081)
- Swagger UI 활성화

### 테스트 환경 (test)
- H2 인메모리 데이터베이스 사용
- 테스트용 최소 로깅
- 랜덤 포트 사용
- Swagger UI 비활성화

### 운영 환경 (prod)
- MySQL 데이터베이스 사용 (AWS EC2)
- 테이블 스키마 검증 모드
- 파일 로깅 활성화
- 보안 강화 설정
- Swagger UI 비활성화
- 환경 변수 기반 설정

## 실행 방법

### 1. MySQL Docker 시작
```bash
./docker-start.sh
# 또는
docker-compose up -d mysql
```

### 2. 개발 환경 실행
```bash
./run-dev.sh
# 또는
./gradlew bootRun --args='--spring.profiles.active=dev'
```

### 3. 운영 환경 실행
```bash
./run-prod.sh
# 또는
java -jar build/libs/roke-backend-0.0.1-SNAPSHOT.jar --spring.profiles.active=prod
```

### 4. 테스트 실행
```bash
./gradlew test --args='--spring.profiles.active=test'
```

### 5. Docker 컨테이너 관리
```bash
# 컨테이너 시작
docker-compose up -d

# 컨테이너 중지
docker-compose down

# 로그 확인
docker-compose logs mysql
```

## 주요 기능

1. **사용자 인증/인가** - JWT 기반 인증
2. **AI 프로덕트 관리** - 유성구 지역 문제 해결 아이디어 관리
3. **API 문서화** - Swagger/OpenAPI 자동 생성
4. **모니터링** - Spring Boot Actuator

## 개발 가이드

### 새로운 API 추가
1. `controller` 패키지에 컨트롤러 클래스 생성
2. `service` 패키지에 비즈니스 로직 구현
3. `repository` 패키지에 데이터 접근 로직 구현
4. `entity` 패키지에 JPA 엔티티 정의

### 데이터베이스 마이그레이션
- JPA Hibernate의 `ddl-auto: update` 사용
- 필요시 Flyway 또는 Liquibase 도입 고려
