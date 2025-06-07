"""個人データを統合してコンテキストを構築するモジュール"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .preference_parser import PreferenceParser, PreferenceData
from ..utils.file_utils import safe_read_text_file, get_personal_data_path


class ContextBuilder:
    """個人データからコンテキストを構築するクラス"""
    
    def __init__(self):
        self.parser = PreferenceParser()
        self.data_path = get_personal_data_path()
    
    def build_full_context(self) -> str:
        """全ての個人データを統合した完全なコンテキストを構築"""
        preference_data = self.parser.parse_all_preferences()
        
        context_parts = [
            self._build_profile_context(preference_data.profile),
            self._build_preference_context(preference_data),
            self._build_skills_context(preference_data),
            self._build_health_context(preference_data),
            self._build_recent_context(),
            self._build_constraints_context(preference_data)
        ]
        
        return "\n\n".join([part for part in context_parts if part.strip()])
    
    def build_recipe_context(self, include_sales_info: bool = False) -> str:
        """レシピ提案用の特化コンテキストを構築"""
        preference_data = self.parser.parse_all_preferences()
        
        context_parts = [
            "# レシピ提案のためのユーザー情報",
            "",
            "## 基本プロフィール",
            f"- {preference_data.profile.age}歳{preference_data.profile.gender}性、{preference_data.profile.family_structure}",
            f"- 調理可能時間: 平日{preference_data.profile.cooking_time_available.get('weekday', '30分')}、休日{preference_data.profile.cooking_time_available.get('weekend', '1時間')}",
            "",
            "## 絶対に避けるべき食材",
            f"- {', '.join(preference_data.disliked_foods) if preference_data.disliked_foods else 'なし'}",
            "",
            "## 料理ジャンルの好み",
        ]
        
        # 好みの料理を評価順でソート
        sorted_cuisines = sorted(preference_data.cuisine_preferences, 
                               key=lambda x: x.rating, reverse=True)
        for cuisine in sorted_cuisines[:5]:  # 上位5つ
            context_parts.append(f"- {cuisine.name}: {'★' * cuisine.rating} ({cuisine.notes})")
        
        context_parts.extend([
            "",
            "## 利用可能な調理器具",
            f"- よく使う: {', '.join(preference_data.cooking_equipment.get('available', []))}"
        ])
        
        if preference_data.cooking_equipment.get('not_available'):
            context_parts.append(f"- 使えない: {', '.join(preference_data.cooking_equipment['not_available'])}")
        
        context_parts.extend([
            "",
            "## 健康面での配慮",
        ])
        
        for goal in preference_data.health_goals[:3]:  # 主要な目標3つ
            context_parts.append(f"- {goal}")
        
        if preference_data.dietary_restrictions:
            context_parts.extend([
                "",
                "## 食事制約",
            ])
            for restriction in preference_data.dietary_restrictions:
                context_parts.append(f"- {restriction}")
        
        context_parts.extend([
            "",
            "## 最近の興味・トレンド",
        ])
        
        for trend in preference_data.recent_trends:
            context_parts.append(f"- {trend}")
        
        return "\n".join(context_parts)
    
    def build_shopping_context(self) -> str:
        """買い物・特売情報活用用のコンテキストを構築"""
        preference_data = self.parser.parse_all_preferences()
        
        # よく使う食材を抽出
        frequently_used = []
        for liked in preference_data.liked_foods:
            if any(keyword in liked.name.lower() for keyword in ['肉', '魚', '野菜', '米', 'パン']):
                frequently_used.append(liked.name)
        
        context = [
            "# 買い物・特売情報活用のためのユーザー情報",
            "",
            "## 購入頻度の高い食材カテゴリ",
        ]
        
        # カテゴリ別に整理
        categories = {
            "肉類": ["鶏肉", "豚肉", "牛肉"],
            "野菜類": ["キャベツ", "大根", "じゃがいも", "さつまいも", "白菜", "もやし"],
            "主食": ["米", "パン", "麺類"],
            "その他": ["木綿豆腐", "季節のフルーツ"]
        }
        
        for category, items in categories.items():
            context.append(f"- {category}: {', '.join(items)}")
        
        context.extend([
            "",
            "## 絶対に買わない食材",
            f"- {', '.join(preference_data.disliked_foods) if preference_data.disliked_foods else 'なし'}",
            "",
            "## 予算・購入パターン",
            "- 牛肉は金銭的な問題でたまにのみ",
            "- 魚は好きだが処理の手間で敬遠気味",
            "",
            "## 調理器具の制約",
            f"- 使えない器具: {', '.join(preference_data.cooking_equipment.get('not_available', []))}",
            "- 特に炊飯器なし（土鍋使用）"
        ])
        
        return "\n".join(context)
    
    def _build_profile_context(self, profile) -> str:
        """プロフィール情報のコンテキスト"""
        lines = [
            "# 基本プロフィール",
            f"- 年齢・性別: {profile.age}歳{profile.gender}性",
            f"- 居住地: {profile.location}",
            f"- 家族構成: {profile.family_structure}",
            f"- 活動量: {profile.activity_level}",
            f"- 外食頻度: {profile.dining_out_frequency}"
        ]
        
        if profile.meal_times:
            lines.append("- 食事時間:")
            for meal, time in profile.meal_times.items():
                meal_jp = {"breakfast": "朝食", "lunch": "昼食", "dinner": "夕食"}.get(meal, meal)
                lines.append(f"  - {meal_jp}: {time}")
        
        return "\n".join(lines)
    
    def _build_preference_context(self, data: PreferenceData) -> str:
        """食べ物の好み情報のコンテキスト"""
        lines = ["# 食べ物の好み"]
        
        if data.disliked_foods:
            lines.extend([
                "## 苦手・避けるべき食材",
                f"- {', '.join(data.disliked_foods)}"
            ])
        
        lines.append("## 料理ジャンルの好み（評価順）")
        sorted_cuisines = sorted(data.cuisine_preferences, key=lambda x: x.rating, reverse=True)
        for cuisine in sorted_cuisines:
            lines.append(f"- {cuisine.name}: {'★' * cuisine.rating} {cuisine.notes}")
        
        if data.recent_trends:
            lines.append("## 最近のトレンド・興味")
            for trend in data.recent_trends:
                lines.append(f"- {trend}")
        
        return "\n".join(lines)
    
    def _build_skills_context(self, data: PreferenceData) -> str:
        """料理スキル情報のコンテキスト"""
        lines = ["# 料理スキル・環境"]
        
        lines.append("## 利用可能な調理器具")
        if data.cooking_equipment.get("available"):
            lines.append("### よく使う")
            for equipment in data.cooking_equipment["available"]:
                lines.append(f"- {equipment}")
        
        if data.cooking_equipment.get("not_available"):
            lines.append("### 使えない（重要な制約）")
            for equipment in data.cooking_equipment["not_available"]:
                lines.append(f"- {equipment}")
        
        if data.cooking_skills:
            lines.append("## 料理スキルレベル")
            for skill in data.cooking_skills:
                lines.append(f"- {skill.skill_name}: {'★' * skill.level} {skill.notes}")
        
        return "\n".join(lines)
    
    def _build_health_context(self, data: PreferenceData) -> str:
        """健康目標・制約のコンテキスト"""
        lines = ["# 健康・栄養面の配慮"]
        
        if data.health_goals:
            lines.append("## 健康目標")
            for goal in data.health_goals:
                lines.append(f"- {goal}")
        
        if data.dietary_restrictions:
            lines.append("## 食事制約")
            for restriction in data.dietary_restrictions:
                lines.append(f"- {restriction}")
        
        if data.profile.allergies:
            lines.append("## アレルギー")
            for allergy in data.profile.allergies:
                lines.append(f"- {allergy}")
        
        return "\n".join(lines)
    
    def _build_recent_context(self) -> str:
        """最近のコンテキスト（履歴・記憶）"""
        context_memory = safe_read_text_file(self.data_path / "context_memory.txt")
        
        if not context_memory.strip():
            return ""
        
        # 短期記憶の部分を抽出
        lines = ["# 最近のコンテキスト"]
        
        # 現在気になっていることを抽出
        if "現在気になっていること" in context_memory:
            lines.append("## 現在の関心事")
            # 簡単な抽出（実際の実装では正規表現で改善可能）
            concern_section = context_memory.split("現在気になっていること")[1].split("##")[0]
            for line in concern_section.split('\n'):
                if line.strip().startswith('-'):
                    lines.append(line.strip())
        
        return "\n".join(lines)
    
    def _build_constraints_context(self, data: PreferenceData) -> str:
        """制約事項の要約"""
        constraints = []
        
        # 調理時間の制約
        cooking_time = data.profile.cooking_time_available
        if cooking_time:
            weekday = cooking_time.get('weekday', '30分')
            constraints.append(f"平日の調理時間制限: {weekday}")
        
        # 器具の制約
        if data.cooking_equipment.get('not_available'):
            unavailable = ', '.join(data.cooking_equipment['not_available'][:3])  # 主要な3つ
            constraints.append(f"使用不可器具: {unavailable}")
        
        # 食材の制約
        if data.disliked_foods:
            dislikes = ', '.join(data.disliked_foods[:5])  # 主要な5つ
            constraints.append(f"避けるべき食材: {dislikes}")
        
        if not constraints:
            return ""
        
        lines = ["# 重要な制約事項"]
        for constraint in constraints:
            lines.append(f"- {constraint}")
        
        return "\n".join(lines)
    
    def get_context_for_sale_integration(self, sale_items: List[str]) -> str:
        """特売商品との組み合わせ用コンテキスト"""
        preference_data = self.parser.parse_all_preferences()
        
        # 特売商品との相性をチェック
        compatible_items = []
        incompatible_items = []
        
        for item in sale_items:
            is_compatible = True
            
            # 苦手な食材チェック
            for disliked in preference_data.disliked_foods:
                if disliked in item:
                    incompatible_items.append(f"{item} (苦手: {disliked})")
                    is_compatible = False
                    break
            
            if is_compatible:
                compatible_items.append(item)
        
        context = [
            "# 特売商品との組み合わせ分析",
            "",
            "## 購入推奨商品",
            f"- {', '.join(compatible_items) if compatible_items else 'なし'}",
        ]
        
        if incompatible_items:
            context.extend([
                "",
                "## 避けるべき商品",
                f"- {', '.join(incompatible_items)}"
            ])
        
        context.extend([
            "",
            "## ユーザーの制約",
            f"- 苦手な食材: {', '.join(preference_data.disliked_foods)}",
            f"- 調理時間制限: 平日{preference_data.profile.cooking_time_available.get('weekday', '30分')}",
            f"- 使えない器具: {', '.join(preference_data.cooking_equipment.get('not_available', []))}"
        ])
        
        return "\n".join(context)