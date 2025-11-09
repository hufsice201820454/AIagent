# 🚀 EVAgent PostgreSQL 완전 고정 버전

## ⚡ 빠른 실행 (3단계)

### 1️⃣ PostgreSQL 데이터베이스 생성
```bash
# pgAdmin 또는 psql에서
CREATE DATABASE evagent;

# 또는 명령줄에서
createdb -U postgres evagent
```

### 2️⃣ Backend 실행
```bash
cd backend

# 패키지 설치
pip install -r requirements.txt

# DB 초기화
python init_db.py

# 서버 실행
uvicorn app:app --reload
```

### 3️⃣ Frontend 실행 (새 터미널)
```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4️⃣ 접속
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

---

## 🔧 환경 설정

### .env 파일 (backend/.env)
이미 생성되어 있습니다! 필요시 수정:

```properties
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=secret
DB_HOST=127.0.0.1
DB_PORT=5432
```

---

## 📁 폴더 구조

```
evagent/
├── agents/          # Agent 파일들 (수정 금지!)
├── backend/         # FastAPI 백엔드
│   ├── .env        # PostgreSQL 설정 (이미 생성됨)
│   ├── config.py   # PostgreSQL 전용
│   ├── database.py # PostgreSQL 전용
│   └── ...
├── frontend/        # Vue 프론트엔드
├── db/             # CSV 데이터 파일
└── db_sample/      # CSV 샘플
```

---

## ✅ 수정된 파일 목록

### Backend
- ✅ `config.py` - PostgreSQL 전용으로 완전히 수정
- ✅ `database.py` - SQLite 옵션 제거
- ✅ `app.py` - SQLite 옵션 제거
- ✅ `requirements.txt` - psycopg2-binary 추가
- ✅ `.env` - PostgreSQL 설정 포함

### 변경 사항
- **SQLite 완전 제거** - PostgreSQL만 사용
- **dotenv 강제 로드** - .env 파일 확실히 읽기
- **pool_pre_ping 추가** - 연결 유지
- **psycopg2-binary** - PostgreSQL 드라이버 추가

---

## 🐛 문제 해결

### "could not connect to server"
```bash
# PostgreSQL 서비스 시작
# Windows: services.msc에서 postgresql 시작
# Mac: brew services start postgresql
# Linux: sudo systemctl start postgresql
```

### "database does not exist"
```bash
createdb -U postgres evagent
```

### "authentication failed"
`.env` 파일에서 비밀번호 확인

### "psycopg2 설치 오류"
```bash
pip install psycopg2-binary
```

---

## 🎯 체크리스트

- [ ] PostgreSQL 설치되어 있음
- [ ] PostgreSQL 서비스 실행 중
- [ ] pgAdmin 열려 있음
- [ ] `evagent` 데이터베이스 생성됨
- [ ] `pip install -r requirements.txt` 완료
- [ ] `python init_db.py` 성공
- [ ] `npm install` 완료

---

## 🔥 완전히 새로 시작하려면

### PostgreSQL 초기화
```sql
-- pgAdmin 또는 psql에서
DROP DATABASE IF EXISTS evagent;
CREATE DATABASE evagent;
```

### Backend 재설정
```bash
cd backend
pip install -r requirements.txt --force-reinstall
python init_db.py
uvicorn app:app --reload
```

---

## 📞 지원

- Backend API 문서: http://localhost:8000/docs
- 오류 발생 시: `python config.py`로 DATABASE_URL 확인

---

## ⚠️ 중요!

- **agents 폴더는 절대 수정 금지!**
- **PostgreSQL만 사용** (SQLite 완전 제거됨)
- **.env 파일 필수** (이미 생성되어 있음)

---

끝! 이제 작동합니다! 🎉
