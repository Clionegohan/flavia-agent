"""個人化されたFlaviaエージェント - RAGシステム統合版"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import structlog

from .base import BaseAgent
from ...utils.error_handler import (
    async_safe_execute, 
    validate_input, 
    RetryManager,
    create_safe_fallback_response,
    error_manager
)
from ...monitoring import async_monitor_performance, cache_result
from ..cache_manager import cached, invalidate_cache
from ...rag.context_builder import ContextBuilder
from ...rag.preference_parser import PreferenceParser
from ...rag.web_sale_fetcher import WebSaleFetcher
from ...rag.learning_system import LearningSystem
from ...rag.smart_context_builder import SmartContextBuilder
from ..models.recipe import Recipe
from ..models.preferences import MealPreferences
from ...utils.logging import get_logger

# 環境変数読み込み
load_dotenv()


class PersonalAgent:
    """RAGベース個人化Flaviaエージェント
    
    あなた専用の食事パートナー。個人の嗜好、健康目標、調理環境、
    特売情報を全て理解した上で最適な献立を提案します。
    """
    
    def __init__(self):
        """個人化エージェントを初期化"""
        self.logger = get_logger(__name__)
        
        # Claude API設定
        import os
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            self.logger.warning("ANTHROPIC_API_KEY not found in environment")
        
        # RAGコンポーネント
        self.context_builder = ContextBuilder()
        self.smart_context_builder = SmartContextBuilder()
        self.preference_parser = PreferenceParser()
        self.sale_fetcher = WebSaleFetcher()
        
        # 学習システム
        self.learning_system = LearningSystem()
        
        # 個人データを読み込み
        self._load_personal_data()
        
        self.logger.info("Personal Flavia Agent initialized successfully")
    
    @cached(cache_type='preference', ttl=300)
    def _load_personal_data(self):
        """個人データを読み込んで解析（学習結果反映）"""
        try:
            # 学習結果を反映した最新の嗜好データを取得
            self.personal_data = self.learning_system.get_updated_preferences()
            
            self.logger.info(
                "Personal data loaded with learning integration",
                age=self.personal_data.profile.age,
                gender=self.personal_data.profile.gender,
                disliked_foods_count=len(self.personal_data.disliked_foods),
                cuisine_preferences_count=len(self.personal_data.cuisine_preferences),
                health_goals_count=len(self.personal_data.health_goals)
            )
            
        except Exception as e:
            self.logger.error("Failed to load personal data", error=str(e))
            raise Exception(f"個人データの読み込みに失敗: {e}")
    
    @async_monitor_performance(include_args=True)
    @async_safe_execute(fallback_value=None, log_error=True)
    @validate_input({
        'days': {'type': int, 'min_value': 1, 'max_value': 14},
        'user_request': {'type': str, 'max_length': 1000}
    })
    async def generate_weekly_dinner_plan(
        self,
        days: int = 7,
        include_sale_info: bool = True,
        sale_url: Optional[str] = None,
        user_request: str = ""
    ) -> Dict[str, Any]:
        """指定日数分の夕食メニュー + 詳細レシピ + 買い物リスト生成"""
        try:
            self.logger.info(
                "Starting weekly dinner plan generation",
                days=days,
                include_sale_info=include_sale_info
            )
            
            # 1. スマートコンテキストの構築
            smart_context_result = self.smart_context_builder.build_smart_context(
                user_request=user_request or f"{days}日分の夕食メニューと詳細レシピ、買い物リスト生成",
                context_type="meal_planning",
                max_tokens=6000
            )
            personal_context = smart_context_result["context"]
            
            # 2. 特売情報の取得
            sale_context = ""
            if include_sale_info and sale_url:
                sale_info = await self._fetch_sale_info(sale_url)
                if sale_info:
                    sale_context = self._build_sale_context(sale_info)
            
            # 3. 週間献立プロンプト作成
            weekly_prompt = self._create_weekly_dinner_prompt(
                days, personal_context, sale_context, user_request
            )
            
            # 4. AI週間献立生成
            dinner_plan = await self._generate_weekly_dinners(weekly_prompt, days)
            
            # 5. 買い物リスト生成
            shopping_list = self._generate_shopping_list(dinner_plan["dinners"])
            
            # 6. 結果構築
            result = {
                "success": True,
                "plan_days": days,
                "dinners": dinner_plan["dinners"],
                "shopping_list": shopping_list,
                "personal_considerations": self._get_personal_considerations(),
                "generation_time": datetime.now().isoformat(),
                "total_estimated_cost": sum(d.get("estimated_cost", 0) for d in dinner_plan["dinners"]),
                "request": user_request
            }
            
            if sale_context:
                result["sale_integration"] = "特売情報を活用しました"
            
            self.logger.info(
                "Weekly dinner plan generated successfully",
                days=days,
                total_cost=result["total_estimated_cost"]
            )
            
            return result
            
        except Exception as e:
            error_manager.record_error(
                "weekly_dinner_generation", 
                e, 
                {"days": days, "user_request": user_request}
            )
            
            # フォールバック応答を返す
            return create_safe_fallback_response("weekly_dinner")

    async def generate_personalized_meal_plan(
        self, 
        user_request: str = "今日の献立を考えて",
        include_sale_info: bool = False,
        sale_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """個人化された献立プランを生成
        
        Args:
            user_request: ユーザーからのリクエスト
            include_sale_info: 特売情報を含めるか
            sale_url: 特売情報のURL
            
        Returns:
            個人化された献立プランと詳細情報
        """
        
        self.logger.info(
            "Starting personalized meal plan generation",
            request=user_request,
            include_sales=include_sale_info
        )
        
        try:
            # 1. スマートコンテキストを構築
            smart_context_result = self.smart_context_builder.build_smart_context(
                user_request=user_request,
                context_type="recipe_suggestion",
                max_tokens=5000
            )
            personal_context = smart_context_result["context"]
            
            # 2. 特売情報の統合（オプション）
            sale_context = ""
            if include_sale_info and sale_url:
                sale_info = await self._fetch_sale_info(sale_url)
                if sale_info:
                    sale_context = self._build_sale_context(sale_info)
            
            # 3. 統合プロンプトの作成
            integrated_prompt = self._create_integrated_prompt(
                user_request, personal_context, sale_context
            )
            
            # 4. AI献立生成
            recipes = await self._generate_recipes_with_constraints(integrated_prompt)
            
            # 5. 個人制約の検証
            validated_recipes = self._validate_personal_constraints(recipes)
            
            # 6. 結果の構築
            result = {
                "success": True,
                "recipes": validated_recipes,
                "personal_considerations": self._get_personal_considerations(),
                "request": user_request,
                "generation_time": datetime.now().isoformat(),
                "constraints_applied": self._get_applied_constraints(),
                "recipe_count": len(validated_recipes)
            }
            
            if sale_context:
                result["sale_integration"] = "特売情報を活用しました"
            
            self.logger.info(
                "Personalized meal plan generated successfully",
                recipe_count=len(validated_recipes),
                has_sale_info=bool(sale_context)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Personalized meal plan generation failed",
                error=str(e),
                request=user_request
            )
            raise Exception(f"個人化献立生成エラー: {e}")
    
    async def _fetch_sale_info(self, sale_url: str) -> Optional[Any]:
        """特売情報を取得"""
        try:
            # 実際のWebFetchは外部で実行される想定
            # ここではキャッシュから読み込み
            cached_info = self.sale_fetcher.load_cached_sale_info()
            
            if cached_info:
                self.logger.info("Sale info loaded from cache", items=len(cached_info.items))
                return cached_info
            else:
                self.logger.warning("No cached sale info available")
                return None
                
        except Exception as e:
            self.logger.error("Failed to fetch sale info", error=str(e))
            return None
    
    def _build_sale_context(self, sale_info) -> str:
        """特売情報のコンテキストを構築"""
        user_context = self.context_builder.build_shopping_context()
        return self.sale_fetcher.create_recipe_prompt_with_sales(
            sale_info, "特売商品を活用した献立", user_context
        )
    
    def _create_integrated_prompt(
        self, 
        user_request: str, 
        personal_context: str, 
        sale_context: str = ""
    ) -> str:
        """統合プロンプトを作成"""
        
        prompt_parts = [
            "# あなた専用の献立提案",
            "",
            "## ユーザーリクエスト",
            user_request,
            "",
            "## 個人プロフィール・制約",
            personal_context,
        ]
        
        if sale_context:
            prompt_parts.extend([
                "",
                "## 特売情報",
                sale_context,
                "",
                "**重要**: 特売商品を積極的に活用しつつ、個人の制約を厳守してください。"
            ])
        
        prompt_parts.extend([
            "",
            "## 提案要件",
            "1. **絶対回避**: 苦手な食材は一切使用しない",
            "2. **設備考慮**: 使用可能な調理器具のみで作れるレシピ", 
            "3. **時間制限**: 指定された調理時間内で完成",
            "4. **健康目標**: 栄養面での配慮を反映",
            "5. **好み優先**: 高評価の料理ジャンルを重視",
            "",
            "個人に最適化された、実現可能で美味しい献立を提案してください。"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _generate_recipes_with_constraints(self, prompt: str) -> List[Recipe]:
        """制約を考慮したレシピ生成"""
        
        try:
            # Claude APIを直接呼び出し
            response = await self._call_claude_api(prompt)
            
            # 自然言語レスポンスをRecipeオブジェクトに変換
            recipes = self._parse_natural_language_response(response)
            
            self.logger.info(
                "Personal recipes generated successfully",
                recipe_count=len(recipes)
            )
            
            return recipes
            
        except Exception as e:
            self.logger.error("Failed to generate personal recipes", error=str(e))
            raise Exception(f"個人化レシピ生成失敗: {e}")
    
    def _build_meal_preferences(self) -> MealPreferences:
        """個人データからMealPreferencesを構築"""
        
        # 好みの料理ジャンルを抽出（評価4以上）
        preferred_cuisines = []
        for pref in self.personal_data.cuisine_preferences:
            if pref.rating >= 4:
                # 英語名に変換
                if pref.name == "和食":
                    preferred_cuisines.append("Japanese")
                elif pref.name == "中華":
                    preferred_cuisines.append("Asian")
                elif pref.name == "洋食":
                    preferred_cuisines.append("American")
                elif pref.name == "イタリアン":
                    preferred_cuisines.append("Italian")
        
        # 食事制限を変換
        dietary_restrictions = []
        for restriction in self.personal_data.dietary_restrictions:
            if "アレルギー" not in restriction and "なし" not in restriction:
                dietary_restrictions.append(restriction)
        
        # 調理時間を抽出（平日の制限）
        cooking_time = 30  # デフォルト
        if self.personal_data.profile.cooking_time_available.get('weekday'):
            time_str = self.personal_data.profile.cooking_time_available['weekday']
            if "30分" in time_str:
                cooking_time = 30
            elif "1時間" in time_str:
                cooking_time = 60
        
        return MealPreferences(
            budget=25.0,  # 適度な予算
            dietary_restrictions=dietary_restrictions,
            cuisine_preferences=preferred_cuisines,
            cooking_time=cooking_time,
            servings=1  # 一人暮らし
        )
    
    def _validate_personal_constraints(self, recipes: List[Recipe]) -> List[Recipe]:
        """個人制約に基づいてレシピを検証・フィルタリング"""
        
        validated_recipes = []
        
        for recipe in recipes:
            is_valid = True
            validation_notes = []
            
            # 苦手な食材チェック
            for disliked in self.personal_data.disliked_foods:
                disliked_clean = disliked.replace("(親子丼なら好き)", "").strip()
                
                # レシピ名と材料をチェック
                recipe_text = f"{recipe.name} {' '.join(recipe.ingredients)}".lower()
                if disliked_clean.lower() in recipe_text:
                    is_valid = False
                    validation_notes.append(f"苦手な食材「{disliked_clean}」を含む")
                    break
            
            # 調理器具チェック
            unavailable_equipment = self.personal_data.cooking_equipment.get('not_available', [])
            for equipment in unavailable_equipment:
                if equipment.lower() in " ".join(recipe.instructions).lower():
                    validation_notes.append(f"使用不可器具「{equipment}」が必要")
                    # 警告のみ、除外はしない（代替方法があるかもしれない）
            
            if is_valid:
                # バリデーション情報を追加
                if validation_notes:
                    recipe.notes = recipe.notes + f" 注意: {'; '.join(validation_notes)}" if hasattr(recipe, 'notes') else f"注意: {'; '.join(validation_notes)}"
                
                validated_recipes.append(recipe)
            
            else:
                self.logger.warning(
                    "Recipe rejected due to personal constraints",
                    recipe_name=recipe.name,
                    reasons=validation_notes
                )
        
        return validated_recipes
    
    def _get_personal_considerations(self) -> Dict[str, Any]:
        """個人配慮事項の要約"""
        return {
            "avoided_ingredients": self.personal_data.disliked_foods,
            "health_goals": self.personal_data.health_goals[:3],
            "equipment_constraints": self.personal_data.cooking_equipment.get('not_available', []),
            "preferred_cuisines": [p.name for p in self.personal_data.cuisine_preferences if p.rating >= 4],
            "cooking_time_limit": self.personal_data.profile.cooking_time_available.get('weekday', '30分')
        }
    
    def _parse_natural_language_response(self, response: str) -> List[Recipe]:
        """自然言語レスポンスをRecipeオブジェクトに変換"""
        
        from ..data.models import Recipe
        import re
        
        recipes = []
        
        # レシピの区切りを検出（# または ## で始まる行）
        recipe_sections = re.split(r'\n(?=#{1,2}\s)', response)
        
        for section in recipe_sections:
            if not section.strip():
                continue
                
            try:
                recipe = self._parse_single_recipe_section(section)
                if recipe:
                    recipes.append(recipe)
            except Exception as e:
                self.logger.warning(f"Failed to parse recipe section: {e}")
                continue
        
        # 最低1つのレシピを保証
        if not recipes:
            # フォールバック: シンプルなレシピを作成
            recipes.append(self._create_fallback_recipe(response))
        
        return recipes
    
    def _parse_single_recipe_section(self, section: str) -> Optional[Recipe]:
        """単一のレシピセクションを解析"""
        
        from ..data.models import Recipe
        import re
        
        lines = section.strip().split('\n')
        if not lines:
            return None
        
        # レシピ名の抽出（最初の見出し行から）
        name_line = lines[0]
        name = re.sub(r'^#{1,2}\s*', '', name_line).strip()
        if ':' in name:
            name = name.split(':')[1].strip()
        
        # 材料の抽出
        ingredients = []
        instructions = []
        cooking_time = 30  # デフォルト
        cost = 10.0  # デフォルト
        
        current_section = ""
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            # セクション判定
            if '材料' in line or 'ingredients' in line.lower():
                current_section = "ingredients"
                continue
            elif '作り方' in line or '手順' in line or 'instructions' in line.lower():
                current_section = "instructions"
                continue
            elif '調理時間' in line or 'time' in line.lower():
                # 時間の抽出
                time_match = re.search(r'(\d+)分', line)
                if time_match:
                    cooking_time = int(time_match.group(1))
                continue
            elif '価格' in line or 'cost' in line.lower() or '円' in line:
                # コストの抽出
                cost_match = re.search(r'(\d+)円', line)
                if cost_match:
                    cost = float(cost_match.group(1)) / 100  # ドル換算（仮）
                continue
            
            # 内容の抽出
            if current_section == "ingredients" and line.startswith('-'):
                ingredient = line[1:].strip()
                if ingredient:
                    ingredients.append(ingredient)
            elif current_section == "instructions":
                if line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith('-'):
                    instruction = re.sub(r'^\d+\.?\s*', '', line).strip()
                    instruction = re.sub(r'^-\s*', '', instruction).strip()
                    if instruction:
                        instructions.append(instruction)
        
        # レシピオブジェクトの作成
        if not ingredients:
            ingredients = ["材料情報が不完全です"]
        if not instructions:
            instructions = ["作り方情報が不完全です"]
        
        return Recipe(
            name=name or "パーソナライズドレシピ",
            ingredients=ingredients,
            instructions=instructions,
            prep_time=5,
            cook_time=cooking_time - 5,
            total_time=cooking_time,
            servings=1,
            estimated_cost=cost,
            cost_per_serving=cost,
            cuisine_type="Personal",
            difficulty="Easy"
        )
    
    def _create_fallback_recipe(self, response: str) -> Recipe:
        """フォールバックレシピを作成"""
        
        from ..data.models import Recipe
        
        # レスポンスから最初のレシピ名らしきものを抽出
        lines = response.split('\n')
        name = "個人化レシピ"
        
        for line in lines[:5]:  # 最初の5行をチェック
            if '肉' in line or '野菜' in line or '炒め' in line or '煮' in line:
                name = line.strip()[:20]  # 最初の20文字
                break
        
        return Recipe(
            name=name,
            ingredients=[
                "鶏もも肉 150g",
                "キャベツ 1/4個", 
                "もやし 1袋",
                "調味料（醤油、みりん等）"
            ],
            instructions=[
                "材料を食べやすい大きさに切る",
                "フライパンで肉を炒める",
                "野菜を加えて炒める",
                "調味料で味付けして完成"
            ],
            prep_time=10,
            cook_time=20,
            total_time=30,
            servings=1,
            estimated_cost=8.0,
            cost_per_serving=8.0,
            cuisine_type="Japanese",
            difficulty="Easy"
        )
    
    def _get_applied_constraints(self) -> List[str]:
        """適用された制約の一覧"""
        constraints = []
        
        if self.personal_data.disliked_foods:
            constraints.append(f"苦手食材回避: {len(self.personal_data.disliked_foods)}種類")
        
        if self.personal_data.cooking_equipment.get('not_available'):
            constraints.append(f"調理器具制限: {len(self.personal_data.cooking_equipment['not_available'])}種類")
        
        if self.personal_data.health_goals:
            constraints.append(f"健康目標: {len(self.personal_data.health_goals)}項目")
        
        return constraints
    
    def get_preference_summary(self) -> str:
        """嗜好データの要約を取得"""
        return self.preference_parser.get_preference_summary()
    
    async def suggest_recipes_for_mood(self, mood: str, context: str = "") -> Dict[str, Any]:
        """気分・状況に応じたレシピ提案"""
        
        mood_mapping = {
            "疲れた": "簡単で栄養豊富な料理",
            "元気": "新しい挑戦的な料理", 
            "忙しい": "15分以内の時短料理",
            "のんびり": "時間をかけて楽しむ料理",
            "健康的": "野菜たっぷりの料理",
            "がっつり": "ボリューム満点の料理"
        }
        
        request = mood_mapping.get(mood, f"{mood}な気分の時の料理")
        if context:
            request += f"（{context}）"
        
        return await self.generate_personalized_meal_plan(request)
    
    # ===============================
    # 学習・フィードバック機能
    # ===============================
    
    def rate_recipe(
        self, 
        recipe_name: str, 
        rating: int, 
        comments: str = "",
        recipe_context: Dict[str, Any] = None
    ) -> str:
        """レシピを評価してフィードバック学習
        
        Args:
            recipe_name: レシピ名
            rating: 1-5の評価（5が最高）
            comments: コメント（オプション）
            recipe_context: レシピ生成時のコンテキスト
            
        Returns:
            フィードバックID
        """
        
        self.logger.info(
            "Recording recipe rating",
            recipe_name=recipe_name,
            rating=rating
        )
        
        # 学習システムにフィードバックを記録
        feedback_id = self.learning_system.record_recipe_feedback(
            recipe_name=recipe_name,
            rating=rating,
            comments=comments,
            recipe_context=recipe_context
        )
        
        # 個人データの再読み込み（学習結果反映）
        self._load_personal_data()
        
        return feedback_id
    
    def update_ingredient_preference(
        self, 
        ingredient: str, 
        new_preference: str, 
        reason: str = ""
    ) -> str:
        """食材の好みを更新
        
        Args:
            ingredient: 食材名
            new_preference: "like", "dislike", "neutral"
            reason: 変更理由（オプション）
            
        Returns:
            フィードバックID
        """
        
        self.logger.info(
            "Updating ingredient preference",
            ingredient=ingredient,
            new_preference=new_preference
        )
        
        # 学習システムに嗜好変化を記録
        feedback_id = self.learning_system.record_ingredient_preference_change(
            ingredient=ingredient,
            new_preference=new_preference,
            reason=reason
        )
        
        # キャッシュ無効化（学習結果反映のため）
        invalidate_cache('preference')
        self._load_personal_data()
        
        return feedback_id
    
    def analyze_my_preferences(self, days: int = 30) -> Dict[str, Any]:
        """個人の嗜好トレンドを分析
        
        Args:
            days: 分析期間（日数）
            
        Returns:
            嗜好分析結果
        """
        
        self.logger.info(
            "Analyzing preference trends",
            analysis_period_days=days
        )
        
        # 学習システムでトレンド分析
        analysis = self.learning_system.analyze_preference_trends(days)
        
        # 現在の嗜好データと組み合わせ
        enhanced_analysis = {
            **analysis,
            "current_profile": {
                "age": self.personal_data.profile.age,
                "location": self.personal_data.profile.location,
                "disliked_foods": self.personal_data.disliked_foods,
                "top_cuisines": [
                    p.name for p in self.personal_data.cuisine_preferences 
                    if p.rating >= 4
                ][:3]
            },
            "learning_summary": self.learning_system.get_learning_summary()
        }
        
        return enhanced_analysis
    
    def record_interaction(
        self, 
        interaction_type: str, 
        details: Dict[str, Any]
    ) -> str:
        """ユーザーとのインタラクションを記録
        
        Args:
            interaction_type: インタラクション種類
            details: 詳細情報
            
        Returns:
            インタラクションID
        """
        
        self.logger.info(
            "Recording user interaction",
            interaction_type=interaction_type
        )
        
        return self.learning_system.record_user_interaction(
            interaction_type=interaction_type,
            details=details
        )
    
    async def get_personalized_recommendations(self) -> Dict[str, Any]:
        """個人化された推奨事項を取得
        
        Returns:
            学習ベースの推奨事項
        """
        
        # 嗜好分析を実行
        analysis = self.analyze_my_preferences(days=30)
        
        # 推奨レシピを生成
        recommendations_request = "学習結果に基づいて、私にぴったりの新しいレシピを提案して"
        
        recommended_recipes = await self.generate_personalized_meal_plan(
            user_request=recommendations_request
        )
        
        return {
            "preference_analysis": analysis,
            "recommended_recipes": recommended_recipes,
            "learning_insights": analysis["recommendations"],
            "next_steps": [
                "新しいレシピを試して評価をつける",
                "嗜好の変化があれば更新する",
                "定期的に分析結果を確認する"
            ]
        }
    
    def get_learning_dashboard(self) -> Dict[str, Any]:
        """学習システムのダッシュボード情報を取得
        
        Returns:
            学習状況のサマリー
        """
        
        summary = self.learning_system.get_learning_summary()
        recent_analysis = self.analyze_my_preferences(days=7)
        
        dashboard = {
            "学習状況": {
                "総フィードバック数": summary["total_feedbacks"],
                "学習イベント数": summary["total_events"],
                "適応的嗜好項目数": summary["adaptive_preferences_count"],
                "最終フィードバック日時": summary["last_feedback"]
            },
            "今週の傾向": {
                "平均レシピ評価": recent_analysis["recipe_ratings"]["average_rating"],
                "評価済みレシピ数": recent_analysis["recipe_ratings"]["rating_count"],
                "嗜好安定性": recent_analysis["preference_stability"]
            },
            "推奨アクション": recent_analysis["recommendations"],
            "システム状態": summary["system_status"]
        }
        
        self.logger.info(
            "Learning dashboard generated",
            total_feedbacks=summary["total_feedbacks"],
            recent_ratings=recent_analysis["recipe_ratings"]["rating_count"]
        )
        
        return dashboard
    
    def _create_weekly_dinner_prompt(
        self, 
        days: int, 
        personal_context: str, 
        sale_context: str, 
        user_request: str
    ) -> str:
        """週間夕食献立生成用プロンプトを作成"""
        
        base_prompt = f"""
