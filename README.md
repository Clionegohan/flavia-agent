# 🍽️ Flavia AI - 学習型料理パートナー
*あなた専用のパーソナライズド料理アシスタント*

Flavia is an intelligent, learning-powered meal planning assistant that evolves with your preferences through advanced AI and continuous feedback learning.

## ✨ Features

- 🧠 **学習型AI**: ユーザーの評価から継続的に学習・改善
- 🎯 **完全パーソナライズ**: 個人の好み・健康目標・制約に最適化
- 💰 **特売情報統合**: リアルタイム価格情報でコスト最適化
- 🎨 **洗練されたUI**: アニメーション付きモダンStreamlitインターフェース
- 📊 **学習ダッシュボード**: 嗜好分析と学習進捗の可視化
- 🌍 **多文化対応**: 世界各国の料理スタイル
- ⚡ **リアルタイム**: 即座のレシピ生成と評価フィードバック

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Clionegohan/flavia-agent.git
   cd flavia-agent
   source .venv/bin/activate
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the chat UI:**
   ```bash
   # 学習型チャットUI (推奨)
   streamlit run flavia_chat.py
   
   # 従来のUI
   streamlit run src/flavia_agent/ui/streamlit_app.py
   
   # スクリプト経由
   ./scripts/run_app.sh
   ```

4. **Start using:**
   - ブラウザで http://localhost:8501 にアクセス
   - サイドバーの「🚀 Flavia起動」でエージェント開始
   - チャットで料理について質問
   - レシピを⭐評価して学習を促進

## Project Structure

```
flavia-agent/
├── flavia_chat.py      # 🎨 学習型チャットUI (メイン)
├── src/
│   └── flavia_agent/
│       ├── agent/      # 🤖 AIエージェントロジック
│       │   ├── flavia.py        # ベースエージェント
│       │   └── personal_flavia.py # 学習型エージェント
│       ├── data/       # 📊 データモデルとストレージ
│       │   ├── models/          # Pydanticモデル
│       │   ├── personal/        # 個人データ・学習履歴
│       │   └── storage/         # 分析・評価データ
│       ├── rag/        # 🧠 学習・コンテキスト生成
│       │   ├── learning_system.py    # 学習エンジン
│       │   ├── preference_parser.py  # 嗜好解析
│       │   └── sale_info_fetcher.py  # 特売情報
│       └── ui/         # 🖥️ 従来のStreamlit UI
├── utils/              # 🛠️ ヘルパー関数
├── tests/              # 🧪 テストファイル
├── docs/               # 📖 プロジェクトドキュメント
└── pyproject.toml      # ⚙️ プロジェクト設定
```

## 🧠 AI Learning System

Flaviaは以下の学習機能で継続的に改善します：

### 学習データ
- **レシピ評価**: ユーザーの⭐評価から嗜好を学習
- **適応的嗜好**: 時間経過による好みの変化を追跡
- **フィードバック履歴**: 詳細なユーザー行動分析
- **コンテキスト記憶**: 過去の料理体験を記憶

### 個人化機能
- **健康目標**: 栄養バランス・カロリー制御
- **料理スキル**: 調理技術レベルの考慮
- **季節適応**: 旬の食材・季節料理の提案
- **特売活用**: 価格情報との統合最適化

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
pytest

# Format code
black .
ruff check .

# Start chat UI for development
streamlit run flavia_chat.py --server.port=8501
```

## Requirements

- Python 3.12+
- OpenAI API key or Anthropic API key
- Optional: AWS credentials for enhanced features

## 🚀 What's New

- ✨ **完全新設計**: 学習型チャットUIインターフェース
- 🎨 **洗練デザイン**: アニメーション・グラデーション付きUI
- 📊 **リアルタイム学習**: 即座のフィードバック反映
- 🎯 **高度パーソナライズ**: 個人嗜好の深度分析
