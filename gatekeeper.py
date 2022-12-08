import subprocess
import socket
import mysql.connector
import random
import sqlite3

def validate(command):
    """
        validate if command is a valid sql command, using the sqlite3 
        ----------
        command:str
            command to validate
        Returns
        -------
        valid:boolean
            returns true if command is a valid sql command
        None
    """
    temp_db = sqlite3.connect(":memory:")
    valid = True
    try:
        temp_db.execute(command)
    except Exception as e:
        print("Invalid SQL command")
        valid = False
        continue
    return valid
  
def forward_to_proxy(command):
    """
        Establishing connection with the proxy node and send command
    """
    with socket.socket() as s:
        """-------------------Ask user for proxy node IP address and connect node------------------------""" 
        host = input("Provide IP address of the proxy node: ")
        print(host)
        s.connect((host, 5050))
        s.send(bytes(command, "utf-8"))
        response = s.recv(1024)
        print('response: ' + response.decode("utf-8"))
        return response
      
    
def main():
    """
        Main function:
        Setting up connection with client
        gets commands from client
        Execute functions to find the right target
        Send the command to the right node
    """


    """-------------------Connect to client via socket-------------------------"""  
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 5050))
        s.listen(5)
        clientsocket, address = s.accept()
        print("Connection on: ", address)
        with clientsocket:
            while True:
                """-------------------Get next command------------------------"""  
                data = clientsocket.recv(1024)
                command = data.decode("utf-8")
                print("Received command: " + command)

                """-------------------Break if no data is received anymore-------------------------"""  
                if not data:
                    break

                """-------------------Validate sql query-------------------------"""  
                valid = validate(command)
                """-------------------Validate sql query-------------------------"""  
                if not valid:
                    response = "Query refused, not valid!"
                    s.send(bytes(response, "utf-8")
                else:
                    response = forward_to_proxy(command)
                    s.send(response)
                
        s.close()
main()
