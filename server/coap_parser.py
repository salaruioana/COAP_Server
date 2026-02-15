from server.payload import payload_decode

class Header:
    def __init__(self, version, msg_type, tkl, code, mid, token):
        self.version = version
        self.msg_type = msg_type
        self.tkl = tkl
        self.code = code
        self.mid = mid
        self.token = token
class CoAPMessage:
    def __init__(self, header, payload):
        self.header = header
        self.payload = payload

# Functia principala de parsare
# primeste un pachet si adresa sursa
# returneaza un instanta a clasei CoAPMessage cu datele colectate prin parsarea pachetului
def parse_coap_message(data):
    try:
        # nu trebuie decode- aici ar trebui sa primim pur binar!!
        # data = data.decode('utf-16')
        if len(data) < 4:
            raise ValueError("Pachet prea scurt pentru un mesaj CoAP valid.")
        # Primii 4 biti din Header

        first_byte = data[0]
        # masca pe biti care selecteaza doar ultimii 2 biti
        version = (first_byte >> 6) & 0x03
        msg_type = (first_byte >> 4) & 0x03
        tkl = first_byte & 0x0F

        #verificam valorile
        if version != 1:
            raise ValueError("Version invalid - trebuie sa fie 1.")
        if tkl > 8:
            raise ValueError("Token invalid (>8).")

        code = data[1]
        # se inverseaza ordinea celor doi bytes fiind in network byte order
        message_id = (data[2] << 8) | data[3]

        # token
        if tkl>0:
            if len(data) < 4+tkl:
                raise ValueError("Pachet prea scurt pentru token.")
            token = data[4:(4+tkl)]
        else:
            raise ValueError("Token invalid (=0)")
        idx = 4+tkl

        # urmeaza payload
        #initializam payload ca byte string gol
        payload_instance = ""
        if idx < len(data):
            # Căutăm markerul doar daca exista în restul datelor
            try:
                payload_marker = data.index(0xFF, idx)
                payload = data[payload_marker+1:]
                #Trebuie decodat payload-ul
                payload_instance= payload_decode(payload)
            except ValueError:
                #Fara payload
                payload_instance = ""
            # apelez metode de handle payload ( payload_decode)
            # trimite payload decodat ca si parametru
        header = Header(version, msg_type, tkl, code, message_id, token)
        return CoAPMessage(header, payload_instance)
    except Exception as e:
        print("Mesaj invalid.")
        # generare RST-empty message
        # ar trebui vazut aici- daca putem citi tokenul si message id-ul sa fie incluse in raspuns...
