"""スマートコンテキストビルダー - リクエスト適応型RAGシステム"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import re
import json
from pathlib import Path

from .preference_parser import PreferenceParser, PreferenceData
from .learning_system import LearningSystem
from ..utils.file_utils import safe_read_text_file, get_personal_data_path
from ..monitoring import cache_result


class RequestType(Enum):
    """リクエストタイプの分類"""
    RECIPE_SUGGESTION = "recipe_suggestion"
    MEAL_PLANNING = "meal_planning"
    SHOPPING_LIST = "shopping_list"
    INGREDIENT_SUBSTITUTION = "ingredient_substitution"
    COOKING_HELP = "cooking_help"
    DIETARY_ADVICE = "dietary_advice"


class ContextPriority(Enum):
    """コンテキスト情報の優先度"""
    CRITICAL = "critical"      # 絶対に含める必要がある情報
    HIGH = "high"             # 高い関連性を持つ情報
    MEDIUM = "medium"         # 参考程度の情報
    LOW = "low"              # 必要に応じて含める情報


class SmartContextBuilder:
    """リクエストに応じて最適なコンテキストを構築するクラス"""
    
    def __init__(self):
        self.preference_parser = PreferenceParser()
        self.learning_system = LearningSystem()
        self.data_path = get_personal_data_path()
        
        # トークン制限の設定
        self.MAX_CONTEXT_TOKENS = 8000  # Claude の context window を考慮
        self.CRITICAL_INFO_TOKENS = 2000  # 絶対に含める情報用
        
    @cache_result(ttl=300)  # 5分キャッシュ
    def build_smart_context(
        self, 
        user_request: str, 
        context_type: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        リクエストに最適化されたコンテキストを構築
        
        Args:
            user_request: ユーザーのリクエスト
            context_type: コンテキストタイプの強制指定
            max_tokens: 最大トークン数の指定
            
        Returns:
            構築されたコンテキスト情報
        """
        max_tokens = max_tokens or self.MAX_CONTEXT_TOKENS
        
        # 1. リクエスト分析
        request_analysis = self._analyze_request(user_request)
        request_type = RequestType(context_type) if context_type else request_analysis["type"]
        
        # 2. 学習データの統合
        updated_preferences = self.learning_system.get_updated_preferences()
        
        # 3. コンテキスト要素の収集と優先度付け
        context_elements = self._collect_context_elements(
            request_analysis, request_type, updated_preferences
        )
        
        # 4. 優先度に基づくコンテキスト選択
        selected_context = self._select_optimal_context(
            context_elements, max_tokens, request_analysis
        )
        
        # 5. 最終コンテキストの構築
        final_context = self._build_final_context(
            selected_context, request_type, request_analysis
        )
        
        return {
            "context": final_context,
            "request_analysis": request_analysis,
            "selected_elements": [elem["name"] for elem in selected_context],
            "total_estimated_tokens": sum(elem["estimated_tokens"] for elem in selected_context),
            "optimization_summary": self._create_optimization_summary(context_elements, selected_context)
        }
    
    def _analyze_request(self, user_request: str) -> Dict[str, Any]:
        """ユーザーリクエストを分析して必要な情報を特定"""
        request_lower = user_request.lower()
        
        # リクエストタイプの判定
        request_type = self._determine_request_type(request_lower)
        
        # キーワード抽出
        keywords = self._extract_keywords(user_request)
        
        # 制約の特定
        constraints = self._identify_constraints(request_lower)
        
        # 時間・季節性の特定
        temporal_context = self._identify_temporal_context(request_lower)
        
        return {
            "type": request_type,
            "keywords": keywords,
            "constraints": constraints,
            "temporal": temporal_context,
            "complexity": self._assess_complexity(request_lower),
            "urgency": self._assess_urgency(request_lower)
        }
    
    def _determine_request_type(self, request_lower: str) -> RequestType:
        """リクエストタイプを判定"""
        type_patterns = {
            RequestType.RECIPE_SUGGESTION: [
                "レシピ", "作り方", "料理", "メニュー", "何作", "おすすめ"
            ],
            RequestType.MEAL_PLANNING: [
                "献立", "メニュー", "日分", "週間", "食事計画", "プラン"
            ],
            RequestType.SHOPPING_LIST: [
                "買い物", "購入", "必要な", "材料", "食材", "リスト"
            ],
            RequestType.INGREDIENT_SUBSTITUTION: [
                "代用", "替え", "ない場合", "使えない", "別の"
            ],
            RequestType.COOKING_HELP: [
                "作り方", "手順", "コツ", "失敗", "うまく", "方法"
            ],
            RequestType.DIETARY_ADVICE: [
                "健康", "栄養", "ダイエット", "体調", "カロリー"
            ]
        }
        
        for request_type, patterns in type_patterns.items():
            if any(pattern in request_lower for pattern in patterns):
                return request_type
        
        return RequestType.RECIPE_SUGGESTION  # デフォルト
    
    def _extract_keywords(self, user_request: str) -> List[str]:
        """重要なキーワードを抽出"""
        # 食材名の抽出
        ingredient_patterns = [
            r'[豚牛鶏]肉', r'魚[類]?', r'野菜', r'[キャベツ大根人参玉ねぎじゃがいも]',
            r'豆腐', r'卵', r'米', r'パン', r'麺'
        ]
        
        # 料理ジャンルの抽出
        cuisine_patterns = [
            r'和食', r'洋食', r'中華', r'イタリアン', r'フレンチ'
        ]
        
        # 調理方法の抽出
        cooking_patterns = [
            r'煮る', r'焼く', r'炒める', r'揚げる', r'蒸す', r'茹でる'
        ]
        
        keywords = []
        all_patterns = ingredient_patterns + cuisine_patterns + cooking_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, user_request)
            keywords.extend(matches)
        
        return list(set(keywords))
    
    def _identify_constraints(self, request_lower: str) -> Dict[str, List[str]]:
        """制約を特定"""
        constraints = {
            "time_limit": [],
            "equipment_limit": [],
            "dietary_restriction": [],
            "budget_constraint": []
        }
        
        # 時間制約
        if any(word in request_lower for word in ["短時間", "簡単", "15分", "30分"]):
            constraints["time_limit"].append("短時間調理")
        
        # 器具制約
        if any(word in request_lower for word in ["レンジ", "フライパン", "鍋"]):
            constraints["equipment_limit"].append("指定器具のみ")
        
        # 食事制約
        if any(word in request_lower for word in ["ヘルシー", "低カロリー", "健康"]):
            constraints["dietary_restriction"].append("健康志向")
        
        return constraints
    
    def _identify_temporal_context(self, request_lower: str) -> Dict[str, Any]:
        """時間・季節性コンテキストを特定"""
        current_season = self._get_current_season()
        current_time = datetime.now().hour
        
        temporal = {
            "season": current_season,
            "time_of_day": self._get_time_period(current_time),
            "is_weekend": datetime.now().weekday() >= 5,
            "seasonal_preference": "spring" in request_lower or "summer" in request_lower or 
                                 "autumn" in request_lower or "winter" in request_lower
        }
        
        return temporal
    
    def _collect_context_elements(
        self, 
        request_analysis: Dict[str, Any], 
        request_type: RequestType,
        preferences: PreferenceData
    ) -> List[Dict[str, Any]]:
        """コンテキスト要素を収集し優先度を付与"""
        elements = []
        
        # 絶対制約（CRITICAL）
        elements.append({
            "name": "absolute_constraints",
            "content": self._build_absolute_constraints(preferences),
            "priority": ContextPriority.CRITICAL,
            "estimated_tokens": 200
        })
        
        # リクエスト特化情報（HIGH）
        if request_type == RequestType.RECIPE_SUGGESTION:
            elements.extend(self._get_recipe_context_elements(request_analysis, preferences))
        elif request_type == RequestType.MEAL_PLANNING:
            elements.extend(self._get_meal_planning_context_elements(request_analysis, preferences))
        elif request_type == RequestType.SHOPPING_LIST:
            elements.extend(self._get_shopping_context_elements(request_analysis, preferences))
        
        # 学習データ（HIGH if recent, MEDIUM if older）
        learning_element = self._get_learning_context_element(request_analysis)
        if learning_element:
            elements.append(learning_element)
        
        # 基本プロフィール（MEDIUM）
        elements.append({
            "name": "basic_profile",
            "content": self._build_basic_profile(preferences.profile),
            "priority": ContextPriority.MEDIUM,
            "estimated_tokens": 150
        })
        
        # 季節・時間情報（LOW to MEDIUM）
        if request_analysis["temporal"]["seasonal_preference"]:
            elements.append({
                "name": "seasonal_context",
                "content": self._build_seasonal_context(request_analysis["temporal"]),
                "priority": ContextPriority.MEDIUM,
                "estimated_tokens": 100
            })
        
        return elements
    
    def _get_recipe_context_elements(
        self, 
        request_analysis: Dict[str, Any], 
        preferences: PreferenceData
    ) -> List[Dict[str, Any]]:
        """レシピ提案用のコンテキスト要素"""
        elements = []
        
        # 料理嗜好（HIGH）
        elements.append({
            "name": "cuisine_preferences",
            "content": self._build_cuisine_preferences(preferences),
            "priority": ContextPriority.HIGH,
            "estimated_tokens": 300
        })
        
        # 調理器具・スキル（HIGH）
        elements.append({
            "name": "cooking_capabilities",
            "content": self._build_cooking_capabilities(preferences),
            "priority": ContextPriority.HIGH,
            "estimated_tokens": 200
        })
        
        # 健康目標（MEDIUM）
        if preferences.health_goals:
            elements.append({
                "name": "health_considerations",
                "content": self._build_health_context(preferences),
                "priority": ContextPriority.MEDIUM,
                "estimated_tokens": 150
            })
        
        return elements
    
    def _get_meal_planning_context_elements(
        self, 
        request_analysis: Dict[str, Any], 
        preferences: PreferenceData
    ) -> List[Dict[str, Any]]:
        """献立計画用のコンテキスト要素"""
        elements = []
        
        # 食事パターン（HIGH）
        elements.append({
            "name": "meal_patterns",
            "content": self._build_meal_patterns(preferences),
            "priority": ContextPriority.HIGH,
            "estimated_tokens": 250
        })
        
        # 栄養バランス考慮（HIGH）
        elements.append({
            "name": "nutritional_balance",
            "content": self._build_nutritional_context(preferences),
            "priority": ContextPriority.HIGH,
            "estimated_tokens": 200
        })
        
        return elements
    
    def _get_shopping_context_elements(
        self, 
        request_analysis: Dict[str, Any], 
        preferences: PreferenceData
    ) -> List[Dict[str, Any]]:
        """買い物リスト用のコンテキスト要素"""
        elements = []
        
        # 購入パターン（HIGH）
        elements.append({
            "name": "shopping_patterns",
            "content": self._build_shopping_patterns(preferences),
            "priority": ContextPriority.HIGH,
            "estimated_tokens": 200
        })
        
        return elements
    
    def _select_optimal_context(
        self, 
        context_elements: List[Dict[str, Any]], 
        max_tokens: int,
        request_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """優先度に基づいて最適なコンテキストを選択"""
        # 優先度順にソート
        priority_order = [
            ContextPriority.CRITICAL,
            ContextPriority.HIGH,
            ContextPriority.MEDIUM,
            ContextPriority.LOW
        ]
        
        sorted_elements = []
        for priority in priority_order:
            priority_elements = [e for e in context_elements if e["priority"] == priority]
            # 同じ優先度内では推定トークン数の少ない順
            priority_elements.sort(key=lambda x: x["estimated_tokens"])
            sorted_elements.extend(priority_elements)
        
        # トークン制限内で選択
        selected = []
        total_tokens = 0
        
        for element in sorted_elements:
            if total_tokens + element["estimated_tokens"] <= max_tokens:
                selected.append(element)
                total_tokens += element["estimated_tokens"]
            elif element["priority"] == ContextPriority.CRITICAL:
                # CRITICALは必ず含める（他を削ってでも）
                selected = [e for e in selected if e["priority"] == ContextPriority.CRITICAL]
                selected.append(element)
                total_tokens = sum(e["estimated_tokens"] for e in selected)
                break
        
        return selected
    
    def _build_final_context(
        self, 
        selected_elements: List[Dict[str, Any]], 
        request_type: RequestType,
        request_analysis: Dict[str, Any]
    ) -> str:
        """最終的なコンテキストを構築"""
        sections = []
        
        # ヘッダー
        sections.append(f"# {request_type.value.replace('_', ' ').title()} Context")
        sections.append("")
        
        # 各要素を統合
        for element in selected_elements:
            if element["content"].strip():
                sections.append(element["content"])
                sections.append("")
        
        # リクエスト分析結果（簡潔に）
        if request_analysis["constraints"]:
            sections.append("## 特定された制約")
            for constraint_type, constraints in request_analysis["constraints"].items():
                if constraints:
                    sections.append(f"- {constraint_type}: {', '.join(constraints)}")
            sections.append("")
        
        return "\n".join(sections)
    
    # ヘルパーメソッド
    def _build_absolute_constraints(self, preferences: PreferenceData) -> str:
        """絶対制約の構築"""
        constraints = ["## 絶対制約（必須遵守）"]
        
        if preferences.disliked_foods:
            constraints.append(f"### 使用禁止食材: {', '.join(preferences.disliked_foods)}")
        
        if preferences.cooking_equipment.get('not_available'):
            constraints.append(f"### 使用不可器具: {', '.join(preferences.cooking_equipment['not_available'])}")
        
        if preferences.dietary_restrictions:
            constraints.append(f"### 食事制約: {', '.join(preferences.dietary_restrictions)}")
        
        return "\n".join(constraints)
    
    def _build_cuisine_preferences(self, preferences: PreferenceData) -> str:
        """料理嗜好の構築"""
        sections = ["## 料理嗜好"]
        
        # 評価順でソート
        sorted_cuisines = sorted(preferences.cuisine_preferences, 
                               key=lambda x: x.rating, reverse=True)
        
        sections.append("### 好みの料理（評価順）")
        for cuisine in sorted_cuisines[:5]:  # 上位5つ
            sections.append(f"- {cuisine.name}: {'★' * cuisine.rating}")
        
        return "\n".join(sections)
    
    def _build_cooking_capabilities(self, preferences: PreferenceData) -> str:
        """調理能力の構築"""
        sections = ["## 調理環境・能力"]
        
        if preferences.cooking_equipment.get('available'):
            sections.append("### 利用可能器具")
            for equipment in preferences.cooking_equipment['available']:
                sections.append(f"- {equipment}")
        
        if preferences.cooking_skills:
            sections.append("### スキルレベル")
            for skill in preferences.cooking_skills:
                sections.append(f"- {skill.skill_name}: {'★' * skill.level}")
        
        return "\n".join(sections)
    
    def _get_current_season(self) -> str:
        """現在の季節を取得"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _get_time_period(self, hour: int) -> str:
        """時間帯を取得"""
        if 5 <= hour < 10:
            return "morning"
        elif 10 <= hour < 14:
            return "lunch"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "dinner"
        else:
            return "late_night"
    
    def _assess_complexity(self, request: str) -> str:
        """リクエストの複雑性を評価"""
        complex_keywords = ["複数", "組み合わせ", "バランス", "栄養", "計画"]
        simple_keywords = ["簡単", "シンプル", "手軽", "すぐ"]
        
        if any(word in request for word in complex_keywords):
            return "complex"
        elif any(word in request for word in simple_keywords):
            return "simple"
        else:
            return "medium"
    
    def _assess_urgency(self, request: str) -> str:
        """リクエストの緊急性を評価"""
        urgent_keywords = ["今すぐ", "急いで", "すぐに", "今日"]
        if any(word in request for word in urgent_keywords):
            return "urgent"
        else:
            return "normal"
    
    def _get_learning_context_element(self, request_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """学習データベースのコンテキスト要素を取得"""
        learning_summary = self.learning_system.get_learning_summary()
        
        if learning_summary["total_feedbacks"] == 0:
            return None
        
        # 最近の傾向分析
        trends = self.learning_system.analyze_preference_trends(days=14)
        
        content = ["## 学習済み嗜好情報"]
        
        if trends["recipe_ratings"]["rating_count"] > 0:
            avg_rating = trends["recipe_ratings"]["average_rating"]
            content.append(f"### 最近の評価傾向")
            content.append(f"- 平均評価: {avg_rating:.1f}/5.0")
            content.append(f"- 評価数: {trends['recipe_ratings']['rating_count']}件")
        
        if trends["recommendations"]:
            content.append("### 学習ベース推奨")
            for rec in trends["recommendations"]:
                content.append(f"- {rec}")
        
        priority = ContextPriority.HIGH if learning_summary["total_feedbacks"] > 5 else ContextPriority.MEDIUM
        
        return {
            "name": "learning_context",
            "content": "\n".join(content),
            "priority": priority,
            "estimated_tokens": 150
        }
    
    def _create_optimization_summary(
        self, 
        all_elements: List[Dict[str, Any]], 
        selected_elements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """最適化サマリーを作成"""
        total_available = len(all_elements)
        total_selected = len(selected_elements)
        
        excluded_by_priority = {}
        for element in all_elements:
            if element not in selected_elements:
                priority = element["priority"].value
                excluded_by_priority[priority] = excluded_by_priority.get(priority, 0) + 1
        
        return {
            "total_available_elements": total_available,
            "total_selected_elements": total_selected,
            "selection_ratio": total_selected / total_available if total_available > 0 else 0,
            "excluded_by_priority": excluded_by_priority,
            "optimization_successful": total_selected > 0
        }
    
    # 追加のヘルパーメソッド（簡潔版）
    def _build_basic_profile(self, profile) -> str:
        return f"## 基本情報\n- {profile.age}歳{profile.gender}性、{profile.family_structure}"
    
    def _build_health_context(self, preferences: PreferenceData) -> str:
        sections = ["## 健康目標"]
        for goal in preferences.health_goals[:3]:
            sections.append(f"- {goal}")
        return "\n".join(sections)
    
    def _build_seasonal_context(self, temporal: Dict[str, Any]) -> str:
        return f"## 季節・時間情報\n- 季節: {temporal['season']}\n- 時間帯: {temporal['time_of_day']}"
    
    def _build_meal_patterns(self, preferences: PreferenceData) -> str:
        return "## 食事パターン\n- 基本的な食事リズムと好み"
    
    def _build_nutritional_context(self, preferences: PreferenceData) -> str:
        return "## 栄養バランス\n- 健康目標に基づく栄養配慮"
    
    def _build_shopping_patterns(self, preferences: PreferenceData) -> str:
        return "## 購入傾向\n- よく購入する食材カテゴリ"