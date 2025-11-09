#!/bin/bash

echo "=== Frontend 시작 ==="
echo ""

# 의존성 설치
echo "의존성 설치 중..."
npm install

# 개발 서버 실행
echo ""
echo "개발 서버 시작 중..."
npm run dev
