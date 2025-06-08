"""構造化ログ設定"""

import logging
import sys
from typing import Any, Dict
import structlog


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """ログ設定を初期化する
    
    Args:
        log_level: ログレベル ("DEBUG", "INFO", "WARNING", "ERROR")
        json_logs: JSON形式でログを出力するかどうか
    """
    
    # 標準ログレベルの設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # structlogの設定
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.filter_by_level,
    ]
    
    if json_logs:
        # 本番環境用のJSON形式
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ])
    else:
        # 開発環境用の読みやすい形式
        processors.extend([
            structlog.processors.CallsiteParameterAdder(
                parameters=[structlog.processors.CallsiteParameter.FILENAME,
                           structlog.processors.CallsiteParameter.LINENO]
            ),
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """構造化ロガーを取得する
    
    Args:
        name: ロガー名（通常は__name__を使用）
        
    Returns:
        設定済みの構造化ロガー
    """
    return structlog.get_logger(name)


def log_function_call(logger: structlog.BoundLogger, func_name: str, **kwargs) -> None:
    """関数呼び出しをログに記録する
    
    Args:
        logger: ロガーインスタンス
        func_name: 関数名
        **kwargs: ログに含める追加情報
    """
    logger.info(
        "Function called",
        function=func_name,
        **kwargs
    )


def log_error(
    logger: structlog.BoundLogger, 
    error: Exception, 
    context: Dict[str, Any] = None
) -> None:
    """エラーを構造化形式でログに記録する
    
    Args:
        logger: ロガーインスタンス
        error: 発生したエラー
        context: エラーの文脈情報
    """
    context = context or {}
    
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context
    )


def log_ai_api_call(
    logger: structlog.BoundLogger,
    provider: str,
    model: str,
    prompt_length: int,
    success: bool,
    response_length: int = None,
    duration: float = None,
    error: str = None
) -> None:
    """AI API呼び出しをログに記録する
    
    Args:
        logger: ロガーインスタンス
        provider: AIプロバイダー名
        model: 使用モデル名
        prompt_length: プロンプトの文字数
        success: 成功/失敗
        response_length: レスポンスの文字数
        duration: 処理時間（秒）
        error: エラーメッセージ（失敗時）
    """
    log_data = {
        "provider": provider,
        "model": model,
        "prompt_length": prompt_length,
        "success": success
    }
    
    if response_length is not None:
        log_data["response_length"] = response_length
    
    if duration is not None:
        log_data["duration_seconds"] = round(duration, 3)
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info("AI API call successful", **log_data)
    else:
        logger.error("AI API call failed", **log_data)