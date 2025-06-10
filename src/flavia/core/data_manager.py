"""シンプルな個人データ管理システム"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class PersonalDataManager:
    """個人データの読み書きを管理するシンプルなクラス"""
    
    def __init__(self):
        self.data_file = Path(__file__).parent.parent / "data" / "personal_data.json"
        self._data = None
    
    def load_data(self) -> Dict[str, Any]:
        """個人データを読み込み"""
        if self._data is None:
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"個人データ読み込みエラー: {e}")
                self._data = self._get_default_data()
        
        return self._data
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """個人データを保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._data = data  # キャッシュ更新
            return True
        except Exception as e:
            print(f"個人データ保存エラー: {e}")
            return False
    
    def get_profile_summary(self) -> str:
        """プロフィールサマリーを取得"""
        data = self.load_data()
        profile = data.get("profile", {})
        
        summary = f"""
## 個人プロフィール
- {profile.get('age', '不明')}歳、{profile.get('gender', '不明')}性
- 居住地: {profile.get('location', '不明')}
- 家族構成: {profile.get('family_structure', '不明')}
- 調理時間: 平日{profile.get('lifestyle', {}).get('cooking_time', {}).get('weekday', '不明')}、休日{profile.get('lifestyle', {}).get('cooking_time', {}).get('weekend', '不明')}
"""
        return summary
    
    def get_preferences_summary(self) -> str:
        """嗜好サマリーを取得"""
        data = self.load_data()
        prefs = data.get("preferences", {})
        
        # 高評価の料理ジャンル
        high_rated_cuisines = [
            name for name, rating in prefs.get("cuisine_ratings", {}).items() 
            if rating >= 4
        ]
        
        summary = f"""
## 食の嗜好
### 好きな料理ジャンル
{', '.join(high_rated_cuisines)}

### 苦手な食材
{', '.join(prefs.get('disliked_foods', []))}

### 味の好み
- 辛さ: {prefs.get('taste_preferences', {}).get('spice_level', '不明')}
- 甘さ: {prefs.get('taste_preferences', {}).get('sweetness', '不明')}
"""
        return summary
    
    def get_cooking_constraints(self) -> str:
        """調理制約を取得"""
        data = self.load_data()
        equipment = data.get("kitchen_equipment", {})
        skills = data.get("cooking_skills", {})
        
        summary = f"""
## 調理環境・制約
### 調理レベル
{skills.get('overall_level', '不明')}

### 使用できない器具
{', '.join(equipment.get('not_available', []))}

### 得意分野
{', '.join(skills.get('strong_areas', []))}

### 苦手分野
{', '.join(skills.get('weak_areas', []))}
"""
        return summary
    
    def get_health_goals(self) -> str:
        """健康目標を取得"""
        data = self.load_data()
        goals = data.get("health_goals", [])
        
        summary = f"""
## 健康目標
{chr(10).join(f'- {goal}' for goal in goals)}
"""
        return summary
    
    def get_pantry_items(self) -> Dict[str, list]:
        """常備品リストを取得"""
        data = self.load_data()
        return data.get("pantry_items", {})
    
    def create_context_for_ai(self) -> str:
        """AI用の統合コンテキストを作成"""
        context_parts = [
            self.get_profile_summary(),
            self.get_preferences_summary(), 
            self.get_cooking_constraints(),
            self.get_health_goals()
        ]
        
        # 最近の嗜好更新を追加
        recent_updates = self.get_recent_updates(days=30)
        if recent_updates:
            context_parts.append("\n## 最近の嗜好変化")
            for update in recent_updates[-5:]:  # 最新5件
                date = update["timestamp"][:10]
                context_parts.append(f"- {date}: {update['update_text']}")
        
        return "\n".join(context_parts)
    
    def update_preferences_from_text(self, update_text: str) -> bool:
        """自然言語での嗜好更新"""
        try:
            data = self.load_data()
            
            # 更新履歴に追加
            if "preference_updates" not in data:
                data["preference_updates"] = []
            
            data["preference_updates"].append({
                "timestamp": datetime.now().isoformat(),
                "update_text": update_text,
                "processed": False  # 今後AI処理で反映予定
            })
            
            return self.save_data(data)
        except Exception as e:
            print(f"嗜好更新エラー: {e}")
            return False
    
    def get_recent_updates(self, days: int = 30) -> List[Dict]:
        """最近の嗜好更新を取得"""
        try:
            data = self.load_data()
            updates = data.get("preference_updates", [])
            
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_updates = []
            for update in updates:
                update_date = datetime.fromisoformat(update["timestamp"])
                if update_date > cutoff_date:
                    recent_updates.append(update)
            
            return recent_updates
        except Exception as e:
            print(f"更新履歴取得エラー: {e}")
            return []
    
    def _get_default_data(self) -> Dict[str, Any]:
        """デフォルトデータを返す"""
        return {
            "profile": {"age": "不明", "gender": "不明"},
            "preferences": {"disliked_foods": [], "cuisine_ratings": {}},
            "health_goals": [],
            "cooking_skills": {"overall_level": "初心者"},
            "kitchen_equipment": {"available": [], "not_available": []},
            "pantry_items": {"basic_seasonings": []},
            "preference_updates": []
        }


# グローバルインスタンス
data_manager = PersonalDataManager()