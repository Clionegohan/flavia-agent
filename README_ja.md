# 🍽️ Flavia - AIによる食事プランニングアシスタント

Flaviaは、予算、食事の好み、調理の制約に基づいて、パーソナライズされたレシピを提案するインテリジェントな食事プランニングアシスタントです。

## 主な機能

- 🤖 OpenAIまたはAnthropicを活用したAIによるレシピ提案
- 💰 予算を考慮した食事プランニング
- 🥗 食事制限への対応
- 🌍 多様な料理ジャンルへの対応
- ⏱️ 調理時間の制約に対応
- 🖥️ 美しいStreamlitウェブインターフェース

## クイックスタート

1. **リポジトリのクローンとセットアップ:**
   ```bash
   git clone <repository-url>
   cd flavia-agent
   source .venv/bin/activate
   ```

2. **APIキーの設定:**
   ```bash
   cp .env.example .env
   # .envファイルにAPIキーを設定
   ```

3. **アプリケーションの起動:**
   ```bash
   streamlit run flavia_agent/ui/streamlit_app.py
   ```

## プロジェクト構成

```
flavia-agent/
├── flavia_agent/
│   ├── agent/          # AIエージェントのロジック
│   ├── data/           # データモデルとストレージ
│   └── ui/             # Streamlitインターフェース
├── tests/              # テストファイル
├── .env.example        # 環境設定テンプレート
└── pyproject.toml      # プロジェクト設定
```

## 開発環境

```bash
# 開発用依存関係のインストール
uv sync --extra dev

# テストの実行
pytest

# コードフォーマット
black .
ruff check .
```

## 必要条件

- Python 3.12以上
- OpenAI APIキーまたはAnthropic APIキー
- オプション: 拡張機能のためのAWS認証情報 
