# 🍽️ Flavia AI - 学習型料理パートナー
*あなた専用のパーソナライズド料理アシスタント*

Flavia is an intelligent, learning-powered meal planning assistant that evolves with your preferences through advanced AI and continuous feedback learning.

## 💡 アプリ概要と制作背景

### 🏠 こんな悩みありませんか？

一人暮らし、主婦、主夫の自炊戦士のみなさん。毎日の献立作りって大変ですよね？

**日常の料理の悩み:**
- スーパーのチラシを見て献立を決める → 買い物リストを作る → レシピを調べる...
- この一連の流れ、とても手間じゃないですか？
- 献立が似たり寄ったりになってしまう
- 作り慣れたものばかりで、新しい料理に挑戦しにくい

もちろん楽しい時もありますが、**日常的にこなすもの**としては少し億劫に感じませんか？

### 🎯 Flaviaが解決すること

しかし、それでは根本的改善とは言えません。

**もしこんなAIエージェントがいたら...**
- 冷蔵庫の中身を把握している
- 近所のスーパーの特売情報をチェックしている  
- あなたの好き嫌いや調味料、キッチン用品を完全に理解している
- 今の気分や料理の練習したいレベルに合わせてくれる
- **見当違いの回答を一切しない**

そんなパーソナルな料理パートナーがいたら嬉しいと思いませんか？
**ということで作られたのが、このFlavia-agent です。**

### 🤖 Flaviaの仕組み

**Flavia-agent**は、完全個人に特化した専用の料理お助けエージェントです。

**RAGシステム活用:**
- あなたの食の好き嫌い・アレルギー情報
- 普段使いする調味料・キッチン用品
- 過去の料理履歴と評価データ
- 健康目標や料理スキルレベル

**使い方の例:**
```
「3日分の夕飯のメニュー。鶏肉と茄子とキャベツが食べたいな。」
```
↓
- 指定日数分の詳細な献立
- それぞれのレシピ（手順・調理時間付き）  
- 効率的な買い物リスト
- あなたの制約を完全に考慮した提案

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

3. **Run the application:**
   ```bash
   # メインアプリケーション (推奨)
   streamlit run src/flavia/ui/streamlit_app.py
   
   # または run_app.py 経由
   python run_app.py
   
   # スクリプト経由
   ./scripts/run_app.sh
   ```

4. **Start using:**
   - ブラウザで http://localhost:8501 にアクセス
   - サイドバーの「🚀 Flavia起動」でエージェント開始
   - チャットで料理について質問・相談
   - レシピを⭐評価して学習を促進

## Project Structure

```
flavia-agent/
├── run_app.py          # 🚀 アプリケーションエントリポイント
├── src/flavia/
│   ├── core/           # 🤖 コアロジック
│   │   ├── agents/     # AIエージェント
│   │   │   ├── base.py         # ベースエージェント
│   │   │   └── personal.py     # パーソナライズドエージェント
│   │   ├── models/     # データモデル
│   │   ├── services/   # ビジネスロジック
│   │   └── cache_manager.py # キャッシュ管理
│   ├── rag/            # 🧠 RAG・学習システム
│   │   ├── smart_context_builder.py # コンテキスト構築
│   │   ├── learning_system.py       # 学習エンジン
│   │   ├── preference_parser.py     # 嗜好解析
│   │   └── sale_info_fetcher.py     # 特売情報
│   ├── ui/             # 🎨 ユーザーインターフェース
│   │   └── streamlit_app.py # メインUI
│   ├── data/personal/  # 📊 個人データ・学習履歴
│   ├── monitoring/     # 📈 パフォーマンス監視
│   └── utils/          # 🛠️ ユーティリティ
├── tests/              # 🧪 テストファイル
├── docs/               # 📖 プロジェクトドキュメント
├── scripts/            # 🔧 運用スクリプト
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

# Start UI for development
streamlit run src/flavia/ui/streamlit_app.py --server.port=8501
```

## Requirements

- **Python 3.12+**: モダンなPython機能を活用
- **Claude API key**: Anthropic Claude APIキー（推奨）
- **OpenAI API key**: OpenAI APIキー（オプション）
- **リソース**: メモリ 4GB以上、ストレージ 1GB以上

詳細なセットアップ手順は [SETUP_API_KEY.md](SETUP_API_KEY.md) をご確認ください。

## 🚀 What's New

- ✨ **完全新設計**: 学習型RAGシステムとモダンアーキテクチャ
- 🎨 **洗練デザイン**: アニメーション・グラデーション付きUI
- 📊 **リアルタイム学習**: 即座のフィードバック反映と嗜好更新
- 🎯 **高度パーソナライズ**: 個人嗜好の深度分析と継続的改善
- 🚀 **パフォーマンス向上**: キャッシュシステムと非同期処理
