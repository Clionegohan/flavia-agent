import pytest
from unittest.mock import AsyncMock, patch
from flavia_agent.agent.flavia import FlaviaAgent
from flavia_agent.agent.base import MealPreferences


@pytest.fixture
def sample_preferences():
    return MealPreferences(
        budget=30.0,
        dietary_restrictions=["vegetarian"],
        cuisine_preferences=["Italian"],
        cooking_time=30,
        servings=4
    )


@pytest.fixture
def agent():
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        return FlaviaAgent(provider="openai")


@pytest.mark.asyncio
async def test_generate_meal_plan(agent, sample_preferences):
    mock_response = '''[
        {
            "name": "Spaghetti Carbonara",
            "ingredients": ["spaghetti", "eggs", "parmesan", "pancetta"],
            "instructions": ["Boil pasta", "Mix eggs and cheese", "Combine"],
            "prep_time": 10,
            "cook_time": 15,
            "servings": 4,
            "estimated_cost": 12.0,
            "cuisine_type": "Italian",
            "difficulty": "Medium"
        }
    ]'''
    
    with patch.object(agent, '_call_ai', return_value=mock_response):
        recipes = await agent.generate_meal_plan(sample_preferences)
        
        assert len(recipes) == 1
        assert recipes[0].name == "Spaghetti Carbonara"
        assert recipes[0].cuisine_type == "Italian"


def test_meal_preferences_validation():
    preferences = MealPreferences(budget=25.0)
    assert preferences.budget == 25.0
    assert preferences.dietary_restrictions == []
    assert preferences.cooking_time == 30