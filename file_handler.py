import os

from server.response_code_handler import error_handler
from server.response_code_handler import code_return

#acces creare si stergere fisiere / directoare

#Directorul default unde vom stoca fisierele
Base_Dir = os.path.abspath("Storage")


#ar trebui sa luam extensia
#Creem path-ul unde vom pune fisierele

#daca avem director apelam functia fara extension
def path_create (path, file_name, extension = ""):
    name = file_name
    if extension != "dir":
        name = name + '.' + extension

    full_path = os.path.join(Base_Dir, path, name)
    normalized = os.path.normpath(os.path.abspath(full_path))

    # masura de securitate
    if not normalized.startswith(Base_Dir):
        raise ValueError(f"Path traversal attempt: {normalized}")
    return normalized

#Crearea directorului unde se vor afla fisierele
def create_base_dir ():
    try:
        os.mkdir(Base_Dir)
    except Exception as error:
        return error_handler(error, "Storage dir"), ""  # Daca exista o sa intoarcem eroarea 5 Internal Error
    return code_return("Created"), ""  # Raspuns 2.01
#Crearea directorului

#Pentru POST
def create_dir (dir_name, path = ""):
    dir_path = path_create(path, dir_name, "dir")
    try:
        os.mkdir(dir_path)
    except Exception as error:
        return error_handler(error, dir_name), "" # Daca exista o sa intoarcem eroarea 5 Internal Error
    return code_return("Created"), ""  # Raspuns 2.01

#Pentru POST
#create cu tot cu content? probabil nu, Folosim write_file ca sa scriem
def create_file (file_name, extension, path = ""):
    file_path = path_create (path, file_name, extension)
    try:
        open(file_path, 'w')
    except Exception as error:
        return error_handler(error, file_name), ""
    return code_return("Created"), ""  # Raspuns 2.01

#Pentru DELETE #Verificam daca este director si daca acesta este gol, altfel incercam sa stergem fisierul
def delete (file_name, extension, path = ""):
    file_path = path_create (path, file_name, extension)
    if extension == "dir":
        try:
            os.rmdir(file_path)
        except Exception as error:
            return error_handler(error, file_name), ""
    else:
        try:
            os.remove(file_path)
        except Exception as error:
            return error_handler(error, file_name), ""
    return code_return("Deleted"), ""  # Raspuns 2.02

#Pentru GET

#trebuie returnat si citit bytes utf-8
# file = open (file_path, 'r', encoding="utf-8")
def read_file (file_name, extension, path = ""):
    file_path = path_create (path, file_name, extension)
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        #Trebuie sa trimitem string-ul ca sa nu avem problme cu JSON-ul
        #content_bytes = content.encode('utf-8')
        return code_return("Content"), content #2.05
    except Exception as error:
        return error_handler(error, file_name), ""

#Pentru PUT
#trebuie citit ca bytes
def write_file (file_name, extension, content, path = ""):
    file_path = path_create(path, file_name, extension)
    try:
        #content = content.decode('utf-8')
        #cum functioneaza scrierea cu biti
        # file = open (file_path, 'wb')
        # file.write(content)

        #O sa primim content ca string deci scriem normal
        with open(file_path, 'a') as file:
            file.write(content)
    except Exception as error:
        return error_handler(error, file_name), ""
    return code_return("Changed"), "" #2.04
#De vazut daca trebuie adaugat la fisier

#folosim la LS la directoare
def list_files (file_name, path = ""):
    file_path = path_create(path, file_name)
    try:
        content = os.listdir(file_path)
        return code_return("Content"), content
    except Exception as error:
        return error_handler(error, file_name), ""



#Testare functii

# create_base_dir()
# create_dir("test")
#
#
# #test file
# create_file("python", "txt") #merge Tare
# a = read_file("test2", "txt")
#
# print (a)

# write_file("test4", "txt", a[1])


# create_file ("test1.txt", "Uite ase", "test")
# create_file ("test2.txt", "Uite ase x2", "test")
# delete("test2.txt", "test")
#
# delete ("test")
#rename("test2.txt", "test")
#rename ("test", "Barcelona")

# create_file ("test1", "txt",  )
# create_file ("test15", "txt",  "Barcelona")
#
# print (list_files("Barcelona"))
#
# print (list_files("test2"))
# print (read_file("test2", "txt"))
#
#
# b = "Salut".encode("utf-8")
# print (b)
# print (b.decode("utf-8"))

#Trebuie vazut cu decodarea cum trebuie facut

# b = "Salut".encode("utf-8")
# print (b)
# print (len(b))
#
# write_file("test1", "txt", b)