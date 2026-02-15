#Explicații cheie:
#Tokenul e acelasi pentru toate fragmentele -> clientul stie ca fac parte din aceeasi sesiune.
#Fiecare fragment are MID unic -> serverul poate trimite NON fără riscul de conflict.
#fragment_count -> ordinea fragmentului in sesiune (incepe de la 1).
#is_last_fragment -> 1 pentru ultimul fragment, 0 pentru restul.
#payload_size -> dimensiunea totala a conținutului (nu fragmentul individual).
#Mesajele sunt NON -> pentru GET/LS mari, dupa ce am trimis ACK gol daca cererea era CON.

import threading
from server.coap_parser import CoAPMessage, Header
from server.payload import payload_instance, content_instance


class Fragmenter:
    def __init__(self, max_payload_size=512):
        self.max_payload_size = max_payload_size
        self.lock = threading.Lock()
        self.next_mid = 1000  # start pentru message_id-uri unice

    def _get_next_mid(self):
        with self.lock:
            mid = self.next_mid
            self.next_mid += 1
        return mid

    # full_content: continutul complet (string) de trimis
    # token: tokenul original al cererii
    # file_name, folder_path, file_type: info necesare pentru payload
    # code: codul CoAP (implicit 2.05 Content)

    # returneaza lista de CoAPMessage NON gata de trimis
    def create_fragments(self, full_content: str, token: bytes, file_name: str,
                         folder_path: str, file_type: str, code: int = 69):

        content_bytes = full_content.encode("utf-8")
        total_size = len(content_bytes)
        fragments = []

        # aceasta formula simuleaza impartirea cu rotunjire in sus (ceil) folosind doar operatii pe intregi
        num_fragments = (total_size + self.max_payload_size - 1) // self.max_payload_size

        for i in range(num_fragments):
            start = i * self.max_payload_size
            end = min(start + self.max_payload_size, total_size)
            chunk = content_bytes[start:end]

            # flagurile fragmentului
            is_last = 1 if i == num_fragments - 1 else 0
            fragment_count = i + 1  # incepe de la 1

            # cream payload-ul pentru fragment
            ## aici se folosesc functiile din payload.py pentru a crea json-ul
            frag_content = content_instance(
                file_name=file_name,
                payload_size=len(chunk),  # dimensiunea completa a mesajului
                file_content=chunk.decode("utf-8"),
                fragment_count=fragment_count,
                is_last_fragment=is_last
            )
            frag_payload = payload_instance(folder_path, file_type, frag_content)

            # Cream header-ul CoAPMessage
            header = Header(
                version=1,
                msg_type=1,  # NON
                tkl=len(token),
                code=code,  # CoAP code pentru content
                mid=self._get_next_mid(),
                token=token
            )

            # Adaugam mesajul la listă
            fragments.append(CoAPMessage(header, frag_payload))

        return fragments
