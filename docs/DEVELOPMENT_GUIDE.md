# 🛠️ Flavia 開発ガイドライン

## 開発環境セットアップ

### 必要な環境
- Python 3.12+
- uv package manager
- Git
- VS Code（推奨）

### 初期セットアップ
```bash
# リポジトリクローン
git clone <repository-url>
cd flavia-agent

# 仮想環境アクティベート
source .venv/bin/activate

# 開発依存関係インストール
uv sync --extra dev

# 環境変数設定
cp .env.example .env
# .envファイルにAPIキーを設定

# プリコミットフック設定（推奨）
pre-commit install
```

## コーディング規約

### 1. Python コードスタイル

#### PEP 8 準拠 + Black フォーマット
```bash
# コード整形
black .

# リンティング
ruff check .

# 型チェック
mypy flavia_agent/
```

#### 命名規約
```python
# ✅ Good
class MealPlanGenerator:
    def generate_weekly_plan(self, preferences: MealPreferences) -> WeeklyPlan:
        pass

# ❌ Bad  
class mealplangenerator:
    def generateWeeklyPlan(self, prefs) -> dict:
        pass
```

#### インポート順序
```python
# 1. 標準ライブラリ
import os
import asyncio
from typing import List, Dict, Optional

# 2. サードパーティ
import streamlit as st
from pydantic import BaseModel
from openai import AsyncOpenAI

# 3. ローカルインポート
from flavia_agent.agent.base import BaseAgent
from flavia_agent.data.models import Recipe
```

### 2. 型ヒント必須

```python
# ✅ Good
async def generate_meal_plan(
    self, 
    preferences: MealPreferences
) -> List[Recipe]:
    """献立を生成する"""
    pass

# ❌ Bad
async def generate_meal_plan(self, preferences):
    pass
```

### 3. ドキュメント文字列

```python
class FlaviaAgent:
    """Flavia AI献立エージェント
    
    ユーザーの好みと制約に基づいて、AIを使用して
    個人化された献立を生成します。
    
    Attributes:
        provider: 使用するAIプロバイダー名
        client: AIクライアントインスタンス
    """
    
    async def generate_meal_plan(
        self, 
        preferences: MealPreferences
    ) -> List[Recipe]:
        """献立プランを生成する
        
        Args:
            preferences: ユーザーの好みと制約
            
        Returns:
            生成されたレシピのリスト
            
        Raises:
            AIProviderError: AI API呼び出しが失敗した場合
            ValidationError: 入力バリデーションが失敗した場合
        """
        pass
```

## Git ワークフロー

### ブランチ戦略
```
main ── develop ── feature/meal-planning
     └─ hotfix/critical-bug
```

### コミットメッセージ規約
```bash
# フォーマット: <type>(<scope>): <description>

# 例
feat(agent): add nutrition calculation to recipe generation
fix(ui): resolve recipe display formatting issue  
docs(arch): update architecture documentation
test(agent): add unit tests for FlaviaAgent
refactor(data): extract common validation logic
```

### プルリクエスト流れ
1. **feature ブランチ作成**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **開発 & テスト**
   ```bash
   # 開発
   # テスト実行
   pytest
   ```

3. **コード品質チェック**
   ```bash
   black .
   ruff check .
   mypy flavia_agent/
   ```

4. **PR作成**
   - 明確なタイトルと説明
   - 関連Issue番号記載
   - スクリーンショット（UI変更時）

## テスト戦略

### 1. テスト実行
```bash
# 全テスト実行
pytest

# カバレッジ付き実行
pytest --cov=flavia_agent

# 特定ファイルのテスト
pytest tests/test_agent.py

# 詳細出力
pytest -v
```

### 2. テスト作成ガイドライン

#### ファイル構成
```
tests/
├── unit/                # 単体テスト
│   ├── test_agent.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/         # 統合テスト
│   ├── test_ai_providers.py
│   └── test_end_to_end.py
├── fixtures/            # テストデータ
│   ├── sample_recipes.json
│   └── sample_preferences.json
└── conftest.py          # pytest設定
```

