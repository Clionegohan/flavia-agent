"""個人の嗜好データを解析・構造化するモジュール"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

from ..utils.file_utils import safe_read_text_file, get_personal_data_path


@dataclass
class FoodPreference:
    """食べ物の好み情報"""
    name: str
    rating: int  # 1-5の評価
    notes: str = ""


@dataclass
class CookingSkill:
    """料理スキル情報"""
    skill_name: str
    level: int  # 1-5のレベル
    notes: str = ""


@dataclass
class PersonalProfile:
    """個人プロフィール情報"""
    age: str
    gender: str
    activity_level: str
    location: str
    family_structure: str
    allergies: List[str]
    health_conditions: List[str]
    meal_times: Dict[str, str]
    cooking_time_available: Dict[str, str]
    dining_out_frequency: str


@dataclass
class PreferenceData:
    """統合された嗜好データ"""
    profile: PersonalProfile
    liked_foods: List[FoodPreference]
    disliked_foods: List[str]
    cuisine_preferences: List[FoodPreference]
    cooking_skills: List[CookingSkill]
    health_goals: List[str]
    dietary_restrictions: List[str]
    recent_trends: List[str]
    cooking_equipment: Dict[str, List[str]]


class PreferenceParser:
    """個人嗜好データの解析クラス"""
    
    def __init__(self):
        self.data_path = get_personal_data_path()
    
    def parse_all_preferences(self) -> PreferenceData:
        """全ての嗜好データを解析して統合"""
        profile = self._parse_profile()
        preferences = self._parse_food_preferences()
        skills = self._parse_cooking_skills()
        health_data = self._parse_health_goals()
        
        return PreferenceData(
            profile=profile,
            liked_foods=preferences["liked"],
            disliked_foods=preferences["disliked"],
            cuisine_preferences=preferences["cuisines"],
            cooking_skills=skills["skills"],
            health_goals=health_data["goals"],
            dietary_restrictions=health_data["restrictions"],
            recent_trends=preferences["trends"],
            cooking_equipment=skills["equipment"]
        )
    
    def _parse_profile(self) -> PersonalProfile:
        """プロフィールファイルを解析"""
        content = safe_read_text_file(self.data_path / "profile.txt")
        
        # 基本情報の抽出
        age = self._extract_field(content, r"年齢:\s*(.+)")
        gender = self._extract_field(content, r"性別:\s*(.+)")
        activity = self._extract_field(content, r"活動量:\s*(.+)")
        location = self._extract_field(content, r"居住地域:\s*(.+)")
        family = self._extract_field(content, r"家族構成:\s*(.+)")
        
        # アレルギー情報
        allergies = self._extract_list_field(content, r"アレルギー:\s*(.+)")
        health_conditions = self._extract_list_field(content, r"持病:\s*(.+)")
        
        # 食事時間の抽出
        meal_times = {}
        meal_section = re.search(r"平日の食事時間:(.*?)(?=\n##|\n-|$)", content, re.DOTALL)
        if meal_section:
            for line in meal_section.group(1).split('\n'):
                if '朝食:' in line:
                    meal_times['breakfast'] = line.split('朝食:')[1].strip()
                elif '昼食:' in line:
                    meal_times['lunch'] = line.split('昼食:')[1].strip()
                elif '夕食:' in line:
                    meal_times['dinner'] = line.split('夕食:')[1].strip()
        
        # 調理時間
        cooking_time = {}
        prep_time = self._extract_field(content, r"食事準備可能時間:\s*(.+)")
        if prep_time:
            parts = prep_time.split('、')
            for part in parts:
                if '平日' in part:
                    cooking_time['weekday'] = part.replace('平日', '').strip()
                elif '休日' in part:
                    cooking_time['weekend'] = part.replace('休日', '').strip()
        
        dining_out = self._extract_field(content, r"外食頻度:\s*(.+)")
        
        return PersonalProfile(
            age=age,
            gender=gender,
            activity_level=activity,
            location=location,
            family_structure=family,
            allergies=allergies,
            health_conditions=health_conditions,
            meal_times=meal_times,
            cooking_time_available=cooking_time,
            dining_out_frequency=dining_out
        )
    
    def _parse_food_preferences(self) -> Dict[str, Any]:
        """食べ物の好みファイルを解析"""
        content = safe_read_text_file(self.data_path / "preferences.txt")
        
        # 大好きな食べ物
        liked_foods = []
        liked_section = self._extract_section(content, "大好きな食べ物")
        for line in liked_section:
            if line.strip().startswith('-'):
                food_info = line.strip()[1:].strip()
                if ':' in food_info:
                    category, items = food_info.split(':', 1)
                    liked_foods.append(FoodPreference(
                        name=f"{category.strip()}: {items.strip()}",
                        rating=5,
                        notes="大好き"
                    ))
        
        # 苦手・嫌いな食べ物
        disliked_foods = []
        disliked_section = self._extract_section(content, "苦手・嫌いな食べ物")
        for line in disliked_section:
            if line.strip().startswith('-'):
                foods = line.strip()[1:].strip()
                # カンマ区切りの食材を分割
                for food in foods.split('、'):
                    if food.strip():
                        disliked_foods.append(food.strip())
        
        # 料理の種類別好み
        cuisine_preferences = []
        cuisine_section = self._extract_section(content, "料理の種類別好み")
        for line in cuisine_section:
            if line.strip().startswith('-') and '★' in line:
                parts = line.strip()[1:].strip().split(':')
                if len(parts) >= 2:
                    cuisine = parts[0].strip()
                    rating_part = parts[1].strip()
                    rating = rating_part.count('★')
                    notes = rating_part.replace('★', '').replace('☆', '').strip()
                    
                    cuisine_preferences.append(FoodPreference(
                        name=cuisine,
                        rating=rating,
                        notes=notes
                    ))
        
        # 最近のトレンド
        trends = []
        trends_section = self._extract_section(content, "最近の気分・トレンド")
        for line in trends_section:
            if line.strip().startswith('-'):
                trends.append(line.strip()[1:].strip())
        
        return {
            "liked": liked_foods,
            "disliked": disliked_foods,
            "cuisines": cuisine_preferences,
            "trends": trends
        }
    
    def _parse_cooking_skills(self) -> Dict[str, Any]:
        """料理スキルファイルを解析"""
        content = safe_read_text_file(self.data_path / "cooking_skills.txt")
        
        # 料理レベル
        level_text = self._extract_field(content, r"全体的なレベル:\s*(.+)")
        
        # 得意な料理・技術
        skills = []
        skills_section = self._extract_section(content, "得意な料理・技術")
        for line in skills_section:
            if line.strip().startswith('-') and '★' in line:
                parts = line.strip()[1:].strip().split(':')
                if len(parts) >= 2:
                    skill = parts[0].strip()
                    rating_part = parts[1].strip()
                    rating = rating_part.count('★')
                    notes = rating_part.replace('★', '').replace('☆', '').strip()
                    
                    skills.append(CookingSkill(
                        skill_name=skill,
                        level=rating,
                        notes=notes
                    ))
        
        # 調理器具
        equipment = {
            "available": [],
            "sometimes": [],
            "not_available": []
        }
        
        # よく使う器具
        often_section = self._extract_section(content, "よく使う")
        for line in often_section:
            if line.strip().startswith('-'):
                equipment["available"].append(line.strip()[1:].strip())
        
        # たまに使う器具
        sometimes_section = self._extract_section(content, "たまに使う")
        for line in sometimes_section:
            if line.strip().startswith('-'):
                equipment["sometimes"].append(line.strip()[1:].strip())
        
        # 持っていない器具
        not_available_section = self._extract_section(content, "持っていない/使えない")
        for line in not_available_section:
            if line.strip().startswith('-'):
                equipment["not_available"].append(line.strip()[1:].strip())
        
        return {
            "skills": skills,
            "equipment": equipment,
            "overall_level": level_text
        }
    
    def _parse_health_goals(self) -> Dict[str, Any]:
        """健康目標ファイルを解析"""
        content = safe_read_text_file(self.data_path / "health_goals.txt")
        
        # 健康目標
        goals = []
        goals_section = self._extract_section(content, "現在の健康目標")
        for line in goals_section:
            if line.strip().startswith('-'):
                goals.append(line.strip()[1:].strip())
        
        # 食事制約
        restrictions = []
        restrictions_section = self._extract_section(content, "食事制約")
        for line in restrictions_section:
            if line.strip().startswith('-') and '：' in line:
                restriction_type, value = line.strip()[1:].split('：', 1)
                if value.strip() not in ['なし', '特になし']:
                    restrictions.append(f"{restriction_type.strip()}: {value.strip()}")
        
        return {
            "goals": goals,
            "restrictions": restrictions
        }
    
    def _extract_field(self, content: str, pattern: str) -> str:
        """正規表現で単一フィールドを抽出"""
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""
    
    def _extract_list_field(self, content: str, pattern: str) -> List[str]:
        """正規表現でリストフィールドを抽出"""
        match = re.search(pattern, content)
        if not match:
            return []
        
        value = match.group(1).strip()
        if value in ['なし', '特になし']:
            return []
        
        return [item.strip() for item in value.split('、') if item.strip()]
    
    def _extract_section(self, content: str, section_title: str) -> List[str]:
        """指定されたセクションの内容を抽出"""
        pattern = rf"##\s*{re.escape(section_title)}(.*?)(?=##|$)"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return []
        
        lines = match.group(1).strip().split('\n')
        return [line for line in lines if line.strip()]
    
    def get_preference_summary(self) -> str:
        """嗜好データの要約を文字列で取得"""
        data = self.parse_all_preferences()
        
        summary = []
        summary.append(f"# {data.profile.age}歳{data.profile.gender}性のプロフィール")
        summary.append(f"居住地: {data.profile.location}")
        summary.append(f"活動量: {data.profile.activity_level}")
        
        if data.disliked_foods:
            summary.append(f"苦手な食べ物: {', '.join(data.disliked_foods)}")
        
        summary.append("## 料理の好み")
        for pref in data.cuisine_preferences:
            summary.append(f"- {pref.name}: {'★' * pref.rating} {pref.notes}")
        
        summary.append("## 健康目標")
        for goal in data.health_goals:
            summary.append(f"- {goal}")
        
        summary.append("## 最近のトレンド")
        for trend in data.recent_trends:
            summary.append(f"- {trend}")
        
        return '\n'.join(summary)