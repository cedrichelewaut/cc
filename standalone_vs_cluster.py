# Keys are defined in configuration file
# MAKE SURE YOU UPDATED YOUR .AWS/credentials file
# MAKE SURE boto3, matplotlib, requests, fabric and tornado are all installed using pip
import boto3
import json
import time
import subprocess
import requests
from multiprocessing import Pool
from datetime import date
from datetime import datetime, timedelta
from random import randrange

import botocore
import paramiko
from paramiko import SSHClient
#from scp import SCPClient
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl

import logging
logging.getLogger('botocore').setLevel(logging.DEBUG)
logging.getLogger('boto3').setLevel(logging.DEBUG)


"""
The user data constants are used to setup and download programs on the instances
They are passed as arguments in the create instance step
"""

standalone_userdata="""#!/bin/bash
sudo apt-get update
yes | sudo apt-get upgrade
yes | sudo apt-get install mysql-server

# Sakila
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"

# Only run necessary commands from mysql_secure_installation.sh
# https://fedingo.com/how-to-automate-mysql_secure_installation-script/
sudo mysql -e "UPDATE mysql.user SET Password=PASSWORD('root') WHERE User='root';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
sudo mysql -e "DROP DATABASE IF EXISTS test;"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql -e "CREATE USER 'cedric'@'localhost' IDENTIFIED BY 'password';"
sudo mysql -e "GRANT ALL PRIVILEGES on sakila.* TO 'cedric'@'localhost';"

# Sysbench installation and benchmarking
yes | sudo apt-get install sysbench
# Prepare
sysbench --db-driver=mysql --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 /usr/share/sysbench/oltp_read_write.lua prepare
sysbench --db-driver=mysql --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 --num-threads=6 --max-time=60 /usr/share/sysbench/oltp_read_write.lua run > standalone.txt
"""

cluster_userdata = """
"""

def createSecurityGroup(ec2_client):
    """
        The function creates a new security group in AWS

        Parameters
        ----------
        ec2_client
            client that allows for certain functions using boto3

        Returns
        -------
        SECURITY_GROUP : list[str]
            list of the created security group ids
        vpc_id : str
            the vpc_id as it is needed for other operations

        Errors
        -------
        The function throws an error if a security group with the same name already exists in your AWS

    """
    # Create security group, using SSH & HHTP access available from anywhere
    groups = ec2_client.describe_security_groups()
    vpc_id = groups["SecurityGroups"][0]["VpcId"]
    clustername = "securityG" 

    new_group = ec2_client.create_security_group(
        Description="SSH and HTTP access",
        GroupName=clustername,
        VpcId=vpc_id
    )

    # Wait for the security group to exist!
    new_group_waiter = ec2_client.get_waiter('security_group_exists')
    new_group_waiter.wait(GroupNames=[clustername])

    group_id = new_group["GroupId"]

    rule_creation = ec2_client.authorize_security_group_ingress(
        GroupName=clustername,
        GroupId=group_id,
        IpPermissions=[
        {
            'FromPort': 0,
            'ToPort': 65535,
            'IpProtocol': '-1',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }]
    )
    SECURITY_GROUP = [group_id]
    return SECURITY_GROUP, vpc_id

def getAvailabilityZones(ec2_client):
    """
        Retrieving the subnet ids for availability zones
        they are required to assign for example instances to a specific availabilityzone

        Parameters
        ----------
        ec2_client
            client of boto3 tho access certain methods related to AWS EC2

        Returns
        -------
        dict
            a dictonary, with availability zone name as key and subnet id as value

        """
    # Availability zones
    response = ec2_client.describe_subnets()

    availabilityzones = {}
    for subnet in response.get('Subnets'):
        # print(subnet)
        availabilityzones.update({subnet.get('AvailabilityZone'): subnet.get('SubnetId')})

    return availabilityzones

