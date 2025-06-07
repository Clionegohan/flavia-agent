# 🏗️ Flavia アーキテクチャ設計書

## システム概要

Flaviaは**レイヤードアーキテクチャ**を採用し、関心の分離と拡張性を重視した設計となっています。

## アーキテクチャ原則

### 1. SOLID原則の遵守
- **Single Responsibility**: 各クラスは単一の責任を持つ
- **Open/Closed**: 拡張に開き、修正に閉じる
- **Liskov Substitution**: 基底クラスは派生クラスで置換可能
- **Interface Segregation**: 必要なインターフェースのみに依存
- **Dependency Inversion**: 抽象に依存し、具象に依存しない

### 2. 設計パターン活用
- **Strategy Pattern**: AIプロバイダーの切り替え
- **Factory Pattern**: エージェントの生成
- **Repository Pattern**: データアクセスの抽象化（将来実装）
- **Observer Pattern**: UI状態管理（将来実装）

## システム構成図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │    Business     │    │      Data       │
│     Layer       │◄──►│     Layer       │◄──►│     Layer       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│                 │    │                 │    │                 │
│ • Streamlit UI  │    │ • FlaviaAgent   │    │ • Pydantic     │
│ • Input Validation │ │ • BaseAgent     │    │   Models        │
│ • Result Display│    │ • AI Providers  │    │ • Future: DB    │
│                 │    │ • Business Logic│    │ • Future: Cache │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## レイヤー詳細

### 1. Presentation Layer (`flavia_agent/ui/`)

**責任**: ユーザーインターフェースとユーザー体験

```python
flavia_agent/ui/
├── streamlit_app.py      # メインUI（現在）
├── components/           # 再利用可能コンポーネント（将来）
│   ├── recipe_card.py    
│   ├── preference_form.py
│   └── meal_plan_view.py
└── utils/                # UI専用ユーティリティ
    ├── formatters.py
    └── validators.py
```

**設計規約**:
- Streamlit特有のロジックはこの層に閉じ込める
- ビジネスロジックを含まない
- 入力値検証は軽量に（詳細検証はPydanticで）
- 非同期処理は`asyncio.run()`で同期化

### 2. Business Layer (`flavia_agent/agent/`)

**責任**: ビジネスロジックとAI連携

```python
flavia_agent/agent/
├── base.py               # 抽象基底クラス
├── flavia.py            # メインエージェント
├── providers/           # AIプロバイダー別実装
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── local_provider.py   # 将来: ローカルLLM
├── strategies/          # 献立生成戦略
│   ├── budget_optimizer.py
│   ├── nutrition_balancer.py
│   └── preference_matcher.py
└── utils/
    ├── prompt_builder.py   # プロンプト構築
    ├── response_parser.py  # AI応答パース
    └── cost_calculator.py  # コスト計算
```

**設計規約**:
- すべてのAI操作は`async`で実装
- プロバイダー切り替えは設定ベース
- エラー処理は例外ベース
- ログ出力は構造化JSON

### 3. Data Layer (`flavia_agent/data/`)

**責任**: データモデルと永続化

```python
flavia_agent/data/
├── models/              # Pydanticデータモデル
│   ├── preferences.py   # MealPreferences
│   ├── recipe.py        # Recipe, Ingredient
│   ├── user.py          # User（将来）
│   └── meal_plan.py     # MealPlan（将来）
├── repositories/        # データアクセス層（将来）
│   ├── recipe_repo.py
│   ├── user_repo.py
│   └── cache_repo.py
└── schemas/             # DBスキーマ（将来）
    ├── tables.py
    └── migrations/
```

**設計規約**:
- すべてのデータはPydanticモデルで型安全
- バリデーションはモデルレベルで実施
- 将来のDB追加に備えたRepository Pattern
- キャッシュ戦略の考慮

## AI連携アーキテクチャ

### Provider Strategy Pattern

```python
# base.py
class BaseAgent(ABC):
    @abstractmethod
    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        pass

# flavia.py
class FlaviaAgent(BaseAgent):
    def __init__(self, provider: str = "openai"):
        self.provider = self._create_provider(provider)
    
    def _create_provider(self, name: str) -> AIProvider:
        # Factory Pattern for provider creation
        pass
```

