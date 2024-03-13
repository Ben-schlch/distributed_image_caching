# This is the python script that finally emulates the user which uses the client to download images from server cluster


# goal is it to make optimal caching on client and server side
# e.g. caching strategy, hit-rate, etc.

from client.client import Client
from client.cache import LRUCache, LFUCache, FIFO, RandomReplacement
import random
import matplotlib.pyplot as plt
import numpy as np
import asyncio

# import matplotlib
# matplotlib.use('TkAgg')


# Configuration
random.seed(44)  # For reproducibility
total_requests = 50000
image_id_range = (0, 9999)
distributions = {
    "gaussian": {"mean": 5000, "std": 1200},
    "random": {"low": image_id_range[0], "high": image_id_range[1] + 1},
    "exponential": {"scale": 1600, "offset": 0}
}


def generate_image_id(distribution_name, params):
    """Generate an image ID based on the specified distribution."""
    result = 0
    if distribution_name == "gaussian":
        result = int(random.gauss(params["mean"], params["std"]))
    elif distribution_name == "random":
        result = random.randint(params["low"], params["high"])
    elif distribution_name == "exponential":
        result = int(random.expovariate(1 / params["scale"])) + params["offset"]

    image_id_generated = result if image_id_range[0] <= result <= image_id_range[1] else 0
    return image_id_generated


async def simulate_requests(client, distribution_name, params):
    """Simulate requests for a given client and distribution."""
    hit_rates = []
    for _ in range(total_requests):
        image_id = generate_image_id(distribution_name, params)
        # Ensure image ID is within valid range
        image_id = str(max(min(image_id, image_id_range[1]), image_id_range[0]))
        await client.request_image(image_id)
        hit_rate = client.cache_hits / (client.cache_hits + client.cache_misses)
        hit_rates.append(hit_rate)
    return hit_rates


async def main():
    backend_url = r"C:\Users\bensc\Projects\verteilte_system\images"  # Example backend URL
    clients = {
        "LFU": Client(backend_url, LFUCache(), debug_local=True),
        "LRU": Client(backend_url, LRUCache(), debug_local=True),
        "FIFO": Client(backend_url, FIFO(), debug_local=True),
        "RR": Client(backend_url, RandomReplacement(), debug_local=True)
    }

    # Simulate requests and plot results
    for distribution_name, params in distributions.items():
        plt.clf()
        plt.figure(figsize=(10, 6))

        for name, client in clients.items():
            client.cache = {}
            client.cache_hits = 0
            client.cache_misses = 0
            hit_rates = await simulate_requests(client, distribution_name, params)
            plt.plot(hit_rates, label=name)

        plt.xlabel('Request Count')
        plt.ylabel('Cache Hit Rate')
        plt.title(f'Cache Hit Rate over Time by Strategy with {distribution_name.capitalize()} Distribution')
        plt.legend()
        plt.show()


asyncio.run(main())
