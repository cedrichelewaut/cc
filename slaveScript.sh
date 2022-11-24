#!/bin/bash
sudo apt-get update
yes | sudo apt-get upgrade

# Install mysql cluster
sudo mkdir -p /opt/mysqlcluster/home
sudo chmod -R 777 /opt/mysqlcluster
cd /opt/mysqlcluster/home
wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.4/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz
tar -zxf mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz
ln -s mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64 mysqlc
sudo chmod -R 777 /etc/profile.d

# Setup Executable Path Globally
echo "export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc" > /etc/profile.d/mysqlc.sh
echo "export PATH=$MYSQLC_HOME/bin:$PATH" >> /etc/profile.d/mysqlc.sh
source /etc/profile.d/mysqlc.sh
sudo apt-get update && sudo apt-get -y install libncurses5

# Master specific steps from here on

sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data
sudo chmod -R 777 /opt/mysqlcluster/home/mysqlc/bin
sudo /opt/mysqlcluster/home/mysqlc/bin/ndbd -c ip-172-31-10-58.ec2.internal