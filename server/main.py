from server.server_thread import Listener
import socket

if __name__ == '__main__':
    # este creat socket-ul unde va rula serverul (unde asculta pentru cereri)
    # host_name = socket.gethostname()
    # ip = socket.gethostbyname(host_name)

    ip = '0.0.0.0'
    port = 5683

    listen_thread = Listener(ip, port)
    listen_thread.start()
    # join mentine programul activ vat timp thread-ul serverului este activ
    listen_thread.join()
