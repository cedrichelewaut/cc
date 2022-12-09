import subprocess
import socket
import mysql.connector
import random
import sqlite3

PROXY_ADDRESS = "TODO"

def validate(command):
    """
        validate if command is a valid sql command, using the sqlite3 

        Parameters
        ----------
        command:str
            command to validate

        Returns
        -------
        valid:boolean
            returns true if command is a valid sql command
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

        Parameters
        ----------
        command:str
            Contains valid query for the database

        Returns
        -------
        response:bytes
            Response from proxy
    """
    with socket.socket() as s:
        """-------------------Ask user for proxy node IP address and connect node------------------------""" 
        host = PROXY_ADDRESS
        if host == "TODO":
            print("Address of proxy unknown")
            break
        s.connect((host, 5050))
        s.send(bytes(command, "utf-8"))
        response = s.recv(1024)
        return response
      
    
def main():
    """
        Main function:
        Receive queries and forward them to the proxy if they are valid
    """
    """-------------------Connect to client via socket-------------------------"""  
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 5050))
        s.listen(5)
        clientsocket, address = s.accept()
        with clientsocket:
            while True:
                """-------------------Get next command------------------------"""  
                data = clientsocket.recv(1024)
                command = data.decode("utf-8")

                """-------------Break if no data is received anymore---------------"""  
                if not data:
                    break

                """-------------------Validate sql query-------------------------"""  
                valid = validate(command)
                """-------------------Forward query if it was valid-------------------------"""  
                if not valid:
                    response = "Query refused, not valid!"
                    s.send(bytes(response, "utf-8"))
                else:
                    response = forward_to_proxy(command)
                    s.send(response)
                
        s.close()
main()
