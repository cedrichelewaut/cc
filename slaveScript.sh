#!/bin/bash
sudo apt-get update
yes | sudo apt-get upgrade

# Install mysql cluster
mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home
wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.4/mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz
tar -zxf mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64.tar.gz
ln -s mysql-cluster-gpl-7.4.10-linux-glibc2.5-x86_64 mysqlc

# Edit script
cat <<EOF >/etc/profile.d/mysqlc.sh
export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc
export PATH=$MYSQLC_HOME/bin:$PATH
EOF
source /etc/profile.d/mysqlc.sh

mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir conf
sudo mkdir mysqld_data
sudo mkdir ndb_data
sudo env "PATH=$PATH" ndbd -c ip-172-31-9-158.ec2.internal:1186
cd conf

# Edit my.cnf
sudo touch my.cnf
sudo cat <<EOF >my.cnf
[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
ndb-connectstring=172.31.9.158
[mysql_cluster]
ndb-connectstring=172.31.9.158
EOF


# Start SQL node
cd /opt/mysqlcluster/home/mysqlc
sudo env "PATH=$PATH" mysqld –defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf –user=root &
































































sudo apt-get update
yes | sudo apt-get upgrade
yes | sudo apt-get install mysql-server
# Common steps on all Nodes

# Download and Extract MySQL Cluster Binaries
mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home
wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz/from/http://mysql.mirrors.pair.com/
tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 mysqlc

# In case wget changes the name of the tar to index.html do: 
mv index.html mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
tar xvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 mysqlc

# Setup Executable Path Globally
echo ‘export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc’ > /etc/profile.d/mysqlc.sh
echo ‘export PATH=$MYSQLC_HOME/bin:$PATH’ >> /etc/profile.d/mysqlc.sh
source /etc/profile.d/mysqlc.sh

# Create the Deployment Directory and Setup Config Files
mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
mkdir conf
mkdir mysqld_data
mkdir ndb_data
cd conf
cat <<EOF >my.cnf
[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306
EOF
cat <<EOF >config.ini
[ndb_mgmd]
hostname=ip-172-31-0-49.ec2.internal
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1

[ndbd default]
noofreplicas=3
datadir=/opt/mysqlcluster/deploy/ndb_data

[ndbd]
hostname=ip-172-31-0-29.ec2.internal
nodeid=3


[ndbd]
hostname=ip-172-31-6-8.ec2.internal
nodeid=4

[ndbd]
hostname=ip-172-31-14-164.ec2.internal
nodeid=5

[mysqld]
nodeid=50
EOF

# Initialize the Database
cd /opt/mysqlcluster/home/mysqlc
scripts/mysql_install_db –no-defaults –datadir=/opt/mysqlcluster/deploy/mysqld_data

# Start management node
ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini –initial –configdir=/opt/mysqlcluster/deploy/conf

# Check health of mgmt/data nodes
ndb_mgm -e show

# Start SQL node
mysqld –defaults-file=/opt/mysqlcluster/deploy/conf/my.cnf –user=root &

# Check health of mgmt/data nodes
ndb_mgm -e show

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

# Prepare
sysbench --db-driver=mysql --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 /usr/share/sysbench/oltp_read_write.lua prepare
sysbench --db-driver=mysql --mysql-user=cedric --mysql_password=password --mysql-db=sakila --tables=8 --table-size=1000 --num-threads=6 --max-time=60 /usr/share/sysbench/oltp_read_write.lua run > cluster.txt