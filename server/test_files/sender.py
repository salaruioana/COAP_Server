import socket
from server.coap_parser import CoAPMessage
from server.payload import payload_encode
from server.coap_parser import parse_coap_message


def build_con_response(coapMessage: CoAPMessage):
    header = bytearray(4)
    # tip 2 = ACK
    header[0] = (coapMessage.header.version << 6) | (coapMessage.header.msg_type<<4) | coapMessage.header.tkl
    header[1] = coapMessage.header.code
    header[2] = (coapMessage.header.mid>>8) & 0xFF
    header[3] = coapMessage.header.mid & 0xFF

    if coapMessage.payload :
        return bytes(header) + coapMessage.header.token + bytes([0xFF]) + payload_encode(coapMessage.payload)
    else:
        return bytes(header) + coapMessage.header.token

def print_coap_message (coapMessage: CoAPMessage):
    print("Version:", coapMessage.header.version)
    #afisam msg type ca text
    msg_type_dict = {0: "CON", 1: "NON", 2: "ACK", 3: "RST"}
    msg_type_str = msg_type_dict.get(coapMessage.header.msg_type, "Unknown")
    print("Message Type:", msg_type_str)
    print("Token Length:", coapMessage.header.tkl)

    print("Code:", coapMessage.header.code)
    #afisam message ID in format hex
    print("Message ID: 0x{:04X}".format(coapMessage.header.mid))

    #afisam token in format 0x...
    print("Token:", coapMessage.header.token.hex())
    # json = coapMessage.payload.to_json()
    # print("Payload:", json)
    print ("Payload:", coapMessage.payload)

# def send_message (bytes_coap):
#     host_name = socket.gethostname()
#     ip = socket.gethostbyname(host_name)
#     my_port = 8005
#     peer_port = 5683
#
#     s_send = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
#     s_send.bind((ip, my_port))
#
#     s_send.sendto(bytes_coap, (ip, peer_port))
#
#     while 1:
#         data, addr = s_send.recvfrom(1024)
#         print("Mesaj primit de la server:", data)
#         coap_message = parse_coap_message(data)
#
#         if coap_message.payload is None:
#             break
#         print_coap_message(coap_message)
#         if coap_message.payload.content.is_last_fragment == 1:
#             break


IP = "127.0.0.1"
PORT = 5683
def send_message(coap_message_bytes):
    # Creăm socket-ul
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # Timeout de 5 secunde ca să nu blocheze infinit
    try:
        # Trimitem cererea (PUT CON)
        print(f"[Sender] Trimit {len(coap_message_bytes)} bytes catre {IP}:{PORT}...")
        sock.sendto(coap_message_bytes, (IP, PORT))

        # Buclă pentru a asculta răspunsurile
        while True:
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                print("[Sender] Timeout! Nu am primit raspuns.")
                break

            # Parsăm ce am primit
            response = parse_coap_message(data)

            # --- BLOC NOU: GESTIONARE ACK GOL ---
            # Dacă e ACK (Tip 2) și Cod 0 (Empty), e doar confirmarea de rețea.
            # O ignorăm și așteptăm următorul pachet care are datele.
            if response.header.msg_type == 2 and response.header.code == 0:
                print(f"[Sender] Am primit ACK gol (MID: {response.header.mid}). Serverul lucrează...")
                continue  # Sărim peste restul codului și ascultăm din nou (recvfrom)
            # ------------------------------------

            # Verificăm dacă avem payload valid înainte să accesăm .content
            if response.payload is None or isinstance(response.payload, str):
                print(f"[Sender] Primit mesaj fără Content obiect (Cod: {response.header.code}).")
                # Putem decide să ne oprim sau să continuăm, depinde de logică.
                # De obicei aici e finalul pentru erori.
                break

            # --- VERIFICAREA FINALĂ (Codul tău vechi) ---
            if hasattr(response.payload, 'content') and response.payload.content.is_last_fragment == 1:
                print(f"[Sender] SUCCES! Am primit răspunsul final: {response.payload.content.file_content}")
                break
            else:
                print(f"[Sender] Primit fragment intermediar...")

    except Exception as e:
        print(f"[Sender] Eroare: {e}")
    finally:
        sock.close()