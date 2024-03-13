import random
import time
from typing import Any, Tuple


class CacheStrategy:
    def __init__(self, ttl=None):
        self.cache = {}
        self.capacity = 1000  # Default capacity
        self.ttl = ttl  # Time to live in seconds

    def is_expired(self, key: str) -> bool:
        if self.ttl is None or key not in self.cache:
            return False
        _, timestamp = self.cache[key]
        return (time.time() - timestamp) > self.ttl

    def get(self, key: str) -> Any:
        raise NotImplementedError

    def put(self, key: str, value: Any):
        raise NotImplementedError


class LRUCache(CacheStrategy):

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            self.cache[key] = self.cache.pop(key)  # Move to end to mark as recently used
            return self.cache[key][0]  # Return the value
        elif key in self.cache and self.is_expired(key):
            # Remove expired item
            self.cache.pop(key)
        return None

    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.pop(next(iter(self.cache)))  # Remove oldest
        self.cache[key] = (value, time.time())  # Insert with current timestamp


class LFUCache(CacheStrategy):
    def __init__(self, ttl=None):
        super().__init__(ttl)
        self.freq = {}

    def get(self, key: str) -> Any:
        if key not in self.cache or self.is_expired(key):
            return None
        freq = self.freq[key]
        self.freq[key] = freq + 1
        return self.cache[key][0]

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity and key not in self.cache:
            self.evict()
        self.cache[key] = (value, time.time())
        self.freq[key] = self.freq.get(key, 0) + 1

    def evict(self):
        least_freq = min(self.freq.values())
        least_freq_keys = [k for k, v in self.freq.items() if v == least_freq]
        for key in least_freq_keys:
            if self.is_expired(key):
                self.cache.pop(key)
                self.freq.pop(key)
                return  # Remove only one expired item at a time
        # Remove the least frequently used item that's not expired
        oldest_key = min(least_freq_keys, key=lambda k: self.cache[k][1])
        self.cache.pop(oldest_key)
        self.freq.pop(oldest_key)


# another example of a cache strategy could be: Random Replacement (RR),
# which would randomly replace an item in the cache when it's full.

class RandomReplacement(CacheStrategy):
    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            return self.cache[key][0]
        elif key in self.cache and self.is_expired(key):
            self.cache.pop(key)  # Remove expired item
        return None

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity:
            key_to_remove = random.choice(list(self.cache.keys()))
            self.cache.pop(key_to_remove)
        self.cache[key] = (value, time.time())


# another example of a cache strategy could be: First In First Out (FIFO),
# which would replace the oldest item in the cache when it's full.

class FIFO(CacheStrategy):
    def __init__(self, ttl=None):
        super().__init__(ttl)
        self.queue = []

    def get(self, key: str) -> Any:
        if key in self.cache and not self.is_expired(key):
            return self.cache[key][0]
        elif key in self.cache and self.is_expired(key):
            self.cache.pop(key)  # Remove expired item
            self.queue.remove(key)  # Remove key from queue
        return None

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity:
            key_to_remove = self.queue.pop(0)
            self.cache.pop(key_to_remove)
        self.cache[key] = (value, time.time())
        self.queue.append(key)
