import time
from typing import Any, Tuple

class CacheStrategy:
    def __init__(self):
        self.cache = {}
        self.capacity = 100  # Example capacity

    def get(self, key: str) -> Any:
        raise NotImplementedError

    def put(self, key: str, value: Any):
        raise NotImplementedError

    def refresh(self, key: str):
        raise NotImplementedError

class LRUCache(CacheStrategy):
    def get(self, key: str) -> Any:
        if key in self.cache:
            self.cache[key] = self.cache.pop(key)  # Move to end to mark as recently used
            return self.cache[key][0]  # Return the image data
        return None

    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.pop(next(iter(self.cache)))  # Remove oldest
        self.cache[key] = (value, time.time())  # Insert as the most recently used

    def refresh(self, key: str):
        if key in self.cache:
            self.cache[key] = self.cache.pop(key)  # Refresh in cache by accessing

class LFUCache(CacheStrategy):
    def __init__(self):
        super().__init__()
        self.freq = {}  # Stores frequency of accesses

    def get(self, key: str) -> Any:
        if key not in self.cache:
            return None
        freq = self.freq[key]
        self.freq[key] = freq + 1
        return self.cache[key][0]

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity and key not in self.cache:
            least_freq = min(self.freq.values())
            least_freq_keys = [k for k, v in self.freq.items() if v == least_freq]
            oldest_key = min(least_freq_keys, key=lambda k: self.cache[k][1])
            self.cache.pop(oldest_key)
            self.freq.pop(oldest_key)
        self.cache[key] = (value, time.time())
        self.freq[key] = self.freq.get(key, 0) + 1

    def refresh(self, key: str):
        if key in self.cache:
            self.get(key)  # Implicitly refreshes by accessing