#### テスト命名規約
```python
class TestFlaviaAgent:
    """FlaviaAgentのテストクラス"""
    
    def test_generate_meal_plan_with_valid_preferences(self):
        """正常な好み設定で献立生成が成功することを確認"""
        pass
    
    def test_generate_meal_plan_with_invalid_budget_raises_error(self):
        """無効な予算設定でエラーが発生することを確認"""
        pass
    
    @pytest.mark.asyncio
    async def test_async_meal_plan_generation(self):
        """非同期での献立生成を確認"""
        pass
```

#### モック使用例
```python
@pytest.mark.asyncio
async def test_generate_meal_plan_success(self, mock_openai_client):
    """AIプロバイダーAPIをモックしてテスト"""
    # Arrange
    mock_response = """[{"name": "Test Recipe", ...}]"""
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = mock_response
    
    agent = FlaviaAgent(provider="openai")
    preferences = MealPreferences(budget=30.0)
    
    # Act
    recipes = await agent.generate_meal_plan(preferences)
    
    # Assert
    assert len(recipes) == 1
    assert recipes[0].name == "Test Recipe"
```

## 設定管理

### 1. 環境変数
```bash
# .env ファイル例
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_DEFAULT_REGION=us-west-2

# アプリ設定
FLAVIA_DEBUG=true
FLAVIA_LOG_LEVEL=INFO
FLAVIA_MAX_RECIPES=10
```

### 2. 設定クラス
```python
# flavia_agent/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # アプリ設定
    debug: bool = False
    log_level: str = "INFO"
    max_recipes: int = 10
    
    class Config:
        env_file = ".env"
        env_prefix = "FLAVIA_"

# 使用例
settings = Settings()
```

## エラー処理ベストプラクティス

### 1. 例外階層
```python
# flavia_agent/exceptions.py
class FlaviaException(Exception):
    """基底例外クラス"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AIProviderError(FlaviaException):
    """AIプロバイダー関連エラー"""
    pass

class ValidationError(FlaviaException):
    """入力バリデーションエラー"""
    pass
```

### 2. エラーハンドリングパターン
```python
async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
    try:
        # AI呼び出し
        response = await self._call_ai(prompt)
        recipes = self._parse_recipes(response)
        
        if not recipes:
            raise AIProviderError(
                "レシピの生成に失敗しました",
                details={"preferences": preferences.dict()}
            )
            
        return recipes
        
    except ValidationError:
        # バリデーションエラーはそのまま再発生
        raise
    except Exception as e:
        # その他のエラーをラップ
        raise AIProviderError(
            f"献立生成中にエラーが発生しました: {str(e)}",
            details={"original_error": type(e).__name__}
        )
```

### 3. ログ戦略
```python
import logging
import structlog

# 構造化ログ設定
logger = structlog.get_logger(__name__)

async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
    logger.info(
        "献立生成開始",
        user_budget=preferences.budget,
        dietary_restrictions=preferences.dietary_restrictions,
        provider=self.provider
    )
    
    try:
        recipes = await self._call_ai(prompt)
        
        logger.info(
            "献立生成成功", 
            recipe_count=len(recipes),
            total_cost=sum(r.estimated_cost for r in recipes)
        )
        
        return recipes
        
    except Exception as e:
        logger.error(
            "献立生成失敗",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

## パフォーマンス最適化

### 1. 非同期プログラミング
```python
# ✅ Good: 複数レシピの並列生成
async def generate_multiple_recipes(
    self, 
    queries: List[str], 
    preferences: MealPreferences
) -> List[Recipe]:
    tasks = [
        self.get_recipe_suggestions(query, preferences) 
        for query in queries
    ]
    results = await asyncio.gather(*tasks)
    return [recipe for result in results for recipe in result]

