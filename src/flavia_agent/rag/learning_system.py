"""個人化学習システム - ユーザーの嗜好変化を学習・更新"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from ..utils.file_utils import get_personal_data_path
from .preference_parser import PreferenceParser, PreferenceData


class FeedbackType(Enum):
    """フィードバックの種類"""
    RECIPE_RATING = "recipe_rating"          # レシピ評価
    INGREDIENT_PREFERENCE = "ingredient"     # 食材好み変化
    CUISINE_PREFERENCE = "cuisine"           # 料理ジャンル好み変化
    DIFFICULTY_PREFERENCE = "difficulty"     # 難易度好み
    TIME_PREFERENCE = "cooking_time"         # 調理時間好み
    COST_PREFERENCE = "budget"               # 予算好み
    HEALTH_GOAL_UPDATE = "health_goal"       # 健康目標更新


@dataclass
class UserFeedback:
    """ユーザーフィードバック記録"""
    feedback_id: str
    timestamp: str
    feedback_type: FeedbackType
    content: Dict[str, Any]
    context: Dict[str, Any]  # リクエスト時の状況
    confidence: float = 1.0  # フィードバックの確信度


@dataclass
class LearningEvent:
    """学習イベント記録"""
    event_id: str
    timestamp: str
    event_type: str
    user_action: str
    recipe_context: Dict[str, Any]
    feedback_data: Optional[Dict[str, Any]]
    learning_outcome: str


@dataclass
class AdaptivePreference:
    """適応的嗜好データ"""
    item_name: str
    current_score: float  # -1.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    last_updated: str
    update_count: int
    trend: str  # "increasing", "decreasing", "stable"


class LearningSystem:
    """個人化学習システム"""
    
    def __init__(self):
        """学習システム初期化"""
        self.logger = structlog.get_logger(__name__)
        self.data_path = get_personal_data_path()
        self.learning_data_path = self.data_path / "learning"
        self.learning_data_path.mkdir(exist_ok=True)
        
        # 学習データファイルパス
        self.feedback_file = self.learning_data_path / "user_feedback.json"
        self.learning_events_file = self.learning_data_path / "learning_events.json"
        self.adaptive_preferences_file = self.learning_data_path / "adaptive_preferences.json"
        self.preference_history_file = self.learning_data_path / "preference_history.json"
        
        # 嗜好パーサー
        self.preference_parser = PreferenceParser()
        
        # 学習データ初期化
        self._initialize_learning_data()
        
        self.logger.info("Learning system initialized")
    
    def _initialize_learning_data(self):
        """学習データファイルを初期化"""
        if not self.feedback_file.exists():
            self._save_json(self.feedback_file, [])
        
        if not self.learning_events_file.exists():
            self._save_json(self.learning_events_file, [])
        
        if not self.adaptive_preferences_file.exists():
            self._save_json(self.adaptive_preferences_file, {})
        
        if not self.preference_history_file.exists():
            self._save_json(self.preference_history_file, {})
    
    def record_recipe_feedback(
        self, 
        recipe_name: str, 
        rating: int, 
        comments: str = "",
        recipe_context: Dict[str, Any] = None
    ) -> str:
        """レシピに対するフィードバックを記録
        
        Args:
            recipe_name: レシピ名
            rating: 1-5の評価
            comments: コメント
            recipe_context: レシピ生成時のコンテキスト
            
        Returns:
            フィードバックID
        """
        feedback_id = f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            timestamp=datetime.now().isoformat(),
            feedback_type=FeedbackType.RECIPE_RATING.value,
            content={
                "recipe_name": recipe_name,
                "rating": rating,
                "comments": comments
            },
            context=recipe_context or {},
            confidence=1.0
        )
        
        self._save_feedback(feedback)
        
        # 学習イベントとして記録
        self._record_learning_event(
            event_type="recipe_feedback",
            user_action=f"rated_recipe_{rating}",
            recipe_context={"recipe_name": recipe_name},
            feedback_data=asdict(feedback)
        )
        
        # 適応的学習の実行
        self._update_adaptive_preferences_from_recipe_rating(
            recipe_name, rating, recipe_context
        )
        
        self.logger.info(
            "Recipe feedback recorded",
            recipe_name=recipe_name,
            rating=rating,
            feedback_id=feedback_id
        )
        
        return feedback_id
    
    def record_ingredient_preference_change(
        self, 
        ingredient: str, 
        new_preference: str, 
        reason: str = ""
    ) -> str:
        """食材の好み変化を記録
        
        Args:
            ingredient: 食材名
            new_preference: "like", "dislike", "neutral"
            reason: 変化の理由
            
        Returns:
            フィードバックID
        """
        feedback_id = f"ingredient_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            timestamp=datetime.now().isoformat(),
            feedback_type=FeedbackType.INGREDIENT_PREFERENCE.value,
            content={
                "ingredient": ingredient,
                "new_preference": new_preference,
                "reason": reason
            },
            context={},
            confidence=0.9
        )
        
        self._save_feedback(feedback)
        
        # 適応的嗜好を更新
        self._update_adaptive_preference(
            ingredient, 
            self._preference_to_score(new_preference),
            "ingredient_feedback"
        )
        
        self.logger.info(
            "Ingredient preference change recorded",
            ingredient=ingredient,
            new_preference=new_preference,
            feedback_id=feedback_id
        )
        
        return feedback_id
    
    def record_user_interaction(
        self, 
        interaction_type: str, 
        details: Dict[str, Any]
    ) -> str:
        """ユーザーインタラクションを記録
        
        Args:
            interaction_type: インタラクションの種類
            details: 詳細情報
            
        Returns:
            イベントID
        """
        event_id = f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        learning_event = LearningEvent(
            event_id=event_id,
            timestamp=datetime.now().isoformat(),
            event_type=interaction_type,
            user_action=details.get("action", "unknown"),
            recipe_context=details.get("recipe_context", {}),
            feedback_data=details.get("feedback", None),
            learning_outcome="recorded"
        )
        
        self._save_learning_event(learning_event)
        
        self.logger.info(
            "User interaction recorded",
            interaction_type=interaction_type,
            event_id=event_id
        )
        
        return event_id
    
    def analyze_preference_trends(self, days: int = 30) -> Dict[str, Any]:
        """嗜好のトレンド分析
        
        Args:
            days: 分析対象期間（日数）
            
        Returns:
            トレンド分析結果
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # フィードバックデータの読み込み
        feedbacks = self._load_json(self.feedback_file)
        recent_feedbacks = [
            f for f in feedbacks 
            if datetime.fromisoformat(f["timestamp"]) > cutoff_date
        ]
        
        analysis = {
            "period_days": days,
            "total_feedback_count": len(recent_feedbacks),
            "recipe_ratings": self._analyze_recipe_ratings(recent_feedbacks),
            "ingredient_trends": self._analyze_ingredient_trends(recent_feedbacks),
            "cuisine_trends": self._analyze_cuisine_trends(recent_feedbacks),
            "preference_stability": self._calculate_preference_stability(),
            "recommendations": self._generate_learning_recommendations()
        }
        
        self.logger.info(
            "Preference trends analyzed",
            period_days=days,
            feedback_count=len(recent_feedbacks)
        )
        
        return analysis
    
    def get_updated_preferences(self) -> PreferenceData:
        """学習結果を反映した最新の嗜好データを取得
        
        Returns:
            学習結果が反映された嗜好データ
        """
        # ベース嗜好データを取得
        base_preferences = self.preference_parser.parse_all_preferences()
        
        # 適応的嗜好データを読み込み
        adaptive_prefs = self._load_json(self.adaptive_preferences_file)
        
        # 学習結果を統合
        updated_preferences = self._merge_adaptive_preferences(
            base_preferences, adaptive_prefs
        )
        
        self.logger.info(
            "Updated preferences generated",
            adaptive_items=len(adaptive_prefs)
        )
        
        return updated_preferences
    
    def _save_feedback(self, feedback: UserFeedback):
        """フィードバックを保存"""
        feedbacks = self._load_json(self.feedback_file)
        feedbacks.append(asdict(feedback))
        self._save_json(self.feedback_file, feedbacks)
    
    def _save_learning_event(self, event: LearningEvent):
        """学習イベントを保存"""
        events = self._load_json(self.learning_events_file)
        events.append(asdict(event))
        self._save_json(self.learning_events_file, events)
    
    def _record_learning_event(
        self, 
        event_type: str, 
        user_action: str, 
        recipe_context: Dict[str, Any],
        feedback_data: Dict[str, Any] = None
    ):
        """学習イベントを記録"""
        event = LearningEvent(
            event_id=f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            user_action=user_action,
            recipe_context=recipe_context,
            feedback_data=feedback_data,
            learning_outcome="preference_updated"
        )
        
        self._save_learning_event(event)
    
    def _update_adaptive_preferences_from_recipe_rating(
        self, 
        recipe_name: str, 
        rating: int, 
        recipe_context: Dict[str, Any]
    ):
        """レシピ評価から適応的嗜好を更新"""
        if not recipe_context:
            return
        
        # 材料から嗜好を推定
        ingredients = recipe_context.get("ingredients", [])
        cuisine_type = recipe_context.get("cuisine_type", "")
        
        # 評価をスコアに変換（1-5 → -1.0 to 1.0）
        score = (rating - 3) / 2.0  # 3が中性点
        
        # 材料の嗜好を更新
        for ingredient in ingredients:
            self._update_adaptive_preference(ingredient, score * 0.3, "recipe_rating")
        
        # 料理ジャンルの嗜好を更新
        if cuisine_type:
            self._update_adaptive_preference(cuisine_type, score * 0.5, "recipe_rating")
    
    def _update_adaptive_preference(
        self, 
        item_name: str, 
        score_change: float, 
        source: str
    ):
        """適応的嗜好を更新"""
        adaptive_prefs = self._load_json(self.adaptive_preferences_file)
        
        if item_name not in adaptive_prefs:
            adaptive_prefs[item_name] = {
                "item_name": item_name,
                "current_score": 0.0,
                "confidence_level": 0.1,
                "last_updated": datetime.now().isoformat(),
                "update_count": 0,
                "trend": "stable"
            }
        
        pref = adaptive_prefs[item_name]
        old_score = pref["current_score"]
        
        # スコア更新（重み付き平均）
        weight = min(0.2, 1.0 / (pref["update_count"] + 1))
        new_score = old_score + (score_change * weight)
        new_score = max(-1.0, min(1.0, new_score))  # -1.0 to 1.0に制限
        
        # トレンド計算
        if abs(new_score - old_score) > 0.1:
            trend = "increasing" if new_score > old_score else "decreasing"
        else:
            trend = "stable"
        
        # 更新
        pref.update({
            "current_score": new_score,
            "confidence_level": min(1.0, pref["confidence_level"] + 0.1),
            "last_updated": datetime.now().isoformat(),
            "update_count": pref["update_count"] + 1,
            "trend": trend
        })
        
        self._save_json(self.adaptive_preferences_file, adaptive_prefs)
    
    def _preference_to_score(self, preference: str) -> float:
        """嗜好文字列をスコアに変換"""
        mapping = {
            "like": 0.8,
            "love": 1.0,
            "neutral": 0.0,
            "dislike": -0.8,
            "hate": -1.0
        }
        return mapping.get(preference.lower(), 0.0)
    
    def _analyze_recipe_ratings(self, feedbacks: List[Dict]) -> Dict[str, Any]:
        """レシピ評価の分析"""
        recipe_feedbacks = [
            f for f in feedbacks 
            if f["feedback_type"] == FeedbackType.RECIPE_RATING.value
        ]
        
        if not recipe_feedbacks:
            return {"average_rating": 0, "rating_count": 0, "trends": []}
        
        ratings = [f["content"]["rating"] for f in recipe_feedbacks]
        
        return {
            "average_rating": sum(ratings) / len(ratings),
            "rating_count": len(ratings),
            "rating_distribution": {i: ratings.count(i) for i in range(1, 6)},
            "recent_trend": "improving" if ratings[-3:] and sum(ratings[-3:]) > sum(ratings[:3]) else "stable"
        }
    
    def _analyze_ingredient_trends(self, feedbacks: List[Dict]) -> Dict[str, Any]:
        """食材トレンドの分析"""
        ingredient_changes = [
            f for f in feedbacks 
            if f["feedback_type"] == FeedbackType.INGREDIENT_PREFERENCE.value
        ]
        
        trends = {}
        for feedback in ingredient_changes:
            ingredient = feedback["content"]["ingredient"]
            preference = feedback["content"]["new_preference"]
            
            if ingredient not in trends:
                trends[ingredient] = []
            trends[ingredient].append(preference)
        
        return {
            "changed_ingredients": len(trends),
            "ingredient_trends": trends
        }
    
    def _analyze_cuisine_trends(self, feedbacks: List[Dict]) -> Dict[str, Any]:
        """料理ジャンルトレンドの分析"""
        # TODO: 料理ジャンル別の分析ロジック
        return {"cuisine_changes": 0}
    
    def _calculate_preference_stability(self) -> float:
        """嗜好の安定性を計算"""
        adaptive_prefs = self._load_json(self.adaptive_preferences_file)
        
        if not adaptive_prefs:
            return 1.0
        
        # 最近の変化度合いを計算
        recent_changes = [
            pref for pref in adaptive_prefs.values()
            if pref["trend"] != "stable"
        ]
        
        stability = 1.0 - (len(recent_changes) / len(adaptive_prefs))
        return max(0.0, stability)
    
    def _generate_learning_recommendations(self) -> List[str]:
        """学習ベースの推奨事項を生成"""
        recommendations = []
        
        adaptive_prefs = self._load_json(self.adaptive_preferences_file)
        
        # 高評価アイテムの推奨
        high_rated = [
            item for item, data in adaptive_prefs.items()
            if data["current_score"] > 0.5 and data["confidence_level"] > 0.5
        ]
        
        if high_rated:
            recommendations.append(f"好評価の食材活用: {', '.join(high_rated[:3])}")
        
        # 新しい挑戦の提案
        stable_prefs = [
            item for item, data in adaptive_prefs.items()
            if data["trend"] == "stable" and data["update_count"] > 5
        ]
        
        if len(stable_prefs) > 10:
            recommendations.append("新しい料理ジャンルへの挑戦を推奨")
        
        return recommendations
    
    def _merge_adaptive_preferences(
        self, 
        base_preferences: PreferenceData, 
        adaptive_prefs: Dict[str, Any]
    ) -> PreferenceData:
        """ベース嗜好と適応的嗜好をマージ"""
        # TODO: より高度なマージロジックの実装
        # 現在は基本的にベース嗜好をそのまま返す
        return base_preferences
    
    def _load_json(self, file_path: Path) -> Any:
        """JSONファイルを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [] if file_path.name.endswith('_events.json') or file_path.name.endswith('_feedback.json') else {}
    
    def _save_json(self, file_path: Path, data: Any):
        """JSONファイルに保存"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """学習システムの要約情報を取得"""
        feedbacks = self._load_json(self.feedback_file)
        events = self._load_json(self.learning_events_file)
        adaptive_prefs = self._load_json(self.adaptive_preferences_file)
        
        return {
            "total_feedbacks": len(feedbacks),
            "total_events": len(events),
            "adaptive_preferences_count": len(adaptive_prefs),
            "last_feedback": feedbacks[-1]["timestamp"] if feedbacks else None,
            "learning_data_path": str(self.learning_data_path),
            "system_status": "active"
        }