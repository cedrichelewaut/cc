import time
import subprocess
import socket


# MODE: choose from "Direct", "Random", "Customized"
MODE = "Direct"
PORT = None
HOST = None



def main():
    # Setup
    t0 = time.time()
    proxy_socket = socket.socket()
    if (HOST is None) OR (PORT is None):
        print("Host and or port not provided")
        break
    proxy_socket.connect((HOST, PORT))
    sleep(5)
    t1 = time.time()
    # Write to DB
    f = open('database.txt', 'r')
    count = 100
    for l in f:
        while (count > 0):
            l = l.strip('\n')
            cmd = 'INSERT INTO inventory VALUES ' + l
            socket.send(pickle.dumps(req = {'type': 'insert', 'command': cmd}))
            socket.recv(2048)
            count -= 1
    f.close()
    sleep(5)
    t2 = time.time()
    # Read from DB
    count = 100
    while (count > 0):
        cmd = 'SELECT * FROM inventory WHERE inventory_id = ' + str(i)
        socket.send(pickle.dumps({'type': 'select', 'command': cmd, 'mode': MODE}))
        socket.recv(2048)
    sleep(5)
    t3 = time.time()
    # Clean up
    socket.send(pickle.dumps({'type': 'delete', 'command': 'DELETE FROM inventory;'}))
    socket.recv(2048)
    sleep(5)
    t4 = time.time()

