#!/bin/bash
sudo apt-get update
yes | sudo apt-get upgrade
# yes | sudo apt-get install mysql-server
# Install mysql cluster
sudo mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home
sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.4/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz
sudo tar -zxf mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz
sudo ln -s mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64 mysqlc

# Edit script
sudo nano <<EOF >/etc/profile.d/mysqlc.sh
export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc
export PATH=$MYSQLC_HOME/bin:$PATH
EOF
source /etc/profile.d/mysqlc.sh

# Master only
sudo mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir conf
sudo mkdir mysqld_data
sudo mkdir ndb_data
cd conf

# Edit my.cnf
sudo touch my.cnf
sudo cat <<EOF >my.cnf
[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306
EOF

# Edit config.ini
sudo touch config.ini
sudo cat <<EOF >config.ini
[ndb_mgmd]
hostname=ip-172-31-9-158.ec2.internal
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1

[ndbd default]
noofreplicas=3
datadir=/opt/mysqlcluster/deploy/ndb_data

[ndbd]
hostname=ip-172-31-15-71.ec2.internal
nodeid=3
serverport=50501

[ndbd]
hostname=ip-172-31-8-196.ec2.internal
nodeid=4
serverport=50502

[ndbd]
hostname=ip-172-31-10-95.ec2.internal
nodeid=5
serverport=50503

[mysqld]
nodeid=50
EOF

# Initialize management node
cd /opt/mysqlcluster/home/mysqlc
sudo scripts/mysql_install_db –no-defaults –datadir=/opt/mysqlcluster/deploy/mysqld_data

# Start managent node 
sudo env "PATH=$PATH" ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini –initial –configdir=/opt/mysqlcluster/deploy/conf

# Check health of mgmt/data nodes
sudo env "PATH=$PATH" ndb_mgm -e show

# Start SQL node
sudo env "PATH=$PATH" mysqld –defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf –user=root &


# Check health of mgmt/data nodes
sudo env "PATH=$PATH" ndb_mgm -e show

# Secure MySQL installation 
# https://fedingo.com/how-to-automate-mysql_secure_installation-script/
sudo mysql -e "UPDATE mysql.user SET Password=PASSWORD('root') WHERE User='root';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
sudo mysql -e "DROP DATABASE IF EXISTS test;"
sudo mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\_%';"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql -e "CREATE USER 'cedric'@'%' IDENTIFIED BY 'password';"
sudo mysql -e "GRANT ALL PRIVILEGES on sakila.* TO 'cedric'@'localhost';"

# Sakila
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"

# Sysbench installation and benchmarking
yes | sudo apt-get install sysbench
sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 /usr/share/sysbench/oltp_read_write.lua --mysql_storage_engine=ndbcluster prepare
sysbench --db-driver=mysql --mysql-host=127.0.0.1 --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 --num-threads=6 --max-time=60 /usr/share/sysbench/oltp_read_write.lua --mysql_storage_engine=ndbcluster run > cluster.txt
