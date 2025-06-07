# Flavia - AI献立アシスタントの開発記録

## プロジェクト概要

Flaviaは、ユーザーの予算・好み・時間制約に基づいて個人化された献立を提案するAI駆動の料理プランニングシステムです。

### 技術スタック
- Python 3.12+
- Streamlit (Web UI)
- OpenAI/Anthropic API
- Pydantic (データバリデーション)
- pytest (テスト)

## 実装のポイント

### 1. モジュラーアーキテクチャ
```python
flavia-agent/
├── src/flavia_agent/
│   ├── agent/      # AIエージェントのロジック
│   ├── data/       # データモデルとストレージ
│   └── ui/         # Streamlitインターフェース
```

### 2. 型安全性の確保
```python
from pydantic import BaseModel

class MealPreferences(BaseModel):
    budget: float
    dietary_restrictions: List[str]
    cooking_time: int
```

### 3. 非同期処理の活用
```python
async def generate_meal_plan(
    self,
    preferences: MealPreferences
) -> List[Recipe]:
    """非同期での献立生成"""
    pass
```

## 開発の課題と解決策

### 1. エラーハンドリング
- カスタム例外クラスの実装
- 詳細なエラーメッセージの提供
- エラー発生時の適切なフォールバック

### 2. データ永続化
- レシピデータの保存
- ユーザー設定の管理
- 履歴の追跡

### 3. パフォーマンス最適化
- 非同期処理の活用
- キャッシュの実装
- レスポンス時間の改善

## 今後の展望

### 1. 機能拡張
- 特売情報の自動取得
- 栄養バランスの分析
- レシピのレコメンデーション

### 2. 技術的改善
- テストカバレッジの向上
- エラーハンドリングの強化
- パフォーマンスの最適化

### 3. ユーザー体験の向上
- UI/UXの改善
- レスポンス速度の向上
- より直感的な操作性

## 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd flavia-agent

# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate

# 依存関係のインストール
uv sync --extra dev

# 環境変数の設定
cp .env.example .env
# .envファイルにAPIキーを設定

# アプリケーションの起動
streamlit run src/flavia_agent/ui/streamlit_app.py
```

## テスト実行

```bash
# 全テストの実行
pytest

# カバレッジ付き実行
pytest --cov=flavia_agent

# 特定のテストファイル実行
pytest tests/test_agent.py
```

## コード品質の維持

```bash
# コードフォーマット
black .

# リンティング
ruff check .

# 型チェック
mypy flavia_agent/
```

## まとめ

Flaviaの開発を通じて、以下の点を学びました：

1. モジュラーアーキテクチャの重要性
2. 型安全性の確保によるバグの防止
3. 非同期処理によるパフォーマンスの向上
4. テスト駆動開発の効果
5. エラーハンドリングの重要性

今後の開発では、これらの知見を活かしながら、より使いやすく、信頼性の高いシステムを目指していきます。
