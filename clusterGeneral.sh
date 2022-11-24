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
