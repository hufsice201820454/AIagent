# EVAgent - 자동차 시장 트렌드 분석

간단한 자동차 산업 분석 웹 서비스

## 🎯 주요 기능

1. **로그인/회원가입** - JWT 인증
2. **기업 분석** - OEM 기업 목록 및 상세 정보
3. **뉴스 피드** - 실시간 뉴스 조회
4. **AI 리포트** - AI 기반 분석 리포트

## 🚀 빠른 시작

### 1. 프로젝트 구조 준비
```bash
# workspace/evagent 디렉토리 구조 생성
mkdir -p workspace/evagent/db

# CSV 파일들을 db 폴더로 복사 (db_sample 폴더에서)
cp db_sample/*.csv workspace/evagent/db/
```

### 2. Backend 실행
```bash
cd backend
pip install -r requirements.txt

# 데이터베이스 초기화
python init_db.py

# 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend 실행
```bash
cd frontend
npm install
npm run dev
```

### 4. 접속
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 📁 구조

```
workspace/
└── evagent/
    ├── backend/          # FastAPI 서버
    │   ├── app.py       # 메인 애플리케이션
    │   ├── models.py    # 데이터베이스 모델
    │   ├── schemas.py   # Pydantic 스키마
    │   ├── config.py    # 설정 (DB 경로 포함)
    │   └── routers/     # API 라우터
    │
    ├── frontend/        # Vue 3 앱
    │   ├── src/
    │   │   ├── views/   # 페이지 컴포넌트
    │   │   ├── stores/  # Pinia 스토어
    │   │   └── router/  # Vue Router
    │   └── package.json
    │
    └── db/              # 데이터베이스 및 CSV 파일
        ├── evagent.db   # SQLite 데이터베이스 (자동 생성)
        ├── oem_factories.csv
        ├── battery_factories.csv
        ├── hvac_factories.csv
        └── news_feed_seed.csv (선택사항)
```

## 🔑 주요 API

### Authentication
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인

### Companies
- `GET /api/companies/oem` - 기업 목록
- `GET /api/companies/oem/{id}` - 기업 상세

### News
- `GET /api/news` - 뉴스 목록
- `GET /api/news/company/{id}/latest` - 기업별 최신 뉴스

### Reports
- `POST /api/reports/generate` - 리포트 생성
- `GET /api/reports` - 리포트 목록

## ⚙️ 환경 변수 (.env)

```env
# 선택사항 - 기본값으로도 작동
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-api-key  # AI 리포트 기능 사용 시 필요
DB_DIR=/custom/path/to/db       # 커스텀 DB 경로 (선택사항)
```

## 🛠 기술 스택

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vue 3, Vite, Pinia, Axios
- **Auth**: JWT
- **Database**: SQLite (workspace/evagent/db/evagent.db)

## 📝 간단한 테스트

1. 회원가입: http://localhost:5173/register
2. 로그인: http://localhost:5173/login
3. 대시보드에서 기능 확인

또는 Swagger UI: http://localhost:8000/docs

## 🔄 주요 변경사항

- **MySQL → SQLite**: 설치 및 설정이 간단해졌습니다
- **자동 경로 설정**: workspace/evagent/db 경로를 자동으로 인식
- **CSV 파일 관리**: 모든 CSV 파일을 db 폴더에 집중

자세한 설정 방법은 `SETUP_GUIDE.md`를 참고하세요.

끝! 🎉
