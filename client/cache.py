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
        # timestamp is the last element in the tuple of between 2 and 3 elements
        if len(self.cache[key]) == 2:
            _, timestamp = self.cache[key]
        else:
            _, timestamp, _ = self.cache[key]
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

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            value, timestamp, freq = self.cache[key]
            self.cache[key] = (value, timestamp, freq + 1)  # Increment frequency
            return value
        elif key in self.cache:
            self.cache.pop(key)  # Remove expired item
        return None

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity and key not in self.cache:
            self.evict()  # Evict the least frequently used item
        timestamp = time.time()
        self.cache[key] = (value, timestamp, 1)  # Initialize with frequency 1

    def evict(self):
        """Remove the least frequently used item."""
        min_freq_key = min(self.cache, key=lambda k: self.cache[k][2])  # Find min frequency key
        self.cache.pop(min_freq_key)


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
