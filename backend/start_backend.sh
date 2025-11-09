#!/bin/bash

echo "=== Backend 시작 ==="
echo ""

# 가상환경이 있으면 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 의존성 설치
echo "의존성 설치 중..."
pip install -r requirements.txt --break-system-packages

# 데이터베이스 초기화
echo ""
echo "데이터베이스 초기화 중..."
python init_db.py

# 서버 실행
echo ""
echo "서버 시작 중..."
uvicorn app:app --reload --port 8000
