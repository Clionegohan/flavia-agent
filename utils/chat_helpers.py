"""
チャットUI用ヘルパー関数
学習機能とUI要素の統合を支援
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


def format_recipe_for_display(recipe: Any) -> Dict[str, Any]:
    """レシピを表示用にフォーマット"""
    return {
        "name": recipe.name,
        "cost": f"${recipe.estimated_cost:.2f}",
        "time": f"{recipe.total_time}分",
        "cuisine": recipe.cuisine_type,
        "servings": f"{recipe.servings}人分",
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "difficulty": recipe.difficulty if hasattr(recipe, 'difficulty') else "普通"
    }


def create_learning_notification(feedback_type: str, item_name: str, old_value: Any = None, new_value: Any = None) -> str:
    """学習通知メッセージを生成"""
    notifications = {
        "recipe_rating": f"📊 「{item_name}」の評価を学習しました！",
        "ingredient_preference": f"🥬 「{item_name}」の好みを更新しました！",
        "cuisine_preference": f"🍽️ {item_name}料理の好みを学習しました！",
        "cooking_time": f"⏰ 調理時間の好みを「{new_value}」に更新しました！",
        "budget": f"💰 予算の好みを「{new_value}」に更新しました！"
    }
    
    return notifications.get(feedback_type, f"📚 {item_name}について学習しました！")


def format_learning_progress(total_feedbacks: int, confidence_score: float) -> str:
    """学習進捗を表示用にフォーマット"""
    if total_feedbacks == 0:
        return "🌱 学習を開始しましょう！"
    elif total_feedbacks < 5:
        return f"🌿 学習初期段階 ({total_feedbacks}件の学習データ)"
    elif total_feedbacks < 20:
        return f"🌳 学習が進んでいます ({total_feedbacks}件の学習データ)"
    else:
        return f"🎯 高精度学習モード ({total_feedbacks}件の学習データ)"


def get_mood_based_suggestions() -> List[Dict[str, str]]:
    """気分ベースの提案候補を取得"""
    return [
        {"emoji": "😴", "text": "疲れた時の簡単料理", "query": "疲れているので15分以内で作れる栄養のある料理を教えて"},
        {"emoji": "🎉", "text": "気分を上げる料理", "query": "今日は気分が良いので、新しい挑戦的な料理を教えて"},
        {"emoji": "⚡", "text": "急いでいる時の料理", "query": "時間がないので10分以内で作れる料理を教えて"},
        {"emoji": "🌱", "text": "ヘルシーな料理", "query": "健康的で野菜たっぷりの料理を教えて"},
        {"emoji": "💰", "text": "節約料理", "query": "予算を抑えたお得な料理を教えて"},
        {"emoji": "🎂", "text": "特別な日の料理", "query": "特別な日にぴったりな少し豪華な料理を教えて"}
    ]


def get_conversation_starters() -> List[str]:
    """会話開始の提案を取得"""
    return [
        "今日の気分にぴったりの料理を教えて",
        "冷蔵庫にあるもので作れる料理はある？",
        "30分以内で作れる美味しい夕食を教えて",
        "今日の特売商品を使ったレシピを教えて",
        "新しい料理に挑戦したい",
        "ヘルシーで栄養バランスの良い料理を教えて",
        "一人分の簡単な料理を教えて",
        "今まで作ったことがない料理を試してみたい"
    ]


def format_time_greeting() -> str:
    """時間帯に応じた挨拶を生成"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 11:
        return "おはようございます！🌅 今日の朝食はいかがでしょうか？"
    elif 11 <= current_hour < 14:
        return "こんにちは！☀️ お昼ご飯の時間ですね！"
    elif 14 <= current_hour < 17:
        return "こんにちは！🍵 おやつタイムですか？"
    elif 17 <= current_hour < 21:
        return "こんばんは！🌆 今日の夕食を一緒に考えましょう！"
    else:
        return "こんばんは！🌙 遅い時間ですが、何か軽い料理はいかがですか？"


