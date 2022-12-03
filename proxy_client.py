import socket
with socket.socket() as s:
    host = '3.89.87.91' # public IP van de ec2 instance	
    s.connect((host, 5050))
    s.send(bytes("hello", "utf-8"))
