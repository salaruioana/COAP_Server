import threading
import time
from coap_parser import CoAPMessage

# dictionar cu cheia token si valoarea lista de fragmente primite in acea sesiune
# il folosim pentru stocarea fragmentelor pana cand le-am primit pe toate - apoi le asamblam si continuam procesarea
class FragmentBuffer:
    def __init__(self, fragment_timeout=300):
        self.buffer = {}
        self.lock = threading.Lock()
        self.fragment_timeout = fragment_timeout

        # Cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._auto_cleanup,
            daemon=True
        )
        self.cleanup_thread.start()

    def _auto_cleanup(self):
        while True:
            time.sleep(60)
            now = time.time()
            with self.lock:
                expired = [
                    token for token, data in self.buffer.items()
                    if now - data["last_update"] > self.fragment_timeout
                ]
                for token in expired:
                    print(f"[FragmentBuffer] Timeout pentru token {token.hex()}")
                    del self.buffer[token]

    def store_fragment(self, coapm: CoAPMessage):
        token_key = coapm.header.token
        content = coapm.payload.content

        with self.lock:
            if token_key not in self.buffer:
                self.buffer[token_key] = {
                    "fragments": [],
                    "is_last_received": False,
                    "header_info": coapm.header
                }
            self.buffer[token_key]["fragments"].append(content)

            # ne asiguram ca este ultimul pachet si ca s-au primit toate pachetele anterioare
            if content.is_last_fragment == 1:
                self.buffer[token_key]["is_last_received"] = True
                self.buffer[token_key]["total_fragments"] = content.fragment_count
            # if self.buffer[token_key]["total_fragments"] and len(self.buffer[token_key]["fragments"]) ==  self.buffer[token_key]["total_fragments"]:
            #     return True
                return True
            return False

    def assemble(self, token_key):
        with self.lock:
            if token_key not in self.buffer:
                return None, None
            data = self.buffer[token_key]["fragments"]
            # sortam dupa fragment_count
            data_sorted = sorted(data, key=lambda x: x.fragment_count)
            # verificam daca avem totalul corect de fragmente
            expected_count = data_sorted[-1].fragment_count if data_sorted else 0
            if len(data_sorted) != expected_count:
                # Lipsesc fragmente
                return None, None
            #verificam daca sunt toate care trebuie
            for i, frag in enumerate(data_sorted, start=1):
                if frag.fragment_count != i:
                    return None, None
            # concatenam continutul -obs: nu se gestioneaza cazul in care lipsesc fragmente (pierderi)
            ## - oare ar fi complicat de gestionat?
            full_content = "".join(f.file_content for f in data_sorted)
            header = self.buffer[token_key]["header_info"]
            # stergem buffer-ul dupa asamblare
            del self.buffer[token_key]
        return full_content, header


#La primirea unui fragment POST CON:
# 1. Trimitem imd ACK gol sa confirmam primirea cererii
# 2. Stocam fragmentul in Fragment Buffer
# 3. Dupa ce primim toate fragmentele procesam si facem post efectiv
# 4. Trimitem ack cu cod corespunzator daca operatia de post s-a efectuat cu succes