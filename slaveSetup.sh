#!/bin/bash
sudo apt-get update
yes | sudo apt-get upgrade
# yes | sudo apt-get install mysql-server
# Install mysql cluster
sudo wget https://cdn.mysql.com/archives/mysql-cluster-gpl-8.0/mysql-cluster-8.0.30-linux-glibc2.12-x86_64.tar.gz
sudo tar xvf mysql-cluster-8.0.30-linux-glibc2.12-x86_64.tar.gz
sudo ln -s mysql-cluster-8.0.30-linux-glibc2.12-x86_64 mysqlc

# Edit script
sudo nano <<EOF >/etc/profile.d/mysqlc.sh
export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc
export PATH=$MYSQLC_HOME/bin:$PATH
EOF
source /etc/profile.d/mysqlc.sh

# Slave only
sudo mkdir -p /opt/mysqlcluster/deploy/ndb_data