あなたは学習型AI料理パートナーFlaviaです。
{days}日分の夕食メニューと詳細レシピ、統合買い物リストを生成してください。

【個人情報・嗜好】
{personal_context}

【特売情報】
{sale_context if sale_context else "特売情報は考慮しません"}

【ユーザーリクエスト】
{user_request if user_request else "栄養バランスが良く、美味しい夕食を考えて"}

【出力形式】
以下のJSON形式で出力してください：

{{
  "dinners": [
    {{
      "day": 1,
      "date": "2025-06-08",
      "main_dish": "料理名",
      "description": "料理の説明",
      "ingredients": ["材料1", "材料2", "材料3"],
      "detailed_recipe": {{
        "prep_time": 15,
        "cook_time": 30,
        "servings": 2,
        "instructions": [
          "手順1",
          "手順2", 
          "手順3"
        ]
      }},
      "estimated_cost": 12.50,
      "nutrition_info": "カロリー・栄養情報",
      "cooking_difficulty": "簡単・普通・難しい"
    }}
  ]
}}

要件：
- {days}日分すべて異なる料理
- 栄養バランスを考慮
- 個人の嗜好・制約を反映
- 実用的で現実的なレシピ
- 買い物しやすい材料使用
"""
        return base_prompt
    
    async def _generate_weekly_dinners(self, prompt: str, days: int) -> Dict[str, Any]:
        """AI を使って週間夕食プランを生成"""
        try:
            response = await self._call_claude_api(prompt)
            
            # JSON解析を試行
            try:
                import json
                dinner_data = json.loads(response)
                return dinner_data
            except json.JSONDecodeError:
                # JSONパースに失敗した場合のフォールバック
                return self._create_fallback_dinner_plan(days)
                
        except Exception as e:
            self.logger.error(f"Weekly dinner generation failed: {e}")
            return self._create_fallback_dinner_plan(days)
    
    def _create_fallback_dinner_plan(self, days: int) -> Dict[str, Any]:
        """フォールバック用のシンプル夕食プラン"""
        from datetime import datetime, timedelta
        
        fallback_dinners = [
            "鶏の照り焼き丼", "鮭のムニエル", "豚の生姜焼き", "オムライス",
            "カレーライス", "ハンバーグ", "麻婆豆腐"
        ]
        
        dinners = []
        start_date = datetime.now()
        
        for i in range(days):
            dinner_name = fallback_dinners[i % len(fallback_dinners)]
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            
            dinners.append({
                "day": i + 1,
                "date": date,
                "main_dish": dinner_name,
                "description": f"美味しい{dinner_name}です",
                "ingredients": ["メイン食材", "調味料", "野菜"],
                "detailed_recipe": {
                    "prep_time": 15,
                    "cook_time": 25,
                    "servings": 2,
                    "instructions": [
                        "材料を準備する",
                        "調理する",
                        "盛り付けて完成"
                    ]
                },
                "estimated_cost": 8.0 + (i * 1.5),
                "nutrition_info": "約500kcal、タンパク質・野菜バランス良し",
                "cooking_difficulty": "普通"
            })
        
        return {"dinners": dinners}
    
    def _generate_shopping_list(self, dinners: list) -> Dict[str, Any]:
        """夕食メニューから統合買い物リストを生成"""
        
        # 材料を分類・集計
        ingredients_by_category = {
            "肉・魚類": [],
            "野菜・果物": [],
            "調味料・スパイス": [],
            "米・麺・パン": [],
            "乳製品・卵": [],
            "その他": []
        }
        
        ingredient_counts = {}
        total_cost = 0
        
        # 各夕食から材料を集計
        for dinner in dinners:
            total_cost += dinner.get("estimated_cost", 0)
            for ingredient in dinner.get("ingredients", []):
                if ingredient in ingredient_counts:
                    ingredient_counts[ingredient] += 1
                else:
                    ingredient_counts[ingredient] = 1
        
        # 材料をカテゴリ分け（シンプルな分類）
        for ingredient, count in ingredient_counts.items():
            ingredient_with_count = f"{ingredient} ×{count}" if count > 1 else ingredient
            
            # カテゴリ分類（キーワードベース）
            if any(word in ingredient.lower() for word in ["鶏", "豚", "牛", "魚", "肉"]):
                ingredients_by_category["肉・魚類"].append(ingredient_with_count)
            elif any(word in ingredient.lower() for word in ["野菜", "キャベツ", "人参", "玉ねぎ", "トマト"]):
                ingredients_by_category["野菜・果物"].append(ingredient_with_count)
            elif any(word in ingredient.lower() for word in ["醤油", "味噌", "塩", "砂糖", "油"]):
                ingredients_by_category["調味料・スパイス"].append(ingredient_with_count)
            elif any(word in ingredient.lower() for word in ["米", "麺", "パン", "パスタ"]):
                ingredients_by_category["米・麺・パン"].append(ingredient_with_count)
            elif any(word in ingredient.lower() for word in ["牛乳", "卵", "チーズ", "バター"]):
                ingredients_by_category["乳製品・卵"].append(ingredient_with_count)
            else:
                ingredients_by_category["その他"].append(ingredient_with_count)
        
        return {
            "ingredients_by_category": ingredients_by_category,
            "total_estimated_cost": total_cost,
            "shopping_notes": [
                "新鮮な食材を選んでください",
                "特売商品があれば代替を検討",
                "冷凍・保存の利く食材は多めに購入OK"
            ],
            "estimated_shopping_time": "30-45分",
            "total_unique_ingredients": len(ingredient_counts)
        }
    
    @async_monitor_performance()
    @RetryManager.async_retry_on_failure(max_attempts=3, delay=1.0)
    async def _call_claude_api(self, prompt: str) -> str:
        """Claude APIを呼び出し"""
        if not self.api_key:
            # フォールバック応答
            return self._create_fallback_response(prompt)
        
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
                system="あなたは日本の家庭料理に詳しいAI料理パートナーFlaviaです。ユーザーの個人的な嗜好、制約、健康目標を理解して、実用的で美味しいレシピや献立を提案します。",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            self.logger.info(
                "Claude API call successful",
                prompt_length=len(prompt),
                response_length=len(response_text)
            )
            
            return response_text
            
        except Exception as e:
            error_manager.record_error(
                "claude_api_call", 
                e, 
                {"prompt_length": len(prompt)}
            )
            self.logger.error(f"Claude API call failed: {e}")
            return self._create_fallback_response(prompt)
    
    def _create_fallback_response(self, prompt: str) -> str:
        """APIエラー時のフォールバック応答"""
        if "週間" in prompt or "日分" in prompt:
            return '''
{
  "dinners": [
    {
      "day": 1,
      "date": "2025-06-08",
      "main_dish": "鶏の照り焼き丼",
      "description": "甘辛い照り焼きソースが美味しい定番料理",
      "ingredients": ["鶏もも肉 200g", "米 1合", "醤油 大さじ2", "みりん 大さじ2", "砂糖 小さじ1"],
      "detailed_recipe": {
        "prep_time": 10,
        "cook_time": 20,
        "servings": 1,
        "instructions": [
          "鶏肉を一口大に切る",
          "フライパンで鶏肉を焼く", 
          "調味料を加えて照り焼きにする",
          "ご飯の上に盛り付ける"
        ]
      },
      "estimated_cost": 8.50,
      "nutrition_info": "約550kcal、タンパク質25g",
      "cooking_difficulty": "簡単"
    }
  ]
}
'''
        else:
            return """
## 鶏の照り焼き丼

### 材料
- 鶏もも肉 200g
- 米 1合
- 醤油 大さじ2
- みりん 大さじ2
- 砂糖 小さじ1

### 作り方
1. 鶏肉を一口大に切る
2. フライパンで鶏肉を焼く
3. 調味料を加えて照り焼きにする
4. ご飯の上に盛り付ける

調理時間: 30分
費用: 約8.50ドル
"""