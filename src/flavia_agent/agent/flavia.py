import os
import time
import json
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from .base import BaseAgent
from ..data.models import MealPreferences, Recipe
from ..exceptions import (
    AIProviderError, NetworkError, ParseError, ConfigurationError,
    classify_ai_error, AuthenticationError, RateLimitError
)
from ..utils.logging import configure_logging, get_logger, log_ai_api_call


class FlaviaAgent(BaseAgent):
    """強化されたFlavia AI献立エージェント
    
    エラーハンドリング、リトライ機能、フォールバック、
    構造化ログを備えた堅牢な実装
    """
    
    def __init__(
        self, 
        primary_provider: str = "openai",
        fallback_provider: Optional[str] = "anthropic",
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        """
        Args:
            primary_provider: メインのAIプロバイダー
            fallback_provider: フォールバック用プロバイダー
            max_retries: リトライ回数
            timeout: API呼び出しタイムアウト（秒）
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries
        self.timeout = timeout
        
        # ログ設定
        configure_logging()
        self.logger = get_logger(__name__)
        
        # クライアント初期化
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """AIクライアントを初期化する"""
        
        # OpenAI クライアント
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.clients["openai"] = AsyncOpenAI(
                api_key=openai_key,
                timeout=self.timeout
            )
            self.logger.info("OpenAI client initialized")
        
        # Anthropic クライアント
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.clients["anthropic"] = AsyncAnthropic(
                api_key=anthropic_key,
                timeout=self.timeout
            )
            self.logger.info("Anthropic client initialized")
        
        # プライマリプロバイダーの確認
        if self.primary_provider not in self.clients:
            raise ConfigurationError(
                f"Primary provider '{self.primary_provider}' is not configured. "
                f"Please set the appropriate API key.",
                config_key=f"{self.primary_provider.upper()}_API_KEY"
            )
    
    async def generate_meal_plan(self, preferences: MealPreferences) -> List[Recipe]:
        """献立プランを生成する（エラーハンドリング強化版）"""
        
        self.logger.info(
            "Starting meal plan generation",
            budget=preferences.budget,
            dietary_restrictions=preferences.dietary_restrictions,
            cuisine_preferences=preferences.cuisine_preferences,
            cooking_time=preferences.cooking_time,
            servings=preferences.servings
        )
        
        try:
            prompt = self._create_meal_plan_prompt(preferences)
            response = await self._call_ai_with_fallback(prompt, "meal_plan_generation")
            recipes = self._parse_recipes(response)
            
            self.logger.info(
                "Meal plan generation completed",
                recipe_count=len(recipes),
                success=True
            )
            
            return recipes
            
        except Exception as e:
            self.logger.error(
                "Meal plan generation failed",
                error_type=type(e).__name__,
                error_message=str(e),
                preferences=preferences.model_dump()
            )
            raise
    
    async def get_recipe_suggestions(self, query: str, preferences: MealPreferences) -> List[Recipe]:
        """レシピ提案を取得する（エラーハンドリング強化版）"""
        
        self.logger.info(
            "Starting recipe suggestions",
            query=query,
            budget=preferences.budget
        )
        
        try:
            prompt = self._create_recipe_prompt(query, preferences)
            response = await self._call_ai_with_fallback(prompt, "recipe_suggestions")
            recipes = self._parse_recipes(response)
            
            self.logger.info(
                "Recipe suggestions completed",
                query=query,
                recipe_count=len(recipes),
                success=True
            )
            
            return recipes
            
        except Exception as e:
            self.logger.error(
                "Recipe suggestions failed",
                query=query,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
    
    async def _call_ai_with_fallback(self, prompt: str, operation: str) -> str:
        """フォールバック機能付きAI呼び出し"""
        
        # プライマリプロバイダーで試行
        try:
            return await self._call_ai_with_retry(prompt, self.primary_provider, operation)
        except (AuthenticationError, ConfigurationError):
            # 認証エラーや設定エラーは即座に再発生
            raise
        except Exception as e:
            self.logger.warning(
                "Primary provider failed, trying fallback",
                primary_provider=self.primary_provider,
                fallback_provider=self.fallback_provider,
                error=str(e)
            )
            
            # フォールバックプロバイダーで試行
            if (self.fallback_provider and 
                self.fallback_provider != self.primary_provider and
                self.fallback_provider in self.clients):
                
                try:
                    return await self._call_ai_with_retry(prompt, self.fallback_provider, operation)
                except Exception as fallback_error:
                    self.logger.error(
                        "Both primary and fallback providers failed",
                        primary_error=str(e),
                        fallback_error=str(fallback_error)
                    )
                    raise AIProviderError(
                        f"Both {self.primary_provider} and {self.fallback_provider} failed",
                        provider="both",
                        original_error=fallback_error
                    )
            else:
                # フォールバックが利用できない場合
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkError, RateLimitError))
    )
    async def _call_ai_with_retry(self, prompt: str, provider: str, operation: str) -> str:
        """リトライ機能付きAI呼び出し"""
        
        if provider not in self.clients:
            raise ConfigurationError(
                f"Provider '{provider}' is not configured",
                config_key=f"{provider.upper()}_API_KEY"
            )
        
        start_time = time.time()
        
        try:
            if provider == "openai":
                response = await self._call_openai(prompt)
            elif provider == "anthropic":
                response = await self._call_anthropic(prompt)
            else:
                raise AIProviderError(f"Unsupported provider: {provider}", provider=provider)
            
            duration = time.time() - start_time
            
            log_ai_api_call(
                self.logger,
                provider=provider,
                model=self._get_model_name(provider),
                prompt_length=len(prompt),
                success=True,
                response_length=len(response) if response else 0,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # エラー分類
            classified_error = classify_ai_error(e, provider)
            
            log_ai_api_call(
                self.logger,
                provider=provider,
                model=self._get_model_name(provider),
                prompt_length=len(prompt),
                success=False,
                duration=duration,
                error=str(classified_error)
            )
            
            raise classified_error
    
    async def _call_openai(self, prompt: str) -> str:
        """OpenAI API呼び出し"""
        try:
            response = await self.clients["openai"].chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise AIProviderError("Empty response from OpenAI", provider="openai")
            
            return response.choices[0].message.content
            
        except Exception as e:
            if "openai" in str(type(e).__module__):
                # OpenAI固有のエラーをFlavia例外に変換
                raise classify_ai_error(e, "openai")
            raise
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Anthropic API呼び出し"""
        try:
            response = await self.clients["anthropic"].messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if not response.content or not response.content[0].text:
                raise AIProviderError("Empty response from Anthropic", provider="anthropic")
            
            return response.content[0].text
            
        except Exception as e:
            if "anthropic" in str(type(e).__module__):
                # Anthropic固有のエラーをFlavia例外に変換
                raise classify_ai_error(e, "anthropic")
            raise
    
    def _get_model_name(self, provider: str) -> str:
        """プロバイダーのモデル名を取得"""
        models = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-5-sonnet-20241022"
        }
        return models.get(provider, "unknown")
    
    def _create_meal_plan_prompt(self, preferences: MealPreferences) -> str:
        """献立生成用プロンプトを作成"""
        return f"""
        Create a meal plan based on the following preferences:
        - Budget: ${preferences.budget}
        - Dietary restrictions: {', '.join(preferences.dietary_restrictions)}
        - Cuisine preferences: {', '.join(preferences.cuisine_preferences)}
        - Cooking time: {preferences.cooking_time} minutes
        - Servings: {preferences.servings}

        Please suggest 3 recipes that fit these criteria. For each recipe, provide:
        - name: Recipe name
        - ingredients: List of ingredients with quantities
        - instructions: Step-by-step cooking instructions
        - prep_time: Preparation time in minutes
        - cook_time: Cooking time in minutes
        - servings: Number of servings
        - estimated_cost: Estimated cost in dollars
        - cuisine_type: Type of cuisine
        - difficulty: Difficulty level (Easy/Medium/Hard)

        IMPORTANT: Format the response as a valid JSON array of recipe objects. 
        Do not include any explanatory text outside the JSON.
        
        Example format:
        [
          {{
            "name": "Recipe Name",
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "prep_time": 10,
            "cook_time": 20,
            "servings": 4,
            "estimated_cost": 15.0,
            "cuisine_type": "Italian",
            "difficulty": "Medium"
          }}
        ]
        """

    def _create_recipe_prompt(self, query: str, preferences: MealPreferences) -> str:
        """レシピ検索用プロンプトを作成"""
        return f"""
        Find recipes related to: {query}
        
        Consider these preferences:
        - Budget: ${preferences.budget}
        - Dietary restrictions: {', '.join(preferences.dietary_restrictions)}
        - Cuisine preferences: {', '.join(preferences.cuisine_preferences)}
        - Cooking time: {preferences.cooking_time} minutes
        - Servings: {preferences.servings}

        Provide 3 relevant recipes in the same JSON format as specified above.
        IMPORTANT: Only return valid JSON array, no additional text.
        """

    def _parse_recipes(self, response: str) -> List[Recipe]:
        """AIレスポンスをRecipeオブジェクトに変換"""
        
        if not response or not response.strip():
            raise ParseError("Empty response from AI provider", raw_data=response)
        
        try:
            # JSONブロックの抽出（```json ```で囲まれている場合）
            cleaned_response = response.strip()
            if "```json" in cleaned_response:
                start = cleaned_response.find("```json") + 7
                end = cleaned_response.find("```", start)
                if end != -1:
                    cleaned_response = cleaned_response[start:end].strip()
            elif "```" in cleaned_response:
                start = cleaned_response.find("```") + 3
                end = cleaned_response.find("```", start)
                if end != -1:
                    cleaned_response = cleaned_response[start:end].strip()
            
            # JSON解析
            recipes_data = json.loads(cleaned_response)
            
            if not isinstance(recipes_data, list):
                raise ParseError(
                    "Expected JSON array but got different type",
                    raw_data=cleaned_response,
                    parser_type="recipe_list"
                )
            
            if not recipes_data:
                self.logger.warning("No recipes found in AI response")
                return []
            
            # Recipeオブジェクトに変換
            recipes = []
            for i, recipe_data in enumerate(recipes_data):
                try:
                    recipe = Recipe(**recipe_data)
                    recipes.append(recipe)
                except Exception as e:
                    self.logger.warning(
                        "Failed to parse recipe",
                        recipe_index=i,
                        recipe_data=recipe_data,
                        error=str(e)
                    )
                    # 個別レシピの解析失敗は無視して続行
                    continue
            
            if not recipes:
                raise ParseError(
                    "No valid recipes could be parsed",
                    raw_data=cleaned_response,
                    parser_type="recipe_validation"
                )
            
            return recipes
            
        except json.JSONDecodeError as e:
            raise ParseError(
                f"Invalid JSON in AI response: {e}",
                raw_data=response,
                parser_type="json_decode",
                original_error=e
            )
        except Exception as e:
            if isinstance(e, ParseError):
                raise
            raise ParseError(
                f"Unexpected error parsing recipes: {e}",
                raw_data=response,
                parser_type="general",
                original_error=e
            )