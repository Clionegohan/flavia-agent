# 🚀 Flavia Agent アーキテクチャ改善 - 実装プラン

## 実装概要

現在のFlaviaAgentを、責務分離されたマルチエージェントアーキテクチャに段階的に移行します。Pydanticを使用した型安全性と、明確なエラーハンドリング戦略を採用します。

## 前提条件・設計方針

### 1. 並列処理戦略
- **依存関係のある処理**: 順次実行（コンテキスト→プロンプト→AI呼び出し）
- **独立した処理**: `asyncio.gather()`で並列実行
- **例**: コンテキスト生成とプロンプトテンプレート準備は並列化可能

### 2. エラーハンドリング戦略
- **基本方針**: 失敗時は明確にエラー表示、フォールバック無し
- **理由**: 成功/失敗の紛らわしさを排除
- **実装**: 各AgentでException発生 → StrandsAgentでキャッチ → UI表示

### 3. 型定義とデータ交換
- **Pydantic使用**: 型安全性とバリデーション
- **JSON形式**: Agent間通信は構造化されたデータ
- **メリット**: IDE支援、ランタイムバリデーション、ドキュメント自動生成

## フェーズ1: 基本実装

### 1.1 データモデル定義

```python
# src/flavia/core/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class UserRequest(BaseModel):
    text: str = Field(..., description="ユーザーのリクエスト内容")
    days: Optional[int] = Field(None, description="献立日数")
    request_id: str = Field(..., description="リクエストID")

class UserContext(BaseModel):
    profile: Dict = Field(..., description="ユーザープロフィール")
    preferences: Dict = Field(..., description="食の嗜好")
    health_goals: List[str] = Field(..., description="健康目標")
    cooking_skills: Dict = Field(..., description="調理スキル")
    kitchen_equipment: Dict = Field(..., description="調理器具")
    pantry_items: Dict = Field(..., description="常備品")
    recent_updates: List[Dict] = Field(default=[], description="最近の更新")

class Recipe(BaseModel):
    name: str = Field(..., description="料理名")
    description: str = Field(..., description="料理の説明")
    ingredients: List[str] = Field(..., description="材料リスト")
    instructions: List[str] = Field(..., description="調理手順")
    prep_time: int = Field(..., description="準備時間（分）")
    cook_time: int = Field(..., description="調理時間（分）")
    total_time: int = Field(..., description="合計時間（分）")
    servings: int = Field(..., description="人数分")
    estimated_cost: int = Field(..., description="推定コスト（円）")
    difficulty: str = Field(..., description="難易度")
    notes: Optional[str] = Field(None, description="ポイント・注意事項")

class DinnerPlan(BaseModel):
    day: int = Field(..., description="日数")
    date: str = Field(..., description="日付")
    main_dish: str = Field(..., description="メイン料理名")
    description: str = Field(..., description="説明")
    ingredients: List[str] = Field(..., description="材料")
    detailed_recipe: Recipe = Field(..., description="詳細レシピ")
    estimated_cost: int = Field(..., description="推定コスト")
    difficulty: str = Field(..., description="難易度")

class WeeklyPlan(BaseModel):
    plan_days: int = Field(..., description="献立日数")
    dinners: List[DinnerPlan] = Field(..., description="夕食プラン")
    generation_time: datetime = Field(..., description="生成時刻")
    request: str = Field(..., description="元リクエスト")

class ShoppingList(BaseModel):
    items: List[str] = Field(..., description="買い物アイテム")
    total_items: int = Field(..., description="アイテム総数")
    excluded_pantry_items: int = Field(..., description="除外された常備品数")
    notes: str = Field(..., description="備考")

class AgentResponse(BaseModel):
    success: bool = Field(..., description="成功フラグ")
    data: Optional[Dict] = Field(None, description="レスポンスデータ")
    error: Optional[str] = Field(None, description="エラーメッセージ")
    agent_name: str = Field(..., description="実行エージェント名")
    execution_time: float = Field(..., description="実行時間（秒）")
```

### 1.2 基本Agentクラス

```python
# src/flavia/core/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict
import time
import asyncio
from ..models import AgentResponse

class BaseAgent(ABC):
    """全Agentの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def execute(self, *args, **kwargs) -> AgentResponse:
        """実行メソッド（エラーハンドリング付き）"""
        start_time = time.time()
        
        try:
            result = await self._execute(*args, **kwargs)
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=True,
                data=result,
                agent_name=self.name,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.name,
                execution_time=execution_time
            )
    
    @abstractmethod
    async def _execute(self, *args, **kwargs) -> Dict[str, Any]:
        """各Agentで実装する実際の処理"""
        pass
```

