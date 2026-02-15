import socket
import threading
import server.receiver_thread as receiver_thread
from server.file_handler import create_base_dir

# thread principal unde se primesc cererile
# este invocata din main la pornirea serverului
# single use: asculta la socketul respectiv si trimite cererile spre procesare la primire
#clasa Listener mosteneste clasa Thread
class Listener(threading.Thread):
    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.ip, self.port))

    def run(self):
        create_base_dir()
        print(f"[LISTENER] Ascult pe {self.ip}:{self.port}")
        # daemon threads pe true <-> atunci cand oprim main, se inchid si toate thread-urile de procesare care ar putea fi agatate
        while True:
            data, addr = self.server_socket.recvfrom(2048)
            threading.Thread(target=receiver_thread.process_received,
                             args=(self.server_socket,data,addr),
                             daemon = True).start()