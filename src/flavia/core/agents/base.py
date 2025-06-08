from abc import ABC, abstractmethod
from typing import List
from ..models.preferences import MealPreferences
from ..models.recipe import Recipe


class BaseAgent(ABC):
    """AIエージェントの抽象基底クラス"""
    
    @abstractmethod
    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        """献立プランを生成する
        
        Args:
            preferences: ユーザーの好みと制約
            
        Returns:
            生成されたレシピのリスト
        """
        pass

    @abstractmethod
    async def get_recipe_suggestions(self, query: str, preferences: MealPreferences) -> List[Recipe]:
        """クエリに基づいてレシピを提案する
        
        Args:
            query: 検索クエリ
            preferences: ユーザーの好みと制約
            
        Returns:
            提案されたレシピのリスト
        """
        pass