### 1.3 ContextAgent実装

```python
# src/flavia/core/agents/context_agent.py
from .base_agent import BaseAgent
from ..data_manager import data_manager
from ..models import UserRequest, UserContext
from typing import Dict, Any

class ContextAgent(BaseAgent):
    """コンテキスト管理エージェント"""
    
    def __init__(self):
        super().__init__("ContextAgent")
    
    async def _execute(self, request: UserRequest) -> Dict[str, Any]:
        """ユーザーコンテキストの生成"""
        
        # 個人データ読み込み
        personal_data = data_manager.load_data()
        
        # 最近の更新取得
        recent_updates = data_manager.get_recent_updates(days=30)
        
        # UserContextモデルで構造化
        context = UserContext(
            profile=personal_data.get("profile", {}),
            preferences=personal_data.get("preferences", {}),
            health_goals=personal_data.get("health_goals", []),
            cooking_skills=personal_data.get("cooking_skills", {}),
            kitchen_equipment=personal_data.get("kitchen_equipment", {}),
            pantry_items=personal_data.get("pantry_items", {}),
            recent_updates=recent_updates
        )
        
        return {"context": context.dict()}
```

### 1.4 RecipeAgent実装

```python
# src/flavia/core/agents/recipe_agent.py
from .base_agent import BaseAgent
from ..models import UserRequest, UserContext, Recipe, WeeklyPlan, DinnerPlan
from typing import Dict, Any
import json
import random
import time
import hashlib
from datetime import datetime, timedelta

class RecipeAgent(BaseAgent):
    """レシピ生成エージェント"""
    
    def __init__(self):
        super().__init__("RecipeAgent")
    
    async def _execute(self, request: UserRequest, context: UserContext) -> Dict[str, Any]:
        """レシピまたは週間献立の生成"""
        
        if request.days:
            # 週間献立生成
            return await self._generate_weekly_plan(request, context)
        else:
            # 単発レシピ生成
            return await self._generate_single_recipe(request, context)
    
    async def _generate_weekly_plan(self, request: UserRequest, context: UserContext) -> Dict[str, Any]:
        """週間献立生成"""
        
        # プロンプト生成
        prompt = self._create_weekly_prompt(request.days, request.text, context)
        
        # AI API呼び出し（別エージェントに移行予定だが、一旦ここで実装）
        response = await self._call_claude_api(prompt)
        
        # JSON解析
        dinner_data = self._parse_json_response(response)
        
        # WeeklyPlanモデルで構造化
        dinners = []
        for dinner_raw in dinner_data.get("dinners", []):
            recipe_raw = dinner_raw.get("detailed_recipe", {})
            
            recipe = Recipe(
                name=recipe_raw.get("name", dinner_raw.get("main_dish", "")),
                description=recipe_raw.get("description", dinner_raw.get("description", "")),
                ingredients=dinner_raw.get("ingredients", []),
                instructions=recipe_raw.get("instructions", []),
                prep_time=recipe_raw.get("prep_time", 0),
                cook_time=recipe_raw.get("cook_time", 0),
                total_time=recipe_raw.get("prep_time", 0) + recipe_raw.get("cook_time", 0),
                servings=recipe_raw.get("servings", 1),
                estimated_cost=dinner_raw.get("estimated_cost", 0),
                difficulty=dinner_raw.get("difficulty", "普通"),
                notes=recipe_raw.get("notes", "")
            )
            
            dinner = DinnerPlan(
                day=dinner_raw.get("day", 0),
                date=dinner_raw.get("date", ""),
                main_dish=dinner_raw.get("main_dish", ""),
                description=dinner_raw.get("description", ""),
                ingredients=dinner_raw.get("ingredients", []),
                detailed_recipe=recipe,
                estimated_cost=dinner_raw.get("estimated_cost", 0),
                difficulty=dinner_raw.get("difficulty", "普通")
            )
            dinners.append(dinner)
        
        weekly_plan = WeeklyPlan(
            plan_days=request.days,
            dinners=dinners,
            generation_time=datetime.now(),
            request=request.text
        )
        
        return {"weekly_plan": weekly_plan.dict()}
    
    async def _generate_single_recipe(self, request: UserRequest, context: UserContext) -> Dict[str, Any]:
        """単発レシピ生成"""
        # TODO: 実装
        pass
    
    def _create_weekly_prompt(self, days: int, user_request: str, context: UserContext) -> str:
        """週間献立用プロンプト生成"""
        # 既存のロジックを移植
        pass
    
    async def _call_claude_api(self, prompt: str) -> str:
        """Claude API呼び出し（一時的実装）"""
        # 既存のロジックを移植
        pass
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """JSONレスポンス解析（一時的実装）"""
        # 既存のロジックを移植
        pass
```