def createInstance(ec2, INSTANCE_TYPE, COUNT, SECURITY_GROUP, SUBNET_ID, userdata, role):
    """
        function that creates EC2 instances on AWS

        Parameters
        ----------
        ec2 : client
            ec2 client to perform actions on AWS EC2 using boto3
        INSTANCE_TYPE : str
            name of the desired instance type.size
        COUNT : int
            number of instances to be created
        SECURITY_GROUP : array[str]
            array of the security groups that should be assigned to the instance
        SUBNET_ID : str
            subnet id that assigns the instance to a certain availability zone
        userdata : str
            string that setups and downloads programs on the instance at creation

        Returns
        -------
        array
            list of all created instances, including their data

        """
    # Don't change these
    KEY_NAME = "vockey"
    INSTANCE_IMAGE = "ami-08d4ac5b634553e16"

    return ec2.create_instances(
        ImageId=INSTANCE_IMAGE,
        MinCount=COUNT,
        MaxCount=COUNT,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=SECURITY_GROUP,
        SubnetId=SUBNET_ID,
        UserData=userdata,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Role',
                        'Value': role,
                    },
                ],
            },
        ]
    )

def getCommands(instances_private_dns):
    """
        generate commands for setting up all instances

        Parameters
        ----------
        instances_private_dns : str
            Private dns addresses of all nodes
            order: standalone, master, slave1, slave2, slave3

        Returns
        -------
        commands : list
            list of all created commands
            order: sakila_commands, master_commands, slave_commands, slave_commands, slave_commands, start_mysqlc_mgmd

        """
    master_commands = [
        # General
        'sudo apt-get update',
        'yes | sudo apt-get upgrade',

        # Get MySQL done
        'sudo mkdir -p /opt/mysqlcluster/home',
        'sudo chmod -R 777 /opt/mysqlcluster',
        'sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.4/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz -P /opt/mysqlcluster/home/',
        'sudo tar -xvf /opt/mysqlcluster/home/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz -C /opt/mysqlcluster/home/',
        'sudo ln -s /opt/mysqlcluster/home/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64 /opt/mysqlcluster/home/mysqlc',
        
        # Adjust the path done
        'sudo chmod -R 777 /etc/profile.d',
        'echo "export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc" > /etc/profile.d/mysqlc.sh',
        'echo "export PATH=$MYSQLC_HOME/bin:$PATH" >> /etc/profile.d/mysqlc.sh',
        'source /etc/profile.d/mysqlc.sh',
        'sudo apt-get update && sudo apt-get -y install libncurses5',

        # Install sysbench
        'yes | sudo apt-get install sysbench',

        # Create the deployment directory
        'sudo mkdir -p /opt/mysqlcluster/deploy',
        'sudo mkdir -p /opt/mysqlcluster/deploy/conf',
        'sudo mkdir -p /opt/mysqlcluster/deploy/mysql_data',
        'sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data',
        'sudo chmod -R 777 /opt/mysqlcluster/deploy',

        # Edit my.cnf
        'echo "[mysqld]" > /opt/mysqlcluster/deploy/conf/my.cnf',
        'echo "datadir=/opt/mysqlcluster/deploy/mysqld_data" >> /opt/mysqlcluster/deploy/conf/my.cnf',
        'echo "basedir=/opt/mysqlcluster/home/mysqlc" >> /opt/mysqlcluster/deploy/conf/my.cnf',
        'echo "port=3306" >> /opt/mysqlcluster/deploy/conf/my.cnf',

        # Edit config.ini
        'echo "[ndb_mgmd]" > /opt/mysqlcluster/deploy/conf/config.ini',
        f'echo "hostname={instances_private_dns[1]}" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "datadir=/opt/mysqlcluster/deploy/ndb_data" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "nodeid=1" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo " " >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "[ndbd default]" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "noofreplicas=1" >> /opt/mysqlcluster/deploy/conf/config.ini',
        #'echo "noofreplicas=3" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "datadir=/opt/mysqlcluster/deploy/ndb_data" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo " " >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "[ndbd]" >> /opt/mysqlcluster/deploy/conf/config.ini',
        f'echo "hostname={instances_private_dns[2]}" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "nodeid=3" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo " " >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "[ndbd]" >> /opt/mysqlcluster/deploy/conf/config.ini',
        f'echo "hostname={instances_private_dns[3]}" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "nodeid=4" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo " " >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "[ndbd]" >> /opt/mysqlcluster/deploy/conf/config.ini',
        f'echo "hostname={instances_private_dns[4]}" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "nodeid=5" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo " " >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "[mysqld]" >> /opt/mysqlcluster/deploy/conf/config.ini',
        'echo "nodeid=50" >> /opt/mysqlcluster/deploy/conf/config.ini',

        # Mysql
        '/opt/mysqlcluster/home/mysqlc/scripts/mysql_install_db --basedir=/opt/mysqlcluster/home/mysqlc --no-defaults --datadir=/opt/mysqlcluster/deploy/mysqld_data',
        '/opt/mysqlcluster/home/mysqlc/bin/ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf/'
    ]

    start_mysqlc_mgmd = ['/opt/mysqlcluster/home/mysqlc/bin/mysqld --defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf --user=root &']


    slave_commands = [
        # General
        'sudo apt-get update',
        'yes | sudo apt-get upgrade',

        # Get MySQL done
        'sudo mkdir -p /opt/mysqlcluster/home',
        'sudo chmod -R 777 /opt/mysqlcluster',
        'sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.4/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz -P /opt/mysqlcluster/home/',
        'sudo tar -xvf /opt/mysqlcluster/home/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz -C /opt/mysqlcluster/home/',
        'sudo ln -s /opt/mysqlcluster/home/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64 /opt/mysqlcluster/home/mysqlc',
        
        # Adjust the path done
        'sudo chmod -R 777 /etc/profile.d',
        'echo "export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc" > /etc/profile.d/mysqlc.sh',
        'echo "export PATH=$MYSQLC_HOME/bin:$PATH" >> /etc/profile.d/mysqlc.sh',
        'source /etc/profile.d/mysqlc.sh',
        'sudo apt-get update && sudo apt-get -y install libncurses5',

        # Install sysbench
        'yes | sudo apt-get install sysbench',
        'mkdir -p /opt/mysqlcluster/deploy/ndb_data',
        f'/opt/mysqlcluster/home/mysqlc/bin/ndbd -c {instances_private_dns[1]}'
    ]

    sakila_commands = [
        # Sakila
        'sudo wget http://downloads.mysql.com/docs/sakila-db.zip',
        'sudo apt install unzip',
        'sudo unzip sakila-db.zip -d "/tmp/"',
        'sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;"',
        'sudo /opt/mysqlcluster/home/mysqlc/bin/mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"',

        # https://fedingo.com/how-to-automate-mysql_secure_installation-script/
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "UPDATE mysql.user SET Password=PASSWORD('root') WHERE User='root';"''',
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "DELETE FROM mysql.user WHERE User='';"''',
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"''',
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "DROP DATABASE IF EXISTS test;"''',
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "FLUSH PRIVILEGES;"''',
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "CREATE USER 'cedric'@'%' IDENTIFIED BY 'password';"''',
        '''/opt/mysqlcluster/home/mysqlc/bin/mysql -e "GRANT ALL PRIVILEGES on sakila.* TO 'cedric'@'localhost';"''',


        # Sysbench installation and benchmarking
        'yes | sudo apt-get install sysbench',
        # 'sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 /usr/share/sysbench/oltp_read_write.lua --mysql_storage_engine=ndbcluster prepare',
        # 'sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 --num-threads=6 --max-time=60 /usr/share/sysbench/oltp_read_write.lua --mysql_storage_engine=ndbcluster run > cluster.txt'
        'sudo sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 /usr/share/sysbench/oltp_read_write.lua --mysql_storage_engine=ndbcluster prepare',
        'sudo sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 --num-threads=6 --max-time=60 /usr/share/sysbench/oltp_read_write.lua --mysql_storage_engine=ndbcluster run > cluster.txt'
        ]

    commands = [sakila_commands, master_commands, slave_commands, slave_commands, slave_commands, start_mysqlc_mgmd]
    return commands

def executeCommands(rsakey, ssh_client, setup_commands, instances_public_dns):
    """
        execute commands for setting up all instances

        Parameters
        ----------
        rsakey
            key needed to access the instances
        ssh_client
            Paramiko ssh client
        setup_commands : list of lists
            list of list of all commands required for the set-up
            order: sakila_commands, master_commands, slave_commands, slave_commands, slave_commands, start_mysqlc_mgmd
        instances_public_dns: list
            list with the dns address of all nodes
            order: standalone, master, slave1, slave2, slave3

        Returns
        -------
        None
            nothing is returned
        """
    # Execute commands on each of the cluster nodes
    for i in range(1, len(instances_public_dns)):
        ssh_client.connect(hostname = instances_public_dns[i], username = "ubuntu", pkey = rsakey)
        for command in setup_commands[i]:
            stdin , stdout, stderr = ssh_client.exec_command(command) 
            while True:
                if stdout.channel.exit_status_ready():
                    break
                time.sleep(0.1)
    time.sleep(20)

    # Start the mgmd
    ssh_client.connect(hostname = instances_public_dns[1], username = "ubuntu", pkey = rsakey)
    for command in setup_commands[5]:
        stdin , stdout, stderr = ssh_client.exec_command(command)
    time.sleep(20)

    # Execute Sakila commands on the master node
    ssh_client.connect(hostname = instances_public_dns[1], username = "ubuntu", pkey = rsakey)
    for command in setup_commands[0]:
        stdin , stdout, stderr = ssh_client.exec_command(command) 
        while True:
            if stdout.channel.exit_status_ready():
                break
            time.sleep(0.1)
    time.sleep(20)
    return None

def main():
    """
        main function for performing the application
        Connects to the boto3 clients
        calls functions for setting up ec2 instances
        calls functions to execute set-up commands on all instances
        calls functions to benchmark both standalone and cluster setup

        """
    """------------Get necesarry clients from boto3------------------------"""
    ec2_client = boto3.client("ec2")
    ec2 = boto3.resource('ec2')

    """-------------------Create security group--------------------------"""
    SECURITY_GROUP, vpc_id = createSecurityGroup(ec2_client)
    print("security_group: ", SECURITY_GROUP)
    print("vpc_id: ", str(vpc_id), "\n")

    """-------------------Get availability Zones--------------------------"""
    availabilityZones = getAvailabilityZones(ec2_client)
    print("Availability zones:")
    print("Zone 1a: ", availabilityZones.get('us-east-1a'), "\n")

    """-------------------Create standalone and cluster instances--------------------------"""    
    availability_zone_1a = availabilityZones.get('us-east-1a')
    standalone_instances = createInstance(ec2, "t2.micro", 1, SECURITY_GROUP, availability_zone_1a, standalone_userdata, "standalone")
    master_instances = createInstance(ec2, "t2.micro", 1, SECURITY_GROUP, availability_zone_1a, cluster_userdata, "master")
    slave_instances = createInstance(ec2, "t2.micro", 3, SECURITY_GROUP, availability_zone_1a, cluster_userdata, "slave")
    instances = standalone_instances + master_instances + slave_instances
    instances_ids = []
    instances_ips = []
    instances_public_dns = []
    instances_private_dns = []
    print(instances)
    for instance in instances:
        instances_ids.append(instance.id)
        instance.wait_until_running()
        instance.reload()
        instances_ips.append(instance.public_ip_address)
        instances_public_dns.append(instance.public_dns_name)
        instances_private_dns.append(instance.private_dns_name)

    
    """-------------------Wait for instances to be launched--------------------------"""  
    instance_running_waiter = ec2_client.get_waiter('instance_running')
    instance_running_waiter.wait(InstanceIds=(instances_ids))

    """-------------------Create paramiko client to add -------------------------"""  
    rsakey = paramiko.RSAKey.from_private_key_file("labsuser.pem")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    time.sleep(60)

    """-------------------Perform commands for cluster set-up--------------------------"""  
    executeCommands(rsakey, ssh_client, getCommands(instances_private_dns), instances_public_dns)

    """-------------------get benchmark results from machine--------------------------"""  
    subprocess.call(['scp', '-o','StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-i', 'labsuser.pem', "ubuntu@"+str(instances_ips[0])+":/../../standalone.txt", '.'])
    subprocess.call(['scp', '-o','StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-i', 'labsuser.pem', "ubuntu@"+str(instances_ips[1])+":cluster.txt", '.'])
main()