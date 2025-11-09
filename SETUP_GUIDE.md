# EVAgent 설정 가이드

## 📁 프로젝트 구조

```
workspace/
└── evagent/
    ├── backend/          # FastAPI 백엔드
    ├── frontend/         # Vue 프론트엔드
    └── db/              # 데이터베이스 및 CSV 파일 폴더
        ├── evagent.db   # SQLite 데이터베이스 (자동 생성됨)
        ├── oem_factories.csv
        ├── battery_factories.csv
        ├── hvac_factories.csv
        └── news_feed_seed.csv (선택사항)
```

## 🚀 설치 및 실행 방법

### 1. CSV 파일 준비

압축을 푼 후, `backend` 폴더에 있는 CSV 파일들을 `workspace/evagent/db/` 폴더로 이동시켜주세요:

```bash
# workspace/evagent 디렉토리 생성
mkdir -p workspace/evagent/db

# CSV 파일들을 db 폴더로 복사
cp backend/oem_factories.csv workspace/evagent/db/
cp backend/battery_factories.csv workspace/evagent/db/
cp backend/hvac_factories.csv workspace/evagent/db/
# news_feed_seed.csv가 있다면 함께 복사
```

### 2. 백엔드 설정 및 실행

```bash
cd backend

# 가상환경 생성 (선택사항이지만 권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화 및 데이터 시딩
python init_db.py

# 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

백엔드는 `http://localhost:8000`에서 실행됩니다.

### 3. 프론트엔드 설정 및 실행

새로운 터미널에서:

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드는 `http://localhost:5173`에서 실행됩니다.

## 🔧 환경 변수 설정 (선택사항)

백엔드 폴더에 `.env` 파일을 생성하여 설정을 커스터마이징할 수 있습니다:

```env
# .env 파일
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key
DB_DIR=/custom/path/to/db  # 기본값: workspace/evagent/db
```

## 📝 주요 변경 사항

### 데이터베이스
- **MySQL → SQLite**로 변경
- 데이터베이스 파일 위치: `workspace/evagent/db/evagent.db`
- CSV 파일 위치: `workspace/evagent/db/`

### 경로 설정
모든 경로가 `workspace/evagent/db`를 기준으로 설정되어 있습니다:
- `backend/config.py`: DB 경로 자동 설정
- `backend/init_db.py`: CSV 파일 경로 자동 설정
- `backend/database.py`: SQLite 설정 포함

### API 엔드포인트
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- API Docs: `http://localhost:8000/docs`

## 🐛 문제 해결

### CSV 파일을 찾을 수 없다는 오류
- `workspace/evagent/db/` 폴더가 존재하는지 확인
- CSV 파일들이 올바른 위치에 있는지 확인

### 데이터베이스 초기화 오류
```bash
# 데이터베이스 파일 삭제 후 재생성
rm workspace/evagent/db/evagent.db
python backend/init_db.py
```

### 포트가 이미 사용 중인 경우
```bash
# 백엔드: 다른 포트 사용
uvicorn app:app --reload --port 8001

# 프론트엔드: vite.config.js에서 포트 변경
```

## 📚 API 문서

백엔드가 실행 중일 때 `http://localhost:8000/docs`에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

## 🎯 기능

- **OEM 회사 관리**: 자동차 제조사 정보 조회 및 관리
- **뉴스 피드**: 회사별 최신 뉴스 조회
- **공장 정보**: OEM, 배터리, HVAC 공장 위치 및 정보
- **보고서 생성**: AI 기반 분석 보고서 생성
- **사용자 인증**: 회원가입, 로그인, 즐겨찾기 기능
