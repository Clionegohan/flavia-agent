"""エラーハンドリングとロバストネス向上のためのユーティリティ"""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, Union
import structlog
from datetime import datetime

from ..exceptions import FlaviaException


logger = structlog.get_logger(__name__)


def safe_execute(
    fallback_value: Any = None,
    log_error: bool = True,
    reraise: bool = False
):
    """安全実行デコレータ - エラー時にフォールバック値を返す"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        "Function execution failed",
                        function=func.__name__,
                        error=str(e),
                        args=str(args)[:100],
                        kwargs=str(kwargs)[:100],
                        traceback=traceback.format_exc()
                    )
                
                if reraise:
                    raise
                
                return fallback_value
        
        return wrapper
    return decorator


def async_safe_execute(
    fallback_value: Any = None,
    log_error: bool = True,
    reraise: bool = False
):
    """非同期安全実行デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        "Async function execution failed",
                        function=func.__name__,
                        error=str(e),
                        args=str(args)[:100],
                        kwargs=str(kwargs)[:100],
                        traceback=traceback.format_exc()
                    )
                
                if reraise:
                    raise
                
                return fallback_value
        
        return wrapper
    return decorator


class ErrorManager:
    """エラー管理クラス"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
    
    def record_error(self, error_type: str, error: Exception, context: Dict[str, Any] = None):
        """エラーを記録"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = {
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        logger.error(
            "Error recorded",
            error_type=error_type,
            error_count=self.error_counts[error_type],
            error_message=str(error),
            context=context
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        return {
            "error_counts": self.error_counts,
            "last_errors": self.last_errors,
            "total_errors": sum(self.error_counts.values())
        }
    
    def should_circuit_break(self, error_type: str, threshold: int = 5) -> bool:
        """サーキットブレーカー判定"""
        return self.error_counts.get(error_type, 0) >= threshold


def validate_input(validation_rules: Dict[str, Any]):
    """入力検証デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 引数の検証
            for param_name, rules in validation_rules.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    
                    # 型チェック
                    if 'type' in rules and not isinstance(value, rules['type']):
                        raise ValueError(f"{param_name} must be of type {rules['type']}")
                    
                    # 必須チェック
                    if rules.get('required', False) and value is None:
                        raise ValueError(f"{param_name} is required")
                    
                    # 長さチェック
                    if 'min_length' in rules and len(str(value)) < rules['min_length']:
                        raise ValueError(f"{param_name} must be at least {rules['min_length']} characters")
                    
                    if 'max_length' in rules and len(str(value)) > rules['max_length']:
                        raise ValueError(f"{param_name} must be at most {rules['max_length']} characters")
                    
                    # 値範囲チェック
                    if 'min_value' in rules and value < rules['min_value']:
                        raise ValueError(f"{param_name} must be at least {rules['min_value']}")
                    
                    if 'max_value' in rules and value > rules['max_value']:
                        raise ValueError(f"{param_name} must be at most {rules['max_value']}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class RetryManager:
    """リトライ管理クラス"""
    
    @staticmethod
    def retry_on_failure(
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """失敗時リトライデコレータ"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            import time
                            sleep_time = delay * (backoff_factor ** attempt)
                            logger.warning(
                                "Function failed, retrying",
                                function=func.__name__,
                                attempt=attempt + 1,
                                max_attempts=max_attempts,
                                retry_after=sleep_time,
                                error=str(e)
                            )
                            time.sleep(sleep_time)
                        else:
                            logger.error(
                                "Function failed after all retries",
                                function=func.__name__,
                                attempts=max_attempts,
                                final_error=str(e)
                            )
                
                raise last_exception
            
            return wrapper
        return decorator
    
    @staticmethod
    def async_retry_on_failure(
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """非同期失敗時リトライデコレータ"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            import asyncio
                            sleep_time = delay * (backoff_factor ** attempt)
                            logger.warning(
                                "Async function failed, retrying",
                                function=func.__name__,
                                attempt=attempt + 1,
                                max_attempts=max_attempts,
                                retry_after=sleep_time,
                                error=str(e)
                            )
                            await asyncio.sleep(sleep_time)
                        else:
                            logger.error(
                                "Async function failed after all retries",
                                function=func.__name__,
                                attempts=max_attempts,
                                final_error=str(e)
                            )
                
                raise last_exception
            
            return wrapper
        return decorator


def create_safe_fallback_response(request_type: str = "unknown") -> Dict[str, Any]:
    """安全なフォールバック応答を作成"""
    fallback_responses = {
        "weekly_dinner": {
            "success": False,
            "content": "申し訳ありません。システムエラーが発生しました。シンプルな献立を提案します。",
            "dinners": [
                {
                    "day": 1,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "main_dish": "鶏の照り焼き丼",
                    "description": "シンプルで美味しい家庭料理",
                    "ingredients": ["鶏もも肉", "米", "醤油", "みりん"],
                    "detailed_recipe": {
                        "prep_time": 10,
                        "cook_time": 20,
                        "servings": 1,
                        "instructions": [
                            "鶏肉を切る",
                            "調味料で味付け", 
                            "ご飯と一緒に盛り付け"
                        ]
                    },
                    "estimated_cost": 8.0,
                    "nutrition_info": "約500kcal",
                    "cooking_difficulty": "簡単"
                }
            ],
            "shopping_list": {
                "ingredients_by_category": {
                    "肉・魚類": ["鶏もも肉"],
                    "米・麺・パン": ["米"],
                    "調味料・スパイス": ["醤油", "みりん"]
                },
                "total_estimated_cost": 8.0,
                "shopping_notes": ["基本的な材料で作れます"],
                "estimated_shopping_time": "15分",
                "total_unique_ingredients": 4
            },
            "fallback": True
        },
        "recipe": {
            "success": False,
            "content": "申し訳ありません。システムエラーが発生しました。基本レシピを提案します。",
            "recipes": [
                {
                    "name": "基本的な炒め物",
                    "ingredients": ["野菜", "肉", "調味料"],
                    "instructions": ["材料を切る", "炒める", "調味する"],
                    "estimated_cost": 6.0,
                    "total_time": 20,
                    "cuisine_type": "家庭料理",
                    "servings": 1
                }
            ],
            "fallback": True
        },
        "default": {
            "success": False,
            "content": "申し訳ありません。一時的なエラーが発生しました。少し時間をおいて再度お試しください。",
            "error_type": "system_error",
            "fallback": True
        }
    }
    
    return fallback_responses.get(request_type, fallback_responses["default"])


class HealthChecker:
    """システムヘルスチェッククラス"""
    
    def __init__(self):
        self.last_check = None
        self.health_status = {}
    
    def check_system_health(self) -> Dict[str, Any]:
        """システム全体のヘルスチェック"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "issues": []
        }
        
        # メモリ使用量チェック
        try:
            import psutil
            memory = psutil.virtual_memory()
            health["components"]["memory"] = {
                "status": "healthy" if memory.percent < 80 else "warning",
                "usage_percent": memory.percent,
                "available_gb": memory.available / (1024**3)
            }
            if memory.percent > 90:
                health["issues"].append("High memory usage detected")
        except ImportError:
            health["components"]["memory"] = {"status": "unknown", "note": "psutil not available"}
        
        # ディスク容量チェック
        try:
            import shutil
            disk_usage = shutil.disk_usage("/")
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            health["components"]["disk"] = {
                "status": "healthy" if disk_percent < 80 else "warning",
                "usage_percent": disk_percent,
                "free_gb": disk_usage.free / (1024**3)
            }
            if disk_percent > 90:
                health["issues"].append("Low disk space detected")
        except Exception:
            health["components"]["disk"] = {"status": "unknown"}
        
        # 全体ステータス判定
        if any(comp.get("status") == "error" for comp in health["components"].values()):
            health["overall_status"] = "error"
        elif any(comp.get("status") == "warning" for comp in health["components"].values()):
            health["overall_status"] = "warning"
        
        self.last_check = health
        return health
    
    def is_healthy(self) -> bool:
        """システムが健全かチェック"""
        if not self.last_check:
            self.check_system_health()
        
        return self.last_check["overall_status"] in ["healthy", "warning"]


# グローバルインスタンス
error_manager = ErrorManager()
health_checker = HealthChecker()


def get_error_context() -> Dict[str, Any]:
    """現在のエラーコンテキストを取得"""
    return {
        "error_summary": error_manager.get_error_summary(),
        "system_health": health_checker.last_check or health_checker.check_system_health(),
        "timestamp": datetime.now().isoformat()
    }