"""
Flavia AI - 学習型料理パートナー

パーソナライズされた料理提案とレシピ生成のためのAIエージェント
"""

__version__ = "0.2.0"
__author__ = "Flavia Development Team"

from .core.agents.personal import PersonalAgent
from .core.models.recipe import Recipe
from .core.models.preferences import MealPreferences

__all__ = [
    "PersonalAgent",
    "Recipe", 
    "MealPreferences",
]