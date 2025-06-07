from typing import List
from pydantic import BaseModel, Field, ConfigDict


class Recipe(BaseModel):
    """レシピを表すモデル"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "カルボナーラ",
                "ingredients": ["スパゲッティ 400g", "ベーコン 100g", "卵 3個", "パルメザンチーズ 50g"],
                "instructions": ["パスタを茹でる", "ベーコンを炒める", "卵とチーズを混ぜる", "すべてを合わせる"],
                "prep_time": 10,
                "cook_time": 15,
                "servings": 4,
                "estimated_cost": 800.0,
                "cuisine_type": "Italian",
                "difficulty": "Medium"
            }
        }
    )
    
    name: str = Field(min_length=1, max_length=100, description="レシピ名")
    ingredients: List[str] = Field(min_length=1, max_length=50, description="材料リスト")
    instructions: List[str] = Field(min_length=1, max_length=20, description="調理手順")
    prep_time: int = Field(ge=0, le=180, description="準備時間（分）")
    cook_time: int = Field(ge=0, le=480, description="調理時間（分）")
    servings: int = Field(ge=1, le=20, description="人数")
    estimated_cost: float = Field(ge=0, le=10000, description="推定費用（円）")
    cuisine_type: str = Field(max_length=50, description="料理の種類")
    difficulty: str = Field(pattern="^(Easy|Medium|Hard)$", description="難易度")
    
    @property
    def total_time(self) -> int:
        """総調理時間を返す"""
        return self.prep_time + self.cook_time
    
    @property
    def cost_per_serving(self) -> float:
        """一人当たりの費用を返す"""
        return self.estimated_cost / self.servings
