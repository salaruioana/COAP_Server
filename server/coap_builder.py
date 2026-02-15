from server.coap_parser import Header, CoAPMessage
from server.coap_methods import handle_coap
from server.payload import Payload, Content, payload_encode
CON = 0
NON = 1
ACK = 2
RST = 3


# input: clasa CoAPMessage - un mesaj pentru care generam raspuns
#output: bitii corespunzatori unui raspuns pentru cererea primita
def create_response(coapm: CoAPMessage):
    # incepe creare pachet raspuns

    #trebuie sa vedem ce raspuns dam ACK RST
    # creare header
    code, content = handle_coap(coapm.header.code, coapm.payload)
    msg_type = RST

    #Daca este cod de eroare payload e gol ("")
    if code >= 128:
        # eroare -> returneaza RST
        header_reply = Header(
            coapm.header.version, RST, coapm.header.tkl,
            0, coapm.header.mid, coapm.header.token  # RST trebuie sa aiba code=0
        )
        reply = CoAPMessage(header_reply, None)
        return build_rst_response(reply)
    else:
        if coapm.header.msg_type == CON:
            #cel confirmabil
            msg_type = ACK
        else:
            msg_type = NON
        file_size = len(content)
        #Fragment_count si Is_last_fragment alta data :(
        #bun- deci ca si concluzie trebuie sa implementez pentru fragmentare
        # 1) mecanismul de stocare, reordonare si apel a functiilor pentru POST pentru o cerere de dimensiune mare
        # 2) mecanismul de trimitere de ack gol, fragementare a datelor stocate si trimitere de fragmente sub forma de pachete independente non pentru cererile GET mari

        #Creare payload-ul nou cu content si file_size
        content_reply= Content (coapm.payload.content.file_name, file_size, content)
        payload = Payload (coapm.payload.folder_path, coapm.payload.file_type, content_reply)

        #CoapMessage contine clsa Payload nu json-ul
        #payload_reply = payload.to_json()

    header_reply = Header(coapm.header.version, msg_type, coapm.header.tkl, code, coapm.header.mid, coapm.header.token)
    reply = CoAPMessage(header_reply, payload)

    reply_bytes = b""
    if coapm.header.msg_type == CON:
        reply_bytes = build_ack_response(reply)
    elif coapm.header.msg_type == NON:
        reply_bytes = build_non_response(reply)
    else:
        return b""

    return reply_bytes

# coapMessage- instanta a clasei CoAPMessage din coap_parser

# construieste un mesaj ACK cu payload piggybacked
# primeste parametru o instanta a clasei CoAPMessage
# returneaza un obiect CoAPMessage corespunzator raspunsului



#Am adaugat Decodarea la payload

def build_ack_response(coapMessage: CoAPMessage):
    header = bytearray(4)
    # tip 2 = ACK
    header[0] = (coapMessage.header.version << 6) | (2<<4) | coapMessage.header.tkl
    header[1] = coapMessage.header.code
    header[2] = (coapMessage.header.mid>>8) & 0xFF
    header[3] = coapMessage.header.mid & 0xFF

    if coapMessage.payload :
        return bytes(header) + coapMessage.header.token + bytes([0xFF])+ payload_encode(coapMessage.payload)
    else:
        return bytes(header) + coapMessage.header.token

# construieste un mesaj NON
# primeste parametru o instanta a clasei CoAPMessage
# returneaza un obiect CoAPMessage corespunzator raspunsului

def build_non_response(coapMessage: CoAPMessage):
    header = bytearray(4)
    # tip 1- NON
    header[0] = (coapMessage.header.version << 6) | (1<<4) | coapMessage.header.tkl
    header[1] = coapMessage.header.code
    header[2] = (coapMessage.header.mid>>8) & 0xFF
    header[3] = coapMessage.header.mid & 0xFF

    if coapMessage.payload:
        return bytes(header) +coapMessage.header.token+ bytes([0xFF])+ payload_encode(coapMessage.payload)
    else:
        return bytes(header) + coapMessage.header.token

# construieste un mesaj RST
# primeste parametru o instanta a clasei CoAPMessage
# returneaza un obiect CoAPMessage corespunzator raspunsului

def build_rst_response(coapMessage:CoAPMessage):
    header = bytearray(4)
    # tip 3- RST
    header[0] = (coapMessage.header.version << 6) | (3<<4) | coapMessage.header.tkl
    # mesajele RST sunt empty message
    header[1] = 0
    header[2] = (coapMessage.header.mid>>8) & 0xFF
    header[3] = coapMessage.header.mid & 0xFF

    return bytes(header)+coapMessage.header.token