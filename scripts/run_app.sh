#!/bin/bash

set -e

echo "🚀 Flavia AI献立エージェントを起動しています..."

# 仮想環境の確認
if [ ! -d ".venv" ]; then
    echo "❌ 仮想環境が見つかりません。setup.shを先に実行してください。"
    exit 1
fi

# 環境変数の確認
if [ ! -f ".env" ]; then
    echo "⚠️  .envファイルが見つかりません。.env.exampleをコピーして設定してください。"
    echo "cp .env.example .env"
    exit 1
fi

# 仮想環境をアクティベート
source .venv/bin/activate

# Streamlitアプリを起動
echo "🌐 Streamlitアプリを起動中..."
streamlit run src/flavia_agent/ui/streamlit_app.py

echo "✅ アプリケーションが終了しました。"