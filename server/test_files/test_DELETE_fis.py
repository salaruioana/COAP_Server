from server.coap_parser import CoAPMessage, Header, parse_coap_message
from server.payload import Payload, Content
import server.test_files.sender as sender

#Avem nevoie de o clasa CoAPMessage

#Content
file_name = "CraciunFericit2"

file_content = ""
payload_size = 0 #numarul octetilor
fragment_count = 1
is_last_fragment = 0
content = Content (file_name, payload_size, file_content, fragment_count, is_last_fragment)

#Payload -> Pentru crearea Json-ului

folder_path = ""
file_type = "txt"
payload = Payload (folder_path, file_type, content)


#Pentru creearea Header-ului
version = 1
msg_type = 1
tkl = 2 #lungimea token-ului 2 octeti

#Crearea codului de raspuns 0.04 pentru DELETE
code = 0 << 5 | 4
mid = 0x4444 #ceva random
token = b'60' #0 sa fie da


header = Header (version, msg_type, tkl, code, mid, token)
coap_message_class = CoAPMessage (header, payload)


#bytes pentru test
coap_message_bytes = sender.build_con_response(coap_message_class)
sender.send_message(coap_message_bytes)

