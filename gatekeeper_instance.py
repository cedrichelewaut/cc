# Keys are defined in configuration file
# MAKE SURE YOU UPDATED YOUR .AWS/credentials file
# MAKE SURE boto3, matplotlib, requests, fabric and tqdm are all installed using pip
import boto3
import json
from time import sleep
import sys
from tqdm import tqdm
import paramiko
from paramiko import SSHClient
from pathlib import Path
import socket
"""
The user data constants are used to setup and download programs on the instances
They are passed as arguments in the create instance step
"""

proxy_userdata="""
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
    clustername = "Proxy" 

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

def main():
    """
        Launch the gatekeeper_instance
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

    """-------------------Create proxy instances--------------------------"""    
    availability_zone_1a = availabilityZones.get('us-east-1a')
    proxy_instance = createInstance(ec2, "t2.large", 1, SECURITY_GROUP, availability_zone_1a, proxy_userdata, "gatekeeper")
    proxy_instance[0].wait_until_running()
    proxy_instance[0].reload()
    proxy_id, proxy_ip, proxy_dns = proxy_instance[0].id, proxy_instance[0].public_ip_address, proxy_instance[0].private_dns_name
    print(proxy_id, proxy_ip, proxy_dns)
main()
