from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel


class MealPreferences(BaseModel):
    budget: float
    dietary_restrictions: List[str] = []
    cuisine_preferences: List[str] = []
    cooking_time: int = 30
    servings: int = 4


class Recipe(BaseModel):
    name: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: int
    cook_time: int
    servings: int
    estimated_cost: float
    cuisine_type: str
    difficulty: str


class BaseAgent(ABC):
    @abstractmethod
    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        pass

    @abstractmethod
    async def get_recipe_suggestions(self, query: str, preferences: MealPreferences) -> List[Recipe]:
        pass