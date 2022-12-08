import socket

def main():
    """
        Establishing connection with the proxy node and send commands
    """
    with socket.socket() as s:
        """-------------------Ask user for proxy node IP address and connect node------------------------""" 
        host = input("Provide IP address of the proxy node: ")
        print(host)
        s.connect((host, 5050))
        while True:
            """-------------------Install required pymysql package-------------------------""" 
            command = input("Next command (enter 'stop' to finish): ")
            if command == "stop":
                break
            s.send(bytes(command, "utf-8"))
            response = s.recv(1024)
            print('response: ' + response.decode("utf-8"))
main()