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

sudo mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir conf
sudo mkdir mysqld_data
sudo mkdir ndb_data
cd conf
sudo chmod -R 777 /opt/mysqlcluster/deploy


# Edit my.cnf
sudo nano <<EOF >my.cnf
[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306
EOF

# Edit config.ini
cat <<EOF >config.ini
[ndb_mgmd]
hostname=ip-172-31-10-58.ec2.internal
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1

[ndbd default]
noofreplicas=3
datadir=/opt/mysqlcluster/deploy/ndb_data

[ndbd]
hostname=ip-172-31-13-240.ec2.internal
nodeid=3
serverport=50501

[ndbd]
hostname=ip-172-31-1-189.ec2.internal
nodeid=4
serverport=50502

[ndbd]
hostname=ip-172-31-3-103.ec2.internal
nodeid=5
serverport=50503

[mysqld]
nodeid=50
EOF

# Initialize management node
cd /opt/mysqlcluster/home/mysqlc
scripts/mysql_install_db --no-defaults --datadir=/opt/mysqlcluster/deploy/mysqld_data

# Start managent node 
sudo /opt/mysqlcluster/home/mysqlc/bin/ndb_mgmd  -f /opt/mysqlcluster/deploy/conf/config.ini --initial --configdir=/opt/mysqlcluster/deploy/conf/