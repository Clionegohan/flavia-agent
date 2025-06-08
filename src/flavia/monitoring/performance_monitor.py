"""パフォーマンス監視とメトリクス収集"""

import time
import functools
import asyncio
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger(__name__)


class PerformanceMetrics:
    """パフォーマンスメトリクス収集クラス"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.execution_times = defaultdict(lambda: deque(maxlen=max_history))
        self.call_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_execution(self, function_name: str, execution_time: float, success: bool = True):
        """実行時間とステータスを記録"""
        self.execution_times[function_name].append({
            'time': execution_time,
            'timestamp': datetime.now(),
            'success': success
        })
        self.call_counts[function_name] += 1
        if not success:
            self.error_counts[function_name] += 1
    
    def get_function_stats(self, function_name: str) -> Dict[str, Any]:
        """関数の統計情報を取得"""
        executions = list(self.execution_times[function_name])
        if not executions:
            return {}
        
        times = [e['time'] for e in executions]
        successful_calls = sum(1 for e in executions if e['success'])
        
        return {
            'total_calls': self.call_counts[function_name],
            'successful_calls': successful_calls,
            'error_count': self.error_counts[function_name],
            'success_rate': successful_calls / len(executions) if executions else 0,
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'median_time': sorted(times)[len(times) // 2],
            'recent_calls': len([e for e in executions if e['timestamp'] > datetime.now() - timedelta(minutes=5)])
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """システム全体の概要を取得"""
        total_calls = sum(self.call_counts.values())
        total_errors = sum(self.error_counts.values())
        
        # 最も呼び出される関数
        most_called = max(self.call_counts.items(), key=lambda x: x[1]) if self.call_counts else None
        
        # 最も遅い関数
        slowest_function = None
        max_avg_time = 0
        for func_name in self.execution_times:
            stats = self.get_function_stats(func_name)
            if stats and stats['avg_time'] > max_avg_time:
                max_avg_time = stats['avg_time']
                slowest_function = func_name
        
        return {
            'uptime': datetime.now() - self.start_time,
            'total_function_calls': total_calls,
            'total_errors': total_errors,
            'overall_success_rate': (total_calls - total_errors) / total_calls if total_calls > 0 else 0,
            'monitored_functions': len(self.call_counts),
            'most_called_function': most_called,
            'slowest_function': {'name': slowest_function, 'avg_time': max_avg_time} if slowest_function else None
        }


# グローバルメトリクスインスタンス
metrics = PerformanceMetrics()


def monitor_performance(include_args: bool = False):
    """パフォーマンス監視デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                execution_time = time.time() - start_time
                metrics.record_execution(func.__name__, execution_time, success)
                
                logger.debug(
                    "Function execution monitored",
                    function=func.__name__,
                    execution_time=execution_time,
                    success=success,
                    args_preview=str(args)[:50] if include_args else None
                )
        
        return wrapper
    return decorator


def async_monitor_performance(include_args: bool = False):
    """非同期パフォーマンス監視デコレータ"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                execution_time = time.time() - start_time
                metrics.record_execution(func.__name__, execution_time, success)
                
                logger.debug(
                    "Async function execution monitored",
                    function=func.__name__,
                    execution_time=execution_time,
                    success=success,
                    args_preview=str(args)[:50] if include_args else None
                )
        
        return wrapper
    return decorator


class CacheManager:
    """シンプルなキャッシュ管理"""
    
    def __init__(self, default_ttl: int = 300):  # 5分デフォルト
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        if key not in self.cache:
            return None
        
        # TTLチェック
        if time.time() - self.timestamps[key] > self.default_ttl:
            self.delete(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """キャッシュに設定"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """キャッシュから削除"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        current_time = time.time()
        valid_items = sum(
            1 for timestamp in self.timestamps.values()
            if current_time - timestamp <= self.default_ttl
        )
        
        return {
            'total_items': len(self.cache),
            'valid_items': valid_items,
            'expired_items': len(self.cache) - valid_items,
            'cache_size_bytes': sum(len(str(v)) for v in self.cache.values())
        }


def cache_result(ttl: int = 300, key_generator: Optional[Callable] = None):
    """結果キャッシュデコレータ"""
    cache_manager = CacheManager(ttl)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # キャッシュキー生成
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args))}:{hash(str(kwargs))}"
            
            # キャッシュから取得を試行
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(
                    "Cache hit",
                    function=func.__name__,
                    cache_key=cache_key
                )
                return cached_result
            
            # 関数実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュ
            cache_manager.set(cache_key, result)
            logger.debug(
                "Cache miss - result cached",
                function=func.__name__,
                cache_key=cache_key
            )
            
            return result
        
        # キャッシュ管理関数を追加
        wrapper.cache_stats = cache_manager.get_stats
        wrapper.clear_cache = cache_manager.clear
        
        return wrapper
    
    return decorator


class ResourceMonitor:
    """リソース使用量監視"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """メモリ使用量を取得"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # MB
                'vms_mb': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    @staticmethod
    def get_cpu_usage() -> Dict[str, Any]:
        """CPU使用量を取得"""
        try:
            import psutil
            process = psutil.Process()
            
            return {
                'percent': process.cpu_percent(),
                'system_percent': psutil.cpu_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    @classmethod
    def get_resource_summary(cls) -> Dict[str, Any]:
        """リソース使用量サマリー"""
        return {
            'memory': cls.get_memory_usage(),
            'cpu': cls.get_cpu_usage(),
            'timestamp': datetime.now().isoformat()
        }


def get_performance_report() -> Dict[str, Any]:
    """パフォーマンスレポートを生成"""
    system_overview = metrics.get_system_overview()
    
    # 主要関数の統計
    important_functions = [
        'generate_weekly_dinner_plan',
        '_call_claude_api',
        'build_smart_context',
        'get_updated_preferences'
    ]
    
    function_stats = {}
    for func_name in important_functions:
        stats = metrics.get_function_stats(func_name)
        if stats:
            function_stats[func_name] = stats
    
    # リソース使用量
    resource_summary = ResourceMonitor.get_resource_summary()
    
    return {
        'system_overview': system_overview,
        'function_performance': function_stats,
        'resource_usage': resource_summary,
        'report_timestamp': datetime.now().isoformat()
    }


def performance_alert_check() -> List[Dict[str, Any]]:
    """パフォーマンスアラートをチェック"""
    alerts = []
    
    # 関数の実行時間チェック
    for func_name in ['generate_weekly_dinner_plan', '_call_claude_api']:
        stats = metrics.get_function_stats(func_name)
        if stats and stats['avg_time'] > 10.0:  # 10秒超過
            alerts.append({
                'type': 'slow_function',
                'function': func_name,
                'avg_time': stats['avg_time'],
                'message': f"{func_name} is running slowly (avg: {stats['avg_time']:.2f}s)"
            })
    
    # エラー率チェック
    system_overview = metrics.get_system_overview()
    if system_overview['overall_success_rate'] < 0.9:  # 90%未満
        alerts.append({
            'type': 'high_error_rate',
            'success_rate': system_overview['overall_success_rate'],
            'message': f"High error rate detected: {system_overview['overall_success_rate']:.1%}"
        })
    
    # メモリ使用量チェック
    memory_usage = ResourceMonitor.get_memory_usage()
    if 'percent' in memory_usage and memory_usage['percent'] > 80:
        alerts.append({
            'type': 'high_memory_usage',
            'memory_percent': memory_usage['percent'],
            'message': f"High memory usage: {memory_usage['percent']:.1f}%"
        })
    
    return alerts