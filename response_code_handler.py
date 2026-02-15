#Trebuie gandita bine partea de erori si ce coduri ar trebui returnate


RESPONSE_CODE = {
    "Created": (2.01, "Successfully created"),
    "Deleted": (2.02, "Successfully deleted"),
    "Changed": (2.04, "Successfully changed"),
    "Content": (2.05, ""), #oare sa-i dam si astuia ceva mesaj? - gen succesfully added
    "Bad Request": (4.00, "Invalid request"),
    "Not Found": (4.04, "Resource not found"),
    "Internal Error": (5.00, "Process Error")
}
def code_return (response):
    code, _ = RESPONSE_CODE[response]

    #extragem partea intreaga din cod
    class_code = int(code)

    #extragem cealalta parte =)
    detail_code = int (round((code - class_code) * 100))

    #calculam codul cu class << 5 | detail
    coap_code = class_code << 5 | detail_code
    return coap_code


def error_handler (error: Exception, file_name):
    error_name = error.__class__.__name__
    if len(error.args) > 1:
        msg = error.args[1]
    else:
        msg = error.args[0]

    if error_name == "FileExistsError":
        print (f"{msg}: {file_name} -> 4.00")
        return code_return("Bad Request") #returnam 4.00
    elif error_name == "FileNotFoundError":
        print (f"{msg}: {file_name} -> 4.04")
        return code_return("Not Found")
    elif error_name == "OSError" or error_name == "JSONDecodeError":
        print (f"{msg}: {file_name} -> 5.00")
        return code_return("Internal Error")
    return code_return("Bad Request")

