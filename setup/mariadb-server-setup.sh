#!/bin/bash

# Install mariadb-server
sudo apt-get -y install mariadb-server
echo "Installation of mariadb-server complete!"
echo

# Configure mariadb-server
sudo cp mariadb_cf/my.cnf.spar /etc/mysql/my.cnf
sudo chown root:root /etc/mysql/my.cnf
sudo chmod 644 /etc/mysql/my.cnf

echo "Updated my.cnf...restarting mysqld"
echo
sudo service mysql restart
