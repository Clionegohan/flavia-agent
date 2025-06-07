"""Flavia専用の例外クラス定義"""

from typing import Dict, Any, Optional


class FlaviaException(Exception):
    """Flaviaの基底例外クラス
    
    すべてのFlavia固有の例外は、この基底クラスを継承する
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self) -> str:
        error_str = self.message
        if self.details:
            error_str += f" Details: {self.details}"
        if self.original_error:
            error_str += f" Original: {type(self.original_error).__name__}: {self.original_error}"
        return error_str


class AIProviderError(FlaviaException):
    """AIプロバイダー関連のエラー
    
    OpenAI、Anthropic APIの呼び出しに関する問題
    """
    
    def __init__(
        self, 
        message: str, 
        provider: str,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        **kwargs
    ):
        details = {
            "provider": provider,
            "status_code": status_code,
            "response_text": response_text
        }
        super().__init__(message, details, **kwargs)


class NetworkError(FlaviaException):
    """ネットワーク関連のエラー
    
    接続タイムアウト、DNS解決失敗など
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ):
        details = {
            "url": url,
            "timeout": timeout
        }
        super().__init__(message, details, **kwargs)


class ValidationError(FlaviaException):
    """入力バリデーション関連のエラー
    
    ユーザー入力やAPIレスポンスの検証失敗
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = {
            "field": field,
            "value": value
        }
        super().__init__(message, details, **kwargs)


class ParseError(FlaviaException):
    """データ解析関連のエラー
    
    JSON解析失敗、レシピデータの構造化失敗など
    """
    
    def __init__(
        self, 
        message: str, 
        raw_data: Optional[str] = None,
        parser_type: Optional[str] = None,
        **kwargs
    ):
        details = {
            "raw_data": raw_data[:500] if raw_data else None,  # 長すぎる場合は切り詰め
            "parser_type": parser_type
        }
        super().__init__(message, details, **kwargs)


class ConfigurationError(FlaviaException):
    """設定関連のエラー
    
    APIキー未設定、無効な設定値など
    """
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = {
            "config_key": config_key
        }
        super().__init__(message, details, **kwargs)


class RateLimitError(AIProviderError):
    """レート制限エラー
    
    APIの使用制限に達した場合
    """
    
    def __init__(
        self, 
        message: str, 
        provider: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = {
            "provider": provider,
            "retry_after": retry_after
        }
        super(AIProviderError, self).__init__(message, details, **kwargs)


class AuthenticationError(AIProviderError):
    """認証エラー
    
    APIキーが無効または期限切れの場合
    """
    
    def __init__(
        self, 
        message: str, 
        provider: str,
        **kwargs
    ):
        details = {
            "provider": provider
        }
        super(AIProviderError, self).__init__(message, details, **kwargs)


class QuotaExceededError(AIProviderError):
    """クォータ超過エラー
    
    APIの使用量制限を超えた場合
    """
    
    def __init__(
        self, 
        message: str, 
        provider: str,
        **kwargs
    ):
        details = {
            "provider": provider
        }
        super(AIProviderError, self).__init__(message, details, **kwargs)


# エラー分類のためのヘルパー関数
def classify_ai_error(error: Exception, provider: str) -> FlaviaException:
    """AI プロバイダーのエラーを適切な例外クラスに変換する"""
    
    error_str = str(error).lower()
    
    if "rate limit" in error_str or "429" in error_str:
        return RateLimitError(
            f"Rate limit exceeded for {provider}",
            provider=provider,
            original_error=error
        )
    
    if "authentication" in error_str or "401" in error_str or "api key" in error_str:
        return AuthenticationError(
            f"Authentication failed for {provider}",
            provider=provider,
            original_error=error
        )
    
    if "quota" in error_str or "billing" in error_str:
        return QuotaExceededError(
            f"Quota exceeded for {provider}",
            provider=provider,
            original_error=error
        )
    
    if "timeout" in error_str or "connection" in error_str:
        return NetworkError(
            f"Network error when connecting to {provider}",
            original_error=error
        )
    
    # その他のエラーは一般的なAIProviderErrorとして扱う
    return AIProviderError(
        f"AI Provider error: {error}",
        provider=provider,
        original_error=error
    )