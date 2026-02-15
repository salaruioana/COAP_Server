# aici sunt functiile pentru gestionarea cozii de pachete care pot fi retransmise in caz de cereri duplicate
# message id este folosit drept cheie a dictionarului de mesaje
import time
from dataclasses import dataclass
import threading

# primeste cereri si verifica daca acestea au fost deja procesate
# daca da, trimite raspunsul din coada
# daca nu, trimite cererea spre procesare la process_thread

EXCHANGE_LIFETIME = 247 #secunde
CLEANUP_INTERVAL = EXCHANGE_LIFETIME

@dataclass
class RecentResponse:
    message_id: int
    message: bytes
    expire_time: float

#cache va fi un dictionar cu cheia = message_id si valoarea = continutul mesajului
class Cache:
    def __init__(self):
        self.recent_cache = {}
        #deoarece mai multe thread-uri pot folosi in paralel instanta Cache, este necesar ca operatiile sa fie facute cu lock-uri pentru a evita inconsistentele
        self.lock = threading.Lock()

        # pornește thread-ul de cleanup
        self.cleanup_thread = threading.Thread(
            target=self._auto_cleanup,
            daemon=True
        )
        self.cleanup_thread.start()

    def add(self,message_id,message: bytes):
        expire_time = time.time() + EXCHANGE_LIFETIME
        with self.lock:
            self.recent_cache[message_id] = RecentResponse(message_id,message,expire_time)

    def get(self,message_id):
        with self.lock:
            entry = self.recent_cache.get(message_id)
            if entry is None:
                return None
            if time.time() > entry.expire_time:
                del self.recent_cache[message_id]
                return None

            return entry.message

    def remove(self,message_id):
        with self.lock:
            if message_id in self.recent_cache:
                del self.recent_cache[message_id]

    def cleanup_cache(self):
        now = time.time()
        expired_keys=[message_id
                    for message_id, entry in self.recent_cache.items()
                    if entry.expire_time <= now]

        for mid in expired_keys:
            del self.recent_cache[mid]

    # ruleaza in background, curata periodic cache-ul
    def _auto_cleanup(self):
        while True:
            time.sleep(CLEANUP_INTERVAL)
            with self.lock:
                self.cleanup_cache()
