import random
import time
from typing import Any


class CacheStrategy:
    def __init__(self, ttl=None):
        self.cache = {}  # Cache storage for key-value pairs
        self.capacity = 1000  # Default cache capacity
        self.ttl = ttl  # Time-to-live in seconds for each cache item

    def is_expired(self, key: str) -> bool:
        """Check if a cached item has expired based on TTL."""
        if self.ttl is None or key not in self.cache:
            return False
        _, timestamp = self.cache[key]
        return (time.time() - timestamp) > self.ttl

    def get(self, key: str) -> Any:
        """Retrieve an item from the cache."""
        raise NotImplementedError

    def put(self, key: str, value: Any):
        """Add or update an item in the cache."""
        raise NotImplementedError



class LRUCache(CacheStrategy):
    """Least Recently Used (LRU) Cache Implementation."""

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            value, _ = self.cache.pop(key)
            self.cache[key] = (value, time.time())  # Update timestamp
            return value
        elif key in self.cache:
            self.cache.pop(key)  # Remove expired item
        return None

    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.pop(next(iter(self.cache)))  # Remove the least recently used item
        self.cache[key] = (value, time.time())  # Insert item with current timestamp


class LFUCache(CacheStrategy):
    """Least Frequently Used (LFU) Cache Implementation."""

    def __init__(self, ttl=None):
        super().__init__(ttl)
        self.freq = {}  # Frequency of accesses for each cache item

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            self.freq[key] += 1
            return self.cache[key][0]
        elif key in self.cache:
            self.cache.pop(key)  # Remove expired item
            self.freq.pop(key)
        return None

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity and key not in self.cache:
            self.evict()  # Evict the least frequently used item
        self.cache[key] = (value, time.time())  # Insert item with current timestamp
        self.freq[key] = self.freq.get(key, 0) + 1

    def evict(self):
        """Remove the least frequently used item."""
        least_freq = min(self.freq.values())
        least_freq_keys = [k for k, v in self.freq.items() if v == least_freq]
        oldest_key = min(least_freq_keys, key=lambda k: self.cache[k][1])
        self.cache.pop(oldest_key)
        self.freq.pop(oldest_key)


class RandomReplacement(CacheStrategy):
    """Random Replacement (RR) Cache Implementation."""

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            return self.cache[key][0]
        elif key in self.cache:
            self.cache.pop(key)  # Remove expired item
        return None

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity:
            key_to_remove = random.choice(list(self.cache.keys()))
            self.cache.pop(key_to_remove)  # Remove a random item
        self.cache[key] = (value, time.time())  # Insert item with current timestamp


class FIFO(CacheStrategy):
    """First In First Out (FIFO) Cache Implementation."""

    def __init__(self, ttl=None):
        super().__init__(ttl)
        self.queue = []  # Queue to keep track of the insertion order

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            return self.cache[key][0]
        elif key in self.cache:
            self.cache.pop(key)  # Remove expired item
            self.queue.remove(key)  # Also remove from the queue
        return None

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity:
            while self.queue:
                oldest_key = self.queue.pop(0)  # Remove the oldest item
                if oldest_key in self.cache:
                    self.cache.pop(oldest_key)
                    break
        self.cache[key] = (value, time.time())  # Insert item with current timestamp
        self.queue.append(key)  # Remember the insertion order
