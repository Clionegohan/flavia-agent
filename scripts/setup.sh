#!/bin/bash

set -e

echo "🚀 Python環境とAWS設定の自動セットアップを開始します..."

# uvのインストール
echo "📦 uvをインストールしています..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    echo "✅ uvのインストールが完了しました"
else
    echo "✅ uvは既にインストールされています"
fi

# Python仮想環境の作成
echo "🐍 Python仮想環境を作成しています..."
if [ ! -d ".venv" ]; then
    uv venv
    echo "✅ 仮想環境を作成しました"
else
    echo "✅ 仮想環境は既に存在します"
fi

# 仮想環境のアクティベート
echo "🔧 仮想環境をアクティベートしています..."
source .venv/bin/activate

# AWS CLIとboto3のインストール
echo "☁️ AWS CLIとboto3をインストールしています..."
uv pip install awscli boto3

echo "✅ セットアップが完了しました！"
echo ""
echo "次の手順："
echo "1. 仮想環境をアクティベート: source .venv/bin/activate"
echo "2. AWS設定: aws configure"
echo "3. 開発開始！"