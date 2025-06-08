"""高性能キャッシュ管理システム"""

import time
import json
import hashlib
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import structlog

logger = structlog.get_logger(__name__)


class LRUCache:
    """LRU (Least Recently Used) キャッシュ実装"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        with self._lock:
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            # TTLチェック
            current_time = time.time()
            if current_time - self.timestamps[key] > self.default_ttl:
                self._remove_expired(key)
                self.miss_count += 1
                return None
            
            # LRU更新
            self.cache.move_to_end(key)
            self.access_times[key] = current_time
            self.hit_count += 1
            
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """キャッシュに値を設定"""
        with self._lock:
            current_time = time.time()
            
            # 容量チェック
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            self.cache[key] = value
            self.timestamps[key] = current_time
            self.access_times[key] = current_time
            
            # 最新に移動
            self.cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """キャッシュから削除"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
                del self.access_times[key]
                return True
            return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
            self.access_times.clear()
            self.hit_count = 0
            self.miss_count = 0
    
    def _evict_lru(self) -> None:
        """最も古いアイテムを削除"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove_expired(oldest_key)
    
    def _remove_expired(self, key: str) -> None:
        """期限切れアイテムを削除"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            del self.access_times[key]
    
    def cleanup_expired(self) -> int:
        """期限切れアイテムを一括削除"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.timestamps.items()
                if current_time - timestamp > self.default_ttl
            ]
            
            for key in expired_keys:
                self._remove_expired(key)
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        with self._lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
                'memory_usage_kb': self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> float:
        """メモリ使用量を推定（KB）"""
        try:
            total_size = 0
            for key, value in self.cache.items():
                total_size += len(str(key)) + len(str(value))
            return total_size / 1024
        except:
            return 0.0


class SmartCacheManager:
    """高性能スマートキャッシュマネージャー"""
    
    def __init__(self):
        self.preference_cache = LRUCache(max_size=100, default_ttl=300)  # 5分
        self.context_cache = LRUCache(max_size=500, default_ttl=180)    # 3分
        self.recipe_cache = LRUCache(max_size=1000, default_ttl=600)    # 10分
        self.api_cache = LRUCache(max_size=200, default_ttl=1800)       # 30分
        
        # 定期クリーンアップ
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # 1分
    
    def get_cache_by_type(self, cache_type: str) -> LRUCache:
        """タイプ別キャッシュ取得"""
        caches = {
            'preference': self.preference_cache,
            'context': self.context_cache,
            'recipe': self.recipe_cache,
            'api': self.api_cache
        }
        return caches.get(cache_type, self.context_cache)
    
    def smart_cache_key(self, function_name: str, *args, **kwargs) -> str:
        """スマートキャッシュキー生成"""
        # 関数名とパラメータからハッシュを生成
        content = f"{function_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        cache = self.get_cache_by_type(cache_type)
        result = cache.get(key)
        
        # 定期クリーンアップ
        self._periodic_cleanup()
        
        return result
    
    def set(self, cache_type: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """キャッシュに設定"""
        cache = self.get_cache_by_type(cache_type)
        cache.set(key, value, ttl)
    
    def invalidate(self, cache_type: str, pattern: Optional[str] = None) -> int:
        """キャッシュ無効化"""
        cache = self.get_cache_by_type(cache_type)
        
        if pattern is None:
            cache.clear()
            return 1
        
        # パターンマッチング削除
        deleted_count = 0
        keys_to_delete = [
            key for key in cache.cache.keys()
            if pattern in key
        ]
        
        for key in keys_to_delete:
            if cache.delete(key):
                deleted_count += 1
        
        return deleted_count
    
    def _periodic_cleanup(self) -> None:
        """定期的な期限切れアイテムクリーンアップ"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            total_cleaned = 0
            for cache in [self.preference_cache, self.context_cache, 
                         self.recipe_cache, self.api_cache]:
                total_cleaned += cache.cleanup_expired()
            
            if total_cleaned > 0:
                logger.debug(f"Cache cleanup: removed {total_cleaned} expired items")
            
            self._last_cleanup = current_time
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """全体キャッシュ統計"""
        stats = {
            'preference': self.preference_cache.get_stats(),
            'context': self.context_cache.get_stats(),
            'recipe': self.recipe_cache.get_stats(),
            'api': self.api_cache.get_stats()
        }
        
        # 合計統計
        total_size = sum(s['size'] for s in stats.values())
        total_hits = sum(s['hit_count'] for s in stats.values())
        total_misses = sum(s['miss_count'] for s in stats.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        stats['overall'] = {
            'total_size': total_size,
            'total_hit_rate': overall_hit_rate,
            'total_memory_kb': sum(s['memory_usage_kb'] for s in stats.values()),
            'cache_efficiency': self._calculate_efficiency()
        }
        
        return stats
    
    def _calculate_efficiency(self) -> float:
        """キャッシュ効率を計算"""
        stats = [
            self.preference_cache.get_stats(),
            self.context_cache.get_stats(),
            self.recipe_cache.get_stats(),
            self.api_cache.get_stats()
        ]
        
        total_hit_rate = sum(s['hit_rate'] for s in stats) / len(stats)
        memory_efficiency = 1.0 - min(1.0, sum(s['memory_usage_kb'] for s in stats) / 10240)  # 10MB基準
        
        return (total_hit_rate + memory_efficiency) / 2


# グローバルキャッシュマネージャー
cache_manager = SmartCacheManager()


def cached(cache_type: str = 'context', ttl: Optional[int] = None, key_generator: Optional[Callable] = None):
    """高性能キャッシュデコレータ"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # キャッシュキー生成
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache_manager.smart_cache_key(func.__name__, *args, **kwargs)
            
            # キャッシュから取得試行
            cached_result = cache_manager.get(cache_type, cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_result
            
            # 関数実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュ
            cache_manager.set(cache_type, cache_key, result, ttl)
            logger.debug(f"Cache miss - result cached: {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(cache_type: str, pattern: Optional[str] = None) -> int:
    """キャッシュ無効化ヘルパー"""
    return cache_manager.invalidate(cache_type, pattern)


def get_cache_stats() -> Dict[str, Any]:
    """キャッシュ統計取得ヘルパー"""
    return cache_manager.get_overall_stats()