def create_recipe_share_text(recipe: Any) -> str:
    """レシピ共有用テキストを生成"""
    ingredients_text = "\n".join([f"・{ing}" for ing in recipe.ingredients[:5]])
    if len(recipe.ingredients) > 5:
        ingredients_text += f"\n・他{len(recipe.ingredients) - 5}種類"
    
    return f"""🍽️ {recipe.name}

💰 コスト: ${recipe.estimated_cost:.2f}
⏱️ 調理時間: {recipe.total_time}分
👤 {recipe.servings}人分

📝 主な材料:
{ingredients_text}

🤖 Flavia AIが個人の好みに合わせて提案したレシピです！
"""


def calculate_user_engagement_score(messages: List[Dict], ratings: Dict) -> float:
    """ユーザーエンゲージメントスコアを計算"""
    if not messages:
        return 0.0
    
    # メッセージ数によるスコア
    message_score = min(len(messages) / 20, 1.0) * 0.4
    
    # 評価数によるスコア
    rating_score = min(len(ratings) / 10, 1.0) * 0.4
    
    # 最近の活動によるスコア
    recent_messages = [m for m in messages if "timestamp" in m]
    if recent_messages:
        latest_time = datetime.fromisoformat(recent_messages[-1]["timestamp"])
        time_diff = (datetime.now() - latest_time).days
        recency_score = max(0, (7 - time_diff) / 7) * 0.2
    else:
        recency_score = 0.0
    
    return message_score + rating_score + recency_score


def get_learning_tips() -> List[str]:
    """学習システムの使い方のヒントを取得"""
    return [
        "💡 レシピを評価するほど、あなたの好みを正確に学習します",
        "🔄 「気に入らない」と感じた時も評価をつけると、避けるべき料理を学習できます",
        "📈 継続的に使用することで、提案精度がどんどん向上します",
        "🎯 具体的なリクエスト（「疲れた時」「節約したい時」など）をすると効果的です",
        "⭐ 5つ星評価で、より詳細な好みを記録できます",
        "🥬 食材の好き嫌いが変わった時は、遠慮なく更新してください"
    ]


def format_dashboard_metrics(dashboard_data: Dict) -> Dict[str, Any]:
    """ダッシュボードメトリクスを表示用にフォーマット"""
    learning_status = dashboard_data.get("学習状況", {})
    week_trends = dashboard_data.get("今週の傾向", {})
    
    return {
        "total_feedback": {
            "value": learning_status.get("総フィードバック数", 0),
            "label": "総フィードバック数",
            "icon": "📊"
        },
        "adaptive_items": {
            "value": learning_status.get("適応的嗜好項目数", 0),
            "label": "学習済み嗜好項目",
            "icon": "🧠"
        },
        "avg_rating": {
            "value": f"{week_trends.get('平均レシピ評価', 0):.1f}/5.0",
            "label": "平均レシピ評価",
            "icon": "⭐"
        },
        "stability": {
            "value": f"{week_trends.get('嗜好安定性', 1.0):.0%}",
            "label": "嗜好安定性",
            "icon": "📊"
        }
    }


def generate_personalized_greeting(user_data: Optional[Dict] = None) -> str:
    """個人化された挨拶を生成"""
    base_greeting = format_time_greeting()
    
    if not user_data:
        return base_greeting
    
    # 学習データに基づいた個人化
    total_feedback = user_data.get("total_feedback", 0)
    
    if total_feedback == 0:
        personal_touch = "\n\n初回利用ですね！あなたの好みを学習していきましょう 🌱"
    elif total_feedback < 5:
        personal_touch = f"\n\n{total_feedback}件のフィードバックをありがとうございます！もっと学習していきますね 📚"
    else:
        personal_touch = f"\n\nこれまで{total_feedback}件のフィードバックで学習しました！精度の高い提案ができそうです 🎯"
    
    return base_greeting + personal_touch