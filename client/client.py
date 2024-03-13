# Verteiltes Caching-System mit Konsistenzgewährleistung für Bilddaten
#
# Client-Anteil:
# • Anfrage und Empfang von Bilddaten: Implementieren Sie Client-Funktionen zum
# Anfordern von Bildern aus dem Cache. Bei einem Cache-Miss sollte die Anfrage an das
# Backend-System weitergeleitet werden, um das Bild zu holen und im Cache zu speichern.
# • Cache-Aktualisierung: Entwickeln Sie Mechanismen, mit denen der Client über
# Änderungen an bereits angeforderten Bildern informiert wird, um sicherzustellen, dass
# stets die aktuellsten Versionen der Bilder angezeigt werden.
#
# Bewertung:
# • Cache-Effizienz: Bewerten Sie die Trefferquote des Caches und die Auswirkungen auf die
# Latenzzeiten beim Abrufen von Bildern. Analysieren Sie, wie effektiv das Caching-System
# die Backend-Belastung reduziert.
# • Konsistenz und Aktualität: Untersuchen Sie, wie konsistent das System
# Bildaktualisierungen handhabt und wie schnell geänderte Bilder den Clients zur Verfügung
# gestellt werden.
# • Ausfallsicherheit und Skalierbarkeit: Bewerten Sie die Robustheit des Systems
# gegenüber Ausfällen und die Fähigkeit des Systems, seine Leistung durch Hinzufügen
# weiterer Ressourcen linear zu skalieren.
# Anforderungen:
# • Schneller Zugriff auf Bilddaten: Das System sollte in der Lage sein, Bilddaten mit
# minimaler Latenz bereitzustellen, um eine reibungslose Benutzererfahrung zu
# gewährleisten, wobei die maximale Antwortzeit für das Abrufen eines Bildes aus dem
# Cache klar definiert sein sollte.
# • Garantierte Bildaktualität: Änderungen an Bildern müssen im gesamten System
# konsistent nachvollzogen werden, sodass Benutzer stets die aktuellsten Versionen sehen.
# Strategien zur Cache-Invalidierung oder -Aktualisierung müssen effektiv implementiert
# werden, um veraltete Daten zu vermeiden.
# • Robustheit und Skalierbarkeit: Das System muss hohe Verfügbarkeit gewährleisten und
# die Fähigkeit besitzen, sich an steigende Lasten anzupassen, ohne dass es zu einem
# signifikanten Leistungsabfall kommt. Dies beinhaltet Mechanismen zur schnellen Erholung
# von Serverausfällen und zur dynamischen Lastverteilung.
#
#
# the images are requested (eah image has an id)
# the server informs the client about changes to the images (with image ID of the changed image),
# so the client can update the cache


import aiohttp
import logging
from typing import Optional
from client.cache import CacheStrategy


logging.basicConfig(level=logging.INFO)


class Client:
    def __init__(self, backend_server_url: str, strategy: CacheStrategy, debug_local: bool = False):
        self.backend_server_url = backend_server_url
        self.debug_local = debug_local
        self.strategy = strategy
        self.cache_hits = 0
        self.cache_misses = 0
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def request_image(self, image_id: str) -> bytes:
        image_data = self.strategy.get(image_id)
        if image_data:
            self.cache_hits += 1
            return image_data
        else:
            self.cache_misses += 1
            return await self.fetch_from_backend(image_id)

    async def fetch_from_backend(self, image_id: str) -> bytes:
        if self.debug_local:
            image_path = f"{self.backend_server_url}/test_{image_id}.jpeg"

            try:
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()

                self.strategy.put(image_id, image_data)
                return image_data

            except Exception as e:
                logging.error(f"Failed to fetch image {image_id} from local debug: {e}")
                raise

        else:
            if not self.session:
                raise RuntimeError("Session not initialized.")
            try:
                async with self.session.get(f"{self.backend_server_url}/images/{image_id}") as response:
                    response.raise_for_status()  # Ensure we handle non-2xx responses
                    image_data = await response.read()

                    self.strategy.put(image_id, image_data)
                    return image_data
            except aiohttp.ClientError as e:
                logging.error(f"Failed to fetch image {image_id} from backend: {e}")
                raise

    def should_cache_image(self) -> bool:
        return len(self.strategy.cache) < self.strategy.capacity

    async def listen_for_updates(self):
        # deactivate when running locally
        if self.debug_local:
            return

        if not self.session:
            raise RuntimeError("Session not initialized.")
        async with self.session.get(f"{self.backend_server_url}/events") as response:
            async for line in response.content:
                if line.startswith(b"data:"):
                    image_id = line.decode().strip().removeprefix("data:").strip()
                    await self.fetch_from_backend(image_id)

    def set_strategy(self, strategy: CacheStrategy):
        self.strategy = strategy
        self.cache_hits, self.cache_misses = 0, 0

    def evaluate_performance(self):
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            logging.info("No requests made yet.")
            return
        hit_rate = (self.cache_hits / total_requests) * 100
        logging.info(f"Cache Hit Rate: {hit_rate:.2f}%")
        logging.info(f"Cache Miss Rate: {100 - hit_rate:.2f}%")
        logging.info(f"Total Requests: {total_requests}")
        logging.info(f"Cache Hits: {self.cache_hits}")
        logging.info(f"Cache Misses: {self.cache_misses}")
