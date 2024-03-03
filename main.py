# This is the python script that finally emulates the user which uses the client to download images from server cluster

# goal is it to make optimal caching on client and server side
# e.g. caching strategy, hit-rate, etc.

from client.client  import Client

from client.cache import LRUCache, LFUCache


async def main():
    backend_url = "http://backend-server.com"  # Example backend URL
    client = Client(backend_url, LRUCache())  # Start with LRU cache strategy

    # Simulate requesting images
    image_ids = ['image1', 'image2', 'image3', 'image4', 'image5']
    for image_id in image_ids:
        await client.request_image(image_id)
        print(f"Requested {image_id} with LRU strategy.")

    # Evaluate performance (example)
    print("Evaluating performance with LRU strategy...")
    client.evaluate_performance()  # This method should be implemented to print cache hits and misses

    # Switch to LFU cache strategy
    client.set_strategy(LFUCache())
    print("Switched to LFU cache strategy.")

    # Simulate requesting more images, including some previously requested
    more_image_ids = ['image3', 'image6', 'image2', 'image7', 'image3']
    for image_id in more_image_ids:
        await client.request_image(image_id)
        print(f"Requested {image_id} with LFU strategy.")

    # Evaluate performance again
    print("Evaluating performance with LFU strategy...")
    client.evaluate_performance()  # Evaluate cache performance again after switching strategy

    await client.close()  # Close the client session

# Run the main function to execute the example
asyncio.run(main())
