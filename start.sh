#!/bin/bash

echo "=== EVAgent 시작 스크립트 ==="
echo ""

# Backend 시작
echo "1. Backend 시작 중..."
cd backend
pip install -r requirements.txt --break-system-packages
python init_db.py
uvicorn app:app --reload --port 8000 &
BACKEND_PID=$!
echo "✓ Backend 시작됨 (PID: $BACKEND_PID)"

# Frontend 시작
echo ""
echo "2. Frontend 시작 중..."
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!
echo "✓ Frontend 시작됨 (PID: $FRONTEND_PID)"

echo ""
echo "=== 서비스 실행 중 ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "종료하려면 Ctrl+C를 누르세요"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
