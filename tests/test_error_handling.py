"""エラーハンドリングのテスト"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from flavia_agent.exceptions import (
    FlaviaException, AIProviderError, NetworkError, ParseError,
    ConfigurationError, AuthenticationError, RateLimitError,
    QuotaExceededError, classify_ai_error
)
from flavia_agent.agent.flavia import FlaviaAgent
from flavia_agent.data.models import MealPreferences


class TestExceptions:
    """例外クラスのテスト"""
    
    def test_base_exception(self):
        """基底例外クラスのテスト"""
        details = {"key": "value"}
        original_error = ValueError("Original error")
        
        exc = FlaviaException("Test message", details, original_error)
        
        assert exc.message == "Test message"
        assert exc.details == details
        assert exc.original_error == original_error
        assert "Test message" in str(exc)
        assert "Original" in str(exc)
    
    def test_ai_provider_error(self):
        """AIプロバイダーエラーのテスト"""
        exc = AIProviderError(
            "API failed",
            provider="openai",
            status_code=429,
            response_text="Rate limit exceeded"
        )
        
        assert exc.details["provider"] == "openai"
        assert exc.details["status_code"] == 429
        assert exc.details["response_text"] == "Rate limit exceeded"
    
    def test_configuration_error(self):
        """設定エラーのテスト"""
        exc = ConfigurationError(
            "API key not found",
            config_key="OPENAI_API_KEY"
        )
        
        assert exc.details["config_key"] == "OPENAI_API_KEY"
    
    def test_parse_error(self):
        """解析エラーのテスト"""
        exc = ParseError(
            "Invalid JSON",
            raw_data='{"invalid": json}',
            parser_type="json"
        )
        
        assert exc.details["raw_data"] == '{"invalid": json}'
        assert exc.details["parser_type"] == "json"


class TestErrorClassification:
    """エラー分類のテスト"""
    
    def test_classify_rate_limit_error(self):
        """レート制限エラーの分類"""
        error = Exception("Rate limit exceeded")
        classified = classify_ai_error(error, "openai")
        
        assert isinstance(classified, RateLimitError)
        assert classified.details["provider"] == "openai"
    
    def test_classify_authentication_error(self):
        """認証エラーの分類"""
        error = Exception("Invalid API key")
        classified = classify_ai_error(error, "anthropic")
        
        assert isinstance(classified, AuthenticationError)
        assert classified.details["provider"] == "anthropic"
    
    def test_classify_quota_error(self):
        """クォータエラーの分類"""
        error = Exception("Quota exceeded")
        classified = classify_ai_error(error, "openai")
        
        assert isinstance(classified, QuotaExceededError)
        assert classified.details["provider"] == "openai"
    
    def test_classify_network_error(self):
        """ネットワークエラーの分類"""
        error = Exception("Connection timeout")
        classified = classify_ai_error(error, "openai")
        
        assert isinstance(classified, NetworkError)
    
    def test_classify_general_error(self):
        """一般的なエラーの分類"""
        error = Exception("Unknown error")
        classified = classify_ai_error(error, "openai")
        
        assert isinstance(classified, AIProviderError)
        assert classified.details["provider"] == "openai"


class TestFlaviaAgentErrorHandling:
    """FlaviaAgentのエラーハンドリングテスト"""
    
    @pytest.fixture
    def mock_preferences(self):
        """テスト用の好み設定"""
        return MealPreferences(
            budget=30.0,
            dietary_restrictions=["vegetarian"],
            cuisine_preferences=["Italian"],
            cooking_time=30,
            servings=4
        )
    
    def test_initialization_with_missing_api_key(self):
        """APIキー未設定時の初期化エラー"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                FlaviaAgent(primary_provider="openai")
            
            assert "not configured" in str(exc_info.value)
            assert exc_info.value.details["config_key"] == "OPENAI_API_KEY"
    
    @pytest.mark.asyncio
    async def test_openai_api_error_handling(self, mock_preferences):
        """OpenAI APIエラーのハンドリング"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            # APIエラーをモック
            mock_error = Exception("API Error")
            with patch.object(agent, '_call_openai', side_effect=mock_error):
                with pytest.raises(AIProviderError):
                    await agent.generate_meal_plan(mock_preferences)
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, mock_preferences):
        """フォールバック機能のテスト"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key-1',
            'ANTHROPIC_API_KEY': 'test-key-2'
        }):
            agent = FlaviaAgent(
                primary_provider="openai",
                fallback_provider="anthropic"
            )
            
            # プライマリが失敗、フォールバックが成功
            mock_response = '[{"name": "Test Recipe", "ingredients": ["test"], "instructions": ["test"], "prep_time": 10, "cook_time": 15, "servings": 4, "estimated_cost": 10.0, "cuisine_type": "Test", "difficulty": "Easy"}]'
            
            with patch.object(agent, '_call_openai', side_effect=Exception("Primary failed")):
                with patch.object(agent, '_call_anthropic', return_value=mock_response):
                    recipes = await agent.generate_meal_plan(mock_preferences)
                    
                    assert len(recipes) == 1
                    assert recipes[0].name == "Test Recipe"
    
    @pytest.mark.asyncio
    async def test_both_providers_fail(self, mock_preferences):
        """両方のプロバイダーが失敗した場合"""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key-1',
            'ANTHROPIC_API_KEY': 'test-key-2'
        }):
            agent = FlaviaAgent(
                primary_provider="openai",
                fallback_provider="anthropic"
            )
            
            with patch.object(agent, '_call_openai', side_effect=Exception("Primary failed")):
                with patch.object(agent, '_call_anthropic', side_effect=Exception("Fallback failed")):
                    with pytest.raises(AIProviderError) as exc_info:
                        await agent.generate_meal_plan(mock_preferences)
                    
                    assert "Both" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_parse_error_handling(self, mock_preferences):
        """解析エラーのハンドリング"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            # 無効なJSONを返す
            invalid_json = "This is not JSON"
            with patch.object(agent, '_call_openai', return_value=invalid_json):
                with pytest.raises(ParseError) as exc_info:
                    await agent.generate_meal_plan(mock_preferences)
                
                assert "Invalid JSON" in str(exc_info.value)
                assert exc_info.value.details["raw_data"] == invalid_json
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_preferences):
        """空のレスポンスのハンドリング"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            with patch.object(agent, '_call_openai', return_value=""):
                with pytest.raises(ParseError) as exc_info:
                    await agent.generate_meal_plan(mock_preferences)
                
                assert "Empty response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_recipe_data_handling(self, mock_preferences):
        """無効なレシピデータのハンドリング"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            # 必須フィールドが不足したレシピデータ
            invalid_recipes = '[{"name": "Incomplete Recipe"}]'  # 必須フィールドなし
            
            with patch.object(agent, '_call_openai', return_value=invalid_recipes):
                with pytest.raises(ParseError) as exc_info:
                    await agent.generate_meal_plan(mock_preferences)
                
                assert "No valid recipes" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_partial_recipe_parsing(self, mock_preferences):
        """部分的なレシピ解析の処理"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            # 1つは有効、1つは無効なレシピ
            mixed_recipes = '''[
                {
                    "name": "Valid Recipe",
                    "ingredients": ["ingredient1"],
                    "instructions": ["step1"],
                    "prep_time": 10,
                    "cook_time": 15,
                    "servings": 4,
                    "estimated_cost": 10.0,
                    "cuisine_type": "Test",
                    "difficulty": "Easy"
                },
                {
                    "name": "Invalid Recipe"
                }
            ]'''
            
            with patch.object(agent, '_call_openai', return_value=mixed_recipes):
                recipes = await agent.generate_meal_plan(mock_preferences)
                
                # 有効なレシピのみが返される
                assert len(recipes) == 1
                assert recipes[0].name == "Valid Recipe"
    
    @pytest.mark.asyncio
    async def test_json_with_code_blocks(self, mock_preferences):
        """コードブロック付きJSONの解析"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            # ```json ``` で囲まれたレスポンス
            json_with_blocks = '''```json
[
    {
        "name": "Test Recipe",
        "ingredients": ["ingredient1"],
        "instructions": ["step1"],
        "prep_time": 10,
        "cook_time": 15,
        "servings": 4,
        "estimated_cost": 10.0,
        "cuisine_type": "Test",
        "difficulty": "Easy"
    }
]
```'''
            
            with patch.object(agent, '_call_openai', return_value=json_with_blocks):
                recipes = await agent.generate_meal_plan(mock_preferences)
                
                assert len(recipes) == 1
                assert recipes[0].name == "Test Recipe"


class TestRetryMechanism:
    """リトライ機能のテスト"""
    
    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """ネットワークエラー時のリトライ"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            # 最初はネットワークエラー、2回目で成功
            call_count = 0
            def mock_call(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise NetworkError("Connection failed")
                return '[{"name": "Success", "ingredients": ["test"], "instructions": ["test"], "prep_time": 10, "cook_time": 15, "servings": 4, "estimated_cost": 10.0, "cuisine_type": "Test", "difficulty": "Easy"}]'
            
            preferences = MealPreferences(budget=30.0)
            
            with patch.object(agent, '_call_openai', side_effect=mock_call):
                # リトライデコレータを無効化して直接テスト
                with patch('flavia_agent.agent.flavia.retry', lambda **kwargs: lambda f: f):
                    recipes = await agent._call_ai_with_retry("test", "openai", "test")
                    assert "Success" in recipes
    
    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """認証エラー時はリトライしない"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FlaviaAgent(primary_provider="openai", fallback_provider=None)
            
            def mock_call(*args, **kwargs):
                raise AuthenticationError("Invalid API key", provider="openai")
            
            with patch.object(agent, '_call_openai', side_effect=mock_call):
                with pytest.raises(AuthenticationError):
                    await agent._call_ai_with_retry("test", "openai", "test")