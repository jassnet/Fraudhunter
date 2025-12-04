@echo off
REM Fraud Checker v2 - Windows起動スクリプト

echo 🚀 Fraud Checker v2 を起動します...
echo.

REM バックエンドを起動
echo 📦 バックエンド (FastAPI) を起動中...
start "FastAPI Backend" cmd /c "py -m uvicorn fraud_checker.api:app --reload --port 8000"

REM 少し待機
timeout /t 2 /nobreak >nul

REM フロントエンドを起動
echo 🌐 フロントエンド (Next.js) を起動中...
cd frontend
start "Next.js Frontend" cmd /c "npm run dev"

echo.
echo ✅ 起動完了!
echo.
echo 📊 フロントエンド: http://localhost:3000
echo 🔧 バックエンドAPI: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo ウィンドウを閉じるとサーバーも停止します
pause