# ❌ Bad: 逐次処理
async def generate_multiple_recipes_slow(
    self, 
    queries: List[str], 
    preferences: MealPreferences
) -> List[Recipe]:
    results = []
    for query in queries:
        recipes = await self.get_recipe_suggestions(query, preferences)
        results.extend(recipes)
    return results
```

### 2. キャッシュ活用（将来実装）
```python
from functools import lru_cache

class FlaviaAgent:
    @lru_cache(maxsize=128)
    def _build_prompt(self, preferences_hash: str) -> str:
        """プロンプト構築のキャッシュ"""
        pass
    
    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        # キャッシュキー生成
        cache_key = hash(preferences.json())
        
        # キャッシュから取得試行
        cached_recipes = await self.cache.get(cache_key)
        if cached_recipes:
            return cached_recipes
            
        # 新規生成
        recipes = await self._generate_fresh_meal_plan(preferences)
        
        # キャッシュに保存
        await self.cache.set(cache_key, recipes, ttl=3600)
        
        return recipes
```

## デバッグとトラブルシューティング

### 1. 開発環境でのデバッグ
```python
# デバッグモード設定
FLAVIA_DEBUG=true

# ログレベル調整
FLAVIA_LOG_LEVEL=DEBUG

# Streamlitデバッグ実行
streamlit run flavia_agent/ui/streamlit_app.py --logger.level=debug
```

### 2. よくある問題と解決策

#### API キーエラー
```bash
# エラー: Authentication failed
# 解決策: .envファイルのAPIキー確認
cat .env | grep API_KEY
```

#### 依存関係エラー
```bash
# エラー: ModuleNotFoundError
# 解決策: 仮想環境と依存関係の再インストール
source .venv/bin/activate
uv sync --extra dev
```

#### テスト失敗
```bash
# 詳細なテスト出力で原因特定
pytest -v --tb=long

# 特定テストのみ実行
pytest tests/test_agent.py::TestFlaviaAgent::test_specific_method -v
```

## セキュリティ考慮事項

### 1. API キー管理
```python
# ✅ Good: 環境変数使用
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ConfigurationError("OpenAI API key not found")

# ❌ Bad: ハードコード
api_key = "sk-1234567890abcdef"  # 絶対にしない！
```

### 2. 入力サニタイゼーション
```python
# Pydanticによる厳密なバリデーション
class MealPreferences(BaseModel):
    budget: float = Field(gt=0, le=1000, description="予算は0より大きく1000以下")
    dietary_restrictions: List[str] = Field(max_items=10)
    cooking_time: int = Field(ge=5, le=480, description="調理時間は5分から8時間")
```

### 3. ログでの機密情報除外
```python
# ✅ Good: 機密情報をマスク
logger.info("API呼び出し実行", provider="openai", model="gpt-3.5-turbo")

# ❌ Bad: APIキーを含む
logger.info(f"API Key: {api_key} でリクエスト実行")  # 絶対にしない！
```

## 継続的インテグレーション

### GitHub Actions 設定例
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Install dependencies
      run: uv sync --extra dev
    
    - name: Run tests
      run: uv run pytest --cov=flavia_agent
    
    - name: Code quality
      run: |
        uv run black --check .
        uv run ruff check .
        uv run mypy flavia_agent/
```

## 学習と成長のためのリソース

### 推奨書籍
- 「Clean Code」- Robert C. Martin
- 「Architecture Patterns with Python」- Harry Percival & Bob Gregory
- 「Effective Python」- Brett Slatkin

### 推奨オンラインリソース
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/) - 現代的なAPI設計
- [Pydantic公式ドキュメント](https://pydantic-docs.helpmanual.io/) - データバリデーション
- [Streamlit公式ドキュメント](https://docs.streamlit.io/) - UI開発

### コードレビューのポイント
1. **機能性**: コードが仕様通りに動作するか
2. **可読性**: 他の開発者が理解しやすいか
3. **保守性**: 将来の変更に対応しやすいか
4. **テスト**: 適切なテストが書かれているか
5. **パフォーマンス**: 不要な処理やボトルネックがないか