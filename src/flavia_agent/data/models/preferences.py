from typing import List
from pydantic import BaseModel, Field, ConfigDict


class MealPreferences(BaseModel):
    """ユーザーの食事の好みと制約を表すモデル"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "budget": 3000.0,
                "dietary_restrictions": ["vegetarian"],
                "cuisine_preferences": ["Italian", "Japanese"],
                "cooking_time": 45,
                "servings": 4
            }
        }
    )
    
    budget: float = Field(gt=0, le=1000, description="予算（円）")
    dietary_restrictions: List[str] = Field(default_factory=list, max_length=10)
    cuisine_preferences: List[str] = Field(default_factory=list, max_length=10)
    cooking_time: int = Field(default=30, ge=5, le=480, description="調理時間（分）")
    servings: int = Field(default=4, ge=1, le=20, description="人数")