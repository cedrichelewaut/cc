Vimport sys
import socket
mode = str(sys.argv[1])
valid_modes = ['direct', 'random', 'custom']
def main():
    if mode in valid_modes:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 5050))
            # No queue set, no parallel accesses, might give inconsistencies
            s.listen(5)
            clientsocket, address = s.accept()
            print("Connection: ", address)
            with clientsocket:
                while True:
                    data = clientsocket.recv(1024)
                    if not data:
                        break
                    print(data)
                    clientsocket.send(bytes("test", "utf-8"))
            s.close()
    else:
        print("invalid mode specified")
main()

