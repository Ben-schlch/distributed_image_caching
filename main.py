# This is the python script that finally emulates the user which uses the client to download images from server cluster


# goal is it to make optimal caching on client and server side
# e.g. caching strategy, hit-rate, etc.

from client.client import Client
from client.cache import LRUCache, LFUCache, FIFO, RandomReplacement
import random
import matplotlib.pyplot as plt
import numpy as np
import asyncio
from tqdm import tqdm

# import matplotlib
# matplotlib.use('TkAgg')

# set logging level to INFO
import logging

logging.basicConfig(level=logging.INFO)

# Configuration
random.seed(42)  # For reproducibility
total_requests = 1000
image_id_range = (1, 9999)
# intitalize array for image id range with all zeros
image_request_count = np.zeros(image_id_range[1] + 1)

# backend_urls = [r"C:\Users\bensc\Projects\verteilte_system\images"]  # local debug
backend_urls = [r"10.8.0.1:8002", "10.8.0.2:8002"]  # local debug

distributions = {
    "gaussian": {"mean": 5000, "std": 1200, "image_request_count": image_request_count.copy()},
    "random": {"low": image_id_range[0], "high": image_id_range[1],
               "image_request_count": image_request_count.copy()},
    "exponential": {"scale": 1200, "offset": 1, "image_request_count": image_request_count.copy()}
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

    # if distribution_name == "random":
    #     if result > image_id_range[1]:
    #         print("x")
    image_id_generated = result if image_id_range[0] <= result <= image_id_range[1] else 1
    return image_id_generated


async def simulate_requests(client, distribution_name, params):
    """Simulate requests for a given client and distribution."""
    hit_rates = []
    for _ in tqdm(range(total_requests), total=total_requests, desc=f"Simulating requests for {distribution_name}"):
        image_id = generate_image_id(distribution_name, params)
        # Ensure image ID is within valid range
        image_id = str(max(min(image_id, image_id_range[1]), image_id_range[0]))

        await client.request_image(image_id)
        hit_rate = client.cache_hits / (client.cache_hits + client.cache_misses)
        hit_rates.append(hit_rate)
        params["image_request_count"][int(image_id)] += 1

    return hit_rates


async def main():
    server_response_times = []

    clients = {
        "LFU": Client(backend_urls, LFUCache(), debug_local=False),
        "LRU": Client(backend_urls, LRUCache(), debug_local=False),
        "FIFO": Client(backend_urls, FIFO(), debug_local=False),
        "RR": Client(backend_urls, RandomReplacement(), debug_local=False)
    }
    #tasks = [asyncio.create_task(client.start_listening_to_updates()) for client in clients.values()]
    # Simulate requests and plot results
    for distribution_name, params in distributions.items():
        plt.clf()
        plt.figure(figsize=(10, 6))

        for name, client in clients.items():
            task = asyncio.create_task(client.start_listening_to_updates())
            client.strategy.cache = {}
            client.cache_hits = 0
            client.cache_misses = 0
            client.local_response_times = []
            client.server_response_times = []
            if not client.debug_local:
                async with client as async_cm:
                    hit_rates = await simulate_requests(async_cm, distribution_name, params)
            else:
                hit_rates = await simulate_requests(client, distribution_name, params)
            plt.plot(hit_rates, label=name)

            server_response_times.append(client.server_response_times)

            print(f"{distribution_name} - {name} - Simulating requests complete")
            client.evaluate_performance()
            print("\n\n")
            client.listening_for_updates = False
            await task

        plt.xlabel('Request Count')
        plt.ylabel('Cache Hit Rate')
        plt.title(f'Cache Hit Rate over Time by Strategy with {distribution_name.capitalize()} Distribution')
        plt.legend()
        plt.show()

        # Plot image request count for each distribution
        plt.clf()
        plt.figure(figsize=(10, 6))
        plt.plot(params["image_request_count"])
        plt.xlabel('Image ID')
        plt.ylabel('Request Count')
        plt.title(f'Image Request Count for {distribution_name.capitalize()} Distribution')
        plt.show()

    # boxplot of server response times across all distributions and client caching strategies
    plt.clf()
    plt.figure(figsize=(10, 6))
    plt.boxplot(server_response_times)
    plt.title('Server Response Times in ms across all tested distributions and client caching strategies')


asyncio.run(main())
