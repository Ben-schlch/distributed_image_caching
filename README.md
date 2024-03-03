# Distributed caching system with consistency guarantee for image data

## Client share:
- Request and receive image data: Implement client functions to request images from the cache. In case of a cache miss, the request should be forwarded to the backend system to fetch the image and store it in the cache.
- Cache refresh: Develop mechanisms to inform the client about changes to already requested images.
changes to previously requested images to ensure that the latest versions of the images are always displayed.

## Cluster share:
- Efficient caching and storage: Design the caching system in such a way that
image data can be stored efficiently and made available quickly when required.
Consider techniques to reduce storage requirements, such as compression or deduplication.
- Consistency mechanisms: Implement consistency mechanisms that
ensure that all clients always receive the latest version of an image, even if it has been changed recently. This could be done by invalidating cache entries,
versioning of image data or other consistency protocols.
- Fail-safe and scalable: The caching system should be fail-safe and
offer the option of adding additional cache servers as the volume of requests increases or to improve reliability.

## Evaluation:
- Cache efficiency: Evaluate the hit rate of the cache and the impact on latency when retrieving images. Analyze how effectively the caching system reduces backend load.
- Consistency and timeliness: Examine how consistently the system handles image updates and how quickly changed images are made available to clients.
- Resilience and scalability: Evaluate the robustness of the system against
to failures and the ability of the system to scale its performance linearly by adding more resources.
Requirements:
- Fast access to image data: The system should be able to provide image data with
minimal latency to ensure a smooth user experience, with a clearly defined maximum response time for retrieving an image from the cache.
- Guaranteed image freshness: Changes to images must be tracked consistently throughout the
consistently throughout the system so that users always see the latest versions. Cache invalidation or refresh strategies must be effectively implemented to avoid outdated data.
- Robustness and scalability: The system must ensure high availability and have the ability to adapt to increasing loads without a significant drop in performance. This includes mechanisms for rapid recovery from server failures and dynamic load balancing.
