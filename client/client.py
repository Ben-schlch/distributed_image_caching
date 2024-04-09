import aiohttp
import logging
import time
import asyncio
from typing import Optional, Tuple
from client.cache import CacheStrategy

logging.basicConfig(level=logging.INFO)

class Client:
    def __init__(self, backend_server_urls: list, strategy: CacheStrategy, debug_local: bool = False):
        self.backend_server_urls = backend_server_urls  # A list of URLs for the Raspberry Pis
        self.current_server_index = 0  # Track the current server for requests
        self.debug_local = debug_local
        self.strategy = strategy
        self.cache_hits = 0
        self.cache_misses = 0
        self.session: Optional[aiohttp.ClientSession] = None
        # Attributes for response times
        self.local_response_times = []
        self.server_response_times = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def request_image(self, image_id: str) -> Tuple[bytes, float]:
        start_time = time.time()
        image_data = self.strategy.get(image_id)
        if image_data:
            self.cache_hits += 1
            response_time = time.time() - start_time
            self.local_response_times.append(response_time)
            return image_data, response_time
        else:
            self.cache_misses += 1
            image_data, response_time = await self.fetch_from_backend(image_id)
            self.server_response_times.append(response_time)
            return image_data, response_time

    async def fetch_from_backend(self, image_id: str) -> Tuple[bytes, float]:
        attempts = 0
        while attempts < len(self.backend_server_urls):
            start_time = time.time()
            server_url = self.backend_server_urls[self.current_server_index]
            try:
                if self.debug_local:
                    # Simulate fetching by getting images from local file path:
                    with open(f"{server_url}/test_{image_id}.JPEG", "rb") as f:
                        image_data = f.read()
                        self.strategy.put(image_id, image_data)
                        return image_data, time.time() - start_time

                else:
                    async with self.session.get(f"{server_url}/images/{image_id}") as response:
                        response.raise_for_status()
                        image_data = await response.read()
                        self.strategy.put(image_id, image_data)
                        return image_data, time.time() - start_time
            except (aiohttp.ClientError, NotImplementedError):
                attempts += 1
                if attempts >= len(self.backend_server_urls) * 3:
                    logging.error("All backend servers failed to respond 3 times. Aborting.")
                    raise

                elif attempts >= len(self.backend_server_urls):
                    logging.info("All backend servers failed to respond. Back off for 2 ** attempts ms.")
                    await asyncio.sleep(2 ** attempts / 1000)
                self.current_server_index = (self.current_server_index + 1) % len(self.backend_server_urls)
                # Log and possibly wait before retrying
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                raise  # Or handle as appropriate
        raise ConnectionError("Failed to fetch image from all backend servers.")

    async def start_listening_to_updates(self):
        tasks = []
        for server_url in self.backend_server_urls:
            task = asyncio.create_task(self.listen_for_updates(server_url))
            tasks.append(task)
        await asyncio.gather(*tasks)

    async def listen_for_updates(self, server_url):
        if self.debug_local:
            return  # Skip in debug mode

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{server_url}/events", headers={'Accept': 'text/event-stream'}) as response:
                while True:
                    line = await response.content.readline()
                    if not line:
                        break
                    data = line.decode().strip()
                    if data.startswith("data:"):
                        image_id = data.removeprefix("data:").strip()
                        if image_id in self.strategy.cache.keys():
                            self.strategy.cache[image_id] = self.fetch_from_backend(image_id)

    def set_strategy(self, strategy: CacheStrategy):
        self.strategy = strategy
        self.cache_hits, self.cache_misses = 0, 0

    def evaluate_performance(self):
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            logging.info("No requests made yet.")
            return
        hit_rate = (self.cache_hits / total_requests) * 100
        avg_local_response_time = sum(self.local_response_times) / len(self.local_response_times) if self.local_response_times else 0
        avg_server_response_time = sum(self.server_response_times) / len(self.server_response_times) if self.server_response_times else 0
        logging.info(f"Cache Hit Rate: {hit_rate:.2f}%")
        logging.info(f"Cache Miss Rate: {100 - hit_rate:.2f}%")
        logging.info(f"Total Requests: {total_requests}")
        logging.info(f"Cache Hits: {self.cache_hits}")
        logging.info(f"Cache Misses: {self.cache_misses}")
        logging.info(f"Average Local Response Time: {avg_local_response_time:.4f} seconds")
        logging.info(f"Average Server Response Time: {avg_server_response_time:.4f} seconds")
