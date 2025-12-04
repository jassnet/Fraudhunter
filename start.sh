#!/bin/bash
# Fraud Checker v2 - 起動スクリプト

echo "🚀 Fraud Checker v2 を起動します..."

# バックエンドを起動
echo "📦 バックエンド (FastAPI) を起動中..."
cd "$(dirname "$0")"
py -m uvicorn fraud_checker.api:app --reload --port 8000 &
BACKEND_PID=$!

# フロントエンドを起動
echo "🌐 フロントエンド (Next.js) を起動中..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 起動完了!"
echo ""
echo "📊 フロントエンド: http://localhost:3000"
echo "🔧 バックエンドAPI: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "終了するには Ctrl+C を押してください"

# 終了時のクリーンアップ
trap "echo '🛑 サーバーを停止します...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait

