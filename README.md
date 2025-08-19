# LOCA Backend

대전 지역 숨은 명소 발굴을 위한 AI 기반 지역 활성화 플랫폼의 백엔드 서비스입니다.

## 기술 스택

- **FastAPI 0.104.1**
- **Python 3.12**
- **SQLAlchemy 2.0.23**
- **SQLite** (개발용)
- **MySQL** (운영 배포용)
- **JWT Authentication**
- **Google Gemini Vision API**
- **Swagger/OpenAPI**

## 프로젝트 구조

```
LOCA-backend/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── database.py          # 데이터베이스 연결 설정
│   ├── models/              # SQLAlchemy 모델 (데이터베이스 테이블)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── keyword.py
│   │   ├── photo.py
│   │   └── post.py
│   ├── schemas/             # Pydantic 스키마 (API 요청/응답)
│   ├── api/                 # API 라우터 (엔드포인트)
│   ├── services/            # 비즈니스 로직
│   └── utils/               # 유틸리티 함수
├── uploads/                 # 이미지 업로드 폴더
├── requirements.txt         # Python 의존성
├── loca.db                  # SQLite 데이터베이스 (자동 생성)
└── venv/                    # Python 가상환경
```

## 실행 방법

### 1. 가상환경 활성화

```bash
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 개발 서버 실행

```bash
uvicorn app.main:app --reload
```

### 4. 운영 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 엔드포인트

### 헬스 체크
- `GET /health` - 서비스 상태 확인

### Swagger UI
- `http://localhost:8000/docs` - API 문서 (자동 생성)

### ReDoc
- `http://localhost:8000/redoc` - 대안 API 문서

## 환경 설정

### 개발 환경
- **SQLite** 데이터베이스 사용 (`loca.db`)
- 자동 테이블 생성/업데이트
- 상세 로깅 활성화
- Swagger UI 활성화
- 파일 업로드 (로컬 저장)

### 운영 환경
- **MySQL** 데이터베이스 사용 (AWS RDS)
- 환경 변수 기반 설정
- 파일 스토리지 (AWS S3)
- 보안 강화 설정
- Swagger UI 비활성화

## 주요 기능

### 1. 일일 키워드 시스템
- 매일 새로운 키워드 제공
- "한적한 놀이터", "분위기 있는 카페" 등

### 2. 사진 업로드
- 갤러리에서 사진 선택
- 키워드와 연결해서 업로드

### 3. AI 이미지 분석
- Google Gemini Vision API 연동
- 자동으로 사진 분석 및 설명 생성

### 4. 커뮤니티 공유
- 다른 사람들이 올린 사진 보기
- 좋아요, 댓글 기능

### 5. 검색 기능
- 키워드 기반 사진 검색
- AI 분석 결과 기반 검색

## 개발 가이드

### 새로운 API 추가
1. `app/api/` 패키지에 라우터 파일 생성
2. `app/services/` 패키지에 비즈니스 로직 구현
3. `app/models/` 패키지에 SQLAlchemy 모델 정의
4. `app/schemas/` 패키지에 Pydantic 스키마 정의

### 데이터베이스 모델 추가
1. `app/models/`에 새로운 모델 파일 생성
2. SQLAlchemy ORM으로 테이블 구조 정의
3. `app/models/__init__.py`에 모델 import 추가

### AI 기능 연동
1. `app/services/ai_service.py`에 Gemini Vision API 연동
2. 이미지 분석 및 태깅 기능 구현
3. 분석 결과를 데이터베이스에 저장

## 배포 가이드

### 개발 → 운영 환경 전환
1. SQLite → MySQL 데이터베이스 마이그레이션
2. 환경 변수 설정 (AWS RDS, S3 등)
3. Docker 컨테이너 배포
4. 도메인 및 SSL 인증서 설정
