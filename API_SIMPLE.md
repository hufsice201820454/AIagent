# EVAgent API 간단 명세

## Base URL
`http://localhost:8000/api`

## 인증
```
Authorization: Bearer {token}
```

---

## 🔐 Auth

### 회원가입
`POST /auth/register`
```json
{
  "email": "test@test.com",
  "password": "test123",
  "name": "홍길동"
}
```

### 로그인
`POST /auth/login` (Form Data)
```
username=test@test.com
password=test123
```

응답:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## 🏢 Companies

### 기업 목록
`GET /companies/oem`

### 기업 상세
`GET /companies/oem/{id}`

### 즐겨찾기 토글
`POST /companies/oem/{id}/favorite`

---

## 📰 News

### 뉴스 목록
`GET /news?limit=20`

### 기업별 뉴스
`GET /news/company/{oem_id}/latest?limit=10`

---

## 📊 Reports

### 리포트 목록
`GET /reports`

### 리포트 생성
`POST /reports/generate`
```json
{
  "company_name": "Tesla",
  "oem_id": "xxx-xxx"
}
```

---

## 👤 Users

### 내 정보
`GET /users/me`

### 정보 수정
`PUT /users/me`
```json
{
  "name": "김철수",
  "phone_number": "010-1234-5678"
}
```

---

## 테스트
Swagger UI: http://localhost:8000/docs