### プロンプト管理戦略

```python
class PromptBuilder:
    """プロンプト構築の中央管理"""
    
    @staticmethod
    def build_meal_plan_prompt(preferences: MealPreferences) -> str:
        # テンプレートベースのプロンプト構築
        pass
    
    @staticmethod  
    def build_recipe_search_prompt(query: str, preferences: MealPreferences) -> str:
        pass
```

## データフロー

```
User Input → Streamlit → MealPreferences → FlaviaAgent → AI Provider
    ↑                                                          ↓
UI Display ← Recipe List ← Response Parser ← AI Response ←─────┘
```

### 1. 入力フロー
1. **UI入力**: Streamlitフォーム
2. **バリデーション**: Pydantic MealPreferences
3. **ビジネスロジック**: FlaviaAgent.generate_meal_plan()
4. **AI呼び出し**: Provider-specific API call

### 2. 出力フロー
1. **AI応答**: JSON文字列
2. **パース**: response_parser.py
3. **モデル化**: Recipe Pydanticモデル
4. **UI表示**: Streamlit components

## エラーハンドリング戦略

### 例外階層

```python
class FlaviaException(Exception):
    """基底例外クラス"""
    pass

class AIProviderError(FlaviaException):
    """AIプロバイダー関連エラー"""
    pass

class ValidationError(FlaviaException):
    """バリデーションエラー"""
    pass

class ConfigurationError(FlaviaException):
    """設定エラー"""
    pass
```

### エラー処理原則
- **Fail Fast**: 早期検出・早期失敗
- **Graceful Degradation**: 部分的な機能低下を許容
- **User-Friendly Messages**: ユーザー向けエラーメッセージ
- **Detailed Logging**: 開発者向け詳細ログ

## セキュリティ考慮事項

### 1. API Key Management
- 環境変数による管理
- `.env`ファイルの`.gitignore`登録
- AWS Secrets Manager連携（将来）

### 2. Input Validation
- Pydanticによる厳密な型チェック
- SQLインジェクション対策（DB追加時）
- XSS対策（Streamlitが基本対応済み）

### 3. Rate Limiting
- AIプロバイダーのレート制限遵守
- 将来的なRedis-based rate limiting

## パフォーマンス最適化

### 1. 非同期処理
- すべてのAI呼び出しは`async/await`
- 複数レシピの並列生成
- キャッシュとの非同期連携

### 2. キャッシュ戦略（将来実装）
```python
# Redis-based caching
class CacheRepository:
    async def get_cached_recipes(self, preferences_hash: str) -> Optional[List[Recipe]]:
        pass
    
    async def cache_recipes(self, preferences_hash: str, recipes: List[Recipe]) -> None:
        pass
```

### 3. レスポンス最適化
- AI応答のStreaming（将来）
- 段階的なレシピ表示
- 画像の遅延ローディング

## 拡張ポイント

### 1. 新AIプロバイダー追加
```python
class NewAIProvider(BaseAgent):
    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        # 新プロバイダーの実装
        pass
```

### 2. 新機能追加
- **栄養計算**: `nutrition/` パッケージ
- **在庫管理**: `inventory/` パッケージ  
- **ソーシャル**: `social/` パッケージ

### 3. 新UI追加
- **モバイルアプリ**: `mobile_api/` パッケージ
- **APIサーバー**: `rest_api/` パッケージ

## テスト戦略

### 1. テストピラミッド
```
    E2E Tests (少数)
   ─────────────────
  Integration Tests (中程度)
 ─────────────────────────
Unit Tests (多数)
```

### 2. テスト種別
- **Unit Tests**: 各クラス・関数の単体テスト
- **Integration Tests**: AI API連携テスト
- **E2E Tests**: Streamlit UI全体テスト
- **Performance Tests**: レスポンス時間・負荷テスト

### 3. テストダブル活用
- **Mock**: AI API呼び出し
- **Stub**: 固定データ返却
- **Fake**: インメモリDB