import os
from typing import List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from .base import BaseAgent, MealPreferences, Recipe


class FlaviaAgent(BaseAgent):
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if provider == "openai":
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "anthropic":
            self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        prompt = self._create_meal_plan_prompt(preferences)
        response = await self._call_ai(prompt)
        return self._parse_recipes(response)

    async def get_recipe_suggestions(self, query: str, preferences: MealPreferences) -> List[Recipe]:
        prompt = self._create_recipe_prompt(query, preferences)
        response = await self._call_ai(prompt)
        return self._parse_recipes(response)

    def _create_meal_plan_prompt(self, preferences: MealPreferences) -> str:
        return f"""
        Create a meal plan based on the following preferences:
        - Budget: ${preferences.budget}
        - Dietary restrictions: {', '.join(preferences.dietary_restrictions)}
        - Cuisine preferences: {', '.join(preferences.cuisine_preferences)}
        - Cooking time: {preferences.cooking_time} minutes
        - Servings: {preferences.servings}

        Please suggest 3 recipes that fit these criteria. For each recipe, provide:
        - Name
        - Ingredients list
        - Step-by-step instructions
        - Prep time and cook time
        - Estimated cost
        - Cuisine type
        - Difficulty level (Easy/Medium/Hard)

        Format the response as a JSON array of recipe objects.
        """

    def _create_recipe_prompt(self, query: str, preferences: MealPreferences) -> str:
        return f"""
        Find recipes related to: {query}
        
        Consider these preferences:
        - Budget: ${preferences.budget}
        - Dietary restrictions: {', '.join(preferences.dietary_restrictions)}
        - Cuisine preferences: {', '.join(preferences.cuisine_preferences)}
        - Cooking time: {preferences.cooking_time} minutes
        - Servings: {preferences.servings}

        Provide 3 relevant recipes in JSON format.
        """

    async def _call_ai(self, prompt: str) -> str:
        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

    def _parse_recipes(self, response: str) -> List[Recipe]:
        import json
        try:
            recipes_data = json.loads(response)
            return [Recipe(**recipe) for recipe in recipes_data]
        except (json.JSONDecodeError, ValueError):
            return []