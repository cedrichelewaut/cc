import subprocess
import socket
import mysql.connector
import random

"""-------------------Install required pymysql package-------------------------"""  
subprocess.call(['sudo pip install pymysql'])

def get_ips():
        """
        Function asks user to input the ip addresses

        Parameters
        ----------
        None

        Returns
        -------
        ips : list[str]
            List ip addresses: master, slave1, slave2 and slave3
    """
    node_names = ['master', 'slave1', 'slave2', 'slave3']
    ip_MASTER = input('Provide the IP-address for the cluster master node: ')
    ip_SLAVE1 = input('Provide the IP-address for the first cluster slave node: ')
    ip_SLAVE2 = input('Provide the IP-address for the second cluster slave node: ')
    ip_SLAVE3 = input('Provide the IP-address for the third cluster slave node: ')
    ips = [ip_MASTER, ip_SLAVE1, ip_SLAVE2, ip_SLAVE3]
    return ips

def get_mode():
    """
        Function asks user to input the mode.
        Will keep asking the mode until a valid one is provided from a provided list.

        Parameters
        ----------
        None

        Returns
        -------
        mode : str
            Mode for execution; either 'direct', 'random' or 'custom'
    """
    valid_modes = ['direct', 'random', 'custom']
    while(True):
        mode = input('Provide a valid mode to use ("direct", "random" or "custom"): ')
        if mode in valid_modes:
            return mode

def get_instruction_type(data):
    """
        Check if instructions is a read or write operation.

        Parameters
        ----------
        data: str
            Command to execute

        Returns
        -------
        insn_type: str
            Type of command, either 'read' or 'write
    """
    insn_type = ''
    if data[:6] == "SELECT":
        insn_type = 'read'
    else:
        insn_type = 'write'
    return insn_type

def get_target(mode, insn_type, ips):
    """
        Function asks user to input the ip addresses

        Parameters
        ----------
        mode:str
            Proxy mode (direct, random or custom)
        insn_type:str
            Instruction type (read or write)
        ips: list[str]
            List of ip addresses (master, slave1, slave2, slave3)

        Returns
        -------
        target: str
            Ip address of node to which we have to send the command
    """
    ip_slaves = ips[1:]
    target = 'not_defined'
    if mode == 'direct' or insn_type == 'write':
        target = ip_MASTER
    elif mode == 'random':
        target = random.choice(ip_slaves)
    else:
        slaves = [mysql.connector.connect(host = ip, user='proxy', password='password') for ip in ip_slaves]
        pings = [ping(slave.serverhost) for slave in slaves]
        ping_times = [ping.rtt_avg for ping in pings]
        target = ip_slaves[ping_times.index(min(ping_times))]
    if target == 'not_defined':
        "WARNING: Failed to assign a target"
    return target

def execute_command(data, target):
    """
        Execute a specified command (data) on a specified target (target)

        Parameters
        ----------
        data:str
            command to execute
        target:str
            target to execute command on
        Returns
        -------
        None
    """
    con = mysql.connector.connect(host=target, user='proxy', password='password', database='sakila')
    try:
        with con.cursor() as cur:
            cur.execute(data)
            print(cur.fetchall())
            con.commit()
            print('executed command: ' + data + ' on ' + target)
    return None

def main():
    """
        Main function:
        Setting up connection with client
        gets commands from client
        Execute functions to find the right target
        Send the command to the right node

    """
    
    """-------------------Ask user for required inputs-------------------------"""  
    ips = get_ips()
    mode = get_mode()

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

                """-------------------Break if no data is received anymore-------------------------"""  
                if not data:
                    break

                """-------------------Check if command is read or write-------------------------"""  
                insn_type = get_instruction_type(data)

                """-------------------Get address of node to which command should be sent -------------------------"""  
                target = get_slave(mode, insn_type)

                """-------------------Execute command on right node-------------------------"""  
                execute_command(data, bind_address)

                """-------------------Execute command on right node-------------------------"""  
                print('response: ' + response.decode("utf-8"))
                resonse =  insn_type + "-command sent to: " + node_names[ips.index(target)]
                s.send(bytes(response, "utf-8"))
                
        s.close()
main()