from cache import Cache
import coap_parser as coap_parser
from coap_builder import create_response
import coap_builder as coap_builder
from fragment_buffer import FragmentBuffer
from fragmenter import Fragmenter
import coap_methods
from payload import Payload, Content
from file_handler import list_files, read_file


#constante pentru lizibilitate
COAP_PUT = 3
COAP_GET = 1
COAP_LS = 5
COAP_CON = 0
COAP_NON = 1
COAP_ACK = 2


# instante globale care sa fie folosite in toate thread-urile
cache = Cache()
fragment_buffer = FragmentBuffer()
fragmenter = Fragmenter(max_payload_size=512)

def send_empty_ack(server_socket, coapm, addr):
    #trimite ACK gol pentru confirmarea primirii cererii CON.
    ack_bytes = coap_builder.build_ack_response(
        coap_parser.CoAPMessage(
            header=coap_parser.Header(
                coapm.header.version, COAP_ACK, coapm.header.tkl,
                0, coapm.header.mid, coapm.header.token
            ),
            payload=None
        )
    )
    server_socket.sendto(ack_bytes, addr)

def send_final_status(server_socket, token, response_code, addr):
    #Trimite mesaj NON cu status final.
    if token is None or len(token) == 0:
        print(f"[Receiver] Token invalid, nu pot trimite status final")
        return
    new_mid = fragmenter._get_next_mid()
    final_header = coap_parser.Header(
        1, COAP_NON, len(token),
        response_code, new_mid, token
    )
    final_message = coap_parser.CoAPMessage(final_header, payload=None)
    response_bytes = coap_builder.build_non_response(final_message)
    server_socket.sendto(response_bytes, addr)


def process_received(server_socket,data,addr):
    # apeleaza functia de procesat mesaje din clasa coapMessage
    # practic incearca sa converteasca sirul de bytes intr-un obiect de clasa CoapMessage pentru a lucra mai usor cu el
    try:
        coapm = coap_parser.parse_coap_message(data)
    except Exception as e:
        # handle error messages
        print(f"[Receiver] Pachet invalid de la {addr}: {e}")
        return
    # daca parsarea genereaza eroare, trimitem mesajul de eroare in consola

    # verificam dacă mesajul exista deja în cache
    cached_resp = cache.get(coapm.header.mid)
    if cached_resp :
        # mesajul e deja in cache, doar facem retransmisie
        print(f"[Receiver] Duplicat {coapm.header.mid}, retransmisie...")
        if isinstance(cached_resp, list):
            # trimite fiecare fragment
            for frag_bytes in cached_resp:
                server_socket.sendto(frag_bytes, addr)
        else:
            #trimite raspuns simplu
            server_socket.sendto(cached_resp, addr)
        return

    # gestionare put con/non
    if coapm.header.code == COAP_PUT: # PUT - trafic ce ar trebui fragmentat de la client
        if coapm.header.msg_type == COAP_CON:  # CON ->trebuie sa trimitem ack gol si apoi fragmentele
            send_empty_ack(server_socket, coapm, addr)

        # stocam fragmentul
        complete = fragment_buffer.store_fragment(coapm)

        # daca am primit toate fragmentele -> PUT efectiv
        if complete:
            full_content, header_info = fragment_buffer.assemble(coapm.header.token)

            if full_content is None:
                print(f"[Receiver] Eroare asamblare fragmente token={coapm.header.token.hex()}")
                send_final_status(server_socket, coapm.header.token, 160, addr)  # 5.00
                return

            # Construim payload pentru handle_coap()
            reconstructed_content = Content(
                file_name=coapm.payload.content.file_name,
                payload_size=len(full_content),
                file_content=full_content
            )
            reconstructed_payload = Payload(
                folder_path=coapm.payload.folder_path,
                file_type=coapm.payload.file_type,
                content=reconstructed_content
            )

            # folosim handle_coap() pentru a scrie fisierul
            response_code, _ = coap_methods.handle_coap(COAP_PUT, reconstructed_payload)

            # trimitem status final
            send_final_status(server_socket, coapm.header.token, response_code, addr)
            print(f"[Receiver] PUT fragmentat finalizat: {coapm.payload.content.file_name}")

        return
    if coapm.header.code in [COAP_GET, COAP_LS]: #GET sau LS - trafic ce ar trebui fragementat de la server
        # Lista pentru cache
        fragment_bytes_list = []
        if coapm.header.msg_type == COAP_CON: #CON -> trimitem empty ack si apoi fragmentele non
            #send_empty_ack(server_socket, coapm, addr)
            ack_bytes = coap_builder.build_ack_response(
                coap_parser.CoAPMessage(
                    header=coap_parser.Header(
                        coapm.header.version, COAP_ACK, coapm.header.tkl,
                        0, coapm.header.mid, coapm.header.token
                    ),
                    payload=None
                )
            )
            server_socket.sendto(ack_bytes, addr)
            fragment_bytes_list.append(ack_bytes)
        # Generam raspuns complet

        response_code, content = coap_methods.handle_coap(coapm.header.code, coapm.payload)
        if response_code >= 128:  # Cod de eroare
            send_final_status(server_socket, coapm.header.token, response_code, addr)
            return
        if isinstance(content, list):
            content = "\n".join(content)

        # Fragmentare și trimitere
        frag_msgs = fragmenter.create_fragments(
            full_content=content,
            token=coapm.header.token,
            file_name=coapm.payload.content.file_name,
            folder_path=coapm.payload.folder_path,
            file_type=coapm.payload.file_type,
            code=response_code  # Folosim codul returnat
        )
        fragment_bytes_list = []
        for frag in frag_msgs:
            frag_bytes = coap_builder.build_non_response(frag)
            server_socket.sendto(frag_bytes, addr)
            fragment_bytes_list.append(frag_bytes)

        # Adauga în cache lista de fragmente
        cache.add(coapm.header.mid, fragment_bytes_list)

        method_name = "GET" if coapm.header.code == COAP_GET else "LS"
        print(f"[Receiver] {method_name} fragmentat finalizat: {coapm.payload.content.file_name}")
        return

    # pentru celelalte cazuri
    response = create_response(coapm)
    server_socket.sendto(response, addr)
    cache.add(coapm.header.mid,response)