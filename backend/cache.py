"""
Music Chords App - Cache Module
In-memory cache with TTL for search results.
"""
import asyncio
import time
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict
from dataclasses import dataclass, field

from config import get_settings
from models import SearchResponse, CacheEntry

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self.stats = CacheStats()
    
    def _generate_key(self, request_dict: Dict[str, Any]) -> str:
        """Generate cache key from request parameters."""
        # Sort keys for consistent hashing
        import json
        sorted_items = sorted(request_dict.items())
        return f"chords:{hash(json.dumps(sorted_items, sort_keys=True))}"
    
    async def get(self, key: str) -> Optional[SearchResponse]:
        """Get value from cache if not expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self.stats.misses += 1
                return None
            
            # Check expiration
            if time.time() > entry.expires_at.timestamp():
                del self._cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self.stats.hits += 1
            return entry.value
    
    async def set(self, key: str, value: SearchResponse, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        async with self._lock:
            # Remove expired entries first
            await self._cleanup_expired()
            
            # Evict LRU if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self.stats.evictions += 1
            
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            from datetime import datetime
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=datetime.fromtimestamp(expires_at)
            )
            self._cache[key] = entry
            self.stats.total_entries = len(self._cache)
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry.expires_at.timestamp()
        ]
        for key in expired_keys:
            del self._cache[key]
            self.stats.evictions += 1
        self.stats.total_entries = len(self._cache)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self.stats = CacheStats()
    
    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        async with self._lock:
            await self._cleanup_expired()
            self.stats.total_entries = len(self._cache)
            return self.stats


# Global cache instance
_cache_instance: Optional[LRUCache] = None


def get_cache() -> LRUCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LRUCache(
            max_size=settings.max_cache_size,
            default_ttl=settings.cache_ttl
        )
    return _cache_instance


async def cache_search_result(request_dict: Dict[str, Any], response: SearchResponse) -> None:
    """Cache a search result."""
    cache = get_cache()
    key = cache._generate_key(request_dict)
    await cache.set(key, response)


async def get_cached_search(request_dict: Dict[str, Any]) -> Optional[SearchResponse]:
    """Get cached search result if available."""
    cache = get_cache()
    key = cache._generate_key(request_dict)
    return await cache.get(key)