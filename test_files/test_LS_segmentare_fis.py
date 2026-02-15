from server.coap_parser import CoAPMessage, Header, parse_coap_message
from server.payload import Payload, Content
import server.test_files.sender as sender

#Avem nevoie de o clasa CoAPMessage

#Content
#Verificare director de baza
#file_name = ""

#Verificare gresit - director inexistent  -> cod 4.04
#file_name = "folder_inexistent"

#Verificare daca dam un txt -> cod 4.00
#file_name = "om.txt"

file_name = "Aqua"


file_content = ""
payload_size = 0 #numarul octetilor
fragment_count = 1
is_last_fragment = 0
content = Content (file_name, payload_size, file_content, fragment_count, is_last_fragment)

#Payload -> Pentru crearea Json-ului

#Pentru folderul de baza
folder_path = "Barcelona"
file_type = "dir"
payload = Payload (folder_path, file_type, content)


#Pentru creearea Header-ului
version = 1
msg_type = 1 #confirmable
tkl = 2 #lungimea token-ului 2 octeti

#Crearea codului de raspuns 0.05 pentru LS
code = 0 << 5 | 5
mid = 0x5555 #ceva random
token = b'60' #0 sa fie da


header = Header (version, msg_type, tkl, code, mid, token)
coap_message_class = CoAPMessage (header, payload)


#de test deocmandata


#bytes pentru test
coap_message_bytes = sender.build_con_response(coap_message_class)
sender.send_message(coap_message_bytes)
