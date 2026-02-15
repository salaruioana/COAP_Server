from http.client import responses

import server.file_handler as f

COAP_METHODS = {
    1: "GET",
    2: "POST",
    3: "PUT",
    4: "DELETE",
    5: "LS"
}


#extragem "folder_type" din JSON-ul de la Payload

# {
#     "action": "POST",
#     "folder_path": "/path/to/folder",
#     "folder_type": "txt",
#     "content": [
#         {
#             "file_name": "document",
#             "file_size": "16KB",   -> Probabil fara file_size
#             "file_content": "codificarea=unui=document"
#         }
#     ]
# }

#raspunsurile trebuie sa le trimit in zecimal, nu cu x.yz
def get_handler (file_name, extension, path):
    return f.read_file(file_name, extension, path)  #returnam de forma response, content

def post_handler (file_name, extension, path):
    if extension == "dir":
        return f.create_dir(file_name, path)
    else:
        return f.create_file(file_name, extension, path)

def put_handler (file_name, extension, content, path):
    return f.write_file(file_name, extension, content, path)

def delete_handler (file_name, extension, path):
    return f.delete(file_name, extension, path)

def ls_handler (file_name, path):
    return f.list_files (file_name, path)

#method o sa fie raspunsul de la code, ca sa stim ce metoda aplicam
def handle_coap (method, payload):
    #trebuie ceva pentru empty
    if method == 1:
        return get_handler(payload.content.file_name, payload.file_type, payload.folder_path) #cred ca asa o sa accesam din payload, urmeaza si ala
    elif method == 2:
        return post_handler(payload.content.file_name, payload.file_type, payload.folder_path)
    elif method == 3:
        return put_handler(payload.content.file_name, payload.file_type, payload.content.file_content, payload.folder_path)
    elif method == 4:
        return delete_handler(payload.content.file_name, payload.file_type, payload.folder_path)
    elif method == 5:
        return  ls_handler(payload.content.file_name, payload.folder_path)
    return 0 #PING