### 1.5 StrandsAgent実装

```python
# src/flavia/core/strands_agent.py
from .agents.context_agent import ContextAgent
from .agents.recipe_agent import RecipeAgent
from .models import UserRequest, UserContext, WeeklyPlan
from typing import Dict, Any
import asyncio

class StrandsAgent:
    """複数の専門エージェントを統合するコーディネーター"""
    
    def __init__(self):
        self.context_agent = ContextAgent()
        self.recipe_agent = RecipeAgent()
    
    async def generate_weekly_dinner_plan(
        self, 
        days: int, 
        user_request: str = "", 
        debug_callback=None
    ) -> Dict[str, Any]:
        """週間夕食献立生成（メインエントリーポイント）"""
        
        try:
            # リクエストオブジェクト作成
            request = UserRequest(
                text=user_request or "栄養バランスの良い夕食",
                days=days,
                request_id=f"req_{int(time.time())}"
            )
            
            if debug_callback:
                debug_callback(f"🎯 リクエスト処理開始: {days}日分")
            
            # 1. コンテキスト生成
            if debug_callback:
                debug_callback("📋 ユーザーコンテキスト作成中...")
            
            context_response = await self.context_agent.execute(request)
            if not context_response.success:
                raise Exception(f"コンテキスト生成エラー: {context_response.error}")
            
            context = UserContext(**context_response.data["context"])
            
            # 2. レシピ生成
            if debug_callback:
                debug_callback("🍳 献立生成中...")
            
            recipe_response = await self.recipe_agent.execute(request, context)
            if not recipe_response.success:
                raise Exception(f"レシピ生成エラー: {recipe_response.error}")
            
            weekly_plan = WeeklyPlan(**recipe_response.data["weekly_plan"])
            
            # 3. 買い物リスト生成（フェーズ2で実装）
            # shopping_list = await self.shopping_agent.execute(weekly_plan.dinners)
            
            if debug_callback:
                debug_callback("✅ 献立生成完了！")
            
            return {
                "success": True,
                "plan_days": weekly_plan.plan_days,
                "dinners": [dinner.dict() for dinner in weekly_plan.dinners],
                "shopping_list": {"items": [], "total_items": 0, "notes": "フェーズ2で実装予定"},  # 仮実装
                "generation_time": weekly_plan.generation_time.isoformat(),
                "request": weekly_plan.request
            }
        
        except Exception as e:
            if debug_callback:
                debug_callback(f"❌ エラー: {str(e)}")
            raise Exception(f"週間献立生成エラー: {str(e)}")
```

## フェーズ1実装手順

### Step 1: 依存関係追加
```bash
# pyproject.toml に追加
pip install pydantic
```

### Step 2: ディレクトリ構造作成
```
src/flavia/core/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── context_agent.py
│   └── recipe_agent.py
├── models.py
└── strands_agent.py
```

### Step 3: 実装順序
1. `models.py` - データモデル定義
2. `base_agent.py` - 基底クラス
3. `context_agent.py` - コンテキストエージェント
4. `recipe_agent.py` - レシピエージェント（既存ロジック移植）
5. `strands_agent.py` - 統合エージェント
6. UI側の接続変更

### Step 4: テスト戦略
1. 各Agentの単体テスト
2. StrandsAgentの統合テスト
3. UI経由のE2Eテスト
4. 既存機能との互換性確認

### Step 5: 移行戦略
1. 新しいStrandsAgentを作成
2. UI側で既存FlaviaAgentと新StrandsAgentの切り替え可能にする
3. 動作確認後、既存コードを段階的に削除

## フェーズ2以降の予定

### フェーズ2: 残りエージェント実装
- ShoppingAgent
- PromptAgent  
- ResponseAgent

### フェーズ3: 最適化
- 並列処理の実装
- エラー処理の強化
- パフォーマンス最適化

## 完了条件

### フェーズ1完了条件
- [ ] 全データモデルがPydanticで定義済み
- [ ] ContextAgentが正常動作
- [ ] RecipeAgentが既存機能と同等
- [ ] StrandsAgentで統合処理が動作
- [ ] UI側で新アーキテクチャが使用可能
- [ ] 既存テストがすべてパス

これで実装を開始しますか？