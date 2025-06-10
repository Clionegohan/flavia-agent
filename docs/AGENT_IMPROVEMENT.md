# 🤖 Flavia Agent 改善案 - Strands Agent アーキテクチャ

## 概要

現在のFlaviaAgentを、より柔軟で拡張性の高いStrands Agentアーキテクチャに改善する提案です。
各エージェントが特定の責務に特化し、それらをStrands Agentが統合することで、より洗練されたシステムを実現します。

## 現状の分析

現在のFlaviaAgentは以下の責務を一つのクラスで管理しています：

1. レシピ生成
2. 買い物リスト管理
3. コンテキスト管理
4. プロンプト生成
5. AI API呼び出しとレスポンス処理

## 提案する改善アーキテクチャ

### 1. 専門エージェントの分割

#### RecipeAgent（レシピ生成エージェント）
```python
class RecipeAgent:
    """レシピ生成に特化したエージェント"""
    
    async def generate_recipe(self, request: str, context: Dict) -> Dict:
        """単発レシピの生成"""
        # 現在の _create_recipe_prompt と _call_claude_api の責務
        pass
    
    async def generate_weekly_plan(self, days: int, request: str, context: Dict) -> Dict:
        """週間献立の生成"""
        # 現在の _create_weekly_prompt の責務
        pass
```

#### ShoppingAgent（買い物リストエージェント）
```python
class ShoppingAgent:
    """買い物リスト管理に特化したエージェント"""
    
    def generate_shopping_list(self, recipes: List[Dict]) -> Dict:
        """買い物リストの生成"""
        # 現在の _generate_shopping_list の責務
        pass
    
    def group_ingredients(self, ingredients: List[str]) -> List[str]:
        """食材のグループ化"""
        # 現在の _group_same_ingredients の責務
        pass
    
    async def send_to_discord(self, shopping_list: Dict) -> bool:
        """Discordへの送信"""
        # 現在の send_shopping_list_to_discord の責務
        pass
```

#### ContextAgent（コンテキスト管理エージェント）
```python
class ContextAgent:
    """ユーザーコンテキスト管理に特化したエージェント"""
    
    def create_context(self, user_request: str) -> Dict:
        """コンテキストの生成"""
        # 現在の data_manager.create_context_for_ai の責務
        pass
    
    def update_preferences(self, feedback: Dict) -> None:
        """ユーザー設定の更新"""
        # 現在の data_manager の設定更新責務
        pass
```

#### PromptAgent（プロンプト管理エージェント）
```python
class PromptAgent:
    """プロンプト生成に特化したエージェント"""
    
    def create_recipe_prompt(self, request: str, context: Dict) -> str:
        """レシピ生成用プロンプトの作成"""
        # 現在の _create_recipe_prompt の責務
        pass
    
    def create_weekly_prompt(self, days: int, request: str, context: Dict) -> str:
        """週間献立用プロンプトの作成"""
        # 現在の _create_weekly_prompt の責務
        pass
```

#### ResponseAgent（レスポンス処理エージェント）
```python
class ResponseAgent:
    """AIレスポンス処理に特化したエージェント"""
    
    async def call_ai_api(self, prompt: str) -> str:
        """AI APIの呼び出し"""
        # 現在の _call_claude_api の責務
        pass
    
    def parse_json_response(self, response: str) -> Dict:
        """JSONレスポンスの解析"""
        # 現在の _parse_json_response の責務
        pass
```

### 2. Strands Agent（統合エージェント）

```python
class StrandsAgent:
    """複数の専門エージェントを統合するコーディネーター"""
    
    def __init__(self):
        self.recipe_agent = RecipeAgent()
        self.shopping_agent = ShoppingAgent()
        self.context_agent = ContextAgent()
        self.prompt_agent = PromptAgent()
        self.response_agent = ResponseAgent()
    
    async def generate_recipe(self, user_request: str) -> Dict:
        # 1. コンテキスト生成
        context = self.context_agent.create_context(user_request)
        
        # 2. プロンプト生成
        prompt = self.prompt_agent.create_recipe_prompt(user_request, context)
        
        # 3. AI呼び出しとレスポンス解析
        response = await self.response_agent.call_ai_api(prompt)
        recipe = self.response_agent.parse_json_response(response)
        
        # 4. 買い物リスト生成
        shopping_list = self.shopping_agent.generate_shopping_list([recipe])
        
        return {
            "recipe": recipe,
            "shopping_list": shopping_list,
            "context": context
        }
```

## 改善の利点

### 1. 単一責任の原則
- 各エージェントが特定の機能に特化
- コードの保守性とテスト容易性の向上
- 機能の追加・変更が容易

### 2. 拡張性
- 新しい機能の追加が容易
- 各エージェントの独立した改善が可能
- 異なるAIプロバイダーの利用が簡単

### 3. 柔軟性
- エージェントの組み合わせ変更が容易
- 機能の有効/無効の切り替えが簡単
- 異なる実装の差し替えが容易

### 4. 並列処理
- 複数のエージェントを並列実行可能
- パフォーマンスの向上
- リソースの効率的な利用

### 5. エラー処理
- 各エージェントで適切なエラー処理
- より細かいエラー制御が可能
- エラーの影響範囲の限定

## 実装計画

### フェーズ1: 基本実装
1. RecipeAgentとContextAgentの実装
2. 基本的なStrandsAgentの実装
3. 既存機能の移行

### フェーズ2: 機能拡張
1. ShoppingAgentの実装
2. PromptAgentの実装
3. ResponseAgentの実装

### フェーズ3: 最適化
1. 並列処理の実装
2. キャッシュ機能の追加
3. エラー処理の強化

## 注意点

1. **段階的な移行**
   - 既存機能を維持しながら移行
   - 各フェーズでのテスト実施
   - ユーザーへの影響を最小限に

2. **後方互換性**
   - 既存のAPIインターフェースを維持
   - 段階的な機能追加
   - 適切なバージョン管理

3. **パフォーマンス**
   - エージェント間の通信オーバーヘッドに注意
   - キャッシュ戦略の検討
   - リソース使用量の監視

## 将来の展望

1. **新しいエージェントの追加**
   - NutritionAgent（栄養管理）
   - CostAgent（コスト最適化）
   - PreferenceAgent（嗜好学習）

2. **高度な機能**
   - エージェント間の協調学習
   - 動的なエージェント構成
   - 自己最適化機能

3. **スケーラビリティ**
   - 分散処理対応
   - クラウドリソースの活用
   - 負荷分散の実装 
