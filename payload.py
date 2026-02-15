import json
from enum import Enum
from server.response_code_handler import error_handler

# {
#     "folder_path": "/path/to/folder",
#     "file_type": "txt",
#     "content": [
#         {
#             "file_name": "document",
#             "payload_size": "16KB",
#             "fragment_count": "1:,
#             "is_last_fragment": "0",
#             "file_content": "codificarea=unui=document"
#         }
#     ]
# }

#Crearea de enumuri pentru a accesa mai clean
class Keys (Enum):
    FOLDER_PATH = "folder_path"
    FILE_TYPE = "file_type"
    CONTENT = "content"

class ContentKeys (Enum):
    FILE_NAME = "file_name"
    PAYLOAD_SIZE = "payload_size"
    FRAGMENT_COUNT = "fragment_count"
    IS_LAST_FRAGMENT = "is_last_fragment"
    FILE_CONTENT = "file_content"

class Content:
    def __init__(self, file_name, payload_size, file_content,
                 fragment_count = 1, is_last_fragment = 1):
        self.file_name = file_name
        self.payload_size = payload_size

        #Verificam daca file_content e in format bytes
        #Acum nu mai avem probleme cu creearea JSON-ului =)
        if isinstance(file_content, bytes):
           file_content = file_content.decode('utf-8')
        self.file_content = file_content
        self.fragment_count = fragment_count
        self.is_last_fragment = is_last_fragment

    #Pentru teste
    def __str__(self):
        return (f"   file_name: {self.file_name}, "
                f"\n   payload_size: {self.payload_size},"
                f"\n   fragment_count: {self.fragment_count},"
                f"\n   is_last_fragment: {self.is_last_fragment},"
                f"\n   file_content: {self.file_content}")

    def to_json(self):
            return{
                        ContentKeys.FILE_NAME.value: self.file_name,
                        ContentKeys.PAYLOAD_SIZE.value: self.payload_size,
                        ContentKeys.FRAGMENT_COUNT.value: self.fragment_count,
                        ContentKeys.IS_LAST_FRAGMENT.value: self.is_last_fragment,
                        ContentKeys.FILE_CONTENT.value: self.file_content
            }

class Payload:
    def __init__(self, folder_path, file_type, content:Content):
        self.folder_path = folder_path
        self.file_type = file_type
        self.content = content

    #Pentru teste
    def __str__ (self):
        return (f"folder_path: {self.folder_path}, "
                f"\nfile_type: {self.file_type},"
                f"\ncontent: \n{self.content}")

    def to_json (self):
        return {
                Keys.FOLDER_PATH.value: self.folder_path,
                Keys.FILE_TYPE.value: self.file_type,
                Keys.CONTENT.value: [self.content.to_json()]
            }


#creare instance separat ca sa nu ne repetam in decode si encode
#O sa le folosim cand trimitem payload-ul inapoi
#Sau noi doar modificam content-ul ??? in functie de metode hmm
def content_instance (file_name, payload_size, file_content, fragment_count, is_last_fragment):
    return Content (file_name, payload_size, file_content, fragment_count, is_last_fragment)

def payload_instance (folder_path, file_type, content: Content):
    return Payload (folder_path, file_type, content)

#Crearea clasei, utilizand un json
def payload_decode (payload_bytes):
    #Asa citim dintr-un json direct din txt, noi dorim din codificare
    # with open (json_file, mode="r", encoding="utf-8") as rf:
    #     json_data = json.load(rf)

    #Asa luam din codificare utf-8
    try:
        text = payload_bytes.decode("utf-8")
        json_data = json.loads(text) #Any
    except Exception as error:
        return error_handler (error, "Payload")

    #Acum trebuie sa creem clasa Payload pe care sa o returnam sa o folosim
    folder_path = json_data[Keys.FOLDER_PATH.value]
    file_type = json_data[Keys.FILE_TYPE.value]
    content = json_data[Keys.CONTENT.value]

    #Datele din Content aici  content e o lista cu un singur element care are restul
    file_name = content[0][ContentKeys.FILE_NAME.value]
    payload_size = content[0][ContentKeys.PAYLOAD_SIZE.value]
    fragment_count = content[0][ContentKeys.FRAGMENT_COUNT.value]
    is_last_fragment = content[0][ContentKeys.IS_LAST_FRAGMENT.value]
    file_content = content[0][ContentKeys.FILE_CONTENT.value]

    return payload_instance(folder_path, file_type, content_instance(file_name, payload_size, file_content, fragment_count, is_last_fragment))

#Primim eroare JSONDecodeError daca nu recunoaste ceva ce ar trebui sa fie intr un json

def payload_encode (payload: Payload):
    #Creeem json-ul dintr-o clasa Payload
    #returnam codul
    json_data = payload.to_json()

    #transforma in string
    text = json.dumps (json_data, ensure_ascii=False)
    #transforma in bytes utf-8
    code = text.encode('utf-8')
    return code


#Doar pentru test asta
def json_to_bytes (file_path):
    with open (file_path, "r") as f:
        data = f.read()
    data_b = data.encode('utf-8')
    print (data_b)
    return data_b

# data_bytes = json_to_bytes("Storage/test.json")
# payload_class = payload_decode(data_bytes)
#
# #print (payload_class.__str__())
# data_bytes2 = payload_encode(payload_class)
# print()
# print (data_bytes2)
# #Acum
#
# payload_class2 = payload_decode(data_bytes2)


# file_name = "CraciunFericit"
# file_content = "Sarbatori Fericite, La Multi Ani!".encode("utf-8")
# payload_size = len(file_content) #numarul octetilor
# fragment_count = 1
# is_last_fragment = 0
# content = Content (file_name, payload_size, file_content, fragment_count, is_last_fragment)
#
# folder_path = ""
# file_type = "txt"
# payload = Payload (folder_path, file_type, content)
#
# payload_send = payload.to_json()
#
# print ("JSON Payload to be sent:")
# print (payload_send)
#
# print ("\n\nPayload class:")
# print (payload)
#
# payload_bytes = payload_encode (payload)
# print ("\n\nPayload bytes to be sent:")
# print (payload_bytes)