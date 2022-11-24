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

import botocore
import paramiko
from paramiko import SSHClient
#from scp import SCPClient
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl

"""
The user data constants are used to setup and download programs on the instances
They are passed as arguments in the create instance step
"""

userdata = """
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

    new_group = ec2_client.create_security_group(
        Description="SSH and HTTP access",
        GroupName="clusterMySQL",
        VpcId=vpc_id
    )

    # Wait for the security group to exist!
    new_group_waiter = ec2_client.get_waiter('security_group_exists')
    new_group_waiter.wait(GroupNames=["clusterMySQL"])

    group_id = new_group["GroupId"]

    rule_creation = ec2_client.authorize_security_group_ingress(
        GroupName="clusterMySQL",
        GroupId=group_id,
        IpPermissions=[{
            'FromPort': 22,
            'ToPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        },
        {
            'FromPort': 80,
            'ToPort': 80,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }, {
            'FromPort': 443,
            'ToPort': 443,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }, {
            'FromPort': 1186,
            'ToPort': 1186,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }, {
            'FromPort': 3306,
            'ToPort': 3306,
            'IpProtocol': 'tcp',
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

def createInstances(ec2_client, ec2, SECURITY_GROUP, availabilityZones):
    """
        function that retrievs and processes attributes as well as defining the amount and types of instances to be created
        getting the decired subnet id
        calling function create instance to create the instances
        parces the return to just return the ids and ips of the instances
        currently handle only creation of one instance

        Parameters
        ----------
        ec2_client : client
            Boto3 client to access certain function to controll AWS CLI
        ec2 : client
            Boto3 client to access certain function to controll AWS CLI
        SECURITY_GROUP : array[str]
            list of security groups to assign to instances
        availabilityZones : dict{str, str}
            dict of availability zone names an key and subnet ids as value

        Returns
        -------
        array
            containg instance id and ip
        """
    # Get wanted availability zone
    availability_zone_1a = availabilityZones.get('us-east-1a')
    slave_instances = createInstance(ec2, "t2.micro", 3, SECURITY_GROUP, availability_zone_1a, userdata, "slave")
    master_instances = createInstance(ec2, "t2.micro", 1, SECURITY_GROUP, availability_zone_1a, userdata, "master")
    instance_ids = []
    instance_ips = []

    for instance in slave_instances:
        instance_ids.append(instance.id)
        instance.wait_until_running()
        instance.reload()
        instance_ips.append(instance.public_ip_address)

    for instance in master_instances:
        instance_ids.append(instance.id)
        instance.wait_until_running()
        instance.reload()
        instance_ips.append(instance.public_ip_address)


    # Wait for all instances to be active!
    instance_running_waiter = ec2_client.get_waiter('instance_running')
    instance_running_waiter.wait(InstanceIds=(instance_ids))

    return [instance_ids, instance_ips]


def main():
    """
        main function fer performing the application
        Connects to the boto3 clients
        calls the required functions

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

    """-------------------Create the instances--------------------------"""
    ins = createInstances(ec2_client, ec2, SECURITY_GROUP, availabilityZones)
    print("First three are slaves, fourth the master")
    print("Instance ids: \n", str(ins[0]), "\n")
    print("Instance ip: \n", str(ins[1]), "\n")
main()